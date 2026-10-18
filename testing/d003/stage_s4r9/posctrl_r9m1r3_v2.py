#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# posctrl_r9m1r3_v2.py -- Positive control tests calling formal verdict and compare scripts (Step S-F, Rule U316). New file per Rule 3.
import argparse, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))
TMP = os.path.join(EV, "tmp", "posctrl")
os.makedirs(TMP, exist_ok=True)

OUT_FILE = os.path.join(EV, "POSCTRL_M1_R9M1R3.txt")

def main():
    parser = argparse.ArgumentParser(description="Run positive control tests for r9m1r3")
    parser.add_argument("--out", default=OUT_FILE)
    parser.add_argument("--compare-script", default=os.path.join(REPO, "testing/d003/stage_s4r9/compare_f3_f4_r9m1r3.py"))
    parser.add_argument("--verdict-script", default=os.path.join(REPO, "testing/d003/stage_s4r9/verdict_r9m1r3.py"))
    parser.add_argument("--prereg", default=os.path.join(EV, "PREREG_M1_F4_R9M1R3.tsv"))
    args = parser.parse_args()

    results = []
    all_ok = True

    # Build clean baseline F4 facts (using R2 formal facts as source, but updating G2c_control per Rule U319)
    src_r2_facts = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r2/runs/formal_R2/FORMAL_FACTS_M1_F4_R9M1R2_pass1.tsv")
    lines = open(src_r2_facts, encoding="utf-8").read().splitlines()
    h = lines[1].split("\t")

    clean_f4_lines = [lines[0], lines[1]]
    for l in lines[2:]:
        parts = l.split("\t")
        if parts[1] == "G2c_control":
            parts[7] = "-"  # rc
            parts[8] = "-"  # rc1
            parts[9] = "-"  # rc2
            parts[10] = "-" # rc3
            parts[11] = "-" # hit
            parts[12] = "NOT_RUN_REGISTRY_ERROR"
        clean_f4_lines.append("\t".join(parts))

    base_f4_path = os.path.join(TMP, "base_f4_facts.tsv")
    with open(base_f4_path, "w", encoding="utf-8") as f:
        f.write("\n".join(clean_f4_lines) + "\n")

    # -------------------------------------------------------------
    # Case 1: F3 frozen facts as input to compare script -> DIFFS == 0
    # -------------------------------------------------------------
    print("=== Positive Control Case 1: F3 frozen facts comparison ===")
    c1_out = os.path.join(TMP, "posctrl_c1_compare.tsv")
    cmd_c1 = [
        "python3", "-I", "-B", args.compare_script,
        "--facts", base_f4_path,
        "--out", c1_out
    ]
    p_c1 = subprocess.run(cmd_c1, cwd=REPO, capture_output=True, text=True)
    assert p_c1.returncode == 0, f"Case 1 compare failed:\n{p_c1.stderr}"

    diff_lines_c1 = 0
    with open(c1_out, encoding="utf-8") as f:
        for l in f:
            if "\tDIFFERENT\t" in l:
                diff_lines_c1 += 1

    case1_pass = (diff_lines_c1 == 0)
    if not case1_pass: all_ok = False
    print(f"Case 1 result: DIFFS = {diff_lines_c1} (expected 0) -> {'PASS' if case1_pass else 'FAIL'}")
    results.append(f"Case 1: F3 frozen facts comparison -> DIFFS = {diff_lines_c1} (expected 0) -> {'PASS' if case1_pass else 'FAIL'}")

    # -------------------------------------------------------------
    # Case 2: Tampered replica -> EXACTLY 5 MISMATCH detections
    # -------------------------------------------------------------
    print("\n=== Positive Control Case 2: Tampered replica (5 injected faults) ===")
    rc1_idx = h.index("rc1")
    rc2_idx = h.index("rc2")
    i1_idx = h.index("I1")
    i3_idx = h.index("I3")

    tampered_lines = [lines[0], lines[1]]
    tampered_pts = []
    for l in clean_f4_lines[2:]:
        parts = l.split("\t")
        sec, grp, pid = parts[0], parts[1], parts[2]
        
        # 1. M1b G2b: rc1 from 20 to 0
        if sec == "M1b" and grp == "G2b" and pid == "M-once-fft-plan-3-F4":
            parts[rc1_idx] = "0"
            tampered_pts.append(f"{sec} {grp} {pid} (rc1: 20 -> 0)")
        # 2. M1c G5: I1 from HOLD to 1
        elif sec == "M1c" and grp == "G5" and pid == "M-once-closed1d-malloc-1-F4":
            parts[i1_idx] = "1"
            tampered_pts.append(f"{sec} {grp} {pid} (I1: HOLD -> 1)")
        # 3. M1b G1: rc2 from 20 to 0 (contract requires rc2 check)
        elif sec == "M1b" and grp == "G1" and pid == "M-twice-closed1d-malloc-2-F4":
            parts[rc2_idx] = "0"
            tampered_pts.append(f"{sec} {grp} {pid} (rc2: 20 -> 0)")
        # 4. M1c G6: I3 from HOLD to 1
        elif sec == "M1c" and grp == "G6" and pid == "R4-ACF1-F-F4":
            parts[i3_idx] = "1"
            tampered_pts.append(f"{sec} {grp} {pid} (I3: HOLD -> 1)")
        # 5. M1b G2c_control: change "-" to "0"
        elif sec == "M1b" and grp == "G2c_control" and pid == "addf-F-ctrl-F4":
            parts[rc1_idx] = "0"
            tampered_pts.append(f"{sec} {grp} {pid} (rc1: '-' -> 0)")
        
        tampered_lines.append("\t".join(parts))

    assert len(tampered_pts) == 5, f"Expected 5 tampered points, got {len(tampered_pts)}: {tampered_pts}"

    t1_path = os.path.join(TMP, "posctrl_tampered_p1.tsv")
    t2_path = os.path.join(TMP, "posctrl_tampered_p2.tsv")
    with open(t1_path, "w", encoding="utf-8") as f: f.write("\n".join(tampered_lines) + "\n")
    with open(t2_path, "w", encoding="utf-8") as f: f.write("\n".join(tampered_lines) + "\n")

    c2_verdict_out = os.path.join(TMP, "posctrl_c2_verdict.tsv")
    cmd_c2 = [
        "python3", "-I", "-B", args.verdict_script,
        "--prereg", args.prereg,
        "--pass1", t1_path,
        "--pass2", t2_path,
        "--out", c2_verdict_out,
        "--out-agg", os.path.join(TMP, "posctrl_c2_agg.tsv")
    ]
    p_c2 = subprocess.run(cmd_c2, cwd=REPO, capture_output=True, text=True)
    assert p_c2.returncode == 0, f"Case 2 verdict failed:\n{p_c2.stderr}"

    mismatches_c2 = []
    with open(c2_verdict_out, encoding="utf-8") as f:
        for l in f:
            if "\tMISMATCH\t" in l:
                mismatches_c2.append(l.strip().split("\t"))

    case2_pass = (len(mismatches_c2) == 5)
    if not case2_pass: all_ok = False
    print(f"Case 2 result: MISMATCH count = {len(mismatches_c2)} (expected 5) -> {'PASS' if case2_pass else 'FAIL'}")
    for m in mismatches_c2:
        print(f"  Detected: {m[0]} {m[1]} {m[2]} -> {m[17]} ({m[18]})")
    results.append(f"Case 2: Tampered replica -> MISMATCH count = {len(mismatches_c2)} (expected exactly 5) -> {'PASS' if case2_pass else 'FAIL'}")

    # -------------------------------------------------------------
    # Case 3: Old prereg 3894d899 vs facts -> detect 22 G2b rows
    # -------------------------------------------------------------
    print("\n=== Positive Control Case 3: Old prereg (3894d899) vs formal facts ===")
    old_prereg_data = subprocess.check_output(
        ["git", "show", "00490a7:checkpoints/p05/registries/s4r9/M1/PREREG_M1_F4_R9M1.tsv"],
        cwd=REPO
    )
    old_prereg_path = os.path.join(TMP, "PREREG_M1_F4_00490a7.tsv")
    with open(old_prereg_path, "wb") as f:
        f.write(old_prereg_data)

    c3_verdict_out = os.path.join(TMP, "posctrl_c3_verdict.tsv")
    cmd_c3 = [
        "python3", "-I", "-B", args.verdict_script,
        "--prereg", old_prereg_path,
        "--pass1", base_f4_path,
        "--pass2", base_f4_path,
        "--out", c3_verdict_out,
        "--out-agg", os.path.join(TMP, "posctrl_c3_agg.tsv")
    ]
    p_c3 = subprocess.run(cmd_c3, cwd=REPO, capture_output=True, text=True)
    assert p_c3.returncode == 0, f"Case 3 verdict failed:\n{p_c3.stderr}"

    g2b_mismatches = []
    other_mismatches = []
    with open(c3_verdict_out, encoding="utf-8") as f:
        for l in f:
            if "\tMISMATCH\t" in l:
                parts = l.strip().split("\t")
                if parts[1] == "G2b":
                    g2b_mismatches.append(parts)
                else:
                    other_mismatches.append(parts)

    case3_pass = (len(g2b_mismatches) == 22 and len(other_mismatches) == 0)
    if not case3_pass: all_ok = False
    print(f"Case 3 result: G2b MISMATCH = {len(g2b_mismatches)} (expected 22), Other MISMATCH = {len(other_mismatches)} (expected 0) -> {'PASS' if case3_pass else 'FAIL'}")
    results.append(f"Case 3: Old prereg 3894d899 comparison -> G2b MISMATCH = {len(g2b_mismatches)} (expected 22), Other = {len(other_mismatches)} -> {'PASS' if case3_pass else 'FAIL'}")

    # Write POSCTRL summary
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("# POSCTRL_M1_R9M1R3.txt -- Positive control verification report (Step S-F, Rule U316)\n\n")
        f.write(f"ALL_POSITIVE_CONTROLS_PASSED: {all_ok}\n\n")
        for r in results:
            f.write("- " + r + "\n")

    print(f"\nWrote {args.out}. ALL CONTROLS PASSED: {all_ok}.")
    if not all_ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
