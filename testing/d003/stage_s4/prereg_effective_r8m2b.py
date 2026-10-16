#!/usr/bin/env python3
# prereg_effective_r8m2b.py -- Generates PREREG_M2_EFFECTIVE_R8_M2b.tsv (150 rows),
# PREREG_M2_SANREF_R8_M2b.tsv (19 rows), PREREG_DIFF_R8_M2b.tsv, and APPARATUS_R8_M2b.tsv.
# Enforces:
#  - Exactly 0 exp_* changes between v2 and v3.
#  - Only allowed changes in v3: M2-10 gdb sha (U254), 19 san_ref_point_id (U257),
#    M2-07-CTRL-vl-ng1-F3 class_rule (U255), and basis column.
#  - Computes sha256 and writes timestamps and hashes.
import csv
import datetime
import hashlib
import os
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
PREREG_V2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a4", "PREREG_M2_EFFECTIVE_R8_M2a4.tsv")

EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b"))

OUT_V3 = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2b.tsv")
OUT_V3_SHA = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2b.tsv.sha256")
OUT_V3_TIME = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2b_TIMESTAMP_UTC.txt")

OUT_SANREF = os.path.join(EV, "PREREG_M2_SANREF_R8_M2b.tsv")
OUT_SANREF_SHA = os.path.join(EV, "PREREG_M2_SANREF_R8_M2b.tsv.sha256")
OUT_SANREF_TIME = os.path.join(EV, "PREREG_M2_SANREF_R8_M2b_TIMESTAMP_UTC.txt")

OUT_DIFF = os.path.join(EV, "PREREG_DIFF_R8_M2b.tsv")
OUT_APPARATUS = os.path.join(EV, "APPARATUS_R8_M2b.tsv")

R6BSTATE_DBG_SHA = "8b269be6e21f7c74fa40a268ed6226e91e481e06000523e8cf0f9942b6e06cdd"
F3_DBG_LIB_SHA = "56f72c5882d4293bbb2d45a272d7c7727e401085b900854b1f49b851effd897a"

R6BSEAM_SEAMF_SHA = "4c882f730c7966f8ff2bead0ec9119ca78969ccb69c635d4c63f0c0ea46ea5f1"
F3_SEAMF_LIB_SHA = "16d43d3ce6fc32ecb07bcfc467bd272b25949fdfecdf8ef1506b4fb6fb82add3"

M210_GDB_ACTUAL_SHA = "d1fc549859f311543ce4b1aaeb23f3adee8a8204b4c17f5fa32d8ff4acca4006"


def sha256_file(path):
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

    with open(PREREG_V2, encoding="utf-8") as fh:
        reader = csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t")
        fieldnames = list(reader.fieldnames)
        v2_rows = list(reader)

    if len(v2_rows) != 150:
        sys.exit(f"FATAL: v2 rows count {len(v2_rows)} != 150")

    v3_rows = []
    diff_rows = []
    sanref_rows = []

    exp_changes = 0

    sanref_mapping = {}
    for i in range(1, 14):
        sanref_mapping[f"M2-03-G5-{i:02d}-F3"] = f"M2-03-SANREF-G5-{i:02d}-F3"
    for i in range(1, 7):
        sanref_mapping[f"M2-03-G6-{i:02d}-F3"] = f"M2-03-SANREF-G6-{i:02d}-F3"

    for r in v2_rows:
        pid = r["point_id"]
        r_new = dict(r)

        # 1. M2-10 gdb sha correction per U254
        if pid == "M2-10-01-B":
            old_gdb_sha = r["gdb_script_sha256"]
            r_new["gdb_script_sha256"] = M210_GDB_ACTUAL_SHA
            diff_rows.append([pid, "gdb_script_sha256", "IDENTITY_CORRECTION", old_gdb_sha, M210_GDB_ACTUAL_SHA, "U254/E8-104: actual git commit c66b7d2 sha"])
            r_new["basis"] = r["basis"] + "; r8m2b: gdb sha corrected per U254/E8-104"
            diff_rows.append([pid, "basis", "NOTE_APPEND", r["basis"], r_new["basis"], "U254/E8-104 basis update"])

        # 2. M2-07-CTRL-vl-ng1-F3 class_rule per U255
        elif pid == "M2-07-CTRL-vl-ng1-F3":
            old_rule = r["class_rule"]
            r_new["class_rule"] = "NATIVE_FAIL_CONTROL"
            diff_rows.append([pid, "class_rule", "RULE_UPDATE", old_rule, "NATIVE_FAIL_CONTROL", "U255/E8-105: native failure control rule per judge_d003.py:145"])
            r_new["basis"] = r["basis"] + "; r8m2b: class_rule=NATIVE_FAIL_CONTROL per U255/E8-105"
            diff_rows.append([pid, "basis", "NOTE_APPEND", r["basis"], r_new["basis"], "U255/E8-105 basis update"])

        # 3. 19 NO_REF points mapped to reference points per U257
        elif pid in sanref_mapping:
            ref_pid = sanref_mapping[pid]
            old_ref = r["san_ref_point_id"]
            r_new["san_ref_point_id"] = ref_pid
            diff_rows.append([pid, "san_ref_point_id", "REF_MAPPING", old_ref, ref_pid, "U257/E8-108: mapped to non-sanitizer reference point"])
            r_new["basis"] = r["basis"] + f"; r8m2b: san_ref={ref_pid} per U257/E8-108"
            diff_rows.append([pid, "basis", "NOTE_APPEND", r["basis"], r_new["basis"], "U257/E8-108 basis update"])

            # Create corresponding SANREF row
            s_row = dict(r)
            s_row["point_id"] = ref_pid
            s_row["item"] = "M2-03-SANREF"
            s_row["tree"] = "F3"
            if "G5" in pid:
                s_row["driver"] = "r6bstate-F3-dbg"
                s_row["driver_sha256"] = R6BSTATE_DBG_SHA
                s_row["lib_sha256"] = F3_DBG_LIB_SHA
            else:
                s_row["driver"] = "r6bseam-seamF-F3"
                s_row["driver_sha256"] = R6BSEAM_SEAMF_SHA
                s_row["lib_sha256"] = F3_SEAMF_LIB_SHA

            s_row["gdb_script"] = "-"
            s_row["gdb_script_sha256"] = "-"
            s_row["control_point_id"] = "-"
            s_row["control_group"] = "NO"
            s_row["exp_I1"] = "-"
            s_row["exp_I2"] = "-"
            s_row["exp_I3"] = "-"
            s_row["exp_I4"] = "-"
            s_row["exp_I5"] = "-"
            s_row["exp_I6"] = "-"
            s_row["exp_I7"] = "-"
            s_row["exp_san"] = "-"
            s_row["exp_stage"] = "-"
            s_row["class_rule"] = "JUDGE_D003"
            s_row["output_assertion"] = "NONE"
            s_row["san_ref_point_id"] = "-"
            s_row["san_options"] = "-"
            s_row["state_analyzer"] = "-"
            s_row["basis"] = f"U257; non-sanitizer reference for {pid}; same env and flags without -fsanitize"
            s_row["status"] = "INFLUENCED"
            sanref_rows.append(s_row)

        # Assert 0 exp_* changes
        for col in fieldnames:
            if col.startswith("exp_"):
                if r_new[col] != r[col]:
                    print(f"FATAL: exp_* change in {pid}.{col}: '{r[col]}' -> '{r_new[col]}'")
                    exp_changes += 1

        v3_rows.append(r_new)

    if exp_changes != 0:
        sys.exit(f"FATAL: {exp_changes} unauthorized exp_* changes detected! Must be 0.")

    if len(v3_rows) != 150:
        sys.exit(f"FATAL: v3 rows count {len(v3_rows)} != 150")

    if len(sanref_rows) != 19:
        sys.exit(f"FATAL: sanref rows count {len(sanref_rows)} != 19")

    # Write PREREG_M2_EFFECTIVE_R8_M2b.tsv
    with open(OUT_V3, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames) + "\n")
        for row in v3_rows:
            fh.write("\t".join([row[f] for f in fieldnames]) + "\n")

    v3_sha = sha256_file(OUT_V3)
    utc_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(OUT_V3_SHA, "w", encoding="utf-8") as fh:
        fh.write(f"{v3_sha}  PREREG_M2_EFFECTIVE_R8_M2b.tsv\n")

    with open(OUT_V3_TIME, "w", encoding="utf-8") as fh:
        fh.write(f"{utc_now}\n")

    # Write PREREG_M2_SANREF_R8_M2b.tsv
    with open(OUT_SANREF, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames) + "\n")
        for row in sanref_rows:
            fh.write("\t".join([row[f] for f in fieldnames]) + "\n")

    sanref_sha = sha256_file(OUT_SANREF)

    with open(OUT_SANREF_SHA, "w", encoding="utf-8") as fh:
        fh.write(f"{sanref_sha}  PREREG_M2_SANREF_R8_M2b.tsv\n")

    with open(OUT_SANREF_TIME, "w", encoding="utf-8") as fh:
        fh.write(f"{utc_now}\n")

    # Write PREREG_DIFF_R8_M2b.tsv
    diff_headers = ["point_id", "field", "diff_type", "v2_value", "v3_value", "notes"]
    with open(OUT_DIFF, "w", encoding="utf-8") as fh:
        fh.write("\t".join(diff_headers) + "\n")
        for row in diff_rows:
            fh.write("\t".join(row) + "\n")

    # Write APPARATUS_R8_M2b.tsv
    apparatus_items = [
        ("run_m2_r8m2b.py", "testing/d003/stage_s4/run_m2_r8m2b.py", "runner", "Runner and command planner supporting dry-run and paired execution (U256)"),
        ("facts_m2_r8m2b.py", "testing/d003/stage_s4/facts_m2_r8m2b.py", "facts", "Facts extractor with paired gdb divergence check and octal exit code parsing (U256)"),
        ("verdict_m2_r8m2b.py", "testing/d003/stage_s4/verdict_m2_r8m2b.py", "verdict", "Verdict engine with GDB_DIVERGENT priority, NATIVE_FAIL_CONTROL, sanref, hit1, and fail_layer1 assertions"),
        ("state_judge_m2_r8m2a4.py", "testing/d003/stage_s4/state_judge_m2_r8m2a4.py", "state_analyzer", "Private state analyzer reused unchanged (89f00f0e...)"),
        ("posctrl_m2_r8m2b.py", "testing/d003/stage_s4/posctrl_m2_r8m2b.py", "positive_control", "Synthetic positive control suite (27 cases)"),
        ("judge_d003.py", "testing/d003/judge_d003.py", "judge_core", "Frozen canonical judge (d2d04145...)"),
    ]

    app_headers = ["apparatus", "path", "sha256", "role", "notes"]
    with open(OUT_APPARATUS, "w", encoding="utf-8") as fh:
        fh.write("\t".join(app_headers) + "\n")
        for name, relpath, role, notes in apparatus_items:
            f_abs = os.path.join(REPO, relpath)
            f_sha = sha256_file(f_abs)
            fh.write("\t".join([name, relpath, f_sha, role, notes]) + "\n")

    print(f"PREREG v3 generated: {OUT_V3} (sha256: {v3_sha})")
    print(f"exp_* changes count: {exp_changes} (ASSERT 0 PASS)")
    print(f"SANREF table generated: {OUT_SANREF} (19 rows, sha256: {sanref_sha})")
    print(f"PREREG diff table generated: {OUT_DIFF} ({len(diff_rows)} differences)")
    print(f"APPARATUS inventory generated: {OUT_APPARATUS}")


if __name__ == "__main__":
    main()
