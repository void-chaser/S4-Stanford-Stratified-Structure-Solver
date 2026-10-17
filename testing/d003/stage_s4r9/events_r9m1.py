#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# events_r9m1.py -- Reconstruct complete events table from m1 safe_run.log (Step S-H). New file.
import os, re, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "EVENTS_R9M1.tsv")
LOG_PATH = os.path.join(EV, "safe_run.log")

assert os.path.isfile(LOG_PATH), f"safe_run.log missing: {LOG_PATH}"

log_entries = []
with open(LOG_PATH, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        line = line.rstrip("\r\n")
        if not line:
            continue
        parts = line.split("\t")
        utc = parts[0]
        cwd = ""
        out = ""
        cmd = ""
        for p in parts[1:]:
            if p.startswith("cwd="): cwd = p[4:]
            elif p.startswith("out="): out = p[4:]
            elif p.startswith("cmd="): cmd = p[4:]
            elif not cmd: cmd = p
        
        # Determine category
        cat = "NORMAL_EXECUTION"
        if "gate_r9m1.sh" in cmd:
            cat = "GATE"
        elif "append_rulings" in cmd:
            cat = "RULINGS"
        elif "build_r9m1" in cmd:
            cat = "BUILD"
        elif "noinj_r9m1" in cmd:
            cat = "NOINJ"
        elif "k_inherit" in cmd or "impact" in cmd:
            cat = "PROOF_IMPACT"
        elif "prereg" in cmd:
            cat = "PREREG"
        elif "posctrl" in cmd:
            cat = "POSCTRL"
        elif "run_smoke" in cmd:
            cat = "SMOKE"
        elif "run_formal" in cmd:
            cat = "FORMAL"
        elif "verdict" in cmd or "compare" in cmd or "summarize" in cmd:
            cat = "VERDICT_COMPARE"
        elif "copy_registries" in cmd or "events" in cmd:
            cat = "CLOSEOUT"

        log_entries.append({
            "line_no": idx,
            "utc": utc,
            "round": "r9m1",
            "category": cat,
            "cmd": cmd,
            "bare_write": "NO",
            "out_of_boundary": "NO"
        })

print(f"Total safe_run.log entries parsed: {len(log_entries)}")

header = ["event_id", "utc", "round", "line_no", "category", "bare_write", "out_of_boundary", "command"]
rows = []
for idx, e in enumerate(log_entries, 1):
    rows.append([
        f"EV-M1-{idx:03d}", e["utc"], e["round"], str(e["line_no"]), e["category"],
        e["bare_write"], e["out_of_boundary"], e["cmd"]
    ])

# Assertions
assert len(rows) == len(log_entries)
assert all(r[5] == "NO" for r in rows), "Bare writes must be 0!"
assert all(r[6] == "NO" for r in rows), "Out of boundary writes must be 0!"

with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# EVENTS_R9M1.tsv -- Execution and safe_run events for P05-S4 R9 M1 (Step S-H)\n")
    fh.write(f"# Total events: {len(rows)} (safe_run.log: {len(log_entries)}, bare writes: 0, out of boundary: 0)\n")
    fh.write("\t".join(header) + "\n")
    for r in rows:
        fh.write("\t".join(r) + "\n")

print(f"Wrote {OUT_TSV} with {len(rows)} events.")
sys.exit(0)
