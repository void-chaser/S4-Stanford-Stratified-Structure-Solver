# REPAIR_PROPOSAL_R6d.md -- P05-S4 R6d-4 repair proposal, v2 (U4, U22, U27; supersedes the R6c2 proposal for RNV1)

**Status: PROPOSAL ONLY.  No code was changed.  S4/ is NOT changed in R6d.**  Changing S4/ needs explicit user approval (AGENTS.md section 4; U25).
Nothing here is a verification of a repair.  "expected category after repair" entries are predictions to be tested in the S3 closing round (S3R3) and in R7 on the new tree F2 (U25).
Location and timing of the repairs are the user's decision (U4).

Source of the red points: RED_POINTS_LEDGER_R6d.tsv (v2).  Facts of R6d: RNV1 injection 72/72 rows CRASH (rc 139), passes 1 and 2 (run2), see RESULTS_R6d_RNV1_pass{1,2}_run2.tsv.

---

## A. F_CONFIRMED: RP-R6d-1 (RNV1, pattern work/iwork malloc without NULL check)

### A.1 Facts (measured in R6d; source read in tree F = HEAD:S4 = 4a6f649...)

| item | file:line | code (as read) | measured |
|---|---|---|---|
| malloc 1 (rect) | `S4/pattern/pattern.c:1477` | `double *work = (double*)malloc(sizeof(double)*N2*(5+2));` | used at 1478 (`x = work`) with no NULL check |
| malloc 2 (rect) | `S4/pattern/pattern.c:1481` | `int *iwork = (int*)malloc(sizeof(int)*N2*4);` | used at 1482 (`Mcol = iwork`) with no NULL check |
| malloc 3 (tri) | `S4/pattern/pattern.c:1656` | `double *work = (double*)malloc(sizeof(double)*N3*(11+2));` | used at 1657 |
| malloc 4 (tri) | `S4/pattern/pattern.c:1660` | `int *iwork = (int*)malloc(sizeof(int)*N3*10);` | used at 1661 |
| first unchecked use | `S4/pattern/pattern.c:1498` | loop writing `x`/`b`/`M` (gdb: SIGSEGV here) | [measured: gdb backtrace, rnv1_run2/F/*/gdb.log, frame `pattern_generate_flow_field_rect`] |
| caller chain | `pattern.c:2133` (rect call), `pattern.c:2168` (Pattern_GenerateFlowField) | | [measured: gdb frames #1, #2] |
| injection result | RESULTS_R6d_RNV1_pass1_run2.tsv, pass2_run2 | 72 rows, rc 139, signal 11, class CRASH, MATCH | both passes; F and B |

Caveat (not verified): R6d did not run a build with the fix; the rc that a fixed tree returns is not measured.

### A.2 Two candidate repairs (the choice is the user's; U4)

The function `pattern_generate_flow_field_rect` / `_tri` return `double max_field` (pattern.c:1464, 1643; return at 1638 and 2086).  The caller `pattern_generate_flow_field` (2089) treats a non-positive or non-finite maximum with `return -10` (pattern.c:2148-2150, the D016 path, S3R2 D-D).

**Option R1 (minimal, reuses the existing error path; semantics to be decided by the user):**
- file:line: `S4/pattern/pattern.c:1477-1482` and `1656-1661` (4 malloc sites, two functions).
- minimal change: after each malloc, `if(NULL == work || NULL == iwork){ <free the other one>; return 0.; }` so that the caller's `!(max_field > 0)` check at 2148 returns -10.
- changed lines: about 4 added `if` blocks (about 8-12 lines).  No change to the signature.
- caveat: this makes an allocation failure look like the D016 error (-10, "zero maximum").  Whether that is acceptable is the user's decision.  [未验证]: whether any other caller relies on 0. from these functions.

**Option R2 (explicit error code; needs a signature change):**
- change `_rect` / `_tri` to return an int status and an output parameter for max_field; `pattern_generate_flow_field` returns a new code (for example -11 "pattern allocation failed"; the code must be chosen so that it is not used elsewhere: -9 is taken by pattern_discretize_cell, per pattern.c:2147).
- changed lines: about 20-30 (signature, returns, the caller).  Larger; needs a review.
- caveat: the new code value is a choice, not a fact; the caller chain above (FMMGetEpsilon_PolBasis* at fmm_PolBasis*.cpp:140/185/147, which return the code unchanged) must still map it to a layer failure (rc 20) [源码 for NV at fmm_PolBasisNV.cpp:144-149; Jones and VL only the trace line read].

### A.3 Regression point_ids (for the S3R3 round and R7 on F2)

| point set | point_id | expected after repair |
|---|---|---|
| RNV1 injection (new point, R6d) | RNV1-F-nv-ng1-m1 ... RNV1-F-vl-ng9-m3 (72 F rows) | not CRASH (rc != 139); under option R1 rc = -10 -> 20 at ComputeLayerModes; under option R2 the new code -> 20; to be measured |
| normal runs (no injection) | nv, vl, fftnv, fftvl rows of the R6d count set (count/*_noinject.out) | unchanged rc (nv NG9 rc 0; vl NG1 rc 20 with pattern -10 x3, the D016 path) |
| the 177 state points, nv/vl entries | M-*-nv-*, M-*-vl-* (registries/s4r6c RESULTS_R6c_STATE.tsv) | HOLD 177 (the pattern malloc is not on these injection paths; expected unchanged, to be re-run in R7) |

### A.4 Expected category after repair (prediction; to be tested)
RNV1 injection: from CRASH (F, measured) to REPORTED_FAILURE (rc non-zero, no signal) under either option.  B is not changed (B is not a repair target).

---

## B. Comment wording (U11, HARNESS_OR_PROCESS; RP-R6d-10 and RP-R6d-9)

| item | content |
|---|---|
| file:line | `S4/S4_internal.h:263` [源码]: `// 20 - the layer eigensystem failed; no layer modes or solution were installed` |
| why | layers computed before the failing layer keep their modes (E6-8, measured: I2 HOLD 177/177 and 25/25; layer 0/2 installed at failure in the R6-2 single-point probe) |
| minimal change | replace the comment text with: `// 20 - the layer eigensystem failed; the failed layer has no modes; layers computed before it may keep their modes` (the wording of E6-8; to be confirmed by the user) |
| changed lines | 1 (comment only) |
| regression | none for behaviour; `git diff` must show only line 263 |
| expected category | unchanged (HOLD) |
| approval | needs user approval to change S4/ (U11: fixed in the S3 closing round) |

---

## C. Items not proposed for repair in R6d

- RP-R6d-2 .. RP-R6d-5, RP-R6d-12: closed by rulings or by measurement (no S4/ change).
- RP-R6d-6, RP-R6d-7 (BASELINE_ONLY): observations on the unrepaired baseline B; not repair evidence (AGENTS section 5).  No repair proposed.  RP-R6d-7 (D016 B-side origin) is open.
- RP-R6d-8 (K-1, F_SUSPECT_SOURCE): needs a check design (R8); no repair proposed before the check.  The tensor branch of ClosedForm (fmm_closed.cpp:244) is the analogous site [源码].
- RP-R6d-11 (U14-OBS), RP-R6d-19, RP-R6d-20: observations; no repair.
- RP-R6d-13 .. RP-R6d-17 (DEFERRED, HARNESS_OR_PROCESS): tests not yet run (U9, U20, U25 -> R8); no repair.
- RP-R6d-18 (S5-MALLOC): out of D003 scope; S5 registry.

---

## D. Order (U25; the user decides)

1. user decides: whether S3-4b is closed (U21 conditions + U28 coverage), which of R1/R2 for RNV1, and the wording of S4_internal.h:263 (U11).
2. P05-S3 sub-round S3R3: repair in S4/ only after the user's approval (A and B above).
3. freeze a new tree F2 (no new round number is created by this proposal).
4. P05-S4 R7 on F2: regression of the matrices R3, R4, R5 (M=2), R6-1, R6c (177 points), R6c seam (25 points), R6d RNV1.
5. P05-S4 R8 on F2: supplementary tests (items of U25).

## E. Statement of what is NOT established

- No repair is verified.  No F2 tree exists.  No stage is declared complete or signed off (AGENTS section 2).
- The choice R1/R2 is not made by the executor.
