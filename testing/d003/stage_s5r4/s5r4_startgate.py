#!/usr/bin/env python3
# s5r4_startgate.py -- P05-S5 R4 opening gate (task brief section 4). New file for s5r4.
# It asserts the baseline recorded in the task brief, the R3 end-gate FAIL set, the R3 evidence and
# registry manifests (all 382 / 10 items), the frozen sha of every s5r3 script, the R3 report and
# sign-off draft v1 shas, the /tmp snapshot, and that the round evidence directory holds no round
# output yet (only what the safe_run wrapper itself creates: tmp/, safe_run.log, gate/).
# PASS/FAIL use a callable, never a pre-computed tuple (R9 M3e lesson).
import os, re, sys, json, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r4")
EV3 = os.path.join(P05, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)

EXP_BRANCH = "codex/p05-d003-fft-error-propagation"
EXP_HEAD = "e6a65ab4751c5ba5a5d6e2e0c093826d37312064"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXP_RULINGS_BYTES = 150471
EXP_RULINGS_SHA = "b3b45b7defa8fca9c74b8647cbc66ffbe5f4f9565346847d323ea9418504115a"
EXP_RULINGS_MAX = "U377"
EXP_ERRATA_BYTES = 8228
EXP_ERRATA_SHA = "cc615647b7c5f13894f396f83821a2cf06201781e810d9f35ab59951859741f7"
EXP_STATE_BYTES = 3135
EXP_STATE_SHA = "964e905bdca66bf52572eb11e91bf57e6d122b42c4b9ae695e98e07482f48fab"
EXP_R3_REPORT_SHA = "30a0f1d2d8ec073c124642279cee149ef17d9e437329a467ce5df220c26fe0bb"
EXP_DRAFT_V1_SHA = "c08bac3f05fe1c2ee087d093cc0dcf9d9cf96e1666f2472c534fb6162e41da93"
EXP_EV3_SUMS_SHA = "ab40c17490157602ccd8693f2b672601dc19669caa5e72ddadf138c40d1c6e67"
EXP_EV3_ITEMS = 382
EXP_REG3_SUMS_SHA = "c982514f41050a31f0a99922aeee525e9281865ec31277dbef3db9e90af3ab1c"
EXP_REG3_ITEMS = 10
EXP_FROZEN3_SHA = "1526b8aafa528e0c133446228d33d6f7869bea661f03823a6914737ed723e7c8"
EXP_S5R3_GATE_END_SHA = "bd589fc5b098c5acb3dd4c3576bd7cccfc498b873ff398e6d8bddf569fc6978a"
EXP_FAIL_NAMES = sorted([
    "RULINGS_LINES_5_FIELDS", "FROZEN_POST_I_CALL_COUNTS_MATCH",
    "MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST", "D016_VERDICT_ROWS_34",
    "CALIB_DIFF_ZERO", "REJUDGE_DIFFS_ZERO", "READINESS_GAP_ZERO", "REGISTRIES_SUMS_ALL_OK"])
# the 26 deliverables S5R3 was supposed to registry; 19 were present, 7 missing (R3 report appendix C)
R3_DELIVERED_19 = [
    "GATE_S5R3_start.txt", "PREREG_D016_S5R3.tsv", "PREREG_D016_S5R3.tsv.sha256.txt",
    "PREREG_MAKETEST_S5R3.tsv", "PREREG_E2E_S5R3.tsv", "PREREG_E2E_S5R3.tsv.sha256.txt",
    "D016_VERDICT_S5R3.tsv", "D016_BUILD_S5R3.tsv", "E2E_VERDICT_S5R3.tsv", "E2E_BUILD_S5R3.tsv",
    "CALIB_DIFF_S5R3.tsv", "MAKETEST_UNITS_S5R3.tsv", "MAKETEST_VERDICT_S5R3.tsv",
    "POSCTRL_D016_S5R3.txt", "POSCTRL_E2E_S5R3.txt", "POSCTRL_MAKETEST_S5R3.txt",
    "FROZEN_SCRIPTS_S5R3.tsv", "s5r2_supplement/D016_VERDICT_S5R2_ERRATA.txt",
    "s5r2_supplement/D016_BUILD_S5R2.tsv"]
R3_MISSING_7 = ["REJUDGE_S5R3.tsv", "READINESS_S5R3.tsv", "P05_ACCEPTANCE_MAP_S5R3.tsv",
                "REGISTRY_APPLY_DIFF_S5R3.txt", "REPORT_CHECK_S5R3.txt", "COPY_DIFF_S5R3.txt",
                "ERRATA_S5.txt"]

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
        CRASHED.append((name, repr(exc)[:200]))
        actual = "EXC:" + repr(exc)[:160]
    ok = str(actual) == str(exp)
    CHECKS.append((name, str(exp), str(actual), ok))


def read_tsv(p, skip_first_field_values=("SUMMARY",)):
    """Read a TSV by column name: skip blank lines, '#' comment lines, the header row, and whole
    rows whose first field is in skip_first_field_values (e.g. SUMMARY). Never makes a summary row
    look like a data row (the S5R3 crash cause)."""
    rows = []
    hdr = None
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None or f[0] == hdr[0]:
            hdr = f
            continue
        if f and f[0] in skip_first_field_values:
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


def listed(sums_path):
    out = set()
    for line in open(sums_path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        out.add(" ".join(parts[1:]))
    return out


def main():
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record("START_TIME_UTC", started)
    record("BASE_HEAD", EXP_HEAD)
    record("BASE_HEAD_S4", EXP_S4)
    record("JUDGE_SHA256", EXP_JUDGE)
    # ---- baseline
    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), EXP_BRANCH)
    safe("HEAD_IS_BASE", lambda: sh(["git", "rev-parse", "HEAD"]), EXP_HEAD)
    safe("HEAD_S4_TREE_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("JUDGE_SHA", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    safe("S4_DIR_ZERO_MODIFICATION", lambda: sh(["git", "diff", "--name-only", "HEAD", "--", "S4"]) or "unmodified", "unmodified")
    def git_status_ok():
        st = sh(["git", "status", "--porcelain=v1"])
        bad = [ln for ln in st.splitlines() if ln.rstrip() not in ("?? testing/d003/stage_s5r4/", "?? testing/d003/stage_s5r4")]
        return "only_stage_s5r4" if not bad else ";".join(bad[:4])
    safe("GIT_STATUS_ONLY_STAGE_S5R4", git_status_ok, "only_stage_s5r4")
    # ---- /tmp snapshot
    names = sorted(os.listdir("/tmp"))
    tmp_count, tmp_sha = len(names), sha_b((NL.join(names) + NL).encode("utf-8"))
    record("TMP_COUNT", tmp_count)
    record("TMP_SHA256", tmp_sha)
    # ---- round evidence must hold no round output yet
    def ev_precontent():
        if not os.path.isdir(EV):
            return "absent"
        # GATE_S5R4_start.txt itself may exist from an earlier start-gate attempt in this round
        # (the version history is preserved under gate/); nothing else may precede the start gate.
        allowed = {"tmp", "safe_run.log", "gate", "GATE_S5R4_start.txt"}
        extra = sorted(set(os.listdir(EV)) - allowed)
        if extra:
            return "extra=" + ",".join(extra[:4])
        logp = os.path.join(EV, "safe_run.log")
        if os.path.isfile(logp):
            # the only prior wrapper calls allowed are directory creation for this round and earlier
            # start-gate attempts; any other command would mean round output exists already.
            bad = [l for l in rd(logp).splitlines()
                   if "s5r4_startgate.py" not in l and "cmd=mkdir " not in l
                   and "GATE_S5R4_start.txt" not in l]
            if bad:
                return "foreign_log_lines=%d" % len(bad)
        return "clean"
    safe("EV_PRECONTENT_ONLY_WRAPPER", ev_precontent, "clean")
    # ---- rulings
    rul = os.path.join(P05, "registries/RULINGS.tsv")
    rb = open(rul, "rb").read()
    record("RULINGS_BYTES", len(rb))
    record("RULINGS_SHA256", sha_b(rb))
    safe("RULINGS_START_BYTES", lambda: len(rb), EXP_RULINGS_BYTES)
    safe("RULINGS_START_SHA256", lambda: sha_b(rb), EXP_RULINGS_SHA)
    def rulings_max_u():
        mu = 0
        for line in rb.decode("utf-8").splitlines():
            if line.startswith("#") or not line.strip():
                continue
            f = line.split(TAB)
            if f and re.match(r"^U(\d+)$", f[0]):
                mu = max(mu, int(f[0][1:]))
        return "U%d" % mu
    safe("RULINGS_START_MAX_U", rulings_max_u, EXP_RULINGS_MAX)
    def rulings_fields():
        n = 0
        for line in rb.decode("utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            n += 1
            if len(line.split(TAB)) != 5:
                return "row_%d_fields_%d" % (n, len(line.split(TAB)))
        return "ok_%d_rows" % n
    safe("RULINGS_LINES_5_FIELDS", lambda: rulings_fields(), lambda: "")  # replaced below
    CHECKS.pop()
    def rulings5():
        for line in rb.decode("utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            if len(line.split(TAB)) != 5:
                return "bad:%d" % len(line.split(TAB))
        return "ok"
    safe("RULINGS_LINES_5_FIELDS", rulings5, "ok")
    # ---- errata
    err = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
    eb = open(err, "rb").read()
    record("ERRATA_S5_BYTES", len(eb))
    record("ERRATA_S5_SHA256", sha_b(eb))
    safe("ERRATA_S5_START_BYTES", lambda: len(eb), EXP_ERRATA_BYTES)
    safe("ERRATA_S5_START_SHA256", lambda: sha_b(eb), EXP_ERRATA_SHA)
    last_e = [l for l in eb.decode("utf-8").splitlines() if l.startswith("ES5-")]
    safe("ERRATA_S5_LAST_IS_ES5_8", lambda: last_e[-1] if last_e else "none", "ES5-8")
    # ---- STATE
    stp = os.path.join(P05, "STATE.md")
    st = open(stp, "rb").read()
    record("STATE_BYTES", len(st))
    record("STATE_SHA256", sha_b(st))
    safe("STATE_START_BYTES", lambda: len(st), EXP_STATE_BYTES)
    safe("STATE_START_SHA256", lambda: sha_b(st), EXP_STATE_SHA)
    s = st.decode("utf-8")
    safe("STATE_HAS_R3_AND_UNSIGNED", lambda: 1 if ("P05-S5 R3" in s and "未签收" in s) else 0, 1)
    # ---- R3 evidence manifest
    ev3sums = os.path.join(EV3, "SHA256SUMS.txt")
    record("S5R3_EVIDENCE_SUMS_SHA256", sha_f(ev3sums))
    safe("S5R3_EVIDENCE_SUMS_SHA", lambda: sha_f(ev3sums), EXP_EV3_SUMS_SHA)
    v3 = verify_sums_dir(EV3)
    safe("S5R3_EVIDENCE_SUMS_ALL_OK", lambda: "%d/%s" % (v3[0], "OK" if not v3[1] else "BAD"), "%d/OK" % EXP_EV3_ITEMS)
    # ---- R3 end gate
    g3 = os.path.join(EV3, "gate/GATE_S5R3_end.txt")
    g3t = rd(g3)
    record("S5R3_GATE_END_SHA256", sha_f(g3))
    safe("S5R3_GATE_END_PRESENT", lambda: "present" if os.path.isfile(g3) else "absent", "present")
    safe("S5R3_GATE_END_SHA", lambda: sha_f(g3), EXP_S5R3_GATE_END_SHA)
    safe("S5R3_GATE_END_FAILS", lambda: re.search(r"FAILS=(\d+)", g3t).group(1), "8")
    safe("S5R3_GATE_END_CRASHED", lambda: re.search(r"CHECK_CRASHED=(\d+)", g3t).group(1), "0")
    def fail_names():
        got = sorted([l.split(TAB)[1] for l in g3t.splitlines() if l.startswith("FAIL" + TAB)])
        return "|".join(got)
    safe("S5R3_GATE_END_FAIL_NAMES", fail_names, "|".join(EXP_FAIL_NAMES))
    safe("REJUDGE_S5R3_ABSENT", lambda: "absent" if not os.path.isfile(os.path.join(EV3, "REJUDGE_S5R3.tsv")) else "present", "absent")
    # ---- R3 registry
    reg3 = os.path.join(P05, "registries/s5r3")
    reg3sums = os.path.join(reg3, "SHA256SUMS.txt")
    record("S5R3_REGISTRY_SUMS_SHA256", sha_f(reg3sums))
    safe("S5R3_REGISTRY_SUMS_SHA", lambda: sha_f(reg3sums), EXP_REG3_SUMS_SHA)
    v3r = verify_sums_dir(reg3)
    safe("S5R3_REGISTRY_SUMS_ALL_OK", lambda: "%d/%s" % (v3r[0], "OK" if not v3r[1] else "BAD"), "%d/OK" % EXP_REG3_ITEMS)
    def reg3_unlisted():
        files = set()
        for root, dirs, fs in os.walk(reg3):
            for f in fs:
                rel = os.path.relpath(os.path.join(root, f), reg3)
                if rel in ("SHA256SUMS.txt",):
                    continue
                files.add(rel)
        return "|".join(sorted(files - listed(reg3sums)))
    unlisted = reg3_unlisted()
    record("S5R3_REGISTRY_UNLISTED", unlisted)
    safe("S5R3_REGISTRY_UNLISTED_10", lambda: len([x for x in unlisted.split("|") if x]), 10)
    def reg3_missing():
        files = set()
        for root, dirs, fs in os.walk(reg3):
            for f in fs:
                files.add(os.path.relpath(os.path.join(root, f), reg3))
        return "|".join(sorted(f for f in R3_MISSING_7 if f not in files))
    missing = reg3_missing()
    record("S5R3_REGISTRY_MISSING", missing)
    safe("S5R3_REGISTRY_MISSING_7", lambda: len([x for x in missing.split("|") if x]), 7)
    def reg3_delivered():
        return "|".join(sorted(f for f in R3_DELIVERED_19 if not os.path.isfile(os.path.join(reg3, f))))
    safe("S5R3_REGISTRY_DELIVERED_19_PRESENT", lambda: "none" if reg3_delivered() == "" else reg3_delivered(), "none")
    # ---- R3 frozen scripts
    fz3 = os.path.join(EV3, "FROZEN_SCRIPTS_S5R3.tsv")
    record("S5R3_FROZEN_SHA256", sha_f(fz3))
    safe("S5R3_FROZEN_SHA", lambda: sha_f(fz3), EXP_FROZEN3_SHA)
    fzrows = read_tsv(fz3)
    def frozen3_ok():
        bad = []
        for r in fzrows:
            p = os.path.join(REPO, r["path"])
            if not os.path.isfile(p) or sha_f(p) != r["sha256"]:
                bad.append(r["path"])
        return "ok_%d" % len(fzrows) if not bad else ",".join(os.path.basename(x) for x in bad[:3])
    safe("S5R3_FROZEN_SCRIPTS_SHA_MATCH", frozen3_ok, "ok_%d" % len(fzrows))
    # ---- R3 report / draft v1 / gate appendix shas
    r3rep = os.path.join(P05, "P05_S5R3_REPORT.md")
    draft1 = os.path.join(P05, "P05_S5_SIGNOFF_DRAFT.md")
    record("R3_REPORT_SHA256", sha_f(r3rep))
    record("DRAFT_V1_SHA256", sha_f(draft1))
    safe("R3_REPORT_SHA", lambda: sha_f(r3rep), EXP_R3_REPORT_SHA)
    safe("DRAFT_V1_SHA", lambda: sha_f(draft1), EXP_DRAFT_V1_SHA)
    safe("DRAFT_V2_ABSENT_BEFORE_START", lambda: "absent" if not os.path.exists(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v2.md")) else "present", "absent")
    safe("S5R4_REPORT_ABSENT_BEFORE_START", lambda: "absent" if not os.path.exists(os.path.join(P05, "P05_S5R4_REPORT.md")) else "present", "absent")
    # ---- write gate
    fails = [c for c in CHECKS if not c[3]]
    lines = ["# P05-S5 R4 start gate GATE_S5R4_start.txt (%s)" % started]
    lines += ["RECORD" + TAB + k + TAB + "value=" + v for k, v in RECORDS]
    for (n, e, a, ok) in CHECKS:
        lines.append(("PASS" if ok else "FAIL") + TAB + n + TAB + "expected=" + e + TAB + "actual=" + a)
    lines.append("COUNTS" + TAB + "pass=%d" % (len(CHECKS) - len(fails)) + TAB + "fail=%d" % len(fails) + TAB + "total=%d" % len(CHECKS))
    lines.append("FAILS=%d" % len(fails))
    lines.append("CHECK_CRASHED=%d" % len(CRASHED))
    for n, x in CRASHED:
        lines.append("CRASHED" + TAB + n + TAB + x)
    os.makedirs(os.path.join(EV, "gate"), exist_ok=True)
    with open(os.path.join(EV, "GATE_S5R4_start.txt"), "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines) + NL)
    print(lines[-3])
    print(lines[-2])
    for n, e, a, ok in CHECKS:
        if not ok:
            print("FAIL\t%s\texpected=%s\tactual=%s" % (n, e, a))
    for n, x in CRASHED:
        print("CRASHED\t%s\t%s" % (n, x))
    print("WROTE " + os.path.relpath(os.path.join(EV, "GATE_S5R4_start.txt"), REPO))
    return 0 if not fails and not CRASHED else 1


if __name__ == "__main__":
    sys.exit(main())
