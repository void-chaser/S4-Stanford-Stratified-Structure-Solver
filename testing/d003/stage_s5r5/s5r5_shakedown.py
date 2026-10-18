#!/usr/bin/env python3
# s5r5_shakedown.py -- run the end gate on the staging roots (U388: the rehearsal and the formal run differ
# ONLY in the root path arguments; same script, same logic). Writes the staging output under $EV/shakedown/gate/.
# The output is NOT read by the gate; it is verified by s5r5_shakedown_verify.py (outside the gate).
import os, sys, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r5")
STAGE = os.path.join(EV, "shakedown")
GATE = os.path.join(REPO, "testing/d003/stage_s5r5/gate_check_s5r5.py")
OUT = os.path.join(STAGE, "gate/GATE_S5R5_end.txt")


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    cmd = [sys.executable, "-I", "-B", GATE, "end",
           "--ev-root", os.path.join(STAGE, "ev"),
           "--p05-root", os.path.join(STAGE, "p05"),
           "--out", OUT]
    p = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
    if not os.path.isfile(OUT):
        print("HARD_STOP staging gate produced no output; stderr tail:")
        print(p.stderr[-2000:])
        return 2
    t = open(OUT, encoding="utf-8").read()
    lines = [l for l in t.splitlines() if l.startswith(("COUNTS", "FAILS=", "CHECK_CRASHED=", "FAIL\t", "CRASHED\t"))]
    print("\n".join(lines))
    print("WROTE " + os.path.relpath(OUT, REPO))
    return 0 if p.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
