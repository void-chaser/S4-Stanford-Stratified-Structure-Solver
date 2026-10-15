#!/usr/bin/env python3
# count_r7_f2_facts_r8m1c2.py -- recount the R7 F2 fact distribution from the committed tables (P05-S4 R8 M1c2).
# Reads only registries/s4r7/M3_F2_STATE_R6c_pass{1,2}.tsv and M3_F2_STATE_SEAM_R6c_pass{1,2}.tsv.
# Writes $EV/R7_F2_FACT_DIST_R8_M1c2.tsv with key<TAB>count.  Also checks pass1 == pass2.
# Usage: python3 -I -B count_r7_f2_facts_r8m1c2.py
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c2")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)


def read_table(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    rows = [dict(zip(head, l.split("\t"))) for l in lines[1:]]
    return rows


def key_of(r, seam):
    kind = r["kind"]
    if kind == "point":
        g = "G6" if seam else "G5"
        rc1, rc2, hit = r["gdb_rc1"], r["gdb_rc2"], r["gdb_hit"]
        if rc1 == "20" and rc2 == "0" and hit == "1":
            return "%s_rc1_20_rc2_0_hit1" % g
        if rc1 == "0" and rc2 == "20" and hit == "1":
            return "%s_rc1_0_rc2_20_hit1" % g
        return "%s_point_OTHER" % g
    if kind == "control":
        rc1, rc2, hit = r["gdb_rc1"], r["gdb_rc2"], r["gdb_hit"]
        g = "G6c" if seam else "G5"
        if rc1 == "0" and rc2 == "0" and hit == "0":
            return "%s_control_zero" % g
        return "%s_control_OTHER" % g
    return "UNKNOWN_KIND_%s" % kind


def dist(rows, seam):
    d = {}
    for r in rows:
        k = key_of(r, seam)
        d[k] = d.get(k, 0) + 1
    return d


p1 = read_table(os.path.join(REG, "M3_F2_STATE_R6c_pass1.tsv"))
p2 = read_table(os.path.join(REG, "M3_F2_STATE_R6c_pass2.tsv"))
s1 = read_table(os.path.join(REG, "M3_F2_STATE_SEAM_R6c_pass1.tsv"))
s2 = read_table(os.path.join(REG, "M3_F2_STATE_SEAM_R6c_pass2.tsv"))
# the seam tables use different column names; map them to the shared key schema
def norm_seam(rows):
    out = []
    for r in rows:
        out.append({"kind": r["kind"], "gdb_rc1": r["gdb_rc1"], "gdb_rc2": r["gdb_rc2"], "gdb_hit": r["gdb_hit"]})
    return out

d_state = dist(p1, False)
d_seam = dist(norm_seam(s1), True)
same_state = p1 == p2
same_seam = s1 == s2
combined = {}
for k, v in d_state.items():
    combined[k] = combined.get(k, 0) + v
for k, v in d_seam.items():
    combined[k] = combined.get(k, 0) + v

out = os.path.join(EV, "R7_F2_FACT_DIST_R8_M1c2.tsv")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("key\tcount\n")
    for k in sorted(combined):
        fh.write("%s\t%d\n" % (k, combined[k]))
    fh.write("PASS1_EQ_PASS2_STATE\t%s\n" % same_state)
    fh.write("PASS1_EQ_PASS2_SEAM\t%s\n" % same_seam)
    fh.write("ROWS_STATE_PASS1\t%d\n" % len(p1))
    fh.write("ROWS_SEAM_PASS1\t%d\n" % len(s1))
for k in sorted(combined):
    print("%s\t%d" % (k, combined[k]))
print("PASS1_EQ_PASS2_STATE=%s" % same_state)
print("PASS1_EQ_PASS2_SEAM=%s" % same_seam)
print("OUT=%s" % out)
