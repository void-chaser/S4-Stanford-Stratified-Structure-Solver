#!/usr/bin/env python3
# count_r7_f2_facts_r8m1c2_R2.py -- R2 of the R7 F2 fact recount (P05-S4 R8 M1c2).
# Supersedes count_r7_f2_facts_r8m1c2.py (not overwritten, U17).  Reason: the first version compared
# pass1 and pass2 as whole rows, which includes gdb_log_sha256 / nogdb_log_sha256 (log-file hashes that
# differ between passes).  Freezing rule (brief section 4) compares the FACT columns only.
# Reads only registries/s4r7/M3_F2_STATE_R6c_pass{1,2}.tsv and M3_F2_STATE_SEAM_R6c_pass{1,2}.tsv.
# Writes $EV/R7_F2_FACT_DIST_R8_M1c2_R2.tsv (key<TAB>count) and a per-row pass comparison.
# Usage: python3 -I -B count_r7_f2_facts_r8m1c2_R2.py
import os

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c2")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)

FACT_COLS = ["gdb_rc1", "gdb_rc2", "gdb_rc3", "gdb_hit", "gdb_done",
             "nogdb_rc1", "nogdb_rc2", "nogdb_rc3", "nogdb_hit", "nogdb_done", "rc_gdb", "rc_nogdb"]
SEAM_FACT_COLS = ["gdb_rc1", "gdb_rc2", "gdb_hit", "gdb_done", "nogdb_rc1", "nogdb_rc2", "nogdb_hit", "nogdb_done",
                  "rc_gdb", "rc_nogdb"]


def read_table(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def key_of(r, seam):
    kind = r["kind"]
    g = ("G6" if seam else "G5") if kind == "point" else ("G6c" if seam else "G5")
    rc1, rc2, hit = r["gdb_rc1"], r["gdb_rc2"], r["gdb_hit"]
    if kind == "point":
        if rc1 == "20" and rc2 == "0" and hit == "1":
            return "%s_rc1_20_rc2_0_hit1" % g
        if rc1 == "0" and rc2 == "20" and hit == "1":
            return "%s_rc1_0_rc2_20_hit1" % g
        return "%s_point_OTHER" % g
    if rc1 == "0" and rc2 == "0" and hit == "0":
        return "%s_control_zero" % g
    return "%s_control_OTHER" % g


def facts(r, cols):
    return tuple(r.get(c, "") for c in cols)


def compare_passes(a, b, cols):
    if len(a) != len(b):
        return False, "rows %d != %d" % (len(a), len(b))
    diffs = [i for i, (x, y) in enumerate(zip(a, b)) if facts(x, cols) != facts(y, cols)]
    return (not diffs), ("fact-column diffs at rows %s" % diffs[:10] if diffs else "all rows equal on fact columns")


p1 = read_table(os.path.join(REG, "M3_F2_STATE_R6c_pass1.tsv"))
p2 = read_table(os.path.join(REG, "M3_F2_STATE_R6c_pass2.tsv"))
s1 = read_table(os.path.join(REG, "M3_F2_STATE_SEAM_R6c_pass1.tsv"))
s2 = read_table(os.path.join(REG, "M3_F2_STATE_SEAM_R6c_pass2.tsv"))

ok_state, msg_state = compare_passes(p1, p2, FACT_COLS)
ok_seam, msg_seam = compare_passes(s1, s2, SEAM_FACT_COLS)

dist = {}
for r in p1:
    k = key_of(r, False)
    dist[k] = dist.get(k, 0) + 1
for r in s1:
    k = key_of(r, True)
    dist[k] = dist.get(k, 0) + 1

out = os.path.join(EV, "R7_F2_FACT_DIST_R8_M1c2_R2.tsv")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("key\tcount\n")
    for k in sorted(dist):
        fh.write("%s\t%d\n" % (k, dist[k]))
    fh.write("STATE_PASS1_EQ_PASS2_ON_FACT_COLUMNS\t%s\t%s\n" % (ok_state, msg_state))
    fh.write("SEAM_PASS1_EQ_PASS2_ON_FACT_COLUMNS\t%s\t%s\n" % (ok_seam, msg_seam))
    fh.write("ROWS_STATE_PASS1\t%d\n" % len(p1))
    fh.write("ROWS_SEAM_PASS1\t%d\n" % len(s1))
for k in sorted(dist):
    print("%s\t%d" % (k, dist[k]))
print("STATE_PASS1_EQ_PASS2_ON_FACT_COLUMNS=%s (%s)" % (ok_state, msg_state))
print("SEAM_PASS1_EQ_PASS2_ON_FACT_COLUMNS=%s (%s)" % (ok_seam, msg_seam))
print("OUT=%s" % out)
