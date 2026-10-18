#!/usr/bin/env python3
# events_r9m3a.py -- frozen event table for the round: one row per non-blank physical line of safe_run.log.
# usage: python3 -I -B testing/d003/stage_s4r9/events_r9m3a.py OUT.tsv
import os, sys

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a")
TAB = chr(9)
NL = chr(10)


def category(cmd):
    c = cmd.strip()
    for key, name in (("base64", "WRITE_FILE"), ("git archive", "TREE_EXPORT"), ("tar -x", "TREE_EXPORT"),
                      ("make ", "BUILD_TEST"), ("g++", "BUILD"), ("gcc", "BUILD"), ("nm ", "INSPECT"),
                      ("git ", "GIT"), ("gate_r9m3a", "GATE"), ("progress_r9m3a", "PROGRESS"),
                      ("events_r9m3a", "EVENTS"), ("sha_sums_r9m3a", "SHA_SUMS"), ("copy_registries_r9m3a", "COPY_REG"),
                      ("report_check_r9m3a", "REPORT_CHECK"), ("stage_s4r9", "SCRIPT")):
        if key in c:
            return name
    return "OTHER"


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV, "EVENTS_R9M3A.tsv")
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
        fh.write("# EVENTS_R9M3A.tsv -- complete safe_run event table under physical line numbering" + NL)
        fh.write(TAB.join(["log_line", "utc_timestamp", "category", "command_summary"]) + NL)
        for r in rows:
            fh.write(TAB.join(str(x) for x in r) + NL)
    print("rows=%d log_lines=%d" % (len(rows), len(lines)))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
