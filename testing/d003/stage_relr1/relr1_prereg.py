#!/usr/bin/env python3
# relr1_prereg.py -- write PREREG_RELR1.tsv (one row per test unit) and PREREG_RELR1.tsv.sha256.txt
# BEFORE any formal run of the round.  The example unit list is taken from the F4 exported tree
# (git HEAD) with 'find'-equivalent walk; the two MPI_example scripts are SKIP_DECLARED because no
# MPI build exists in this environment.  No expectation is ever rewritten afterwards; corrections go
# to ERRATA_RELR1.txt only.
import os, sys, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1")
TREES = os.path.join(EV, "trees")
TAB = chr(9)
NL = chr(10)
EX_TOL = {"examples/simple/simple.lua": "1e-12",
          "examples/0d/fabry_perot/fresnel.lua": "1e-12",
          "examples/2d/Fan_PRB_65_2002/fig12.lua": "1e-10"}


def wrap(text, cols=None):
    return text


def main():
    if os.path.exists(os.path.join(EV, "PREREG_RELR1.tsv")) or os.path.exists(os.path.join(EV, "PREREG_RELR1.tsv.sha256.txt")):
        print("HARD_STOP pre-registration already written; corrections belong in ERRATA_RELR1.txt")
        return 2
    f4 = os.path.join(TREES, "F4")
    b = os.path.join(TREES, "B")
    rels = []
    for root, dirs, files in os.walk(os.path.join(f4, "examples")):
        dirs.sort()
        for f in sorted(files):
            if f.endswith(".lua"):
                rel = os.path.relpath(os.path.join(root, f), f4)
                rels.append(rel)
    rels.sort()
    if len(rels) != 51:
        print("HARD_STOP expected 51 .lua under examples/, got %d" % len(rels))
        return 2
    skip_mpi = [r for r in rels if r.startswith(os.path.join("examples", "MPI_example"))]
    if len(skip_mpi) != 2:
        print("HARD_STOP expected 2 MPI_example scripts, got %d" % len(skip_mpi))
        return 2
    run_rels = [r for r in rels if r not in skip_mpi]

    def eid(rel):
        s = rel[len("examples/"):]
        s = s.replace("/", "__")
        if s.endswith(".lua"):
            s = s[:-4]
        return s

    cols = ["unit_id", "suite", "command", "cwd", "timeout_s", "expect_B", "expect_F4", "compare_rule", "note"]
    rows = []
    rows.append("# PREREG_RELR1.tsv -- P05 delivery round REL-R1 pre-registration. STATUS: INFLUENCED.")
    rows.append("# Status INFLUENCED: the expectations were formed from source reading (D003 touches only failure paths ->")
    rows.append("#   the non-failure outputs are expected to be byte-identical) and from the S5R3 unit count, not from a blind trial.")
    rows.append("# Written before the first formal run; sha256 recorded in PREREG_RELR1.tsv.sha256.txt; no row is rewritten later.")
    rows.append("# Placeholders: $REPO = repository root; $EV = checkpoints/p05/evidence/p05-rel-r1; $TREES = $EV/trees;")
    rows.append("#   <T> in {B,F4}; <P> in {1,2}; example ids replace '/' with '__' and drop the .lua suffix.")
    rows.append("# Suites: T1 make test (per tree, 2 passes); T2 runtests.sh and its 3 independent references;")
    rows.append("#   T3 examples; T4 P04 pipeline (F4 only); T5 P04 unit tests; T6 C API; T7 fresh clone; T8 optional D003 E2E.")
    rows.append("# Comparison rules:")
    rows.append("#   MAKETEST_UNIT_STATUS: per unit name status (ok/FAIL/ERROR/skipped) compared across the four passes;")
    rows.append("#     unit_count must equal 'Ran N' (reconciliation) and is compared with the S5R3 value 265.")
    rows.append("#   BYTE_IDENTICAL_ELSE_NUMDIFF_1E-12: sha256 of stdout/stderr must be equal; if not, numdiff with relative")
    rows.append("#     tolerance 1e-12 decides DIFF_WITHIN_TOL, otherwise DIFF.  Same-tree two-pass difference = FLAKY.")
    rows.append("#   REFERENCE_NUMDIFF_<tol>: compare stdout to the committed reference with that tolerance (independent reference).")
    rows.append("#   AGGREGATE_JSON_PASS: the P04 aggregate AGGREGATE.json verdict field must be PASS.")
    rows.append("#   STATUS_EQUAL: the two trees must give the same status (or F4 better); no golden reference exists.")
    rows.append("#   RECORD_ONLY: U tree cannot be built (U_BUILD_UNAVAILABLE); recorded, not judged (task brief section 5).")
    rows.append(TAB.join(cols))
    # ---------------- T1
    for tree in ("B", "F4"):
        for pas in ("1", "2"):
            rows.append(TAB.join([
                "T1_%s_p%s" % (tree, pas), "T1_make_test",
                "python3 -B testing/d003/stage_relr1/relr1_maketest.py %s:%s" % (tree, pas),
                "$EV/maketest", "5400", "PASS" if tree == "B" else "NA", "PASS" if tree == "F4" else "NA",
                "MAKETEST_UNIT_STATUS",
                "make -C $TREES/%s test PYTHON=python3; expected unit_count 265 as in S5R3; FLAKY if p1 and p2 differ" % tree]))
    # ---------------- T2
    t2cases = [("simple", "examples/simple/simple.lua", "examples/simple/simple.txt", "1e-12"),
               ("fresnel", "examples/0d/fabry_perot/fresnel.lua", "examples/0d/fabry_perot/fresnel.txt", "1e-12"),
               ("fanfig12", "examples/2d/Fan_PRB_65_2002/fig12.lua", "examples/2d/Fan_PRB_65_2002/fig12.txt", "1e-10")]
    for tree in ("B", "F4"):
        for cid, script, ref, tol in t2cases:
            rows.append(TAB.join([
                "T2_%s_%s" % (tree, cid), "T2_runtests_reference",
                "python3 -B testing/d003/stage_relr1/relr1_t2.py %s %s" % (tree, cid),
                "$EV/run/t2/%s/%s" % (tree, cid), "600", "PASS", "PASS",
                "REFERENCE_NUMDIFF_%s" % tol,
                "run $TREES/<T>/build/S4 on %s, numdiff against committed %s (independent reference)" % (script, ref)]))
        rows.append(TAB.join([
            "T2_%s_runtests_sh" % tree, "T2_runtests_reference",
            "python3 -B testing/d003/stage_relr1/relr1_t2.py %s script" % tree,
            "$EV/run/t2/%s/script" % tree, "600", "PASS", "PASS", "STATUS_EQUAL",
            "run the project's own testing/runtests.sh with its committed testcases.txt on $TREES/<T>"]))
    # ---------------- T3
    for rel in run_rels:
        for tree in ("B", "F4"):
            for pas in ("1", "2"):
                rows.append(TAB.join([
                    "T3_%s_%s_p%s" % (eid(rel), tree, pas), "T3_examples",
                    "python3 -B testing/d003/stage_relr1/relr1_examples.py run-unit --example %s --tree %s --pass %s" % (rel, tree, pas),
                    "$EV/run/%s/%s/%s" % (tree, pas, eid(rel)), "3600",
                    "RECORD_ONLY" if tree == "B" else "NO_LOSS",
                    "RECORD_ONLY" if tree == "B" else "NO_LOSS",
                    "BYTE_IDENTICAL_ELSE_NUMDIFF_1E-12",
                    "B pass => F4 must pass; stdout/stderr byte-identical; else numdiff 1e-12; B fail + F4 fail = BOTH_FAIL%s" %
                    ("; reference file exists, also numdiff vs reference tol " + EX_TOL[rel] if rel in EX_TOL else "")]))
    # ---------------- SKIP_DECLARED (before running)
    for rel in skip_mpi:
        rows.append(TAB.join([
            "T3_%s_SKIP" % eid(rel), "T3_examples",
            "not run", "NA", "0", "SKIP_DECLARED", "SKIP_DECLARED", "SKIP_DECLARED",
            "MPI_example script needs an MPI build (mpicc/S4mpi); this environment has no MPI (task brief section 4)"]))
    rows.append(TAB.join([
        "T8_F4_d003_e2e42", "T8_d003_smoke_optional",
        "not run", "NA", "0", "NA", "SKIP_DECLARED", "SKIP_DECLARED",
        "T8 is optional in task brief section 5; S5R3 is already signed off (U391); repeating the 42 injection points would need a new copy of the S5R3 E2E apparatus and is not needed for the non-regression conclusion of this round"]))
    # ---------------- U (record only)
    rows.append(TAB.join([
        "U_T2_record", "U_reference_only", "not run (U_BUILD_UNAVAILABLE)", "NA", "0",
        "NA", "NA", "RECORD_ONLY", "U tree 7fd00a2 does not build in this environment (old S4/main_lua.c vs its own headers; pyext needs 'python'); task brief section 3.2/5 allows recording and continuing"]))
    rows.append(TAB.join([
        "U_T3_record", "U_reference_only", "not run (U_BUILD_UNAVAILABLE)", "NA", "0",
        "NA", "NA", "RECORD_ONLY", "same as U_T2_record; U is the upstream original master and is recorded only, U vs B differences belong to P04"]))
    # ---------------- T4/T5/T6/T7
    rows.append(TAB.join([
        "T4_F4_p04_pipeline", "T4_p04_pipeline",
        "python3 -B testing/d003/stage_relr1/relr1_t4.py", "$EV/p04run/F4", "7200", "NA", "PASS",
        "AGGREGATE_JSON_PASS", "sh $TREES/F4/testing/p04_run_all.sh $EV/p04run/F4, then AGGREGATE.json verdict; run last (it rebuilds the F4 tree)" ]))
    for tree in ("B", "F4"):
        for name, path in (("p04_aggregate", "testing/p04_aggregate_test.py"), ("d002", "testing/d002/test_run_d002.py")):
            rows.append(TAB.join([
                "T5_%s_%s" % (tree, name), "T5_p04_unit_tests",
                "python3 -B testing/d003/stage_relr1/relr1_t5.py %s %s" % (tree, name),
                "$EV/run/t5/%s/%s" % (tree, name), "1800", "PASS", "PASS", "STATUS_EQUAL",
                "python3 -I -B $TREES/<T>/%s with cwd under $EV; both trees must agree" % path]))
    for tree in ("B", "F4"):
        rows.append(TAB.join([
            "T6_%s_capi" % tree, "T6_c_api",
            "python3 -B testing/d003/stage_relr1/relr1_t6.py %s" % tree,
            "$EV/run/t6/%s" % tree, "1200", "PASS", "PASS",
            "BYTE_IDENTICAL_ELSE_NUMDIFF_1E-12",
            "build examples/C_api/main.c with the Linux libraries (the shipped Makefile is macOS-only), run spec.awk 36 frequencies, compare with spec.awk.out and across trees"]))
    rows.append(TAB.join([
        "T7_clone_maketest", "T7_fresh_clone",
        "python3 -B testing/d003/stage_relr1/relr1_t7.py", "$EV/clone/relr1", "7200", "NA", "PASS",
        "MAKETEST_UNIT_STATUS",
        "git clone $REPO $EV/clone/relr1 (source read-only) then make test once; unit status set must equal T1 F4"]))
    out = os.path.join(EV, "PREREG_RELR1.tsv")
    if not os.path.realpath(out).startswith(os.path.join(REPO, "checkpoints/p05") + os.sep):
        raise SystemExit("WRITE_OUTSIDE " + out)
    data = (NL.join(rows) + NL).encode("utf-8")
    open(out, "wb").write(data)
    sha = hashlib.sha256(data).hexdigest()
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    shaf = os.path.join(EV, "PREREG_RELR1.tsv.sha256.txt")
    open(shaf, "w", encoding="utf-8").write(
        "# PREREG_RELR1.tsv.sha256.txt -- sha256 of the pre-registration written before any formal run" + NL +
        "# algorithm: sha256; unit: bytes; UTC: " + utc + NL +
        "PREREG_RELR1.tsv" + TAB + sha + TAB + "bytes=%d" % len(data) + TAB + "utc=" + utc + NL)
    n = len(rows) - 7
    print("PREREG rows=%d sha256=%s" % (n, sha))
    print("WROTE " + os.path.relpath(out, REPO))
    print("WROTE " + os.path.relpath(shaf, REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
