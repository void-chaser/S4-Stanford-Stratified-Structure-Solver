# M2 design, P05-S4 R8 M2a (section 4.3)

All expectations are design expectations (status INFLUENCED). No S4 run was made in this round.

## M2-00

- source: U231; section 4.1
- purpose: control for the three A_CTRL combinations under injection-free run
- method: A_CTRL combos closed2d-ng1, fft-ng5, kottke-ng5 on F2 and F3; M0 covers all six (crosswalk R2)
- driver_and_injector: existing driver d003 (M0 build); no new apparatus
- tree: F2, F3
- env_template: FMM_MODE=<m>;S4FMM_NG=<n>
- points: 0 (not required: all six covered by M0)
- expectation_basis: A10_CONTROL_CROSSWALK_R8_M2a_R2.tsv: 6 of 6 COVERED_BY_M0 (rc 0, call IDENTICAL)
- prereg_status: INFLUENCED
- judge_rule: CONTROL_OK expected; crosswalk status COVERED_BY_M0 on each row
- feasibility: FEASIBLE_EXISTING
- limitation: none for these six; the other 4 A-10 mismatches are a register error (U231)

## M2-01

- source: U232 (I1-I6 for 806/1729/415)
- purpose: I1-I6 state judgement on the 17 F3 repair injection points
- method: 17 injection points of ADD22 A-1..6 and B-11..21 with their env exactly as in ADDITIONS_MAPPING_22_R8_M1a6; state driver with win:/init: injector; two passes; judged by the G5 rule of R6c/R7 M3 (I1-I6, I7 DEFERRED)
- driver_and_injector: driver_r6b_state.cpp linked with inject_s3r4_init.cpp (init:) or inject_s3r4c3_poly.cpp (win:) [源码]; R8 M1 already linked init-F3 this way (link_s3r4_r8m1.sh, section 5.2); new copy driver_r8m2a_state_add.cpp only if the existing driver cannot link both injectors
- tree: F3
- env_template: as M1a6 row (FMM_MODE, S4FMM_NG, S4FMM_INJECT)
- points: 17 points x 2 passes
- expectation_basis: rule source: checkpoints/p05/registries/s4r6c/REGISTRY_S4_PRE_R6b_STATE_v2.tsv (I1-I6 definitions); R7 M3 G5 expectation HOLD (REGRESS_R7_M3.tsv); F2 not judged (806, 415 are CRASH on F2)
- prereg_status: INFLUENCED
- judge_rule: I1-I6 HOLD where applicable (G5 rule, R6b registry header lines 5-11); reported failure rc1 != 0 required
- feasibility: FEASIBLE_NEW_APPARATUS
- limitation: I1-I6 are judged on the state snapshots only; a win: point not reached is INVALID, not HOLD

## M2-02

- source: U5b, E6-4; ERRATA_6d.txt lines 50-70 (stage e)
- purpose: stage e: failure outside every ENTER/RETURN window
- method: list every candidate request; mark the source location and whether it is inside the D003 scope (U5b/E6-4)
- driver_and_injector: no injector call; analysis of stage_s4 requests (see M2_DESIGN_R8_M2a.md)
- tree: F3
- env_template: -
- points: 0 (no in-scope candidate found; see .md)
- expectation_basis: ERRATA_6d.txt 50-70 (definition); U5b/E6-4 (out-of-scope TWICE 12th plan call from GetFieldOnGrid)
- prereg_status: INFLUENCED
- judge_rule: NOT_FOUND_IN_SCOPE if all candidates are out of scope
- feasibility: NOT_FOUND
- limitation: the candidate search over stage_s4 requests has NOT been completed in M2a; status is not a result; the scope decision belongs to the user

## M2-03

- source: U2-10 (I7 DEFERRED); task brief 4.3 M2-03
- purpose: I7 sanitizer judgement for the F3 state points and the 17 repair points
- method: san_probe_r8m2a.sh (new): compile and run a non-S4 probe with -fsanitize=address,undefined; then F3 sanitizer library and state drivers in $EV/build/san/; points: each (mode x stage x inj_kind) cell once, plus the 17 F3 repair points
- driver_and_injector: new sanitizer build of build_r8m2a.sh (library + drivers under build/san)
- tree: F3
- env_template: as the corresponding state or ADD22 row; sanitizer flags via env
- points: one point per cell + 17 repair points (exact count in PREREG)
- expectation_basis: U2-10; R6c/R7 G5 stage cells
- prereg_status: INFLUENCED
- judge_rule: I7: sanitizer report count = 0 AND rc/class equal to the non-sanitizer run
- feasibility: FEASIBLE_NEW_APPARATUS
- limitation: sanitizer build not run in M2a (no S4 driver run); probe only

## M2-04

- source: U4/U5; M2 brief 4.3 M2-04
- purpose: dual-target injection: two failures in one run
- method: (a) same layer, two injections; (b) two layers, one injection each; inject_r8m2a_dual.cpp appends the second target; the original branches are unchanged (copy of inject_r4_plan.cpp)
- driver_and_injector: new inject_r8m2a_dual.cpp (copy with second-target logic) + driver_r6b_state.cpp
- tree: F3
- env_template: FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=<target1>|<target2>
- points: 2 per configuration (a and b)
- expectation_basis: no historical dual run; expectation rc != 0, no signal, I1-I6 by the M2-01 rule
- prereg_status: INFLUENCED
- judge_rule: rc1 != 0 and no signal; I1-I6 HOLD where applicable
- feasibility: FEASIBLE_NEW_APPARATUS
- limitation: no historical dual-target result: expectation is a design expectation only

## M2-05

- source: U20 (other layers)
- purpose: failure in layer 0, layer 2, or two pattern layers
- method: failure in the first or second of two pattern layers; driver_r8m2a_layers.cpp (new) for the two-pattern layout
- driver_and_injector: driver_r8m2a_layers.cpp (new) + inject_s3r4_init.cpp
- tree: F3
- env_template: FMM_MODE per layer config; S4FMM_INJECT=init:K
- points: 3 configs x 2 positions x 2 passes (exact in PREREG)
- expectation_basis: R6c REPAIR_PROPOSAL_R6c.md R7-2 (two layers not covered by the one-layer runner)
- prereg_status: INFLUENCED
- judge_rule: I1-I6 HOLD for the failing layer; other layers q-hash and control unchanged
- feasibility: FEASIBLE_NEW_APPARATUS
- limitation: layer count limited to the configs of the new driver

## M2-06

- source: RP-R6d-8; fmm_closed.cpp:244-245 [源码]
- purpose: K-1 tensor path: LinearSolve failure and the finiteness check
- method: FMM_MODE=tensor; inject a failure of the seam whose ID maps to fmm_closed.cpp:244 (linearsolve_null2 ID 244 is a candidate; the ID-to-line mapping is NOT yet verified, see limitation) and an allocation failure in the tensor path
- driver_and_injector: inject_r4_plan.cpp (linearsolve_null2:244:K) [源码]; driver_r6_state.cpp
- tree: F3
- env_template: FMM_MODE=tensor;S4FMM_NG=5;S4FMM_INJECT=linearsolve_null2:244:1
- points: 2 injection points (seam, alloc)
- expectation_basis: fmm_closed.cpp:244-245 [源码]: zero solve_info returns 1 (reported); R4-CL04-F is HOLD only for I1-I6 and does not answer K-1 (RED_POINTS_LEDGER_R6c K-1 row)
- prereg_status: INFLUENCED
- judge_rule: REPORTED_FAILURE (rc1 = 1) expected; no CRASH; judged by judge_d003 classify
- feasibility: FEASIBLE_EXISTING
- limitation: an alloc failure path is not separately injected at 244; only the seam

## M2-07

- source: RP-R6d-16; S3 T14 (NB, n_G)
- purpose: NB=1-8 coverage of the injection modes
- method: NG=1..8 x modes {closed2d, fft, kottke, PolBasis modes in the inventory}; one injection-free control per cell; one representative injection per mode; n_G recorded per the S3 T14 count
- driver_and_injector: existing driver d003 (plain F3 build) + inject_r4_plan.cpp (plan:, s4malloc)
- tree: F3
- env_template: FMM_MODE=<m>;S4FMM_NG=<1..8>
- points: per mode: 8 controls + representative injections (exact in PREREG)
- expectation_basis: S3 T14; M0 (vl NG=1 rc 20, RESULTS_R8_NOINJECT_run1.tsv)
- prereg_status: INFLUENCED
- judge_rule: control rc = expected (0, or 20 for vl NG=1 and fftvl NG=1 per M0)
- feasibility: FEASIBLE_EXISTING
- limitation: NG range of the driver is 1..64 [源码]; cells with NG not in M0 are INFLUENCED

## M2-08

- source: RP-R6d-17; S3 T13 (NB=9 no allocation)
- purpose: category C: intermediate error propagates to the final output
- method: search configurations with NB>=2 and an allocation inside the execution window; report the search table; judge: failure is reported (rc != 0) and the output buffer keeps its sentinel or is not used
- driver_and_injector: existing drivers; search performed on source [源码]
- tree: F3
- env_template: per configuration found
- points: 0 if no configuration found (NOT_FOUND)
- expectation_basis: S3 T13 (NB=9 has no allocation)
- prereg_status: INFLUENCED
- judge_rule: rc != 0 and output sentinel unchanged
- feasibility: NOT_FOUND
- limitation: the NB>=2 configuration search has NOT been completed in M2a; status is not a result; the search table is open work for the user to rule on

## M2-09

- source: ES3R4-29; U118; U124; CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv
- purpose: fmmret plain clean control and complete CTRL_SEAM fmmret re-test
- method: control: fmmret plain (no injection) on F3 and F2; then all fmmret rows of R7 M2b CTRL_SEAM
- driver_and_injector: seam-fmmret-F3 (DRIVERS_R8.tsv) and seamF-F2 (R7) [registry]
- tree: F3, F2
- env_template: FMM_MODE=<m>;S4FMM_NG=<n>;S4FMM_INJECT=fmmret:<k>
- points: one control per tree + each fmmret row (exact in PREREG)
- expectation_basis: CTRL-SEAM-fmmret-F and -F2 rows of CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv show DISAGREE
- prereg_status: INFLUENCED
- judge_rule: control CONTROL_OK; fmmret rows: REPORTED_FAILURE or SILENT_SWALLOW by judge_d003
- feasibility: FEASIBLE_EXISTING
- limitation: DISAGREE rows are a known historical finding; re-test is a measurement, not a fix

## M2-10

- source: RP-R6d-7 (BASELINE_ONLY)
- purpose: B-side source of vl NG=1 no-injection rc 20
- method: gdb breakpoint on the B tree at the return of the vl path; result is a baseline only
- driver_and_injector: gdb script (new, R8 M2a); breakpoint at file:line [源码] to be fixed from the B source
- tree: B
- env_template: FMM_MODE=vl;S4FMM_NG=1
- points: 1 point (baseline, not a fix)
- expectation_basis: M0 vl NG=1 rc 20 on F2 and F3; B observation is not fix evidence (AGENTS.md 5)
- prereg_status: INFLUENCED
- judge_rule: BASELINE_ONLY: record rc and the breakpoint hits; no PASS/FAIL
- feasibility: FEASIBLE_NEW_APPARATUS
- limitation: B is not a fix tree; gdb not run in M2a (停止条件 6)

## M3_DEFERRED

- source: U235; RP-R6d-15
- purpose: Python/Lua visibility of the failure (end-to-end path)
- method: deferred to M3 with the end-to-end chain
- driver_and_injector: -
- tree: -
- env_template: -
- points: 0
- expectation_basis: U235 (M3 takes Python/Lua)
- prereg_status: DEFERRED
- judge_rule: -
- feasibility: M3_DEFERRED
- limitation: not part of M2

