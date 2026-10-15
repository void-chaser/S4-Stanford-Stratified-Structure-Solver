#!/usr/bin/env python3
# posctrl_m2_r8m2a3.py -- P05-S4 R8 M2a3 Section 7: positive control harness for formal verdict.
# Calls testing/d003/stage_s4/verdict_m2_r8m2a3.py across synthetic test cases A through K:
#   A: Exact match (all points MATCH)
#   B: Changed rc1 (MISMATCH on exp_rc1)
#   C: Value changed only in pass 2 (FLAKY)
#   D: NZ token: D0 (rc1=0 -> MISMATCH) and D20 (rc1=20 -> MATCH)
#   E: Invariant observation changed (MISMATCH on exp_I1)
#   F: Dual failure recovery rc3 non-zero (MISMATCH on exp_rc3)
#   G: Missing gdb state on required HOLD invariant (SCHEMA_ERROR)
#   H: ID errors (H1 duplicate, H2 missing, H3 extra -> SCHEMA_ERROR)
#   I: Tree mismatch (SCHEMA_ERROR)
#   J: Control mapping / output dump error (SCHEMA_ERROR)
#   K: Sanitizer report non-zero (MISMATCH on exp_san)
# Validates exact expected point_ids and fields for each failure.
# Refuses to overwrite existing output (U17).
import copy
import os
import subprocess
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a3")
VERDICT_SCRIPT = os.path.join(REPO, "testing", "d003", "stage_s4", "verdict_m2_r8m2a3.py")

# R1 kept as POSCTRL_M2_R8_M2a3.txt; R2 output:
DEFAULT_OUT = os.path.join(EV, "POSCTRL_M2_R8_M2a3_R2.txt")
BASE_TMP = os.path.join(EV, "tmp", "posctrl_r8m2a3_run1")

SYN_PREREG_HEAD = [
    "point_id", "item", "tree", "driver", "driver_sha256", "lib_sha256",
    "gdb_script", "gdb_script_sha256", "argv", "env", "n_G_actual", "passes",
    "target_layer", "control_point_id", "output_call", "control_output_call",
    "inj_call", "k_before", "k_fail", "k_preretry", "k_retry", "retry_call",
    "control_group", "exp_rc1", "exp_rc2", "exp_rc3", "exp_signal", "exp_hit",
    "exp_class", "exp_I1", "exp_I2", "exp_I3", "exp_I4", "exp_I5", "exp_I6",
    "exp_I7", "exp_san", "exp_stage", "basis", "status"
]

SYN_CTRL_MAP_HEAD = [
    "point_id", "item", "env", "target_layer", "control_point_id",
    "test_output_call", "control_output_call", "comparison_purpose", "basis"
]

SYN_RESULT_HEAD = [
    "point_id", "tree", "rc", "rc1", "rc2", "rc3", "signal", "hit", "class", "san_reports"
] + ["I%d" % i for i in range(1, 8)]

SYN_PREREG_ROWS = [
    # 1. Standard test point (M2-01)
    {
        "point_id": "SYN-REP-01", "item": "M2-01", "tree": "F3", "driver": "init-F3-dbg",
        "driver_sha256": "d5200355", "lib_sha256": "56f72c58",
        "gdb_script": "testing/d003/stage_s4/r6c_state_r8m2a3.gdb", "gdb_script_sha256": "5afecd95",
        "argv": "pattern both 4 3", "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=win:1", "n_G_actual": "5", "passes": "2",
        "target_layer": "1", "control_point_id": "SYN-CTRL-01", "output_call": "2", "control_output_call": "2",
        "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "2", "k_retry": "3", "retry_call": "2",
        "control_group": "NO", "exp_rc1": "20", "exp_rc2": "0", "exp_rc3": "0", "exp_signal": "0", "exp_hit": "1",
        "exp_class": "REPORTED_FAILURE", "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD",
        "exp_I5": "HOLD", "exp_I6": "HOLD", "exp_I7": "-", "exp_san": "-", "exp_stage": "-",
        "basis": "synth", "status": "INFLUENCED"
    },
    # 2. Control point
    {
        "point_id": "SYN-CTRL-01", "item": "M2-01-CTRL", "tree": "F3", "driver": "init-F3-dbg",
        "driver_sha256": "d5200355", "lib_sha256": "56f72c58",
        "gdb_script": "testing/d003/stage_s4/r6c_state_r8m2a3.gdb", "gdb_script_sha256": "5afecd95",
        "argv": "pattern both 4 3", "env": "FMM_MODE=fft;S4FMM_NG=5", "n_G_actual": "5", "passes": "2",
        "target_layer": "1", "control_point_id": "-", "output_call": "2", "control_output_call": "2",
        "inj_call": "-", "k_before": "0", "k_fail": "-", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
        "control_group": "YES", "exp_rc1": "0", "exp_rc2": "0", "exp_rc3": "0", "exp_signal": "0", "exp_hit": "0",
        "exp_class": "CONTROL_OK", "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-",
        "exp_I5": "-", "exp_I6": "-", "exp_I7": "-", "exp_san": "-", "exp_stage": "-",
        "basis": "synth", "status": "INFLUENCED"
    },
    # 3. NZ token test point (M2-07)
    {
        "point_id": "SYN-NZ-01", "item": "M2-07", "tree": "F3", "driver": "d003plan-F3-plain",
        "driver_sha256": "be478d90", "lib_sha256": "abbc01c7",
        "gdb_script": "-", "gdb_script_sha256": "-",
        "argv": "pattern both 4 3", "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=s4malloc;S4FMM_NTH=1", "n_G_actual": "5", "passes": "2",
        "target_layer": "1", "control_point_id": "SYN-CTRL-01", "output_call": "1", "control_output_call": "1",
        "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
        "control_group": "NO", "exp_rc1": "NZ", "exp_rc2": "-", "exp_rc3": "-", "exp_signal": "0", "exp_hit": "1",
        "exp_class": "REPORTED_FAILURE", "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-",
        "exp_I5": "-", "exp_I6": "-", "exp_I7": "-", "exp_san": "-", "exp_stage": "-",
        "basis": "synth", "status": "INFLUENCED"
    },
    # 4. Dual target failure test point (M2-04)
    {
        "point_id": "SYN-DUAL-01", "item": "M2-04", "tree": "F3", "driver": "dual-F3-dbg",
        "driver_sha256": "fb846819", "lib_sha256": "56f72c58",
        "gdb_script": "testing/d003/stage_s4/r6c_state_r8m2a3.gdb", "gdb_script_sha256": "5afecd95",
        "argv": "pattern both 4 3", "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=s4malloc;S4FMM_NTH=1;S4FMM_INJECT2=s4malloc;S4FMM_NTH2=2", "n_G_actual": "5", "passes": "2",
        "target_layer": "1", "control_point_id": "SYN-CTRL-01", "output_call": "3", "control_output_call": "3",
        "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "3", "k_retry": "4", "retry_call": "3",
        "control_group": "NO", "exp_rc1": "20", "exp_rc2": "20", "exp_rc3": "0", "exp_signal": "0", "exp_hit": "2",
        "exp_class": "REPORTED_FAILURE", "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD",
        "exp_I5": "HOLD", "exp_I6": "HOLD", "exp_I7": "-", "exp_san": "-", "exp_stage": "-",
        "basis": "synth", "status": "INFLUENCED"
    },
    # 5. Sanitizer test point (M2-03)
    {
        "point_id": "SYN-SAN-01", "item": "M2-03", "tree": "F3", "driver": "r6bstate-F3-san",
        "driver_sha256": "6b6aad38", "lib_sha256": "2775b9b2",
        "gdb_script": "-", "gdb_script_sha256": "-",
        "argv": "pattern both 4 3", "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=s4malloc;S4FMM_NTH=1", "n_G_actual": "5", "passes": "2",
        "target_layer": "1", "control_point_id": "-", "output_call": "2", "control_output_call": "-",
        "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "2", "k_retry": "3", "retry_call": "2",
        "control_group": "NO", "exp_rc1": "20", "exp_rc2": "0", "exp_rc3": "-", "exp_signal": "0", "exp_hit": "1",
        "exp_class": "REPORTED_FAILURE", "exp_I1": "UNOBSERVED", "exp_I2": "UNOBSERVED", "exp_I3": "-", "exp_I4": "UNOBSERVED",
        "exp_I5": "UNOBSERVED", "exp_I6": "UNOBSERVED", "exp_I7": "HOLD", "exp_san": "0", "exp_stage": "-",
        "basis": "synth", "status": "INFLUENCED"
    }
]

SYN_CTRL_MAP_ROWS = [
    {
        "point_id": "SYN-REP-01", "item": "M2-01", "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=win:1",
        "target_layer": "1", "control_point_id": "SYN-CTRL-01", "test_output_call": "2",
        "control_output_call": "2", "comparison_purpose": "I2_I6_COMPARISON", "basis": "synth"
    },
    {
        "point_id": "SYN-NZ-01", "item": "M2-07", "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=s4malloc;S4FMM_NTH=1",
        "target_layer": "1", "control_point_id": "SYN-CTRL-01", "test_output_call": "1",
        "control_output_call": "1", "comparison_purpose": "GRID_NG5_INJ_COMPARISON", "basis": "synth"
    },
    {
        "point_id": "SYN-DUAL-01", "item": "M2-04", "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=s4malloc;S4FMM_NTH=1;S4FMM_INJECT2=s4malloc;S4FMM_NTH2=2",
        "target_layer": "1", "control_point_id": "SYN-CTRL-01", "test_output_call": "3",
        "control_output_call": "3", "comparison_purpose": "DUAL_CALL3_I6_COMPARISON", "basis": "synth"
    }
]


def write_tsv(path, head, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(head) + "\n")
        for r in rows:
            fh.write("\t".join(str(r.get(h, "")) for h in head) + "\n")


def make_synth_base_results():
    rows = [
        # SYN-REP-01
        {
            "point_id": "SYN-REP-01", "tree": "F3", "rc": "20", "rc1": "20", "rc2": "0", "rc3": "0",
            "signal": "0", "hit": "1", "class": "REPORTED_FAILURE", "san_reports": "0",
            "I1": "HOLD", "I2": "HOLD", "I3": "-", "I4": "HOLD", "I5": "HOLD", "I6": "HOLD", "I7": "-"
        },
        # SYN-CTRL-01
        {
            "point_id": "SYN-CTRL-01", "tree": "F3", "rc": "0", "rc1": "0", "rc2": "0", "rc3": "0",
            "signal": "0", "hit": "0", "class": "CONTROL_OK", "san_reports": "0",
            "I1": "-", "I2": "-", "I3": "-", "I4": "-", "I5": "-", "I6": "-", "I7": "-"
        },
        # SYN-NZ-01
        {
            "point_id": "SYN-NZ-01", "tree": "F3", "rc": "20", "rc1": "20", "rc2": "0", "rc3": "0",
            "signal": "0", "hit": "1", "class": "REPORTED_FAILURE", "san_reports": "0",
            "I1": "-", "I2": "-", "I3": "-", "I4": "-", "I5": "-", "I6": "-", "I7": "-"
        },
        # SYN-DUAL-01
        {
            "point_id": "SYN-DUAL-01", "tree": "F3", "rc": "0", "rc1": "20", "rc2": "20", "rc3": "0",
            "signal": "0", "hit": "2", "class": "REPORTED_FAILURE", "san_reports": "0",
            "I1": "HOLD", "I2": "HOLD", "I3": "-", "I4": "HOLD", "I5": "HOLD", "I6": "HOLD", "I7": "-"
        },
        # SYN-SAN-01
        {
            "point_id": "SYN-SAN-01", "tree": "F3", "rc": "20", "rc1": "20", "rc2": "0", "rc3": "0",
            "signal": "0", "hit": "1", "class": "REPORTED_FAILURE", "san_reports": "0",
            "I1": "UNOBSERVED", "I2": "UNOBSERVED", "I3": "-", "I4": "UNOBSERVED", "I5": "UNOBSERVED", "I6": "UNOBSERVED", "I7": "HOLD"
        }
    ]
    return rows


def write_dumps(dumps_dir):
    for pass_name in ("pass1", "pass2"):
        for pid in ("SYN-REP-01", "SYN-CTRL-01", "SYN-NZ-01", "SYN-DUAL-01", "SYN-SAN-01"):
            p_dir = os.path.join(dumps_dir, pass_name, pid)
            os.makedirs(p_dir, exist_ok=True)
            for c_num in (1, 2, 3):
                with open(os.path.join(p_dir, "call%d.txt" % c_num), "wb") as fh:
                    # Output of test points and control point match for same call
                    fh.write(("FIELD_DUMP_call%d\n" % c_num).encode("utf-8"))


def run_verdict_case(case_dir, prereg_file, ctrl_map_file, prefix, dumps_dir=None):
    cmd = [sys.executable, "-I", "-B", VERDICT_SCRIPT, case_dir, prereg_file, ctrl_map_file, case_dir, prefix]
    if dumps_dir:
        cmd.extend(["--dumps-dir", dumps_dir])
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    v_path = os.path.join(case_dir, prefix + "_VERDICT.tsv")
    s_path = os.path.join(case_dir, prefix + "_SUMMARY.txt")
    v_rows = []
    if os.path.isfile(v_path):
        with open(v_path, "r", encoding="utf-8") as fh:
            lines = [l.rstrip("\r\n") for l in fh if l.strip() and not l.startswith("#")]
        if lines:
            h = lines[0].split("\t")
            for l in lines[1:]:
                v_rows.append(dict(zip(h, l.split("\t"))))
    summary = open(s_path, "r", encoding="utf-8").read() if os.path.isfile(s_path) else ""
    return res.returncode, v_rows, summary


def main():
    out_file = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    if os.path.exists(out_file):
        sys.stderr.write("posctrl_m2_r8m2a3: REFUSED output exists (U17): %s\n" % out_file)
        return 2

    os.makedirs(BASE_TMP, exist_ok=True)
    log_lines = []
    cases_passed = 0
    total_cases = 0

    def record_case(case_id, passed, detail):
        nonlocal cases_passed, total_cases
        total_cases += 1
        if passed:
            cases_passed += 1
        st = "PASS" if passed else "FAIL"
        line = "CASE_%s\t%s\t%s" % (case_id, st, detail)
        log_lines.append(line)
        print(line)

    synth_prereg = os.path.join(BASE_TMP, "PREREG_SYNTH.tsv")
    synth_ctrlmap = os.path.join(BASE_TMP, "CTRLMAP_SYNTH.tsv")
    write_tsv(synth_prereg, SYN_PREREG_HEAD, SYN_PREREG_ROWS)
    write_tsv(synth_ctrlmap, SYN_CTRL_MAP_HEAD, SYN_CTRL_MAP_ROWS)

    base_results = make_synth_base_results()

    # ----------------------------------------------------
    # Case A: Exact match (all 5 MATCH)
    # ----------------------------------------------------
    case_a_dir = os.path.join(BASE_TMP, "case_A")
    dumps_a = os.path.join(case_a_dir, "dumps")
    write_tsv(os.path.join(case_a_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, base_results)
    write_tsv(os.path.join(case_a_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, base_results)
    write_dumps(dumps_a)
    rc, v_rows, summary = run_verdict_case(case_a_dir, synth_prereg, synth_ctrlmap, "verdict_A", dumps_dir=dumps_a)
    match_cnt = sum(1 for r in v_rows if r["verdict"] == "MATCH")
    ok_a = (rc == 0 and match_cnt == len(SYN_PREREG_ROWS) and "MISMATCH=0" in summary and "FLAKY=0" in summary and "SCHEMA_ERRORS=0" in summary)
    record_case("A_EXACT_MATCH", ok_a, "%d points match, MISMATCH=0, FLAKY=0, SCHEMA_ERRORS=0" % len(SYN_PREREG_ROWS))

    # ----------------------------------------------------
    # Case B: Changed rc1
    # ----------------------------------------------------
    case_b_dir = os.path.join(BASE_TMP, "case_B")
    rows_b1 = copy.deepcopy(base_results)
    rows_b2 = copy.deepcopy(base_results)
    for r in rows_b1:
        if r["point_id"] == "SYN-REP-01":
            r["rc1"] = "0"
    for r in rows_b2:
        if r["point_id"] == "SYN-REP-01":
            r["rc1"] = "0"
    write_tsv(os.path.join(case_b_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_b1)
    write_tsv(os.path.join(case_b_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, rows_b2)
    rc, v_rows, summary = run_verdict_case(case_b_dir, synth_prereg, synth_ctrlmap, "verdict_B")
    target_b = next((r for r in v_rows if r["point_id"] == "SYN-REP-01"), None)
    ok_b = (rc == 0 and "MISMATCH=1" in summary and target_b is not None and "MISMATCH" in target_b["verdict"] and "exp_rc1" in target_b["mismatch_fields"])
    record_case("B_CHANGE_RC1", ok_b, "SYN-REP-01 MISMATCH on exp_rc1, total MISMATCH=1")

    # ----------------------------------------------------
    # Case C: Value changed only in pass 2 (FLAKY)
    # ----------------------------------------------------
    case_c_dir = os.path.join(BASE_TMP, "case_C")
    rows_c1 = copy.deepcopy(base_results)
    rows_c2 = copy.deepcopy(base_results)
    for r in rows_c2:
        if r["point_id"] == "SYN-REP-01":
            r["rc1"] = "10"
    write_tsv(os.path.join(case_c_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_c1)
    write_tsv(os.path.join(case_c_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, rows_c2)
    rc, v_rows, summary = run_verdict_case(case_c_dir, synth_prereg, synth_ctrlmap, "verdict_C")
    target_c = next((r for r in v_rows if r["point_id"] == "SYN-REP-01"), None)
    ok_c = (rc == 0 and "FLAKY=1" in summary and target_c is not None and "FLAKY" in target_c["verdict"] and "rc1" in target_c["flaky_fields"])
    record_case("C_PASS2_FLAKY", ok_c, "SYN-REP-01 FLAKY on rc1, total FLAKY=1")

    # ----------------------------------------------------
    # Case D: NZ token: D0 (rc1=0 -> MISMATCH) and D20 (rc1=20 -> MATCH)
    # ----------------------------------------------------
    case_d0_dir = os.path.join(BASE_TMP, "case_D0")
    rows_d0 = copy.deepcopy(base_results)
    for r in rows_d0:
        if r["point_id"] == "SYN-NZ-01":
            r["rc1"] = "0"
    write_tsv(os.path.join(case_d0_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_d0)
    write_tsv(os.path.join(case_d0_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, rows_d0)
    rc, v_rows, summary = run_verdict_case(case_d0_dir, synth_prereg, synth_ctrlmap, "verdict_D0")
    target_d0 = next((r for r in v_rows if r["point_id"] == "SYN-NZ-01"), None)
    ok_d0 = (rc == 0 and "MISMATCH=1" in summary and target_d0 is not None and "exp_rc1" in target_d0["mismatch_fields"])

    case_d20_dir = os.path.join(BASE_TMP, "case_D20")
    rows_d20 = copy.deepcopy(base_results)
    for r in rows_d20:
        if r["point_id"] == "SYN-NZ-01":
            r["rc1"] = "20"
    write_tsv(os.path.join(case_d20_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_d20)
    write_tsv(os.path.join(case_d20_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, rows_d20)
    rc, v_rows, summary = run_verdict_case(case_d20_dir, synth_prereg, synth_ctrlmap, "verdict_D20")
    target_d20 = next((r for r in v_rows if r["point_id"] == "SYN-NZ-01"), None)
    ok_d20 = (rc == 0 and "MISMATCH=0" in summary and target_d20 is not None and target_d20["verdict"] == "MATCH")
    record_case("D_NZ_TOKEN", ok_d0 and ok_d20, "D0 (rc=0 -> MISMATCH) and D20 (rc=20 -> MATCH) on NZ expectation")

    # ----------------------------------------------------
    # Case E: Changed invariant observation (I1 -> VIOLATED)
    # ----------------------------------------------------
    case_e_dir = os.path.join(BASE_TMP, "case_E")
    rows_e = copy.deepcopy(base_results)
    for r in rows_e:
        if r["point_id"] == "SYN-REP-01":
            r["I1"] = "VIOLATED"
    write_tsv(os.path.join(case_e_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_e)
    write_tsv(os.path.join(case_e_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, rows_e)
    rc, v_rows, summary = run_verdict_case(case_e_dir, synth_prereg, synth_ctrlmap, "verdict_E")
    target_e = next((r for r in v_rows if r["point_id"] == "SYN-REP-01"), None)
    ok_e = (rc == 0 and "MISMATCH=1" in summary and target_e is not None and "exp_I1" in target_e["mismatch_fields"])
    record_case("E_CHANGE_INVARIANT", ok_e, "SYN-REP-01 MISMATCH on exp_I1 (VIOLATED!=HOLD)")

    # ----------------------------------------------------
    # Case F: Dual failure recovery rc3 non-zero
    # ----------------------------------------------------
    case_f_dir = os.path.join(BASE_TMP, "case_F")
    rows_f = copy.deepcopy(base_results)
    for r in rows_f:
        if r["point_id"] == "SYN-DUAL-01":
            r["rc3"] = "20"
    write_tsv(os.path.join(case_f_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_f)
    write_tsv(os.path.join(case_f_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, rows_f)
    rc, v_rows, summary = run_verdict_case(case_f_dir, synth_prereg, synth_ctrlmap, "verdict_F")
    target_f = next((r for r in v_rows if r["point_id"] == "SYN-DUAL-01"), None)
    ok_f = (rc == 0 and "MISMATCH=1" in summary and target_f is not None and "exp_rc3" in target_f["mismatch_fields"])
    record_case("F_DUAL_FAILURE_RC3_NONZERO", ok_f, "SYN-DUAL-01 MISMATCH on exp_rc3 (rc3=20!=0)")

    # ----------------------------------------------------
    # Case G: Missing gdb state on required HOLD invariant
    # ----------------------------------------------------
    case_g_dir = os.path.join(BASE_TMP, "case_G")
    rows_g = copy.deepcopy(base_results)
    for r in rows_g:
        if r["point_id"] == "SYN-REP-01":
            r["I1"] = ""
    write_tsv(os.path.join(case_g_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_g)
    write_tsv(os.path.join(case_g_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, rows_g)
    rc, v_rows, summary = run_verdict_case(case_g_dir, synth_prereg, synth_ctrlmap, "verdict_G")
    target_g = next((r for r in v_rows if r["point_id"] == "SYN-REP-01"), None)
    ok_g = (rc == 0 and target_g is not None and target_g["verdict"] == "SCHEMA_ERROR" and "MISSING_GDB_STATE" in target_g["mismatch_fields"])
    record_case("G_MISSING_GDB_STATE", ok_g, "SYN-REP-01 SCHEMA_ERROR on MISSING_GDB_STATE_PASS1(I1)")

    # ----------------------------------------------------
    # Case H: Duplicate, missing, and extra point_id
    # ----------------------------------------------------
    # H1: duplicate
    case_h1_dir = os.path.join(BASE_TMP, "case_H1")
    rows_h1 = copy.deepcopy(base_results)
    rows_h1.append(copy.deepcopy(rows_h1[0]))
    write_tsv(os.path.join(case_h1_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_h1)
    write_tsv(os.path.join(case_h1_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, base_results)
    rc, v_rows, summary = run_verdict_case(case_h1_dir, synth_prereg, synth_ctrlmap, "verdict_H1")
    ok_h1 = (rc == 0 and "Duplicate point_id in pass 1" in summary)

    # H2: missing
    case_h2_dir = os.path.join(BASE_TMP, "case_H2")
    rows_h2 = [r for r in base_results if r["point_id"] != "SYN-REP-01"]
    write_tsv(os.path.join(case_h2_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_h2)
    write_tsv(os.path.join(case_h2_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, base_results)
    rc, v_rows, summary = run_verdict_case(case_h2_dir, synth_prereg, synth_ctrlmap, "verdict_H2")
    ok_h2 = (rc == 0 and "Missing point_id in pass 1" in summary)

    # H3: extra
    case_h3_dir = os.path.join(BASE_TMP, "case_H3")
    rows_h3 = copy.deepcopy(base_results)
    extra_row = copy.deepcopy(base_results[0])
    extra_row["point_id"] = "SYN-EXTRA-999"
    rows_h3.append(extra_row)
    write_tsv(os.path.join(case_h3_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_h3)
    write_tsv(os.path.join(case_h3_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, base_results)
    rc, v_rows, summary = run_verdict_case(case_h3_dir, synth_prereg, synth_ctrlmap, "verdict_H3")
    ok_h3 = (rc == 0 and "Extra point_id in pass 1" in summary)
    record_case("H_ID_ERRORS", ok_h1 and ok_h2 and ok_h3, "Duplicate (H1), Missing (H2), Extra (H3) correctly detected as SCHEMA_ERROR")

    # ----------------------------------------------------
    # Case I: Tree mismatch
    # ----------------------------------------------------
    case_i_dir = os.path.join(BASE_TMP, "case_I")
    rows_i = copy.deepcopy(base_results)
    for r in rows_i:
        if r["point_id"] == "SYN-REP-01":
            r["tree"] = "B"
    write_tsv(os.path.join(case_i_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_i)
    write_tsv(os.path.join(case_i_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, rows_i)
    rc, v_rows, summary = run_verdict_case(case_i_dir, synth_prereg, synth_ctrlmap, "verdict_I")
    target_i = next((r for r in v_rows if r["point_id"] == "SYN-REP-01"), None)
    ok_i = (rc == 0 and target_i is not None and target_i["verdict"] == "SCHEMA_ERROR" and "TREE_MISMATCH" in target_i["mismatch_fields"])
    record_case("I_TREE_MISMATCH", ok_i, "SYN-REP-01 SCHEMA_ERROR on TREE_MISMATCH(B!=F3)")

    # ----------------------------------------------------
    # Case J: Control mapping / output dump error
    # ----------------------------------------------------
    case_j_dir = os.path.join(BASE_TMP, "case_J")
    dumps_j = os.path.join(case_j_dir, "dumps")
    write_tsv(os.path.join(case_j_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, base_results)
    write_tsv(os.path.join(case_j_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, base_results)
    write_dumps(dumps_j)
    # Corrupt call3.txt of SYN-DUAL-01
    corrupt_file = os.path.join(dumps_j, "pass1", "SYN-DUAL-01", "call3.txt")
    with open(corrupt_file, "wb") as fh:
        fh.write(b"CORRUPTED_FIELD_OUTPUT_DIFFERENT_FROM_CONTROL\n")
    rc, v_rows, summary = run_verdict_case(case_j_dir, synth_prereg, synth_ctrlmap, "verdict_J", dumps_dir=dumps_j)
    target_j = next((r for r in v_rows if r["point_id"] == "SYN-DUAL-01"), None)
    ok_j = (rc == 0 and target_j is not None and target_j["verdict"] == "SCHEMA_ERROR" and "OUTPUT_DIFF" in target_j["mismatch_fields"])
    record_case("J_CONTROL_DUMP_ERROR", ok_j, "SYN-DUAL-01 SCHEMA_ERROR on OUTPUT_DIFF between test call3 and control call3")

    # ----------------------------------------------------
    # Case K: Sanitizer report non-zero
    # ----------------------------------------------------
    case_k_dir = os.path.join(BASE_TMP, "case_K")
    rows_k = copy.deepcopy(base_results)
    for r in rows_k:
        if r["point_id"] == "SYN-SAN-01":
            r["san_reports"] = "1"
    write_tsv(os.path.join(case_k_dir, "RESULTS_pass1.tsv"), SYN_RESULT_HEAD, rows_k)
    write_tsv(os.path.join(case_k_dir, "RESULTS_pass2.tsv"), SYN_RESULT_HEAD, rows_k)
    rc, v_rows, summary = run_verdict_case(case_k_dir, synth_prereg, synth_ctrlmap, "verdict_K")
    target_k = next((r for r in v_rows if r["point_id"] == "SYN-SAN-01"), None)
    ok_k = (rc == 0 and "MISMATCH=1" in summary and target_k is not None and "exp_san" in target_k["mismatch_fields"])
    record_case("K_SANITIZER_REPORT_NONZERO", ok_k, "SYN-SAN-01 MISMATCH on exp_san (1!=0)")

    # Overall verdict
    overall_status = "PASS" if cases_passed == total_cases else "FAIL"
    summary_line = "POSCTRL_M2_R8_M2a3 total=%d passed=%d failed=%d -> %s" % (
        total_cases, cases_passed, total_cases - cases_passed, overall_status
    )
    print(summary_line)

    with open(out_file, "x", encoding="utf-8") as fh:
        fh.write("# POSCTRL_M2_R8_M2a3: positive control verification of verdict_m2_r8m2a3.py\n")
        fh.write("\n".join(log_lines) + "\n")
        fh.write(summary_line + "\n")

    return 0 if overall_status == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
