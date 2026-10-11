#!/usr/bin/env python3
"""P05-S3R2 numeric comparison of two field dumps (read-only; stdout only).

Each dump line is 'E|H index value' with value written by %.17g.  For every value pair the
relative difference is |a-b| / max(|a|,|b|) over pairs where max(|a|,|b|) > 0 (pairs where both are
exactly zero contribute 0).  Non-finite values are counted and excluded from the relative
difference, and reported separately.

Prints: n_values, n_identical_text, n_nonfinite_pairs, max_rel, median_rel, n_over_1e10.
Usage: python3 -I -B testing/d003/stage_s3r2/rel_diff.py FILE_A FILE_B
No pass/fail judgement is made here.
"""
import math
import sys


def load(path):
    vals = []
    with open(path, "r", encoding="utf-8") as fh:
        for ln in fh:
            p = ln.split()
            if len(p) == 3:
                vals.append((p[0], p[1], p[2]))
    return vals


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("usage: rel_diff.py FILE_A FILE_B\n")
        return 2
    a = load(sys.argv[1])
    b = load(sys.argv[2])
    n = min(len(a), len(b))
    n_same_text = 0
    n_nonfinite = 0
    rels = []
    for i in range(n):
        ka, ia, sa = a[i]
        kb, ib, sb = b[i]
        if sa == sb:
            n_same_text += 1
            continue
        va = float(sa)
        vb = float(sb)
        if not (math.isfinite(va) and math.isfinite(vb)):
            n_nonfinite += 1
            continue
        scale = max(abs(va), abs(vb))
        if scale == 0.0:
            rels.append(0.0)
        else:
            rels.append(abs(va - vb) / scale)
    rels.sort()
    max_rel = rels[-1] if rels else 0.0
    if rels:
        m = len(rels) // 2
        med = rels[m] if len(rels) % 2 == 1 else 0.5 * (rels[m - 1] + rels[m])
    else:
        med = 0.0
    n_over = sum(1 for r in rels if r > 1e-10)
    print("n_values=%d" % n)
    print("n_identical_text=%d" % n_same_text)
    print("n_nonfinite_pairs=%d" % n_nonfinite)
    print("n_differ_numeric=%d" % len(rels))
    print("max_rel=%.6e" % max_rel)
    print("median_rel=%.6e" % med)
    print("n_over_1e10=%d" % n_over)
    return 0


if __name__ == "__main__":
    sys.exit(main())
