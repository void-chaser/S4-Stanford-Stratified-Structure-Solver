#!/usr/bin/env python3
# write_frozen_r9m3b.py -- write FROZEN_SCRIPTS_R9M3B.tsv before record commit (i). New file (r9m3b).
# Columns: path, sha256, expected_calls, mode (the end gate derives its call-count checks from this file, U337).
import os, sys, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
OUT = os.path.join(EV, "FROZEN_SCRIPTS_R9M3B.tsv")
TAB = chr(9)
NL = chr(10)
S = "testing/d003/stage_s4r9/"
P = "checkpoints/p05/evidence/p05-s4r9/m3b/"
ROWS = [
    (S + "run_e2e_r9m3b.py", ">=1", "formal"),
    (S + "judge_e2e_r9m3b.py", "1", "posctrl"),
    (S + "judge_e2e_r9m3b.py", "1", "formal"),
    (S + "judge_maketest_r9m3b_v2.py", "1", "posctrl"),
    (S + "judge_maketest_r9m3b_v2.py", "1", "formal"),
    (S + "closeout_report_state_r9m3b.py", "1", "-"),
    (S + "report_check_r9m3b.py", "1", "-"),
    (S + "copy_registries_r9m3b.py", "1", "-"),
    (S + "events_r9m3b.py", "1", "-"),
    (S + "sha_sums_r9m3b.py", "1", "-"),
    (S + "gate_r9m3b_v3.sh", "1", "end"),
    (S + "gate_check_r9m3b_v3.py", "0", "-"),
    (P + "PREREG_E2E_R9M3B.tsv", "0", "-"),
    (P + "CALIB_E2E_R9M3B.tsv", "0", "-"),
]


def main():
    lines = ["# FROZEN_SCRIPTS_R9M3B.tsv -- frozen scripts and pre-registration/calibration files recorded before record commit (i)",
             "# expected_calls: the end gate's POST_I count expectation read from this file (U337); '-' mode means any invocation token"]
    lines.append(TAB.join(["path", "sha256", "expected_calls", "mode"]))
    for rel, exp, mode in ROWS:
        p = os.path.join(REPO, rel)
        if not os.path.isfile(p):
            print("MISSING " + rel)
            return 2
        lines.append(TAB.join([rel, hashlib.sha256(open(p, "rb").read()).hexdigest(), exp, mode]))
    open(OUT, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("frozen rows=%d" % len(ROWS))
    print("WROTE " + OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
