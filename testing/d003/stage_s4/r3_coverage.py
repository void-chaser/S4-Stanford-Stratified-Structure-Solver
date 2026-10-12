#!/usr/bin/env python3
# r3_coverage.py -- P05-S4 R3-5 coverage table builder (new file, R3).  Reads SITEMAP.tsv (r1_id per point) and
# RESULTS_R3.tsv (observed class and hit per point and tree), and writes COVERAGE_R3.tsv: one row per R1 registry id
# (REGISTRY_S4_PRE.tsv), with the R3 point ids that map to it, the observed classes on B and F, and whether the
# R1 point was reached.  No class is computed here: observed classes are copied from RESULTS_R3.tsv.
#
#   python3 -I -B testing/d003/stage_s4/r3_coverage.py SITEMAP RESULTS_R3 R1_REGISTRY OUT_TSV
#
# An R1 id with no R3 point is written UNMAPPED with the reason from REASONS below (a reason is given only where the
# source or the injector structure shows it; otherwise "unconfirmed").
import sys
from collections import defaultdict

# Reasons for R1 ids that have no in-scope R3 point (only where the cause is established by the source, the
# registry or the harness; anything else is written as "unconfirmed").
REASONS = {
    "AL02": "same source site as EXP40 (experimental.cpp:40 ivalues); R1 registered it twice; counted under EXP40",
    "AL18": "fmm_kottke.cpp:78 uses fft_alloc_complex, not S4_malloc; the --wrap of S4_malloc cannot reach it; needs the kottke_alloc hook (R2 family D), not used in the R3 sweep",
    "FE01": "fmm_ret status of FMMGetEpsilon_Experimental (S4.cpp dispatch); needs the fmmret seam (apply_seam_r5_fmmret.py), absent in the plain R2 build",
    "FE02": "fmm_ret status of FMMGetEpsilon_Kottke; needs the fmmret seam, absent in the plain build",
    "FE03": "fmm_ret status of FMMGetEpsilon_FFT; needs the fmmret seam, absent in the plain build",
    "FE04": "fmm_ret status of FMMGetEpsilon_PolBasisJones (basis 1); needs the fmmret seam, absent in the plain build",
    "FE05": "fmm_ret status of FMMGetEpsilon_PolBasisNV (basis 1); needs the fmmret seam, absent in the plain build",
    "FE06": "fmm_ret status of FMMGetEpsilon_PolBasisVL (basis 1); needs the fmmret seam, absent in the plain build",
    "FE07": "fmm_ret status of FMMGetEpsilon_ClosedForm; needs the fmmret seam, absent in the plain build",
    "FE08": "fmm_ret status of FMMGetEpsilon_PolBasisJones (basis 2); needs the fmmret seam, absent in the plain build",
    "FE09": "fmm_ret status of FMMGetEpsilon_PolBasisNV (basis 2); needs the fmmret seam, absent in the plain build",
    "FE10": "fmm_ret status of FMMGetEpsilon_PolBasisVL (basis 2); needs the fmmret seam, absent in the plain build",
    "SI01": "solve_info of LinearSolve at fmm_FFT.cpp:204; needs the linearsolve seam (family A), absent in the plain build",
    "SI02": "solve_info of LinearSolve at fmm_kottke.cpp:279; needs the linearsolve seam, absent in the plain build",
    "CL01": "LinearSolve info=NULL seam site, closed.cpp:129; needs the linearsolve_null seam (family B), absent in the plain build; F-only seam (R1 U2)",
    "CL02": "LinearSolve info=NULL seam site, closed.cpp:132; needs the linearsolve_null seam, absent in the plain build",
    "CL03": "LinearSolve info=NULL seam site, closed.cpp:137; needs the linearsolve_null seam, absent in the plain build",
    "CL04": "LinearSolve info=NULL seam site, closed.cpp:234; needs the linearsolve_null seam, absent in the plain build",
    "PJ01": "LinearSolve info=NULL, PolBasisJones.cpp:361; needs the linearsolve_null seam, absent in the plain build",
    "PN01": "LinearSolve info=NULL, PolBasisNV.cpp:252; needs the linearsolve_null seam, absent in the plain build",
    "PV01": "LinearSolve info=NULL, PolBasisVL.cpp:260; needs the linearsolve_null seam, absent in the plain build",
    "CLM1": "libc malloc at S4.cpp:2267 (ComputeLayerModes); not an S4_malloc call; the R3 discovery and injector attach only to the S4_malloc, fft_plan and fft_plan_exec wrappers, so this libc call is neither observed nor selectable by the s4malloc request",
    "CLM2": "S4_malloc inside S4.o (same translation unit as S4_malloc); --wrap cannot intercept it (P05_S2_TEST_HARNESS.md lines 115 and 488); needs the R2 allocation seam",
    "CLM3": "S4_malloc inside S4.o (ComputeLayerModes non-uniform path); --wrap cannot intercept it; needs the allocation seam",
    "CLM4": "S4_malloc inside S4.o (ComputeLayerModes non-uniform path); --wrap cannot intercept it; needs the allocation seam",
    "ACF1": "S4_malloc inside S4.o (AddFieldToCache); --wrap cannot intercept it; needs the R5 addfield seam (apply_seam_r5_addfield.py), absent in the plain build",
    "K1A": "numerical NaN Epsilon2 case (kottke), not an allocation/plan/exec point; covered by the S3R probe, not by the R3 sweep",
    "K1B": "numerical NaN Epsilon2 case (kottke), not an allocation/plan/exec point; covered by the S3R probe, not by the R3 sweep",
    "D016": "pattern zero-field check (VL, NG 1), not an allocation/plan/exec point; covered by S3R2, not by the R3 sweep",
    "RNV1": "NV error path before normalization, not an allocation/plan/exec point; NOT_TRIGGERED in S3R2; not by the R3 sweep",
}


def read_rows(path, skip_prefix):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith(skip_prefix):
                continue
            rows.append(line.rstrip("\n").split("\t"))
    return rows


def main(argv):
    if len(argv) != 5:
        print("usage: r3_coverage.py SITEMAP RESULTS_R3 R1_REGISTRY OUT_TSV", file=sys.stderr)
        return 2
    sitemap, results, r1reg, out = argv[1], argv[2], argv[3], argv[4]
    sm = read_rows(sitemap, "point_id\t")
    res = read_rows(results, "point_id\t")
    r1 = [l.split("\t")[0] for l in open(r1reg, encoding="utf-8") if l.strip() and not l.startswith("#") and not l.startswith("point\t")]
    obs = defaultdict(dict)
    for r in res:
        obs[r[0]][r[1]] = r
    by_label = defaultdict(list)
    for r in sm:
        if r[6] == "YES" and r[7] != "NONE":
            by_label[r[7]].append(r[0])
    lines = []
    summary = {"in_scope_points": 0, "reached_both": 0, "not_reached": 0}
    for pid_list in by_label.values():
        summary["in_scope_points"] += len(pid_list)
    # distinct in-scope points (a point maps to one r1 label)
    all_pts = sorted({p for v in by_label.values() for p in v})
    reached = [p for p in all_pts if obs.get(p, {}).get("B") and obs.get(p, {}).get("F")
               and obs[p]["B"][11] != "0" and obs[p]["F"][11] != "0"]
    notreached = [p for p in all_pts if p not in reached]
    summary["in_scope_points"] = len(all_pts)
    summary["reached_both"] = len(reached)
    summary["not_reached"] = len(notreached)
    # EX05-EX08 is a SET label: the four Jones exec sites are not tied one by one to their NTH (return addresses are
    # distinct but the order to the source lines is unconfirmed).  The four R1 ids therefore share the same eight
    # points and are written as ONE row, with the set claim, not as four separate per-site claims.
    EX_SET = ("EX05", "EX06", "EX07", "EX08")
    ex_set_pts = sorted({p for p in by_label.get("EX05-EX08(unconfirmed)", [])})
    done_set = False
    for rid in r1:
        if rid in EX_SET:
            if done_set:
                continue
            done_set = True
            pts = ex_set_pts
            rid = "EX05-EX08 (set)"
        else:
            labels = [lbl for lbl in by_label if lbl == rid]
            pts = sorted({p for lbl in labels for p in by_label[lbl]})
        if not pts:
            lines.append((rid, "UNMAPPED", "-", "-", "-", REASONS.get(rid, "unconfirmed")))
            continue
        bobs = sorted({obs[p]["B"][6] for p in pts if p in obs and "B" in obs[p]})
        fobs = sorted({obs[p]["F"][6] for p in pts if p in obs and "F" in obs[p]})
        nreach = sum(1 for p in pts if p in reached)
        status = "REACHED(%d/%d)" % (nreach, len(pts))
        note = "" if nreach == len(pts) else "some points not reached (INVALID): see RESULTS_R3"
        lines.append((rid, status, ",".join(pts[:4]) + (" ..." if len(pts) > 4 else ""),
                      "B=" + "|".join(bobs), "F=" + "|".join(fobs), note))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# COVERAGE_R3.tsv -- P05-S4 R3-5 coverage of the R1 registry (62 ids).  Built by r3_coverage.py.\n")
        fh.write("# status: REACHED(n/m) = n of the m R3 points mapped to this R1 id were reached on B and F (hit>=1);\n")
        fh.write("#   UNMAPPED = no in-scope R3 point; the reason column gives the cause (or 'unconfirmed').\n")
        fh.write("# In-scope R3 points: %d; reached on both trees: %d; not reached (INVALID): %d.\n"
                 % (summary["in_scope_points"], summary["reached_both"], summary["not_reached"]))
        fh.write("r1_id\tstatus\tR3_point_ids\tB_observed\tF_observed\tnote_or_reason\n")
        for l in lines:
            fh.write("\t".join(l) + "\n")
    print("r1_ids=%d in_scope=%d reached_both=%d not_reached=%d unmapped=%d" % (
        len(r1), summary["in_scope_points"], summary["reached_both"], summary["not_reached"],
        sum(1 for l in lines if l[1] == "UNMAPPED")))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
