# P04 targeted tests: D001 (physics) and D002 (RNP workspace / status)

Scope of this change set (see `checkpoints/p04/` for the run evidence):

| item | code | test |
|---|---|---|
| D001 zgebak permutation index (left and right) | `S4/RNP/Eigensystems.cpp` | `testing/d001/` |
| D002 zhseqr status received; NULL z offset; workspace ownership; failure not installed; error 20 propagated rcwa -> S4 -> Python / Lua / C | `S4/RNP/Eigensystems.cpp`, `S4/rcwa.cpp`, `S4/rcwa.h`, `S4/S4.cpp`, `S4/main_python.c`, `S4/main_lua.c`, `S4/S4_internal.h` | `testing/d002/`, `testing/s4test/error20/` |

Not in this change set: the GetWaves rewrite, the geom helper removal, cubature, the
dead `ConvertUnits`, `SolveInParallel` cleanup, and every other item of the 102-item
landing patch.

## One-command verification

From a clean checkout of the product branch:

```sh
sh testing/p04_run_all.sh /path/to/new-run-dir     # the directory must not exist or be empty
echo $?                                            # 0 only when the aggregate verdict is PASS
cat /path/to/new-run-dir/STEPS.txt                 # raw return code of every step
cat /path/to/new-run-dir/AGGREGATE.json            # per-step classification and reason
```

The script exports the base commit `963ccf1` into the run directory, builds candidate
and baseline (clean `build/`), builds a test-only seam library of the candidate
(`build-seam/`, never used for the normal products), and runs every check below.
Each check writes its own JSON summary.  Raw return codes are never rewritten.  The
last step, `testing/p04_aggregate.py`, classifies each step as `ok`, `expected_defect`
(a baseline that reproduces the registered defect: rc 1 and its judgement shows the
defect signature with the controls passing) or `unexpected`.  The exit status is the
aggregate verdict: 0 only when every step is `ok` or `expected_defect` and every
expected step is present once.  A baseline rc 0, a crash code, a missing judgement or
a changed signature all fail the run.

## Layout

* `testing/d001/` — `model_d001.py` (model builder, no S4 import), `oracle_d001.py` /
  `oracle_d001_ext.py` (independent Airy/TMM and Fresnel references from the inputs
  only), `cases/d001_first_matrix.json` (frozen 12-case matrix),
  `run_d001_matrix.py` (frozen matrix, absolute tolerance 1e-10),
  `run_d001_extension.py` (frequency, incidence, polarization, basis, memory mode).
* `testing/d002/` — `tools/d002_driver.cpp` (drives the real `Eigensystems.cpp` through
  `-DD002_SRC`; the RNP-level status seam is compiled only with `-DD002_TEST_SEAM`, which
  renames the single definition in a derived copy), `PLAN.json` (frozen 59 cases and
  thresholds: eig_rel_tol 1e-10, residual_tol 1e-10, vector_norm_tol 1e-12, query work[0]
  == 2n), `cases/matrices.json` (fixed matrices and analytic eigenvalues),
  `run_d002.py` (build / run / judge / positives).
* `testing/d002/test_run_d002.py` — negative and positive tests of the judge (137 tests).
  The formal fixture is the schema-2 control run `tests/fixtures/p04_schema2_control.tar.gz`
  (real saved driver output of all six variants, plus the D001 summaries and the sanitizer
  positives).  `tests/fixtures/*_legacy_run.tar.gz` are schema-1 runs, read only by
  `LegacyRunTests` with the explicit request.
* `testing/p04_aggregate.py` and `testing/p04_aggregate_test.py` — the aggregate verdict
  and its failure-injection tests.  The control is the real fixture: the D002 judgements
  are recomputed from the raw driver output and must agree with each recorded judgement;
  the artifact manifest is checked against the files on disk.  Only the STEPS return codes
  are written by the test.
* `testing/s4test/error20/` — `run_error20.py` (Python in process, Lua and C in fresh
  processes, seam build), `error20_lua.lua`, `error20_lua_parallel.lua` (SolveInParallel,
  one and two objects, with and without injection), `error20_capi.c`, `link_seam_ext.py`.
* `testing/s4test/test_seams/seam.h` — the S4-level injection header (`S4_TEST_EIGEN_INFO`).
  It is found through the test build's include path only; a normal build neither defines
  `S4_TEST_EIGEN_INFO` nor reads this file.

## Judgement rules (fixed before the runs)

* D001: |R - R_ref| <= 1e-10 and |T - T_ref| <= 1e-10, finite values, incident flux > 0.
  R_ref, T_ref come from the physical inputs (f, d, eps, angle, polarization).
* D002, integrity first (every non-probe case): normal exit (RUN_INDEX rc is 0), empty
  stdout (schema-2 runs), strict output grammar (no duplicate or unknown record, finite
  numbers only, complete file ending in driver_rc), identities that match the case
  (case_id, entry, matrix, variant, n, lda, seam fields, reported layout and capacities,
  exact vector index sets including unrequested outputs), and no sanitizer line other than
  a registered UBSan report form (`UBSAN_REPORT_RE`: the RNP pointer-offset forms seen in the
  saved asan_baseline A-38 runs).  Any other sanitizer text is an unsupported report, not a
  defect.
* D002, abnormal exit (rc non-zero): the .out may be empty or cut short.  Every complete
  line must parse and every identity, seam or layout record present must match the case;
  an unterminated last line is accepted only as a prefix of its expected value.  The exit
  is a defect only as a registered mechanism: SIGABRT with the glibc diagnostic, or an
  AddressSanitizer report of a registered kind (rc 1).  SIGSEGV is not registered for any
  judged case; the saved A-10r SIGSEGV is a recorded contract probe only.
* D002, verdict (judged cases only): eigenvalues as a multiset, error / max|lambda_ref|
  <= 1e-10; right and left residuals / (max|A| ||v||) <= 1e-10; | ||v|| - 1 | <= 1e-12;
  padding rows keep 0+0i; info == 0 unless the case injects a status; query work[0] == 2n
  exactly; HELPER_GEBAK compares every element of v as a complex number with an
  independent 1-based LAPACK model of zgebak (scaling, then permutation) on the zgebal
  ilo/ihi/scale, after the producer output itself is checked against the zgebal convention.
  A-10r is a registered contract probe and is recorded, not judged.
* D002 run scope: RUN_INDEX `scope` is `full` (all 59 cases, the only scope that can
  accept) or `subset` (`run --cases`, a targeted diagnostic that is never accepted).
  Formal judging accepts RUN_INDEX schema 2 only.  Schema-1 (legacy 2026-10-09) runs,
  including a run without a schema field, are judged only with
  `run_d002.py judge --allow-legacy-schema1`, for re-judging historical data.
* D002 baseline signature: a must-fail or may-fail case shows the defect only through a
  judged verdict failure or a registered mechanism (abnormal exit, sanitizer report).
  A missing, malformed, truncated, driver-error or wrongly identified record never
  shows the defect, whatever the case's classification.  Round-5 correction (asan_baseline
  only): A-07 moved from must-fail to may-fail, because its saved observations are both
  info 0 (pass) and non-zero (fail); seam_asan_baseline A-07 stays must-fail.  See
  `checkpoints/p04-remediation/REMEDIATION_REPORT_ROUND5.md`.  Self-audit correction of
  2026-10-10 (not independently reviewed; asan_baseline only): A-36 moved from must-pass to
  may-fail, because the same uninitialised `info` either gives info 0 (pass) or crashes in
  RescaleMatrix at Eigensystems.cpp:4715 (ASan SEGV, 17 of 26 reruns).  Such a crash counts
  as the defect only at that registered site (`REGISTERED_SITES`); seam_asan_baseline A-36
  stays must-fail under the same site rule.  Evidence and limits:
  `testing/d002/evidence/A36_RULE_CORRECTION.md`.
* D001 summaries are checked as a complete set: every expected case key exactly once with
  its identity; a baseline's failures must be exactly the registered defect set (frozen:
  N9 B/C; extension: N9/N25 B/C and the memory-mode rows) and every other row must pass.
* Sanitizer positives: each of the three controls once, its stderr containing its
  signature.
* Artifacts: every label in the manifest must be present once with its SHA-256, and the
  file must exist and hash to that value when the aggregate runs.
* error 20: Python raises RuntimeError with "could not be solved"; Lua exits non-zero with
  the same message on stderr (the non-interactive frontend aborts); C returns 20; a
  retry on the same object after clearing the environment, and a fresh object, both give
  the reference flux.
