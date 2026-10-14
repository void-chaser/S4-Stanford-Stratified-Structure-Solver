#!/usr/bin/env python3
# gate_check_r8m1b2.py -- P05-S4 R8 M1b2 gate helper. New file.
import hashlib, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

EXPECTED_BASE = "274738dd2367db15a6915d1bccf7babd66394623"
EXPECTED_M1B_SHA = "66696e831b18a98c1bad30903a45a39e525b6b1c0f9563b01b0f135f343829e2"
EXPECTED_M1C_SHA = "e1e555ee4ca20421b6e5681e18be6cd1b873fc7cff06d246c01fad65d8d3a562"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECTED_S4_TREE = "6cff923a02baf19e01966b2339755cbf3a5deeef"
EXPECTED_F2_TREE = "e124925f5b242486a913b813fa181664f665b048"

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
                key = parts[1]
                val = parts[2]
                if val.startswith("value="):
                    val = val[6:]
                records[key] = val
    return records

def run_checks(mode, start_file=None):
    results = [] # (status, check_name, expected, actual)
    fails = 0

    def check(name, cond, exp, act):
        nonlocal fails
        st = "PASS" if cond else "FAIL"
        if not cond:
            fails += 1
        results.append((st, name, str(exp), str(act)))

    # 1. Base / Commit check
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    if mode == "start":
        check("HEAD_IS_BASE", head == EXPECTED_BASE, EXPECTED_BASE, head)
    else:
        # At end: head can be base, or head can be a commit whose parent is base (e.g. freeze commit)
        parent = ""
        try:
            parent = subprocess.check_output(["git", "rev-parse", "HEAD^"], cwd=REPO, text=True).strip()
        except Exception:
            pass
        head_ok = (head == EXPECTED_BASE) or (parent == EXPECTED_BASE)
        check("HEAD_VALID_FOR_END", head_ok, "base or child-of-base", head)

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

    # 4. r8m1b1 SHA256SUMS.txt all -c OK
    m1b1_dir = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1b", "r8m1b1")
    m1b1_sums = os.path.join(m1b1_dir, "SHA256SUMS.txt")
    check("M1B1_SUMS_EXISTS", os.path.isfile(m1b1_sums), "exists", "exists" if os.path.isfile(m1b1_sums) else "missing")
    if os.path.isfile(m1b1_sums):
        m1b1_ok = True
        m1b1_count = 0
        with open(m1b1_sums, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                exp_sha, fname = line.split(None, 1)
                fpath = os.path.join(m1b1_dir, fname)
                m1b1_count += 1
                if not os.path.isfile(fpath) or sha256_file(fpath) != exp_sha:
                    m1b1_ok = False
                    break
        check("M1B1_ALL_FILES_MATCH_SHA256", m1b1_ok and m1b1_count == 9, "all 9 OK", ("all %d OK" % m1b1_count) if (m1b1_ok and m1b1_count == 9) else "mismatch")

    # 5. M1a6 SHA256SUMS_R8_M1a6.txt all 16 files -c OK
    m1a_dir = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
    m1a6_sums = os.path.join(m1a_dir, "SHA256SUMS_R8_M1a6.txt")
    check("M1A6_SUMS_EXISTS", os.path.isfile(m1a6_sums), "exists", "exists" if os.path.isfile(m1a6_sums) else "missing")
    if os.path.isfile(m1a6_sums):
        m1a6_ok = True
        m1a6_count = 0
        with open(m1a6_sums, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                exp_sha, fname = line.split(None, 1)
                fpath = os.path.join(m1a_dir, fname)
                m1a6_count += 1
                if not os.path.isfile(fpath) or sha256_file(fpath) != exp_sha:
                    m1a6_ok = False
                    break
        check("M1A6_ALL_FILES_MATCH_SHA256", m1a6_ok and m1a6_count == 16, "all 16 OK", ("all %d OK" % m1a6_count) if (m1a6_ok and m1a6_count == 16) else "mismatch")

    # 6. Two M1a6 preregistrations hashes match PREREG_RECORD
    m1b_path = os.path.join(m1a_dir, "REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv")
    m1c_path = os.path.join(m1a_dir, "REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv")
    m1b_act_sha = sha256_file(m1b_path) if os.path.isfile(m1b_path) else "missing"
    m1c_act_sha = sha256_file(m1c_path) if os.path.isfile(m1c_path) else "missing"
    check("M1B_PREREG_SHA256", m1b_act_sha == EXPECTED_M1B_SHA, EXPECTED_M1B_SHA, m1b_act_sha)
    check("M1C_PREREG_SHA256", m1c_act_sha == EXPECTED_M1C_SHA, EXPECTED_M1C_SHA, m1c_act_sha)

    prereg_rec_path = os.path.join(m1a_dir, "PREREG_RECORD_R8_M1a6.txt")
    prereg_rec_text = open(prereg_rec_path, encoding="utf-8").read() if os.path.isfile(prereg_rec_path) else ""
    check("PREREG_RECORD_M1B_MATCH", EXPECTED_M1B_SHA in prereg_rec_text, "contains m1b sha", "matched" if EXPECTED_M1B_SHA in prereg_rec_text else "not found")
    check("PREREG_RECORD_M1C_MATCH", EXPECTED_M1C_SHA in prereg_rec_text, "contains m1c sha", "matched" if EXPECTED_M1C_SHA in prereg_rec_text else "not found")

    # 7. RULINGS & ERRATA_8 prefix checks (living files, append only)
    rulings_path = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")
    errata8_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "ERRATA_8.txt")

    rul_base = subprocess.check_output(["git", "show", EXPECTED_BASE + ":checkpoints/p05/registries/RULINGS.tsv"], cwd=REPO)
    rul_now = open(rulings_path, "rb").read() if os.path.isfile(rulings_path) else b""
    check("RULINGS_BASE_PREFIX_UNCHANGED", rul_now.startswith(rul_base), True, rul_now.startswith(rul_base))

    # All non-comment, non-empty lines in RULINGS.tsv must have 5 tab-separated fields
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

    # In end mode, verify prefix against start gate records if available
    start_records = parse_start_records(start_file)
    if mode == "end" and start_records:
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

    # 8. STATE <= 8192 UTF-8 bytes
    state_path = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
    state_bytes = len(open(state_path, "rb").read()) if os.path.isfile(state_path) else 999999
    check("STATE_BYTES_LE_8192", state_bytes <= 8192, "<= 8192", state_bytes)

    # 9. No tracked files under testing/d003 modified or deleted
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
