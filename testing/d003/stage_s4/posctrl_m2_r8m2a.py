#!/usr/bin/env python3
# posctrl_m2_r8m2a.py -- P05-S4 R8 M2a section 4.6: positive controls of verdict_m2_r8m2a.py on SYNTHETIC data.
# No S4 driver is run.  A small synthetic prereg is generated under EV/tmp/posctrl_*/, then:
#   A = observed equals expected for every point                 -> expected MISMATCH 0, FLAKY 0
#   B = one observed rc1 changed (pass1 only)                    -> expected MISMATCH 1 and the changed point_id in output
#   C = pass1 and pass2 disagree on one point                    -> expected FLAKY 1
# The formal verdict script is called through subprocess (not reimplemented).  Output: POSCTRL_M2_R8_M2a.txt,
# last line POSCTRL=PASS or POSCTRL=FAIL.  Refuses to overwrite (U17).
import os
import subprocess
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
VERDICT = os.path.join(REPO, "testing", "d003", "stage_s4", "verdict_m2_r8m2a.py")
# R2 names: the first run wrote POSCTRL_M2_R8_M2a.txt (POSCTRL=FAIL, B-case design error: FLAKY leaked into B,
# and the point check looked for MISMATCH on a row whose verdict is FLAKY).  That output is kept (U17); this run
# writes _R2 names throughout.
OUT = os.path.join(EV, "POSCTRL_M2_R8_M2a_R2.txt")
TAG = "_R2"

# Synthetic prereg: 3 points.  Columns as in verdict_m2_r8m2a.py: exp_rc1, exp_rc2, exp_class, exp_I1..exp_I7.
PREREG_COLS = ["point_id", "exp_rc1", "exp_rc2", "exp_class"] + ["exp_I%d" % i for i in range(1, 8)]
RESULT_COLS = ["point_id", "tree", "rc1", "rc2", "rc", "signal", "hit"] + ["I%d" % i for i in range(1, 8)]
PREREG_ROWS = [
    # point_id, rc1, rc2, class, I1..I7   (class: REPORTED_FAILURE needs rc1 != 0 and hit >= 1)
    ["SYN-REP-1", "1", "1", "REPORTED_FAILURE", "HOLD", "HOLD", "HOLD", "HOLD", "HOLD", "HOLD", "DEFERRED"],
    ["SYN-CTRL-1", "0", "0", "CONTROL_OK", "-", "-", "-", "-", "-", "-", "-"],
    ["SYN-SWAL-1", "0", "0", "SILENT_SWALLOW", "VIOLATED", "-", "-", "-", "-", "-", "DEFERRED"],
]


def write_case(dirpath, name, rows_pass1, rows_pass2):
    os.makedirs(dirpath, exist_ok=True)
    pre_path = os.path.join(dirpath, "PREREG_SYN_%s.tsv" % name)
    with open(pre_path, "x", encoding="utf-8") as fh:
        fh.write("\t".join(PREREG_COLS) + "\n")
        for r in PREREG_ROWS:
            fh.write("\t".join(r) + "\n")
    for tag, rows in (("pass1", rows_pass1), ("pass2", rows_pass2)):
        with open(os.path.join(dirpath, "RESULTS_%s.tsv" % tag), "x", encoding="utf-8") as fh:
            fh.write("\t".join(RESULT_COLS) + "\n")
            for r in rows:
                fh.write("\t".join(r) + "\n")
    return pre_path


def observed_from_prereg(rc1_override=None):
    """Observation that equals the prereg expectation.  The class is derived by judge_d003 from rc/rc1/hit."""
    rows = []
    for r in PREREG_ROWS:
        pid, rc1, rc2, cls = r[0], r[1], r[2], r[3]
        if cls == "CONTROL_OK":
            hit = "0"
            rc = "0"
        elif cls == "REPORTED_FAILURE":
            hit = "1"
            rc = rc1
        else:  # SILENT_SWALLOW
            hit = "1"
            rc = "0"
        obs_rc1 = rc1
        if rc1_override and pid == rc1_override[0]:
            obs_rc1 = rc1_override[1]
        i_fields = r[4:11]  # observed I1..I7 equal the prereg I1..I7 (synthetic: observation = expectation)
        rows.append([pid, "F3", obs_rc1, rc2, rc, "0", hit] + list(i_fields))
    return rows


def run_verdict(pre_path, res_dir, prefix):
    cmd = ["python3", "-I", "-B", VERDICT, os.path.relpath(res_dir, REPO), os.path.relpath(pre_path, REPO), prefix]
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def parse_summary(prefix):
    path = os.path.join(EV, prefix + "_SUMMARY.txt")
    with open(path, encoding="utf-8") as fh:
        first = fh.readline().strip()
    parts = dict(p.split("=", 1) for p in first.split() if "=" in p)
    return parts


def main():
    if os.path.exists(OUT):
        print("posctrl_m2_r8m2a: REFUSED exists (U17): %s" % OUT)
        return 2
    base = os.path.join(EV, "tmp", "posctrl" + TAG)
    lines = []
    results = {}

    # Case A: all equal expectation (both passes identical).  Expected MISMATCH 0, FLAKY 0.
    dA = os.path.join(base, "posctrl_A")
    obsA = observed_from_prereg()
    preA = write_case(dA, "A", obsA, obsA)
    rcA, outA, errA = run_verdict(preA, dA, "VERDICT_M2_R8_M2a_POSCTRL_A" + TAG)
    sA = parse_summary("VERDICT_M2_R8_M2a_POSCTRL_A" + TAG) if rcA == 0 else {}
    results["A"] = (rcA, sA)
    lines.append("CASE_A rc=%d summary=%s" % (rcA, outA or errA))

    # Case B: change the observed rc1 of SYN-REP-1 in pass1 only (1 -> 0).  Expected MISMATCH 1 and the point in output.
    # Both passes carry the same changed value, so the change is a MISMATCH and not a FLAKY (passes agree).
    dB = os.path.join(base, "posctrl_B")
    obsB1 = observed_from_prereg(rc1_override=("SYN-REP-1", "0"))
    obsB2 = observed_from_prereg(rc1_override=("SYN-REP-1", "0"))
    preB = write_case(dB, "B", obsB1, obsB2)
    rcB, outB, errB = run_verdict(preB, dB, "VERDICT_M2_R8_M2a_POSCTRL_B" + TAG)
    sB = parse_summary("VERDICT_M2_R8_M2a_POSCTRL_B" + TAG) if rcB == 0 else {}
    verdictB = open(os.path.join(EV, "VERDICT_M2_R8_M2a_POSCTRL_B" + TAG + "_VERDICT.tsv"), encoding="utf-8").read() if rcB == 0 else ""
    # the changed point must appear in the output with verdict MISMATCH (not FLAKY)
    pid_in_out = any(l.split("\t")[0] == "SYN-REP-1" and l.split("\t")[1] == "MISMATCH" for l in verdictB.splitlines())
    results["B"] = (rcB, sB, pid_in_out)
    lines.append("CASE_B rc=%d summary=%s point_in_output=%s" % (rcB, outB or errB, pid_in_out))

    # Case C: pass1 and pass2 disagree on SYN-SWAL-1 (class changed in pass2).  Expected FLAKY 1.
    dC = os.path.join(base, "posctrl_C")
    obsC2 = observed_from_prereg()
    for r in obsC2:
        if r[0] == "SYN-SWAL-1":
            r[2] = "1"  # rc1 0 -> 1 in pass2 (rc1 decides the class): SILENT_SWALLOW becomes REPORTED_FAILURE
    preC = write_case(dC, "C", obsA, obsC2)
    rcC, outC, errC = run_verdict(preC, dC, "VERDICT_M2_R8_M2a_POSCTRL_C" + TAG)
    sC = parse_summary("VERDICT_M2_R8_M2a_POSCTRL_C" + TAG) if rcC == 0 else {}
    results["C"] = (rcC, sC)
    lines.append("CASE_C rc=%d summary=%s" % (rcC, outC or errC))

    okA = results["A"][0] == 0 and results["A"][1].get("MISMATCH") == "0" and results["A"][1].get("FLAKY") == "0"
    okB = results["B"][0] == 0 and results["B"][1].get("MISMATCH") == "1" and results["B"][1].get("FLAKY") == "0" and results["B"][2]
    okC = results["C"][0] == 0 and results["C"][1].get("FLAKY") == "1"
    passed = okA and okB and okC
    lines.insert(0, "# POSCTRL_M2_R8_M2a -- positive controls of verdict_m2_r8m2a.py on synthetic data (no S4 run)")
    lines.append("A MISMATCH=%s FLAKY=%s expected 0/0" % (results["A"][1].get("MISMATCH"), results["A"][1].get("FLAKY")))
    lines.append("B MISMATCH=%s FLAKY=%s point_in_output=%s expected 1/0/True" % (results["B"][1].get("MISMATCH"), results["B"][1].get("FLAKY"), results["B"][2]))
    lines.append("C FLAKY=%s expected 1" % results["C"][1].get("FLAKY"))
    lines.append("POSCTRL=%s" % ("PASS" if passed else "FAIL"))
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("POSCTRL=%s" % ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
