#!/usr/bin/env python3
# s5r3_startgate.py -- P05-S5 R3 start gate (task brief section 0).
# Asserts the four baseline facts plus the artifacts named in the brief, records START_TIME_UTC and
# a read-only /tmp top-level snapshot, and writes $EV/GATE_S5R3_start.txt. Any FAIL prints FAILS=...
import os, sys, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
P05 = os.path.join(REPO, "checkpoints/p05")
OUT = os.path.join(EV, "GATE_S5R3_start.txt")
TAB = chr(9)
NL = chr(10)
EXP_BRANCH = "codex/p05-d003-fft-error-propagation"
EXP_HEAD = "29dfd1c04e18d351e72d50f57deb0299f8f74d08"
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
EXP_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXP_RULINGS_BYTES = 148522
EXP_RULINGS_MAX_U = "U371"
EXP_D016_S5R2_SUMMARY = "MATCH=31 MISMATCH=2 FLAKY=0"
EXP_M3B_PREREG_SHA = "9e3895bb05f3b454a08b65824ba6740718ae4ae4af77b1515121a4d49b9b31da"
EXP_M3B_PREREG_ROWS = 42
RECORDS = []
CHECKS = []
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
    return subprocess.check_output(cmd, text=True, cwd=REPO).strip()


def record(k, v):
    RECORDS.append((k, str(v)))


def safe(name, fn, exp):
    try:
        actual = fn()
    except Exception as exc:
        CRASHED.append((name, repr(exc)))
        actual = "EXC:" + repr(exc)[:160]
    ok = actual == exp
    CHECKS.append((name, exp, actual, ok))


def tmp_snapshot():
    names = sorted(os.listdir("/tmp"))
    return len(names), sha_b(("\n".join(names) + "\n").encode("utf-8"))


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
        if len(parts) < 2:
            bad.append(("MALFORMED", line))
            continue
        n += 1
        fp = os.path.join(d, " ".join(parts[1:]))
        if not os.path.isfile(fp):
            bad.append(("MISSING", os.path.basename(fp)))
        elif sha_f(fp) != parts[0]:
            bad.append(("SHA", os.path.basename(fp)))
    return n, bad


def main():
    record("START_TIME_UTC", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    record("HEAD", sh(["git", "rev-parse", "HEAD"]))
    record("HEAD_S4", sh(["git", "rev-parse", "HEAD:S4"]))
    tmp_n, tmp_sha = tmp_snapshot()
    record("TMP_COUNT", tmp_n)
    record("TMP_SHA256", tmp_sha)
    # --- baseline four
    safe("BRANCH_IS_EXPECTED", lambda: sh(["git", "branch", "--show-current"]), EXP_BRANCH)
    safe("HEAD_IS_BASE", lambda: sh(["git", "rev-parse", "HEAD"]), EXP_HEAD)
    safe("HEAD_S4_TREE_EQ_F4", lambda: sh(["git", "rev-parse", "HEAD:S4"]), EXP_S4)
    safe("JUDGE_SHA256", lambda: sha_f(os.path.join(REPO, "testing/d003/judge_d003.py")), EXP_JUDGE)
    def git_status_clean():
        st = sh(["git", "status", "--short"])
        if not st:
            return "empty"
        allowed = ("testing/d003/stage_s5r3/",)
        bad = [ln for ln in st.splitlines() if not any(ln[3:].startswith(a) for a in allowed)]
        return "empty" if not bad else "not-empty:" + ";".join(bad[:4])
    record("GIT_STATUS_RAW", sh(["git", "status", "--short"]) or "empty")
    safe("GIT_STATUS_EMPTY", git_status_clean, "empty")
    # --- rulings
    rul = os.path.join(P05, "registries/RULINGS.tsv")
    rb = open(rul, "rb").read()
    record("RULINGS_BYTES", len(rb))
    record("RULINGS_SHA256", sha_b(rb))
    safe("RULINGS_START_BYTES", lambda: len(open(rul, "rb").read()), EXP_RULINGS_BYTES)
    maxu = "U0"
    for line in rb.decode("utf-8").splitlines():
        f = line.split(TAB)
        if f and f[0].startswith("U") and f[0][1:].isdigit():
            if int(f[0][1:]) > int(maxu[1:]):
                maxu = f[0]
    record("RULINGS_MAX_U", maxu)
    safe("RULINGS_START_MAX_U", lambda: maxu, EXP_RULINGS_MAX_U)
    # --- errata list (s5r2)
    err = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
    record("ERRATA_S5_BYTES", len(open(err, "rb").read()))
    record("ERRATA_S5_SHA256", sha_f(err))
    # --- state
    stp = os.path.join(P05, "STATE.md")
    record("STATE_BYTES", len(open(stp, "rb").read()))
    record("STATE_SHA256", sha_f(stp))
    # --- registries/s5r2 SHA256SUMS
    r = verify_sums_dir(os.path.join(P05, "registries/s5r2"))
    record("S5R2_REGISTRY_ITEMS", r[0] if r else "MISSING")
    safe("S5R2_REGISTRY_SUMS_ALL_OK", lambda: ("all %d OK" % r[0]) if r and not r[1] else ("BAD %s" % (r[1][:3] if r else "missing")), "all 11 OK")
    # --- p05-s5r2 evidence SHA256SUMS
    r2 = verify_sums_dir(os.path.join(P05, "evidence/p05-s5r2"))
    record("S5R2_EVIDENCE_ITEMS", r2[0] if r2 else "MISSING")
    safe("S5R2_EVIDENCE_SUMS_ALL_OK", lambda: ("all %d OK" % r2[0]) if r2 and not r2[1] else ("BAD %s" % (r2[1][:3] if r2 else "missing")), "all %d OK" % (r2[0] if r2 else -1))
    # --- D016 S5R2 verdict summary
    dv = os.path.join(P05, "evidence/p05-s5r2/D016_VERDICT_S5R2.tsv")
    summ = ""
    if os.path.isfile(dv):
        for line in open(dv, encoding="utf-8"):
            if line.startswith("SUMMARY" + TAB):
                f = line.rstrip(NL).split(TAB)
                d = {}
                for x in f[1:]:
                    k, _, v = x.partition("=")
                    d[k] = v
                summ = "MATCH=%s MISMATCH=%s FLAKY=%s" % (d.get("MATCH"), d.get("MISMATCH"), d.get("FLAKY"))
    record("D016_S5R2_SUMMARY", summ)
    safe("D016_S5R2_SUMMARY_MATCH31_MISMATCH2", lambda: summ, EXP_D016_S5R2_SUMMARY)
    # --- M3b prereg rows + sha
    pre = os.path.join(P05, "registries/s4r9/M3b/PREREG_E2E_R9M3B.tsv")
    rows = [l for l in open(pre, encoding="utf-8").read().splitlines() if l.strip() and not l.startswith("#")]
    record("M3B_PREREG_ROWS", len(rows) - 1)
    record("M3B_PREREG_SHA256", sha_f(pre))
    safe("M3B_PREREG_42_DATA_ROWS", lambda: len(rows) - 1, EXP_M3B_PREREG_ROWS)
    rec_sha = None
    for line in open(os.path.join(P05, "registries/s4r9/M3b/PREREG_E2E_R9M3B.sha256.txt"), encoding="utf-8"):
        if line.startswith("PREREG_E2E_R9M3B.tsv" + TAB):
            rec_sha = line.split(TAB)[1]
    record("M3B_PREREG_RECORDED_SHA256", rec_sha or "MISSING")
    safe("M3B_PREREG_SHA_MATCHES_RECORD", lambda: sha_f(pre), rec_sha)
    # --- first-write invariants
    rerun = "--rerun" in sys.argv
    record("GATE_RERUN", "yes" if rerun else "no")
    if not rerun:
        safe("GATE_FILE_ABSENT_BEFORE_START", lambda: "present" if os.path.exists(OUT) else "absent", "absent")
    def ev_precheck():
        if not os.path.isdir(EV):
            return "absent"
        extra = [x for x in os.listdir(EV) if x not in ("tmp", "gate", "safe_run.log", "GATE_S5R3_start.txt")]
        return "absent" if not extra else "present:" + ",".join(sorted(extra)[:5])
    safe("EV_ABSENT_BEFORE_START", ev_precheck, "absent")
    fails = [c for c in CHECKS if not c[3]]
    os.makedirs(EV, exist_ok=True)
    lines = ["# P05-S5 R3 start gate GATE_S5R3_start.txt (" + dict(RECORDS)["START_TIME_UTC"] + ")"]
    lines += ["RECORD" + TAB + k + TAB + "value=" + v for k, v in RECORDS]
    lines += ["PASS" + TAB + n + TAB + "expected=" + str(e) + TAB + "actual=" + str(a) if ok else
              "FAIL" + TAB + n + TAB + "expected=" + str(e) + TAB + "actual=" + str(a) for (n, e, a, ok) in CHECKS]
    lines.append("COUNTS" + TAB + "pass=%d" % (len(CHECKS) - len(fails)) + TAB + "fail=%d" % len(fails) + TAB + "total=%d" % len(CHECKS))
    lines.append("FAILS=%d" % len(fails))
    lines.append("CHECK_CRASHED=%d" % len(CRASHED))
    for n, x in CRASHED:
        lines.append("CRASHED" + TAB + n + TAB + x)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines) + NL)
    for l in lines:
        print(l)
    print("WROTE " + OUT)
    return 0 if not fails and not CRASHED else 1


if __name__ == "__main__":
    sys.exit(main())
