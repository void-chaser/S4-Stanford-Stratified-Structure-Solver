#!/usr/bin/env python3
# completeness_m2_r8m2b.py -- Generates COMPLETENESS_R8_M2b.tsv based on actual run results (P05-S4 R8 M2b §5 S-H).
# Enforces allowed completeness statuses:
#  JUDGED (MATCH, MISMATCH, FLAKY, GDB_DIVERGENT), UNJUDGED_MISSING, UNJUDGED_BY_DESIGN, NOT_RUN_UNRESOLVED_INDEX.
# Strictly asserts totals for Main (150), SanRef (19), Win64 (5), and Combined (174).
import csv
import os
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b"))

PREREG_COMBINED = os.path.join(EV, "PREREG_M2_COMBINED_174_R8_M2b.tsv")
VERDICT_TSV = os.path.join(EV, "VERDICT_R8_M2b.tsv")
PLAN_TSV = os.path.join(EV, "COMMAND_PLAN_R8_M2b.tsv")
FACTS1_TSV = os.path.join(EV, "FACTS_R8_M2b_pass1.tsv")

OUT_COMPLETENESS = os.path.join(EV, "COMPLETENESS_R8_M2b.tsv")
OUT_SUMMARY = os.path.join(EV, "COMPLETENESS_SUMMARY_R8_M2b.txt")


def read_tsv_dict(path, key_col="point_id"):
    rows = {}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"):
            rows[r[key_col]] = r
    return rows


def main():
    prereg = read_tsv_dict(PREREG_COMBINED)
    verdict = read_tsv_dict(VERDICT_TSV)
    plan_rows = {}
    with open(PLAN_TSV, encoding="utf-8") as fh:
        for r in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"):
            pid = r["point_id"]
            pas = r["pass"]
            cmd_id = r["command_id"]
            if pid not in plan_rows:
                plan_rows[pid] = {}
            plan_rows[pid][pas] = cmd_id

    completeness_rows = []
    status_counts = {
        "JUDGED": 0,
        "UNJUDGED_MISSING": 0,
        "UNJUDGED_BY_DESIGN": 0,
        "NOT_RUN_UNRESOLVED_INDEX": 0,
    }
    verdict_subcounts = {
        "MATCH": 0,
        "MISMATCH": 0,
        "FLAKY": 0,
        "GDB_DIVERGENT": 0,
    }
    table_counts = {
        "MAIN": {"JUDGED": 0, "UNJUDGED_MISSING": 0, "UNJUDGED_BY_DESIGN": 0, "NOT_RUN_UNRESOLVED_INDEX": 0},
        "SANREF": {"JUDGED": 0, "UNJUDGED_MISSING": 0, "UNJUDGED_BY_DESIGN": 0, "NOT_RUN_UNRESOLVED_INDEX": 0},
        "WIN64": {"JUDGED": 0, "UNJUDGED_MISSING": 0, "UNJUDGED_BY_DESIGN": 0, "NOT_RUN_UNRESOLVED_INDEX": 0},
    }

    for pid, pr in prereg.items():
        v = verdict.get(pid, {})
        v_primary = v.get("verdict", "UNJUDGED")
        v_detail = v.get("verdict_detail", "UNJUDGED_MISSING")

        # Determine table membership
        item = pr.get("item", "")
        if item == "M2-03-SANREF":
            tbl = "SANREF"
        elif "win:64" in pr.get("env", ""):
            tbl = "WIN64"
        else:
            tbl = "MAIN"

        # Determine completeness status
        if v_primary in ("MATCH", "MISMATCH", "FLAKY", "GDB_DIVERGENT"):
            c_status = "JUDGED"
            verdict_subcounts[v_primary] += 1
        elif v_detail == "UNJUDGED_BY_DESIGN":
            c_status = "UNJUDGED_BY_DESIGN"
        elif v_detail == "UNJUDGED_MISSING":
            c_status = "UNJUDGED_MISSING"
        elif "UNRESOLVED_INDEX" in pr.get("basis", ""):
            c_status = "NOT_RUN_UNRESOLVED_INDEX"
        else:
            c_status = "UNJUDGED_MISSING"

        status_counts[c_status] += 1
        table_counts[tbl][c_status] += 1

        p1_cmd = plan_rows.get(pid, {}).get("1", "-")
        p2_cmd = plan_rows.get(pid, {}).get("2", "-")
        plan_str = f"p1_cmd={p1_cmd},p2_cmd={p2_cmd}"

        has_gdb = (pr.get("gdb_script") not in (None, "", "-"))
        if has_gdb:
            facts_src = "stdout:rc1,rc2; exitcode:rc,signal; gdb.log:inferior_rc,hit,m210; dumps:call*.txt"
            analysis_rule = f"{pr.get('state_analyzer', 'state_judge').split(':')[0]}(I1..I6) + verdict_m2_r8m2b.py({pr.get('class_rule')})"
        else:
            facts_src = "stdout:rc1,rc2; exitcode:rc,signal; dumps:call*.txt"
            analysis_rule = f"verdict_m2_r8m2b.py({pr.get('class_rule')})"

        ctrl_ref = pr.get("control_point_id", "-")
        if ctrl_ref in (None, "", "-"):
            ctrl_ref = pr.get("san_ref_point_id", "-")

        notes = v.get("notes", "-")
        if v.get("mismatches") not in (None, "", "-"):
            notes = f"mismatches={v['mismatches']}; {notes}"

        completeness_rows.append([
            pid, item, plan_str, facts_src, analysis_rule, ctrl_ref,
            v_primary, c_status, notes
        ])

    # Assertions
    total_evaluated = sum(status_counts.values())
    main_total = sum(table_counts["MAIN"].values())
    sanref_total = sum(table_counts["SANREF"].values())
    win64_total = sum(table_counts["WIN64"].values())

    if total_evaluated != 174:
        sys.exit(f"FATAL: Total evaluated {total_evaluated} != 174")
    if main_total != 150:
        sys.exit(f"FATAL: Main total {main_total} != 150")
    if sanref_total != 19:
        sys.exit(f"FATAL: SanRef total {sanref_total} != 19")
    if win64_total != 5:
        sys.exit(f"FATAL: Win64 total {win64_total} != 5")

    # Write COMPLETENESS TSV
    headers = [
        "point_id", "item", "command_plan_rows", "facts_sources", "analysis_rules",
        "control_or_ref", "actual_verdict", "completeness_status", "blocker_or_limitation_note"
    ]
    with open(OUT_COMPLETENESS, "w", encoding="utf-8") as fh:
        fh.write("\t".join(headers) + "\n")
        for r in completeness_rows:
            fh.write("\t".join(r) + "\n")

    # Write SUMMARY TXT
    sum_lines = [
        "# COMPLETENESS_SUMMARY_R8_M2b.txt -- P05-S4 R8 M2b Completeness Summary",
        f"Total points evaluated: {total_evaluated} (ASSERT 174 == 174: PASS)",
        f"Main matrix: {main_total} (ASSERT 150 == 150: PASS)",
        f"SanRef matrix: {sanref_total} (ASSERT 19 == 19: PASS)",
        f"Win64 matrix: {win64_total} (ASSERT 5 == 5: PASS)",
        "",
        "## Status breakdown (Overall 174):",
        f"JUDGED: {status_counts['JUDGED']} (MATCH={verdict_subcounts['MATCH']}, MISMATCH={verdict_subcounts['MISMATCH']}, FLAKY={verdict_subcounts['FLAKY']}, GDB_DIVERGENT={verdict_subcounts['GDB_DIVERGENT']})",
        f"UNJUDGED_MISSING: {status_counts['UNJUDGED_MISSING']}",
        f"UNJUDGED_BY_DESIGN: {status_counts['UNJUDGED_BY_DESIGN']}",
        f"NOT_RUN_UNRESOLVED_INDEX: {status_counts['NOT_RUN_UNRESOLVED_INDEX']}",
        "",
        "## Table-by-table breakdown:",
        "matrix\tJUDGED\tUNJUDGED_MISSING\tUNJUDGED_BY_DESIGN\tNOT_RUN_UNRESOLVED\tTOTAL",
        f"MAIN\t{table_counts['MAIN']['JUDGED']}\t{table_counts['MAIN']['UNJUDGED_MISSING']}\t{table_counts['MAIN']['UNJUDGED_BY_DESIGN']}\t{table_counts['MAIN']['NOT_RUN_UNRESOLVED_INDEX']}\t{main_total}",
        f"SANREF\t{table_counts['SANREF']['JUDGED']}\t{table_counts['SANREF']['UNJUDGED_MISSING']}\t{table_counts['SANREF']['UNJUDGED_BY_DESIGN']}\t{table_counts['SANREF']['NOT_RUN_UNRESOLVED_INDEX']}\t{sanref_total}",
        f"WIN64\t{table_counts['WIN64']['JUDGED']}\t{table_counts['WIN64']['UNJUDGED_MISSING']}\t{table_counts['WIN64']['UNJUDGED_BY_DESIGN']}\t{table_counts['WIN64']['NOT_RUN_UNRESOLVED_INDEX']}\t{win64_total}",
        f"GRAND_TOTAL\t{status_counts['JUDGED']}\t{status_counts['UNJUDGED_MISSING']}\t{status_counts['UNJUDGED_BY_DESIGN']}\t{status_counts['NOT_RUN_UNRESOLVED_INDEX']}\t{total_evaluated}",
    ]
    with open(OUT_SUMMARY, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sum_lines) + "\n")

    print("\n".join(sum_lines))
    print(f"Completeness written to {OUT_COMPLETENESS}")


if __name__ == "__main__":
    main()
