#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# verdict_r9m1r2.py -- Official verdict generation for P05-S4 R9 M1R2 (Rules U314, U316). New file.
import argparse, csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
os.makedirs(EV, exist_ok=True)

def main():
    parser = argparse.ArgumentParser(description="Evaluate formal verdict for M1 F4")
    parser.add_argument("--prereg", default=os.path.join(EV, "PREREG_M1_F4_R9M1R2.tsv"))
    parser.add_argument("--pass1", default=os.path.join(EV, "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1R2_pass1.tsv"))
    parser.add_argument("--pass2", default=os.path.join(EV, "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1R2_pass2.tsv"))
    parser.add_argument("--out", default=os.path.join(EV, "VERDICT_M1_F4_R9M1R2.tsv"))
    parser.add_argument("--out-agg", default=os.path.join(EV, "VERDICT_M1_F4_R9M1R2_AGG.tsv"))
    args = parser.parse_args()

    # 1. Load prereg
    prereg_map = {}
    with open(args.prereg, encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            prereg_map[(r["section"], r["group"], r["point_id"])] = r

    assert len(prereg_map) == 651, f"Expected 651 prereg rows, got {len(prereg_map)}"

    # 2. Load facts
    def load_facts(p):
        facts = {}
        with open(p, encoding="utf-8") as fh:
            lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
            h = lines[0]
            for l in lines[1:]:
                r = dict(zip(h, l))
                facts[(r["section"], r["group"], r["point_id"])] = r
        return facts

    facts_p1 = load_facts(args.pass1)
    facts_p2 = load_facts(args.pass2)
    assert len(facts_p1) == 651
    assert len(facts_p2) == 651

    # 3. Evaluate verdict per row
    counts = {
        "MATCH": 0,
        "NOT_REACHED_AS_EXPECTED": 0,
        "NOT_RUN_AS_EXPECTED": 0,
        "MISMATCH": 0,
        "FLAKY": 0,
        "GDB_DIV": 0
    }
    agg_counts = {}
    verdict_rows = []

    for key in sorted(prereg_map.keys()):
        sec, grp, pid = key
        exp = prereg_map[key]
        p1 = facts_p1[key]
        p2 = facts_p2[key]

        # Check pass1 vs pass2 consistency
        p1_rc1, p2_rc1 = p1["rc1"], p2["rc1"]
        p1_rc2, p2_rc2 = p1["rc2"], p2["rc2"]
        p1_rc3, p2_rc3 = p1["rc3"], p2["rc3"]
        p1_hit, p2_hit = p1["hit"], p2["hit"]
        p1_cls, p2_cls = p1["class"], p2["class"]

        consistent = (
            p1_rc1 == p2_rc1 and
            p1_rc2 == p2_rc2 and
            p1_rc3 == p2_rc3 and
            p1_hit == p2_hit and
            p1_cls == p2_cls and
            p1["I1"] == p2["I1"] and p1["I2"] == p2["I2"] and p1["I3"] == p2["I3"] and
            p1["I4"] == p2["I4"] and p1["I5"] == p2["I5"] and p1["I6"] == p2["I6"]
        )

        diff_fields = []
        if not consistent:
            v = "FLAKY"
            diff_fields.append("pass1_vs_pass2_disagree")
            note = "Pass 1 and Pass 2 disagreed"
        else:
            contract = exp.get("contract", "-")
            exp_eff = exp["f3_effective_verdict"]

            if contract == "NOT_RUN_REGISTRY_ERROR" or exp_eff == "NOT_RUN_AS_EXPECTED":
                v = "NOT_RUN_AS_EXPECTED"
                note = "Control row deliberately not run as expected"
            elif contract == "NOT_REACHED_AS_EXPECTED" or exp_eff == "NOT_REACHED_AS_EXPECTED":
                if p1_hit == "0" and p1_cls == "INVALID":
                    v = "NOT_REACHED_AS_EXPECTED"
                    note = "Fault site not reached as expected (hit=0)"
                else:
                    v = "MISMATCH"
                    diff_fields.append(f"unexpected_hit({p1_hit})")
                    note = "Expected NOT_REACHED but hit > 0"
            else:
                # Check rc1
                if exp["exp_rc1"] != "-" and p1_rc1 != exp["exp_rc1"]:
                    diff_fields.append(f"rc1({p1_rc1}!={exp['exp_rc1']})")

                # Check rc2 per Rule U314 / plan_and_run_m1b_r8m1b1.py:107-109
                if sec == "M1b":
                    if exp["exp_rc2"] not in ("-", "", "0", None):
                        if p1_rc2 != exp["exp_rc2"]:
                            diff_fields.append(f"rc2({p1_rc2}!={exp['exp_rc2']})")
                else:
                    if exp["exp_rc2"] != "-" and p1_rc2 != exp["exp_rc2"]:
                        diff_fields.append(f"rc2({p1_rc2}!={exp['exp_rc2']})")

                # Check rc3
                if exp["exp_rc3"] != "-" and p1_rc3 != exp["exp_rc3"]:
                    diff_fields.append(f"rc3({p1_rc3}!={exp['exp_rc3']})")

                # Check hit
                if exp["exp_hit"] != "-" and p1_hit != exp["exp_hit"]:
                    diff_fields.append(f"hit({p1_hit}!={exp['exp_hit']})")

                # Check class / point_verdict
                if sec == "M1c":
                    exp_pv = exp["exp_point_verdict"]
                    # Rule U314 citation: verdict_m1c_r8m1c3.py:103-108
                    if exp_pv == "-" and grp in ("G6c", "CTRL_AUX"):
                        exp_pv = "CONTROL_OK"
                    if p1_cls != exp_pv:
                        diff_fields.append(f"point_verdict({p1_cls}!={exp_pv})")

                    # Check invariants I1..I6 for G5
                    if grp == "G5":
                        for iname in ("I1", "I2", "I3", "I4", "I5", "I6"):
                            if exp[f"exp_{iname}"] != "-" and p1[iname] != exp[f"exp_{iname}"]:
                                diff_fields.append(f"{iname}({p1[iname]}!={exp[f'exp_{iname}']})")
                else:
                    # M1b class check
                    exp_c = exp["exp_class"]
                    if p1_cls != exp_c:
                        diff_fields.append(f"class({p1_cls}!={exp_c})")

                if not diff_fields:
                    v = "MATCH"
                    note = "All observed facts match preregistered expectations"
                else:
                    v = "MISMATCH"
                    note = "Observed facts differ from preregistration: " + ";".join(diff_fields)

        counts[v] += 1
        agg_key = (sec, grp, v)
        agg_counts[agg_key] = agg_counts.get(agg_key, 0) + 1

        verdict_rows.append([
            sec, grp, pid, exp["base_id"], "F4", exp["driver_name"],
            p1_rc1, p1_rc2, p1_rc3, p1_hit, p1_cls,
            p2_rc1, p2_rc2, p2_rc3, p2_hit, p2_cls,
            "YES" if consistent else "NO", v, ";".join(diff_fields) if diff_fields else "NONE", note
        ])

    print(f"Verdict evaluation completed across {len(verdict_rows)} rows.")
    print("Summary counts:", counts)

    # Write detailed TSV
    out_header = [
        "section", "group", "point_id", "base_id", "tree", "driver_name",
        "pass1_rc1", "pass1_rc2", "pass1_rc3", "pass1_hit", "pass1_class",
        "pass2_rc1", "pass2_rc2", "pass2_rc3", "pass2_hit", "pass2_class",
        "pass_consistent", "verdict", "difference_fields", "note"
    ]
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("# VERDICT_M1_F4_R9M1R2.tsv -- Official verdict table for P05-S4 R9 M1R2 (Rules U314, U316)\n")
        fh.write("\t".join(out_header) + "\n")
        for row in verdict_rows:
            fh.write("\t".join(row) + "\n")

    # Write AGG TSV
    with open(args.out_agg, "w", encoding="utf-8") as fh:
        fh.write("# VERDICT_M1_F4_R9M1R2_AGG.tsv -- Aggregated verdict counts by section and group\n")
        fh.write("section\tgroup\tverdict\tcount\n")
        for (sec, grp, v), cnt in sorted(agg_counts.items()):
            fh.write(f"{sec}\t{grp}\t{v}\t{cnt}\n")

    print(f"Wrote {args.out} and {args.out_agg}.")
    return counts

if __name__ == "__main__":
    main()
