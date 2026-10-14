#!/usr/bin/env python3
# check_facts_r8m1a5.py -- read-only check of the facts that rulings U193, U196 and U197 depend on (CONT3b1).  New file.
# Writes FACTS_R8_M1a5.txt to the evidence directory.  It changes no committed file.
import os, re, sys
from collections import Counter

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a5")
R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")


def rows_of(path):
    with open(path, encoding="utf-8", newline="") as fh:
        lines = [l.rstrip("\n") for l in fh if not l.startswith("#") and l.strip() != ""]
    header = lines[0].split("\t")
    out = []
    for l in lines[1:]:
        c = l.split("\t")
        if len(c) == len(header):
            out.append(dict(zip(header, c)))
    return out


out = []
def w(s):
    out.append(s)

# ---- U193: PLANCALL points in the G5-F2 K-source (U189 EVIDENCE_INSUFFICIENT) and the S4FMM_INJECT of the two STATE passes
ks = rows_of(os.path.join(M1A, "K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv"))
ev_ins = [r for r in ks if r["status"] == "EVIDENCE_INSUFFICIENT"]
w("U193_EVIDENCE_INSUFFICIENT_POINTS\t%d" % len(ev_ins))
req = rows_of(os.path.join(M1A, "REQUEST_TARGETS_R8_M1a4AUDIT3.tsv"))
w("U193_KIND_COUNTS\t%s" % sorted(Counter(r["kind"] for r in req).items()))
# U193 denominator: the EVIDENCE_INSUFFICIENT points of the G5-F2 K source; their request text is taken from the F2 request row
# of the same base point (K_SOURCE point_id has no tree suffix; request rows carry the suffix -F2).
def base(pid):
    return re.sub(r"-F2?$", "", pid)
req_f2_by_pid = {}
for r in req:
    # match on the exact point_id (the K source and the request rows use the same id, including the -F suffix)
    if r["source_tree"] == "F2":
        req_f2_by_pid.setdefault(r["point_id"], []).append(r)
pl = []
for r in ev_ins:
    cands = req_f2_by_pid.get(r["point_id"], [])
    if len(cands) == 1:
        pl.append(cands[0])
    else:
        pl.append({"point_id": r["point_id"], "request_raw": "NO_UNIQUE_REQUEST_ROW(%d)" % len(cands), "kind": "?"})
w("U193_DENOMINATOR_EVIDENCE_INSUFFICIENT_WITH_F2_REQUEST\t%d" % len(pl))

def state_inject(path):
    res = {}
    with open(path, encoding="utf-8") as fh:
        for l in fh:
            if not l.startswith("point\t"):
                continue
            c = l.rstrip("\n").split("\t")
            pid = c[1]
            envs = c[7]
            m = re.search(r"S4FMM_INJECT=([^;]*)", envs)
            res[pid] = m.group(1) if m else None
    return res

p1 = state_inject(os.path.join(R7, "M3_F2_STATE_R6c_pass1.tsv"))
p2 = state_inject(os.path.join(R7, "M3_F2_STATE_R6c_pass2.tsv"))
w("U193_STATE_PASS1_POINTS\t%d\tPASS2_POINTS\t%d" % (len(p1), len(p2)))

agree = 0
disagree = []
for r in pl:
    m = re.match(r"plancall:(\d+):(\d+)$", r["request_raw"])
    if not m:
        disagree.append((r["point_id"], "request_unparsed", r["request_raw"]))
        continue
    want = "plancall:%s:%s" % (m.group(1), m.group(2))
    # STATE keys are the full ids (M2 series keep the -F suffix, G5 ids have none); look up the exact request point_id
    a = p1.get(r["point_id"], p1.get(base(r["point_id"])))
    b = p2.get(r["point_id"], p2.get(base(r["point_id"])))
    if a == want and b == want:
        agree += 1
    else:
        disagree.append((r["point_id"], want, "%s|%s" % (a, b)))
w("U193_PLANCALL_AGREE\t%d\tDISAGREE_OR_MISSING\t%d" % (agree, len(disagree)))
for d in disagree[:20]:
    w("U193_DIS\t%s" % "\t".join(d))

# ---- U196(a): unit ids of REQUEST_TARGETS F2 and F3 rows must each map to exactly one CALLSEQ pair with status IDENTICAL
cs = rows_of(os.path.join(M1A, "CALLSEQ_F2_F3_R8_M1a4_R2.tsv"))
pair_f2 = {}
pair_f3 = {}
for r in cs:
    pair_f2.setdefault(r["unit_f2"], []).append(r)
    pair_f3.setdefault(r["unit_f3"], []).append(r)
units_f2 = {r["unit_id"] for r in req if r["source_tree"] == "F2"}
units_f3 = {r["unit_id"] for r in req if r["source_tree"] == "F3"}
w("U196_CALLSEQ_PAIRS\t%d\tSTATUS\t%s" % (len(cs), sorted(Counter(r["status"] for r in cs).items())))
w("U196_REQ_UNITS_F2\t%d\tF3\t%d" % (len(units_f2), len(units_f3)))
w("U196_REQ_F3_ROWS\t%d" % sum(1 for r in req if r["source_tree"] == "F3"))

sys.stdout.write("\n".join(out) + "\n")
dst = os.path.join(EV, "FACTS_R8_M1a5_R5.txt")
if os.path.exists(dst):
    sys.exit("check_facts: exists (U17): " + dst)
with open(dst, "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
