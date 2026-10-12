#!/usr/bin/env python3
# r3_prereg.py -- P05-S4 R3-3 pre-registration generator (new file, R3).  Reads SITEMAP.tsv and writes
# REGISTRY_S4_PRE_R3.tsv: one expectation row per (in_D003_scope=YES point, tree B or F).  The rule is fixed
# here, before any R3 injection run.  The generator reads no run result (there is none yet for R3 injections).
#
#   python3 -I -B testing/d003/stage_s4/r3_prereg.py SITEMAP_TSV OUT_TSV
#
# Rules (task R3-3, fixed):
#   F column: malloc -> REPORTED_FAILURE (FMM-side check, source-verified at HEAD: each FMM allocation is followed by
#             an if(NULL == ...) return, FMM files, see the basis text);  plan -> REPORTED_FAILURE;
#             exec -> REPORTED_FAILURE (boundary simulation, the caller returns 1 on nonzero).
#   B column: malloc -> CRASH (no check; the pointer is dereferenced or offset and used);
#             plan -> CRASH (fft_plan_exec(NULL) on the returned NULL plan);  exec -> SILENT_SWALLOW (return discarded).
# A point whose source differs from the rule gets its own basis text (none is found for the in-scope FMM points
# at HEAD/B; see the report).  Known historical observations that conflict with a rule are kept as the rule
# value and recorded in basis (never silently replaced).
# status: every row is INFLUENCED (the R1, R2 and discovery observations were read before this file).
import sys

HEAD = "33b8bf8"
B_COMMIT = "37a82e8"
F_COMMIT = "1c11905"

BASIS_MALLOC_F = "[源码 S4/fmm/*.cpp:NULL-check@%s] every FMM S4_malloc is followed by an if(NULL==...) return (verified by sed at HEAD)" % HEAD
BASIS_PLAN_F = "[源码 S4/fmm/*.cpp:plan-check@%s] plan NULL is checked after fft_plan_dft_2d (verified at HEAD)" % HEAD
BASIS_EXEC_F = "[源码 S4/fmm/*.cpp:exec-check@%s] nonzero fft_plan_exec return is reported (ret=1, goto cleanup) (verified at HEAD)" % HEAD
BASIS_MALLOC_B = "[源码 S4/fmm/*.cpp:no-check@%s] S4_malloc result used without a NULL check" % B_COMMIT
BASIS_PLAN_B = "[源码 S4/fmm/*.cpp:no-check@%s] fft_plan_dft_2d NULL is passed to fft_plan_exec" % B_COMMIT
BASIS_EXEC_B = "[源码 S4/fmm/*.cpp:discard@%s] fft_plan_exec return value discarded" % B_COMMIT


def expected(tree, cat):
    if tree == "F":
        return {"malloc": "REPORTED_FAILURE", "plan": "REPORTED_FAILURE", "exec": "REPORTED_FAILURE"}[cat], \
               {"malloc": BASIS_MALLOC_F, "plan": BASIS_PLAN_F, "exec": BASIS_EXEC_F}[cat]
    return {"malloc": "CRASH", "plan": "CRASH", "exec": "SILENT_SWALLOW"}[cat], \
           {"malloc": BASIS_MALLOC_B, "plan": BASIS_PLAN_B, "exec": BASIS_EXEC_B}[cat]


def main(argv):
    if len(argv) != 3:
        print("usage: r3_prereg.py SITEMAP_TSV OUT_TSV", file=sys.stderr)
        return 2
    rows = []
    with open(argv[1], encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#") or line.startswith("point_id\t"):
                continue
            f = line.rstrip("\n").split("\t")
            if len(f) != 9:
                raise SystemExit("SITEMAP row has %d fields" % len(f))
            pid, mode, cat, nth, size, caller, scope, r1, note = f
            if scope != "YES":
                continue
            rows.append((pid, mode, cat, nth, size, caller, r1))
    out = []
    for pid, mode, cat, nth, size, caller, r1 in rows:
        for tree in ("B", "F"):
            exp, basis = expected(tree, cat)
            out.append((pid, tree, mode, cat, nth, exp, basis + " ; r1=" + r1 + " ; caller=" + caller, "INFLUENCED"))
    with open(argv[2], "w", encoding="utf-8") as fh:
        fh.write("# REGISTRY_S4_PRE_R3.tsv -- P05-S4 R3-3 pre-registration (WRITTEN BEFORE ANY R3 INJECTION RUN).\n")
        fh.write("# One row per (in_D003_scope=YES point, tree B or F).  point_id = M-<route>-<mode>-<category>-<NTH>.\n")
        fh.write("# Trees: B = 37a82e8 (plain-B driver, R2 run2), F = 1c11905 (plain-F driver, R2 run2).  A is a control only.\n")
        fh.write("# Expected class: rule in r3_prereg.py.  Judge: judge_d003.py classify() from rc, rc1, rc2, hit.\n")
        fh.write("# status: INFLUENCED for every row (R1 registry, R2 results and the R3 discovery were read first).\n")
        fh.write("# NOT in this file: in_D003_scope=NO points (counted only, see SITEMAP.tsv).\n")
        fh.write("point_id\ttree\tmode\tcategory\tNTH\texpected_class\tbasis\tstatus\n")
        for r in out:
            fh.write("\t".join(r) + "\n")
    print("rows=%d points=%d" % (len(out), len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
