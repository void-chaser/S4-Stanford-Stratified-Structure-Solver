#!/usr/bin/env python3
# build_prereg_v2_r8m2a4.py -- Generate PREREG_M2_EFFECTIVE_R8_M2a4.tsv and diff.
import csv
import hashlib
import os
import sys
from datetime import datetime, timezone

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a4"))
OLD_PREREG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "PREREG_M2_EFFECTIVE_R8_M2a3.tsv")

OUT_PREREG = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2a4.tsv")
OUT_SHA = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2a4.tsv.sha256")
OUT_TIME = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2a4_TIMESTAMP_UTC.txt")
OUT_DIFF = os.path.join(EV, "PREREG_DIFF_R8_M2a4.tsv")

STATE_JUDGE_REL = "testing/d003/stage_s4/state_judge_m2_r8m2a4.py"
STATE_JUDGE_PATH = os.path.join(REPO, STATE_JUDGE_REL)


def get_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def main():
    os.makedirs(EV, exist_ok=True)
    state_judge_sha = get_sha256(STATE_JUDGE_PATH)
    state_analyzer_str = f"{STATE_JUDGE_REL}:{state_judge_sha}"

    old_rows = []
    with open(OLD_PREREG, encoding="utf-8") as fh:
        r = csv.DictReader(fh, delimiter="\t")
        old_headers = r.fieldnames
        for row in r:
            old_rows.append(row)

    if len(old_rows) != 150:
        sys.exit(f"Expected 150 rows in old prereg, got {len(old_rows)}")

    # Define new columns
    # We will place new columns logically before basis and status
    new_cols = [
        "class_rule",
        "output_assertion",
        "exp_hit1",
        "exp_hit2",
        "exp_inject2_invalid",
        "exp_inject2_suppressed",
        "k_before2",
        "k_fail2",
        "fail_layer1",
        "fail_layer2",
        "san_ref_point_id",
        "san_options",
        "state_analyzer",
    ]

    # Target field order
    # Keep existing columns unchanged, insert new columns right before 'basis'
    basis_idx = old_headers.index("basis")
    target_headers = old_headers[:basis_idx] + new_cols + old_headers[basis_idx:]

    new_rows = []
    diff_records = []
    exp_mod_count = 0

    san_options_val = "ASAN_OPTIONS=detect_leaks=0:abort_on_error=0:log_path=$EV/run/pass{pass}/{point_id}/asan.log;UBSAN_OPTIONS=abort_on_error=0:log_path=$EV/run/pass{pass}/{point_id}/ubsan.log"

    for r in old_rows:
        pid = r["point_id"]
        item = r["item"]
        new_r = dict(r)

        # 1. class_rule
        if item == "M2-10" or pid == "M2-10-01-B":
            class_rule = "BASELINE_ONLY_RULE"
        else:
            class_rule = "JUDGE_D003"
        new_r["class_rule"] = class_rule

        # 2. output_assertion
        if item in ("M2-01", "M2-04", "M2-05") and r["control_group"] == "NO":
            out_assert = "I6_ONLY"
        elif item == "M2-06" and r["control_group"] == "NO":
            out_assert = "RECORD_ONLY"
        else:
            out_assert = "NONE"
        new_r["output_assertion"] = out_assert

        # 3. Dual failure columns
        if item == "M2-04":
            new_r["exp_hit1"] = "1"
            new_r["exp_hit2"] = "1"
            new_r["exp_inject2_invalid"] = "0"
            new_r["exp_inject2_suppressed"] = "0"
            new_r["k_before2"] = "2"
            new_r["k_fail2"] = "3"
            new_r["fail_layer1"] = "1"
            if pid == "M2-04-01-F3":
                new_r["fail_layer2"] = "1"
            else:
                new_r["fail_layer2"] = "UNRESOLVED"
        else:
            new_r["exp_hit1"] = "-"
            new_r["exp_hit2"] = "-"
            new_r["exp_inject2_invalid"] = "-"
            new_r["exp_inject2_suppressed"] = "-"
            new_r["k_before2"] = "-"
            new_r["k_fail2"] = "-"
            new_r["fail_layer1"] = "-"
            new_r["fail_layer2"] = "-"

        # 4. san_ref_point_id
        if item == "M2-03":
            if pid.startswith("M2-03-REP-INIT-01"):
                san_ref = "M2-01-01-F3"
            elif pid.startswith("M2-03-REP-INIT-02"):
                san_ref = "M2-01-02-F3"
            elif pid.startswith("M2-03-REP-INIT-03"):
                san_ref = "M2-01-03-F3"
            elif pid.startswith("M2-03-REP-INIT-04"):
                san_ref = "M2-01-04-F3"
            elif pid.startswith("M2-03-REP-INIT-05"):
                san_ref = "M2-01-05-F3"
            elif pid.startswith("M2-03-REP-INIT-06"):
                san_ref = "M2-01-06-F3"
            elif pid.startswith("M2-03-REP-POLY-11"):
                san_ref = "M2-01-11-F3"
            elif pid.startswith("M2-03-REP-POLY-12"):
                san_ref = "M2-01-12-F3"
            elif pid.startswith("M2-03-REP-POLY-14"):
                san_ref = "M2-01-14-F3"
            elif pid.startswith("M2-03-REP-POLY-16"):
                san_ref = "M2-01-16-F3"
            elif pid.startswith("M2-03-REP-POLY-18"):
                san_ref = "M2-01-18-F3"
            elif pid.startswith("M2-03-REP-POLY-20"):
                san_ref = "M2-01-20-F3"
            else:
                san_ref = "NO_REF"
        else:
            san_ref = "-"
        new_r["san_ref_point_id"] = san_ref

        # 5. san_options
        if item == "M2-03":
            new_r["san_options"] = san_options_val
        else:
            new_r["san_options"] = "-"

        # 6. state_analyzer
        if r["gdb_script"] not in ("-", "", None) and item in ("M2-01", "M2-04", "M2-05"):
            new_r["state_analyzer"] = state_analyzer_str
        else:
            new_r["state_analyzer"] = "-"

        # 7. status remains INFLUENCED
        new_r["status"] = "INFLUENCED"

        # 8. Basis append
        added_basis = []
        if item == "M2-04":
            added_basis.append("inject_r8m2a2_dual_R3.cpp:153,157,711; driver_r6b_state.cpp:227,238; INDEX_DERIVATION_R8_M2a2_R2B.tsv")
        if item == "M2-03":
            added_basis.append(f"san_ref={san_ref}; san_options frozen under EV; U246")
        if item == "M2-10":
            added_basis.append("class_rule=BASELINE_ONLY_RULE (m210_b_r8m2a2_R2.gdb breakpoint check; no classify)")
        if new_r["output_assertion"] != "NONE":
            added_basis.append(f"output_assertion={new_r['output_assertion']}")

        if added_basis:
            new_r["basis"] = r["basis"] + "; r8m2a4: " + "; ".join(added_basis)
        else:
            new_r["basis"] = r["basis"]

        # Track differences relative to r8m2a3
        for col in target_headers:
            old_val = r.get(col)
            new_val = new_r.get(col)
            if old_val is None:
                # New column
                diff_records.append((pid, col, "NEW_COLUMN", "-", str(new_val), "added in r8m2a4"))
            elif old_val != new_val:
                if col.startswith("exp_"):
                    exp_mod_count += 1
                diff_records.append((pid, col, "MODIFIED", str(old_val), str(new_val), "modified in r8m2a4"))

        new_rows.append(new_r)

    # Write PREREG_M2_EFFECTIVE_R8_M2a4.tsv
    with open(OUT_PREREG, "w", encoding="utf-8") as fh:
        fh.write("\t".join(target_headers) + "\n")
        for r in new_rows:
            fh.write("\t".join([str(r.get(c, "-")) for c in target_headers]) + "\n")

    prereg_sha = get_sha256(OUT_PREREG)
    with open(OUT_SHA, "w", encoding="utf-8") as fh:
        fh.write(f"{prereg_sha}  PREREG_M2_EFFECTIVE_R8_M2a4.tsv\n")

    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(OUT_TIME, "w", encoding="utf-8") as fh:
        fh.write(f"{now_utc}\n")

    # Write PREREG_DIFF_R8_M2a4.tsv
    diff_headers = ["point_id", "field", "diff_kind", "old_value_r8m2a3", "new_value_r8m2a4", "note"]
    with open(OUT_DIFF, "w", encoding="utf-8") as fh:
        fh.write("\t".join(diff_headers) + "\n")
        for d in diff_records:
            fh.write("\t".join(d) + "\n")

    print(f"Generated PREREG_M2_EFFECTIVE_R8_M2a4.tsv ({len(new_rows)} rows).")
    print(f"SHA256: {prereg_sha}")
    print(f"UTC Freeze Time: {now_utc}")
    print(f"Total diff entries: {len(diff_records)}")
    print(f"exp_* modification count: {exp_mod_count}")

    if exp_mod_count != 0:
        sys.exit(f"HARD FAILURE: exp_* modifications ({exp_mod_count}) must be exactly 0!")
    else:
        print("exp_* modification check PASSED: exactly 0 modifications.")


if __name__ == "__main__":
    main()
