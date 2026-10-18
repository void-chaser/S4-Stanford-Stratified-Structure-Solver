#!/usr/bin/env python3
# events_r9m3c.py -- frozen event table: one row per non-blank physical line of safe_run.log. New file (r9m3c).
# usage: events_r9m3c.py OUT.tsv
import os, sys
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
TAB = chr(9)
NL = chr(10)


def category(cmd):
    c = cmd.strip()
    for key, name in (
        ("base64", "WRITE_FILE"), ("safe_run.sh", "SAFE_RUN_FILE"), ("git archive", "TREE_EXPORT"),
        ("tar -x", "TREE_EXPORT"), ("make ", "BUILD_TEST"), ("g++", "BUILD"), ("gcc", "BUILD"),
        ("nm ", "INSPECT"), ("grep", "INSPECT"), ("git ", "GIT"),
        ("gate_r9m3c", "GATE"), ("gate_check_r9m3c", "GATE_CHECK"),
        ("progress_r9m3c", "PROGRESS"), ("events_r9m3c", "EVENTS"), ("sha_sums_r9m3c", "SHA_SUMS"),
        ("copy_registries_r9m3c", "COPY_REG"), ("report_check_r9m3c", "REPORT_CHECK"),
        ("posctrl_report_check_r9m3c", "POSCTRL_REPORT_CHECK"), ("closeout_report_state_r9m3c", "CLOSEOUT"),
        ("rejudge_e2e_r9m3c", "REJUDGE_E2E"), ("posctrl_rejudge_r9m3c", "POSCTRL_REJUDGE"),
        ("reverify_sums_r9m3c", "REVERIFY"), ("readiness_r9m3c", "READINESS"),
        ("red_ledger_final_r9m3c", "RED_LEDGER"), ("audit_r9m3b_r9m3c", "AUDIT"),
        ("append_rulings_r9m3c", "APPEND_RULINGS"), ("append_errata_r9m3c", "APPEND_ERRATA"),
        ("write_frozen_r9m3c", "FROZEN"), ("stage_s4r9", "SCRIPT")):
        if key in c:
            return name
    return "OTHER"


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV, "EVENTS_R9M3C.tsv")
    log = os.path.join(EV, "safe_run.log")
    lines = open(log, encoding="utf-8", errors="replace").read().splitlines()
    rows = []
    parent = ""
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if len(line) > 20 and line[4] == "-" and line[0:4].isdigit():
            parent = line.split(TAB)[0]
            cmd = ""
            for p in line.split(TAB)[1:]:
                if p.startswith("cmd="):
                    cmd = p[4:]
                    break
            rows.append((i, parent, category(cmd), "cmd=" + cmd[:160]))
        else:
            rows.append((i, parent, "CONTINUATION", line[:160]))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# EVENTS_R9M3C.tsv -- complete safe_run event table under physical line numbering" + NL)
        fh.write(TAB.join(["log_line", "utc_timestamp", "category", "command_summary"]) + NL)
        for r in rows:
            fh.write(TAB.join(str(x) for x in r) + NL)
    print("rows=%d log_lines=%d" % (len(rows), len(lines)))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
