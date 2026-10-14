#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 3 (r8m1a4audit3): append ERRATA E8-67 to registries/s4r8/ERRATA_8.txt.  New file.

Appends only; the existing content is checked to be unchanged (prefix bytes and sha256 from the start gate).
The entry text is read from the file APPEND_ERRATA_E8_67_R8_M1a4AUDIT3.txt in the round evidence directory (written by the
round before this script runs), so the ERRATA body itself never contains a temporary-area literal.
Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/append_errata_r8m1a4audit3.py PREFIX_BYTES PREFIX_SHA256 ENTRY_FILE_NAME
"""
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit3")
ERR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "ERRATA_8.txt")
NAME_RE = re.compile(r"^APPEND_ERRATA_E8_67_R8_M1a4AUDIT3[A-Za-z0-9_]*\.txt$")


def main(argv):
    if len(argv) != 4 or not NAME_RE.match(argv[3]):
        raise SystemExit("usage: append_errata_r8m1a4audit3.py PREFIX_BYTES PREFIX_SHA256 APPEND_ERRATA_E8_67_R8_M1a4AUDIT3<name>.txt")
    pref_bytes = int(argv[1])
    pref_sha = argv[2]
    with open(ERR, "rb") as fh:
        data = fh.read()
    if len(data) < pref_bytes:
        raise SystemExit("REFUSED: ERRATA_8.txt is shorter than the recorded prefix")
    if hashlib.sha256(data[:pref_bytes]).hexdigest() != pref_sha:
        raise SystemExit("REFUSED: ERRATA_8.txt prefix sha256 differs from the start record")
    if b"E8-67" in data:
        raise SystemExit("REFUSED: E8-67 already present")
    src = os.path.join(EV, argv[3])
    with open(src, "rb") as fh:
        body = fh.read()
    if not body.endswith(b"\n"):
        raise SystemExit("REFUSED: entry body must end with a newline")
    if b"/tmp" in body:
        raise SystemExit("REFUSED: entry body contains a temporary-area literal")
    with open(ERR, "ab") as fh:
        fh.write(body)
    print("appended bytes=%d" % len(body))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
