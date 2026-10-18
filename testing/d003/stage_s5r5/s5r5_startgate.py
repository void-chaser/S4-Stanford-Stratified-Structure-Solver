#!/usr/bin/env python3
# s5r5_startgate.py -- P05-S5 R5 opening gate (task brief section 0).
# New file for s5r5. It asserts the opening baseline named in the task brief, the immutability of the
# S5R4 evidence/registry manifests (all 941 / 15 items, read-only), the frozen sha of the R4 end gate and
# its single FAIL, the S5R3 manifests, the /tmp top-level snapshot, and that the round evidence directory
# holds no round output yet (only what the safe_run wrapper itself creates: tmp/, safe_run.log, gate/,
# TMP_SNAPSHOT_S5R5.tsv, GATE_S5R5_start.txt).
# PASS/FAIL use a callable + expected thunk, never a pre-computed tuple (R9 M3e lesson).
import os, re, sys, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
EV4 = os.path.join(P05, "evidence/p05-s5r4")
P05R4REG = os.path.join(P05, "registries/s5r4")
TAB = chr(9)
NL = chr(10)

EXP_BRANCH = "codex/p05-d003-fft-error-propagation"
EXP_BASE_HEAD = "1600ca1ba333e68988dc6d22211487b27e676191"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXP_RULINGS_BYTES = 154825
EXP_RULINGS_SHA = "24e65c3223c94deafbfd58d74e613aec2e5749159b39dfe93014ee32dc86a2d3"
EXP_RULINGS_MAX = "U385"
EXP_ERRATA_BYTES = 13848
EXP_ERRATA_SHA = "8aec8fd5e21c9fd2d3e5f3189d921eebe2fdde23524c5ea41087137fd641ba4f"
EXP_STATE_BYTES = 3424
EXP_STATE_SHA = "1a962c77e13f8c3f1189b7227855bf8826f48b7af84a43badd6cc21de509807c"
EXP_R4REPORT_SHA = "2ceba6d197c8f026a4480432cf58bacff5021d999107630dd286d17d66fd47c6"
EXP_DRAFT_V1_SHA = "c08bac3f05fe1c2ee087d093cc0dcf9d9cf96e1666f2472c534fb6162e41da93"
EXP_DRAFT_V2_SHA = "67876cd420c1ab44a6bd300f36ba2ae6cd382bdc855538203747e528d5acb69e"
EXP_EV4_SUMS_SHA = "e996f364a38b8aa07a160f59b04e2ff0e9dd4f0497e8afca6fb14fc901758367"
EXP_EV4_ITEMS = 941
EXP_REG4_SUMS_SHA = "7f2b30eb026ccb28e9c686bba5ceaff3bdee1ca47a611e6856e8b68a3aaed9a3"
EXP_REG4_ITEMS = 15
EXP_R4_GATE_SHA = "20bb6ad031d50929e68631c166bab9aa4cb24c0a707c8fa1d07ecac7b7873065"
EXP_R4_GATE_FAILS = "1"
EXP_R4_GATE_CRASHED = "0"
EXP_R4_GATE_PASS = "138"
EXP_R4_GATE_FAIL_NAME = "SHAKEDOWN_USED_STAGING_ROOTS"
EXP_EV3_SUMS_SHA = "ab40c17490157602ccd8693f2b672601dc19669caa5e72ddadf138c40d1c6e67"
EXP_REG3_SUMS_SHA = "c982514f41050a31f0a99922aeee525e9281865ec31277dbef3db9e90af3ab1c"

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


def read_kv(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 2:
            d[f[0]] = f[1]
    return d


def main():
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    record("START_TIME_UTC", started)
    record("BASE_HEAD", EXP_BASE_HEAD)
    record("BASE_HEAD_S4", EXP_S4)
    record("JUDGE_SHA256", EXP_JUDGE)
    # ---- baseline
    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), EXP_BRANCH)
    safe("HEAD_IS_BASE", lambda: sh(["git", "rev-parse", "HEAD"]), EXP_BASE_HEAD)
    safe("HEAD_S4_TREE_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("JUDGE_SHA", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    safe("BASE_COMMIT_PRESENT", lambda: sh(["git", "rev-parse", "--verify", EXP_BASE_HEAD + "^{commit}"]), EXP_BASE_HEAD)
    safe("S4_DIR_ZERO_MODIFICATION", lambda: sh(["git", "diff", "--name-only", "HEAD", "--", "S4"]) or "unmodified", "unmodified")

    def git_status_ok():
        st = sh(["git", "status", "--porcelain=v1"])
        bad = [ln for ln in st.splitlines() if ln.rstrip() not in ("?? testing/d003/stage_s5r5/", "?? testing/d003/stage_s5r5")]
        return "only_stage_s5r5" if not bad else ";".join(bad[:4])
    safe("GIT_STATUS_ONLY_STAGE_S5R5", git_status_ok, "only_stage_s5r5")
    # ---- /tmp top-level snapshot (read only) -> TMP_SNAPSHOT_S5R5.tsv (not a gate output)
    names = sorted(os.listdir("/tmp"))
    tmp_count, tmp_sha = len(names), sha_b((NL.join(names) + NL).encode("utf-8"))
    record("TMP_COUNT", tmp_count)
    record("TMP_SHA256", tmp_sha)
    snaps = os.path.join(EV, "TMP_SNAPSHOT_S5R5.tsv")
    body = ["# TMP_SNAPSHOT_S5R5.tsv -- /tmp top-level snapshot at P05-S5 R5 start (read only)",
            "# captured by s5r5_startgate.py; the end gate compares the live /tmp list against this record",
            "key" + TAB + "value",
            "TMP_COUNT" + TAB + str(tmp_count),
            "TMP_SHA256" + TAB + tmp_sha]
    os.makedirs(EV, exist_ok=True)
    open(snaps, "w", encoding="utf-8").write(NL.join(body) + NL)
    record("TMP_SNAPSHOT_FILE", os.path.relpath(snaps, REPO))
    # ---- round evidence must hold no round output yet
    def ev_precontent():
        if not os.path.isdir(EV):
            return "absent"
        allowed = {"tmp", "safe_run.log", "gate", "GATE_S5R5_start.txt", "TMP_SNAPSHOT_S5R5.tsv"}
        extra = sorted(set(os.listdir(EV)) - allowed)
        if extra:
            return "extra=" + ",".join(extra[:4])
        logp = os.path.join(EV, "safe_run.log")
        if os.path.isfile(logp):
            bad = [l for l in rd(logp).splitlines()
                   if "s5r5_startgate.py" not in l and "cmd=mkdir " not in l
                   and "GATE_S5R5_start.txt" not in l and "TMP_SNAPSHOT_S5R5.tsv" not in l]
            if bad:
                return "foreign_log_lines=%d" % len(bad)
        return "clean"
    safe("EV_PRECONTENT_ONLY_WRAPPER", ev_precontent, "clean")
    # ---- rulings
    rul = os.path.join(P05, "registries/RULINGS.tsv")
    rb = open(rul, "rb").read()
    record("RULINGS_BYTES", len(rb))
    record("RULINGS_SHA256", sha_b(rb))
    safe("RULINGS_START_BYTES_154825", lambda: len(rb), EXP_RULINGS_BYTES)
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
    safe("RULINGS_START_MAX_U385", rulings_max_u, EXP_RULINGS_MAX)

    def rulings5():
        for line in rb.decode("utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            if len(line.split(TAB)) != 5:
                return "bad:%d" % len(line.split(TAB))
        return "ok"
    safe("RULINGS_START_LINES_5_FIELDS", rulings5, "ok")
    # ---- errata
    err = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
    eb = open(err, "rb").read()
    record("ERRATA_S5_BYTES", len(eb))
    record("ERRATA_S5_SHA256", sha_b(eb))
    safe("ERRATA_START_BYTES_13848", lambda: len(eb), EXP_ERRATA_BYTES)
    safe("ERRATA_START_SHA256", lambda: sha_b(eb), EXP_ERRATA_SHA)
    last_e = [l for l in eb.decode("utf-8").splitlines() if l.startswith("ES5-")]
    safe("ERRATA_START_LAST_IS_ES5_14", lambda: last_e[-1] if last_e else "none", "ES5-14")
    # ---- STATE / S5R4 report / draft v1 v2
    st = open(os.path.join(P05, "STATE.md"), "rb").read()
    record("STATE_BYTES", len(st))
    record("STATE_SHA256", sha_b(st))
    safe("STATE_START_BYTES_3424", lambda: len(st), EXP_STATE_BYTES)
    safe("STATE_START_SHA256", lambda: sha_b(st), EXP_STATE_SHA)
    safe("STATE_HAS_R4_AND_UNSIGNED", lambda: 1 if ("P05-S5 R4" in st.decode("utf-8") and "未签收" in st.decode("utf-8")) else 0, 1)
    safe("S5R4_REPORT_SHA", lambda: sha_f(os.path.join(P05, "P05_S5R4_REPORT.md")), EXP_R4REPORT_SHA)
    safe("DRAFT_V1_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT.md")), EXP_DRAFT_V1_SHA)
    safe("DRAFT_V2_SHA", lambda: sha_f(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v2.md")), EXP_DRAFT_V2_SHA)
    # ---- S5R5 outputs must be absent before the start gate
    safe("DRAFT_V3_ABSENT_BEFORE_START", lambda: "absent" if not os.path.exists(os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v3.md")) else "present", "absent")
    safe("S5R5_REPORT_ABSENT_BEFORE_START", lambda: "absent" if not os.path.exists(os.path.join(P05, "P05_S5R5_REPORT.md")) else "present", "absent")
    safe("REG5_ABSENT_BEFORE_START", lambda: "absent" if not os.path.exists(os.path.join(P05, "registries/s5r5")) else "present", "absent")
    # ---- S5R4 evidence manifest (read only; 941 items)
    ev4sums = os.path.join(EV4, "SHA256SUMS.txt")
    record("S5R4_EVIDENCE_SUMS_SHA256", sha_f(ev4sums))
    safe("S5R4_EVIDENCE_SUMS_SHA", lambda: sha_f(ev4sums), EXP_EV4_SUMS_SHA)
    v4 = verify_sums_dir(EV4)
    safe("S5R4_EVIDENCE_SUMS_ALL_OK_941", lambda: "%d/%s" % (v4[0], "OK" if not v4[1] else "BAD"), "%d/OK" % EXP_EV4_ITEMS)
    # ---- S5R4 end gate (formal, run once) + shakedown output
    g4 = os.path.join(EV4, "gate/GATE_S5R4_end.txt")
    g4t = rd(g4)
    record("S5R4_GATE_END_SHA256", sha_f(g4))
    safe("S5R4_GATE_END_SHA", lambda: sha_f(g4), EXP_R4_GATE_SHA)
    safe("S5R4_GATE_END_FAILS", lambda: re.search(r"FAILS=(\d+)", g4t).group(1), EXP_R4_GATE_FAILS)
    safe("S5R4_GATE_END_CRASHED", lambda: re.search(r"CHECK_CRASHED=(\d+)", g4t).group(1), EXP_R4_GATE_CRASHED)
    safe("S5R4_GATE_END_PASS_138", lambda: len([l for l in g4t.splitlines() if l.startswith("PASS" + TAB)]), EXP_R4_GATE_PASS)
    safe("S5R4_GATE_END_FAIL_NAME", lambda: "|".join(l.split(TAB)[1] for l in g4t.splitlines() if l.startswith("FAIL" + TAB)), EXP_R4_GATE_FAIL_NAME)
    safe("S5R4_SHAKEDOWN_GATE_PRESENT", lambda: "present" if os.path.isfile(os.path.join(EV4, "shakedown/gate/GATE_S5R4_end.txt")) else "absent", "present")
    safe("S5R4_SHAKEDOWN_GATE_FAILS_ZERO",
         lambda: (lambda t: re.search(r"FAILS=(\d+)", t).group(1))(rd(os.path.join(EV4, "shakedown/gate/GATE_S5R4_end.txt"))), "0")
    # ---- S5R4 registry manifest
    reg4sums = os.path.join(P05R4REG, "SHA256SUMS.txt")
    record("S5R4_REGISTRY_SUMS_SHA256", sha_f(reg4sums))
    safe("S5R4_REGISTRY_SUMS_SHA", lambda: sha_f(reg4sums), EXP_REG4_SUMS_SHA)
    vr4 = verify_sums_dir(P05R4REG)
    safe("S5R4_REGISTRY_SUMS_ALL_OK_15", lambda: "%d/%s" % (vr4[0], "OK" if not vr4[1] else "BAD"), "%d/OK" % EXP_REG4_ITEMS)
    # ---- S5R3 manifests unchanged
    safe("S5R3_EVIDENCE_SUMS_SHA_UNCHANGED", lambda: sha_f(os.path.join(P05, "evidence/p05-s5r3/SHA256SUMS.txt")), EXP_EV3_SUMS_SHA)
    safe("S5R3_REGISTRY_SUMS_SHA_UNCHANGED", lambda: sha_f(os.path.join(P05, "registries/s5r3/SHA256SUMS.txt")), EXP_REG3_SUMS_SHA)
    # ---- write the start gate
    fails = [c for c in CHECKS if not c[3]]
    lines = ["# P05-S5 R5 start gate GATE_S5R5_start.txt (%s)" % started]
    lines += ["RECORD" + TAB + k + TAB + "value=" + v for k, v in RECORDS]
    for (n, e, a, ok) in CHECKS:
        lines.append(("PASS" if ok else "FAIL") + TAB + n + TAB + "expected=" + e + TAB + "actual=" + a)
    lines.append("COUNTS" + TAB + "pass=%d" % (len(CHECKS) - len(fails)) + TAB + "fail=%d" % len(fails) + TAB + "total=%d" % len(CHECKS))
    lines.append("FAILS=%d" % len(fails))
    lines.append("CHECK_CRASHED=%d" % len(CRASHED))
    for n, x in CRASHED:
        lines.append("CRASHED" + TAB + n + TAB + x)
    os.makedirs(os.path.join(EV, "gate"), exist_ok=True)
    with open(os.path.join(EV, "GATE_S5R5_start.txt"), "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines) + NL)
    print(lines[-3])
    print(lines[-2])
    for n, e, a, ok in CHECKS:
        if not ok:
            print("FAIL\t%s\texpected=%s\tactual=%s" % (n, e, a))
    for n, x in CRASHED:
        print("CRASHED\t%s\t%s" % (n, x))
    print("WROTE " + os.path.relpath(os.path.join(EV, "GATE_S5R5_start.txt"), REPO))
    return 0 if not fails and not CRASHED else 1


if __name__ == "__main__":
    sys.exit(main())
