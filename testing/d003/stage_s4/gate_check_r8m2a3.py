#!/usr/bin/env python3
# gate_check_r8m2a3.py -- P05-S4 R8 M2a3 gate helper. New file (copied from gate_check_r8m2a2.py; original unchanged).
# Baseline HEAD: c66b7d2ca11927b5de652e5db8cfd8e7e215fbc8
# Checks:
#  - baseline HEAD c66b7d2; STATE/RULINGS/ERRATA_8 start values from r8m2a2 closeout;
#  - start-only: r8m2a2 SHA256SUMS.txt (60 entries) -c OK; postcommit_r8m2a2.py tracked + sha;
#  - stray build products are BASELINE-based: start writes STRAY_BASELINE_R8_M2a3.tsv (path, bytes, mtime_ns, sha256)
#    and checks the two known testing/d003 pyc files; end rescans and fails only for new or changed entries.
import hashlib, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2a3")
EV = os.path.join(REPO, EV_REL)
BASELINE_TSV = os.path.join(EV, "STRAY_BASELINE_R8_M2a3.tsv")

EXPECTED_BASE = "c66b7d2ca11927b5de652e5db8cfd8e7e215fbc8"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECTED_S4_TREE = "6cff923a02baf19e01966b2339755cbf3a5deeef"
EXPECTED_F2_TREE = "e124925f5b242486a913b813fa181664f665b048"
EXPECTED_B_TREE = "1d738e64f9864a475fdb3de34cd3601605df2c64"
EXPECTED_POSTCOMMIT_R8M2A2_SHA = "60d8d5ad99d585208afbb8b72f73de8a0f967d231f0bce10068a1f2a01ec1a97"
EXPECTED_PREREG_R8M2A2_SHA = "1b60f95ccb1ab4b77e26d71fc1d9bf4f4fee25c29092ae0c3620a6c9e42be7ce"
EXPECTED_STATE_BYTES = 8077
EXPECTED_STATE_SHA = "6dce1b93dbc4a51b1d83cc370ecd293406880169eecf80dc690a9ccc03d05c21"
EXPECTED_RULINGS_BYTES = 101120
EXPECTED_RULINGS_SHA = "d2aced9b76e8a2e69845f076f78a71b6d7954e7691829814cf60abcec1f6cd1d"
EXPECTED_ERRATA8_BYTES = 68512
EXPECTED_ERRATA8_SHA = "6f1d1366f3340712629140dae7c4b585045113317abc05ec38b270ff3eb0149d"

HIST_RUNNERS = [
    "testing/d003/stage_s4/run_r6c_state.py",
    "testing/d003/stage_s4/r6c2_seam_state.py",
    "testing/d003/stage_s4/r6c_judge.py",
    "testing/d003/stage_s4/r6c2_seam_judge.py",
    "testing/d003/stage_s4/r6c_state.gdb",
    "testing/d003/stage_s4/r6c_state_gdb.py",
]
R8M2A2_DIR = os.path.join("checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a2")
KNOWN_PYC = [
    "testing/d003/__pycache__/judge_d003.cpython-314.pyc",
    "testing/d003/__pycache__/matrix_r2.cpython-314.pyc",
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


def read_sums(sums_path):
    listed = []
    with open(sums_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            exp_sha, fname = line.split(None, 1)
            listed.append((exp_sha, fname))
    return listed


def verify_sums_dir(dir_path, expected_count):
    sums = os.path.join(dir_path, "SHA256SUMS.txt")
    if not os.path.isfile(sums):
        return False, "missing SHA256SUMS.txt"
    listed = read_sums(sums)
    if len(listed) != expected_count:
        return False, "count %d != %d" % (len(listed), expected_count)
    for exp_sha, fname in listed:
        fpath = os.path.join(dir_path, fname)
        if not os.path.isfile(fpath) or sha256_file(fpath) != exp_sha:
            return False, "sha mismatch: %s" % fname
    return True, "all %d OK" % len(listed)


def scan_build_products():
    out = {}
    ev_all = os.path.join(REPO, "checkpoints", "p05", "evidence")
    scan_roots = [os.path.join(REPO, "testing", "d003"), os.path.join(REPO, "checkpoints", "p05")]
    for base in scan_roots:
        for root, dirs, files in os.walk(base):
            if root == ev_all or root.startswith(ev_all + os.sep):
                dirs[:] = []
                continue
            for d in list(dirs):
                if d == "__pycache__":
                    rel = os.path.relpath(os.path.join(root, d), REPO)
                    out[rel] = ("DIR", 0, os.stat(os.path.join(root, d)).st_mtime_ns, "-")
                    for root2, _dirs2, files2 in os.walk(os.path.join(root, d)):
                        for f2 in files2:
                            p2 = os.path.join(root2, f2)
                            st = os.stat(p2)
                            out[os.path.relpath(p2, REPO)] = ("FILE", st.st_size, st.st_mtime_ns, sha256_file(p2))
            for f in files:
                if f.endswith(".o") or f == "a.out":
                    p = os.path.join(root, f)
                    st = os.stat(p)
                    out[os.path.relpath(p, REPO)] = ("FILE", st.st_size, st.st_mtime_ns, sha256_file(p))
    return out


def write_baseline(entries):
    os.makedirs(EV, exist_ok=True)
    with open(BASELINE_TSV, "x", encoding="utf-8") as fh:
        fh.write("# STRAY_BASELINE_R8_M2a3 (start): path\tkind\tbytes\tmtime_ns\tsha256\n")
        for k in sorted(entries):
            kind, size, mt, sh = entries[k]
            fh.write("%s\t%s\t%d\t%d\t%s\n" % (k, kind, size, mt, sh))


def read_baseline():
    out = {}
    with open(BASELINE_TSV, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            k, kind, size, mt, sh = line.rstrip("\n").split("\t")
            out[k] = (kind, int(size), int(mt), sh)
    return out


def run_checks(mode, start_file=None):
    results = []
    fails = 0

    def check(name, cond, exp, act):
        nonlocal fails
        st = "PASS" if cond else "FAIL"
        if not cond:
            fails += 1
        results.append((st, name, str(exp), str(act)))

    # 1. HEAD equals the frozen base in both modes
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    check("HEAD_IS_BASE", head == EXPECTED_BASE, EXPECTED_BASE, head)

    # 2. S4 tree checks
    head_s4 = subprocess.check_output(["git", "rev-parse", "HEAD:S4"], cwd=REPO, text=True).strip()
    check("HEAD_S4_TREE", head_s4 == EXPECTED_S4_TREE, EXPECTED_S4_TREE, head_s4)
    f3_s4 = subprocess.check_output(["git", "rev-parse", "8d8202a:S4"], cwd=REPO, text=True).strip()
    check("F3_8d8202a_S4_TREE", f3_s4 == EXPECTED_S4_TREE, EXPECTED_S4_TREE, f3_s4)
    f2_s4 = subprocess.check_output(["git", "rev-parse", "a07b5ac:S4"], cwd=REPO, text=True).strip()
    check("F2_a07b5ac_S4_TREE", f2_s4 == EXPECTED_F2_TREE, EXPECTED_F2_TREE, f2_s4)
    b_s4 = subprocess.check_output(["git", "rev-parse", "37a82e8:S4"], cwd=REPO, text=True).strip()
    check("B_37a82e8_S4_TREE", b_s4 == EXPECTED_B_TREE, EXPECTED_B_TREE, b_s4)

    # 3. Judge sha256
    judge_path = os.path.join(REPO, "testing", "d003", "judge_d003.py")
    judge_sha = sha256_file(judge_path) if os.path.isfile(judge_path) else "missing"
    check("JUDGE_SHA256", judge_sha == EXPECTED_JUDGE_SHA, EXPECTED_JUDGE_SHA, judge_sha)

    # 4. start-only: STATE.md size and sha256; r8m2a2 postcommit, prereg; r8m2a2 manifests
    if mode == "start":
        state_path = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
        state_b = open(state_path, "rb").read() if os.path.isfile(state_path) else b""
        check("STATE_START_BYTES", len(state_b) == EXPECTED_STATE_BYTES, EXPECTED_STATE_BYTES, len(state_b))
        check("STATE_START_SHA256", hashlib.sha256(state_b).hexdigest() == EXPECTED_STATE_SHA, EXPECTED_STATE_SHA, hashlib.sha256(state_b).hexdigest())
        pcm = os.path.join(REPO, "testing", "d003", "stage_s4", "postcommit_r8m2a2.py")
        pcm_sha = sha256_file(pcm) if os.path.isfile(pcm) else "missing"
        check("POSTCOMMIT_R8M2A2_SHA256", pcm_sha == EXPECTED_POSTCOMMIT_R8M2A2_SHA, EXPECTED_POSTCOMMIT_R8M2A2_SHA, pcm_sha)
        pcm_tracked = subprocess.check_output(["git", "ls-files", "testing/d003/stage_s4/postcommit_r8m2a2.py"], cwd=REPO, text=True).strip()
        check("POSTCOMMIT_R8M2A2_TRACKED", pcm_tracked == "testing/d003/stage_s4/postcommit_r8m2a2.py", "tracked", pcm_tracked or "untracked")
        pr = os.path.join(REPO, R8M2A2_DIR, "PREREG_M2_R8_M2a2.tsv")
        pr_sha = sha256_file(pr) if os.path.isfile(pr) else "missing"
        check("R8M2A2_PREREG_SHA256", pr_sha == EXPECTED_PREREG_R8M2A2_SHA, EXPECTED_PREREG_R8M2A2_SHA, pr_sha)
        ok_m2a2, detail_m2a2 = verify_sums_dir(os.path.join(REPO, R8M2A2_DIR), 60)
        check("R8M2A2_SUMS_60_ALL_OK", ok_m2a2, "all 60 OK", detail_m2a2)
        n_r8m2a2 = len(os.listdir(os.path.join(REPO, R8M2A2_DIR)))
        check("R8M2A2_DIR_FILE_COUNT_61", n_r8m2a2 == 61, 61, n_r8m2a2)

    # 5. RULINGS & ERRATA_8 prefix checks (living files, append only)
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

    # 6. Start-only: the append bases recorded at start
    if mode == "start":
        check("RULINGS_START_BYTES", len(rul_now) == EXPECTED_RULINGS_BYTES, EXPECTED_RULINGS_BYTES, len(rul_now))
        check("RULINGS_START_SHA256", hashlib.sha256(rul_now).hexdigest() == EXPECTED_RULINGS_SHA, EXPECTED_RULINGS_SHA, hashlib.sha256(rul_now).hexdigest())
        check("ERRATA_8_START_BYTES", len(err_now) == EXPECTED_ERRATA8_BYTES, EXPECTED_ERRATA8_BYTES, len(err_now))
        check("ERRATA_8_START_SHA256", hashlib.sha256(err_now).hexdigest() == EXPECTED_ERRATA8_SHA, EXPECTED_ERRATA8_SHA, hashlib.sha256(err_now).hexdigest())

    start_records = parse_start_records(start_file)
    if mode == "end":
        check("START_RECORDS_PRESENT", bool(start_records), True, bool(start_records))
        start_rul_sha = start_records.get("RULINGS_SHA256")
        start_rul_bytes = int(start_records.get("RULINGS_BYTES", "0"))
        start_err_sha = start_records.get("ERRATA_8_SHA256")
        start_err_bytes = int(start_records.get("ERRATA_8_BYTES", "0"))
        check("START_RULINGS_BASE_FROM_RECORD", (start_rul_bytes, start_rul_sha) == (EXPECTED_RULINGS_BYTES, EXPECTED_RULINGS_SHA), "record", "%s %s" % (start_rul_bytes, start_rul_sha))
        check("START_ERRATA8_BASE_FROM_RECORD", (start_err_bytes, start_err_sha) == (EXPECTED_ERRATA8_BYTES, EXPECTED_ERRATA8_SHA), "record", "%s %s" % (start_err_bytes, start_err_sha))
        if start_rul_bytes > 0:
            rul_pfx_sha = hashlib.sha256(rul_now[:start_rul_bytes]).hexdigest()
            check("RULINGS_PREFIX_OF_START_UNCHANGED", rul_pfx_sha == start_rul_sha, start_rul_sha, rul_pfx_sha)
            check("RULINGS_NOT_TRUNCATED", len(rul_now) >= start_rul_bytes, True, len(rul_now) >= start_rul_bytes)
        if start_err_bytes > 0:
            err_pfx_sha = hashlib.sha256(err_now[:start_err_bytes]).hexdigest()
            check("ERRATA_8_PREFIX_OF_START_UNCHANGED", err_pfx_sha == start_err_sha, start_err_sha, err_pfx_sha)
            check("ERRATA_8_NOT_TRUNCATED", len(err_now) >= start_err_bytes, True, len(err_now) >= start_err_bytes)
        # r8m2a2 directory: unchanged
        ok_m2a2_end, det_m2a2_end = verify_sums_dir(os.path.join(REPO, R8M2A2_DIR), 60)
        check("R8M2A2_ORIGINAL_60_SHA_UNCHANGED_END", ok_m2a2_end, "all 60 OK", det_m2a2_end)

    # 7. Baseline-based stray build products
    if mode == "start":
        entries = scan_build_products()
        if os.path.exists(BASELINE_TSV):
            check("STRAY_BASELINE_NOT_PRESENT_BEFORE_START", False, "absent", "present")
        else:
            write_baseline(entries)
        for kp in KNOWN_PYC:
            check("STRAY_BASELINE_HAS_" + os.path.basename(kp), kp in entries, "present", "present" if kp in entries else "absent")
        check("STRAY_BASELINE_COUNT_RECORDED", True, "recorded", len(entries))
    if mode == "end":
        base = read_baseline() if os.path.isfile(BASELINE_TSV) else {}
        now = scan_build_products()
        new_items = sorted(k for k in now if k not in base)
        changed_items = sorted(k for k in now if k in base and now[k] != base[k])
        removed_items = sorted(k for k in base if k not in now)
        check("STRAY_NEW_OR_CHANGED_NONE", (not new_items and not changed_items), "none", "new=%s changed=%s" % (new_items, changed_items))
        check("STRAY_BASELINE_REMOVED_NONE_INFO", True, "info", "removed=%s" % (removed_items,))

    # 8. Historical runners and judges
    for rel in HIST_RUNNERS:
        head_blob = subprocess.check_output(["git", "rev-parse", "HEAD:" + rel], cwd=REPO, text=True).strip()
        d58_blob = subprocess.check_output(["git", "rev-parse", "d58bafd:" + rel], cwd=REPO, text=True).strip()
        wt = subprocess.check_output(["git", "hash-object", os.path.join(REPO, rel)], cwd=REPO, text=True).strip()
        check("HIST_UNCHANGED_SINCE_D58BAFD " + os.path.basename(rel), head_blob == d58_blob == wt, head_blob, "%s|%s|%s" % (head_blob, d58_blob, wt))

    # 9. STATE <= 8192 UTF-8 bytes
    state_path = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
    state_bytes = len(open(state_path, "rb").read()) if os.path.isfile(state_path) else 999999
    check("STATE_BYTES_LE_8192", state_bytes <= 8192, "<= 8192", state_bytes)

    # 10. No tracked files under testing/d003 modified or deleted
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
