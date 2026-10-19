#!/usr/bin/env python3
# relr4_prereg.py -- write PREREG_RELR4.tsv (one row per test unit / comparison unit) and
# PREREG_RELR4.tsv.sha256.txt BEFORE any formal run of the round (task brief section 4).
# Status: INFLUENCED (expectations were formed from source reading: the registered Lua API scan
# EXPECT_SCAN_RELR4.tsv, the REL-R1 rules, the U401 ruling about the original GetAmplitudes bug, and the
# three-tree build logs; no formal run of this round has happened yet).
# No expectation is ever rewritten afterwards; corrections go to ERRATA_RELR4.txt only.
import os, sys, hashlib, datetime

REPO = subprocess_repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# repository root resolved from this script's location: <repo>/testing/d003/stage_relr4/relr4_prereg.py
for _ in range(6):
    if os.path.isdir(os.path.join(REPO, ".git")) or os.path.isfile(os.path.join(REPO, "AGENTS.md")):
        break
    REPO = os.path.dirname(REPO)
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
F4 = os.path.join(EV, "trees", "F4")
TAB = chr(9)
NL = chr(10)
TOL_T1 = "1e-12"
TOL_T2 = {"simple": "1e-12", "fresnel": "1e-12", "fanfig12": "1e-10"}
TOL_CAPI_REL = "5e-6"
TOL_CAPI_ABS = "1e-6"
TOL_POSCTRL = "1e-10"
TOL_MPI = "1e-12"

# ---- source-reading knowledge used to form the expectations -------------------------------------
# REL-R1 established that B (5b72793) and F4 (3de6d8b) give the SAME 38 / BOTH_FAIL 11 split over the
# 49 non-MPI examples.  The same 49 example scripts exist with identical content in U (git diff 7fd00a2
# 3de6d8b -- examples shows only the 3 reference .txt files added).  EXPECT_SCAN_RELR4.tsv shows:
#   * every passing example calls only API functions registered by the U frontend as well;
#   * the 11 B/F4 failures are 1 GetRealMaterial call, 4 loadstring calls (nil in Lua 5.2) and 2 Lua
#     syntax errors plus the 4 Li JOSA singular-system runs.
KNOWN_FAIL = ["examples/1d/Christ_PRB_70_125113_2004/fig2b.lua",
              "examples/2d/Li_JOSA_14_2758_1997/ex1_new.lua",
              "examples/2d/Li_JOSA_14_2758_1997/ex1_normal.lua",
              "examples/2d/Li_JOSA_14_2758_1997/ex1_orig.lua",
              "examples/2d/Li_JOSA_14_2758_1997/ex2.lua",
              "examples/convergence/1d/binary_grating.lua",
              "examples/convergence/Li_JOSA_14_2758_1997/ex1/cellA.lua",
              "examples/convergence/Li_JOSA_14_2758_1997/ex1/cellB.lua",
              "examples/convergence/resonance_pos/ref.lua",
              "examples/convergence/Li_JOSA_14_2758_1997/ex2/fig2.lua",
              "examples/magneto/slab.lua"]
# U expectations: the failure reasons above are independent of the fixes in B/F4, so U is expected to
# fail the same way for all but the four Li singular runs, whose U outcome is genuinely unknown.
U_BOTH_FAIL_EXPECTED = set(KNOWN_FAIL) - set([
    "examples/2d/Li_JOSA_14_2758_1997/ex1_new.lua",
    "examples/2d/Li_JOSA_14_2758_1997/ex1_normal.lua",
    "examples/2d/Li_JOSA_14_2758_1997/ex1_orig.lua",
    "examples/2d/Li_JOSA_14_2758_1997/ex2.lua"])
MPI_EXAMPLES = ["examples/MPI_example/binary_grating_mpi.lua", "examples/MPI_example/mpi_simple.lua"]
T2_CASES = [("simple", "examples/simple/simple.lua", "examples/simple/simple.txt"),
            ("fresnel", "examples/0d/fabry_perot/fresnel.lua", "examples/0d/fabry_perot/fresnel.txt"),
            ("fanfig12", "examples/2d/Fan_PRB_65_2002/fig12.lua", "examples/2d/Fan_PRB_65_2002/fig12.txt")]
TREE_LABEL = {"U": "U", "B": "B", "F4": "F4"}


def eid(rel):
    s = rel[len("examples/"):].replace("/", "__")
    return s[:-4] if s.endswith(".lua") else s


def lua_rels():
    out = []
    for root, dirs, files in os.walk(os.path.join(F4, "examples")):
        dirs.sort()
        for f in sorted(files):
            if f.endswith(".lua"):
                out.append(os.path.relpath(os.path.join(root, f), F4))
    return sorted(out)


def main():
    if os.path.exists(os.path.join(EV, "PREREG_RELR4.tsv")) or os.path.exists(os.path.join(EV, "PREREG_RELR4.tsv.sha256.txt")):
        print("HARD_STOP pre-registration already written; corrections belong in ERRATA_RELR4.txt")
        return 2
    rels = lua_rels()
    if len(rels) != 51:
        print("HARD_STOP expected 51 .lua under the F4 tree examples/, got %d" % len(rels))
        return 2
    non_mpi = [r for r in rels if r not in MPI_EXAMPLES]
    if len(non_mpi) != 49:
        print("HARD_STOP expected 49 non-MPI examples, got %d" % len(non_mpi))
        return 2
    passing = [r for r in non_mpi if r not in KNOWN_FAIL]
    if len(passing) != 38:
        print("HARD_STOP expected 38 passing non-MPI examples, got %d" % len(passing))
        return 2
    cols = ["unit_id", "suite", "tree", "command", "cwd", "timeout_s", "expected", "criterion", "note"]
    rows = ["# PREREG_RELR4.tsv -- P05 delivery round REL-R4 pre-registration. STATUS: INFLUENCED.",
            "# Status INFLUENCED: expectations formed before any formal run from (a) source reading of the three",
            "# trees (EXPECT_SCAN_RELR4.tsv: registered Lua API, loadstring/GetRealMaterial/syntax failures),",
            "# (b) the REL-R1 result split for B vs F4 (38 SAME / 11 BOTH_FAIL on the 49 non-MPI examples),",
            "# (c) ruling U401 (the original GetAmplitudes int-conversion bug and its fix 93b1c90), and",
            "# (d) the three-tree build logs BUILD_RELR4.tsv / WARN_DIFF_RELR4.tsv.",
            "# Written before the first formal run; sha256 recorded in PREREG_RELR4.tsv.sha256.txt; no row is rewritten.",
            "# Placeholders: $REPO = repository root; $EV = checkpoints/p05/evidence/p05-rel-r4; <T> in {U,B,F4};",
            "#   <P> in {1,2}; example ids replace '/' with '__' and drop the .lua suffix.",
            "# Comparison units carry tree = U_vs_F4 or B_vs_F4.  Categories (task brief section 4):",
            "#   SAME, DIFF_WITHIN_TOL, DIFF_ATTRIBUTED, REGRESSION, IMPROVED, BOTH_FAIL, U_UNAVAILABLE, FLAKY.",
            "#   SAME = both rc=0, stdout and file products byte-identical (tree root path normalised first).",
            "#   DIFF_WITHIN_TOL = both pass, not byte-identical, numdiff relative max difference <= tolerance.",
            "#   DIFF_ATTRIBUTED = both pass, beyond tolerance; requires the section 5.3 M-tree attribution.",
            "#   REGRESSION = U passes and F4 fails (recorded, NOT a stop condition of this round).",
            "#   IMPROVED = U fails and F4 passes (U failure reason must be written down).",
            "#   BOTH_FAIL = both fail (paths normalised before comparing messages).",
            "#   U_UNAVAILABLE = a capability U itself cannot provide (Python interface, own regression suite, etc.).",
            "#   FLAKY = the same tree gives different results in pass 1 vs pass 2.",
            "#   UNKNOWN = the expected category is genuinely unknown from source reading; whatever is observed is recorded.",
            TAB.join(cols)]
    # ------------------------------------------------------------------ T1 examples: 51 x 3 trees x 2 passes
    for rel in rels:
        is_mpi = rel in MPI_EXAMPLES
        for tree in ("U", "B", "F4"):
            if is_mpi:
                exp = "PASS"
                note = ("MPI_example script run with the NON-MPI build/S4 in T1: MPIRank=0, MPISize=1, so it is the "
                        "single-process reference reused by T3 (task brief section 5.1)")
            elif tree == "U":
                if rel in U_BOTH_FAIL_EXPECTED:
                    exp = "FAIL_EXPECTED"
                    note = "U expected to fail like B/F4: " + (
                        "GetRealMaterial not registered by any tree" if "Christ" in rel else
                        "loadstring is nil under Lua 5.2" if "convergence/1d" in rel or "cellA" in rel or "cellB" in rel or "resonance_pos" in rel else
                        "Lua syntax error in the script itself" if "magneto/slab" in rel else
                        "script parse/exec error already present upstream")
                elif rel in KNOWN_FAIL:
                    exp = "UNKNOWN"
                    note = "Li JOSA singular interface system: U outcome genuinely unknown (task brief section 4)"
                else:
                    exp = "PASS"
                    note = "passing example; every API it calls is also registered by the U frontend (EXPECT_SCAN_RELR4.tsv)"
            else:
                exp = "FAIL_EXPECTED" if rel in KNOWN_FAIL else "PASS"
                note = "REL-R1 established this B/F4 outcome; this round must reproduce it (task brief section 5.1)"
            rows.append(TAB.join(["T1_%s_%s_p%s" % (eid(rel), tree, "1" if tree == "U" else "P"),
                                  "T1_examples", tree,
                                  "python3 -B testing/d003/stage_relr4/relr4_examples.py run-unit --example %s --tree %s --pass P" % (rel, tree),
                                  "$EV/run/%s/P/%s" % (tree, eid(rel)), "3600", exp,
                                  "STATUS_%s" % exp, note]))
    # fill the two passes properly (rows printed above use P placeholder; rewrite deterministic: emit 2 passes)
    rows = [r for r in rows if not r.startswith("T1_") or TAB + "T1_examples" + TAB not in r]
    for rel in rels:
        is_mpi = rel in MPI_EXAMPLES
        for tree in ("U", "B", "F4"):
            for pas in ("1", "2"):
                if is_mpi:
                    exp, note = "PASS", ("MPI_example script with the NON-MPI build/S4: MPIRank=0, MPISize=1; "
                                         "single-process reference reused by T3")
                elif tree == "U":
                    if rel in U_BOTH_FAIL_EXPECTED:
                        exp = "FAIL_EXPECTED"
                        note = "U expected to fail like B/F4 (GetRealMaterial / loadstring / script syntax; EXPECT_SCAN_RELR4.tsv)"
                    elif rel in KNOWN_FAIL:
                        exp = "UNKNOWN"
                        note = "Li JOSA singular interface system: U outcome genuinely unknown (task brief section 4)"
                    else:
                        exp = "PASS"
                        note = "passing example; every API it calls is registered by the U frontend (EXPECT_SCAN_RELR4.tsv)"
                else:
                    exp = "FAIL_EXPECTED" if rel in KNOWN_FAIL else "PASS"
                    note = "REL-R1 established this B/F4 outcome; reproduced here (task brief section 5.1)"
                rows.append(TAB.join(["T1_%s_%s_p%s" % (eid(rel), tree, pas), "T1_examples", tree,
                                      "python3 -B testing/d003/stage_relr4/relr4_examples.py run-unit --example %s --tree %s --pass %s" % (rel, tree, pas),
                                      "$EV/run/%s/%s/%s" % (tree, pas, eid(rel)), "3600", exp,
                                      "STATUS_%s" % exp, note]))
    # ------------------------------------------------------------------ T1 comparisons: 49 x (U vs F4) + 49 x (B vs F4)
    for rel in non_mpi:
        if rel in KNOWN_FAIL:
            cat = "UNKNOWN" if rel in ("examples/2d/Li_JOSA_14_2758_1997/ex1_new.lua",
                                       "examples/2d/Li_JOSA_14_2758_1997/ex1_normal.lua",
                                       "examples/2d/Li_JOSA_14_2758_1997/ex1_orig.lua",
                                       "examples/2d/Li_JOSA_14_2758_1997/ex2.lua") else "BOTH_FAIL"
            note = "expected BOTH_FAIL because the failure is independent of the B/F4 fixes" if cat == "BOTH_FAIL" else "U outcome unknown"
        else:
            cat = "UNKNOWN"
            note = ("both expected to pass; SAME if byte-identical, DIFF_WITHIN_TOL if numdiff <= %s, otherwise "
                    "DIFF_ATTRIBUTED with section 5.3 attribution (P04 frontend/fix history lies between U and F4)" % TOL_T1)
        rows.append(TAB.join(["T1CMP_%s_U_vs_F4" % eid(rel), "T1_compare", "U_vs_F4", "not a run", "NA", "0",
                              cat, "BYTE_IDENTICAL_ELSE_NUMDIFF_%s" % TOL_T1, note]))
    for rel in non_mpi:
        cat = "BOTH_FAIL" if rel in KNOWN_FAIL else "SAME"
        rows.append(TAB.join(["T1CMP_%s_B_vs_F4" % eid(rel), "T1_compare", "B_vs_F4", "not a run", "NA", "0",
                              cat, "BYTE_IDENTICAL_ELSE_NUMDIFF_%s" % TOL_T1,
                              "REL-R1 reproduction: 38 SAME and 11 BOTH_FAIL are expected over the 49 non-MPI examples"]))
    # ------------------------------------------------------------------ T2 reference cases: 3 trees x (3 cases + runtests.sh)
    for tree in ("U", "B", "F4"):
        for cid, script, ref in T2_CASES:
            rows.append(TAB.join(["T2_%s_%s" % (tree, cid), "T2_runtests_reference", tree,
                                  "python3 -B testing/d003/stage_relr4/relr4_t2.py case --tree %s --case %s" % (tree, cid),
                                  "$EV/run/t2/%s/%s" % (tree, cid), "600", "PASS_REF",
                                  "REFERENCE_NUMDIFF_%s" % TOL_T2[cid],
                                  "run the tree's build/S4 on the F4 tree's %s and numdiff against the F4 tree's committed %s" % (script, ref)]))
        rows.append(TAB.join(["T2_%s_runtests_sh" % tree, "T2_runtests_reference", tree,
                              "python3 -B testing/d003/stage_relr4/relr4_t2.py sh --tree %s" % tree,
                              "$EV/run/t2/%s/script" % tree, "600", "PASS_REF", "STATUS_EQUAL",
                              "run the F4 tree's testing/runtests.sh with S4_BIN=<tree>/build/S4 (task brief section 5.2)"]))
    rows.append(TAB.join(["T2_U_OWN_MANIFEST", "T2_runtests_reference", "U",
                          "python3 -B testing/d003/stage_relr4/relr4_t2.py u-own",
                          "$EV/run/t2/U/own_manifest", "600", "UNRUNNABLE",
                          "RECORD_ONLY",
                          "U's own testing/runtests.sh with U's testing/testcases.txt: 10 baselines and 7 of 10 scripts are missing (EXPECT_SCAN_RELR4.tsv), so the original suite cannot run"]))
    for cid, script, ref in T2_CASES:
        rows.append(TAB.join(["T2CMP_%s_U_vs_F4" % cid, "T2_compare", "U_vs_F4", "not a run", "NA", "0",
                              "UNKNOWN", "BYTE_IDENTICAL_ELSE_NUMDIFF_%s" % TOL_T2[cid],
                              "both expected to pass their committed reference; numeric category to be observed"]))
    for cid, script, ref in T2_CASES:
        rows.append(TAB.join(["T2CMP_%s_B_vs_F4" % cid, "T2_compare", "B_vs_F4", "not a run", "NA", "0",
                              "SAME", "BYTE_IDENTICAL_ELSE_NUMDIFF_%s" % TOL_T2[cid],
                              "B and F4 are expected byte-identical on the reference cases"]))
    # ------------------------------------------------------------------ T3 MPI
    rows.append(TAB.join(["T3_PRECHECK_MPIRUN_TRUE", "T3_mpi", "ALL", "python3 -B testing/d003/stage_relr4/relr4_mpi.py precheck",
                          "$EV/mpi", "120", "PASS", "RC0", "mpirun -np 2 true must pass (task brief section 5.4.1)"]))
    rows.append(TAB.join(["T3_PRECHECK_RANK_PROBE", "T3_mpi", "ALL", "python3 -B testing/d003/stage_relr4/relr4_mpi.py precheck",
                          "$EV/mpi", "120", "PASS", "RANKS_0_AND_1",
                          "minimal MPI program printing its rank must show ranks 0 and 1"]))
    for tree in ("U", "B", "F4"):
        rows.append(TAB.join(["T3_%s_build_s4mpi" % tree, "T3_mpi", tree,
                              "make build/S4mpi CC=mpicc CXX=mpicxx MPI_INC=... MPI_LIB=... (relr4_mpi.py build --tree %s)" % tree,
                              "$EV/trees/%s" % tree if tree != "U" else "$EV/upstream/S4", "1800", "BUILD_OK", "RC0",
                              "same command for all trees; U additionally gets CFLAGS=-Wno-error=int-conversion"]))
        rows.append(TAB.join(["T3_%s_banner" % tree, "T3_mpi", tree,
                              "build/S4mpi -v (relr4_mpi.py build --tree %s)" % tree,
                              "$EV/trees/%s" % tree if tree != "U" else "$EV/upstream/S4", "60", "WITH_MPI", "BANNER",
                              "output must contain 'With MPI support' (task brief section 5.4.3)"]))
    for rel in MPI_EXAMPLES:
        for tree in ("U", "B", "F4"):
            for np_ in ("1", "4"):
                for pas in ("1", "2"):
                    rows.append(TAB.join(["T3_%s_%s_np%s_p%s" % (eid(rel), tree, np_, pas), "T3_mpi", tree,
                                          "mpirun -np %s build/S4mpi %s (relr4_mpi.py run --example %s --tree %s --np %s --pass %s)" % (np_, rel, rel, tree, np_, pas),
                                          "$EV/mpi/run/%s/%s/np%s/p%s" % (eid(rel), tree, np_, pas), "1800", "PASS",
                                          "RC0_AND_OUTFILES", "one independent cwd per run (task brief section 5.4.4)"]))
    for rel in MPI_EXAMPLES:
        for tree in ("U", "B", "F4"):
            rows.append(TAB.join(["T3CMP_%s_%s_np4_vs_np1" % (eid(rel), tree), "T3_compare", tree, "not a run", "NA", "0",
                                  "DIFF_WITHIN_TOL", "REL_%s" % TOL_MPI,
                                  "merged out0..3.txt of -np 4 vs out0.txt of -np 1; frequency coverage recorded, not judged"]))
            rows.append(TAB.join(["T3CMP_%s_%s_np4_vs_t1" % (eid(rel), tree), "T3_compare", tree, "not a run", "NA", "0",
                                  "DIFF_WITHIN_TOL", "REL_%s" % TOL_MPI,
                                  "merged out0..3.txt of -np 4 vs the T1 non-MPI out0.txt (single-process reference)"]))
    for rel in MPI_EXAMPLES:
        for np_ in ("1", "4"):
            rows.append(TAB.join(["T3CMP_%s_B_vs_F4_np%s" % (eid(rel), np_), "T3_compare", "B_vs_F4", "not a run", "NA", "0",
                                  "SAME", "BYTE_IDENTICAL", "same-named MPI output files must be byte-identical (task brief section 5.4.5b)"]))
            rows.append(TAB.join(["T3CMP_%s_U_vs_F4_np%s" % (eid(rel), np_), "T3_compare", "U_vs_F4", "not a run", "NA", "0",
                                  "UNKNOWN", "BYTE_IDENTICAL_ELSE_NUMDIFF_%s" % TOL_MPI,
                                  "both expected to pass; numeric category to be observed (task brief section 5.4.5c)"]))
    rows.append(TAB.join(["T3_RECORD_MISSING_1D_REFERENCE", "T3_mpi", "ALL", "not a run", "NA", "0", "RECORD_ONLY",
                          "FILE_ABSENT", "README points at ../1d/binary_grating.txt, which does not exist; recorded, not judged"]))
    # ------------------------------------------------------------------ T4 C API
    for tree in ("B", "F4"):
        rows.append(TAB.join(["T4_%s_build_capi" % tree, "T4_capi", tree,
                              "gcc -O0 -g -IS4 capi_fig12_relr4.c -o $EV/capi/%s/fig12 -L<tree>/build -lS4 -llapack -lblas -lstdc++ -lm" % tree,
                              "$EV/capi/%s" % tree, "600", "BUILD_OK", "RC0",
                              "Linux link line from task brief section 5.5.2; public API only"]))
    rows.append(TAB.join(["T4_U_build_capi", "T4_capi", "U",
                          "gcc -O0 -g -IS4 capi_fig12_relr4.c -o $EV/capi/U/fig12 -L<U>/build -lS4 -llapack -lblas -lstdc++ -lm",
                          "$EV/capi/U", "600", "UNKNOWN", "RC0", "U attempt (task brief section 5.5.2 'U also once')"]))
    for tree in ("B", "F4", "U"):
        rows.append(TAB.join(["T4_%s_original_makefile" % tree, "T4_capi", tree,
                              "make -C examples/C_api (original shipped Makefile, unchanged)",
                              "<tree>/examples/C_api", "300", "RC2", "RC_EQ_2",
                              "the shipped Makefile is macOS-only (-framework Accelerate -lc++); rc=2 expected on Linux"]))
    for tree in ("B", "F4", "U"):
        rows.append(TAB.join(["T4_%s_spec_sweep" % tree, "T4_capi", tree,
                              "awk -f examples/C_api/spec.awk in $EV/capi/%s (unmodified spec.awk, calls ./fig12)" % tree,
                              "$EV/capi/%s" % tree, "600", "PASS_REF" if tree != "U" else "UNKNOWN",
                              "REF_ABS_%s_PLUS_REL_%s_AND_ROWS35_FREQ_EQ" % (TOL_CAPI_ABS, TOL_CAPI_REL),
                              "35 rows 0.25..0.59 step 0.01 compared with the committed spec.awk.out (2015 macOS %g data)"]))
    for tree in ("B", "F4", "U"):
        rows.append(TAB.join(["T4_%s_posctrl_c_vs_lua" % tree, "T4_capi", tree,
                              "C fig12 --lua-sweep vs Lua fig12.lua forward flux on 0.25..0.268 step 0.003",
                              "$EV/capi/%s" % tree, "600", "PASS" if tree != "U" else "UNKNOWN",
                              "REL_%s" % TOL_POSCTRL,
                              "same structure; independent positive control that does not depend on the 2015 data"]))
    rows.append(TAB.join(["T4CMP_B_vs_F4_byte_identical", "T4_compare", "B_vs_F4", "not a run", "NA", "0",
                          "SAME", "BYTE_IDENTICAL", "B and F4 C output must be byte-identical (task brief section 5.5.4)"]))
    rows.append(TAB.join(["T4_RECORD_U_CAPI_EXAMPLE", "T4_capi", "U", "not a run", "NA", "0", "RECORD_ONLY",
                          "RECORD_ONLY", "the original examples/C_api/main.c is written against the pre-P04 C API names; its "
                          "availability in U is recorded, not judged"]))
    # ------------------------------------------------------------------ T5 main suite
    rows.append(TAB.join(["T5_F4_make_test", "T5_make_test", "F4", "python3 -B testing/d003/stage_relr4/relr4_maketest.py",
                          "$EV/maketest/F4", "5400", "PASS", "RC0_UNIT265_NO_FAILURE",
                          "make test once on F4 only; rc=0, unit_count=265, no failures (environment drift check)"]))
    rows.append(TAB.join(["T5_U_make_test", "T5_make_test", "U", "not run", "NA", "0", "U_UNAVAILABLE", "TARGET_ABSENT",
                          "U's Makefile has no 'test' target (task brief section 5.6)"]))
    rows.append(TAB.join(["M_ATTRIBUTION_CONDITIONAL", "T1_compare", "M", "not a run", "NA", "0", "CONDITIONAL",
                          "SOURCE_COMMIT", "M = b97f639 (original plus Lua/Python frontend fixes, no D001/D002 physics fixes) is "
                          "built and run ONLY for units whose U vs F4 category is DIFF_ATTRIBUTED (task brief section 5.3)"]))
    out = os.path.join(EV, "PREREG_RELR4.tsv")
    if not os.path.realpath(out).startswith(os.path.join(REPO, "checkpoints/p05") + os.sep):
        raise SystemExit("WRITE_OUTSIDE " + out)
    data = (NL.join(rows) + NL).encode("utf-8")
    open(out, "wb").write(data)
    sha = hashlib.sha256(data).hexdigest()
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    shaf = os.path.join(EV, "PREREG_RELR4.tsv.sha256.txt")
    open(shaf, "w", encoding="utf-8").write(
        "# PREREG_RELR4.tsv.sha256.txt -- sha256 of the pre-registration written before any formal run" + NL +
        "# algorithm: sha256; unit: bytes; UTC: " + utc + NL +
        "PREREG_RELR4.tsv" + TAB + sha + TAB + "bytes=%d" % len(data) + TAB + "utc=" + utc + NL)
    n = len(rows) - len([r for r in rows if r.startswith("#")])
    print("PREREG rows=%d sha256=%s" % (n, sha))
    print("WROTE " + os.path.relpath(out, REPO))
    print("WROTE " + os.path.relpath(shaf, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
