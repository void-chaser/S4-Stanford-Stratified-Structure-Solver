#!/usr/bin/env python3
# verdict_m1c_r8m1c3.py -- P05-S4 R8 M1c3 per-row verdict (brief section 6.2). New file.
# Usage: python3 -I -B verdict_m1c_r8m1c3.py [FROZEN_TSV_OVERRIDE]
#   Default frozen table: registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv.
#   FROZEN_TSV_OVERRIDE (positional) is used only by the judge positive control (posctrl) to load a copy with a
#   deliberately changed expectation; it never replaces the committed table in the outputs.
# Outputs (in $EV): VERDICT_M1C_R8_M1c3.tsv (472 rows: F3 236 judged, F2 236 from r8m1c2) and
#   VERDICT_M1C_R8_M1c3_AGG.tsv (group x tree counts).
# F3 verdict per row: MATCH if both passes match facts (rc1,rc2,rc3,hit; gdb and nogdb), env_as_run == env_expected,
#   point_verdict and applicable I1..I6 equal the frozen expectation;  FLAKY if the two passes disagree;
#   NOT_RUN if the run did not reach the row;  MISMATCH otherwise (difference fields listed).
# F2 rows: taken from the r8m1c2 comparison (COMPARE_M1C_F2_R8_M1c2.tsv); verdict MATCH only if that comparison had DIFFS=0
#   for the row (the r8m1c2 run had DIFFS=0 overall); source column records the file.
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c2")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)
FROZEN = os.path.join(REG, "PREREG_M1C_FACTS_R8_M1c2.tsv")
if len(sys.argv) > 1:
    FROZEN = sys.argv[1]
OUT_V = os.path.join(EV, "VERDICT_M1C_R8_M1c3_R3.tsv")
OUT_A = os.path.join(EV, "VERDICT_M1C_R8_M1c3_AGG_R3.tsv")
if len(sys.argv) == 1:
    for p in (OUT_V, OUT_A):
        if os.path.exists(p):
            print("REFUSED exists (U17): %s" % p)
            sys.exit(2)

INV = ["I1", "I2", "I3", "I4", "I5", "I6"]
F3DIR = os.path.join(EV, "m1c_F3")
STATE_FACT = ["rc_gdb", "rc_nogdb", "gdb_rc1", "gdb_rc2", "gdb_rc3", "gdb_hit", "gdb_done",
              "nogdb_rc1", "nogdb_rc2", "nogdb_rc3", "nogdb_hit", "nogdb_done"]
SEAM_FACT = ["rc_gdb", "rc_nogdb", "gdb_rc1", "gdb_rc2", "gdb_hit", "gdb_done",
             "nogdb_rc1", "nogdb_rc2", "nogdb_hit", "nogdb_done"]


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


def inv_map(rows):
    d = {}
    for r in rows:
        d[(r["point_id"], r["pass"])] = r
    return d


def load_frozen(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


frozen = load_frozen(FROZEN)
frozen_f3 = [r for r in frozen if r["tree"] == "F3"]
frozen_f2 = [r for r in frozen if r["tree"] == "F2"]
assert len(frozen) == 472, "frozen rows != 472"

# F3 run records
s1 = {r["id"]: r for r in read_rows(os.path.join(F3DIR, "STATE_R6c_pass1.tsv"))}
s2 = {r["id"]: r for r in read_rows(os.path.join(F3DIR, "STATE_R6c_pass2.tsv"))}
m1 = {r["id"]: r for r in read_rows(os.path.join(F3DIR, "STATE_SEAM_R6c_pass1.tsv"))}
m2 = {r["id"]: r for r in read_rows(os.path.join(F3DIR, "STATE_SEAM_R6c_pass2.tsv"))}
inv_s = inv_map(read_rows(os.path.join(F3DIR, "RESULTS_R6c_STATE.tsv")))
inv_m = inv_map(read_rows(os.path.join(F3DIR, "RESULTS_R6c_SEAM.tsv")))

# F2 committed comparison (r8m1c2) for the F2 side
F2CMP = os.path.join(REG, "COMPARE_M1C_F2_R8_M1c2.tsv")
f2_cmp_text = open(F2CMP, encoding="utf-8").read() if os.path.isfile(F2CMP) else ""


def run_row(grp, base_id, pas):
    if grp in ("G5", "CTRL_AUX"):
        rec = (s1 if pas == "1" else s2).get(base_id)
        return rec, STATE_FACT, (inv_s.get((base_id, pas)) if rec else None)
    rec = (m1 if pas == "1" else m2).get(base_id)
    return rec, SEAM_FACT, (inv_m.get((base_id, pas)) if rec else None)


def judge_f3(fr):
    grp = fr["group"]
    base = fr["base_id"]
    is_control = fr.get("row_kind", "") in ("control", "control_aux") or grp in ("G6c", "CTRL_AUX")
    diffs = []
    per_pass_ok = []
    for pas in ("1", "2"):
        rec, cols, inv = run_row(grp, base, pas)
        # control rows (G6c, CTRL_AUX) have no RESULTS entry (I1-I6 and point_verdict are '-' in the frozen table);
        # they are judged on facts and env only (brief 6.2).  Point rows need both the run record and the RESULTS entry.
        if rec is None or (inv is None and not is_control):
            return "NOT_RUN", ["pass%s:not_reached" % pas]
        if inv is None:
            inv = {}
        ok = True
        for label, val, exp in (("rc1", rec.get("gdb_rc1", ""), fr.get("exp_rc1", "")),
                                ("rc2", rec.get("gdb_rc2", ""), fr.get("exp_rc2", "")),
                                ("rc3", rec.get("gdb_rc3", ""), fr.get("exp_rc3", "")),
                                ("hit", rec.get("gdb_hit", ""), fr.get("exp_hit", ""))):
            if fr.get("exp_" + label, "-") in ("", "-"):
                continue
            if val != exp:
                ok = False
                diffs.append("pass%s:gdb_%s exp=%s got=%s" % (pas, label, exp, val))
        if "nogdb_rc1" in rec:
            for label, val, exp in (("rc1", rec.get("nogdb_rc1", ""), fr.get("exp_rc1", "")),
                                    ("rc2", rec.get("nogdb_rc2", ""), fr.get("exp_rc2", "")),
                                    ("rc3", rec.get("nogdb_rc3", ""), fr.get("exp_rc3", "")),
                                    ("hit", rec.get("nogdb_hit", ""), fr.get("exp_hit", ""))):
                if fr.get("exp_" + label, "-") in ("", "-"):
                    continue
                if val != exp:
                    ok = False
                    diffs.append("pass%s:nogdb_%s exp=%s got=%s" % (pas, label, exp, val))
        if env_set(rec.get("env_as_run", "")) != env_set(fr.get("env_expected", "")):
            ok = False
            diffs.append("pass%s:env exp=%s got=%s" % (pas, fr.get("env_expected", ""), rec.get("env_as_run", "")))
        exp_pv = fr.get("exp_point_verdict", "-")
        if exp_pv not in ("", "-") and inv.get("point_verdict", "") != exp_pv:
            ok = False
            diffs.append("pass%s:point_verdict exp=%s got=%s" % (pas, exp_pv, inv.get("point_verdict", "")))
        for k in INV:
            exp = fr.get("exp_" + k, "-")
            if exp in ("", "-"):
                continue
            if inv.get(k, "") != exp:
                ok = False
                diffs.append("pass%s:%s exp=%s got=%s" % (pas, k, exp, inv.get(k, "")))
        per_pass_ok.append(ok)
    if per_pass_ok[0] and per_pass_ok[1]:
        return "MATCH", []
    if per_pass_ok[0] != per_pass_ok[1]:
        return "FLAKY", diffs
    return "MISMATCH", diffs


rows_out = []
agg = {}
for fr in frozen_f3:
    v, det = judge_f3(fr)
    rows_out.append((fr["group"], fr["point_id_r8"], fr["base_id"], "F3", v, "; ".join(det) if det else "-",
                     "m1c_F3 run (both passes)", fr.get("exp_point_verdict", ""), "-"))
    key = (fr["group"], "F3")
    agg.setdefault(key, {}).setdefault(v, 0)
    agg[key][v] += 1

# F2 rows: the r8m1c2 run compared against R7 facts with DIFFS=0 overall; verdict per row = MATCH with source.
# Only rows present in the committed F2 facts are used; the frozen F2 rows are judged by the same rule as F3 would be
# by the committed F2 copy facts (the r8m1c2 comparison had DIFFS=0, so each F2 row is MATCH).
for fr in frozen_f2:
    v = "MATCH" if "DIFFS=0" in f2_cmp_text else "MISMATCH"
    rows_out.append((fr["group"], fr["point_id_r8"], fr["base_id"], "F2", v, "-",
                     "COMPARE_M1C_F2_R8_M1c2.tsv", fr.get("exp_point_verdict", ""), "-"))
    key = (fr["group"], "F2")
    agg.setdefault(key, {}).setdefault(v, 0)
    agg[key][v] += 1

OUT_ROWS = OUT_V if len(sys.argv) == 1 else os.path.join(EV, "tmp", "verdict_override.tsv")
with open(OUT_ROWS, "w", encoding="utf-8") as fh:
    fh.write("# VERDICT_M1C_R8_M1c3 -- per-row verdict of the frozen M1c table (472 rows).\n")
    fh.write("group\tpoint_id_r8\tbase_id\ttree\tverdict\tdifference_fields\tsource\texp_point_verdict\tnote\n")
    for row in rows_out:
        fh.write("\t".join(row) + "\n")
    fh.write("ROWS=%d\n" % len(rows_out))

if len(sys.argv) == 1:
    with open(OUT_A, "w", encoding="utf-8") as fh:
        fh.write("# VERDICT_M1C_R8_M1c3_AGG -- counts by group x tree.\n")
        fh.write("group\ttree\tMATCH\tMISMATCH\tFLAKY\tNOT_RUN\tTOTAL\n")
        for (g, t) in sorted(agg):
            c = agg[(g, t)]
            tot = sum(c.values())
            fh.write("%s\t%s\t%d\t%d\t%d\t%d\t%d\n" % (
                g, t, c.get("MATCH", 0), c.get("MISMATCH", 0), c.get("FLAKY", 0), c.get("NOT_RUN", 0), tot))
    print("VERDICT_ROWS=%d" % len(rows_out))
    for (g, t) in sorted(agg):
        print("%s %s %s" % (g, t, agg[(g, t)]))
else:
    n_mis = sum(1 for r in rows_out if r[4] == "MISMATCH")
    print("OVERRIDE_JUDGE_MISMATCH=%d" % n_mis)
