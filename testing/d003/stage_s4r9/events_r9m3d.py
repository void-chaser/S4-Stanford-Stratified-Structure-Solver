#!/usr/bin/env python3
# events_r9m3d.py -- frozen event table: one row per non-blank physical line of safe_run.log. New file (r9m3d).
# usage: events_r9m3d.py [OUT.tsv]
import os, sys
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
TAB = chr(9)
NL = chr(10)


def category(cmd):
    c = cmd.strip()
    for key, name in (
        ("base64", "WRITE_FILE"), ("safe_run.sh", "SAFE_RUN_FILE"), ("git archive", "TREE_EXPORT"),
        ("tar -x", "TREE_EXPORT"), ("make ", "BUILD_TEST"), ("g++", "BUILD"), ("gcc", "BUILD"),
        ("nm ", "INSPECT"), ("grep", "INSPECT"), ("git ", "GIT"),
        ("gate_r9m3d", "GATE"), ("gate_check_r9m3d", "GATE_CHECK"),
        ("progress_r9m3d", "PROGRESS"), ("events_r9m3d", "EVENTS"), ("sha_sums_r9m3d", "SHA_SUMS"),
        ("copy_registries_r9m3d", "COPY_REG"), ("report_check_r9m3d", "REPORT_CHECK"),
        ("posctrl_report_check_r9m3d", "POSCTRL_REPORT_CHECK"), ("closeout_report_state_r9m3d", "CLOSEOUT"),
        ("posctrl_handoff_r9m3d", "POSCTRL_HANDOFF"), ("posctrl_readiness_r9m3d", "POSCTRL_READINESS"),
        ("s5_handoff_r9m3d", "S5_HANDOFF"), ("readiness_r9m3d", "READINESS"),
        ("red_ledger_final_r9m3d", "RED_LEDGER"), ("update_state_r9m3d", "STATE_UPDATE"),
        ("audit_r9m3c_r9m3d", "AUDIT"), ("append_rulings_r9m3d", "APPEND_RULINGS"),
        ("append_errata_r9m3d", "APPEND_ERRATA"), ("write_signoff_v2_r9m3d", "SIGNOFF_V2"),
        ("fix_report_r9m3d", "FIX_REPORT"), ("write_frozen_r9m3d", "FROZEN"),
        ("stage_s4r9", "SCRIPT")):
        if key in c:
            return name
    return "OTHER"


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV, "EVENTS_R9M3D.tsv")
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
        fh.write("# EVENTS_R9M3D.tsv -- complete safe_run event table under physical line numbering" + NL)
        fh.write(TAB.join(["log_line", "utc_timestamp", "category", "command_summary"]) + NL)
        for r in rows:
            fh.write(TAB.join(str(x) for x in r) + NL)
        fh.write("# UNIQUE=%d ROWS=%d" % (len(set(r[0] for r in rows)), len(rows)) + NL)
    print("rows=%d log_lines=%d" % (len(rows), len(lines)))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
