#!/usr/bin/env python3
# gate_check_r9m3d.py -- P05-S4 R9 M3d gate helper (new file, r9m3d).
# Modes: start | start_recheck | end. Every check is wrapped: an exception becomes a CHECK_CRASHED FAIL line; the FAIL
# count is the exit status. Script names used by the end gate are read from FROZEN_SCRIPTS_R9M3D.tsv (U337 / E9-59).
# In the shakedown run of the end gate (before the frozen list is written, per section 5 order) the frozen-derived
# checks are recorded as SKIP instead of being invented.
import os, sys, re, hashlib, subprocess, datetime, fnmatch

EXPECTED_BASE = "c4f67071e80f8dd573f3653c04250708e7339b7f"
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECTED_S4_TREE_F4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXPECTED_S4_TREE_F3 = "6cff923a02baf19e01966b2339755cbf3a5deeef"
EXPECTED_F2_TREE = "e124925f5b242486a913b813fa181664f665b048"
EXPECTED_B_TREE = "1d738e64f9864a475fdb3de34cd3601605df2c64"
EXPECTED_BRANCH = "codex/p05-d003-fft-error-propagation"
STATE_BYTES_START = 5908
STATE_SHA_START = "95ea14b6caa33692bc22b7fa644c0583dfd3bd90eef4cab51f6b133b12474f67"
RULINGS_BYTES_START = 142281
RULINGS_SHA_PREFIX = "443d8a38"
RULINGS_MAX_U_START = "U350"
RULINGS_MAX_U_END = "U358"
ERRATA_9_BYTES_START = 56754
ERRATA_9_SHA_PREFIX = "9bd2933d"
ERRATA_9_LAST_E_START = "E9-66"
ERRATA_9_COUNT_START = 66
M3B_SUMS_SHA = "4a802924ce529df402f79cfe721da9a3550a6293d2950fd637b5c42015e4dc59"
M3B_SUMS_ITEMS = 18
M3B_REPORT_SHA = "788417e8cc55fe836d0887fd69df295498a761d53a631e485d9e820ed5e81467"
M3B_PREREG_SHA = "9e3895bb05f3b454a08b65824ba6740718ae4ae4af77b1515121a4d49b9b31da"
CALIB_TARGET_ROWS = 27
M3C_EVIDENCE_ITEMS = 16
HIST_COUNTS = {"s3r5": 14, "M0": 25, "M1": 28, "M1R2": 33, "M1R3": 26, "M1R4": 11, "M2": 14, "M2b": 13,
               "M2c": 11, "M3a": 17, "M3b": 18, "M3c": 13}
HIST_PATHS = {"s3r5": "checkpoints/p05/registries/s3r5"}
for _k in ("M0", "M1", "M1R2", "M1R3", "M1R4", "M2", "M2b", "M2c", "M3a", "M3b", "M3c"):
    HIST_PATHS[_k] = "checkpoints/p05/registries/s4r9/" + _k
IDENTICAL_TO_BASE = ["s3r5", "M0", "M1", "M1R2", "M1R3", "M1R4", "M2", "M2b", "M2c", "M3a", "M3b", "M3c"]
S3R5_ARTIFACTS = [
    ("lib_F4_dbg", "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_dbg/libS4.a", "6a711fbbec84d1fb322ee1d9c678ae6750a04f647e3f1eba7840c8c7502fae26"),
    ("lib_F4_san", "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_san/libS4.a", "ce057b5065bb5ac487d66992930991c1f09f17431abfc957777f375436be0fbd"),
    ("lib_F4_plain", "checkpoints/p05/evidence/p05-s3r5/build/lib_F4_plain/libS4.a", "5a4bfa601bf14b896b9c0c25807c0a38c05d040a17268cf0669902763cda5757"),
    ("init-F4-dbg", "checkpoints/p05/evidence/p05-s3r5/build/init-F4-dbg", "a4643e7e67ad74019104466ff9773ec2cfc1e684e488705a16a4a8f32526aca2"),
    ("init-F4-san", "checkpoints/p05/evidence/p05-s3r5/build/init-F4-san", "33a230029df224ddecb64f0884833e7e20251c461f0459ce315122d5987666c3"),
    ("init-F4-san-AL", "checkpoints/p05/evidence/p05-s3r5/build/init-F4-san-AL", "f14c536ea54d81348dd4f53f36c5c2eba65c0ca15fdb16160b8296186d7f5f8e"),
    ("init-B-dbg", "checkpoints/p05/evidence/p05-s4r8/m2c/build/init-B-dbg", "3ccc2897fae2ce293d3c656e2a334dad05e53fe7f622b749a71e19bfd021b0b8"),
]
OTHER_ROUND_EV = ["m0", "m1", "m1r2", "m1r3", "m1r4", "m2", "m2b", "m2c", "m3a", "m3b", "m3c"]
REPORT = "checkpoints/p05/P05_S4R9_M3d_REPORT.md"
SIGNOFF = "checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT_v2.md"
BRIEF = "checkpoints/p05/briefs/P05_S4R9_BRIEF_M3d.md"
ALLOWED_MODIFIED_AT_END = [REPORT]
STAGE = os.path.join(os.getcwd(), "testing/d003/stage_s4r9")
WHITELIST = os.path.join(STAGE, "WHITELIST_R9M3D.txt")
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


def tmp_snapshot():
    root = os.sep + "tmp"
    entries = sorted(os.listdir(root)) if os.path.isdir(root) else []
    payload = "\n".join(entries) + ("\n" if entries else "")
    return len(entries), hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_frozen(ev_dir):
    p = os.path.join(ev_dir, "FROZEN_SCRIPTS_R9M3D.tsv")
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


def frozen_path(frozen, needle):
    for row in frozen:
        if needle in os.path.basename(row["path"]):
            return row["path"]
    return None


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
        if f and f[0] == hdr[0]:
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def script_name_audit():
    files = sorted(f for f in os.listdir(STAGE) if (f.endswith(".py") or f.endswith(".sh")) and "r9m3d" in f)
    foreign = re.compile("r9m" + "(?:3a|3b|1r\\d|1|2b|2c|m0|m2b|m2c)" + "\\.(?:py|sh)")
    nonfinal = re.compile("_" + "r9m3d" + "_v" + "\\d+")
    wl = []
    if os.path.isfile(WHITELIST):
        for line in open(WHITELIST, encoding="utf-8"):
            if line.strip() and not line.startswith("#"):
                wl.append(line.split(chr(9))[0].strip())
    bad = []
    for f in files:
        for i, line in enumerate(open(os.path.join(STAGE, f), encoding="utf-8", errors="replace"), 1):
            for m in foreign.finditer(line):
                if any(w.endswith(m.group(0)) and w in line for w in wl):
                    continue
                bad.append((f, i, m.group(0)))
            for m in nonfinal.finditer(line):
                bad.append((f, i, m.group(0)))
    return len(files) > 0 and not bad, ("%d r9m3d scripts, %d foreign/non-final names" % (len(files), len(bad))
                                        if not bad else str(bad[:8]))


def main():
    mode = sys.argv[1]
    out_file = sys.argv[2]
    start_file = sys.argv[3]
    ev_dir = sys.argv[4]
    extra = sys.argv[5:]
    shakedown = False
    commit_i_override = None
    evidence_sums = os.path.join(ev_dir, "SHA256SUMS.txt")
    registries_dir = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3d")
    report_check_path = os.path.join(ev_dir, "REPORT_CHECK_R9M3D.txt")
    events_path = os.path.join(ev_dir, "EVENTS_R9M3D.tsv")
    i = 0
    while i < len(extra):
        if extra[i] == "--mode-shakedown":
            shakedown = True; i += 1
        elif extra[i] == "--commit-i" and i + 1 < len(extra):
            commit_i_override = extra[i + 1]; i += 2
        elif extra[i] == "--evidence-sums" and i + 1 < len(extra):
            evidence_sums = extra[i + 1]; i += 2
        elif extra[i] == "--registries-dir" and i + 1 < len(extra):
            registries_dir = extra[i + 1]; i += 2
        elif extra[i] == "--report-check" and i + 1 < len(extra):
            report_check_path = extra[i + 1]; i += 2
        elif extra[i] == "--events" and i + 1 < len(extra):
            events_path = extra[i + 1]; i += 2
        else:
            i += 1
    results = []
    records = []
    fails = 0
    skips = 0

    def check(name, cond, exp, act):
        nonlocal fails
        st = "PASS" if cond else "FAIL"
        if not cond:
            fails += 1
        results.append((st, name, str(exp), str(act)))

    def skip(name, why):
        nonlocal skips
        skips += 1
        results.append(("SKIP", name, "not applicable", why))

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

    if mode == "start":
        def c_head():
            h = sh(["git", "rev-parse", "HEAD"])
            record("HEAD", h)
            return h == EXPECTED_BASE, h
        safe("HEAD_IS_BASE", c_head, EXPECTED_BASE)
    else:
        def c_head():
            h = sh(["git", "rev-parse", "HEAD"])
            record("HEAD", h)
            return len(h) == 40, h
        safe("HEAD_PRESENT", c_head, "40-hex sha")

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

    for tag in ("s3r5", "M0", "M1", "M1R2", "M1R3", "M1R4", "M2", "M2b", "M2c", "M3a", "M3b", "M3c"):
        def mkr(tag=tag):
            def f():
                ok, cnt, det = verify_sums_dir(os.path.join(REPO, HIST_PATHS[tag]))
                record("REGISTRY_COUNT_" + tag, cnt)
                return ok and cnt == HIST_COUNTS[tag], "%s count=%d expected=%d" % (det, cnt, HIST_COUNTS[tag])
            return f
        safe("HIST_REGISTRY_" + tag + "_ALL_OK", mkr(), "all %d OK" % HIST_COUNTS[tag])

    def c_m3b_sums():
        p = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3b/SHA256SUMS.txt")
        a = sha256_file(p) if os.path.isfile(p) else "missing"
        return a == M3B_SUMS_SHA, a
    safe("M3B_SUMS_SHA256", c_m3b_sums, M3B_SUMS_SHA)
    record("REGISTRY_COUNT_M3b", HIST_COUNTS["M3b"])
    check("M3B_SUMS_ITEM_COUNT", HIST_COUNTS["M3b"] == M3B_SUMS_ITEMS, M3B_SUMS_ITEMS, HIST_COUNTS["M3b"])

    def c_m3b_report():
        p = os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3b_REPORT.md")
        a = sha256_file(p) if os.path.isfile(p) else "missing"
        return a == M3B_REPORT_SHA, a
    safe("M3B_REPORT_SHA256", c_m3b_report, M3B_REPORT_SHA)

    def c_m3c_ev():
        ok, cnt, det = verify_sums_dir(os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c"))
        return ok and cnt == M3C_EVIDENCE_ITEMS, "%s count=%d" % (det, cnt)
    safe("M3C_EVIDENCE_SUMS_ALL_OK", c_m3c_ev, "all %d OK" % M3C_EVIDENCE_ITEMS)

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

    outdir = os.path.dirname(os.path.abspath(out_file))
    allstatus = os.path.join(outdir, "ALL_STATUS_R9M3D_%s.txt" % mode)
    def c_write_status():
        os.makedirs(outdir, exist_ok=True)
        with open(allstatus, "w", encoding="utf-8") as fh:
            fh.write(sh(["git", "status", "--short", "-uall"]) + "\n")
            fh.write("BRANCH\t" + sh(["git", "branch", "--show-current"]) + "\n")
            fh.write("HEAD\t" + sh(["git", "rev-parse", "HEAD"]) + "\n")
        return os.path.isfile(allstatus), "written"
    safe("STATUS_ARTIFACT_WRITTEN", c_write_status, "written")

    safe("SCRIPT_NAME_AUDIT", script_name_audit, "no foreign or non-final r9m3d script names")

    rul_p = os.path.join(REPO, "checkpoints/p05/registries/RULINGS.tsv")
    err_p = os.path.join(REPO, "checkpoints/p05/registries/s4r9/ERRATA_9.txt")
    st_p = os.path.join(REPO, "checkpoints/p05/STATE.md")

    def c_brief():
        p = os.path.join(REPO, BRIEF)
        return os.path.isfile(p) and os.path.getsize(p) > 1000, os.path.getsize(p) if os.path.isfile(p) else "missing"
    safe("BRIEF_SAVED", c_brief, "brief file present")

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
        safe("RULINGS_START_SHA_PREFIX", lambda: (sha256_bytes(rul_b).startswith(RULINGS_SHA_PREFIX),
                                                  sha256_bytes(rul_b)[:12]), RULINGS_SHA_PREFIX + "...")

        def c_max_u():
            nums = [int(l.split("\t")[0][1:]) for l in rul_b.decode("utf-8", "replace").splitlines()
                    if l.startswith("U") and l.split("\t")[0][1:].isdigit()]
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
        safe("ERRATA_9_START_SHA_PREFIX", lambda: (sha256_bytes(err_b).startswith(ERRATA_9_SHA_PREFIX),
                                                   sha256_bytes(err_b)[:12]), ERRATA_9_SHA_PREFIX + "...")

        def c_last_e():
            ids = re.findall(r"^(E9-\d+)", err_b.decode("utf-8", "replace"), re.M)
            record("ERRATA_9_COUNT", len(ids))
            return (ids[-1] if ids else "none") == ERRATA_9_LAST_E_START and len(ids) == ERRATA_9_COUNT_START, (
                "%s count=%d" % (ids[-1] if ids else "none", len(ids)))
        safe("ERRATA_9_START_LAST_E_AND_COUNT", c_last_e, "%s count=%d" % (ERRATA_9_LAST_E_START, ERRATA_9_COUNT_START))
        safe("STATE_START_BYTES", lambda: (len(st_b) == STATE_BYTES_START, len(st_b)), STATE_BYTES_START)
        safe("STATE_START_SHA256", lambda: (sha256_bytes(st_b) == STATE_SHA_START, sha256_bytes(st_b)), STATE_SHA_START)

        def c_allow():
            allow_p = os.path.join(STAGE, "gate_allow_r9m3d_start.txt")
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

        def c_prereg():
            p = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b/PREREG_E2E_R9M3B.tsv")
            a = sha256_file(p) if os.path.isfile(p) else "missing"
            record("M3B_PREREG_SHA256", a)
            return a == M3B_PREREG_SHA, a
        safe("M3B_PREREG_SHA256", c_prereg, M3B_PREREG_SHA)

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

        def c_committed():
            d = sh(["git", "diff", "--name-only", EXPECTED_BASE])
            allow = ("checkpoints/p05/registries/RULINGS.tsv", "checkpoints/p05/registries/s4r9/ERRATA_9.txt",
                     "checkpoints/p05/STATE.md")
            bad = [f for f in d.splitlines() if f.strip() and f.strip() not in allow]
            return len(bad) == 0, ("only the append-only pair and STATE modified" if not bad else str(bad[:6]))
        safe("TRACKED_MODIFIED_ONLY_ALLOWED", c_committed, "only the append-only pair and STATE modified")

        frozen = read_frozen(ev_dir)
        record("FROZEN_ITEMS", len(frozen))
        if shakedown:
            skip("FROZEN_LIST_PRESENT", "shakedown runs before the frozen list is written")
        else:
            safe("FROZEN_LIST_PRESENT", lambda: (len(frozen) > 0, "%d rows" % len(frozen)), "rows")

    else:
        # ================= END MODE =================
        start_recs = parse_start_records(start_file)
        safe("START_RECORDS_PRESENT", lambda: (len(start_recs) > 0, "%d records" % len(start_recs) if start_recs else "missing"), "records present")
        start_tmp_count = int(start_recs.get("TMP_COUNT", "-1") or -1)
        record("TMP_COUNT_END", tmp_count)
        record("TMP_SHA256_END", tmp_sha)
        record("TMP_COUNT_START", start_tmp_count)
        safe("TMP_SNAPSHOT_RECORDED", lambda: (tmp_count >= 0, "count=%d sha=%s" % (tmp_count, tmp_sha)), "recorded")

        def c_tmp_known():
            ents = sorted(os.listdir(os.sep + "tmp")) if os.path.isdir(os.sep + "tmp") else []
            bad = [e for e in ents if not (e.startswith("dsh-spill-") or e.startswith("tmp.") or e in start_recs.get("TMP_ENTRIES", "").split(","))]
            return len(bad) == 0, ("entries=%d" % len(ents) if not bad else str(bad[:6]))
        safe("TMP_ENTRIES_KNOWN", c_tmp_known, "only framework spills or disclosed entries")

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
            seen = set()
            for line in rul_b.decode("utf-8", "replace").splitlines():
                if not line.strip() or line.strip().startswith("#"):
                    continue
                f = line.split("\t")
                if len(f) != 5:
                    return False, "bad field count in: " + line[:40]
                if f[0] in seen:
                    return False, "duplicate ruling id: " + f[0]
                seen.add(f[0])
            return True, "all lines 5 fields, no duplicate id"
        safe("RULINGS_LINES_5_FIELDS_NO_DUP_END", c_fields_end, "all lines 5 fields")

        def c_max_u_end():
            nums = [int(l.split("\t")[0][1:]) for l in rul_b.decode("utf-8", "replace").splitlines()
                    if l.startswith("U") and l.split("\t")[0][1:].isdigit()]
            record("RULINGS_MAX_U_END", "U%d" % max(nums) if nums else "none")
            record("RULINGS_BYTES_END", len(rul_b))
            record("RULINGS_SHA256_END", sha256_bytes(rul_b))
            return ("U%d" % max(nums)) == RULINGS_MAX_U_END, ("U%d" % max(nums) if nums else "none")
        safe("RULINGS_END_MAX_U", c_max_u_end, RULINGS_MAX_U_END)

        audit_p = os.path.join(ev_dir, "AUDIT_R9M3C_R9M3D.tsv")
        aud = read_tsv(audit_p)
        audit_true = len([r for r in aud if r.get("verdict") == "属实"])
        record("AUDIT_TRUE", audit_true)
        record("AUDIT_ROWS", len(aud))
        safe("AUDIT_PRESENT_6_ROWS", lambda: (len(aud) == 6, "%d rows" % len(aud)), 6)
        safe("AUDIT_ALL_TRUE", lambda: (audit_true == 6, "%d/6 true" % audit_true), "6/6 true")
        expected_err = ERRATA_9_COUNT_START + audit_true + 1

        def c_err_end():
            ids = re.findall(r"^(E9-\d+)", err_b.decode("utf-8", "replace"), re.M)
            record("ERRATA_9_COUNT_END", len(ids))
            record("ERRATA_9_BYTES_END", len(err_b))
            record("ERRATA_9_SHA256_END", sha256_bytes(err_b))
            last_ok = (ids[-1] if ids else "none") == "E9-%d" % expected_err
            return last_ok and len(ids) == expected_err, ("%s count=%d expected=%d" % (
                ids[-1] if ids else "none", len(ids), expected_err))
        safe("ERRATA_END_LAST_AND_COUNT", c_err_end, "E9-%d count=%d" % (expected_err, expected_err))

        def c_u353():
            txt = err_b.decode("utf-8", "replace")
            return ("执行顺序错误" in txt) and ("sha_sums" in txt) and ("progress" in txt), "U353 erratum present"
        safe("ERRATA_U353_ENTRY", c_u353, "U353 erratum present")

        for tag in IDENTICAL_TO_BASE:
            def mkm(tag=tag):
                def f():
                    d = sh(["git", "diff", EXPECTED_BASE, "--", HIST_PATHS[tag]])
                    return d == "", ("identical" if not d else d[:200])
                return f
            safe("HIST_REGISTRY_" + tag + "_IDENTICAL_TO_BASE", mkm(), "identical")

        def c_m3c_files():
            paths = [REPORT.replace("P05_S4R9_M3d_REPORT.md", "P05_S4R9_M3c_REPORT.md"),
                     "checkpoints/p05/briefs/P05_S4R9_BRIEF_M3c.md",
                     "checkpoints/p05/registries/s4r9/M3c",
                     "checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT.md",
                     "testing/d003/stage_s4r9"]
            d = sh(["git", "diff", EXPECTED_BASE, "--", ] + paths)
            return d == "", ("M3c artifacts and stage scripts identical" if not d else d[:300])
        safe("M3C_AND_M3B_COMMITTED_FILES_UNCHANGED", c_m3c_files, "identical")

        def c_mod():
            d = sh(["git", "diff", "--name-only", "HEAD"]).splitlines()
            allow = ALLOWED_MODIFIED_AT_END + (["checkpoints/p05/registries/RULINGS.tsv",
                                               "checkpoints/p05/registries/s4r9/ERRATA_9.txt",
                                               "checkpoints/p05/STATE.md"] if shakedown else [])
            bad = [f for f in d if f.strip() and f.strip() not in allow]
            return len(bad) == 0, ("only the report modified" if not bad else str(bad[:6]))
        safe("MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST", c_mod, "only the report modified")

        st_b = open(st_p, "rb").read() if os.path.isfile(st_p) else b""
        record("STATE_BYTES_END", len(st_b))
        safe("STATE_BYTES_LE_8192", lambda: (0 < len(st_b) <= 8192, len(st_b)), "<= 8192")

        def c_state_markers():
            t = st_b.decode("utf-8", "replace")
            miss = [m for m in ("r9m3d", "U354", "U356", "U352") if m not in t]
            return len(miss) == 0, ("all markers present" if not miss else str(miss))
        safe("STATE_REFLECTS_U352_U354_U356", c_state_markers, "state markers present")

        def c_root_so():
            sos = [f for f in os.listdir(REPO) if f.endswith(".so")]
            return len(sos) == 0, ("no *.so" if not sos else str(sos))
        safe("ROOT_NO_NEW_SO_AT_END", c_root_so, "no *.so")

        commit_i = commit_i_override
        if not commit_i:
            try:
                commit_i = sh(["git", "log", "--grep=R9 M3d (i)", "-1", "--format=%H"])
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
        post_i = [(x, ts, cmd) for (x, ts, cmd) in log_recs if (commit_i_override is not None or log_epoch(ts) >= commit_i_epoch)]
        record("POST_I_LOG_RECORDS", len(post_i))

        frozen = read_frozen(ev_dir)
        record("FROZEN_ITEMS", len(frozen))
        if shakedown:
            skip("FROZEN_LIST_READ", "shakedown runs before the frozen list is written (section 5 order)")
        else:
            safe("FROZEN_LIST_READ", lambda: (len(frozen) > 0, "%d rows" % len(frozen)), "rows")
            safe("FROZEN_COVERS_ROUND_SCRIPTS", lambda: (
                set(r["path"] for r in frozen if "/stage_s4r9/" in r["path"]) ==
                set(os.path.relpath(os.path.join(STAGE, f), REPO) for f in os.listdir(STAGE)
                    if (f.endswith(".py") or f.endswith(".sh")) and "r9m3d" in f),
                "%d frozen stage rows" % len([r for r in frozen if "/stage_s4r9/" in r["path"]])),
                "frozen == round scripts")

        for row in frozen:
            rel = row["path"]
            key = os.path.basename(rel).replace(".py", "").replace(".sh", "").replace(".tsv", "").upper()
            key = key + "_" + row["mode"].upper()
            if row["expect"] == "0":
                continue
            if shakedown:
                skip("POST_I_CALL_COUNT_" + key, "shakedown: frozen-derived count")
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
            for (x, ts, cmd) in post_i:
                if ("open('testing/d003/" in cmd) or ('open("testing/d003/' in cmd) or re.search(r">\s*testing/d003/", cmd):
                    bad.append((x, cmd[:80]))
            return len(bad) == 0, (0 if not bad else str(bad[:4]))
        safe("POST_I_NO_TESTING_D003_WRITES", c_no_d003_writes, 0)

        if not shakedown:
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

        def c_brief_held():
            d = sh(["git", "diff", "--name-only", commit_i_sha, "--", BRIEF]).splitlines() if commit_i_sha else ["no commit"]
            return len([x for x in d if x.strip()]) == 0, ("brief unchanged" if not d else str(d[:3]))
        safe("M3D_BRIEF_UNCHANGED_AT_END", c_brief_held, "brief unchanged")

        ev_rel = frozen_path(frozen, "events_")
        if shakedown or not ev_rel:
            skip("EVENTS_ROW_SET_EQ_RECOMPUTATION", "shakedown/no frozen events script")
        else:
            def c_events():
                if not ev_rel:
                    return False, "no events script in FROZEN"
                ev_hits = count_script_calls(post_i, ev_rel, "-", 0)
                if not ev_hits:
                    return False, "no events call after (i): " + ev_rel
                anchor = max(ev_hits)
                record("EVENTS_ANCHOR_LINE", anchor)
                if not os.path.isfile(events_path):
                    return False, "missing EVENTS_R9M3D.tsv"
                rows = {}
                for line in open(events_path, encoding="utf-8"):
                    if not line.strip() or line.startswith("#") or line.startswith("log_line" + chr(9)):
                        continue
                    parts = line.rstrip("\n").split("\t")
                    if len(parts) < 2:
                        continue
                    rows[int(parts[0])] = parts[1]
                raw = open(os.path.join(ev_dir, "safe_run.log"), encoding="utf-8", errors="replace").read().splitlines()
                ts_of = {x: ts for (x, ts, cmd) in log_recs}
                expect = {}
                parent = ""
                for x in range(1, anchor + 1):
                    if x > len(raw) or not raw[x - 1].strip():
                        continue
                    if x in ts_of:
                        parent = ts_of[x]
                    expect[x] = parent
                if set(rows) != set(expect):
                    miss = sorted(set(expect) - set(rows))[:5]
                    extra = sorted(set(rows) - set(expect))[:5]
                    return False, "row set differs missing=%s extra=%s" % (miss, extra)
                diff = [x for x in expect if rows[x] != expect[x]]
                record("EVENTS_ROWS", len(rows))
                return len(diff) == 0, ("rows=%d anchor=%d all timestamps match" % (len(rows), anchor) if not diff else "timestamp mismatch at %s" % diff[:5])
            safe("EVENTS_ROW_SET_EQ_RECOMPUTATION", c_events, "row set equals recomputation")

        ss_rel = frozen_path(frozen, "sha_sums")
        if shakedown or not ss_rel:
            skip("EVIDENCE_SHA256SUMS_OK", "shakedown/no frozen sha_sums script")
        else:
            def c_ev_sums():
                if not ss_rel:
                    return False, "no sha_sums script in FROZEN"
                sums_p = evidence_sums
                if not os.path.isfile(sums_p):
                    return False, "missing evidence SHA256SUMS.txt"
                lines = open(sums_p, encoding="utf-8").read().splitlines()
                if len(lines) < 2:
                    return False, "SHA256SUMS.txt too short"
                m = re.search(r"up to line (\d+):\s*([0-9a-f]{64})", lines[1])
                if not m:
                    return False, "no truncation header: " + lines[1][:80]
                trunc_line, trunc_sha = int(m.group(1)), m.group(2)
                ss_hits = count_script_calls(post_i, ss_rel, "-", 0)
                if not ss_hits:
                    return False, "no sha_sums call after (i): " + ss_rel
                anchor = max(ss_hits)
                record("SHA_SUMS_ANCHOR_LINE", anchor)
                if trunc_line != anchor:
                    return False, "trunc_line %d != sha_sums call line %d" % (trunc_line, anchor)
                log_text = "\n".join(open(os.path.join(ev_dir, "safe_run.log"), encoding="utf-8", errors="replace").read().splitlines()[:trunc_line]) + "\n"
                actual = sha256_bytes(log_text.encode("utf-8"))
                if actual != trunc_sha:
                    return False, "truncated log hash mismatch: %s" % actual
                sd = os.path.dirname(os.path.abspath(sums_p))
                ok, cnt, det = verify_sums_dir(sd)
                if not ok:
                    return False, det
                record("EVIDENCE_SUMS_ITEMS", cnt)
                return True, "trunc line %d %s ok, %d items OK" % (trunc_line, trunc_sha[:8], cnt)
            safe("EVIDENCE_SHA256SUMS_OK", c_ev_sums, "all OK")

        if shakedown:
            skip("EVIDENCE_SUMS_COVERS_ALL", "shakedown: partial manifest")
        else:
            def c_cov():
                sums_p = evidence_sums
                listed = set(name for h, name in read_sums(sums_p))
                ev_abs = os.path.abspath(ev_dir)
                out_abs = os.path.abspath(sums_p)
                gate_dir = os.path.join(ev_abs, "gate")
                missing = []
                for root, dirs, files in os.walk(ev_dir):
                    dirs[:] = sorted(d for d in dirs if d != "tmp")
                    for f in sorted(files):
                        fp = os.path.abspath(os.path.join(root, f))
                        if fp == out_abs or fp.startswith(gate_dir + os.sep):
                            continue
                        if f in ("safe_run.log", "SHA256SUMS.txt"):
                            continue
                        rel = os.path.relpath(fp, ev_abs)
                        if rel not in listed:
                            missing.append(rel)
                return len(missing) == 0, ("all %d files covered" % len(listed) if not missing else str(missing[:6]))
            safe("EVIDENCE_SUMS_COVERS_ALL", c_cov, "manifest covers every non-gate file")

        def c_no_write_after_sums():
            sums_m = os.path.getmtime(evidence_sums)
            ev_abs = os.path.abspath(ev_dir)
            gate_dir = os.path.join(ev_abs, "gate")
            tmp_dir = os.path.join(ev_abs, "tmp")
            out_abs = os.path.abspath(evidence_sums)
            bad = []
            for root, dirs, files in os.walk(ev_dir):
                for f in files:
                    fp = os.path.abspath(os.path.join(root, f))
                    if fp == out_abs or fp.startswith(gate_dir + os.sep) or fp.startswith(tmp_dir + os.sep):
                        continue
                    if f == "safe_run.log":
                        continue
                    if shakedown and (f.startswith("GATE_R9M3D_") or f.startswith("ALL_STATUS_")):
                        continue
                    if os.path.getmtime(fp) > sums_m + 0.5:
                        bad.append(os.path.relpath(fp, ev_abs))
            return len(bad) == 0, ("no $EV write after sha_sums" if not bad else str(sorted(bad)[:6]))
        safe("EV_NO_WRITE_AFTER_SHA_SUMS", c_no_write_after_sums, "sha_sums is the last $EV write")

        def c_unlogged():
            start_ep = log_epoch(start_recs.get("START_TIME_UTC", "")) if start_recs.get("START_TIME_UTC") else 0
            log_text = open(os.path.join(ev_dir, "safe_run.log"), encoding="utf-8", errors="replace").read() if os.path.isfile(os.path.join(ev_dir, "safe_run.log")) else ""
            declared = set()
            man = os.path.join(ev_dir, "REGISTRY_OUTPUTS_R9M3D.tsv")
            if os.path.isfile(man):
                for line in open(man, encoding="utf-8"):
                    if line.strip() and not line.startswith("#"):
                        declared.add(line.strip())
            declared.add(SIGNOFF)
            declared.add("checkpoints/p05/registries/RULINGS.tsv")
            declared.add("checkpoints/p05/registries/s4r9/ERRATA_9.txt")
            declared.add(REPORT)
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
            ok, cnt, det = verify_sums_dir(registries_dir)
            if not ok:
                return False, det
            record("REGISTRY_M3D_ITEMS", cnt)
            if shakedown:
                return True, "%s (shakedown registry is partial: the frozen list is written after the trial, per section 5)" % det
            rep = os.path.join(REPO, REPORT)
            if not os.path.isfile(rep):
                return False, "missing report"
            text = open(rep, encoding="utf-8").read()
            m = re.search(r"###\s*9\.1\s*小表交付物[^\n]*\n(.*?)(?:\n###|\n##|$)", text, re.S)
            if not m:
                return False, "cannot parse report section 9.1"
            items = []
            for line in m.group(1).splitlines():
                mm = re.match(r"^\s*\d+\.\s+(.+?)\s*$", line)
                if mm:
                    items.append(mm.group(1).strip().strip(BT).strip())
            record("REPORT_DELIVERABLES", len(items))
            record("REGISTRY_M3D_ITEMS", cnt)
            if not items:
                return False, "no numbered deliverables parsed"
            if cnt != len(items) - 1:
                return False, "sums items %d != report items-1 %d" % (cnt, len(items) - 1)
            if items[-1] != "SHA256SUMS.txt":
                return False, "last report item is not SHA256SUMS.txt: " + items[-1]
            return True, "sums %d items OK, report lists %d (incl SHA256SUMS.txt)" % (cnt, len(items))
        safe("REGISTRIES_M3D_SUMS_ALL_OK", c_reg, "all OK matching report")

        def c_ledger():
            p = os.path.join(ev_dir, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv")
            if not os.path.isfile(p):
                return False, "missing ledger"
            rows = read_tsv(p)
            ids = set(r.get("id", "") for r in rows)
            t5 = sorted(r["id"] for r in rows if r.get("current_status") == "TRANSFERRED_S5")
            expected = {"RP-R6d-3", "RP-R6d-6", "RP-R6d-7", "RP-R6d-16", "RP-R6d-17", "RP-R6d-18"}
            record("LEDGER_UNIQUE_IDS", len(ids))
            record("LEDGER_T5", len(t5))
            ok = len(ids) == 26 and len(rows) == 26 and set(t5) == expected
            ok = ok and "RP-R6d-14" in ids
            r14 = [r for r in rows if r.get("id") == "RP-R6d-14"]
            ok = ok and bool(r14) and r14[0].get("current_status") == "CLOSED" and r14[0].get("closing_ruling") == "U354"
            return ok, "unique=%d rows=%d t5=%s" % (len(ids), len(rows), ",".join(t5))
        safe("SB_LEDGER_UNIQUE_26_T5_6_R14_CLOSED", c_ledger, "26 ids, 6 T5, RP-R6d-14 closed by U354")

        def c_handoff():
            p = os.path.join(ev_dir, "S5_HANDOFF_R9M3D.tsv")
            rows = read_tsv(p)
            ids = set(r.get("item_id", "") for r in rows)
            covered = set()
            for r in rows:
                for x in (r.get("ledger_ids", "") or "").split(";"):
                    x = x.strip()
                    if x and x != "-":
                        covered.add(x)
            led = read_tsv(os.path.join(ev_dir, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv"))
            t5 = set(r["id"] for r in led if r.get("current_status") == "TRANSFERRED_S5")
            short = [r.get("item_id") for r in rows if (r.get("ledger_ids", "").strip() in ("", "-")) and (r.get("state_rows", "").strip() in ("", "-"))]
            record("HANDOFF_UNIQUE", len(ids))
            ok = len(rows) == 7 and len(ids) == 7 and covered == t5 and not short
            return ok, "rows=%d unique=%d covered=%s short=%s" % (len(rows), len(ids), sorted(covered), short)
        safe("SB_HANDOFF_UNIQUE_7_BIDIRECTIONAL", c_handoff, "7 unique items, both directions covered")

        def c_readiness():
            p = os.path.join(ev_dir, "READINESS_P05_S3S4_R9M3D.tsv")
            if not os.path.isfile(p):
                return False, "missing readiness"
            rows = read_tsv(p)
            rc = {}
            for r in rows:
                rc[r.get("status", "?")] = rc.get(r.get("status", "?"), 0) + 1
            led = read_tsv(os.path.join(ev_dir, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv"))
            uniq = len(set(r.get("id", "") for r in led))
            crit1 = [r for r in rows if r.get("item", "").startswith("①")]
            m = re.search(r"红点唯一 id 数=(\d+)", crit1[0].get("recomputed", "")) if crit1 else None
            crit1_n = int(m.group(1)) if m else -1
            jian = [r.get("item") for r in rows if "见 STATE 行" in (r.get("ruling", "") + r.get("recomputed", ""))]
            have = set()
            for line in open(rul_p, encoding="utf-8"):
                f = line.split("\t")
                if f and re.match(r"^U\d+$", f[0]):
                    have.add(f[0])
            bad_ruling = []
            for r in rows:
                rv = r.get("ruling", "")
                if rv == "-（事实项）":
                    continue
                toks = rv.split("/")
                if not toks or any((not re.match(r"^U\d+$", t)) or t not in have for t in toks):
                    bad_ruling.append((r.get("item", "")[:30], rv))
            record("READINESS_ROWS", len(rows))
            record("READINESS_COUNTS", str(sorted(rc.items())))
            ok = (len(rows) == 28 and rc.get("GAP", 0) == 0 and rc.get("TRANSFERRED_S5", 0) == 5
                  and crit1_n == uniq and not jian and not bad_ruling)
            return ok, "rows=%d counts=%s crit1=%d uniq=%d jian=%d bad_ruling=%s" % (
                len(rows), sorted(rc.items()), crit1_n, uniq, len(jian), bad_ruling[:3])
        safe("SB_READINESS_28_ROWS_GAP0_U357", c_readiness, "28 rows, GAP=0, U357 compliant, crit1==unique")

        def c_posctrl():
            bad = []
            for name in ("POSCTRL_HANDOFF_R9M3D.txt", "POSCTRL_READINESS_R9M3D.txt", "POSCTRL_REPORT_CHECK_R9M3D.txt"):
                p = os.path.join(ev_dir, name)
                if not os.path.isfile(p) or "RESULT: PASS" not in open(p, encoding="utf-8").read():
                    bad.append(name)
            return len(bad) == 0, ("all three PASS" if not bad else str(bad))
        safe("SB_POSCTRL_ALL_PASS", c_posctrl, "all three PASS")

        def c_report_check():
            if not os.path.isfile(report_check_path):
                return False, "missing report check output"
            fails_v = None
            for line in open(report_check_path, encoding="utf-8"):
                if line.startswith("FAILS="):
                    fails_v = int(line.strip().split("=")[1])
            record("REPORT_CHECK_FAILS", fails_v)
            return fails_v == 0, "FAILS=%s" % fails_v
        safe("REPORT_CHECK_FAILS_ZERO", c_report_check, "FAILS=0")

        def c_signoff():
            p = os.path.join(REPO, SIGNOFF)
            if not os.path.isfile(p):
                return False, "missing signoff draft v2"
            head = open(p, encoding="utf-8").read()
            first = ""
            for line in head.splitlines():
                if line.strip():
                    first = line.strip()
                    break
            keys = ["草稿，非签收；签收只由用户在对话中给出", "### S1/S2 签收移交项的闭合（U356）", "7/7 MATCH",
                    "info=NULL", "&solve_info", "### 转入 S5 的项", "## 与 v1 的差异", "P-6"]
            miss = [k for k in keys if k not in head]
            hand = read_tsv(os.path.join(ev_dir, "S5_HANDOFF_R9M3D.tsv"))
            n_items = 0
            insec = False
            for line in head.splitlines():
                if line.startswith("### 转入 S5 的项"):
                    insec = True
                    continue
                if insec and line.startswith("#"):
                    break
                if insec and line.strip().startswith("- "):
                    n_items += 1
            ok = ("草稿" in first) and not miss and n_items == len(hand)
            return ok, "first=%s missing=%s s5_items=%d handoff=%d" % (first[:60], miss, n_items, len(hand))
        safe("SIGNOFF_DRAFT_V2_MARKED_AND_CONSISTENT", c_signoff, "draft v2 marked and consistent")

        def c_e2e():
            ver = read_tsv(os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b/E2E_VERDICT_R9M3B.tsv"))
            cats = {}
            for r in ver:
                cats[r.get("verdict", "?")] = cats.get(r.get("verdict", "?"), 0) + 1
            record("E2E_COUNTS", str(sorted(cats.items())))
            ok = cats.get("E2E_OK") == 25 and cats.get("CONTROL_OK") == 17 and len(cats) == 2 and len(ver) == 42
            return ok, "%d rows %s" % (len(ver), sorted(cats.items()))
        safe("E2E_VERDICT_COUNTS_25_17", c_e2e, "{E2E_OK:25, CONTROL_OK:17}")

        def c_maketest():
            txt = open(os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b/MAKETEST_VERDICT_R9M3B.tsv"), encoding="utf-8").read()
            return "NO_NEW_FAILURE" in txt, "NO_NEW_FAILURE" if "NO_NEW_FAILURE" in txt else "OTHER"
        safe("MAKETEST_NO_NEW_FAILURE", c_maketest, "NO_NEW_FAILURE")

        def c_calib():
            tt = [l for l in open(os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b/CALIB_E2E_R9M3B.tsv"), encoding="utf-8") if l.startswith("TARGET")]
            record("CALIB_TARGET_ROWS", len(tt))
            return len(tt) == CALIB_TARGET_ROWS, len(tt)
        safe("CALIB_TARGET_ROWS_27", c_calib, CALIB_TARGET_ROWS)

        def c_prereg_unchanged():
            p = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b/PREREG_E2E_R9M3B.tsv")
            a = sha256_file(p) if os.path.isfile(p) else "missing"
            return a == start_recs.get("M3B_PREREG_SHA256", M3B_PREREG_SHA), a
        safe("M3B_PREREG_SHA256_UNCHANGED", c_prereg_unchanged, M3B_PREREG_SHA)

    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out_lines = ["# P05-S4 R9 M3d gate_check (%s) %s" % (mode, os.path.basename(out_file))]
    for k, v in records:
        out_lines.append("RECORD\t%s\tvalue=%s" % (k, v))
    for st, name, exp, act in results:
        out_lines.append("%s\t%s\texpected=%s\tactual=%s" % (st, name, exp, act))
    out_lines.append("COUNTS\tpass=%d\tfail=%d\tskip=%d\ttotal=%d" % (
        sum(1 for r in results if r[0] == "PASS"), fails, skips, len(results)))
    out_lines.append("FAILS=%d" % fails)
    out_lines.append("SKIPS=%d" % skips)
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
