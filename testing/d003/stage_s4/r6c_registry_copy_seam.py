#!/usr/bin/env python3
# r6c_registry_copy_seam.py -- P05-S4 R6c-2 seam small tables: copy to checkpoints/p05/registries/s4r6c/ and write a SEPARATE
# checksum file SHA256SUMS_seam.txt (the milestone manifest SHA256SUMS.txt is not rewritten; U17).  Every comparison is computed
# here.  Refuses to overwrite any destination.
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c_registry_copy_seam.py EVDIR DESTDIR NAME [NAME ...]
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
        raise SystemExit("usage: r6c_registry_copy_seam.py EVDIR DESTDIR NAME [NAME ...]")
    ev, dest, names = argv[1], argv[2], argv[3:]
    os.makedirs(dest, exist_ok=True)
    sums = os.path.join(dest, "SHA256SUMS_seam.txt")
    if os.path.exists(sums):
        raise SystemExit("REFUSED: exists: %s" % sums)
    for n in names:
        src, dst = os.path.join(ev, n), os.path.join(dest, n)
        if not os.path.isfile(src):
            raise SystemExit("REFUSED: missing source %s" % src)
        if os.path.exists(dst):
            raise SystemExit("REFUSED: destination exists, never overwritten (U17): %s" % dst)
    for n in names:
        shutil.copyfile(os.path.join(ev, n), os.path.join(dest, n))
    lines = ["# SHA256SUMS_seam.txt for checkpoints/p05/registries/s4r6c (R6c-2 seam small tables).  Written by "
             "r6c_registry_copy_seam.py.  Separate from SHA256SUMS.txt (milestone) by U17."]
    for n in names:
        lines.append("%s  %s" % (sha256_file(os.path.join(dest, n)), n))
    with open(sums, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    ok, bad = 0, []
    for n in names:
        if sha256_file(os.path.join(ev, n)) == sha256_file(os.path.join(dest, n)):
            ok += 1
        else:
            bad.append(n)
    man_ok, man_bad = 0, []
    with open(sums, encoding="utf-8") as fh:
        for raw in fh:
            if raw.startswith("#") or not raw.strip():
                continue
            want, name = raw.rstrip("\n").split("  ", 1)
            if sha256_file(os.path.join(dest, name)) == want:
                man_ok += 1
            else:
                man_bad.append(name)
    print("copied=%d src_eq_dst_ok=%d bad=%s manifest_ok=%d manifest_bad=%s" % (len(names), ok, bad, man_ok, man_bad))
    return 0 if not bad and not man_bad else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
