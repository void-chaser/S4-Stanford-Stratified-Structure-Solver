#!/usr/bin/env python3
# events_r9m3b.py -- frozen event table: one row per non-blank physical line of safe_run.log. New file (r9m3b).
# usage: python3 -I -B testing/d003/stage_s4r9/events_r9m3b.py OUT.tsv
import os, sys

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
TAB = chr(9)
NL = chr(10)


def category(cmd):
    c = cmd.strip()
    for key, name in (("base64", "WRITE_FILE"), ("git archive", "TREE_EXPORT"), ("tar -x", "TREE_EXPORT"),
                      ("make ", "BUILD_TEST"), ("g++", "BUILD"), ("gcc", "BUILD"), ("nm ", "INSPECT"),
                      ("git ", "GIT"), ("gate_r9m3b", "GATE"), ("progress_r9m3b", "PROGRESS"),
                      ("events_r9m3b", "EVENTS"), ("sha_sums_r9m3b", "SHA_SUMS"), ("copy_registries_r9m3b", "COPY_REG"),
                      ("report_check_r9m3b", "REPORT_CHECK"), ("closeout_report_state_r9m3b", "CLOSEOUT"),
                      ("judge_e2e_r9m3b", "JUDGE_E2E"), ("run_e2e_r9m3b", "RUN_E2E"),
                      ("judge_maketest_r9m3b", "JUDGE_MAKETEST"), ("calib_e2e_r9m3b", "CALIB"),
                      ("build_e2e_r9m3b", "BUILD_E2E"), ("audit_r9m3a_r9m3b", "AUDIT"),
                      ("append_rulings_r9m3b", "APPEND_RULINGS"), ("append_errata_r9m3b", "APPEND_ERRATA"),
                      ("write_prereg_r9m3b", "PREREG"), ("coverage_e2e_r9m3b", "COVERAGE"),
                      ("ledger_r9m3b", "LEDGER"), ("write_frozen_r9m3b", "FROZEN"),
                      ("stage_s4r9", "SCRIPT")):
        if key in c:
            return name
    return "OTHER"


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV, "EVENTS_R9M3B.tsv")
    log = os.path.join(EV, "safe_run.log")
    lines = open(log, encoding="utf-8", errors="replace").read().splitlines()
    rows = []
    parent = ""
    for i, line in enumerate(lines, 1):
        if not line.strip():
            continue
        if line[:4] == "2026" and len(line) > 20 and line[4] == "-":
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
        fh.write("# EVENTS_R9M3B.tsv -- complete safe_run event table under physical line numbering" + NL)
        fh.write(TAB.join(["log_line", "utc_timestamp", "category", "command_summary"]) + NL)
        for r in rows:
            fh.write(TAB.join(str(x) for x in r) + NL)
    print("rows=%d log_lines=%d" % (len(rows), len(lines)))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
