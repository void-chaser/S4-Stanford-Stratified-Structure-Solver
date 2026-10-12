#!/usr/bin/env python3
"""P05-S4 R7 cont6 section 3: copy the small M2b prep tables to registries/s4r7/ and write SHA256SUMS_M2bprep.txt (new file).

Copies, from $EV (evidence) to registries/s4r7/ (repository), each listed file, verifies the copy byte for byte (sha256), and
writes one manifest.  Refuses if a destination already exists (U17).  Usage (through safe_run, absolute EVDIR):
  python3 -I -B testing/d003/stage_s4r7/copy_m2b_prep_r7.py EVDIR
"""
import hashlib
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DEST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
FILES = [
    "DRIVERS_R7_SEAM.tsv",
    "REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv",
    "DRYRUN_R7_M2b_run5b.txt",
    "PREFIX_CHECK_R7_run5.txt",
    "PREFIX_REFS_R7_run5.tsv",
    "CHECK_DRIVERS_VS_R4_R7_run5.tsv",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: copy_m2b_prep_r7.py EVDIR")
    ev = argv[1]
    if not os.path.isabs(ev):
        raise SystemExit("REFUSED: EVDIR must be absolute")
    manifest = os.path.join(DEST, "SHA256SUMS_M2bprep.txt")
    if os.path.exists(manifest):
        raise SystemExit("REFUSED: exists (U17): %s" % manifest)
    lines = []
    for name in FILES:
        src = os.path.join(ev, name)
        dst = os.path.join(DEST, name)
        if not os.path.isfile(src):
            raise SystemExit("REFUSED: missing source %s" % src)
        if os.path.exists(dst):
            raise SystemExit("REFUSED: exists (U17): %s" % dst)
        shutil.copyfile(src, dst)
        if sha256(src) != sha256(dst):
            raise SystemExit("REFUSED: copy mismatch %s" % name)
        lines.append("%s  %s" % (sha256(dst), name))
    with open(manifest, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("copied %d files; manifest %s" % (len(FILES), manifest))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
