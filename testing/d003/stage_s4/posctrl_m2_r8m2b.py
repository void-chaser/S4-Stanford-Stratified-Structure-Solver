#!/usr/bin/env python3
# posctrl_m2_r8m2b.py -- Synthetic positive controls for P05-S4 R8 M2b.
# Executes 27 cases:
#  - 19 baseline cases (A, B, C, D, E, F, F2, F3, F4, G, H, I, J, L, M, K, P, Q, R);
#  - 8 new cases:
#    * S1: gdb exit code 0, log exited 024 -> rc=20;
#    * S2: no-gdb SIGSEGV -> CRASH;
#    * S3: gdb rc1 != nogdb rc1 -> GDB_DIVERGENT;
#    * S4: log_path contains $ -> runner refuses;
#    * S5: NATIVE_FAIL_CONTROL with rc1=0 -> MISMATCH;
#    * S6: M2-10 missing M210_HIT -> MISMATCH;
#    * S7: hit1 mismatch -> MISMATCH;
#    * S8: san_ref rc mismatch -> MISMATCH.
# Calls formal scripts: facts_m2_r8m2b.py, state_judge_m2_r8m2a4.py, verdict_m2_r8m2b.py, run_m2_r8m2b.py.
# All paths parameterized. Scratch files strictly under EV/tmp/.
import argparse
import csv
import os
import shutil
import subprocess
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
PREREG_DEFAULT = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b", "PREREG_M2_EFFECTIVE_R8_M2b.tsv")
SANREF_DEFAULT = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b", "PREREG_M2_SANREF_R8_M2b.tsv")
CTRL_MAP_DEFAULT = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "CONTROL_MAPPING_R8_M2a3.tsv")

FACTS_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "facts_m2_r8m2b.py")
STATE_JUDGE_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "state_judge_m2_r8m2a4.py")
VERDICT_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "verdict_m2_r8m2b.py")
RUNNER_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "run_m2_r8m2b.py")


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

    # k = 2
    lines.append("R6BSTATE 2 n_layers 3 n_G 1")
    lines.append("R6STATE 2 layer 0 modes_null 0 modes_ptr 0x1 copy -1 nshapes 0")
    lines.append("R6STATE 2 layer 1 modes_null 1 modes_ptr 0 copy -1 nshapes 1")
    lines.append("R6STATE 2 layer 2 modes_null 1 modes_ptr 0 copy -1 nshapes 0")
    lines.append("R6BSTATE 2 layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
    lines.append("R6BSTATE 2 layer 1 modes_null 1 q_len 2 q_sha256 NA")
    lines.append("R6BSTATE 2 layer 2 modes_null 1 q_len 2 q_sha256 NA")
    lines.append("R6BSTATE 2 solution solved 0=0 1=0 2=0")

    if not is_dual:
        # call 2 (retry)
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

        # k = 4
        lines.append("R6BSTATE 4 n_layers 3 n_G 1")
        lines.append("R6BSTATE 4 layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
        lines.append("R6BSTATE 4 layer 1 modes_null 0 q_len 2 q_sha256 bbbbbbbb")
        lines.append("R6BSTATE 4 layer 2 modes_null 0 q_len 2 q_sha256 cccccccc")
        lines.append("R6BSTATE 4 solution solved 0=1 1=1 2=1")
    else:
        # Dual failure: call 2 is second failure
        lines.append("R6CREQ 2 1")
        lines.append("R6BCLM ENTER idx 1 name Slab")
        lines.append("R6BCLM RETURN idx 1 name Slab rc 20")
        lines.append("R6CALLS 2 20")
        lines.append("RC retry 20")

        # k = 3
        lines.append("R6BSTATE 3 n_layers 3 n_G 1")
        lines.append("R6STATE 3 layer 0 modes_null 0 modes_ptr 0x1 copy -1 nshapes 0")
        lines.append("R6STATE 3 layer 1 modes_null 1 modes_ptr 0 copy -1 nshapes 1")
        lines.append("R6STATE 3 layer 2 modes_null 1 modes_ptr 0 copy -1 nshapes 0")
        lines.append("R6BSTATE 3 layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
        lines.append("R6BSTATE 3 layer 1 modes_null 1 q_len 2 q_sha256 NA")
        lines.append("R6BSTATE 3 layer 2 modes_null 1 q_len 2 q_sha256 NA")
        lines.append("R6BSTATE 3 solution solved 0=0 1=0 2=0")

        # call 3 (final retry)
        lines.append("R6CREQ 3 1")
        lines.append("R6BCLM ENTER idx 1 name Slab")
        lines.append("R6BCLM RETURN idx 1 name Slab rc 0")
        lines.append("R6BCLM ENTER idx 2 name Below")
        lines.append("R6BCLM RETURN idx 2 name Below rc 0")
        lines.append("R6CALLS 3 0")
        lines.append("S4FMM HITCOUNT 2")
        lines.append("S4FMM HIT dual target2 real S4_malloc failure: FMM call 16 B (stream index 2, hit2=1 total=2)")

        # k = 4
        lines.append("R6BSTATE 4 n_layers 3 n_G 1")
        lines.append("R6STATE 4 layer 0 modes_null 0 modes_ptr 0x1 copy -1 nshapes 0")
        lines.append("R6STATE 4 layer 1 modes_null 0 modes_ptr 0x2 copy -1 nshapes 1")
        lines.append("R6STATE 4 layer 2 modes_null 0 modes_ptr 0x3 copy -1 nshapes 0")
        lines.append("R6BSTATE 4 layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
        lines.append("R6BSTATE 4 layer 1 modes_null 0 q_len 2 q_sha256 bbbbbbbb")
        lines.append("R6BSTATE 4 layer 2 modes_null 0 q_len 2 q_sha256 cccccccc")
        lines.append("R6BSTATE 4 solution solved 0=1 1=1 2=1")

    # Append gdb inferior exit line (octal format for exit code)
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


def run_pipeline(work_dir, prereg_path, ctrl_map_path=CTRL_MAP_DEFAULT):
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

    # Combine prereg with SANREF for facts extraction so reference points are present in facts
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
    r_v = subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                          "--prereg", prereg_path,
                          "--facts1", f1_tsv,
                          "--facts2", f2_tsv,
                          "--state1", s1_tsv,
                          "--state2", s2_tsv,
                          "--control-map", ctrl_map_path,
                          "--out-verdict", v_tsv,
                          "--out-summary", v_sum],
                         capture_output=True, text=True)
    if r_v.returncode != 0:
        return False, f"verdict failed: {r_v.stderr}"

    verdict_dict = {}
    with open(v_tsv, encoding="utf-8") as fh:
        for r in csv.DictReader((line for line in fh if not line.startswith("#")), delimiter="\t"):
            verdict_dict[r["point_id"]] = r

    return True, verdict_dict


def main():
    parser = argparse.ArgumentParser(description="P05-S4 POSCTRL runner v3")
    parser.add_argument("--prereg", default=PREREG_DEFAULT, help="Path to effective preregistration table")
    parser.add_argument("--control-map", default=CTRL_MAP_DEFAULT, help="Path to control mapping table")
    parser.add_argument("--ev", default=None, help="Evidence directory root")
    parser.add_argument("--out", required=True, help="Path to write POSCTRL result log")
    args = parser.parse_args()

    ev_root = os.path.abspath(args.ev or os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2b"))
    scratch = os.path.join(ev_root, "tmp", "posctrl_m2b_scratch")
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

    # Case A: Clean baseline -> ALL MATCH (all 150 match since sanref points are mapped in prereg v3)
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

    # Case B: rc1 mismatch on M2-01-01-F3 (exp 20 -> obs 0, in both stdout and gdb.log to avoid divergence)
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

    # Case C: rc2 mismatch on M2-01-01-F3 (exp 0 -> obs 20, both stdout and gdb.log agree)
    c_dir = os.path.join(scratch, "case_C")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-01-01-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 20\nRC retry 20\nS4FMM HITCOUNT 1\n")
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        # gdb log has rc2=20 as well
        gtxt = make_clean_gdb_log("M2-01-01-F3", "M2-01", rc1=20, ec=20)
        gtxt = gtxt.replace("R6CALLS 2 0", "R6CALLS 2 20").replace("RC retry 0", "RC retry 20")
        with open(gp, "w") as fh:
            fh.write(gtxt)
    ok, v_c = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_c["M2-01-01-F3"]
        record_case("Case C", "单点 rc2 不符 (rc2 mismatch)",
                    r["verdict"] == "MISMATCH" and "exp_rc2(20!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case C", "单点 rc2 不符", False, v_c)

    # Case D: signal mismatch on M2-01-01-F3 (exp 0 -> obs 11)
    c_dir = os.path.join(scratch, "case_D")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt")
        with open(p, "w") as fh:
            fh.write("139\n")
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        with open(gp, "w") as fh:
            fh.write("Program terminated with signal SIGSEGV, Segmentation fault.\n")
    ok, v_d = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_d["M2-01-01-F3"]
        record_case("Case D", "单点信号异常 (Signal abnormal)",
                    r["verdict"] == "MISMATCH" and "exp_signal(11!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case D", "单点信号异常", False, v_d)

    # Case E: hit mismatch on M2-01-01-F3 (exp 1 -> obs 0, in both)
    c_dir = os.path.join(scratch, "case_E")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-01-01-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 0\n")
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        gtxt = make_clean_gdb_log("M2-01-01-F3", "M2-01", rc1=20, ec=20)
        gtxt = gtxt.replace("S4FMM HITCOUNT 1", "S4FMM HITCOUNT 0")
        with open(gp, "w") as fh:
            fh.write(gtxt)
    ok, v_e = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_e["M2-01-01-F3"]
        record_case("Case E", "命中数不符 (Hit mismatch)",
                    r["verdict"] == "MISMATCH" and "exp_hit(0!=1)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case E", "命中数不符", False, v_e)

    # Case F: Dual failure hit2 mismatch on M2-04-01-F3 (both agree on hit2=0)
    c_dir = os.path.join(scratch, "case_F")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-04-01-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 20\nRC retry 20\nR6CALLS 3 0\nS4FMM HITCOUNT 1\nS4FMM HIT dual target2 real S4_malloc failure: FMM call 16 B (stream index 2, hit2=0 total=1)\n")
        gp = os.path.join(c_dir, pas, "M2-04-01-F3", "gdb.log")
        with open(gp, "w") as fh:
            fh.write(make_clean_gdb_log("M2-04-01-F3", "M2-04").replace("hit2=1 total=2", "hit2=0 total=1").replace("S4FMM HITCOUNT 2", "S4FMM HITCOUNT 1"))
    ok, v_f = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_f["M2-04-01-F3"]
        record_case("Case F", "双失败 hit2 不符 (Dual failure hit2 mismatch)",
                    r["verdict"] == "MISMATCH" and "exp_hit2(0!=1)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F", "双失败 hit2 不符", False, v_f)

    # Case F2: inject2_invalid mismatch on M2-04-01-F3 (added to both)
    c_dir = os.path.join(scratch, "case_F2")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-04-01-F3", "stdout.txt")
        with open(p, "a") as fh:
            fh.write("S4FMM INJECT2 INVALID\n")
        gp = os.path.join(c_dir, pas, "M2-04-01-F3", "gdb.log")
        with open(gp, "a") as fh:
            fh.write("S4FMM INJECT2 INVALID\n")
    ok, v_f2 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_f2["M2-04-01-F3"]
        record_case("Case F2", "双失败 inject2_invalid 检出",
                    r["verdict"] == "MISMATCH" and "exp_inject2_invalid(1!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F2", "双失败 inject2_invalid 检出", False, v_f2)

    # Case F3: inject2_suppressed mismatch on M2-04-01-F3 (added to both)
    c_dir = os.path.join(scratch, "case_F3")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-04-01-F3", "stdout.txt")
        with open(p, "a") as fh:
            fh.write("S4FMM INJECT2 SUPPRESSED\n")
        gp = os.path.join(c_dir, pas, "M2-04-01-F3", "gdb.log")
        with open(gp, "a") as fh:
            fh.write("S4FMM INJECT2 SUPPRESSED\n")
    ok, v_f3 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_f3["M2-04-01-F3"]
        record_case("Case F3", "双失败 inject2_suppressed 检出",
                    r["verdict"] == "MISMATCH" and "exp_inject2_suppressed(1!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F3", "双失败 inject2_suppressed 检出", False, v_f3)

    # Case F4: rc3 mismatch on M2-04-01-F3 (both agree rc3=20)
    c_dir = os.path.join(scratch, "case_F4")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-04-01-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 20\nRC retry 20\nR6CALLS 3 20\nS4FMM HITCOUNT 2\nS4FMM HIT dual target2 real S4_malloc failure: FMM call 16 B (stream index 2, hit2=1 total=2)\n")
        gp = os.path.join(c_dir, pas, "M2-04-01-F3", "gdb.log")
        with open(gp, "w") as fh:
            fh.write(make_clean_gdb_log("M2-04-01-F3", "M2-04").replace("R6CALLS 3 0", "R6CALLS 3 20"))
    ok, v_f4 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_f4["M2-04-01-F3"]
        record_case("Case F4", "双失败恢复 rc3 不符",
                    r["verdict"] == "MISMATCH" and "exp_rc3(20!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F4", "双失败恢复 rc3 不符", False, v_f4)

    # Case G: Missing gdb log for M2-01-01-F3 -> UNJUDGED_MISSING
    c_dir = os.path.join(scratch, "case_G")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        if os.path.isfile(gp):
            os.remove(gp)
    ok, v_g = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_g["M2-01-01-F3"]
        record_case("Case G", "缺 gdb 日志 (Missing gdb log -> UNJUDGED_MISSING)",
                    r["verdict"] == "UNJUDGED" and r["verdict_detail"] == "UNJUDGED_MISSING",
                    f"verdict={r['verdict']}, detail={r['verdict_detail']}")
    else:
        record_case("Case G", "缺 gdb 日志", False, v_g)

    # Case H: Missing ID in pass 1 -> SCHEMA_ERROR
    c_dir = os.path.join(scratch, "case_H")
    setup_base_case_dirs(c_dir, prereg_rows)
    shutil.rmtree(os.path.join(c_dir, "pass1", "M2-01-01-F3"))
    ok, v_h = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_h["M2-01-01-F3"]
        record_case("Case H", "缺失 ID (Missing ID in pass 1 -> SCHEMA_ERROR)",
                    r["verdict"] == "SCHEMA_ERROR" and "MISSING_IN_PASS1" in r["mismatches"],
                    f"verdict={r['verdict']}, issues={r['mismatches']}")
    else:
        record_case("Case H", "缺失 ID", False, v_h)

    # Case I: Tree mismatch -> SCHEMA_ERROR
    c_dir = os.path.join(scratch, "case_I")
    setup_base_case_dirs(c_dir, prereg_rows)
    f1_tsv = os.path.join(c_dir, "FACTS_pass1.tsv")
    f2_tsv = os.path.join(c_dir, "FACTS_pass2.tsv")
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", args.prereg,
                    "--run-dir", os.path.join(c_dir, "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", args.prereg,
                    "--run-dir", os.path.join(c_dir, "pass2"), "--pass", "2", "--out", f2_tsv], check=True)
    with open(f1_tsv, "r") as fh:
        ftxt = fh.read()
    ftxt_tampered = ftxt.replace("M2-01-01-F3\t1\tF3", "M2-01-01-F3\t1\tB")
    with open(f1_tsv, "w") as fh:
        fh.write(ftxt_tampered)
    v_tsv = os.path.join(c_dir, "VERDICT.tsv")
    v_sum = os.path.join(c_dir, "VERDICT_SUMMARY.txt")
    r_v = subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                          "--prereg", args.prereg,
                          "--facts1", f1_tsv,
                          "--facts2", f2_tsv,
                          "--out-verdict", v_tsv,
                          "--out-summary", v_sum],
                         capture_output=True, text=True)
    v_dict = read_tsv_dict(v_tsv, "point_id")
    r = v_dict.get("M2-01-01-F3", {})
    record_case("Case I", "Tree 不符 (Tree mismatch -> SCHEMA_ERROR)",
                r.get("verdict") == "SCHEMA_ERROR" and "TREE_MISMATCH_PASS1" in r.get("mismatches", ""),
                f"verdict={r.get('verdict')}, issues={r.get('mismatches')}")

    # Case J: I6 output difference -> MISMATCH(I6)
    c_dir = os.path.join(scratch, "case_J")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-01-01-F3", "call2.txt")
        with open(p, "w") as fh:
            fh.write("corrupted output difference\n9.9 9.9 9.9\n")
    ok, v_j = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_j["M2-01-01-F3"]
        record_case("Case J", "I6 恢复输出差异判为 MISMATCH (I6 diff -> MISMATCH)",
                    r["verdict"] == "MISMATCH" and "I6=VIOLATED" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case J", "I6 恢复输出差异判为 MISMATCH", False, v_j)

    # Case L: Flaky detection between pass 1 and pass 2
    c_dir = os.path.join(scratch, "case_L")
    setup_base_case_dirs(c_dir, prereg_rows)
    p = os.path.join(c_dir, "pass1", "M2-01-01-F3", "stdout.txt")
    with open(p, "w") as fh:
        fh.write("R6CALLS 1 0\nRC first 0\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 1\n")
    with open(os.path.join(c_dir, "pass1", "M2-01-01-F3", "exitcode.txt"), "w") as fh:
        fh.write("0\n")
    with open(os.path.join(c_dir, "pass1", "M2-01-01-F3", "gdb.log"), "w") as fh:
        fh.write(make_clean_gdb_log("M2-01-01-F3", "M2-01", rc1=0, ec=0))
    ok, v_l = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_l["M2-01-01-F3"]
        record_case("Case L", "跨 pass 不一致检为 FLAKY (Flaky between passes)",
                    r["verdict"] == "FLAKY" and "rc1" in r["flaky_fields"],
                    f"verdict={r['verdict']}, flaky_fields={r['flaky_fields']}")
    else:
        record_case("Case L", "跨 pass 不一致检为 FLAKY", False, v_l)

    # Case M: M2-10-01-B baseline rule pass
    c_dir = os.path.join(scratch, "case_M")
    setup_base_case_dirs(c_dir, prereg_rows)
    ok, v_m = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_m["M2-10-01-B"]
        record_case("Case M", "M2-10 baseline_only_rule 正确判 MATCH",
                    r["verdict"] == "MATCH",
                    f"verdict={r['verdict']}, detail={r['verdict_detail']}")
    else:
        record_case("Case M", "M2-10 baseline_only_rule 正确判 MATCH", False, v_m)

    # Case K: ASAN error reported on M2-03-G5-01-F3 -> MISMATCH
    c_dir = os.path.join(scratch, "case_K")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-03-G5-01-F3", "stderr.txt")
        with open(p, "w") as fh:
            fh.write("==12345==ERROR: AddressSanitizer: heap-use-after-free on address 0x...\n")
    ok, v_k = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_k["M2-03-G5-01-F3"]
        record_case("Case K", "sanitizer 检出报告判为 MISMATCH",
                    r["verdict"] == "MISMATCH" and "exp_san(1!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case K", "sanitizer 检出报告判为 MISMATCH", False, v_k)

    # Case P: sanitizer rc differs from san_ref
    c_dir = os.path.join(scratch, "case_P")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        p = os.path.join(c_dir, pas, "M2-03-REP-INIT-01-F3", "stdout.txt")
        with open(p, "w") as fh:
            fh.write("R6CALLS 1 0\nRC first 0\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 1\n")
        with open(os.path.join(c_dir, pas, "M2-03-REP-INIT-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("0\n")
    ok, v_p = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_p["M2-03-REP-INIT-01-F3"]
        record_case("Case P", "sanitizer rc 与 san_ref 不同",
                    r["verdict"] == "MISMATCH" and "san_ref_rc1(0!=20)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case P", "sanitizer rc 与 san_ref 不同", False, v_p)

    # Case Q: san_ref=NO_REF -> UNJUDGED_BY_DESIGN
    c_dir = os.path.join(scratch, "case_Q")
    setup_base_case_dirs(c_dir, prereg_rows)
    # Temporarily set san_ref_point_id=NO_REF on M2-03-G5-01-F3
    q_prereg = os.path.join(c_dir, "q_prereg.tsv")
    with open(q_prereg, "w", encoding="utf-8") as fh:
        fh.write("\t".join(prereg_rows[0].keys()) + "\n")
        for row in prereg_rows:
            r_copy = dict(row)
            if r_copy["point_id"] == "M2-03-G5-01-F3":
                r_copy["san_ref_point_id"] = "NO_REF"
            fh.write("\t".join(r_copy.values()) + "\n")

    ok, v_q = run_pipeline(c_dir, q_prereg, args.control_map)
    if ok:
        r = v_q["M2-03-G5-01-F3"]
        record_case("Case Q", "san_ref=NO_REF -> UNJUDGED_BY_DESIGN",
                    r["verdict"] == "UNJUDGED" and r["verdict_detail"] == "UNJUDGED_BY_DESIGN",
                    f"verdict={r['verdict']}, detail={r['verdict_detail']}")
    else:
        record_case("Case Q", "san_ref=NO_REF", False, v_q)

    # Case R: Total != 150 asserts exit failure
    c_dir = os.path.join(scratch, "case_R")
    setup_base_case_dirs(c_dir, prereg_rows)
    tampered_prereg = os.path.join(c_dir, "prereg_149.tsv")
    with open(tampered_prereg, "w", encoding="utf-8") as fh:
        fh.write("\t".join(prereg_rows[0].keys()) + "\n")
        for row in prereg_rows[:-1]:
            fh.write("\t".join(row.values()) + "\n")

    f1_tsv = os.path.join(c_dir, "FACTS_pass1.tsv")
    f2_tsv = os.path.join(c_dir, "FACTS_pass2.tsv")
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", tampered_prereg,
                    "--run-dir", os.path.join(c_dir, "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", tampered_prereg,
                    "--run-dir", os.path.join(c_dir, "pass2"), "--pass", "2", "--out", f2_tsv], check=True)

    v_tsv = os.path.join(c_dir, "VERDICT.tsv")
    v_sum = os.path.join(c_dir, "VERDICT_SUMMARY.txt")
    r_v = subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                          "--prereg", tampered_prereg,
                          "--facts1", f1_tsv,
                          "--facts2", f2_tsv,
                          "--out-verdict", v_tsv,
                          "--out-summary", v_sum,
                          "--expected-total", "150"],
                         capture_output=True, text=True)
    record_case("Case R", "汇总合计!=150 构造输入断言失败退出",
                r_v.returncode != 0 and "FATAL: Total points evaluated" in r_v.stderr,
                f"exit_code={r_v.returncode}, stderr={r_v.stderr.strip()[:60]}")

    # ================= NEW CASES (S1 - S8) =================

    # Case S1: gdb exit code 0, log exited 024 -> rc=20 parsed correctly
    c_dir = os.path.join(scratch, "case_S1")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        gp = os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log")
        with open(gp, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 1\n[Inferior 1 (process 123) exited with code 024]\n")
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "exitcode.txt"), "w") as fh:
            fh.write("20\n")
    f1_tsv = os.path.join(c_dir, "FACTS_pass1.tsv")
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", args.prereg,
                    "--run-dir", os.path.join(c_dir, "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    facts_s1 = read_tsv_dict(f1_tsv, "point_id")
    r_s1 = facts_s1.get("M2-01-01-F3", {})
    record_case("Case S1", "gdb 退出码 0、日志 exited 024 解析为 rc=20 且 gdb_divergent=0",
                r_s1.get("rc") == "20" and r_s1.get("gdb_divergent") == "0",
                f"rc={r_s1.get('rc')}, signal={r_s1.get('signal')}, gdb_divergent={r_s1.get('gdb_divergent')}")

    # Case S2: No-gdb SIGSEGV -> CRASH
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
                    r["verdict"] == "MISMATCH" and "exp_signal(11!=0)" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case S2", "不挂 gdb 的运行出现 SIGSEGV", False, v_s2)

    # Case S3: gdb rc1 != nogdb rc1 -> GDB_DIVERGENT
    c_dir = os.path.join(scratch, "case_S3")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("pass1", "pass2"):
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "stdout.txt"), "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 1\n")
        with open(os.path.join(c_dir, pas, "M2-01-01-F3", "gdb.log"), "w") as fh:
            fh.write("R6CALLS 1 0\nRC first 0\nR6CALLS 2 0\nRC retry 0\nS4FMM HITCOUNT 1\n[Inferior 1 (process 123) exited with code 024]\n")
    ok, v_s3 = run_pipeline(c_dir, args.prereg, args.control_map)
    if ok:
        r = v_s3["M2-01-01-F3"]
        record_case("Case S3", "gdb 与 nogdb 的 rc1 不同 -> GDB_DIVERGENT",
                    r["verdict"] == "GDB_DIVERGENT",
                    f"verdict={r['verdict']}, detail={r['verdict_detail']}, notes={r['notes']}")
    else:
        record_case("Case S3", "gdb 与 nogdb 的 rc1 不同", False, v_s3)

    # Case S4: log_path contains $ -> runner refuses
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
        p = os.path.join(c_dir, pas, "M2-04-01-F3", "stdout.txt")
        with open(p, "w") as fh:
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

    # Write POSCTRL summary log
    lines = [
        "# POSCTRL_M2_R8_M2b -- Synthetic Positive Control Results",
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
    print(f"POSCTRL_M2_R8_M2b: {len(cases_results)} cases, {sum(1 for c in cases_results if c[2] == 'PASS')} PASSED, {sum(1 for c in cases_results if c[2] == 'FAIL')} FAILED.")
    if not all_passed:
        sys.exit("Some positive control cases failed!")
    else:
        print("ALL POSITIVE CONTROLS PASSED.")


if __name__ == "__main__":
    main()
