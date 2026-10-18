#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# posctrl_r9m1r2_R2.py -- Positive control tests calling formal verdict and compare scripts (Step S-F, Rule U316). New file.
import argparse, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
TMP = os.path.join(EV, "tmp")
os.makedirs(TMP, exist_ok=True)

OUT_FILE = os.path.join(EV, "POSCTRL_M1_R9M1R2.txt")

def main():
    parser = argparse.ArgumentParser(description="Run positive control tests")
    parser.add_argument("--out", default=OUT_FILE)
    args = parser.parse_args()

    results = []
    all_ok = True

    # -------------------------------------------------------------
    # Case 1: F3 frozen facts as input to compare script -> DIFFS == 0
    # -------------------------------------------------------------
    print("=== Positive Control Case 1: F3 frozen facts comparison ===")
    p1_orig = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/runs/formal/FORMAL_FACTS_M1_F4_R9M1_pass1.tsv")
    c1_out = os.path.join(TMP, "posctrl_c1_compare.tsv")
    cmd_c1 = [
        "python3", "-I", "-B", "testing/d003/stage_s4r9/compare_f3_f4_r9m1r2_R2.py",
        "--facts", p1_orig,
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
    # Case 2: Tampered replica -> EXACTLY 3 MISMATCH detections
    # -------------------------------------------------------------
    print("\n=== Positive Control Case 2: Tampered replica (3 injected faults) ===")
    with open(p1_orig, encoding="utf-8") as f:
        lines1 = f.read().splitlines()

    h = lines1[1].split("\t")
    rc1_idx = h.index("rc1")
    rc2_idx = h.index("rc2")
    i1_idx = h.index("I1")

    tampered_lines = []
    tampered_pts = []
    for l in lines1:
        if l.startswith("#") or l.startswith("section\t"):
            tampered_lines.append(l)
            continue
        parts = l.split("\t")
        sec, grp, pid = parts[0], parts[1], parts[2]
        if sec == "M1b" and grp == "G2b" and pid == "M-once-fft-plan-3-F4":
            parts[rc1_idx] = "0"
            tampered_pts.append(f"{sec} {grp} {pid} (rc1: 20 -> 0)")
        elif sec == "M1c" and grp == "G5" and pid == "M-once-closed1d-malloc-1-F4":
            parts[i1_idx] = "1"
            tampered_pts.append(f"{sec} {grp} {pid} (I1: HOLD -> 1)")
        elif sec == "M1b" and grp == "G1" and pid == "M-twice-closed1d-malloc-2-F4":
            parts[rc2_idx] = "0"
            tampered_pts.append(f"{sec} {grp} {pid} (rc2: 20 -> 0)")
        tampered_lines.append("\t".join(parts))

    assert len(tampered_pts) == 3, f"Expected 3 tampered points, got {len(tampered_pts)}: {tampered_pts}"

    t1_path = os.path.join(TMP, "posctrl_tampered_p1.tsv")
    t2_path = os.path.join(TMP, "posctrl_tampered_p2.tsv")
    with open(t1_path, "w", encoding="utf-8") as f: f.write("\n".join(tampered_lines) + "\n")
    with open(t2_path, "w", encoding="utf-8") as f: f.write("\n".join(tampered_lines) + "\n")

    c2_verdict_out = os.path.join(TMP, "posctrl_c2_verdict.tsv")
    cmd_c2 = [
        "python3", "-I", "-B", "testing/d003/stage_s4r9/verdict_r9m1r2.py",
        "--prereg", os.path.join(EV, "PREREG_M1_F4_R9M1R2.tsv"),
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

    case2_pass = (len(mismatches_c2) == 3)
    if not case2_pass: all_ok = False
    print(f"Case 2 result: MISMATCH count = {len(mismatches_c2)} (expected 3) -> {'PASS' if case2_pass else 'FAIL'}")
    for m in mismatches_c2:
        print(f"  Detected: {m[0]} {m[1]} {m[2]} -> {m[17]} ({m[18]})")
    results.append(f"Case 2: Tampered replica -> MISMATCH count = {len(mismatches_c2)} (expected exactly 3) -> {'PASS' if case2_pass else 'FAIL'}")

    # -------------------------------------------------------------
    # Case 3: Old prereg (00490a7) vs facts -> detect F-1 G2b 22 rows
    # -------------------------------------------------------------
    print("\n=== Positive Control Case 3: Old prereg (3894d899) vs formal facts ===")
    old_prereg = os.path.join(EV, "forensic", "PREREG_M1_F4_00490a7.tsv")
    p2_orig = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1/runs/formal/FORMAL_FACTS_M1_F4_R9M1_pass2.tsv")
    c3_verdict_out = os.path.join(TMP, "posctrl_c3_verdict.tsv")
    cmd_c3 = [
        "python3", "-I", "-B", "testing/d003/stage_s4r9/verdict_r9m1r2.py",
        "--prereg", old_prereg,
        "--pass1", p1_orig,
        "--pass2", p2_orig,
        "--out", c3_verdict_out,
        "--out-agg", os.path.join(TMP, "posctrl_c3_agg.tsv")
    ]
    p_c3 = subprocess.run(cmd_c3, cwd=REPO, capture_output=True, text=True)
    assert p_c3.returncode == 0, f"Case 3 verdict failed:\n{p_c3.stderr}"

    mismatches_c3 = []
    with open(c3_verdict_out, encoding="utf-8") as f:
        for l in f:
            if "\tMISMATCH\t" in l:
                mismatches_c3.append(l.strip().split("\t"))

    case3_pass = (len(mismatches_c3) == 22 and all(m[1] == "G2b" for m in mismatches_c3))
    if not case3_pass: all_ok = False
    print(f"Case 3 result: MISMATCH count = {len(mismatches_c3)} in G2b (expected 22) -> {'PASS' if case3_pass else 'FAIL'}")
    results.append(f"Case 3: Old prereg vs formal facts -> detected {len(mismatches_c3)} G2b MISMATCH rows (expected 22) -> {'PASS' if case3_pass else 'FAIL'}")

    report_text = "# POSCTRL_M1_R9M1R2.txt -- Positive control test report for P05-S4 R9 M1R2 (Rule U316)\n\n" + "\n".join(results) + "\n\nOVERALL: " + ("PASS" if all_ok else "FAIL") + "\n"
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"\nWrote {args.out}. Overall: {'PASS' if all_ok else 'FAIL'}")
    if not all_ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
