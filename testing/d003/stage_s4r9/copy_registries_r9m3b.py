#!/usr/bin/env python3
# copy_registries_r9m3b.py -- copy the round's small tables into registries/s4r9/M3b, verify every sha256, write the
# manifest, and declare the script-internal outputs in $EV/REGISTRY_OUTPUTS_R9M3B.tsv (U335). New file (r9m3b).
# usage: python3 -I -B testing/d003/stage_s4r9/copy_registries_r9m3b.py DEST FILE [FILE ...]
import os, sys, hashlib, shutil

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
NL = chr(10)


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            b = fh.read(65536)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def main():
    dest = sys.argv[1]
    srcs = sys.argv[2:]
    os.makedirs(dest, exist_ok=True)
    rows = []
    bad = []
    for src in srcs:
        if not os.path.isfile(src):
            bad.append(src + ":missing")
            continue
        name = os.path.basename(src)
        dst = os.path.join(dest, name)
        shutil.copyfile(src, dst)
        a, b = sha(src), sha(dst)
        if a != b:
            bad.append(name + ":sha")
        rows.append((a, name))
    rows.sort(key=lambda x: x[1])
    man = os.path.join(dest, "SHA256SUMS.txt")
    with open(man, "w", encoding="utf-8") as fh:
        for h, name in rows:
            fh.write("%s  %s" % (h, name) + NL)
    declared = [os.path.relpath(os.path.join(dest, name), REPO) for h, name in rows]
    declared.append(os.path.relpath(man, REPO))
    with open(os.path.join(EV, "REGISTRY_OUTPUTS_R9M3B.tsv"), "w", encoding="utf-8") as fh:
        fh.write("# REGISTRY_OUTPUTS_R9M3B.tsv -- outputs produced inside the scripts (declared for the end gate, U335)" + NL)
        for rel in declared:
            fh.write(rel + NL)
    for rel in declared:
        print("DECLARED " + rel)
    print("copied=%d manifest=%s bad=%d" % (len(rows), os.path.relpath(man, REPO), len(bad)))
    for b in bad:
        print("BAD " + b)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
