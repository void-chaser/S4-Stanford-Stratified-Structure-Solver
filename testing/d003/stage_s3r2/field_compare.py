#!/usr/bin/env python3
"""P05-S3R2 field comparison (read-only, stdout only).

Compares two field dumps written by the probes (lines 'E i value' and 'H i value', %.17g).
Reports:
  identical_text   : every line is byte-identical
  n_values         : number of values compared
  n_different      : values whose text differs
  max_rel_diff     : max over values of |a-b| / max(|a|,|b|,tiny), over values where either is nonzero
  median_rel_diff  : median of the same quantity over the values that differ
  nonfinite_a/b    : count of non-finite values in each file
Usage: python3 -I -B testing/d003/stage_s3r2/field_compare.py FILE_A FILE_B [LABEL]
No pass/fail judgement is made here; the caller reads the numbers.
"""
import math
import sys


def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for ln in fh:
            rows.append(ln.rstrip("\n"))
    return rows


def main():
    if len(sys.argv) not in (3, 4):
        sys.stderr.write("usage: field_compare.py FILE_A FILE_B [LABEL]\n")
        return 2
    a_rows = load(sys.argv[1])
    b_rows = load(sys.argv[2])
    label = sys.argv[3] if len(sys.argv) == 4 else "compare"
    identical_text = (a_rows == b_rows)
    n = 0
    n_diff = 0
    rels = []
    nf_a = 0
    nf_b = 0
    for ra, rb in zip(a_rows, b_rows):
        pa = ra.split()
        pb = rb.split()
        if len(pa) != 3 or len(pb) != 3:
            continue
        va = float(pa[2])
        vb = float(pb[2])
        if not math.isfinite(va):
            nf_a += 1
        if not math.isfinite(vb):
            nf_b += 1
        n += 1
        if pa[2] != pb[2]:
            n_diff += 1
            scale = max(abs(va), abs(vb))
            if scale > 0.0 and math.isfinite(scale):
                rels.append(abs(va - vb) / scale)
            else:
                rels.append(float("inf"))
    rels.sort()
    max_rel = rels[-1] if rels else 0.0
    if rels:
        mid = len(rels) // 2
        med = rels[mid] if len(rels) % 2 == 1 else 0.5 * (rels[mid - 1] + rels[mid])
    else:
        med = 0.0
    print("label=%s" % label)
    print("identical_text=%s" % ("yes" if identical_text else "no"))
    print("lines_a=%d lines_b=%d" % (len(a_rows), len(b_rows)))
    print("n_values=%d" % n)
    print("n_different=%d" % n_diff)
    print("max_rel_diff=%.6e" % max_rel)
    print("median_rel_diff=%.6e" % med)
    print("nonfinite_a=%d nonfinite_b=%d" % (nf_a, nf_b))
    return 0


if __name__ == "__main__":
    sys.exit(main())
