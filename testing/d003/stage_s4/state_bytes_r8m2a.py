#!/usr/bin/env python3
# state_bytes_r8m2a.py -- P05-S4 R8 M2a: report the UTF-8 byte count of checkpoints/p05/STATE.md (limit 8192).
# Writes $EV/STATE_BYTES_R8_M2a.txt (refuses to overwrite, U17).  Read-only on STATE.md.
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
STATE = os.path.join(REPO, "checkpoints", "p05", "STATE.md")
# R2 name: the first run wrote STATE_BYTES_R8_M2a.txt (8900 bytes, FAIL, before compression); kept (U17).
# R3 name: R2 (8393 bytes, FAIL, before the second compression) is kept (U17).
OUT = os.path.join(EV, "STATE_BYTES_R8_M2a_R3.txt")


def main():
    if os.path.exists(OUT):
        print("state_bytes_r8m2a: REFUSED exists (U17): %s" % OUT)
        return 2
    with open(STATE, "rb") as fh:
        data = fh.read()
    n = len(data)
    digest = hashlib.sha256(data).hexdigest()
    ok = n <= 8192
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("STATE_BYTES=%d\nSTATE_SHA256=%s\nLIMIT=8192\nSTATE_LE_8192=%s\n" % (n, digest, "PASS" if ok else "FAIL"))
    print("STATE_BYTES=%d LE_8192=%s" % (n, "PASS" if ok else "FAIL"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
