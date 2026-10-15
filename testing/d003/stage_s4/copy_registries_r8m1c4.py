#!/usr/bin/env python3
# copy_registries_r8m1c4.py -- P05-S4 R8 M1c4 registry copy (brief 8.2, AGENTS.md 7.1). New file.
# Copies the small result tables of this round from $EV to checkpoints/p05/registries/s4r8/M1c/r8m1c4/ KEEPING THE
# ORIGINAL NAMES (U226: no renaming, no suffix stripping). Checks that every input exists BEFORE the directory is created,
# verifies each copy's sha256 against its source, and writes SHA256SUMS.txt.
# The end-gate files are copied afterwards by append_end_registries_r8m1c4.py, into SHA256SUMS_END.txt.
# Usage: python3 -I -B testing/d003/stage_s4/copy_registries_r8m1c4.py
import hashlib
import os
import shutil
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
DST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c4")
STAGE = os.path.join(REPO, "testing", "d003", "stage_s4")

# (source path, destination name = source name). Names are kept as they are (U226).
PLAN = []
for name in ("GATE_R8_M1c4_START.txt", "GATE_DIFF_R8_M1c4.txt",
             "RECHECK_F3_R8_M1c4.tsv", "M1_SUMMARY_R8_M1c4.tsv",
             "FIX_COVERAGE_M1_R8_M1c4_R2.tsv", "COMPARE_DIFF_R8_M1c4.txt",
             "CMP_REAL_R8_M1c4_VS_FROZEN.tsv", "CMP_REAL_R8_M1c4_F2_F3_DIFF.tsv",
             "CMP_OUTPUTS_R8_M1c4.txt",
             "POSCTRL_A_R8_M1c4_VS_FROZEN.tsv", "POSCTRL_A_R8_M1c4_F2_F3_DIFF.tsv",
             "POSCTRL_A2_R8_M1c4_VS_FROZEN.tsv", "POSCTRL_A2_R8_M1c4_F2_F3_DIFF.tsv",
             "POSCTRL_B_R8_M1c4_VS_FROZEN.tsv", "POSCTRL_B_R8_M1c4_F2_F3_DIFF.tsv",
             "POSCTRL_M1C_R8_M1c4.txt",
             "REGISTRY_NAME_MAP_R8_M1c3.tsv",
             "ERRATA_APPEND_R8_M1c4.txt", "RULINGS_APPEND_R8_M1c4.tsv"):
    PLAN.append((os.path.join(EV, name), name))
# the round's gate and registry scripts (committed as copies of the r8m1c4 records)
for name in ("gate_r8m1c4.sh", "gate_check_r8m1c4.py", "gate_allow_r8m1c4_start.txt",
             "gate_allow_r8m1c4_end.txt", "diff_gate_r8m1c4.sh"):
    PLAN.append((os.path.join(STAGE, name), name))

# 1. every input must exist before the directory is created
missing = [s for s, _ in PLAN if not os.path.isfile(s)]
if missing:
    print("MISSING_INPUTS=%d" % len(missing))
    for m in missing:
        print("  missing: %s" % m)
    sys.exit(2)
if os.path.exists(DST):
    print("REFUSED destination exists (U17): %s" % DST)
    sys.exit(2)

os.makedirs(DST)
sums = []
for src, dst_name in PLAN:
    dst = os.path.join(DST, dst_name)
    shutil.copyfile(src, dst)
    with open(src, "rb") as fh:
        s_sha = hashlib.sha256(fh.read()).hexdigest()
    with open(dst, "rb") as fh:
        d_sha = hashlib.sha256(fh.read()).hexdigest()
    if s_sha != d_sha:
        print("COPY_SHA_MISMATCH %s" % dst_name)
        sys.exit(1)
    sums.append((d_sha, dst_name))

with open(os.path.join(DST, "SHA256SUMS.txt"), "w", encoding="utf-8") as fh:
    for sha, name in sorted(sums, key=lambda x: x[1]):
        fh.write("%s  %s\n" % (sha, name))
print("COPIED=%d DST=%s" % (len(PLAN), DST))
