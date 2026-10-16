#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate_check_r9m2b.py -- P05-S4 R9 M2b gate helper. New file.
# Baseline HEAD: ebf3d007b921e64cdb838c714c0ea53299d365c9
import hashlib, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

EXPECTED_BASE = "ebf3d007b921e64cdb838c714c0ea53299d365c9"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECTED_S4_TREE_F4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXPECTED_S4_TREE_F3 = "6cff923a02baf19e01966b2339755cbf3a5deeef"
EXPECTED_F2_TREE = "e124925f5b242486a913b813fa181664f665b048"
EXPECTED_B_TREE = "1d738e64f9864a475fdb3de34cd3601605df2c64"

EXPECTED_STATE_BYTES = 7014
EXPECTED_STATE_SHA = "18a56a5667508cc29ac5911d8df5f86f213bad39108039bd7e6fe7dfafc9d4ae"
EXPECTED_RULINGS_BYTES = 121086
EXPECTED_RULINGS_SHA = "f17bd838a699282b7a993f82ee93455aceae06e3ba3bb3d07b5277a5d20e6986"
EXPECTED_ERRATA_S3R5_BYTES = 1712
EXPECTED_ERRATA_S3R5_SHA = "a23ff03cd260548ae74205ca27c94d47a8a677d9c47bacfc5be6f5dec3077349"
EXPECTED_ERRATA_9_BYTES = 260
EXPECTED_ERRATA_9_SHA = "c381586d31f0d640d5a8daf4c1125d76c67ec68c6c033e10c71730cbc429034c"

HIST_RUNNERS = [
    "testing/d003/stage_s4/run_r6c_state.py",
    "testing/d003/stage_s4/r6c2_seam_state.py",
    "testing/d003/stage_s4/r6c_judge.py",
    "testing/d003/stage_s4/r6c2_seam_judge.py",
    "testing/d003/stage_s4/r6c_state.gdb",
    "testing/d003/stage_s4/r6c_state_gdb.py",
]

S3R5_DIR = os.path.join("checkpoints", "p05", "registries", "s3r5")
M0_DIR = os.path.join("checkpoints", "p05", "registries", "s4r9", "M0")
M2_DIR = os.path.join("checkpoints", "p05", "registries", "s4r9", "M2")

KNOWN_PYC = [
    "testing/d003/__pycache__/judge_d003.cpython-314.pyc",
    "testing/d003/__pycache__/matrix_r2.cpython-314.pyc",
]

S3R5_ARTIFACTS = [
    ("lib_F4_dbg", "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_dbg/libS4.a", "6a711fbbec84d1fb322ee1d9c678ae6750a04f647e3f1eba7840c8c7502fae26"),
    ("lib_F4_san", "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_san/libS4.a", "ce057b5065bb5ac487d66992930991c1f09f17431abfc957777f375436be0fbd"),
    ("lib_F4_plain", "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_plain/libS4.a", "5a4bfa601bf14b896b9c0c25807c0a38c05d040a17268cf0669902763cda5757"),
    ("init-F4-dbg", "checkpoints/p05/evidence/p05-s3r5/build/init-F4-dbg", "a4643e7e67ad74019104466ff9773ec2cfc1e684e488705a16a4a8f32526aca2"),
    ("init-F4-san", "checkpoints/p05/evidence/p05-s3r5/build/init-F4-san", "33a230029df224ddecb64f0884833e7e20251c461f0459ce315122d5987666c3"),
    ("init-F4-san-AL", "checkpoints/p05/evidence/p05-s3r5/build/init-F4-san-AL", "f14c536ea54d81348dd4f53f36c5c2eba65c0ca15fdb16160b8296186d7f5f8e"),
    ("init-B-dbg", "checkpoints/p05/evidence/p05-s4r8/m2c/build/init-B-dbg", "3ccc2897fae2ce293d3c656e2a334dad05e53fe7f622b749a71e19bfd021b0b8"),
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

def write_baseline(entries, baseline_tsv):
    os.makedirs(os.path.dirname(baseline_tsv), exist_ok=True)
    with open(baseline_tsv, "x", encoding="utf-8") as fh:
        fh.write("# STRAY_BASELINE_R9M2b (start): path\tkind\tbytes\tmtime_ns\tsha256\n")
        for k in sorted(entries):
            kind, size, mt, sh = entries[k]
            fh.write("%s\t%s\t%d\t%d\t%s\n" % (k, kind, size, mt, sh))

def read_baseline(baseline_tsv):
    out = {}
    with open(baseline_tsv, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            k, kind, size, mt, sh = line.rstrip("\n").split("\t")
            out[k] = (kind, int(size), int(mt), sh)
    return out

def run_checks(mode, start_file=None, ev_dir=None):
    if not ev_dir:
        ev_dir = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b"))
    baseline_tsv = os.path.join(ev_dir, "STRAY_BASELINE_R9M2b.tsv")

    results = []
    fails = 0

    def check(name, cond, exp, act):
        nonlocal fails
        st = "PASS" if cond else "FAIL"
        if not cond:
            fails += 1
        results.append((st, name, str(exp), str(act)))

    # 1. Base commit / HEAD
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    if mode == "start":
        check("HEAD_IS_BASE", head == EXPECTED_BASE, EXPECTED_BASE, head)
    else:
        check("HEAD_NOT_EMPTY", bool(head), "valid_sha", head)

    # 2. S4 tree checks
    head_s4 = subprocess.check_output(["git", "rev-parse", "HEAD:S4"], cwd=REPO, text=True).strip()
    check("HEAD_S4_TREE_EQ_F4", head_s4 == EXPECTED_S4_TREE_F4, EXPECTED_S4_TREE_F4, head_s4)

    f3_s4 = subprocess.check_output(["git", "rev-parse", "8d8202a:S4"], cwd=REPO, text=True).strip()
    check("F3_8d8202a_S4_TREE", f3_s4 == EXPECTED_S4_TREE_F3, EXPECTED_S4_TREE_F3, f3_s4)
    f2_s4 = subprocess.check_output(["git", "rev-parse", "a07b5ac:S4"], cwd=REPO, text=True).strip()
    check("F2_a07b5ac_S4_TREE", f2_s4 == EXPECTED_F2_TREE, EXPECTED_F2_TREE, f2_s4)
    b_s4 = subprocess.check_output(["git", "rev-parse", "37a82e8:S4"], cwd=REPO, text=True).strip()
    check("B_37a82e8_S4_TREE", b_s4 == EXPECTED_B_TREE, EXPECTED_B_TREE, b_s4)

    # 3. Judge sha256
    judge_path = os.path.join(REPO, "testing", "d003", "judge_d003.py")
    judge_sha = sha256_file(judge_path) if os.path.isfile(judge_path) else "missing"
    check("JUDGE_SHA256", judge_sha == EXPECTED_JUDGE_SHA, EXPECTED_JUDGE_SHA, judge_sha)

    # 4. s3r5 artifacts
    for art_name, art_rel, art_exp_sha in S3R5_ARTIFACTS:
        p = os.path.join(REPO, art_rel)
        act_sha = sha256_file(p) if os.path.isfile(p) else "missing"
        check("ARTIFACT_" + art_name, act_sha == art_exp_sha, art_exp_sha, act_sha)

    # 5. s3r5 SHA256SUMS.txt
    ok_s3r5, detail_s3r5 = verify_sums_dir(os.path.join(REPO, S3R5_DIR), 14)
    check("S3R5_SUMS_14_ALL_OK", ok_s3r5, "all 14 OK", detail_s3r5)

    # 6. M0 and M2 SHA256SUMS.txt
    ok_m0, detail_m0 = verify_sums_dir(os.path.join(REPO, M0_DIR), 25)
    check("M0_SUMS_25_ALL_OK", ok_m0, "all 25 OK", detail_m0)

    ok_m2, detail_m2 = verify_sums_dir(os.path.join(REPO, M2_DIR), 14)
    check("M2_SUMS_14_ALL_OK", ok_m2, "all 14 OK", detail_m2)

    # 7. start-only: STATE.md size and sha256
    state_path = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
    state_b = open(state_path, "rb").read() if os.path.isfile(state_path) else b""
    if mode == "start":
        check("STATE_START_BYTES", len(state_b) == EXPECTED_STATE_BYTES, EXPECTED_STATE_BYTES, len(state_b))
        check("STATE_START_SHA256", hashlib.sha256(state_b).hexdigest() == EXPECTED_STATE_SHA, EXPECTED_STATE_SHA, hashlib.sha256(state_b).hexdigest())

    # 8. RULINGS & ERRATA prefix checks
    rulings_path = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")
    errata_s3r5_path = os.path.join(REPO, "checkpoints", "p05", "ERRATA_S3R5.txt")
    errata_9_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "ERRATA_9.txt")

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

    err_base = subprocess.check_output(["git", "show", EXPECTED_BASE + ":checkpoints/p05/ERRATA_S3R5.txt"], cwd=REPO)
    err_now = open(errata_s3r5_path, "rb").read() if os.path.isfile(errata_s3r5_path) else b""
    check("ERRATA_S3R5_BASE_PREFIX_UNCHANGED", err_now.startswith(err_base), True, err_now.startswith(err_base))

    err9_base = subprocess.check_output(["git", "show", EXPECTED_BASE + ":checkpoints/p05/registries/s4r9/ERRATA_9.txt"], cwd=REPO)
    err9_now = open(errata_9_path, "rb").read() if os.path.isfile(errata_9_path) else b""
    check("ERRATA_9_BASE_PREFIX_UNCHANGED", err9_now.startswith(err9_base), True, err9_now.startswith(err9_base))

    if mode == "start":
        check("RULINGS_START_BYTES", len(rul_now) == EXPECTED_RULINGS_BYTES, EXPECTED_RULINGS_BYTES, len(rul_now))
        check("RULINGS_START_SHA256", hashlib.sha256(rul_now).hexdigest() == EXPECTED_RULINGS_SHA, EXPECTED_RULINGS_SHA, hashlib.sha256(rul_now).hexdigest())
        check("ERRATA_S3R5_START_BYTES", len(err_now) == EXPECTED_ERRATA_S3R5_BYTES, EXPECTED_ERRATA_S3R5_BYTES, len(err_now))
        check("ERRATA_S3R5_START_SHA256", hashlib.sha256(err_now).hexdigest() == EXPECTED_ERRATA_S3R5_SHA, EXPECTED_ERRATA_S3R5_SHA, hashlib.sha256(err_now).hexdigest())
        check("ERRATA_9_START_BYTES", len(err9_now) == EXPECTED_ERRATA_9_BYTES, EXPECTED_ERRATA_9_BYTES, len(err9_now))
        check("ERRATA_9_START_SHA256", hashlib.sha256(err9_now).hexdigest() == EXPECTED_ERRATA_9_SHA, EXPECTED_ERRATA_9_SHA, hashlib.sha256(err9_now).hexdigest())

    start_records = parse_start_records(start_file)
    if mode == "end":
        check("START_RECORDS_PRESENT", bool(start_records), True, bool(start_records))
        start_rul_sha = start_records.get("RULINGS_SHA256")
        start_rul_bytes = int(start_records.get("RULINGS_BYTES", "0"))
        start_err_sha = start_records.get("ERRATA_S3R5_SHA256")
        start_err_bytes = int(start_records.get("ERRATA_S3R5_BYTES", "0"))
        start_err9_sha = start_records.get("ERRATA_9_SHA256")
        start_err9_bytes = int(start_records.get("ERRATA_9_BYTES", "0"))

        if start_rul_bytes > 0:
            rul_pfx_sha = hashlib.sha256(rul_now[:start_rul_bytes]).hexdigest()
            check("RULINGS_PREFIX_OF_START_UNCHANGED", rul_pfx_sha == start_rul_sha, start_rul_sha, rul_pfx_sha)
            check("RULINGS_NOT_TRUNCATED", len(rul_now) >= start_rul_bytes, True, len(rul_now) >= start_rul_bytes)
        if start_err_bytes > 0:
            err_pfx_sha = hashlib.sha256(err_now[:start_err_bytes]).hexdigest()
            check("ERRATA_S3R5_PREFIX_OF_START_UNCHANGED", err_pfx_sha == start_err_sha, start_err_sha, err_pfx_sha)
            check("ERRATA_S3R5_NOT_TRUNCATED", len(err_now) >= start_err_bytes, True, len(err_now) >= start_err_bytes)
        if start_err9_bytes > 0:
            err9_pfx_sha = hashlib.sha256(err9_now[:start_err9_bytes]).hexdigest()
            check("ERRATA_9_PREFIX_OF_START_UNCHANGED", err9_pfx_sha == start_err9_sha, start_err9_sha, err9_pfx_sha)
            check("ERRATA_9_NOT_TRUNCATED", len(err9_now) >= start_err9_bytes, True, len(err9_now) >= start_err9_bytes)

        ok_s3r5_end, det_s3r5_end = verify_sums_dir(os.path.join(REPO, S3R5_DIR), 14)
        check("S3R5_ORIGINAL_14_SHA_UNCHANGED_END", ok_s3r5_end, "all 14 OK", det_s3r5_end)
        ok_m0_end, det_m0_end = verify_sums_dir(os.path.join(REPO, M0_DIR), 25)
        check("M0_ORIGINAL_25_SHA_UNCHANGED_END", ok_m0_end, "all 25 OK", det_m0_end)
        ok_m2_end, det_m2_end = verify_sums_dir(os.path.join(REPO, M2_DIR), 14)
        check("M2_ORIGINAL_14_SHA_UNCHANGED_END", ok_m2_end, "all 14 OK", det_m2_end)

    # 9. Baseline stray build products
    if mode == "start":
        entries = scan_build_products()
        if os.path.exists(baseline_tsv):
            check("STRAY_BASELINE_NOT_PRESENT_BEFORE_START", False, "absent", "present")
        else:
            write_baseline(entries, baseline_tsv)
        for kp in KNOWN_PYC:
            check("STRAY_BASELINE_HAS_" + os.path.basename(kp), kp in entries, "present", "present" if kp in entries else "absent")
        check("STRAY_BASELINE_COUNT_RECORDED", True, "recorded", len(entries))
    if mode == "end":
        base = read_baseline(baseline_tsv) if os.path.isfile(baseline_tsv) else {}
        now = scan_build_products()
        new_items = sorted(k for k in now if k not in base)
        changed_items = sorted(k for k in now if k in base and now[k] != base[k])
        removed_items = sorted(k for k in base if k not in now)
        check("STRAY_NEW_OR_CHANGED_NONE", (not new_items and not changed_items), "none", "new=%s changed=%s" % (new_items, changed_items))
        check("STRAY_BASELINE_REMOVED_NONE_INFO", True, "info", "removed=%s" % (removed_items,))

    # 10. Historical runners and judges
    for rel in HIST_RUNNERS:
        head_blob = subprocess.check_output(["git", "rev-parse", "HEAD:" + rel], cwd=REPO, text=True).strip()
        d58_blob = subprocess.check_output(["git", "rev-parse", "d58bafd:" + rel], cwd=REPO, text=True).strip()
        wt = subprocess.check_output(["git", "hash-object", os.path.join(REPO, rel)], cwd=REPO, text=True).strip()
        check("HIST_UNCHANGED_SINCE_D58BAFD " + os.path.basename(rel), head_blob == d58_blob == wt, head_blob, "%s|%s|%s" % (head_blob, d58_blob, wt))

    # 11. STATE <= 8192 UTF-8 bytes
    state_bytes = len(open(state_path, "rb").read()) if os.path.isfile(state_path) else 999999
    check("STATE_BYTES_LE_8192", state_bytes <= 8192, "<= 8192", state_bytes)

    # 12. No tracked files under testing/d003 modified or deleted since base
    diff_d003 = subprocess.check_output(["git", "diff", "--name-only", "--diff-filter=MD", EXPECTED_BASE, "--", "testing/d003"], cwd=REPO, text=True).strip()
    check("TRACKED_TESTING_D003_NO_MOD_DEL", diff_d003 == "", "no modified or deleted", diff_d003 if diff_d003 else "unmodified")

    return fails, results

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "start"
    start_file = sys.argv[2] if len(sys.argv) > 2 else None
    ev_dir = sys.argv[3] if len(sys.argv) > 3 else None
    fails, results = run_checks(mode, start_file, ev_dir)
    for st, name, exp, act in results:
        print("%s\t%s\texpected=%s\tactual=%s" % (st, name, exp, act))
