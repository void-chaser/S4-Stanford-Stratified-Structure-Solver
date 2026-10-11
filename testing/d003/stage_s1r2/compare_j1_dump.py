#!/usr/bin/env python3
"""P05-S1R2 J1 full-matrix comparison (read-only, stdout only).

Compares the binary dumps written by the J1 dump runner (entry and return state of
FMMGetEpsilon_PolBasis* for each (tree, chain, injection) cell) element by element over the
whole matrix, not only the first values:

  Epsilon2  : n2 x n2 complex (n2 = 2n), column-major as in the source; compared in full
  Epsilon_inv: n x n complex, compared in full

Per cell it reports, for Epsilon2:
  n_total      number of complex entries
  n_same       entries identical at entry and return (bitwise on the 8-byte doubles)
  n_changed    entries that differ
  block_states per quadrant (00, 10, 01, 11): SAME if all n*n entries equal, NEW if all differ,
               MIXED if some differ, NA if no return dump
and the Epsilon_inv comparison (same fields).

Matrix state (Epsilon2): FFT_ORIGINAL if n_changed == 0; NEW_VALUES if every quadrant is NEW;
MIXED if some changed and some not; NO_RETURN if no return dump.

Usage: python3 -I -B testing/d003/stage_s1r2/compare_j1_dump.py EV_J1_DUMP_DIR
"""
import os
import struct
import sys


def load(path, count):
    with open(path, "rb") as fh:
        data = fh.read()
    if len(data) != count * 16:
        return None
    vals = struct.unpack("<%dd" % (2 * count), data)
    return [(vals[2 * i], vals[2 * i + 1]) for i in range(count)]


def quadrant_state(e2_in, e2_out, n, n2, qr, qc):
    diff = 0
    total = 0
    for j in range(n):
        for i in range(n):
            idx = (qr + i) + (qc + j) * n2
            total += 1
            if e2_in[idx] != e2_out[idx]:
                diff += 1
    if diff == 0:
        return "SAME", diff, total
    if diff == total:
        return "NEW", diff, total
    return "MIXED", diff, total


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("usage: compare_j1_dump.py EV_J1_DUMP_DIR\n")
        return 2
    base = sys.argv[1]
    cells = sorted(d for d in os.listdir(base) if os.path.isdir(os.path.join(base, d)))
    print("\t".join(["tree", "chain", "injection", "E2_state", "E2_changed", "E2_total",
                     "Q00", "Q10", "Q01", "Q11", "INV_state", "INV_changed", "INV_total", "return_eax"]))
    for cell in cells:
        parts = cell.split("-", 2)
        if len(parts) != 3:
            continue
        tree, chain, inj = parts
        # n is fixed by the probe (NB=9, n_G=9): Epsilon_inv is n x n = 9 x 9, Epsilon2 is 18 x 18
        n = 9
        n2 = 2 * n
        d = os.path.join(base, cell)
        e2_in = load(os.path.join(d, "entry_E2.bin"), n2 * n2)
        inv_in = load(os.path.join(d, "entry_INV.bin"), n * n)
        e2_out = load(os.path.join(d, "return_E2.bin"), n2 * n2)
        inv_out = load(os.path.join(d, "return_INV.bin"), n * n)
        eax = "NA"
        gdbf = os.path.join(base, "gdb-dump-%s.txt" % cell)
        if os.path.exists(gdbf):
            with open(gdbf, "r", encoding="utf-8", errors="replace") as fh:
                for ln in fh:
                    if ln.startswith("DUMP_RETURN eax="):
                        eax = ln.strip().split("=", 1)[1]
        crashed = False
        if os.path.exists(gdbf):
            with open(gdbf, "r", encoding="utf-8", errors="replace") as fh:
                crashed = any("Program received signal" in ln for ln in fh)
        if e2_in is None or e2_out is None:
            print("\t".join([tree, chain, inj, "NO_RETURN", "NA", str(n2 * n2), "NA", "NA", "NA", "NA",
                             "NA", "NA", str(n * n), eax]))
            continue
        changed = sum(1 for a, b in zip(e2_in, e2_out) if a != b)
        qs = {}
        for name, (qr, qc) in (("Q00", (0, 0)), ("Q10", (n, 0)), ("Q01", (0, n)), ("Q11", (n, n))):
            qs[name] = quadrant_state(e2_in, e2_out, n, n2, qr, qc)[0]
        if crashed:
            # SIGSEGV inside PolBasis: the 'return' dump is not a normal return (see classify_j1.py).
            e2_state = "CRASHED"
        elif changed == 0:
            e2_state = "FFT_ORIGINAL"
        elif all(v == "NEW" for v in qs.values()):
            e2_state = "NEW_VALUES"
        else:
            e2_state = "MIXED"
        inv_changed = sum(1 for a, b in zip(inv_in, inv_out) if a != b) if (inv_in and inv_out) else -1
        inv_state = "UNCHANGED" if inv_changed == 0 else ("CHANGED" if inv_changed > 0 else "NA")
        print("\t".join([tree, chain, inj, e2_state, str(changed), str(n2 * n2),
                         qs["Q00"], qs["Q10"], qs["Q01"], qs["Q11"],
                         inv_state, str(inv_changed), str(n * n), eax]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
