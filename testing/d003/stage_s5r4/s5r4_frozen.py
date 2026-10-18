#!/usr/bin/env python3
# s5r4_frozen.py -- FROZEN_SCRIPTS_S5R4.tsv: the scripts frozen by record commit (i), their sha256 and the
# number of POST_I invocations the end gate must observe (mode '-' = any invocation token; mode 'formal'
# requires the word formal in the command).  Every formal chain step is invoked exactly once; scripts that
# only run before commit (i) have expected_calls=0.
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV4 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r4")
TAB = chr(9)
NL = chr(10)
ROWS = [
    ("s5r4_startgate.py", 0, "-"), ("s5r4_prep.py", 0, "-"), ("s5r4_prereg.py", 0, "-"),
    ("rejudge_s5r4.py", 1, "formal"), ("s5r4_rejudge_check.py", 0, "-"), ("s5r4_copycheck.py", 0, "-"),
    ("s5r4_gate_posctrl.py", 0, "-"), ("s5r4_frozen.py", 0, "-"),
    ("s5r4_state.py", 1, "formal"), ("s5r4_readiness.py", 1, "formal"), ("s5r4_r3recheck.py", 1, "formal"),
    ("s5r4_acceptance.py", 1, "formal"), ("s5r4_signoff.py", 1, "formal"),
    ("s5r4_apply_patch.py", 1, "formal"), ("s5r4_report.py", 1, "formal"),
    ("s5r4_report_check.py", 1, "formal"), ("s5r4_registry.py", 1, "formal"),
    ("s5r4_events.py", 1, "formal"), ("s5r4_sha_sums.py", 1, "formal"), ("s5r4_chain.py", 1, "formal"),
    ("gate_s5r4.sh", 1, "-"), ("gate_check_s5r4.py", 0, "-"), ("s5r4_appendix.py", 0, "-"),
]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    rows = ["# FROZEN_SCRIPTS_S5R4.tsv -- frozen scripts after the shakedown rehearsal and before record commit (i).",
            "# The end gate reads POST_I call expectations from this file BY COLUMN NAME (task brief section 6).",
            "# mode '-' means any invocation counts; the other value names the mode word that must appear in the command.",
            TAB.join(["path", "sha256", "expected_calls", "mode"])]
    miss = []
    for name, calls, mode in ROWS:
        rel = "testing/d003/stage_s5r4/" + name
        p = os.path.join(REPO, rel)
        if not os.path.isfile(p):
            miss.append(name)
            continue
        rows.append(TAB.join([rel, sha_f(p), str(calls), mode]))
    out = os.path.join(EV4, "FROZEN_SCRIPTS_S5R4.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("FROZEN rows=%d sha=%s" % (len(rows) - 4, sha_f(out)))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if not miss else 1


if __name__ == "__main__":
    sys.exit(main())
