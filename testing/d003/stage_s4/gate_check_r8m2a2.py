#!/usr/bin/env python3
# gate_check_r8m2a2.py -- P05-S4 R8 M2a2 gate helper. New file (copied from gate_check_r8m2a.py; original unchanged).
# Changes from the r8m2a version:
#  - baseline HEAD 6a4f003; STATE/RULINGS/ERRATA_8 start values from brief section 0;
#  - start-only: r8m2a SHA256SUMS.txt (19 entries) -c OK; SHA256SUMS_END.txt absent; postcommit_r8m2a.py tracked + sha;
#  - stray build products are BASELINE-based (U237): start writes STRAY_BASELINE_R8_M2a2.tsv (path, bytes, mtime_ns, sha256)
#    and checks the two known testing/d003 pyc files; end rescans and fails only for new or changed entries (U17: nothing deleted).
import hashlib, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
EV = os.path.join(REPO, EV_REL)
BASELINE_TSV = os.path.join(EV, "STRAY_BASELINE_R8_M2a2.tsv")

EXPECTED_BASE = "6a4f0031afeda0a3105c9983d5a65a2d847f1488"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECTED_S4_TREE = "6cff923a02baf19e01966b2339755cbf3a5deeef"
EXPECTED_F2_TREE = "e124925f5b242486a913b813fa181664f665b048"
EXPECTED_M1C_PREREG_SHA = "e1e555ee4ca20421b6e5681e18be6cd1b873fc7cff06d246c01fad65d8d3a562"
EXPECTED_FROZEN_SHA = "58ce124161c0cdb0bd10f10acac351ab7ffa460bb11152abaa6e8004b036f924"
EXPECTED_EFFECTIVE_M1B_SHA = "e248b671fac5d83be2081ca3212a91c3ec2668cc43aa6158578a5573c6cd1ef0"
EXPECTED_M1_SUMMARY_R8M1C4_SHA = "f678af1fb3b62fddb840cba3086e8ef6d4030ff9e7d1577adc179adb37ab6d8b"
EXPECTED_FIX_COVERAGE_R8M1C4_SHA = "1226f73bf96d44185444b4b9b4c82f01aae8a9b762c482feb82a7a0e2cfa53b7"
EXPECTED_POSTCOMMIT_R8M1C4_SHA = "07752ac2f8d7b31df69ee7f3d27a885028030d62f82f94ddc4d3bc53ca1ab05f"
EXPECTED_POSTCOMMIT_R8M2A_SHA = "8063c17108d6b3e9e2c8b4f8d7495375f45e655eae05930dd5a416d55ae38081"
EXPECTED_PREREG_R8M2A_SHA = "557f568a787f3d216c0a412c597cabc41dbc46771f1404691565f3b2ae362e80"
EXPECTED_STATE_BYTES = 7857
EXPECTED_STATE_SHA = "5554334a11200e9dfc0bb8f371c57e5155f49e71b9dc109a556eaac7531e87ab"
EXPECTED_RULINGS_BYTES = 92855
EXPECTED_RULINGS_SHA = "c1632c0f518ff20d3139891230b379772ad6757ef16e60cc7564abf71c19813c"
EXPECTED_ERRATA8_BYTES = 67104
EXPECTED_ERRATA8_SHA = "e559b0110a26f3f039b27a39c1a08924eee4b43e394ddf799cee347706cf7520"
HIST_RUNNERS = [
    "testing/d003/stage_s4/run_r6c_state.py",
    "testing/d003/stage_s4/r6c2_seam_state.py",
    "testing/d003/stage_s4/r6c_judge.py",
    "testing/d003/stage_s4/r6c2_seam_judge.py",
    "testing/d003/stage_s4/r6c_state.gdb",
    "testing/d003/stage_s4/r6c_state_gdb.py",
]
R8M1C4_DIR = os.path.join("checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c4")
R8M2A_DIR = os.path.join("checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a")
# Known pre-existing products at start (U237): both must be present in the start baseline.
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
    """Return list of (sha, fname) from a SHA256SUMS-style file, skipping blank and comment lines."""
    listed = []
    with open(sums_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            exp_sha, fname = line.split(None, 1)
            listed.append((exp_sha, fname))
    return listed


def check_sums_dir(dir_path, expected_count):
    """Return (ok, detail). Every listed file verifies and the listed set equals the directory set minus SHA256SUMS.txt."""
    sums = os.path.join(dir_path, "SHA256SUMS.txt")
    if not os.path.isfile(sums):
        return False, "missing SHA256SUMS.txt"
    listed = read_sums(sums)
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


def verify_sums_file(dir_path, sums_name, expected_count):
    """Return (ok, detail, names). Verifies every entry of one manifest (-c semantics)."""
    sums = os.path.join(dir_path, sums_name)
    if not os.path.isfile(sums):
        return False, "missing %s" % sums_name, []
    listed = read_sums(sums)
    if len(listed) != expected_count:
        return False, "count %d != %d" % (len(listed), expected_count), []
    for exp_sha, fname in listed:
        fpath = os.path.join(dir_path, fname)
        if not os.path.isfile(fpath) or sha256_file(fpath) != exp_sha:
            return False, "sha mismatch: %s" % fname, []
    return True, "all %d OK" % len(listed), [f for _, f in listed]


def scan_build_products():
    """Return dict relpath -> (kind, bytes, mtime_ns, sha256) for __pycache__ dirs (their files), *.o and a.out.
    Scope (fixed before start, U237): testing/d003 and checkpoints/p05, excluding checkpoints/p05/evidence/."""
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
    with open(BASELINE_TSV, "x", encoding="utf-8") as fh:  # U17: refuse overwrite
        fh.write("# STRAY_BASELINE_R8_M2a2 (start): path\tkind\tbytes\tmtime_ns\tsha256\n")
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
    results = []  # (status, check_name, expected, actual)
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

    # 3. Judge sha256
    judge_path = os.path.join(REPO, "testing", "d003", "judge_d003.py")
    judge_sha = sha256_file(judge_path) if os.path.isfile(judge_path) else "missing"
    check("JUDGE_SHA256", judge_sha == EXPECTED_JUDGE_SHA, EXPECTED_JUDGE_SHA, judge_sha)

    # 4. M1c prereg / frozen facts / effective M1b sha256 (unchanged historical baselines)
    prereg = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a", "REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv")
    prereg_sha = sha256_file(prereg) if os.path.isfile(prereg) else "missing"
    check("M1C_PREREG_SHA256", prereg_sha == EXPECTED_M1C_PREREG_SHA, EXPECTED_M1C_PREREG_SHA, prereg_sha)
    frozen = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c2", "PREREG_M1C_FACTS_R8_M1c2.tsv")
    frozen_sha = sha256_file(frozen) if os.path.isfile(frozen) else "missing"
    check("M1C_FROZEN_FACTS_SHA256", frozen_sha == EXPECTED_FROZEN_SHA, EXPECTED_FROZEN_SHA, frozen_sha)
    eff = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1b", "r8m1b3", "EFFECTIVE_M1B_R8_M1b3.tsv")
    eff_sha = sha256_file(eff) if os.path.isfile(eff) else "missing"
    check("EFFECTIVE_M1B_SHA256", eff_sha == EXPECTED_EFFECTIVE_M1B_SHA, EXPECTED_EFFECTIVE_M1B_SHA, eff_sha)

    # 4d. M1c4 summary and fix coverage sha256
    ms = os.path.join(REPO, R8M1C4_DIR, "M1_SUMMARY_R8_M1c4.tsv")
    ms_sha = sha256_file(ms) if os.path.isfile(ms) else "missing"
    check("M1C4_SUMMARY_SHA256", ms_sha == EXPECTED_M1_SUMMARY_R8M1C4_SHA, EXPECTED_M1_SUMMARY_R8M1C4_SHA, ms_sha)
    fc = os.path.join(REPO, R8M1C4_DIR, "FIX_COVERAGE_M1_R8_M1c4_R2.tsv")
    fc_sha = sha256_file(fc) if os.path.isfile(fc) else "missing"
    check("M1C4_FIX_COVERAGE_R2_SHA256", fc_sha == EXPECTED_FIX_COVERAGE_R8M1C4_SHA, EXPECTED_FIX_COVERAGE_R8M1C4_SHA, fc_sha)

    # 4e. postcommit_r8m1c4.py sha256 and tracked
    pc = os.path.join(REPO, "testing", "d003", "stage_s4", "postcommit_r8m1c4.py")
    pc_sha = sha256_file(pc) if os.path.isfile(pc) else "missing"
    check("POSTCOMMIT_R8M1C4_SHA256", pc_sha == EXPECTED_POSTCOMMIT_R8M1C4_SHA, EXPECTED_POSTCOMMIT_R8M1C4_SHA, pc_sha)
    pc_tracked = subprocess.check_output(["git", "ls-files", "testing/d003/stage_s4/postcommit_r8m1c4.py"], cwd=REPO, text=True).strip()
    check("POSTCOMMIT_R8M1C4_TRACKED", pc_tracked == "testing/d003/stage_s4/postcommit_r8m1c4.py", "tracked", pc_tracked or "untracked")

    # 4f. start-only: STATE.md size and sha256; r8m2a postcommit, prereg; r8m2a manifests
    if mode == "start":
        state_path = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
        state_b = open(state_path, "rb").read() if os.path.isfile(state_path) else b""
        check("STATE_START_BYTES", len(state_b) == EXPECTED_STATE_BYTES, EXPECTED_STATE_BYTES, len(state_b))
        check("STATE_START_SHA256", hashlib.sha256(state_b).hexdigest() == EXPECTED_STATE_SHA, EXPECTED_STATE_SHA, hashlib.sha256(state_b).hexdigest())
        pcm = os.path.join(REPO, "testing", "d003", "stage_s4", "postcommit_r8m2a.py")
        pcm_sha = sha256_file(pcm) if os.path.isfile(pcm) else "missing"
        check("POSTCOMMIT_R8M2A_SHA256", pcm_sha == EXPECTED_POSTCOMMIT_R8M2A_SHA, EXPECTED_POSTCOMMIT_R8M2A_SHA, pcm_sha)
        pcm_tracked = subprocess.check_output(["git", "ls-files", "testing/d003/stage_s4/postcommit_r8m2a.py"], cwd=REPO, text=True).strip()
        check("POSTCOMMIT_R8M2A_TRACKED", pcm_tracked == "testing/d003/stage_s4/postcommit_r8m2a.py", "tracked", pcm_tracked or "untracked")
        pr = os.path.join(REPO, R8M2A_DIR, "PREREG_M2_R8_M2a_R2.tsv")
        pr_sha = sha256_file(pr) if os.path.isfile(pr) else "missing"
        check("R8M2A_PREREG_R2_SHA256", pr_sha == EXPECTED_PREREG_R8M2A_SHA, EXPECTED_PREREG_R8M2A_SHA, pr_sha)
        ok_m2a, detail_m2a, _names_m2a = verify_sums_file(os.path.join(REPO, R8M2A_DIR), "SHA256SUMS.txt", 19)
        check("R8M2A_SUMS_19_ALL_OK", ok_m2a, "all 19 OK", detail_m2a)
        check("R8M2A_SUMS_END_ABSENT", not os.path.exists(os.path.join(REPO, R8M2A_DIR, "SHA256SUMS_END.txt")), "absent", "absent" if not os.path.exists(os.path.join(REPO, R8M2A_DIR, "SHA256SUMS_END.txt")) else "present")
        n_r8m2a = len(os.listdir(os.path.join(REPO, R8M2A_DIR)))
        check("R8M2A_DIR_FILE_COUNT_20", n_r8m2a == 20, 20, n_r8m2a)

    # 5. r8m1b3 (10 files) SHA256SUMS all OK
    d = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1b", "r8m1b3")
    ok_b, det_b = check_sums_dir(d, 10)
    check("R8M1B3_SUMS_ALL_OK", ok_b, "all 10 OK", det_b)

    # 5b. r8m1c2 (19 entries) SHA256SUMS all OK
    d2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c2")
    ok2, detail2 = check_sums_dir(d2, 19)
    check("R8M1C2_SUMS_ALL_OK", ok2, "all 19 OK", detail2)

    # 5c. r8m1c4 manifests (24 + 2 entries) -c OK, and the union covers the directory (28 files)
    dc4 = os.path.join(REPO, R8M1C4_DIR)
    okA, detailA, namesA = verify_sums_file(dc4, "SHA256SUMS.txt", 24)
    check("R8M1C4_SUMS_24_ALL_OK", okA, "all 24 OK", detailA)
    okB, detailB, namesB = verify_sums_file(dc4, "SHA256SUMS_END.txt", 2)
    check("R8M1C4_SUMS_END_2_ALL_OK", okB, "all 2 OK", detailB)
    dir_names_c4 = sorted(n for n in os.listdir(dc4) if n not in ("SHA256SUMS.txt", "SHA256SUMS_END.txt"))
    union_c4 = sorted(namesA + namesB)
    check("R8M1C4_MANIFEST_UNION_EQ_DIR", union_c4 == dir_names_c4, "%d names" % len(dir_names_c4), "%d names, equal=%s" % (len(union_c4), union_c4 == dir_names_c4))
    check("R8M1C4_DIR_FILE_COUNT_28", len(os.listdir(dc4)) == 28, 28, len(os.listdir(dc4)))

    # 6. s4r8 SHA256SUMS: all lines except the living ERRATA_8.txt line must verify (-c OK).
    s4r8 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8")
    sums_path = os.path.join(s4r8, "SHA256SUMS.txt")
    sums_bad = []
    sums_n = 0
    with open(sums_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            exp_sha, fname = line.split(None, 1)
            if fname == "ERRATA_8.txt":
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

    # 8. ERRATA_8 prefix at the R8 M1a6 record (72dc6aed..., 13990 bytes)
    check("ERRATA_8_SUMS_LINE_PREFIX", hashlib.sha256(err_now[:13990]).hexdigest() == "72dc6aedfe698022727c7871a643a354dfa245c495d5346405b42c9ba01a1551", "72dc6aed...", hashlib.sha256(err_now[:13990]).hexdigest())

    # 8b. Start-only: the append bases recorded in the brief (section 0)
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
        # r8m2a directory: its 20 original files unchanged (only the 5 section 4.0 files may be added)
        ok_m2a_end, det_m2a_end, _n = verify_sums_file(os.path.join(REPO, R8M2A_DIR), "SHA256SUMS.txt", 19)
        check("R8M2A_ORIGINAL_19_SHA_UNCHANGED_END", ok_m2a_end, "all 19 OK", det_m2a_end)

    # 8c. Baseline-based stray build products (U237)
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
