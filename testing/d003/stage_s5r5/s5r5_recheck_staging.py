#!/usr/bin/env python3
# s5r5_recheck_staging.py -- P05-S5 R5 correction re-judgement of the S5R4 end-gate FAIL (U386, task brief section 4).
# Read-only on the R4 frozen shakedown gate output: it re-evaluates SHAKEDOWN_USED_STAGING_ROOTS both with the
# corrected column parser (field2 == STAGING_MODE and field3 == value=yes) and with the R4 original substring test
# (`STAGING_MODE\\tyes` in text), and also checks EV_ROOT / P05_ROOT / FAILS / CHECK_CRASHED in the same file.
# The same evaluation function is run over four fixtures on disk in $EV/posctrl/ (positive control).
# usage: s5r5_recheck_staging.py recheck|posctrl
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
EV4 = os.path.join(P05, "evidence/p05-s5r4")
INP = os.path.join(EV4, "shakedown/gate/GATE_S5R4_end.txt")
SUMS4 = os.path.join(EV4, "SHA256SUMS.txt")
INP_REL = "shakedown/gate/GATE_S5R4_end.txt"
SHAKEDOWN_PREFIX = "checkpoints/p05/evidence/p05-s5r4/shakedown/"
FORMAL_EV_ROOT = "checkpoints/p05/evidence/p05-s5r5"
TAB = chr(9)
NL = chr(10)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def rd(p):
    return open(p, encoding="utf-8").read()


def sums_lookup(p, rel):
    for line in rd(p).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        if " ".join(parts[1:]) == rel:
            return parts[0]
    return None


def evaluate(text):
    """Return the re-judgement dictionary for one gate-output text."""
    d = {"corrected": "FAIL", "r4_original": "FAIL", "ev_root": "MISSING", "p05_root": "MISSING",
         "fails": "MISSING", "crashed": "MISSING"}
    for line in text.splitlines():
        f = line.split(TAB)
        if len(f) >= 3 and f[0] == "RECORD":
            key, val = f[1], f[2]
            if key == "STAGING_MODE" and val == "value=yes":
                d["corrected"] = "PASS"
            if key == "EV_ROOT":
                d["ev_root"] = val.replace("value=", "")
            if key == "P05_ROOT":
                d["p05_root"] = val.replace("value=", "")
    if "STAGING_MODE" + TAB + "yes" in text:
        d["r4_original"] = "PASS"
    else:
        d["r4_original"] = "not_staging"
    import re
    m = re.search(r"^FAILS=(\d+)$", text, re.M)
    d["fails"] = m.group(1) if m else "MISSING"
    m = re.search(r"^CHECK_CRASHED=(\d+)$", text, re.M)
    d["crashed"] = m.group(1) if m else "MISSING"
    return d


def ro_check(d):
    return "PASS" if (d["ev_root"].startswith(SHAKEDOWN_PREFIX) and d["ev_root"] != FORMAL_EV_ROOT) else "FAIL:" + d["ev_root"]


def p05_check(d):
    return "PASS" if d["p05_root"].startswith(SHAKEDOWN_PREFIX) else "FAIL:" + d["p05_root"]


def verdicts(text):
    d = evaluate(text)
    return {
        "CORRECTED_LOGIC": ("PASS", d["corrected"]),
        "R4_ORIGINAL_LOGIC": ("not_staging", d["r4_original"]),
        "EV_ROOT_IS_SHAKEDOWN_PATH": ("PASS", ro_check(d)),
        "P05_ROOT_IS_SHAKEDOWN_PATH": ("PASS", p05_check(d)),
        "FAILS_ZERO": ("0", d["fails"]),
        "CHECK_CRASHED_ZERO": ("0", d["crashed"]),
    }


def run_recheck():
    if not os.path.isfile(INP):
        print("HARD_STOP input missing: " + INP_REL)
        return 2
    act_sha = sha_f(INP)
    # The S5R4 manifest declares that shakedown/ is excluded, so the frozen shakedown gate output cannot be a
    # manifest entry; the comparison is (a) the input is not listed BECAUSE the manifest declares the exclusion,
    # and (b) the manifest-covered R4 artifact that records the same shakedown iteration matches its entry.
    hdr = rd(SUMS4).splitlines()[0]
    listed = sums_lookup(SUMS4, INP_REL)
    excluded = ("shakedown/" in hdr) and listed is None
    iter_exp = sums_lookup(SUMS4, "SHAKEDOWN_ITERATIONS_S5R4.txt")
    iter_act = sha_f(os.path.join(EV4, "SHAKEDOWN_ITERATIONS_S5R4.txt"))
    v = verdicts(rd(INP))
    rows = [("INPUT_SHA256", act_sha, act_sha),
            ("INPUT_NOT_IN_S5R4_SUMS_DECLARED_EXCLUSION", "excluded",
             "excluded" if excluded else "listed_or_not_declared"),
            ("SHAKEDOWN_ITERATIONS_SHA_MATCHES_S5R4_SUMS", iter_exp or "NOT_LISTED", iter_act)]
    for k in ("CORRECTED_LOGIC", "R4_ORIGINAL_LOGIC", "EV_ROOT_IS_SHAKEDOWN_PATH",
              "P05_ROOT_IS_SHAKEDOWN_PATH", "FAILS_ZERO", "CHECK_CRASHED_ZERO"):
        rows.append((k, v[k][0], v[k][1]))
    body = ["# RECHECK_STAGING_S5R5.tsv -- correction re-judgement of SHAKEDOWN_USED_STAGING_ROOTS (U386)",
            "# input=" + INP_REL + " sha256=" + act_sha,
            "# r4_original_logic=substring 'STAGING_MODE\\tyes'; corrected_logic=RECORD line field2==STAGING_MODE and field3==value=yes",
            "# read only: the R4 frozen files are not modified",
            TAB.join(["check", "expected", "actual", "status"])]
    fails = 0
    for (k, exp, act) in rows:
        ok = str(exp) == str(act)
        if not ok:
            fails += 1
        body.append(TAB.join([k, str(exp), str(act), "PASS" if ok else "FAIL"]))
    corr = next(r for r in rows if r[0] == "CORRECTED_LOGIC")
    orig = next(r for r in rows if r[0] == "R4_ORIGINAL_LOGIC")
    body.append("SUMMARY" + TAB + "CORRECTED=" + corr[2] + TAB + "R4_ORIGINAL=" + orig[2]
                + TAB + "ROWS=" + str(len(rows)) + TAB + "FAILS=" + str(fails))
    out = os.path.join(EV, "RECHECK_STAGING_S5R5.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("CORRECTED=%s R4_ORIGINAL=%s EV_ROOT=%s P05_ROOT=%s FAILS=%s CHECK_CRASHED=%s rows_fails=%d"
          % (corr[2], orig[2], v["EV_ROOT_IS_SHAKEDOWN_PATH"][1], v["P05_ROOT_IS_SHAKEDOWN_PATH"][1],
             v["FAILS_ZERO"][1], v["CHECK_CRASHED_ZERO"][1], fails))
    print("WROTE " + os.path.relpath(out, REPO))
    ok = (corr[2] == "PASS" and orig[2] == "not_staging" and fails == 0 and excluded)
    return 0 if ok else 1


def run_posctrl():
    real = rd(INP)
    base = os.path.join(EV, "posctrl/recheck_staging")
    os.makedirs(base, exist_ok=True)

    def write_fixture(name, text):
        p = os.path.join(base, name + ".txt")
        open(p, "w", encoding="utf-8").write(text)
        return p

    fixtures = []
    p1 = write_fixture("case1_real_copy", real)
    fixtures.append(("case1_real_copy_expect_PASS", p1, "PASS"))
    lines = real.splitlines()
    tampered2 = []
    for line in lines:
        f = line.split(TAB)
        if len(f) >= 3 and f[0] == "RECORD" and f[1] == "STAGING_MODE" and f[2] == "value=yes":
            line = TAB.join([f[0], f[1], "value=no"])
        tampered2.append(line)
    p2 = write_fixture("case2_value_no", NL.join(tampered2) + NL)
    fixtures.append(("case2_value_yes_to_no_expect_FAIL", p2, "FAIL"))
    tampered3 = [line for line in lines
                 if not (len(line.split(TAB)) >= 2 and line.split(TAB)[0] == "RECORD" and line.split(TAB)[1] == "STAGING_MODE")]
    p3 = write_fixture("case3_line_deleted", NL.join(tampered3) + NL)
    fixtures.append(("case3_staging_line_deleted_expect_FAIL", p3, "FAIL"))
    tampered4 = []
    for line in lines:
        f = line.split(TAB)
        if len(f) >= 3 and f[0] == "RECORD" and f[1] == "EV_ROOT":
            line = TAB.join([f[0], f[1], "value=" + FORMAL_EV_ROOT])
        tampered4.append(line)
    p4 = write_fixture("case4_ev_root_formal", NL.join(tampered4) + NL)
    fixtures.append(("case4_ev_root_formal_path_expect_FAIL", p4, "FAIL"))
    body = ["# POSCTRL_RECHECK_STAGING_S5R5.txt -- positive control of s5r5_recheck_staging.py (U386)",
            "# four fixtures are written on disk under " + os.path.relpath(base, REPO) + "/ and evaluated by",
            "# the same evaluation function as the formal run; a case passes when the overall verdict of the",
            "# fixture equals the expected verdict (CORRECTED_LOGIC decides PASS/FAIL)."]
    npass = 0
    for (name, path, want) in fixtures:
        v = verdicts(rd(path))
        got = "PASS" if (v["CORRECTED_LOGIC"][1] == "PASS" and v["EV_ROOT_IS_SHAKEDOWN_PATH"][1] == "PASS"
                         and v["FAILS_ZERO"][1] == "0" and v["CHECK_CRASHED_ZERO"][1] == "0") else "FAIL"
        ok = got == want
        npass += 1 if ok else 0
        body.append(("PASS" if ok else "FAIL") + TAB + name + TAB + "expected=" + want + TAB + "actual=" + got
                    + TAB + "corrected=" + v["CORRECTED_LOGIC"][1] + TAB + "original=" + v["R4_ORIGINAL_LOGIC"][1])
    overall = "PASS" if npass == len(fixtures) else "FAIL"
    body.append("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % (overall, npass, len(fixtures)))
    out = os.path.join(EV, "POSCTRL_RECHECK_STAGING_S5R5.txt")
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print(NL.join(body))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if overall == "PASS" else 1


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "recheck":
        return run_recheck()
    if mode == "posctrl":
        return run_posctrl()
    print("usage: s5r5_recheck_staging.py recheck|posctrl", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
