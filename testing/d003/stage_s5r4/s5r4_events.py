#!/usr/bin/env python3
# s5r4_events.py -- EVENTS_S5R4.tsv: safe_run.log line -> UTC timestamp for rows 1..anchor, where anchor is
# this script's own invocation line. The end gate recomputes the exact same row set (task brief section 6).
# usage: s5r4_events.py formal [--ev-root DIR]
import os, sys, re, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV4_REAL = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r4")
TAB = chr(9)
NL = chr(10)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "formal":
        print("usage: s5r4_events.py formal [--ev-root DIR]", file=sys.stderr)
        return 2
    EV = os.path.abspath(sys.argv[sys.argv.index("--ev-root") + 1]) if "--ev-root" in sys.argv else EV4_REAL
    ls = open(os.path.join(EV4_REAL, "safe_run.log"), encoding="utf-8").read().splitlines()
    anchor = 0
    for i in range(len(ls), 0, -1):
        if "s5r4_events.py formal" in ls[i - 1]:
            anchor = i
            break
    if anchor <= 0:
        print("HARD_STOP no events anchor")
        return 2
    ts_re = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")
    parent = ""
    body = ["# EVENTS_S5R4.tsv -- safe_run.log line -> UTC timestamp (rows 1..%d; anchor = events call line %d)" % (anchor, anchor),
            TAB.join(["log_line", "ts_utc"])]
    for x in range(1, anchor + 1):
        m = ts_re.match(ls[x - 1])
        if m:
            parent = m.group(1)
        body.append(TAB.join([str(x), parent]))
    body.append("# ROWS=%d" % anchor)
    out = os.path.join(EV, "EVENTS_S5R4.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("EVENTS rows=%d anchor=%d" % (anchor, anchor))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
