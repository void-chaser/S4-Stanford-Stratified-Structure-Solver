#!/usr/bin/env python3
# report_facts_r8m1a5.py -- read-only tallies for the CONT3b1 report (callseq_status distribution, K sources, counts).  New file.
# Writes REPORT_FACTS_R8_M1a5.txt to the evidence directory.  It changes no committed file.
import os, sys
from collections import Counter

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a5")
M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")


def rows_of(path):
    with open(path, encoding="utf-8", newline="") as fh:
        lines = [l.rstrip("\n") for l in fh if not l.startswith("#") and l.strip() != ""]
    header = lines[0].split("\t")
    return [dict(zip(header, l.split("\t"))) for l in lines[1:] if len(l.split("\t")) == len(header)]


out = []
req = rows_of(os.path.join(M1A, "REQUEST_TARGETS_R8_M1a4AUDIT3.tsv"))
cs = rows_of(os.path.join(M1A, "CALLSEQ_F2_F3_R8_M1a4_R2.tsv"))
ks = rows_of(os.path.join(M1A, "K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv"))
out.append("REQUEST_ROWS\t%d" % len(req))
out.append("REQUEST_STATUS\t%s" % sorted(Counter(r["status"] for r in req).items()))
out.append("REQUEST_TREE_STATUS\t%s" % sorted(Counter((r["source_tree"], r["status"]) for r in req).items()))
out.append("CALLSEQ_PAIRS\t%d\tSTATUS\t%s" % (len(cs), sorted(Counter(r["status"] for r in cs).items())))
out.append("CALLSEQ_DRIVER_FAMILY\t%s" % sorted(Counter(r["driver_family"] for r in cs).items()))
out.append("K_SOURCE_STATUS\t%s" % sorted(Counter(r["status"] for r in ks).items()))
out.append("K_SOURCE_ROWS\t%d" % len(ks))
dst = os.path.join(EV, "REPORT_FACTS_R8_M1a5.txt")
if os.path.exists(dst):
    sys.exit("report_facts: exists (U17): " + dst)
with open(dst, "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
sys.stdout.write("\n".join(out) + "\n")
