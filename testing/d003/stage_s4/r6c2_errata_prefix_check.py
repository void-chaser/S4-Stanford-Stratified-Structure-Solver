#!/usr/bin/env python3
# r6c2_errata_prefix_check.py -- P05-S4 R6c2 (new file; ERRATA E6c-6).
# Compares the first 64 lines of the CURRENT registries/s4r6c/ERRATA_6c.txt, byte for byte, with the 64-line version
# committed in 6bba0bd (read with git show; nothing is written to the repository).  Result to EVDIR/ERRATA_6c_PREFIX_CHECK.txt.
# Usage: python3 -I -B testing/d003/stage_s4/r6c2_errata_prefix_check.py EVDIR
import hashlib
import os
import subprocess
import sys

REL = "checkpoints/p05/registries/s4r6c/ERRATA_6c.txt"
COMMIT = "6bba0bd"
N = 64


def git_bytes(*args):
    p = subprocess.run(["git"] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.returncode, p.stdout


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: r6c2_errata_prefix_check.py EVDIR")
    ev = argv[1]
    out = os.path.join(ev, "ERRATA_6c_PREFIX_CHECK.txt")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out)
    repo = subprocess.run(["git", "rev-parse", "--show-toplevel"], stdout=subprocess.PIPE, check=False).stdout.decode().strip()
    with open(os.path.join(repo, REL), "rb") as fh:
        cur = fh.read()
    rc, old = git_bytes("show", "%s:%s" % (COMMIT, REL))
    if rc != 0:
        raise SystemExit("REFUSED: git show failed for %s:%s" % (COMMIT, REL))
    cur_l = cur.splitlines(keepends=True)
    old_l = old.splitlines(keepends=True)
    same = (len(old_l) == N and len(cur_l) >= N and cur_l[:N] == old_l)
    lines = [
        "# ERRATA_6c_PREFIX_CHECK.txt -- E6c-6 check (r6c2_errata_prefix_check.py)",
        "file\t%s" % REL,
        "commit\t%s" % COMMIT,
        "committed_lines\t%d" % len(old_l),
        "committed_sha256\t%s" % hashlib.sha256(old).hexdigest(),
        "current_lines\t%d" % len(cur_l),
        "current_sha256\t%s" % hashlib.sha256(cur).hexdigest(),
        "first_%d_lines_byte_identical\t%s" % (N, "YES" if same else "NO"),
        "RESULT\t%s" % ("PASS" if same else "FAIL"),
    ]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0 if same else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
