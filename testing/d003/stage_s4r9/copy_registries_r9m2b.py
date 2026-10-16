#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_r9m2b.py -- Copy small tables to registries/s4r9/M2b/ and generate SHA256SUMS.txt (Step S-H).
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b"))
REG_DIR = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M2b")
os.makedirs(REG_DIR, exist_ok=True)

TABLES_TO_COPY = [
    "EVENTS_R9_ALL_R9M2b.tsv",
    "GATE_R9M2b_start.txt",
    "GATE_R9M2b_end.txt",
    "GATE_R9M2b_end_R2.txt",
    "HITSEQ_F3_F4_R9M2b.tsv",
    "JUDGE_TOOL_DIFF_R9M2b.txt",
    "K_INHERIT_R9M2b.tsv",
    "K_INHERIT_RAW_R9M2b.txt",
    "POSCTRL_K_R9M2b.txt",
    "POSCTRL_SOLN_R9M2b.txt",
    "RUNNER_DIFF_R9M2b.txt",
    "SOLN_SUPP_JUDGE_R9M2b.tsv",
    "STRAY_BASELINE_R9M2b.tsv",
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
    print(f"Copying {len(TABLES_TO_COPY)} small tables from {EV} to {REG_DIR}...")
    copied = 0
    reg_sums = []

    for fname in sorted(TABLES_TO_COPY):
        src = os.path.join(EV, fname)
        dst = os.path.join(REG_DIR, fname)
        if not os.path.isfile(src):
            sys.exit(f"Error: source table missing: {src}")

        shutil.copy2(src, dst)
        sha_src = sha256_file(src)
        sha_dst = sha256_file(dst)
        if sha_src != sha_dst:
            sys.exit(f"Error: sha mismatch after copy for {fname}")

        reg_sums.append(f"{sha_dst}  {fname}")
        copied += 1
        print(f"  [OK] {fname} ({sha_dst[:12]}...)")

    # Write registries SHA256SUMS.txt
    reg_sums_path = os.path.join(REG_DIR, "SHA256SUMS.txt")
    with open(reg_sums_path, "w", encoding="utf-8") as fh:
        for l in sorted(reg_sums):
            fh.write(l + "\n")
    print(f"Wrote registries SHA256SUMS.txt ({len(reg_sums)} files).")

    # Verify each item in registries
    with open(reg_sums_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            exp_sha, fn = line.split(None, 1)
            act_sha = sha256_file(os.path.join(REG_DIR, fn))
            assert exp_sha == act_sha, f"Registries verification mismatch: {fn}"
    print("Registries SHA256SUMS.txt self-check: ALL OK.")

    # Write evidence SHA256SUMS.txt (covers all non-binary text/tsv/log files)
    ev_files = []
    for f in sorted(os.listdir(EV)):
        fp = os.path.join(EV, f)
        if os.path.isfile(fp) and f != "SHA256SUMS.txt":
            ev_files.append((sha256_file(fp), f))

    ev_sums_path = os.path.join(EV, "SHA256SUMS.txt")
    with open(ev_sums_path, "w", encoding="utf-8") as fh:
        for sh, fn in sorted(ev_files):
            fh.write(f"{sh}  {fn}\n")
    print(f"Wrote evidence SHA256SUMS.txt ({len(ev_files)} files).")

    # Verify each item in evidence
    with open(ev_sums_path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            exp_sha, fn = line.split(None, 1)
            act_sha = sha256_file(os.path.join(EV, fn))
            assert exp_sha == act_sha, f"Evidence verification mismatch: {fn}"
    print("Evidence SHA256SUMS.txt self-check: ALL OK.")

if __name__ == "__main__":
    main()
