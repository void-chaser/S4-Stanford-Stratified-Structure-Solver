# P05 D003: FMM/FFT failure propagation to the public API

Product-branch summary. This document describes the source change carried by branch
`p05/d003-fft-error-propagation`; it is written from the P05 commit diff and the P05 phase
reports only. It does not add any verification claim.

## 1 Provenance

* Baseline **B**: upstream master `5b72793` (S4 tree `1d738e64f9864a475fdb3de34cd3601605df2c64`).
* Fix tree **F4**: P05 commit `3de6d8b` (S4 tree `589e15eb11fcb04e031b524f25a443e7921946cf`).
* This branch = B plus exactly the ten-file S4 delta `git diff 5b72793 3de6d8b -- S4`
  (+311 / -80). Nothing outside `S4/` was taken from F4 except this document.
* The P05 audit trail (reports, registries, evidence, gate scripts) is not part of this branch;
  it lives on the archive branch and tags listed in section 6.

## 2 Problem

The failure paths of the FMM/FFT epsilon generation, the layer-mode machinery and the pattern
intersection code either dereferenced a failed allocation (crash) or ignored an error status and
continued with unsolved or unwritten data, then returned success to the public API. Several
`RNP::LinearSolve` calls also passed `NULL` for the `solve_info` output and so discarded a zero
pivot. Because the public Lua/Python API reports only a small set of error codes
(`S4_internal.h`: 1 = memory allocation error, 20 = layer eigensystem failure), an untended
failure was observable as a crash or as silently wrong output.

The change makes each such failure visible: every allocation and solver status on these paths is
checked, whatever was allocated is released exactly once, and the existing error code is propagated
to `Simulation_ComputeLayerModes` / `Simulation_InitSolution`, where the public API turns it into
an error.

## 3 Per-file changes (from the diff)

| File | Change | Intent |
|---|---|---|
| `S4/S4_internal.h` | `Simulation_AddFieldToCache` returns `int`; comment for code 20 updated | The cache insertion can fail; its callers must see that. Code 20 now says the failed layer has no modes while earlier layers may keep theirs. |
| `S4/S4.cpp` | `Simulation_InitSolution`: check the `pattern.parent` allocation (only when `nshapes > 0`), map containment-tree `-4` to 1, allocate the solution into a local and assign it only after all three allocations succeed, free partial allocations on failure. `Simulation_ComputeLayerModes`: check `LayerModes`, `q`, `rwork` and `work`, discard the modes and return 20 on failure; collect the FMM epsilon return codes and stop with 20. `Simulation_AddFieldToCache`: return 1 instead of dereferencing NULL. | A failed allocation is reported as 1/20 instead of crashing. |
| `S4/fmm/fmm_FFT.cpp` | Check `work`, `discval`, the five FFT plans, `Pattern_DiscretizeCell` return `-12`, each `fft_plan_exec` and the `LinearSolve` status; one cleanup label; return the accumulated status. | Report allocation and solver failures to the caller instead of continuing. |
| `S4/fmm/fmm_PolBasisJones.cpp` | Check `ivalues`, `work`, `vfield` and the FFT plan, the four `fft_plan_exec` calls, `Simulation_AddFieldToCache` and the `LinearSolve` status; free on every error path; return the status. | Same; the field-cache insertion failure must not be lost. |
| `S4/fmm/fmm_PolBasisNV.cpp` | Same checks as Jones; the `Pattern_GenerateFlowField` error check is moved before the field is normalised, so an unwritten field is never read. | Same; ordering fix inside the error path only. |
| `S4/fmm/fmm_PolBasisVL.cpp` | Same checks as Jones. | Same. |
| `S4/fmm/fmm_closed.cpp` | Check `ivalues` and each of the four `LinearSolve` statuses before the next statement overwrites or reads their result. | A zero pivot is reported instead of a partially solved epsilon matrix. |
| `S4/fmm/fmm_experimental.cpp` | Check `ivalues` before `values` is derived from it; return 20. | Same; the P05-S5 report records this path as driver-unreachable and verified by static reading only. |
| `S4/fmm/fmm_kottke.cpp` | Same allocation/plan/`-12`/exec/`LinearSolve` checks as FFT; add a non-finite check on the averaged `Epsilon2` / `Epsilon_inv` before returning success; cleanup label. | Report non-finite averaged tensors instead of passing them to the eigensolver. |
| `S4/pattern/pattern.c` | New status-reporting variant of the intersection-area helper; `pattern_discretize_cell` returns `-12` on a failed triangle-index allocation; containment tree returns `-4` on a failed area allocation; `cg` / `sparse_linsolve_d` return a status; the flow-field helpers return `-1.0` on allocation failure, mapped to `-11` by `pattern_generate_flow_field`, which also returns `-10` for a zero or non-finite maximum. | Same principle in the pattern layer: failures are reported through the existing status channels instead of being ignored. |

## 4 Verification summary (quoted from the P05 reports)

From the P05 delivery round REL-R1 (non-regression of F4 against B, same compiler and flags):
`SAME=317`, `BOTH_FAIL=12` (all pre-existing failures, identical on B), `SKIP_DECLARED=5`,
`NEW_FAIL=0`, `DIFF=0`, `FLAKY=0`, `unit_count=265`, and `NON_REGRESSION=PASS`. The three
independent references (simple, fresnel, Fan fig12) passed with the REL-R1 tolerances.

From P05-S5 R3 (public-API end-to-end points on F4): 42 points = 25 injected failure points
(Python 10, Lua batch 11, Lua REPL 4) + 17 no-injection controls; `CONTROL_OK=17`, `E2E_OK=25`,
and `FLAKY / INVALID / HIT_OFF_TARGET / API_SILENT / RETRY_* / MISSING_RUN` all zero. The D016
point family reported `MATCH=33 MISMATCH=0 FLAKY=0`.

**Dependency to note:** the injected points depend on the S5 fault-injection harness, which is
evidence and is *not* part of this branch. Without that harness the allocation-failure branches are
not reachable from the public API; REL-R2 therefore ships no D003-specific regression test (see the
REL-R2 report for the candidates that were checked).

## 5 Known limitations

1. Independent reference data exist only for the three REL-R1 T2 cases (simple, fresnel, Fan fig12);
   the other examples are compared against B, not against an independent reference, so
   "F4 output equals B output" is not a statement about physical correctness.
2. REL-R1 ran with Python 3.14, the system LAPACK/BLAS 3.12.1 and no MPI; the upstream reference
   tree U (`7fd00a2`) could not be built in that environment.
3. Eleven examples fail in B and in F4 in the same way (existing failures): `GetRealMaterial`
   no longer exists, two scripts have Lua syntax errors, four convergence scripts fail on the
   singular interface system, five use `loadstring` (nil in Lua 5.2), one existing failure in
   `magneto/slab`.
4. `examples/C_api` ships a macOS-only Makefile and uses pre-P04 C API names; it does not build here
   (roadmap item P13). This environment also has no MPI, so `examples/MPI_example` is out of scope.
5. REL-R2 did not re-run the REL-R1 example matrix on this branch; the non-regression evidence is
   REL-R1 on F4, whose `S4/` tree is byte-identical to this branch, with the same `Makefile*` and
   `examples/` as B.

Transferred items, not fixed on this branch:

* **D017** — remaining non-FMM `S4_malloc` call sites are outside the D003 scope.
* **R-P05-01** — a VL-basis `n_G=1` configuration is uncomputable; changing it would be a behaviour
  change, not a failure-propagation change.
* **R-P05-02** — existing pathologies in the containment tree and dead pattern helpers, left OPEN.
* **R-P05-03** — `Pattern_DiscretizeCell` return values other than `-12` are still not reported by
  the FFT/Kottke callers.

## 6 Where the audit records live

The complete P05 audit (phase reports, decision register, registries and evidence) is kept on the
archive branch `archive/p05-d003-full-20261019` and on the annotated tags
`p05-signed-20261019` (P05 S1-S5 sign-off, commit `3de6d8b`) and `p05-rel-r1-20261019`
(REL-R1 non-regression, commit `c88bf30`). At the time of writing those refs exist only in the
local repository and are **pending the REL-R3 push**.
