#!/usr/bin/env python3
# posctrl_report_check_r9m3d.py -- positive control for the formal report check: write a deliberately wrong copy of the
# report (wrong derived counts) under $EV/posctrl/report_check/ and require the formal report_check to report FAILS>0.
# New file (r9m3d). usage: posctrl_report_check_r9m3d.py SRC_REPORT [--state PATH]
import os, sys, subprocess
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
D = os.path.join(EV, "posctrl/report_check")
CHECK = os.path.join(REPO, "testing/d003/stage_s4r9/report_check_r9m3d.py")
OUT = os.path.join(EV, "POSCTRL_REPORT_CHECK_R9M3D.txt")
NL = chr(10)
TAMPERS = [("6/6 属实", "5/6 属实"), ("唯一 id=26", "唯一 id=27"), ("S5 移交：唯一项=7", "S5 移交：唯一项=8"),
           ("ERRATA_9.txt 最后 E9-73", "ERRATA_9.txt 最后 E9-99")]


def main():
    args = [a for a in sys.argv[1:]]
    src = os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3d_REPORT.md")
    state = os.path.join(REPO, "checkpoints/p05/STATE.md")
    i = 0
    while i < len(args):
        if args[i] == "--state" and i + 1 < len(args):
            state = args[i + 1]; i += 2
        else:
            src = args[i]; i += 1
    os.makedirs(D, exist_ok=True)
    text = open(src, encoding="utf-8").read()
    wrong = text
    hit = 0
    for a, b in TAMPERS:
        if a in wrong:
            wrong = wrong.replace(a, b)
            hit += 1
    if hit == 0:
        print("POSCTRL_REPORT_CHECK: FAIL (no sentinel text to tamper)")
        open(OUT, "w", encoding="utf-8").write("# POSCTRL_REPORT_CHECK_R9M3D.txt" + NL + "RESULT: FAIL (no sentinel)" + NL)
        return 1
    wp = os.path.join(D, "WRONG_REPORT.md")
    open(wp, "w", encoding="utf-8").write(wrong)
    cout = os.path.join(D, "REPORT_CHECK_WRONG.txt")
    p = subprocess.run([sys.executable, "-I", "-B", CHECK, wp, cout, state], cwd=REPO,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    fails = -1
    if os.path.isfile(cout):
        for line in open(cout, encoding="utf-8"):
            if line.startswith("FAILS="):
                fails = int(line.strip().split("=")[1])
    ok = fails > 0
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_REPORT_CHECK_R9M3D.txt -- report_check on a deliberately wrong report copy" + NL)
        fh.write("TAMPERED_COPY: " + os.path.relpath(wp, REPO) + " (sentinel replacements=%d)" % hit + NL)
        fh.write("REPORT_CHECK_FAILS_ON_WRONG_COPY=%d" % fails + NL)
        fh.write("RESULT: %s (required FAILS>0)" % ("PASS" if ok else "FAIL") + NL)
    print("tampered_sentinels=%d wrong-copy FAILS=%d -> %s" % (hit, fails, "PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
