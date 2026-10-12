#!/usr/bin/env python3
# r3_tables.py -- P05-S4 R3-5 red-point table and out-of-scope count table (new file, R3).  Reads RESULTS_R3.tsv
# (in-scope observations), RESULTS_R3_OUTSCOPE.raw.tsv (out-of-scope observations), SITEMAP.tsv and the static count
# file.  Writes RED_POINTS_R3.tsv and OUTSCOPE_COUNT_R3.tsv.  Nothing is classified here: classes are copied.
#
#   python3 -I -B testing/d003/stage_s4/r3_tables.py RESULTS_R3 OUTSCOPE_RAW SITEMAP OUT_DIR
#
# Red point (task R3-5 definition, tree F only): in-scope AND (observed CRASH or SILENT_SWALLOW) OR not reached (hit 0).
# A not-reached point is a red point by definition, but its cause is a measurement limit, recorded as "cause".
import sys
from collections import Counter, defaultdict


def rows(path, skip):
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith(skip):
                continue
            out.append(line.rstrip("\n").split("\t"))
    return out


def main(argv):
    if len(argv) != 5:
        print("usage: r3_tables.py RESULTS_R3 OUTSCOPE_RAW SITEMAP OUT_DIR", file=sys.stderr)
        return 2
    res_path, out_path, sm_path, outdir = argv[1], argv[2], argv[3], argv[4]
    res = rows(res_path, "point_id\t")
    outs = rows(out_path, "point_id\t")
    sm = rows(sm_path, "point_id\t")
    caller = {r[0]: r[5] for r in sm}
    # ---- red points (tree F, in scope) ----
    red = []
    for r in res:
        pid, tree, mode, cat, nth, expected, observed, match, rc, rc1, signal, hit, inj_call = r
        if tree != "F" or pid.startswith("CTL") or cat == "control":
            continue   # controls are not injection points: hit 0 is their correct value
        if observed in ("CRASH", "SILENT_SWALLOW"):
            cause = "observed %s" % observed
        elif hit == "0":
            cause = "not reached (hit 0): injector cannot select this call (see ERRATA_3 f); not evidence about the code"
        else:
            continue
        red.append((pid, mode, cat, nth, caller.get(pid, "?"), rc, rc1, signal, hit, observed, cause))
    with open(outdir + "/RED_POINTS_R3.tsv", "w", encoding="utf-8") as fh:
        fh.write("# RED_POINTS_R3.tsv -- P05-S4 R3-5 red points on tree F (in scope).  Recorded only; not fixed in R3.\n")
        fh.write("# Red point = observed CRASH or SILENT_SWALLOW on F, or not reached (hit 0) on F.\n")
        fh.write("point_id\tmode\tcategory\tNTH\tcaller_function\trc\trc1\tsignal\thit\tobserved_class\tcause\n")
        for r in red:
            fh.write("\t".join(str(x) for x in r) + "\n")
    # ---- out-of-scope S4_malloc count is static (see report); the NO plan/exec observations are counted here ----
    cnt = Counter()
    by_cat = defaultdict(Counter)
    for r in outs:
        pid, tree, mode, cat, nth, caller_fn, observed, rc, rc1, rc2, hit, inj_call, reason, log = r
        cnt[(tree, observed)] += 1
        by_cat[(cat, tree)][observed] += 1
    with open(outdir + "/OUTSCOPE_COUNT_R3.tsv", "w", encoding="utf-8") as fh:
        fh.write("# OUTSCOPE_COUNT_R3.tsv -- P05-S4 R3-5 out-of-scope (in_D003_scope=NO) counts.  Counted only; not red points.\n")
        fh.write("# Section A: observed NO plan/exec points (GetFieldOnGrid, rcwa.cpp).  Section B: non-FMM S4_malloc (static).\n")
        fh.write("section\tcategory\ttree\tobserved_class\tcount\n")
        for (cat, tree), c in sorted(by_cat.items()):
            for obs_cls, n in sorted(c.items()):
                fh.write("A\t%s\t%s\t%s\t%d\n" % (cat, tree, obs_cls, n))
    print("red_points_F=%d outscope_observations=%d" % (len(red), len(outs)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
