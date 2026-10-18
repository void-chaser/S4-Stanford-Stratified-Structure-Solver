#!/usr/bin/env python3
# gate_check_s5r4.py -- P05-S5 R4 end gate. Copied from gate_check_s5r3.py (same check structure and names
# where the check is inherited). Declared differences (COPY_DIFF_S5R4.txt, categories CONSTANT / FIX1..FIX5 /
# STAGING / NEW_CHECK; no strength reduction):
#   (a) constants: EV4/EV3 roots, baseline HEAD, RULINGS/ERRATA/STATE expectations read from the S5R4 start gate;
#   (b) FIX1 RULINGS_LINES_5_FIELDS: skip '#' lines, every other non-empty line must have exactly 5 tab fields;
#       FIX2 FROZEN_POST_I_CALL_COUNTS_MATCH: FROZEN read by column name, mode='-' means any invocation,
#            mode=formal requires the formal word in the command, actual calls == expected for every row;
#       FIX3 MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST: git status --porcelain=v1 is NOT stripped as a
#            whole; each line is parsed as status=ln[:2] path=ln[3:] (leading space is the status column);
#       FIX4 D016_VERDICT_ROWS_34: exclude '#' lines, the point_id header row and SUMMARY rows; 34 rows and
#            the verdict column must be MATCH=33 / RECORD=1;
#       FIX5 CALIB_DIFF_ZERO: exclude rows whose first field is SUMMARY, every other row must be SAME, and the
#            SUMMARY row's DIFFS must be 0;
#   (c) new checks for the S5R4 deliverables (rejudge v2, R3 gate recheck, R3 immutability, readiness, STATE,
#       sign-off draft v2, registry completion, errata, rulings, registry patch, report, shakedown);
#   (d) staging overrides: --ev-root, --ev3-root, --p05-root, --stage-repo, --post-i-from, --commit-i, --out.
# The run log is always the real round log (checkpoints/p05/evidence/p05-s5r4/safe_run.log), also when the
# evidence root is a staging copy.
# usage: gate_check_s5r4.py end [--ev-root DIR] [--ev3-root DIR] [--p05-root DIR] [--stage-repo DIR]
#          [--commit-i SHA|HEAD] [--post-i-from N] [--out PATH] [--only CHECK] [--status-override PATH]
import os, sys, re, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
TAB = chr(9)
NL = chr(10)
EXP_BRANCH = "codex/p05-d003-fft-error-propagation"
EXP_HEAD = "e6a65ab4751c5ba5a5d6e2e0c093826d37312064"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
FIXED_CHECK_NAMES = ("RULINGS_LINES_5_FIELDS", "FROZEN_POST_I_CALL_COUNTS_MATCH",
                     "MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST", "D016_VERDICT_ROWS_34", "CALIB_DIFF_ZERO")
R3_FAIL_NAMES = sorted(["RULINGS_LINES_5_FIELDS", "FROZEN_POST_I_CALL_COUNTS_MATCH",
                        "MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST", "D016_VERDICT_ROWS_34",
                        "CALIB_DIFF_ZERO", "REJUDGE_DIFFS_ZERO", "READINESS_GAP_ZERO", "REGISTRIES_SUMS_ALL_OK"])
CAUSE_CLASSES = "CK_COMMENT,FROZEN_MODE,CK_STRIP,CK_HEADER,CK_SUMMARY,REAL_CRASH,ORDER,CASCADE"
R3_DELIVERED_19 = ["GATE_S5R3_start.txt", "PREREG_D016_S5R3.tsv", "PREREG_D016_S5R3.tsv.sha256.txt",
                   "PREREG_MAKETEST_S5R3.tsv", "PREREG_E2E_S5R3.tsv", "PREREG_E2E_S5R3.tsv.sha256.txt",
                   "D016_VERDICT_S5R3.tsv", "D016_BUILD_S5R3.tsv", "E2E_VERDICT_S5R3.tsv", "E2E_BUILD_S5R3.tsv",
                   "CALIB_DIFF_S5R3.tsv", "MAKETEST_UNITS_S5R3.tsv", "MAKETEST_VERDICT_S5R3.tsv",
                   "POSCTRL_D016_S5R3.txt", "POSCTRL_E2E_S5R3.txt", "POSCTRL_MAKETEST_S5R3.txt",
                   "FROZEN_SCRIPTS_S5R3.tsv", "s5r2_supplement/D016_VERDICT_S5R2_ERRATA.txt",
                   "s5r2_supplement/D016_BUILD_S5R2.tsv"]
S5R3_COMPLETION_7 = ["REJUDGE_S5R3.tsv", "READINESS_S5R3.tsv", "P05_ACCEPTANCE_MAP_S5R3.tsv",
                     "REGISTRY_APPLY_DIFF_S5R3.txt", "REPORT_CHECK_S5R3.txt", "COPY_DIFF_S5R3.txt",
                     "ERRATA_S5_R3FINAL.txt"]

CHECKS = []
RECORDS = []
CRASHED = []


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def sh(cmd):
    return subprocess.check_output(cmd, text=True, cwd=REPO, stderr=subprocess.DEVNULL).strip()


def sh_raw(cmd):
    """Like sh() but WITHOUT stripping: git status --porcelain=v1 lines start with the two status columns,
    so a global strip() would move the first line's path by one character (the S5R3 FIX3 defect)."""
    return subprocess.check_output(cmd, text=True, cwd=REPO, stderr=subprocess.DEVNULL).rstrip("\n")


def rd(p):
    return open(p, encoding="utf-8").read()


def record(k, v):
    RECORDS.append((k, str(v)))


def safe(name, fn, exp):
    try:
        actual = fn()
        if isinstance(actual, bool):
            actual = int(actual)
    except Exception as exc:
        CRASHED.append((name, repr(exc)[:200]))
        actual = "EXC:" + repr(exc)[:160]
    ok = str(actual) == str(exp)
    CHECKS.append((name, str(exp), str(actual), ok))


def read_tsv(p, skip_first=("SUMMARY",)):
    """Read a TSV BY COLUMN NAME. Skips blank lines, '#' comments, the header row (also when repeated)
    and rows whose first field is in skip_first (e.g. SUMMARY) -- the FIX4/S5R3-crash rule."""
    rows = []
    hdr = None
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f[0] == hdr[0]:
            continue
        if f[0] in skip_first:
            continue
        rows.append(dict(zip(hdr, f + [""] * (len(hdr) - len(f)))))
    return rows


def read_kv(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 2:
            d[f[0]] = f[1]
    return d


def verify_sums_dir(d):
    p = os.path.join(d, "SHA256SUMS.txt")
    if not os.path.isfile(p):
        return None
    bad = []
    n = 0
    for line in open(p, encoding="utf-8"):
        line = line.rstrip(NL)
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        n += 1
        fp = os.path.join(d, " ".join(parts[1:]))
        if not os.path.isfile(fp) or sha_f(fp) != parts[0]:
            bad.append(os.path.basename(fp))
    return n, bad


def listed_map(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        d[" ".join(parts[1:])] = parts[0]
    return d


def log_records(path):
    recs = []
    if not os.path.isfile(path):
        return recs
    for i, line in enumerate(rd(path).splitlines(), 1):
        m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t(.*)$", line)
        if not m:
            continue
        rest = m.group(2)
        idx = rest.find(TAB + "cmd=")
        cmd = rest[idx + 5:] if idx >= 0 else rest
        recs.append((i, m.group(1), cmd))
    return recs


def epoch_of(ts):
    return int(datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp())


def count_calls(recs, relpath, mode):
    n = 0
    for i, ts, cmd in recs:
        if relpath not in cmd:
            continue
        if mode != "-" and mode not in cmd:
            continue
        n += 1
    return n


def first_line(recs, needle):
    for i, ts, cmd in recs:
        if needle in cmd:
            return i
    return -1


ONLY_EXPECT = {
    "RULINGS_LINES_5_FIELDS": "ok",
    "FROZEN_POST_I_CALL_COUNTS_MATCH": "ok",
    "MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST": "ok",
    "D016_VERDICT_ROWS_34": "34/MATCH=33,RECORD=1",
    "CALIB_DIFF_ZERO": "ok",
    "REJUDGE_S5R4_DIFFS_ZERO": "0",
    "SHAKEDOWN_GATE_FAILS_ZERO": "PASS",
}


def run_only(only, EV, EV3, P05, STAGE, outp, post, status_override, precommit):
    """Single-check mode used by the positive control: evaluate exactly one check (robust to the other
    artefacts being absent from the tampered staged roots) and write a normal gate-shaped output."""
    def evaluate():
        if only == "RULINGS_LINES_5_FIELDS":
            rb = open(os.path.join(P05, "registries/RULINGS.tsv"), "rb").read()
            for line in rb.decode("utf-8").splitlines():
                if not line.strip() or line.startswith("#"):
                    continue
                if len(line.split(TAB)) != 5:
                    return "bad_%d_fields" % len(line.split(TAB))
            return "ok"
        if only == "FROZEN_POST_I_CALL_COUNTS_MATCH":
            frozen = read_tsv(os.path.join(EV, "FROZEN_SCRIPTS_S5R4.tsv"))
            bad = []
            for r in frozen:
                mode = r.get("mode", "-").strip() or "-"
                actual = count_calls(post, r["path"], mode)
                if str(actual) != r.get("expected_calls", "").strip():
                    bad.append(r["path"])
            return "ok" if not bad else "bad_%d" % len(bad)
        if only == "MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST":
            allow = {"checkpoints/p05/STATE.md", "checkpoints/p05/P05_S5R4_REPORT.md",
                     "checkpoints/p05/P05_S5_SIGNOFF_DRAFT_v2.md", "testing/s4test/ISSUE_REGISTRY.md",
                     "PROJECT_ROADMAP.md"}
            if precommit:
                allow |= {"checkpoints/p05/registries/RULINGS.tsv", "checkpoints/p05/registries/s5r2/ERRATA_S5.txt"}
            untracked = ("testing/d003/stage_s5r4/", "checkpoints/p05/registries/s5r4/")
            if status_override:
                lines = [l.rstrip() for l in rd(status_override).splitlines() if l.strip()]
            else:
                lines = [l.rstrip() for l in sh_raw(["git", "status", "--porcelain=v1"]).splitlines() if l.strip()]
            bad = []
            for ln in lines:
                status, path = ln[:2], ln[3:]
                if path in allow:
                    continue
                if status.strip() == "??" and any(path.startswith(p) for p in untracked):
                    continue
                bad.append(ln)
            return "ok" if not bad else ";".join(bad[:3])
        if only == "D016_VERDICT_ROWS_34":
            rows = read_tsv(os.path.join(EV3, "D016_VERDICT_S5R3.tsv"))
            cnt = {}
            for r in rows:
                cnt[r.get("verdict", "?")] = cnt.get(r.get("verdict", "?"), 0) + 1
            bad = not (len(rows) == 34 and cnt.get("MATCH") == 33 and cnt.get("RECORD") == 1)
            return ("34/MATCH=33,RECORD=1" if not bad else "%d/%s" % (len(rows), cnt))
        if only == "CALIB_DIFF_ZERO":
            cald = read_tsv(os.path.join(EV3, "CALIB_DIFF_S5R3.tsv"))
            bad = [r for r in cald if r.get("diff") != "SAME"]
            summ = [l for l in rd(os.path.join(EV3, "CALIB_DIFF_S5R3.tsv")).splitlines() if l.startswith("SUMMARY" + TAB)]
            if bad or len(summ) != 1 or "DIFFS=0" not in summ[0]:
                return "rows_diff=%d summary=%s" % (len(bad), summ[0] if summ else "MISSING")
            return "ok"
        if only == "REJUDGE_S5R4_DIFFS_ZERO":
            d = {}
            p = os.path.join(EV, "REJUDGE_S5R4.tsv")
            for line in rd(p).splitlines() if os.path.isfile(p) else []:
                if line.startswith("SUMMARY" + TAB):
                    for x in line.split(TAB)[1:]:
                        k, _, v = x.partition("=")
                        d[k] = v
            return d.get("DIFFS", "MISSING")
        return "UNKNOWN_CHECK"
    try:
        actual = evaluate()
    except Exception as exc:
        CRASHED.append((only, repr(exc)[:200]))
        actual = "EXC:" + repr(exc)[:160]
    exp = ONLY_EXPECT.get(only, "?")
    ok = str(actual) == str(exp)
    CHECKS.append((only, str(exp), str(actual), ok))
    lines = ["# P05-S5 R4 end gate single-check mode (--only) " + only,
             "RECORD" + TAB + "ONLY_CHECK" + TAB + "value=" + only,
             ("PASS" if ok else "FAIL") + TAB + only + TAB + "expected=" + str(exp) + TAB + "actual=" + str(actual),
             "COUNTS" + TAB + "pass=%d" % (1 if ok else 0) + TAB + "fail=%d" % (0 if ok else 1) + TAB + "total=1",
             "FAILS=%d" % (0 if ok else 1), "CHECK_CRASHED=%d" % len(CRASHED)]
    for n, x in CRASHED:
        lines.append("CRASHED" + TAB + n + TAB + x)
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    open(outp, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print(NL.join(lines))
    return 0 if ok and not CRASHED else 1


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] != "end":
        print("usage: gate_check_s5r4.py end [--ev-root DIR] [--ev3-root DIR] [--p05-root DIR] [--stage-repo DIR] "
              "[--commit-i SHA|HEAD] [--post-i-from N] [--out PATH] [--only CHECK] [--status-override PATH]")
        return 2
    def arg(name, default=None):
        return argv[argv.index(name) + 1] if name in argv else default
    EV = os.path.abspath(arg("--ev-root", EV4_REAL))
    EV3 = os.path.abspath(arg("--ev3-root", os.path.join(P05_REAL, "evidence/p05-s5r3")))
    P05 = os.path.abspath(arg("--p05-root", P05_REAL))
    STAGE = os.path.abspath(arg("--stage-repo", REPO))
    LOG = os.path.join(EV4_REAL, "safe_run.log")          # always the real round log
    outp = os.path.abspath(arg("--out", os.path.join(EV, "gate/GATE_S5R4_end.txt")))
    only = arg("--only")
    status_override = arg("--status-override")
    staging = (os.path.realpath(EV) != os.path.realpath(EV4_REAL) or os.path.realpath(P05) != os.path.realpath(P05_REAL))
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    recs = log_records(LOG)
    recs3 = log_records(os.path.join(EV3, "safe_run.log"))
    srec = {}
    sgp = os.path.join(EV, "GATE_S5R4_start.txt")
    if os.path.isfile(sgp):
        for line in rd(sgp).splitlines():
            if line.startswith("RECORD" + TAB):
                f = line.split(TAB)
                srec[f[1]] = f[2].replace("value=", "")
    record("END_TIME_UTC", started)
    record("GATE_SCRIPT", "testing/d003/stage_s5r4/gate_check_s5r4.py")
    record("STAGING_MODE", "yes" if staging else "no")
    record("EV_ROOT", os.path.relpath(EV, REPO))
    record("P05_ROOT", os.path.relpath(P05, REPO))
    record("EV3_ROOT", os.path.relpath(EV3, REPO))
    # ---------- commit (i) and POST_I window
    commit_i = arg("--commit-i")
    if commit_i == "HEAD":
        commit_i = sh(["git", "rev-parse", "HEAD"])
    if not commit_i:
        commit_i = sh(["git", "log", "--grep=P05-S5 R4 (i)", "-1", "--format=%H"])
    record("COMMIT_I_SHA", commit_i or "MISSING")
    record("COMMIT_I_OVERRIDE", "yes" if arg("--commit-i") else "no")
    commit_epoch = 0
    if commit_i and re.match(r"^[0-9a-f]{40}$", commit_i or ""):
        commit_epoch = int(sh(["git", "log", "-1", "--format=%ct", commit_i]))
    post_from = arg("--post-i-from")
    if post_from:
        post_from = int(post_from)
    else:
        post_from = len(recs) + 1
        for i, ts, cmd in recs:
            if epoch_of(ts) >= commit_epoch:
                post_from = i
                break
    record("POST_I_FROM_LINE", post_from)
    record("POST_I_FROM_OVERRIDE", "yes" if arg("--post-i-from") else "no")
    post = [r for r in recs if r[0] >= post_from]
    precommit = ("--precommit-i" in argv) or staging
    if only:
        return run_only(only, EV, EV3, P05, STAGE, outp, post, status_override, precommit)
    record("POST_I_LOG_RECORDS", len(post))
    record("COMMIT_I_EPOCH", commit_epoch)
    record("COMMIT_I_SUBJECT", sh(["git", "log", "-1", "--format=%s", commit_i]) if commit_i else "?")

    # ---------- baseline (inherited)
    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), EXP_BRANCH)
    safe("HEAD_S4_TREE_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("JUDGE_SHA256", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    safe("F2_S4_TREE", lambda: sh(["git", "rev-parse", "a07b5ac:S4"]), "e124925f5b242486a913b813fa181664f665b048")
    safe("B_S4_TREE", lambda: sh(["git", "rev-parse", "37a82e8:S4"]), "1d738e64f9864a475fdb3de34cd3601605df2c64")
    safe("S4_DIR_ZERO_MODIFICATION", lambda: sh(["git", "diff", "--name-only", "HEAD", "--", "S4"]) or "unmodified", "unmodified")
    # ---------- start gate (inherited)
    safe("START_GATE_PRESENT", lambda: "present" if os.path.isfile(sgp) else "absent", "present")
    safe("START_GATE_FAILS_ZERO", lambda: re.search(r"FAILS=(\d+)", rd(sgp)).group(1), "0")
    safe("START_GATE_CRASHED_ZERO", lambda: re.search(r"CHECK_CRASHED=(\d+)", rd(sgp)).group(1), "0")
    safe("START_RECORDS_PRESENT", lambda: "present" if srec else "absent", "present")
    record("START_TIME_UTC", srec.get("START_TIME_UTC", "?"))
    # ---------- rulings (FIX1)
    rul = os.path.join(P05, "registries/RULINGS.tsv")
    rb = open(rul, "rb").read()
    safe("RULINGS_NOT_TRUNCATED", lambda: 1 if len(rb) >= int(srec["RULINGS_BYTES"]) else 0, "1")
    safe("RULINGS_PREFIX_OF_START_UNCHANGED", lambda: sha_b(rb[:int(srec["RULINGS_BYTES"])]), srec.get("RULINGS_SHA256"))
    def rulings_max_u():
        mu = 0
        for line in rb.decode("utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            f = line.split(TAB)
            if f and re.match(r"^U(\d+)$", f[0]):
                mu = max(mu, int(f[0][1:]))
        return "U%d" % mu
    safe("RULINGS_MAX_U_385", rulings_max_u, "U385")
    def rulings_5_fields():
        n = 0
        for line in rb.decode("utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            n += 1
            if len(line.split(TAB)) != 5:
                return "row%d=%dfields" % (n, len(line.split(TAB)))
        record("RULINGS_DATA_ROWS", n)
        return "ok_%d_rows" % n
    def _r5():
        got = rulings_5_fields()
        return "ok" if got.startswith("ok_") else got
    safe("RULINGS_LINES_5_FIELDS", _r5, "ok")
    def rulings_u378_u385():
        ids = [l.split(TAB)[0] for l in rb.decode("utf-8").splitlines()
               if not l.startswith("#") and re.match(r"^U(\d+)$", l.split(TAB)[0] if l.split(TAB) else "")]
        bad = [u for u in ("U378", "U379", "U380", "U381", "U382", "U383", "U384", "U385") if ids.count(u) != 1]
        return "ok" if not bad else ",".join(bad)
    safe("RULINGS_U378_U385_ONCE", rulings_u378_u385, "ok")
    # ---------- errata (inherited, S5R4 last entry)
    err = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
    eb = open(err, "rb").read()
    safe("ERRATA_S5_PREFIX_OF_START_UNCHANGED", lambda: sha_b(eb[:int(srec["ERRATA_S5_BYTES"])]), srec.get("ERRATA_S5_SHA256"))
    last_e = [l for l in eb.decode("utf-8").splitlines() if l.startswith("ES5-")]
    safe("ERRATA_S5_LAST_IS_ES5_14", lambda: last_e[-1] if last_e else "none", "ES5-14")
    safe("ERRATA_S5_HAS_ES5_9_TO_14", lambda: ",".join(x for x in last_e if x in ["ES5-%d" % i for i in range(9, 15)]),
         "ES5-9,ES5-10,ES5-11,ES5-12,ES5-13,ES5-14")
    safe("ERRATA_S5_GREW", lambda: 1 if len(eb) > int(srec["ERRATA_S5_BYTES"]) else 0, "1")
    record("ERRATA_S5_BYTES", len(eb))
    # ---------- STATE (FIXED expectations from start records)
    stp = os.path.join(P05, "STATE.md")
    st = open(stp, "rb").read()
    safe("STATE_BYTES_LE_8192", lambda: 1 if len(st) <= 8192 else 0, "1")
    record("STATE_BYTES", len(st))
    record("STATE_SHA256", sha_b(st))
    state_txt = st.decode("utf-8")
    safe("STATE_MARKERS_R4", lambda: 0 if [k for k in ("P05-S5 R4", "未签收") if k not in state_txt] else 1, "1")
    def state_numbers():
        miss = [k for k in ("DIFFS=0", "GAP=0", "26/26", "33", "265", "NO_NEW_FAILURE") if k not in state_txt]
        return "ok" if not miss else ",".join(miss)
    safe("STATE_CRITICAL_NUMBERS", state_numbers, "ok")
    safe("STATE_CHANGED_FROM_START", lambda: 1 if sha_b(st) != srec.get("STATE_SHA256") else 0, "1")
    # ---------- commit (i)
    safe("COMMIT_I_PRESENT", lambda: 1 if commit_i and re.match(r"^[0-9a-f]{40}$", commit_i or "") else 0, "1")
    safe("COMMIT_I_IS_HEAD", lambda: sh(["git", "rev-parse", "HEAD"]), commit_i)
    def post_from_is_chain():
        line = recs[post_from - 1] if 0 < post_from <= len(recs) else None
        if line is None:
            return "missing"
        return "ok" if "s4_chain.py" in line[2] or "s5r4_chain.py" in line[2] else line[2][:80]
    safe("POST_I_FROM_LINE_IS_CHAIN", post_from_is_chain, "ok")
    def post_from_after_commit():
        line = recs[post_from - 1] if 0 < post_from <= len(recs) else None
        if line is None:
            return "missing"
        return 1 if epoch_of(line[1]) >= commit_epoch else 0
    safe("POST_I_FROM_AFTER_COMMIT", post_from_after_commit, "1")
    # ---------- FROZEN (FIX2)
    fz = os.path.join(EV, "FROZEN_SCRIPTS_S5R4.tsv")
    safe("FROZEN_LIST_PRESENT", lambda: "present" if os.path.isfile(fz) else "absent", "present")
    frozen = read_tsv(fz) if os.path.isfile(fz) else []
    record("FROZEN_ROWS", len(frozen))
    safe("FROZEN_ROWS_POSITIVE", lambda: 1 if len(frozen) >= 15 else 0, "1")
    frozen_map = {r["path"]: r for r in frozen}
    bad_sha = [r["path"] for r in frozen if not os.path.isfile(os.path.join(REPO, r["path"]))
               or sha_f(os.path.join(REPO, r["path"])) != r["sha256"]]
    safe("FROZEN_SCRIPTS_SHA_UNCHANGED_END", lambda: 1 if not bad_sha else 0, "1")
    if bad_sha:
        record("FROZEN_SHA_BAD", ",".join(os.path.basename(x) for x in bad_sha[:5]))
    def frozen_counts():
        bad = []
        for r in frozen:
            mode = r.get("mode", "-").strip() or "-"
            actual = count_calls(post, r["path"], mode)
            if str(actual) != r.get("expected_calls", "").strip():
                bad.append("%s mode=%s exp=%s act=%d" % (os.path.basename(r["path"]), mode, r.get("expected_calls"), actual))
        if bad:
            for b in bad[:12]:
                record("CALL_COUNT_DIFF", b)
        return "ok" if not bad else "bad_%d" % len(bad)
    safe("FROZEN_POST_I_CALL_COUNTS_MATCH", frozen_counts, "ok")
    frozen_names = [os.path.basename(r["path"]) for r in frozen]
    foreign = [i for i, ts, cmd in post if "testing/d003" in cmd and not any(nm in cmd for nm in frozen_names)]
    safe("POST_I_NO_TESTING_D003_WRITES", lambda: len(foreign), 0)
    if commit_i and re.match(r"^[0-9a-f]{40}$", commit_i or ""):
        safe("COMMITTED_I_FILES_UNCHANGED_AT_END",
             lambda: sh(["git", "diff", "--name-only", commit_i, "HEAD", "--", "testing/d003"]) or "unmodified", "unmodified")
    # ---------- modified tracked files (FIX3)
    allow_files = {"checkpoints/p05/STATE.md", "checkpoints/p05/P05_S5R4_REPORT.md",
                   "checkpoints/p05/P05_S5_SIGNOFF_DRAFT_v2.md", "testing/s4test/ISSUE_REGISTRY.md",
                   "PROJECT_ROADMAP.md"}
    allow_untracked = ("testing/d003/stage_s5r4/", "checkpoints/p05/registries/s5r4/")
    if precommit:
        # the staging rehearsal (and the pre-commit positive control) run before record commit (i): the two
        # files this round appends to are still modified in the real work tree. The formal gate post-(i) has
        # precommit=False, so a post-(i) edit to them would still fail.
        allow_files |= {"checkpoints/p05/registries/RULINGS.tsv", "checkpoints/p05/registries/s5r2/ERRATA_S5.txt"}
    def modified_ok():
        st_lines = [l.rstrip() for l in sh_raw(["git", "status", "--porcelain=v1"]).splitlines() if l.strip()]
        if status_override:
            st_lines = [l.rstrip() for l in rd(status_override).splitlines() if l.strip()]
        bad = []
        for ln in st_lines:
            status, path = ln[:2], ln[3:]
            if path in allow_files:
                continue
            if status.strip() == "??" and any(path.startswith(p) for p in allow_untracked):
                continue
            bad.append(ln)
        record("MODIFIED_TRACKED_LINES", len(st_lines))
        return "ok" if not bad else ";".join(bad[:4])
    safe("MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST", modified_ok, "ok")
    # ---------- D016 inherited (FIX4)
    pre16 = os.path.join(EV3, "PREREG_D016_S5R3.tsv")
    rec16 = read_tsv(os.path.join(EV3, "PREREG_D016_S5R3.tsv.sha256.txt")) if os.path.isfile(os.path.join(EV3, "PREREG_D016_S5R3.tsv.sha256.txt")) else []
    safe("PREREG_D016_PRESENT", lambda: "present" if os.path.isfile(pre16) else "absent", "present")
    if rec16:
        safe("PREREG_D016_SHA_MATCHES_RECORD", lambda: sha_f(pre16), rec16[0]["sha256"])
        safe("PREREG_D016_STATUS_INFLUENCED", lambda: rec16[0]["status"], "INFLUENCED")
    rows16 = read_tsv(pre16) if os.path.isfile(pre16) else []
    safe("PREREG_D016_ROWS_36", lambda: len(rows16), 36)
    safe("PREREG_D016_HAS_EXPECTED_COUNT_COL", lambda: "expected_count" if rows16 and "expected_count" in rows16[0] else "missing", "expected_count")
    safe("PREREG_D016_STDERR_COUNT_ZERO", lambda: ";".join("%s=%s" % (r["point_id"], r["expected_count"]) for r in rows16 if r["point_id"] in ("PY_STDERR_INFO2", "LUA_STDERR_INFO2")), "PY_STDERR_INFO2=0;LUA_STDERR_INFO2=0")
    safe("PREREG_D016_BEFORE_FIRST_FORMAL_RUN", lambda: 1 if 0 < first_line(recs3, "s5r3_prereg.py d016") < first_line(recs3, "d016_run_s5r3.py formal") else 0, "1")
    for passno in ("1", "2"):
        p = os.path.join(EV3, "D016_PASS%s_S5R3.json" % passno)
        safe("D016_PASS%s_PRESENT" % passno, lambda p=p: "present" if os.path.isfile(p) else "absent", "present")
    v16 = os.path.join(EV3, "D016_VERDICT_S5R3.tsv")
    def d16sum():
        if not os.path.isfile(v16):
            return "missing"
        for line in rd(v16).splitlines():
            if line.startswith("SUMMARY" + TAB):
                return line.replace(TAB, " ")
        return "missing"
    safe("D016_VERDICT_SUMMARY", d16sum, "SUMMARY MATCH=33 MISMATCH=0 FLAKY=0")
    def d16rows():
        if not os.path.isfile(v16):
            return -1
        rows = read_tsv(v16)
        counts = {}
        for r in rows:
            counts[r.get("verdict", "?")] = counts.get(r.get("verdict", "?"), 0) + 1
        record("D016_VERDICT_ROWS", len(rows))
        record("D016_VERDICT_COUNTS", ";".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
        return "%d/%s" % (len(rows), "MATCH=33,RECORD=1" if counts.get("MATCH") == 33 and counts.get("RECORD") == 1 else "bad")
    safe("D016_VERDICT_ROWS_34", d16rows, "34/MATCH=33,RECORD=1")
    pc16 = os.path.join(EV3, "POSCTRL_D016_S5R3.txt")
    safe("D016_POSCTRL_5_OF_5", lambda: (re.search(r"OVERALL_POSITIVE_CONTROL: (PASS|FAIL) \((\d+)/(\d+)\)", rd(pc16)).groups() if os.path.isfile(pc16) else ("MISSING", "0", "0")), ("PASS", "5", "5"))
    # ---------- E2E inherited (EV3)
    pre2 = os.path.join(EV3, "PREREG_E2E_S5R3.tsv")
    rec2 = read_tsv(os.path.join(EV3, "PREREG_E2E_S5R3.tsv.sha256.txt")) if os.path.isfile(os.path.join(EV3, "PREREG_E2E_S5R3.tsv.sha256.txt")) else []
    rows2 = read_tsv(pre2) if os.path.isfile(pre2) else []
    safe("PREREG_E2E_42_ROWS", lambda: len(rows2), 42)
    if rec2:
        safe("PREREG_E2E_SHA_MATCHES_RECORD", lambda: sha_f(pre2), rec2[0]["sha256"])
    safe("PREREG_E2E_BEFORE_FIRST_INJECTION_RUN", lambda: 1 if 0 < first_line(recs3, "s5r3_prereg.py e2e") < first_line(recs3, "run_e2e_s5r3.py formal") else 0, "1")
    for passno in ("1", "2"):
        pdir = os.path.join(EV3, "e2e/pass%s/points" % passno)
        safe("E2E_PASS%s_42_POINTS" % passno, lambda pdir=pdir: len([f for f in os.listdir(pdir) if f.endswith(".json")]) if os.path.isdir(pdir) else -1, 42)
    def e2ecounts():
        p_ev = os.path.join(EV3, "E2E_VERDICT_S5R3.tsv")
        if not os.path.isfile(p_ev):
            return "missing"
        c = {}
        for r in read_tsv(p_ev):
            c[r["verdict"]] = c.get(r["verdict"], 0) + 1
        return ";".join("%s=%d" % (k, c[k]) for k in sorted(c))
    safe("E2E_VERDICT_COUNTS", e2ecounts, "CONTROL_OK=17;E2E_OK=25")
    pce = os.path.join(EV3, "POSCTRL_E2E_S5R3.txt")
    safe("E2E_POSCTRL_19_OF_19", lambda: (re.search(r"OVERALL_POSITIVE_CONTROL: (PASS|FAIL) \((\d+)/(\d+)\)", rd(pce)).groups() if os.path.isfile(pce) else ("MISSING", "0", "0")), ("PASS", "19", "19"))
    calp = os.path.join(EV3, "CALIB_E2E_S5R3.tsv")
    safe("CALIB_TARGET_27", lambda: len([r for r in read_tsv(calp) if r["row_kind"] == "TARGET"]), 27)
    cald = read_tsv(os.path.join(EV3, "CALIB_DIFF_S5R3.tsv")) if os.path.isfile(os.path.join(EV3, "CALIB_DIFF_S5R3.tsv")) else []
    def calib_zero():
        bad = [r["key"] + "=" + r["diff"] for r in cald if r["diff"] != "SAME"]
        if bad:
            return ";".join(bad[:4])
        summ = [l for l in rd(os.path.join(EV3, "CALIB_DIFF_S5R3.tsv")).splitlines() if l.startswith("SUMMARY" + TAB)]
        if len(summ) != 1 or "DIFFS=0" not in summ[0]:
            return "summary_missing_or_nonzero"
        return "ok"
    safe("CALIB_DIFF_ZERO", calib_zero, "ok")
    bld = read_kv(os.path.join(EV3, "E2E_BUILD_S5R3.tsv")) if os.path.isfile(os.path.join(EV3, "E2E_BUILD_S5R3.tsv")) else {}
    safe("E2E_BUILD_WRAP_PY", lambda: bld.get("PYEXT_NM_WRAP_DEFINED", "MISSING"), "4/4")
    safe("E2E_BUILD_WRAP_LUA", lambda: bld.get("LUA_FRONTEND_NM_WRAP_DEFINED", "MISSING"), "4/4")
    safe("E2E_BUILD_UNRESOLVED_FFT_ZERO", lambda: bld.get("PYEXT_UNRESOLVED_RAW_FFT", "MISSING") + "/" + bld.get("LUA_FRONTEND_UNRESOLVED_RAW_FFT", "MISSING"), "0/0")
    cp3 = os.path.join(EV3, "COPY_DIFF_S5R3.txt")
    safe("COPY_DIFF_STRICT_UNEXPECTED_ZERO", lambda: (re.search(r"strict_unexpected=(\d+)", rd(cp3)).group(1) if os.path.isfile(cp3) else "MISSING"), "0")
    # ---------- make test inherited (EV3)
    for seg in ("B_p1", "F4_p1", "B_p2", "F4_p2"):
        safe("MAKETEST_%s_LOG_AND_DONE" % seg,
             lambda seg=seg: "ok" if os.path.isfile(os.path.join(EV3, "maketest", seg + ".log")) and os.path.isfile(os.path.join(EV3, "maketest", seg + ".done")) else "missing", "ok")
    mtv = os.path.join(EV3, "MAKETEST_VERDICT_S5R3.tsv")
    mt = read_kv(mtv) if os.path.isfile(mtv) else {}
    safe("MAKETEST_VERDICT_NO_NEW_FAILURE", lambda: mt.get("verdict", "MISSING"), "NO_NEW_FAILURE")
    safe("MAKETEST_UNIT_COUNT_265", lambda: mt.get("unit_count", "MISSING"), "265")
    def recon():
        bad = []
        n = 0
        if os.path.isfile(mtv):
            for line in rd(mtv).splitlines():
                f = line.split(TAB)
                if len(f) >= 8 and f[0] == "reconcile":
                    n += 1
                    if f[7] != "OK":
                        bad.append(line)
        return "ok_8" if n == 8 and not bad else "rows=%d bad=%d" % (n, len(bad))
    safe("MAKETEST_RECONCILE_ALL_OK", recon, "ok_8")
    pcm = os.path.join(EV3, "POSCTRL_MAKETEST_S5R3.txt")
    safe("MAKETEST_POSCTRL_4_OF_4", lambda: (re.search(r"OVERALL_POSITIVE_CONTROL: (PASS|FAIL) \((\d+)/(\d+)\)", rd(pcm)).groups() if os.path.isfile(pcm) else ("MISSING", "0", "0")), ("PASS", "4", "4"))
    # ---------- REJUDGE_S5R4 (new)
    rjp = os.path.join(EV, "REJUDGE_S5R4.tsv")
    def rej_summary():
        d = {}
        for line in rd(rjp).splitlines() if os.path.isfile(rjp) else []:
            if line.startswith("SUMMARY" + TAB):
                for x in line.split(TAB)[1:]:
                    k, _, v = x.partition("=")
                    d[k] = v
        return d
    desc = rej_summary() if os.path.isfile(rjp) else {}
    safe("REJUDGE_S5R4_PRESENT", lambda: "present" if os.path.isfile(rjp) else "absent", "present")
    safe("REJUDGE_S5R4_DIFFS_ZERO", lambda: desc.get("DIFFS", "MISSING"), "0")
    safe("REJUDGE_S5R4_E2E_ROWS_42", lambda: desc.get("E2E_ROWS", "MISSING"), "42")
    safe("REJUDGE_S5R4_D016_ROWS", lambda: "%s/%s" % (desc.get("D016_REJUDGED_ROWS", "?"), desc.get("D016_NOT_JUDGED", "?")), "33/1")
    safe("REJUDGE_S5R4_D016_RECORDED_34", lambda: desc.get("D016_RECORDED_ROWS", "MISSING"), "34")
    def rej_all_same():
        if not os.path.isfile(rjp):
            return "missing"
        rows = read_tsv(rjp)
        judged = [r for r in rows if r.get("match") == "SAME"]
        diff = [r for r in rows if r.get("match") == "DIFF"]
        nrec = [r for r in rows if r.get("rejudged_verdict") == "NOT_JUDGED_SOURCE_RECORD"]
        return "%d/%d/%d" % (len(judged), len(diff), len(nrec))
    safe("REJUDGE_S5R4_MATCH_COUNTS", rej_all_same, "75/0/1")
    pre_rj = os.path.join(EV, "PREREG_REJUDGE_S5R4.tsv")
    safe("PREREG_REJUDGE_PRESENT", lambda: "present" if os.path.isfile(pre_rj) else "absent", "present")
    pre_rec = read_tsv(os.path.join(EV, "PREREG_REJUDGE_S5R4.tsv.sha256.txt")) if os.path.isfile(os.path.join(EV, "PREREG_REJUDGE_S5R4.tsv.sha256.txt")) else []
    if pre_rec:
        safe("PREREG_REJUDGE_SHA_MATCHES_RECORD", lambda: sha_f(pre_rj), pre_rec[0]["sha256"])
        safe("PREREG_REJUDGE_STATUS_INFLUENCED", lambda: pre_rec[0]["status"], "INFLUENCED")
    def prereg_inputs_ok():
        if not os.path.isfile(pre_rj):
            return "missing"
        sums = listed_map(os.path.join(EV3, "SHA256SUMS.txt"))
        bad = []
        n = 0
        for r in read_tsv(pre_rj):
            if r.get("row_kind") != "INPUT":
                continue
            n += 1
            rel = r["key"]
            p = os.path.join(EV3, rel)
            if not os.path.isfile(p) or sha_f(p) != r["sha256"]:
                bad.append(rel)
            elif rel in sums and sums[rel] != r["sha256"]:
                bad.append(rel + ":sums")
        return "ok_%d" % n if not bad else ",".join(bad[:3])
    safe("REJUDGE_INPUT_SHAS_MATCH_S5R3", prereg_inputs_ok, "ok_91")
    def prereg_order():
        prline = first_line(recs, "s5r4_prereg.py")
        frline = -1
        for i, ts, cmd in recs:
            if "rejudge_s5r4.py formal" in cmd and "REJUDGE_S5R4.tsv" in cmd:
                frline = i
                break
        return 1 if 0 < prline < frline else 0
    safe("PREREG_REJUDGE_BEFORE_FIRST_FORMAL_REJUDGE", prereg_order, "1")
    pcr = os.path.join(EV, "POSCTRL_REJUDGE_S5R4.txt")
    safe("REJUDGE_POSCTRL_4_OF_4", lambda: (re.search(r"OVERALL_POSITIVE_CONTROL: (PASS|FAIL) \((\d+)/(\d+)\)", rd(pcr)).groups() if os.path.isfile(pcr) else ("MISSING", "0", "0")), ("PASS", "4", "4"))
    scr = os.path.join(EV, "SELFTEST_REJUDGE_S5R4.txt")
    safe("REJUDGE_SELFTEST_6_OF_6", lambda: (re.search(r"OVERALL_SELFTEST: (PASS|FAIL) \((\d+)/(\d+)\)", rd(scr)).groups() if os.path.isfile(scr) else ("MISSING", "0", "0")), ("PASS", "6", "6"))
    # ---------- R3 gate recheck (new)
    r3c = os.path.join(EV, "R3_GATE_RECHECK_S5R4.tsv")
    r3rows = read_tsv(r3c) if os.path.isfile(r3c) else []
    safe("R3_GATE_RECHECK_ROWS_8", lambda: len(r3rows), 8)
    safe("R3_GATE_RECHECK_NAMES", lambda: "|".join(sorted(r["fail_name"] for r in r3rows)), "|".join(R3_FAIL_NAMES))
    safe("R3_GATE_RECHECK_ALL_PASS", lambda: "ok" if all(r.get("r4_result") == "PASS" for r in r3rows) and len(r3rows) == 8 else "bad", "ok")
    safe("R3_GATE_RECHECK_CAUSE_CLASSES", lambda: ",".join(sorted(set(r["cause_class"] for r in r3rows))), ",".join(sorted(CAUSE_CLASSES.split(","))))
    def r3_data_sha():
        sums = listed_map(os.path.join(EV3, "SHA256SUMS.txt"))
        bad = []
        for r in r3rows:
            rel = r["data_file"]
            if rel.startswith("registries/") or rel.startswith("r3_final/"):
                p = r3_data_path(rel)
            else:
                p = os.path.join(EV3, rel)
            if not p or not os.path.isfile(p) or sha_f(p) != r["data_sha256"]:
                bad.append(rel)
        return "ok" if not bad else ",".join(bad[:3])
    def r3_data_path(rel):
        if rel.startswith("r3_final/"):
            return os.path.join(EV, rel)
        if rel == "registries/RULINGS.tsv":
            return os.path.join(EV, "r3_final/RULINGS_S5R3_FINAL.tsv")
        if rel.startswith("registries/"):
            return os.path.join(P05, rel)
        return None
    safe("R3_GATE_RECHECK_DATA_SHA_UNCHANGED", r3_data_sha, "ok")
    # ---------- R3 immutability (new)
    safe("R3_EVIDENCE_SUMS_SHA_UNCHANGED", lambda: sha_f(os.path.join(EV3, "SHA256SUMS.txt")), srec.get("S5R3_EVIDENCE_SUMS_SHA256"))
    def r3_ev_sums():
        v = verify_sums_dir(EV3)
        return "%d/%s" % (v[0], "OK" if not v[1] else "BAD") if v else "MISSING"
    safe("R3_EVIDENCE_SUMS_ALL_OK_382", r3_ev_sums, "382/OK")
    safe("R3_GATE_END_SHA_UNCHANGED", lambda: sha_f(os.path.join(EV3, "gate/GATE_S5R3_end.txt")), srec.get("S5R3_GATE_END_SHA256"))
    safe("R3_REGISTRY_SUMS_SHA_UNCHANGED", lambda: sha_f(os.path.join(P05, "registries/s5r3/SHA256SUMS.txt")), srec.get("S5R3_REGISTRY_SUMS_SHA256"))
    def r3_frozen():
        fz3 = os.path.join(EV3, "FROZEN_SCRIPTS_S5R3.tsv")
        if sha_f(fz3) != srec.get("S5R3_FROZEN_SHA256"):
            return "list_sha"
        bad = [r["path"] for r in read_tsv(fz3) if not os.path.isfile(os.path.join(REPO, r["path"])) or sha_f(os.path.join(REPO, r["path"])) != r["sha256"]]
        return "ok" if not bad else "bad_%d" % len(bad)
    safe("R3_SCRIPTS_SHA_UNCHANGED", r3_frozen, "ok")
    safe("R3_REPORT_SHA_UNCHANGED", lambda: sha_f(os.path.join(P05, "P05_S5R3_REPORT.md")), srec.get("R3_REPORT_SHA256"))
    safe("R3_DRAFT_V1_SHA_UNCHANGED", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT.md")), srec.get("DRAFT_V1_SHA256"))
    # ---------- readiness (new)
    rp = os.path.join(EV, "READINESS_S5R4.tsv")
    rrows = read_tsv(rp, skip_first=()) if os.path.isfile(rp) else []
    safe("READINESS_PRESENT", lambda: "present" if os.path.isfile(rp) else "absent", "present")
    safe("READINESS_GAP_ZERO", lambda: sum(1 for r in rrows if r.get("status") == "GAP"), 0)
    def rd_meta():
        d = {}
        for line in rd(rp).splitlines() if os.path.isfile(rp) else []:
            if line.startswith("# META" + TAB):
                for x in line.split(TAB)[1:]:
                    k, _, v = x.partition("=")
                    d[k] = v
        return d
    meta = rd_meta() if os.path.isfile(rp) else {}
    safe("READINESS_STATE_BYTES_MATCH", lambda: meta.get("STATE_BYTES", "MISSING"), str(len(st)))
    safe("READINESS_STATE_SHA_MATCH", lambda: meta.get("STATE_SHA256", "MISSING"), sha_b(st))
    def rd_after_state():
        if not os.path.isfile(rp) or not os.path.isfile(stp):
            return "missing"
        return 1 if os.path.getmtime(rp) > os.path.getmtime(stp) else 0
    safe("READINESS_AFTER_FINAL_STATE", rd_after_state, "1")
    def rd_consistency():
        for r in rrows:
            if r.get("item") == "CONSISTENCY":
                note = r.get("note", "")
                need = ["33", "265", "NO_NEW_FAILURE", "DIFFS=0", "GAP=0", "26/26"]
                miss = [k for k in need if k not in note]
                return "ok" if not miss else ",".join(miss)
        return "row_missing"
    safe("READINESS_CONSISTENCY_ROW", rd_consistency, "ok")
    def rd_red():
        red = [r for r in rrows if r.get("row_kind") == "RED_POINT"]
        met = [r for r in red if r.get("status") == "MET"]
        return "%d/%d" % (len(met), len(red))
    safe("READINESS_RED_POINT_26_26", rd_red, "26/26")
    def rd_items():
        items = set(r.get("item") for r in rrows if r.get("row_kind") == "SUMMARY")
        need = {"OPEN_ITEMS", "PENDING_RUNS", "CONSISTENCY", "MAKETEST", "PREREG_MATRIX", "E2E_CHAINS",
                "REGISTRY_COMPLETION", "SHAKEDOWN"}
        return "ok" if need <= items else ",".join(sorted(need - items))
    safe("READINESS_SUMMARY_ITEMS", rd_items, "ok")
    # ---------- acceptance (new + inherited S5R3)
    ap4 = os.path.join(EV, "P05_ACCEPTANCE_MAP_S5R4.tsv")
    safe("ACCEPTANCE_S5R4_ALL_MET", lambda: sum(1 for r in (read_tsv(ap4) if os.path.isfile(ap4) else []) if r.get("status") != "MET") if os.path.isfile(ap4) else -1, 0)
    ap3 = os.path.join(EV3, "P05_ACCEPTANCE_MAP_S5R3.tsv")
    safe("ACCEPTANCE_S5R3_ALL_MET", lambda: sum(1 for r in (read_tsv(ap3) if os.path.isfile(ap3) else []) if r.get("status") != "MET") if os.path.isfile(ap3) else -1, 0)
    # ---------- sign-off draft v2 (new)
    d2 = os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v2.md")
    safe("SIGNOFF_DRAFT_V2_PRESENT", lambda: "present" if os.path.isfile(d2) else "absent", "present")
    d2t = rd(d2) if os.path.isfile(d2) else ""
    safe("SIGNOFF_V2_UNSIGNED", lambda: 1 if "未签收" in d2t else 0, "1")
    safe("SIGNOFF_V2_REJUDGE_MEASURED", lambda: 1 if ("REJUDGE_S5R4" in d2t and "DIFFS=0" in d2t and "42" in d2t and "33" in d2t) else 0, "1")
    safe("SIGNOFF_V2_NO_COMPLETION_CLAIM", lambda: 0 if any(k in d2t for k in ("已签收", "P05 完成", "P05-S5 完成")) else 1, "1")
    # ---------- registry (new)
    reg = os.path.join(P05, "registries/s5r4")
    exp = os.path.join(reg, "REGISTRY_EXPECTED_S5R4.txt")
    safe("REGISTRY_EXPECTED_PRESENT", lambda: "present" if os.path.isfile(exp) else "absent", "present")
    def reg_expected():
        if not os.path.isfile(exp):
            return "missing"
        sums = listed_map(os.path.join(reg, "SHA256SUMS.txt"))
        bad = []
        n = 0
        for line in rd(exp).splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            n += 1
            f = line.split(TAB) if TAB in line else line.split()
            rel, want = f[0], f[1]
            p = os.path.join(reg, rel)
            if not os.path.isfile(p) or sha_f(p) != want or sums.get(rel) != want:
                bad.append(rel)
        return "ok_%d" % n if not bad else ",".join(bad[:3])
    safe("REGISTRY_EXPECTED_ALL_IN_SUMS", reg_expected, "ok_13")
    def reg_unlisted():
        if not os.path.isdir(reg):
            return "missing"
        sums = listed_map(os.path.join(reg, "SHA256SUMS.txt"))
        files = set()
        for root, dirs, fs in os.walk(reg):
            for f in fs:
                rel = os.path.relpath(os.path.join(root, f), reg)
                if rel in ("SHA256SUMS.txt", "GATE_S5R4_end.txt"):
                    continue
                if rel.startswith("s5r3_completion/"):
                    continue   # verified by REGISTRY_S5R3_COMPLETION_SUMS_OK
                files.add(rel)
        miss = sorted(files - set(sums))
        extra = sorted(set(sums) - files)
        return "ok" if not miss and not extra else "miss=%s extra=%s" % (miss[:3], extra[:3])
    safe("REGISTRY_NO_UNLISTED_FILES", reg_unlisted, "ok")
    comp = os.path.join(reg, "s5r3_completion")
    def comp7():
        if not os.path.isdir(comp):
            return "missing"
        miss = [f for f in S5R3_COMPLETION_7 if not os.path.isfile(os.path.join(comp, f))]
        return "ok" if not miss else ",".join(miss)
    safe("REGISTRY_S5R3_COMPLETION_7_ITEMS", comp7, "ok")
    def comp_sums():
        v = verify_sums_dir(comp)
        return "%d/%s" % (v[0], "OK" if not v[1] else "BAD") if v else "MISSING"
    safe("REGISTRY_S5R3_COMPLETION_SUMS_OK", comp_sums, "8/OK")
    def comp19():
        sums3 = listed_map(os.path.join(EV3, "SHA256SUMS.txt"))
        supp = {}
        for r in read_tsv(os.path.join(EV3, "S5R2_SUPPLEMENT_COPY_S5R3.tsv"), skip_first=()):
            if r.get("file", "").endswith((".tsv", ".txt")):
                supp[r["file"]] = r["sha256_copy"]
        reg3 = os.path.join(P05, "registries/s5r3")
        bad = []
        for rel in R3_DELIVERED_19:
            p = os.path.join(reg3, rel)
            want = supp.get(os.path.basename(rel)) if rel.startswith("s5r2_supplement/") else sums3.get(rel)
            if not os.path.isfile(p) or want != sha_f(p):
                bad.append(rel)
        return "ok_19" if not bad else ",".join(bad[:3])
    safe("REGISTRY_S5R3_19_SHA_MATCH", comp19, "ok_19")
    def comp26():
        readme = os.path.join(comp, "README.md")
        if not os.path.isfile(readme):
            return "missing_readme"
        t = rd(readme)
        v = verify_sums_dir(comp)
        rows = v[0] if v else 0
        return "ok" if ("26/26" in t and rows == 8) else "readme=%s rows=%d" % ("26/26" in t, rows)
    safe("REGISTRY_S5R3_COVERAGE_26_26", comp26, "ok")
    safe("REGISTRY_REG3_UNCHANGED_SHA", lambda: sha_f(os.path.join(P05, "registries/s5r3/SHA256SUMS.txt")), srec.get("S5R3_REGISTRY_SUMS_SHA256"))
    # ---------- registry patch (new; chained R3 -> R4)
    rda3 = os.path.join(EV3, "REGISTRY_APPLY_DIFF_S5R3.txt")
    rda = os.path.join(EV, "REGISTRY_APPLY_DIFF_S5R4.txt")
    def rda_assert():
        t = rd(rda) if os.path.isfile(rda) else ""
        return "PASS" if "# ASSERT_ONLY_LISTED_LINES_CHANGED: PASS" in t else "FAIL"
    safe("REGISTRY_APPLY_ASSERT_ONLY_LISTED", rda_assert, "PASS")
    def rda_meta(p):
        d = {}
        for line in rd(p).splitlines() if os.path.isfile(p) else []:
            m = re.match(r"FILE (testing/s4test/ISSUE_REGISTRY.md|PROJECT_ROADMAP.md) before_bytes=(\d+) after_bytes=(\d+) before_sha256=([0-9a-f]{64}) after_sha256=([0-9a-f]{64})", line)
            if m:
                d[m.group(1)] = m.groups()[1:]
        return d
    m3, m4 = rda_meta(rda3), rda_meta(rda)
    safe("REGISTRY_ISSUE_SHA_MATCHES_AFTER", lambda: sha_f(os.path.join(STAGE, "testing/s4test/ISSUE_REGISTRY.md")), (m4.get("testing/s4test/ISSUE_REGISTRY.md") or [None, None, None, "MISSING"])[3])
    safe("REGISTRY_ROADMAP_SHA_MATCHES_AFTER", lambda: sha_f(os.path.join(STAGE, "PROJECT_ROADMAP.md")), (m4.get("PROJECT_ROADMAP.md") or [None, None, None, "MISSING"])[3])
    def r3_to_r4_chain():
        ok = []
        for f in ("testing/s4test/ISSUE_REGISTRY.md", "PROJECT_ROADMAP.md"):
            a = (m3.get(f) or [None, None, None, None])[3]
            b = (m4.get(f) or [None, None, None, None])[2]
            ok.append(a is not None and a == b)
        return "ok" if all(ok) else "mismatch"
    safe("REGISTRY_R3_TO_R4_CHAIN", r3_to_r4_chain, "ok")
    iss = rd(os.path.join(STAGE, "testing/s4test/ISSUE_REGISTRY.md"))
    rdm = rd(os.path.join(STAGE, "PROJECT_ROADMAP.md"))
    safe("REGISTRY_ISSUE_HAS_ES5_9", lambda: 1 if "ES5-9" in iss and "S5R4" in iss else 0, "1")
    safe("REGISTRY_ROADMAP_HAS_S5R4", lambda: 1 if "ES5-9" in rdm and "S5R4" in rdm else 0, "1")
    # ---------- report (new)
    rp4 = os.path.join(P05, "P05_S5R4_REPORT.md")
    safe("REPORT_PRESENT", lambda: "present" if os.path.isfile(rp4) else "absent", "present")
    rchk = os.path.join(EV, "REPORT_CHECK_S5R4.txt")
    safe("REPORT_CHECK_FAILS_ZERO", lambda: (re.search(r"FAILS=(\d+)", rd(rchk)).group(1) if os.path.isfile(rchk) else "MISSING"), "0")
    rt = rd(rp4) if os.path.isfile(rp4) else ""
    def report_final_status():
        m = re.search(r"FINAL_STATUS=([A-Z_]+)", rt)
        return m.group(1) if m else "MISSING"
    safe("REPORT_FINAL_STATUS_MARKER", report_final_status, "PENDING_GATE")
    safe("REPORT_VERDICT_LINE", lambda: 1 if "本轮 P05-S5 R4 范围证据已生成" in rt else 0, "1")
    safe("REPORT_SIGNOFF_DRAFT_V2_REF", lambda: 1 if "P05_S5_SIGNOFF_DRAFT_v2.md" in rt else 0, "1")
    safe("REPORT_APPENDICES_AB", lambda: 1 if ("附录 A" in rt and "附录 B" in rt) else 0, "1")
    def report_deliv():
        if not os.path.isdir(reg):
            return "missing"
        v = verify_sums_dir(reg)
        n = v[0] if v else 0
        m = re.search(r"交付物数量=([0-9]+)", rt)
        return "ok" if (m and int(m.group(1)) == n) else "reg=%d report=%s" % (n, m.group(1) if m else "MISSING")
    safe("REPORT_DELIVERABLES_COUNT_FROM_REGISTRY", report_deliv, "ok")
    safe("REPORT_CHECK_STATE_BYTES_LE_8192", lambda: (re.search(r"STATE_BYTES=(\d+)", rd(rchk)).group(1) if os.path.isfile(rchk) else "MISSING"), str(len(st)))
    # ---------- copy diff of the gate itself (new)
    cp4 = os.path.join(EV, "COPY_DIFF_S5R4.txt")
    def copy4():
        if not os.path.isfile(cp4):
            return "MISSING"
        m = re.search(r"strict_unexpected=(\d+)", rd(cp4))
        return m.group(1) if m else "MISSING"
    safe("COPY_DIFF_S5R4_GATE_DECLARED_ONLY", copy4, "0")
    # ---------- evidence manifest (inherited, EV4)
    def ev_ok():
        v = verify_sums_dir(EV)
        if not v:
            return "MISSING"
        return "OK" if not v[1] and v[0] > 0 else "BAD"
    safe("EVIDENCE_SHA256SUMS_OK", ev_ok, "OK")
    evsum = os.path.join(EV, "SHA256SUMS.txt")
    def ev_cover():
        if not os.path.isfile(evsum):
            return "MISSING"
        listed = set(listed_map(evsum))
        actual = set()
        for root, dirs, files in os.walk(EV):
            dirs[:] = sorted(d for d in dirs if d not in ("tmp", "gate", "trees", "shakedown"))
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), EV)
                if rel in ("safe_run.log", "SHA256SUMS.txt"):
                    continue
                actual.add(rel)
        miss = sorted(actual - listed)
        extra = sorted(listed - actual)
        record("EVIDENCE_ITEMS", len(actual))
        return "missing=%s extra=%s" % (miss[:3] or "none", extra[:3] or "none")
    safe("EVIDENCE_SUMS_COVERS_ALL", ev_cover, "missing=none extra=none")
    def trunc_ok():
        if not os.path.isfile(evsum):
            return "MISSING"
        m = re.search(r"safe_run.log up to line (\d+)", rd(evsum))
        a = first_line(post, "s5r4_sha_sums.py formal")
        if not m or a <= 0:
            return "anchor=%d trunc=%s" % (a, m.group(1) if m else "missing")
        return "OK" if int(m.group(1)) == a else "trunc=%s anchor=%d" % (m.group(1), a)
    safe("EVIDENCE_SUMS_TRUNC_LINE_IS_SHA_SUMS_CALL", trunc_ok, "OK")
    # ---------- events (inherited, EV4)
    evp2 = os.path.join(EV, "EVENTS_S5R4.tsv")
    def ev_rows():
        if not os.path.isfile(evp2):
            return "MISSING"
        anchor = first_line(post, "s5r4_events.py formal")
        rows = {}
        for line in rd(evp2).splitlines():
            if line.startswith("#") or line.startswith("log_line"):
                continue
            f = line.split(TAB)
            rows[int(f[0])] = f[1]
        need = {}
        parent = ""
        ts_re = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")
        ls = rd(LOG).splitlines()
        for x in range(1, anchor + 1):
            m = ts_re.match(ls[x - 1])
            if m:
                parent = m.group(1)
            need[x] = parent
        return "OK" if rows == need and anchor > 0 else "rows=%d need=%d anchor=%d" % (len(rows), len(need), anchor)
    safe("EVENTS_ROW_SET_EQ_RECOMPUTATION", ev_rows, "OK")
    # ---------- tmp snapshot / other evidence (inherited)
    def tmp_snap():
        names = sorted(os.listdir("/tmp"))
        return "%d/%s" % (len(names), sha_b((NL.join(names) + NL).encode("utf-8")))
    safe("TMP_SNAPSHOT_UNCHANGED", tmp_snap, "%s/%s" % (srec.get("TMP_COUNT", "?"), srec.get("TMP_SHA256", "?")))
    def other_ev():
        start_epoch = epoch_of(srec.get("START_TIME_UTC", "2000-01-01T00:00:00Z"))
        bad = []
        evdir = os.path.join(P05_REAL, "evidence")
        for d in sorted(os.listdir(evdir)):
            if d in ("p05-s5r4",) or not d.startswith("p05-"):
                continue
            p = os.path.join(evdir, d)
            if not os.path.isdir(p):
                continue
            newest = 0
            for root, dirs, files in os.walk(p):
                for f in files:
                    try:
                        newest = max(newest, os.path.getmtime(os.path.join(root, f)))
                    except OSError:
                        pass
            if newest > start_epoch:
                bad.append(d)
        return "none" if not bad else ",".join(bad[:3])
    safe("OTHER_ROUND_EVIDENCE_UNTOUCHED", other_ev, "none")
    # ---------- shakedown (U381) and formal run-once (new)
    def shak():
        rec_path = os.path.join(EV4_REAL, "shakedown/SHAKEDOWN_REHEARSAL.txt")
        out_path = os.path.join(EV4_REAL, "shakedown/gate/GATE_S5R4_end.txt")
        if os.path.realpath(outp) == os.path.realpath(out_path):
            # we are inside the shakedown gate run: its own output cannot be read yet; validate the
            # rehearsal record the chain wrote before invoking this gate (the formal gate re-checks the output)
            if not os.path.isfile(rec_path):
                return "rehearsal_record_missing"
            t = rd(rec_path)
            return "PASS" if ("STAGING_EV_ROOT=" in t and "POST_I_FROM=" in t and "STAGED_STEPS=" in t) else "rehearsal_record_bad"
        if not os.path.isfile(out_path):
            return "shakedown_output_missing"
        t = rd(out_path)
        mf = re.search(r"FAILS=(\d+)", t)
        mc = re.search(r"CHECK_CRASHED=(\d+)", t)
        if not mf or not mc:
            return "unparsed"
        return "PASS" if (mf.group(1) == "0" and mc.group(1) == "0") else "fails=%s crashed=%s" % (mf.group(1), mc.group(1))
    safe("SHAKEDOWN_GATE_FAILS_ZERO", shak, "PASS")
    shakf = os.path.join(EV4_REAL, "shakedown/gate/GATE_S5R4_end.txt")
    def shak_roots():
        if os.path.realpath(outp) == os.path.realpath(shakf):
            rec_path = os.path.join(EV4_REAL, "shakedown/SHAKEDOWN_REHEARSAL.txt")
            return "ok" if os.path.isfile(rec_path) else "missing"
        if not os.path.isfile(shakf):
            return "missing"
        return "ok" if "STAGING_MODE" + TAB + "yes" in rd(shakf) else "not_staging"
    safe("SHAKEDOWN_USED_STAGING_ROOTS", shak_roots, "ok")
    def chain_marker():
        m = os.path.join(EV, "FORMAL_CHAIN_RAN.txt")
        if not os.path.isfile(m):
            return "missing"
        txt = rd(m)
        line = None
        mm = re.search(r"^LOG_LINE=(\d+)$", txt, re.M)
        if mm:
            line = int(mm.group(1))
        if line is None or not (0 < line <= len(recs)):
            return "bad_line"
        cmd = recs[line - 1][2]
        return "ok" if "s5r4_chain.py formal" in cmd else cmd[:80]
    safe("CHAIN_FORMAL_RAN_ONCE", chain_marker, "ok")
    def end_gate_first_run():
        formal_out = os.path.join(EV4_REAL, "gate/GATE_S5R4_end.txt")
        # the formal output must not exist before a formal gate run starts (end gate runs exactly once)
        return "absent" if not os.path.isfile(formal_out) else "present"
    safe("END_GATE_FIRST_FORMAL_RUN", end_gate_first_run, "absent")
    # ---------- single-check mode (positive control of one fixed check)
    if only:
        CHECKS[:] = [c for c in CHECKS if c[0] == only]
        CRASHED[:] = [(n, x) for (n, x) in CRASHED if n == only]
        record("ONLY_CHECK", only)
    # ---------- final
    fails = [c for c in CHECKS if not c[3]]
    lines = ["# P05-S5 R4 end gate GATE_S5R4_end.txt (" + started + ")"]
    lines += ["RECORD" + TAB + k + TAB + "value=" + v for k, v in RECORDS]
    for (n, e, a, ok) in CHECKS:
        lines.append(("PASS" if ok else "FAIL") + TAB + n + TAB + "expected=" + e + TAB + "actual=" + a)
    lines.append("COUNTS" + TAB + "pass=%d" % (len(CHECKS) - len(fails)) + TAB + "fail=%d" % len(fails) + TAB + "total=%d" % len(CHECKS))
    lines.append("FAILS=%d" % len(fails))
    lines.append("CHECK_CRASHED=%d" % len(CRASHED))
    for n, x in CRASHED:
        lines.append("CRASHED" + TAB + n + TAB + x)
    open(outp, "w", encoding="utf-8").write(NL.join(lines) + NL)
    for l in lines:
        print(l)
    print("WROTE " + outp)
    return 0 if not fails and not CRASHED else 1


if __name__ == "__main__":
    sys.exit(main())
