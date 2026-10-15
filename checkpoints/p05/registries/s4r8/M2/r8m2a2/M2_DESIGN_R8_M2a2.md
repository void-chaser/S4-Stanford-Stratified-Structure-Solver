# M2 design v3, P05-S4 R8 M2a2 (CONT1 section 8.1)

All expectations are design expectations (status INFLUENCED). No S4 run was made in this round.

## M2-00

- source: U231; section 4.1
- purpose: control for the three A_CTRL combinations under injection-free run
- method: A_CTRL combos closed2d-ng1, fft-ng5, kottke-ng5 on F2 and F3; M0 covers all six (crosswalk R2)
- driver_and_injector: existing driver d003 (M0 build); no new apparatus
- tree: F2, F3
- env_template: FMM_MODE=<m>;S4FMM_NG=<n>
- points: 0
- expectation_basis: A10_CONTROL_CROSSWALK_R8_M2a_R2.tsv: 6 of 6 COVERED_BY_M0 (rc 0, call IDENTICAL)
- prereg_status: INFLUENCED
- judge_rule: CONTROL_OK expected; crosswalk status COVERED_BY_M0 on each row
- feasibility: COVERED_BY_M0
- limitation: none for these six; the other 4 A-10 mismatches are a register error (U231)
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M2-00

## M2-01

- source: U232, U238
- purpose: I1-I6 state judgement on the F3 repair injection points
- method: 12 resolved repair points (6 init: M2-01-01..06; 6 poly win:1: M2-01-11, 12, 14, 16, 18, 20) + 9 controls; 5 poly win:64 points unresolved (INDEX_DERIVATION_R8_M2a2_R2.tsv); dbg drivers init-F3-dbg and polyinj-F3-dbg (-O0 -g, F3 dbg library); judged by G5 rule (I1-I6, I7 DEFERRED)
- driver_and_injector: init-F3-dbg, polyinj-F3-dbg
- tree: F3
- env_template: as ADD22 row (FMM_MODE, S4FMM_NG, S4FMM_INJECT)
- points: 21
- expectation_basis: INDEX_DERIVATION_R8_M2a2_R2.tsv; REGISTRY_S4_PRE_R6b_STATE_v2.tsv (I1-I6 definitions); R7 M3 G5 expectation HOLD; U232, U238
- prereg_status: INFLUENCED
- judge_rule: I1-I6 HOLD where applicable; reported failure rc1 != 0 required for test points; CONTROL_OK for controls
- feasibility: FEASIBLE_NEW_APPARATUS
- limitation: 5 win:64 points are UNRESOLVED_INDEX (call 1 not fixed without gdb run) and not preregistered; will await user review (brief section 9)
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M2-01

## M2-02

- source: U5b, E6-4; ERRATA_6d.txt lines 48-70 (E6d-3); U241
- purpose: stage e: failure outside every ENTER/RETURN window
- method: candidate search over 227 registered requests (Part A) and 77 tree F3 calls outside CLM (Part B); search table STAGE_E_SEARCH_R8_M2a2_R2.tsv
- driver_and_injector: none (search table only)
- tree: F3
- env_template: -
- points: 0
- expectation_basis: STAGE_E_SEARCH_R8_M2a2_R2.tsv (A_ROWS=227, B_ROWS=77, STAGE_E_IN_SCOPE=0); ERRATA_6d.txt E6d-3; E6-4
- prereg_status: INFLUENCED
- judge_rule: NOT_FOUND_IN_SCOPE if all candidates are out of scope
- feasibility: NOT_FOUND_IN_SCOPE
- limitation: all candidates outside CLM are either E6-4 (GetFieldOnGrid) or S5 (non-FMM allocations); destination awaits user ruling
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M2-02

## M2-03

- source: U2-10 (I7 DEFERRED); U246; task brief section 4.6
- purpose: I7 sanitizer judgement for F3 state points and repair points
- method: san_probe_r8m2a2 passed (ASan reports overflow); F3 sanitizer library and drivers (r6bstate-F3-san, init-F3-san, polyinj-F3-san, seamF-F3-san, fmmret-F3-san) built in build_R3; 19 representative G5/G6 stage cells + 12 M2-01 repair points = 31 points
- driver_and_injector: r6bstate-F3-san, init-F3-san, polyinj-F3-san, seamF-F3-san, fmmret-F3-san
- tree: F3
- env_template: as corresponding state row; sanitizer flags via build
- points: 31
- expectation_basis: U246; SAN_PROBE_R8_M2a2.txt; REGRESS_R7_M3.tsv (19 cells); INDEX_DERIVATION_R8_M2a2_R2.tsv (12 repair points)
- prereg_status: INFLUENCED
- judge_rule: I7: sanitizer report count = 0 AND rc/class equal to non-sanitizer run
- feasibility: FEASIBLE_NEW_APPARATUS
- limitation: only judged when sanitizer build is run; probe verified in M2a2
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M2-03

## M2-04

- source: U4, U5, U244; task brief section 4.3
- purpose: dual-target injection: two failures in one run (call1 fails, call2 retry fails, call3 recovers)
- method: (a) same layer: dual-F3-dbg, fft ng5, s4malloc NTH=1, NTH2=2; (b) two layers: layers-dual-F3-dbg, fft ng5 PP1, s4malloc NTH=1, NTH2=4; plus 2 controls
- driver_and_injector: dual-F3-dbg, layers-dual-F3-dbg (build_R3 / build_R4) + inject_r8m2a2_dual_R2/R3
- tree: F3
- env_template: FMM_MODE=fft;S4FMM_NG=5;[S4FMM_LAYOUT=PP1;]S4FMM_INJECT=s4malloc;S4FMM_NTH=1;S4FMM_INJECT2=s4malloc;S4FMM_NTH2=<2|4>
- points: 4
- expectation_basis: U244; DUAL_HARNESS_R8_M2a2.tsv (11/11 PASS); INDEX_DERIVATION_R8_M2a2_R2.tsv; S4.cpp:1894
- prereg_status: INFLUENCED
- judge_rule: call1 rc1 != 0, call2 rc2 != 0, call3 rc=0; no signal; I1-I6 HOLD where applicable
- feasibility: FEASIBLE_NEW_APPARATUS
- limitation: synthetic harness tested (DUAL_HARNESS); full S4 driver execution deferred to M2b
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M2-04

## M2-05

- source: U20; U245; task brief section 4.3
- purpose: failure in layer 0, layer 2, or two pattern layers (P0, P2, PP1, PP2)
- method: driver_r8m2a2_layers_R2.cpp with layout P0 (layer 0, NTH=1), P2 (layer 2, NTH=1), PP1 (layer 1, NTH=1), PP2 (layer 2, NTH=3); plus 4 controls
- driver_and_injector: layers-F3-dbg + inject_r4_plan.cpp
- tree: F3
- env_template: FMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=<P0|P2|PP1|PP2>;S4FMM_INJECT=s4malloc;S4FMM_NTH=<1|3>
- points: 8
- expectation_basis: U245; INDEX_DERIVATION_R8_M2a2_R2.tsv; fmm_FFT.cpp:75,83; S4.cpp:1894
- prereg_status: INFLUENCED
- judge_rule: I1-I6 HOLD for the failing layer; other layers unaffected; rc1 != 0 for test, rc=0 for control
- feasibility: FEASIBLE_NEW_APPARATUS
- limitation: NTH=3 for PP2 is corrected from R1 NTH=2 (first pattern layer consumes 2 allocations)
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M2-05

## M2-06

- source: RP-R6d-8; U240; fmm_closed.cpp:244-245 [源码]
- purpose: K-1 tensor path: solve_info=0 with non-finite Epsilon_inv
- method: nan-F3 driver linked with lib_F3_bufseam (DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2BUF); inject linearsolve_nanbuf:244:1; 1 test point + 1 control
- driver_and_injector: nan-F3 + inject_r8m2a2_nan_R2.cpp
- tree: F3
- env_template: FMM_MODE=tensor;S4FMM_NG=5;S4FMM_INJECT=linearsolve_nanbuf:244:1
- points: 2
- expectation_basis: U240; K1_ANCHOR_R8_M2a2.tsv; INDEX_DERIVATION_R8_M2a2_R2.tsv; [源码]: tensor branch has no isfinite check
- prereg_status: INFLUENCED
- judge_rule: exp_rc1 = 0, exp_class = SILENT_SWALLOW (if bug present); CONTROL_OK for control
- feasibility: FEASIBLE_NEW_APPARATUS
- limitation: expectation is design expectation [源码]; if observed SILENT_SWALLOW in M2b, candidate for K-1 red point (U4)
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M2-06

## M2-07

- source: RP-R6d-16; S3 T14; U243
- purpose: NB=1-8 grid coverage across all 9 injection modes
- method: 9 modes x NG 1..8: 72 injection-free controls (d003-F3-plain) + 9 representative injections at NG=5 (d003plan-F3-plain, s4malloc NTH=1); records n_G_actual
- driver_and_injector: d003-F3-plain, d003plan-F3-plain (reused from DRIVERS_R8.tsv)
- tree: F3
- env_template: FMM_MODE=<m>;S4FMM_NG=<1..8>[;S4FMM_INJECT=s4malloc;S4FMM_NTH=1]
- points: 81
- expectation_basis: U243; CATC_SEARCH_R8_M2a2_R2B.tsv (n_G_actual rules); M0/M1 observations for controls; NZ token for unmeasured injections
- prereg_status: INFLUENCED
- judge_rule: controls: rc=0 (or 20 for vl NG=1 / fftvl NG=1 per M0); injections: exp_rc1 = NZ (non-zero)
- feasibility: FEASIBLE_EXISTING
- limitation: unmeasured cells use NZ token supported by verdict_m2_r8m2a2.py
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M2-07

## M2-08

- source: RP-R6d-17; S3 T13; U242
- purpose: category C: intermediate error propagates to final output (NB>=2 with exec allocation)
- method: candidate search over 63 (mode x NG) grid configurations; CATC_SEARCH_R8_M2a2_R2B.tsv
- driver_and_injector: none (search table only)
- tree: F3
- env_template: -
- points: 0
- expectation_basis: CATC_SEARCH_R8_M2a2_R2B.tsv (ROWS=63, FOUND=0, NOT_FOUND=63); kiss_fft.c allocation rules
- prereg_status: INFLUENCED
- judge_rule: NOT_FOUND if no configuration in grid
- feasibility: NOT_FOUND
- limitation: on square lattice no NB>=2 configuration has a dimension of length 1; 1D lattice + FFT candidate outside U242 grid listed in CANDIDATES_OUTSIDE_U242_GRID for user ruling
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M2-08

## M2-09

- source: ES3R4-29; U118; U239
- purpose: fmmret plain clean control on F3 and F2
- method: seam-fmmret-F3 and seam-fmmret-F2 with FMM_MODE=fft, S4FMM_NG=9, no injection; 2 control points
- driver_and_injector: seam-fmmret-F3 (DRIVERS_R8.tsv) and seam-fmmret-F2 (DRIVERS_R7_SEAM.tsv)
- tree: F3, F2
- env_template: FMM_MODE=fft;S4FMM_NG=9
- points: 2
- expectation_basis: U239; DRIVERS_R8.tsv; DRIVERS_R7_SEAM.tsv; RESULTS_R8_D_pass1.tsv:4
- prereg_status: INFLUENCED
- judge_rule: CONTROL_OK, rc=0, signal=0
- feasibility: FEASIBLE_EXISTING
- limitation: pair comparison between F3 and F2; injection rows already covered in M1
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M2-09

## M2-10

- source: RP-R6d-7; U247; task brief section 4.3 & section 7
- purpose: B-side source of vl NG=1 rc 20 (BASELINE_ONLY)
- method: r6dnv1-B-dbg driver (same-family B dbg driver built in build/B-dbg) with gdb script m210_b_r8m2a2_R2.gdb; 3 return 20 breakpoints (lines 2362, 2416, 2432)
- driver_and_injector: r6dnv1-B-dbg (BUILD_B_DBG_R8_M2a2.tsv)
- tree: B
- env_template: FMM_MODE=vl;S4FMM_NG=1
- points: 1
- expectation_basis: M210_BREAKPOINTS_R8_M2a2_R2.tsv; tree_B/S4/S4.cpp:2362,2416,2432; m210_b_r8m2a2_R2.gdb
- prereg_status: INFLUENCED
- judge_rule: BASELINE_ONLY: record rc and breakpoint hits; no PASS/FAIL
- feasibility: FEASIBLE_NEW_APPARATUS
- limitation: B tree observation is baseline only, not fix evidence (AGENTS.md section 5); gdb script prepared, not run in M2a2
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M2-10

## M3_DEFERRED

- source: U235; RP-R6d-15
- purpose: Python/Lua visibility of failure (end-to-end path)
- method: deferred to M3
- driver_and_injector: -
- tree: -
- env_template: -
- points: 0
- expectation_basis: U235
- prereg_status: DEFERRED
- judge_rule: -
- feasibility: M3_DEFERRED
- limitation: not part of M2
- supersedes: M2_DESIGN_R8_M2a_R2.tsv:M3_DEFERRED

