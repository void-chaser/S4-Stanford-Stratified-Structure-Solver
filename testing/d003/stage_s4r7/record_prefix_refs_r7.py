#!/usr/bin/env python3
"""P05-S4 R7 cont5 (U57, E7-25): record the prefix references from the commit history (new file; writes OUT only).

For each append-only file, reads its content at a fixed earlier commit with `git show <commit>:<path>` (read only, via a
subprocess, no shell pipe), takes the byte length N of that content, and records (file, N, sha256 of the whole content).
Because the file is append-only, sha256 of the first N bytes of the current file must equal that value.
Writes one new file OUT (U17).  Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r7/record_prefix_refs_r7.py OUT.tsv
"""
import hashlib
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
# (name in the check, path in the repository, commit at which the content was the recorded state)
TARGETS = [
    ("RULINGS", "checkpoints/p05/registries/RULINGS.tsv", "db92648"),
    ("ERRATA_7", "checkpoints/p05/registries/s4r7/ERRATA_7.txt", "6319a3c"),
]


def show(commit, path):
    p = subprocess.run(["git", "-C", REPO, "show", "%s:%s" % (commit, path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise SystemExit("REFUSED: git show failed for %s:%s: %s" % (commit, path, p.stderr.decode("utf-8", "replace")))
    return p.stdout


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: record_prefix_refs_r7.py OUT.tsv")
    out = argv[1]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    lines = ["# prefix references for append-only files (U57, E7-25).  Each row: name, N bytes at the commit, sha256 of those bytes.",
             "# source commit and path are listed in the comment column."]
    for name, path, commit in TARGETS:
        data = show(commit, path)
        lines.append("# %s source=%s:%s" % (name, commit, path))
        lines.append("\t".join([name, str(len(data)), hashlib.sha256(data).hexdigest()]))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
