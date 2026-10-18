#!/usr/bin/env python3
# s5r5_appendix_a.py -- append the staging-rehearsal appendix (A) to the R5 report, after the rehearsal and
# BEFORE record commit (i). Only appends; the report body above the "## 附录 A" heading is not touched.
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
REPORT = os.path.join(P05, "P05_S5R5_REPORT.md")
NL = chr(10)


def main():
    if "## 附录 C" in open(REPORT, encoding="utf-8").read():
        print("HARD_STOP appendix C already present; appendix A must be appended before the gate")
        return 2
    t = open(REPORT, encoding="utf-8").read()
    if "## 附录 A" not in t:
        print("HARD_STOP report has no appendix A heading")
        return 2
    a = open(os.path.join(EV, "APPENDIX_A_S5R5.txt"), encoding="utf-8").read()
    if a and not a.startswith(NL):
        a = NL + a
    with open(REPORT, "a", encoding="utf-8") as fh:
        fh.write(a + ("" if a.endswith(NL) else NL))
    print("APPENDIX_A appended bytes=%d" % len(a))
    print("REPORT sha256=" + hashlib.sha256(open(REPORT, "rb").read()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
