#!/usr/bin/env python3
# append_end_registries_r8m1c4.py -- P05-S4 R8 M1c4 end-gate registry copy (brief 8.2). New file.
# Copies the end-gate file(s) and the report-count check file(s) from $EV to registries/s4r8/M1c/r8m1c4/ with their
# original names (U226), verifies sha256, and writes SHA256SUMS_END.txt. Refuses if SHA256SUMS_END.txt exists (U17).
# Usage: python3 -I -B testing/d003/stage_s4/append_end_registries_r8m1c4.py
import glob
import hashlib
import os
import shutil
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
DST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c4")
END_SUMS = os.path.join(DST, "SHA256SUMS_END.txt")
if os.path.exists(END_SUMS):
    print("REFUSED exists (U17): %s" % END_SUMS)
    sys.exit(2)
if not os.path.isdir(DST):
    print("REFUSED registries r8m1c4 directory missing")
    sys.exit(2)

# the end gate file(s) and the report count check file(s), by name pattern (no renaming)
names = sorted(set(
    [os.path.basename(p) for p in glob.glob(os.path.join(EV, "GATE_R8_M1c4_END*.txt"))] +
    [os.path.basename(p) for p in glob.glob(os.path.join(EV, "REPORT_COUNT_CHECK_R8_M1c4*.txt"))]
))
if not names:
    print("MISSING_END_FILES: no GATE_R8_M1c4_END / REPORT_COUNT_CHECK file in EV")
    sys.exit(2)
sums = []
for name in names:
    src = os.path.join(EV, name)
    dst = os.path.join(DST, name)
    if os.path.exists(dst):
        print("REFUSED destination exists (U17): %s" % dst)
        sys.exit(2)
    shutil.copyfile(src, dst)
    with open(src, "rb") as fh:
        s_sha = hashlib.sha256(fh.read()).hexdigest()
    with open(dst, "rb") as fh:
        d_sha = hashlib.sha256(fh.read()).hexdigest()
    if s_sha != d_sha:
        print("COPY_SHA_MISMATCH %s" % name)
        sys.exit(1)
    sums.append((d_sha, name))
with open(END_SUMS, "x", encoding="utf-8") as fh:
    for sha, name in sums:
        fh.write("%s  %s\n" % (sha, name))
print("END_COPIED=%d files: %s" % (len(sums), ",".join(n for _, n in sums)))
