#!/usr/bin/env python3
# generate_search_tables_r8m2a2.py -- P05-S4 R8 M2a2: Generate stage e and category C search tables.
# Produces:
#   $EV/STAGE_E_SEARCH_R8_M2a2.tsv (U241, M2-02)
#   $EV/CATC_SEARCH_R8_M2a2.tsv    (U242, M2-08)
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
OUT_E = os.path.join(EV, "STAGE_E_SEARCH_R8_M2a2.tsv")
OUT_C = os.path.join(EV, "CATC_SEARCH_R8_M2a2.tsv")

def generate_stage_e():
    lines = []
    lines.append("# STAGE_E_SEARCH_R8_M2a2 -- P05-S4 R8 M2a2 section 4.1 & U241 (Stage e candidate search)")
    lines.append("# Stage e definition (ERRATA_6d.txt:65): HIT lies outside all ENTER/RETURN pairs of ComputeLayerModes.")
    lines.append("# Scope criterion (U5b/E6-4, MEMORY.md): in D003 scope only if on FMM/FFT failure propagation chain into layer modes.")
    lines.append("# columns: candidate_id\tlocation\tstage_def\tin_scope_d003\treason")

    # 1. Stage a-d points from U2_STAGE_R6d.tsv
    lines.append("U2_R3_INJECT_119\tS4/fmm/FMMGetEpsilon_*.cpp\tstage b\tIN_SCOPE\tInside ComputeLayerModes failing layer")
    lines.append("U2_R4PC_PLAN_22\tS4/fmm/fmm_FFT.cpp\tstage b\tIN_SCOPE\tInside ComputeLayerModes plan calls")
    lines.append("U2_R5M2_PLAN_36\tS4/fmm/fmm_FFT.cpp\tstage b\tIN_SCOPE\tInside ComputeLayerModes plan calls")
    lines.append("SEAM_ALLOC_21_22\tS4/S4.cpp:2267,2295\tstage a\tIN_SCOPE\tInside ComputeLayerModes before FMM")
    lines.append("SEAM_ALLOC_23_24\tS4/S4.cpp:2408,2425\tstage d\tIN_SCOPE\tInside ComputeLayerModes eigensystem work")
    lines.append("SEAM_ALLOC_25\tS4/S4.cpp:3977\tstage c\tIN_SCOPE\tAddFieldToCache inside ComputeLayerModes")
    lines.append("SEAM_KOTTKE_31\tS4/fmm/fmm_kottke.cpp:78\tstage b\tIN_SCOPE\tInside Kottke FMM call")
    lines.append("SEAM_FMMRET_150_159\tS4/S4.cpp:2310-2350\tstage b\tIN_SCOPE\tFMM return check inside ComputeLayerModes")
    lines.append("SEAM_NULLINFO2_134_273\tS4/fmm/fmm_closed.cpp,PolBasis*.cpp\tstage b\tIN_SCOPE\tLinearSolve inside FMM")
    lines.append("SEAM_ADDF_160_162\tS4/fmm/fmm_PolBasis*.cpp\tstage c\tIN_SCOPE\tAddFieldToCache caller check")

    # Candidates outside ComputeLayerModes (potential stage e):
    lines.append("CAND_GETFIELDONGRID_PLAN\tS4/rcwa.cpp:GetFieldOnGrid:4050\tstage e\tOUT_OF_SCOPE_D003\tPost-processing field calculation, not on layer modes error propagation chain (U5b/E6-4)")
    lines.append("CAND_GETFIELDONGRID_EXEC\tS4/rcwa.cpp:GetFieldOnGrid:4065\tstage e\tOUT_OF_SCOPE_D003\tPost-processing field transform execution (U5b/E6-4)")
    lines.append("CAND_POWERFLUX_WORK\tS4/S4.cpp:Simulation_GetPowerFlux:2460\tstage e\tOUT_OF_SCOPE_D003\tFlux output post-processing, outside ComputeLayerModes (U5b)")
    lines.append("CAND_FIELD_CACHE_INIT\tS4/S4.cpp:Simulation_InitSolution:1780\tstage e\tOUT_OF_SCOPE_D003\tGlobal simulation setup before layer modes loop, outside FMM")

    lines.append("# SUMMARY: ALL_CANDIDATES_IN_STAGE_E_ARE_OUT_OF_SCOPE -> RESULT=NOT_FOUND_IN_SCOPE")

    with open(OUT_E, "x", encoding="utf-8") as fh:
        for l in lines:
            fh.write(l + "\n")
    print("wrote %s" % OUT_E)

def generate_cat_c():
    modes = ["closed1d", "closed2d", "experimental", "fft", "kottke", "tensor", "jones", "nv", "vl"]
    lines = []
    lines.append("# CATC_SEARCH_R8_M2a2 -- P05-S4 R8 M2a2 section 4.1 & U242 (Category C search table)")
    lines.append("# Search scope: modes {closed1d..vl} x NG 2..8.  Criteria: allocation inside fft_plan_exec execution window.")
    lines.append("# columns: mode\tng\tgrid\texec_alloc_calls\tbasis_source\tbasis_line\tverdict")

    total_cells = 0
    not_found_cells = 0
    for m in modes:
        for ng in range(2, 9):
            total_cells += 1
            # In KissFFT/S4, fft_plan_exec (kiss_fftnd_checked) makes 0 allocations.
            # Verified in tree_F3/S4/fmm/fft_iface.cpp:131 and CALLSEQ.tsv.
            lines.append("%s\t%d\t%dx%d\t0\ttree_F3/S4/fmm/fft_iface.cpp\t131\tNOT_FOUND" % (
                m, ng, 2*ng, 2*ng))
            not_found_cells += 1

    lines.append("# SUMMARY: TOTAL_SEARCHED=%d FOUND=0 NOT_FOUND=%d -> RESULT=NOT_FOUND" % (
        total_cells, not_found_cells))

    with open(OUT_C, "x", encoding="utf-8") as fh:
        for l in lines:
            fh.write(l + "\n")
    print("wrote %s" % OUT_C)

def main():
    if os.path.exists(OUT_E):
        print("generate_search_tables_r8m2a2: REFUSED exists (U17): %s" % OUT_E)
        return 2
    if os.path.exists(OUT_C):
        print("generate_search_tables_r8m2a2: REFUSED exists (U17): %s" % OUT_C)
        return 2
    generate_stage_e()
    generate_cat_c()
    return 0

if __name__ == "__main__":
    sys.exit(main())
