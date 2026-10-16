#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_s3r5.py -- Copy small tables to registries/s3r5 and write SHA256SUMS (S-K, U288).
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s3r5")
EV = os.path.join(REPO, EV_REL)
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r5")

REG_FILES = [
    ("BUILD_S3R5.tsv", os.path.join(EV, "BUILD_S3R5.tsv")),
    ("WARN_DIFF_F3_F4_S3R5.txt", os.path.join(EV, "WARN_DIFF_F3_F4_S3R5.txt")),
    ("DIFF_F3_F4_S3R5.txt", os.path.join(EV, "DIFF_F3_F4_S3R5.txt")),
    ("LINEMAP_F3_F4_S3R5.tsv", os.path.join(EV, "LINEMAP_F3_F4_S3R5.tsv")),
    ("K_MAP_F4_S3R5.tsv", os.path.join(EV, "K_MAP_F4_S3R5.tsv")),
    ("K_MAP_RAW_S3R5.txt", os.path.join(EV, "K_MAP_RAW_S3R5.txt")),
    ("SELFCHECK_D_S3R5.tsv", os.path.join(EV, "SELFCHECK_D_S3R5.tsv")),
    ("R9_INPUTS_S3R5.tsv", os.path.join(EV, "R9_INPUTS_S3R5.tsv")),
    ("REGRESSION_PLAN_F4_S3R5.tsv", os.path.join(EV, "REGRESSION_PLAN_F4_S3R5.tsv")),
    ("STRAY_BASELINE_S3R5.tsv", os.path.join(EV, "STRAY_BASELINE_S3R5.tsv")),
    ("GATE_S3R5_start.txt", os.path.join(EV, "GATE_S3R5_start.txt")),
    ("GATE_S3R5_end.txt", os.path.join(EV, "GATE_S3R5_end.txt")),
    ("noinj_control_s3r5.txt", os.path.join(EV, "probe", "noinj_control_s3r5.txt")),
    ("map_k_s3r5.txt", os.path.join(EV, "probe", "map_k_s3r5.txt")),
]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    os.makedirs(REG, exist_ok=True)
    print('Copying %d small tables to %s...' % (len(REG_FILES), REG))
    reg_sums = []
    for name, src in REG_FILES:
        if not os.path.isfile(src):
            raise SystemExit('Source file missing: %s' % src)
        dst = os.path.join(REG, name)
        shutil.copy2(src, dst)
        s_sha = sha256_file(src)
        d_sha = sha256_file(dst)
        if s_sha != d_sha:
            raise SystemExit('SHA mismatch copying %s: %s != %s' % (name, s_sha, d_sha))
        reg_sums.append('%s  %s' % (d_sha, name))
        print('  Copied %s: sha256=%s' % (name, d_sha))
    
    # Write registries SHA256SUMS.txt
    reg_sums_path = os.path.join(REG, "SHA256SUMS.txt")
    with open(reg_sums_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sorted(reg_sums)) + "\n")
    print("Wrote %s (%d files)" % (reg_sums_path, len(reg_sums)))
    
    # Write evidence SHA256SUMS.txt
    ev_sums = []
    ev_text_files = [
        "BUILD_S3R5.tsv",
        "WARN_DIFF_F3_F4_S3R5.txt",
        "DIFF_F3_F4_S3R5.txt",
        "LINEMAP_F3_F4_S3R5.tsv",
        "K_MAP_F4_S3R5.tsv",
        "K_MAP_RAW_S3R5.txt",
        "SELFCHECK_D_S3R5.tsv",
        "R9_INPUTS_S3R5.tsv",
        "REGRESSION_PLAN_F4_S3R5.tsv",
        "STRAY_BASELINE_S3R5.tsv",
        "GATE_S3R5_start.txt",
        "GATE_S3R5_end.txt",
        os.path.join("probe", "noinj_control_s3r5.txt"),
        os.path.join("probe", "map_k_s3r5.txt"),
    ]
    for rel in ev_text_files:
        p = os.path.join(EV, rel)
        if os.path.isfile(p):
            sha = sha256_file(p)
            ev_sums.append('%s  %s' % (sha, rel))
        else:
            raise SystemExit('Evidence file missing: %s' % p)
            
    # U288 rule for safe_run.log: record lines count N and sha256 of first N lines
    safe_log = os.path.join(EV, "safe_run.log")
    if os.path.isfile(safe_log):
        with open(safe_log, "rb") as fh:
            lines = fh.readlines()
        n_lines = len(lines)
        log_sha = hashlib.sha256(b''.join(lines)).hexdigest()
        log_entry = '# safe_run.log snapshot (U288): lines=%d sha256=%s' % (n_lines, log_sha)
    else:
        log_entry = '# safe_run.log: missing'
        
    ev_sums_path = os.path.join(EV, "SHA256SUMS.txt")
    with open(ev_sums_path, "w", encoding="utf-8") as fh:
        fh.write("# Evidence SHA256SUMS for P05-S3R5\n")
        fh.write(log_entry + "\n")
        fh.write("\n".join(sorted(ev_sums)) + "\n")
    print("Wrote %s (%d files + log snapshot)" % (ev_sums_path, len(ev_sums)))
    return 0

if __name__ == "__main__":
    sys.exit(main())
