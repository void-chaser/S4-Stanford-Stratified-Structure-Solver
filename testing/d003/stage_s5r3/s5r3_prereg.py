#!/usr/bin/env python3
# s5r3_prereg.py -- write the three S5R3 pre-registration tables (D016, make test, E2E), each in its own
# call so the gate can assert their safe_run.log line order. Expectations are never rewritten afterwards.
#   s5r3_prereg.py d016 | maketest | e2e
import os, sys, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)


def sha_f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def wr(p, t):
    rp = os.path.realpath(p)
    if not rp.startswith(os.path.join(REPO, "checkpoints/p05") + os.sep):
        raise SystemExit("WRITE_OUTSIDE " + rp)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(t)


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
    return hdr, rows


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def d016():
    src = os.path.join(P05, "registries/s5r2/PREREG_D016_S5R2.tsv")
    hdr, rows = read_tsv(src)
    out = os.path.join(EV, "PREREG_D016_S5R3.tsv")
    cols = ["point_id", "frontend", "basis", "NumBasis", "kind", "expected_status", "expected_rc",
            "expected_exception", "expected_text", "expected_finite", "expected_count",
            "rel_err_threshold", "status", "note"]
    lines = [
        "# PREREG_D016_S5R3.tsv -- D016 public-API pre-registration, P05-S5 R3 (U372). status INFLUENCED.",
        "# Same point family and the same expectation meaning as PREREG_D016_S5R2.tsv; this is a new run, not a change of",
        "# expectation. Comparator v2 reads expectations BY COLUMN NAME. For a stderr row the rule is:",
        "#   expected_count=0 means 'pre-registered ABSENT <=> observed occurrence count == 0'. No row is compared",
        "#   by a label string against a number.",
        "# PROCESS rows: expected_rc for rc rows, expected_count for occurrence-count rows.",
        "# ARTIFACT rows: expected_status=MATCH_D016_BUILD_S5R3 means the observed sha256 must equal the value recorded",
        "#   in D016_BUILD_S5R3.tsv (the S5R3 F4 build).",
        "# Written before the first formal D016 run of this round; sha256/UTC in PREREG_D016_S5R3.tsv.sha256.txt.",
        TAB.join(cols),
    ]
    n = 0
    for r in rows:
        pid = r["point_id"]
        kind = r["kind"]
        row = {c: r.get(c, "") for c in cols}
        row["expected_count"] = r.get("expected_count", "")
        if kind == "PROCESS":
            if pid in ("PY_STDERR_INFO2", "LUA_STDERR_INFO2"):
                row["expected_count"] = "0"
                row["expected_rc"] = ""
            elif pid == "LUA_STDERR_MSG_COUNT":
                row["expected_count"] = "8"
                row["expected_rc"] = ""
            else:
                row["expected_count"] = ""
        if kind == "ARTIFACT":
            row["expected_status"] = "MATCH_D016_BUILD_S5R3"
            row["expected_count"] = ""
        lines.append(TAB.join(row[c] for c in cols))
        n += 1
    wr(out, NL.join(lines) + NL)
    sha = sha_f(out)
    rec = os.path.join(EV, "PREREG_D016_S5R3.tsv.sha256.txt")
    wr(rec, NL.join([
        "# PREREG_D016_S5R3.tsv.sha256.txt -- sha256/UTC recorded immediately after the pre-registration",
        TAB.join(["file", "sha256", "bytes", "rows", "status", "utc_recorded"]),
        TAB.join(["PREREG_D016_S5R3.tsv", sha, str(len(open(out, "rb").read())), str(n), "INFLUENCED", utc()]),
    ]) + NL)
    print("PREREG_D016 rows=%d sha=%s" % (n, sha))
    return 0


def maketest():
    out = os.path.join(EV, "PREREG_MAKETEST_S5R3.tsv")
    items = [
        ("status", "INFLUENCED", "historical M3a/M3b results are known; criteria unchanged (U374)"),
        ("criterion", "NO_NEW_FAILURE", "F4 failing set subset of B failing set AND F4 p1/p2 no difference AND identical unit sets AND every log reconciles with Ran N / skipped=k"),
        ("tree_B", "37a82e8", "S4 tree 1d738e64f9864a475fdb3de34cd3601605df2c64; exported with git archive to $EV/trees/B"),
        ("tree_F4", "05097a7", "S4 tree 589e15eb11fcb04e031b524f25a443e7921946cf; exported with git archive to $EV/trees/F4"),
        ("runs", "B:1,F4:1,B:2,F4:2", "four segments, one run_maketest_s5r3.py call per segment, resumable"),
        ("command", "make -C <tree> test PYTHON=python3", "same build and make test command as M3a (task brief section 4)"),
        ("historical_M3a", "unit_count=175 B_failing=none F4_failing=none", "MAKETEST_VERDICT_R9M3A.tsv (INFLUENCED basis; M3a did not reconcile docstring units)"),
        ("historical_M3b_reparse", "unit_count=265 (261 unittest + 4 stage) per-log reconcile 257/257 + 4/4", "MAKETEST_VERDICT_R9M3B.tsv; the S5R3 judge copies the M3b v2 reconcile logic"),
        ("expect_unit_rows", "265", "B_p1/B_p2/F4_p1/F4_p2 unit sets must be identical and reconcile with Ran N"),
        ("posctrl_categories", "NEW_FAILURE,FLAKY,SUITE_DIFF,RECONCILE_FAIL", "4 tampered on-disk log cases, one per category"),
        ("judge", "judge_maketest_s5r3.py", "copied from judge_maketest_r9m3b_v2.py; line diff in COPY_DIFF_S5R3.txt"),
        ("runner", "run_maketest_s5r3.py", "copied from run_maketest_r9m3a.py with per-segment resume; line diff in COPY_DIFF_S5R3.txt"),
    ]
    lines = ["# PREREG_MAKETEST_S5R3.tsv -- make test pre-registration, P05-S5 R3 (U374). Written before any S5R3 make test run.",
             "# The unit count must be reconciled with the unittest 'Ran N' line; a mismatch is RECONCILE_FAIL, never adjusted away.",
             TAB.join(["item", "value", "note"])]
    for it in items:
        lines.append(TAB.join(it))
    wr(out, NL.join(lines) + NL)
    print("PREREG_MAKETEST rows=%d sha=%s" % (len(items), sha_f(out)))
    return 0


def e2e():
    src = os.path.join(P05, "registries/s4r9/M3b/PREREG_E2E_R9M3B.tsv")
    hdr, rows = read_tsv(src)
    out = os.path.join(EV, "PREREG_E2E_S5R3.tsv")
    lines = [
        "# PREREG_E2E_S5R3.tsv -- P05-S5 R3 re-run of the M3b public-API E2E matrix (U373).",
        "# status: INFLUENCED. The 42 data rows below are the M3b rows verbatim (same columns, options,",
        "#   nth / calib_size / exp_visible / tolerance); this round only re-runs them on a fresh F4 build.",
        "# Written after the injection-free S5R3 gdb calibration and BEFORE any S5R3 injection run.",
        "# sha256 and UTC are recorded in PREREG_E2E_S5R3.tsv.sha256.txt.",
        TAB.join(hdr),
    ]
    for r in rows:
        lines.append(TAB.join(r.get(c, "") for c in hdr))
    wr(out, NL.join(lines) + NL)
    sha = sha_f(out)
    rec = os.path.join(EV, "PREREG_E2E_S5R3.tsv.sha256.txt")
    wr(rec, NL.join([
        "# PREREG_E2E_S5R3.tsv.sha256.txt -- sha256/UTC recorded immediately after the pre-registration",
        TAB.join(["file", "sha256", "bytes", "rows", "status", "utc_recorded"]),
        TAB.join(["PREREG_E2E_S5R3.tsv", sha, str(len(open(out, "rb").read())), str(len(rows)), "INFLUENCED", utc()]),
    ]) + NL)
    print("PREREG_E2E rows=%d sha=%s" % (len(rows), sha))
    return 0


def main():
    if len(sys.argv) < 2:
        print("usage: s5r3_prereg.py d016|maketest|e2e")
        return 2
    sub = sys.argv[1]
    if sub == "d016":
        return d016()
    if sub == "maketest":
        return maketest()
    if sub == "e2e":
        return e2e()
    print("unknown " + sub)
    return 2


if __name__ == "__main__":
    sys.exit(main())
