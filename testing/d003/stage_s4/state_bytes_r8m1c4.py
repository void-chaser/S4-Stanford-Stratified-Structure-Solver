#!/usr/bin/env python3
# state_bytes_r8m1c4.py -- P05-S4 R8 M1c4: byte count of checkpoints/p05/STATE.md (must be <= 8192; brief 8.4). New file.
# Output: $EV/STATE_BYTES_R8_M1c4.txt (one line: STATE_BYTES=<n> LIMIT=8192 RESULT=PASS|FAIL).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- python3 -I -B testing/d003/stage_s4/state_bytes_r8m1c4.py
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
STATE = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
OUT = os.path.join(EV, "STATE_BYTES_R8_M1c4.txt")
if os.path.exists(OUT):
    print("REFUSED exists (U17): %s" % OUT)
    sys.exit(2)
n = os.path.getsize(STATE)
res = "PASS" if n <= 8192 else "FAIL"
with open(OUT, "x", encoding="utf-8") as fh:
    fh.write("STATE_BYTES=%d LIMIT=8192 RESULT=%s\n" % (n, res))
print("STATE_BYTES=%d RESULT=%s" % (n, res))
sys.exit(0 if res == "PASS" else 1)
