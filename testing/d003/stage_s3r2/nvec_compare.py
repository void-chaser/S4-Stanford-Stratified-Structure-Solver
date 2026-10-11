#!/usr/bin/env python3
"""P05-S3R2 nvec comparison (read-only, stdout only).

Reads two gdb records written by gdb_d138_nvec.gdb (lines 'SGN_ENTER k=.. shape_ptr=.. x=..,..'
and 'SGN_RET nvec=..,..') and compares, call by call, the input point, the shape pointer and
the returned normal.  Reports:
  calls                : number of calls in each file
  same_x               : number of calls where the input point is identical in both files
  distinct_shape_ptr_a : distinct shape pointers in file A (index = shape ordinal)
  distinct_shape_ptr_b : distinct shape pointers in file B
  n_nvec_different     : calls whose returned normal differs (text compare of the two numbers)
  max_nvec_angle_deg   : largest angle between the two normals over the calls (degrees)
Usage: python3 -I -B testing/d003/stage_s3r2/nvec_compare.py FILE_A FILE_B
No pass/fail judgement is made here.
"""
import math
import re
import sys

ENTER = re.compile(r"SGN_ENTER k=(\d+) shape_ptr=(0x[0-9a-fA-F]+) x=([^,]+),([^\s]+)")
RET = re.compile(r"SGN_RET nvec=([^,]+),(\S+)")


def load(path):
    enters = []
    rets = []
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for ln in fh:
            m = ENTER.search(ln)
            if m:
                enters.append((m.group(2), float(m.group(3)), float(m.group(4)), m.group(0)))
                continue
            m = RET.search(ln)
            if m:
                rets.append((float(m.group(1)), float(m.group(2)), m.group(0)))
    return enters, rets


def main():
    if len(sys.argv) != 3:
        sys.stderr.write("usage: nvec_compare.py FILE_A FILE_B\n")
        return 2
    ea, ra = load(sys.argv[1])
    eb, rb = load(sys.argv[2])
    n = min(len(ea), len(eb), len(ra), len(rb))
    same_x = 0
    n_diff = 0
    max_angle = 0.0
    for i in range(n):
        xa = (ea[i][1], ea[i][2])
        xb = (eb[i][1], eb[i][2])
        if xa == xb:
            same_x += 1
        na = (ra[i][0], ra[i][1])
        nb = (rb[i][0], rb[i][1])
        if na != nb:
            n_diff += 1
            dot = na[0] * nb[0] + na[1] * nb[1]
            la = math.hypot(*na)
            lb = math.hypot(*nb)
            if la > 0 and lb > 0:
                c = max(-1.0, min(1.0, dot / (la * lb)))
                ang = math.degrees(math.acos(c))
                if ang > max_angle:
                    max_angle = ang
    pa = sorted(set(e[0] for e in ea))
    pb = sorted(set(e[0] for e in eb))
    print("calls_a=%d calls_b=%d compared=%d" % (len(ea), len(eb), n))
    print("same_x=%d" % same_x)
    print("distinct_shape_ptr_a=%d" % len(pa))
    print("distinct_shape_ptr_b=%d" % len(pb))
    print("n_nvec_different=%d" % n_diff)
    print("max_nvec_angle_deg=%.6f" % max_angle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
