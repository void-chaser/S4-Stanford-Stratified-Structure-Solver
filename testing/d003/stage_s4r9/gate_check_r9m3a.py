#!/usr/bin/env python3
# gate_check_r9m3a.py -- P05-S4 R9 M3a gate helper. New file (r9m3a).
# Baseline HEAD: 2f86aa11c7ee1bb16f663abf03ddbf04674a6912
# Every check is wrapped in try/except: an exception produces a FAIL line with CHECK_CRASHED
# and the run continues. The FAIL count is the number of lines starting with "FAIL\t" and is
# also the exit status (capped at 255).
import os, sys, re, hashlib, subprocess, datetime, fnmatch

# ==================== CONSTANTS ====================
ROUND_TAG = "r9m3a"
ROUND_NAME = "M3a"
EXPECTED_BASE = "2f86aa11c7ee1bb16f663abf03ddbf04674a6912"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECTED_S4_TREE_F4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXPECTED_S4_TREE_F3 = "6cff923a02baf19e01966b2339755cbf3a5deeef"
EXPECTED_F2_TREE = "e124925f5b242486a913b813fa181664f665b048"
EXPECTED_B_TREE = "1d738e64f9864a475fdb3de34cd3601605df2c64"
EXPECTED_BRANCH = "codex/p05-d003-fft-error-propagation"
EXPECTED_STATE_BYTES_START = 8480
EXPECTED_STATE_SHA_START = "10b66407c3b50059ec55b6c4c9f513ef25d63993bf06632eb4ec0b4e34dfa7a7"
EXPECTED_RULINGS_BYTES_START = 134794
EXPECTED_RULINGS_SHA_START = "8b3d0e31fff12ddd84827e2f508f458f73c8574681feb2100aa684f9a3428ae2"
EXPECTED_RULINGS_MAX_U_START = "U327"
EXPECTED_ERRATA_9_BYTES_START = 30931
EXPECTED_ERRATA_9_SHA_START = "49add16f2343c92893fc500d25f3d37b6b1c4c76be5e7cb3eb891308037f5748"
EXPECTED_ERRATA_9_LAST_E_START = "E9-34"
EXPECTED_M1R4_SUMS_SHA = "57d72574415e9b255f2805cf65b88049964123d6a6980487d6565a46311e5d75"
HIST_REGISTRIES = [
    ("s3r5", "checkpoints/p05/registries/s3r5"),
    ("M0", "checkpoints/p05/registries/s4r9/M0"),
    ("M2", "checkpoints/p05/registries/s4r9/M2"),
    ("M2b", "checkpoints/p05/registries/s4r9/M2b"),
    ("M2c", "checkpoints/p05/registries/s4r9/M2c"),
    ("M1", "checkpoints/p05/registries/s4r9/M1"),
    ("M1R2", "checkpoints/p05/registries/s4r9/M1R2"),
    ("M1R3", "checkpoints/p05/registries/s4r9/M1R3"),
    ("M1R4", "checkpoints/p05/registries/s4r9/M1R4"),
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
# Frozen scripts expected at the end gate: gate itself counts 1 (its own start line is logged).
POST_I_SCRIPTS = [
    ("RUN_MAKETEST", "testing/d003/stage_s4r9/run_maketest_r9m3a.py", ""),
    ("JUDGE_MAKETEST_POSCTRL", "testing/d003/stage_s4r9/judge_maketest_r9m3a.py", "posctrl"),
    ("JUDGE_MAKETEST_FORMAL", "testing/d003/stage_s4r9/judge_maketest_r9m3a.py", "formal"),
    ("REPORT_CHECK", "testing/d003/stage_s4r9/report_check_r9m3a.py", ""),
    ("COPY_REGISTRIES", "testing/d003/stage_s4r9/copy_registries_r9m3a.py", ""),
    ("EVENTS", "testing/d003/stage_s4r9/events_r9m3a.py", ""),
    ("SHA_SUMS", "testing/d003/stage_s4r9/sha_sums_r9m3a.py", ""),
    ("GATE", "testing/d003/stage_s4r9/gate_r9m3a.sh", "end"),
]
OTHER_ROUND_EV = ["m1", "m1r2", "m1r3", "m1r4"]
LOG_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")


def sh(cmd):
    return subprocess.check_output(cmd, cwd=REPO, text=True, stderr=subprocess.STDOUT).strip()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            b = fh.read(65536)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def read_sums(sums_path):
    out = []
    with open(sums_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(None, 1)
            if len(parts) == 2:
                out.append((parts[0], parts[1]))
    return out


def verify_sums_dir(dir_path):
    sums = os.path.join(dir_path, "SHA256SUMS.txt")
    if not os.path.isfile(sums):
        return False, 0, "missing SHA256SUMS.txt"
    listed = read_sums(sums)
    if not listed:
        return False, 0, "empty SHA256SUMS.txt"
    for exp, name in listed:
        fp = os.path.join(dir_path, name)
        if not os.path.isfile(fp) or sha256_file(fp) != exp:
            return False, len(listed), "sha mismatch: " + name
    return True, len(listed), "all %d OK" % len(listed)


def parse_start_records(start_file):
    recs = {}
    if not start_file or not os.path.isfile(start_file):
        return recs
    with open(start_file, encoding="utf-8") as fh:
        for line in fh:
            parts = line.rstrip("\r\n").split("\t")
            if len(parts) >= 3 and parts[0] == "RECORD":
                val = parts[2]
                if val.startswith("value="):
                    val = val[6:]
                recs[parts[1]] = val
    return recs


def parse_log(ev_dir):
    # one record per physical line that starts with a UTC timestamp and a TAB
    path = os.path.join(ev_dir, "safe_run.log")
    recs = []
    if not os.path.isfile(path):
        return recs
    with open(path, encoding="utf-8", errors="replace") as fh:
        for idx, line in enumerate(fh, 1):
            m = LOG_TS_RE.match(line)
            if not m:
                continue
            parts = line.rstrip("\n").split("\t")
            cmd = ""
            for p in parts[1:]:
                if p.startswith("cmd="):
                    cmd = p[4:]
                    break
            recs.append((idx, m.group(1), cmd))
    return recs


def log_epoch(ts):
    try:
        return int(datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp())
    except Exception:
        return 0


def is_script_call(cmd, relpath, mode_word):
    # token match: the script must appear as a standalone word, invoked by python3 or sh
    head = cmd.strip()
    if not re.match(r"^(?:python3|sh)\b", head):
        return False
    toks = head.split()
    if relpath not in toks:
        return False
    if mode_word:
        return mode_word in toks
    return True


def count_script_calls(log_recs, relpath, mode_word, min_epoch):
    hits = []
    for idx, ts, cmd in log_recs:
        if log_epoch(ts) < min_epoch:
            continue
        if is_script_call(cmd, relpath, mode_word):
            hits.append(idx)
    return hits


def scan_repo_reported_files():
    # files under testing/d003/stage_s4r9 and checkpoints/p05 excluding evidence/
    out = {}
    for target in [os.path.join(REPO, "testing", "d003", "stage_s4r9"), os.path.join(REPO, "checkpoints", "p05")]:
        for root, dirs, files in os.walk(target):
            parts = root.split(os.sep)
            if "evidence" in parts:
                continue
            for f in files:
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, REPO)
                out[rel] = int(os.path.getmtime(fp))
    return out


def build_manifest():
    out = {}
    bdir = os.path.join(REPO, "build")
    if os.path.isdir(bdir):
        for root, dirs, files in os.walk(bdir):
            for f in files:
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, REPO)
                st = os.stat(fp)
                out[rel] = (st.st_size, int(st.st_mtime), sha256_file(fp))
    return out


def tmp_snapshot():
    root = os.sep + "tmp"
    entries = sorted(os.listdir(root)) if os.path.isdir(root) else []
    sha = hashlib.sha256(("\n".join(entries).encode("utf-8") + (b"\n" if entries else b"")).hexdigest().encode()).hexdigest() if False else hashlib.sha256(("\n".join(entries).encode("utf-8") + ("\n" if entries else "")).encode("utf-8")).hexdigest()
    return len(entries), sha


def main():
    mode = sys.argv[1]
    out_file = sys.argv[2]
    start_file = sys.argv[3]
    ev_dir = sys.argv[4]
    extra = sys.argv[5:]
    commit_i_override = None
    i = 0
    while i < len(extra):
        if extra[i] == "--commit-i" and i + 1 < len(extra):
            commit_i_override = extra[i + 1]
        i += 1

    results = []
    records = []
    fails = 0

    def check(name, cond, exp, act):
        nonlocal fails
        st = "PASS" if cond else "FAIL"
        if not cond:
            fails += 1
        results.append((st, name, str(exp), str(act)))

    def safe(name, fn, exp):
        nonlocal fails
        try:
            ok, act = fn()
            check(name, ok, exp, act)
        except Exception as exc:
            check(name, False, exp, "CHECK_CRASHED: %s: %s" % (type(exc).__name__, exc))

    def record(name, val):
        records.append((name, str(val)))

    # ---------- self check ----------
    def c_clean():
        bad = [w for w in ["m1r2", "m1r3", "m1r4"] if (w in ROUND_TAG.lower() or w in ROUND_NAME.lower())]
        return (len(bad) == 0), ("clean" if not bad else "found " + ",".join(bad))
    safe("CONSTANTS_CLEAN_NO_OLD_ROUNDS", c_clean, "clean")

    # ---------- common checks ----------
    def c_branch():
        b = sh(["git", "branch", "--show-current"])
        return b == EXPECTED_BRANCH, b
    safe("BRANCH_IS_EXPECTED", c_branch, EXPECTED_BRANCH)

    def c_head():
        h = sh(["git", "rev-parse", "HEAD"])
        record("HEAD", h)
        if mode == "start":
            return h == EXPECTED_BASE, h
        return len(h) == 40, h
    safe("HEAD_IS_BASE" if mode == "start" else "HEAD_PRESENT", c_head, EXPECTED_BASE if mode == "start" else "40-hex sha")

    def c_s4():
        t = sh(["git", "rev-parse", "HEAD:S4"])
        record("HEAD_S4", t)
        return t == EXPECTED_S4_TREE_F4, t
    safe("HEAD_S4_TREE_EQ_F4", c_s4, EXPECTED_S4_TREE_F4)

    def c_f3():
        t = sh(["git", "rev-parse", "8d8202a:S4"])
        return t == EXPECTED_S4_TREE_F3, t
    safe("F3_8d8202a_S4_TREE", c_f3, EXPECTED_S4_TREE_F3)

    def c_f2():
        t = sh(["git", "rev-parse", "a07b5ac:S4"])
        return t == EXPECTED_F2_TREE, t
    safe("F2_a07b5ac_S4_TREE", c_f2, EXPECTED_F2_TREE)

    def c_b():
        t = sh(["git", "rev-parse", "37a82e8:S4"])
        return t == EXPECTED_B_TREE, t
    safe("B_37a82e8_S4_TREE", c_b, EXPECTED_B_TREE)

    def c_judge():
        p = os.path.join(REPO, "testing", "d003", "judge_d003.py")
        a = sha256_file(p) if os.path.isfile(p) else "missing"
        return a == EXPECTED_JUDGE_SHA, a
    safe("JUDGE_SHA256", c_judge, EXPECTED_JUDGE_SHA)

    for name, rel, exp in S3R5_ARTIFACTS:
        def mk(rel=rel, exp=exp):
            def f():
                p = os.path.join(REPO, rel)
                a = sha256_file(p) if os.path.isfile(p) else "missing"
                return a == exp, a
            return f
        safe("ARTIFACT_" + name, mk(), exp)

    for tag, d in HIST_REGISTRIES:
        def mkr(tag=tag, d=d):
            def f():
                ok, cnt, det = verify_sums_dir(os.path.join(REPO, d))
                record("REGISTRY_COUNT_" + tag, cnt)
                return ok, det
            return f
        safe("HIST_REGISTRY_" + tag + "_ALL_OK", mkr(), "all OK")

    def c_m1r4_sums_sha():
        p = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R4/SHA256SUMS.txt")
        a = sha256_file(p) if os.path.isfile(p) else "missing"
        return a == EXPECTED_M1R4_SUMS_SHA, a
    safe("M1R4_SUMS_SHA256", c_m1r4_sums_sha, EXPECTED_M1R4_SUMS_SHA)

    def c_clean_addons():
        # every untracked/modified entry must match the round allow list patterns
        allow_p = os.path.join(REPO, "testing/d003/stage_s4r9/gate_allow_r9m3a_start.txt")
        pats = [l.strip() for l in open(allow_p, encoding="utf-8") if l.strip() and not l.strip().startswith("#")]
        st = sh(["git", "status", "--short", "-uall"]).splitlines()
        bad = []
        for line in st:
            line = line.rstrip()
            if not line:
                continue
            if not any(fnmatch.fnmatch(line, p) for p in pats):
                bad.append(line)
        return len(bad) == 0, ("all entries within round allow list" if not bad else str(bad[:6]))
    safe("GIT_STATUS_WITHIN_ROUND_ALLOW_LIST", c_clean_addons, "all entries within round allow list")

    def c_no_tracked_mods_outside():
        d = sh(["git", "diff", "HEAD", "--name-only"])
        return d == "", (d if d else "no tracked modification")
    safe("GIT_TRACKED_NO_MODIFICATION", c_no_tracked_mods_outside, "no tracked modification")

    def c_s4_zero_mod():
        d = sh(["git", "diff", "HEAD", "--", "S4"])
        return d == "", (d if d else "S4 unmodified")
    safe("S4_DIR_ZERO_MODIFICATION", c_s4_zero_mod, "S4 unmodified")

    tmp_count, tmp_sha = 0, ""
    def c_tmp():
        nonlocal tmp_count, tmp_sha
        tmp_count, tmp_sha = tmp_snapshot()
        return True, "count=%d sha=%s" % (tmp_count, tmp_sha)
    safe("TMP_SNAPSHOT_READ", c_tmp, "snapshot read")

    allstatus = os.path.join(ev_dir, "ALL_STATUS_R9M3A.txt")
    def c_write_status():
        os.makedirs(ev_dir, exist_ok=True)
        with open(allstatus, "w", encoding="utf-8") as fh:
            fh.write(sh(["git", "status", "--short", "-uall"]) + "\n")
            fh.write("BRANCH\t" + sh(["git", "branch", "--show-current"]) + "\n")
            fh.write("HEAD\t" + sh(["git", "rev-parse", "HEAD"]) + "\n")
        return os.path.isfile(allstatus), "written"
    safe("STATUS_ARTIFACT_WRITTEN", c_write_status, "written")

    if mode == "start":
        record("START_TIME_UTC", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        record("TMP_COUNT", tmp_count)
        record("TMP_SHA256", tmp_sha)

        rul_p = os.path.join(REPO, "checkpoints/p05/registries/RULINGS.tsv")
        err_p = os.path.join(REPO, "checkpoints/p05/registries/s4r9/ERRATA_9.txt")
        st_p = os.path.join(REPO, "checkpoints/p05/STATE.md")
        rul_b = open(rul_p, "rb").read() if os.path.isfile(rul_p) else b""
        err_b = open(err_p, "rb").read() if os.path.isfile(err_p) else b""
        st_b = open(st_p, "rb").read() if os.path.isfile(st_p) else b""
        record("RULINGS_BYTES", len(rul_b))
        record("RULINGS_SHA256", sha256_bytes(rul_b))
        record("ERRATA_9_BYTES", len(err_b))
        record("ERRATA_9_SHA256", sha256_bytes(err_b))
        record("STATE_BYTES", len(st_b))

        safe("RULINGS_START_BYTES", lambda: (len(rul_b) == EXPECTED_RULINGS_BYTES_START, len(rul_b)), EXPECTED_RULINGS_BYTES_START)
        safe("RULINGS_START_SHA256", lambda: (sha256_bytes(rul_b) == EXPECTED_RULINGS_SHA_START, sha256_bytes(rul_b)), EXPECTED_RULINGS_SHA_START)

        def c_max_u():
            nums = []
            for line in rul_b.decode("utf-8", "replace").splitlines():
                f = line.split("\t")[0]
                if f.startswith("U") and f[1:].isdigit():
                    nums.append(int(f[1:]))
            return ("U%d" % max(nums)) == EXPECTED_RULINGS_MAX_U_START if nums else False, ("U%d" % max(nums) if nums else "none")
        safe("RULINGS_START_MAX_U", c_max_u, EXPECTED_RULINGS_MAX_U_START)

        def c_rul_fields():
            for line in rul_b.decode("utf-8", "replace").splitlines():
                if not line.strip() or line.strip().startswith("#"):
                    continue
                if len(line.split("\t")) != 5:
                    return False, "bad field count in: " + line[:40]
            return True, "all lines 5 fields"
        safe("RULINGS_LINES_5_FIELDS", c_rul_fields, "all lines 5 fields")

        safe("ERRATA_9_START_BYTES", lambda: (len(err_b) == EXPECTED_ERRATA_9_BYTES_START, len(err_b)), EXPECTED_ERRATA_9_BYTES_START)
        safe("ERRATA_9_START_SHA256", lambda: (sha256_bytes(err_b) == EXPECTED_ERRATA_9_SHA_START, sha256_bytes(err_b)), EXPECTED_ERRATA_9_SHA_START)

        def c_last_e():
            ids = []
            for line in err_b.decode("utf-8", "replace").splitlines():
                m = re.match(r"^(E9-\d+)", line)
                if m:
                    ids.append(m.group(1))
            return (ids[-1] if ids else "none") == EXPECTED_ERRATA_9_LAST_E_START, (ids[-1] if ids else "none")
        safe("ERRATA_9_START_LAST_E", c_last_e, EXPECTED_ERRATA_9_LAST_E_START)

        safe("STATE_START_BYTES", lambda: (len(st_b) == EXPECTED_STATE_BYTES_START, len(st_b)), EXPECTED_STATE_BYTES_START)
        safe("STATE_START_SHA256", lambda: (sha256_bytes(st_b) == EXPECTED_STATE_SHA_START, sha256_bytes(st_b)), EXPECTED_STATE_SHA_START)

        def c_tmp_zero():
            return tmp_count == int(record_map_get("TMP_COUNT", "0")), tmp_count
        # /tmp baseline is whatever the start gate saw; recorded above
        safe("TMP_SNAPSHOT_RECORDED", lambda: (tmp_sha != "", "count=%d" % tmp_count), "recorded")

        def c_root_so():
            sos = [f for f in os.listdir(REPO) if f.endswith(".so")]
            return len(sos) == 0, ("no *.so" if not sos else str(sos))
        safe("ROOT_NO_SO_AT_START", c_root_so, "no *.so")

        bpath = os.path.join(ev_dir, "BUILD_BASELINE_R9M3A.tsv")
        def c_build_baseline():
            man = build_manifest()
            os.makedirs(ev_dir, exist_ok=True)
            with open(bpath, "w", encoding="utf-8") as fh:
                fh.write("# BUILD_BASELINE_R9M3A.tsv -- repository-root build/ manifest at the start gate (Rule: supplemental note 2)\n")
                fh.write("relpath\tsize\tmtime\tsha256\n")
                for k in sorted(man):
                    s, mt, h = man[k]
                    fh.write("%s\t%d\t%d\t%s\n" % (k, s, mt, h))
            record("BUILD_BASELINE_ITEMS", len(man))
            return os.path.isfile(bpath), "items=%d" % len(man)
        safe("BUILD_BASELINE_SAVED", c_build_baseline, "saved")

        sbpath = os.path.join(ev_dir, "STRAY_BASELINE_R9M3A.tsv")
        def c_stray():
            rows = []
            for root, dirs, files in os.walk(os.path.join(REPO, "testing", "d003")):
                for f in files:
                    if f.endswith(".pyc") or f.endswith(".o"):
                        fp = os.path.join(root, f)
                        st = os.stat(fp)
                        rows.append((os.path.relpath(fp, REPO), st.st_size, int(st.st_mtime), sha256_file(fp)))
            with open(sbpath, "w", encoding="utf-8") as fh:
                fh.write("# STRAY_BASELINE_R9M3A.tsv -- stray build products under testing/d003 at the start gate\n")
                fh.write("relpath\tsize\tmtime\tsha256\n")
                for r in sorted(rows):
                    fh.write("%s\t%d\t%d\t%s\n" % r)
            return True, "items=%d" % len(rows)
        safe("STRAY_BASELINE_SAVED", c_stray, "saved")

    else:
        # ================= END MODE =================
        start_recs = parse_start_records(start_file)
        safe("START_RECORDS_PRESENT", lambda: (len(start_recs) > 0, "%d records" % len(start_recs) if start_recs else "missing"), "records present")

        start_tmp_count = int(start_recs.get("TMP_COUNT", "-1") or -1)
        start_tmp_sha = start_recs.get("TMP_SHA256", "")
        safe("TMP_COUNT_MATCHES_START", lambda: (tmp_count == start_tmp_count, tmp_count), start_tmp_count)
        safe("TMP_SHA_MATCHES_START", lambda: (tmp_sha == start_tmp_sha, tmp_sha), start_tmp_sha)

        # RULINGS / ERRATA_9 prefix unchanged from the start gate
        rul_p = os.path.join(REPO, "checkpoints/p05/registries/RULINGS.tsv")
        err_p = os.path.join(REPO, "checkpoints/p05/registries/s4r9/ERRATA_9.txt")
        rul_b = open(rul_p, "rb").read() if os.path.isfile(rul_p) else b""
        err_b = open(err_p, "rb").read() if os.path.isfile(err_p) else b""
        start_rul_bytes = int(start_recs.get("RULINGS_BYTES", "0") or 0)
        start_rul_sha = start_recs.get("RULINGS_SHA256", "")
        start_err_bytes = int(start_recs.get("ERRATA_9_BYTES", "0") or 0)
        start_err_sha = start_recs.get("ERRATA_9_SHA256", "")
        safe("RULINGS_PREFIX_OF_START_UNCHANGED", lambda: (sha256_bytes(rul_b[:start_rul_bytes]) == start_rul_sha, sha256_bytes(rul_b[:start_rul_bytes])), start_rul_sha)
        safe("RULINGS_NOT_TRUNCATED", lambda: (len(rul_b) >= start_rul_bytes, len(rul_b)), ">= %d" % start_rul_bytes)
        safe("ERRATA_9_PREFIX_OF_START_UNCHANGED", lambda: (sha256_bytes(err_b[:start_err_bytes]) == start_err_sha, sha256_bytes(err_b[:start_err_bytes])), start_err_sha)
        safe("ERRATA_9_NOT_TRUNCATED", lambda: (len(err_b) >= start_err_bytes, len(err_b)), ">= %d" % start_err_bytes)

        def c_fields_end():
            for line in rul_b.decode("utf-8", "replace").splitlines():
                if not line.strip() or line.strip().startswith("#"):
                    continue
                if len(line.split("\t")) != 5:
                    return False, "bad field count in: " + line[:40]
            return True, "all lines 5 fields"
        safe("RULINGS_LINES_5_FIELDS_END", c_fields_end, "all lines 5 fields")

        # historical registries identical to the base commit
        for tag in ["M1", "M1R2", "M1R3", "M1R4"]:
            def mkm(tag=tag):
                def f():
                    d = sh(["git", "diff", EXPECTED_BASE, "--", "checkpoints/p05/registries/s4r9/" + tag])
                    return d == "", ("identical" if not d else d[:200])
                return f
            safe("HIST_REGISTRY_" + tag + "_IDENTICAL_TO_BASE", mkm(), "identical")

        # STATE.md size
        st_p = os.path.join(REPO, "checkpoints/p05/STATE.md")
        st_b = open(st_p, "rb").read() if os.path.isfile(st_p) else b""
        safe("STATE_BYTES_LE_8192", lambda: (len(st_b) <= 8192, len(st_b)), "<= 8192")

        # build/ unchanged vs baseline, no *.so in root
        def c_build_unchanged():
            base_p = os.path.join(ev_dir, "BUILD_BASELINE_R9M3A.tsv")
            if not os.path.isfile(base_p):
                return False, "missing BUILD_BASELINE_R9M3A.tsv"
            base = {}
            for line in open(base_p, encoding="utf-8"):
                if not line.strip() or line.startswith("#") or line.startswith("relpath\t"):
                    continue
                rel, size, mt, h = line.rstrip("\n").split("\t")
                base[rel] = (int(size), int(mt), h)
            now = build_manifest()
            if set(now) != set(base):
                return False, "item set differs: +%s -%s" % (sorted(set(now) - set(base))[:3], sorted(set(base) - set(now))[:3])
            diff = [k for k in base if base[k] != now[k]]
            return len(diff) == 0, ("identical (%d items)" % len(base) if not diff else str(diff[:3]))
        safe("ROOT_BUILD_UNCHANGED_VS_BASELINE", c_build_unchanged, "identical")

        def c_root_so():
            sos = [f for f in os.listdir(REPO) if f.endswith(".so")]
            return len(sos) == 0, ("no *.so" if not sos else str(sos))
        safe("ROOT_NO_NEW_SO_AT_END", c_root_so, "no *.so")

        # (i) commit and the POST_I block
        commit_i = commit_i_override
        if not commit_i:
            try:
                commit_i = sh(["git", "log", "--grep=R9 M3a (i)", "-1", "--format=%H"])
            except Exception:
                commit_i = ""
        if commit_i == "HEAD":
            commit_i_sha = sh(["git", "rev-parse", "HEAD"])
        else:
            commit_i_sha = commit_i
        safe("COMMIT_I_PRESENT", lambda: (bool(commit_i_sha), commit_i_sha if commit_i_sha else "missing"), "commit (i) found")
        record("COMMIT_I_SHA", commit_i_sha)
        record("COMMIT_I_OVERRIDE", "yes" if commit_i_override else "no")

        log_recs = parse_log(ev_dir)
        record("LOG_RECORDS", len(log_recs))
        commit_i_epoch = 0
        if commit_i_sha:
            try:
                commit_i_epoch = int(sh(["git", "log", "-1", "--format=%ct", commit_i_sha]))
            except Exception:
                commit_i_epoch = 0
        record("COMMIT_I_EPOCH", commit_i_epoch)

        post_i = [(i, ts, cmd) for (i, ts, cmd) in log_recs if (commit_i_override is not None or log_epoch(ts) >= commit_i_epoch)]
        record("POST_I_LOG_RECORDS", len(post_i))

        # item 1: frozen script call counts
        for key, rel, word in POST_I_SCRIPTS:
            def mkc(rel=rel, word=word, key=key):
                def f():
                    hits = count_script_calls(post_i, rel, word, 0)
                    record("CALL_LINES_" + key, ",".join(str(h) for h in hits))
                    return len(hits) == 1, len(hits)
                return f
            safe("POST_I_CALL_COUNT_" + key + "_EQ_1", mkc(), 1)

        # item 2: no writes under testing/d003 after (i)
        def c_no_d003_writes():
            bad = []
            for (i, ts, cmd) in post_i:
                if re.search(r"open\(['\"]testing/d003/", cmd) or re.search(r">\s*testing/d003/", cmd):
                    bad.append((i, cmd[:80]))
            return len(bad) == 0, (len(bad) if not bad else str(bad[:4]))
        safe("POST_I_NO_TESTING_D003_WRITES", c_no_d003_writes, 0)

        # item 3: frozen list unchanged
        frozen_p = os.path.join(ev_dir, "FROZEN_SCRIPTS_R9M3A.tsv")
        if not os.path.isfile(frozen_p):
            frozen_p = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3a/FROZEN_SCRIPTS_R9M3A.tsv")
        def c_frozen():
            if not os.path.isfile(frozen_p):
                return False, "missing FROZEN_SCRIPTS_R9M3A.tsv"
            bad = []
            n = 0
            for line in open(frozen_p, encoding="utf-8"):
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("path\t"):
                    continue
                parts = line.split("\t")
                if len(parts) < 2:
                    continue
                n += 1
                rel, exp = parts[0], parts[1]
                fp = rel if os.path.isabs(rel) else os.path.join(REPO, rel)
                if not os.path.isfile(fp):
                    bad.append("missing: " + rel)
                elif sha256_file(fp) != exp:
                    bad.append("sha: " + rel)
            record("FROZEN_ITEMS", n)
            return len(bad) == 0, ("all %d frozen OK" % n if not bad else str(bad[:5]))
        safe("FROZEN_SCRIPTS_SHA_UNCHANGED_END", c_frozen, "all frozen OK")

        # item 4: no modification of files committed at (i)
        def c_committed_i():
            if not commit_i_sha:
                return False, "no commit (i)"
            head_diff = sh(["git", "diff", "--name-only", "--diff-filter=M", commit_i_sha, "HEAD", "--", "testing/d003", "checkpoints/p05/briefs", "checkpoints/p05/registries"]).splitlines()
            wt_diff = sh(["git", "diff", "--name-only", commit_i_sha, "--", "testing/d003", "checkpoints/p05/briefs", "checkpoints/p05/registries"]).splitlines()
            allow = ("checkpoints/p05/registries/RULINGS.tsv", "checkpoints/p05/registries/s4r9/ERRATA_9.txt")
            bad = [f for f in set(head_diff) | set(wt_diff) if f.strip() not in allow]
            return len(bad) == 0, ("unmodified" if not bad else str(sorted(bad)[:6]))
        safe("COMMITTED_I_FILES_UNCHANGED_AT_END", c_committed_i, "unmodified")

        # item 5: EVENTS row set equals recomputation up to the last events call line after (i)
        ev_p = os.path.join(ev_dir, "EVENTS_R9M3A.tsv")
        if not os.path.isfile(ev_p):
            ev_p = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3a/EVENTS_R9M3A.tsv")
        def c_events():
            ev_hits = count_script_calls(post_i, "testing/d003/stage_s4r9/events_r9m3a.py", "", 0)
            if not ev_hits:
                return False, "no events_r9m3a.py call after (i)"
            anchor = max(ev_hits)
            record("EVENTS_ANCHOR_LINE", anchor)
            if not os.path.isfile(ev_p):
                return False, "missing EVENTS_R9M3A.tsv"
            rows = {}
            for line in open(ev_p, encoding="utf-8"):
                if not line.strip() or line.startswith("#") or line.startswith("log_line\t"):
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 2:
                    continue
                rows[int(parts[0])] = parts[1]
            expect = {i: ts for (i, ts, cmd) in log_recs if i <= anchor}
            if set(rows) != set(expect):
                miss = sorted(set(expect) - set(rows))[:5]
                extra = sorted(set(rows) - set(expect))[:5]
                return False, "row set differs missing=%s extra=%s" % (miss, extra)
            diff = [i for i in expect if rows[i] != expect[i]]
            record("EVENTS_ROWS", len(rows))
            return len(diff) == 0, ("rows=%d anchor=%d all timestamps match" % (len(rows), anchor) if not diff else "timestamp mismatch at %s" % diff[:5])
        safe("EVENTS_ROW_SET_EQ_RECOMPUTATION", c_events, "row set equals recomputation")

        # item 6: evidence SHA256SUMS all OK, truncation line == sha_sums call line, hash correct
        def c_ev_sums():
            sums_p = os.path.join(ev_dir, "SHA256SUMS.txt")
            if not os.path.isfile(sums_p):
                return False, "missing evidence SHA256SUMS.txt"
            lines = open(sums_p, encoding="utf-8").read().splitlines()
            if len(lines) < 2:
                return False, "SHA256SUMS.txt too short"
            m = re.search(r"up to line (\d+):\s*([0-9a-f]{64})", lines[1])
            if not m:
                return False, "no truncation header: " + lines[1][:80]
            trunc_line, trunc_sha = int(m.group(1)), m.group(2)
            ss_hits = count_script_calls(post_i, "testing/d003/stage_s4r9/sha_sums_r9m3a.py", "", 0)
            if not ss_hits:
                return False, "no sha_sums_r9m3a.py call after (i)"
            anchor = max(ss_hits)
            record("SHA_SUMS_ANCHOR_LINE", anchor)
            if trunc_line != anchor:
                return False, "trunc_line %d != sha_sums call line %d" % (trunc_line, anchor)
            log_text = "\n".join(open(os.path.join(ev_dir, "safe_run.log"), encoding="utf-8", errors="replace").read().splitlines()[:trunc_line]) + "\n"
            actual = sha256_bytes(log_text.encode("utf-8"))
            if actual != trunc_sha:
                return False, "truncated log hash mismatch: %s" % actual
            ok, cnt, det = verify_sums_dir(ev_dir)
            if not ok:
                return False, det
            record("EVIDENCE_SUMS_ITEMS", cnt)
            return True, "trunc line %d %s ok, %d items OK" % (trunc_line, trunc_sha[:8], cnt)
        safe("EVIDENCE_SHA256SUMS_OK", c_ev_sums, "all OK")

        # item 7: UNLOGGED_SELF == 0
        def c_unlogged():
            start_ep = log_epoch(start_recs.get("START_TIME_UTC", "")) if start_recs.get("START_TIME_UTC") else 0
            log_text = open(os.path.join(ev_dir, "safe_run.log"), encoding="utf-8", errors="replace").read() if os.path.isfile(os.path.join(ev_dir, "safe_run.log")) else ""
            bad = []
            for rel, mt in sorted(scan_repo_reported_files().items()):
                if start_ep and mt >= start_ep:
                    if rel not in log_text and os.path.basename(rel) not in log_text:
                        bad.append(rel)
            record("UNLOGGED_SELF", len(bad))
            return len(bad) == 0, (len(bad) if not bad else str(bad[:8]))
        safe("UNLOGGED_SELF_ZERO", c_unlogged, 0)

        # item 8: other rounds' evidence dirs untouched after the start gate
        def c_other_ev():
            start_ep = log_epoch(start_recs.get("START_TIME_UTC", "")) if start_recs.get("START_TIME_UTC") else 0
            bad = []
            for r in OTHER_ROUND_EV:
                p = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9", r)
                if not os.path.isdir(p):
                    continue
                for root, dirs, files in os.walk(p):
                    for f in files:
                        fp = os.path.join(root, f)
                        if start_ep and int(os.path.getmtime(fp)) > start_ep:
                            bad.append(os.path.relpath(fp, REPO))
            return len(bad) == 0, ("none" if not bad else str(bad[:6]))
        safe("OTHER_ROUND_EVIDENCE_UNTOUCHED", c_other_ev, "none")

        # item 11: registries M3a sums OK and item count equals the report deliverable count
        def c_m3a_reg():
            d = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3a")
            ok, cnt, det = verify_sums_dir(d)
            if not ok:
                return False, det
            rep = os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3a_REPORT.md")
            if not os.path.isfile(rep):
                return False, "missing report"
            text = open(rep, encoding="utf-8").read()
            m = re.search(r"###\s*10\.1[^\n]*\n(.*?)(?:\n###|\n##|$)", text, re.S)
            if not m:
                return False, "cannot parse report section 10.1"
            items = re.findall(r"^\s*\d+\.\s+([A-Za-z0-9_.\-]+)\s*$", m.group(1), re.M)
            record("REPORT_DELIVERABLES", len(items))
            record("REGISTRY_M3A_ITEMS", cnt)
            if not items:
                return False, "no numbered deliverables parsed"
            if cnt != len(items) - 1:
                return False, "sums items %d != report items-1 %d" % (cnt, len(items) - 1)
            if items[-1] != "SHA256SUMS.txt":
                return False, "last report item is not SHA256SUMS.txt: " + items[-1]
            return True, "sums %d items OK, report lists %d (incl SHA256SUMS.txt)" % (cnt, len(items))
        safe("REGISTRIES_M3A_SUMS_ALL_OK", c_m3a_reg, "all OK matching report")

        # item 12/13 already above (build, so, tmp)

    # ---------- write output ----------
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_lines = ["# P05-S4 R9 M3a gate_check (%s) %s" % (mode, os.path.basename(out_file))]
    for k, v in records:
        out_lines.append("RECORD\t%s\tvalue=%s" % (k, v))
    for st, name, exp, act in results:
        out_lines.append("%s\t%s\texpected=%s\tactual=%s" % (st, name, exp, act))
    out_lines.append("COUNTS\tpass=%d\tfail=%d\ttotal=%d" % (sum(1 for r in results if r[0] == "PASS"), fails, len(results)))
    out_lines.append("FAILS=%d" % fails)
    body = "\n".join(out_lines) + "\n"
    d = os.path.dirname(os.path.abspath(out_file))
    if d:
        os.makedirs(d, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as fh:
        fh.write(body)
    sys.stdout.write(body)
    sys.stdout.flush()
    return min(fails, 255)


def record_map_get(*a):
    return "0"


if __name__ == "__main__":
    REPO = sh(["git", "rev-parse", "--show-toplevel"])
    sys.exit(main())
