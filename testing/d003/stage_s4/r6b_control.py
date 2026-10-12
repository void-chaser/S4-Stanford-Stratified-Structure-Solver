#!/usr/bin/env python3
# r6b_control.py -- P05-S4 R6b-2 control registration (new file).
# One no-injection control run per distinct (mode, route, twice) combination of the 177 judgeable points.
# The control runs the same driver with the same stack (pattern both 4 3), NG 9, TWICE set explicitly, and
# S4FMM_INJECT unset.  Its snapshots and call outputs are the reference for I2(a)(b), I3, I5 and I6.
# Reads REGISTRY_S4_PRE_R6b_STATE.tsv (hash-locked) and writes REGISTRY_S4_PRE_R6b_CONTROL.tsv.
#
# Usage: python3 -I -B testing/d003/stage_s4/r6b_control.py PREREG OUT_TSV
import os
import sys


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: r6b_control.py PREREG OUT_TSV")
    prereg, out = argv[1], argv[2]
    header = None
    combos = {}
    with open(prereg, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            d = dict(zip(header, f))
            key = (d["mode"], d["route"], d["twice"])
            combos.setdefault(key, []).append(d["point_id"])
    keys = sorted(combos)
    if len(keys) != 16:
        raise SystemExit("REFUSED: expected 16 control combinations, got %d" % len(keys))
    cols = ["control_id", "mode", "route", "twice", "stack", "NG", "inj_env", "points_served", "n_points", "status"]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# REGISTRY_S4_PRE_R6b_CONTROL.tsv -- P05-S4 R6b-2 control runs (no injection), one per (mode, route, twice).\n")
        fh.write("# Written BEFORE any R6b state run.  inj_env is empty (S4FMM_INJECT unset).  TWICE set explicitly (slab or empty for once).\n")
        fh.write("\t".join(cols) + "\n")
        for i, (mode, route, twice) in enumerate(keys, 1):
            served = combos[(mode, route, twice)]
            fh.write("\t".join(["C-%02d-%s-%s-%s" % (i, mode, route, twice if twice != "-" else "once"), mode, route,
                                twice, "pattern both 4 3", "9", "", ";".join(served), str(len(served)),
                                "INFLUENCED"]) + "\n")
    total = sum(len(v) for v in combos.values())
    print("controls=%d points_covered=%d" % (len(keys), total))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
