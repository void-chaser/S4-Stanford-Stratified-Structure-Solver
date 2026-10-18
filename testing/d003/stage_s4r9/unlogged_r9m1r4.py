#!/usr/bin/env python3
# unlogged_r9m1r4.py -- Correlate repository & evidence files from r9m1r3 with safe_run.log (Step S-B). New file.
import os, sys, subprocess, datetime, hashlib

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r4"))
OUT_TSV = os.path.join(EV, "UNLOGGED_WRITES_R9M1R3.tsv")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def main():
    os.makedirs(EV, exist_ok=True)
    
    # 1. Read m1r3 safe_run.log
    log_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3", "safe_run.log")
    logged_cmds = []
    if os.path.isfile(log_path):
        with open(log_path, "r", encoding="utf-8") as lf:
            for idx, line in enumerate(lf, 1):
                parts = line.split("\t")
                if len(parts) >= 4:
                    logged_cmds.append((idx, parts[0], parts[3]))
    
    # 2. Files changed in git commit range 16a7897..4e9ff8b
    diff_files = subprocess.check_output(
        ["git", "diff", "16a7897..4e9ff8b", "--name-only"], cwd=REPO, text=True
    ).splitlines()

    # Time window of r9m1r3
    t_start = 1792288450 # ~01:54Z
    t_end = 1792299000   # ~04:50Z

    rows = []

    # Process repo diff files
    for rel in sorted(diff_files):
        full_p = os.path.join(REPO, rel)
        if not os.path.exists(full_p):
            continue
        st = os.stat(full_p)
        mtime_iso = datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat()
        
        # Check if rel or basename is in any log command
        found_idx = None
        for l_idx, l_ts, l_cmd in logged_cmds:
            if rel in l_cmd or os.path.basename(rel) in l_cmd:
                found_idx = l_idx
                break
        
        log_line_str = str(found_idx) if found_idx else "无"
        status = "LOGGED" if found_idx else "UNLOGGED"
        category = "STAGE_SCRIPT" if "stage_s4r9" in rel else ("REPORT_OR_STATE" if rel.endswith(".md") else "REGISTRY_OR_OTHER")
        notes = "Recorded in safe_run.log" if found_idx else "Direct write outside safe_run.log (editor tool)"
        rows.append([rel, mtime_iso, category, status, log_line_str, notes])

    # Check evidence/p05-s4r9/m1r2 for modified files in window
    m1r2_dir = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2")
    if os.path.isdir(m1r2_dir):
        for root, dirs, files in os.walk(m1r2_dir):
            for f in files:
                fp = os.path.join(root, f)
                st = os.stat(fp)
                if 1792294400 <= st.st_mtime <= 1792295000: # 03:33Z to 03:43Z (window of H-1)
                    rel = os.path.relpath(fp, REPO)
                    mtime_iso = datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).isoformat()
                    found_idx = None
                    for l_idx, l_ts, l_cmd in logged_cmds:
                        if rel in l_cmd or "gate_r9m1r3_v2.sh" in l_cmd:
                            found_idx = l_idx
                            break
                    log_line_str = str(found_idx) if found_idx else "无"
                    rows.append([rel, mtime_iso, "EVIDENCE_M1R2_CROSS_ROUND", "CROSS_ROUND_WRITE", log_line_str, "H-1 cross-round write caused by gate_r9m1r3_v2.sh start _v2"])

    with open(OUT_TSV, "w", encoding="utf-8") as f:
        f.write("# UNLOGGED_WRITES_R9M1R3.tsv -- Comprehensive audit of files modified during r9m1r3 vs safe_run.log (Step S-B)\n")
        f.write("\t".join(["file_path", "mtime_utc", "category", "logged_status", "safe_run_log_line", "audit_notes"]) + "\n")
        for r in rows:
            f.write("\t".join(r) + "\n")

    print(f"Wrote UNLOGGED_WRITES_R9M1R3.tsv ({len(rows)} entries audited).")

if __name__ == "__main__":
    main()
