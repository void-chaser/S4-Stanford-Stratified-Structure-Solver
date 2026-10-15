#!/usr/bin/env python3
# compare_m1c_f3_r8m1c3.py -- P05-S4 R8 M1c3 F3 comparison (brief section 6.1). New file.
# Usage: python3 -I -B compare_m1c_f3_r8m1c3.py <R8_DIR_NAME_UNDER_EV> <F2_SOURCE> <OUT_PREFIX>
#   e.g. compare_m1c_f3_r8m1c3.py m1c_F3 REG COMPARE_M1C_F3_R8_M1c3
#   F2_SOURCE = REG means the committed copies registries/s4r8/M1c/r8m1c2/M1C_F2_* (read-only).
# Outputs: $EV/<OUT_PREFIX>_VS_FROZEN... is written as COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv
#          and F2_F3_DIFF_M1C_R8_M1c3.tsv.  Last line of each: DIFFS=<n> GDB_DIVERGENT=<m>.
# Frozen side: registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv (F3 rows, 236).
# Comparison items vs frozen: facts (rc1, rc2, rc3, hit; gdb and nogdb sides; log-hash excluded),
#   env_as_run vs env_expected (S4FMM_DUMP* removed), point_verdict, I1-I6 (I1..I6 skipped where expected is '-').
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c2")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)

if len(sys.argv) != 4:
    print("usage: compare_m1c_f3_r8m1c3.py <R8_DIR_NAME_UNDER_EV> <F2_SOURCE> <OUT_PREFIX>")
    sys.exit(2)
R8DIR = os.path.join(EV, sys.argv[1])
F2SRC = sys.argv[2]
PREFIX = sys.argv[3]
if F2SRC != "REG":
    print("REFUSED F2_SOURCE must be REG (committed copies only)")
    sys.exit(2)
OUT_FROZEN = os.path.join(EV, "COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv")
OUT_F2 = os.path.join(EV, "F2_F3_DIFF_M1C_R8_M1c3.tsv")
for p in (OUT_FROZEN, OUT_F2):
    if os.path.exists(p):
        print("REFUSED exists (U17): %s" % p)
        sys.exit(2)

FACT_COLS = ["rc1", "rc2", "rc3", "hit"]  # frozen columns (expected); facts compare against the F3 run
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


# ---- F3 run (R8) ----
f3_s1 = read_rows(os.path.join(R8DIR, "STATE_R6c_pass1.tsv"))
f3_s2 = read_rows(os.path.join(R8DIR, "STATE_R6c_pass2.tsv"))
f3_m1 = read_rows(os.path.join(R8DIR, "STATE_SEAM_R6c_pass1.tsv"))
f3_m2 = read_rows(os.path.join(R8DIR, "STATE_SEAM_R6c_pass2.tsv"))
f3_inv_s = read_rows(os.path.join(R8DIR, "RESULTS_R6c_STATE.tsv"))
f3_inv_m = read_rows(os.path.join(R8DIR, "RESULTS_R6c_SEAM.tsv"))

# ---- F2 committed copies (read-only) ----
f2_s1 = read_rows(os.path.join(REG, "M1C_F2_STATE_R6c_pass1.tsv"))
f2_s2 = read_rows(os.path.join(REG, "M1C_F2_STATE_R6c_pass2.tsv"))
f2_m1 = read_rows(os.path.join(REG, "M1C_F2_STATE_SEAM_R6c_pass1.tsv"))
f2_m2 = read_rows(os.path.join(REG, "M1C_F2_STATE_SEAM_R6c_pass2.tsv"))
f2_inv_s = read_rows(os.path.join(REG, "M1C_F2_RESULTS_R6c_STATE.tsv"))
f2_inv_m = read_rows(os.path.join(REG, "M1C_F2_RESULTS_R6c_SEAM.tsv"))

# ---- frozen table F3 rows (236) ----
frozen_path = os.path.join(REG, "PREREG_M1C_FACTS_R8_M1c2.tsv")
with open(frozen_path, encoding="utf-8") as fh:
    flines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
fhead = flines[0].split("\t")
frozen = [dict(zip(fhead, l.split("\t"))) for l in flines[1:]]
frozen_f3 = [r for r in frozen if r["tree"] == "F3"]


def index_by(rows, key):
    d = {}
    for r in rows:
        d.setdefault(r[key], r)
    return d


f3_s1i = index_by(f3_s1, "id")
f3_s2i = index_by(f3_s2, "id")
f3_m1i = index_by(f3_m1, "id")
f3_m2i = index_by(f3_m2, "id")
f2_s1i = index_by(f2_s1, "id")
f2_s2i = index_by(f2_s2, "id")
f2_m1i = index_by(f2_m1, "id")
f2_m2i = index_by(f2_m2, "id")


def inv_index(rows):
    d = {}
    for r in rows:
        d[(r["point_id"], r["pass"])] = {c: r.get(c, "") for c in INV}
    return d


f3_is, f3_im = inv_index(f3_inv_s), inv_index(f3_inv_m)
f2_is, f2_im = inv_index(f2_inv_s), inv_index(f2_inv_m)

# ---- Output 1: F3 vs frozen (per frozen F3 row) ----
# Each frozen F3 row is compared on both passes (pass1 and pass2 where the run has them):
#   facts: rc1, rc2, rc3, hit on the gdb side (expected columns exp_rc1..exp_hit) and the nogdb side
#          (same expectations, as the frozen table states one expectation per row);
#   env_as_run vs env_expected (S4FMM_DUMP* removed);
#   point_verdict and I1..I6 vs the frozen expectation columns (exp_I1..exp_I6; '-' skipped).
frozen_lines = []
frozen_diffs = 0
frozen_gdb_div = 0
# GDB_DIVERGENT: F3 rows whose gdb and nogdb facts disagree, or whose status says so
for r in f3_s1 + f3_s2 + f3_m1 + f3_m2:
    if r.get("status", "") == "GDB_DIVERGENT":
        frozen_gdb_div += 1
    if (r.get("rc_gdb"), r.get("rc_nogdb")) and r.get("rc_gdb") != r.get("rc_nogdb"):
        frozen_gdb_div += 1


def run_rec(grp, pid, pas):
    if grp in ("G5", "CTRL_AUX"):
        return (f3_s1i if pas == 1 else f3_s2i).get(pid), STATE_FACT
    return (f3_m1i if pas == 1 else f3_m2i).get(pid), SEAM_FACT


def run_env(r):
    return r.get("env_as_run", "")


for fr in frozen_f3:
    pid = fr["point_id_r8"]
    grp = fr["group"]
    checks = []
    if grp == "CTRL_AUX":
        rec_pids = [fr["base_id"]]
    else:
        rec_pids = [fr["base_id"]]
    for pas in (1, 2):
        rec, cols = run_rec(grp, rec_pids[0], pas)
        tag = "P%d" % pas
        if rec is None:
            checks.append((tag + "_RUN_RECORD", "MISSING", "-", "-"))
            frozen_diffs += 1
            continue
        # facts: expected rc1, rc2, rc3, hit against the gdb side of the run record
        for label, val, exp in (("rc1", rec.get("gdb_rc1", ""), fr.get("exp_rc1", "")),
                                ("rc2", rec.get("gdb_rc2", ""), fr.get("exp_rc2", "")),
                                ("rc3", rec.get("gdb_rc3", ""), fr.get("exp_rc3", "")),
                                ("hit", rec.get("gdb_hit", ""), fr.get("exp_hit", ""))):
            if exp in ("", "-"):
                continue
            ok = (val == exp)
            checks.append((tag + "_FACT_" + label, "MATCH" if ok else "DIFF", exp, val))
            if not ok:
                frozen_diffs += 1
        # nogdb side: same expectation
        if "nogdb_rc1" in rec:
            for label, val, exp in (("rc1", rec.get("nogdb_rc1", ""), fr.get("exp_rc1", "")),
                                    ("rc2", rec.get("nogdb_rc2", ""), fr.get("exp_rc2", "")),
                                    ("rc3", rec.get("nogdb_rc3", ""), fr.get("exp_rc3", "")),
                                    ("hit", rec.get("nogdb_hit", ""), fr.get("exp_hit", ""))):
                if exp in ("", "-"):
                    continue
                ok = (val == exp)
                checks.append((tag + "_NOGDB_" + label, "MATCH" if ok else "DIFF", exp, val))
                if not ok:
                    frozen_diffs += 1
        # env_as_run vs env_expected (S4FMM_DUMP* removed on both sides)
        got_env = env_set(run_env(rec))
        want_env = env_set(fr.get("env_expected", ""))
        ok_env = (got_env == want_env)
        checks.append((tag + "_ENV", "MATCH" if ok_env else "DIFF", fr.get("env_expected", ""), run_env(rec)))
        if not ok_env:
            frozen_diffs += 1
    # point_verdict and invariants: state points use the RESULTS_R6c_STATE rows, seam points RESULTS_R6c_SEAM rows
    inv_map = f3_is if grp in ("G5", "CTRL_AUX") else f3_im
    for pas in ("1", "2"):
        key = (fr["base_id"], pas)
        if key not in inv_map:
            checks.append(("P%s_INV_RECORD" % pas, "MISSING", "-", "-"))
            continue
        got = inv_map[key]
        for inv in ("point_verdict", "I1", "I2", "I3", "I4", "I5", "I6"):
            if inv == "point_verdict":
                exp = fr.get("exp_point_verdict", "-")
            else:
                exp = fr.get("exp_" + inv, "-")
            if exp in ("", "-"):
                continue
            ok = (got.get(inv, "") == exp)
            checks.append(("P%s_%s" % (pas, inv), "MATCH" if ok else "DIFF", exp, got.get(inv, "")))
            if not ok:
                frozen_diffs += 1
    frozen_lines.append((grp, pid, checks))

# ---- Output 2: F3 vs F2 committed (per point id, per item) ----
f2_lines = []
f2_diffs = 0
for pid in sorted(set(f2_s1i) | set(f3_s1i)):
    if pid not in f3_s1i or pid not in f2_s1i:
        f2_lines.append(("POINT", pid, "MISSING_IN_ONE_SIDE", "f3=%s f2=%s" % (pid in f3_s1i, pid in f2_s1i)))
        f2_diffs += 1
        continue
    a, b = f3_s1i[pid], f2_s1i[pid]
    cols = STATE_FACT if a.get("kind") != "seam" else SEAM_FACT
    if fact_tuple(a, cols) != fact_tuple(b, cols):
        f2_lines.append(("STATE_FACT", pid, "DIFF", "f3=%s f2=%s" % (fact_tuple(a, cols), fact_tuple(b, cols))))
        f2_diffs += 1
    else:
        f2_lines.append(("STATE_FACT", pid, "MATCH", ""))
for pid in sorted(set(f2_m1i) | set(f3_m1i)):
    if pid not in f3_m1i or pid not in f2_m1i:
        f2_lines.append(("SEAM_POINT", pid, "MISSING_IN_ONE_SIDE", ""))
        f2_diffs += 1
        continue
    a, b = f3_m1i[pid], f2_m1i[pid]
    if fact_tuple(a, SEAM_FACT) != fact_tuple(b, SEAM_FACT):
        f2_lines.append(("SEAM_FACT", pid, "DIFF", "f3=%s f2=%s" % (fact_tuple(a, SEAM_FACT), fact_tuple(b, SEAM_FACT))))
        f2_diffs += 1
    else:
        f2_lines.append(("SEAM_FACT", pid, "MATCH", ""))
for key in sorted(set(f2_is) | set(f3_is)):
    if key not in f3_is or key not in f2_is:
        f2_lines.append(("INV_STATE", "%s#%s" % key, "MISSING_IN_ONE_SIDE", ""))
        f2_diffs += 1
    elif f3_is[key] != f2_is[key]:
        f2_lines.append(("INV_STATE", "%s#%s" % key, "DIFF", "f3=%s f2=%s" % (f3_is[key], f2_is[key])))
        f2_diffs += 1
    else:
        f2_lines.append(("INV_STATE", "%s#%s" % key, "MATCH", ""))
for key in sorted(set(f2_im) | set(f3_im)):
    if key not in f3_im or key not in f2_im:
        f2_lines.append(("INV_SEAM", "%s#%s" % key, "MISSING_IN_ONE_SIDE", ""))
        f2_diffs += 1
    elif f3_im[key] != f2_im[key]:
        f2_lines.append(("INV_SEAM", "%s#%s" % key, "DIFF", "f3=%s f2=%s" % (f3_im[key], f2_im[key])))
        f2_diffs += 1
    else:
        f2_lines.append(("INV_SEAM", "%s#%s" % key, "MATCH", ""))

# ---- write Output 1 ----
with open(OUT_FROZEN, "w", encoding="utf-8") as fh:
    fh.write("# COMPARE_M1C_F3_VS_FROZEN_R8_M1c3 -- F3 actual (%s) vs frozen table F3 rows (236).\n" % sys.argv[1])
    fh.write("group\tpoint_id\titem\tstatus_or_expected\tactual\n")
    for grp, pid, checks in frozen_lines:
        if not checks:
            fh.write("%s\t%s\tNO_CHECKS\t-\t-\n" % (grp, pid))
        for item, st, exp, act in checks:
            fh.write("%s\t%s\t%s\t%s\t%s\n" % (grp, pid, item, exp, act))
    fh.write("DIFFS=%d GDB_DIVERGENT=%d\n" % (frozen_diffs, frozen_gdb_div))

# ---- write Output 2 ----
with open(OUT_F2, "w", encoding="utf-8") as fh:
    fh.write("# F2_F3_DIFF_M1C_R8_M1c3 -- F3 actual (%s) vs R8 F2 committed copies (registries/s4r8/M1c/r8m1c2).\n" % sys.argv[1])
    fh.write("kind\tkey\tstatus\tdetail\n")
    for kind, key, st, detail in f2_lines:
        fh.write("%s\t%s\t%s\t%s\n" % (kind, key, st, detail))
    fh.write("DIFFS=%d GDB_DIVERGENT=%d\n" % (f2_diffs, frozen_gdb_div))

print("FROZEN_DIFFS=%d F2_DIFFS=%d GDB_DIVERGENT=%d" % (frozen_diffs, f2_diffs, frozen_gdb_div))
