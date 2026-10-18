#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_r9m1r2.py -- Copy small tables to checkpoints/p05/registries/s4r9/M1R2/ (Rules §1-12, U316). New file.
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
REG_M1R2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R2")
os.makedirs(REG_M1R2, exist_ok=True)

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
        "BUILD_KMAP_R9M1R2.tsv",
        "BUILD_OPTION_DIFF_KMAP_R9M1R2.txt",
        "K_INHERIT_R9M1R2.tsv",
        "K_INHERIT_RAW_R9M1R2.txt",
        "PREREG_M1_F4_R9M1R2.tsv",
        "PREREG_M1_F4_R9M1R2.tsv.sha256",
        "PREREG_M1_F4_R9M1R2_TIMESTAMP_UTC.txt",
        "PREREG_M1_CITED_F2_R9M1R2.tsv",
        "PREREG_M1_CITED_F2_R9M1R2.tsv.sha256",
        "PREREG_M1_CITED_F2_R9M1R2_TIMESTAMP_UTC.txt",
        "PREREG_VS_R9M1_DIFF_R9M1R2.tsv",
        "ENGINE_COLUMNS_R9M1R2.txt",
        "FROZEN_SCRIPTS_R9M1R2.tsv",
        "GATE_R9M1R2_start.txt",
        "RUNNER_DIFF_R9M1R2.txt",
        "PREREG_DIFF_R9M1R2.tsv",
        "REJUDGE_OLD_PREREG_R9M1R2.tsv",
        "BARE_WRITE_AUDIT_R9M1R2.tsv",
    ]
elif mode == "final":
    # Full list at closeout
    FILES_TO_COPY = [
        "BUILD_KMAP_R9M1R2.tsv",
        "BUILD_OPTION_DIFF_KMAP_R9M1R2.txt",
        "K_INHERIT_R9M1R2.tsv",
        "K_INHERIT_RAW_R9M1R2.txt",
        "PREREG_M1_F4_R9M1R2.tsv",
        "PREREG_M1_F4_R9M1R2.tsv.sha256",
        "PREREG_M1_F4_R9M1R2_TIMESTAMP_UTC.txt",
        "PREREG_M1_CITED_F2_R9M1R2.tsv",
        "PREREG_M1_CITED_F2_R9M1R2.tsv.sha256",
        "PREREG_M1_CITED_F2_R9M1R2_TIMESTAMP_UTC.txt",
        "PREREG_VS_R9M1_DIFF_R9M1R2.tsv",
        "ENGINE_COLUMNS_R9M1R2.txt",
        "FROZEN_SCRIPTS_R9M1R2.tsv",
        "GATE_R9M1R2_start.txt",
        "RUNNER_DIFF_R9M1R2.txt",
        "PREREG_DIFF_R9M1R2.tsv",
        "REJUDGE_OLD_PREREG_R9M1R2.tsv",
        "BARE_WRITE_AUDIT_R9M1R2.tsv",
        "POSCTRL_M1_R9M1R2.txt",
        "SMOKE_M1_F4_R9M1R2.tsv",
        "SMOKE_SUMMARY_R9M1R2.txt",
        "VERDICT_M1_F4_R9M1R2.tsv",
        "VERDICT_M1_F4_R9M1R2_AGG.tsv",
        "F3_F4_EQUIV_R9M1R2.tsv",
        "R9M1_VS_R9M1R2_R9M1R2.tsv",
        "M1_SUMMARY_F4_R9M1R2.tsv",
        "EVENTS_R9M1R2.tsv",
        "GATE_R9M1R2_end.txt",
    ]
else:
    raise ValueError(f"Unknown mode: {mode}")

print(f"Copying {len(FILES_TO_COPY)} registry tables ({mode})...")
sums_lines = []
for fname in sorted(FILES_TO_COPY):
    src = os.path.join(EV, fname)
    dst = os.path.join(REG_M1R2, fname)
    assert os.path.isfile(src), f"Source file missing: {src}"
    shutil.copy2(src, dst)
    sha_src = sha256_file(src)
    sha_dst = sha256_file(dst)
    # Rule §1-12 assertion
    assert sha_src == sha_dst, f"Rule §1-12 assertion failed: {fname} sha {sha_dst} != {sha_src}"
    sums_lines.append(f"{sha_dst}  {fname}\n")
    print(f"  {fname}: {sha_dst[:12]}... OK")

# Write SHA256SUMS.txt in registries dir
with open(os.path.join(REG_M1R2, "SHA256SUMS.txt"), "w", encoding="utf-8") as fh:
    for l in sums_lines:
        fh.write(l)

print(f"Registry copy completed. Wrote {os.path.join(REG_M1R2, 'SHA256SUMS.txt')}.")
