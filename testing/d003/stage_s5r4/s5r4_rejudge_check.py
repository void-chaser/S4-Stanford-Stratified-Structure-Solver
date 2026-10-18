#!/usr/bin/env python3
# s5r4_rejudge_check.py -- offline self-test and positive control for rejudge_s5r4.py (task brief section 5).
# Every case is materialised on disk (a full copy of the S5R3 inputs) and the FORMAL rejudge script itself is
# invoked on it; no constant self-proof. The clean copy must give DIFFS=0; every tampered copy must give
# DIFFS>=1. The self-test covers: verdict file with SUMMARY rows not crashing / being excluded, normal MATCH,
# tamper -> MISMATCH, two different passes -> FLAKY, missing pass -> MISSING_RUN.
import os, sys, json, shutil, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV4 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r4")
EV3 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
REJ = os.path.join(REPO, "testing/d003/stage_s5r4/rejudge_s5r4.py")
TAB = chr(9)
NL = chr(10)

FILES = ["PREREG_E2E_S5R3.tsv", "E2E_VERDICT_S5R3.tsv", "PREREG_D016_S5R3.tsv",
         "D016_PASS1_S5R3.json", "D016_PASS2_S5R3.json", "D016_VERDICT_S5R3.tsv", "D016_BUILD_S5R3.tsv"]


def materialise(dst):
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    os.makedirs(dst)
    for rel in FILES:
        shutil.copyfile(os.path.join(EV3, rel), os.path.join(dst, rel))
    for pn in (1, 2):
        d = os.path.join(dst, "e2e/pass%d/points" % pn)
        os.makedirs(d)
        src = os.path.join(EV3, "e2e/pass%d/points" % pn)
        for f in sorted(os.listdir(src)):
            if f.endswith(".json"):
                shutil.copyfile(os.path.join(src, f), os.path.join(d, f))
    return dst


def run_case(root, out):
    p = subprocess.run([sys.executable, "-I", "-B", REJ, "formal", "--ev3-root", root, "--out", out],
                       text=True, capture_output=True, cwd=REPO)
    text = p.stdout + p.stderr
    diag = {}
    if os.path.isfile(out):
        for line in open(out, encoding="utf-8"):
            if line.startswith("SUMMARY" + TAB):
                for x in line.rstrip("\r\n").split(TAB)[1:]:
                    k, _, v = x.partition("=")
                    diag[k] = v
    return p.returncode, diag, text


def mutate_py_silent(root, passno):
    p = os.path.join(root, "e2e/pass%d/points/py_cf_s4malloc.json" % passno)
    rec = json.load(open(p, encoding="utf-8"))
    ref = json.loads(rec["steps"]["ref"]["stdout"])["steps"]["ref"]
    inj = json.loads(rec["steps"]["inject"]["stdout"])
    inj["steps"]["A_inject"] = {"ok": True, "values": ref["values"], "error_type": None, "error_msg": None}
    rec["steps"]["inject"]["stdout"] = json.dumps(inj, sort_keys=True)
    json.dump(rec, open(p, "w", encoding="utf-8"), indent=1)


def mutate_d016_recovery(root):
    for pn in (1, 2):
        p = os.path.join(root, "D016_PASS%s_S5R3.json" % pn)
        d = json.load(open(p, encoding="utf-8"))
        obs = d["observations"]["py"]
        ref = d["observations"]["py_ref"]["VL_NB9_REF"]["values"]
        obs["VL_NB9_RECOVER"]["values"] = [y + 1e-6 * abs(y) for y in ref]
        json.dump(d, open(p, "w", encoding="utf-8"), indent=1)


def mutate_recorded_verdict(root):
    p = os.path.join(root, "E2E_VERDICT_S5R3.tsv")
    lines = open(p, encoding="utf-8").read().splitlines()
    done = False
    for i, line in enumerate(lines):
        if line.startswith("#") or not line.strip():
            continue
        f = line.split(TAB)
        if f[0] == "point_id":
            continue
        f[4] = "INVALID"
        lines[i] = TAB.join(f)
        done = True
        break
    assert done
    open(p, "w", encoding="utf-8").write(NL.join(lines) + NL)


def append_noise(root):
    for rel, first in (("E2E_VERDICT_S5R3.tsv", "SUMMARY"), ("D016_VERDICT_S5R3.tsv", "SUMMARY")):
        p = os.path.join(root, rel)
        with open(p, "a", encoding="utf-8") as fh:
            fh.write("# extra comment line added by the s5r4 self-test" + NL)
            fh.write(first + TAB + "EXTRA=1" + NL)


def main():
    fails = []
    lines = ["# SELFTEST_REJUDGE_S5R4.txt -- offline self-test of rejudge_s5r4.py on on-disk fixtures" + NL,
             "# every case is a full copy of the S5R3 inputs under selftest/rejudge/<case>/; the formal rejudge",
             "# script is invoked as a subprocess on each fixture (no constant self-proof)." + NL]

    def check(name, cond, msg):
        print(("PASS" if cond else "FAIL") + TAB + name + TAB + msg)
        lines.append(("PASS" if cond else "FAIL") + ": " + name + " -- " + msg + NL)
        if not cond:
            fails.append(name)

    # case 1: clean copy, verdict files contain SUMMARY rows: must not crash and must be excluded
    c1 = materialise(os.path.join(EV4, "selftest/rejudge/case1_normal/inputs"))
    rc, diag, txt = run_case(c1, os.path.join(EV4, "selftest/rejudge/case1_normal/REJUDGE.tsv"))
    check("normal_clean_copy", rc == 0 and diag.get("DIFFS") == "0" and diag.get("E2E_ROWS") == "42"
          and diag.get("D016_REJUDGED_ROWS") == "33" and diag.get("D016_NOT_JUDGED") == "1",
          "rc=%d DIFFS=%s E2E_ROWS=%s D016_REJUDGED=%s D016_NOT_JUDGED=%s" %
          (rc, diag.get("DIFFS"), diag.get("E2E_ROWS"), diag.get("D016_REJUDGED_ROWS"), diag.get("D016_NOT_JUDGED")))
    evtxt = open(os.path.join(c1, "E2E_VERDICT_S5R3.tsv"), encoding="utf-8").read()
    d16txt = open(os.path.join(c1, "D016_VERDICT_S5R3.tsv"), encoding="utf-8").read()
    check("summary_rows_present_and_skipped", ("SUMMARY" + TAB) in d16txt and rc == 0,
          "D016_VERDICT contains SUMMARY rows (the S5R3 crash cause); rejudge returned rc=%d (no crash)" % rc)
    check("e2e_verdict_has_no_summary_row", ("SUMMARY" + TAB) not in evtxt,
          "E2E_VERDICT has no SUMMARY row (only per-point rows); rejudge still reads it by column name")
    # case 2: extra comment + extra SUMMARY rows appended: still no crash, same counts
    c2 = materialise(os.path.join(EV4, "selftest/rejudge/case2_summary_noise/inputs"))
    append_noise(c2)
    rc, diag, txt = run_case(c2, os.path.join(EV4, "selftest/rejudge/case2_summary_noise/REJUDGE.tsv"))
    check("extra_summary_and_comment_skipped", rc == 0 and diag.get("DIFFS") == "0",
          "rc=%d DIFFS=%s" % (rc, diag.get("DIFFS")))
    # case 3: tampered on-disk record (visible error removed) -> MISMATCH -> DIFF
    c3 = materialise(os.path.join(EV4, "selftest/rejudge/case3_tamper_mismatch/inputs"))
    mutate_py_silent(c3, 1)
    mutate_py_silent(c3, 2)
    rc, diag, txt = run_case(c3, os.path.join(EV4, "selftest/rejudge/case3_tamper_mismatch/REJUDGE.tsv"))
    hit = [l for l in txt.splitlines() if l.startswith("DIFF ") and "py_cf_s4malloc" in l]
    check("tamper_yields_mismatch_diag", rc == 1 and int(diag.get("DIFFS", "0")) >= 1 and hit
          and "API_SILENT" in hit[0], "rc=%d DIFFS=%s diff_rows=%d" % (rc, diag.get("DIFFS"), len(hit)))
    # case 4: two passes different -> FLAKY
    c4 = materialise(os.path.join(EV4, "selftest/rejudge/case4_flaky/inputs"))
    mutate_py_silent(c4, 2)
    rc, diag, txt = run_case(c4, os.path.join(EV4, "selftest/rejudge/case4_flaky/REJUDGE.tsv"))
    hit = [l for l in txt.splitlines() if l.startswith("DIFF ") and "py_cf_s4malloc" in l]
    check("two_passes_differ_yields_flaky", rc == 1 and hit and "FLAKY" in hit[0],
          "rc=%d DIFFS=%s diff_rows=%d" % (rc, diag.get("DIFFS"), len(hit)))
    # case 5: missing pass record -> MISSING_RUN
    c5 = materialise(os.path.join(EV4, "selftest/rejudge/case5_missing_run/inputs"))
    os.remove(os.path.join(c5, "e2e/pass2/points/py_cf_s4malloc.json"))
    rc, diag, txt = run_case(c5, os.path.join(EV4, "selftest/rejudge/case5_missing_run/REJUDGE.tsv"))
    hit = [l for l in txt.splitlines() if l.startswith("DIFF ") and "py_cf_s4malloc" in l]
    check("missing_pass_yields_missing_run", rc == 1 and hit and "MISSING_RUN" in hit[0],
          "rc=%d DIFFS=%s diff_rows=%d" % (rc, diag.get("DIFFS"), len(hit)))
    # case 6: D016 recovery value moved beyond threshold -> MISMATCH
    c6 = materialise(os.path.join(EV4, "selftest/rejudge/case6_d016_mismatch/inputs"))
    mutate_d016_recovery(c6)
    rc, diag, txt = run_case(c6, os.path.join(EV4, "selftest/rejudge/case6_d016_mismatch/REJUDGE.tsv"))
    hit = [l for l in txt.splitlines() if l.startswith("DIFF ") and "VL_NB9_RECOVER" in l]
    check("d016_threshold_tamper_yields_mismatch", rc == 1 and hit and "MISMATCH" in hit[0],
          "rc=%d DIFFS=%s diff_rows=%d" % (rc, diag.get("DIFFS"), len(hit)))

    out = os.path.join(EV4, "SELFTEST_REJUDGE_S5R4.txt")
    lines.append("SELFTEST_CASES=6" + NL)
    lines.append("SELFTEST_FAILS=%d" % len(fails) + NL)
    lines.append("OVERALL_SELFTEST: %s (%d/%d)" % ("PASS" if not fails else "FAIL", 6 - len(fails), 6) + NL)
    open(out, "w", encoding="utf-8").write("".join(lines))
    print("OVERALL_SELFTEST %s %d/6" % ("PASS" if not fails else "FAIL", 6 - len(fails)))
    print("WROTE " + os.path.relpath(out, REPO))

    # ---------------- positive control on the formal script (full input set, one tamper each)
    pc_fails = []
    pc = ["# POSCTRL_REJUDGE_S5R4.txt -- positive control of rejudge_s5r4.py on tampered on-disk copies" + NL,
          "# each case is a full copy of the S5R3 inputs; the formal rejudge script is run on it." + NL,
          "# clean copy must give DIFFS=0; each tampered copy must give DIFFS>=1." + NL]

    def pcheck(name, cond, msg):
        print(("PASS" if cond else "FAIL") + TAB + "posctrl_" + name + TAB + msg)
        pc.append(("PASS" if cond else "FAIL") + ": " + name + " -- " + msg + NL)
        if not cond:
            pc_fails.append(name)

    base = os.path.join(EV4, "posctrl/rejudge")
    clean = materialise(os.path.join(base, "clean/inputs"))
    rc, diag, txt = run_case(clean, os.path.join(base, "clean/REJUDGE.tsv"))
    pcheck("clean_copy", rc == 0 and diag.get("DIFFS") == "0", "rc=%d DIFFS=%s" % (rc, diag.get("DIFFS")))
    a = materialise(os.path.join(base, "tamper_e2e_visible_error_removed/inputs"))
    mutate_py_silent(a, 1)
    mutate_py_silent(a, 2)
    rc, diag, txt = run_case(a, os.path.join(base, "tamper_e2e_visible_error_removed/REJUDGE.tsv"))
    pcheck("tamper_e2e_visible_error_removed", int(diag.get("DIFFS", "0")) >= 1,
           "DIFFS=%s (must be >=1)" % diag.get("DIFFS"))
    b = materialise(os.path.join(base, "tamper_d016_recovery_over_threshold/inputs"))
    mutate_d016_recovery(b)
    rc, diag, txt = run_case(b, os.path.join(base, "tamper_d016_recovery_over_threshold/REJUDGE.tsv"))
    pcheck("tamper_d016_recovery_over_threshold", int(diag.get("DIFFS", "0")) >= 1,
           "DIFFS=%s (must be >=1)" % diag.get("DIFFS"))
    c = materialise(os.path.join(base, "tamper_recorded_verdict_flip/inputs"))
    mutate_recorded_verdict(c)
    rc, diag, txt = run_case(c, os.path.join(base, "tamper_recorded_verdict_flip/REJUDGE.tsv"))
    pcheck("tamper_recorded_verdict_flip", int(diag.get("DIFFS", "0")) >= 1,
           "DIFFS=%s (must be >=1)" % diag.get("DIFFS"))
    pc.append("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % ("PASS" if not pc_fails else "FAIL", 4 - len(pc_fails), 4) + NL)
    open(os.path.join(EV4, "POSCTRL_REJUDGE_S5R4.txt"), "w", encoding="utf-8").write("".join(pc))
    print("OVERALL_POSITIVE_CONTROL %s %d/4" % ("PASS" if not pc_fails else "FAIL", 4 - len(pc_fails)))
    return 0 if not fails and not pc_fails else 1


if __name__ == "__main__":
    sys.exit(main())
