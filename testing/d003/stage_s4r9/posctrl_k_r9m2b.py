#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# posctrl_k_r9m2b.py -- Positive control for K inheritance proof redo (Step S-D).
import argparse, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "testing", "d003", "stage_s4r9"))

from k_inherit_r9m2b import evaluate_group, parse_hits_exact

DEFAULT_EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b"))

# Synthetic GDB outputs
SYN_HIT3 = """
Breakpoint 1, S4_TEST_ALLOC_HOOK (id=21, size=48) at inject.cpp:538
#0  S4_TEST_ALLOC_HOOK (id=21, size=48) at inject.cpp:538
#1  0x00005555557dfe1a in Simulation_ComputeLayerModes (S=0x1, L=0x2) at S4/S4.cpp:2280
Breakpoint 1, S4_TEST_ALLOC_HOOK (id=22, size=11952) at inject.cpp:538
#0  S4_TEST_ALLOC_HOOK (id=22, size=11952) at inject.cpp:538
#1  0x00005555557e091a in Simulation_ComputeLayerModes (S=0x1, L=0x2) at S4/S4.cpp:2318
Breakpoint 1, S4_TEST_ALLOC_HOOK (id=21, size=48) at inject.cpp:538
#0  S4_TEST_ALLOC_HOOK (id=21, size=48) at inject.cpp:538
#1  0x00005555557dfe1a in Simulation_ComputeLayerModes (S=0x1, L=0x2) at S4/S4.cpp:2280
"""

SYN_HIT2 = """
Breakpoint 1, S4_TEST_ALLOC_HOOK (id=21, size=48) at inject.cpp:538
#0  S4_TEST_ALLOC_HOOK (id=21, size=48) at inject.cpp:538
#1  0x00005555557dfe3a in Simulation_ComputeLayerModes (S=0x1, L=0x2) at S4/S4.cpp:2293
Breakpoint 1, S4_TEST_ALLOC_HOOK (id=22, size=11952) at inject.cpp:538
#0  S4_TEST_ALLOC_HOOK (id=22, size=11952) at inject.cpp:538
#1  0x00005555557e093a in Simulation_ComputeLayerModes (S=0x1, L=0x2) at S4/S4.cpp:2331
"""

SYN_SIZE_DIFF_F4 = """
Breakpoint 1, S4_TEST_ALLOC_HOOK (id=21, size=96) at inject.cpp:538
#0  S4_TEST_ALLOC_HOOK (id=21, size=96) at inject.cpp:538
#1  0x00005555557dfe3a in Simulation_ComputeLayerModes (S=0x1, L=0x2) at S4/S4.cpp:2293
Breakpoint 1, S4_TEST_ALLOC_HOOK (id=22, size=11952) at inject.cpp:538
#0  S4_TEST_ALLOC_HOOK (id=22, size=11952) at inject.cpp:538
#1  0x00005555557e093a in Simulation_ComputeLayerModes (S=0x1, L=0x2) at S4/S4.cpp:2331
"""

SYN_NO_FRAME = """
Breakpoint 1, 0x00005555555592b0 in __wrap__Z9S4_mallocm ()
#0  0x00005555555592b0 in __wrap__Z9S4_mallocm ()
#1  0x0000555555572f92 in FMMGetEpsilon_ClosedForm ()
#2  0x000055555555bd28 in Simulation_ComputeLayerModes ()
"""

def main():
    parser = argparse.ArgumentParser(description="Positive control for K inheritance proof redo")
    parser.add_argument("--ev", default=DEFAULT_EV, help="Evidence directory")
    parser.add_argument("--out", default=None, help="Output TXT path")
    args = parser.parse_args()

    ev = os.path.realpath(args.ev)
    os.makedirs(ev, exist_ok=True)
    out_file = args.out or os.path.join(ev, "POSCTRL_K_R9M2b.txt")

    results = []
    all_pass = True

    # Case 1: Hit count mismatch (F3=3 hits, F4=2 hits)
    h3_c1 = parse_hits_exact(SYN_HIT3)
    h4_c1 = parse_hits_exact(SYN_HIT2)
    v1, r1, _ = evaluate_group(h3_c1, h4_c1)
    pass_c1 = (v1 == "K_DIVERGENT_R2" and "HIT_COUNT_MISMATCH" in r1)
    results.append(("CASE_1_HIT_COUNT_MISMATCH", "K_DIVERGENT_R2", v1, r1, "PASS" if pass_c1 else "FAIL"))
    if not pass_c1:
        all_pass = False

    # Case 2: Size mismatch (F3 size=48 vs F4 size=96 at call 1)
    # Parse 2 hits on F3
    h3_c2 = parse_hits_exact(SYN_HIT3)[:2]
    h4_c2 = parse_hits_exact(SYN_SIZE_DIFF_F4)
    v2, r2, _ = evaluate_group(h3_c2, h4_c2)
    pass_c2 = (v2 == "K_DIVERGENT_R2" and "SIZE_MISMATCH" in r2)
    results.append(("CASE_2_SIZE_MISMATCH", "K_DIVERGENT_R2", v2, r2, "PASS" if pass_c2 else "FAIL"))
    if not pass_c2:
        all_pass = False

    # Case 3: No sequence evidence (plain driver without debug symbols / frames)
    h3_c3 = parse_hits_exact(SYN_NO_FRAME)
    h4_c3 = parse_hits_exact(SYN_NO_FRAME)
    v3, r3, _ = evaluate_group(h3_c3, h4_c3)
    pass_c3 = (v3 == "NO_SEQ_EVIDENCE_R2")
    results.append(("CASE_3_NO_SEQ_EVIDENCE", "NO_SEQ_EVIDENCE_R2", v3, r3, "PASS" if pass_c3 else "FAIL"))
    if not pass_c3:
        all_pass = False

    # Case 4: All identical (F3 lines 2280/2318 map to F4 lines 2293/2331)
    h3_c4 = parse_hits_exact(SYN_HIT3)[:2]
    h4_c4 = parse_hits_exact(SYN_HIT2)
    v4, r4, _ = evaluate_group(h3_c4, h4_c4)
    pass_c4 = (v4 == "PASS_K_INHERITED_R2")
    results.append(("CASE_4_ALL_IDENTICAL", "PASS_K_INHERITED_R2", v4, r4, "PASS" if pass_c4 else "FAIL"))
    if not pass_c4:
        all_pass = False

    # Write report
    with open(out_file, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_K_R9M2b.txt -- Positive control report for K inheritance redo (U300)\n\n")
        for name, exp, act, reason, status in results:
            fh.write(f"CASE: {name}\n")
            fh.write(f"  Expected: {exp}\n")
            fh.write(f"  Actual:   {act} ({reason})\n")
            fh.write(f"  Status:   {status}\n\n")
        fh.write(f"OVERALL_RESULT: {'ALL_PASS' if all_pass else 'SOME_FAILED'}\n")

    print(f"Positive control completed. Output written to {out_file}")
    for name, exp, act, reason, status in results:
        print(f"[{status}] {name}: exp={exp} act={act} ({reason})")

    if not all_pass:
        sys.exit(1)

if __name__ == "__main__":
    main()
