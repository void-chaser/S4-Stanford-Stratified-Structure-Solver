#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# verdict_r9m1r3.py -- Official verdict engine for P05-S4 R9 M1R3 (Rules U314, U319, U320, Step S-H). New file.
import argparse, csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))

DEFAULT_PREREG = os.path.join(EV, "PREREG_M1_F4_R9M1R3.tsv")
DEFAULT_P1 = os.path.join(EV, "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1R3_pass1.tsv")
DEFAULT_P2 = os.path.join(EV, "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1R3_pass2.tsv")
DEFAULT_OUT = os.path.join(EV, "VERDICT_M1_F4_R9M1R3.tsv")
DEFAULT_AGG = os.path.join(EV, "VERDICT_M1_F4_R9M1R3_AGG.tsv")

def main():
    parser = argparse.ArgumentParser(description="Official verdict engine for M1 F4")
    parser.add_argument("--prereg", default=DEFAULT_PREREG)
    parser.add_argument("--pass1", default=DEFAULT_P1)
    parser.add_argument("--pass2", default=DEFAULT_P2)
    parser.add_argument("--out", default=DEFAULT_OUT)
    parser.add_argument("--out-agg", default=DEFAULT_AGG)
    args = parser.parse_args()

    # Load prereg
    prereg_rows = {}
    with open(args.prereg, encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            prereg_rows[(r["section"], r["group"], r["point_id"])] = r

    # Load pass1
    pass1_rows = {}
    with open(args.pass1, encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            pass1_rows[(r["section"], r["group"], r["point_id"])] = r

    # Load pass2
    pass2_rows = {}
    with open(args.pass2, encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            pass2_rows[(r["section"], r["group"], r["point_id"])] = r

    assert len(prereg_rows) == 651, f"Expected 651 prereg rows, got {len(prereg_rows)}"
    assert len(pass1_rows) == 651, f"Expected 651 pass1 rows, got {len(pass1_rows)}"
    assert len(pass2_rows) == 651, f"Expected 651 pass2 rows, got {len(pass2_rows)}"

    verdict_rows = []
    counts = {
        "MATCH": 0, "NOT_REACHED_AS_EXPECTED": 0, "NOT_RUN_AS_EXPECTED": 0,
        "MISMATCH": 0, "FLAKY": 0, "GDB_DIVERGENT": 0
    }
    agg_counts = {}

    for key in sorted(prereg_rows.keys()):
        sec, grp, pid = key
        exp = prereg_rows[key]
        p1 = pass1_rows[key]
        p2 = pass2_rows[key]

        p1_rc1, p1_rc2, p1_rc3, p1_hit, p1_cls = p1["rc1"], p1["rc2"], p1["rc3"], p1["hit"], p1["class"]
        p2_rc1, p2_rc2, p2_rc3, p2_hit, p2_cls = p2["rc1"], p2["rc2"], p2["rc3"], p2["hit"], p2["class"]

        # Check two-pass consistency
        consistent = (p1_rc1 == p2_rc1 and p1_rc2 == p2_rc2 and p1_rc3 == p2_rc3 and p1_hit == p2_hit and p1_cls == p2_cls)

        # Check I1..I6 consistency for M1c G5 and G6
        if sec == "M1c" and grp in ("G5", "G6"):
            for iname in ("I1", "I2", "I3", "I4", "I5", "I6"):
                if p1.get(iname, "-") != p2.get(iname, "-"):
                    consistent = False

        diff_fields = []
        if not consistent:
            if p1_rc3 != p2_rc3:
                v = "GDB_DIVERGENT"
                diff_fields.append("rc3_divergent")
                note = "Pass 1 and Pass 2 GDB rc3 diverged"
            else:
                v = "FLAKY"
                diff_fields.append("pass1_vs_pass2_disagree")
                note = "Pass 1 and Pass 2 disagreed"
        else:
            contract = exp.get("contract", "-")
            exp_eff = exp["f3_effective_verdict"]

            if contract == "NOT_RUN_REGISTRY_ERROR" or exp_eff == "NOT_RUN_AS_EXPECTED" or exp["env"] == "NOT_RUN":
                if p1_cls == "NOT_RUN_REGISTRY_ERROR" and p1_rc1 == "-":
                    v = "NOT_RUN_AS_EXPECTED"
                    note = "Control row deliberately not run as expected (Rule U319)"
                else:
                    v = "MISMATCH"
                    diff_fields.append("fabricated_execution_facts")
                    note = "Expected un-run but observed facts were fabricated"
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

                # Check rc2 per Rule U314
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
                    if exp_pv == "-" and grp in ("G6c", "CTRL_AUX"):
                        exp_pv = "CONTROL_OK"
                    if p1_cls != exp_pv and p1_cls != exp["exp_class"]:
                        diff_fields.append(f"point_verdict({p1_cls}!={exp_pv})")

                    # Rule U320: Check invariants I1..I6 for G5 and G6
                    if grp in ("G5", "G6"):
                        for iname in ("I1", "I2", "I3", "I4", "I5", "I6"):
                            if exp.get(f"exp_{iname}", "-") != "-" and p1.get(iname, "-") != exp[f"exp_{iname}"]:
                                diff_fields.append(f"{iname}({p1.get(iname, '-')}!={exp[f'exp_{iname}']})")
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

        counts[v] = counts.get(v, 0) + 1
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
        fh.write("# VERDICT_M1_F4_R9M1R3.tsv -- Official verdict table for P05-S4 R9 M1R3 (Rules U314, U319, U320)" + chr(10))
        fh.write(chr(9).join(out_header) + chr(10))
        for row in verdict_rows:
            fh.write(chr(9).join(row) + chr(10))

    # Write AGG TSV
    with open(args.out_agg, "w", encoding="utf-8") as fh:
        fh.write("# VERDICT_M1_F4_R9M1R3_AGG.tsv -- Aggregated verdict counts by section and group" + chr(10))
        fh.write(chr(9).join(["section", "group", "verdict", "count"]) + chr(10))
        for (sec, grp, v), count in sorted(agg_counts.items()):
            fh.write(f"{sec}\t{grp}\t{v}\t{count}\n")

    print(f"Wrote detailed verdict -> {args.out} ({len(verdict_rows)} rows).")
    print(f"Wrote aggregated counts -> {args.out_agg} ({len(agg_counts)} rows).")

if __name__ == "__main__":
    main()
