#!/usr/bin/env python3
# gate_check_s5r3.py -- P05-S5 R3 end gate. usage:
#   gate_check_s5r3.py end [--commit-i SHA|HEAD] [--out PATH]
# Every script name used for call counting is read from FROZEN_SCRIPTS_S5R3.tsv by column name.
# A shakedown run passes --commit-i HEAD: all log lines are then "post (i)" and several assertions are
# expected to FAIL (formal results / commit (i) do not exist yet); CHECK_CRASHED=0 is the shakedown criterion.
import os, sys, re, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)
EXP_BRANCH = "codex/p05-d003-fft-error-propagation"
EXP_BASE = "29dfd1c04e18d351e72d50f57deb0299f8f74d08"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
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
        CRASHED.append((name, repr(exc)))
        actual = "EXC:" + repr(exc)[:160]
    ok = str(actual) == str(exp)
    CHECKS.append((name, exp, actual, ok))


def read_tsv(p):
    rows = []
    hdr = None
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
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


def start_records():
    d = {}
    p = os.path.join(EV, "GATE_S5R3_start.txt")
    if os.path.isfile(p):
        for line in rd(p).splitlines():
            if line.startswith("RECORD" + TAB):
                f = line.split(TAB)
                d[f[1]] = f[2].replace("value=", "")
    return d


def log_records():
    p = os.path.join(EV, "safe_run.log")
    recs = []
    if not os.path.isfile(p):
        return recs
    for i, line in enumerate(rd(p).splitlines(), 1):
        m = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t(.*)$", line)
        if not m:
            continue
        ts = m.group(1)
        rest = m.group(2)
        idx = rest.find(TAB + "cmd=")
        cmd = rest[idx + 5:] if idx >= 0 else rest
        recs.append((i, ts, cmd))
    return recs


def epoch_of(ts):
    return int(datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc).timestamp())


def count_calls(recs, relpath, mode, min_epoch):
    n = 0
    for i, ts, cmd in recs:
        if epoch_of(ts) < min_epoch:
            continue
        if relpath not in cmd:
            continue
        if mode != "-" and mode not in cmd:
            continue
        n += 1
    return n


def first_line(recs, needle, min_epoch=0):
    for i, ts, cmd in recs:
        if epoch_of(ts) < min_epoch:
            continue
        if needle in cmd:
            return i
    return -1


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] != "end":
        print("usage: gate_check_s5r3.py end [--commit-i SHA|HEAD] [--out PATH]")
        return 2
    outp = os.path.join(EV, "gate/GATE_S5R3_end.txt")
    if "--out" in argv:
        outp = argv[argv.index("--out") + 1]
    override = None
    if "--commit-i" in argv:
        override = argv[argv.index("--commit-i") + 1]
    os.makedirs(os.path.dirname(outp), exist_ok=True)
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    recs = log_records()
    srec = start_records()
    record("END_TIME_UTC", started)
    record("GATE_SCRIPT", "testing/d003/stage_s5r3/gate_check_s5r3.py")
    # ---------- baseline
    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), EXP_BRANCH)
    safe("HEAD_S4_TREE_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("JUDGE_SHA256", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    safe("F2_S4_TREE", lambda: sh(["git", "rev-parse", "a07b5ac:S4"]), "e124925f5b242486a913b813fa181664f665b048")
    safe("B_S4_TREE", lambda: sh(["git", "rev-parse", "37a82e8:S4"]), "1d738e64f9864a475fdb3de34cd3601605df2c64")
    safe("S4_DIR_ZERO_MODIFICATION", lambda: sh(["git", "diff", "--name-only", "HEAD", "--", "S4"]) or "unmodified", "unmodified")
    # ---------- start gate
    sp = os.path.join(EV, "GATE_S5R3_start.txt")
    safe("START_GATE_PRESENT", lambda: "present" if os.path.isfile(sp) else "absent", "present")
    safe("START_GATE_FAILS_ZERO", lambda: re.search(r"FAILS=(\d+)", rd(sp)).group(1), "0")
    safe("START_GATE_CRASHED_ZERO", lambda: re.search(r"CHECK_CRASHED=(\d+)", rd(sp)).group(1), "0")
    safe("START_RECORDS_PRESENT", lambda: "present" if srec else "absent", "present")
    record("START_TIME_UTC", srec.get("START_TIME_UTC", "?"))
    # ---------- rulings / errata
    rul = os.path.join(P05, "registries/RULINGS.tsv")
    rb = open(rul, "rb").read()
    safe("RULINGS_NOT_TRUNCATED", lambda: 1 if len(rb) >= int(srec["RULINGS_BYTES"]) else 0, "1")
    safe("RULINGS_PREFIX_OF_START_UNCHANGED", lambda: sha_b(rb[:int(srec["RULINGS_BYTES"])]), srec.get("RULINGS_SHA256"))
    mu = "U0"
    fields_ok = True
    for line in rb.decode("utf-8").splitlines():
        f = line.split(TAB)
        if f and f[0].startswith("U") and f[0][1:].isdigit():
            if int(f[0][1:]) > int(mu[1:]):
                mu = f[0]
        if len(f) != 5:
            fields_ok = False
    safe("RULINGS_MAX_U_377", lambda: mu, "U377")
    safe("RULINGS_LINES_5_FIELDS", lambda: 1 if fields_ok else 0, "1")
    err = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
    eb = open(err, "rb").read()
    safe("ERRATA_S5_PREFIX_OF_START_UNCHANGED", lambda: sha_b(eb[:int(srec["ERRATA_S5_BYTES"])]), srec.get("ERRATA_S5_SHA256"))
    last_e = [l for l in eb.decode("utf-8").splitlines() if l.startswith("ES5-")]
    safe("ERRATA_S5_LAST_IS_ES5_8", lambda: last_e[-1] if last_e else "none", "ES5-8")
    # ---------- STATE
    stp = os.path.join(P05, "STATE.md")
    st = open(stp, "rb").read()
    safe("STATE_BYTES_LE_8192", lambda: 1 if len(st) <= 8192 else 0, "1")
    record("STATE_BYTES", len(st))
    smiss = [k for k in ("P05-S5 R3", "未签收", "S5 进行中", "READINESS_S5R3.tsv", "P05_S5_SIGNOFF_DRAFT.md") if k not in st.decode("utf-8")]
    safe("STATE_MARKERS", lambda: 0 if smiss else 1, "1")
    # ---------- commit (i)
    commit_i = override
    if commit_i == "HEAD":
        commit_i = sh(["git", "rev-parse", "HEAD"])
    if not commit_i:
        commit_i = sh(["git", "log", "--grep=P05-S5 R3 (i)", "-1", "--format=%H"])
    record("COMMIT_I_SHA", commit_i or "MISSING")
    record("COMMIT_I_OVERRIDE", "yes" if override else "no")
    safe("COMMIT_I_PRESENT", lambda: 1 if commit_i and re.match(r"^[0-9a-f]{40}$", commit_i or "") else 0, "1")
    commit_epoch = 0
    if commit_i and re.match(r"^[0-9a-f]{40}$", commit_i):
        commit_epoch = int(sh(["git", "log", "-1", "--format=%ct", commit_i]))
    record("COMMIT_I_EPOCH", commit_epoch)
    record("COMMIT_I_SUBJECT", sh(["git", "log", "-1", "--format=%s", commit_i]) if commit_i else "?")
    post = [(i, ts, cmd) for (i, ts, cmd) in recs if (override is not None or epoch_of(ts) >= commit_epoch)]
    record("POST_I_LOG_RECORDS", len(post))
    # ---------- FROZEN
    fz = os.path.join(EV, "FROZEN_SCRIPTS_S5R3.tsv")
    safe("FROZEN_LIST_PRESENT", lambda: "present" if os.path.isfile(fz) else "absent", "present")
    frozen = read_tsv(fz) if os.path.isfile(fz) else []
    record("FROZEN_ROWS", len(frozen))
    frozen_map = {r["path"]: r for r in frozen}
    bad_sha = []
    for r in frozen:
        p = os.path.join(REPO, r["path"])
        if not os.path.isfile(p) or sha_f(p) != r["sha256"]:
            bad_sha.append(r["path"])
    safe("FROZEN_SCRIPTS_SHA_UNCHANGED_END", lambda: 0 if bad_sha else 1, "1")
    if bad_sha:
        record("FROZEN_SHA_BAD", ",".join(bad_sha[:5]))
    bad_counts = []
    for r in frozen:
        actual = count_calls(post, r["path"], r["mode"], commit_epoch)
        if str(actual) != r["expected_calls"]:
            bad_counts.append((r["path"], r["mode"], r["expected_calls"], actual))
    safe("FROZEN_POST_I_CALL_COUNTS_MATCH", lambda: 0 if bad_counts else 1, "1")
    for b in bad_counts[:12]:
        record("CALL_COUNT_DIFF", "%s mode=%s exp=%s act=%s" % b)
    # POST_I foreign writes: post-I safe_run lines with a testing/d003 mention that is not a frozen script call
    frozen_names = [os.path.basename(r["path"]) for r in frozen]
    foreign = []
    for i, ts, cmd in post:
        if "testing/d003" in cmd and not any(nm in cmd for nm in frozen_names):
            foreign.append(i)
    safe("POST_I_NO_TESTING_D003_WRITES", lambda: len(foreign), 0)
    # ---------- committed (i) files unchanged / allow list
    if commit_i and re.match(r"^[0-9a-f]{40}$", commit_i):
        safe("COMMITTED_I_FILES_UNCHANGED_AT_END",
             lambda: sh(["git", "diff", "--name-only", commit_i, "HEAD", "--", "testing/d003"]) or "unmodified", "unmodified")
    allow = {"checkpoints/p05/STATE.md", "checkpoints/p05/P05_S5R3_REPORT.md",
             "testing/s4test/ISSUE_REGISTRY.md", "PROJECT_ROADMAP.md", "checkpoints/p05/P05_S5R3_GATE_APPENDIX.md"}
    def modified_ok():
        st = sh(["git", "status", "--short"])
        bad = []
        for ln in st.splitlines():
            rel = ln[3:]
            if ln[:2].strip() == "??" and (rel.startswith("checkpoints/p05/registries/s5r3/") or rel.startswith("checkpoints/p05/P05_S5_SIGNOFF_DRAFT.md")):
                continue
            if rel in allow:
                continue
            bad.append(ln)
        return "ok" if not bad else ";".join(bad[:4])
    safe("MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST", modified_ok, "ok")
    # ---------- D016
    pre16 = os.path.join(EV, "PREREG_D016_S5R3.tsv")
    rec16 = read_tsv(os.path.join(EV, "PREREG_D016_S5R3.tsv.sha256.txt")) if os.path.isfile(os.path.join(EV, "PREREG_D016_S5R3.tsv.sha256.txt")) else []
    safe("PREREG_D016_PRESENT", lambda: "present" if os.path.isfile(pre16) else "absent", "present")
    if rec16:
        safe("PREREG_D016_SHA_MATCHES_RECORD", lambda: sha_f(pre16), rec16[0]["sha256"])
        safe("PREREG_D016_STATUS_INFLUENCED", lambda: rec16[0]["status"], "INFLUENCED")
    rows16 = read_tsv(pre16) if os.path.isfile(pre16) else []
    safe("PREREG_D016_ROWS", lambda: len(rows16), 36)
    safe("PREREG_D016_HAS_EXPECTED_COUNT_COL", lambda: "expected_count" if rows16 and "expected_count" in rows16[0] else "missing", "expected_count")
    stderr_rows = [r for r in rows16 if r["point_id"] in ("PY_STDERR_INFO2", "LUA_STDERR_INFO2")]
    safe("PREREG_D016_STDERR_COUNT_ZERO", lambda: ";".join("%s=%s" % (r["point_id"], r["expected_count"]) for r in stderr_rows), "PY_STDERR_INFO2=0;LUA_STDERR_INFO2=0")
    p16line = first_line(recs, "s5r3_prereg.py d016")
    f16line = first_line(recs, "d016_run_s5r3.py formal")
    safe("PREREG_D016_BEFORE_FIRST_FORMAL_RUN", lambda: 1 if 0 < p16line < f16line else 0, "1")
    record("PREREG_D016_LINE", p16line)
    record("FIRST_D016_FORMAL_LINE", f16line)
    for passno in ("1", "2"):
        p = os.path.join(EV, "D016_PASS%s_S5R3.json" % passno)
        safe("D016_PASS%s_PRESENT" % passno, lambda p=p: "present" if os.path.isfile(p) else "absent", "present")
    v16 = os.path.join(EV, "D016_VERDICT_S5R3.tsv")
    def d16sum():
        if not os.path.isfile(v16):
            return "missing"
        for line in rd(v16).splitlines():
            if line.startswith("SUMMARY" + TAB):
                return line.replace(TAB, " ")
        return "missing"
    safe("D016_VERDICT_SUMMARY", d16sum, "SUMMARY MATCH=33 MISMATCH=0 FLAKY=0")
    safe("D016_VERDICT_ROWS_34", lambda: len([l for l in rd(v16).splitlines() if l.strip() and not l.startswith("#") and not l.startswith("SUMMARY")]) if os.path.isfile(v16) else -1, 34)
    pc16 = os.path.join(EV, "POSCTRL_D016_S5R3.txt")
    safe("D016_POSCTRL_5_OF_5", lambda: (re.search(r"OVERALL_POSITIVE_CONTROL: (PASS|FAIL) \((\d+)/(\d+)\)", rd(pc16)).groups() if os.path.isfile(pc16) else ("MISSING", "0", "0")), ("PASS", "5", "5"))
    # ---------- E2E
    pre2 = os.path.join(EV, "PREREG_E2E_S5R3.tsv")
    rec2 = read_tsv(os.path.join(EV, "PREREG_E2E_S5R3.tsv.sha256.txt")) if os.path.isfile(os.path.join(EV, "PREREG_E2E_S5R3.tsv.sha256.txt")) else []
    rows2 = read_tsv(pre2) if os.path.isfile(pre2) else []
    safe("PREREG_E2E_42_ROWS", lambda: len(rows2), 42)
    if rec2:
        safe("PREREG_E2E_SHA_MATCHES_RECORD", lambda: sha_f(pre2), rec2[0]["sha256"])
    e2line = first_line(recs, "s5r3_prereg.py e2e")
    f2line = first_line(recs, "run_e2e_s5r3.py formal")
    safe("PREREG_E2E_BEFORE_FIRST_INJECTION_RUN", lambda: 1 if 0 < e2line < f2line else 0, "1")
    for passno in ("1", "2"):
        pdir = os.path.join(EV, "e2e/pass%s/points" % passno)
        safe("E2E_PASS%s_42_POINTS" % passno, lambda pdir=pdir: len([f for f in os.listdir(pdir) if f.endswith(".json")]) if os.path.isdir(pdir) else -1, 42)
    def e2ecounts():
        c = {}
        p_ev = os.path.join(EV, "E2E_VERDICT_S5R3.tsv")
        if not os.path.isfile(p_ev):
            return "missing"
        for line in rd(p_ev).splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            f = line.split(TAB)
            if len(f) >= 5 and f[0] != "point_id":
                c[f[4]] = c.get(f[4], 0) + 1
        return ";".join("%s=%d" % (k, c[k]) for k in sorted(c))
    safe("E2E_VERDICT_COUNTS", e2ecounts, "CONTROL_OK=17;E2E_OK=25")
    pce = os.path.join(EV, "POSCTRL_E2E_S5R3.txt")
    safe("E2E_POSCTRL_19_OF_19", lambda: (re.search(r"OVERALL_POSITIVE_CONTROL: (PASS|FAIL) \((\d+)/(\d+)\)", rd(pce)).groups() if os.path.isfile(pce) else ("MISSING", "0", "0")), ("PASS", "19", "19"))
    calp = os.path.join(EV, "CALIB_E2E_S5R3.tsv")
    safe("CALIB_TARGET_27", lambda: len([r for r in read_tsv(calp) if r["row_kind"] == "TARGET"]), 27)
    cald = read_tsv(os.path.join(EV, "CALIB_DIFF_S5R3.tsv")) if os.path.isfile(os.path.join(EV, "CALIB_DIFF_S5R3.tsv")) else []
    safe("CALIB_DIFF_ZERO", lambda: ";".join(r["key"] + "=" + r["diff"] for r in cald if r["diff"] != "SAME"), "")
    bld = read_kv(os.path.join(EV, "E2E_BUILD_S5R3.tsv")) if os.path.isfile(os.path.join(EV, "E2E_BUILD_S5R3.tsv")) else {}
    safe("E2E_BUILD_WRAP_PY", lambda: bld.get("PYEXT_NM_WRAP_DEFINED", "MISSING"), "4/4")
    safe("E2E_BUILD_WRAP_LUA", lambda: bld.get("LUA_FRONTEND_NM_WRAP_DEFINED", "MISSING"), "4/4")
    safe("E2E_BUILD_UNRESOLVED_FFT_ZERO", lambda: bld.get("PYEXT_UNRESOLVED_RAW_FFT", "MISSING") + "/" + bld.get("LUA_FRONTEND_UNRESOLVED_RAW_FFT", "MISSING"), "0/0")
    cp = os.path.join(EV, "COPY_DIFF_S5R3.txt")
    safe("COPY_DIFF_STRICT_UNEXPECTED_ZERO", lambda: (re.search(r"strict_unexpected=(\d+)", rd(cp)).group(1) if os.path.isfile(cp) else "MISSING"), "0")
    # ---------- make test
    for seg in ("B_p1", "F4_p1", "B_p2", "F4_p2"):
        safe("MAKETEST_%s_LOG_AND_DONE" % seg,
             lambda seg=seg: "ok" if os.path.isfile(os.path.join(EV, "maketest", seg + ".log")) and os.path.isfile(os.path.join(EV, "maketest", seg + ".done")) else "missing", "ok")
    mtv = os.path.join(EV, "MAKETEST_VERDICT_S5R3.tsv")
    mt = read_kv(mtv) if os.path.isfile(mtv) else {}
    safe("MAKETEST_VERDICT_NO_NEW_FAILURE", lambda: mt.get("verdict", "MISSING"), "NO_NEW_FAILURE")
    safe("MAKETEST_UNIT_COUNT_265", lambda: mt.get("unit_count", "MISSING"), "265")
    reconbad = []
    if os.path.isfile(mtv):
        for line in rd(mtv).splitlines():
            f = line.split(TAB)
            if len(f) >= 8 and f[0] == "reconcile" and f[7] != "OK":
                reconbad.append(line)
    safe("MAKETEST_RECONCILE_ALL_OK", lambda: len(reconbad), 0)
    pcm = os.path.join(EV, "POSCTRL_MAKETEST_S5R3.txt")
    safe("MAKETEST_POSCTRL_4_OF_4", lambda: (re.search(r"OVERALL_POSITIVE_CONTROL: (PASS|FAIL) \((\d+)/(\d+)\)", rd(pcm)).groups() if os.path.isfile(pcm) else ("MISSING", "0", "0")), ("PASS", "4", "4"))
    # ---------- rejudge / readiness / acceptance
    rjp = os.path.join(EV, "REJUDGE_S5R3.tsv")
    safe("REJUDGE_DIFFS_ZERO", lambda: (re.search(r"DIFFS=(\d+)", rd(rjp)).group(1) if os.path.isfile(rjp) else "MISSING"), "0")
    rp = os.path.join(EV, "READINESS_S5R3.tsv")
    safe("READINESS_GAP_ZERO", lambda: sum(1 for r in read_tsv(rp) if r.get("status") == "GAP") if os.path.isfile(rp) else -1, 0)
    ap = os.path.join(EV, "P05_ACCEPTANCE_MAP_S5R3.tsv")
    safe("ACCEPTANCE_ALL_MET", lambda: sum(1 for r in read_tsv(ap) if r.get("status") != "MET") if os.path.isfile(ap) else -1, 0)
    # ---------- registry patch
    rda = os.path.join(EV, "REGISTRY_APPLY_DIFF_S5R3.txt")
    safe("REGISTRY_APPLY_ASSERT_ONLY_LISTED", lambda: "PASS" if (os.path.isfile(rda) and "# ASSERT_ONLY_LISTED_LINES_CHANGED: PASS" in rd(rda)) else "FAIL", "PASS")
    def regsha():
        d = {}
        for line in rd(rda).splitlines():
            m = re.match(r"FILE (testing/s4test/ISSUE_REGISTRY.md|PROJECT_ROADMAP.md) .* after_sha256=([0-9a-f]{64})", line)
            if m:
                d[m.group(1)] = m.group(2)
        return d
    rs = regsha() if os.path.isfile(rda) else {}
    safe("REGISTRY_ISSUE_SHA_MATCHES_AFTER", lambda: sha_f(os.path.join(REPO, "testing/s4test/ISSUE_REGISTRY.md")), rs.get("testing/s4test/ISSUE_REGISTRY.md", "MISSING"))
    safe("REGISTRY_ROADMAP_SHA_MATCHES_AFTER", lambda: sha_f(os.path.join(REPO, "PROJECT_ROADMAP.md")), rs.get("PROJECT_ROADMAP.md", "MISSING"))
    safe("REGISTRY_ISSUE_HAS_ES5_6", lambda: 1 if "ES5-6" in rd(os.path.join(REPO, "testing/s4test/ISSUE_REGISTRY.md")) else 0, "1")
    safe("REGISTRY_ROADMAP_HAS_ES5_6", lambda: 1 if "ES5-6" in rd(os.path.join(REPO, "PROJECT_ROADMAP.md")) else 0, "1")
    # ---------- report
    rp2 = os.path.join(P05, "P05_S5R3_REPORT.md")
    safe("REPORT_PRESENT", lambda: "present" if os.path.isfile(rp2) else "absent", "present")
    rchk = os.path.join(EV, "REPORT_CHECK_S5R3.txt")
    safe("REPORT_CHECK_FAILS_ZERO", lambda: (re.search(r"FAILS=(\d+)", rd(rchk)).group(1) if os.path.isfile(rchk) else "MISSING"), "0")
    txt = rd(rp2) if os.path.isfile(rp2) else ""
    safe("REPORT_VERDICT_LINE", lambda: 1 if "本轮已完成 P05-S5 R3 范围，等待用户审核" in txt else 0, "1")
    safe("REPORT_SIGNOFF_DRAFT_REF", lambda: 1 if "P05_S5_SIGNOFF_DRAFT.md" in txt else 0, "1")
    # ---------- registries
    reg = os.path.join(P05, "registries/s5r3")
    rv = verify_sums_dir(reg)
    safe("REGISTRIES_SUMS_ALL_OK", lambda: ("%d/%s" % (rv[0], "OK" if not rv[1] else "BAD")) if rv else "MISSING", "26/OK")
    record("REGISTRY_ITEMS", rv[0] if rv else "MISSING")
    # ---------- evidence manifest
    evsum = os.path.join(EV, "SHA256SUMS.txt")
    evp = verify_sums_dir(EV)
    # expected count is not fixed: assert bad empty and count > 0
    def ev_ok():
        if not evp:
            return "MISSING"
        return "OK" if not evp[1] and evp[0] > 0 else "BAD"
    safe("EVIDENCE_SHA256SUMS_OK", ev_ok, "OK")
    def ev_cover():
        if not os.path.isfile(evsum):
            return "MISSING"
        listed = set()
        for line in rd(evsum).splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            listed.add(" ".join(line.split()[1:]))
        actual = set()
        for root, dirs, files in os.walk(EV):
            dirs[:] = sorted(d for d in dirs if d not in ("tmp", "gate", "trees"))
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), EV)
                if rel in ("safe_run.log", "SHA256SUMS.txt"):
                    continue
                actual.add(rel)
        miss = sorted(actual - listed)
        extra = sorted(listed - actual)
        return "missing=%s extra=%s" % (miss[:3] or "none", extra[:3] or "none")
    safe("EVIDENCE_SUMS_COVERS_ALL", ev_cover, "missing=none extra=none")
    def trunc_ok():
        if not os.path.isfile(evsum):
            return "MISSING"
        a = first_line(recs, "s5r3_chain.py sha_sums", commit_epoch)
        m = re.search(r"safe_run.log up to line (\d+)", rd(evsum))
        if not m or a <= 0:
            return "anchor=%d trunc=%s" % (a, m.group(1) if m else "missing")
        return "OK" if int(m.group(1)) == a else "trunc=%s anchor=%d" % (m.group(1), a)
    safe("EVIDENCE_SUMS_TRUNC_LINE_IS_SHA_SUMS_CALL", trunc_ok, "OK")
    # ---------- events
    evp2 = os.path.join(EV, "EVENTS_S5R3.tsv")
    def ev_rows():
        if not os.path.isfile(evp2):
            return "MISSING"
        anchor = first_line(recs, "s5r3_chain.py events", commit_epoch)
        rows = {}
        for line in rd(evp2).splitlines():
            if line.startswith("#") or line.startswith("log_line"):
                continue
            f = line.split(TAB)
            rows[int(f[0])] = f[1]
        need = {}
        parent = ""
        ts_re = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")
        ls = rd(os.path.join(EV, "safe_run.log")).splitlines()
        for x in range(1, anchor + 1):
            m = ts_re.match(ls[x - 1])
            if m:
                parent = m.group(1)
            need[x] = parent
        return "OK" if rows == need and anchor > 0 else "rows=%d need=%d anchor=%d" % (len(rows), len(need), anchor)
    safe("EVENTS_ROW_SET_EQ_RECOMPUTATION", ev_rows, "OK")
    # ---------- tmp snapshot and other-round evidence
    def tmp_snap():
        names = sorted(os.listdir("/tmp"))
        return "%d/%s" % (len(names), sha_b(("\n".join(names) + "\n").encode("utf-8")))
    safe("TMP_SNAPSHOT_UNCHANGED", tmp_snap, "%s/%s" % (srec.get("TMP_COUNT", "?"), srec.get("TMP_SHA256", "?")))
    def other_ev():
        start_epoch = epoch_of(srec.get("START_TIME_UTC", "2000-01-01T00:00:00Z"))
        bad = []
        for d in sorted(os.listdir(os.path.join(P05, "evidence"))):
            if d == "p05-s5r3" or not d.startswith("p05-"):
                continue
            p = os.path.join(P05, "evidence", d)
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
    # ---------- report/STATE/registries consistency
    safe("REPORT_CHECK_STATE_BYTES_LE_8192", lambda: (re.search(r"STATE_BYTES=(\d+)", rd(rchk)).group(1) if os.path.isfile(rchk) else "MISSING"), str(len(st)))
    # ---------- final
    fails = [c for c in CHECKS if not c[3]]
    lines = ["# P05-S5 R3 end gate GATE_S5R3_end.txt (" + started + ")"]
    lines += ["RECORD" + TAB + k + TAB + "value=" + v for k, v in RECORDS]
    for (n, e, a, ok) in CHECKS:
        lines.append(("PASS" if ok else "FAIL") + TAB + n + TAB + "expected=" + str(e) + TAB + "actual=" + str(a))
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