#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# compare_f3_f4_r9m1r2.py -- Field-by-field equivalence comparison between F3 frozen facts and F4 results (Rules U315, U316). New file.
import argparse, csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
os.makedirs(EV, exist_ok=True)

def clean_base_env(env_str):
    # Rule U316: Env comparison explicitly ignores injection variables
    parts = [p.strip() for p in env_str.split(";") if p.strip()]
    kept = []
    for p in parts:
        k = p.split("=")[0]
        if k.startswith("S4FMM_INJECT") or k.startswith("S4FMM_NTH") or k.startswith("S4FMM_TWICE"):
            continue
        kept.append(p)
    return ";".join(sorted(kept))

def main():
    parser = argparse.ArgumentParser(description="Field-by-field F3 vs F4 equivalence comparison")
    parser.add_argument("--facts", default=os.path.join(EV, "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1R2_pass1.tsv"))
    parser.add_argument("--out", default=os.path.join(EV, "F3_F4_EQUIV_R9M1R2.tsv"))
    args = parser.parse_args()

    # 1. Load F3 facts (M1b 415 rows + M1c 236 rows = 651 rows)
    # M1b from RESULTS_M1B_R8_M1b1 and RESULTS_SUPP_R8_M1b3 per EFFECTIVE_M1B_R8_M1b3
    plan_b1 = {}
    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b1/PLAN_M1B_R8_M1b1.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            plan_b1[(r["group"], r["point_id"])] = r

    res_b1 = {}
    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b1/RESULTS_M1B_R8_M1b1.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader(f, delimiter="\t"):
            if r["tree"] == "F3":
                res_b1[r["point_id"]] = r

    supp_b3 = {}
    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/RESULTS_SUPP_R8_M1b3.tsv"), encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            if r["tree"] == "F3":
                supp_b3[(r["group"], r["point_id"])] = r

    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv"), encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
        eff_m1b = [dict(zip(lines[0], l)) for l in lines[1:] if dict(zip(lines[0], l))["tree"] == "F3"]

    f3_facts = {}
    for r in eff_m1b:
        grp = r["group"]
        pid = r["point_id"]
        src = r["source"]
        if src == "M1b1_NOT_RUN":
            f3_facts[("M1b", grp, pid)] = {
                "rc1": "0", "rc2": "0", "rc3": "-", "hit": "-", "class": "CONTROL_OK",
                "I1": "-", "I2": "-", "I3": "-", "I4": "-", "I5": "-", "I6": "-",
                "env": clean_base_env(plan_b1[(grp, pid)]["env_str"])
            }
        elif src == "M1b1_ENV_AGREE":
            res = res_b1[pid]
            f3_facts[("M1b", grp, pid)] = {
                "rc1": res["p1_rc1"], "rc2": res["p1_rc2"], "rc3": "-", "hit": res["p1_hit"], "class": res["p1_class"],
                "I1": "-", "I2": "-", "I3": "-", "I4": "-", "I5": "-", "I6": "-",
                "env": clean_base_env(plan_b1[(grp, pid)]["env_str"])
            }
        elif src == "SUPP_R8_M1b3":
            res = supp_b3[(grp, pid)]
            f3_facts[("M1b", grp, pid)] = {
                "rc1": res["p1_rc1"], "rc2": res["p1_rc2"], "rc3": "-", "hit": res["p1_hit"], "class": res["p1_class"],
                "I1": "-", "I2": "-", "I3": "-", "I4": "-", "I5": "-", "I6": "-",
                "env": clean_base_env(res["env"])
            }

    # Load M1c facts
    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c3/COMPARE_M1C_F3_VS_FROZEN_R8_M1c3.tsv"), encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            grp = r["group"]
            pid = r["point_id_r8"]
            f3_facts[("M1c", grp, pid)] = {
                "rc1": r["p1_rc1"], "rc2": r["p1_rc2"], "rc3": r["p1_rc3"], "hit": r["p1_hit"], "class": r["p1_class"],
                "I1": r["p1_I1"], "I2": r["p1_I2"], "I3": r["p1_I3"], "I4": r["p1_I4"], "I5": r["p1_I5"], "I6": r["p1_I6"],
                "env": clean_base_env(r["env_expected"])
            }

    assert len(f3_facts) == 651, f"Expected 651 F3 facts, got {len(f3_facts)}"

    # 2. Load F4 facts
    f4_facts = {}
    with open(args.facts, encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            f4_facts[(r["section"], r["group"], r["point_id"])] = r

    assert len(f4_facts) == 651, f"Expected 651 F4 facts, got {len(f4_facts)}"

    # 3. Perform field-by-field comparison
    diff_records = []
    equiv_rows = []
    both_empty_count = 0
    nonempty_identical_count = 0
    not_run_count = 0

    for key in sorted(f4_facts.keys()):
        sec, grp, pid_f4 = key
        f4_r = f4_facts[key]
        pid_f3 = f4_r["f3_point_id"]
        f3_key = (sec, grp, pid_f3)

        assert f3_key in f3_facts, f"Missing F3 fact for {f3_key}"
        f3_r = f3_facts[f3_key]

        diff_fields = []

        # Compare rc1, rc2, rc3, hit, class
        for fld in ("rc1", "rc2", "rc3", "hit", "class"):
            v3, v4 = f3_r[fld], f4_r[fld]
            if v3 != v4:
                diff_fields.append(f"{fld}(F3={v3}!=F4={v4})")

        # Compare invariants I1..I6
        for i in range(1, 7):
            fld = f"I{i}"
            v3, v4 = f3_r[fld], f4_r[fld]
            if v3 != "-" and v4 != "-" and v3 != v4:
                diff_fields.append(f"{fld}(F3={v3}!=F4={v4})")

        # Compare clean base env
        env3 = f3_r["env"]
        env4 = clean_base_env(f4_r["env"])
        if env3 != env4:
            diff_fields.append(f"env(F3={env3}!=F4={env4})")

        # HIT classification (Rule U315: distinguish BOTH_EMPTY vs NONEMPTY_IDENTICAL)
        h3, h4 = f3_r["hit"], f4_r["hit"]
        if h3 == "-" or h4 == "-":
            hit_equiv_class = "NOT_RUN"
            not_run_count += 1
        elif h3 == "0" and h4 == "0":
            hit_equiv_class = "BOTH_EMPTY"
            both_empty_count += 1
        elif h3 == h4 and int(h3) > 0:
            hit_equiv_class = "NONEMPTY_IDENTICAL"
            nonempty_identical_count += 1
        else:
            hit_equiv_class = f"HIT_MISMATCH(F3={h3},F4={h4})"
            diff_fields.append(hit_equiv_class)

        status = "EQUIVALENT" if not diff_fields else "DIFFERENT"
        diff_str = ";".join(diff_fields) if diff_fields else "NONE"

        equiv_rows.append([
            sec, grp, pid_f3, pid_f4, f3_r["rc1"], f4_r["rc1"], f3_r["rc2"], f4_r["rc2"],
            f3_r["hit"], f4_r["hit"], f3_r["class"], f4_r["class"],
            f3_r["I1"], f4_r["I1"], f3_r["I2"], f4_r["I2"], f3_r["I3"], f4_r["I3"],
            f3_r["I4"], f4_r["I4"], f3_r["I5"], f4_r["I5"], f3_r["I6"], f4_r["I6"],
            hit_equiv_class, status, diff_str
        ])

        if status != "EQUIVALENT":
            diff_records.append((key, diff_str))

    print(f"Equivalence comparison complete: CHECKS = {len(equiv_rows)}, DIFFS = {len(diff_records)}")
    print(f"HIT split: BOTH_EMPTY = {both_empty_count}, NONEMPTY_IDENTICAL = {nonempty_identical_count}, NOT_RUN = {not_run_count}")

    # Write output
    out_header = [
        "section", "group", "f3_point_id", "f4_point_id",
        "f3_rc1", "f4_rc1", "f3_rc2", "f4_rc2", "f3_hit", "f4_hit", "f3_class", "f4_class",
        "f3_I1", "f4_I1", "f3_I2", "f4_I2", "f3_I3", "f4_I3",
        "f3_I4", "f4_I4", "f3_I5", "f4_I5", "f3_I6", "f4_I6",
        "hit_equivalence", "status", "differences"
    ]
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("# F3_F4_EQUIV_R9M1R2.tsv -- Field-by-field equivalence comparison between F3 and F4 (Rule U316)\n")
        fh.write("\t".join(out_header) + "\n")
        for row in equiv_rows:
            fh.write("\t".join(row) + "\n")

    print(f"Wrote {args.out}.")
    return len(diff_records)

if __name__ == "__main__":
    main()
