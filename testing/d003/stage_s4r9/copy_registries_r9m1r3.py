#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_r9m1r3.py -- Copy small tables to checkpoints/p05/registries/s4r9/M1R3/ (Step S-I). New file.
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))
REG_M1R3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R3")
os.makedirs(REG_M1R3, exist_ok=True)

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            c = fh.read(65536)
            if not c: break
            h.update(c)
    return h.hexdigest()

mode = sys.argv[1] if len(sys.argv) > 1 else "commit_i"

if mode == "commit_i":
    FILES_TO_COPY = [
        "AUDIT_R9M1R2_R9M1R3.tsv",
        "BARE_WRITE_AUDIT_R9M1R3.tsv",
        "ENGINE_COLUMNS_R9M1R3.txt",
        "FROZEN_SCRIPTS_R9M1R3.tsv",
        "GATE_R9M1R3_start_v4.txt",
        "K_COUNT_R9M1R3.tsv",
        "K_COVERAGE_R9M1R3.tsv",
        "PREREG_M1_CITED_F2_R9M1R3.tsv",
        "PREREG_M1_CITED_F2_R9M1R3.tsv.sha256",
        "PREREG_M1_CITED_F2_R9M1R3_TIMESTAMP_UTC.txt",
        "PREREG_M1_F4_R9M1R3.tsv",
        "PREREG_M1_F4_R9M1R3.tsv.sha256",
        "PREREG_M1_F4_R9M1R3_TIMESTAMP_UTC.txt",
        "PREREG_VS_R9M1R2_DIFF_R9M1R3.tsv",
        "RUNNER_DIFF_R9M1R3.txt",
        "SCRIPT_VERSIONS_R9M1R3.tsv",
    ]
elif mode == "final":
    FILES_TO_COPY = [
        "AUDIT_R9M1R2_R9M1R3.tsv",
        "BARE_WRITE_AUDIT_R9M1R3.tsv",
        "ENGINE_COLUMNS_R9M1R3.txt",
        "EVENTS_R9M1R3.tsv",
        "F3_F4_EQUIV_R9M1R3.tsv",
        "FROZEN_SCRIPTS_R9M1R3.tsv",
        "GATE_R9M1R3_start_v4.txt",
        "K_COUNT_R9M1R3.tsv",
        "K_COVERAGE_R9M1R3.tsv",
        "M1_SUMMARY_F4_R9M1R3.tsv",
        "POSCTRL_M1_R9M1R3.txt",
        "PREREG_M1_CITED_F2_R9M1R3.tsv",
        "PREREG_M1_CITED_F2_R9M1R3.tsv.sha256",
        "PREREG_M1_CITED_F2_R9M1R3_TIMESTAMP_UTC.txt",
        "PREREG_M1_F4_R9M1R3.tsv",
        "PREREG_M1_F4_R9M1R3.tsv.sha256",
        "PREREG_M1_F4_R9M1R3_TIMESTAMP_UTC.txt",
        "PREREG_VS_R9M1R2_DIFF_R9M1R3.tsv",
        "R9M1R2_VS_R9M1R3_R9M1R3.tsv",
        "RUNNER_DIFF_R9M1R3.txt",
        "SCRIPT_VERSIONS_R9M1R3.tsv",
        "SMOKE_M1_F4_R9M1R3.tsv",
        "SMOKE_SUMMARY_R9M1R3.txt",
        "VERDICT_M1_F4_R9M1R3.tsv",
        "VERDICT_M1_F4_R9M1R3_AGG.tsv",
    ]
else:
    raise ValueError(f"Unknown mode: {mode}")

print(f"Copying {len(FILES_TO_COPY)} registry tables ({mode})...")
sums_lines = []
for fname in sorted(FILES_TO_COPY):
    src = os.path.join(EV, fname)
    dst = os.path.join(REG_M1R3, fname)
    assert os.path.isfile(src), f"Source file missing: {src}"
    shutil.copy2(src, dst)
    sha_src = sha256_file(src)
    sha_dst = sha256_file(dst)
    assert sha_src == sha_dst, f"Rule §1-12 assertion failed: {fname} sha {sha_dst} != {sha_src}"
    sums_lines.append(f"{sha_dst}  {fname}\n")
    print(f"  {fname}: {sha_dst[:12]}... OK")

with open(os.path.join(REG_M1R3, "SHA256SUMS.txt"), "w", encoding="utf-8") as fh:
    for l in sums_lines:
        fh.write(l)

print(f"Registry copy completed. Wrote {os.path.join(REG_M1R3, 'SHA256SUMS.txt')} with {len(sums_lines)} entries.")
