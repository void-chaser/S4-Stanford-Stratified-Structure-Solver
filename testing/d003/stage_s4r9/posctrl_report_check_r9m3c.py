#!/usr/bin/env python3
# posctrl_report_check_r9m3c.py -- shakedown positive control: write a deliberately wrong copy of the report under
# $EV/posctrl/report_check/, invoke the formal report_check on it, and require a FAIL. New file (r9m3c).
# usage: posctrl_report_check_r9m3c.py SRC_REPORT
import os, sys, subprocess
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
D = os.path.join(EV, "posctrl/report_check")
CHECK = os.path.join(REPO, "testing/d003/stage_s4r9/report_check_r9m3c.py")
OUT = os.path.join(EV, "POSCTRL_REPORT_CHECK_R9M3C.txt")
NL = chr(10)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3c_REPORT.md")
    os.makedirs(D, exist_ok=True)
    text = open(src, encoding="utf-8").read()
    wrong = text
    for a, b in (("CONTROL_OK=17, E2E_OK=25", "CONTROL_OK=99, E2E_OK=25"),
                 ("4 遍 × 2 段对账 全部 OK", "4 遍 × 2 段对账 存在 FAIL"),
                 ("DIFFS=0", "DIFFS=7")):
        wrong = wrong.replace(a, b)
    if wrong == text:
        print("POSCTRL_REPORT_CHECK: FAIL (no sentinel text to tamper)")
        open(OUT, "w", encoding="utf-8").write("# POSCTRL_REPORT_CHECK_R9M3C.txt" + NL + "RESULT: FAIL (no sentinel found)" + NL)
        return 1
    wp = os.path.join(D, "WRONG_REPORT.md")
    open(wp, "w", encoding="utf-8").write(wrong)
    cout = os.path.join(D, "REPORT_CHECK_WRONG.txt")
    p = subprocess.run([sys.executable, "-I", "-B", CHECK, wp, cout], cwd=REPO,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    fails = -1
    if os.path.isfile(cout):
        for line in open(cout, encoding="utf-8"):
            if line.startswith("FAILS="):
                fails = int(line.strip().split("=")[1])
    ok = fails > 0
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_REPORT_CHECK_R9M3C.txt -- report_check on a deliberately wrong report copy (shakedown)" + NL)
        fh.write("TAMPERED_COPY: " + os.path.relpath(wp, REPO) + NL)
        fh.write("REPORT_CHECK_FAILS_ON_WRONG_COPY=%d" % fails + NL)
        fh.write("RESULT: %s (required FAILS>0)" % ("PASS" if ok else "FAIL") + NL)
    print("wrong-copy FAILS=%d -> %s" % (fails, "PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
