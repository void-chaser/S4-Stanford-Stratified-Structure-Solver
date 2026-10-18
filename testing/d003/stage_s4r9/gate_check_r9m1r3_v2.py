#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate_check_r9m1r3.py -- P05-S4 R9 M1R2 gate helper. New file.
# Baseline HEAD: 16a789791f792f8814dc8896e03fb1b3f75c6294
import hashlib, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

EXPECTED_BASE = "56b1e43fa4b4b88437d2c49543ee764f39d3ee28"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECTED_S4_TREE_F4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXPECTED_S4_TREE_F3 = "6cff923a02baf19e01966b2339755cbf3a5deeef"
EXPECTED_F2_TREE = "e124925f5b242486a913b813fa181664f665b048"
EXPECTED_B_TREE = "1d738e64f9864a475fdb3de34cd3601605df2c64"

EXPECTED_STATE_BYTES = 8056
EXPECTED_STATE_SHA = "27ae5a33dbf4ebeecde0f92dbf4f989b56f772220d390e3ea9888f24b799651d"
EXPECTED_RULINGS_BYTES = 130798
EXPECTED_RULINGS_SHA = "84d3871c2dabdc609c365b09ae58a4b7fb40a10a8ec450af77ede20ec64b5729"

EXPECTED_ERRATA_S3R5_BYTES = 1712
EXPECTED_ERRATA_S3R5_SHA = "a23ff03cd260548ae74205ca27c94d47a8a677d9c47bacfc5be6f5dec3077349"
EXPECTED_ERRATA_9_BYTES = 19322
EXPECTED_ERRATA_9_SHA = "0e416f01a52f652a80dd4b34abea9ea7264459dece0297149025a94253a0a745"

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
M2B_DIR = os.path.join("checkpoints", "p05", "registries", "s4r9", "M2b")
M2C_DIR = os.path.join("checkpoints", "p05", "registries", "s4r9", "M2c")
M1_DIR = os.path.join("checkpoints", "p05", "registries", "s4r9", "M1")
M1R2_DIR = os.path.join("checkpoints", "p05", "registries", "s4r9", "M1R2")

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
    res = {}
    search_root = os.path.join(REPO, "testing", "d003")
    for root, dirs, files in os.walk(search_root):
        for f in files:
            if f.endswith(".pyc") or f.endswith(".o"):
                full = os.path.join(root, f)
                rel = os.path.relpath(full, REPO)
                st = os.stat(full)
                h = sha256_file(full)
                res[rel] = ("file", st.st_size, int(st.st_mtime), h)
    return res

def write_baseline(entries, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("# STRAY_BASELINE_R9M1R2.tsv -- Baseline stray build products in testing/d003\n")
        fh.write("relpath\tkind\tsize\tmtime\tsha256\n")
        for k in sorted(entries.keys()):
            kind, size, mt, sh = entries[k]
            fh.write("%s\t%s\t%d\t%d\t%s\n" % (k, kind, size, mt, sh))

def read_baseline(path):
    out = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith("relpath\t"):
                continue
            k, kind, size, mt, sh = line.rstrip("\n").split("\t")
            out[k] = (kind, int(size), int(mt), sh)
    return out

def run_checks(mode, start_file=None, ev_dir=None):
    if not ev_dir:
        ev_dir = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))
    baseline_tsv = os.path.join(ev_dir, "STRAY_BASELINE_R9M1R2.tsv")

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

    # 5. SHA256SUMS checks: s3r5, M0, M2, M2b, M2c, M1
    ok_s3r5, detail_s3r5 = verify_sums_dir(os.path.join(REPO, S3R5_DIR), 14)
    check("S3R5_SUMS_14_ALL_OK", ok_s3r5, "all 14 OK", detail_s3r5)

    ok_m0, detail_m0 = verify_sums_dir(os.path.join(REPO, M0_DIR), 25)
    check("M0_SUMS_25_ALL_OK", ok_m0, "all 25 OK", detail_m0)

    ok_m2, detail_m2 = verify_sums_dir(os.path.join(REPO, M2_DIR), 14)
    check("M2_SUMS_14_ALL_OK", ok_m2, "all 14 OK", detail_m2)

    ok_m2b, detail_m2b = verify_sums_dir(os.path.join(REPO, M2B_DIR), 13)
    check("M2B_SUMS_13_ALL_OK", ok_m2b, "all 13 OK", detail_m2b)

    ok_m2c, detail_m2c = verify_sums_dir(os.path.join(REPO, M2C_DIR), 11)
    check("M2C_SUMS_11_ALL_OK", ok_m2c, "all 11 OK", detail_m2c)

    ok_m1, detail_m1 = verify_sums_dir(os.path.join(REPO, M1_DIR), 28)
    check("M1_SUMS_28_ALL_OK", ok_m1, "all 28 OK", detail_m1)

    ok_m1r2, detail_m1r2 = verify_sums_dir(os.path.join(REPO, M1R2_DIR), 33)
    check("M1R2_SUMS_33_ALL_OK", ok_m1r2, "all 33 OK", detail_m1r2)

    # 6. STATE.md size and sha256 at start
    state_path = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
    state_b = open(state_path, "rb").read() if os.path.isfile(state_path) else b""
    if mode == "start":
        check("STATE_START_BYTES", len(state_b) == EXPECTED_STATE_BYTES, EXPECTED_STATE_BYTES, len(state_b))
        check("STATE_START_SHA256", hashlib.sha256(state_b).hexdigest() == EXPECTED_STATE_SHA, EXPECTED_STATE_SHA, hashlib.sha256(state_b).hexdigest())

    # 7. RULINGS & ERRATA prefix checks
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
        ok_m2b_end, det_m2b_end = verify_sums_dir(os.path.join(REPO, M2B_DIR), 13)
        check("M2B_ORIGINAL_13_SHA_UNCHANGED_END", ok_m2b_end, "all 13 OK", det_m2b_end)
        ok_m2c_end, det_m2c_end = verify_sums_dir(os.path.join(REPO, M2C_DIR), 11)
        check("M2C_ORIGINAL_11_SHA_UNCHANGED_END", ok_m2c_end, "all 11 OK", det_m2c_end)
        ok_m1_end, det_m1_end = verify_sums_dir(os.path.join(REPO, M1_DIR), 28)
        check("M1_ORIGINAL_28_SHA_UNCHANGED_END", ok_m1_end, "all 28 OK", det_m1_end)

        # End gate check: checkpoints/p05/registries/s4r9/M1/ all files identical to 56b1e43
        diff_m1 = subprocess.check_output(["git", "diff", EXPECTED_BASE, "--", "checkpoints/p05/registries/s4r9/M1"], cwd=REPO, text=True).strip()
        check("M1_REGISTRIES_ALL_IDENTICAL_TO_BASE", diff_m1 == "", "no diff against base", "diff: %s" % diff_m1 if diff_m1 else "identical")

        diff_m1r2 = subprocess.check_output(["git", "diff", EXPECTED_BASE, "--", "checkpoints/p05/registries/s4r9/M1R2"], cwd=REPO, text=True).strip()
        check("M1R2_REGISTRIES_ALL_IDENTICAL_TO_BASE", diff_m1r2 == "", "no diff against base", "diff: %s" % diff_m1r2 if diff_m1r2 else "identical")

        # End gate check: §1-10 frozen files sha assertion
        frozen_tsv_path = os.path.join(ev_dir, "FROZEN_SCRIPTS_R9M1R2.tsv")
        if not os.path.isfile(frozen_tsv_path):
            frozen_tsv_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R2", "FROZEN_SCRIPTS_R9M1R2.tsv")
        if os.path.isfile(frozen_tsv_path):
            frozen_ok = True
            frozen_details = []
            with open(frozen_tsv_path, encoding="utf-8") as ffh:
                for fline in ffh:
                    fline = fline.strip()
                    if not fline or fline.startswith("#") or fline.startswith("path\t"):
                        continue
                    parts = fline.split("\t")
                    if len(parts) >= 2:
                        f_rel, f_sha = parts[0], parts[1]
                        full_fp = os.path.join(REPO, f_rel) if not os.path.isabs(f_rel) else f_rel
                        if not os.path.isfile(full_fp):
                            frozen_ok = False
                            frozen_details.append("missing: " + f_rel)
                        else:
                            curr_sha = sha256_file(full_fp)
                            if curr_sha != f_sha:
                                frozen_ok = False
                                frozen_details.append("sha mismatch: %s (%s != %s)" % (f_rel, curr_sha, f_sha))
            check("FROZEN_SCRIPTS_SHA_UNCHANGED_END", frozen_ok, True, "; ".join(frozen_details) if frozen_details else "all frozen OK")
        else:
            check("FROZEN_SCRIPTS_TSV_EXISTS", False, "present", "missing")

        # End gate check: allow files have NO " M " wildcard items
        allow_end_path = os.path.join(REPO, "testing", "d003", "stage_s4r9", "gate_allow_r9m1r3_end.txt")
        has_m_wildcard = False
        bad_m_lines = []
        if os.path.isfile(allow_end_path):
            with open(allow_end_path, encoding="utf-8") as afh:
                for aline in afh:
                    aline = aline.strip()
                    if aline.startswith("M ") or aline.startswith(" M "):
                        if "*" in aline:
                            has_m_wildcard = True
                            bad_m_lines.append(aline)
        check("ALLOW_END_NO_M_WILDCARD", not has_m_wildcard, True, "bad: " + str(bad_m_lines) if has_m_wildcard else "clean")

        # End gate check: Commit (i) and safe_run.log calls in frozen period
        import re, datetime
        commit_i = subprocess.check_output(["git", "log", "--grep=R9 M1R3 (i)", "-1", "--format=%H"], cwd=REPO, text=True).strip()
        check("COMMIT_I_PRESENT", bool(commit_i), "commit (i) found", commit_i if commit_i else "missing")

        if commit_i:
            commit_i_epoch = int(subprocess.check_output(["git", "log", "-1", "--format=%ct", commit_i], cwd=REPO, text=True).strip())
            log_path = os.path.join(ev_dir, "safe_run.log")
            log_entries = []
            if os.path.isfile(log_path):
                with open(log_path, "r", encoding="utf-8") as lf:
                    for line_idx, line in enumerate(lf, 1):
                        line = line.strip()
                        if not line:
                            continue
                        parts = line.split("\t")
                        if len(parts) >= 4:
                            ts_str = parts[0]
                            cmd_str = parts[3]
                            try:
                                dt = datetime.datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
                                epoch = int(dt.timestamp())
                            except Exception:
                                epoch = 0
                            log_entries.append((line_idx, ts_str, epoch, cmd_str))

            post_i_entries = [e for e in log_entries if e[2] >= commit_i_epoch]

            target_scripts = {
                "posctrl": "posctrl_r9m1r3.py",
                "smoke": "run_smoke_r9m1r3.py",
                "formal": "run_formal_r9m1r3.py",
                "verdict": "verdict_r9m1r3.py",
                "compare": "compare_f3_f4_r9m1r3.py",
            }
            call_counts = {k: 0 for k in target_scripts}
            testing_d003_writes = []
            unfrozen_stage_calls = []

            for l_idx, l_ts, l_epoch, l_cmd in post_i_entries:
                for key, s_name in target_scripts.items():
                    if re.search(r"\b" + re.escape(s_name) + r"\b", l_cmd):
                        if not any(prefix in l_cmd for prefix in ("diff ", "git diff", "grep ", "cat ")):
                            call_counts[key] += 1

                if "open('testing/d003/" in l_cmd or 'open("testing/d003/' in l_cmd:
                    testing_d003_writes.append((l_idx, l_cmd))
                if re.search(r">\s*testing/d003/", l_cmd):
                    testing_d003_writes.append((l_idx, l_cmd))

                stage_matches = re.findall(r"(?:testing/d003/stage_s4r9/[A-Za-z0-9_.-]+)", l_cmd)
                for sm in stage_matches:
                    if sm.endswith(".py") or sm.endswith(".sh"):
                        if sm not in frozen_map:
                            unfrozen_stage_calls.append((l_idx, sm))

            for key in ["posctrl", "smoke", "formal", "verdict", "compare"]:
                check("POST_I_CALL_COUNT_" + key.upper() + "_EQ_1", call_counts[key] == 1, 1, call_counts[key])

            check("POST_I_NO_TESTING_D003_WRITES", len(testing_d003_writes) == 0, 0, len(testing_d003_writes))
            check("POST_I_STAGE_SCRIPTS_ALL_FROZEN", len(unfrozen_stage_calls) == 0, "all frozen", str(unfrozen_stage_calls) if unfrozen_stage_calls else "all frozen")

        # End gate check: events covers all safe_run lines before gate
        events_tsv_path = os.path.join(ev_dir, "EVENTS_R9M1R3.tsv")
        if not os.path.isfile(events_tsv_path):
            events_tsv_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R3", "EVENTS_R9M1R3.tsv")
        if os.path.isfile(events_tsv_path):
            with open(events_tsv_path, encoding="utf-8") as ef:
                events_lines = [l for l in ef if l.strip() and not l.startswith("#") and not l.startswith("log_line\t")]
            log_path = os.path.join(ev_dir, "safe_run.log")
            safe_log_count = len(open(log_path, encoding="utf-8").read().splitlines()) if os.path.isfile(log_path) else 0
            check("EVENTS_COVERS_ALL_LOGS_BEFORE_GATE", len(events_lines) == safe_log_count - 1, safe_log_count - 1, len(events_lines))
        else:
            check("EVENTS_TSV_EXISTS", False, "present", "missing")

        # End gate check: evidence SHA256SUMS.txt
        ev_sums_path = os.path.join(ev_dir, "SHA256SUMS.txt")
        if os.path.isfile(ev_sums_path):
            sums_proc = subprocess.run(["sha256sum", "-c", "SHA256SUMS.txt"], cwd=ev_dir, capture_output=True, text=True)
            check("EVIDENCE_SHA256SUMS_ALL_OK", sums_proc.returncode == 0, 0, sums_proc.returncode)
        else:
            check("EVIDENCE_SHA256SUMS_EXISTS", False, "present", "missing")


    # 8. Baseline stray build products
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

    # 9. Historical runners and judges
    for rel in HIST_RUNNERS:
        head_blob = subprocess.check_output(["git", "rev-parse", "HEAD:" + rel], cwd=REPO, text=True).strip()
        d58_blob = subprocess.check_output(["git", "rev-parse", "d58bafd:" + rel], cwd=REPO, text=True).strip()
        wt = subprocess.check_output(["git", "hash-object", os.path.join(REPO, rel)], cwd=REPO, text=True).strip()
        check("HIST_UNCHANGED_SINCE_D58BAFD " + os.path.basename(rel), head_blob == d58_blob == wt, head_blob, "%s|%s|%s" % (head_blob, d58_blob, wt))

    # 10. STATE <= 8192 UTF-8 bytes
    state_bytes = len(open(state_path, "rb").read()) if os.path.isfile(state_path) else 999999
    check("STATE_BYTES_LE_8192", state_bytes <= 8192, "<= 8192", state_bytes)

    # 11. No tracked files under testing/d003 modified or deleted since base
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
    sys.exit(fails)
