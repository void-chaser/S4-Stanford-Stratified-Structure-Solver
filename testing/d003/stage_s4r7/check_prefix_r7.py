#!/usr/bin/env python3
"""P05-S4 R7 cont5 (U57, E7-25): prefix check for append-only files (new file; read only except OUT).

For an append-only file F, a manifest line "<sha256>  <path>  <N>" (N = byte length of F when the manifest was written) is
checked as: sha256(first N bytes of the current F) == <sha256>.  The check is done for ERRATA_7.txt and RULINGS.tsv.
The older manifests are not edited.  The result is written to OUT (one new file, U17).

Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r7/check_prefix_r7.py REFS.tsv OUT.txt
REFS.tsv is written by record_prefix_refs_r7.py (rows: name, N, sha256), read by name: ERRATA_7 or RULINGS.
Exit status 0 only if every check holds.
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ERRATA = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7", "ERRATA_7.txt")
RULINGS = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")

def sha_prefix(path, n):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        left = n
        while left > 0:
            chunk = fh.read(min(1 << 16, left))
            if not chunk:
                return None
            h.update(chunk)
            left -= len(chunk)
    return h.hexdigest()


def read_refs(path):
    refs = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 3:
                raise SystemExit("REFUSED: bad reference line in %s: %r" % (path, line))
            refs.append((parts[0], int(parts[1]), parts[2]))
    return refs


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: check_prefix_r7.py REFS.tsv OUT.txt")
    refs_path, out = argv[1], argv[2]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    lines = ["# prefix check for append-only files (U57, E7-25).  sha256(first N bytes of current file) must equal the reference sha256.",
             "file\tN_bytes\treference_sha256\tcurrent_prefix_sha256\tresult"]
    ok = True
    for path in (ERRATA, RULINGS):
        name = os.path.relpath(path, REPO)
        size = os.path.getsize(path)
        lines.append("# %s current_size=%d" % (name, size))
    if not os.path.isfile(refs_path):
        lines.append("# no reference file; cannot compare without recorded (N, sha256) pairs")
        ok = False
    else:
        for fname, n, ref in read_refs(refs_path):
            target = ERRATA if fname == "ERRATA_7" else RULINGS
            cur = sha_prefix(target, n)
            res = "OK" if (cur is not None and cur == ref) else "FAIL"
            ok = ok and res == "OK"
            lines.append("\t".join([fname, str(n), ref, cur or "NONE", res]))
    lines.append("# all_ok=%s" % ("YES" if ok else "NO"))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("all_ok=%s -> %s" % ("YES" if ok else "NO", out))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
