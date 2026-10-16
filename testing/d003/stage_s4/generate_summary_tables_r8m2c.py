#!/usr/bin/env python3
# generate_summary_tables_r8m2c.py -- Generate red points, class dist, consolidated table, and ledger append.
import csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2c")
EV = os.environ.get("EV", os.path.join(REPO, EV_REL))

REJUDGE_TSV = os.path.join(EV, "REJUDGE_R8_M2b_v4.tsv")
VERDICT_DELTA_TSV = os.path.join(EV, "VERDICT_R8_M2c.tsv")
DELTA_PREREG_TSV = os.path.join(EV, "PREREG_M2_DELTA_R8_M2c.tsv")
FACTS1_DELTA_TSV = os.path.join(EV, "FACTS_R8_M2c_pass1.tsv")
FACTS2_DELTA_TSV = os.path.join(EV, "FACTS_R8_M2c_pass2.tsv")

RED_POINTS_TSV = os.path.join(EV, "RED_POINTS_R8_M2c.tsv")
CLASS_DIST_TSV = os.path.join(EV, "CLASS_DIST_R8_M2c.tsv")
CONSOLIDATED_TSV = os.path.join(EV, "M2_CONSOLIDATED_R8_M2c.tsv")
LEDGER_APPEND_TSV = os.path.join(EV, "RED_POINTS_LEDGER_APPEND_R8_M2c.tsv")

def read_tsv_list(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))

def main():
    os.makedirs(EV, exist_ok=True)

    rejudge_rows = read_tsv_list(REJUDGE_TSV)
    verdict_delta_rows = read_tsv_list(VERDICT_DELTA_TSV)
    delta_prereg = {r["point_id"]: r for r in read_tsv_list(DELTA_PREREG_TSV)}
    facts1_delta = {r["point_id"]: r for r in read_tsv_list(FACTS1_DELTA_TSV)}
    facts2_delta = {r["point_id"]: r for r in read_tsv_list(FACTS2_DELTA_TSV)}

    # 1. Generate RED_POINTS_R8_M2c.tsv (from delta verdict MISMATCH rows)
    red_points = []
    for r in verdict_delta_rows:
        if r["verdict"] == "MISMATCH":
            pid = r["point_id"]
            pr = delta_prereg.get(pid, {})
            f1 = facts1_delta.get(pid, {})
            f2 = facts2_delta.get(pid, {})

            p1_str = f"rc={f1.get('rc')},rc1={f1.get('rc1')},rc2={f1.get('rc2')},sig={f1.get('signal')},hit={f1.get('hit')}"
            p2_str = f"rc={f2.get('rc')},rc1={f2.get('rc1')},rc2={f2.get('rc2')},sig={f2.get('signal')},hit={f2.get('hit')}"

            red_points.append({
                "point_id": pid,
                "item": r.get("item", "-"),
                "driver": pr.get("driver", "-"),
                "tree": pr.get("tree", "-"),
                "verdict": r["verdict"],
                "verdict_detail": r["verdict_detail"],
                "mismatches": r["mismatches"],
                "flaky_fields": r["flaky_fields"],
                "pass1_rc_rc1_rc2_sig_hit": p1_str,
                "pass2_rc_rc1_rc2_sig_hit": p2_str,
                "gdb_divergent": f1.get("gdb_divergent", "-"),
                "notes": r["notes"]
            })

    rp_headers = ["point_id", "item", "driver", "tree", "verdict", "verdict_detail", "mismatches", "flaky_fields", "pass1_rc_rc1_rc2_sig_hit", "pass2_rc_rc1_rc2_sig_hit", "gdb_divergent", "notes"]
    with open(RED_POINTS_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rp_headers, delimiter="\t")
        writer.writeheader()
        for row in red_points:
            writer.writerow(row)
    print(f"generate_summary_tables_r8m2c: wrote {len(red_points)} rows to {RED_POINTS_TSV}")

    # 2. Generate CLASS_DIST_R8_M2c.tsv (for delta run)
    item_stats = {}
    for r in verdict_delta_rows:
        item = r.get("item", "-")
        v = r.get("verdict", "MATCH")
        v_det = r.get("verdict_detail", "")
        if item not in item_stats:
            item_stats[item] = {"MATCH": 0, "MISMATCH": 0, "FLAKY": 0, "GDB_DIVERGENT": 0, "UNJUDGED_DESIGN": 0, "UNJUDGED_MISSING": 0, "TOTAL": 0}
        item_stats[item]["TOTAL"] += 1
        if v in ("MATCH", "MISMATCH", "FLAKY", "GDB_DIVERGENT"):
            item_stats[item][v] += 1
        elif v == "UNJUDGED":
            if "DESIGN" in v_det:
                item_stats[item]["UNJUDGED_DESIGN"] += 1
            else:
                item_stats[item]["UNJUDGED_MISSING"] += 1

    cd_headers = ["item", "MATCH", "MISMATCH", "FLAKY", "GDB_DIVERGENT", "UNJUDGED_DESIGN", "UNJUDGED_MISSING", "TOTAL"]
    with open(CLASS_DIST_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=cd_headers, delimiter="\t")
        writer.writeheader()
        for it in sorted(item_stats):
            row = {"item": it}
            row.update(item_stats[it])
            writer.writerow(row)
    print(f"generate_summary_tables_r8m2c: wrote class distribution to {CLASS_DIST_TSV}")

    # 3. Generate M2_CONSOLIDATED_R8_M2c.tsv
    # Mapping of superseded rows from r8m2b
    superseded_set = {
        # M2-01 (6)
        "M2-01-01-F3": "M2-01-01-F3-C", "M2-01-02-F3": "M2-01-02-F3-C", "M2-01-03-F3": "M2-01-03-F3-C",
        "M2-01-04-F3": "M2-01-04-F3-C", "M2-01-05-F3": "M2-01-05-F3-C", "M2-01-06-F3": "M2-01-06-F3-C",
        # REP-INIT (6)
        "M2-03-REP-INIT-01-F3": "M2-03-REP-INIT-01-F3-C", "M2-03-REP-INIT-02-F3": "M2-03-REP-INIT-02-F3-C", "M2-03-REP-INIT-03-F3": "M2-03-REP-INIT-03-F3-C",
        "M2-03-REP-INIT-04-F3": "M2-03-REP-INIT-04-F3-C", "M2-03-REP-INIT-05-F3": "M2-03-REP-INIT-05-F3-C", "M2-03-REP-INIT-06-F3": "M2-03-REP-INIT-06-F3-C",
        # G6 (5)
        "M2-03-G6-01-F3": "M2-03-G6-01-F3-C", "M2-03-G6-03-F3": "M2-03-G6-03-F3-C", "M2-03-G6-04-F3": "M2-03-G6-04-F3-C",
        "M2-03-G6-05-F3": "M2-03-G6-05-F3-C", "M2-03-G6-06-F3": "M2-03-G6-06-F3-C",
        # SANREF-G6 (5)
        "M2-03-SANREF-G6-01-F3": "M2-03-SANREF-G6-01-F3-C", "M2-03-SANREF-G6-03-F3": "M2-03-SANREF-G6-03-F3-C", "M2-03-SANREF-G6-04-F3": "M2-03-SANREF-G6-04-F3-C",
        "M2-03-SANREF-G6-05-F3": "M2-03-SANREF-G6-05-F3-C", "M2-03-SANREF-G6-06-F3": "M2-03-SANREF-G6-06-F3-C",
        # vl-ng (3)
        "M2-07-CTRL-vl-ng2-F3": "M2-07-CTRL-vl-ng2-F3-C", "M2-07-CTRL-vl-ng3-F3": "M2-07-CTRL-vl-ng3-F3-C", "M2-07-CTRL-vl-ng4-F3": "M2-07-CTRL-vl-ng4-F3-C",
        # M2-05-P0 (1)
        "M2-05-P0-F3": "M2-05-P0-F3-C"
    }

    assert len(superseded_set) == 26, f"Superseded count {len(superseded_set)} != 26"

    consolidated_rows = []

    # 174 rejudged rows
    for r in rejudge_rows:
        pid = r["point_id"]
        is_sup = pid in superseded_set
        sup_by = superseded_set.get(pid, "-")
        c_status = "SUPERSEDED" if is_sup else "ACTIVE"
        consolidated_rows.append({
            "point_id": pid,
            "origin": "r8m2b_v4_rejudge",
            "item": r["item"],
            "verdict": r["verdict"],
            "verdict_detail": r["verdict_detail"],
            "mismatches": r["mismatches"],
            "flaky_fields": r["flaky_fields"],
            "superseded_by": sup_by,
            "consolidation_status": c_status,
            "notes": r["notes"]
        })

    # 54 delta rows
    for r in verdict_delta_rows:
        pid = r["point_id"]
        consolidated_rows.append({
            "point_id": pid,
            "origin": "r8m2c_delta",
            "item": r["item"],
            "verdict": r["verdict"],
            "verdict_detail": r["verdict_detail"],
            "mismatches": r["mismatches"],
            "flaky_fields": r["flaky_fields"],
            "superseded_by": "-",
            "consolidation_status": "ACTIVE",
            "notes": r["notes"]
        })

    total_all = len(consolidated_rows)
    active_rows = [r for r in consolidated_rows if r["consolidation_status"] == "ACTIVE"]
    effective_count = len(active_rows)

    assert total_all == 228, f"Total consolidated rows {total_all} != 228 (174 + 54)"
    assert effective_count == 202, f"Effective rows {effective_count} != 202 (174 + 54 - 26)"
    print(f"Consolidation assertion PASSED: total={total_all}, superseded=26, effective={effective_count} (174 + 54 - 26 = 202)")

    cons_headers = ["point_id", "origin", "item", "verdict", "verdict_detail", "mismatches", "flaky_fields", "superseded_by", "consolidation_status", "notes"]
    with open(CONSOLIDATED_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=cons_headers, delimiter="\t")
        writer.writeheader()
        for r in consolidated_rows:
            writer.writerow(r)
    print(f"generate_summary_tables_r8m2c: wrote {total_all} rows ({effective_count} active) to {CONSOLIDATED_TSV}")

    # Breakdown of effective rows:
    eff_matches = sum(1 for r in active_rows if r["verdict"] == "MATCH")
    eff_mismatches = sum(1 for r in active_rows if r["verdict"] == "MISMATCH")
    print(f"Effective breakdown: MATCH={eff_matches}, MISMATCH={eff_mismatches}, TOTAL={effective_count}")

    # 4. Generate RED_POINTS_LEDGER_APPEND_R8_M2c.tsv
    ledger_records = [
        {
            "id": "RP-R8-M2c-1",
            "source_round": "R8 M2c (U265)",
            "site": "S4/S4.cpp:1763-1766",
            "tree": "F3, B",
            "category": "F_CONFIRMED",
            "evidence": "checkpoints/p05/evidence/p05-s4r8/m2c/MALLOC_MAP_R8_M2c.tsv; ASAN SEGV at S4.cpp:1764 (dereference S->solution before NULL check)",
            "status": "OPEN (characterized, unrepaired)",
            "destination": "待用户裁决：S3R5 修复轮（改 S4.cpp InitSolution 判空清理，冻结新树 F4）或转 S5"
        },
        {
            "id": "RP-R8-M2c-1b",
            "source_round": "R8 M2c (U265)",
            "site": "S4/S4.cpp:1764,1765; 1798-1815",
            "tree": "F3, B",
            "category": "OBSERVATION",
            "evidence": "S4/S4.cpp:1764-1772, 1798-1815 [源码]; ab/solved failure returns 1 leaving S->solution non-NULL; retry Simulation_GetLayerSolution uses NULL pointer",
            "status": "[源码] 未验证",
            "destination": "与 RP-R8-M2c-1 一并待用户裁决"
        },
        {
            "id": "K-1",
            "source_round": "R8 M2c (U264)",
            "site": "fmm_closed.cpp:244 / S4.cpp:2474-2478",
            "tree": "F3",
            "category": "OBSERVATION",
            "evidence": "checkpoints/p05/evidence/p05-s4r8/m2c/diag/m206/M206_DIAG_SUMMARY.txt; rcwa.cpp:666 prints info=10, S4.cpp:2477 returns 20; K-1 silent swallow refuted on nan-F3",
            "status": "MISMATCH (refuted on nan-F3 model 1; returns rc 20)",
            "destination": "待用户裁决是否以「F3 上未复现」关闭"
        },
        {
            "id": "AUDIT-TRACE-M2c",
            "source_round": "R8 M2c (S-B)",
            "site": "SOURCE_TRACE_R8_M2c.tsv",
            "tree": "-",
            "category": "HARNESS_OR_PROCESS",
            "evidence": "checkpoints/p05/evidence/p05-s4r8/m2c/SOURCE_TRACE_R8_M2c.tsv (174 rows audited; 0 new diffs beyond F1-F3)",
            "status": "AUDIT_PASSED (0 new diffs)",
            "destination": "none"
        }
    ]

    ledger_headers = ["id", "source_round", "site", "tree", "category", "evidence", "status", "destination"]
    with open(LEDGER_APPEND_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ledger_headers, delimiter="\t")
        writer.writeheader()
        for r in ledger_records:
            writer.writerow(r)
    print(f"generate_summary_tables_r8m2c: wrote {len(ledger_records)} records to {LEDGER_APPEND_TSV}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
