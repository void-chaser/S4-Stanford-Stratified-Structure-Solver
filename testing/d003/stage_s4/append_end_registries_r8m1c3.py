#!/usr/bin/env python3
# append_end_registries_r8m1c3.py -- P05-S4 R8 M1c3 end-gate registry copy (brief 9.2). New file.
# After the end gate: copies GATE_R8_M1c3_END.txt and REPORT_COUNT_CHECK_R8_M1c3.txt into
# checkpoints/p05/registries/s4r8/M1c/r8m1c3/ and writes SHA256SUMS_END.txt (the list of these two files).
# The original SHA256SUMS.txt is not rewritten (U17); SHA256SUMS_END.txt records the two appended entries.
# Checks each copy's sha256 against its source.  Refuses if a destination exists.
# Usage: python3 -I -B append_end_registries_r8m1c3.py
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
DST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c3")
PLAN = [
    (os.path.join(EV, "GATE_R8_M1c3_END.txt"), "GATE_R8_M1c3_END.txt"),
    (os.path.join(EV, "REPORT_COUNT_CHECK_R8_M1c3.txt"), "REPORT_COUNT_CHECK_R8_M1c3.txt"),
]
missing = [s for s, _ in PLAN if not os.path.isfile(s)]
if missing:
    print("MISSING_INPUTS=%d %s" % (len(missing), missing))
    sys.exit(2)
if not os.path.isdir(DST):
    print("REFUSED destination directory missing: %s" % DST)
    sys.exit(2)
out_sums = os.path.join(DST, "SHA256SUMS_END.txt")
if os.path.exists(out_sums):
    print("REFUSED exists (U17): %s" % out_sums)
    sys.exit(2)
for _, name in PLAN:
    if os.path.exists(os.path.join(DST, name)):
        print("REFUSED destination exists (U17): %s" % name)
        sys.exit(2)

sums = []
for src, name in PLAN:
    dst = os.path.join(DST, name)
    shutil.copyfile(src, dst)
    s_sha = hashlib.sha256(open(src, "rb").read()).hexdigest()
    d_sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()
    if s_sha != d_sha:
        print("COPY_SHA_MISMATCH %s" % name)
        sys.exit(1)
    sums.append((d_sha, name))
with open(out_sums, "w", encoding="utf-8") as fh:
    for sha, name in sums:
        fh.write("%s  %s\n" % (sha, name))
print("END_COPIED=%d -> %s" % (len(sums), DST))
