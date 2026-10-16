#!/usr/bin/env python3
# replay_r6c_r8m2a4.py -- Replay historical R6c evidence using state_judge_m2_r8m2a4.py.
# Verifies zero differences against checkpoints/p05/evidence/p05-s4r6c/RESULTS_R6c_STATE.tsv.
# Outputs: $EV/REPLAY_R6c_R8_M2a4.tsv and $EV/REPLAY_R6c_SUMMARY_R8_M2a4.txt
import csv
import os
import subprocess
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a4"))
R6C_EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r6c")
R6C_PREREG = os.path.join(R6C_EV, "REGISTRY_S4_PRE_R6b_STATE_v2.tsv")
R6C_CTRL = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r6b", "REGISTRY_S4_PRE_R6b_CONTROL.tsv")
HIST_RESULTS = os.path.join(R6C_EV, "RESULTS_R6c_STATE.tsv")

REPLAY_RES = os.path.join(EV, "RESULTS_R6c_REPLAY_RAW.tsv")
REPLAY_SUM = os.path.join(EV, "STATE_SUMMARY_R6c_REPLAY_RAW.txt")
OUT_TSV = os.path.join(EV, "REPLAY_R6c_R8_M2a4.tsv")
OUT_SUM = os.path.join(EV, "REPLAY_R6c_SUMMARY_R8_M2a4.txt")

INV_LIST = ["I1", "I2", "I3", "I4", "I5", "I6"]


def read_tsv_rows(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        r = csv.DictReader((line for line in fh if not line.startswith("#")), delimiter="\t")
        for row in r:
            rows.append(row)
    return rows


def main():
    os.makedirs(EV, exist_ok=True)
    if os.path.exists(REPLAY_RES):
        os.remove(REPLAY_RES)
    if os.path.exists(REPLAY_SUM):
        os.remove(REPLAY_SUM)

    # 1. Run state_judge_m2_r8m2a4.py on R6c inputs
    judge_py = os.path.join(REPO, "testing", "d003", "stage_s4", "state_judge_m2_r8m2a4.py")
    cmd = [
        sys.executable, "-I", "-B", judge_py,
        "--prereg", R6C_PREREG,
        "--control", R6C_CTRL,
        "--ev", R6C_EV,
        "--out-res", REPLAY_RES,
        "--out-sum", REPLAY_SUM,
    ]
    print("Running state analyzer on historical R6c evidence...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("STDOUT:", res.stdout)
        print("STDERR:", res.stderr)
        sys.exit(f"state_judge_m2_r8m2a4.py failed with returncode {res.returncode}")

    print(res.stdout.strip())

    # 2. Compare REPLAY_RES with HIST_RESULTS
    hist_rows = read_tsv_rows(HIST_RESULTS)
    replay_rows = read_tsv_rows(REPLAY_RES)

    hist_by_key = {(r["point_id"], r["pass"]): r for r in hist_rows}
    replay_by_key = {(r["point_id"], r["pass"]): r for r in replay_rows}

    if len(hist_by_key) != 354 or len(replay_by_key) != 354:
        sys.exit(f"Row count mismatch: hist={len(hist_by_key)}, replay={len(replay_by_key)}, expected 354")

    diffs = []
    comparison_records = []

    total_checks = 0
    match_checks = 0

    header = [
        "point_id", "pass", "invariant", "hist_verdict", "replay_verdict",
        "hist_point_verdict", "replay_point_verdict", "diff_flag", "notes"
    ]

    for key in sorted(hist_by_key.keys()):
        pid, pas = key
        hr = hist_by_key[key]
        rr = replay_by_key.get(key)
        if not rr:
            diffs.append((pid, pas, "ALL", "EXISTS", "MISSING", "Row missing in replay"))
            continue

        for inv in INV_LIST:
            total_checks += 1
            hv = hr[inv]
            rv = rr[inv]
            hpv = hr["point_verdict"]
            rpv = rr["point_verdict"]
            is_same = (hv == rv and hpv == rpv)
            if is_same:
                match_checks += 1
                flag = "SAME"
            else:
                flag = "DIFF"
                diffs.append((pid, pas, inv, hv, rv, f"hist={hv}, replay={rv}"))

            comparison_records.append([
                pid, pas, inv, hv, rv, hpv, rpv, flag, hr.get("notes", "")
            ])

    with open(OUT_TSV, "w", encoding="utf-8") as fh:
        fh.write("\t".join(header) + "\n")
        for rec in comparison_records:
            fh.write("\t".join(rec) + "\n")

    summary_text = [
        "# REPLAY_R6c_SUMMARY_R8_M2a4 -- Historical R6c State Analysis Replay Summary",
        f"points_evaluated: 177",
        f"passes_evaluated: 2",
        f"total_point_pass_rows: {len(hist_by_key)}",
        f"invariants_checked_per_row: 6 (I1, I2, I3, I4, I5, I6)",
        f"total_invariant_checks: {total_checks} (177 * 2 * 6)",
        f"matching_invariant_checks: {match_checks}",
        f"differing_invariant_checks: {len(diffs)}",
        f"replay_status: {'PASS_ZERO_DIFFERENCE' if len(diffs) == 0 else 'FAIL_DIFFERENCES_FOUND'}",
    ]
    if diffs:
        summary_text.append("\nDifferences:")
        for d in diffs:
            summary_text.append(f"  {d[0]} pass {d[1]} {d[2]}: {d[5]}")

    with open(OUT_SUM, "w", encoding="utf-8") as fh:
        fh.write("\n".join(summary_text) + "\n")

    print("\n".join(summary_text))

    if len(diffs) != 0:
        sys.exit(f"Replay verification failed: {len(diffs)} differences found!")
    else:
        print("Replay verification SUCCESSFUL: 0 differences across 2124 invariant checks.")


if __name__ == "__main__":
    main()
