#!/usr/bin/env python3
# gate_check_r8m1c1.py -- P05-S4 R8 M1c1 gate helper. New file (copied from gate_check_r8m1b3.py; original unchanged).
import hashlib, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

EXPECTED_BASE = "9d8333364d57977bbeb00e1ce522924b2399fd51"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECTED_S4_TREE = "6cff923a02baf19e01966b2339755cbf3a5deeef"
EXPECTED_F2_TREE = "e124925f5b242486a913b813fa181664f665b048"
EXPECTED_M1C_PREREG_SHA = "e1e555ee4ca20421b6e5681e18be6cd1b873fc7cff06d246c01fad65d8d3a562"
HIST_RUNNERS = [
    "testing/d003/stage_s4/run_r6c_state.py",
    "testing/d003/stage_s4/r6c2_seam_state.py",
    "testing/d003/stage_s4/r6c_judge.py",
    "testing/d003/stage_s4/r6c2_seam_judge.py",
    "testing/d003/stage_s4/r6c_state.gdb",
    "testing/d003/stage_s4/r6c_state_gdb.py",
]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def parse_start_records(start_file):
    records = {}
    if not start_file or not os.path.isfile(start_file):
        return records
    with open(start_file, encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\r\n").split("\t")
            if len(parts) >= 3 and parts[0] == "RECORD":
                val = parts[2]
                if val.startswith("value="):
                    val = val[6:]
                records[parts[1]] = val
    return records

def check_sums_dir(dir_path, expected_count):
    """Return (ok, detail). Verifies every listed file's sha256 and that the listed
    set (sorted) equals the directory file set minus SHA256SUMS.txt (sorted)."""
    sums = os.path.join(dir_path, "SHA256SUMS.txt")
    if not os.path.isfile(sums):
        return False, "missing SHA256SUMS.txt"
    listed = []
    with open(sums, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            exp_sha, fname = line.split(None, 1)
            listed.append((exp_sha, fname))
    listed_names = sorted(f for _, f in listed)
    dir_names = sorted(n for n in os.listdir(dir_path) if n != "SHA256SUMS.txt")
    if listed_names != dir_names:
        return False, "file list differs (sorted compare)"
    if len(listed) != expected_count:
        return False, "count %d != %d" % (len(listed), expected_count)
    for exp_sha, fname in listed:
        fpath = os.path.join(dir_path, fname)
        if not os.path.isfile(fpath) or sha256_file(fpath) != exp_sha:
            return False, "sha mismatch: %s" % fname
    return True, "all %d OK" % len(listed)

def run_checks(mode, start_file=None):
    results = []  # (status, check_name, expected, actual)
    fails = 0

    def check(name, cond, exp, act):
        nonlocal fails
        st = "PASS" if cond else "FAIL"
        if not cond:
            fails += 1
        results.append((st, name, str(exp), str(act)))

    # 1. HEAD equals the frozen base in both modes (end mode does not inspect HEAD^)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    check("HEAD_IS_BASE", head == EXPECTED_BASE, EXPECTED_BASE, head)

    # 2. S4 tree checks
    head_s4 = subprocess.check_output(["git", "rev-parse", "HEAD:S4"], cwd=REPO, text=True).strip()
    check("HEAD_S4_TREE", head_s4 == EXPECTED_S4_TREE, EXPECTED_S4_TREE, head_s4)
    f3_s4 = subprocess.check_output(["git", "rev-parse", "8d8202a:S4"], cwd=REPO, text=True).strip()
    check("F3_8d8202a_S4_TREE", f3_s4 == EXPECTED_S4_TREE, EXPECTED_S4_TREE, f3_s4)
    f2_s4 = subprocess.check_output(["git", "rev-parse", "a07b5ac:S4"], cwd=REPO, text=True).strip()
    check("F2_a07b5ac_S4_TREE", f2_s4 == EXPECTED_F2_TREE, EXPECTED_F2_TREE, f2_s4)

    # 3. Judge sha256
    judge_path = os.path.join(REPO, "testing", "d003", "judge_d003.py")
    judge_sha = sha256_file(judge_path) if os.path.isfile(judge_path) else "missing"
    check("JUDGE_SHA256", judge_sha == EXPECTED_JUDGE_SHA, EXPECTED_JUDGE_SHA, judge_sha)

    # 4. M1c prereg sha256 (frozen in brief section 0)
    prereg = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a", "REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv")
    prereg_sha = sha256_file(prereg) if os.path.isfile(prereg) else "missing"
    check("M1C_PREREG_SHA256", prereg_sha == EXPECTED_M1C_PREREG_SHA, EXPECTED_M1C_PREREG_SHA, prereg_sha)

    # 5. r8m1b3 (10 files) SHA256SUMS all OK; r8m1b1 and r8m1b2 are checked at their own recorded lists
    for tag, cnt in (("r8m1b3", 10),):
        d = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1b", tag)
        ok, detail = check_sums_dir(d, cnt)
        check("%s_SUMS_ALL_OK" % tag.upper(), ok, "all %d OK" % cnt, detail)

    # 6. s4r8 SHA256SUMS: all lines except the living ERRATA_8.txt line must verify (-c OK).
    #    ERRATA_8.txt is checked by prefix (U121 / MEMORY) in section 7.
    s4r8 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8")
    sums_path = os.path.join(s4r8, "SHA256SUMS.txt")
    sums_bad = []
    sums_n = 0
    err8_line_sha = None
    with open(sums_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            exp_sha, fname = line.split(None, 1)
            if fname == "ERRATA_8.txt":
                err8_line_sha = exp_sha
                continue
            sums_n += 1
            fpath = os.path.join(s4r8, fname)
            if not os.path.isfile(fpath) or sha256_file(fpath) != exp_sha:
                sums_bad.append(fname)
    check("S4R8_SUMS_NONERRATA_ALL_OK", not sums_bad, "all %d OK" % sums_n, "bad=%s" % (sums_bad,))

    # 7. RULINGS & ERRATA_8 prefix checks (living files, append only)
    rulings_path = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")
    errata8_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "ERRATA_8.txt")

    rul_base = subprocess.check_output(["git", "show", EXPECTED_BASE + ":checkpoints/p05/registries/RULINGS.tsv"], cwd=REPO)
    rul_now = open(rulings_path, "rb").read() if os.path.isfile(rulings_path) else b""
    check("RULINGS_BASE_PREFIX_UNCHANGED", rul_now.startswith(rul_base), True, rul_now.startswith(rul_base))

    rul_lines_ok = True
    for l in rul_now.decode("utf-8").splitlines():
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        if len(l.split("\t")) != 5:
            rul_lines_ok = False
            break
    check("RULINGS_LINES_5_FIELDS", rul_lines_ok, True, rul_lines_ok)

    err_base = subprocess.check_output(["git", "show", EXPECTED_BASE + ":checkpoints/p05/registries/s4r8/ERRATA_8.txt"], cwd=REPO)
    err_now = open(errata8_path, "rb").read() if os.path.isfile(errata8_path) else b""
    check("ERRATA_8_BASE_PREFIX_UNCHANGED", err_now.startswith(err_base), True, err_now.startswith(err_base))

    # 8. ERRATA_8 prefix of the living file (SHA256SUMS.txt line) at the R8 M1a6 record (72dc6aed..., 13990 bytes)
    check("ERRATA_8_SUMS_LINE_PREFIX", hashlib.sha256(err_now[:13990]).hexdigest() == "72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551", "72dc6aed...", hashlib.sha256(err_now[:13990]).hexdigest())

    start_records = parse_start_records(start_file)
    if mode == "end":
        check("START_RECORDS_PRESENT", bool(start_records), True, bool(start_records))
        start_rul_sha = start_records.get("RULINGS_SHA256")
        start_rul_bytes = int(start_records.get("RULINGS_BYTES", "0"))
        start_err_sha = start_records.get("ERRATA_8_SHA256")
        start_err_bytes = int(start_records.get("ERRATA_8_BYTES", "0"))
        if start_rul_bytes > 0:
            rul_pfx_sha = hashlib.sha256(rul_now[:start_rul_bytes]).hexdigest()
            check("RULINGS_PREFIX_OF_START_UNCHANGED", rul_pfx_sha == start_rul_sha, start_rul_sha, rul_pfx_sha)
            check("RULINGS_NOT_TRUNCATED", len(rul_now) >= start_rul_bytes, True, len(rul_now) >= start_rul_bytes)
        if start_err_bytes > 0:
            err_pfx_sha = hashlib.sha256(err_now[:start_err_bytes]).hexdigest()
            check("ERRATA_8_PREFIX_OF_START_UNCHANGED", err_pfx_sha == start_err_sha, start_err_sha, err_pfx_sha)
            check("ERRATA_8_NOT_TRUNCATED", len(err_now) >= start_err_bytes, True, len(err_now) >= start_err_bytes)

    # 9. Historical runners and judges: sha256 equal to HEAD version; unchanged since d58bafd
    for rel in HIST_RUNNERS:
        head_blob = subprocess.check_output(["git", "rev-parse", "HEAD:" + rel], cwd=REPO, text=True).strip()
        d58_blob = subprocess.check_output(["git", "rev-parse", "d58bafd:" + rel], cwd=REPO, text=True).strip()
        wt = subprocess.check_output(["git", "hash-object", os.path.join(REPO, rel)], cwd=REPO, text=True).strip()
        check("HIST_UNCHANGED_SINCE_D58BAFD " + os.path.basename(rel), head_blob == d58_blob == wt, head_blob, "%s|%s|%s" % (head_blob, d58_blob, wt))

    # 10. STATE <= 8192 UTF-8 bytes
    state_path = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
    state_bytes = len(open(state_path, "rb").read()) if os.path.isfile(state_path) else 999999
    check("STATE_BYTES_LE_8192", state_bytes <= 8192, "<= 8192", state_bytes)

    # 11. No tracked files under testing/d003 modified or deleted
    diff_d003 = subprocess.check_output(["git", "diff", "--name-only", "--diff-filter=MD", "HEAD", "--", "testing/d003"], cwd=REPO, text=True).strip()
    check("TRACKED_TESTING_D003_NO_MOD_DEL", diff_d003 == "", "no modified or deleted", diff_d003 if diff_d003 else "clean")

    return fails, results

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "start"
    start_file = sys.argv[2] if len(sys.argv) > 2 else None
    fails, results = run_checks(mode, start_file)
    for st, name, exp, act in results:
        print("%s\t%s\texpected=%s\tactual=%s" % (st, name, exp, act))
    print("PYTHON_CHECKS_FAILS=%d" % fails)
    sys.exit(fails)
