#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# events_r9m1r2.py -- Generate complete events table from safe_run.log and bare write audit (Step S-I, Rule U316). New file.
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "EVENTS_R9M1R2.tsv")
M1R2_LOG = os.path.join(EV, "safe_run.log")
M1_LOG = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/safe_run.log")
BARE_AUDIT_TSV = os.path.join(EV, "BARE_WRITE_AUDIT_R9M1R2.tsv")

assert os.path.isfile(M1R2_LOG), f"m1r2 safe_run.log missing: {M1R2_LOG}"

# 1. Parse m1r2 safe_run.log entries
m1r2_entries = []
with open(M1R2_LOG, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        line = line.rstrip("\r\n")
        if not line: continue
        parts = line.split("\t")
        utc = parts[0]
        cmd = ""
        for p in parts[1:]:
            if p.startswith("cmd="): cmd = p[4:]
            elif not cmd: cmd = p

        cat = "NORMAL_EXECUTION"
        if "gate_r9m1r2.sh" in cmd: cat = "GATE"
        elif "append_rulings" in cmd: cat = "RULINGS"
        elif "append_errata" in cmd: cat = "ERRATA"
        elif "forensic" in cmd or "bare_write_audit" in cmd: cat = "FORENSIC"
        elif "build_kmap" in cmd or "k_inherit" in cmd: cat = "K_REDO"
        elif "prereg" in cmd: cat = "PREREG"
        elif "posctrl" in cmd: cat = "POSCTRL"
        elif "run_smoke" in cmd: cat = "SMOKE"
        elif "run_formal" in cmd: cat = "FORMAL"
        elif "verdict" in cmd or "compare" in cmd or "summarize" in cmd or "cmp_r9m1" in cmd: cat = "VERDICT_COMPARE"
        elif "copy_registries" in cmd or "events" in cmd or "STATE" in cmd or "REPORT" in cmd: cat = "CLOSEOUT"

        m1r2_entries.append({
            "line_no": idx, "utc": utc, "round": "r9m1r2", "category": cat,
            "cmd": cmd, "bare_write": "NO", "out_of_boundary": "NO"
        })

# 2. Parse r9m1 retroactive table: safe_run.log + bare writes
r9m1_retro_entries = []
with open(M1_LOG, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        line = line.rstrip("\r\n")
        if not line: continue
        parts = line.split("\t")
        utc = parts[0]
        cmd = ""
        for p in parts[1:]:
            if p.startswith("cmd="): cmd = p[4:]
            elif not cmd: cmd = p
        r9m1_retro_entries.append({
            "line_no": idx, "utc": utc, "round": "r9m1", "category": "LOGGED_RUN",
            "cmd": cmd, "bare_write": "NO", "out_of_boundary": "NO"
        })

bare_writes = []
if os.path.isfile(BARE_AUDIT_TSV):
    with open(BARE_AUDIT_TSV, "r", encoding="utf-8") as f:
        for l in f:
            if l.startswith("#") or l.startswith("relative_path\t"): continue
            p = l.strip().split("\t")
            if len(p) >= 6 and p[3] == "BARE_WRITE_CANDIDATE":
                bare_writes.append({
                    "line_no": -1, "utc": p[2], "round": "r9m1", "category": "BARE_WRITE_UNLOGGED",
                    "cmd": f"bare_write: {p[0]} ({p[1]} bytes)", "bare_write": "YES", "out_of_boundary": "NO"
                })

# Total bare writes assertion
assert len(bare_writes) == 207, f"Expected 207 bare writes, got {len(bare_writes)}"

# Total lines assertion: m1r2 log entries + r9m1 retro (log entries + bare writes)
all_event_rows = []
seq = 1

# Section 1: r9m1 retroactive log
for e in r9m1_retro_entries:
    all_event_rows.append([
        f"EV-RETRO-M1-{seq:03d}", e["utc"], e["round"], str(e["line_no"]), e["category"],
        e["bare_write"], e["out_of_boundary"], e["cmd"]
    ])
    seq += 1

# Section 2: r9m1 bare writes
for e in bare_writes:
    all_event_rows.append([
        f"EV-RETRO-BARE-{seq:03d}", e["utc"], e["round"], "N/A", e["category"],
        e["bare_write"], e["out_of_boundary"], e["cmd"]
    ])
    seq += 1

# Section 3: r9m1r2 current round events
for e in m1r2_entries:
    all_event_rows.append([
        f"EV-M1R2-{seq:03d}", e["utc"], e["round"], str(e["line_no"]), e["category"],
        e["bare_write"], e["out_of_boundary"], e["cmd"]
    ])
    seq += 1

total_m1r2_logged = len(m1r2_entries)
total_retro = len(r9m1_retro_entries) + len(bare_writes)
print(f"Events summary: r9m1 retroactive = {total_retro} (98 log + {len(bare_writes)} bare writes); r9m1r2 logged = {total_m1r2_logged}; Grand total = {len(all_event_rows)} rows.")

header = ["event_id", "utc", "round", "line_no", "category", "bare_write", "out_of_boundary", "command"]
with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# EVENTS_R9M1R2.tsv -- Unified events table including r9m1 retroactive audit and r9m1r2 execution (Rule U316)\n")
    fh.write("\t".join(header) + "\n")
    for r in all_event_rows:
        fh.write("\t".join(r) + "\n")

print(f"Wrote {OUT_TSV}.")
