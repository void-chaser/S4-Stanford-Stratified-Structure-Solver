#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# compare_f3_f4_r9m1.py -- Field-by-field equivalence comparison between F3 frozen facts and F4 results (Rule U306). New file.
import argparse, csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DEFAULT_EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1"))

def clean_base_env(env_str):
    parts = [p.strip() for p in env_str.split(";") if p.strip()]
    kept = []
    for p in parts:
        k = p.split("=")[0]
        if k.startswith("S4FMM_INJECT") or k.startswith("S4FMM_NTH") or k.startswith("S4FMM_TWICE"):
            continue
        kept.append(p)
    return ";".join(sorted(kept))

def load_f3_facts():
    # 1. Load M1b F3 results
    res_b1 = {}
    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b1/RESULTS_M1B_R8_M1b1.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t"):
            if r["tree"] == "F3":
                res_b1[(r["group"], r["point_id"])] = r

    res_b3 = {}
    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/RESULTS_SUPP_R8_M1b3.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t"):
            if r["tree"] == "F3":
                res_b3[(r["group"], r["point_id"])] = r

    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1b/r8m1b3/EFFECTIVE_M1B_R8_M1b3.tsv"), encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
        h = lines[0]
        eff_m1b = [dict(zip(h, l)) for l in lines[1:] if dict(zip(h, l))["tree"] == "F3"]

    facts = {}
    for r in eff_m1b:
        grp = r["group"]
        pid = r["point_id"]
        src = r["source"]
        if src == "M1b1_ENV_AGREE":
            f3_r = res_b1[(grp, pid)]
            rc1 = str(f3_r["p1_rc1"])
            rc2 = str(f3_r["p1_rc2"])
            rc3 = "-"
            hit = str(f3_r["p1_hit"])
            cls = str(f3_r["p1_class"])
            env = f3_r["env"]
        elif src == "SUPP_R8_M1b3":
            f3_r = res_b3[(grp, pid)]
            rc1 = str(f3_r["p1_rc1"])
            rc2 = str(f3_r["p1_rc2"])
            rc3 = "-"
            hit = str(f3_r["p1_hit"])
            cls = str(f3_r["p1_class"])
            env = f3_r["env_as_run"]
        elif src == "M1b1_NOT_RUN":
            rc1 = "-"
            rc2 = "-"
            rc3 = "-"
            hit = "-"
            cls = "NOT_RUN_REGISTRY_ERROR"
            env = "NOT_RUN"
        else:
            continue

        key = ("M1b", grp, pid)
        facts[key] = {
            "section": "M1b", "group": grp, "point_id": pid,
            "rc1": rc1, "rc2": rc2, "rc3": rc3, "hit": hit, "class": cls,
            "I1": "-", "I2": "-", "I3": "-", "I4": "-", "I5": "-", "I6": "-",
            "env": env, "base_env": clean_base_env(env), "effective_verdict": r["effective_verdict"]
        }

    # 2. Load M1c F3 facts
    g5_f3 = {}
    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c3/M1C_F3_STATE_R6c_pass1.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t"):
            g5_f3[r["id"]] = r

    seam_f3 = {}
    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c3/M1C_F3_STATE_SEAM_R6c_pass1.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t"):
            seam_f3[r["id"]] = r

    g5_judgements = {}
    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c3/M1C_F3_RESULTS_R6c_STATE.tsv"), encoding="utf-8") as f:
        for r in csv.DictReader((l for l in f if not l.startswith("#")), delimiter="\t"):
            if r.get("pass") == "1":
                g5_judgements[r["point_id"]] = r

    with open(os.path.join(REPO, "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv"), encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            if r["tree"] == "F3":
                pid = r["point_id_r8"]
                grp = r["group"]
                base_id = r["base_id"]
                if grp in ("G5", "CTRL_AUX"):
                    f3_r = g5_f3[base_id]
                    j = g5_judgements.get(base_id, {})
                    rc1 = str(f3_r.get("gdb_rc1", f3_r.get("nogdb_rc1", "-")))
                    rc2 = str(f3_r.get("gdb_rc2", f3_r.get("nogdb_rc2", "-")))
                    rc3 = str(f3_r.get("gdb_rc3", f3_r.get("nogdb_rc3", "-")))
                    hit = str(f3_r.get("gdb_hit", f3_r.get("nogdb_hit", "-")))
                    i1 = str(j.get("I1", "-"))
                    i2 = str(j.get("I2", "-"))
                    i3 = str(j.get("I3", "-"))
                    i4 = str(j.get("I4", "-"))
                    i5 = str(j.get("I5", "-"))
                    i6 = str(j.get("I6", "-"))
                    cls = str(j.get("point_verdict", "HOLD" if grp == "G5" else "CONTROL_OK"))
                else:
                    f3_r = seam_f3[base_id]
                    rc1 = str(f3_r.get("gdb_rc1", f3_r.get("nogdb_rc1", "-")))
                    rc2 = str(f3_r.get("gdb_rc2", f3_r.get("nogdb_rc2", "-")))
                    rc3 = "-"
                    hit = str(f3_r.get("gdb_hit", f3_r.get("nogdb_hit", "-")))
                    i1 = i2 = i3 = i4 = i5 = i6 = "-"
                    cls = "HOLD" if grp == "G6" else "CONTROL_OK"

                key = ("M1c", grp, pid)
                facts[key] = {
                    "section": "M1c", "group": grp, "point_id": pid,
                    "rc1": rc1, "rc2": rc2, "rc3": rc3, "hit": hit, "class": cls,
                    "I1": i1, "I2": i2, "I3": i3, "I4": i4, "I5": i5, "I6": i6,
                    "env": r["env_expected"], "base_env": clean_base_env(r["env_expected"]), "effective_verdict": "MATCH"
                }

    assert len(facts) == 651, f"Expected 651 F3 facts, got {len(facts)}"
    return facts

def load_f4_results(path):
    rows = {}
    with open(path, "r", encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
        if not lines:
            return rows
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            sec = r.get("section", "M1b")
            grp = r.get("group", "")
            pid = r.get("f3_point_id", r.get("point_id"))
            key = (sec, grp, pid)
            rows[key] = r
    return rows

def compare(f3_facts, f4_data):
    results = []
    total_diffs = 0
    both_empty_count = 0
    nonempty_identical_count = 0
    divergent_hit_count = 0

    for key in sorted(f3_facts.keys()):
        sec, grp, pid = key
        f3 = f3_facts[key]
        f4 = f4_data.get(key)
        if not f4:
            results.append([sec, grp, "MISSING", pid, "-", f3["rc1"], "NO", "-", f3["rc2"], "NO", "-", f3["rc3"], "NO", "-", f3["hit"], "NO", "-", f3["class"], "NO", "NO", "NO", "NO", "NO", "NO", "NO", "NO", "DIVERGENT", "DIFF", "MISSING_F4_ROW"])
            total_diffs += 1
            divergent_hit_count += 1
            continue

        f4_pid = f4.get("point_id", "-")
        rc1_m = (str(f4.get("rc1", "")) == f3["rc1"])
        rc2_m = (str(f4.get("rc2", "")) == f3["rc2"])
        rc3_m = (str(f4.get("rc3", "")) == f3["rc3"])
        hit_m = (str(f4.get("hit", "")) == f3["hit"])
        cls_m = (str(f4.get("class", "")) == f3["class"])

        i_matches = []
        for iname in ("I1", "I2", "I3", "I4", "I5", "I6"):
            i_matches.append(str(f4.get(iname, "")) == f3[iname])

        env_m = (clean_base_env(f4.get("env", "")) == f3["base_env"]) or (f3["env"] == "NOT_RUN")

        # HIT classification
        h3_val = int(f3["hit"]) if f3["hit"].isdigit() else -1
        h4_val = int(f4.get("hit", "-1")) if str(f4.get("hit", "")).isdigit() else -1

        if (h3_val == 0 and h4_val == 0) or (f3["hit"] == "-" and str(f4.get("hit")) in ("-", "0")):
            hit_cat = "BOTH_EMPTY"
            both_empty_count += 1
        elif h3_val > 0 and h3_val == h4_val:
            hit_cat = "NONEMPTY_IDENTICAL"
            nonempty_identical_count += 1
        else:
            hit_cat = "DIVERGENT"
            divergent_hit_count += 1

        diff_fields = []
        if not rc1_m: diff_fields.append("rc1")
        if not rc2_m: diff_fields.append("rc2")
        if not rc3_m: diff_fields.append("rc3")
        if not hit_m: diff_fields.append("hit")
        if not cls_m: diff_fields.append("class")
        for idx, im in enumerate(i_matches, 1):
            if not im: diff_fields.append(f"I{idx}")
        if not env_m: diff_fields.append("env")

        row_v = "EQUIV" if not diff_fields else "DIFF"
        if row_v == "DIFF":
            total_diffs += 1

        results.append([
            sec, grp, f4_pid, pid,
            str(f4.get("rc1", "-")), f3["rc1"], "MATCH" if rc1_m else "MISMATCH",
            str(f4.get("rc2", "-")), f3["rc2"], "MATCH" if rc2_m else "MISMATCH",
            str(f4.get("rc3", "-")), f3["rc3"], "MATCH" if rc3_m else "MISMATCH",
            str(f4.get("hit", "-")), f3["hit"], "MATCH" if hit_m else "MISMATCH",
            str(f4.get("class", "-")), f3["class"], "MATCH" if cls_m else "MISMATCH",
            *["MATCH" if m else "MISMATCH" for m in i_matches],
            "MATCH" if env_m else "MISMATCH",
            hit_cat, row_v, ";".join(diff_fields) if diff_fields else "NONE"
        ])

    return results, total_diffs, both_empty_count, nonempty_identical_count, divergent_hit_count

def main():
    parser = argparse.ArgumentParser(description="Compare F3 frozen facts with F4 results.")
    parser.add_argument("--f4", default=None, help="Path to F4 results TSV (if omitted, uses F3 frozen facts as self-test)")
    parser.add_argument("--tamper", default=None, help="Path to tampered F3 facts TSV for positive control")
    parser.add_argument("--out", default=os.path.join(DEFAULT_EV, "F3_F4_EQUIV_R9M1.tsv"), help="Output path")
    args = parser.parse_args()

    f3_facts = load_f3_facts()

    if args.tamper:
        f4_data = load_f4_results(args.tamper)
    elif args.f4:
        f4_data = load_f4_results(args.f4)
    else:
        f4_data = f3_facts

    results, total_diffs, both_empty, nonempty_id, divergent_hits = compare(f3_facts, f4_data)

    header = [
        "section", "group", "point_id_f4", "point_id_f3",
        "rc1_f4", "rc1_f3", "rc1_match",
        "rc2_f4", "rc2_f3", "rc2_match",
        "rc3_f4", "rc3_f3", "rc3_match",
        "hit_f4", "hit_f3", "hit_match",
        "class_f4", "class_f3", "class_match",
        "I1_match", "I2_match", "I3_match", "I4_match", "I5_match", "I6_match",
        "env_match", "hit_category", "row_verdict", "difference_fields"
    ]

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write(f"# F3_F4_EQUIV_R9M1.tsv -- Field-by-field equivalence comparison (CHECKS={len(results)}, DIFFS={total_diffs})\n")
        fh.write(f"# HIT counts: BOTH_EMPTY={both_empty}, NONEMPTY_IDENTICAL={nonempty_id}, DIVERGENT={divergent_hits}\n")
        fh.write("\t".join(header) + "\n")
        for r in results:
            fh.write("\t".join(r) + "\n")

    print(f"Comparison complete: ROWS={len(results)}, DIFFS={total_diffs}")
    print(f"HIT counts: BOTH_EMPTY={both_empty}, NONEMPTY_IDENTICAL={nonempty_id}, DIVERGENT={divergent_hits}")
    print(f"Output -> {args.out}")
    return total_diffs

if __name__ == "__main__":
    sys.exit(main())
