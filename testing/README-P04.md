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
sh testing/p04_run_all.sh /path/to/new-run-dir
cat /path/to/new-run-dir/STEPS.txt        # one line per step with its return code
```

The script exports the base commit `963ccf1` into the run directory, builds candidate
and baseline (clean `build/`), builds a test-only seam library of the candidate
(`build-seam/`, never used for the normal products), and runs every check below.
Each check writes its own JSON summary; the baseline is expected to fail the
D001 and D002 cases that exercise the defects, and that record is the evidence.

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
* `testing/s4test/error20/` — `run_error20.py` (Python in process, Lua and C in fresh
  processes, seam build), `error20_lua.lua`, `error20_capi.c`, `link_seam_ext.py`.
* `testing/s4test/test_seams/seam.h` — the S4-level injection header (`S4_TEST_EIGEN_INFO`).
  It is found through the test build's include path only; a normal build neither defines
  `S4_TEST_EIGEN_INFO` nor reads this file.

## Judgement rules (fixed before the runs)

* D001: |R - R_ref| <= 1e-10 and |T - T_ref| <= 1e-10, finite values, incident flux > 0.
  R_ref, T_ref come from the physical inputs (f, d, eps, angle, polarization).
* D002: eigenvalues as a multiset, error / max|lambda_ref| <= 1e-10; right and left
  residuals / (max|A| ||v||) <= 1e-10; | ||v|| - 1 | <= 1e-12; info == 0 unless the case
  injects a status; HELPER_GEBAK output equals an independent 1-based LAPACK model of
  zgebak (scaling, then permutation) on the zgebal ilo/ihi/scale. Sanitizer reports
  count as failures. A-10r is a registered contract probe and is recorded, not judged.
* error 20: Python raises RuntimeError with "could not be solved"; Lua exits non-zero with
  the same message on stderr (the non-interactive frontend aborts); C returns 20; a
  retry on the same object after clearing the environment, and a fresh object, both give
  the reference flux.
