#!/usr/bin/env python3
"""P05-S1R2 J3 index statistics (read-only, stdout only).

For each gdb trace of the J3 probe, converts every shape_get_normal argument pointer into a
shape index: index = (pointer - shapes_base) / sizeof(shape).  shapes_base and the element size
are taken from the trace itself (the 'J3 SHAPE' lines give the addresses of shapes[0..n-1];
the element size is their difference).  Reports the set of indices and the call count, and
whether every index lies in [0, nshapes-1].

Usage: python3 -I -B testing/d003/stage_s1r2/shape_index_stats.py EV_J3_RUNS_DIR
"""
import os
import re
import sys

SGN_RE = re.compile(r"SGN k=(\d+) shape_ptr=0x([0-9a-fA-F]+)")
SHAPE_RE = re.compile(r"J3 SHAPE k=(\d+) addr=0x([0-9a-fA-F]+) tag=(-?\d+)")
LAYER_RE = re.compile(r"J3 LAYER slab_index=(\d+) nshapes=(\d+) shapes_base=0x([0-9a-fA-F]+)")


def analyse(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    layer = LAYER_RE.search(text)
    if not layer:
        return None
    nshapes = int(layer.group(2))
    base = int(layer.group(3), 16)
    addrs = [int(m.group(2), 16) for m in SHAPE_RE.finditer(text)]
    if len(addrs) >= 2:
        stride = addrs[1] - addrs[0]
    else:
        stride = None
    calls = [int(m.group(2), 16) for m in SGN_RE.finditer(text)]
    idx = []
    bad = 0
    for p in calls:
        if stride is None:
            # One shape: no second address to derive the stride.  A pointer equal to the base is
            # index 0 (the only element).  Any other value cannot be mapped (counted as unmapped).
            if p == base:
                idx.append(0)
            else:
                bad += 1
                idx.append(None)
            continue
        if stride <= 0:
            idx.append(None)
            continue
        off = p - base
        if off < 0 or off % stride != 0:
            bad += 1
            idx.append(None)
            continue
        idx.append(off // stride)
    known = [i for i in idx if i is not None]
    distinct = sorted(set(known))
    in_range = all(0 <= i <= nshapes - 1 for i in known) if known else False
    return {
        "nshapes": nshapes,
        "stride": stride if stride is not None else "NA",
        "calls": len(calls),
        "distinct_indices": ",".join(str(i) for i in distinct) if distinct else "NONE",
        "unmapped_pointers": bad,
        "all_in_range": "YES" if (in_range and bad == 0) else "NO",
    }


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("usage: shape_index_stats.py EV_J3_RUNS_DIR\n")
        return 2
    d = sys.argv[1]
    names = sorted(f for f in os.listdir(d) if f.startswith("trace-") and f.endswith(".txt"))
    print("\t".join(["trace", "nshapes", "stride_bytes", "shape_get_normal_calls",
                     "distinct_indices", "unmapped_pointers", "all_in_range"]))
    for fn in names:
        r = analyse(os.path.join(d, fn))
        tag = fn[len("trace-"):-len(".txt")]
        if r is None:
            print("\t".join([tag, "NA", "NA", "NA", "NA", "NA", "NA"]))
            continue
        print("\t".join([tag, str(r["nshapes"]), str(r["stride"]), str(r["calls"]),
                         r["distinct_indices"], str(r["unmapped_pointers"]), r["all_in_range"]]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
