#!/usr/bin/env python3
# posctrl_m2_r8m2a2.py -- P05-S4 R8 M2a2 section 4.7: positive controls of verdict_m2_r8m2a2.py on SYNTHETIC data.
# Every case builds its own synthetic prereg and synthetic RESULTS under $EV/tmp/posctrl/<case>/ and calls the FORMAL
# verdict script through subprocess (python3 -I -B).  No S4 code is run.  The expected counts are fixed here before the run.
#   A: all observations equal the expectation                       -> MISMATCH 0
#   B: one rc1 observation changed (point P2)                       -> MISMATCH 1, P2 listed in the verdict table
#   C: pass1 and pass2 disagree on one point (rc2 of P1)            -> FLAKY 1
#   D: NZ expectation (P3): observation rc1=0 -> MISMATCH 1 ; observation rc1=20 -> MISMATCH 0
#   E: one exp_I1 observation changed (point P4)                    -> MISMATCH 1
# Output: $EV/POSCTRL_M2_R8_M2a2.txt, last line POSCTRL=PASS or POSCTRL=FAIL.  Refuses to overwrite (U17).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2a2 -- python3 -I -B testing/d003/stage_s4/posctrl_m2_r8m2a2.py
import os
import re
import subprocess
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
VERDICT = os.path.join(REPO, "testing", "d003", "stage_s4", "verdict_m2_r8m2a2.py")
# R1 (first run, FAIL: P1 expected class and B single-pass override) is kept as POSCTRL_M2_R8_M2a2.txt.
OUT = os.path.join(EV, "POSCTRL_M2_R8_M2a2_R2.txt")
BASE = os.path.join(EV, "tmp", "posctrl")
REL_BASE = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2a2", "tmp", "posctrl")

PREREG_HEAD = ["point_id", "item", "tree", "exp_rc1", "exp_rc2", "exp_signal", "exp_hit", "exp_class",
               "exp_I1", "exp_I2", "exp_I3", "exp_I4", "exp_I5", "exp_I6", "exp_I7", "exp_san"]
RESULT_HEAD = ["point_id", "tree", "rc1", "rc2", "rc", "signal", "hit", "I1", "I2", "I3", "I4", "I5", "I6", "I7", "san_reports", "class"]

# point: (exp_rc1, exp_rc2, exp_class, exp_I1, exp_hit, observed rc1, observed rc2, observed hit, observed I1)
# R2 correction (see the header of the output): P1 has rc1=0, so judge_d003.classify gives SILENT_SWALLOW (the first call
# decides the class; rc2 does not), so its expected class is SILENT_SWALLOW.  The R1 run wrote REPORTED_FAILURE here.
POINTS = {
    "P1": ("0", "20", "SILENT_SWALLOW", "-", "1", "0", "20", "1", "-"),
    "P2": ("0", "0", "CONTROL_OK", "-", "0", "0", "0", "0", "-"),
    "P3": ("NZ", "0", "REPORTED_FAILURE", "-", "1", "20", "0", "1", "-"),
    "P4": ("20", "0", "REPORTED_FAILURE", "1", "1", "20", "0", "1", "1"),
}


def write_prereg(path):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\t".join(PREREG_HEAD) + "\n")
        for pid, v in POINTS.items():
            exp_rc1, exp_rc2, exp_class, exp_i1, exp_hit = v[0], v[1], v[2], v[3], v[4]
            row = [pid, "POSCTRL", "F3", exp_rc1, exp_rc2, "-", exp_hit, exp_class,
                   exp_i1, "-", "-", "-", "-", "-", "-", "-"]
            f.write("\t".join(row) + "\n")


def write_results(path, pass_no, overrides=None):
    overrides = overrides or {}
    with open(path, "w", encoding="utf-8") as f:
        f.write("\t".join(RESULT_HEAD) + "\n")
        for pid, v in POINTS.items():
            obs_rc1, obs_rc2, obs_hit, obs_i1 = v[5], v[6], v[7], v[8]
            if (pid, "rc1") in overrides:
                obs_rc1 = overrides[(pid, "rc1")]
            if (pid, "I1") in overrides:
                obs_i1 = overrides[(pid, "I1")]
            if (pid, "rc2_pass%d" % pass_no) in overrides:
                obs_rc2 = overrides[(pid, "rc2_pass%d" % pass_no)]
            rc = obs_rc1 if obs_rc1 != "0" else obs_rc2
            row = [pid, "F3", obs_rc1, obs_rc2, rc, "-", obs_hit, obs_i1, "-", "-", "-", "-", "-", "-", "-", "-", "-"]
            f.write("\t".join(row) + "\n")


def run_verdict(case, out_prefix):
    res_rel = os.path.join(REL_BASE, case)
    pre_rel = os.path.join(REL_BASE, case, "PREREG_SYN.tsv")
    r = subprocess.run([sys.executable, "-I", "-B", VERDICT, res_rel, pre_rel, out_prefix],
                       cwd=REPO, capture_output=True, text=True)
    return r.returncode, r.stdout.strip(), r.stderr.strip()


def counts_from_summary(out_prefix):
    p = os.path.join(EV, out_prefix + "_SUMMARY.txt")
    with open(p, encoding="utf-8") as f:
        first = f.readline()
    m = re.search(r"MISMATCH=(\d+) FLAKY=(\d+) MISSING=(\d+)", first)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else None


def verdict_rows(out_prefix):
    p = os.path.join(EV, out_prefix + "_VERDICT.tsv")
    rows = {}
    with open(p, encoding="utf-8") as f:
        next(f)
        for line in f:
            parts = line.rstrip("\n").split("\t")
            rows[parts[0]] = parts[1:]
    return rows


def main():
    if os.path.exists(OUT):
        print("posctrl_m2_r8m2a2: REFUSED exists (U17): %s" % OUT)
        return 2
    cases = [
        # name, expected (mismatch, flaky), overrides for pass1, pass2, description
        ("A", (0, 0, 0), {}, {}, "all observations equal the expectation"),
        ("B", (1, 0, 0), {("P2", "rc1"): "20"}, {("P2", "rc1"): "20"}, "P2 rc1 changed to 20 in both passes"),
        ("C", (0, 1, 0), {}, {("P1", "rc2_pass2"): "0"}, "P1 rc2 differs between pass1 and pass2"),
        ("D0", (1, 0, 0), {("P3", "rc1"): "0"}, {("P3", "rc1"): "0"}, "NZ expectation with observed rc1=0 (both passes)"),
        ("D20", (0, 0, 0), {}, {}, "NZ expectation with observed rc1=20 (P3 as prepared)"),
        ("E", (1, 0, 0), {("P4", "I1"): "0"}, {("P4", "I1"): "0"}, "exp_I1 expectation 1, observed I1 changed to 0"),
    ]
    os.makedirs(BASE, exist_ok=True)
    lines = ["# POSCTRL_M2_R8_M2a2 -- positive controls of verdict_m2_r8m2a2.py on synthetic data (no S4 run)",
             "# columns: case	description	expect_mismatch	expect_flaky	obs_mismatch	obs_flaky	obs_missing	point_P2_verdict	point_P3_verdict	point_P4_verdict	rc	result"]
    all_ok = True
    for name, exp, ov1, ov2, desc in cases:
        d = os.path.join(BASE, name)
        os.makedirs(d, exist_ok=True)
        pre = os.path.join(d, "PREREG_SYN.tsv")
        write_prereg(pre)
        write_results(os.path.join(d, "RESULTS_pass1.tsv"), 1, ov1)
        write_results(os.path.join(d, "RESULTS_pass2.tsv"), 2, ov2)
        prefix = "VERDICT_M2_R8_M2a2_POSCTRL_%s_R2" % name
        rc, out, err = run_verdict(name, prefix)
        counts = counts_from_summary(prefix) if rc == 0 else None
        rows = verdict_rows(prefix) if rc == 0 else {}
        ok = (counts is not None and counts == exp)
        if name == "B":
            ok = ok and ("P2" in rows and rows["P2"][0] == "MISMATCH")
        if name == "C":
            ok = ok and ("P1" in rows and rows["P1"][0] == "FLAKY")
        # D0: the mismatch must come from the NZ expectation (exp_rc1), not from another field of P3
        if name == "D0":
            ok = ok and ("P3" in rows and "exp_rc1" in rows["P3"][1])
        # D20: the NZ expectation must be satisfied by observed rc1=20, so P3 is MATCH or only has a non-NZ field
        if name == "D20":
            ok = ok and ("P3" in rows and "exp_rc1" not in rows["P3"][1])
        # E: the mismatch must come from exp_I1 on P4
        if name == "E":
            ok = ok and ("P4" in rows and "exp_I1" in rows["P4"][1])
        p2v = rows.get("P2", ["-"])[0]
        p3v = rows.get("P3", ["-"])[0]
        p4v = rows.get("P4", ["-"])[0]
        if counts is None:
            counts = (-1, -1, -1)
        all_ok = all_ok and ok
        lines.append("\t".join([name, desc, str(exp[0]), str(exp[1]), str(counts[0]), str(counts[1]), str(counts[2]),
                                p2v, p3v, p4v, str(rc), "PASS" if ok else "FAIL"]))
    lines.append("POSCTRL_CASES=%d" % len(cases))
    lines.append("POSCTRL=%s" % ("PASS" if all_ok else "FAIL"))
    with open(OUT, "x", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[-2:]))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
