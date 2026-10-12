#!/usr/bin/env python3
"""P05-S4 R7 M2: compare the two passes of one group point by point (new file).

Reads RESULTS_R7_<GROUP>_pass1_run4.tsv and RESULTS_R7_<GROUP>_pass2_run4.tsv (read only) and writes one new file:
the per-point comparison of class, verdict, rc, rc1, rc2 and hit, with a flag FLAKY where the two passes disagree.
Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r7/compare_passes_r7.py EVDIR GROUP OUT.tsv
Exit status is 0 only if there is no FLAKY row and no non-MATCH verdict in either pass.
"""
import os
import sys

FIELDS = ["class", "verdict", "rc", "rc1", "rc2", "hit"]


def load(path):
    header, rows = None, {}
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            d = dict(zip(header, f))
            rows[(d["point_id"], d["tree"])] = d
    return rows


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: compare_passes_r7.py EVDIR GROUP OUT.tsv")
    ev, group, out = argv[1], argv[2], argv[3]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    p1 = load(os.path.join(ev, "RESULTS_R7_%s_pass1_run4.tsv" % group))
    p2 = load(os.path.join(ev, "RESULTS_R7_%s_pass2_run4.tsv" % group))
    if set(p1) != set(p2):
        raise SystemExit("REFUSED: pass point sets differ for %s" % group)
    lines = ["# compare of passes 1 and 2 for group %s (run4).  FLAKY = any field differs between the passes." % group,
             "point_id\ttree\t" + "\t".join("p1_" + f for f in FIELDS) + "\t" + "\t".join("p2_" + f for f in FIELDS) + "\tflaky"]
    flaky = nonmatch = 0
    for key in sorted(p1):
        a, b = p1[key], p2[key]
        differ = any(a[f] != b[f] for f in FIELDS)
        if differ:
            flaky += 1
        if a["verdict"] != "MATCH" or b["verdict"] != "MATCH":
            nonmatch += 1
        lines.append("\t".join([key[0], key[1]] + [a[f] for f in FIELDS] + [b[f] for f in FIELDS]
                               + ["FLAKY" if differ else "-"]))
    lines.append("# points=%d flaky=%d non_match_in_either_pass=%d" % (len(p1), flaky, nonmatch))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("group=%s points=%d flaky=%d non_match=%d -> %s" % (group, len(p1), flaky, nonmatch, out))
    return 0 if (flaky == 0 and nonmatch == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
