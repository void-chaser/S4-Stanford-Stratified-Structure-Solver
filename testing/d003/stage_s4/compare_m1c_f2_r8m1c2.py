#!/usr/bin/env python3
# compare_m1c_f2_r8m1c2.py -- P05-S4 R8 M1c2 F2 comparison (brief section 6).
# Compares an R8 F2 run directory with the committed R7 F2 facts (registries/s4r7).
# Usage: python3 -I -B compare_m1c_f2_r8m1c2.py <R8_DIR_NAME_UNDER_EV> <OUT_NAME>
#   e.g. compare_m1c_f2_r8m1c2.py m1c_F2 COMPARE_M1C_F2_R8_M1c2.tsv
# Output: $EV/<OUT_NAME>; last line DIFFS=<n> GDB_DIVERGENT=<m>.
# Compared: facts (rc/hit/done, log-hash columns excluded), env_as_run (key/value set), invariants and
# point_verdict (per point id and pass), two-pass consistency (R8), control facts (CTRL_AUX and G6c).
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c2")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)

if len(sys.argv) != 3:
    print("usage: compare_m1c_f2_r8m1c2.py <R8_DIR_NAME_UNDER_EV> <OUT_NAME>")
    sys.exit(2)
R8DIR = os.path.join(EV, sys.argv[1])
OUT = os.path.join(EV, sys.argv[2])
if os.path.exists(OUT):
    print("REFUSED exists (U17): %s" % OUT)
    sys.exit(2)

STATE_FACT = ["rc_gdb", "rc_nogdb", "gdb_rc1", "gdb_rc2", "gdb_rc3", "gdb_hit", "gdb_done",
              "nogdb_rc1", "nogdb_rc2", "nogdb_rc3", "nogdb_hit", "nogdb_done"]
SEAM_FACT = ["rc_gdb", "rc_nogdb", "gdb_rc1", "gdb_rc2", "gdb_hit", "gdb_done",
             "nogdb_rc1", "nogdb_rc2", "nogdb_hit", "nogdb_done"]
INV = ["I1", "I2", "I3", "I4", "I5", "I6", "I7", "point_verdict"]


def read_rows(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def env_set(s):
    d = {}
    for kv in s.split(";"):
        if kv and not kv.startswith("S4FMM_DUMP"):
            k, _, v = kv.partition("=")
            d[k] = v
    return d


def fact_tuple(r, cols):
    return tuple(r.get(c, "") for c in cols)


lines = []
diffs = []
gdb_div = []


def emit(kind, key, status, detail=""):
    lines.append("%s\t%s\t%s\t%s" % (kind, key, status, detail))
    if status != "MATCH":
        diffs.append((kind, key, detail))


# ---- R8 reads ----
r8_s1 = read_rows(os.path.join(R8DIR, "STATE_R6c_pass1.tsv"))
r8_s2 = read_rows(os.path.join(R8DIR, "STATE_R6c_pass2.tsv"))
r8_m1 = read_rows(os.path.join(R8DIR, "STATE_SEAM_R6c_pass1.tsv"))
r8_m2 = read_rows(os.path.join(R8DIR, "STATE_SEAM_R6c_pass2.tsv"))
r8_inv_s = read_rows(os.path.join(R8DIR, "RESULTS_R6c_STATE.tsv"))
r8_inv_m = read_rows(os.path.join(R8DIR, "RESULTS_R6c_SEAM.tsv"))

# ---- R7 reads (committed) ----
r7_s1 = read_rows(os.path.join(REG, "M3_F2_STATE_R6c_pass1.tsv"))
r7_s2 = read_rows(os.path.join(REG, "M3_F2_STATE_R6c_pass2.tsv"))
r7_m1 = read_rows(os.path.join(REG, "M3_F2_STATE_SEAM_R6c_pass1.tsv"))
r7_m2 = read_rows(os.path.join(REG, "M3_F2_STATE_SEAM_R6c_pass2.tsv"))
r7_inv_s = read_rows(os.path.join(REG, "M3_F2_RESULTS_R6c_STATE.tsv"))
r7_inv_m = read_rows(os.path.join(REG, "M3_F2_RESULTS_R6c_SEAM.tsv"))


def index(rows, idcol="id"):
    d = {}
    for r in rows:
        d.setdefault(r[idcol], r)
    return d


r8_s1i, r7_s1i = index(r8_s1), index(r7_s1)
r8_s2i, r7_s2i = index(r8_s2), index(r7_s2)
r8_m1i, r7_m1i = index(r8_m1), index(r7_m1)
r8_m2i, r7_m2i = index(r8_m2), index(r7_m2)

# ---- state points: facts, env, two-pass ----
for pid in sorted(set(r7_s1i) | set(r8_s1i)):
    if pid not in r8_s1i or pid not in r7_s1i:
        emit("STATE_POINT", pid, "MISSING_IN_ONE_SIDE", "r8=%s r7=%s" % (pid in r8_s1i, pid in r7_s1i))
        continue
    a, b = r8_s1i[pid], r7_s1i[pid]
    kind = a["kind"]
    cols = STATE_FACT
    if fact_tuple(a, cols) != fact_tuple(b, cols):
        emit("STATE_FACT", pid, "DIFF", "r8=%s r7=%s" % (fact_tuple(a, cols), fact_tuple(b, cols)))
    else:
        emit("STATE_FACT", pid, "MATCH")
    if env_set(a["env_as_run"]) != env_set(b["env_as_run"]):
        emit("ENV", pid, "DIFF", "r8=%s r7=%s" % (a["env_as_run"], b["env_as_run"]))
    else:
        emit("ENV", pid, "MATCH")
    if a.get("gdb_hit") is not None and a.get("rc_gdb") != a.get("rc_nogdb"):
        gdb_div.append(pid)
    if pid in r8_s2i:
        if fact_tuple(r8_s1i[pid], cols) != fact_tuple(r8_s2i[pid], cols):
            emit("TWO_PASS_STATE", pid, "DIFF")
        else:
            emit("TWO_PASS_STATE", pid, "MATCH")
    else:
        emit("TWO_PASS_STATE", pid, "MISSING_PASS2")

# ---- seam points and controls: facts, env, two-pass ----
for pid in sorted(set(r7_m1i) | set(r8_m1i)):
    if pid not in r8_m1i or pid not in r7_m1i:
        emit("SEAM_POINT", pid, "MISSING_IN_ONE_SIDE", "r8=%s r7=%s" % (pid in r8_m1i, pid in r7_m1i))
        continue
    a, b = r8_m1i[pid], r7_m1i[pid]
    tag = "SEAM_CONTROL" if a["kind"] == "control" else "SEAM_POINT"
    if fact_tuple(a, SEAM_FACT) != fact_tuple(b, SEAM_FACT):
        emit(tag + "_FACT", pid, "DIFF", "r8=%s r7=%s" % (fact_tuple(a, SEAM_FACT), fact_tuple(b, SEAM_FACT)))
    else:
        emit(tag + "_FACT", pid, "MATCH")
    if env_set(a["env_as_run"]) != env_set(b["env_as_run"]):
        emit("ENV_SEAM", pid, "DIFF", "r8=%s r7=%s" % (a["env_as_run"], b["env_as_run"]))
    else:
        emit("ENV_SEAM", pid, "MATCH")
    if pid in r8_m2i:
        if fact_tuple(a, SEAM_FACT) != fact_tuple(r8_m2i[pid], SEAM_FACT):
            emit("TWO_PASS_SEAM", pid, "DIFF")
        else:
            emit("TWO_PASS_SEAM", pid, "MATCH")
    else:
        emit("TWO_PASS_SEAM", pid, "MISSING_PASS2")
    if a.get("rc_gdb") != a.get("rc_nogdb"):
        gdb_div.append(pid)

# ---- invariants and point_verdict (state: keyed by point_id and pass) ----
def inv_index(rows):
    d = {}
    for r in rows:
        d[(r["point_id"], r["pass"])] = tuple(r.get(c, "") for c in INV)
    return d


r8_is, r7_is = inv_index(r8_inv_s), inv_index(r7_inv_s)
r8_im, r7_im = inv_index(r8_inv_m), inv_index(r7_inv_m)
for key in sorted(set(r7_is) | set(r8_is)):
    if key not in r8_is or key not in r7_is:
        emit("INV_STATE", "%s#%s" % key, "MISSING_IN_ONE_SIDE")
    elif r8_is[key] != r7_is[key]:
        emit("INV_STATE", "%s#%s" % key, "DIFF", "r8=%s r7=%s" % (r8_is[key], r7_is[key]))
    else:
        emit("INV_STATE", "%s#%s" % key, "MATCH")
for key in sorted(set(r7_im) | set(r8_im)):
    if key not in r8_im or key not in r7_im:
        emit("INV_SEAM", "%s#%s" % key, "MISSING_IN_ONE_SIDE")
    elif r8_im[key] != r7_im[key]:
        emit("INV_SEAM", "%s#%s" % key, "DIFF", "r8=%s r7=%s" % (r8_im[key], r7_im[key]))
    else:
        emit("INV_SEAM", "%s#%s" % key, "MATCH")

# ---- the GDB_DIVERGENT count: rows whose gdb and nogdb facts disagree (rc or hit) ----
GDB_DIVERGENT = 0
for r in r8_s1 + r8_s2 + r8_m1 + r8_m2:
    if (r.get("gdb_rc1"), r.get("gdb_rc2"), r.get("gdb_hit")) != (r.get("nogdb_rc1"), r.get("nogdb_rc2"), r.get("nogdb_hit")):
        GDB_DIVERGENT += 1
    if r.get("status", "") == "GDB_DIVERGENT":
        GDB_DIVERGENT += 1

n_diff = len(diffs)
lines.append("SUMMARY\tr8_dir=%s\tr7_ref=checkpoints/p05/registries/s4r7\tcompared=%d" % (sys.argv[1], len(lines)))
lines.append("DIFFS=%d GDB_DIVERGENT=%d" % (n_diff, GDB_DIVERGENT))
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("# COMPARE_M1C_F2_R8_M1c2 -- R8 F2 (%s) vs R7 F2 (registries/s4r7).\n" % sys.argv[1])
    fh.write("kind\tkey\tstatus\tdetail\n")
    fh.write("\n".join(lines) + "\n")
print("DIFFS=%d GDB_DIVERGENT=%d" % (n_diff, GDB_DIVERGENT))
