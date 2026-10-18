#!/usr/bin/env python3
# calib_diff_s5r3.py -- point-by-point comparison of the S5R3 injection-free E2E calibration with the
# M3b calibration (U373). A single DIFF is a hard stop (no nth adjustment is allowed).
# Writes CALIB_DIFF_S5R3.tsv and returns 2 on any DIFF.
import os, sys, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
NEW = os.path.join(EV, "CALIB_E2E_S5R3.tsv")
REF = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3b/CALIB_E2E_R9M3B.tsv")
OUT = os.path.join(EV, "CALIB_DIFF_S5R3.tsv")
TAB = chr(9)
NL = chr(10)


def read(p):
    rows = []
    hdr = None
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return hdr, rows


def key_event(r):
    return (r["frontend"], r["spec"], r["kind"], r.get("call_seq", ""), r.get("size", ""))


def main():
    if not os.path.isfile(NEW):
        print("HARD_STOP missing " + NEW)
        return 2
    h1, a = read(NEW)
    h2, b = read(REF)
    # TARGET rows carry the point's nth and calibrated size (U373 hard requirement)
    ta = [key_event(r) for r in a if r["row_kind"] == "TARGET"]
    tb = [key_event(r) for r in b if r["row_kind"] == "TARGET"]
    ea = [key_event(r) for r in a if r["row_kind"] == "EVENT"]
    eb = [key_event(r) for r in b if r["row_kind"] == "EVENT"]
    lines = [
        "# CALIB_DIFF_S5R3.tsv -- point-by-point comparison of CALIB_E2E_S5R3.tsv against registries/s4r9/M3b/CALIB_E2E_R9M3B.tsv (U373)",
        "# key = frontend/spec/kind/call_seq/size; the invocation-free gdb calibration must agree exactly.",
        TAB.join(["row_kind", "key", "s5r3", "m3b", "diff"]),
    ]
    diffs = 0
    for kind, ja, jb in (("TARGET", ta, tb), ("EVENT", ea, eb)):
        seta, setb = set(ja), set(jb)
        for k in sorted(seta | setb):
            same = k in seta and k in setb
            if not same:
                diffs += 1
            lines.append(TAB.join([kind, "/".join(k), "present" if k in seta else "MISSING",
                                   "present" if k in setb else "MISSING", "SAME" if same else "DIFF"]))
        lines.append(TAB.join([kind, "COUNT", str(len(ja)), str(len(jb)), "SAME" if len(ja) == len(jb) else "DIFF"]))
        if len(ja) != len(jb):
            diffs += 1
    lines.append(TAB.join(["SUMMARY", "DIFFS=%d" % diffs, "", "", ""]))
    open(OUT, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("CALIB_DIFF TARGET %d/%d EVENT %d/%d DIFFS=%d" % (len(ta), len(tb), len(ea), len(eb), diffs))
    print("WROTE " + os.path.relpath(OUT, REPO))
    return 0 if diffs == 0 else 2


if __name__ == "__main__":
    sys.exit(main())
