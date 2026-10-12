# RNV1_SOURCE_R6d.md -- source reading for RNV1 (P05-S4 R6d, section 4.1 of the brief)

Read-only reading of tree F as frozen (HEAD:S4 = 4a6f64927a30537740dd0c8f11f9a5aae5e46ba4).  [源码] = read in R6d; no run is the basis of these lines.
Line numbers refer to S4/ in the frozen tree F.  No file in S4/ was changed.

## 1. Callers of pattern_generate_flow_field (the C entry point, pattern.c:2089)

| caller | file:line | how the return code is used |
|---|---|---|
| Pattern_GenerateFlowField (convenience wrapper) | S4/pattern/pattern.c:2161-2169 | returns the value unchanged (`return pattern_generate_flow_field(...)`) |
| FMMGetEpsilon_PolBasisNV (defined fmm_PolBasisNV.cpp:42) | S4/fmm/fmm_PolBasisNV.cpp:140 | `error = Pattern_GenerateFlowField(...)`; `if(0 != error)` at :144 traces, frees `vfield`, `work`, `ivalues` if non-NULL, and `return error` at :149 |
| FMMGetEpsilon_PolBasisJones (defined fmm_PolBasisJones.cpp:91) | S4/fmm/fmm_PolBasisJones.cpp:185 | `error = Pattern_GenerateFlowField(...)`; trace at :188 [源码; the branch was not read line by line in R6d] |
| FMMGetEpsilon_PolBasisVL (defined fmm_PolBasisVL.cpp:42) | S4/fmm/fmm_PolBasisVL.cpp:144 | `int error = Pattern_GenerateFlowField(...)`; trace at :147 [源码] |

Only these three callers exist in S4/ (grep `Pattern_GenerateFlowField` and `pattern_generate_flow_field`, R6d).  All three are PolBasis modes (nv, jones, vl).  The fft, kottke, closed and experimental modes do not call the pattern field generator.

## 2. Return path to GetFieldPlane

- pattern_generate_flow_field returns -1 .. -8 for argument errors (pattern.c:2099-2106) and -10 for a zero or non-finite maximum (pattern.c:2148-2150; the D016 path, S3R2 D-D).  It returns 0 on success.
- In the NV branch the error is returned from FMMGetEpsilon_PolBasisNV (fmm_PolBasisNV.cpp:149).  The same holds for the other two callers by the same pattern [源码 for Jones :188 and VL :147 only, not read in full].  FMMGetEpsilon_PolBasis* are the epsilon routines of the FMM route; their caller chain up to ComputeLayerModes (and the point at which their return code becomes rc 20) is NOT traced to the end in R6d.  This is an open item of the repair proposal, not a fact stated here.
- The code that maps a non-zero return of the layer builder to rc 20 (ComputeLayerModes "layer eigensystem failed", S4_internal.h:263 comment) was traced in R5 (FFT 1 -> CLM 20 -> GFP 20, R5 report section 2 / S3R2 report).  R6d does not re-trace that chain; the injection (section 4 of the report) measures the observed rc instead.

## 3. The four native malloc sites (pattern.c 1477, 1481, 1656, 1660)

Two functions contain the native malloc calls (libc malloc; pattern.c includes stdlib.h at :22 and has no malloc macro):

| function | definition | malloc sites | code after the allocation |
|---|---|---|---|
| pattern_generate_flow_field_rect | pattern.c:1464 | 1477 `work = malloc(sizeof(double)*N2*(5+2))`; 1481 `iwork = malloc(sizeof(int)*N2*4)` | 1478 `x = work`, 1482 `Mcol = iwork`; no NULL check before use |
| pattern_generate_flow_field_tri | pattern.c:1643 | 1656 `work = malloc(sizeof(double)*N3*(11+2))`; 1660 `iwork = malloc(sizeof(int)*N3*10)` | 1657 `x = work`, 1661 `Mcol = iwork`; no NULL check before use |

The function that runs is decided by pattern.c:2126-2143: if |u.v|/max(|u|,|v|) < DBL_EPSILON the rect function runs, else the tri function runs.  Therefore ONE call of pattern_generate_flow_field enters EXACTLY ONE of the two functions by this code path.  Each function contains two malloc sites (a pair).  NOTE (corrected by the measurement in section 4): a call of the flow-field window performs the pair of its function AND, through sparse_linsolve_d -> cg, one more native malloc at pattern.c:1251.  So the reading "EXACTLY TWO mallocs per call" is WRONG for the window as a whole; the measured count is three (section 4), which agrees with the R5 count of 3.

## 4. Native mallocs inside the window, MEASURED in R6d (gdb, nv, NG=9, no injection; r6d_rnv1_callers.gdb)

The three calls made inside the window of Pattern_GenerateFlowField (R6d injector counts them; gdb gives the callers):

| k | size (B) | caller (gdb backtrace, frame #1) | malloc expression |
|---|---|---|---|
| 1 | 7168 | pattern_generate_flow_field_rect, pattern.c:1477 | `work = malloc(sizeof(double)*N2*(5+2))` (N2 = 128 for nu=nv=8) |
| 2 | 2048 | pattern_generate_flow_field_rect, pattern.c:1481 | `iwork = malloc(sizeof(int)*N2*4)` |
| 3 | 4096 | cg (called from sparse_linsolve_d, pattern.c:1404), pattern.c:1251 | `work = malloc(sizeof(double)*4*n)` (n = 128) |

Facts from this measurement (they correct the source reading of section 3):
- The rect branch ran (lattice_type rect for Lr = {1,0,0,1}); the tri pair (1656, 1660) did NOT run for this point.
- pattern.c:1251 (inside cg, called by sparse_linsolve_d at pattern.c:1404) IS inside the flow-field window and runs in the nv case.  Section 3 did not list it as a pair; it is the third malloc of the R5 count.
- So the repair (RNV1) has to cover THREE native malloc sites in the nv window on this geometry: 1477, 1481 and 1251 (plus 1656, 1660 for the tri lattice).

Other native mallocs in pattern.c (not in the window of this point; listed, NULL checks not read in R6d):

| file:line | expression | note |
|---|---|---|
| 415, 528 | `int *tri = malloc(sizeof(int)*3*(n_vertices-2))` | polygon triangulation (not measured in the window) |
| 806 | `area = malloc(sizeof(double)*nshapes)` | not measured in the window |
| 1164 | `target = malloc(sizeof(char)*(len+lexpsymb))` | not measured in the window |

## 5. Cleanup on the failure path (to be used by the repair proposal)

- The native malloc sites inside the window have NO error path: a NULL pointer is used at once.  Measured/read sites: rect 1477 (used at 1478), rect 1481 (used at 1482), cg 1251 (used at 1252, `p = work`), and tri 1656/1660 (used at 1657/1661) for the tri lattice.  The write through NULL is the fault (SEGV, expected; to be observed in section 4 of the report).
- Frees: rect/tri work is freed at pattern.c:2085 (`free(work)`, on the success path of pattern_generate_flow_field_rect/_tri, after the solve); cg work is freed at pattern.c:1272 and 1319 (inside cg).  The repair must free any buffer already allocated when a later malloc fails (for rect: free the 1477 buffer if 1481 fails; for cg: nothing before 1251).  The exact code is NOT written here (repair proposal).
- The caller's cleanup for the vfield buffer exists (fmm_PolBasisNV.cpp:146-148): `S4_free(vfield)`, `S4_free(work)`, `S4_free(ivalues)`.  A non-zero return from pattern_generate_flow_field is therefore cleaned up by the caller, provided the return code is non-zero.  The return value expected for a native malloc failure is NOT decided here (open; the repair round must choose a value that the caller traces as an error; -10 is a D016 value and must not be reused silently).

## 6. Statement about the nv test point (R6d)

The R5 and R6c nv points carry the NG and mode settings of the state runner.  Whether the nv driver path reaches pattern_generate_flow_field with lattice_type rect or tri depends on the lattice of the test grid; this is recorded from the gdb run in R6d (section 4.3 of the report), not assumed.
