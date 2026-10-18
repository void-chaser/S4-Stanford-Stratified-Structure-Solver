#!/usr/bin/env python3
# s5r3_frozen.py -- write FROZEN_SCRIPTS_S5R3.tsv: the sha256 of every S5R3 script plus the POST_I call
# expectation read by the end gate BY COLUMN NAME. Run once, after the shakedown chain and before commit (i).
import os, sys, subprocess, hashlib

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)
ROWS = [
    ("testing/d003/stage_s5r3/d016_run_s5r3.py", "2", "formal"),
    ("testing/d003/stage_s5r3/d016_run_s5r3.py", "1", "judge"),
    ("testing/d003/stage_s5r3/d016_run_s5r3.py", "1", "posctrl"),
    ("testing/d003/stage_s5r3/d016_py_s5r3.py", "0", "-"),
    ("testing/d003/stage_s5r3/d016_lua_s5r3.lua", "0", "-"),
    ("testing/d003/stage_s5r3/build_e2e_s5r3.py", "0", "-"),
    ("testing/d003/stage_s5r3/calib_e2e_s5r3.py", "0", "-"),
    ("testing/d003/stage_s5r3/calib_diff_s5r3.py", "0", "-"),
    ("testing/d003/stage_s5r3/e2e_python_s5r3.py", "0", "-"),
    ("testing/d003/stage_s5r3/e2e_lua_s5r3.lua", "0", "-"),
    ("testing/d003/stage_s5r3/e2e_lua_repl_s5r3.txt", "0", "-"),
    ("testing/d003/stage_s5r3/run_e2e_s5r3.py", "2", "formal"),
    ("testing/d003/stage_s5r3/judge_e2e_s5r3.py", "1", "posctrl"),
    ("testing/d003/stage_s5r3/judge_e2e_s5r3.py", "1", "formal"),
    ("testing/d003/stage_s5r3/s5r3_build_trees.py", "0", "-"),
    ("testing/d003/stage_s5r3/s5r3_d016_build_record.py", "0", "-"),
    ("testing/d003/stage_s5r3/run_maketest_s5r3.py", "1", "B:1"),
    ("testing/d003/stage_s5r3/run_maketest_s5r3.py", "1", "F4:1"),
    ("testing/d003/stage_s5r3/run_maketest_s5r3.py", "1", "B:2"),
    ("testing/d003/stage_s5r3/run_maketest_s5r3.py", "1", "F4:2"),
    ("testing/d003/stage_s5r3/judge_maketest_s5r3.py", "1", "posctrl"),
    ("testing/d003/stage_s5r3/judge_maketest_s5r3.py", "1", "formal"),
    ("testing/d003/stage_s5r3/rejudge_s5r3.py", "1", "formal"),
    ("testing/d003/stage_s5r3/apply_patch_s5r3.py", "1", "-"),
    ("testing/d003/stage_s5r3/s5r3_chain.py", "8", "-"),
    ("testing/d003/stage_s5r3/s5r3_frozen.py", "0", "-"),
    ("testing/d003/stage_s5r3/s5r3_copycheck.py", "0", "-"),
    ("testing/d003/stage_s5r3/s5r3_prereg.py", "0", "-"),
    ("testing/d003/stage_s5r3/s5r3_prep.py", "0", "-"),
    ("testing/d003/stage_s5r3/s5r3_startgate.py", "0", "-"),
    ("testing/d003/stage_s5r3/s5r3_state_i.py", "0", "-"),
    ("testing/d003/stage_s5r3/gate_s5r3.sh", "1", "end"),
    ("testing/d003/stage_s5r3/gate_check_s5r3.py", "0", "-"),
    ("testing/d003/stage_s5r3/s5r3_appendix.py", "0", "-"),
]


def sha_f(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    lines = ["# FROZEN_SCRIPTS_S5R3.tsv -- frozen scripts after the shakedown chain and before record commit (i).",
             "# The end gate reads the POST_I call expectations from this file BY COLUMN NAME (task brief section 6/7).",
             "# mode '-' means any invocation token counts; the other values name the mode/segment word in the command.",
             TAB.join(["path", "sha256", "expected_calls", "mode"])]
    missing = []
    for rel, exp, mode in ROWS:
        p = os.path.join(REPO, rel)
        if not os.path.isfile(p):
            missing.append(rel)
            continue
        lines.append(TAB.join([rel, sha_f(p), exp, mode]))
    if missing:
        print("HARD_STOP missing scripts: " + ",".join(missing))
        return 2
    out = os.path.join(EV, "FROZEN_SCRIPTS_S5R3.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("FROZEN rows=%d sha=%s" % (len(ROWS), sha_f(out)))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())