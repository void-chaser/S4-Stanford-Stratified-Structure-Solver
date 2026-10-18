#!/usr/bin/env python3
# write_frozen_r9m3d.py -- write FROZEN_SCRIPTS_R9M3D.tsv after the shakedown chain and before the start-prefix
# recheck / record commit (i). Columns: path, sha256, expected_calls, mode. expected_calls is the end gate's POST_I
# count expectation; "-" mode means any invocation token. New file (r9m3d).
import os, sys, hashlib
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
OUT = os.path.join(EV, "FROZEN_SCRIPTS_R9M3D.tsv")
TAB = chr(9)
NL = chr(10)
S = "testing/d003/stage_s4r9/"
E = "checkpoints/p05/evidence/p05-s4r9/"
ROWS = [
    (S + "red_ledger_final_r9m3d.py", "1", "-"),
    (S + "s5_handoff_r9m3d.py", "1", "-"),
    (S + "readiness_r9m3d.py", "1", "-"),
    (S + "closeout_report_state_r9m3d.py", "1", "-"),
    (S + "report_check_r9m3d.py", "1", "-"),
    (S + "copy_registries_r9m3d.py", "1", "-"),
    (S + "events_r9m3d.py", "1", "-"),
    (S + "sha_sums_r9m3d.py", "1", "-"),
    (S + "gate_r9m3d.sh", "1", "end"),
    (S + "progress_r9m3d.py", "1", "-"),
    (S + "gate_check_r9m3d.py", "0", "-"),
    (S + "update_state_r9m3d.py", "0", "-"),
    (S + "append_rulings_r9m3d.py", "0", "-"),
    (S + "append_errata_r9m3d.py", "0", "-"),
    (S + "audit_r9m3c_r9m3d.py", "0", "-"),
    (S + "write_signoff_v2_r9m3d.py", "0", "-"),
    (S + "posctrl_handoff_r9m3d.py", "0", "-"),
    (S + "posctrl_readiness_r9m3d.py", "0", "-"),
    (S + "posctrl_report_check_r9m3d.py", "0", "-"),
    (S + "fix_report_r9m3d.py", "0", "-"),
    (S + "write_frozen_r9m3d.py", "0", "-"),
    (E + "m3b/PREREG_E2E_R9M3B.tsv", "0", "-"),
    (E + "m3b/CALIB_E2E_R9M3B.tsv", "0", "-"),
    (E + "m3d/AUDIT_R9M3C_R9M3D.tsv", "0", "-"),
    ("checkpoints/p05/registries/s4r9/M3c/RED_POINTS_LEDGER_FINAL_R9M3C.tsv", "0", "-"),
]


def main():
    lines = ["# FROZEN_SCRIPTS_R9M3D.tsv -- frozen scripts and referenced result tables recorded after the shakedown",
             "# chain and before the start-prefix recheck / record commit (i). The end gate reads every script name and",
             "# POST_I count expectation from this file (U337 / E9-59 discipline)." + NL + TAB.join(
                 ["path", "sha256", "expected_calls", "mode"])]
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
