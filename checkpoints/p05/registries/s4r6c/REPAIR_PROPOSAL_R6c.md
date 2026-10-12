# REPAIR_PROPOSAL_R6c.md -- P05-S4 R6c2-3 repair proposal (input of the later S3 closing repair round, U22)

**Status: proposal only.  No code was changed.  S4/ is NOT changed in R6c2.**  Changing S4/ requires explicit user approval (AGENTS.md section 4).
Nothing here is a verification of a repair.  The "expected category after repair" entries are predictions to be tested in that round, not results.

Scope of this proposal: (A) F-confirmed candidates from R6c2 (none found, stated below); (B) comment wording (U11); (C) RNV1, the pattern malloc without NULL check (source fact, not run).

---

## A. F_CONFIRMED candidates from R6c2

**None.**  The 177-point state run (R6c, two passes) and the 25-point seam run (R6c2, two passes) gave 0 VIOLATED, 0 FLAKY and 0 GDB_DIVERGENT.
The only F-side items that remain are in B (comment wording) and C (RNV1, not run).  Therefore no repair of S4/ logic is proposed on the basis of R6c2 data.

Evidence for the zero count:
- checkpoints/p05/registries/s4r6c/STATE_SUMMARY_R6c.txt (177 points, pass 1 and pass 2: HOLD 177)
- checkpoints/p05/evidence/p05-s4r6c/STATE_SUMMARY_R6c_SEAM.txt (25 points, pass 1 and pass 2: HOLD 25)

---

## B. Comment wording (U11, HARNESS_OR_PROCESS, E6-8)

| item | content |
|---|---|
| file:line | `S4/S4_internal.h:263` ([源码]: `// 20 - the layer eigensystem failed; no layer modes or solution were installed`) |
| why | Under the failure of layer 1 (Slab), layers 0 and 2 that were computed earlier DO have modes installed (E6-8, E6b-1). The sentence reads literally as "no layer modes installed", which conflicts with that. |
| minimal change | Replace the comment text on line 263 with: `// 20 - the layer eigensystem failed; the failed layer has no modes; layers computed before it may keep their modes` (wording to be confirmed by the user; the proposal is the wording of E6-8). |
| changed lines | 1 (comment only; no code) |
| regression point_id | none needed for behaviour (comment only).  Check: `git diff` shows only line 263; a build of libS4.a is not required for a comment change, but if run, the sha256 changes and must be recorded. |
| expected category after repair | not applicable (no behaviour change; the 177-point and 25-point categories must stay HOLD) |
| approval | **needs user approval to change S4/** (U11: "fixed later, in the S3 closing repair round") |

---

## C. RNV1: pattern work malloc without NULL check (source fact; injection NOT done; U16 defers RNV1 to R7)

Source facts ([源码], read in R6c2; no run):

| item | file:line | code (as read) | note |
|---|---|---|---|
| 1 | `S4/pattern/pattern.c:1477` | `double *work = (double*)malloc(sizeof(double)*N2*(5+2));` | next use at 1478 (`x = work`), no NULL check in between |
| 2 | `S4/pattern/pattern.c:1481` | `int *iwork = (int*)malloc(sizeof(int)*N2*4);` | next use at 1482 (`Mcol = iwork`), no NULL check |
| 3 | `S4/pattern/pattern.c:1656` | `double *work = (double*)malloc(sizeof(double)*N3*(11+2));` | next use at 1657 (`x = work`), no NULL check |
| 4 | `S4/pattern/pattern.c:1660` | `int *iwork = (int*)malloc(sizeof(int)*N3*10);` | next use at 1661 (`Mcol = iwork`), no NULL check |
| 5 | `S4/pattern/pattern.c:415, 528` | `int *tri = (int*)malloc(...)` | not read in R6c2; out of the RNV1 list |
| 6 | `S4/pattern/pattern.c:806, 1164, 1251` | `area`, `target`, `work` mallocs | not read in R6c2 for NULL checks; listed for completeness |

Runtime fact from R5 (not from R6c2): on nv runs the pattern call stack has 3 malloc calls, identical for B and F (checkpoints/p05/P05_S4R5_REPORT.md section 4.4).  The injection of RNV1 was NOT run (U16).  The expected behaviour (a segmentation fault before the -10 path) is a prediction recorded in R5, not an observation.

| field | proposal |
|---|---|
| minimal change | after each of the four malloc lines, check the pointer and return an error through the existing error path of pattern_generate_flow_field.  The exact return value and the error path are **未验证** (not checked in R6c2; the -10 seen on F in R5 is a value of the D016 path, not a verified design for this check).  Each check is 2-3 lines.  The 4 checks = about 8-12 changed lines (estimate, from the line counts above). |
| file:line | pattern.c:1477-1481 and pattern.c:1656-1660 |
| regression point_id | the nv points of the 177 set (M-once-nv-*, M-twice-nv-*, state runs) and the RNV1 injection point to be designed in R7 (not yet defined) |
| expected category after repair | REPORTED_FAILURE (rc non-zero under injection) for the RNV1 injection; HOLD for the 177 nv points (no change under normal runs) |
| approval | **needs user approval to change S4/**.  Not in R6c2. |
| caveat | This is a proposal from source reading.  Whether the fix is correct depends on what pattern_generate_flow_field returns to its caller; that is not verified here. |

---

## D. Items not proposed for repair

- RP-R5-1, RP-R5-2, RP-R5-3, RP-R5-4, E6-3, E6-4: closed or downgraded by rulings (see the ledger); no S4/ change.
- Non-FMM S4_malloc sites: outside D003 (scope decision); S5 registry.  No repair proposed in this round.
- B-side SILENT_SWALLOW (jones, vl, fft, kottke) and CRASH (nv, fft, closed, jones, kottke, vl): these are observations on the unrepaired baseline B (not repair evidence, AGENTS section 5).  No repair proposed.

---

## E. R7 candidate list (for the user's decision on R7 scope)

| item | suggested method | dependency |
|---|---|---|
| R7-1 RNV1 injection (U16) | a new injector (new file, not in S4/) that makes the pattern work malloc return NULL at the first call; observe rc; the expected -10 path is in question | needs the RNV1 injector design; the -10 path must be traced from pattern_generate_flow_field |
| R7-2 other-layer failure variants (U20) | two layers with a pattern, or the pattern layer not at position 1; re-run I1-I6 | needs the state runner extended (R6c2 runner is per-layer-1 only) |
| R7-3 dual-target injection and I7 sanitizer (U9) | a second injection in the same run; sanitizer build | needs a new injector and a sanitizer build of tree F |
| R7-4 Python / Lua visibility of FMM failures (S3-4 handoff) | run the Python and Lua front ends with an injected failure; record the visible error | needs the front-end harness (not written) |
| R7-5 NB = 1 to 8 coverage (S3-4 handoff) | sweep NB 1..8 under injection | needs a sweep driver (not written) |
| R7-6 category C (intermediate-quantity error) | design a check of intermediate values after the failure | needs a definition of the quantity (not written) |
| R7-7 tensor path K-1 | extend K-1 check to the tensor route | needs K-1 check design (S3R2 section 3.4) |
| R7-8 D016 B-side rc 20 origin | trace the B-side return value of pattern_generate_flow_field | needs gdb on B |
| R7-9 seam I2/I3 N/A cases | decide whether N/A points (I2 N/A 2, I3 N/A 15) need another observation | needs a rule decision by the user |
