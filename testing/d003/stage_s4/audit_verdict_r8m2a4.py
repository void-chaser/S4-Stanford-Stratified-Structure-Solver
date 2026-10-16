#!/usr/bin/env python3
# audit_verdict_r8m2a4.py -- Audit defects of r8m2a3 verdict and execution chain.
# Outputs: $EV/VERDICT_AUDIT_R8_M2a4.tsv
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a4"))
OUT_FILE = os.path.join(EV, "VERDICT_AUDIT_R8_M2a4.tsv")

DEFECTS = [
    {
        "id": "D1",
        "category": "STATE_ANALYSIS",
        "location": "testing/d003/stage_s4/verdict_m2_r8m2a3.py:234-236,279-303",
        "count": 49,
        "affected_points": "M2-01 (12 points), M2-04 (2 points), M2-05 (4 points), M2-03 (31 points)",
        "description": "I1-I6 only compared as strings from input table; no gdb.log -> I-value analyzer existed in r8m2a3 execution chain.",
        "correction": "Implement state_judge_m2_r8m2a4.py (derived from r6c_judge.py) to parse gdb.log into objective HOLD/VIOLATED/N/A/UNJUDGED."
    },
    {
        "id": "D2",
        "category": "CONTROL_MAPPING",
        "location": "testing/d003/stage_s4/verdict_m2_r8m2a3.py:252-271; CONTROL_MAPPING_R8_M2a3.tsv:20-29",
        "count": 10,
        "affected_points": "M2-06-01-F3 (1 point), M2-07-INJ-*-ng5-F3 (9 points)",
        "description": "Byte-by-byte field output comparison applied to all 28 control mapping rows, including M2-06 and M2-07 injection rows (output_call=1, failed call) -> guaranteed OUTPUT_DIFF; driver_d003 writes S4FMM_DUMP1/S4FMM_DUMP instead of callN.txt -> guaranteed MISSING_DUMP.",
        "correction": "Separate output_assertion column (I6_ONLY, RECORD_ONLY, NONE); M2-06 and M2-07 injection rows set to RECORD_ONLY/NONE with no equality assertion; I6 compared only by state analyzer."
    },
    {
        "id": "D3",
        "category": "VERDICT_RULE",
        "location": "testing/d003/stage_s4/verdict_m2_r8m2a3.py:270,274; posctrl_m2_r8m2a3.py:126-130",
        "count": 18,
        "affected_points": "M2-01 (12 points), M2-04 (2 points), M2-05 (4 points)",
        "description": "I6 output differences recorded as SCHEMA_ERROR; Posctrl Case J codified this design error.",
        "correction": "I6 output discrepancy recorded as I6=VIOLATED -> MISMATCH(I6), not SCHEMA_ERROR; Case J updated in posctrl_m2_r8m2a4.py."
    },
    {
        "id": "D4",
        "category": "CLASS_RULE",
        "location": "testing/d003/stage_s4/verdict_m2_r8m2a3.py:209-214,288-289",
        "count": 1,
        "affected_points": "M2-10-01-B (1 point)",
        "description": "M2-10 exp_class=BASELINE_ONLY disjoint from judge_d003.classify output domain (CRASH, SILENT_SWALLOW, REPORTED_FAILURE, CONTROL_OK, INVALID) -> guaranteed MISMATCH.",
        "correction": "Add class_rule column to prereg v2 (JUDGE_D003 vs BASELINE_ONLY_RULE); BASELINE_ONLY_RULE validates facts (rc1, signal, hit, breakpoints) without classify."
    },
    {
        "id": "D5",
        "category": "DUAL_FAILURE",
        "location": "PREREG_M2_EFFECTIVE_R8_M2a3.tsv:14,15; testing/d003/stage_s4/inject_r8m2a2_dual_R3.cpp:153,157",
        "count": 2,
        "affected_points": "M2-04-01-F3, M2-04-02-F3 (2 points)",
        "description": "M2-04 only checked total exp_hit=2; no breakdown check for target 1 and target 2 hits (hit2); no INJECT2 INVALID/SUPPRESSED assertions; no assertion on second failure layer.",
        "correction": "Prereg v2 adds exp_hit1, exp_hit2, exp_inject2_invalid=0, exp_inject2_suppressed=0, k_before2, k_fail2, fail_layer1, fail_layer2."
    },
    {
        "id": "D6",
        "category": "STATE_ANALYSIS",
        "location": "testing/d003/stage_s4/r6c_judge.py:31-35",
        "count": 2,
        "affected_points": "M2-04-01-F3, M2-04-02-F3 (2 points)",
        "description": "r6c_judge.py index maps hardcoded inj_call in {1, 2}, cannot support M2-04 dual failure event sequence (call1 fail, call2 fail, call3 retry, retry_call=3).",
        "correction": "state_judge_m2_r8m2a4.py dynamically reads k_before, k_fail, k_before2, k_fail2, k_preretry, k_retry, retry_call from prereg row."
    },
    {
        "id": "D7",
        "category": "SANITIZER",
        "location": "PREREG_M2_EFFECTIVE_R8_M2a3.tsv:23-53; INVARIANT_SPEC_R8_M2a3.md:40-43",
        "count": 31,
        "affected_points": "M2-03 (31 points)",
        "description": "M2-03 lacked non-sanitizer reference point_id (U246 requirement of matching rc and class with non-san run unverifiable); ASAN/UBSAN_OPTIONS and san_reports counting rules not frozen.",
        "correction": "Prereg v2 adds san_ref_point_id (M2-01 reference for REP-INIT/POLY, M1 F3 frozen reference for G5/G6, NO_REF for unreferenced); freezes ASAN/UBSAN_OPTIONS with log_path under EV; freezes san_reports accumulation rules."
    },
    {
        "id": "D8",
        "category": "RUNNER_AND_FACTS",
        "location": "COMPLETENESS_R8_M2a3.tsv:1-151; checkpoints/p05/P05_S4R8_M2A3_REPORT.md:166-172",
        "count": 150,
        "affected_points": "All 150 points",
        "description": "No runner script or facts extraction script existed in r8m2a3; claiming 150/150 PASS in COMPLETENESS_R8_M2a3 was invalid.",
        "correction": "Implement run_m2_r8m2a4.py (--dry-run command planning) and facts_m2_r8m2a4.py; replace with COMPLETENESS v2 with accurate evidence chain traceability."
    },
    {
        "id": "D9",
        "category": "CONTROL_MAPPING",
        "location": "CONTROL_MAPPING_R8_M2a3.tsv:20-29",
        "count": 10,
        "affected_points": "M2-06-01-F3 (1 point), M2-07-INJ-*-ng5-F3 (9 points)",
        "description": "Failed calls erroneously mapped for output comparison under NANBUF_K1_COMPARISON and GRID_NG5_INJ_COMPARISON.",
        "correction": "Remove equality comparison expectations for failed calls; classify M2-06 as RECORD_ONLY and M2-07 injection rows as NONE."
    },
    {
        "id": "D10",
        "category": "VERDICT_RULE",
        "location": "testing/d003/stage_s4/verdict_m2_r8m2a3.py:238-249",
        "count": 18,
        "affected_points": "M2-01 (12 points), M2-04 (2 points), M2-05 (4 points)",
        "description": "Missing gdb private state classified as SCHEMA_ERROR instead of UNJUDGED_MISSING.",
        "correction": "verdict_m2_r8m2a4.py classifies missing evidence as UNJUDGED (distinguishing UNJUDGED_MISSING vs UNJUDGED_BY_DESIGN), reserving SCHEMA_ERROR for structural registry defects."
    },
    {
        "id": "D11",
        "category": "VERDICT_RULE",
        "location": "testing/d003/stage_s4/verdict_m2_r8m2a3.py:320-336",
        "count": 150,
        "affected_points": "All 150 points",
        "description": "Summary classification used non-partitioning labels (MISMATCH_AND_FLAKY) preventing exact 150 partition assertion.",
        "correction": "Establish strict precedence and mutually exclusive partition: SCHEMA_ERROR > UNJUDGED > FLAKY > MISMATCH > MATCH, asserting sum equals exactly 150."
    },
    {
        "id": "D12",
        "category": "CONTROL_CLASS_CONFLICT",
        "location": "PREREG_M2_EFFECTIVE_R8_M2a3.tsv:140; judge_d003.py:74-76,145",
        "count": 1,
        "affected_points": "M2-07-CTRL-vl-ng1-F3 (1 point)",
        "description": "M2-07-CTRL-vl-ng1-F3 has exp_rc1=20 and exp_class=CONTROL_OK; but judge_d003:145 returns INVALID for control vl ng1 native failure.",
        "correction": "verdict v2 accommodates INVALID for M2-07-CTRL-vl-ng1-F3 while preserving exp_class=CONTROL_OK (0 exp_* modification rule)."
    }
]


def main():
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    header = [
        "defect_id",
        "category",
        "source_location",
        "affected_point_count",
        "affected_point_ids",
        "defect_description",
        "corrective_action_r8m2a4"
    ]
    with open(OUT_FILE, "w", encoding="utf-8") as fh:
        fh.write("\t".join(header) + "\n")
        for d in DEFECTS:
            row = [
                d["id"],
                d["category"],
                d["location"],
                str(d["count"]),
                d["affected_points"],
                d["description"],
                d["correction"]
            ]
            fh.write("\t".join(row) + "\n")

    print(f"audit_verdict_r8m2a4: wrote {len(DEFECTS)} defects to {OUT_FILE}")


if __name__ == "__main__":
    main()
