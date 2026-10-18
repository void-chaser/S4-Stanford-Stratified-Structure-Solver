#!/usr/bin/env python3
# fix_report_r9m3b.py -- fill the numbered deliverable list of report section 14.1 (pre-(i) draft fix). New file (r9m3b).
import os, sys, hashlib
REP = "checkpoints/p05/P05_S4R9_M3b_REPORT.md"
PH = "（CLOSEOUT_FILLS_DELIVERABLES）"
ITEMS = [
    "GATE_R9M3B_start.txt",
    "GATE_R9M3B_start_RECHECK.txt",
    "AUDIT_R9M3A_R9M3B.tsv",
    "MAKETEST_UNITS_R9M3B.tsv",
    "MAKETEST_VERDICT_R9M3B.tsv",
    "POSCTRL_MAKETEST_R9M3B.txt",
    "E2E_API_SURVEY_R9M3B.md",
    "COVERAGE_E2E_R9M3B.tsv",
    "E2E_BUILD_R9M3B.tsv",
    "CALIB_E2E_R9M3B.tsv",
    "PREREG_E2E_R9M3B.tsv",
    "PREREG_E2E_R9M3B.sha256.txt",
    "E2E_VERDICT_R9M3B.tsv",
    "POSCTRL_E2E_R9M3B.txt",
    "RED_POINTS_LEDGER_APPEND_R9M3B.tsv",
    "LEDGER_CHECK_R9M3B.tsv",
    "FROZEN_SCRIPTS_R9M3B.tsv",
    "REPORT_CHECK_R9M3B.txt",
    "SHA256SUMS.txt",
]


def main():
    data = open(REP, "rb").read()
    txt = data.decode("utf-8")
    if txt.count(PH) != 1:
        print("HARD_STOP placeholder count %d" % txt.count(PH))
        return 2
    body = "\n".join("%d. %s" % (i + 1, name) for i, name in enumerate(ITEMS))
    txt = txt.replace(PH, body)
    open(REP, "wb").write(txt.encode("utf-8"))
    print("items=%d report bytes %d -> %d sha %s" % (len(ITEMS), len(data), len(txt.encode("utf-8")),
                                                     hashlib.sha256(txt.encode("utf-8")).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
