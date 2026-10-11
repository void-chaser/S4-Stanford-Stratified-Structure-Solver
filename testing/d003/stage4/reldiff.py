#!/usr/bin/env python3
"""Per-component relative difference of two driver field dumps (P05-S2R3 stage 4, evidence only).

Input lines: "E|H index value" (the S4FMM_DUMP format, %.17g).  Definition, per component:
    rel = |a - b| / max(|a|, |b|)     (0 when both are 0)
Reports: component count, identical-bytes flag, count differing (bytewise), max rel, median rel, index of max.
"""
import sys, statistics

def load(path):
    vals = {}
    raw = open(path, 'rb').read()
    for line in raw.decode('ascii').splitlines():
        if not line.strip():
            continue
        tag, idx, v = line.split()
        vals[(tag, int(idx))] = float(v)
    return raw, vals

def main(a_path, b_path):
    raw_a, a = load(a_path)
    raw_b, b = load(b_path)
    if set(a) != set(b):
        raise SystemExit("key sets differ")
    keys = sorted(a)
    rels = []
    n_bytes_diff = 0
    for k in keys:
        x, y = a[k], b[k]
        if x != y:
            n_bytes_diff += 1
        m = max(abs(x), abs(y))
        rels.append(0.0 if m == 0.0 else abs(x - y) / m)
    mx = max(rels)
    k_mx = keys[rels.index(mx)]
    med = statistics.median(rels)
    print("components=%d  files_byte_identical=%s  components_differing=%d" % (
        len(keys), raw_a == raw_b, n_bytes_diff))
    print("max_rel=%.4e (at %s)  median_rel=%.4e" % (mx, k_mx, med))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
