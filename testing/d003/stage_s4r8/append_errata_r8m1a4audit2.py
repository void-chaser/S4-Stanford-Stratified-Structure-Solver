#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a audit part 2 (r8m1a4audit2): append-only extension of registries/s4r8/ERRATA_8.txt.  New file (U17).

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/append_errata_r8m1a4audit2.py TEXT_FILE OLD_BYTES OLD_SHA256

TEXT_FILE is a plain UTF-8 evidence file written before this call (under the round's evidence directory); its content is
appended verbatim.  The script refuses unless:
  - the first OLD_BYTES bytes of ERRATA_8.txt hash to OLD_SHA256 (the prefix that existed before the append);
  - TEXT_FILE ends with a newline;
  - the entry id on the first line of TEXT_FILE does not already appear in ERRATA_8.txt.
After the append the same prefix is checked again.  The script never truncates, never rewrites and never edits an earlier line.
"""
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ERRATA = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "ERRATA_8.txt")
EVDIR = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit2")
ID_RE = re.compile(r"^(E8-\d+)\s")


def prefix_sha(path, nbytes):
    with open(path, "rb") as fh:
        data = fh.read(nbytes)
    if len(data) != nbytes:
        raise SystemExit("REFUSED: file shorter than %d bytes" % nbytes)
    return hashlib.sha256(data).hexdigest()


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: append_errata_r8m1a4audit2.py TEXT_FILE OLD_BYTES OLD_SHA256")
    text_file = os.path.realpath(argv[1])
    old_bytes = int(argv[2])
    old_sha = argv[3]
    if not text_file.startswith(os.path.realpath(EVDIR) + os.sep):
        raise SystemExit("REFUSED: TEXT_FILE must be inside the round evidence directory")
    if not os.path.isfile(text_file):
        raise SystemExit("REFUSED: text file missing: %s" % text_file)
    if not os.path.isfile(ERRATA):
        raise SystemExit("REFUSED: ERRATA missing: %s" % ERRATA)
    if os.path.getsize(ERRATA) != old_bytes:
        raise SystemExit("REFUSED: ERRATA size %d != expected %d" % (os.path.getsize(ERRATA), old_bytes))
    if prefix_sha(ERRATA, old_bytes) != old_sha:
        raise SystemExit("REFUSED: ERRATA prefix sha256 mismatch before append")
    with open(text_file, "rb") as fh:
        payload = fh.read()
    if not payload.endswith(b"\n"):
        raise SystemExit("REFUSED: TEXT_FILE must end with a newline")
    text = payload.decode("utf-8")
    m = ID_RE.match(text.splitlines()[0])
    if not m:
        raise SystemExit("REFUSED: TEXT_FILE first line does not start with an E8 id")
    eid = m.group(1)
    with open(ERRATA, "r", encoding="utf-8") as fh:
        existing = fh.read()
    if re.search(r"^%s\s" % re.escape(eid), existing, flags=re.M):
        raise SystemExit("REFUSED: entry %s already present" % eid)
    with open(ERRATA, "ab") as fh:
        fh.write(payload)
    new_size = os.path.getsize(ERRATA)
    if new_size != old_bytes + len(payload):
        raise SystemExit("REFUSED: post-append size unexpected")
    if prefix_sha(ERRATA, old_bytes) != old_sha:
        raise SystemExit("FAIL: prefix changed by append (should be impossible)")
    print("append_errata_r8m1a4audit2: appended entry %s, bytes %d -> %d; prefix %d verified" % (
        eid, old_bytes, new_size, old_bytes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
