#!/usr/bin/env python3
# recheck_f3_r8m1c4.py -- P05-S4 R8 M1c4 independent recheck of the F3 M1c facts against the frozen table.
# New file. Implemented from scratch: imports nothing from the r8m1c3 scripts and reads only committed files.
# Inputs (committed):
#   frozen fact table (472 rows; only tree F3 rows are used: 236 rows)
#   registries/s4r8/M1c/r8m1c3/M1C_F3_STATE_R6c_pass{1,2}.tsv        (G5 points, CTRL_AUX controls; key = id)
#   registries/s4r8/M1c/r8m1c3/M1C_F3_STATE_SEAM_R6c_pass{1,2}.tsv    (G6 points, G6c controls; key = id)
#   registries/s4r8/M1c/r8m1c3/M1C_F3_RESULTS_R6c_STATE.tsv           (judgement, key = point_id + pass)
#   registries/s4r8/M1c/r8m1c3/M1C_F3_RESULTS_R6c_SEAM.tsv            (judgement, key = point_id + pass)
# Output: $EV/RECHECK_F3_R8_M1c4.tsv
#   part 1: per-item check counts; part 2: group x row_kind row counts; part 3: all differences;
#   last line CHECKS=<n> DIFFS=<m>.
# Run: sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- python3 -I -B testing/d003/stage_s4/recheck_f3_r8m1c4.py
import os
import sys
from collections import Counter

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8")
FROZEN = os.path.join(REG, "M1c", "r8m1c2", "PREREG_M1C_FACTS_R8_M1c2.tsv")
R3 = os.path.join(REG, "M1c", "r8m1c3")
OUT = os.path.join(EV, "RECHECK_F3_R8_M1c4.tsv")
EXPECTED_GROUP_ROWS = {("G5", "point"): 177, ("G6", "point"): 25, ("G6c", "control"): 18, ("CTRL_AUX", "control_aux"): 16}


def read_tsv(path):
    """Return list of dict rows; lines starting with '#' are comments; first other line is the header."""
    rows = []
    header = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if header is None:
                header = parts
                continue
            if len(parts) != len(header):
                raise SystemExit("column count mismatch in %s: %d != %d" % (path, len(parts), len(header)))
            rows.append(dict(zip(header, parts)))
    return rows


def env_pairs(s):
    """Sorted (key, value) pairs of a ';'-separated env string, with S4FMM_DUMP* keys removed."""
    out = []
    for item in s.split(";"):
        if not item:
            continue
        if "=" not in item:
            out.append((item, ""))
            continue
        k, v = item.split("=", 1)
        if k.startswith("S4FMM_DUMP"):
            continue
        out.append((k, v))
    return sorted(out)


def main():
    frozen_all = read_tsv(FROZEN)
    frozen = [r for r in frozen_all if r["tree"] == "F3"]

    state = {p: {} for p in (1, 2)}
    seam = {p: {} for p in (1, 2)}
    for p in (1, 2):
        for r in read_tsv(os.path.join(R3, "M1C_F3_STATE_R6c_pass%d.tsv" % p)):
            state[p][r["id"]] = r
        for r in read_tsv(os.path.join(R3, "M1C_F3_STATE_SEAM_R6c_pass%d.tsv" % p)):
            seam[p][r["id"]] = r

    res_state = {}
    for r in read_tsv(os.path.join(R3, "M1C_F3_RESULTS_R6c_STATE.tsv")):
        res_state[(r["point_id"], r["pass"])] = r
    res_seam = {}
    for r in read_tsv(os.path.join(R3, "M1C_F3_RESULTS_R6c_SEAM.tsv")):
        res_seam[(r["point_id"], r["pass"])] = r

    checks = Counter()     # (group, row_kind, field) -> number of checks
    diffs = []             # (group, row_kind, base_id, pass, field, expected, actual)
    rows_by_group = Counter()

    def check(group, kind, base, pas, field, exp, act):
        checks[(group, kind, field)] += 1
        if exp != act:
            diffs.append((group, kind, base, pas, field, exp, act))

    for fr in frozen:
        group = fr["group"]
        kind = fr["row_kind"]
        base = fr["base_id"]
        rows_by_group[(group, kind)] += 1
        if group == "G5" or group == "CTRL_AUX":
            src = state
        else:
            src = seam
        for p in (1, 2):
            obs = src[p].get(base)
            if obs is None:
                check(group, kind, base, p, "row_present", "present", "missing")
                continue
            # rc1, rc2, rc3, hit: compare gdb_* and nogdb_* where the expectation is not '-'
            for k in ("rc1", "rc2", "rc3", "hit"):
                ev = fr["exp_" + k]
                if ev == "-":
                    continue
                for src_name in ("gdb", "nogdb"):
                    col = "%s_%s" % (src_name, k)
                    check(group, kind, base, p, k, ev, obs.get(col, "MISSING_COLUMN"))
            # env: as-run (without S4FMM_DUMP*) against expected (without S4FMM_DUMP*)
            check(group, kind, base, p, "env", env_pairs(fr["env_expected"]), env_pairs(obs["env_as_run"]))
            # judgement: only point rows (G5 and G6) have a RESULTS row
            if kind == "point":
                rr = (res_state if group == "G5" else res_seam).get((base, str(p)))
                if rr is None:
                    check(group, kind, base, p, "results_row_present", "present", "missing")
                    continue
                ev = fr["exp_point_verdict"]
                if ev != "-":
                    check(group, kind, base, p, "point_verdict", ev, rr["point_verdict"])
                for i in range(1, 7):
                    ev = fr["exp_I%d" % i]
                    if ev == "-":
                        continue
                    check(group, kind, base, p, "I%d" % i, ev, rr["I%d" % i])

    # per-group row counts against the planning figures
    for key, n in sorted(EXPECTED_GROUP_ROWS.items()):
        got = rows_by_group.get(key, 0)
        if got != n:
            diffs.append((key[0], key[1], "ROW_COUNT", "-", "rows", str(n), str(got)))

    total_checks = sum(checks.values())
    if os.path.exists(OUT):
        raise SystemExit("REFUSED exists (U17): %s" % OUT)
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# RECHECK_F3_R8_M1c4 -- independent recheck of the F3 M1c facts (committed r8m1c3 registries vs frozen table)\n")
        fh.write("# part 1: check counts per group x row_kind x field\n")
        fh.write("group\trow_kind\tfield\tchecks\n")
        for k in sorted(checks):
            fh.write("%s\t%s\t%s\t%d\n" % (k[0], k[1], k[2], checks[k]))
        fh.write("# part 1b: totals per field\n")
        by_field = Counter()
        for k, v in checks.items():
            by_field[k[2]] += v
        for f in sorted(by_field):
            fh.write("FIELD_TOTAL\t%s\t%d\n" % (f, by_field[f]))
        fh.write("# part 2: rows per group x row_kind (planned: G5 point 177, G6 point 25, G6c control 18, CTRL_AUX control_aux 16)\n")
        for k in sorted(rows_by_group):
            fh.write("ROWS\t%s\t%s\t%d\n" % (k[0], k[1], rows_by_group[k]))
        fh.write("# part 3: differences\n")
        fh.write("group\trow_kind\tbase_id\tpass\tfield\texpected\tactual\n")
        for d in diffs:
            fh.write("\t".join(str(x) for x in d) + "\n")
        fh.write("CHECKS=%d DIFFS=%d\n" % (total_checks, len(diffs)))
    print("CHECKS=%d DIFFS=%d" % (total_checks, len(diffs)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
