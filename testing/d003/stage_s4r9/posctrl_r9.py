#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m0; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# posctrl_r9.py -- Synthetic positive controls for P05-S4 R9 (Section 4 S-J).
# Executes 41 cases:
#  - 34 r8m2c regression cases (A..R, S1..S8, P1..P7)
#  - 7 new r8m2e cases (D1..D7):
#     D1: crash_call mismatch -> MISMATCH
#     D2: crash_site mismatch -> MISMATCH
#     D3: exp_rc1="-" with rc1=MISSING -> does not judge (MATCH)
#     D4: post_call1_solution mismatch -> MISMATCH
#     D5: libc frame skipped and first S4/ frame extracted (facts test)
#     D6: SUPERSEDED statistics correct (verdict summary test)
#     D7: exp_crash_site normalized matching with [源码]推断 -> MATCH
# Calls formal scripts: facts_m2_r8m2e.py, state_judge_m2_r8m2e.py, verdict_m2_r8m2e.py, run_m2_r8m2e.py, smoke_gate_r8m2e.py.
# All paths parameterized. Scratch files strictly under EV/tmp/.
import argparse
import csv
import os
import re
import shutil
import subprocess
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
PREREG_DEFAULT = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2b", "PREREG_M2_EFFECTIVE_R8_M2b.tsv")
SANREF_DEFAULT = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2b", "PREREG_M2_SANREF_R8_M2b.tsv")
CTRL_MAP_DEFAULT = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "CONTROL_MAPPING_R8_M2a3.tsv")

FACTS_PY = os.path.join(REPO, "testing", "d003", "stage_s4r9", "facts_m2_r9.py")
STATE_JUDGE_PY = os.path.join(REPO, "testing", "d003", "stage_s4r9", "state_judge_m2_r9.py")
VERDICT_PY = os.path.join(REPO, "testing", "d003", "stage_s4r9", "verdict_m2_r9.py")
RUNNER_PY = os.path.join(REPO, "testing", "d003", "stage_s4r9", "run_m2_r9.py")
SMOKE_GATE_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "smoke_gate_r8m2e.py")
SUMMARY_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "generate_summary_tables_r8m2e.py")


def read_tsv_dict(path, key_col="point_id"):
    rows = {}
    if not path or not os.path.isfile(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader((line for line in fh if not line.startswith("#")), delimiter="\t"):
            k = r.get(key_col)
            if k:
                rows[k] = r
    return rows


def make_clean_gdb_log(pid, item, rc1=20, ec=20):
    """Generate standard synthetic gdb log that passes all applicable invariants."""
    is_dual = (item == "M2-04")
    lines = []
    # k = 0
    lines.append("R6BSTATE 0 n_layers 3 n_G 1")
    lines.append("R6STATE 0 layer 0 modes_null 1 modes_ptr 0 copy -1 nshapes 0")
    lines.append("R6STATE 0 layer 1 modes_null 1 modes_ptr 0 copy -1 nshapes 1")
    lines.append("R6STATE 0 layer 2 modes_null 1 modes_ptr 0 copy -1 nshapes 0")
    lines.append("R6BSTATE 0 layer 0 modes_null 1 q_len 2 q_sha256 NA")
    lines.append("R6BSTATE 0 layer 1 modes_null 1 q_len 2 q_sha256 NA")
    lines.append("R6BSTATE 0 layer 2 modes_null 1 q_len 2 q_sha256 NA")
    lines.append("R6BSTATE 0 solution null")
    lines.append("R6BSTATE 0 cache_count 0 cache_layers none")

    # call 1
    lines.append("R6CREQ 1 1")
    lines.append("R6BCLM ENTER idx 0 name Above")
    lines.append("R6BCLM RETURN idx 0 name Above rc 0")
    lines.append("R6BCLM ENTER idx 1 name Slab")
    lines.append(f"R6BCLM RETURN idx 1 name Slab rc {rc1}")
    lines.append(f"R6CALLS 1 {rc1}")
    lines.append(f"RC first {rc1}")

    # k = 1
    lines.append("R6BSTATE 1 n_layers 3 n_G 1")
    lines.append("R6STATE 1 layer 0 modes_null 0 modes_ptr 0x1 copy -1 nshapes 0")
    lines.append("R6STATE 1 layer 1 modes_null 1 modes_ptr 0 copy -1 nshapes 1")
    lines.append("R6STATE 1 layer 2 modes_null 1 modes_ptr 0 copy -1 nshapes 0")
    lines.append("R6BSTATE 1 layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
    lines.append("R6BSTATE 1 layer 1 modes_null 1 q_len 2 q_sha256 NA")
    lines.append("R6BSTATE 1 layer 2 modes_null 1 q_len 2 q_sha256 NA")
    lines.append("R6BSTATE 1 solution solved 0=0 1=0 2=0")
    lines.append("R6BSTATE 1 cache_count 0 cache_layers none")

    # k = 2
    lines.append("R6BSTATE 2 n_layers 3 n_G 1")
    lines.append("R6STATE 2 layer 0 modes_null 0 modes_ptr 0x1 copy -1 nshapes 0")
    lines.append("R6STATE 2 layer 1 modes_null 1 modes_ptr 0 copy -1 nshapes 1")
    lines.append("R6STATE 2 layer 2 modes_null 1 modes_ptr 0 copy -1 nshapes 0")
    lines.append("R6BSTATE 2 layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
    lines.append("R6BSTATE 2 layer 1 modes_null 1 q_len 2 q_sha256 NA")
    lines.append("R6BSTATE 2 layer 2 modes_null 1 q_len 2 q_sha256 NA")
    lines.append("R6BSTATE 2 solution solved 0=0 1=0 2=0")
    lines.append("R6BSTATE 2 cache_count 0 cache_layers none")

    # call 2 (retry)
    if not is_dual:
        lines.append("R6CREQ 2 1")
        lines.append("R6BCLM ENTER idx 1 name Slab")
        lines.append("R6BCLM RETURN idx 1 name Slab rc 0")
        lines.append("R6BCLM ENTER idx 2 name Below")
        lines.append("R6BCLM RETURN idx 2 name Below rc 0")
        lines.append("R6CALLS 2 0")
        lines.append("RC retry 0")
        lines.append("S4FMM HITCOUNT 1")

        # k = 3
        lines.append("R6BSTATE 3 n_layers 3 n_G 1")
        lines.append("R6STATE 3 layer 0 modes_null 0 modes_ptr 0x1 copy -1 nshapes 0")
        lines.append("R6STATE 3 layer 1 modes_null 0 modes_ptr 0x2 copy -1 nshapes 1")
        lines.append("R6STATE 3 layer 2 modes_null 0 modes_ptr 0x3 copy -1 nshapes 0")
        lines.append("R6BSTATE 3 layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
        lines.append("R6BSTATE 3 layer 1 modes_null 0 q_len 2 q_sha256 bbbbbbbb")
        lines.append("R6BSTATE 3 layer 2 modes_null 0 q_len 2 q_sha256 cccccccc")
        lines.append("R6BSTATE 3 solution solved 0=1 1=1 2=1")
        lines.append("R6BSTATE 3 cache_count 0 cache_layers none")

        # k = 4
        lines.append("R6BSTATE 4 n_layers 3 n_G 1")
        lines.append("R6BSTATE 4 layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
        lines.append("R6BSTATE 4 layer 1 modes_null 0 q_len 2 q_sha256 bbbbbbbb")
        lines.append("R6BSTATE 4 layer 2 modes_null 0 q_len 2 q_sha256 cccccccc")
        lines.append("R6BSTATE 4 solution solved 0=1 1=1 2=1")
        lines.append("R6BSTATE 4 cache_count 0 cache_layers none")
    else:
        # Dual failure: call 2 is second failure
        lines.append("R6CREQ 2 1")
        lines.append("R6BCLM ENTER idx 1 name Slab")
        lines.append("R6BCLM RETURN idx 1 name Slab rc 20")
        lines.append("R6CALLS 2 20")
        lines.append("RC retry 20")
        lines.append("S4FMM HITCOUNT 2")
        lines.append("S4FMM HIT dual target2 real S4_malloc failure: FMM call 16 B (stream index 2, hit2=1 total=2)")

        # k = 3
        lines.append("R6BSTATE 3 n_layers 3 n_G 1")
        lines.append("R6STATE 3 layer 0 modes_null 0 modes_ptr 0x1 copy -1 nshapes 0")
        lines.append("R6STATE 3 layer 1 modes_null 1 modes_ptr 0 copy -1 nshapes 1")
        lines.append("R6STATE 3 layer 2 modes_null 1 modes_ptr 0 copy -1 nshapes 0")
        lines.append("R6BSTATE 3 layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
        lines.append("R6BSTATE 3 layer 1 modes_null 1 q_len 2 q_sha256 NA")
        lines.append("R6BSTATE 3 layer 2 modes_null 1 q_len 2 q_sha256 NA")
        lines.append("R6BSTATE 3 solution solved 0=0 1=0 2=0")
        lines.append("R6BSTATE 3 cache_count 0 cache_layers none")

        # call 3 (final retry)
        lines.append("R6CREQ 3 1")
        lines.append("R6BCLM ENTER idx 1 name Slab")
        lines.append("R6BCLM RETURN idx 1 name Slab rc 0")
        lines.append("R6BCLM ENTER idx 2 name Below")
        lines.append("R6BCLM RETURN idx 2 name Below rc 0")
        lines.append("R6CALLS 3 0")

        # k = 4
        lines.append("R6BSTATE 4 n_layers 3 n_G 1")
        lines.append("R6STATE 4 layer 0 modes_null 0 modes_ptr 0x1 copy -1 nshapes 0")
        lines.append("R6STATE 4 layer 1 modes_null 0 modes_ptr 0x2 copy -1 nshapes 1")
        lines.append("R6STATE 4 layer 2 modes_null 0 modes_ptr 0x3 copy -1 nshapes 0")
        lines.append("R6BSTATE 4 layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
        lines.append("R6BSTATE 4 layer 1 modes_null 0 q_len 2 q_sha256 bbbbbbbb")
        lines.append("R6BSTATE 4 layer 2 modes_null 0 q_len 2 q_sha256 cccccccc")
        lines.append("R6BSTATE 4 solution solved 0=1 1=1 2=1")
        lines.append("R6BSTATE 4 cache_count 0 cache_layers none")

    # inferior exit
    if ec == 0:
        lines.append("[Inferior 1 (process 123) exited normally]")
    else:
        oct_ec = oct(ec)[2:]
        if len(oct_ec) == 1:
            oct_ec = "0" + oct_ec
        lines.append(f"[Inferior 1 (process 123) exited with code 0{oct_ec}]")

    return "\n".join(lines) + "\n"


def make_control_gdb_log(cid):
    """Generate control run synthetic gdb log (baseline)."""
    lines = []
    for k in range(5):
        lines.append(f"R6BSTATE {k} n_layers 3 n_G 1")
        lines.append(f"R6STATE {k} layer 0 modes_null 0 modes_ptr 0x1 copy -1 nshapes 0")
        lines.append(f"R6STATE {k} layer 1 modes_null 0 modes_ptr 0x2 copy -1 nshapes 1")
        lines.append(f"R6STATE {k} layer 2 modes_null 0 modes_ptr 0x3 copy -1 nshapes 0")
        lines.append(f"R6BSTATE {k} layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
        lines.append(f"R6BSTATE {k} layer 1 modes_null 0 q_len 2 q_sha256 bbbbbbbb")
        lines.append(f"R6BSTATE {k} layer 2 modes_null 0 q_len 2 q_sha256 cccccccc")
        lines.append(f"R6BSTATE {k} solution solved 0=1 1=1 2=1")
        lines.append(f"R6BSTATE {k} cache_count 0 cache_layers none")
    lines.append("R6CALLS 1 0")
    lines.append("R6CALLS 2 0")
    lines.append("S4FMM HITCOUNT 0")
    lines.append("[Inferior 1 (process 123) exited normally]")
    return "\n".join(lines) + "\n"


def make_m210_gdb_log():
    lines = [
        "M210_HIT: Simulation_ComputeLayerModes line 2362 returns 20",
        "R6CALLS 1 20",
        "RC first 20",
        "[Inferior 1 (process 123) exited with code 024]"
    ]
    return "\n".join(lines) + "\n"


def setup_base_case_dirs(base_dir, prereg_rows):
    """Create full 150-point standard synthetic run environment for pass1 and pass2."""
    for pas in ("1", "2"):
        p_dir = os.path.join(base_dir, f"pass{pas}")
        for r in prereg_rows:
            pid = r["point_id"]
            pt_dir = os.path.join(p_dir, pid)
            os.makedirs(pt_dir, exist_ok=True)

            is_ctrl = (r.get("control_group") == "YES" or r.get("exp_class") == "CONTROL_OK")
            item = r.get("item", "")
            class_rule = r.get("class_rule", "")

            # Exit code
            ec = 0
            if item == "M2-10" or class_rule == "BASELINE_ONLY_RULE":
                ec = 20
            elif class_rule == "NATIVE_FAIL_CONTROL":
                ec = 20
            elif not is_ctrl and r.get("exp_rc1") not in (None, "", "-", "0", "NZ"):
                ec = int(r["exp_rc1"])
            elif not is_ctrl and r.get("exp_rc1") == "NZ":
                ec = 20

            with open(os.path.join(pt_dir, "exitcode.txt"), "w") as fh:
                fh.write(f"{ec}\n")

            # stdout
            if r.get("exp_rc1") == "NZ":
                rc1 = 20
            elif r.get("exp_rc1") not in (None, "", "-"):
                rc1 = int(r["exp_rc1"])
            elif class_rule in ("BASELINE_ONLY_RULE", "NATIVE_FAIL_CONTROL"):
                rc1 = 20
            else:
                rc1 = 0

            if r.get("exp_rc2") not in (None, "", "-"):
                rc2 = int(r["exp_rc2"])
            elif class_rule == "NATIVE_FAIL_CONTROL":
                rc2 = 20
            else:
                rc2 = 0

            rc3 = int(r.get("exp_rc3", 0) if r.get("exp_rc3") not in (None, "", "-") else 0)
            hit = int(r.get("exp_hit", 0) if r.get("exp_hit") not in (None, "", "-") else 0)

            stdout_lines = [
                f"R6CALLS 1 {rc1}",
                f"RC first {rc1}",
                f"R6CALLS 2 {rc2}",
                f"RC retry {rc2}",
                f"R6CALLS 3 {rc3}",
                f"S4FMM HITCOUNT {hit}",
            ]
            if item == "M2-04":
                stdout_lines.append("S4FMM HIT dual target2 real S4_malloc failure: FMM call 16 B (stream index 2, hit2=1 total=2)")

            with open(os.path.join(pt_dir, "stdout.txt"), "w") as fh:
                fh.write("\n".join(stdout_lines) + "\n")

            with open(os.path.join(pt_dir, "stderr.txt"), "w") as fh:
                fh.write("")

            # Field dumps
            for c_n in (1, 2, 3):
                with open(os.path.join(pt_dir, f"call{c_n}.txt"), "w") as fh:
                    fh.write(f"call {c_n} standard field dump\n1.0 2.0 3.0\n")

            # gdb.log if dbg
            if r.get("gdb_script") not in (None, "", "-"):
                if item == "M2-10" or class_rule == "BASELINE_ONLY_RULE":
                    gdb_txt = make_m210_gdb_log()
                elif is_ctrl:
                    gdb_txt = make_control_gdb_log(pid)
                else:
                    gdb_txt = make_clean_gdb_log(pid, item, rc1=rc1, ec=ec)
                with open(os.path.join(pt_dir, "gdb.log"), "w") as fh:
                    fh.write(gdb_txt)

        # Also populate reference points from SANREF_DEFAULT if present
        if os.path.isfile(SANREF_DEFAULT):
            with open(SANREF_DEFAULT, encoding="utf-8") as sfh:
                s_rows = list(csv.DictReader((line for line in sfh if not line.startswith("#")), delimiter="\t"))
            for sr in s_rows:
                spid = sr["point_id"]
                pt_dir = os.path.join(p_dir, spid)
                os.makedirs(pt_dir, exist_ok=True)
                with open(os.path.join(pt_dir, "exitcode.txt"), "w") as fh:
                    fh.write("20\n")
                s_lines = [
                    "R6CALLS 1 20",
                    "RC first 20",
                    "R6CALLS 2 0",
                    "RC retry 0",
                    "R6CALLS 3 0",
                    "S4FMM HITCOUNT 1",
                ]
                with open(os.path.join(pt_dir, "stdout.txt"), "w") as fh:
                    fh.write("\n".join(s_lines) + "\n")
                with open(os.path.join(pt_dir, "stderr.txt"), "w") as fh:
                    fh.write("")
                for c_n in (1, 2, 3):
                    with open(os.path.join(pt_dir, f"call{c_n}.txt"), "w") as fh:
                        fh.write(f"call {c_n} standard field dump\n1.0 2.0 3.0\n")


def run_pipeline(work_dir, prereg_path, ctrl_map_path=CTRL_MAP_DEFAULT, assert_total=150):
    """Run facts -> state_judge -> verdict on work_dir."""
    p1_dir = os.path.join(work_dir, "pass1")
    p2_dir = os.path.join(work_dir, "pass2")

    f1_tsv = os.path.join(work_dir, "FACTS_pass1.tsv")
    f2_tsv = os.path.join(work_dir, "FACTS_pass2.tsv")
    s1_tsv = os.path.join(work_dir, "STATE_pass1.tsv")
    s2_tsv = os.path.join(work_dir, "STATE_pass2.tsv")
    s_sum = os.path.join(work_dir, "STATE_SUMMARY.txt")
    v_tsv = os.path.join(work_dir, "VERDICT.tsv")
    v_sum = os.path.join(work_dir, "VERDICT_SUMMARY.txt")

    # Combine prereg with SANREF for facts extraction
    facts_prereg = os.path.join(work_dir, "facts_combined_prereg.tsv")
    with open(prereg_path, encoding="utf-8") as fh:
        p_lines = [l for l in fh if not l.startswith("#")]
    with open(facts_prereg, "w", encoding="utf-8") as out_fh:
        out_fh.write(p_lines[0])  # header
        for l in p_lines[1:]:
            out_fh.write(l)
        if os.path.isfile(SANREF_DEFAULT):
            with open(SANREF_DEFAULT, encoding="utf-8") as sfh:
                s_lines = [l for l in sfh if not l.startswith("#")]
            for l in s_lines[1:]:
                out_fh.write(l)

    # 1. Facts pass 1
    r_f1 = subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", facts_prereg,
                           "--run-dir", p1_dir, "--pass", "1", "--out", f1_tsv],
                          capture_output=True, text=True)
    if r_f1.returncode != 0:
        return False, f"facts1 failed: {r_f1.stderr}"

    # 2. Facts pass 2
    r_f2 = subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", facts_prereg,
                           "--run-dir", p2_dir, "--pass", "2", "--out", f2_tsv],
                          capture_output=True, text=True)
    if r_f2.returncode != 0:
        return False, f"facts2 failed: {r_f2.stderr}"

    # 3. State judge
    r_sj = subprocess.run([sys.executable, "-I", "-B", STATE_JUDGE_PY,
                           "--prereg", prereg_path,
                           "--control", ctrl_map_path,
                           "--ev", work_dir,
                           "--facts1", f1_tsv,
                           "--facts2", f2_tsv,
                           "--state-dir", work_dir,
                           "--dumps-dir", work_dir,
                           "--out-res", s1_tsv,
                           "--out-sum", s_sum],
                          capture_output=True, text=True)
    if r_sj.returncode != 0:
        return False, f"state_judge failed: {r_sj.stderr}"

    shutil.copyfile(s1_tsv, s2_tsv)

    # 4. Verdict
    v_cmd = [sys.executable, "-I", "-B", VERDICT_PY,
             "--prereg", prereg_path,
             "--facts1", f1_tsv,
             "--facts2", f2_tsv,
             "--state1", s1_tsv,
             "--state2", s2_tsv,
             "--control-map", ctrl_map_path,
             "--out-verdict", v_tsv,
             "--out-summary", v_sum]
    if assert_total is not None:
        v_cmd.extend(["--assert-total", str(assert_total)])

    r_v = subprocess.run(v_cmd, capture_output=True, text=True)
    if r_v.returncode != 0:
        return False, f"verdict failed: {r_v.stderr}"

    verdict_dict = {}
    with open(v_tsv, encoding="utf-8") as fh:
        for r in csv.DictReader((line for line in fh if not line.startswith("#")), delimiter="\t"):
            verdict_dict[r["point_id"]] = r

    return True, verdict_dict


def main():
    parser = argparse.ArgumentParser(description="P05-S4 POSCTRL runner v5")
    parser.add_argument("--prereg", default=PREREG_DEFAULT, help="Path to effective preregistration table")
    parser.add_argument("--control-map", default=CTRL_MAP_DEFAULT, help="Path to control mapping table")
    parser.add_argument("--ev", default=None, help="Evidence directory root")
    parser.add_argument("--out", required=True, help="Path to write POSCTRL result log")
    args = parser.parse_args()

    ev_root = os.path.abspath(args.ev or os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2e"))
    scratch = os.path.join(ev_root, "tmp", "posctrl_m2e_scratch")
    if os.path.exists(scratch):
        shutil.rmtree(scratch)
    os.makedirs(scratch, exist_ok=True)

    with open(args.prereg, encoding="utf-8") as fh:
        prereg_rows = list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))

    cases_results = []

    def record_case(case_id, description, passed, detail):
        status = "PASS" if passed else "FAIL"
        cases_results.append((case_id, description, status, detail))
        print(f"[{status}] {case_id}: {description} -- {detail}")

    # Case A: Clean baseline -> ALL MATCH
    c_dir = os.path.join(scratch, "case_A")
    setup_base_case_dirs(c_dir, prereg_rows)
    ok, v_a = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        matches = sum(1 for p in v_a.values() if p["verdict"] == "MATCH")
        unjudged = sum(1 for p in v_a.values() if p["verdict"] == "UNJUDGED")
        record_case("Case A", "全通基线验证 (All clean synthetic baseline passes)",
                    matches == 150,
                    f"MATCH={matches}/150, UNJUDGED={unjudged}")
    else:
        record_case("Case A", "全通基线验证", False, v_a)

    # Case B: rc1 mismatch on M2-01-01-F3
    c_dir = os.path.join(scratch, "case_B")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-01-01-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 0\nRC first 0\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 1\n")
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        with open(gp, "w") as fh:
            fh.write(make_clean_gdb_log("M2-01-01-F3", "M2-01", rc1=0, ec=0))
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("0\n")
    ok, v_b = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_b["M2-01-01-F3"]
        record_case("Case B", "单点 rc1 不符 (rc1 mismatch)",
                    r["verdict"] == "MISMATCH" and "exp_rc1(0!=20)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case B", "单点 rc1 不符", False, v_b)

    # Case C: rc2 mismatch on M2-01-01-F3
    c_dir = os.path.join(scratch, "case_C")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-01-01-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 20\nRC retry 20\nS4FMM HITCOUNT 1\n")
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        with open(gp, "w") as fh:
            fh.write(make_clean_gdb_log("M2-01-01-F3", "M2-01", rc1=20, ec=20).replace("RC retry 0", "RC retry 20").replace("R6CALLS 2 0", "R6CALLS 2 20"))
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("20\n")
    ok, v_c = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_c["M2-01-01-F3"]
        record_case("Case C", "单点 rc2 不符 (rc2 mismatch)",
                    r["verdict"] == "MISMATCH" and "exp_rc2(20!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case C", "单点 rc2 不符", False, v_c)

    # Case D: abnormal signal
    c_dir = os.path.join(scratch, "case_D")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("139\n")
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        with open(gp, "w") as fh:
            fh.write("Program terminated with signal SIGSEGV, Segmentation fault.\n")
    ok, v_d = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_d["M2-01-01-F3"]
        record_case("Case D", "异常退出信号 (signal mismatch)",
                    r["verdict"] == "MISMATCH" and "exp_signal(11!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case D", "异常退出信号", False, v_d)

    # Case E: hit mismatch
    c_dir = os.path.join(scratch, "case_E")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-01-01-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 0\n")
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        with open(gp, "w") as fh:
            fh.write(make_clean_gdb_log("M2-01-01-F3", "M2-01", rc1=20, ec=20).replace("S4FMM HITCOUNT 1", "S4FMM HITCOUNT 0"))
    ok, v_e = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_e["M2-01-01-F3"]
        record_case("Case E", "命中次数不符 (hit mismatch)",
                    r["verdict"] == "MISMATCH" and "exp_hit(0!=1)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case E", "命中次数不符", False, v_e)

    # Case F: hit2 mismatch on M2-04-01-F3
    c_dir = os.path.join(scratch, "case_F")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-04-01-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 20\nRC retry 20\nR6CALLS 3 0\nS4FMM HITCOUNT 2\n")
    ok, v_f = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_f["M2-04-01-F3"]
        record_case("Case F", "双失败 hit2 不符 (hit2 mismatch)",
                    r["verdict"] == "MISMATCH" and "exp_hit2(0!=1)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F", "双失败 hit2 不符", False, v_f)

    # Case F2: inject2_invalid
    c_dir = os.path.join(scratch, "case_F2")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-04-01-F3", "stderr.txt")
        with open(p, "w") as fh:
            fh.write("S4FMM INJECT2 INVALID: bad parameter\n")
    ok, v_f2 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_f2["M2-04-01-F3"]
        record_case("Case F2", "第二注入无效报错 (INJECT2 INVALID)",
                    r["verdict"] == "MISMATCH" and "exp_inject2_invalid(1!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F2", "第二注入无效报错", False, v_f2)

    # Case F3: inject2_suppressed
    c_dir = os.path.join(scratch, "case_F3")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-04-01-F3", "stderr.txt")
        with open(p, "w") as fh:
            fh.write("S4FMM INJECT2 SUPPRESSED: unreached\n")
    ok, v_f3 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_f3["M2-04-01-F3"]
        record_case("Case F3", "第二注入抑制报错 (INJECT2 SUPPRESSED)",
                    r["verdict"] == "MISMATCH" and "exp_inject2_suppressed(1!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F3", "第二注入抑制报错", False, v_f3)

    # Case F4: rc3 mismatch
    c_dir = os.path.join(scratch, "case_F4")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-04-01-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 20\nRC retry 20\nR6CALLS 3 20\nS4FMM HITCOUNT 2\nS4FMM HIT dual target2 real S4_malloc failure: FMM call 16 B (stream index 2, hit2=1 total=2)\n")
        gp = os.path.join(c_dir, pas, "M2-04-01-F3", "gdb.log")
        with open(gp, "w") as fh:
            fh.write(make_clean_gdb_log("M2-04-01-F3", "M2-04", rc1=20, ec=20).replace("R6CALLS 3 0", "R6CALLS 3 20"))
    ok, v_f4 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_f4["M2-04-01-F3"]
        record_case("Case F4", "双失败恢复调用 rc3 不符 (rc3 mismatch)",
                    r["verdict"] == "MISMATCH" and "exp_rc3(20!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F4", "双失败恢复调用 rc3 不符", False, v_f4)

    # Case G: missing gdb.log -> UNJUDGED_MISSING
    c_dir = os.path.join(scratch, "case_G")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        if os.path.isfile(gp):
            os.remove(gp)
    ok, v_g = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_g["M2-01-01-F3"]
        record_case("Case G", "私有状态缺失 (Missing gdb.log) -> UNJUDGED_MISSING",
                    r["verdict"] == "UNJUDGED" and r["verdict_detail"] == "UNJUDGED_MISSING",
                    f"verdict={r['verdict']}, detail={r['verdict_detail']}")
    else:
        record_case("Case G", "私有状态缺失", False, v_g)

    # Case H: missing pass1 dir -> SCHEMA_ERROR
    c_dir = os.path.join(scratch, "case_H")
    setup_base_case_dirs(c_dir, prereg_rows)
    pt_dir_p1 = os.path.join(c_dir, "pass1", "M2-01-01-F3")
    if os.path.isdir(pt_dir_p1):
        shutil.rmtree(pt_dir_p1)
    ok, v_h = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_h["M2-01-01-F3"]
        record_case("Case H", "缺失 pass 目录结构 -> SCHEMA_ERROR",
                    r["verdict"] == "SCHEMA_ERROR" and "MISSING_IN_PASS1" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case H", "缺失 pass 目录结构", False, v_h)

    # Case I: Tree mismatch -> SCHEMA_ERROR
    c_dir = os.path.join(scratch, "case_I")
    setup_base_case_dirs(c_dir, prereg_rows)
    f1_tsv = os.path.join(c_dir, "FACTS_pass1.tsv")
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", args.prereg,
                    "--run-dir", os.path.join(c_dir, "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    with open(f1_tsv, encoding="utf-8") as fh:
        f1_txt = fh.read()
    with open(f1_tsv, "w", encoding="utf-8") as fh:
        for l in f1_txt.splitlines():
            if l.startswith("M2-01-01-F3\t"):
                parts = l.split("\t")
                parts[2] = "TREE_CORRUPTED"
                fh.write("\t".join(parts) + "\n")
            else:
                fh.write(l + "\n")
    f2_tsv = os.path.join(c_dir, "FACTS_pass2.tsv")
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", args.prereg,
                    "--run-dir", os.path.join(c_dir, "pass2"), "--pass", "2", "--out", f2_tsv], check=True)
    s1_tsv = os.path.join(c_dir, "STATE_pass1.tsv")
    s2_tsv = os.path.join(c_dir, "STATE_pass2.tsv")
    s_sum = os.path.join(c_dir, "STATE_SUMMARY.txt")
    subprocess.run([sys.executable, "-I", "-B", STATE_JUDGE_PY, "--prereg", args.prereg, "--control", args.control_map,
                    "--ev", c_dir, "--facts1", f1_tsv, "--facts2", f2_tsv, "--state-dir", c_dir, "--dumps-dir", c_dir,
                    "--out-res", s1_tsv, "--out-sum", s_sum], check=True)
    shutil.copyfile(s1_tsv, s2_tsv)
    v_tsv = os.path.join(c_dir, "VERDICT.tsv")
    v_sum = os.path.join(c_dir, "VERDICT_SUMMARY.txt")
    subprocess.run([sys.executable, "-I", "-B", VERDICT_PY, "--prereg", args.prereg, "--facts1", f1_tsv, "--facts2", f2_tsv,
                    "--state1", s1_tsv, "--state2", s2_tsv, "--control-map", args.control_map,
                    "--out-verdict", v_tsv, "--out-summary", v_sum, "--assert-total", "150"], check=True)
    v_i = {}
    with open(v_tsv, encoding="utf-8") as fh:
        for r in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"):
            v_i[r["point_id"]] = r
    r = v_i["M2-01-01-F3"]
    record_case("Case I", "树哈希不符 -> SCHEMA_ERROR",
                r["verdict"] == "SCHEMA_ERROR" and "TREE_MISMATCH_PASS1" in r["mismatches"],
                f"verdict={r['verdict']}, mismatches={r['mismatches']}")

    # Case J: Output diff -> MISMATCH
    c_dir = os.path.join(scratch, "case_J")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "call2.txt"), "w") as fh:
            fh.write("CORRUPTED_OUTPUT_DATA\n")
    ok, v_j = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_j["M2-01-01-F3"]
        record_case("Case J", "恢复输出数据与对照组不符 -> MISMATCH",
                    r["verdict"] == "MISMATCH" and "I6_OUTPUT_DIFF" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case J", "恢复输出数据与对照组不符", False, v_j)

    # Case L: Flaky -> FLAKY
    c_dir = os.path.join(scratch, "case_L")
    setup_base_case_dirs(c_dir, prereg_rows)
    with open(os.path.join(c_dir, "pass2", "M2-01-01-F3", "stdout.txt"), "w") as fh:
        fh.write("R6CALLS 1 0\nRC first 0\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 1\n")
    with open(os.path.join(c_dir, "pass2", "M2-01-01-F3", "gdb.log"), "w") as fh:
        fh.write(make_clean_gdb_log("M2-01-01-F3", "M2-01", rc1=0, ec=0))
    with open(os.path.join(c_dir, "pass2", "M2-01-01-F3", "exitcode.txt"), "w") as fh:
        fh.write("0\n")
    ok, v_l = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_l["M2-01-01-F3"]
        record_case("Case L", "两遍运行不一致 -> FLAKY",
                    r["verdict"] == "FLAKY" and "rc1" in r["flaky_fields"],
                    f"verdict={r['verdict']}, detail={r['verdict_detail']}, flaky_fields={r['flaky_fields']}")
    else:
        record_case("Case L", "两遍运行不一致", False, v_l)

    # Case M: M2-10-01-B
    c_dir = os.path.join(scratch, "case_M")
    setup_base_case_dirs(c_dir, prereg_rows)
    ok, v_m = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_m["M2-10-01-B"]
        record_case("Case M", "M2-10-01-B 基线断点命中且 rc=20 -> MATCH",
                    r["verdict"] == "MATCH",
                    f"verdict={r['verdict']}, detail={r['verdict_detail']}")
    else:
        record_case("Case M", "M2-10-01-B 基线断点命中", False, v_m)

    # Case K: Sanitizer error -> MISMATCH
    c_dir = os.path.join(scratch, "case_K")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-03-G5-01-F3", "stderr.txt"), "w") as fh:
            fh.write("==1234==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x0\n")
    ok, v_k = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_k["M2-03-G5-01-F3"]
        record_case("Case K", "sanitizer 报错 (exp_san=0!=1) -> MISMATCH",
                    r["verdict"] == "MISMATCH" and "exp_san(1!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case K", "sanitizer 报错", False, v_k)

    # Case P: Reference point rc drift -> MISMATCH
    c_dir = os.path.join(scratch, "case_P")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-03-SANREF-G5-01-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 0\nRC first 0\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 1\n")
        with open(os.path.join(c_dir, pas, "M2-03-SANREF-G5-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("0\n")
    ok, v_p = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_p["M2-03-G5-01-F3"]
        record_case("Case P", "参照点行为漂移 (san_ref_rc1 20!=0) -> MISMATCH",
                    r["verdict"] == "MISMATCH" and "san_ref_rc1(20!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case P", "参照点行为漂移", False, v_p)

    # Case Q: NO_REF -> UNJUDGED_BY_DESIGN
    c_dir = os.path.join(scratch, "case_Q")
    setup_base_case_dirs(c_dir, prereg_rows)
    pr_q = os.path.join(c_dir, "prereg_no_ref.tsv")
    with open(args.prereg, encoding="utf-8") as fh:
        lines_q = fh.readlines()
    with open(pr_q, "w", encoding="utf-8") as fh:
        for l in lines_q:
            if l.startswith("M2-03-G5-01-F3\t"):
                parts = l.split("\t")
                parts[48] = "NO_REF"
                fh.write("\t".join(parts))
            else:
                fh.write(l)
    ok, v_q = run_pipeline(c_dir, pr_q, args.control_map)
    if ok:
        r = v_q["M2-03-G5-01-F3"]
        record_case("Case Q", "设计未决项 (NO_REF) -> UNJUDGED_BY_DESIGN",
                    r["verdict"] == "UNJUDGED" and r["verdict_detail"] == "UNJUDGED_BY_DESIGN",
                    f"verdict={r['verdict']}, detail={r['verdict_detail']}")
    else:
        record_case("Case Q", "设计未决项 (NO_REF)", False, v_q)

    # Case R: assert-total mismatch -> non-zero exit
    c_dir = os.path.join(scratch, "case_A")
    f1_tsv = os.path.join(c_dir, "FACTS_pass1.tsv")
    f2_tsv = os.path.join(c_dir, "FACTS_pass2.tsv")
    s1_tsv = os.path.join(c_dir, "STATE_pass1.tsv")
    s2_tsv = os.path.join(c_dir, "STATE_pass2.tsv")
    v_tsv = os.path.join(c_dir, "VERDICT_R.tsv")
    v_sum = os.path.join(c_dir, "VERDICT_SUMMARY_R.txt")
    r_bad = subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                            "--prereg", args.prereg,
                            "--facts1", f1_tsv,
                            "--facts2", f2_tsv,
                            "--state1", s1_tsv,
                            "--state2", s2_tsv,
                            "--control-map", args.control_map,
                            "--out-verdict", v_tsv,
                            "--out-summary", v_sum,
                            "--assert-total", "999"], capture_output=True, text=True)
    record_case("Case R", "汇总断言失败 (Total!=150) -> 异常退出",
                r_bad.returncode != 0 and "ASSERTION FAILED" in r_bad.stderr,
                f"exit_code={r_bad.returncode}, stderr={r_bad.stderr.strip()[:60]}")

    # Case S1: GDB exit 0, exited 024 -> rc=20
    c_dir = os.path.join(scratch, "case_S1")
    setup_base_case_dirs(c_dir, prereg_rows)
    f1_tsv = os.path.join(c_dir, "FACTS_pass1.tsv")
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", args.prereg,
                    "--run-dir", os.path.join(c_dir, "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    f1_rows = read_tsv_dict(f1_tsv)
    r10 = f1_rows["M2-10-01-B"]
    record_case("Case S1", "gdb 退出码 0，日志写 exited with code 024 -> rc=20, divergent=0",
                r10["rc"] == "20" and r10["signal"] == "0" and r10["gdb_divergent"] == "0",
                f"rc={r10['rc']}, signal={r10['signal']}, divergent={r10['gdb_divergent']}")

    # Case S2: nogdb exit 139 -> SIGSEGV -> CRASH -> MISMATCH
    c_dir = os.path.join(scratch, "case_S2")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("139\n")
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log"), "w") as fh:
            fh.write("Program terminated with signal SIGSEGV, Segmentation fault.\n")
    ok, v_s2 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_s2["M2-01-01-F3"]
        record_case("Case S2", "不挂 gdb 的运行出现 SIGSEGV -> CRASH -> MISMATCH",
                    r["verdict"] == "MISMATCH" and "exp_class(CRASH!=REPORTED_FAILURE)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case S2", "不挂 gdb 的运行出现 SIGSEGV", False, v_s2)

    # Case S3: GDB divergent -> GDB_DIVERGENT
    c_dir = os.path.join(scratch, "case_S3")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "stdout.txt"), "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 1\n")
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log"), "w") as fh:
            fh.write(make_clean_gdb_log("M2-01-01-F3", "M2-01", rc1=0, ec=0))
    ok, v_s3 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_s3["M2-01-01-F3"]
        record_case("Case S3", "gdb 与 nogdb 的 rc1 不同 -> GDB_DIVERGENT",
                    r["verdict"] == "GDB_DIVERGENT",
                    f"verdict={r['verdict']}, detail={r['verdict_detail']}, notes={r['notes']}")
    else:
        record_case("Case S3", "gdb 与 nogdb 的 rc1 不同", False, v_s3)

    # Case S4: Runner rejects unexpanded $
    c_dir = os.path.join(scratch, "case_S4")
    os.makedirs(c_dir, exist_ok=True)
    bad_prereg = os.path.join(c_dir, "bad_prereg.tsv")
    bad_row = dict(prereg_rows[0])
    bad_row["san_options"] = "ASAN_OPTIONS=log_path=$OTHER_VAR/bad.log"
    with open(bad_prereg, "w", encoding="utf-8") as fh:
        fh.write("\t".join(bad_row.keys()) + "\n")
        fh.write("\t".join(bad_row.values()) + "\n")
    r_plan = subprocess.run([sys.executable, "-I", "-B", RUNNER_PY,
                             "--prereg", bad_prereg,
                             "--ev", c_dir,
                             "--out-plan", os.path.join(c_dir, "plan.tsv"),
                             "--dry-run"],
                            capture_output=True, text=True)
    record_case("Case S4", "log_path 含 $ -> 运行器拒绝",
                r_plan.returncode != 0 and "contains unexpanded '$'" in r_plan.stderr,
                f"exit_code={r_plan.returncode}, stderr={r_plan.stderr.strip()[:60]}")

    # Case S5: NATIVE_FAIL_CONTROL in rc1=0 -> MISMATCH
    c_dir = os.path.join(scratch, "case_S5")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-07-CTRL-vl-ng1-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 0\nRC first 0\nR6CALLS 2 20\nRC retry 20\nS4FMM HITCOUNT 0\n")
    ok, v_s5 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_s5["M2-07-CTRL-vl-ng1-F3"]
        record_case("Case S5", "NATIVE_FAIL_CONTROL 在 rc1=0 时 -> MISMATCH",
                    r["verdict"] == "MISMATCH" and "native_fail_rc1(0!=20)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case S5", "NATIVE_FAIL_CONTROL 在 rc1=0 时", False, v_s5)

    # Case S6: M2-10 missing M210_HIT -> MISMATCH
    c_dir = os.path.join(scratch, "case_S6")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        gp = os.path.join(c_dir, pas, "M2-10-01-B", "gdb.log")
        with open(gp, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\n[Inferior 1 (process 123) exited with code 024]\n")
    ok, v_s6 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_s6["M2-10-01-B"]
        record_case("Case S6", "M2-10 没有 M210_HIT -> MISMATCH",
                    r["verdict"] == "MISMATCH" and "baseline_m210_hits_none" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case S6", "M2-10 没有 M210_HIT", False, v_s6)

    # Case S7: hit1 mismatch -> MISMATCH
    c_dir = os.path.join(scratch, "case_S7")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        out_p = os.path.join(c_dir, pas, "M2-04-01-F3", "stdout.txt")
        with open(out_p, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 20\nRC retry 20\nR6CALLS 3 0\nS4FMM HITCOUNT 3\nS4FMM HIT dual target2 real S4_malloc failure: FMM call 16 B (stream index 2, hit2=1 total=3)\n")
        gp = os.path.join(c_dir, pas, "M2-04-01-F3", "gdb.log")
        with open(gp, "w") as fh:
            fh.write(make_clean_gdb_log("M2-04-01-F3", "M2-04").replace("hit2=1 total=2", "hit2=1 total=3").replace("S4FMM HITCOUNT 2", "S4FMM HITCOUNT 3"))
    ok, v_s7 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_s7["M2-04-01-F3"]
        record_case("Case S7", "hit1 不符 (hit1=2!=1) -> MISMATCH",
                    r["verdict"] == "MISMATCH" and "exp_hit1(2!=1)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case S7", "hit1 不符", False, v_s7)

    # Case S8: Reference point rc differs -> MISMATCH
    c_dir = os.path.join(scratch, "case_S8")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        ref_p = os.path.join(c_dir, pas, "M2-01-01-F3", "stdout.txt")
        with open(ref_p, "w") as fh:
            fh.write("R6CALLS 1 0\nRC first 0\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 1\n")
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("0\n")
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log"), "w") as fh:
            fh.write(make_clean_gdb_log("M2-01-01-F3", "M2-01", rc1=0, ec=0))
    ok, v_s8 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_s8["M2-03-REP-INIT-01-F3"]
        record_case("Case S8", "参照点 rc 不同 -> MISMATCH",
                    r["verdict"] == "MISMATCH" and "san_ref_rc1(20!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case S8", "参照点 rc 不同", False, v_s8)

    # Case P1: exp HOLD, observed N/A -> MISMATCH (U267)
    c_dir = os.path.join(scratch, "case_P1")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        with open(gp, "r") as fh:
            log_c = fh.read()
        log_mod = "\n".join([l for l in log_c.splitlines() if not l.startswith("R6BCLM")])
        with open(gp, "w") as fh:
            fh.write(log_mod + "\n")
    ok, v_p1 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_p1["M2-01-01-F3"]
        passed = (r["verdict"] == "MISMATCH" and any("I1(N/A!=HOLD)" in m or "I2(N/A!=HOLD)" in m for m in r["mismatches"].split(",")))
        record_case("Case P1", "exp HOLD 实测 N/A -> MISMATCH (U267)", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case P1", "exp HOLD 实测 N/A", False, v_p1)

    # Case P2: exp N/A, observed HOLD -> MISMATCH (U267)
    c_dir = os.path.join(scratch, "case_P2")
    setup_base_case_dirs(c_dir, prereg_rows)
    pr_p2 = os.path.join(scratch, "PREREG_CASE_P2.tsv")
    with open(args.prereg, encoding="utf-8") as fh:
        p2_lines = fh.readlines()
    with open(pr_p2, "w", encoding="utf-8") as fh:
        for l in p2_lines:
            if l.startswith("M2-01-01-F3\t"):
                parts = l.split("\t")
                parts[29] = "N/A"
                fh.write("\t".join(parts))
            else:
                fh.write(l)
    ok, v_p2 = run_pipeline(c_dir, pr_p2, args.control_map)
    if ok:
        r = v_p2["M2-01-01-F3"]
        passed = (r["verdict"] == "MISMATCH" and "I1(HOLD!=N/A)" in r["mismatches"])
        record_case("Case P2", "exp N/A 实测 HOLD -> MISMATCH (U267)", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case P2", "exp N/A 实测 HOLD", False, v_p2)

    # Case P3: ASAN SEGV log -> san_crash=1, SAN_CRASH (U269)
    c_dir = os.path.join(scratch, "case_P3")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-03-G5-01-F3", "stderr.txt"), "w") as fh:
            fh.write("AddressSanitizer:DEADLYSIGNAL\nERROR: AddressSanitizer: SEGV on unknown address 0x0\nABORTING\n")
    pr_p3 = os.path.join(scratch, "PREREG_CASE_P3.tsv")
    with open(args.prereg, encoding="utf-8") as fh:
        p3_lines = fh.readlines()
    with open(pr_p3, "w", encoding="utf-8") as fh:
        for l in p3_lines:
            if l.startswith("M2-03-G5-01-F3\t"):
                parts = l.split("\t")
                parts[28] = "SAN_CRASH"
                fh.write("\t".join(parts))
            else:
                fh.write(l)
    ok, v_p3 = run_pipeline(c_dir, pr_p3, args.control_map)
    if ok:
        r = v_p3["M2-03-G5-01-F3"]
        passed = (r["verdict"] == "MATCH")
        record_case("Case P3", "ASAN SEGV 日志 -> san_crash=1, exp=SAN_CRASH 判定 MATCH (U269)", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case P3", "ASAN SEGV 日志", False, v_p3)

    # Case P4: Injected row hit=0 -> smoke gate FAIL (U270a)
    c_dir = os.path.join(scratch, "case_P4")
    setup_base_case_dirs(c_dir, prereg_rows)
    f1_tsv = os.path.join(c_dir, "FACTS_pass1.tsv")
    f2_tsv = os.path.join(c_dir, "FACTS_pass2.tsv")
    for pas, ft in [("pass1", f1_tsv), ("pass2", f2_tsv)]:
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "stdout.txt"), "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 0\n")
        subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", args.prereg,
                        "--run-dir", os.path.join(c_dir, pas), "--pass", "1" if pas == "pass1" else "2", "--out", ft], check=True)
    tr_path = os.path.join(c_dir, "TRIAGE_DUMMY.tsv")
    with open(tr_path, "w") as fh:
        fh.write("point_id\tr8m2b_verdict\tcategory\tevidence\taction\n")
    plan_p4 = os.path.join(c_dir, "COMMAND_PLAN_SMOKE.tsv")
    subprocess.run([sys.executable, "-I", "-B", RUNNER_PY, "--prereg", args.prereg,
                    "--ev", c_dir, "--out-plan", plan_p4, "--dry-run"], check=True)
    res_p4 = subprocess.run([sys.executable, "-I", "-B", SMOKE_GATE_PY,
                             "--prereg", args.prereg,
                             "--smoke-dir", c_dir,
                             "--triage", tr_path],
                            capture_output=True, text=True)
    passed = (res_p4.returncode != 0 and "Gate 6 (U270a: exp_hit>=1 observed hit>=1): FAIL" in res_p4.stdout)
    record_case("Case P4", "注入行 hit=0 -> 冒烟门禁 FAIL (U270a)", passed, f"rc={res_p4.returncode}")

    # Case P5: INIT_CLEAN assertion violated -> MISMATCH (U268)
    c_dir = os.path.join(scratch, "case_P5")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        with open(gp, "r") as fh:
            log_c = fh.read()
        log_mod = log_c.replace("R6BSTATE 1 layer 0 modes_null 0", "R6BSTATE 1 layer 0 modes_null 0")
        with open(gp, "w") as fh:
            fh.write(log_mod)
    pr_p5 = os.path.join(scratch, "PREREG_CASE_P5.tsv")
    with open(args.prereg, encoding="utf-8") as fh:
        r_pr = list(csv.DictReader(fh, delimiter="\t"))
    fieldnames_p5 = list(r_pr[0].keys()) + ["exp_init_clean"]
    with open(pr_p5, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames_p5) + "\n")
        for row in r_pr:
            row["exp_init_clean"] = "HOLD" if row["point_id"] == "M2-01-01-F3" else "-"
            fh.write("\t".join([row.get(h, "-") for h in fieldnames_p5]) + "\n")
    ok, v_p5 = run_pipeline(c_dir, pr_p5, args.control_map)
    if ok:
        r = v_p5["M2-01-01-F3"]
        passed = (r["verdict"] == "MISMATCH" and "init_clean(VIOLATED!=HOLD)" in r["mismatches"])
        record_case("Case P5", "INIT_CLEAN 断言失败 (VIOLATED!=HOLD) -> MISMATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case P5", "INIT_CLEAN 断言失败", False, v_p5)

    # Case P6: SUPERSEDED_BY row not double counted
    c_dir = os.path.join(scratch, "case_P6")
    setup_base_case_dirs(c_dir, prereg_rows)
    pr_p6 = os.path.join(scratch, "PREREG_CASE_P6.tsv")
    with open(args.prereg, encoding="utf-8") as fh:
        r_pr = list(csv.DictReader(fh, delimiter="\t"))
    fieldnames_p6 = list(r_pr[0].keys()) + ["SUPERSEDED_BY"]
    with open(pr_p6, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames_p6) + "\n")
        for row in r_pr:
            row["SUPERSEDED_BY"] = "M2-01-01-F3-C" if row["point_id"] == "M2-01-01-F3" else "-"
            fh.write("\t".join([row.get(h, "-") for h in fieldnames_p6]) + "\n")
    ok, v_p6 = run_pipeline(c_dir, pr_p6, args.control_map)
    if ok:
        sum_p6 = os.path.join(c_dir, "VERDICT_SUMMARY.txt")
        with open(sum_p6) as fh:
            sum_txt = fh.read()
        passed = ("superseded_points: 1" in sum_txt and "effective_points: 149" in sum_txt)
        record_case("Case P6", "SUPERSEDED_BY 行不重复计数 (superseded=1, effective=149)", passed, f"summary={sum_txt.splitlines()[:5]}")
    else:
        record_case("Case P6", "SUPERSEDED_BY 行不重复计数", False, v_p6)

    # Case P7: NATIVE_FAIL_CONTROL used for vl-ng2 -> MATCH (U263)
    c_dir = os.path.join(scratch, "case_P7")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-07-CTRL-vl-ng2-F3", "stdout.txt"), "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 20\nRC retry 20\nS4FMM HITCOUNT 0\n")
        with open(os.path.join(c_dir, pas, "M2-07-CTRL-vl-ng2-F3", "exitcode.txt"), "w") as fh:
            fh.write("20\n")
    pr_p7 = os.path.join(scratch, "PREREG_CASE_P7.tsv")
    with open(args.prereg, encoding="utf-8") as fh:
        p7_lines = fh.readlines()
    with open(pr_p7, "w", encoding="utf-8") as fh:
        for l in p7_lines:
            if l.startswith("M2-07-CTRL-vl-ng2-F3\t"):
                parts = l.split("\t")
                parts[38] = "NATIVE_FAIL_CONTROL" # class_rule
                parts[23] = "20" # exp_rc1
                parts[24] = "20" # exp_rc2
                fh.write("\t".join(parts))
            else:
                fh.write(l)
    ok, v_p7 = run_pipeline(c_dir, pr_p7, args.control_map)
    if ok:
        r = v_p7["M2-07-CTRL-vl-ng2-F3"]
        passed = (r["verdict"] == "MATCH")
        record_case("Case P7", "NATIVE_FAIL_CONTROL 用于 vl-ng2 实测 20 -> MATCH (U263)", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case P7", "NATIVE_FAIL_CONTROL 用于 vl-ng2", False, v_p7)

    # ==================== NEW R8M2D CASES (D1 - D7) ====================

    # Case D1: crash_call mismatch -> MISMATCH
    c_dir = os.path.join(scratch, "case_D1")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log"), "w") as fh:
            fh.write(
                "Program received signal SIGSEGV, Segmentation fault.\n"
                "#0 0x0 in Simulation_ComputeLayerSolution () at S4/S4.cpp:1995\n"
                "#1 0x0 in main () at testing/d003/stage_s4/driver_r6b_state.cpp:211\n"
            )
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("139\n")
    pr_d1 = os.path.join(scratch, "PREREG_CASE_D1.tsv")
    with open(args.prereg, encoding="utf-8") as fh:
        r_pr = list(csv.DictReader(fh, delimiter="\t"))
    fieldnames_d = list(r_pr[0].keys()) + ["exp_crash_call", "exp_crash_site", "exp_post_call1_solution"]
    with open(pr_d1, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames_d) + "\n")
        for row in r_pr:
            if row["point_id"] == "M2-01-01-F3":
                row["exp_crash_call"] = "2"
                row["exp_class"] = "CRASH"
                row["exp_signal"] = "11"
                row["exp_rc1"] = "-"
                row["exp_rc2"] = "-"
                row["exp_rc3"] = "-"
            fh.write("\t".join([row.get(h, "-") for h in fieldnames_d]) + "\n")
    ok, v_d1 = run_pipeline(c_dir, pr_d1, args.control_map)
    if ok:
        r = v_d1["M2-01-01-F3"]
        passed = (r["verdict"] == "MISMATCH" and "exp_crash_call(1!=2)" in r["mismatches"])
        record_case("Case D1", "crash_call 不符 (实测1 != 预期2) -> MISMATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case D1", "crash_call 不符", False, v_d1)

    # Case D2: crash_site mismatch -> MISMATCH
    c_dir = os.path.join(scratch, "case_D2")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log"), "w") as fh:
            fh.write(
                "Program received signal SIGSEGV, Segmentation fault.\n"
                "#0 0x0 in Simulation_ComputeLayerSolution () at S4/S4.cpp:2021\n"
                "#1 0x0 in main () at testing/d003/stage_s4/driver_r6b_state.cpp:227\n"
            )
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("139\n")
    pr_d2 = os.path.join(scratch, "PREREG_CASE_D2.tsv")
    with open(pr_d1, encoding="utf-8") as fh:
        r_pr = list(csv.DictReader(fh, delimiter="\t"))
    with open(pr_d2, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames_d) + "\n")
        for row in r_pr:
            if row["point_id"] == "M2-01-01-F3":
                row["exp_crash_call"] = "2"
                row["exp_crash_site"] = "S4.cpp:1995"
            fh.write("\t".join([row.get(h, "-") for h in fieldnames_d]) + "\n")
    ok, v_d2 = run_pipeline(c_dir, pr_d2, args.control_map)
    if ok:
        r = v_d2["M2-01-01-F3"]
        passed = (r["verdict"] == "MISMATCH" and "exp_crash_site(S4.cpp:2021!=S4.cpp:1995)" in r["mismatches"])
        record_case("Case D2", "crash_site 不符 (实测2021 != 预期1995) -> MISMATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case D2", "crash_site 不符", False, v_d2)

    # Case D3: exp_rc1="-" with rc1=MISSING -> does not judge (MATCH)
    c_dir = os.path.join(scratch, "case_D3")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "stdout.txt"), "w") as fh:
            fh.write("S4FMM HITCOUNT 1\n") # missing R6CALLS
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log"), "w") as fh:
            fh.write(
                "Program received signal SIGSEGV, Segmentation fault.\n"
                "R6BSTATE 1 solution solved 0=0 1=0 2=0\n"
                "#0 0x0 in Simulation_ComputeLayerSolution () at S4/S4.cpp:2021\n"
                "#1 0x0 in main () at testing/d003/stage_s4/driver_r6b_state.cpp:227\n"
            )
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("139\n")
    pr_d3 = os.path.join(scratch, "PREREG_CASE_D3.tsv")
    with open(pr_d1, encoding="utf-8") as fh:
        r_pr = list(csv.DictReader(fh, delimiter="\t"))
    with open(pr_d3, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames_d) + "\n")
        for row in r_pr:
            if row["point_id"] == "M2-01-01-F3":
                row["exp_rc1"] = "-"
                row["exp_rc2"] = "-"
                row["exp_rc3"] = "-"
                row["exp_signal"] = "11"
                row["exp_hit"] = "1"
                row["exp_class"] = "CRASH"
                row["exp_crash_call"] = "2"
                row["exp_crash_site"] = "S4.cpp:2021"
                row["exp_post_call1_solution"] = "NONNULL"
                row["state_analyzer"] = "-"
            fh.write("\t".join([row.get(h, "-") for h in fieldnames_d]) + "\n")
    ok, v_d3 = run_pipeline(c_dir, pr_d3, args.control_map)
    if ok:
        r = v_d3["M2-01-01-F3"]
        passed = (r["verdict"] == "MATCH")
        record_case("Case D3", "exp_rc1='-' 时 rc1=MISSING 不判 -> MATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case D3", "exp_rc1='-' 不判", False, v_d3)

    # Case D4: post_call1_solution mismatch -> MISMATCH
    c_dir = os.path.join(scratch, "case_D4")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        with open(gp, "r") as fh:
            txt = fh.read()
        txt_mod = txt.replace("R6BSTATE 1 solution solved 0=0 1=0 2=0", "R6BSTATE 1 solution null")
        with open(gp, "w") as fh:
            fh.write(txt_mod)
    pr_d4 = os.path.join(scratch, "PREREG_CASE_D4.tsv")
    with open(pr_d1, encoding="utf-8") as fh:
        r_pr = list(csv.DictReader(fh, delimiter="\t"))
    with open(pr_d4, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames_d) + "\n")
        for row in r_pr:
            if row["point_id"] == "M2-01-01-F3":
                row["exp_post_call1_solution"] = "NONNULL"
            fh.write("\t".join([row.get(h, "-") for h in fieldnames_d]) + "\n")
    ok, v_d4 = run_pipeline(c_dir, pr_d4, args.control_map)
    if ok:
        r = v_d4["M2-01-01-F3"]
        passed = (r["verdict"] == "MISMATCH" and "exp_post_call1_solution(NULL!=NONNULL)" in r["mismatches"])
        record_case("Case D4", "post_call1_solution 不符 (实测NULL != 预期NONNULL) -> MISMATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case D4", "post_call1_solution 不符", False, v_d4)

    # Case D5: Libc frame skipped and first S4 frame extracted (facts test)
    c_dir = os.path.join(scratch, "case_D5")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log"), "w") as fh:
            fh.write(
                "Program received signal SIGSEGV, Segmentation fault.\n"
                "#0  0x00007ffff7a87000 in __memset_avx2_unaligned_erms () from /lib/x86_64-linux-gnu/libc.so.6\n"
                "#1  0x000055555555daee in Simulation_ComputeLayerSolution (S=0x1) at S4/S4.cpp:1995\n"
                "#2  0x0000555555560c30 in Simulation_GetLayerSolution () at S4/S4.cpp:1815\n"
                "#3  0x0000555555569cb3 in main () at testing/d003/stage_s4/driver_r6b_state.cpp:227\n"
            )
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("139\n")
    f1_tsv = os.path.join(c_dir, "FACTS_pass1.tsv")
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", args.prereg, "--run-dir", os.path.join(c_dir, "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    facts_d5 = read_tsv_dict(f1_tsv)
    r_d5 = facts_d5["M2-01-01-F3"]
    passed = (r_d5["crash_site"] == "S4.cpp:1995" and r_d5["crash_call"] == "2")
    record_case("Case D5", "libc 帧被跳过，提取第一个 S4/ 帧 (S4.cpp:1995) 且 crash_call=2", passed, f"site={r_d5['crash_site']}, call={r_d5['crash_call']}")

    # Case D6: SUPERSEDED statistics correct
    c_dir = os.path.join(scratch, "case_D6")
    setup_base_case_dirs(c_dir, prereg_rows)
    pr_d6 = os.path.join(scratch, "PREREG_CASE_D6.tsv")
    with open(args.prereg, encoding="utf-8") as fh:
        r_pr = list(csv.DictReader(fh, delimiter="\t"))
    fieldnames_d6 = list(r_pr[0].keys()) + ["SUPERSEDED_BY"]
    with open(pr_d6, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames_d6) + "\n")
        for i, row in enumerate(r_pr[:2]):
            row["SUPERSEDED_BY"] = "NEW_ROW" if i == 1 else "-"
            fh.write("\t".join([row.get(h, "-") for h in fieldnames_d6]) + "\n")
    ok, v_d6 = run_pipeline(c_dir, pr_d6, args.control_map, assert_total=2)
    if ok:
        sum_d6 = os.path.join(c_dir, "VERDICT_SUMMARY.txt")
        with open(sum_d6) as fh:
            sum_txt = fh.read()
        passed = ("total_points: 2" in sum_txt and "superseded_points: 1" in sum_txt and "effective_points: 1" in sum_txt)
        record_case("Case D6", "SUPERSEDED 统计正确 (total=2, superseded=1, effective=1)", passed, f"summary={sum_txt.splitlines()[:5]}")
    else:
        record_case("Case D6", "SUPERSEDED 统计", False, v_d6)

    # Case D7: exp_crash_site normalized comparison with （[源码] 推断）
    c_dir = os.path.join(scratch, "case_D7")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "stdout.txt"), "w") as fh:
            fh.write("S4FMM HITCOUNT 1\n")
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log"), "w") as fh:
            fh.write(
                "Program received signal SIGSEGV, Segmentation fault.\n"
                "R6BSTATE 1 solution solved 0=0 1=0 2=0\n"
                "#0 0x0 in Simulation_ComputeLayerSolution () at S4/S4.cpp:1995\n"
                "#1 0x0 in main () at testing/d003/stage_s4/driver_r6b_state.cpp:227\n"
            )
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("139\n")
    pr_d7 = os.path.join(scratch, "PREREG_CASE_D7.tsv")
    with open(pr_d1, encoding="utf-8") as fh:
        r_pr = list(csv.DictReader(fh, delimiter="\t"))
    with open(pr_d7, "w", encoding="utf-8") as fh:
        fh.write("\t".join(fieldnames_d) + "\n")
        for row in r_pr:
            if row["point_id"] == "M2-01-01-F3":
                row["exp_rc1"] = "-"
                row["exp_rc2"] = "-"
                row["exp_rc3"] = "-"
                row["exp_signal"] = "11"
                row["exp_hit"] = "1"
                row["exp_class"] = "CRASH"
                row["exp_crash_call"] = "2"
                row["exp_crash_site"] = "S4.cpp:1995（[源码] 推断）"
                row["exp_post_call1_solution"] = "NONNULL"
                row["state_analyzer"] = "-"
            fh.write("\t".join([row.get(h, "-") for h in fieldnames_d]) + "\n")
    ok, v_d7 = run_pipeline(c_dir, pr_d7, args.control_map)
    if ok:
        r = v_d7["M2-01-01-F3"]
        passed = (r["verdict"] == "MATCH")
        record_case("Case D7", "exp_crash_site 带[源码]推断归一化比对 -> MATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case D7", "exp_crash_site 归一化比对", False, v_d7)


    # ==================== NEW R8M2E CASES (E1 - E6) ====================

    # Case E1: ASAN interceptor frame (__interceptor_memset, __asan_memset) skipped and S4/ frame extracted (facts test)
    c_dir = os.path.join(scratch, "case_E1")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log"), "w") as fh:
            fh.write(
                "==999==ERROR: AddressSanitizer: SEGV on unknown address 0x0 (pc 0x7f)\n"
                "#0 0x7f00 in __interceptor_memset from /lib/x86_64-linux-gnu/libasan.so.8\n"
                "#1 0x5555 in Simulation_ComputeLayerSolution (S=0x1) at S4/S4.cpp:1995\n"
                "#2 0x5555 in Simulation_GetLayerSolution () at S4/S4.cpp:1815\n"
                "#3 0x5555 in main () at testing/d003/stage_s4/driver_r6b_state.cpp:227\n"
            )
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("139\n")
    f1_tsv = os.path.join(c_dir, "FACTS_pass1.tsv")
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", args.prereg, "--run-dir", os.path.join(c_dir, "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    facts_e1 = read_tsv_dict(f1_tsv)
    r_e1 = facts_e1["M2-01-01-F3"]
    passed = (r_e1["crash_site"] == "S4.cpp:1995" and r_e1["crash_call"] == "2")
    record_case("Case E1", "ASAN 拦截帧 (__interceptor_memset) 被跳过，提取首个 S4 帧 (S4.cpp:1995)", passed, f"site={r_e1['crash_site']}, call={r_e1['crash_call']}")

    # Case E2: aligned:K request parsing verification (U277)
    drv_al = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r5", "build", "init-F4-san-AL")
    env_e2 = os.environ.copy()
    env_e2["FMM_MODE"] = "closed2d"
    env_e2["S4FMM_NG"] = "1"
    env_e2["S4FMM_INJECT"] = "aligned:3"
    env_e2["ASAN_OPTIONS"] = "detect_leaks=0:abort_on_error=0"
    env_e2["UBSAN_OPTIONS"] = "abort_on_error=0"
    p_e2 = subprocess.run([drv_al, "pattern", "both", "4", "3"], cwd=REPO, env=env_e2, capture_output=True, text=True)
    e2_hit = ("S4FMM HIT real malloc failure: malloc_aligned 3" in p_e2.stderr) or ("S4FMM HITCOUNT 1" in p_e2.stdout)
    record_case("Case E2", "S4FMM_INJECT=aligned:3 请求被解析并触发 K=3 注入与 HIT 报告", e2_hit, f"rc={p_e2.returncode}, hit={e2_hit}")

    # Case E3: S4FMM HITCOUNT parsing in facts extractor
    sys.path.insert(0, os.path.dirname(FACTS_PY))
    import facts_m2_r9 as facts_mod
    sample_text = "R6CALLS 1 0\nRC first 0\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 1\n"
    rc1, rc2, rc3, hit = facts_mod.parse_output_rcs_and_hits(sample_text, is_ctrl=False, env_str="S4FMM_INJECT=aligned:3", item="SOLN-1764")
    passed_e3 = (hit == "1" and rc1 == "0" and rc2 == "0")
    record_case("Case E3", "facts 提取器正确解析 stdout 中的 S4FMM HITCOUNT 1 为 hit=1", passed_e3, f"hit={hit}, rc1={rc1}, rc2={rc2}")

    # Case E4: verdict_source 列在合并总表生成器中支持并写入
    c_dir_e4 = os.path.join(scratch, "case_E4")
    os.makedirs(c_dir_e4, exist_ok=True)
    mock_formal_tsv = os.path.join(c_dir_e4, "MOCK_VERDICT_FORMAL.tsv")
    pr_formal = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2e", "PREREG_EFFECTIVE_FORMAL_R8_M2e.tsv")
    with open(pr_formal, encoding="utf-8") as fh:
        pr_rows = list(csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"))
    with open(mock_formal_tsv, "w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t")
        writer.writerow(["point_id", "item", "verdict", "verdict_detail", "mismatches", "flaky_fields", "unjudged_missing", "unjudged_by_design", "superseded_by", "notes"])
        for r in pr_rows:
            writer.writerow([r["point_id"], r["item"], "MATCH", "MATCH", "-", "-", "-", "-", "-", "mock formal"])
    mock_cons = os.path.join(c_dir_e4, "MOCK_CONSOLIDATED.tsv")
    mock_status = os.path.join(c_dir_e4, "MOCK_STATUS.tsv")
    mock_ledger = os.path.join(c_dir_e4, "MOCK_LEDGER.tsv")
    res_e4 = subprocess.run([
        sys.executable, "-I", "-B", SUMMARY_PY,
        "--verdict-formal", mock_formal_tsv,
        "--prereg-formal", pr_formal,
        "--out-consolidated", mock_cons,
        "--out-f3-status", mock_status,
        "--out-ledger", mock_ledger,
        "--ev", c_dir_e4
    ], capture_output=True, text=True)
    cons_e4_rows = read_tsv_dict(mock_cons)
    first_row = next(iter(cons_e4_rows.values()))
    has_vs_col = "verdict_source" in first_row
    record_case("Case E4", "合并总表生成器产出 verdict_source 列 (U280)", has_vs_col and res_e4.returncode == 0, f"rc={res_e4.returncode}, has_col={has_vs_col}")

    # Case E5: 有效行不允许 smoke_* 来源断言生效 (U280)
    active_smoke = [r["point_id"] for r in cons_e4_rows.values() if r["consolidation_status"] == "ACTIVE" and r["verdict_source"].startswith("smoke_")]
    passed_e5 = (len(active_smoke) == 0 and sum(1 for r in cons_e4_rows.values() if r["consolidation_status"] == "SUPERSEDED" and r["verdict_source"] == "smoke_r8m2d") == 3)
    record_case("Case E5", "合并总表有效行中无 smoke_* 来源，仅 3 个 SUPERSEDED -FA 行保留 smoke_r8m2d", passed_e5, f"active_smoke_count={len(active_smoke)}")

    # Case E6: 合并总表合计断言 (总行数 259, SUPERSEDED 57, 有效行 202, 类别之和 202)
    total_e6 = len(cons_e4_rows)
    sup_e6 = sum(1 for r in cons_e4_rows.values() if r["consolidation_status"] == "SUPERSEDED")
    act_e6 = sum(1 for r in cons_e4_rows.values() if r["consolidation_status"] == "ACTIVE")
    passed_e6 = (total_e6 == 259 and sup_e6 == 57 and act_e6 == 202)
    record_case("Case E6", "合并总表合计断言满足 (总行数 259, SUPERSEDED 57, 有效行 202)", passed_e6, f"total={total_e6}, sup={sup_e6}, act={act_e6}")

            # =========================================================================
    # R9 New Synthetic Positive Control Cases (Section 4 S-J)
    # Testing: post_call1_solution=NULL, crash_call=NONE, I6 HOLD/VIOLATED
    # =========================================================================

    def make_prereg_file(out_p, mod_fn):
        with open(args.prereg, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh, delimiter="\t"))
        fnames = list(rows[0].keys())
        for f in ["exp_crash_call", "exp_crash_site", "exp_post_call1_solution"]:
            if f not in fnames:
                fnames.append(f)
        with open(out_p, "w", encoding="utf-8", newline="") as fh:
            fh.write("\t".join(fnames) + "\n")
            for r in rows:
                if r["point_id"] == "M2-01-01-F3":
                    mod_fn(r)
                fh.write("\t".join([r.get(h, "-") for h in fnames]) + "\n")

    # Case R9_1: post_call1_solution=NULL matches expectation -> MATCH
    c_dir_r9_1 = os.path.join(scratch, "case_R9_1")
    setup_base_case_dirs(c_dir_r9_1, prereg_rows)
    pr_r9_1 = os.path.join(scratch, "PREREG_CASE_R9_1.tsv")
    make_prereg_file(pr_r9_1, lambda r: r.update({"exp_post_call1_solution": "NULL", "exp_crash_call": "NONE", "exp_I1": "-", "exp_I2": "-", "exp_I4": "-", "exp_I5": "-"}))
    for pas in ("pass1", "pass2"):
        p_path = os.path.join(c_dir_r9_1, pas, "M2-01-01-F3", "gdb.log")
        txt = open(p_path, encoding="utf-8").read()
        txt = re.sub(r"R6BSTATE\s+1\s+solution\s+\S+", "R6BSTATE 1 solution null", txt)
        with open(p_path, "w", encoding="utf-8") as fh:
            fh.write(txt)
    ok, v_r9_1 = run_pipeline(c_dir_r9_1, pr_r9_1, args.control_map)
    if ok:
        r = v_r9_1["M2-01-01-F3"]
        passed = (r["verdict"] == "MATCH" and r["mismatches"] == "-")
        record_case("Case R9_1", "post_call1_solution=NULL 匹配预期 -> MATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case R9_1", "post_call1_solution=NULL", False, "pipeline failed")

    # Case R9_2: post_call1_solution=NONNULL 不符预期 NULL -> MISMATCH
    c_dir_r9_2 = os.path.join(scratch, "case_R9_2")
    setup_base_case_dirs(c_dir_r9_2, prereg_rows)
    pr_r9_2 = os.path.join(scratch, "PREREG_CASE_R9_2.tsv")
    make_prereg_file(pr_r9_2, lambda r: r.update({"exp_post_call1_solution": "NULL"}))
    for pas in ("pass1", "pass2"):
        p_path = os.path.join(c_dir_r9_2, pas, "M2-01-01-F3", "gdb.log")
        with open(p_path, "a", encoding="utf-8") as fh:
            fh.write("\nR6BSTATE 1 solution solved 0=1\n")
    ok, v_r9_2 = run_pipeline(c_dir_r9_2, pr_r9_2, args.control_map)
    if ok:
        r = v_r9_2["M2-01-01-F3"]
        passed = (r["verdict"] == "MISMATCH" and "exp_post_call1_solution(NONNULL!=NULL)" in r["mismatches"])
        record_case("Case R9_2", "post_call1_solution 不符 (实测NONNULL != 预期NULL) -> MISMATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case R9_2", "post_call1_solution 不符", False, "pipeline failed")

    # Case R9_3: crash_call=NONE 匹配预期 -> MATCH
    c_dir_r9_3 = os.path.join(scratch, "case_R9_3")
    setup_base_case_dirs(c_dir_r9_3, prereg_rows)
    pr_r9_3 = os.path.join(scratch, "PREREG_CASE_R9_3.tsv")
    make_prereg_file(pr_r9_3, lambda r: r.update({"exp_crash_call": "NONE"}))
    ok, v_r9_3 = run_pipeline(c_dir_r9_3, pr_r9_3, args.control_map)
    if ok:
        r = v_r9_3["M2-01-01-F3"]
        passed = (r["verdict"] == "MATCH" and r["mismatches"] == "-")
        record_case("Case R9_3", "crash_call=NONE 匹配预期 -> MATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case R9_3", "crash_call=NONE", False, "pipeline failed")

    # Case R9_4: crash_call=1 不符预期 NONE -> MISMATCH
    c_dir_r9_4 = os.path.join(scratch, "case_R9_4")
    setup_base_case_dirs(c_dir_r9_4, prereg_rows)
    pr_r9_4 = os.path.join(scratch, "PREREG_CASE_R9_4.tsv")
    make_prereg_file(pr_r9_4, lambda r: r.update({"exp_crash_call": "NONE", "exp_class": "REPORTED_FAILURE"}))
    for pas in ("pass1", "pass2"):
        p_path = os.path.join(c_dir_r9_4, pas, "M2-01-01-F3")
        with open(os.path.join(p_path, "exitcode.txt"), "w") as fh:
            fh.write("139\n")
        with open(os.path.join(p_path, "gdb.log"), "w") as fh:
            fh.write("Program received signal SIGSEGV, Segmentation fault.\n#0 0x0 in Simulation_ComputeLayerSolution () at S4/S4.cpp:1995\n#1 0x0 in main () at testing/d003/stage_s4/driver_r6b_state.cpp:211\n")
    ok, v_r9_4 = run_pipeline(c_dir_r9_4, pr_r9_4, args.control_map)
    if ok:
        r = v_r9_4["M2-01-01-F3"]
        passed = (r["verdict"] == "MISMATCH" and "exp_crash_call(1!=NONE)" in r["mismatches"])
        record_case("Case R9_4", "crash_call 不符 (实测1 != 预期NONE) -> MISMATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case R9_4", "crash_call 不符", False, "pipeline failed")

    # Case R9_5: I6=HOLD 匹配预期 -> MATCH
    c_dir_r9_5 = os.path.join(scratch, "case_R9_5")
    setup_base_case_dirs(c_dir_r9_5, prereg_rows)
    pr_r9_5 = os.path.join(scratch, "PREREG_CASE_R9_5.tsv")
    make_prereg_file(pr_r9_5, lambda r: r.update({"exp_I6": "HOLD", "state_analyzer": "STATE_JUDGE"}))
    ok, v_r9_5 = run_pipeline(c_dir_r9_5, pr_r9_5, args.control_map)
    if ok:
        r = v_r9_5["M2-01-01-F3"]
        passed = (r["verdict"] == "MATCH" and r["mismatches"] == "-")
        record_case("Case R9_5", "I6=HOLD 匹配预期 -> MATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case R9_5", "I6=HOLD", False, "pipeline failed")

    # Case R9_6: I6=VIOLATED 不符预期 HOLD -> MISMATCH
    c_dir_r9_6 = os.path.join(scratch, "case_R9_6")
    setup_base_case_dirs(c_dir_r9_6, prereg_rows)
    pr_r9_6 = os.path.join(scratch, "PREREG_CASE_R9_6.tsv")
    make_prereg_file(pr_r9_6, lambda r: r.update({"exp_I6": "HOLD", "state_analyzer": "STATE_JUDGE"}))
    for pas in ("pass1", "pass2"):
        p_path = os.path.join(c_dir_r9_6, pas, "M2-01-01-F3", "call2.txt")
        with open(p_path, "wb") as fh:
            fh.write(b"CORRUPTED_CALL2_OUTPUT")
    ok, v_r9_6 = run_pipeline(c_dir_r9_6, pr_r9_6, args.control_map)
    if ok:
        r = v_r9_6["M2-01-01-F3"]
        passed = (r["verdict"] == "MISMATCH" and ("I6_OUTPUT_DIFF" in r["mismatches"] or "I6(VIOLATED!=HOLD)" in r["mismatches"]))
        record_case("Case R9_6", "I6 输出与对照不符 (实测VIOLATED != 预期HOLD) -> MISMATCH", passed, f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case R9_6", "I6=VIOLATED", False, "pipeline failed")

# Write POSCTRL summary log
    lines = [
        "# POSCTRL_R9.txt -- Synthetic Positive Control Results (P05-S4 R9 S-J)",
        f"total_cases: {len(cases_results)}",
        f"passed_cases: {sum(1 for c in cases_results if c[2] == 'PASS')}",
        f"failed_cases: {sum(1 for c in cases_results if c[2] == 'FAIL')}",
        "\nCase\tDescription\tStatus\tDetail",
    ]
    for cid, desc, st, det in cases_results:
        lines.append(f"{cid}\t{desc}\t{st}\t{det}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    all_passed = all(c[2] == "PASS" for c in cases_results)
    print("\n" + "="*60)
    print(f"POSCTRL_R9: {len(cases_results)} cases, {sum(1 for c in cases_results if c[2] == 'PASS')} PASSED, {sum(1 for c in cases_results if c[2] == 'FAIL')} FAILED.")
    if not all_passed:
        sys.exit("Some positive control cases failed!")
    else:
        print("ALL POSITIVE CONTROLS PASSED.")


if __name__ == "__main__":
    main()
