#!/usr/bin/env python3
# prereg_r8m2a2.py -- P05-S4 R8 M2a2 CONT1 section 8.2: M2 complete pre-registration.
# Writes $EV/PREREG_M2_R8_M2a2.tsv, .sha256, _TIMESTAMP_UTC.txt, and PREREG_M2_COUNT_R8_M2a2.txt.
# Uses only non-STALE artifacts in BUILD_FINAL_R8_M2a2.tsv and BUILD_B_DBG_R8_M2a2.tsv.
# Uses INDEX_DERIVATION_R8_M2a2_R2.tsv for resolved indices (win:64 marked UNRESOLVED_INDEX does not produce points).
# Asserts item x tree counts equal row total, each item points equal design table points, and M2-01 >= 9 controls.
# Refuses to overwrite (U17).
import datetime
import hashlib
import os
import re
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
PREREG = os.path.join(EV, "PREREG_M2_R8_M2a2.tsv")
SHA_FILE = os.path.join(EV, "PREREG_M2_R8_M2a2.sha256")
TS_FILE = os.path.join(EV, "PREREG_M2_R8_M2a2_TIMESTAMP_UTC.txt")
COUNT_FILE = os.path.join(EV, "PREREG_M2_COUNT_R8_M2a2.txt")
DESIGN_TSV = os.path.join(EV, "M2_DESIGN_R8_M2a2.tsv")
BUILD_FINAL = os.path.join(EV, "BUILD_FINAL_R8_M2a2.tsv")
BUILD_B_DBG = os.path.join(EV, "BUILD_B_DBG_R8_M2a2.tsv")
INDEX_DERIV = os.path.join(EV, "INDEX_DERIVATION_R8_M2a2_R2.tsv")

COLS = [
    "point_id", "item", "tree", "driver", "driver_sha256", "lib_sha256", "gdb_script", "argv", "env",
    "n_G_actual", "passes", "inj_call", "k_before", "k_fail", "k_preretry", "k_retry", "retry_call",
    "control_group", "exp_rc1", "exp_rc2", "exp_signal", "exp_hit", "exp_class",
    "exp_I1", "exp_I2", "exp_I3", "exp_I4", "exp_I5", "exp_I6", "exp_I7", "exp_san",
    "exp_stage", "basis", "status"
]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()

def get_build_hashes():
    hashes = {}
    with open(BUILD_FINAL, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip(): continue
            parts = line.rstrip().split("\t")
            if len(parts) >= 6 and parts[5] == "OK":
                hashes[parts[0]] = parts[4]
    if os.path.exists(BUILD_B_DBG):
        with open(BUILD_B_DBG, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("#") or not line.strip(): continue
                parts = line.rstrip().split("\t")
                if len(parts) >= 8 and parts[7] == "0":
                    hashes[parts[0]] = parts[6]
    # Reused plain drivers from DRIVERS_R8.tsv
    drv_r8 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "DRIVERS_R8.tsv")
    with open(drv_r8, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip(): continue
            parts = line.rstrip().split("\t")
            if len(parts) >= 5:
                hashes[parts[0]] = parts[4]
                hashes["lib_" + parts[0]] = parts[3]
    # Reused seam drivers from DRIVERS_R7_SEAM.tsv
    drv_r7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7", "DRIVERS_R7_SEAM.tsv")
    with open(drv_r7, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip(): continue
            parts = line.rstrip().split("\t")
            if len(parts) >= 4:
                hashes[parts[0]] = parts[3]
                hashes["lib_" + parts[0]] = parts[2]
    return hashes

def calc_nG_actual(mode, ng):
    if mode == "closed1d":
        return 1 + 2 * ((ng - 1) // 2)
    elif ng in (1, 2, 3, 4):
        return 1
    elif ng in (5, 6, 7, 8):
        return 5
    elif ng == 9:
        return 9
    return ng

def main():
    if os.path.exists(PREREG) or os.path.exists(SHA_FILE) or os.path.exists(COUNT_FILE):
        print("prereg_r8m2a2: REFUSED exists (U17)")
        return 2

    hashes = get_build_hashes()
    lib_f3_dbg = hashes.get("lib_F3_dbg_REUSED", "-")
    lib_f3_san = hashes.get("lib_F3_san", "-")
    lib_f3_buf = hashes.get("lib_F3_bufseam", "-")
    lib_b_dbg = hashes.get("lib_B_dbg", "-")

    rows = []

    # -------------------------------------------------------------
    # M2-01: 12 resolved test points + 9 controls
    # -------------------------------------------------------------
    # 6 init points (resolved)
    init_configs = [
        ("01", "closed2d", 1, "win:1", "Pattern_GetContainmentTree", "window malloc 1", 1),
        ("02", "fft", 5, "win:1", "Pattern_GetContainmentTree", "window malloc 1", 1),
        ("03", "kottke", 5, "win:1", "Pattern_GetContainmentTree", "window malloc 1", 1),
        ("04", "closed2d", 1, "init:7", "malloc", "outside malloc 7", 1),
        ("05", "fft", 5, "init:8", "malloc", "outside malloc 8", 1),
        ("06", "kottke", 5, "init:8", "malloc", "outside malloc 8", 1),
    ]
    for idx, mode, ng, inj, wrap, hook_desc, tgt_layer in init_configs:
        rows.append({
            "point_id": "M2-01-%s-F3" % idx, "item": "M2-01", "tree": "F3",
            "driver": "init-F3-dbg", "driver_sha256": hashes.get("init-F3-dbg", "-"), "lib_sha256": lib_f3_dbg,
            "gdb_script": "-", "argv": "pattern both 4 3",
            "env": "FMM_MODE=%s;S4FMM_NG=%d;S4FMM_INJECT=%s" % (mode, ng, inj),
            "n_G_actual": str(calc_nG_actual(mode, ng)), "passes": "2",
            "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "2", "k_retry": "3", "retry_call": "2",
            "control_group": "NO", "exp_rc1": "20", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "1", "exp_class": "REPORTED_FAILURE",
            "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD", "exp_I5": "HOLD", "exp_I6": "HOLD", "exp_I7": "DEFERRED",
            "exp_san": "-", "exp_stage": "-",
            "basis": "testing/d003/stage_s4/driver_r6b_state.cpp:216; testing/d003/stage_s3r4/inject_s3r4_init.cpp:5; U232, U238",
            "status": "INFLUENCED"
        })

    # 6 poly win:1 points (resolved)
    poly_configs = [
        ("11", "fft", 1),
        ("12", "fft", 5),
        ("14", "fft", 9),
        ("16", "kottke", 1),
        ("18", "kottke", 5),
        ("20", "kottke", 9),
    ]
    for idx, mode, ng in poly_configs:
        rows.append({
            "point_id": "M2-01-%s-F3" % idx, "item": "M2-01", "tree": "F3",
            "driver": "polyinj-F3-dbg", "driver_sha256": hashes.get("polyinj-F3-dbg", "-"), "lib_sha256": lib_f3_dbg,
            "gdb_script": "-", "argv": "pattern both 4 3",
            "env": "FMM_MODE=%s;S4FMM_NG=%d;S4FMM_INJECT=win:1" % (mode, ng),
            "n_G_actual": str(calc_nG_actual(mode, ng)), "passes": "2",
            "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "2", "k_retry": "3", "retry_call": "2",
            "control_group": "NO", "exp_rc1": "20", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "1", "exp_class": "REPORTED_FAILURE",
            "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD", "exp_I5": "HOLD", "exp_I6": "HOLD", "exp_I7": "DEFERRED",
            "exp_san": "-", "exp_stage": "-",
            "basis": "testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp:219; testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp:54; U232, U238",
            "status": "INFLUENCED"
        })

    # 9 M2-01 controls
    m201_ctrls = [
        ("01", "init-F3-dbg", "closed2d", 1),
        ("02", "init-F3-dbg", "fft", 5),
        ("03", "init-F3-dbg", "kottke", 5),
        ("11", "polyinj-F3-dbg", "fft", 1),
        ("12", "polyinj-F3-dbg", "fft", 5),
        ("14", "polyinj-F3-dbg", "fft", 9),
        ("16", "polyinj-F3-dbg", "kottke", 1),
        ("18", "polyinj-F3-dbg", "kottke", 5),
        ("20", "polyinj-F3-dbg", "kottke", 9),
    ]
    for idx, drv, mode, ng in m201_ctrls:
        rows.append({
            "point_id": "M2-01-CTRL-%s-F3" % idx, "item": "M2-01-CTRL", "tree": "F3",
            "driver": drv, "driver_sha256": hashes.get(drv, "-"), "lib_sha256": lib_f3_dbg,
            "gdb_script": "-", "argv": "pattern both 4 3",
            "env": "FMM_MODE=%s;S4FMM_NG=%d" % (mode, ng),
            "n_G_actual": str(calc_nG_actual(mode, ng)), "passes": "2",
            "inj_call": "-", "k_before": "0", "k_fail": "-", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
            "control_group": "YES", "exp_rc1": "0", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "0", "exp_class": "CONTROL_OK",
            "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
            "exp_san": "-", "exp_stage": "-",
            "basis": "no injection; control group for M2-01; brief section 4.6",
            "status": "INFLUENCED"
        })

    # -------------------------------------------------------------
    # M2-03: Sanitizer points (19 G5/G6 cells + 12 M2-01 repair = 31 points)
    # -------------------------------------------------------------
    # 19 G5/G6 representative cells
    g5_rep = [
        ("01", "closed1d", 1, "s4malloc", "NTH=1", "r6bstate-F3-san", "M-once-closed1d-malloc-1"),
        ("02", "closed2d", 1, "s4malloc", "NTH=1", "r6bstate-F3-san", "M-once-closed2d-malloc-1"),
        ("03", "experimental", 1, "s4malloc", "NTH=1", "r6bstate-F3-san", "M-once-experimental-malloc-1"),
        ("04", "fft", 5, "exec", "K=1", "r6bstate-F3-san", "M-once-fft-exec-1"),
        ("05", "fft", 5, "s4malloc", "NTH=1", "r6bstate-F3-san", "M-once-fft-malloc-1"),
        ("06", "jones", 5, "exec", "K=1", "r6bstate-F3-san", "M-once-jones-exec-1"),
        ("07", "jones", 5, "s4malloc", "NTH=1", "r6bstate-F3-san", "M-once-jones-malloc-1"),
        ("08", "kottke", 5, "exec", "K=1", "r6bstate-F3-san", "M-once-kottke-exec-1"),
        ("09", "kottke", 5, "s4malloc", "NTH=1", "r6bstate-F3-san", "M-once-kottke-malloc-1"),
        ("10", "nv", 5, "exec", "K=1", "r6bstate-F3-san", "M-once-nv-exec-1"),
        ("11", "nv", 5, "s4malloc", "NTH=1", "r6bstate-F3-san", "M-once-nv-malloc-1"),
        ("12", "vl", 5, "exec", "K=1", "r6bstate-F3-san", "M-once-vl-exec-1"),
        ("13", "vl", 5, "s4malloc", "NTH=1", "r6bstate-F3-san", "M-once-vl-malloc-1"),
    ]
    for idx, mode, ng, inj_kind, nth, drv, orig_pid in g5_rep:
        inj_env = "S4FMM_INJECT=s4malloc;S4FMM_NTH=1" if inj_kind == "s4malloc" else "S4FMM_INJECT=exec;S4FMM_K=1"
        rows.append({
            "point_id": "M2-03-G5-%s-F3" % idx, "item": "M2-03", "tree": "F3",
            "driver": drv, "driver_sha256": hashes.get(drv, "-"), "lib_sha256": lib_f3_san,
            "gdb_script": "-", "argv": "pattern both 4 3",
            "env": "FMM_MODE=%s;S4FMM_NG=%d;%s" % (mode, ng, inj_env),
            "n_G_actual": str(calc_nG_actual(mode, ng)), "passes": "2",
            "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "2", "k_retry": "3", "retry_call": "2",
            "control_group": "NO", "exp_rc1": "20", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "1", "exp_class": "REPORTED_FAILURE",
            "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD", "exp_I5": "HOLD", "exp_I6": "HOLD", "exp_I7": "HOLD",
            "exp_san": "0", "exp_stage": "-",
            "basis": "U246; REGRESS_R7_M3.tsv:%s; -fsanitize=address,undefined" % orig_pid,
            "status": "INFLUENCED"
        })
    # 6 G6 seam cells
    g6_rep = [
        ("01", "seamF-F3-san", "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=clm:1", "R4-CLM1-F", hashes.get("lib_F3_seamF_san", "-")),
        ("02", "seamF-F3-san", "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=linearsolve:1:1:info", "R4-SI01-F", hashes.get("lib_F3_seamF_san", "-")),
        ("03", "seamF-F3-san", "FMM_MODE=closed1d;S4FMM_NG=5;S4FMM_INJECT=linearsolve_null2:130:1", "R4-CL01-F", hashes.get("lib_F3_seamF_san", "-")),
        ("04", "seamF-F3-san", "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=alloc:18", "R4-AL18-F", hashes.get("lib_F3_seamF_san", "-")),
        ("05", "seamF-F3-san", "FMM_MODE=jones;S4FMM_NG=5;S4FMM_INJECT=acf:1", "R4-ACF1-F", hashes.get("lib_F3_seamF_san", "-")),
        ("06", "seamF-F3-san", "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=clm:3", "R4-CLM3-F", hashes.get("lib_F3_seamF_san", "-")),
    ]
    for idx, drv, env_str, orig_pid, lsha in g6_rep:
        rows.append({
            "point_id": "M2-03-G6-%s-F3" % idx, "item": "M2-03", "tree": "F3",
            "driver": drv, "driver_sha256": hashes.get(drv, "-"), "lib_sha256": lsha,
            "gdb_script": "-", "argv": "pattern both 4 3",
            "env": env_str,
            "n_G_actual": "5", "passes": "2",
            "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "2", "k_retry": "3", "retry_call": "2",
            "control_group": "NO", "exp_rc1": "20", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "1", "exp_class": "REPORTED_FAILURE",
            "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD", "exp_I5": "HOLD", "exp_I6": "HOLD", "exp_I7": "HOLD",
            "exp_san": "0", "exp_stage": "-",
            "basis": "U246; REGRESS_R7_M3.tsv:%s; -fsanitize=address,undefined" % orig_pid,
            "status": "INFLUENCED"
        })
    # 12 M2-01 repair points in sanitizer
    for idx, mode, ng, inj, wrap, hook_desc, tgt_layer in init_configs:
        rows.append({
            "point_id": "M2-03-REP-INIT-%s-F3" % idx, "item": "M2-03", "tree": "F3",
            "driver": "init-F3-san", "driver_sha256": hashes.get("init-F3-san", "-"), "lib_sha256": lib_f3_san,
            "gdb_script": "-", "argv": "pattern both 4 3",
            "env": "FMM_MODE=%s;S4FMM_NG=%d;S4FMM_INJECT=%s" % (mode, ng, inj),
            "n_G_actual": str(calc_nG_actual(mode, ng)), "passes": "2",
            "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "2", "k_retry": "3", "retry_call": "2",
            "control_group": "NO", "exp_rc1": "20", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "1", "exp_class": "REPORTED_FAILURE",
            "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD", "exp_I5": "HOLD", "exp_I6": "HOLD", "exp_I7": "HOLD",
            "exp_san": "0", "exp_stage": "-",
            "basis": "U246; M2-01-%s-F3; -fsanitize=address,undefined" % idx,
            "status": "INFLUENCED"
        })
    for idx, mode, ng in poly_configs:
        rows.append({
            "point_id": "M2-03-REP-POLY-%s-F3" % idx, "item": "M2-03", "tree": "F3",
            "driver": "polyinj-F3-san", "driver_sha256": hashes.get("polyinj-F3-san", "-"), "lib_sha256": lib_f3_san,
            "gdb_script": "-", "argv": "pattern both 4 3",
            "env": "FMM_MODE=%s;S4FMM_NG=%d;S4FMM_INJECT=win:1" % (mode, ng),
            "n_G_actual": str(calc_nG_actual(mode, ng)), "passes": "2",
            "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "2", "k_retry": "3", "retry_call": "2",
            "control_group": "NO", "exp_rc1": "20", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "1", "exp_class": "REPORTED_FAILURE",
            "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD", "exp_I5": "HOLD", "exp_I6": "HOLD", "exp_I7": "HOLD",
            "exp_san": "0", "exp_stage": "-",
            "basis": "U246; M2-01-%s-F3; -fsanitize=address,undefined" % idx,
            "status": "INFLUENCED"
        })

    # -------------------------------------------------------------
    # M2-04: Dual target (2 test + 2 control = 4 points)
    # -------------------------------------------------------------
    rows.append({
        "point_id": "M2-04-01-F3", "item": "M2-04", "tree": "F3",
        "driver": "dual-F3-dbg", "driver_sha256": hashes.get("dual-F3-dbg", "-"), "lib_sha256": lib_f3_dbg,
        "gdb_script": "-", "argv": "pattern both 4 3",
        "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=s4malloc;S4FMM_NTH=1;S4FMM_INJECT2=s4malloc;S4FMM_NTH2=2",
        "n_G_actual": "5", "passes": "2",
        "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "2", "k_retry": "3", "retry_call": "2",
        "control_group": "NO", "exp_rc1": "20", "exp_rc2": "20", "exp_signal": "0", "exp_hit": "2", "exp_class": "REPORTED_FAILURE",
        "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD", "exp_I5": "HOLD", "exp_I6": "HOLD", "exp_I7": "-",
        "exp_san": "-", "exp_stage": "-",
        "basis": "U244(a); DUAL_HARNESS_R8_M2a2.tsv; INDEX_DERIVATION_R8_M2a2_R2.tsv",
        "status": "INFLUENCED"
    })
    rows.append({
        "point_id": "M2-04-02-F3", "item": "M2-04", "tree": "F3",
        "driver": "layers-dual-F3-dbg", "driver_sha256": hashes.get("layers-dual-F3-dbg", "-"), "lib_sha256": lib_f3_dbg,
        "gdb_script": "-", "argv": "pattern both 4 3",
        "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=PP1;S4FMM_INJECT=s4malloc;S4FMM_NTH=1;S4FMM_INJECT2=s4malloc;S4FMM_NTH2=4",
        "n_G_actual": "5", "passes": "2",
        "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "2", "k_retry": "3", "retry_call": "2",
        "control_group": "NO", "exp_rc1": "20", "exp_rc2": "20", "exp_signal": "0", "exp_hit": "2", "exp_class": "REPORTED_FAILURE",
        "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD", "exp_I5": "HOLD", "exp_I6": "HOLD", "exp_I7": "-",
        "exp_san": "-", "exp_stage": "-",
        "basis": "U244(b); DUAL_HARNESS_R8_M2a2.tsv; INDEX_DERIVATION_R8_M2a2_R2.tsv; S4.cpp:1894",
        "status": "INFLUENCED"
    })
    rows.append({
        "point_id": "M2-04-CTRL-01-F3", "item": "M2-04-CTRL", "tree": "F3",
        "driver": "dual-F3-dbg", "driver_sha256": hashes.get("dual-F3-dbg", "-"), "lib_sha256": lib_f3_dbg,
        "gdb_script": "-", "argv": "pattern both 4 3",
        "env": "FMM_MODE=fft;S4FMM_NG=5",
        "n_G_actual": "5", "passes": "2",
        "inj_call": "-", "k_before": "0", "k_fail": "-", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
        "control_group": "YES", "exp_rc1": "0", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "0", "exp_class": "CONTROL_OK",
        "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
        "exp_san": "-", "exp_stage": "-",
        "basis": "no injection; control group for M2-04 (single layer)",
        "status": "INFLUENCED"
    })
    rows.append({
        "point_id": "M2-04-CTRL-02-F3", "item": "M2-04-CTRL", "tree": "F3",
        "driver": "layers-dual-F3-dbg", "driver_sha256": hashes.get("layers-dual-F3-dbg", "-"), "lib_sha256": lib_f3_dbg,
        "gdb_script": "-", "argv": "pattern both 4 3",
        "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=PP1",
        "n_G_actual": "5", "passes": "2",
        "inj_call": "-", "k_before": "0", "k_fail": "-", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
        "control_group": "YES", "exp_rc1": "0", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "0", "exp_class": "CONTROL_OK",
        "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
        "exp_san": "-", "exp_stage": "-",
        "basis": "no injection; control group for M2-04 (multi-layer PP1)",
        "status": "INFLUENCED"
    })

    # -------------------------------------------------------------
    # M2-05: Other layers (4 test + 4 control = 8 points)
    # -------------------------------------------------------------
    l_configs = [
        ("P0", 1, 0, "P0"),
        ("P2", 1, 2, "P2"),
        ("PP1", 1, 1, "PP1"),
        ("PP2", 3, 2, "PP2"),
    ]
    for layout, nth, tgt, tag in l_configs:
        rows.append({
            "point_id": "M2-05-%s-F3" % tag, "item": "M2-05", "tree": "F3",
            "driver": "layers-F3-dbg", "driver_sha256": hashes.get("layers-F3-dbg", "-"), "lib_sha256": lib_f3_dbg,
            "gdb_script": "-", "argv": "pattern both 4 3",
            "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=%s;S4FMM_INJECT=s4malloc;S4FMM_NTH=%d" % (layout, nth),
            "n_G_actual": "5", "passes": "2",
            "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "2", "k_retry": "3", "retry_call": "2",
            "control_group": "NO", "exp_rc1": "20", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "1", "exp_class": "REPORTED_FAILURE",
            "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD", "exp_I5": "HOLD", "exp_I6": "HOLD", "exp_I7": "-",
            "exp_san": "-", "exp_stage": "-",
            "basis": "U245; INDEX_DERIVATION_R8_M2a2_R2.tsv; fmm_FFT.cpp:75,83; S4.cpp:1894",
            "status": "INFLUENCED"
        })
        rows.append({
            "point_id": "M2-05-CTRL-%s-F3" % tag, "item": "M2-05-CTRL", "tree": "F3",
            "driver": "layers-F3-dbg", "driver_sha256": hashes.get("layers-F3-dbg", "-"), "lib_sha256": lib_f3_dbg,
            "gdb_script": "-", "argv": "pattern both 4 3",
            "env": "FMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=%s" % layout,
            "n_G_actual": "5", "passes": "2",
            "inj_call": "-", "k_before": "0", "k_fail": "-", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
            "control_group": "YES", "exp_rc1": "0", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "0", "exp_class": "CONTROL_OK",
            "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
            "exp_san": "-", "exp_stage": "-",
            "basis": "no injection; control group for M2-05 layout %s" % layout,
            "status": "INFLUENCED"
        })

    # -------------------------------------------------------------
    # M2-06: K-1 tensor path (1 test + 1 control = 2 points)
    # -------------------------------------------------------------
    rows.append({
        "point_id": "M2-06-01-F3", "item": "M2-06", "tree": "F3",
        "driver": "nan-F3", "driver_sha256": hashes.get("nan-F3", "-"), "lib_sha256": lib_f3_buf,
        "gdb_script": "-", "argv": "pattern both 4 3",
        "env": "FMM_MODE=tensor;S4FMM_NG=5;S4FMM_INJECT=linearsolve_nanbuf:244:1",
        "n_G_actual": "5", "passes": "2",
        "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
        "control_group": "NO", "exp_rc1": "0", "exp_rc2": "-", "exp_signal": "0", "exp_hit": "1", "exp_class": "SILENT_SWALLOW",
        "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
        "exp_san": "-", "exp_stage": "-",
        "basis": "U240; K1_ANCHOR_R8_M2a2.tsv; [源码]: fmm_closed.cpp:244 tensor branch has no isfinite check",
        "status": "INFLUENCED"
    })
    rows.append({
        "point_id": "M2-06-CTRL-01-F3", "item": "M2-06-CTRL", "tree": "F3",
        "driver": "nan-F3", "driver_sha256": hashes.get("nan-F3", "-"), "lib_sha256": lib_f3_buf,
        "gdb_script": "-", "argv": "pattern both 4 3",
        "env": "FMM_MODE=tensor;S4FMM_NG=5",
        "n_G_actual": "5", "passes": "2",
        "inj_call": "-", "k_before": "0", "k_fail": "-", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
        "control_group": "YES", "exp_rc1": "0", "exp_rc2": "-", "exp_signal": "0", "exp_hit": "0", "exp_class": "CONTROL_OK",
        "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
        "exp_san": "-", "exp_stage": "-",
        "basis": "no injection; control group for M2-06",
        "status": "INFLUENCED"
    })

    # -------------------------------------------------------------
    # M2-07: NB=1-8 grid (9 modes x NG 1..8: 72 controls + 9 injections = 81 points)
    # -------------------------------------------------------------
    all_modes = ["closed1d", "closed2d", "experimental", "fft", "kottke", "tensor", "jones", "nv", "vl"]
    drv_d003 = hashes.get("d003-F3-plain", "-")
    drv_d003plan = hashes.get("d003plan-F3-plain", "-")
    lib_f3_plain = hashes.get("lib_d003-F3-plain", "-")

    for m in all_modes:
        # 8 controls
        for ng in range(1, 9):
            act_ng = calc_nG_actual(m, ng)
            exp_rc = "20" if (m == "vl" and ng == 1) else "0"
            rows.append({
                "point_id": "M2-07-CTRL-%s-ng%d-F3" % (m, ng), "item": "M2-07-CTRL", "tree": "F3",
                "driver": "d003-F3-plain", "driver_sha256": drv_d003, "lib_sha256": lib_f3_plain,
                "gdb_script": "-", "argv": "pattern both 4 3",
                "env": "FMM_MODE=%s;S4FMM_NG=%d" % (m, ng),
                "n_G_actual": str(act_ng), "passes": "2",
                "inj_call": "-", "k_before": "0", "k_fail": "-", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
                "control_group": "YES", "exp_rc1": exp_rc, "exp_rc2": exp_rc, "exp_signal": "0", "exp_hit": "0", "exp_class": "CONTROL_OK",
                "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
                "exp_san": "-", "exp_stage": "-",
                "basis": "U243; M0 baseline (RESULTS_R8_NOINJECT_run1.tsv: vl NG=1 rc 20; others 0)",
                "status": "INFLUENCED"
            })
        # 1 representative injection at NG=5
        rows.append({
            "point_id": "M2-07-INJ-%s-ng5-F3" % m, "item": "M2-07", "tree": "F3",
            "driver": "d003plan-F3-plain", "driver_sha256": drv_d003plan, "lib_sha256": lib_f3_plain,
            "gdb_script": "-", "argv": "pattern both 4 3",
            "env": "FMM_MODE=%s;S4FMM_NG=5;S4FMM_INJECT=s4malloc;S4FMM_NTH=1" % m,
            "n_G_actual": "5", "passes": "2",
            "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
            "control_group": "NO", "exp_rc1": "NZ", "exp_rc2": "-", "exp_signal": "0", "exp_hit": "1", "exp_class": "REPORTED_FAILURE",
            "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
            "exp_san": "-", "exp_stage": "-",
            "basis": "U243; representative s4malloc injection at NG=5; NZ token (verdict_m2_r8m2a2.py)",
            "status": "INFLUENCED"
        })

    # -------------------------------------------------------------
    # M2-09: CTRL_SEAM clean control (2 points: F3, F2)
    # -------------------------------------------------------------
    rows.append({
        "point_id": "M2-09-01-F3", "item": "M2-09-CTRL", "tree": "F3",
        "driver": "seam-fmmret-F3", "driver_sha256": hashes.get("seam-fmmret-F3", "-"), "lib_sha256": hashes.get("lib_seam-fmmret-F3", "-"),
        "gdb_script": "-", "argv": "pattern both 4 3",
        "env": "FMM_MODE=fft;S4FMM_NG=9",
        "n_G_actual": "9", "passes": "2",
        "inj_call": "-", "k_before": "0", "k_fail": "-", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
        "control_group": "YES", "exp_rc1": "0", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "0", "exp_class": "CONTROL_OK",
        "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
        "exp_san": "-", "exp_stage": "-",
        "basis": "U239; DRIVERS_R8.tsv:7; RESULTS_R8_D_pass1.tsv:4",
        "status": "INFLUENCED"
    })
    rows.append({
        "point_id": "M2-09-01-F2", "item": "M2-09-CTRL", "tree": "F2",
        "driver": "seam-fmmret-F2", "driver_sha256": hashes.get("seam-fmmret-F2", "-"), "lib_sha256": hashes.get("lib_seam-fmmret-F2", "-"),
        "gdb_script": "-", "argv": "pattern both 4 3",
        "env": "FMM_MODE=fft;S4FMM_NG=9",
        "n_G_actual": "9", "passes": "2",
        "inj_call": "-", "k_before": "0", "k_fail": "-", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
        "control_group": "YES", "exp_rc1": "0", "exp_rc2": "0", "exp_signal": "0", "exp_hit": "0", "exp_class": "CONTROL_OK",
        "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
        "exp_san": "-", "exp_stage": "-",
        "basis": "U239; DRIVERS_R7_SEAM.tsv:4",
        "status": "INFLUENCED"
    })

    # -------------------------------------------------------------
    # M2-10: B-side baseline (1 point: tree B)
    # -------------------------------------------------------------
    rows.append({
        "point_id": "M2-10-01-B", "item": "M2-10", "tree": "B",
        "driver": "r6dnv1-B-dbg", "driver_sha256": hashes.get("r6dnv1-B-dbg", "-"), "lib_sha256": lib_b_dbg,
        "gdb_script": "testing/d003/stage_s4/m210_b_r8m2a2_R2.gdb", "argv": "pattern both 4 3",
        "env": "FMM_MODE=vl;S4FMM_NG=1",
        "n_G_actual": "1", "passes": "2",
        "inj_call": "1", "k_before": "0", "k_fail": "1", "k_preretry": "-", "k_retry": "-", "retry_call": "-",
        "control_group": "NO", "exp_rc1": "20", "exp_rc2": "-", "exp_signal": "0", "exp_hit": "-", "exp_class": "BASELINE_ONLY",
        "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
        "exp_san": "-", "exp_stage": "-",
        "basis": "U247; M210_BREAKPOINTS_R8_M2a2_R2.tsv; tree_B/S4/S4.cpp:2362,2416,2432",
        "status": "INFLUENCED"
    })

    total = len(rows)

    # -------------------------------------------------------------
    # Assertions
    # -------------------------------------------------------------
    # Read design table points
    design_points = {}
    with open(DESIGN_TSV, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip(): continue
            parts = line.rstrip().split("\t")
            if len(parts) >= 8 and parts[0] != "item":
                design_points[parts[0]] = int(parts[7])

    # Count by base item (mapping M2-xx-CTRL to M2-xx)
    item_tree_counts = {}
    base_item_counts = {}
    m201_ctrl_count = 0
    for r in rows:
        it = (r["item"], r["tree"])
        item_tree_counts[it] = item_tree_counts.get(it, 0) + 1
        base_item = r["item"].replace("-CTRL", "")
        base_item_counts[base_item] = base_item_counts.get(base_item, 0) + 1
        if r["item"] == "M2-01-CTRL":
            m201_ctrl_count += 1

    # Assert 1: sum of item x tree counts == total rows
    s = sum(item_tree_counts.values())
    if s != total:
        print("prereg_r8m2a2: FAIL sum of item counts %d != total %d" % (s, total))
        return 1

    # Assert 2: each design item point count equals design table
    for it, exp_cnt in design_points.items():
        actual_cnt = base_item_counts.get(it, 0)
        if actual_cnt != exp_cnt:
            print("prereg_r8m2a2: FAIL item %s count %d != design points %d" % (it, actual_cnt, exp_cnt))
            return 1

    # Assert 3: M2-01 has >= 9 controls
    if m201_ctrl_count < 9:
        print("prereg_r8m2a2: FAIL M2-01 controls %d < 9" % m201_ctrl_count)
        return 1

    # Write files
    os.makedirs(EV, exist_ok=True)
    with open(PREREG, "x", encoding="utf-8") as fh:
        fh.write("\t".join(COLS) + "\n")
        for r in rows:
            fh.write("\t".join(r[c] for c in COLS) + "\n")

    digest = sha256_file(PREREG)
    with open(SHA_FILE, "x", encoding="utf-8") as fh:
        fh.write("%s  PREREG_M2_R8_M2a2.tsv\n" % digest)

    utc_now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(TS_FILE, "x", encoding="utf-8") as fh:
        fh.write("PREREG_M2_R8_M2a2.tsv frozen at %s\n" % utc_now)

    not_written = {
        "M2-00": "COVERED_BY_M0: all six A_CTRL combos covered by M0 (A10 crosswalk R2)",
        "M2-02": "NOT_FOUND_IN_SCOPE: STAGE_E_SEARCH_R8_M2a2_R2.tsv shows 0 in-scope stage e candidates",
        "M2-08": "NOT_FOUND: CATC_SEARCH_R8_M2a2_R2B.tsv shows 0 category C configurations in grid",
        "M3_DEFERRED": "M3_DEFERRED: Python/Lua visibility deferred to M3 (U235)",
    }

    with open(COUNT_FILE, "x", encoding="utf-8") as fh:
        fh.write("# PREREG_M2_COUNT_R8_M2a2 -- counts by item x tree (sum asserted = total)\n")
        for k in sorted(item_tree_counts):
            fh.write("COUNT\t%s\t%s\t%d\n" % (k[0], k[1], item_tree_counts[k]))
        fh.write("TOTAL_ROWS\t%d\n" % total)
        fh.write("SUM_OF_ITEMS\t%d\n" % s)
        fh.write("ASSERT_SUM_EQ_TOTAL\tPASS\n")
        fh.write("ASSERT_ITEM_POINTS_EQ_DESIGN\tPASS\n")
        fh.write("ASSERT_M201_CONTROLS_GE_9\tPASS\n")
        for k in sorted(not_written):
            fh.write("NOT_WRITTEN\t%s\t%s\n" % (k, not_written[k]))

    print("prereg_r8m2a2: rows=%d sha256=%s" % (total, digest))
    return 0

if __name__ == "__main__":
    sys.exit(main())
