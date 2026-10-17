#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# verdict_r9m1.py -- Generate official verdict for F4 M1 regression runs (Rule U306). New file.
import csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "VERDICT_M1_F4_R9M1.tsv")
OUT_AGG = os.path.join(EV, "VERDICT_M1_F4_R9M1_AGG.tsv")

# 1. Load PREREG_M1_F4_R9M1.tsv
prereg_path = os.path.join(EV, "PREREG_M1_F4_R9M1.tsv")
prereg_map = {}
with open(prereg_path, encoding="utf-8") as fh:
    lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        r = dict(zip(h, l))
        key = (r["section"], r["group"], r["point_id"])
        prereg_map[key] = r

assert len(prereg_map) == 651, f"Expected 651 prereg rows, got {len(prereg_map)}"

# 2. Load Pass 1 and Pass 2 facts
pass1_path = os.path.join(EV, "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1_pass1.tsv")
pass2_path = os.path.join(EV, "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1_pass2.tsv")

def load_facts(p):
    facts = {}
    with open(p, encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            key = (r["section"], r["group"], r["point_id"])
            facts[key] = r
    return facts

facts_p1 = load_facts(pass1_path)
facts_p2 = load_facts(pass2_path)
assert len(facts_p1) == 651, f"Pass 1 facts count {len(facts_p1)} != 651"
assert len(facts_p2) == 651, f"Pass 2 facts count {len(facts_p2)} != 651"

# 3. Evaluate verdict per row
verdict_rows = []
counts = {
    "MATCH": 0,
    "NOT_REACHED_AS_EXPECTED": 0,
    "NOT_RUN_AS_EXPECTED": 0,
    "MISMATCH": 0,
    "FLAKY": 0,
    "GDB_DIV": 0
}

agg_counts = {}

for key in sorted(prereg_map.keys()):
    sec, grp, pid = key
    exp = prereg_map[key]
    p1 = facts_p1[key]
    p2 = facts_p2[key]

    # Check Pass 1 vs Pass 2 consistency
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
        # Check against preregistration
        exp_f3_eff = exp["f3_effective_verdict"]
        if exp_f3_eff == "NOT_RUN_AS_EXPECTED":
            v = "NOT_RUN_AS_EXPECTED"
            note = "Control row deliberately not run as expected"
        elif exp_f3_eff == "NOT_REACHED_AS_EXPECTED":
            if p1_hit == "0" and p1_cls == "INVALID":
                v = "NOT_REACHED_AS_EXPECTED"
                note = "Fault site not reached as expected (hit=0)"
            else:
                v = "MISMATCH"
                diff_fields.append(f"unexpected_hit({p1_hit})")
                note = "Expected NOT_REACHED but hit > 0"
        else:
            # Expected MATCH
            # Check return codes, hits, class, and invariants
            if exp["exp_rc1"] != "-" and p1_rc1 != exp["exp_rc1"]:
                diff_fields.append(f"rc1({p1_rc1}!={exp['exp_rc1']})")

            # In M1b, per contract U65/R8, exp_rc2 is enforced if != 0
            if sec == "M1b":
                if exp["exp_rc2"] not in ("-", "", "0") and p1_rc2 != exp["exp_rc2"]:
                    diff_fields.append(f"rc2({p1_rc2}!={exp['exp_rc2']})")
            else:
                if exp["exp_rc2"] != "-" and p1_rc2 != exp["exp_rc2"]:
                    diff_fields.append(f"rc2({p1_rc2}!={exp['exp_rc2']})")

            if exp["exp_rc3"] != "-" and p1_rc3 != exp["exp_rc3"]:
                diff_fields.append(f"rc3({p1_rc3}!={exp['exp_rc3']})")
            if exp["exp_hit"] != "-" and p1_hit != exp["exp_hit"]:
                diff_fields.append(f"hit({p1_hit}!={exp['exp_hit']})")

            # Check class / point_verdict
            exp_c = exp["exp_class"]
            if sec == "M1c":
                exp_p_verdict = exp["exp_point_verdict"]
                if exp_p_verdict == "-" and grp in ("G6c", "CTRL_AUX"):
                    exp_p_verdict = "CONTROL_OK"
                if p1_cls != exp_p_verdict:
                    diff_fields.append(f"point_verdict({p1_cls}!={exp_p_verdict})")
                # Check invariants I1..I6 for G5
                if grp == "G5":
                    for iname in ("I1", "I2", "I3", "I4", "I5", "I6"):
                        if exp[f"exp_{iname}"] != "-" and p1[iname] != exp[f"exp_{iname}"]:
                            diff_fields.append(f"{iname}({p1[iname]}!={exp[f'exp_{iname}']})")
            else:
                # For M1b
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

# Assertions
assert counts["MATCH"] == 626, f"Expected 626 MATCH, got {counts['MATCH']}"
assert counts["NOT_REACHED_AS_EXPECTED"] == 22, f"Expected 22 NOT_REACHED_AS_EXPECTED, got {counts['NOT_REACHED_AS_EXPECTED']}"
assert counts["NOT_RUN_AS_EXPECTED"] == 3, f"Expected 3 NOT_RUN_AS_EXPECTED, got {counts['NOT_RUN_AS_EXPECTED']}"
assert counts["MISMATCH"] == 0, f"MISMATCH must be 0, got {counts['MISMATCH']}"
assert counts["FLAKY"] == 0, f"FLAKY must be 0, got {counts['FLAKY']}"
assert counts["GDB_DIV"] == 0, f"GDB_DIV must be 0, got {counts['GDB_DIV']}"

header = [
    "section", "group", "point_id", "base_id", "tree", "driver_name",
    "pass1_rc1", "pass1_rc2", "pass1_rc3", "pass1_hit", "pass1_class",
    "pass2_rc1", "pass2_rc2", "pass2_rc3", "pass2_hit", "pass2_class",
    "pass_consistent", "verdict", "difference_fields", "note"
]

with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# VERDICT_M1_F4_R9M1.tsv -- Formal verdict table for F4 M1 regression (651 rows)\n")
    fh.write("\t".join(header) + "\n")
    for r in verdict_rows:
        fh.write("\t".join(r) + "\n")

# Write aggregate table
with open(OUT_AGG, "w", encoding="utf-8") as fh:
    fh.write("# VERDICT_M1_F4_R9M1_AGG.tsv -- Aggregate counts by section, group, and verdict\n")
    fh.write("section\tgroup\tverdict\tcount\n")
    for k in sorted(agg_counts.keys()):
        fh.write(f"{k[0]}\t{k[1]}\t{k[2]}\t{agg_counts[k]}\n")

print(f"Wrote {OUT_TSV} (651 rows) and {OUT_AGG}")
sys.exit(0)
