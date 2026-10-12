#!/usr/bin/env python3
# r6c_registry_copy.py -- P05-S4 R6c registry copy and checksum (new file).  Copies the small result tables from the evidence
# directory to checkpoints/p05/registries/s4r6c/, writes SHA256SUMS.txt there, and re-reads both sides to compare sha256.
# Every comparison is computed by this script.  Refuses to overwrite an existing destination (U17).
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c_registry_copy.py EVDIR DESTDIR NAME [NAME ...]
import hashlib
import os
import shutil
import sys


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv):
    if len(argv) < 4:
        raise SystemExit("usage: r6c_registry_copy.py EVDIR DESTDIR NAME [NAME ...]")
    ev, dest, names = argv[1], argv[2], argv[3:]
    os.makedirs(dest, exist_ok=True)
    pairs = []
    for n in names:
        src = os.path.join(ev, n)
        dst = os.path.join(dest, n)
        if not os.path.isfile(src):
            raise SystemExit("REFUSED: missing source %s" % src)
        if os.path.exists(dst):
            raise SystemExit("REFUSED: destination exists, never overwritten (U17): %s" % dst)
        pairs.append((src, dst, n))
    for src, dst, n in pairs:
        shutil.copyfile(src, dst)
    sums = os.path.join(dest, "SHA256SUMS.txt")
    if os.path.exists(sums):
        raise SystemExit("REFUSED: exists: %s" % sums)
    lines = ["# SHA256SUMS for checkpoints/p05/registries/s4r6c (R6c milestone copy).  Written by r6c_registry_copy.py.",
             "# Excludes the evidence safe_run.log (AGENTS 7; U17)."]
    for src, dst, n in pairs:
        lines.append("%s  %s" % (sha256_file(dst), n))
    # files already in the destination (e.g. ERRATA_6c.txt, written at the gate) are listed too, without copying
    for n in sorted(os.listdir(dest)):
        p = os.path.join(dest, n)
        if os.path.isfile(p) and n != "SHA256SUMS.txt" and n not in names:
            lines.append("%s  %s" % (sha256_file(p), n))
    with open(sums, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    # verification: compare source and copy sha256, and the manifest entries
    ok = 0
    bad = []
    for src, dst, n in pairs:
        if sha256_file(src) == sha256_file(dst):
            ok += 1
        else:
            bad.append(n)
    man_ok = 0
    man_bad = []
    with open(sums, encoding="utf-8") as fh:
        for raw in fh:
            if raw.startswith("#") or not raw.strip():
                continue
            want, name = raw.rstrip("\n").split("  ", 1)
            if sha256_file(os.path.join(dest, name)) == want:
                man_ok += 1
            else:
                man_bad.append(name)
    print("copied=%d src_eq_dst_ok=%d bad=%s manifest_ok=%d manifest_bad=%s" % (len(pairs), ok, bad, man_ok, man_bad))
    return 0 if (not bad and not man_bad) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
