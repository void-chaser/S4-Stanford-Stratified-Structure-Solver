#!/usr/bin/env python3
# copy_registries_r8m1c3.py -- P05-S4 R8 M1c3 registry copy (brief 9.2, AGENTS.md 7.1). New file.
# Copies the small result tables of this round from $EV to checkpoints/p05/registries/s4r8/M1c/r8m1c3/,
# checks that every input exists BEFORE creating the directory, verifies each copy's sha256 against its source,
# and writes SHA256SUMS.txt.  gdb logs and dumps are not copied.  The end-gate files are copied by a separate
# script (append_end_registries_r8m1c3.py) after the end gate, and listed then.
# Usage: python3 -I -B copy_registries_r8m1c3.py
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
DST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c3")
RUN = os.path.join(EV, "m1c_F3")

# (source path, destination name)
PLAN = [
    (os.path.join(EV, "PREFLIGHT_M1C_R8_M1c3.txt"), "PREFLIGHT_M1C_R8_M1c3.txt"),
    (os.path.join(EV, "RUNNER_DIFF_R8_M1c3.txt"), "RUNNER_DIFF_R8_M1c3.txt"),
    (os.path.join(EV, "DRIVER_RUN_RECORD_R8_M1c3.tsv"), "DRIVER_RUN_RECORD_R8_M1c3.tsv"),
    (os.path.join(EV, "COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv"), "COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv"),
    (os.path.join(EV, "F2_F3_DIFF_M1C_R8_M1c3.tsv"), "F2_F3_DIFF_M1C_R8_M1c3.tsv"),
    (os.path.join(EV, "VERDICT_M1C_R8_M1c3_R3.tsv"), "VERDICT_M1C_R8_M1c3.tsv"),
    (os.path.join(EV, "VERDICT_M1C_R8_M1c3_AGG_R3.tsv"), "VERDICT_M1C_R8_M1c3_AGG.tsv"),
    (os.path.join(EV, "POSCTRL_M1C_R8_M1c3.txt"), "POSCTRL_M1C_R8_M1c3.txt"),
    (os.path.join(EV, "M1_SUMMARY_R8_M1c3_R2.tsv"), "M1_SUMMARY_R8_M1c3.tsv"),
    (os.path.join(EV, "FIX_COVERAGE_M1_R8_M1c3_R2.tsv"), "FIX_COVERAGE_M1_R8_M1c3.tsv"),
    (os.path.join(EV, "GATE_DIFF_R8_M1c3.txt"), "GATE_DIFF_R8_M1c3.txt"),
    (os.path.join(EV, "GATE_R8_M1c3_START_R2.txt"), "GATE_R8_M1c3_START_R2.txt"),
    (os.path.join(REPO, "testing", "d003", "stage_s4", "gate_allow_r8m1c3_start.txt"), "gate_allow_r8m1c3_start.txt"),
    (os.path.join(REPO, "testing", "d003", "stage_s4", "gate_allow_r8m1c3_end.txt"), "gate_allow_r8m1c3_end.txt"),
    (os.path.join(REPO, "testing", "d003", "stage_s4", "gate_r8m1c3.sh"), "gate_r8m1c3.sh"),
    (os.path.join(REPO, "testing", "d003", "stage_s4", "gate_check_r8m1c3.py"), "gate_check_r8m1c3.py"),
    (os.path.join(REPO, "testing", "d003", "stage_s4", "diff_gate_r8m1c3.sh"), "diff_gate_r8m1c3.sh"),
]
# F3 result files, with the M1C_F3_ prefix
F3_FILES = ["STATE_R6c_pass1.tsv", "STATE_R6c_pass2.tsv", "STATE_SEAM_R6c_pass1.tsv", "STATE_SEAM_R6c_pass2.tsv",
            "RESULTS_R6c_STATE.tsv", "RESULTS_R6c_SEAM.tsv"]
for f in F3_FILES:
    PLAN.append((os.path.join(RUN, f), "M1C_F3_" + f))
# the two SUMMARY files, if the runner wrote them; their presence is checked below
SUMMARY_CANDIDATES = [
    (os.path.join(RUN, "STATE_SUMMARY_R6c.txt"), "M1C_F3_STATE_SUMMARY_R6c.txt"),
    (os.path.join(RUN, "STATE_SUMMARY_R6c_SEAM.txt"), "M1C_F3_STATE_SUMMARY_R6c_SEAM.txt"),
]
for src, dst in SUMMARY_CANDIDATES:
    if os.path.isfile(src):
        PLAN.append((src, dst))

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
    s_sha = hashlib.sha256(open(src, "rb").read()).hexdigest()
    d_sha = hashlib.sha256(open(dst, "rb").read()).hexdigest()
    if s_sha != d_sha:
        print("COPY_SHA_MISMATCH %s" % dst_name)
        sys.exit(1)
    sums.append((d_sha, dst_name))

with open(os.path.join(DST, "SHA256SUMS.txt"), "w", encoding="utf-8") as fh:
    for sha, name in sorted(sums, key=lambda x: x[1]):
        fh.write("%s  %s\n" % (sha, name))
print("COPIED=%d DST=%s" % (len(PLAN), DST))
