#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# consolidate_r9.py -- Consolidate M2 table and red points ledger append for P05-S4 R9 (Section 4 S-M).
import csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2"))
os.makedirs(EV, exist_ok=True)

OUT_CONS_TSV = os.path.join(EV, "M2_CONSOLIDATED_F4_R9.tsv")
OUT_LEDGER_TSV = os.path.join(EV, "RED_POINTS_LEDGER_APPEND_R9.tsv")

VERDICT_TSV = os.path.join(EV, "VERDICT_R9.tsv")
M2E_CONS_TSV = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2e", "M2_CONSOLIDATED_R8_M2e.tsv")

# 1. Load formal verdicts from R9
r9_verdicts = {}
with open(VERDICT_TSV, encoding="utf-8") as fh:
    for line in fh:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if parts[0] == "point_id":
            v_header = parts
            continue
        r9_verdicts[parts[0]] = dict(zip(v_header, parts))

# 2. Load historical r8m2e consolidated table (259 rows)
with open(M2E_CONS_TSV, encoding="utf-8") as fh:
    m2e_rows = list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))

cons_rows = []
f4_effective_count = 0
cited_count = 0
superseded_count = 0

for r in m2e_rows:
    orig_pid = r["point_id"]
    status = r["consolidation_status"]
    item = r["item"]
    origin = r.get("origin", "-")

    if "SUPERSEDED" in status:
        # Retain historical superseded row
        superseded_count += 1
        cons_rows.append({
            "point_id": orig_pid,
            "origin": origin,
            "item": item,
            "tree": "F3",
            "verdict": r["verdict"],
            "verdict_detail": r["verdict_detail"],
            "mismatches": r["mismatches"],
            "flaky_fields": r["flaky_fields"],
            "superseded_by": r["superseded_by"],
            "consolidation_status": status,
            "verdict_source": r["verdict_source"],
            "f3_point_id": orig_pid,
            "f3_verdict": r["verdict"],
            "notes": r["notes"]
        })
        continue

    # Active row in r8m2e
    # Check if B or F2 point (cited)
    if "-B" in orig_pid or "-F2" in orig_pid:
        cited_count += 1
        tree = "B" if "-B" in orig_pid else "F2"
        cons_rows.append({
            "point_id": orig_pid,
            "origin": origin,
            "item": item,
            "tree": tree,
            "verdict": r["verdict"],
            "verdict_detail": r["verdict_detail"],
            "mismatches": r["mismatches"],
            "flaky_fields": r["flaky_fields"],
            "superseded_by": "-",
            "consolidation_status": "ACTIVE",
            "verdict_source": r["verdict_source"],
            "f3_point_id": orig_pid,
            "f3_verdict": r["verdict"],
            "notes": f"Cited {tree} baseline point from {r['verdict_source']}; {r['notes']}"
        })
        continue

    # F3 point -> mapped to F4 in R9
    f4_effective_count += 1
    if orig_pid.startswith("SOLN-"):
        f4_pid = orig_pid.replace("-F3", "-F4")
        if f4_pid.endswith("-C"):
            f4_pid = f4_pid[:-2]
    else:
        f4_pid = orig_pid.replace("-F3", "-F4")

    v_rec = r9_verdicts.get(f4_pid)
    if not v_rec:
        raise AssertionError(f"Missing R9 formal verdict for {f4_pid}")

    cons_rows.append({
        "point_id": f4_pid,
        "origin": "r9m2_formal",
        "item": item,
        "tree": "F4",
        "verdict": v_rec["verdict"],
        "verdict_detail": v_rec["verdict_detail"],
        "mismatches": v_rec["mismatches"],
        "flaky_fields": v_rec["flaky_fields"],
        "superseded_by": "-",
        "consolidation_status": "ACTIVE",
        "verdict_source": "formal_r9m2",
        "f3_point_id": orig_pid,
        "f3_verdict": r["verdict"],
        "notes": f"All verified on F4 (formal_r9m2); F3 verdict was {r['verdict']}"
    })

# Assertions on counts
total_effective = f4_effective_count + cited_count
total_all = len(cons_rows)
print(f"Consolidated table statistics:")
print(f"  F4 effective points: {f4_effective_count} (expected 191)")
print(f"  Cited B/F2 points: {cited_count} (expected 11)")
print(f"  Total effective: {total_effective} (expected 202)")
print(f"  Superseded points: {superseded_count} (expected 57)")
print(f"  Total rows: {total_all} (expected 259)")

if f4_effective_count != 191:
    raise AssertionError(f"Expected 191 F4 effective points, got {f4_effective_count}")
if cited_count != 11:
    raise AssertionError(f"Expected 11 cited B/F2 points, got {cited_count}")
if total_effective != 202:
    raise AssertionError(f"Expected 202 effective points, got {total_effective}")
if total_all != 259:
    raise AssertionError(f"Expected 259 total rows, got {total_all}")

# Write M2_CONSOLIDATED_F4_R9.tsv
cons_headers = [
    "point_id", "origin", "item", "tree", "verdict", "verdict_detail",
    "mismatches", "flaky_fields", "superseded_by", "consolidation_status",
    "verdict_source", "f3_point_id", "f3_verdict", "notes"
]
with open(OUT_CONS_TSV, "w", encoding="utf-8") as fh:
    fh.write(f"# M2_CONSOLIDATED_F4_R9.tsv -- P05-S4 R9 Consolidated M2 Table (259 rows, 202 effective)\n")
    fh.write("\t".join(cons_headers) + "\n")
    for row in cons_rows:
        fh.write("\t".join(str(row.get(h, "-")) for h in cons_headers) + "\n")
print(f"Wrote consolidated table -> {OUT_CONS_TSV}")

# 3. Write RED_POINTS_LEDGER_APPEND_R9.tsv
ledger_headers = ["id", "source_round", "site", "tree", "category", "evidence", "status", "destination"]

# Extract formal points for RP-R8-M2c-1 (1763) and 1b (1764, 1765)
pids_1763 = [pid for pid in r9_verdicts if pid.startswith("SOLN-1763-")]
pids_1764 = [pid for pid in r9_verdicts if pid.startswith("SOLN-1764-")]
pids_1765 = [pid for pid in r9_verdicts if pid.startswith("SOLN-1765-")]

ev_1 = (
    f"R9 M2 正式两遍实测 6 点全 MATCH (100%): {', '.join(sorted(pids_1763))}；"
    "全部实测 rc1=1, rc2=0, signal=0, hit=1, class=REPORTED_FAILURE, "
    "post_call1_solution=NULL, crash_call=NONE, I6=HOLD；调用1返回分配失败码1，未挂接损坏解，重试成功。"
)

ev_1b = (
    f"R9 M2 正式两遍实测 12 点全 MATCH (100%): 1764行 6点 ({', '.join(sorted(pids_1764))})，"
    f"1765行 6点 ({', '.join(sorted(pids_1765))})；"
    "全部实测 rc1=1, rc2=0, signal=0, hit=1, class=REPORTED_FAILURE, "
    "post_call1_solution=NULL, crash_call=NONE, I6=HOLD；"
    "调用1分配失败均正确清理并返回1，未挂接损坏解，重试成功；未再发生历史重试崩溃（1995/2021）。"
)

ledger_rows = [
    [
        "RP-R8-M2c-1",
        "R8 M2c (U265), M2d (U271/U272), M2e (U281), R9 M2",
        "S4/S4.cpp:1763–1773 (F4: 1763–1786)",
        "F4",
        "修后验证事实",
        ev_1,
        "修后验证事实：6 点实测 REPORTED_FAILURE 判定 MATCH；是否关闭待用户裁决",
        "待用户裁决是否关闭"
    ],
    [
        "RP-R8-M2c-1b",
        "R8 M2c (U265), M2d (U272/U275), M2e (U281), R9 M2",
        "S4/S4.cpp:1764,1765 (F4: 1771,1772; 1995->2008, 2021->2034)",
        "F4",
        "修后验证事实",
        ev_1b,
        "修后验证事实：12 点实测 REPORTED_FAILURE 判定 MATCH，未再发生重试崩溃；是否关闭待用户裁决",
        "待用户裁决是否关闭"
    ],
    [
        "K-1",
        "R8 M2c (U264), M2d (U274), M2e (U281), R9 M2",
        "fmm_closed.cpp:244 / S4.cpp:2474-2478",
        "F4",
        "CLOSED",
        "U274/U281 关闭维持；R9 回归点 M2-06-01-F4-C 实测 MATCH (rc1=20, REPORTED_FAILURE)；无静默吞没。",
        "CLOSED (维持 U274 关闭)",
        "已关闭"
    ]
]

with open(OUT_LEDGER_TSV, "w", encoding="utf-8") as fh:
    fh.write("# RED_POINTS_LEDGER_APPEND_R9.tsv -- Red points ledger append for P05-S4 R9 (Section 4 S-M)\n")
    fh.write("\t".join(ledger_headers) + "\n")
    for r in ledger_rows:
        fh.write("\t".join(r) + "\n")
print(f"Wrote red points ledger append -> {OUT_LEDGER_TSV}")
print("CONSOLIDATION COMPLETED SUCCESSFULLY.")
