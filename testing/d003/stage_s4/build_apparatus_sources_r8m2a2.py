#!/usr/bin/env python3
# build_apparatus_sources_r8m2a2.py -- P05-S4 R8 M2a2: Generate new apparatus source files and diffs.
import difflib, hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
ST4 = os.path.join(REPO, "testing", "d003", "stage_s4")

def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def write_diff_file(diff_path, old_rel, new_rel, old_bytes, new_bytes):
    diff = difflib.unified_diff(
        old_bytes.decode("utf-8").splitlines(keepends=True),
        new_bytes.decode("utf-8").splitlines(keepends=True),
        fromfile="a/" + old_rel,
        tofile="b/" + new_rel,
        n=3
    )
    with open(diff_path, "w", encoding="utf-8") as fh:
        fh.write("# SRC_DIFF -- base %s (%s) -> %s (%s)\n" % (
            old_rel, sha256_bytes(old_bytes), new_rel, sha256_bytes(new_bytes)))
        fh.write("".join(diff))

def main():
    os.makedirs(EV, exist_ok=True)
    os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)

    base_inj_p = os.path.join(ST4, "inject_r4_plan.cpp")
    with open(base_inj_p, "rb") as fh:
        base_inj = fh.read()
    base_inj_str = base_inj.decode("utf-8")

    # -------------------------------------------------------------
    # 1. inject_r8m2a2_dual.cpp
    # -------------------------------------------------------------
    dual_code = base_inj_str

    # Common target 2 declarations before s4fmm_inject_hits
    dual_decl = """
/* [P05-S4 R8 M2a2, U244] Target 2 independent parsing and hits */
static const char *mode2(void){ const char *m = getenv("S4FMM_INJECT2"); return m ? m : ""; }
static long nth2(void){ const char *e = getenv("S4FMM_NTH2"); return e ? strtol(e, NULL, 10) : 1; }
static long n_hits2 = 0;

static int pc2_ok = 0;
static long pc2_k = 0, pc2_m = 0, pc2_alloc = 0;
static void pc2_parse(void){
	const char *m = mode2();
	long k = 0, mm = 0;
	int used = 0;
	pc2_ok = 0;
	if(0 != strncmp(m, "plancall:", 9)){ return; }
	if(2 != sscanf(m + 9, "%ld:%ld%n", &k, &mm, &used)){ return; }
	if('\\0' != m[9 + used]){ return; }
	if(k < 1 || mm < 1){ return; }
	pc2_k = k; pc2_m = mm; pc2_ok = 1;
}

extern "C" long s4fmm_inject2_hits(void){ return n_hits2; }
extern "C" int s4fmm_inject2_requested(void){ return '\\0' != mode2()[0]; }
"""
    dual_anchor1 = '/* Read-only view of the hit counter for the driver. */'
    dual_code = dual_code.replace(dual_anchor1, dual_decl + "\n" + dual_anchor1)

    # In __wrap_malloc: plancall target 2
    wrap_malloc_target = """\tif(1 == arm && pc_ok){
\t\tpc_alloc++;
\t\tif(pc_alloc == pc_m){
\t\t\tn_hits++;
\t\t\tstd::fprintf(stderr, "S4FMM HIT real malloc failure: plan call %ld malloc %ld, %zu B (hit=%ld)\\n", pc_k, pc_alloc, n, n_hits);
\t\t\treturn NULL;
\t\t}
\t}"""
    wrap_malloc_repl = wrap_malloc_target + """
\t/* [P05-S4 R8 M2a2] Target 2 plancall */
\tif(1 == arm && pc2_ok){
\t\tpc2_alloc++;
\t\tif(pc2_alloc == pc2_m){
\t\t\tn_hits2++;
\t\t\tn_hits++;
\t\t\tstd::fprintf(stderr, "S4FMM HIT dual real malloc failure: plan call %ld malloc %ld, %zu B (hit2=%ld total=%ld)\\n", pc2_k, pc2_alloc, n, n_hits2, n_hits);
\t\t\treturn NULL;
\t\t}
\t}"""
    dual_code = dual_code.replace(wrap_malloc_target, wrap_malloc_repl)

    # In __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i
    wrap_plan_target = """\tpc_parse();
\tif(pc_ok && n_plan_calls == pc_k){
\t\tpc_alloc = 0;
\t\tarm = 1;
\t\tfft_plan p = __real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(n, a, b, s);
\t\tarm = 0;
\t\treturn p;
\t}"""
    wrap_plan_repl = wrap_plan_target + """
\tpc2_parse();
\tif(pc2_ok && n_plan_calls == pc2_k){
\t\tpc2_alloc = 0;
\t\tarm = 1;
\t\tfft_plan p = __real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(n, a, b, s);
\t\tarm = 0;
\t\treturn p;
\t}"""
    dual_code = dual_code.replace(wrap_plan_target, wrap_plan_repl)

    # In __wrap__Z9S4_mallocm
    wrap_s4malloc_target = """\tif(0 == strcmp(mode(), "s4malloc")){
\t\tn_s4malloc++;
\t\tif(n_s4malloc == nth()){
\t\t\tn_hits++;
\t\t\tstd::fprintf(stderr, "S4FMM HIT real S4_malloc failure: FMM call %zu B (hit=%ld)\\n", size, n_s4malloc);
\t\t\treturn NULL;
\t\t}
\t}"""
    wrap_s4malloc_repl = wrap_s4malloc_target + """
\t/* [P05-S4 R8 M2a2] Target 2 s4malloc */
\tif(0 == strcmp(mode2(), "s4malloc")){
\t\tif(n_s4malloc == nth2()){
\t\t\tn_hits2++;
\t\t\tn_hits++;
\t\t\tstd::fprintf(stderr, "S4FMM HIT dual real S4_malloc failure: FMM call %zu B (hit2=%ld total=%ld)\\n", size, n_hits2, n_hits);
\t\t\treturn NULL;
\t\t}
\t}"""
    dual_code = dual_code.replace(wrap_s4malloc_target, wrap_s4malloc_repl)

    # Before S4_TEST_LINEARSOLVE_NULLINFO2_AFTER, define b2_2_parse_request
    b2_2_decl = """
static int b2_2_req_ok = 0, b2_2_req_id = 0, b2_2_req_k = 0;
static void b2_2_parse_request(void){
	const char *m = mode2();
	b2_2_req_ok = 0;
	if(0 != strncmp(m, "linearsolve_null2:", 18)){ return; }
	int id = 0, k = 0;
	if(2 != sscanf(m + 18, "%d:%d", &id, &k)){ return; }
	if(b2_index(id) < 0 || k < 1){ return; }
	b2_2_req_id = id; b2_2_req_k = k; b2_2_req_ok = 1;
}
"""
    b2_anchor = 'extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2_AFTER'
    dual_code = dual_code.replace(b2_anchor, b2_2_decl + "\n" + b2_anchor)

    # Inside S4_TEST_LINEARSOLVE_NULLINFO2_AFTER
    b2_fn_old = """extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2_AFTER(int id, int *info, std::complex<double> *b, int n, int ld, int model){
\tb2_parse_request();
\tconst int ix = b2_index(id);
\tif(ix < 0){ return; }
\tb2_calls[ix]++;
\tif(!b2_req_ok || id != b2_req_id){ return; }
\tif(b2_calls[ix] != b2_req_k){ return; }
\tif(NULL == info){ return; }
\t*info = 1;                                  /* models a zero pivot: the existing check takes its failure return */
\tif(1 == model){
\t\t/* identity RHS with the solve's real leading dimension ld */
\t\tfor(int j = 0; j < n; ++j){
\t\t\tfor(int i = 0; i < n; ++i){
\t\t\t\tb[i + j*ld] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
\t\t\t}
\t\t}
\t}
\tb2_hits[ix]++;
\tn_hits++;
\tstd::fprintf(stderr, "S4FMM HIT linearsolve_null2 id=%d call=%ld model=%d (hit=%ld)\\n",
\t             id, b2_calls[ix], model, n_hits);
}"""

    b2_fn_new = """extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2_AFTER(int id, int *info, std::complex<double> *b, int n, int ld, int model){
\tconst int ix = b2_index(id);
\tif(ix < 0){ return; }
\tb2_calls[ix]++;

\tb2_parse_request();
\tif(b2_req_ok && id == b2_req_id && b2_calls[ix] == b2_req_k){
\t\tif(NULL != info){ *info = 1; }
\t\tif(1 == model){
\t\t\tfor(int j = 0; j < n; ++j){
\t\t\t\tfor(int i = 0; i < n; ++i){
\t\t\t\t\tb[i + j*ld] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
\t\t\t\t}
\t\t\t}
\t\t}
\t\tb2_hits[ix]++;
\t\tn_hits++;
\t\tstd::fprintf(stderr, "S4FMM HIT linearsolve_null2 id=%d call=%ld model=%d (hit=%ld)\\n",
\t\t             id, b2_calls[ix], model, n_hits);
\t\treturn;
\t}

\t/* [P05-S4 R8 M2a2] Target 2 linearsolve_null2 */
\tb2_2_parse_request();
\tif(b2_2_req_ok && id == b2_2_req_id && b2_calls[ix] == b2_2_req_k){
\t\tif(NULL != info){ *info = 1; }
\t\tif(1 == model){
\t\t\tfor(int j = 0; j < n; ++j){
\t\t\t\tfor(int i = 0; i < n; ++i){
\t\t\t\t\tb[i + j*ld] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
\t\t\t\t}
\t\t\t}
\t\t}
\t\tn_hits2++;
\t\tn_hits++;
\t\tstd::fprintf(stderr, "S4FMM HIT dual linearsolve_null2 id=%d call=%ld model=%d (hit2=%ld total=%ld)\\n",
\t\t             id, b2_calls[ix], model, n_hits2, n_hits);
\t\treturn;
\t}
}"""
    dual_code = dual_code.replace(b2_fn_old, b2_fn_new)

    dual_out_p = os.path.join(ST4, "inject_r8m2a2_dual.cpp")
    with open(dual_out_p, "w", encoding="utf-8") as fh:
        fh.write(dual_code)
    diff_dual_p = os.path.join(EV, "SRC_DIFF_R8_M2a2_inject_dual_R3.txt")
    write_diff_file(diff_dual_p, "testing/d003/stage_s4/inject_r4_plan.cpp",
                    "testing/d003/stage_s4/inject_r8m2a2_dual.cpp", base_inj, dual_code.encode("utf-8"))
    print("wrote %s and %s" % (dual_out_p, diff_dual_p))

    # -------------------------------------------------------------
    # 2. inject_r8m2a2_nan.cpp
    # -------------------------------------------------------------
    nan_code = base_inj_str
    nan_decl = """
/* [P05-S4 R8 M2a2, U240] linearsolve_nanbuf:ID:K */
#include <limits>
static int nan_req_ok = 0, nan_req_id = 0, nan_req_k = 0;
static long nan_hits_count = 0;

static void nan_parse_request(void){
	const char *m = mode();
	nan_req_ok = 0;
	if(0 != strncmp(m, "linearsolve_nanbuf:", 19)){ return; }
	int id = 0, k = 0;
	if(2 != sscanf(m + 19, "%d:%d", &id, &k)){ return; }
	if(b2b_index(id) < 0 || k < 1){ return; }
	nan_req_id = id; nan_req_k = k; nan_req_ok = 1;
}
"""
    nan_anchor = 'extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER'
    nan_code = nan_code.replace(nan_anchor, nan_decl + "\n" + nan_anchor)

    nan_fn_old = """extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER(int id, std::complex<double> *b, int n, int ld, int model){
\tb2b_parse_request();
\tconst int ix = b2b_index(id);
\tif(ix < 0){ return; }
\tb2b_calls[ix]++;
\tif(!b2b_req_ok || id != b2b_req_id){ return; }
\tif(b2b_calls[ix] != b2b_req_k){ return; }
\tif(1 == model){
\t\t/* identity RHS with the solve's real leading dimension ld: the same write as family B */
\t\tfor(int j = 0; j < n; ++j){
\t\t\tfor(int i = 0; i < n; ++i){
\t\t\t\tb[i + j*ld] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
\t\t\t}
\t\t}
\t}
\tb2b_hits[ix]++;
\tn_hits++;
\tstd::fprintf(stderr, "S4FMM HIT linearsolve_null2buf id=%d call=%ld model=%d (hit=%ld)\\n",
\t             id, b2b_calls[ix], model, n_hits);
}"""

    nan_fn_new = """extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER(int id, std::complex<double> *b, int n, int ld, int model){
\tconst int ix = b2b_index(id);
\tif(ix < 0){ return; }
\tb2b_calls[ix]++;

\tb2b_parse_request();
\tif(b2b_req_ok && id == b2b_req_id && b2b_calls[ix] == b2b_req_k){
\t\tif(1 == model){
\t\t\tfor(int j = 0; j < n; ++j){
\t\t\t\tfor(int i = 0; i < n; ++i){
\t\t\t\t\tb[i + j*ld] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
\t\t\t\t}
\t\t\t}
\t\t}
\t\tb2b_hits[ix]++;
\t\tn_hits++;
\t\tstd::fprintf(stderr, "S4FMM HIT linearsolve_null2buf id=%d call=%ld model=%d (hit=%ld)\\n",
\t\t             id, b2b_calls[ix], model, n_hits);
\t\treturn;
\t}

\t/* [P05-S4 R8 M2a2, U240] linearsolve_nanbuf: writes NaN to output buffer b, leaving solve_info unchanged */
\tnan_parse_request();
\tif(nan_req_ok && id == nan_req_id && b2b_calls[ix] == nan_req_k){
\t\tconst double qnan = std::numeric_limits<double>::quiet_NaN();
\t\tfor(int j = 0; j < n; ++j){
\t\t\tfor(int i = 0; i < n; ++i){
\t\t\t\tb[i + j*ld] = std::complex<double>(qnan, qnan);
\t\t\t}
\t\t}
\t\tnan_hits_count++;
\t\tn_hits++;
\t\tstd::fprintf(stderr, "S4FMM HIT linearsolve_nanbuf id=%d call=%ld (hit=%ld)\\n",
\t\t             id, b2b_calls[ix], n_hits);
\t\treturn;
\t}
}"""
    nan_code = nan_code.replace(nan_fn_old, nan_fn_new)

    nan_out_p = os.path.join(ST4, "inject_r8m2a2_nan.cpp")
    with open(nan_out_p, "w", encoding="utf-8") as fh:
        fh.write(nan_code)
    diff_nan_p = os.path.join(EV, "SRC_DIFF_R8_M2a2_inject_nan_R2.txt")
    write_diff_file(diff_nan_p, "testing/d003/stage_s4/inject_r4_plan.cpp",
                    "testing/d003/stage_s4/inject_r8m2a2_nan.cpp", base_inj, nan_code.encode("utf-8"))
    print("wrote %s and %s" % (nan_out_p, diff_nan_p))

    return 0

if __name__ == "__main__":
    sys.exit(main())
