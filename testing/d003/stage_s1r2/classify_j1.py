#!/usr/bin/env python3
"""P05-S1R2 J1 classifier (read-only).

Reads the gdb probe outputs written by the J1 matrix runner and classifies, for each
(tree, chain, injection) cell, the state of the matrix (Epsilon_inv and the four
Epsilon2 blocks) at the return of FMMGetEpsilon_PolBasis*, relative to the entry state.

Usage:  python3 -I -B testing/d003/stage_s1r2/classify_j1.py EVJ1_DIR > OUT.tsv

Block states (each block compares its first 4 complex values, read from the gdb dump):
  SAME    returned block equals entry block (FFT value kept)
  NEW     returned block differs from entry block (PolBasis wrote it)
  NA      no return state (process crashed before return)

Matrix state:
  FFT_ORIGINAL  every compared block SAME
  NEW_VALUES    every compared block NEW
  MIXED         some SAME and some NEW
  NO_RETURN     the probe did not reach PB_RETURN (crash)

The classifier never writes outside the directory given on the command line (stdout only).
It does not read the driver's PASS/FAIL line; it reads only the raw numbers in the gdb dump.
"""
import os
import re
import sys

BLOCKS = ["inv", "E2_blk00", "E2_blk10", "E2_blk01", "E2_blk11"]
NUM_RE = re.compile(r"^0x[0-9a-f]+:\t(.*)$")


def read_section(lines, start_tag, end_tags):
    """Return the list of numeric pairs printed after start_tag until an end tag."""
    out = []
    active = False
    for ln in lines:
        s = ln.rstrip("\n")
        if s.startswith(start_tag):
            active = True
            continue
        if active and any(s.startswith(t) for t in end_tags):
            break
        if active:
            m = NUM_RE.match(s)
            if m:
                out.extend(m.group(1).split("\t"))
    return out


def parse(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    entry = {}
    ret = {}
    tags_entry = ["PB_ENTRY inv_first4", "PB_ENTRY E2_blk00_first4", "PB_ENTRY E2_blk10_first4",
                  "PB_ENTRY E2_blk01_first4", "PB_ENTRY E2_blk11_first4"]
    tags_ret = ["PB_RETURN inv_first4", "PB_RETURN E2_blk00_first4", "PB_RETURN E2_blk10_first4",
                "PB_RETURN E2_blk01_first4", "PB_RETURN E2_blk11_first4"]
    all_tags = tags_entry + tags_ret + ["PB_RETURN eax=", "PB_ENTRY n=", "Program received signal"]
    for name, tag in zip(BLOCKS, tags_entry):
        entry[name] = read_section(lines, tag, [t for t in all_tags if t != tag])
    got_return = any(ln.startswith("PB_RETURN eax=") for ln in lines)
    for name, tag in zip(BLOCKS, tags_ret):
        ret[name] = read_section(lines, tag, [t for t in all_tags if t != tag])
    eax = None
    for ln in lines:
        if ln.startswith("PB_RETURN eax="):
            eax = ln.strip().split("=", 1)[1]
            break
    signal = None
    for ln in lines:
        if "Program received signal" in ln:
            signal = ln.strip()
            break
    return entry, ret, got_return, eax, signal


def classify(entry, ret, got_return, signal=None):
    # A SIGSEGV inside PolBasis is not a normal return: gdb's 'finish' still prints a
    # PB_RETURN block, but its eax and the memory it reads are not the result of a return.
    # Such a cell is CRASHED, whatever the block comparison says (revision v3; v2 had
    # classified these as FFT_ORIGINAL, see the report).
    if signal:
        return "CRASHED", {n: "NA" for n in BLOCKS}
    if not got_return:
        return "NO_RETURN", {n: "NA" for n in BLOCKS}
    states = {}
    for name in BLOCKS:
        e, r = entry.get(name, []), ret.get(name, [])
        if not e or not r:
            states[name] = "NA"
        elif e[:8] == r[:8]:
            states[name] = "SAME"
        else:
            states[name] = "NEW"
    # Epsilon2 blocks decide the matrix state.  Epsilon_inv is reported separately: PolBasis
    # does not write it (source comment: "we do not modify it").  A first version that also
    # counted Epsilon_inv reported MIXED on the normal path; that was a classifier error (see
    # the revision record in the report).
    vals = [states[n] for n in BLOCKS if n != "inv" and states[n] != "NA"]
    if not vals:
        return "NO_RETURN", states
    if all(v == "SAME" for v in vals):
        return "FFT_ORIGINAL", states
    if all(v == "NEW" for v in vals):
        return "NEW_VALUES", states
    return "MIXED", states


def main():
    if len(sys.argv) != 2:
        sys.stderr.write("usage: classify_j1.py EVJ1_DIR\n")
        return 2
    d = sys.argv[1]
    names = sorted(f for f in os.listdir(d) if f.startswith("gdb-") and f.endswith(".txt"))
    print("tree\tchain\tinjection\tmatrix_state\tinv\tE2_blk00\tE2_blk10\tE2_blk01\tE2_blk11\teax_at_return\tsignal")
    for fn in names:
        core = fn[len("gdb-"):-len(".txt")]
        tree, chain, inj = core.split("-", 2)
        entry, ret, got, eax, sig = parse(os.path.join(d, fn))
        state, per = classify(entry, ret, got, sig)
        print("\t".join([tree, chain, inj, state] + [per[n] for n in BLOCKS] + [eax or "NA", sig or "none"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
