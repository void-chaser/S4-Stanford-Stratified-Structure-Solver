#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_r9m1.py -- Copy small tables from evidence to registries/s4r9/M1/ and verify sha256 (Step S-D / S-H).
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
DEST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1")
os.makedirs(DEST, exist_ok=True)

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            c = fh.read(65536)
            if not c: break
            h.update(c)
    return h.hexdigest()

ALL_REGISTRY_FILES = [
    "BUILD_OPTION_DIFF_R9M1.txt",
    "BUILD_R9M1.tsv",
    "DRIVERS_F3_SIDE_R9M1.tsv",
    "ENGINE_COLUMNS_R9M1.txt",
    "EVENTS_R9M1.tsv",
    "F3_F4_EQUIV_R9M1.tsv",
    "GATE_R9M1_start.txt",
    "GATE_R9M1_end.txt",\n    "GATE_R9M1_end_R2.txt",\n    "GATE_R9M1_end_R3.txt",
    "IMPACT_S3R5_R9M1.tsv",
    "K_INHERIT_RAW_R9M1.txt",
    "K_INHERIT_R9M1.tsv",
    "M1_SUMMARY_F4_R9M1.tsv",
    "NOINJ_R9M1.tsv",
    "noinj_r9m1.txt",
    "POSCTRL_M1_R9M1.txt",
    "PREREG_M1_CITED_F2_R9M1.tsv",
    "PREREG_M1_CITED_F2_R9M1.tsv.sha256",
    "PREREG_M1_CITED_F2_R9M1_TIMESTAMP_UTC.txt",
    "PREREG_M1_F4_R9M1.tsv",
    "PREREG_M1_F4_R9M1.tsv.sha256",
    "PREREG_M1_F4_R9M1_TIMESTAMP_UTC.txt",
    "RUNNER_DIFF_R9M1.txt",
    "SMOKE_M1_F4_R9M1.tsv",
    "SMOKE_SUMMARY_R9M1.txt",
    "STRAY_BASELINE_R9M1.tsv",
    "VERDICT_M1_F4_R9M1.tsv",
    "VERDICT_M1_F4_R9M1_AGG.tsv",
    "WARN_COUNT_R9M1.tsv",
]

copied = []
for fn in ALL_REGISTRY_FILES:
    src_p = os.path.join(EV, fn)
    dst_p = os.path.join(DEST, fn)
    if os.path.isfile(src_p):
        shutil.copy2(src_p, dst_p)
        s_src = sha256_file(src_p)
        s_dst = sha256_file(dst_p)
        assert s_src == s_dst, f"Copy mismatch for {fn}: {s_src} != {s_dst}"
        copied.append((fn, s_dst))
        print(f"Copied {fn}: sha={s_dst[:12]}... OK")

# Write SHA256SUMS.txt
sums_path = os.path.join(DEST, "SHA256SUMS.txt")
with open(sums_path, "w", encoding="utf-8") as fh:
    for fn, sh in sorted(copied):
        fh.write(f"{sh}  {fn}\n")

print(f"Wrote {sums_path} with {len(copied)} items.")

# Verify all items in SHA256SUMS.txt
with open(sums_path, "r", encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line: continue
        exp_sh, fn = line.split(None, 1)
        act_sh = sha256_file(os.path.join(DEST, fn))
        assert exp_sh == act_sh, f"Verification failed for {fn}: act={act_sh}, exp={exp_sh}"

print(f"Verified all {len(copied)} items in registries/s4r9/M1/SHA256SUMS.txt!")
