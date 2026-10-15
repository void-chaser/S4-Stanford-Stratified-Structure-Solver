#!/usr/bin/env python3
# prereg_effective_r8m2a3.py -- P05-S4 R8 M2a3 Section 5: generate effective preregistration.
# Reads: checkpoints/p05/registries/s4r8/M2/r8m2a2/PREREG_M2_R8_M2a2.tsv
# Outputs under EV:
#   PREREG_M2_EFFECTIVE_R8_M2a3.tsv
#   PREREG_M2_EFFECTIVE_R8_M2a3.tsv.sha256
#   PREREG_M2_EFFECTIVE_R8_M2a3_TIMESTAMP_UTC.txt
#   PREREG_DIFF_R8_M2a3.tsv
#   CONTROL_MAPPING_R8_M2a3.tsv
import datetime
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a3")
SRC_PREREG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a2", "PREREG_M2_R8_M2a2.tsv")

GDB_SCRIPT_R8M2A3 = "testing/d003/stage_s4/r6c_state_r8m2a3.gdb"
GDB_SCRIPT_R8M2A3_SHA = "5afecd95cc5a914e7ce8d7d6f054daea0d3942b294503833ae28ac59b7ce7221"

M210_GDB_SCRIPT = "testing/d003/stage_s4/m210_b_r8m2a2_R2.gdb"
M210_GDB_SCRIPT_SHA = "bbab8579d1a3b10ea52250c609be54848bb22687c461329bf70d0611e5ae74a5"

F2_DRIVER_NAME = "seam-fmmret-F2"
F2_DRIVER_SHA = "a4061e4c429df6f969993eab72c06a9afdaa2cbcab46535e9ca43851cca05fa6"
F2_LIB_SHA = "b513f840bdbacf10efd120429abf5637fa277debcf8dbbe4a59ff25d59e02bbf"

POLBASIS = {"jones", "nv", "vl", "fftjones", "fftnv", "fftvl"}


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def main():
    if not os.path.isfile(SRC_PREREG):
        sys.stderr.write("prereg_effective_r8m2a3: missing source prereg\n")
        return 2

    with open(SRC_PREREG, "r", encoding="utf-8") as fh:
        src_lines = [l.rstrip("\r\n") for l in fh if l.strip() and not l.startswith("#")]

    src_head = src_lines[0].split("\t")
    src_rows = [dict(zip(src_head, l.split("\t"))) for l in src_lines[1:]]

    if len(src_rows) != 150:
        sys.stderr.write("prereg_effective_r8m2a3: source rows %d != 150\n" % len(src_rows))
        return 2

    # New headers: explicit target_layer, control_point_id, output_call, control_output_call, exp_rc3, gdb_script_sha256
    new_head = [
        "point_id", "item", "tree", "driver", "driver_sha256", "lib_sha256",
        "gdb_script", "gdb_script_sha256", "argv", "env", "n_G_actual", "passes",
        "target_layer", "control_point_id", "output_call", "control_output_call",
        "inj_call", "k_before", "k_fail", "k_preretry", "k_retry", "retry_call",
        "control_group", "exp_rc1", "exp_rc2", "exp_rc3", "exp_signal", "exp_hit",
        "exp_class", "exp_I1", "exp_I2", "exp_I3", "exp_I4", "exp_I5", "exp_I6",
        "exp_I7", "exp_san", "exp_stage", "basis", "status"
    ]

    effective_rows = []
    diff_rows = []
    ctrl_mappings = []

    def record_diff(pid, item, field, old_val, new_val, reason):
        if str(old_val) != str(new_val):
            diff_rows.append([pid, item, field, str(old_val), str(new_val), reason])

    for r in src_rows:
        pid = r["point_id"]
        item = r["item"]
        tree = r["tree"]
        driver = r["driver"]
        dsha = r["driver_sha256"]
        lsha = r["lib_sha256"]
        gdb_script = r["gdb_script"]
        gdb_sha = "-"
        argv = r["argv"]
        env = r["env"]
        ng_actual = r["n_G_actual"]
        passes = r["passes"]
        inj_call = r["inj_call"]
        k_before = r["k_before"]
        k_fail = r["k_fail"]
        k_preretry = r["k_preretry"]
        k_retry = r["k_retry"]
        retry_call = r["retry_call"]
        ctrl_grp = r["control_group"]
        exp_rc1 = r["exp_rc1"]
        exp_rc2 = r["exp_rc2"]
        exp_rc3 = "-"
        exp_sig = r["exp_signal"]
        exp_hit = r["exp_hit"]
        exp_class = r["exp_class"]
        exp_I = {("I%d" % i): r["exp_I%d" % i] for i in range(1, 8)}
        exp_san = r["exp_san"]
        exp_stage = r["exp_stage"]
        basis = r["basis"]
        status = r["status"]

        target_layer = "-"
        control_point_id = "-"
        output_call = "-"
        control_output_call = "-"

        # 1. M2-01 (12 test points, 9 control points)
        if item == "M2-01":
            target_layer = "1"
            output_call = "2"
            control_output_call = "2"
            exp_rc3 = "0"
            gdb_script = GDB_SCRIPT_R8M2A3
            gdb_sha = GDB_SCRIPT_R8M2A3_SHA
            record_diff(pid, item, "gdb_script", r["gdb_script"], gdb_script, "SPECIFY_GDB_STATE_COLLECTOR")
            record_diff(pid, item, "exp_rc3", "-", exp_rc3, "EXPLICIT_RECOVERY_RC3")

            # Map to exact control point
            if pid in ("M2-01-01-F3", "M2-01-04-F3"):
                control_point_id = "M2-01-CTRL-01-F3"
            elif pid in ("M2-01-02-F3", "M2-01-05-F3"):
                control_point_id = "M2-01-CTRL-02-F3"
            elif pid in ("M2-01-03-F3", "M2-01-06-F3"):
                control_point_id = "M2-01-CTRL-03-F3"
            elif pid == "M2-01-11-F3":
                control_point_id = "M2-01-CTRL-11-F3"
            elif pid == "M2-01-12-F3":
                control_point_id = "M2-01-CTRL-12-F3"
            elif pid == "M2-01-14-F3":
                control_point_id = "M2-01-CTRL-14-F3"
            elif pid == "M2-01-16-F3":
                control_point_id = "M2-01-CTRL-16-F3"
            elif pid == "M2-01-18-F3":
                control_point_id = "M2-01-CTRL-18-F3"
            elif pid == "M2-01-20-F3":
                control_point_id = "M2-01-CTRL-20-F3"

            ctrl_mappings.append([pid, item, env, target_layer, control_point_id, output_call, control_output_call, "I2_I6_COMPARISON", "M2-01 exact match on mode, ng, driver"])

        elif item == "M2-01-CTRL":
            target_layer = "1"
            output_call = "2"
            control_output_call = "2"
            exp_rc3 = "0"
            gdb_script = GDB_SCRIPT_R8M2A3
            gdb_sha = GDB_SCRIPT_R8M2A3_SHA
            record_diff(pid, item, "gdb_script", r["gdb_script"], gdb_script, "SPECIFY_GDB_STATE_COLLECTOR")
            record_diff(pid, item, "exp_rc3", "-", exp_rc3, "EXPLICIT_RECOVERY_RC3")

        # 2. M2-03 (Sanitizer 31 points)
        elif item == "M2-03":
            target_layer = "1"
            output_call = "2"
            control_output_call = "-"
            control_point_id = "-"
            exp_rc3 = "-"
            gdb_script = "-"
            gdb_sha = "-"
            # Private state invariants cannot be collected under standalone sanitizer runs without gdb
            # Set to UNOBSERVED as required by prompt Section 5 & 6
            for inv in ("I1", "I2", "I3", "I4", "I5", "I6"):
                if exp_I[inv] == "HOLD":
                    record_diff(pid, item, "exp_" + inv, exp_I[inv], "UNOBSERVED", "SANITIZER_GDB_UNOBSERVED")
                    exp_I[inv] = "UNOBSERVED"
            # I7 is HOLD, defined as exp_san == 0
            exp_I["I7"] = "HOLD"
            exp_san = "0"

        # 3. M2-04 (Dual failure 2 test points, 2 control points)
        elif item == "M2-04":
            gdb_script = GDB_SCRIPT_R8M2A3
            gdb_sha = GDB_SCRIPT_R8M2A3_SHA
            record_diff(pid, item, "gdb_script", r["gdb_script"], gdb_script, "SPECIFY_GDB_STATE_COLLECTOR")
            # Dual target recovery is call3!
            record_diff(pid, item, "retry_call", r["retry_call"], "3", "DUAL_RECOVERY_IS_CALL3")
            retry_call = "3"
            record_diff(pid, item, "k_preretry", r["k_preretry"], "3", "DUAL_PRERETRY_SNAPSHOT_IS_K3")
            k_preretry = "3"
            record_diff(pid, item, "k_retry", r["k_retry"], "4", "DUAL_RETRY_SNAPSHOT_IS_K4")
            k_retry = "4"
            exp_rc1 = "20"
            exp_rc2 = "20"
            exp_rc3 = "0"
            record_diff(pid, item, "exp_rc3", "-", exp_rc3, "DUAL_RECOVERY_RC3_EQ_0")
            output_call = "3"
            control_output_call = "3"

            if pid == "M2-04-01-F3":
                target_layer = "1"
                control_point_id = "M2-04-CTRL-01-F3"
                ctrl_mappings.append([pid, item, env, target_layer, control_point_id, output_call, control_output_call, "DUAL_CALL3_I6_COMPARISON", "Single-layer same-mode control"])
            elif pid == "M2-04-02-F3":
                target_layer = "1,2"
                control_point_id = "M2-04-CTRL-02-F3"
                ctrl_mappings.append([pid, item, env, target_layer, control_point_id, output_call, control_output_call, "DUAL_CALL3_I6_COMPARISON", "PP1 multi-layer control"])

        elif item == "M2-04-CTRL":
            gdb_script = GDB_SCRIPT_R8M2A3
            gdb_sha = GDB_SCRIPT_R8M2A3_SHA
            record_diff(pid, item, "gdb_script", r["gdb_script"], gdb_script, "SPECIFY_GDB_STATE_COLLECTOR")
            exp_rc3 = "0"
            record_diff(pid, item, "exp_rc3", "-", exp_rc3, "CONTROL_CALL3_RC3_EQ_0")
            output_call = "3"
            control_output_call = "3"
            target_layer = "1" if pid == "M2-04-CTRL-01-F3" else "1,2"

        # 4. M2-05 (4 test points, 4 control points)
        elif item == "M2-05":
            gdb_script = GDB_SCRIPT_R8M2A3
            gdb_sha = GDB_SCRIPT_R8M2A3_SHA
            record_diff(pid, item, "gdb_script", r["gdb_script"], gdb_script, "SPECIFY_GDB_STATE_COLLECTOR")
            output_call = "2"
            control_output_call = "2"
            exp_rc3 = "0"
            record_diff(pid, item, "exp_rc3", "-", exp_rc3, "EXPLICIT_RECOVERY_RC3")

            if pid == "M2-05-P0-F3":
                target_layer = "0"
                control_point_id = "M2-05-CTRL-P0-F3"
            elif pid == "M2-05-P2-F3":
                target_layer = "2"
                control_point_id = "M2-05-CTRL-P2-F3"
            elif pid == "M2-05-PP1-F3":
                target_layer = "1"
                control_point_id = "M2-05-CTRL-PP1-F3"
            elif pid == "M2-05-PP2-F3":
                target_layer = "2"
                control_point_id = "M2-05-CTRL-PP2-F3"
            ctrl_mappings.append([pid, item, env, target_layer, control_point_id, output_call, control_output_call, "LAYOUT_I2_I6_COMPARISON", "Matching layout control"])

        elif item == "M2-05-CTRL":
            gdb_script = GDB_SCRIPT_R8M2A3
            gdb_sha = GDB_SCRIPT_R8M2A3_SHA
            record_diff(pid, item, "gdb_script", r["gdb_script"], gdb_script, "SPECIFY_GDB_STATE_COLLECTOR")
            output_call = "2"
            control_output_call = "2"
            exp_rc3 = "0"
            record_diff(pid, item, "exp_rc3", "-", exp_rc3, "EXPLICIT_RECOVERY_RC3")
            if pid == "M2-05-CTRL-P0-F3":
                target_layer = "0"
            elif pid == "M2-05-CTRL-P2-F3":
                target_layer = "2"
            elif pid == "M2-05-CTRL-PP1-F3":
                target_layer = "1"
            elif pid == "M2-05-CTRL-PP2-F3":
                target_layer = "2"

        # 5. M2-06 (1 test point, 1 control point)
        elif item == "M2-06":
            target_layer = "1"
            output_call = "1"
            control_output_call = "1"
            control_point_id = "M2-06-CTRL-01-F3"
            ctrl_mappings.append([pid, item, env, target_layer, control_point_id, output_call, control_output_call, "NANBUF_K1_COMPARISON", "Uninjected tensor control"])
        elif item == "M2-06-CTRL":
            target_layer = "1"
            output_call = "1"
            control_output_call = "1"

        # 6. M2-07 (9 test points, 72 control points)
        elif item == "M2-07":
            target_layer = "1"
            output_call = "1"
            control_output_call = "1"
            mode_tok = ""
            for kv in env.split(";"):
                if kv.startswith("FMM_MODE="):
                    mode_tok = kv.split("=", 1)[1]
            control_point_id = "M2-07-CTRL-%s-ng5-F3" % mode_tok
            ctrl_mappings.append([pid, item, env, target_layer, control_point_id, output_call, control_output_call, "GRID_NG5_INJ_COMPARISON", "Same-mode NG=5 control"])
        elif item == "M2-07-CTRL":
            target_layer = "1"
            output_call = "1"
            control_output_call = "1"

        # 7. M2-09 (2 control points)
        elif item == "M2-09-CTRL":
            target_layer = "1"
            output_call = "1"
            control_output_call = "1"
            if pid == "M2-09-01-F2":
                driver = F2_DRIVER_NAME
                dsha = F2_DRIVER_SHA
                lsha = F2_LIB_SHA
                record_diff(pid, item, "driver", r["driver"], driver, "COMPLETE_F2_DRIVER_NAME")
                record_diff(pid, item, "driver_sha256", r["driver_sha256"], dsha, "COMPLETE_F2_DRIVER_SHA")
                record_diff(pid, item, "lib_sha256", r["lib_sha256"], lsha, "COMPLETE_F2_LIB_SHA")

        # 8. M2-10 (1 baseline diagnostic point)
        elif item == "M2-10":
            target_layer = "1"
            output_call = "1"
            control_output_call = "-"
            control_point_id = "-"
            gdb_script = M210_GDB_SCRIPT
            gdb_sha = M210_GDB_SCRIPT_SHA
            record_diff(pid, item, "gdb_script_sha256", "-", gdb_sha, "SPECIFY_M210_GDB_SHA")

        eff_row = [
            pid, item, tree, driver, dsha, lsha,
            gdb_script, gdb_sha, argv, env, ng_actual, passes,
            target_layer, control_point_id, output_call, control_output_call,
            inj_call, k_before, k_fail, k_preretry, k_retry, retry_call,
            ctrl_grp, exp_rc1, exp_rc2, exp_rc3, exp_sig, exp_hit,
            exp_class, exp_I["I1"], exp_I["I2"], exp_I["I3"], exp_I["I4"], exp_I["I5"], exp_I["I6"],
            exp_I["I7"], exp_san, exp_stage, basis, status
        ]
        effective_rows.append(eff_row)

    os.makedirs(EV, exist_ok=True)

    # 1. Write PREREG_M2_EFFECTIVE_R8_M2a3.tsv
    eff_path = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2a3.tsv")
    with open(eff_path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(new_head) + "\n")
        for r in effective_rows:
            fh.write("\t".join(r) + "\n")

    # 2. Write sha256 and UTC timestamp
    eff_content = open(eff_path, "rb").read()
    eff_sha = hashlib.sha256(eff_content).hexdigest()
    sha_path = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2a3.tsv.sha256")
    with open(sha_path, "w", encoding="utf-8") as fh:
        fh.write("%s  PREREG_M2_EFFECTIVE_R8_M2a3.tsv\n" % eff_sha)

    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_path = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2a3_TIMESTAMP_UTC.txt")
    with open(ts_path, "w", encoding="utf-8") as fh:
        fh.write(now_utc + "\n")

    # 3. Write PREREG_DIFF_R8_M2a3.tsv
    diff_path = os.path.join(EV, "PREREG_DIFF_R8_M2a3.tsv")
    diff_head = ["point_id", "item", "field", "r8m2a2_frozen_value", "r8m2a3_effective_value", "reason"]
    with open(diff_path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(diff_head) + "\n")
        for r in diff_rows:
            fh.write("\t".join(r) + "\n")

    # 4. Write CONTROL_MAPPING_R8_M2a3.tsv
    ctrl_path = os.path.join(EV, "CONTROL_MAPPING_R8_M2a3.tsv")
    ctrl_head = ["point_id", "item", "env", "target_layer", "control_point_id", "test_output_call", "control_output_call", "comparison_purpose", "basis"]
    with open(ctrl_path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(ctrl_head) + "\n")
        for r in ctrl_mappings:
            fh.write("\t".join(r) + "\n")

    print("prereg_effective_r8m2a3: generated %d effective rows" % len(effective_rows))
    print("Effective prereg sha256: %s" % eff_sha)
    print("UTC freeze timestamp: %s" % now_utc)
    print("Diff records: %d" % len(diff_rows))
    print("Control mappings: %d" % len(ctrl_mappings))
    return 0


if __name__ == "__main__":
    sys.exit(main())
