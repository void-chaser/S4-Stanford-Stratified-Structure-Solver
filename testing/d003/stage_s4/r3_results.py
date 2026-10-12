#!/usr/bin/env python3
# r3_results.py -- P05-S4 R3-5 result table builder (new file, R3).  Reads the raw sweep tables written by
# run_r3_sweep.py (RESULTS_R3.raw.tsv) and writes RESULTS_R3.tsv with the columns required by the R3 task:
#   point_id, tree, expected_class, observed_class, match, rc, rc1, signal, hit
# plus the field call (inj_call).  It does NOT re-classify anything: observed_class is copied from the raw table, which
# was produced by judge_d003.classify.  match is derived from expected and observed and from hit:
#   INVALID    hit == 0 (the injection was not reached; not evidence about the code under test)
#   MATCH      hit >= 1 and observed == expected
#   MISMATCH   hit >= 1 and observed != expected
# signal = rc - 128 when the process was killed by a signal (rc >= 128), else "-".
#
#   python3 -I -B testing/d003/stage_s4/r3_results.py RAW_TSV OUT_TSV
import sys


def main(argv):
    if len(argv) != 3:
        print("usage: r3_results.py RAW_TSV OUT_TSV", file=sys.stderr)
        return 2
    raw, out = argv[1], argv[2]
    rows = []
    with open(raw, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith("point_id\t"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) != 14:
                raise SystemExit("raw row has %d fields" % len(f))
            pid, tree, mode, cat, nth, expected, observed, rc, rc1, rc2, hit, inj_call, reason, log = f
            hit_i = int(hit)
            rc_i = int(rc) if rc not in ("None", "") else None
            if cat == "control":
                # a control run has no injection: hit 0 is its correct value, not INVALID
                match = "MATCH" if observed == expected else "MISMATCH"
            elif hit_i == 0:
                match = "INVALID"
            elif observed == expected:
                match = "MATCH"
            else:
                match = "MISMATCH"
            signal = str(rc_i - 128) if (rc_i is not None and rc_i >= 128) else "-"
            rows.append((pid, tree, mode, cat, nth, expected, observed, match, str(rc), rc1, signal, hit, inj_call))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# RESULTS_R3.tsv -- P05-S4 R3-4 results.  Derived by r3_results.py from RESULTS_R3.raw.tsv (judge_d003.classify).\n")
        fh.write("# match: INVALID = hit 0 (not reached); MATCH = hit >= 1 and observed == expected; MISMATCH = hit >= 1 and observed != expected.\n")
        fh.write("point_id\ttree\tmode\tcategory\tnth\texpected_class\tobserved_class\tmatch\trc\trc1\tsignal\thit\tinj_call\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    from collections import Counter
    c = Counter(r[7] for r in rows)
    print("rows=%d MATCH=%d MISMATCH=%d INVALID=%d" % (len(rows), c["MATCH"], c["MISMATCH"], c["INVALID"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
