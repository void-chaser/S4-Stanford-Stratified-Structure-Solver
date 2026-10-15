#!/usr/bin/env python3
# copy_r8m2a_end_r8m2a2.py -- P05-S4 R8 M2a2 section 4.0: backfill of the r8m2a end-gate registry files (E8-93).
# New file. Copies four r8m2a evidence files into the r8m2a registry directory under their original names,
# refuses to overwrite (U17), writes SHA256SUMS_END.txt for those four files and verifies each copy against its source.
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_SRC = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
EV_OUT = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a")
NAMES = [
    "GATE_R8_M2a_end.txt",
    "GATE_R8_M2a_end_R2.txt",
    "GATE_R8_M2a_end_R3.txt",
    "POSTCOMMIT_R8_M2a.txt",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    fails = 0
    report = []
    # All four sources must exist; all four targets and the manifest must be absent.
    for n in NAMES:
        src = os.path.join(EV_SRC, n)
        if not os.path.isfile(src):
            report.append("FAIL source_missing %s" % n)
            fails += 1
        dst = os.path.join(REG, n)
        if os.path.exists(dst):
            report.append("FAIL target_exists %s" % n)
            fails += 1
    man = os.path.join(REG, "SHA256SUMS_END.txt")
    if os.path.exists(man):
        report.append("FAIL target_exists SHA256SUMS_END.txt")
        fails += 1
    if fails:
        for line in report:
            print(line)
        print("COPY_END_R8M2A_FAILS=%d" % fails)
        return fails
    # Copy and verify.
    os.makedirs(REG, exist_ok=True)
    lines = []
    for n in NAMES:
        src = os.path.join(EV_SRC, n)
        dst = os.path.join(REG, n)
        with open(dst, "xb") as out, open(src, "rb") as inp:  # 'x': refuse overwrite (U17)
            shutil.copyfileobj(inp, out)
        s_sha = sha256_file(src)
        d_sha = sha256_file(dst)
        ok = s_sha == d_sha
        if not ok:
            fails += 1
        report.append("%s %s src_sha256=%s dst_sha256=%s" % ("PASS" if ok else "FAIL", n, s_sha, d_sha))
        lines.append("%s  %s" % (d_sha, n))
    with open(man, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    # Re-verify the manifest with -c semantics.
    ok_m = True
    with open(man, encoding="utf-8") as fh:
        for line in fh:
            sha, name = line.rstrip("\n").split("  ", 1)
            if sha256_file(os.path.join(REG, name)) != sha:
                ok_m = False
    report.append("%s SHA256SUMS_END_C_CHECK" % ("PASS" if ok_m else "FAIL"))
    if not ok_m:
        fails += 1
    for line in report:
        print(line)
    print("COPY_END_R8M2A_FAILS=%d" % fails)
    return fails


if __name__ == "__main__":
    sys.exit(main())
