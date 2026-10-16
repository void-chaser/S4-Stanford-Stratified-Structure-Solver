#!/usr/bin/env python3
# formal_m2_r8m2b.py -- Orchestrates formal two-pass execution of 174 points (P05-S4 R8 M2b §5 S-G).
# Runs pass 1 (174 points: main 150 + sanref 19 + win64 5), then pass 2 (174 points).
# No interleaving, no overwriting.
# Runs facts extraction, state analysis, verdict, and generates:
#  - FACTS_R8_M2b_pass{1,2}.tsv
#  - STATE_R8_M2b_pass{1,2}.tsv
#  - VERDICT_R8_M2b.tsv
#  - SUMMARY_R8_M2b.txt (asserts main 150, sanref 19, win64 5, total 174)
#  - RED_POINTS_R8_M2b.tsv
#  - CLASS_DIST_R8_M2b.tsv
import csv
import os
import shutil
import subprocess
import sys
from collections import Counter, OrderedDict

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b"))

PREREG_MAIN = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2b.tsv")
PREREG_SANREF = os.path.join(EV, "PREREG_M2_SANREF_R8_M2b.tsv")
PREREG_WIN64 = os.path.join(EV, "PREREG_M2_WIN64_R8_M2b.tsv")
PREREG_COMBINED = os.path.join(EV, "PREREG_M2_COMBINED_174_R8_M2b.tsv")

PLAN_TSV = os.path.join(EV, "COMMAND_PLAN_R8_M2b.tsv")
CTRL_MAP = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "CONTROL_MAPPING_R8_M2a3.tsv")

RUNNER_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "run_m2_r8m2b.py")
FACTS_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "facts_m2_r8m2b.py")
STATE_JUDGE_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "state_judge_m2_r8m2a4.py")
VERDICT_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "verdict_m2_r8m2b.py")

sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003 as judge  # noqa: E402


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))


def int_or_none(v):
    if v in (None, "", "-", "NA", "None", "MISSING", "TIMEOUT"):
        return None
    try:
        return int(v)
    except ValueError:
        return None


def main():
    print("=== Step 1: Combining 3 prereg tables (150 + 19 + 5 = 174) ===")
    main_rows = read_tsv(PREREG_MAIN)
    sanref_rows = read_tsv(PREREG_SANREF)
    win64_rows = read_tsv(PREREG_WIN64)

    if len(main_rows) != 150:
        sys.exit(f"FATAL: main rows {len(main_rows)} != 150")
    if len(sanref_rows) != 19:
        sys.exit(f"FATAL: sanref rows {len(sanref_rows)} != 19")
    if len(win64_rows) != 5:
        sys.exit(f"FATAL: win64 rows {len(win64_rows)} != 5")

    with open(PREREG_MAIN, encoding="utf-8") as fh:
        fieldnames = list(csv.DictReader(fh, delimiter="\t").fieldnames)

    combined_rows = main_rows + sanref_rows + win64_rows
    if len(combined_rows) != 174:
        sys.exit(f"FATAL: combined rows {len(combined_rows)} != 174")

    with open(PREREG_COMBINED, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames) + "\n")
        for r in combined_rows:
            fh.write("\t".join([r.get(f, "-") for f in fieldnames]) + "\n")
    print(f"Combined prereg written to {PREREG_COMBINED} (174 rows).")

    print("\n=== Step 2: Planning commands (dry-run) ===")
    r_plan = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                             "--prereg", PREREG_COMBINED,
                             "--ev", EV,
                             "--out-plan", PLAN_TSV,
                             "--dry-run"],
                            capture_output=True, text=True)
    print(r_plan.stdout)
    if r_plan.returncode != 0:
        sys.exit(f"FATAL: Planning failed: {r_plan.stderr}")

    plan_rows = read_tsv(PLAN_TSV)
    if len(plan_rows) != 348:
        sys.exit(f"FATAL: Planned commands count {len(plan_rows)} != 348 (174 * 2)")

    dollar_count = sum(1 for p in plan_rows if "$" in p["env_as_run"] or "$" in p["full_command_a"] or "$" in p["full_command_b"])
    if dollar_count != 0:
        sys.exit(f"FATAL: {dollar_count} commands contain unexpanded '$'")

    ident_fails = sum(1 for p in plan_rows if p["identity_status"] == "IDENTITY_FAIL")
    if ident_fails != 0:
        sys.exit(f"FATAL: {ident_fails} commands have IDENTITY_FAIL")

    print("Planning verified: 348 commands, 0 identity failures, 0 '$' characters.")

    print("\n=== Step 3: Formal Pass 1 Execution (174 points) ===")
    r_p1 = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                           "--prereg", PREREG_COMBINED,
                           "--ev", EV,
                           "--out-plan", PLAN_TSV,
                           "--pass", "1",
                           "--execute"],
                          capture_output=True, text=True)
    print(r_p1.stdout)
    if r_p1.returncode != 0:
        sys.exit(f"FATAL: Pass 1 execution failed: {r_p1.stderr}")

    print("\n=== Step 4: Formal Pass 2 Execution (174 points) ===")
    r_p2 = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                           "--prereg", PREREG_COMBINED,
                           "--ev", EV,
                           "--out-plan", PLAN_TSV,
                           "--pass", "2",
                           "--execute"],
                          capture_output=True, text=True)
    print(r_p2.stdout)
    if r_p2.returncode != 0:
        sys.exit(f"FATAL: Pass 2 execution failed: {r_p2.stderr}")

    print("\n=== Step 5: Facts Extraction (Pass 1 and Pass 2) ===")
    f1_tsv = os.path.join(EV, "FACTS_R8_M2b_pass1.tsv")
    f2_tsv = os.path.join(EV, "FACTS_R8_M2b_pass2.tsv")

    subprocess.run([sys.executable, "-I", "-B", FACTS_PY,
                    "--prereg", PREREG_COMBINED,
                    "--run-dir", os.path.join(EV, "run", "pass1"),
                    "--pass", "1",
                    "--out", f1_tsv], check=True)

    subprocess.run([sys.executable, "-I", "-B", FACTS_PY,
                    "--prereg", PREREG_COMBINED,
                    "--run-dir", os.path.join(EV, "run", "pass2"),
                    "--pass", "2",
                    "--out", f2_tsv], check=True)

    facts1 = read_tsv(f1_tsv)
    facts2 = read_tsv(f2_tsv)
    print(f"Facts extracted: Pass 1 has {len(facts1)} rows, Pass 2 has {len(facts2)} rows.")

    print("\n=== Step 6: State Analysis ===")
    s1_tsv = os.path.join(EV, "STATE_R8_M2b_pass1.tsv")
    s2_tsv = os.path.join(EV, "STATE_R8_M2b_pass2.tsv")
    s1_sum = os.path.join(EV, "STATE_SUMMARY_R8_M2b_pass1.txt")
    s2_sum = os.path.join(EV, "STATE_SUMMARY_R8_M2b_pass2.txt")

    # State analysis output
    s_combined_tsv = os.path.join(EV, "STATE_R8_M2b.tsv")
    s_combined_sum = os.path.join(EV, "STATE_SUMMARY_R8_M2b.txt")

    r_s1 = subprocess.run([sys.executable, "-I", "-B", STATE_JUDGE_PY,
                           "--prereg", PREREG_COMBINED,
                           "--control", CTRL_MAP,
                           "--ev", EV,
                           "--facts1", f1_tsv,
                           "--facts2", f2_tsv,
                           "--state-dir", os.path.join(EV, "run"),
                           "--dumps-dir", os.path.join(EV, "run"),
                           "--out-res", s_combined_tsv,
                           "--out-sum", s_combined_sum],
                          capture_output=True, text=True)
    print(r_s1.stdout)
    if r_s1.returncode != 0:
        sys.exit(f"FATAL: State judge failed: {r_s1.stderr}")

    # Split state into pass1 and pass2
    s_all_lines = open(s_combined_tsv, encoding="utf-8").readlines()
    header_line = s_all_lines[2] if len(s_all_lines) > 2 and s_all_lines[2].startswith("point_id") else s_all_lines[0]
    comment_lines = [l for l in s_all_lines if l.startswith("#")]
    p1_state_lines = [l for l in s_all_lines if not l.startswith("#") and "\t1\t" in l]
    p2_state_lines = [l for l in s_all_lines if not l.startswith("#") and "\t2\t" in l]

    with open(s1_tsv, "w", encoding="utf-8") as fh:
        for l in comment_lines:
            fh.write(l)
        fh.write(header_line)
        for l in p1_state_lines:
            fh.write(l)

    with open(s2_tsv, "w", encoding="utf-8") as fh:
        for l in comment_lines:
            fh.write(l)
        fh.write(header_line)
        for l in p2_state_lines:
            fh.write(l)

    print("\n=== Step 7: Verdict Engine (Main 150, SanRef 19, Win64 5, Combined 174) ===")
    scratch_tmp = os.path.join(EV, "tmp")

    # 7.1 Main 150 table verdict
    v_main_tsv = os.path.join(scratch_tmp, "VERDICT_MAIN_150.tsv")
    s_main_sum = os.path.join(scratch_tmp, "SUMMARY_MAIN_150.txt")
    subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                    "--prereg", PREREG_MAIN,
                    "--facts1", f1_tsv,
                    "--facts2", f2_tsv,
                    "--state1", s1_tsv,
                    "--state2", s2_tsv,
                    "--control-map", CTRL_MAP,
                    "--out-verdict", v_main_tsv,
                    "--out-summary", s_main_sum,
                    "--expected-total", "150"], check=True)

    # 7.2 SanRef 19 table verdict
    v_sanref_tsv = os.path.join(scratch_tmp, "VERDICT_SANREF_19.tsv")
    s_sanref_sum = os.path.join(scratch_tmp, "SUMMARY_SANREF_19.txt")
    subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                    "--prereg", PREREG_SANREF,
                    "--facts1", f1_tsv,
                    "--facts2", f2_tsv,
                    "--state1", s1_tsv,
                    "--state2", s2_tsv,
                    "--out-verdict", v_sanref_tsv,
                    "--out-summary", s_sanref_sum,
                    "--expected-total", "19"], check=True)

    # 7.3 Win64 5 table verdict
    v_win64_tsv = os.path.join(scratch_tmp, "VERDICT_WIN64_5.tsv")
    s_win64_sum = os.path.join(scratch_tmp, "SUMMARY_WIN64_5.txt")
    subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                    "--prereg", PREREG_WIN64,
                    "--facts1", f1_tsv,
                    "--facts2", f2_tsv,
                    "--state1", s1_tsv,
                    "--state2", s2_tsv,
                    "--control-map", CTRL_MAP,
                    "--out-verdict", v_win64_tsv,
                    "--out-summary", s_win64_sum,
                    "--expected-total", "5"], check=True)

    # 7.4 Formal combined 174 table verdict
    v_combined_tsv = os.path.join(EV, "VERDICT_R8_M2b.tsv")
    s_combined_sum = os.path.join(scratch_tmp, "SUMMARY_COMBINED_174.txt")
    subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                    "--prereg", PREREG_COMBINED,
                    "--facts1", f1_tsv,
                    "--facts2", f2_tsv,
                    "--state1", s1_tsv,
                    "--state2", s2_tsv,
                    "--control-map", CTRL_MAP,
                    "--out-verdict", v_combined_tsv,
                    "--out-summary", s_combined_sum,
                    "--expected-total", "174"], check=True)

    # Read verdicts
    verdict_rows = read_tsv(v_combined_tsv)
    verdict_map = {r["point_id"]: r for r in verdict_rows}

    # Summary texts
    with open(s_main_sum) as fh:
        sum_main_txt = fh.read()
    with open(s_sanref_sum) as fh:
        sum_sanref_txt = fh.read()
    with open(s_win64_sum) as fh:
        sum_win64_txt = fh.read()
    with open(s_combined_sum) as fh:
        sum_combined_txt = fh.read()

    # 7.5 Write SUMMARY_R8_M2b.txt
    out_summary_file = os.path.join(EV, "SUMMARY_R8_M2b.txt")
    summary_lines = [
        "# SUMMARY_R8_M2b.txt -- P05-S4 R8 M2b Formal Execution Summary",
        "# Table Totals Assertion: Main=150, SanRef=19, Win64=5, Grand Total=174",
        "",
        "============================================================",
        "=== SECTION 1: GRAND COMBINED SUMMARY (174 POINTS) ===",
        "============================================================",
        sum_combined_txt.strip(),
        "",
        "============================================================",
        "=== SECTION 2: MAIN MATRIX SUMMARY (150 POINTS) ===",
        "============================================================",
        sum_main_txt.strip(),
        "",
        "============================================================",
        "=== SECTION 3: SANREF MATRIX SUMMARY (19 POINTS) ===",
        "============================================================",
        sum_sanref_txt.strip(),
        "",
        "============================================================",
        "=== SECTION 4: WIN64 MATRIX SUMMARY (5 POINTS) ===",
        "============================================================",
        sum_win64_txt.strip(),
    ]
    with open(out_summary_file, "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary_lines) + "\n")
    print(f"Summary written to {out_summary_file}")

    # 7.6 Write RED_POINTS_R8_M2b.tsv
    red_headers = [
        "point_id", "item", "driver", "tree", "verdict", "verdict_detail",
        "mismatches", "flaky_fields", "pass1_rc_rc1_rc2_sig_hit", "pass2_rc_rc1_rc2_sig_hit",
        "gdb_divergent", "notes"
    ]
    facts1_map = {r["point_id"]: r for r in facts1}
    facts2_map = {r["point_id"]: r for r in facts2}

    red_rows = []
    for r in verdict_rows:
        pid = r["point_id"]
        v = r["verdict"]
        if v != "MATCH":
            f1 = facts1_map.get(pid, {})
            f2 = facts2_map.get(pid, {})
            p1_str = f"rc={f1.get('rc')},rc1={f1.get('rc1')},rc2={f1.get('rc2')},sig={f1.get('signal')},hit={f1.get('hit')}"
            p2_str = f"rc={f2.get('rc')},rc1={f2.get('rc1')},rc2={f2.get('rc2')},sig={f2.get('signal')},hit={f2.get('hit')}"
            red_rows.append([
                pid, r["item"], f1.get("driver", "-"), f1.get("tree", "-"),
                v, r["verdict_detail"], r["mismatches"], r["flaky_fields"],
                p1_str, p2_str, f1.get("gdb_divergent", "-"), r["notes"]
            ])

    red_tsv = os.path.join(EV, "RED_POINTS_R8_M2b.tsv")
    with open(red_tsv, "w", encoding="utf-8") as fh:
        fh.write("\t".join(red_headers) + "\n")
        for rr in red_rows:
            fh.write("\t".join(rr) + "\n")
    print(f"RED_POINTS_R8_M2b.tsv written with {len(red_rows)} red points.")

    # 7.7 Write CLASS_DIST_R8_M2b.tsv
    class_headers = [
        "point_id", "item", "tree", "driver", "control_group",
        "p1_rc", "p1_rc1", "p1_rc2", "p1_hit", "p1_class",
        "p2_rc", "p2_rc1", "p2_rc2", "p2_hit", "p2_class",
        "exp_class", "class_rule", "class_agreement"
    ]
    class_rows = []
    comb_prereg_dict = {r["point_id"]: r for r in combined_rows}

    for pid in [r["point_id"] for r in combined_rows]:
        pr = comb_prereg_dict[pid]
        f1 = facts1_map.get(pid, {})
        f2 = facts2_map.get(pid, {})
        is_ctrl = (pr.get("control_group") == "YES" or pr.get("exp_class") == "CONTROL_OK")
        c_rule = pr.get("class_rule", "JUDGE_D003")

        if c_rule == "BASELINE_ONLY_RULE":
            c1 = "BASELINE_ONLY"
            c2 = "BASELINE_ONLY"
        else:
            c1_t = judge.classify(int_or_none(f1.get("rc")), int_or_none(f1.get("rc1")),
                                  int_or_none(f1.get("rc2")), int_or_none(f1.get("hit", 0)), control=is_ctrl)
            c2_t = judge.classify(int_or_none(f2.get("rc")), int_or_none(f2.get("rc1")),
                                  int_or_none(f2.get("rc2")), int_or_none(f2.get("hit", 0)), control=is_ctrl)
            c1 = c1_t[0]
            c2 = c2_t[0]

        agree = "AGREE" if c1 == c2 else "DIFF"
        class_rows.append([
            pid, pr.get("item", "-"), pr.get("tree", "-"), pr.get("driver", "-"), pr.get("control_group", "-"),
            f1.get("rc", "-"), f1.get("rc1", "-"), f1.get("rc2", "-"), f1.get("hit", "-"), c1,
            f2.get("rc", "-"), f2.get("rc1", "-"), f2.get("rc2", "-"), f2.get("hit", "-"), c2,
            pr.get("exp_class", "-"), c_rule, agree
        ])

    class_dist_tsv = os.path.join(EV, "CLASS_DIST_R8_M2b.tsv")
    with open(class_dist_tsv, "w", encoding="utf-8") as fh:
        fh.write("\t".join(class_headers) + "\n")
        for cr in class_rows:
            fh.write("\t".join(cr) + "\n")
    print(f"CLASS_DIST_R8_M2b.tsv written with {len(class_rows)} points.")

    print("\nALL S-G STEPS COMPLETED SUCCESSFULLY.")


if __name__ == "__main__":
    main()
