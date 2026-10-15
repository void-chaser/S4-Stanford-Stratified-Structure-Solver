#!/usr/bin/env python3
# state_bytes_r8m1c2.py -- reports the UTF-8 byte size of checkpoints/p05/STATE.md and checks the 8192 limit.
# Usage: python3 -I -B state_bytes_r8m1c2.py
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
STATE = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
n = os.path.getsize(STATE)
print("STATE_BYTES=%d" % n)
print("STATE_LIMIT_OK=%s" % (n <= 8192))
sys.exit(0 if n <= 8192 else 1)
