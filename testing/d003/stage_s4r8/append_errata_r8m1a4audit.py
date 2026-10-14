#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a audit (r8m1a4audit): append-only extension of registries/s4r8/ERRATA_8.txt.  New file.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/append_errata_r8m1a4audit.py TEXT_FILE OLD_BYTES OLD_SHA256

TEXT_FILE is an evidence file written before this call; its content is appended verbatim.
The script refuses unless the first OLD_BYTES bytes of ERRATA_8.txt hash to OLD_SHA256 (the prefix
that existed before the append), and it re-checks the same prefix after the append.  It never truncates,
never rewrites, and never edits an earlier line.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ERRATA = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "ERRATA_8.txt")


def prefix_sha(path, nbytes):
    with open(path, "rb") as fh:
        data = fh.read(nbytes)
    if len(data) != nbytes:
        raise SystemExit("REFUSED: file shorter than %d bytes" % nbytes)
    return hashlib.sha256(data).hexdigest()


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: append_errata_r8m1a4audit.py TEXT_FILE OLD_BYTES OLD_SHA256")
    text_file = argv[1]
    old_bytes = int(argv[2])
    old_sha = argv[3]
    if not os.path.isfile(text_file):
        raise SystemExit("REFUSED: text file missing: %s" % text_file)
    if not os.path.isfile(ERRATA):
        raise SystemExit("REFUSED: ERRATA missing: %s" % ERRATA)
    cur_size = os.path.getsize(ERRATA)
    if cur_size != old_bytes:
        raise SystemExit("REFUSED: ERRATA size %d != expected %d" % (cur_size, old_bytes))
    got = prefix_sha(ERRATA, old_bytes)
    if got != old_sha:
        raise SystemExit("REFUSED: prefix sha256 %s != expected %s" % (got, old_sha))
    with open(text_file, "rb") as fh:
        add = fh.read()
    if not add.endswith(b"\n"):
        raise SystemExit("REFUSED: text must end with a newline")
    with open(ERRATA, "ab") as fh:
        fh.write(add)
    new_size = os.path.getsize(ERRATA)
    if new_size != old_bytes + len(add):
        raise SystemExit("REFUSED: post-append size mismatch")
    if prefix_sha(ERRATA, old_bytes) != old_sha:
        raise SystemExit("FAIL: prefix changed after append")
    print("APPEND_ERRATA_R8_M1a4AUDIT: appended %d bytes; prefix %d bytes unchanged; new size %d" % (
        len(add), old_bytes, new_size))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
