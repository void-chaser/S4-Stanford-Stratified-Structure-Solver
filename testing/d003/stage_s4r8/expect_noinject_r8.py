#!/usr/bin/env python3
"""P05-S4 R8 M0 step 5: pre-registration of the F2<->F3 no-injection equivalence (new file).

Writes $EV/EXPECT_R8_NOINJECT.txt once (refused if it exists, U17).  The file is written BEFORE run_noinject_equiv_r8.sh is
started; its sha256 is recorded in the output of this script.  Status INFLUENCED: the expectation is informed by the
R7 result of the same matrix (RESULTS_R7_NOINJECT_run1.tsv, run1b, E7-3, U40), so it is not BLIND.

Changes against the R7 brief (recorded in ERRATA_8 E8-5): the mode "closed" of the R7 matrix is replaced by "closed2d"
(E7-3 and its addendum, U40: the driver accepts closed2d and closed1d only; the R7 run with "closed" was an input error on
both trees, and the R7 follow-up run1b with closed2d is IDENTICAL, 9/9, rc 0/0).  No other mode changes.
Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r8/expect_noinject_r8.py
"""
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
OUT = os.path.join(EV, "EXPECT_R8_NOINJECT.txt")
R7_RUN1 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7", "RESULTS_R7_NOINJECT_run1.tsv")

SQUARE = [("closed2d", 1), ("closed2d", 5), ("closed2d", 9), ("fft", 1), ("fft", 5), ("fft", 9),
          ("kottke", 1), ("kottke", 5), ("kottke", 9), ("experimental", 1), ("experimental", 5), ("experimental", 9),
          ("tensor", 1), ("tensor", 5), ("tensor", 9), ("closed1d", 1), ("closed1d", 5), ("closed1d", 9),
          ("jones", 1), ("jones", 5), ("jones", 9), ("nv", 1), ("nv", 5), ("nv", 9), ("vl", 1), ("vl", 5), ("vl", 9),
          ("fftjones", 1), ("fftjones", 5), ("fftjones", 9), ("fftnv", 1), ("fftnv", 5), ("fftnv", 9),
          ("fftvl", 1), ("fftvl", 5), ("fftvl", 9)]
TRI = [("nv", 9), ("vl", 9), ("jones", 9)]
RC_20 = {("vl", 1, "square"), ("fftvl", 1, "square")}


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: expect_noinject_r8.py")
    if os.path.exists(OUT):
        raise SystemExit("REFUSED: exists (U17): %s" % OUT)
    # the R7 record that informs the expectation is read here (read only).  Each expected rc pair must equal the R7
    # value of the same combination (closed2d rows come from run1b and are checked there); otherwise nothing is written.
    r7 = {}
    with open(R7_RUN1, encoding="utf-8") as fh:
        for raw in fh:
            f = raw.rstrip("\n").split("\t")
            if len(f) >= 8 and f[3] == "F" and f[1] in ("1", "5", "9") and f[2] in ("square", "tri"):
                r7[(f[0], int(f[1]), f[2])] = (f[4], f[5])
    for mode, ng in SQUARE:
        if mode == "closed2d":
            continue
        want = ("20", "20") if (mode, ng, "square") in RC_20 else ("0", "0")
        got = r7.get((mode, ng, "square"))
        if got != want:
            raise SystemExit("REFUSED: R7 record of %s NG%d square is %r, expectation %r" % (mode, ng, got, want))
    for mode, ng in TRI:
        got = r7.get((mode, ng, "tri"))
        if got != ("0", "0"):
            raise SystemExit("REFUSED: R7 record of %s NG%d tri is %r" % (mode, ng, got))
    lines = ["# EXPECT_R8_NOINJECT.txt -- P05-S4 R8 M0 step 5 (F2 against F3, no injection).  Status INFLUENCED.",
             "# Expectation: every call1/call2/call3 comparison IDENTICAL (byte equal); rc1 and rc2 equal on the two trees;",
             "# rc 20 for vl NG1 and fftvl NG1 on both trees (rc1 = rc2 = 20, as R7 run1).  Basis [source]: F2 to F3 changes only",
             "# failure paths (git diff a07b5ac 8d8202a -- S4/), normal return values unchanged.",
             "# Substitution: closed -> closed2d (ERRATA_8 E8-5; E7-3 and addendum U40).",
             "# R7 record read for this file: RESULTS_R7_NOINJECT_run1.tsv (sha256 of this record is not checked here).",
             "mode\tNG\tlattice\texpected_rc1\texpected_rc2\texpected_call_compare\tbasis"]
    for mode, ng in SQUARE:
        rc = "20" if (mode, ng, "square") in RC_20 else "0"
        basis = "R7 run1 (rc 20 both trees)" if rc == "20" else "R7 run1 / run1b (rc 0 both trees)"
        if mode == "closed2d":
            basis = "R7 run1b (closed2d, E7-3)"
        lines.append("%s\t%d\tsquare\t%s\t%s\tIDENTICAL\t%s" % (mode, ng, rc, rc, basis))
    for mode, ng in TRI:
        lines.append("%s\t%d\ttri\t0\t0\tIDENTICAL\tR7 run1 tri rows (rc 0 both trees)" % (mode, ng))
    lines.append("# total comparison rows: %d square x 3 calls + %d tri x 3 calls" % (len(SQUARE), len(TRI)))
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(OUT, "rb") as fh:
        digest = hashlib.sha256(fh.read()).hexdigest()
    print("expect_noinject_r8: written %s sha256=%s" % (OUT, digest))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
