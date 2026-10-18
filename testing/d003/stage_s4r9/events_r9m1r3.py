#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# events_r9m1r3.py -- Extract all events from safe_run.log up to the last line (Step S-I). New file.
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))
LOG_PATH = os.path.join(EV, "safe_run.log")
OUT_TSV = os.path.join(EV, "EVENTS_R9M1R3.tsv")

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
        cwd = parts[1] if len(parts) > 1 else ""
        out = parts[2] if len(parts) > 2 else ""
        cmd = parts[3] if len(parts) > 3 else ""

        # Categorize
        if "gate" in cmd: cat = "GATE"
        elif "audit" in cmd: cat = "AUDIT"
        elif "append_rulings" in cmd: cat = "RULINGS"
        elif "append_errata" in cmd: cat = "ERRATA"
        elif "kcount" in cmd or "test_kcount" in cmd: cat = "K_COUNT"
        elif "prereg" in cmd: cat = "PREREG"
        elif "posctrl" in cmd: cat = "POSCTRL"
        elif "run_smoke" in cmd: cat = "SMOKE"
        elif "run_formal" in cmd: cat = "FORMAL"
        elif "verdict" in cmd: cat = "VERDICT"
        elif "compare" in cmd: cat = "COMPARE"
        elif "cmp_vs" in cmd: cat = "CMP_PREV"
        elif "summarize" in cmd: cat = "SUMMARIZE"
        elif "copy_registries" in cmd: cat = "COPY_REG"
        elif "events" in cmd: cat = "EVENTS"
        elif "sha_sums" in cmd: cat = "SHA_SUMS"
        elif "report_check" in cmd: cat = "REPORT_CHECK"
        elif "finalize" in cmd: cat = "FINALIZE"
        elif "open(" in cmd: cat = "WRITE_FILE"
        else: cat = "OTHER"

        cmd_summary = cmd[:140] + ("..." if len(cmd) > 140 else "")
        rows.append([str(idx), utc_ts, cat, cmd_summary])

    with open(OUT_TSV, "w", encoding="utf-8") as f:
        f.write("# EVENTS_R9M1R3.tsv -- Complete safe_run event log table for P05-S4 R9 M1R3 (Rule §1-6)" + chr(10))
        f.write(chr(9).join(["log_line", "utc_timestamp", "category", "command_summary"]) + chr(10))
        for r in rows:
            f.write(chr(9).join(r) + chr(10))

    print(f"Wrote EVENTS_R9M1R3.tsv ({len(rows)} entries covering safe_run.log).")

if __name__ == "__main__":
    main()
