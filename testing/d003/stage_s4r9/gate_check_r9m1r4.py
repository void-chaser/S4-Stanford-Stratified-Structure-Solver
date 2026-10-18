#!/usr/bin/env python3
# gate_check_r9m1r4.py -- P05-S4 R9 M1R4 gate helper. New file.
# Baseline HEAD: 4e9ff8be523bbf52a6b11757a6e04405a4a114e9
import hashlib, os, subprocess, sys, re, datetime

# ==================== CONSTANTS ====================
ROUND_TAG = "r9m1r4"
ROUND_NAME = "M1R4"
EXPECTED_BASE = "4e9ff8be523bbf52a6b11757a6e04405a4a114e9"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECTED_S4_TREE_F4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXPECTED_S4_TREE_F3 = "6cff923a02baf19e01966b2339755cbf3a5deeef"
EXPECTED_F2_TREE = "e124925f5b242486a913b813fa181664f665b048"
EXPECTED_B_TREE = "1d738e64f9864a475fdb3de34cd3601605df2c64"

EXPECTED_STATE_BYTES = 8050
EXPECTED_STATE_SHA = "0b559cf93e69edc385589c3fa982013e31076cd9fc34676ba2700bb964cd817a"
EXPECTED_RULINGS_BYTES = 133250
EXPECTED_RULINGS_SHA = "78350022fe02dd03a92487f1575edcbed0a84d49feefeb543e1a04baba69a33c"
EXPECTED_ERRATA_S3R5_BYTES = 1712
EXPECTED_ERRATA_S3R5_SHA = "a23ff03cd260548ae74205ca27c94d47a8a677d9c47bacfc5be6f5dec3077349"
EXPECTED_ERRATA_9_BYTES = 25685
EXPECTED_ERRATA_9_SHA = "a2c70924eb6cf5a3dc7c3623771d8c8a33e2920dfaa8799920be016b850b15ef"
EXPECTED_M1R3_SUMS_SHA = "c25e998ad56fceb85128a83b7836071a7804c4181865b744f52d4f4001e43b45"

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

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
M1R3_DIR = os.path.join("checkpoints", "p05", "registries", "s4r9", "M1R3")

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
            if not chunk: break
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
        fh.write("# STRAY_BASELINE_R9M1R4.tsv -- Baseline stray build products in testing/d003\n")
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
        ev_dir = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r4"))
    baseline_tsv = os.path.join(ev_dir, "STRAY_BASELINE_R9M1R4.tsv")

    results = []
    fails = 0

    def check(name, cond, exp, act):
        nonlocal fails
        st = "PASS" if cond else "FAIL"
        if not cond:
            fails += 1
        results.append((st, name, str(exp), str(act)))

    def safe_check(name, check_fn, exp_val):
        nonlocal fails
        try:
            cond, act_val = check_fn()
            check(name, cond, exp_val, act_val)
        except Exception as exc:
            check(name, False, exp_val, f"CHECK_CRASHED: {type(exc).__name__}: {exc}")

    # 0. Self-check: constants clean and do not contain old round names (m1r2, m1r3)
    def check_clean_constants():
        forbidden = ["m1r2", "m1r3"]
        for w in forbidden:
            if w in ROUND_TAG.lower() or w in ROUND_NAME.lower():
                return False, f"found {w} in round constants"
        return True, "clean"
    safe_check("CONSTANTS_CLEAN_NO_OLD_ROUNDS", check_clean_constants, "clean")

    # 1. Base commit / HEAD
    def check_head():
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
        if mode == "start":
            return head == EXPECTED_BASE, head
        else:
            return bool(head), head
    safe_check("HEAD_IS_BASE" if mode == "start" else "HEAD_NOT_EMPTY", check_head, EXPECTED_BASE if mode == "start" else "valid_sha")

    # 2. S4 tree checks
    def check_s4_tree():
        head_s4 = subprocess.check_output(["git", "rev-parse", "HEAD:S4"], cwd=REPO, text=True).strip()
        return head_s4 == EXPECTED_S4_TREE_F4, head_s4
    safe_check("HEAD_S4_TREE_EQ_F4", check_s4_tree, EXPECTED_S4_TREE_F4)

    def check_f3_tree():
        f3_s4 = subprocess.check_output(["git", "rev-parse", "8d8202a:S4"], cwd=REPO, text=True).strip()
        return f3_s4 == EXPECTED_S4_TREE_F3, f3_s4
    safe_check("F3_8d8202a_S4_TREE", check_f3_tree, EXPECTED_S4_TREE_F3)

    def check_f2_tree():
        f2_s4 = subprocess.check_output(["git", "rev-parse", "a07b5ac:S4"], cwd=REPO, text=True).strip()
        return f2_s4 == EXPECTED_F2_TREE, f2_s4
    safe_check("F2_a07b5ac_S4_TREE", check_f2_tree, EXPECTED_F2_TREE)

    def check_b_tree():
        b_s4 = subprocess.check_output(["git", "rev-parse", "37a82e8:S4"], cwd=REPO, text=True).strip()
        return b_s4 == EXPECTED_B_TREE, b_s4
    safe_check("B_37a82e8_S4_TREE", check_b_tree, EXPECTED_B_TREE)

    # 3. Judge sha256
    def check_judge():
        judge_path = os.path.join(REPO, "testing", "d003", "judge_d003.py")
        act_sha = sha256_file(judge_path) if os.path.isfile(judge_path) else "missing"
        return act_sha == EXPECTED_JUDGE_SHA, act_sha
    safe_check("JUDGE_SHA256", check_judge, EXPECTED_JUDGE_SHA)

    # 4. s3r5 artifacts
    for art_name, art_rel, art_exp_sha in S3R5_ARTIFACTS:
        def make_check_art(rel=art_rel, exp=art_exp_sha):
            def chk():
                p = os.path.join(REPO, rel)
                act = sha256_file(p) if os.path.isfile(p) else "missing"
                return act == exp, act
            return chk
        safe_check("ARTIFACT_" + art_name, make_check_art(), art_exp_sha)

    # 5. SHA256SUMS checks: s3r5, M0, M2, M2b, M2c, M1, M1R2, M1R3
    def check_s3r5_sums():
        ok, detail = verify_sums_dir(os.path.join(REPO, S3R5_DIR), 14)
        return ok, detail
    safe_check("S3R5_SUMS_14_ALL_OK", check_s3r5_sums, "all 14 OK")

    def check_m0_sums():
        ok, detail = verify_sums_dir(os.path.join(REPO, M0_DIR), 25)
        return ok, detail
    safe_check("M0_SUMS_25_ALL_OK", check_m0_sums, "all 25 OK")

    def check_m2_sums():
        ok, detail = verify_sums_dir(os.path.join(REPO, M2_DIR), 14)
        return ok, detail
    safe_check("M2_SUMS_14_ALL_OK", check_m2_sums, "all 14 OK")

    def check_m2b_sums():
        ok, detail = verify_sums_dir(os.path.join(REPO, M2B_DIR), 13)
        return ok, detail
    safe_check("M2B_SUMS_13_ALL_OK", check_m2b_sums, "all 13 OK")

    def check_m2c_sums():
        ok, detail = verify_sums_dir(os.path.join(REPO, M2C_DIR), 11)
        return ok, detail
    safe_check("M2C_SUMS_11_ALL_OK", check_m2c_sums, "all 11 OK")

    def check_m1_sums():
        ok, detail = verify_sums_dir(os.path.join(REPO, M1_DIR), 28)
        return ok, detail
    safe_check("M1_SUMS_28_ALL_OK", check_m1_sums, "all 28 OK")

    def check_m1r2_sums():
        ok, detail = verify_sums_dir(os.path.join(REPO, M1R2_DIR), 34)
        return ok, detail
    safe_check("M1R2_SUMS_34_ALL_OK", check_m1r2_sums, "all 34 OK")

    def check_m1r3_sums():
        sums_f = os.path.join(REPO, M1R3_DIR, "SHA256SUMS.txt")
        if not os.path.isfile(sums_f):
            return False, "missing SHA256SUMS.txt"
        actual_sha = sha256_file(sums_f)
        if actual_sha != EXPECTED_M1R3_SUMS_SHA:
            return False, f"sums sha mismatch: {actual_sha} != {EXPECTED_M1R3_SUMS_SHA}"
        ok, detail = verify_sums_dir(os.path.join(REPO, M1R3_DIR), 26)
        return ok, detail
    safe_check("M1R3_SUMS_26_ALL_OK", check_m1r3_sums, "all 26 OK")

    # 6. STATE.md size and sha256 at start
    state_path = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
    state_b = open(state_path, "rb").read() if os.path.isfile(state_path) else b""
    if mode == "start":
        def check_state_bytes(): return len(state_b) == EXPECTED_STATE_BYTES, len(state_b)
        safe_check("STATE_START_BYTES", check_state_bytes, EXPECTED_STATE_BYTES)
        def check_state_sha(): act = hashlib.sha256(state_b).hexdigest(); return act == EXPECTED_STATE_SHA, act
        safe_check("STATE_START_SHA256", check_state_sha, EXPECTED_STATE_SHA)

    # 7. RULINGS & ERRATA prefix checks
    rulings_path = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")
    errata_s3r5_path = os.path.join(REPO, "checkpoints", "p05", "ERRATA_S3R5.txt")
    errata_9_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "ERRATA_9.txt")

    rul_base = subprocess.check_output(["git", "show", EXPECTED_BASE + ":checkpoints/p05/registries/RULINGS.tsv"], cwd=REPO)
    rul_now = open(rulings_path, "rb").read() if os.path.isfile(rulings_path) else b""
    def check_rul_pfx(): return rul_now.startswith(rul_base), "prefix matched" if rul_now.startswith(rul_base) else "diverged"
    safe_check("RULINGS_BASE_PREFIX_UNCHANGED", check_rul_pfx, "prefix matched")

    def check_rul_fields():
        for l in rul_now.decode("utf-8").splitlines():
            l = l.strip()
            if not l or l.startswith("#"): continue
            if len(l.split("\t")) != 5:
                return False, f"bad line: {l[:50]}"
        return True, "all 5 fields"
    safe_check("RULINGS_LINES_5_FIELDS", check_rul_fields, "all 5 fields")

    err_base = subprocess.check_output(["git", "show", EXPECTED_BASE + ":checkpoints/p05/ERRATA_S3R5.txt"], cwd=REPO)
    err_now = open(errata_s3r5_path, "rb").read() if os.path.isfile(errata_s3r5_path) else b""
    def check_err_pfx(): return err_now.startswith(err_base), "prefix matched" if err_now.startswith(err_base) else "diverged"
    safe_check("ERRATA_S3R5_BASE_PREFIX_UNCHANGED", check_err_pfx, "prefix matched")

    err9_base = subprocess.check_output(["git", "show", EXPECTED_BASE + ":checkpoints/p05/registries/s4r9/ERRATA_9.txt"], cwd=REPO)
    err9_now = open(errata_9_path, "rb").read() if os.path.isfile(errata_9_path) else b""
    def check_err9_pfx(): return err9_now.startswith(err9_base), "prefix matched" if err9_now.startswith(err9_base) else "diverged"
    safe_check("ERRATA_9_BASE_PREFIX_UNCHANGED", check_err9_pfx, "prefix matched")

    if mode == "start":
        def check_rul_start_bytes(): return len(rul_now) == EXPECTED_RULINGS_BYTES, len(rul_now)
        safe_check("RULINGS_START_BYTES", check_rul_start_bytes, EXPECTED_RULINGS_BYTES)
        def check_rul_start_sha(): act = hashlib.sha256(rul_now).hexdigest(); return act == EXPECTED_RULINGS_SHA, act
        safe_check("RULINGS_START_SHA256", check_rul_start_sha, EXPECTED_RULINGS_SHA)
        def check_err_start_bytes(): return len(err_now) == EXPECTED_ERRATA_S3R5_BYTES, len(err_now)
        safe_check("ERRATA_S3R5_START_BYTES", check_err_start_bytes, EXPECTED_ERRATA_S3R5_BYTES)
        def check_err_start_sha(): act = hashlib.sha256(err_now).hexdigest(); return act == EXPECTED_ERRATA_S3R5_SHA, act
        safe_check("ERRATA_S3R5_START_SHA256", check_err_start_sha, EXPECTED_ERRATA_S3R5_SHA)
        def check_err9_start_bytes(): return len(err9_now) == EXPECTED_ERRATA_9_BYTES, len(err9_now)
        safe_check("ERRATA_9_START_BYTES", check_err9_start_bytes, EXPECTED_ERRATA_9_BYTES)
        def check_err9_start_sha(): act = hashlib.sha256(err9_now).hexdigest(); return act == EXPECTED_ERRATA_9_SHA, act
        safe_check("ERRATA_9_START_SHA256", check_err9_start_sha, EXPECTED_ERRATA_9_SHA)

    start_records = parse_start_records(start_file)
    if mode == "end":
        def check_start_records(): return bool(start_records), "records present" if start_records else "empty"
        safe_check("START_RECORDS_PRESENT", check_start_records, "records present")

        start_rul_sha = start_records.get("RULINGS_SHA256")
        start_rul_bytes = int(start_records.get("RULINGS_BYTES", "0"))
        start_err_sha = start_records.get("ERRATA_S3R5_SHA256")
        start_err_bytes = int(start_records.get("ERRATA_S3R5_BYTES", "0"))
        start_err9_sha = start_records.get("ERRATA_9_SHA256")
        start_err9_bytes = int(start_records.get("ERRATA_9_BYTES", "0"))

        if start_rul_bytes > 0:
            def check_rul_start_pfx():
                pfx_sha = hashlib.sha256(rul_now[:start_rul_bytes]).hexdigest()
                return pfx_sha == start_rul_sha, pfx_sha
            safe_check("RULINGS_PREFIX_OF_START_UNCHANGED", check_rul_start_pfx, start_rul_sha)
            def check_rul_not_trunc(): return len(rul_now) >= start_rul_bytes, len(rul_now)
            safe_check("RULINGS_NOT_TRUNCATED", check_rul_not_trunc, f">= {start_rul_bytes}")

        if start_err_bytes > 0:
            def check_err_start_pfx():
                pfx_sha = hashlib.sha256(err_now[:start_err_bytes]).hexdigest()
                return pfx_sha == start_err_sha, pfx_sha
            safe_check("ERRATA_S3R5_PREFIX_OF_START_UNCHANGED", check_err_start_pfx, start_err_sha)
            def check_err_not_trunc(): return len(err_now) >= start_err_bytes, len(err_now)
            safe_check("ERRATA_S3R5_NOT_TRUNCATED", check_err_not_trunc, f">= {start_err_bytes}")

        if start_err9_bytes > 0:
            def check_err9_start_pfx():
                pfx_sha = hashlib.sha256(err9_now[:start_err9_bytes]).hexdigest()
                return pfx_sha == start_err9_sha, pfx_sha
            safe_check("ERRATA_9_PREFIX_OF_START_UNCHANGED", check_err9_start_pfx, start_err9_sha)
            def check_err9_not_trunc(): return len(err9_now) >= start_err9_bytes, len(err9_now)
            safe_check("ERRATA_9_NOT_TRUNCATED", check_err9_not_trunc, f">= {start_err9_bytes}")

        # End gate check: registries M1, M1R2, M1R3 identical to HEAD 4e9ff8b
        def check_diff_m1():
            d = subprocess.check_output(["git", "diff", EXPECTED_BASE, "--", "checkpoints/p05/registries/s4r9/M1"], cwd=REPO, text=True).strip()
            return d == "", "identical" if not d else f"diff: {d[:100]}"
        safe_check("M1_REGISTRIES_ALL_IDENTICAL_TO_BASE", check_diff_m1, "identical")

        def check_diff_m1r2():
            d = subprocess.check_output(["git", "diff", EXPECTED_BASE, "--", "checkpoints/p05/registries/s4r9/M1R2"], cwd=REPO, text=True).strip()
            return d == "", "identical" if not d else f"diff: {d[:100]}"
        safe_check("M1R2_REGISTRIES_ALL_IDENTICAL_TO_BASE", check_diff_m1r2, "identical")

        def check_diff_m1r3():
            d = subprocess.check_output(["git", "diff", EXPECTED_BASE, "--", "checkpoints/p05/registries/s4r9/M1R3"], cwd=REPO, text=True).strip()
            return d == "", "identical" if not d else f"diff: {d[:100]}"
        safe_check("M1R3_REGISTRIES_ALL_IDENTICAL_TO_BASE", check_diff_m1r3, "identical")

        # End gate check: FROZEN_SCRIPTS_R9M1R4.tsv sha assertion
        frozen_tsv_path = os.path.join(ev_dir, "FROZEN_SCRIPTS_R9M1R4.tsv")
        if not os.path.isfile(frozen_tsv_path):
            frozen_tsv_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R4", "FROZEN_SCRIPTS_R9M1R4.tsv")
        frozen_map = {}
        def check_frozen_scripts():
            if not os.path.isfile(frozen_tsv_path):
                return False, "missing FROZEN_SCRIPTS_R9M1R4.tsv"
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
                        frozen_map[f_rel] = f_sha
                        full_fp = os.path.join(REPO, f_rel) if not os.path.isabs(f_rel) else f_rel
                        if not os.path.isfile(full_fp):
                            frozen_ok = False
                            frozen_details.append("missing: " + f_rel)
                        else:
                            curr_sha = sha256_file(full_fp)
                            if curr_sha != f_sha:
                                frozen_ok = False
                                frozen_details.append(f"sha mismatch: {f_rel} ({curr_sha} != {f_sha})")
            return frozen_ok, "; ".join(frozen_details) if frozen_details else "all frozen OK"
        safe_check("FROZEN_SCRIPTS_SHA_UNCHANGED_END", check_frozen_scripts, "all frozen OK")

        # End gate check: allow files have NO " M " wildcard items
        def check_allow_end_wildcards():
            allow_end_path = os.path.join(REPO, "testing", "d003", "stage_s4r9", "gate_allow_r9m1r4_end.txt")
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
            return not has_m_wildcard, "clean" if not has_m_wildcard else f"bad: {bad_m_lines}"
        safe_check("ALLOW_END_NO_M_WILDCARD", check_allow_end_wildcards, "clean")

        # End gate check: Commit (i) and safe_run.log calls in frozen period
        commit_i = subprocess.check_output(["git", "log", "--grep=R9 M1R4 (i)", "-1", "--format=%H"], cwd=REPO, text=True).strip()
        def check_commit_i(): return bool(commit_i), commit_i if commit_i else "missing"
        safe_check("COMMIT_I_PRESENT", check_commit_i, "commit (i) found")

        if commit_i:
            commit_i_epoch = int(subprocess.check_output(["git", "log", "-1", "--format=%ct", commit_i], cwd=REPO, text=True).strip())
            log_path = os.path.join(ev_dir, "safe_run.log")
            log_entries = []
            if os.path.isfile(log_path):
                with open(log_path, "r", encoding="utf-8") as lf:
                    for line_idx, line in enumerate(lf, 1):
                        line = line.strip()
                        if not line: continue
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
                "unlogged": "unlogged_r9m1r4.py",
                "recert_posctrl": "recert_r9m1r4.py posctrl",
                "recert_formal": "recert_r9m1r4.py formal",
                "kmatch": "kmatch_r9m1r4.py",
                "summarize_recert": "summarize_recert_r9m1r4.py",
                "report_check": "report_check_r9m1r4.py",
                "copy_registries": "copy_registries_r9m1r4.py",
                "events": "events_r9m1r4.py",
                "sha_sums": "sha_sums_r9m1r4.py",
                "gate": "gate_r9m1r4.sh end",
                "finalize": "finalize_r9m1r4.py",
            }
            call_counts = {k: 0 for k in target_scripts}
            testing_d003_writes = []
            unfrozen_stage_calls = []

            for l_idx, l_ts, l_epoch, l_cmd in post_i_entries:
                for key, pattern in target_scripts.items():
                    if pattern in l_cmd:
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

            for key in target_scripts:
                def make_chk_call(k=key):
                    return lambda: (call_counts[k] == 1, call_counts[k])
                safe_check(f"POST_I_CALL_COUNT_{key.upper()}_EQ_1", make_chk_call(), 1)

            def check_post_i_writes(): return len(testing_d003_writes) == 0, len(testing_d003_writes)
            safe_check("POST_I_NO_TESTING_D003_WRITES", check_post_i_writes, 0)

            def check_post_i_frozen(): return len(unfrozen_stage_calls) == 0, str(unfrozen_stage_calls) if unfrozen_stage_calls else "all frozen"
            safe_check("POST_I_STAGE_SCRIPTS_ALL_FROZEN", check_post_i_frozen, "all frozen")

            def check_committed_i():
                diff_i = subprocess.check_output(["git", "diff", "--name-only", "--diff-filter=M", commit_i, "HEAD", "--", "testing/d003", "checkpoints/p05/briefs/"], cwd=REPO, text=True).strip()
                return diff_i == "", diff_i if diff_i else "unmodified"
            safe_check("COMMITTED_I_FILES_UNCHANGED_AT_END", check_committed_i, "unmodified")

        # End gate check: events covers all safe_run lines before gate
        def check_events_cover():
            events_tsv_path = os.path.join(ev_dir, "EVENTS_R9M1R4.tsv")
            if not os.path.isfile(events_tsv_path):
                events_tsv_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R4", "EVENTS_R9M1R4.tsv")
            if not os.path.isfile(events_tsv_path):
                return False, "missing EVENTS_R9M1R4.tsv"
            with open(events_tsv_path, encoding="utf-8") as ef:
                events_rows = [l for l in ef if l.strip() and not l.startswith("#") and not l.startswith("log_line\t")]
            log_path = os.path.join(ev_dir, "safe_run.log")
            safe_log_lines = open(log_path, encoding="utf-8").read().splitlines() if os.path.isfile(log_path) else []
            gate_line_idx = len(safe_log_lines)
            for idx, l in enumerate(safe_log_lines, 1):
                if "gate_r9m1r4.sh end" in l:
                    gate_line_idx = idx
                    break
            expected_count = gate_line_idx - 1
            if len(events_rows) != expected_count:
                return False, f"row count {len(events_rows)} != expected {expected_count}"
            for r_idx, r in enumerate(events_rows, 1):
                parts = r.split("\t")
                if parts[0] != str(r_idx):
                    return False, f"row {r_idx} log_line is {parts[0]}"
            return True, f"{len(events_rows)} rows strictly matched"
        safe_check("EVENTS_COVERS_ALL_LOGS_BEFORE_GATE", check_events_cover, "rows strictly matched")

        # End gate check: evidence SHA256SUMS.txt & truncated hash line match
        def check_evidence_sums():
            ev_sums_path = os.path.join(ev_dir, "SHA256SUMS.txt")
            if not os.path.isfile(ev_sums_path):
                return False, "missing SHA256SUMS.txt"
            sums_proc = subprocess.run(["sha256sum", "-c", "SHA256SUMS.txt"], cwd=ev_dir, capture_output=True, text=True)
            if sums_proc.returncode != 0:
                return False, f"sha256sum -c failed: {sums_proc.stderr[:100]}"
            with open(ev_sums_path, encoding="utf-8") as sf:
                lines = [l.strip() for l in sf if l.strip()]
            trunc_match = re.search(r"up to line (\d+):\s*([0-9a-f]{64})", lines[1] if len(lines) > 1 else "")
            if not trunc_match:
                return False, "line 2 missing truncated sha annotation"
            trunc_n = int(trunc_match.group(1))
            trunc_exp_sha = trunc_match.group(2)
            log_path = os.path.join(ev_dir, "safe_run.log")
            with open(log_path, "r", encoding="utf-8") as lf:
                all_lf_lines = lf.read().splitlines(True)
            first_n_text = "".join(all_lf_lines[:trunc_n]).encode("utf-8")
            act_trunc_sha = hashlib.sha256(first_n_text).hexdigest()
            if act_trunc_sha != trunc_exp_sha:
                return False, f"truncated hash mismatch at line {trunc_n}: {act_trunc_sha} != {trunc_exp_sha}"
            return True, f"all OK, truncated line {trunc_n} verified"
        safe_check("EVIDENCE_SHA256SUMS_ALL_OK", check_evidence_sums, "all OK")

        # End gate check: unlogged repo writes since start gate
        def check_unlogged_self():
            start_mtime = os.path.getmtime(start_file) if start_file and os.path.isfile(start_file) else 0
            log_path = os.path.join(ev_dir, "safe_run.log")
            logged_cmds = open(log_path, encoding="utf-8").read() if os.path.isfile(log_path) else ""
            unlogged = []
            for sdir in [os.path.join(REPO, "testing", "d003", "stage_s4r9"), os.path.join(REPO, "checkpoints", "p05")]:
                for root, dirs, files in os.walk(sdir):
                    if "evidence" in root:
                        continue
                    for f in files:
                        fp = os.path.join(root, f)
                        st = os.stat(fp)
                        if st.st_mtime > start_mtime:
                            rel = os.path.relpath(fp, REPO)
                            if rel not in logged_cmds and os.path.basename(rel) not in logged_cmds:
                                unlogged.append(rel)
            return len(unlogged) == 0, f"unlogged count: {len(unlogged)}: {unlogged[:5]}"
        safe_check("UNLOGGED_SELF_ZERO", check_unlogged_self, "unlogged count: 0: []")

        # End gate check: other rounds evidence dirs not touched
        def check_other_rounds_untouched():
            start_mtime = os.path.getmtime(start_file) if start_file and os.path.isfile(start_file) else 0
            other_touched = []
            for rname in ["m1", "m1r2", "m1r3"]:
                edir = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", rname)
                if os.path.isdir(edir):
                    for root, dirs, files in os.walk(edir):
                        for f in files:
                            fp = os.path.join(root, f)
                            if os.stat(fp).st_mtime > start_mtime:
                                other_touched.append(os.path.relpath(fp, REPO))
            return len(other_touched) == 0, f"touched: {other_touched}" if other_touched else "clean"
        safe_check("OTHER_ROUNDS_EVIDENCE_UNTOUCHED", check_other_rounds_untouched, "clean")

    # 8. Baseline stray build products
    if mode == "start":
        def check_stray_start():
            entries = scan_build_products()
            if os.path.exists(baseline_tsv):
                return False, "present before start"
            write_baseline(entries, baseline_tsv)
            return True, f"recorded {len(entries)} items"
        safe_check("STRAY_BASELINE_NOT_PRESENT_BEFORE_START", check_stray_start, "recorded items")

        entries = scan_build_products()
        for kp in KNOWN_PYC:
            def make_chk_pyc(k=kp):
                return lambda: (k in entries, "present" if k in entries else "absent")
            safe_check("STRAY_BASELINE_HAS_" + os.path.basename(kp), make_chk_pyc(), "present")
        def check_stray_count(): return True, len(entries)
        safe_check("STRAY_BASELINE_COUNT_RECORDED", check_stray_count, len(entries))

    if mode == "end":
        def check_stray_end():
            base = read_baseline(baseline_tsv) if os.path.isfile(baseline_tsv) else {}
            now = scan_build_products()
            new_items = sorted(k for k in now if k not in base)
            changed_items = sorted(k for k in now if k in base and now[k] != base[k])
            ok = not new_items and not changed_items
            return ok, f"new={new_items} changed={changed_items}" if not ok else "none"
        safe_check("STRAY_NEW_OR_CHANGED_NONE", check_stray_end, "none")

    # 9. Historical runners and judges
    for rel in HIST_RUNNERS:
        def make_chk_hist(r=rel):
            def chk():
                head_blob = subprocess.check_output(["git", "rev-parse", "HEAD:" + r], cwd=REPO, text=True).strip()
                d58_blob = subprocess.check_output(["git", "rev-parse", "d58bafd:" + r], cwd=REPO, text=True).strip()
                wt = subprocess.check_output(["git", "hash-object", os.path.join(REPO, r)], cwd=REPO, text=True).strip()
                ok = (head_blob == d58_blob == wt)
                return ok, f"{head_blob}|{d58_blob}|{wt}"
            return chk
        safe_check("HIST_UNCHANGED_SINCE_D58BAFD " + os.path.basename(rel), make_chk_hist(), "matched")

    # 10. STATE <= 8192 UTF-8 bytes
    def check_state_size():
        sb = len(open(state_path, "rb").read()) if os.path.isfile(state_path) else 999999
        return sb <= 8192, sb
    safe_check("STATE_BYTES_LE_8192", check_state_size, "<= 8192")

    # 11. No tracked files under testing/d003 modified or deleted since base
    def check_tracked_d003():
        diff_d003 = subprocess.check_output(["git", "diff", "--name-only", "--diff-filter=MD", EXPECTED_BASE, "--", "testing/d003"], cwd=REPO, text=True).strip()
        return diff_d003 == "", diff_d003 if diff_d003 else "unmodified"
    safe_check("TRACKED_TESTING_D003_NO_MOD_DEL", check_tracked_d003, "unmodified")

    return fails, results

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "start"
    start_file = sys.argv[2] if len(sys.argv) > 2 else None
    ev_dir = sys.argv[3] if len(sys.argv) > 3 else None
    fails, results = run_checks(mode, start_file, ev_dir)
    for st, name, exp, act in results:
        print("%s\t%s\texpected=%s\tactual=%s" % (st, name, exp, act))
    sys.exit(fails)
