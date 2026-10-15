#!/usr/bin/env python3
# build_apparatus_sources_r8m2a2_R2.py -- P05-S4 R8 M2a2: corrected apparatus sources (version R2 of the source builder).
# Writes NEW files only (U17; the R1 sources and their SRC_DIFF files stay):
#   testing/d003/stage_s4/inject_r8m2a2_dual_R2.cpp   (copy of inject_r4_plan.cpp + independent second target, strict parsing)
#   testing/d003/stage_s4/inject_r8m2a2_nan_R2.cpp    (copy of inject_r4_plan.cpp + linearsolve_nanbuf, strict parsing)
#   testing/d003/stage_s4/driver_r8m2a2_layers_R2.cpp (copy of driver_r6b_state.cpp + S4FMM_LAYOUT; unknown layout fails closed)
#   $EV/SRC_DIFF_R8_M2a2_inject_dual_srcR2.txt, ..._inject_nan_srcR2.txt, ..._driver_layers_srcR2.txt
# Every replacement is asserted to match exactly once; the original branches of the base files are not edited except
# the three signature/anchor lines named below (the original function bodies stay byte-identical).
import difflib, hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
ST4 = os.path.join(REPO, "testing", "d003", "stage_s4")


def sha(b):
    return hashlib.sha256(b).hexdigest()


def rep(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit("ANCHOR ERROR %s: matched %d time(s); refusing to guess" % (label, n))
    return text.replace(old, new)


def write_new(path, text):
    with open(path, "x", encoding="utf-8") as fh:
        fh.write(text)


def write_diff(name, old_rel, new_rel, old_b, new_b):
    d = difflib.unified_diff(old_b.decode("utf-8").splitlines(keepends=True), new_b.decode("utf-8").splitlines(keepends=True),
                             fromfile="a/" + old_rel, tofile="b/" + new_rel, n=3)
    with open(os.path.join(EV, name), "x", encoding="utf-8") as fh:
        fh.write("# SRC_DIFF -- base %s (%s) -> %s (%s)\n" % (old_rel, sha(old_b), new_rel, sha(new_b)))
        fh.write("".join(d))


T2_BLOCK = r'''/* ------------------------------------------------------------------------
 * [P05-S4 R8 M2a2 R2, U244] Target 2 of the dual-target injector.
 *   S4FMM_INJECT2 = s4malloc                (with S4FMM_NTH2 = plain integer >= 1)
 *   S4FMM_INJECT2 = plancall:K:M            (K-th fft_plan_dft_2d call of the process, M-th malloc inside it)
 *   S4FMM_INJECT2 = linearsolve_null2:ID:K  (ID in the seven B2 sites, K-th call of that ID)
 * Target 2 has its own parser (whole string must be consumed; anything else is refused and the request fails closed:
 * nothing is injected, the hit count stays low and the judge reports INVALID), its own armed flag, its own malloc
 * counters and its own hit counter.  It does not read or change S4FMM_INJECT / S4FMM_NTH; the call streams (S4_malloc
 * calls from FMM objects, fft_plan_dft_2d calls, per-site LinearSolve calls) are the process-wide event streams that
 * both targets index.  A request that names the same event as target 1 is refused.
 * ------------------------------------------------------------------------ */
static const char *mode2(void){ const char *m = getenv("S4FMM_INJECT2"); return m ? m : ""; }
static int t2_parsed = 0;
static int t2_kind = 0;              /* 0 none, 1 s4malloc, 2 plancall, 3 linearsolve_null2, -1 invalid request */
static long t2_nth = 0, t2_k = 0, t2_m = 0;
static int t2_id = 0;
static long n_hits2 = 0;
static long t2_malloc_seen = 0;      /* S4_malloc calls from FMM objects, counted for target 2 on its own */
static int t2_arm = 0;
static long t2_plan_alloc = 0;
static const int t2_b2_ids[7] = {134, 138, 144, 244, 375, 265, 273};

static int t2_strict_long(const char *s, long *out){
	if(NULL == s || s[0] < '0' || s[0] > '9'){ return 0; }
	char *end = NULL;
	long v = strtol(s, &end, 10);
	if(end == s || '\0' != *end){ return 0; }
	*out = v;
	return 1;
}
static void t2_invalid(const char *why){
	t2_kind = -1;
	std::fprintf(stderr, "S4FMM DUAL_REQUEST_INVALID %s\n", why);
}
static void t2_parse(void){
	if(t2_parsed){ return; }
	t2_parsed = 1;
	const char *m = mode2();
	if('\0' == m[0]){ return; }
	if(0 == strcmp(m, "s4malloc")){
		long v = 0;
		if(!t2_strict_long(getenv("S4FMM_NTH2"), &v) || v < 1){ t2_invalid("s4malloc needs S4FMM_NTH2 as a plain integer >= 1"); return; }
		if(0 == strcmp(mode(), "s4malloc") && nth() == v){ t2_invalid("target 1 and target 2 name the same S4_malloc call"); return; }
		t2_kind = 1; t2_nth = v;
		return;
	}
	if(0 == strcmp(mode(), m)){ t2_invalid("target 2 repeats target 1"); return; }
	if(0 == strncmp(m, "plancall:", 9)){
		long k = 0, mm = 0;
		int used = 0;
		if(m[9] < '0' || m[9] > '9' || 2 != sscanf(m + 9, "%ld:%ld%n", &k, &mm, &used) || '\0' != m[9 + used] || k < 1 || mm < 1){
			t2_invalid("plancall needs K:M as plain integers >= 1"); return;
		}
		pc_parse();
		if(pc_ok && pc_k == k){ t2_invalid("target 1 and target 2 name the same plan call"); return; }
		t2_kind = 2; t2_k = k; t2_m = mm;
		return;
	}
	if(0 == strncmp(m, "linearsolve_null2:", 18)){
		int id = 0, k = 0, used = 0, known = 0;
		if(m[18] < '0' || m[18] > '9' || 2 != sscanf(m + 18, "%d:%d%n", &id, &k, &used) || '\0' != m[18 + used] || k < 1){
			t2_invalid("linearsolve_null2 needs ID:K as plain integers"); return;
		}
		for(int i = 0; i < 7; ++i){ if(t2_b2_ids[i] == id){ known = 1; } }
		if(!known){ t2_invalid("linearsolve_null2 ID is not one of the seven B2 sites"); return; }
		t2_kind = 3; t2_id = id; t2_k = k;
		return;
	}
	t2_invalid("unknown target 2 kind");
}
extern "C" long s4fmm_inject2_hits(void){ return n_hits2; }
extern "C" int s4fmm_inject2_requested(void){ return '\0' != mode2()[0]; }

'''

MALLOC_T2 = r'''	/* [P05-S4 R8 M2a2 R2, U244] target 2 plancall: its own armed flag and malloc counter. */
	t2_parse();
	if(1 == t2_arm && 2 == t2_kind){
		t2_plan_alloc++;
		if(t2_plan_alloc == t2_m){
			n_hits2++;
			n_hits++;
			std::fprintf(stderr, "S4FMM HIT dual target2 real malloc failure: plan call %ld malloc %ld, %zu B (hit2=%ld total=%ld)\n", t2_k, t2_plan_alloc, n, n_hits2, n_hits);
			return NULL;
		}
	}
'''

PLAN_T2 = r'''	/* [P05-S4 R8 M2a2 R2, U244] target 2 plancall: arm only for its own plan call K and restart its own count there. */
	t2_parse();
	if(2 == t2_kind && n_plan_calls == t2_k){
		t2_plan_alloc = 0;
		t2_arm = 1;
		fft_plan p = __real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(n, a, b, s);
		t2_arm = 0;
		return p;
	}
	return __real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(n, a, b, s);
}
'''

S4MALLOC_HEAD = r'''extern "C" void *__wrap__Z9S4_mallocm(size_t size){
	/* [P05-S4 R8 M2a2 R2, U244] the target 2 stream index is counted before target 1 can return NULL, so a call that
	 * target 1 fails still advances target 2's index (both index the same process-wide stream of FMM S4_malloc calls). */
	t2_parse();
	const long t2_idx = (1 == t2_kind) ? ++t2_malloc_seen : 0;
'''

S4MALLOC_TAIL = r'''	if(1 == t2_kind && t2_idx == t2_nth){
		n_hits2++;
		n_hits++;
		std::fprintf(stderr, "S4FMM HIT dual target2 real S4_malloc failure: FMM call %zu B (stream index %ld, hit2=%ld total=%ld)\n", size, t2_idx, n_hits2, n_hits);
		return NULL;
	}
	return __real__Z9S4_mallocm(size);
}
'''

B2_WRAPPER = r'''/* [P05-S4 R8 M2a2 R2, U244] Target 2 for family B2.  The original hook (target 1; body unchanged, it also counts this
 * call in b2_calls) runs first; target 2 then acts only if target 1 did not consume this event. */
extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2_AFTER(int id, int *info, std::complex<double> *b, int n, int ld, int model){
	const long hits_before = n_hits;
	b2_target1_hook(id, info, b, n, ld, model);
	t2_parse();
	if(3 != t2_kind || id != t2_id){ return; }
	const int ix = b2_index(id);
	if(ix < 0 || n_hits != hits_before){ return; }
	if(b2_calls[ix] != t2_k){ return; }
	if(NULL == info){ return; }
	*info = 1;
	if(1 == model){
		for(int j = 0; j < n; ++j){
			for(int i = 0; i < n; ++i){
				b[i + j*ld] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
			}
		}
	}
	n_hits2++;
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT dual target2 linearsolve_null2 id=%d call=%ld model=%d (hit2=%ld total=%ld)\n", id, b2_calls[ix], model, n_hits2, n_hits);
}

'''

NAN_WRAPPER = r'''/* [P05-S4 R8 M2a2 R2, U240] linearsolve_nanbuf:ID:K.  The original B2BUF hook (body unchanged, it also counts this call
 * in b2b_calls) runs first; the NaN request then acts only if the original did not consume this event.  The output buffer
 * of the solve is overwritten with quiet NaN; solve_info is NOT touched (the real solve left it 0). */
#include <limits>
static int nan_parsed = 0, nan_ok = 0, nan_id = 0, nan_k = 0;
static void nan_parse(void){
	if(nan_parsed){ return; }
	nan_parsed = 1;
	const char *m = mode();
	if(0 != strncmp(m, "linearsolve_nanbuf:", 19)){ return; }
	int id = 0, k = 0, used = 0;
	if(m[19] < '0' || m[19] > '9' || 2 != sscanf(m + 19, "%d:%d%n", &id, &k, &used) || '\0' != m[19 + used] || k < 1 || b2b_index(id) < 0){
		std::fprintf(stderr, "S4FMM NAN_REQUEST_INVALID %s\n", m);
		return;
	}
	nan_id = id; nan_k = k; nan_ok = 1;
}
extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER(int id, std::complex<double> *b, int n, int ld, int model){
	const long hits_before = n_hits;
	b2b_original_hook(id, b, n, ld, model);
	nan_parse();
	if(!nan_ok || id != nan_id){ return; }
	const int ix = b2b_index(id);
	if(ix < 0 || n_hits != hits_before){ return; }
	if(b2b_calls[ix] != nan_k){ return; }
	const double qnan = std::numeric_limits<double>::quiet_NaN();
	for(int j = 0; j < n; ++j){
		for(int i = 0; i < n; ++i){
			b[i + j*ld] = std::complex<double>(qnan, qnan);
		}
	}
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT linearsolve_nanbuf id=%d call=%ld model=%d (hit=%ld)\n", id, b2b_calls[ix], model, n_hits);
}

'''

HDR_B2BUF = "/* ------------------------------------------------------------------------\n * Family B2-buf (P05-S2R4, R4-1)."
HDR_FAMILY_E = "/* ------------------------------------------------------------------------\n * Family E (P05-S2R5, R5-1)."

LAYERS_STACK = r'''	if(0 == strcmp(which, "pattern")){
		S4_real radius[2] = {0.25, 0.25}, center[2] = {0.0, 0.0}, angle_frac = 0.0;
		const int is1d = (NULL != mode && 0 == strcmp(mode, "closed1d"));
		const int rtype = is1d ? S4_REGION_TYPE_INTERVAL : S4_REGION_TYPE_CIRCLE;
		S4_real ival[2] = {0.25, 0.0};
		S4_real *halfw = is1d ? ival : radius;
		/* [P05-S4 R8 M2a2 R2, U245] S4FMM_LAYOUT selects the layer stack.  Unset = the original stack of
		 * driver_r6b_state.cpp (Above, Slab with the pattern, Below).  P0: pattern on layer 0.  P2: pattern on layer 2.
		 * PP1 and PP2: the same two-pattern stack (layers 1 and 2); the names differ only in which pattern layer the
		 * injection index targets.  Any other value, including an empty one, fails closed (the fixture is not built). */
		const char *layout = getenv("S4FMM_LAYOUT");
		const char *names[4] = {NULL, NULL, NULL, NULL};
		int pat[4] = {0, 0, 0, 0};
		S4_real *thick[4] = {&zero, &zero, &zero, &zero};
		int nl = 0;
		if(NULL == layout){
			names[0] = "Above"; names[1] = "Slab"; pat[1] = 1; thick[1] = &half; names[2] = "Below"; nl = 3;
		}else if(0 == strcmp(layout, "P0")){
			names[0] = "Slab"; pat[0] = 1; thick[0] = &half; names[1] = "Spacer"; names[2] = "Below"; nl = 3;
		}else if(0 == strcmp(layout, "P2")){
			names[0] = "Above"; names[1] = "Spacer"; names[2] = "Slab"; pat[2] = 1; thick[2] = &half; nl = 3;
		}else if(0 == strcmp(layout, "PP1") || 0 == strcmp(layout, "PP2")){
			names[0] = "Above"; names[1] = "Slab1"; pat[1] = 1; thick[1] = &half; names[2] = "Slab2"; pat[2] = 1; thick[2] = &half; names[3] = "Below"; nl = 4;
		}else{
			std::fprintf(stderr, "S4FMM ARGERROR unknown S4FMM_LAYOUT=%s\n", layout);
			S4_Simulation_Destroy(S);
			return NULL;
		}
		for(int li = 0; li < nl; ++li){
			S4_LayerID lid = S4_Simulation_SetLayer(S, -1, names[li], thick[li], -1, mAir);
			if(pat[li] && 0 != S4_Layer_SetRegionHalfwidths(S, lid, mGlass, rtype, halfw, center, &angle_frac)){
				S4_Simulation_Destroy(S);
				return NULL;
			}
		}
	}else{
'''


def main():
    outs = [os.path.join(ST4, "inject_r8m2a2_dual_R2.cpp"), os.path.join(ST4, "inject_r8m2a2_nan_R2.cpp"),
            os.path.join(ST4, "driver_r8m2a2_layers_R2.cpp")]
    for p in outs:
        if os.path.exists(p):
            print("REFUSED exists (U17): %s" % p)
            return 2
    base_p = os.path.join(ST4, "inject_r4_plan.cpp")
    base_b = open(base_p, "rb").read()
    base = base_b.decode("utf-8")

    # ---- dual ----
    t = base
    t = rep(t, 'extern "C" void *__real_malloc(size_t);\n', T2_BLOCK + 'extern "C" void *__real_malloc(size_t);\n', "dual: T2 block")
    t = rep(t, '\tif(2 == arm && 0 == strcmp(mode(), "scratch") && 16 == n){\n', MALLOC_T2 + '\tif(2 == arm && 0 == strcmp(mode(), "scratch") && 16 == n){\n', "dual: malloc wrapper")
    t = rep(t, '\treturn __real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(n, a, b, s);\n}\n', PLAN_T2, "dual: plan wrapper")
    t = rep(t, 'extern "C" void *__wrap__Z9S4_mallocm(size_t size){\n', S4MALLOC_HEAD, "dual: S4_malloc head")
    t = rep(t, '\treturn __real__Z9S4_mallocm(size);\n}\n', S4MALLOC_TAIL, "dual: S4_malloc tail")
    t = rep(t, 'extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2_AFTER(int id, int *info, std::complex<double> *b, int n, int ld, int model){',
            'static void b2_target1_hook(int id, int *info, std::complex<double> *b, int n, int ld, int model){', "dual: b2 signature")
    t = rep(t, HDR_B2BUF, B2_WRAPPER + HDR_B2BUF, "dual: b2 wrapper")
    # the seven site IDs duplicated in the T2 block must equal the base list
    if 'static const int b2_ids[7] = {134, 138, 144, 244, 375, 265, 273};' not in base:
        raise SystemExit("ANCHOR ERROR: b2_ids list differs from t2_b2_ids")
    write_new(outs[0], t)
    write_diff("SRC_DIFF_R8_M2a2_inject_dual_srcR2.txt", "testing/d003/stage_s4/inject_r4_plan.cpp",
               "testing/d003/stage_s4/inject_r8m2a2_dual_R2.cpp", base_b, t.encode("utf-8"))

    # ---- nan ----
    n = base
    n = rep(n, 'extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER(int id, std::complex<double> *b, int n, int ld, int model){',
            'static void b2b_original_hook(int id, std::complex<double> *b, int n, int ld, int model){', "nan: b2buf signature")
    n = rep(n, HDR_FAMILY_E, NAN_WRAPPER + HDR_FAMILY_E, "nan: wrapper")
    write_new(outs[1], n)
    write_diff("SRC_DIFF_R8_M2a2_inject_nan_srcR2.txt", "testing/d003/stage_s4/inject_r4_plan.cpp",
               "testing/d003/stage_s4/inject_r8m2a2_nan_R2.cpp", base_b, n.encode("utf-8"))

    # ---- layers driver ----
    dp = os.path.join(ST4, "driver_r6b_state.cpp")
    d_b = open(dp, "rb").read()
    d = d_b.decode("utf-8")
    start_marker = '\tif(0 == strcmp(which, "pattern")){\n'
    end_marker = '\t}else{\n\t\tS4_Simulation_SetLayer(S, -1, "Above", &zero, -1, mAir);\n\t\tS4_Simulation_SetLayer(S, -1, "Spacer", &zero, -1, mAir);\n'
    if d.count(start_marker) != 1 or d.count(end_marker) != 1:
        raise SystemExit("ANCHOR ERROR layers: stack markers")
    i0 = d.index(start_marker)
    i1 = d.index(end_marker)
    if not i0 < i1:
        raise SystemExit("ANCHOR ERROR layers: marker order")
    d = d[:i0] + LAYERS_STACK + d[i1 + len('\t}else{\n'):]
    d = rep(d, '\tconst int twice = (NULL != tw && 0 == strcmp(tw, "slab"));\n',
            '\tconst int twice = (NULL != tw && 0 == strcmp(tw, "slab"));\n'
            '\tif(twice && NULL != getenv("S4FMM_LAYOUT")){ std::fprintf(stderr, "S4FMM ARGERROR S4FMM_TWICE is not supported with S4FMM_LAYOUT\\n"); return 2; }\n',
            "layers: twice guard")
    d = rep(d, '\tif(NULL == S){ std::fprintf(stderr, "fixture failed\\n"); return 2; }\n',
            '\tif(NULL == S){ std::fprintf(stderr, "fixture failed\\n"); return 2; }\n'
            '\t{ const char *lay_name = getenv("S4FMM_LAYOUT"); std::printf("S4FMM LAYOUT %s n_layers %d\\n", NULL != lay_name ? lay_name : "default", (int)S->n_layers); }\n',
            "layers: layout print")
    write_new(outs[2], d)
    write_diff("SRC_DIFF_R8_M2a2_driver_layers_srcR2.txt", "testing/d003/stage_s4/driver_r6b_state.cpp",
               "testing/d003/stage_s4/driver_r8m2a2_layers_R2.cpp", d_b, d.encode("utf-8"))
    for p in outs:
        print("wrote %s sha256=%s" % (os.path.relpath(p, REPO), sha(open(p, "rb").read())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
