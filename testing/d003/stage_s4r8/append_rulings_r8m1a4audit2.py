#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a audit part 2 (r8m1a4audit2): append-only extension of registries/RULINGS.tsv.  New file (U17).

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/append_rulings_r8m1a4audit2.py TEXT_FILE OLD_BYTES OLD_SHA256

TEXT_FILE is a 5-column TSV evidence file written before this call (under the round's evidence directory); its
content is appended verbatim.  The script refuses unless:
  - the first OLD_BYTES bytes of RULINGS.tsv hash to OLD_SHA256 (the prefix that existed before the append);
  - every non-comment line of TEXT_FILE has exactly 5 TAB-separated fields;
  - no ruling id in TEXT_FILE already appears in RULINGS.tsv.
After the append the same prefix is checked again.  The script never truncates, never rewrites and never edits an earlier line.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
RULINGS = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")
EVDIR = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit2")


def prefix_sha(path, nbytes):
    with open(path, "rb") as fh:
        data = fh.read(nbytes)
    if len(data) != nbytes:
        raise SystemExit("REFUSED: file shorter than %d bytes" % nbytes)
    return hashlib.sha256(data).hexdigest()


def read_ids(path):
    ids = set()
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            ids.add(line.split("\t", 1)[0])
    return ids


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: append_rulings_r8m1a4audit2.py TEXT_FILE OLD_BYTES OLD_SHA256")
    text_file = os.path.realpath(argv[1])
    old_bytes = int(argv[2])
    old_sha = argv[3]
    if not text_file.startswith(os.path.realpath(EVDIR) + os.sep):
        raise SystemExit("REFUSED: TEXT_FILE must be inside the round evidence directory")
    if not os.path.isfile(text_file):
        raise SystemExit("REFUSED: text file missing: %s" % text_file)
    if not os.path.isfile(RULINGS):
        raise SystemExit("REFUSED: RULINGS missing: %s" % RULINGS)
    if os.path.getsize(RULINGS) != old_bytes:
        raise SystemExit("REFUSED: RULINGS size %d != expected %d" % (os.path.getsize(RULINGS), old_bytes))
    if prefix_sha(RULINGS, old_bytes) != old_sha:
        raise SystemExit("REFUSED: RULINGS prefix sha256 mismatch before append")
    with open(text_file, "rb") as fh:
        payload = fh.read()
    if not payload.endswith(b"\n"):
        raise SystemExit("REFUSED: TEXT_FILE must end with a newline")
    lines = payload.decode("utf-8").splitlines()
    new_ids = []
    for ln in lines:
        if ln.startswith("#") or not ln.strip():
            continue
        fields = ln.split("\t")
        if len(fields) != 5:
            raise SystemExit("REFUSED: TEXT_FILE line does not have 5 columns: %r" % ln[:80])
        new_ids.append(fields[0])
    if not new_ids:
        raise SystemExit("REFUSED: TEXT_FILE has no ruling rows")
    existing = read_ids(RULINGS)
    dup = [i for i in new_ids if i in existing]
    if dup:
        raise SystemExit("REFUSED: ruling id already present: %s" % ",".join(dup))
    with open(RULINGS, "ab") as fh:
        fh.write(payload)
    new_size = os.path.getsize(RULINGS)
    if new_size != old_bytes + len(payload):
        raise SystemExit("REFUSED: post-append size unexpected")
    if prefix_sha(RULINGS, old_bytes) != old_sha:
        raise SystemExit("FAIL: prefix changed by append (should be impossible)")
    print("append_rulings_r8m1a4audit2: appended %d rows, bytes %d -> %d; prefix %d verified" % (
        len(new_ids), old_bytes, new_size, old_bytes))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
