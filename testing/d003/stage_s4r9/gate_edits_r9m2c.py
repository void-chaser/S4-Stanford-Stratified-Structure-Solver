#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate_edits_r9m2c.py -- Audit undisclosed edits to committed gate files and RULINGS (Step S-C-3).
import datetime, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2c"))
os.makedirs(EV, exist_ok=True)
OUT_TXT = os.path.join(EV, "GATE_EDITS_R9M2b_UNDISCLOSED.txt")

# 1. git diff between fbf3054 and 42d7d97 for gate files
diff_text = subprocess.check_output(
    ["git", "diff", "fbf3054", "42d7d97", "--", "testing/d003/stage_s4r9/gate_*"],
    cwd=REPO, text=True
)

# 2. Files to check mtime
files_to_check = [
    "checkpoints/p05/registries/RULINGS.tsv",
    "testing/d003/stage_s4r9/gate_check_r9m2b.py",
    "testing/d003/stage_s4r9/gate_r9m2b.sh",
    "testing/d003/stage_s4r9/gate_allow_r9m2b_end.txt",
]

# 3. Read m2b safe_run.log
log_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b", "safe_run.log")
log_entries = []
if os.path.isfile(log_path):
    with open(log_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                log_entries.append(line)

log_timestamps = set()
for l in log_entries:
    parts = l.split("\t")
    if parts:
        log_timestamps.add(parts[0])

mtime_results = []
for rel in files_to_check:
    full = os.path.join(REPO, rel)
    st = os.stat(full)
    mtime_utc = datetime.datetime.fromtimestamp(st.st_mtime, tz=datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    has_safe_run = mtime_utc in log_timestamps
    status_label = "对应 safe_run 条目" if has_safe_run else "无对应 safe_run 条目"
    mtime_results.append((rel, mtime_utc, status_label))

with open(OUT_TXT, "w", encoding="utf-8") as out:
    out.write("# GATE_EDITS_R9M2b_UNDISCLOSED.txt -- Undisclosed edits audit (Step S-C-3)\n")
    out.write("# Audit of fbf3054 -> 42d7d97 modifications to committed gate files and RULINGS.tsv\n\n")
    out.write("=== File Current mtime (UTC) vs m2b safe_run.log ===\n")
    for rel, mt, st in mtime_results:
        out.write(f"File: {rel}\n")
        out.write(f"  mtime (UTC): {mt}\n")
        out.write(f"  safe_run status: {st}\n\n")
    
    out.write("=== Unified diff: git diff fbf3054 42d7d97 -- testing/d003/stage_s4r9/gate_* ===\n")
    out.write(diff_text)

print(f"Gate edits audit complete. Output written to {OUT_TXT}")
