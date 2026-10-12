#!/usr/bin/env python3
"""P05-S4 R7 part 1 (section 2 item 2): summarise the existing run1b no-injection outputs (new file).

Read only.  Does NOT run any driver.  For each (mode, NG) in run1b, compares call1/2/3.txt of F and F2 with cmp
(Python filecmp, byte-for-byte) and parses "RC first" / "RC retry" from stdout.txt of both trees.
Output: argv[1] = the result file to create (must not exist; U17).  Usage:
  python3 -I -B testing/d003/stage_s4r7/summarize_noinject_run1b_r7.py EVDIR/RESULTS_R7_NOINJECT_run1b.tsv
Run through safe_run so that the single write goes to $EV.
"""
import filecmp
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7")
ROOT = os.path.join(EV, "noinject_r7", "run1b")
RE_RC1 = re.compile(r"^RC first (-*\d+)\s*$", re.M)
RE_RC2 = re.compile(r"^RC retry (-*\d+)\s*$", re.M)


def rc_of(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    m1, m2 = RE_RC1.search(text), RE_RC2.search(text)
    return (m1.group(1) if m1 else "NA", m2.group(1) if m2 else "NA")


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: summarize_noinject_run1b_r7.py OUT.tsv")
    out = argv[1]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    rows = []
    n_ident = n_bad = 0
    for mode in ("closed2d",):
        for ng in (1, 5, 9):
            d = "%s-ng%d-square" % (mode, ng)
            rf = {}
            rr = {}
            for t in ("F", "F2"):
                p = os.path.join(ROOT, t, d, "stdout.txt")
                rf[t], rr[t] = rc_of(p)
            for f in ("call1.txt", "call2.txt", "call3.txt"):
                a = os.path.join(ROOT, "F", d, f)
                b = os.path.join(ROOT, "F2", d, f)
                same = os.path.isfile(a) and os.path.isfile(b) and filecmp.cmp(a, b, shallow=False)
                n_ident += 1 if same else 0
                n_bad += 0 if same else 1
                rows.append([mode, str(ng), "square", f, rf["F"], rr["F"], rf["F2"], rr["F2"],
                             "IDENTICAL" if same else "NOT_IDENTICAL_OR_MISSING"])
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# RESULTS_R7_NOINJECT_run1b -- closed2d follow-up of run1 (E7-3, U40).  Read-only summary of existing outputs.\n")
        fh.write("mode\tNG\tlattice\tfile\tF_rc_first\tF_rc_retry\tF2_rc_first\tF2_rc_retry\tcmp\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
        fh.write("# summary: IDENTICAL=%d NOT_IDENTICAL_OR_MISSING=%d\n" % (n_ident, n_bad))
    print("rows=%d identical=%d bad=%d -> %s" % (len(rows), n_ident, n_bad, out))
    return 0 if n_bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
