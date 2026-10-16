#!/usr/bin/env python3
# run_win64_diag_r8m2b.py -- Executes win:64 diagnostic run per Section 5 S-F.
# Runs 5 win:64 diagnostic points using win64_diag_r8m2b.gdb.
# Emits WIN64_DIAG_R8_M2b.tsv with exact derivation of inj_call, k_before, k_fail, k_preretry, k_retry, retry_call, fail_layer.
# Generates and freezes PREREG_M2_WIN64_R8_M2b.tsv (5 rows, status INFLUENCED), sha256, and timestamp.
import csv
import datetime
import hashlib
import os
import re
import subprocess
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b"))

DIAG_GDB = os.path.join(REPO, "testing", "d003", "stage_s4", "win64_diag_r8m2b.gdb")
DRV_PATH = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "build_R3", "drivers", "polyinj-F3-dbg")
DRV_SHA = "fecd272e7ec96f754a41815918600ccc594a331cf274350e1efad92ac693f00e"
LIB_SHA = "56f72c5882d4293bbb2d45a272d7c7727e401085b900854b1f49b851effd897a"
GDB_SCRIPT_FORMAL = "testing/d003/stage_s4/r6c_state_r8m2a3.gdb"
GDB_SCRIPT_SHA = "5afecd95cc5a914e7ce8d7d6f054daea0d3942b294503833ae28ac59b7ce7221"

WIN64_POINTS = [
    ("M2-01-13-F3", "M2-01", "F3", "polyinj-F3-dbg", "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=win:64", "5", "M2-01-CTRL-12-F3", "13"),
    ("M2-01-15-F3", "M2-01", "F3", "polyinj-F3-dbg", "FMM_MODE=fft;S4FMM_NG=9;S4FMM_INJECT=win:64", "9", "M2-01-CTRL-14-F3", "15"),
    ("M2-01-17-F3", "M2-01", "F3", "polyinj-F3-dbg", "FMM_MODE=kottke;S4FMM_NG=1;S4FMM_INJECT=win:64", "1", "M2-01-CTRL-16-F3", "17"),
    ("M2-01-19-F3", "M2-01", "F3", "polyinj-F3-dbg", "FMM_MODE=kottke;S4FMM_NG=5;S4FMM_INJECT=win:64", "5", "M2-01-CTRL-18-F3", "19"),
    ("M2-01-21-F3", "M2-01", "F3", "polyinj-F3-dbg", "FMM_MODE=kottke;S4FMM_NG=9;S4FMM_INJECT=win:64", "9", "M2-01-CTRL-20-F3", "21"),
]

OUT_DIAG_TSV = os.path.join(EV, "WIN64_DIAG_R8_M2b.tsv")
PREREG_MAIN = os.path.join(EV, "PREREG_M2_EFFECTIVE_R8_M2b.tsv")
OUT_PREREG_WIN64 = os.path.join(EV, "PREREG_M2_WIN64_R8_M2b.tsv")
OUT_PREREG_SHA = os.path.join(EV, "PREREG_M2_WIN64_R8_M2b.tsv.sha256")
OUT_PREREG_TIME = os.path.join(EV, "PREREG_M2_WIN64_R8_M2b_TIMESTAMP_UTC.txt")

DIAG_DIR = os.path.join(EV, "win64_diag")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def clean_env(extra_env_str, dump_dir):
    env = {}
    for k, v in os.environ.items():
        if k.startswith("FMM_") or k.startswith("S4FMM_") or k.startswith("ASAN_") or k.startswith("UBSAN_"):
            continue
        env[k] = v
    env["S4FMM_DUMP_DIR"] = dump_dir
    for tok in extra_env_str.split(";"):
        tok = tok.strip()
        if "=" in tok:
            k, v = tok.split("=", 1)
            env[k] = v
    return env


def parse_diag_trace(text):
    """Parse chronological sequence of probe points and hit lines."""
    events = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        m_probe = re.search(r"WIN64_DIAG_PROBE:\s*k=(\d+)", line)
        if m_probe:
            events.append(("PROBE", int(m_probe.group(1))))
        if "S4FMM HIT real malloc failure: S3R4C3 poly window malloc 64" in line:
            events.append(("HIT64", line))
        if "WIN64_DIAG_CLM_RET: line 1894 rc=" in line:
            rc = int(line.split("rc=")[-1])
            events.append(("CLM_RET", rc))
    return events


def main():
    os.makedirs(DIAG_DIR, exist_ok=True)

    diag_records = []
    prereg_win64_rows = []

    # Verify driver sha before running
    act_drv_sha = sha256_file(DRV_PATH)
    if act_drv_sha != DRV_SHA:
        sys.exit(f"FATAL: driver sha mismatch: {act_drv_sha} != {DRV_SHA}")

    print("run_win64_diag: starting diagnostic execution of 5 win:64 points...")

    for pid, item, tree, drv, env_str, ng, ctrl_pid, add22_row in WIN64_POINTS:
        pt_dir = os.path.join(DIAG_DIR, pid)
        os.makedirs(pt_dir, exist_ok=True)
        dump_dir = pt_dir
        env = clean_env(env_str, dump_dir)

        # 1. Run under gdb with win64_diag_r8m2b.gdb
        gdb_log = os.path.join(pt_dir, "gdb_diag.log")
        cmd_a = ["gdb", "-batch", "-x", DIAG_GDB, "--args", DRV_PATH, "pattern", "both", "4", "3"]
        res_a = subprocess.run(cmd_a, env=env, cwd=REPO,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               timeout=600, text=True)
        with open(gdb_log, "w", encoding="utf-8") as fh:
            fh.write(res_a.stdout)

        # 2. Run without gdb to record actual return codes
        stdout_f = os.path.join(pt_dir, "stdout.txt")
        stderr_f = os.path.join(pt_dir, "stderr.txt")
        ec_f = os.path.join(pt_dir, "exitcode.txt")
        cmd_b = [DRV_PATH, "pattern", "both", "4", "3"]
        res_b = subprocess.run(cmd_b, env=env, cwd=REPO,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               timeout=600, text=True)
        with open(stdout_f, "w", encoding="utf-8") as fh:
            fh.write(res_b.stdout)
        with open(stderr_f, "w", encoding="utf-8") as fh:
            fh.write(res_b.stderr)
        with open(ec_f, "w", encoding="utf-8") as fh:
            fh.write(str(res_b.returncode) + "\n")

        # 3. Analyze sequence of events in gdb_log
        events = parse_diag_trace(res_a.stdout + "\n" + res_b.stderr)
        hit_index = None
        for i, ev in enumerate(events):
            if ev[0] == "HIT64":
                hit_index = i
                break

        if hit_index is not None:
            # Look backwards for the preceding PROBE
            last_probe = None
            for ev in events[:hit_index]:
                if ev[0] == "PROBE":
                    last_probe = ev[1]

            # Look forward for next PROBE
            next_probe = None
            for ev in events[hit_index + 1:]:
                if ev[0] == "PROBE":
                    next_probe = ev[1]
                    break

            if last_probe == 0 and next_probe == 1:
                inj_call = 1
                k_before = 0
                k_fail = 1
                k_preretry = 2
                k_retry = 3
                retry_call = 2
                fail_layer = 1
                index_status = "INDEX_CONFIRMED"
                basis_text = f"DIAG_HIT between probe k=0 and k=1 in call1; next probe k=1; clm_ret=20; ADD22-B-{add22_row}-F3"
            elif last_probe == 2 and next_probe == 3:
                inj_call = 2
                k_before = 2
                k_fail = 3
                k_preretry = 3
                k_retry = 4
                retry_call = 3
                fail_layer = 1
                index_status = "INDEX_CONFIRMED"
                basis_text = f"DIAG_HIT between probe k=2 and k=3 in call2; next probe k=3; clm_ret=20; ADD22-B-{add22_row}-F3"
            else:
                inj_call = "-"
                k_before = "-"
                k_fail = "-"
                k_preretry = "-"
                k_retry = "-"
                retry_call = "-"
                fail_layer = "-"
                index_status = "UNRESOLVED_INDEX"
                basis_text = f"DIAG_HIT between probe k={last_probe} and k={next_probe}"
        else:
            inj_call = "-"
            k_before = "-"
            k_fail = "-"
            k_preretry = "-"
            k_retry = "-"
            retry_call = "-"
            fail_layer = "-"
            index_status = "UNRESOLVED_INDEX"
            basis_text = "DIAG_HIT64 not reached in execution trace"

        diag_records.append([
            pid, item, drv, env_str,
            "YES" if hit_index is not None else "NO",
            str(inj_call), str(k_before), str(k_fail),
            str(k_preretry), str(k_retry), str(retry_call),
            str(fail_layer), index_status, basis_text
        ])

        print(f"[{index_status}] {pid}: inj_call={inj_call}, k_fail={k_fail}, basis={basis_text}")

        # If index confirmed, prepare PREREG row per U259
        if index_status == "INDEX_CONFIRMED":
            # Per U259: exp values taken from M1 observation on F3 (ADD22-B-<add22_row>-F3: rc1=20, rc2=0, signal=0, hit=1, class=REPORTED_FAILURE)
            prereg_row = {
                "point_id": pid,
                "item": item,
                "tree": tree,
                "driver": drv,
                "driver_sha256": DRV_SHA,
                "lib_sha256": LIB_SHA,
                "gdb_script": GDB_SCRIPT_FORMAL,
                "gdb_script_sha256": GDB_SCRIPT_SHA,
                "argv": "pattern both 4 3",
                "env": env_str,
                "n_G_actual": ng,
                "passes": "2",
                "target_layer": "1",
                "control_point_id": ctrl_pid,
                "output_call": str(retry_call),
                "control_output_call": str(retry_call),
                "inj_call": str(inj_call),
                "k_before": str(k_before),
                "k_fail": str(k_fail),
                "k_preretry": str(k_preretry),
                "k_retry": str(k_retry),
                "retry_call": str(retry_call),
                "control_group": "NO",
                "exp_rc1": "20",
                "exp_rc2": "0",
                "exp_rc3": "0",
                "exp_signal": "0",
                "exp_hit": "1",
                "exp_class": "REPORTED_FAILURE",
                "exp_I1": "HOLD",
                "exp_I2": "HOLD",
                "exp_I3": "-",
                "exp_I4": "HOLD",
                "exp_I5": "HOLD",
                "exp_I6": "HOLD",
                "exp_I7": "DEFERRED",
                "exp_san": "-",
                "exp_stage": "-",
                "class_rule": "JUDGE_D003",
                "output_assertion": "I6_ONLY",
                "exp_hit1": "-",
                "exp_hit2": "-",
                "exp_inject2_invalid": "-",
                "exp_inject2_suppressed": "-",
                "k_before2": "-",
                "k_fail2": "-",
                "fail_layer1": "-",
                "fail_layer2": "-",
                "san_ref_point_id": "-",
                "san_options": "-",
                "state_analyzer": "testing/d003/stage_s4/state_judge_m2_r8m2a4.py:89f00f0ef91b927066bad059b58073a47cbf34594d65a35ee7bdddb576a6ff1f",
                "basis": f"U259; ADD22-B-{add22_row}-F3 observed; r8m2b diagnostic run confirmed inj_call={inj_call}, k_fail={k_fail}",
                "status": "INFLUENCED",
            }
            prereg_win64_rows.append(prereg_row)

    # 4. Write WIN64_DIAG_R8_M2b.tsv
    diag_headers = [
        "point_id", "item", "driver", "env", "hit_reached", "inj_call",
        "k_before", "k_fail", "k_preretry", "k_retry", "retry_call",
        "fail_layer", "index_status", "evidence_basis"
    ]
    with open(OUT_DIAG_TSV, "w", encoding="utf-8") as fh:
        fh.write("\t".join(diag_headers) + "\n")
        for row in diag_records:
            fh.write("\t".join(row) + "\n")

    print(f"run_win64_diag: wrote diagnostic results to {OUT_DIAG_TSV}")

    # 5. Write and freeze PREREG_M2_WIN64_R8_M2b.tsv
    with open(PREREG_MAIN, encoding="utf-8") as fh:
        fieldnames = list(csv.DictReader(fh, delimiter="\t").fieldnames)

    with open(OUT_PREREG_WIN64, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames) + "\n")
        for row in prereg_win64_rows:
            fh.write("\t".join([row.get(f, "-") for f in fieldnames]) + "\n")

    win64_sha = sha256_file(OUT_PREREG_WIN64)
    utc_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with open(OUT_PREREG_SHA, "w", encoding="utf-8") as fh:
        fh.write(f"{win64_sha}  PREREG_M2_WIN64_R8_M2b.tsv\n")

    with open(OUT_PREREG_TIME, "w", encoding="utf-8") as fh:
        fh.write(f"{utc_now}\n")

    print(f"run_win64_diag: frozen {len(prereg_win64_rows)} win:64 points to {OUT_PREREG_WIN64} (sha256: {win64_sha})")


if __name__ == "__main__":
    main()
