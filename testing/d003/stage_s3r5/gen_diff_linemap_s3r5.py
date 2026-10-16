#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gen_diff_linemap_s3r5.py -- Generate DIFF_F3_F4_S3R5.txt and LINEMAP_F3_F4_S3R5.tsv for P05-S3R5 (U289).
import os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s3r5")
EV = os.path.join(REPO, EV_REL)
DIFF_OUT = os.path.join(EV, "DIFF_F3_F4_S3R5.txt")
LINEMAP_OUT = os.path.join(EV, "LINEMAP_F3_F4_S3R5.tsv")

F3_REV = "8d8202a"
F4_REV = "05097a7"
F3_TREE = "6cff923a02baf19e01966b2339755cbf3a5deeef"
F4_TREE = "589e15eb11fcb04e031b524f25a443e7921946cf"

def main():
    os.makedirs(EV, exist_ok=True)
    # 1. Full diff S4/
    diff_text = subprocess.check_output(["git", "diff", F3_REV, F4_REV, "--", "S4/"], cwd=REPO, text=True)
    stat_text = subprocess.check_output(["git", "diff", "--stat", F3_REV, F4_REV, "--", "S4/"], cwd=REPO, text=True)
    with open(DIFF_OUT, 'w', encoding='utf-8') as fh:
        fh.write("# DIFF_F3_F4_S3R5.txt -- S4/ diff between F3 (%s) and F4 (%s)\n" % (F3_REV, F4_REV))
        fh.write("# F3 S4 tree: %s\n# F4 S4 tree: %s\n" % (F3_TREE, F4_TREE))
        fh.write("# git diff --stat:\n%s\n" % stat_text)
        fh.write(diff_text)
    print("Wrote %s" % DIFF_OUT)

    # 2. Line map
    # Check that diff is strictly in S4/S4.cpp:1760-1774
    diff_files = subprocess.check_output(["git", "diff", "--name-only", F3_REV, F4_REV, "--", "S4/"], cwd=REPO, text=True).strip().split()
    if diff_files != ["S4/S4.cpp"]:
        raise SystemExit("HARD STOP: diff modified files != [S4/S4.cpp]: %s" % diff_files)

    rows = [
        ("site_id", "file", "F3_line", "F4_line", "offset", "status", "function", "F3_text", "note"),
        ("InitSolution_entry", "S4/S4.cpp", "1738", "1738", "0", "SAME_LINE", "Simulation_InitSolution", "int Simulation_InitSolution(S4_Simulation *S){", "function entry"),
        ("destroy_old_sol", "S4/S4.cpp", "1760", "1760", "0", "SAME_LINE", "Simulation_InitSolution", "if(NULL != S->solution){ Simulation_DestroySolution(S); }", "destroy old solution if exists"),
        ("alloc_sol_struct", "S4/S4.cpp", "1763", "1763", "0", "MODIFIED_BY_FIX", "Simulation_InitSolution", "S->solution = (Solution_*)malloc(sizeof(Solution_));", "F4: Solution_ *sol = ... with immediate NULL check"),
        ("alloc_sol_ab", "S4/S4.cpp", "1764", "1771", "+7", "MODIFIED_BY_FIX", "Simulation_InitSolution", "S->solution->ab = ... S4_malloc(...)", "F4: sol->ab = ... S4_malloc(...)"),
        ("alloc_sol_solved", "S4/S4.cpp", "1765", "1772", "+7", "MODIFIED_BY_FIX", "Simulation_InitSolution", "S->solution->solved = (int*)malloc(...)", "F4: sol->solved = (int*)malloc(...)"),
        ("null_check_cleanup", "S4/S4.cpp", "1766", "1773", "+7", "MODIFIED_BY_FIX", "Simulation_InitSolution", "if(NULL == S->solution || ...)", "F4: if(NULL == sol->ab || NULL == sol->solved) with S4_free/free"),
        ("memset_solved", "S4/S4.cpp", "1773", "1785", "+12", "MODIFIED_BY_FIX", "Simulation_InitSolution", "memset(S->solution->solved, 0, ...)", "F4: memset(sol->solved, 0, ...) and S->solution = sol"),
        ("trace_g_vectors", "S4/S4.cpp", "1775", "1788", "+13", "SHIFTED", "Simulation_InitSolution", "S4_TRACE(\"I  Simulation_InitSolution G:...\")", "post-fix trace, first line after fix section"),
        ("caller_GetLayerSolution_guard", "S4/S4.cpp", "1802", "1815", "+13", "SHIFTED", "Simulation_GetLayerSolution", "if(NULL == S->solution){", "caller 1 guard check"),
        ("caller_GetLayerSolution_call", "S4/S4.cpp", "1803", "1816", "+13", "SHIFTED", "Simulation_GetLayerSolution", "error = Simulation_InitSolution(S);", "caller 1 invocation"),
        ("caller_GetLayerSolution_assign", "S4/S4.cpp", "1809", "1822", "+13", "SHIFTED", "Simulation_GetLayerSolution", "sol = S->solution;", "caller 1 dereference guard"),
        ("ComputeLayerSolution_sol", "S4/S4.cpp", "1889", "1902", "+13", "SHIFTED", "Simulation_ComputeLayerSolution", "Solution_ *sol = S->solution;", "layer solution computation"),
        ("RP_R8_M2c_1b_crash_ab", "S4/S4.cpp", "1995", "2008", "+13", "SHIFTED", "Simulation_ComputeLayerSolution", "memset(pab, 0, sizeof(std::complex<double>) * 4 * n);", "F3 crash site when 1764 failed"),
        ("RP_R8_M2c_1b_crash_solved", "S4/S4.cpp", "2021", "2034", "+13", "SHIFTED", "Simulation_ComputeLayerSolution", "sol->solved[layer_idx] = 1;", "F3 crash site when 1765 failed"),
        ("DestroySolution_sol", "S4/S4.cpp", "2844", "2857", "+13", "SHIFTED", "Simulation_DestroySolution", "sol = S->solution;", "solution destructor"),
        ("DestroySolution_free", "S4/S4.cpp", "2857", "2870", "+13", "SHIFTED", "Simulation_DestroySolution", "free(S->solution); S->solution = NULL;", "solution destructor cleanup"),
        ("DestroyLayerSolutions_sol", "S4/S4.cpp", "2869", "2882", "+13", "SHIFTED", "Simulation_DestroyLayerSolutions", "sol = S->solution;", "layer solution cleanup"),
        ("caller_OutputStructurePOVRay", "S4/S4.cpp", "2969", "2982", "+13", "SHIFTED", "Simulation_OutputStructurePOVRay", "ret = Simulation_InitSolution(S);", "caller 2"),
        ("caller_OutputLayerPattern", "S4/S4.cpp", "3318", "3331", "+13", "SHIFTED", "Simulation_OutputLayerPatternRealization", "int error = Simulation_InitSolution(S);", "caller 3"),
        ("caller_GetEpsilon", "S4/S4.cpp", "3565", "3578", "+13", "SHIFTED", "Simulation_GetEpsilon", "int error = Simulation_InitSolution(S);", "caller 4"),
        ("caller_GetSMatrix", "S4/S4.cpp", "4070", "4083", "+13", "SHIFTED", "Simulation_GetSMatrix", "int error = Simulation_InitSolution(S);", "caller 5"),
        ("fn_GetFieldPlane", "S4/S4.cpp", "4219", "4232", "+13", "SHIFTED", "S4_Simulation_GetFieldPlane", "int S4_Simulation_GetFieldPlane(...){", "public API"),
    ]
    with open(LINEMAP_OUT, 'w', encoding='utf-8') as fh:
        fh.write("# LINEMAP_F3_F4_S3R5.tsv -- Line mapping between F3 (8d8202a) and F4 (05097a7)\n")
        fh.write("# Rule: lines 1-1759 offset=0; lines 1760-1773 modified by fix (+13 net lines); lines 1774+ offset=+13\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print("Wrote %s" % LINEMAP_OUT)
    return 0

if __name__ == "__main__":
    sys.exit(main())
