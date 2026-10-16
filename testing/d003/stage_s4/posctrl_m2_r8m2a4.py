#!/usr/bin/env python3
# posctrl_m2_r8m2a4.py -- Synthetic positive controls for P05-S4 R8 M2a4.
# Executes 19 cases (A, B, C, D, E, F, F2, F3, F4, G, H, I, J, L, M, K, P, Q, R) by calling
# the formal scripts: facts_m2_r8m2a4.py, state_judge_m2_r8m2a4.py, and verdict_m2_r8m2a4.py.
# Does not replicate logic. Output paths are fully parameterized.
import argparse
import csv
import os
import shutil
import subprocess
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
PREREG_FILE = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a4", "PREREG_M2_EFFECTIVE_R8_M2a4.tsv")
CTRL_MAP_FILE = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2a3", "CONTROL_MAPPING_R8_M2a3.tsv")

FACTS_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "facts_m2_r8m2a4.py")
STATE_JUDGE_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "state_judge_m2_r8m2a4.py")
VERDICT_PY = os.path.join(REPO, "testing", "d003", "stage_s4", "verdict_m2_r8m2a4.py")


def make_clean_gdb_log(pid, item):
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
    lines.append("R6BCLM RETURN idx 1 name Slab rc 20")

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

        # k = 4
        lines.append("R6BSTATE 4 n_layers 3 n_G 1")
        lines.append("R6STATE 4 layer 0 modes_null 0 modes_ptr 0x1 copy -1 nshapes 0")
        lines.append("R6STATE 4 layer 1 modes_null 0 modes_ptr 0x2 copy -1 nshapes 1")
        lines.append("R6STATE 4 layer 2 modes_null 0 modes_ptr 0x3 copy -1 nshapes 0")
        lines.append("R6BSTATE 4 layer 0 modes_null 0 q_len 2 q_sha256 aaaaaaaa")
        lines.append("R6BSTATE 4 layer 1 modes_null 0 q_len 2 q_sha256 bbbbbbbb")
        lines.append("R6BSTATE 4 layer 2 modes_null 0 q_len 2 q_sha256 cccccccc")
        lines.append("R6BSTATE 4 solution solved 0=1 1=1 2=1")

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

            # Exit code
            ec = 0
            if item == "M2-10":
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
            else:
                rc1 = 0

            if r.get("exp_rc2") not in (None, "", "-"):
                rc2 = int(r["exp_rc2"])
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
                if is_ctrl:
                    gdb_txt = make_control_gdb_log(pid)
                else:
                    gdb_txt = make_clean_gdb_log(pid, item)
                with open(os.path.join(pt_dir, "gdb.log"), "w") as fh:
                    fh.write(gdb_txt)


def run_pipeline(work_dir, prereg_path):
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

    # 1. Facts pass 1
    r_f1 = subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", prereg_path,
                           "--run-dir", p1_dir, "--pass", "1", "--out", f1_tsv],
                          capture_output=True, text=True)
    if r_f1.returncode != 0:
        return False, f"facts1 failed: {r_f1.stderr}"

    # 2. Facts pass 2
    r_f2 = subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", prereg_path,
                           "--run-dir", p2_dir, "--pass", "2", "--out", f2_tsv],
                          capture_output=True, text=True)
    if r_f2.returncode != 0:
        return False, f"facts2 failed: {r_f2.stderr}"

    # 3. State judge
    r_sj = subprocess.run([sys.executable, "-I", "-B", STATE_JUDGE_PY,
                           "--prereg", prereg_path,
                           "--control", CTRL_MAP_FILE,
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

    # Copy s1_tsv to s2_tsv for state pass 2
    shutil.copyfile(s1_tsv, s2_tsv)

    # 4. Verdict
    r_v = subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                          "--prereg", prereg_path,
                          "--facts1", f1_tsv,
                          "--facts2", f2_tsv,
                          "--state1", s1_tsv,
                          "--state2", s2_tsv,
                          "--control-map", CTRL_MAP_FILE,
                          "--out-verdict", v_tsv,
                          "--out-summary", v_sum],
                         capture_output=True, text=True)
    if r_v.returncode != 0:
        return False, f"verdict failed: {r_v.stderr}"

    # Read verdict rows
    v_dict = {}
    with open(v_tsv, encoding="utf-8") as fh:
        for row in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"):
            v_dict[row["point_id"]] = row

    return True, v_dict


def main():
    parser = argparse.ArgumentParser(description="P05-S4 synthetic positive controls")
    parser.add_argument("--out", required=True, help="Output POSCTRL log path")
    parser.add_argument("--work-dir", default=None, help="Scratch directory")

    args = parser.parse_args()

    if os.path.exists(args.out):
        sys.exit(f"REFUSED: {args.out} already exists (U17)")

    scratch = args.work_dir or os.path.join(os.path.dirname(os.path.abspath(args.out)), "tmp_posctrl")
    if os.path.isdir(scratch):
        shutil.rmtree(scratch)
    os.makedirs(scratch, exist_ok=True)

    with open(PREREG_FILE, encoding="utf-8") as fh:
        prereg_rows = list(csv.DictReader(fh, delimiter="\t"))

    cases_results = []

    def record_case(cid, desc, passed, detail):
        status_str = "PASS" if passed else "FAIL"
        cases_results.append((cid, desc, status_str, detail))
        print(f"[{status_str}] {cid}: {desc} -> {detail}")

    # Case A: Full match baseline
    c_dir = os.path.join(scratch, "case_A")
    setup_base_case_dirs(c_dir, prereg_rows)
    ok, v_a = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        m_cnt = sum(1 for r in v_a.values() if r["verdict"] == "MATCH")
        u_cnt = sum(1 for r in v_a.values() if r["verdict_detail"] == "UNJUDGED_BY_DESIGN")
        tot = len(v_a)
        record_case("Case A", "完全匹配 (Full match baseline)",
                    tot == 150 and m_cnt == 131 and u_cnt == 19,
                    f"total={tot}, MATCH={m_cnt}, UNJUDGED_DESIGN={u_cnt}")
    else:
        record_case("Case A", "完全匹配", False, v_a)

    # Case B: Tamper rc1 of M2-01-01-F3
    c_dir = os.path.join(scratch, "case_B")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("1", "2"):
        p_f = os.path.join(c_dir, f"pass{pas}", "M2-01-01-F3", "stdout.txt")
        with open(p_f, "w") as fh:
            fh.write("R6CALLS 1 0\nRC first 0\nR6CALLS 2 0\nRC retry 0\nR6CALLS 3 0\nS4FMM HITCOUNT 1\n")
    ok, v_b = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_b["M2-01-01-F3"]
        record_case("Case B", "改 rc1 (Tamper rc1)",
                    r["verdict"] == "MISMATCH" and "exp_rc1" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case B", "改 rc1", False, v_b)

    # Case C: Flaky on M2-01-01-F3 (only pass 2 changed)
    c_dir = os.path.join(scratch, "case_C")
    setup_base_case_dirs(c_dir, prereg_rows)
    p2_f = os.path.join(c_dir, "pass2", "M2-01-01-F3", "stdout.txt")
    with open(p2_f, "w") as fh:
        fh.write("R6CALLS 1 0\nRC first 0\nR6CALLS 2 0\nRC retry 0\nR6CALLS 3 0\nS4FMM HITCOUNT 1\n")
    ok, v_c = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_c["M2-01-01-F3"]
        record_case("Case C", "仅第二遍改值 (FLAKY on pass 2)",
                    r["verdict"] == "FLAKY" and "rc1" in r["flaky_fields"],
                    f"verdict={r['verdict']}, flaky_fields={r['flaky_fields']}")
    else:
        record_case("Case C", "仅第二遍改值", False, v_c)

    # Case D: NZ testing (M2-07-INJ-closed1d-ng5-F3)
    c_dir = os.path.join(scratch, "case_D")
    setup_base_case_dirs(c_dir, prereg_rows)
    # D0: rc1 = 0 -> MISMATCH
    for pas in ("1", "2"):
        p_f = os.path.join(c_dir, f"pass{pas}", "M2-07-INJ-closed1d-ng5-F3", "stdout.txt")
        with open(p_f, "w") as fh:
            fh.write("RC first 0\nRC retry 0\nS4FMM HITCOUNT 1\n")
        with open(os.path.join(c_dir, f"pass{pas}", "M2-07-INJ-closed1d-ng5-F3", "exitcode.txt"), "w") as fh:
            fh.write("0\n")
    ok, v_d = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_d["M2-07-INJ-closed1d-ng5-F3"]
        record_case("Case D", "NZ 对 0 与 20 (NZ notation rc1=0 fails)",
                    r["verdict"] == "MISMATCH" and "exp_rc1" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case D", "NZ 对 0 与 20", False, v_d)

    # Case E: Synthetic gdb log causes I1 violation on M2-01-01-F3
    c_dir = os.path.join(scratch, "case_E")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("1", "2"):
        g_f = os.path.join(c_dir, f"pass{pas}", "M2-01-01-F3", "gdb.log")
        with open(g_f, "r") as fh:
            gtxt = fh.read()
        # Change modes_null 1 to modes_null 0 at k=1
        gtxt_tampered = gtxt.replace("R6BSTATE 1 layer 1 modes_null 1", "R6BSTATE 1 layer 1 modes_null 0")
        with open(g_f, "w") as fh:
            fh.write(gtxt_tampered)
    ok, v_e = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_e["M2-01-01-F3"]
        record_case("Case E", "I1 违反 (I1 VIOLATED -> MISMATCH)",
                    r["verdict"] == "MISMATCH" and "I1=VIOLATED" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case E", "I1 违反", False, v_e)

    # Case F: Dual failure rc3 != 0 on M2-04-01-F3
    c_dir = os.path.join(scratch, "case_F")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("1", "2"):
        p_f = os.path.join(c_dir, f"pass{pas}", "M2-04-01-F3", "stdout.txt")
        with open(p_f, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 20\nRC retry 20\nR6CALLS 3 20\nS4FMM HITCOUNT 2\nS4FMM HIT dual target2 real S4_malloc failure: FMM call 16 B (stream index 2, hit2=1 total=2)\n")
    ok, v_f = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_f["M2-04-01-F3"]
        record_case("Case F", "双失败 rc3!=0 (Dual failure rc3 non-zero)",
                    r["verdict"] == "MISMATCH" and "exp_rc3" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F", "双失败 rc3!=0", False, v_f)

    # Case F2: Dual failure hit2=0 on M2-04-01-F3
    c_dir = os.path.join(scratch, "case_F2")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("1", "2"):
        p_f = os.path.join(c_dir, f"pass{pas}", "M2-04-01-F3", "stdout.txt")
        # Omit hit2 line
        with open(p_f, "w") as fh:
            fh.write("R6CALLS 1 20\nRC first 20\nR6CALLS 2 20\nRC retry 20\nR6CALLS 3 0\nS4FMM HITCOUNT 2\n")
    ok, v_f2 = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_f2["M2-04-01-F3"]
        record_case("Case F2", "双失败 hit2=0 (Dual failure hit2=0)",
                    r["verdict"] == "MISMATCH" and "exp_hit2" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F2", "双失败 hit2=0", False, v_f2)

    # Case F3: Dual failure INJECT2 SUPPRESSED on M2-04-01-F3
    c_dir = os.path.join(scratch, "case_F3")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("1", "2"):
        p_f = os.path.join(c_dir, f"pass{pas}", "M2-04-01-F3", "stderr.txt")
        with open(p_f, "w") as fh:
            fh.write("S4FMM INJECT2 SUPPRESSED plan (target 1 consumed the same event)\n")
    ok, v_f3 = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_f3["M2-04-01-F3"]
        record_case("Case F3", "双失败出现 INJECT2 SUPPRESSED",
                    r["verdict"] == "MISMATCH" and "exp_inject2_suppressed" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F3", "双失败出现 INJECT2 SUPPRESSED", False, v_f3)

    # Case F4: Dual failure second failure layer differs from fail_layer2
    c_dir = os.path.join(scratch, "case_F4")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("1", "2"):
        g_f = os.path.join(c_dir, f"pass{pas}", "M2-04-01-F3", "gdb.log")
        with open(g_f, "r") as fh:
            gtxt = fh.read()
        # In call2, change failure from layer 1 to layer 2
        gtxt_tampered = gtxt.replace("R6BCLM RETURN idx 1 name Slab rc 20", "R6BCLM RETURN idx 2 name Below rc 20")
        with open(g_f, "w") as fh:
            fh.write(gtxt_tampered)
    ok, v_f4 = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_f4["M2-04-01-F3"]
        record_case("Case F4", "第二失败层与 fail_layer2 不符 (Second fail layer mismatch)",
                    r["verdict"] == "MISMATCH" and "I1=VIOLATED" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case F4", "第二失败层与 fail_layer2 不符", False, v_f4)

    # Case G: Missing gdb log for M2-01-01-F3
    c_dir = os.path.join(scratch, "case_G")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("1", "2"):
        g_f = os.path.join(c_dir, f"pass{pas}", "M2-01-01-F3", "gdb.log")
        if os.path.isfile(g_f):
            os.remove(g_f)
    ok, v_g = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_g["M2-01-01-F3"]
        record_case("Case G", "缺 gdb 日志 (Missing gdb log -> UNJUDGED)",
                    r["verdict"] == "UNJUDGED" and r["verdict_detail"] == "UNJUDGED_MISSING",
                    f"verdict={r['verdict']}, detail={r['verdict_detail']}")
    else:
        record_case("Case G", "缺 gdb 日志", False, v_g)

    # Case H: Structural ID errors (H1 duplicate, H2 missing, H3 extra)
    # Tested by checking verdict behavior on missing/extra point in facts
    c_dir = os.path.join(scratch, "case_H")
    setup_base_case_dirs(c_dir, prereg_rows)
    # Remove M2-01-01-F3 directory from pass 1
    shutil.rmtree(os.path.join(c_dir, "pass1", "M2-01-01-F3"))
    ok, v_h = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_h["M2-01-01-F3"]
        record_case("Case H", "缺失 ID (Missing ID in pass 1 -> SCHEMA_ERROR)",
                    r["verdict"] == "SCHEMA_ERROR" and "MISSING_IN_PASS1" in r["mismatches"],
                    f"verdict={r['verdict']}, issues={r['mismatches']}")
    else:
        record_case("Case H", "缺失 ID", False, v_h)

    # Case I: Tree mismatch
    c_dir = os.path.join(scratch, "case_I")
    setup_base_case_dirs(c_dir, prereg_rows)
    # Run pipeline up to facts, then modify tree in facts1
    f1_tsv = os.path.join(c_dir, "FACTS_pass1.tsv")
    f2_tsv = os.path.join(c_dir, "FACTS_pass2.tsv")
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", PREREG_FILE,
                    "--run-dir", os.path.join(c_dir, "pass1"), "--pass", "1", "--out", f1_tsv], check=True)
    subprocess.run([sys.executable, "-I", "-B", FACTS_PY, "--prereg", PREREG_FILE,
                    "--run-dir", os.path.join(c_dir, "pass2"), "--pass", "2", "--out", f2_tsv], check=True)
    # Tamper tree in f1_tsv
    with open(f1_tsv, "r") as fh:
        ftxt = fh.read()
    ftxt_tampered = ftxt.replace("M2-01-01-F3\t1\tF3", "M2-01-01-F3\t1\tB")
    with open(f1_tsv, "w") as fh:
        fh.write(ftxt_tampered)

    v_tsv = os.path.join(c_dir, "VERDICT.tsv")
    v_sum = os.path.join(c_dir, "VERDICT_SUMMARY.txt")
    r_v = subprocess.run([sys.executable, "-I", "-B", VERDICT_PY,
                          "--prereg", PREREG_FILE,
                          "--facts1", f1_tsv,
                          "--facts2", f2_tsv,
                          "--out-verdict", v_tsv,
                          "--out-summary", v_sum],
                         capture_output=True, text=True)
    if r_v.returncode == 0:
        v_dict = {}
        with open(v_tsv) as fh:
            for row in csv.DictReader((l for l in fh if not l.startswith("#")), delimiter="\t"):
                v_dict[row["point_id"]] = row
        r = v_dict["M2-01-01-F3"]
        record_case("Case I", "tree 不符 (Tree mismatch -> SCHEMA_ERROR)",
                    r["verdict"] == "SCHEMA_ERROR" and "TREE_MISMATCH" in r["mismatches"],
                    f"verdict={r['verdict']}, issues={r['mismatches']}")
    else:
        record_case("Case I", "tree 不符", False, r_v.stderr)

    # Case J: I6 output difference on M2-04-01-F3 -> MISMATCH(I6), NOT SCHEMA_ERROR!
    c_dir = os.path.join(scratch, "case_J")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("1", "2"):
        d_f = os.path.join(c_dir, f"pass{pas}", "M2-04-01-F3", "call3.txt")
        with open(d_f, "w") as fh:
            fh.write("corrupted divergent call 3 field dump\n")
    ok, v_j = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_j["M2-04-01-F3"]
        record_case("Case J", "I6 输出不同记为 MISMATCH(I6) (I6 diff -> MISMATCH, not SCHEMA_ERROR)",
                    r["verdict"] == "MISMATCH" and "I6=VIOLATED" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case J", "I6 输出不同", False, v_j)

    # Case L: M2-07 injection row call1 differs from control -> does NOT error!
    c_dir = os.path.join(scratch, "case_L")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("1", "2"):
        d_f = os.path.join(c_dir, f"pass{pas}", "M2-07-INJ-closed1d-ng5-F3", "call1.txt")
        with open(d_f, "w") as fh:
            fh.write("failed injection different dump output\n")
    ok, v_l = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_l["M2-07-INJ-closed1d-ng5-F3"]
        record_case("Case L", "M2-07 注入行 call1 输出与对照不同不报错 (Failed call output diff not judged)",
                    r["verdict"] == "MATCH",
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case L", "M2-07 注入行 call1 输出", False, v_l)

    # Case M: M2-10 rc1=20 -> MATCH (BASELINE_ONLY_RULE)
    c_dir = os.path.join(scratch, "case_M")
    setup_base_case_dirs(c_dir, prereg_rows)
    ok, v_m = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_m["M2-10-01-B"]
        record_case("Case M", "M2-10 rc1=20 -> MATCH (BASELINE_ONLY_RULE)",
                    r["verdict"] == "MATCH",
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case M", "M2-10 rc1=20", False, v_m)

    # Case K: san_reports != 0 -> MISMATCH
    c_dir = os.path.join(scratch, "case_K")
    setup_base_case_dirs(c_dir, prereg_rows)
    for pas in ("1", "2"):
        err_f = os.path.join(c_dir, f"pass{pas}", "M2-03-REP-INIT-01-F3", "stderr.txt")
        with open(err_f, "w") as fh:
            fh.write("==1234==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x1234\n")
    ok, v_k = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_k["M2-03-REP-INIT-01-F3"]
        record_case("Case K", "san_reports!=0 -> MISMATCH (ASan report detected)",
                    r["verdict"] == "MISMATCH" and "exp_san" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case K", "san_reports!=0", False, v_k)

    # Case P: sanitizer rc differs from san_ref -> MISMATCH
    c_dir = os.path.join(scratch, "case_P")
    setup_base_case_dirs(c_dir, prereg_rows)
    # In M2-03-REP-INIT-01-F3 (ref is M2-01-01-F3 rc1=20), set rc1=0
    for pas in ("1", "2"):
        p_f = os.path.join(c_dir, f"pass{pas}", "M2-03-REP-INIT-01-F3", "stdout.txt")
        with open(p_f, "w") as fh:
            fh.write("R6CALLS 1 0\nRC first 0\nR6CALLS 2 0\nRC retry 0\nR6CALLS 3 0\nS4FMM HITCOUNT 1\n")
    ok, v_p = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_p["M2-03-REP-INIT-01-F3"]
        record_case("Case P", "sanitizer rc 与 san_ref 不同 -> MISMATCH",
                    r["verdict"] == "MISMATCH" and "san_ref_rc1" in r["mismatches"],
                    f"verdict={r['verdict']}, mismatches={r['mismatches']}")
    else:
        record_case("Case P", "sanitizer rc 与 san_ref 不同", False, v_p)

    # Case Q: san_ref=NO_REF -> UNJUDGED_BY_DESIGN
    c_dir = os.path.join(scratch, "case_Q")
    setup_base_case_dirs(c_dir, prereg_rows)
    ok, v_q = run_pipeline(c_dir, PREREG_FILE)
    if ok:
        r = v_q["M2-03-G5-01-F3"]
        record_case("Case Q", "san_ref=NO_REF -> UNJUDGED_BY_DESIGN",
                    r["verdict"] == "UNJUDGED" and r["verdict_detail"] == "UNJUDGED_BY_DESIGN",
                    f"verdict={r['verdict']}, detail={r['verdict_detail']}")
    else:
        record_case("Case Q", "san_ref=NO_REF", False, v_q)

    # Case R: Constructed input where total points != 150 asserts exit failure
    c_dir = os.path.join(scratch, "case_R")
    setup_base_case_dirs(c_dir, prereg_rows)
    # Create prereg with 149 rows (remove M2-10-01-B)
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
                          "--out-summary", v_sum],
                         capture_output=True, text=True)
    record_case("Case R", "汇总合计!=150 构造输入断言失败退出 (Total!=150 exits non-zero)",
                r_v.returncode != 0 and "FATAL: Total points evaluated" in r_v.stderr,
                f"exit_code={r_v.returncode}, stderr={r_v.stderr.strip()[:60]}")

    # Output POSCTRL log
    lines = [
        "# POSCTRL_M2_R8_M2a4 -- Synthetic Positive Control Results",
        f"total_cases: {len(cases_results)}",
        f"passed_cases: {sum(1 for c in cases_results if c[2] == 'PASS')}",
        f"failed_cases: {sum(1 for c in cases_results if c[2] == 'FAIL')}",
        "\nCase\tDescription\tStatus\tDetail",
    ]
    for cid, desc, st, det in cases_results:
        lines.append(f"{cid}\t{desc}\t{st}\t{det}")

    with open(args.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    all_passed = all(c[2] == "PASS" for c in cases_results)
    print("\n" + "="*60)
    print(f"POSCTRL_M2_R8_M2a4: {len(cases_results)} cases, {sum(1 for c in cases_results if c[2] == 'PASS')} PASSED, {sum(1 for c in cases_results if c[2] == 'FAIL')} FAILED.")
    if not all_passed:
        sys.exit("Some positive control cases failed!")
    else:
        print("ALL POSITIVE CONTROLS PASSED.")


if __name__ == "__main__":
    main()
