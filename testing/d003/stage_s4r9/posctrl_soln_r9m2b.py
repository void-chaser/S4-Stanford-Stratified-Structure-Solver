#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# posctrl_soln_r9m2b.py -- Positive control for SOLN supplementary judge (Step S-E).
import argparse, copy, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "testing", "d003", "stage_s4r9"))

from soln_supp_r9m2b import judge_soln_row, load_facts, load_tsv

DEFAULT_EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b"))

def main():
    parser = argparse.ArgumentParser(description="Positive control for SOLN supplementary judge")
    parser.add_argument("--ev", default=DEFAULT_EV, help="Evidence directory")
    parser.add_argument("--out", default=None, help="Output TXT path")
    args = parser.parse_args()

    ev = os.path.realpath(args.ev)
    os.makedirs(ev, exist_ok=True)
    out_file = args.out or os.path.join(ev, "POSCTRL_SOLN_R9M2b.txt")

    prereg_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M0", "PREREG_SOLN_F4_R9.tsv")
    facts1_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M2", "FACTS_pass1_R9.tsv")
    facts2_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M2", "FACTS_pass2_R9.tsv")

    prereg_rows = load_tsv(prereg_path)
    facts1_orig = load_facts(facts1_path)
    facts2_orig = load_facts(facts2_path)

    results = []
    all_pass = True

    # Case 1: Untampered real rows -> all 18 must be MATCH
    case1_matches = 0
    for r in prereg_rows:
        i6_p1, i6_p2, san_p1, san_p2, v, det = judge_soln_row(r, facts1_orig, facts2_orig)
        if v == "MATCH":
            case1_matches += 1
    c1_ok = (case1_matches == 18)
    results.append(("CASE_1_UNTAMPERED_MATCH", "18/18 MATCH", f"{case1_matches}/18 MATCH", "PASS" if c1_ok else "FAIL"))
    if not c1_ok:
        all_pass = False

    # Case 2: Tamper call2 sha on pass 1 for SOLN-1763-closed2d-ng1-F4-dbg -> VIOLATED & MISMATCH
    target_row = next(r for r in prereg_rows if r["point_id"] == "SOLN-1763-closed2d-ng1-F4-dbg")
    f1_tamper = copy.deepcopy(facts1_orig)
    f1_tamper["SOLN-1763-closed2d-ng1-F4-dbg"]["call2_sha256"] = "tampered_call2_sha_p1"
    i6_p1, i6_p2, san_p1, san_p2, v, det = judge_soln_row(target_row, f1_tamper, facts2_orig)
    c2_ok = (i6_p1 == "VIOLATED" and v == "MISMATCH")
    results.append(("CASE_2_TAMPER_CALL2_SHA_P1", "i6_p1=VIOLATED,verdict=MISMATCH", f"i6_p1={i6_p1},verdict={v}", "PASS" if c2_ok else "FAIL"))
    if not c2_ok:
        all_pass = False

    # Case 3: Tamper call2 sha on pass 2 for SOLN-1763-closed2d-ng1-F4-dbg -> VIOLATED & MISMATCH
    f2_tamper = copy.deepcopy(facts2_orig)
    f2_tamper["SOLN-1763-closed2d-ng1-F4-dbg"]["call2_sha256"] = "tampered_call2_sha_p2"
    i6_p1, i6_p2, san_p1, san_p2, v, det = judge_soln_row(target_row, facts1_orig, f2_tamper)
    c3_ok = (i6_p2 == "VIOLATED" and v == "MISMATCH")
    results.append(("CASE_3_TAMPER_CALL2_SHA_P2", "i6_p2=VIOLATED,verdict=MISMATCH", f"i6_p2={i6_p2},verdict={v}", "PASS" if c3_ok else "FAIL"))
    if not c3_ok:
        all_pass = False

    # Case 4: Tamper san_reports to 1 for SOLN-1763-closed2d-ng1-F4-san (exp_san=0) -> san_p1=FAIL & MISMATCH
    target_san = next(r for r in prereg_rows if r["point_id"] == "SOLN-1763-closed2d-ng1-F4-san")
    f1_san_tamper = copy.deepcopy(facts1_orig)
    f1_san_tamper["SOLN-1763-closed2d-ng1-F4-san"]["san_reports"] = "1"
    i6_p1, i6_p2, san_p1, san_p2, v, det = judge_soln_row(target_san, f1_san_tamper, facts2_orig)
    c4_ok = (san_p1 == "FAIL" and v == "MISMATCH")
    results.append(("CASE_4_TAMPER_SAN_REPORTS_P1", "san_p1=FAIL,verdict=MISMATCH", f"san_p1={san_p1},verdict={v}", "PASS" if c4_ok else "FAIL"))
    if not c4_ok:
        all_pass = False

    # Case 5: Tamper san_crash to 1 for SOLN-1763-closed2d-ng1-F4-san (exp 0) -> san_p1=FAIL & MISMATCH
    f1_crash_tamper = copy.deepcopy(facts1_orig)
    f1_crash_tamper["SOLN-1763-closed2d-ng1-F4-san"]["san_crash"] = "1"
    i6_p1, i6_p2, san_p1, san_p2, v, det = judge_soln_row(target_san, f1_crash_tamper, facts2_orig)
    c5_ok = (san_p1 == "FAIL" and v == "MISMATCH")
    results.append(("CASE_5_TAMPER_SAN_CRASH_P1", "san_p1=FAIL,verdict=MISMATCH", f"san_p1={san_p1},verdict={v}", "PASS" if c5_ok else "FAIL"))
    if not c5_ok:
        all_pass = False

    # Write report
    with open(out_file, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_SOLN_R9M2b.txt -- Positive control report for SOLN supplementary judge (Step S-E)\n\n")
        for name, exp, act, status in results:
            fh.write(f"CASE: {name}\n")
            fh.write(f"  Expected: {exp}\n")
            fh.write(f"  Actual:   {act}\n")
            fh.write(f"  Status:   {status}\n\n")
        fh.write(f"OVERALL_RESULT: {'ALL_PASS' if all_pass else 'SOME_FAILED'}\n")

    print(f"Positive control completed. Output written to {out_file}")
    for name, exp, act, status in results:
        print(f"[{status}] {name}: exp={exp} act={act}")

    if not all_pass:
        sys.exit(1)

if __name__ == "__main__":
    main()
