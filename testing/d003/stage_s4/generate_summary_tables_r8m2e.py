#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2e; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# generate_summary_tables_r8m2e.py -- Generates M2_CONSOLIDATED_R8_M2e.tsv, M2_F3_STATUS_R8_M2e.tsv,
# RED_POINTS_LEDGER_APPEND_R8_M2e.tsv for P05-S4 R8 M2e (S-I, S-K).
import argparse, csv, os, sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2e")
EV = os.environ.get("EV", os.path.join(REPO, EV_REL))

M2D_CONSOLIDATED = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2d", "M2_CONSOLIDATED_R8_M2d.tsv")
VERDICT_FORMAL_TSV = os.path.join(EV, "formal", "VERDICT_R8_M2e.tsv")
PREREG_FORMAL_TSV = os.path.join(EV, "PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv")

CONSOLIDATED_TSV = os.path.join(EV, "M2_CONSOLIDATED_R8_M2e.tsv")
F3_STATUS_TSV = os.path.join(EV, "M2_F3_STATUS_R8_M2e.tsv")
LEDGER_APPEND_TSV = os.path.join(EV, "RED_POINTS_LEDGER_APPEND_R8_M2e.tsv")


def read_tsv_list(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))


def main():
    parser = argparse.ArgumentParser(description="P05-S4 summary tables generator v6")
    parser.add_argument("--m2d-consolidated", default=M2D_CONSOLIDATED, help="Path to M2_CONSOLIDATED_R8_M2d.tsv")
    parser.add_argument("--verdict-formal", default=VERDICT_FORMAL_TSV, help="Path to VERDICT_R8_M2e.tsv")
    parser.add_argument("--prereg-formal", default=PREREG_FORMAL_TSV, help="Path to PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv")
    parser.add_argument("--out-consolidated", default=CONSOLIDATED_TSV, help="Output consolidated TSV path")
    parser.add_argument("--out-f3-status", default=F3_STATUS_TSV, help="Output F3 status TSV path")
    parser.add_argument("--out-ledger", default=LEDGER_APPEND_TSV, help="Output red points ledger append TSV path")
    parser.add_argument("--ev", default=EV, help="Evidence directory")

    args = parser.parse_args()
    os.makedirs(args.ev, exist_ok=True)

    m2d_rows = read_tsv_list(args.m2d_consolidated)
    formal_verdicts = {r["point_id"]: r for r in read_tsv_list(args.verdict_formal)}
    prereg_formal = {r["point_id"]: r for r in read_tsv_list(args.prereg_formal)}

    # Check that formal verdicts cover all 28 expected rows
    assert len(formal_verdicts) == 28, f"Expected 28 formal verdicts, got {len(formal_verdicts)}"

    consolidated_rows = []

    # 1. First 228 rows (174 r8m2b + 54 r8m2c) from M2d consolidated table
    # Set verdict_source = formal_r8m2b or formal_r8m2c
    for r in m2d_rows[:228]:
        pid = r["point_id"]
        origin = r["origin"]
        v_source = "formal_r8m2b" if origin == "r8m2b_v4_rejudge" else "formal_r8m2c"
        consolidated_rows.append({
            "point_id": pid,
            "origin": origin,
            "item": r["item"],
            "verdict": r["verdict"],
            "verdict_detail": r["verdict_detail"],
            "mismatches": r["mismatches"],
            "flaky_fields": r["flaky_fields"],
            "superseded_by": r["superseded_by"],
            "consolidation_status": r["consolidation_status"],
            "verdict_source": v_source,
            "notes": r["notes"]
        })

    # 2. Next 28 rows from M2d (the r8m2d_delta rows)
    # 25 non-FA rows: update with formal run results from r8m2e (verdict_source = formal_r8m2e, ACTIVE)
    # 3 -FA rows: supersede by -AL rows (verdict_source = smoke_r8m2d, SUPERSEDED)
    for r in m2d_rows[228:256]:
        pid = r["point_id"]
        if pid.endswith("-san-FA"):
            al_pid = pid.replace("-san-FA", "-san-AL")
            consolidated_rows.append({
                "point_id": pid,
                "origin": "r8m2d_delta",
                "item": r["item"],
                "verdict": r["verdict"],
                "verdict_detail": r["verdict_detail"],
                "mismatches": r["mismatches"],
                "flaky_fields": r["flaky_fields"],
                "superseded_by": al_pid,
                "consolidation_status": "SUPERSEDED",
                "verdict_source": "smoke_r8m2d",
                "notes": f"superseded by {al_pid} per U276/U279 (apparatus error: S4_FAIL_ALLOC_AT not armed)"
            })
        else:
            fv = formal_verdicts[pid]
            consolidated_rows.append({
                "point_id": pid,
                "origin": "r8m2d_delta",
                "item": r["item"],
                "verdict": fv["verdict"],
                "verdict_detail": fv["verdict_detail"],
                "mismatches": fv["mismatches"],
                "flaky_fields": fv["flaky_fields"],
                "superseded_by": "-",
                "consolidation_status": "ACTIVE",
                "verdict_source": "formal_r8m2e",
                "notes": f"formal run in r8m2e ({fv['notes']})"
            })

    # 3. Add 3 new -AL rows from r8m2e
    for al_pid in [
        "SOLN-1764-closed2d-ng1-F3-san-AL",
        "SOLN-1764-fft-ng5-F3-san-AL",
        "SOLN-1764-kottke-ng5-F3-san-AL"
    ]:
        fv = formal_verdicts[al_pid]
        consolidated_rows.append({
            "point_id": al_pid,
            "origin": "r8m2e_delta",
            "item": "SOLN-1764",
            "verdict": fv["verdict"],
            "verdict_detail": fv["verdict_detail"],
            "mismatches": fv["mismatches"],
            "flaky_fields": fv["flaky_fields"],
            "superseded_by": "-",
            "consolidation_status": "ACTIVE",
            "verdict_source": "formal_r8m2e",
            "notes": f"formal run in r8m2e (malloc_aligned injection; {fv['notes']})"
        })

    total_all = len(consolidated_rows)
    superseded_rows = [r for r in consolidated_rows if r["consolidation_status"] == "SUPERSEDED"]
    active_rows = [r for r in consolidated_rows if r["consolidation_status"] == "ACTIVE"]
    total_sup = len(superseded_rows)
    effective_count = len(active_rows)

    active_match = sum(1 for r in active_rows if r["verdict"] == "MATCH")
    active_mismatch = sum(1 for r in active_rows if r["verdict"] == "MISMATCH")
    active_flaky = sum(1 for r in active_rows if r["verdict"] == "FLAKY")
    active_gdb_div = sum(1 for r in active_rows if r["verdict"] == "GDB_DIVERGENT")
    active_categories_sum = active_match + active_mismatch + active_flaky + active_gdb_div

    # Assertions per S-I
    print("=== S-I ASSERTIONS EVALUATION ===")
    print(f"Assertion 1 (Total rows): 174 + 54 + 28 + 3 = 259. Actual: {total_all}")
    assert total_all == 259, f"Total rows {total_all} != 259 (174 + 54 + 28 + 3)"

    print(f"Assertion 2 (SUPERSEDED rows): 26 + 28 + 3 = 57. Actual: {total_sup}")
    print(f"  Note on counting: (27 r8m2b sup in r8m2c/d + 27 r8m2c sup in r8m2d + 3 -FA sup in r8m2e = 57)")
    print(f"  Or: (26 r8m2b in r8m2c + 28 in r8m2d [1 r8m2b + 27 r8m2c] + 3 -FA in r8m2e = 57)")
    assert total_sup == 57, f"Total superseded {total_sup} != 57"

    print(f"Assertion 3 (Effective rows): 259 - 57 = 202. Actual: {effective_count}")
    assert effective_count == 202, f"Effective rows {effective_count} != 202"

    print(f"Assertion 4 (Categories sum): MATCH({active_match}) + MISMATCH({active_mismatch}) + FLAKY({active_flaky}) + GDB_DIV({active_gdb_div}) = {active_categories_sum}. Expected: 202")
    assert active_categories_sum == 202, f"Active categories sum {active_categories_sum} != 202"

    # Assertion: in active rows, verdict_source must NOT start with smoke_
    active_smoke_sources = [r["point_id"] for r in active_rows if r["verdict_source"].startswith("smoke_")]
    print(f"Assertion 5 (No smoke_* in active rows): Found {len(active_smoke_sources)} smoke sources in active rows")
    assert len(active_smoke_sources) == 0, f"Found smoke sources in active rows: {active_smoke_sources}"

    # Write M2_CONSOLIDATED_R8_M2e.tsv
    c_headers = [
        "point_id", "origin", "item", "verdict", "verdict_detail",
        "mismatches", "flaky_fields", "superseded_by", "consolidation_status", "verdict_source", "notes"
    ]
    with open(args.out_consolidated, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=c_headers, delimiter="\t")
        fh.write("# M2_CONSOLIDATED_R8_M2e.tsv -- Consolidated M2 table v6 (259 rows, 202 effective)\n")
        writer.writeheader()
        for r in consolidated_rows:
            writer.writerow(r)

    print(f"Wrote {total_all} rows to {args.out_consolidated}")

    # Write M2_F3_STATUS_R8_M2e.tsv
    status_headers = ["point_id", "item", "tree", "verdict", "category_kind", "rp_id", "verdict_source", "notes"]
    status_rows = []

    for r in active_rows:
        pid = r["point_id"]
        v = r["verdict"]
        item = r["item"]
        pr = prereg_formal.get(pid, {})
        tree = pr.get("tree", "F3")

        cat_kind = "-"
        rp_id = "-"

        if v == "MATCH":
            if "SOLN-1763" in pid:
                cat_kind = "红点表征 MATCH (CRASH类)"
                rp_id = "RP-R8-M2c-1"
            elif "SOLN-1764" in pid:
                cat_kind = "红点表征 MATCH (CRASH类)"
                rp_id = "RP-R8-M2c-1b"
            elif "SOLN-1765" in pid:
                cat_kind = "红点表征 MATCH (CRASH类)"
                rp_id = "RP-R8-M2c-1b"
            else:
                cat_kind = "健康 MATCH"
                rp_id = "-"
        elif v == "MISMATCH":
            cat_kind = "MISMATCH"
            rp_id = "-"

        status_rows.append({
            "point_id": pid,
            "item": item,
            "tree": tree,
            "verdict": v,
            "category_kind": cat_kind,
            "rp_id": rp_id,
            "verdict_source": r["verdict_source"],
            "notes": r["notes"]
        })

    with open(args.out_f3_status, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=status_headers, delimiter="\t")
        fh.write("# M2_F3_STATUS_R8_M2e.tsv -- Effective points status breakdown v6 (healthy match vs red-point characterization match)\n")
        writer.writeheader()
        for r in status_rows:
            writer.writerow(r)

    n_healthy = sum(1 for r in status_rows if r["category_kind"] == "健康 MATCH")
    n_rp_match = sum(1 for r in status_rows if "红点表征 MATCH" in r["category_kind"])
    print(f"Wrote {len(status_rows)} status rows to {args.out_f3_status} (healthy: {n_healthy}, rp_match: {n_rp_match})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
