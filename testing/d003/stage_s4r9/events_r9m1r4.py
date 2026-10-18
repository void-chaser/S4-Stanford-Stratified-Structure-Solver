#!/usr/bin/env python3
# events_r9m1r4.py -- Extract all safe_run events for P05-S4 R9 M1R4 (Step S-G). New file.
# Baseline HEAD: 4e9ff8be523bbf52a6b11757a6e04405a4a114e9
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r4"))
LOG_PATH = os.path.join(EV, "safe_run.log")
OUT_TSV = os.path.join(EV, "EVENTS_R9M1R4.tsv")

def main():
    if not os.path.isfile(LOG_PATH):
        print(f"safe_run.log missing at {LOG_PATH}", file=sys.stderr)
        sys.exit(1)

    with open(LOG_PATH, "r", encoding="utf-8") as f:
        log_lines = f.read().splitlines()

    rows = []
    for idx, line in enumerate(log_lines, 1):
        line = line.strip()
        if not line: continue
        parts = line.split("\t")
        utc_ts = parts[0] if len(parts) > 0 else ""
        cmd = parts[3] if len(parts) > 3 else ""

        if "gate" in cmd: cat = "GATE"
        elif "audit" in cmd: cat = "AUDIT"
        elif "append_rulings" in cmd: cat = "RULINGS"
        elif "append_errata" in cmd: cat = "ERRATA"
        elif "recert" in cmd and "posctrl" in cmd: cat = "POSCTRL"
        elif "recert" in cmd: cat = "RECERT"
        elif "kmatch" in cmd: cat = "K_MATCH"
        elif "unlogged" in cmd: cat = "UNLOGGED"
        elif "summarize" in cmd: cat = "SUMMARIZE"
        elif "report_check" in cmd: cat = "REPORT_CHECK"
        elif "copy_registries" in cmd: cat = "COPY_REG"
        elif "events" in cmd: cat = "EVENTS"
        elif "sha_sums" in cmd: cat = "SHA_SUMS"
        elif "finalize" in cmd: cat = "FINALIZE"
        elif "open(" in cmd: cat = "WRITE_FILE"
        else: cat = "OTHER"

        cmd_summary = cmd[:140] + ("..." if len(cmd) > 140 else "")
        rows.append([str(idx), utc_ts, cat, cmd_summary])

    with open(OUT_TSV, "w", encoding="utf-8") as f:
        f.write("# EVENTS_R9M1R4.tsv -- Complete safe_run event log table for P05-S4 R9 M1R4 (Rule §1-6)\n")
        f.write("\t".join(["log_line", "utc_timestamp", "category", "command_summary"]) + "\n")
        for r in rows:
            f.write("\t".join(r) + "\n")

    print(f"Wrote EVENTS_R9M1R4.tsv ({len(rows)} entries covering safe_run.log).")

if __name__ == "__main__":
    main()
