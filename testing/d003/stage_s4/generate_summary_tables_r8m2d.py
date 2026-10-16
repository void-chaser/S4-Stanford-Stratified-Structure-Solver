#!/usr/bin/env python3
# generate_m2d_summary_tables.py -- Generates M2_CONSOLIDATED_R8_M2d.tsv, M2_F3_STATUS_R8_M2d.tsv,
# RED_POINTS_LEDGER_APPEND_R8_M2d.tsv, and REGRESSION_PLAN_F4_R8_M2d.tsv.
import csv
import os
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2d")
EV = os.environ.get("EV", os.path.join(REPO, EV_REL))

M2C_CONSOLIDATED = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2c", "M2_CONSOLIDATED_R8_M2c.tsv")
VERDICT_SMOKE_TSV = os.path.join(EV, "smoke", "VERDICT_SMOKE.tsv")
PREREG_M2D_TSV = os.path.join(EV, "PREREG_M2_DELTA_R8_M2d.tsv")

CONSOLIDATED_TSV = os.path.join(EV, "M2_CONSOLIDATED_R8_M2d.tsv")
F3_STATUS_TSV = os.path.join(EV, "M2_F3_STATUS_R8_M2d.tsv")
LEDGER_APPEND_TSV = os.path.join(EV, "RED_POINTS_LEDGER_APPEND_R8_M2d.tsv")
REGRESSION_PLAN_TSV = os.path.join(EV, "REGRESSION_PLAN_F4_R8_M2d.tsv")


def read_tsv_list(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))


def main():
    os.makedirs(EV, exist_ok=True)

    m2c_rows = read_tsv_list(M2C_CONSOLIDATED)
    smoke_verdict_rows = read_tsv_list(VERDICT_SMOKE_TSV)
    prereg_m2d = {r["point_id"]: r for r in read_tsv_list(PREREG_M2D_TSV)}

    # Newly superseded rows in r8m2d:
    # 1. M2-06-01-F3 -> M2-06-01-F3-C
    # 2. 27 SOLN rows from r8m2c -> SOLN-*-C (or -FA)
    m2d_superseded = {
        "M2-06-01-F3": "M2-06-01-F3-C",
        "SOLN-1763-closed2d-ng1-F3-dbg": "SOLN-1763-closed2d-ng1-F3-dbg-C",
        "SOLN-1763-closed2d-ng1-B-dbg": "SOLN-1763-closed2d-ng1-B-dbg-C",
        "SOLN-1763-closed2d-ng1-F3-san": "SOLN-1763-closed2d-ng1-F3-san-C",
        "SOLN-1763-fft-ng5-F3-dbg": "SOLN-1763-fft-ng5-F3-dbg-C",
        "SOLN-1763-fft-ng5-B-dbg": "SOLN-1763-fft-ng5-B-dbg-C",
        "SOLN-1763-fft-ng5-F3-san": "SOLN-1763-fft-ng5-F3-san-C",
        "SOLN-1763-kottke-ng5-F3-dbg": "SOLN-1763-kottke-ng5-F3-dbg-C",
        "SOLN-1763-kottke-ng5-B-dbg": "SOLN-1763-kottke-ng5-B-dbg-C",
        "SOLN-1763-kottke-ng5-F3-san": "SOLN-1763-kottke-ng5-F3-san-C",
        "SOLN-1764-closed2d-ng1-F3-dbg": "SOLN-1764-closed2d-ng1-F3-dbg-C",
        "SOLN-1764-closed2d-ng1-B-dbg": "SOLN-1764-closed2d-ng1-B-dbg-C",
        "SOLN-1764-closed2d-ng1-F3-san": "SOLN-1764-closed2d-ng1-F3-san-FA",
        "SOLN-1764-fft-ng5-F3-dbg": "SOLN-1764-fft-ng5-F3-dbg-C",
        "SOLN-1764-fft-ng5-B-dbg": "SOLN-1764-fft-ng5-B-dbg-C",
        "SOLN-1764-fft-ng5-F3-san": "SOLN-1764-fft-ng5-F3-san-FA",
        "SOLN-1764-kottke-ng5-F3-dbg": "SOLN-1764-kottke-ng5-F3-dbg-C",
        "SOLN-1764-kottke-ng5-B-dbg": "SOLN-1764-kottke-ng5-B-dbg-C",
        "SOLN-1764-kottke-ng5-F3-san": "SOLN-1764-kottke-ng5-F3-san-FA",
        "SOLN-1765-closed2d-ng1-F3-dbg": "SOLN-1765-closed2d-ng1-F3-dbg-C",
        "SOLN-1765-closed2d-ng1-B-dbg": "SOLN-1765-closed2d-ng1-B-dbg-C",
        "SOLN-1765-closed2d-ng1-F3-san": "SOLN-1765-closed2d-ng1-F3-san-C",
        "SOLN-1765-fft-ng5-F3-dbg": "SOLN-1765-fft-ng5-F3-dbg-C",
        "SOLN-1765-fft-ng5-B-dbg": "SOLN-1765-fft-ng5-B-dbg-C",
        "SOLN-1765-fft-ng5-F3-san": "SOLN-1765-fft-ng5-F3-san-C",
        "SOLN-1765-kottke-ng5-F3-dbg": "SOLN-1765-kottke-ng5-F3-dbg-C",
        "SOLN-1765-kottke-ng5-B-dbg": "SOLN-1765-kottke-ng5-B-dbg-C",
        "SOLN-1765-kottke-ng5-F3-san": "SOLN-1765-kottke-ng5-F3-san-C",
    }
    assert len(m2d_superseded) == 28, f"Expected 28 superseded rows, got {len(m2d_superseded)}"

    consolidated_rows = []

    # 1. Existing 228 rows from r8m2c
    for r in m2c_rows:
        pid = r["point_id"]
        c_status = r["consolidation_status"]
        sup_by = r["superseded_by"]

        if pid in m2d_superseded:
            c_status = "SUPERSEDED"
            sup_by = m2d_superseded[pid]

        consolidated_rows.append({
            "point_id": pid,
            "origin": r["origin"],
            "item": r["item"],
            "verdict": r["verdict"],
            "verdict_detail": r["verdict_detail"],
            "mismatches": r["mismatches"],
            "flaky_fields": r["flaky_fields"],
            "superseded_by": sup_by,
            "consolidation_status": c_status,
            "notes": r["notes"]
        })

    # 2. Append 28 delta rows from r8m2d
    for r in smoke_verdict_rows:
        pid = r["point_id"]
        consolidated_rows.append({
            "point_id": pid,
            "origin": "r8m2d_delta",
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
    superseded_rows = [r for r in consolidated_rows if r["consolidation_status"] == "SUPERSEDED"]
    active_rows = [r for r in consolidated_rows if r["consolidation_status"] == "ACTIVE"]

    total_sup = len(superseded_rows)
    effective_count = len(active_rows)

    # Assertions
    assert total_all == 256, f"Total consolidated rows {total_all} != 256 (228 + 28)"
    assert total_sup == 54, f"Total superseded rows {total_sup} != 54 (26 + 28)"
    assert effective_count == 202, f"Effective rows {effective_count} != 202 (256 - 54)"

    active_match = sum(1 for r in active_rows if r["verdict"] == "MATCH")
    active_mismatch = sum(1 for r in active_rows if r["verdict"] == "MISMATCH")
    active_flaky = sum(1 for r in active_rows if r["verdict"] == "FLAKY")
    active_gdb_div = sum(1 for r in active_rows if r["verdict"] == "GDB_DIVERGENT")
    active_unjudged = sum(1 for r in active_rows if r["verdict"] == "UNJUDGED")

    assert (active_match + active_mismatch + active_flaky + active_gdb_div + active_unjudged) == effective_count, \
        "Sum of categories does not equal effective count"

    # Write M2_CONSOLIDATED_R8_M2d.tsv
    c_headers = [
        "point_id", "origin", "item", "verdict", "verdict_detail",
        "mismatches", "flaky_fields", "superseded_by", "consolidation_status", "notes"
    ]
    with open(CONSOLIDATED_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=c_headers, delimiter="\t")
        fh.write("# M2_CONSOLIDATED_R8_M2d.tsv -- Consolidated M2 table v5 (256 rows, 202 effective)\n")
        writer.writeheader()
        for r in consolidated_rows:
            writer.writerow(r)

    print(f"Wrote {total_all} rows to {CONSOLIDATED_TSV} (effective {effective_count}: MATCH {active_match}, MISMATCH {active_mismatch})")

    # 3. Generate M2_F3_STATUS_R8_M2d.tsv
    # Split effective MATCH into "健康 MATCH" and "红点表征 MATCH"
    status_headers = ["point_id", "item", "tree", "verdict", "category_kind", "rp_id", "notes"]
    status_rows = []

    for r in active_rows:
        pid = r["point_id"]
        v = r["verdict"]
        item = r["item"]
        pr = prereg_m2d.get(pid, {})
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
            if "-FA" in pid:
                cat_kind = "红点表征未命中 (S4_FAIL_ALLOC_AT 待授权/待 arm)"
                rp_id = "RP-R8-M2c-1 (S4_FAIL_ALLOC_AT)"
            else:
                cat_kind = "MISMATCH"
                rp_id = "-"

        status_rows.append({
            "point_id": pid,
            "item": item,
            "tree": tree,
            "verdict": v,
            "category_kind": cat_kind,
            "rp_id": rp_id,
            "notes": r["notes"]
        })

    with open(F3_STATUS_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=status_headers, delimiter="\t")
        fh.write("# M2_F3_STATUS_R8_M2d.tsv -- Effective points status breakdown (healthy match vs red-point characterization match)\n")
        writer.writeheader()
        for r in status_rows:
            writer.writerow(r)

    n_healthy = sum(1 for r in status_rows if r["category_kind"] == "健康 MATCH")
    n_rp_match = sum(1 for r in status_rows if "红点表征 MATCH" in r["category_kind"])
    print(f"Wrote {len(status_rows)} status rows -> {F3_STATUS_TSV} (健康 MATCH: {n_healthy}, 红点表征 MATCH: {n_rp_match})")

    # 4. Generate RED_POINTS_LEDGER_APPEND_R8_M2d.tsv
    ledger_entries = [
        {
            "id": "RP-R8-M2c-1",
            "source_round": "R8 M2c (U265), M2d (U271/U272)",
            "site": "S4/S4.cpp:1763–1766 (B: 1754–1757)",
            "tree": "F3, B",
            "category": "F_CONFIRMED",
            "evidence": "S4MALLOC_MAP_R8_M2d.tsv; ASAN SEGV at S4.cpp:1764 (调用1 driver_r6b_state.cpp:211); S->solution 解引用空指针崩溃。改正 r8m2c 误写 1773 的问题。",
            "status": "OPEN (已表征，待修复)",
            "destination": "P05-S3R5 修复轮（改 S4.cpp InitSolution 判空清理，冻结新树 F4）"
        },
        {
            "id": "RP-R8-M2c-1b",
            "source_round": "R8 M2c (U265), M2d (U272/U275)",
            "site": "S4/S4.cpp:1764,1765; 1802; 1995,2021 (B: 1755,1756; 1793; 1986,2012)",
            "tree": "F3, B",
            "category": "F_CONFIRMED",
            "evidence": "实测证实：R6BSTATE 1 记录 solution solved 非 NULL；S4.cpp:1802 重试跳过 InitSolution；调用 2（driver_r6b_state.cpp:227）解引用空指针；1764 经 bt 24 确认崩于 S4.cpp:1995 memset(pab)；1765 经 ASAN/bt 确认崩于 S4.cpp:2021 sol->solved。升级为 F_CONFIRMED。",
            "status": "OPEN (已实测证实重试崩溃，待修复)",
            "destination": "P05-S3R5 修复轮（与 RP-R8-M2c-1 一并修复）"
        },
        {
            "id": "K-1",
            "source_round": "R8 M2c (U264), M2d (U274)",
            "site": "fmm_closed.cpp:244 / S4.cpp:2474-2478",
            "tree": "F3",
            "category": "CLOSED",
            "evidence": "U274; M206_DIAG_SUMMARY.txt; F3 nan 驱动 tensor NG=5 model 1 上未复现静默吞没：NaN 到达本征求解 info=10，S4.cpp:2477 return 20。M2-06-01-F3-C 实测 MATCH（rc1=20, REPORTED_FAILURE）。",
            "status": "CLOSED (带范围声明关闭：本装置与模型下未复现静默吞没，由 U274 关闭)",
            "destination": "关闭"
        }
    ]

    ledger_headers = ["id", "source_round", "site", "tree", "category", "evidence", "status", "destination"]
    with open(LEDGER_APPEND_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=ledger_headers, delimiter="\t")
        fh.write("# RED_POINTS_LEDGER_APPEND_R8_M2d.tsv -- Red points ledger append for r8m2d\n")
        writer.writeheader()
        for r in ledger_entries:
            writer.writerow(r)

    print(f"Wrote {len(ledger_entries)} entries to {LEDGER_APPEND_TSV}")

    # 5. Generate REGRESSION_PLAN_F4_R8_M2d.tsv
    reg_headers = [
        "point_id", "f4_driver", "f4_exp_rc1", "f4_exp_rc2", "f4_exp_class",
        "f4_exp_init_clean", "f4_exp_crash_call", "b_baseline_behavior", "notes"
    ]
    reg_rows = []

    soln_ids = [r["point_id"] for r in smoke_verdict_rows if "SOLN-" in r["point_id"]]
    for pid in soln_ids:
        is_b = "-B-" in pid
        reg_rows.append({
            "point_id": pid,
            "f4_driver": "init-F4-dbg" if "dbg" in pid else "init-F4-san",
            "f4_exp_rc1": "1" if not is_b else "-",
            "f4_exp_rc2": "0" if not is_b else "-",
            "f4_exp_class": "REPORTED_FAILURE" if not is_b else "CRASH",
            "f4_exp_init_clean": "HOLD" if not is_b else "-",
            "f4_exp_crash_call": "NONE" if not is_b else ("1" if "1763" in pid else "2"),
            "b_baseline_behavior": "CRASH at call 1 (1763) or call 2 (1764/1765) [BASELINE_ONLY 非修复证据]" if is_b else "对照基线依然崩溃",
            "notes": "S3R5 修后：分配失败立即置 S->solution=NULL 并报 S4_MSG 返回 1；调用2重试时 S->solution==NULL 重新进入 InitSolution 成功"
        })

    with open(REGRESSION_PLAN_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=reg_headers, delimiter="\t")
        fh.write("# REGRESSION_PLAN_F4_R8_M2d.tsv -- F4 regression plan for SOLN 27 points\n")
        writer.writeheader()
        for r in reg_rows:
            writer.writerow(r)

    print(f"Wrote {len(reg_rows)} regression rows to {REGRESSION_PLAN_TSV}")
    return 0


if __name__ == "__main__":
    main()
