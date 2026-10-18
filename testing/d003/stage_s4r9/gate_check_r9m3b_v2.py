#!/usr/bin/env python3
# gate_check_r9m3b.py -- P05-S4 R9 M3b gate helper (new file, r9m3b).
# Modes: start | start_recheck | end.
# Opening baseline HEAD: 6aa11d8b2eb3bea896406842c30eda742af19080
# Every check is wrapped so that an exception becomes a CHECK_CRASHED FAIL line; the FAIL count is also the exit status.
import os, sys, re, hashlib, subprocess, datetime, fnmatch

ROUND_TAG = "r9m3b"
EXPECTED_BASE = "6aa11d8b2eb3bea896406842c30eda742af19080"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECTED_S4_TREE_F4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXPECTED_S4_TREE_F3 = "6cff923a02baf19e01966b2339755cbf3a5deeef"
EXPECTED_F2_TREE = "e124925f5b242486a913b813fa181664f665b048"
EXPECTED_B_TREE = "1d738e64f9864a475fdb3de34cd3601605df2c64"
EXPECTED_BRANCH = "codex/p05-d003-fft-error-propagation"
STATE_BYTES_START = 5191
STATE_SHA_START = "7ae31ae099345433f348369eb3b8cd29e611de73a0f660d384a07e4f274025d1"
RULINGS_BYTES_START = 136951
RULINGS_SHA_START = "579b73c9d8952c3465d7402231b167d09d5eb087dd5519d6b0cefbffbf089951"
RULINGS_MAX_U_START = "U333"
ERRATA_9_BYTES_START = 38912
ERRATA_9_SHA_START = "d5d8d9a0f46086df6855cb4637b035a641b327dd2f95fff1773002b9fbdc49ee"
ERRATA_9_LAST_E_START = "E9-45"
ERRATA_9_COUNT_START = 45
M3A_SUMS_SHA = "1fdf80ac147a3aa7f29ea899433d13513ef8c0816e4d83878c89c2093899d3d8"
M3A_SUMS_ITEMS = 17
M3A_PREREG_SHA = "88f020705cc4ab55b56baeabbcff4c53d111e281afac3a6b7babf42513de5b9e"
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
    ("M3a", "checkpoints/p05/registries/s4r9/M3a"),
]
IDENTICAL_TO_BASE = ["M1", "M1R2", "M1R3", "M1R4", "M3a"]
S3R5_ARTIFACTS = [
    ("lib_F4_dbg", "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_dbg/libS4.a", "6a711fbbec84d1fb322ee1d9c678ae6750a04f647e3f1eba7840c8c7502fae26"),
    ("lib_F4_san", "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_san/libS4.a", "ce057b5065bb5ac487d66992930991c1f09f17431abfc957777f375436be0fbd"),
    ("lib_F4_plain", "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_plain/libS4.a", "5a4bfa601bf14b896b9c0c25807c0a38c05d040a17268cf0669902763cda5757"),
    ("init-F4-dbg", "checkpoints/p05/evidence/p05-s3r5/build/init-F4-dbg", "a4643e7e67ad74019104466ff9773ec2cfc1e684e488705a16a4a8f32526aca2"),
    ("init-F4-san", "checkpoints/p05/evidence/p05-s3r5/build/init-F4-san", "33a230029df224ddecb64f0884833e7e20251c461f0459ce315122d5987666c3"),
    ("init-F4-san-AL", "checkpoints/p05/evidence/p05-s3r5/build/init-F4-san-AL", "f14c536ea54d81348dd4f53f36c5c2eba65c0ca15fdb16160b8296186d7f5f8e"),
    ("init-B-dbg", "checkpoints/p05/evidence/p05-s4r8/m2c/build/init-B-dbg", "3ccc2897fae2ce293d3c656e2a334dad05e53fe7f622b749a71e19bfd021b0b8"),
]
OTHER_ROUND_EV = ["m0", "m1", "m1r2", "m1r3", "m1r4", "m2", "m2b", "m2c", "m3a"]
REPORT = "checkpoints/p05/P05_S4R9_M3b_REPORT.md"
ALLOWED_MODIFIED_AT_END = [REPORT, "checkpoints/p05/STATE.md"]
LOG_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")
BT = chr(96)

REPO = os.getcwd()


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
    for line in open(sums_path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            out.append((parts[0], parts[1].strip()))
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
    for line in open(start_file, encoding="utf-8"):
        parts = line.rstrip("\r\n").split("\t")
        if len(parts) >= 3 and parts[0] == "RECORD":
            val = parts[2]
            if val.startswith("value="):
                val = val[6:]
            recs[parts[1]] = val
    return recs


def parse_log(ev_dir):
    path = os.path.join(ev_dir, "safe_run.log")
    recs = []
    if not os.path.isfile(path):
        return recs
    for idx, line in enumerate(open(path, encoding="utf-8", errors="replace"), 1):
        m = LOG_TS_RE.match(line)
        if not m:
            continue
        cmd = ""
        for p in line.rstrip("\n").split("\t")[1:]:
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
    head = cmd.strip()
    if not re.match(r"^(?:python3|sh)\b", head):
        return False
    toks = head.split()
    if relpath not in toks:
        return False
    if mode_word and mode_word != "-":
        return mode_word in toks
    return True


def count_script_calls(log_recs, relpath, mode_word, min_epoch):
    return [idx for idx, ts, cmd in log_recs if log_epoch(ts) >= min_epoch and is_script_call(cmd, relpath, mode_word)]


def scan_repo_reported_files():
    out = {}
    for target in [os.path.join(REPO, "testing", "d003", "stage_s4r9"), os.path.join(REPO, "checkpoints", "p05")]:
        for root, dirs, files in os.walk(target):
            if "evidence" in root.split(os.sep):
                continue
            for f in files:
                fp = os.path.join(root, f)
                out[os.path.relpath(fp, REPO)] = int(os.path.getmtime(fp))
    return out


def build_manifest():
    out = {}
    bdir = os.path.join(REPO, "build")
    if os.path.isdir(bdir):
        for root, dirs, files in os.walk(bdir):
            for f in files:
                fp = os.path.join(root, f)
                st = os.stat(fp)
                out[os.path.relpath(fp, REPO)] = (st.st_size, int(st.st_mtime), sha256_file(fp))
    return out


def tmp_snapshot():
    root = os.sep + "tmp"
    entries = sorted(os.listdir(root)) if os.path.isdir(root) else []
    payload = "\n".join(entries) + ("\n" if entries else "")
    return len(entries), hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_frozen(ev_dir):
    p = os.path.join(ev_dir, "FROZEN_SCRIPTS_R9M3B.tsv")
    rows = []
    if not os.path.isfile(p):
        return rows
    for line in open(p, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.strip() or line.startswith("#") or line.startswith("path" + chr(9)):
            continue
        f = line.split(chr(9))
        if len(f) < 2:
            continue
        rows.append({"path": f[0], "sha256": f[1],
                     "expect": f[2] if len(f) > 2 else "1",
                     "mode": f[3] if len(f) > 3 else "-"})
    return rows


def read_tsv(path):
    rows = []
    if not os.path.isfile(path):
        return rows
    hdr = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(chr(9))
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


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
        try:
            ok, act = fn()
            check(name, ok, exp, act)
        except Exception as exc:
            check(name, False, exp, "CHECK_CRASHED: %s: %s" % (type(exc).__name__, exc))

    def record(name, val):
        records.append((name, str(val)))

    def c_branch():
        b = sh(["git", "branch", "--show-current"])
        return b == EXPECTED_BRANCH, b
    safe("BRANCH_IS_EXPECTED", c_branch, EXPECTED_BRANCH)

    def c_head_start():
        h = sh(["git", "rev-parse", "HEAD"])
        record("HEAD", h)
        return h == EXPECTED_BASE, h
    if mode == "start":
        safe("HEAD_IS_BASE", c_head_start, EXPECTED_BASE)

    def c_head_present():
        h = sh(["git", "rev-parse", "HEAD"])
        record("HEAD", h)
        return len(h) == 40, h
    if mode != "start":
        safe("HEAD_PRESENT", c_head_present, "40-hex sha")

    def c_s4():
        t = sh(["git", "rev-parse", "HEAD:S4"])
        record("HEAD_S4", t)
        return t == EXPECTED_S4_TREE_F4, t
    safe("HEAD_S4_TREE_EQ_F4", c_s4, EXPECTED_S4_TREE_F4)

    def mk_tree(rev, exp):
        def f():
            t = sh(["git", "rev-parse", rev + ":S4"])
            return t == exp, t
        return f
    safe("F3_8d8202a_S4_TREE", mk_tree("8d8202a", EXPECTED_S4_TREE_F3), EXPECTED_S4_TREE_F3)
    safe("F2_a07b5ac_S4_TREE", mk_tree("a07b5ac", EXPECTED_F2_TREE), EXPECTED_F2_TREE)
    safe("B_37a82e8_S4_TREE", mk_tree("37a82e8", EXPECTED_B_TREE), EXPECTED_B_TREE)

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

    def c_m3a_sums_sha():
        p = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3a/SHA256SUMS.txt")
        a = sha256_file(p) if os.path.isfile(p) else "missing"
        return a == M3A_SUMS_SHA, a
    safe("M3A_SUMS_SHA256", c_m3a_sums_sha, M3A_SUMS_SHA)
    check("M3A_SUMS_ITEM_COUNT", int(records[-1][1]) == M3A_SUMS_ITEMS if records and records[-1][0] == "REGISTRY_COUNT_M3a" else False,
          M3A_SUMS_ITEMS, records[-1][1] if records and records[-1][0] == "REGISTRY_COUNT_M3a" else "?")

    def c_m3a_prereg():
        p = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3a/PREREG_E2E_R9M3A.tsv")
        a = sha256_file(p) if os.path.isfile(p) else "missing"
        return a == M3A_PREREG_SHA, a
    safe("M3A_PREREG_E2E_SHA256", c_m3a_prereg, M3A_PREREG_SHA)

    def c_s4_zero():
        d = sh(["git", "diff", "HEAD", "--", "S4"])
        return d == "", (d if d else "S4 unmodified")
    safe("S4_DIR_ZERO_MODIFICATION", c_s4_zero, "S4 unmodified")

    tmp_count, tmp_sha = 0, ""
    def c_tmp():
        nonlocal tmp_count, tmp_sha
        tmp_count, tmp_sha = tmp_snapshot()
        return True, "count=%d sha=%s" % (tmp_count, tmp_sha)
    safe("TMP_SNAPSHOT_READ", c_tmp, "snapshot read")

    allstatus = os.path.join(ev_dir, "ALL_STATUS_R9M3B_%s.txt" % mode)
    def c_write_status():
        os.makedirs(ev_dir, exist_ok=True)
        with open(allstatus, "w", encoding="utf-8") as fh:
            fh.write(sh(["git", "status", "--short", "-uall"]) + "\n")
            fh.write("BRANCH\t" + sh(["git", "branch", "--show-current"]) + "\n")
            fh.write("HEAD\t" + sh(["git", "rev-parse", "HEAD"]) + "\n")
        return os.path.isfile(allstatus), "written"
    safe("STATUS_ARTIFACT_WRITTEN", c_write_status, "written")

    rul_p = os.path.join(REPO, "checkpoints/p05/registries/RULINGS.tsv")
    err_p = os.path.join(REPO, "checkpoints/p05/registries/s4r9/ERRATA_9.txt")
    st_p = os.path.join(REPO, "checkpoints/p05/STATE.md")

    if mode == "start":
        record("START_TIME_UTC", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
        record("TMP_COUNT", tmp_count)
        record("TMP_SHA256", tmp_sha)
        rul_b = open(rul_p, "rb").read() if os.path.isfile(rul_p) else b""
        err_b = open(err_p, "rb").read() if os.path.isfile(err_p) else b""
        st_b = open(st_p, "rb").read() if os.path.isfile(st_p) else b""
        record("RULINGS_BYTES", len(rul_b))
        record("RULINGS_SHA256", sha256_bytes(rul_b))
        record("ERRATA_9_BYTES", len(err_b))
        record("ERRATA_9_SHA256", sha256_bytes(err_b))
        record("STATE_BYTES", len(st_b))
        safe("RULINGS_START_BYTES", lambda: (len(rul_b) == RULINGS_BYTES_START, len(rul_b)), RULINGS_BYTES_START)
        safe("RULINGS_START_SHA256", lambda: (sha256_bytes(rul_b) == RULINGS_SHA_START, sha256_bytes(rul_b)), RULINGS_SHA_START)

        def c_max_u():
            nums = []
            for line in rul_b.decode("utf-8", "replace").splitlines():
                f = line.split("\t")[0]
                if f.startswith("U") and f[1:].isdigit():
                    nums.append(int(f[1:]))
            return ("U%d" % max(nums)) == RULINGS_MAX_U_START if nums else False, ("U%d" % max(nums) if nums else "none")
        safe("RULINGS_START_MAX_U", c_max_u, RULINGS_MAX_U_START)

        def c_rul_fields():
            for line in rul_b.decode("utf-8", "replace").splitlines():
                if not line.strip() or line.strip().startswith("#"):
                    continue
                if len(line.split("\t")) != 5:
                    return False, "bad field count in: " + line[:40]
            return True, "all lines 5 fields"
        safe("RULINGS_LINES_5_FIELDS", c_rul_fields, "all lines 5 fields")

        safe("ERRATA_9_START_BYTES", lambda: (len(err_b) == ERRATA_9_BYTES_START, len(err_b)), ERRATA_9_BYTES_START)
        safe("ERRATA_9_START_SHA256", lambda: (sha256_bytes(err_b) == ERRATA_9_SHA_START, sha256_bytes(err_b)), ERRATA_9_SHA_START)

        def c_last_e():
            ids = re.findall(r"^(E9-\d+)", err_b.decode("utf-8", "replace"), re.M)
            record("ERRATA_9_COUNT", len(ids))
            return (ids[-1] if ids else "none") == ERRATA_9_LAST_E_START, (ids[-1] if ids else "none")
        safe("ERRATA_9_START_LAST_E", c_last_e, ERRATA_9_LAST_E_START)
        check("ERRATA_9_START_COUNT", int(records[-1][1]) == ERRATA_9_COUNT_START if records and records[-1][0] == "ERRATA_9_COUNT" else False,
              ERRATA_9_COUNT_START, records[-1][1] if records and records[-1][0] == "ERRATA_9_COUNT" else "?")
        safe("STATE_START_BYTES", lambda: (len(st_b) == STATE_BYTES_START, len(st_b)), STATE_BYTES_START)
        safe("STATE_START_SHA256", lambda: (sha256_bytes(st_b) == STATE_SHA_START, sha256_bytes(st_b)), STATE_SHA_START)

        def c_allow():
            allow_p = os.path.join(REPO, "testing/d003/stage_s4r9/gate_allow_r9m3b_start.txt")
            pats = [l.strip() for l in open(allow_p, encoding="utf-8") if l.strip() and not l.strip().startswith("#")]
            st = sh(["git", "status", "--short", "-uall"]).splitlines()
            bad = [line for line in st if line.strip() and not any(fnmatch.fnmatch(line.rstrip(), p) for p in pats)]
            record("GIT_STATUS_LINES", len([l for l in st if l.strip()]))
            return len(bad) == 0, ("all entries within round allow list" if not bad else str(bad[:6]))
        safe("GIT_STATUS_WITHIN_ROUND_ALLOW_LIST", c_allow, "all entries within round allow list")

        def c_no_tracked_mods():
            d = sh(["git", "diff", "HEAD", "--name-only"])
            return d == "", (d if d else "no tracked modification")
        safe("GIT_TRACKED_NO_MODIFICATION", c_no_tracked_mods, "no tracked modification")

        def c_root_so():
            sos = [f for f in os.listdir(REPO) if f.endswith(".so")]
            return len(sos) == 0, ("no *.so" if not sos else str(sos))
        safe("ROOT_NO_SO_AT_START", c_root_so, "no *.so")

        bpath = os.path.join(ev_dir, "BUILD_BASELINE_R9M3B.tsv")
        def c_build_baseline():
            man = build_manifest()
            with open(bpath, "w", encoding="utf-8") as fh:
                fh.write("# BUILD_BASELINE_R9M3B.tsv -- repository-root build/ manifest at the start gate" + chr(10))
                fh.write("relpath\tsize\tmtime\tsha256" + chr(10))
                for k in sorted(man):
                    s, mt, h = man[k]
                    fh.write("%s\t%d\t%d\t%s\n" % (k, s, mt, h))
            record("BUILD_BASELINE_ITEMS", len(man))
            return os.path.isfile(bpath), "items=%d" % len(man)
        safe("BUILD_BASELINE_SAVED", c_build_baseline, "saved")

        sbpath = os.path.join(ev_dir, "STRAY_BASELINE_R9M3B.tsv")
        def c_stray():
            rows = []
            for root, dirs, files in os.walk(os.path.join(REPO, "testing", "d003")):
                for f in files:
                    if f.endswith(".pyc") or f.endswith(".o"):
                        fp = os.path.join(root, f)
                        stt = os.stat(fp)
                        rows.append((os.path.relpath(fp, REPO), stt.st_size, int(stt.st_mtime), sha256_file(fp)))
            with open(sbpath, "w", encoding="utf-8") as fh:
                fh.write("# STRAY_BASELINE_R9M3B.tsv -- stray build products under testing/d003 at the start gate" + chr(10))
                fh.write("relpath\tsize\tmtime\tsha256" + chr(10))
                for r in sorted(rows):
                    fh.write("%s\t%d\t%d\t%s\n" % r)
            return True, "items=%d" % len(rows)
        safe("STRAY_BASELINE_SAVED", c_stray, "saved")

    elif mode == "start_recheck":
        recs = parse_start_records(start_file)
        safe("START_RECORDS_PRESENT", lambda: (len(recs) > 0, "%d records" % len(recs) if recs else "missing"), "records present")
        rul_b = open(rul_p, "rb").read() if os.path.isfile(rul_p) else b""
        err_b = open(err_p, "rb").read() if os.path.isfile(err_p) else b""
        rb = int(recs.get("RULINGS_BYTES", "0") or 0)
        rs = recs.get("RULINGS_SHA256", "")
        eb = int(recs.get("ERRATA_9_BYTES", "0") or 0)
        es = recs.get("ERRATA_9_SHA256", "")
        record("RULINGS_BYTES_NOW", len(rul_b))
        record("ERRATA_9_BYTES_NOW", len(err_b))
        safe("RULINGS_PREFIX_OF_START_UNCHANGED", lambda: (sha256_bytes(rul_b[:rb]) == rs, sha256_bytes(rul_b[:rb])), rs)
        safe("RULINGS_NOT_TRUNCATED", lambda: (len(rul_b) >= rb, len(rul_b)), ">= %d" % rb)
        safe("ERRATA_9_PREFIX_OF_START_UNCHANGED", lambda: (sha256_bytes(err_b[:eb]) == es, sha256_bytes(err_b[:eb])), es)
        safe("ERRATA_9_NOT_TRUNCATED", lambda: (len(err_b) >= eb, len(err_b)), ">= %d" % eb)
        # no modification of any committed file other than the append-only pair
        def c_committed():
            d = sh(["git", "diff", "--name-only", EXPECTED_BASE])
            allow = ("checkpoints/p05/STATE.md", "checkpoints/p05/registries/RULINGS.tsv",
                     "checkpoints/p05/registries/s4r9/ERRATA_9.txt")
            bad = [f for f in d.splitlines() if f.strip() and f.strip() not in allow]
            return len(bad) == 0, ("only allowed files modified" if not bad else str(bad[:6]))
        safe("TRACKED_MODIFIED_ONLY_ALLOWED", c_committed, "only allowed files modified")

    else:
        # ================= END MODE =================
        start_recs = parse_start_records(start_file)
        safe("START_RECORDS_PRESENT", lambda: (len(start_recs) > 0, "%d records" % len(start_recs) if start_recs else "missing"), "records present")
        start_tmp_count = int(start_recs.get("TMP_COUNT", "-1") or -1)
        start_tmp_sha = start_recs.get("TMP_SHA256", "")
        safe("TMP_COUNT_MATCHES_START", lambda: (tmp_count == start_tmp_count, tmp_count), start_tmp_count)
        safe("TMP_SHA_MATCHES_START", lambda: (tmp_sha == start_tmp_sha, tmp_sha), start_tmp_sha)

        rul_b = open(rul_p, "rb").read() if os.path.isfile(rul_p) else b""
        err_b = open(err_p, "rb").read() if os.path.isfile(err_p) else b""
        rb = int(start_recs.get("RULINGS_BYTES", "0") or 0)
        rs = start_recs.get("RULINGS_SHA256", "")
        eb = int(start_recs.get("ERRATA_9_BYTES", "0") or 0)
        es = start_recs.get("ERRATA_9_SHA256", "")
        safe("RULINGS_PREFIX_OF_START_UNCHANGED", lambda: (sha256_bytes(rul_b[:rb]) == rs, sha256_bytes(rul_b[:rb])), rs)
        safe("RULINGS_NOT_TRUNCATED", lambda: (len(rul_b) >= rb, len(rul_b)), ">= %d" % rb)
        safe("ERRATA_9_PREFIX_OF_START_UNCHANGED", lambda: (sha256_bytes(err_b[:eb]) == es, sha256_bytes(err_b[:eb])), es)
        safe("ERRATA_9_NOT_TRUNCATED", lambda: (len(err_b) >= eb, len(err_b)), ">= %d" % eb)

        def c_fields_end():
            for line in rul_b.decode("utf-8", "replace").splitlines():
                if not line.strip() or line.strip().startswith("#"):
                    continue
                if len(line.split("\t")) != 5:
                    return False, "bad field count in: " + line[:40]
            return True, "all lines 5 fields"
        safe("RULINGS_LINES_5_FIELDS_END", c_fields_end, "all lines 5 fields")

        for tag in IDENTICAL_TO_BASE:
            def mkm(tag=tag):
                def f():
                    d = sh(["git", "diff", EXPECTED_BASE, "--", "checkpoints/p05/registries/s4r9/" + tag])
                    return d == "", ("identical" if not d else d[:200])
                return f
            safe("HIST_REGISTRY_" + tag + "_IDENTICAL_TO_BASE", mkm(), "identical")

        def c_m3a_files():
            d = sh(["git", "diff", EXPECTED_BASE, "--", "checkpoints/p05/P05_S4R9_M3a_REPORT.md",
                    "checkpoints/p05/briefs/P05_S4R9_BRIEF_M3a.md", "checkpoints/p05/registries/s4r9/M3a"])
            return d == "", ("identical" if not d else d[:200])
        safe("M3A_COMMITTED_FILES_UNCHANGED", c_m3a_files, "identical")

        def c_mod():
            d = sh(["git", "diff", "--name-only", "HEAD"]).splitlines()
            bad = [f for f in d if f.strip() and f.strip() not in ALLOWED_MODIFIED_AT_END]
            return len(bad) == 0, ("only the report and STATE modified" if not bad else str(bad[:6]))
        safe("MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST", c_mod, "only the report and STATE modified")

        st_b = open(st_p, "rb").read() if os.path.isfile(st_p) else b""
        safe("STATE_BYTES_LE_8192", lambda: (len(st_b) <= 8192, len(st_b)), "<= 8192")

        def c_build_unchanged():
            base_p = os.path.join(ev_dir, "BUILD_BASELINE_R9M3B.tsv")
            if not os.path.isfile(base_p):
                return False, "missing BUILD_BASELINE_R9M3B.tsv"
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

        commit_i = commit_i_override
        if not commit_i:
            try:
                commit_i = sh(["git", "log", "--grep=R9 M3b (i)", "-1", "--format=%H"])
            except Exception:
                commit_i = ""
        commit_i_sha = sh(["git", "rev-parse", "HEAD"]) if commit_i == "HEAD" else commit_i
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
        post_i = [(i2, ts, cmd) for (i2, ts, cmd) in log_recs if (commit_i_override is not None or log_epoch(ts) >= commit_i_epoch)]
        record("POST_I_LOG_RECORDS", len(post_i))

        frozen = read_frozen(ev_dir)
        record("FROZEN_ITEMS", len(frozen))
        safe("FROZEN_LIST_READ", lambda: (len(frozen) > 0, "%d rows" % len(frozen)), "rows")

        for row in frozen:
            rel = row["path"]
            key = os.path.basename(rel).replace(".py", "").replace(".sh", "").replace(".tsv", "").upper()
            key = key + "_" + row["mode"].upper()
            if row["expect"] == "0":
                continue
            def mkc(rel=rel, row=row, key=key):
                def f():
                    hits = count_script_calls(post_i, rel, row["mode"], 0)
                    record("CALL_LINES_" + key, ",".join(str(h) for h in hits))
                    if row["expect"] == ">=1":
                        return len(hits) >= 1, len(hits)
                    return len(hits) == int(row["expect"]), len(hits)
                return f
            safe("POST_I_CALL_COUNT_" + key + ("_GE_1" if row["expect"] == ">=1" else "_EQ_" + row["expect"]), mkc(),
                 ">=1" if row["expect"] == ">=1" else row["expect"])

        def c_no_d003_writes():
            bad = []
            for (i2, ts, cmd) in post_i:
                if re.search(r"open\(['\"]testing/d003/", cmd) or re.search(r">\s*testing/d003/", cmd):
                    bad.append((i2, cmd[:80]))
            return len(bad) == 0, (0 if not bad else str(bad[:4]))
        safe("POST_I_NO_TESTING_D003_WRITES", c_no_d003_writes, 0)

        def c_frozen():
            bad = []
            for row in frozen:
                fp = row["path"] if os.path.isabs(row["path"]) else os.path.join(REPO, row["path"])
                if not os.path.isfile(fp):
                    bad.append("missing: " + row["path"])
                elif sha256_file(fp) != row["sha256"]:
                    bad.append("sha: " + row["path"])
            return len(bad) == 0, ("all %d frozen OK" % len(frozen) if not bad else str(bad[:5]))
        safe("FROZEN_SCRIPTS_SHA_UNCHANGED_END", c_frozen, "all frozen OK")

        def c_committed_i():
            if not commit_i_sha:
                return False, "no commit (i)"
            head_diff = sh(["git", "diff", "--name-only", commit_i_sha, "HEAD", "--", "testing/d003",
                            "checkpoints/p05/briefs", "checkpoints/p05/registries"]).splitlines()
            wt_diff = sh(["git", "diff", "--name-only", commit_i_sha, "--", "testing/d003",
                          "checkpoints/p05/briefs", "checkpoints/p05/registries"]).splitlines()
            allow = ("checkpoints/p05/registries/RULINGS.tsv", "checkpoints/p05/registries/s4r9/ERRATA_9.txt")
            bad = [f for f in set(head_diff) | set(wt_diff) if f.strip() and f.strip() not in allow]
            return len(bad) == 0, ("unmodified" if not bad else str(sorted(bad)[:6]))
        safe("COMMITTED_I_FILES_UNCHANGED_AT_END", c_committed_i, "unmodified")

        ev_p = os.path.join(ev_dir, "EVENTS_R9M3B.tsv")
        def c_events():
            ev_hits = count_script_calls(post_i, "testing/d003/stage_s4r9/events_r9m3b.py", "-", 0)
            if not ev_hits:
                return False, "no events_r9m3b.py call after (i)"
            anchor = max(ev_hits)
            record("EVENTS_ANCHOR_LINE", anchor)
            if not os.path.isfile(ev_p):
                return False, "missing EVENTS_R9M3B.tsv"
            rows = {}
            for line in open(ev_p, encoding="utf-8"):
                if not line.strip() or line.startswith("#") or line.startswith("log_line\t"):
                    continue
                parts = line.rstrip("\n").split("\t")
                if len(parts) < 2:
                    continue
                rows[int(parts[0])] = parts[1]
            raw = open(os.path.join(ev_dir, "safe_run.log"), encoding="utf-8", errors="replace").read().splitlines()
            ts_of = {i2: ts for (i2, ts, cmd) in log_recs}
            expect = {}
            parent = ""
            for i2 in range(1, anchor + 1):
                if i2 > len(raw) or not raw[i2 - 1].strip():
                    continue
                if i2 in ts_of:
                    parent = ts_of[i2]
                expect[i2] = parent
            if set(rows) != set(expect):
                miss = sorted(set(expect) - set(rows))[:5]
                extra = sorted(set(rows) - set(expect))[:5]
                return False, "row set differs missing=%s extra=%s" % (miss, extra)
            diff = [i2 for i2 in expect if rows[i2] != expect[i2]]
            record("EVENTS_ROWS", len(rows))
            return len(diff) == 0, ("rows=%d anchor=%d all timestamps match" % (len(rows), anchor) if not diff else "timestamp mismatch at %s" % diff[:5])
        safe("EVENTS_ROW_SET_EQ_RECOMPUTATION", c_events, "row set equals recomputation")

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
            ss_hits = count_script_calls(post_i, "testing/d003/stage_s4r9/sha_sums_r9m3b.py", "-", 0)
            if not ss_hits:
                return False, "no sha_sums_r9m3b.py call after (i)"
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

        def c_unlogged():
            start_ep = log_epoch(start_recs.get("START_TIME_UTC", "")) if start_recs.get("START_TIME_UTC") else 0
            log_text = open(os.path.join(ev_dir, "safe_run.log"), encoding="utf-8", errors="replace").read() if os.path.isfile(os.path.join(ev_dir, "safe_run.log")) else ""
            declared = set()
            man = os.path.join(ev_dir, "REGISTRY_OUTPUTS_R9M3B.tsv")
            if os.path.isfile(man):
                for line in open(man, encoding="utf-8"):
                    if line.strip() and not line.startswith("#"):
                        declared.add(line.strip())
            bad = []
            for rel, mt in sorted(scan_repo_reported_files().items()):
                if start_ep and mt >= start_ep:
                    if rel in declared:
                        continue
                    if rel not in log_text and os.path.basename(rel) not in log_text:
                        bad.append(rel)
            record("UNLOGGED_SELF", len(bad))
            record("DECLARED_OUTPUTS", len(declared))
            return len(bad) == 0, (0 if not bad else str(bad[:8]))
        safe("UNLOGGED_SELF_ZERO", c_unlogged, 0)

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

        def c_reg():
            d = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3b")
            ok, cnt, det = verify_sums_dir(d)
            if not ok:
                return False, det
            rep = os.path.join(REPO, REPORT)
            if not os.path.isfile(rep):
                return False, "missing report"
            text = open(rep, encoding="utf-8").read()
            m = re.search(r"###\s*1[24]\.1[^\n]*\n(.*?)(?:\n###|\n##|$)", text, re.S)
            if not m:
                return False, "cannot parse report section 12.1"
            items = []
            for line in m.group(1).splitlines():
                mm = re.match(r"^\s*\d+\.\s+(.+?)\s*$", line)
                if mm:
                    items.append(mm.group(1).strip().strip(BT).strip())
            record("REPORT_DELIVERABLES", len(items))
            record("REGISTRY_M3B_ITEMS", cnt)
            if not items:
                return False, "no numbered deliverables parsed"
            if cnt != len(items) - 1:
                return False, "sums items %d != report items-1 %d" % (cnt, len(items) - 1)
            if items[-1] != "SHA256SUMS.txt":
                return False, "last report item is not SHA256SUMS.txt: " + items[-1]
            return True, "sums %d items OK, report lists %d (incl SHA256SUMS.txt)" % (cnt, len(items))
        safe("REGISTRIES_M3B_SUMS_ALL_OK", c_reg, "all OK matching report")

        def c_prereg_sha():
            p = os.path.join(ev_dir, "PREREG_E2E_R9M3B.tsv")
            s = os.path.join(ev_dir, "PREREG_E2E_R9M3B.sha256.txt")
            if not os.path.isfile(p) or not os.path.isfile(s):
                return False, "missing prereg or sha record"
            a = sha256_file(p)
            txt = open(s, encoding="utf-8").read()
            record("PREREG_SHA256", a)
            return (a in txt and "INFLUENCED" in txt and re.search(r"20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ", txt) is not None), "sha recorded"
        safe("PREREG_SHA_RECORDED", c_prereg_sha, "sha recorded")

        def c_prereg_order():
            p = os.path.join(ev_dir, "PREREG_E2E_R9M3B.tsv")
            if not os.path.isfile(p):
                return False, "missing prereg"
            pre_mt = int(os.path.getmtime(p))
            start_ep = log_epoch(start_recs.get("START_TIME_UTC", "")) if start_recs.get("START_TIME_UTC") else 0
            early = []
            for base in (os.path.join(ev_dir, "shakedown"), os.path.join(ev_dir, "runs")):
                if not os.path.isdir(base):
                    continue
                for root, dirs, files in os.walk(base):
                    for f in files:
                        if f.endswith(".json") and os.path.basename(root) == "points":
                            fp = os.path.join(root, f)
                            if int(os.path.getmtime(fp)) < pre_mt:
                                early.append(os.path.relpath(fp, ev_dir))
            record("E2E_POINT_FILES_BEFORE_PREREG", len(early))
            ok = len(early) == 0 and pre_mt >= start_ep
            return ok, ("prereg mtime %d >= start %d, no E2E point file earlier" % (pre_mt, start_ep) if ok else str(early[:5]))
        safe("PREREG_WRITTEN_BEFORE_FIRST_E2E_RUN", c_prereg_order, "prereg first")

        def c_formal_runs():
            bad = []
            counts = []
            want = len(read_tsv(os.path.join(ev_dir, "PREREG_E2E_R9M3B.tsv"))) if os.path.isfile(os.path.join(ev_dir, "PREREG_E2E_R9M3B.tsv")) else 0
            for p in ("pass1", "pass2"):
                d = os.path.join(ev_dir, "runs", p, "points")
                n = len([f for f in os.listdir(d) if f.endswith(".json")]) if os.path.isdir(d) else 0
                counts.append("%s=%d" % (p, n))
                if want and n != want:
                    bad.append(p)
            record("E2E_FORMAL_POINT_COUNTS", ",".join(counts))
            return len(bad) == 0 and len(counts) == 2, ",".join(counts)
        safe("E2E_FORMAL_RUNS_PRESENT", c_formal_runs, "both passes complete")

        def c_verdict():
            p = os.path.join(ev_dir, "E2E_VERDICT_R9M3B.tsv")
            rows = read_tsv(p)
            record("E2E_VERDICT_ROWS", len(rows))
            cats = {}
            for r in rows:
                cats[r.get("verdict", "?")] = cats.get(r.get("verdict", "?"), 0) + 1
            record("E2E_VERDICT_COUNTS", str(sorted(cats.items())))
            return len(rows) > 0, "%d rows %s" % (len(rows), sorted(cats.items()))
        safe("E2E_VERDICT_PRESENT", c_verdict, "verdict rows")

        def c_calib():
            p = os.path.join(ev_dir, "CALIB_E2E_R9M3B.tsv")
            if not os.path.isfile(p):
                return False, "missing CALIB"
            tt = [l for l in open(p, encoding="utf-8") if l.startswith("TARGET")]
            record("CALIB_TARGET_ROWS", len(tt))
            return len(tt) > 0, "%d target rows" % len(tt)
        safe("CALIB_PRESENT", c_calib, "target rows")

        def c_maketest():
            p = os.path.join(ev_dir, "MAKETEST_VERDICT_R9M3B.tsv")
            if not os.path.isfile(p):
                return False, "missing MAKETEST_VERDICT_R9M3B.tsv"
            txt = open(p, encoding="utf-8").read()
            record("MAKETEST_VERDICT", "NO_NEW_FAILURE" if "NO_NEW_FAILURE" in txt else "OTHER")
            return "NO_NEW_FAILURE" in txt, "NO_NEW_FAILURE"
        safe("MAKETEST_VERDICT_PRESENT", c_maketest, "NO_NEW_FAILURE")

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_lines = ["# P05-S4 R9 M3b gate_check (%s) %s" % (mode, os.path.basename(out_file))]
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


if __name__ == "__main__":
    sys.exit(main())
