/* D003 test-only fault injector (P05-S2 consolidated version).
 *
 * Test-only.  Nothing here is compiled into the candidate or the real tree; it
 * is linked only by testing/d003/run_d003.sh, with link-time --wrap options.
 *
 * Provenance: derived from the history injector (testing/d003/src/history/
 * inject.history.cpp, sha256 13b2cbf5...), with the S2/S3 observation code
 * kept behind -DS4FMM_OBSERVE.  Injection decisions are unchanged from the
 * history version.  The new "s4malloc" mode and the hit-count accessor are
 * added by P05-S2 (this round).
 *
 * Environment:
 *   S4FMM_INJECT = scratch | plan | exec | s4malloc   (unset = no request)
 *   S4FMM_NTH    = k                                    (1-based)
 *
 *   scratch  : the k-th 16-byte allocation made inside fft_plan_exec really fails
 *              (kf_bfly_generic scratch for a length-1 transform).  REAL site.
 *   plan     : the k-th allocation made inside fft_plan_dft_2d really fails
 *              (preparation stage).  REAL site.
 *   exec     : the k-th fft_plan_exec returns 1 without running the transform.
 *              BOUNDARY SIMULATION: no execution-time allocation exists there.
 *   s4malloc : the k-th S4_malloc call that is made from an FMM translation unit
 *              returns NULL.  Implemented with the link-time wrapper
 *              --wrap=_Z9S4_mallocm; S4.o's own calls are not intercepted
 *              (measured, see P05_S2_TEST_HARNESS.md).  REAL site.
 *
 * The injector fires at most once per process.  s4fmm_inject_hits() returns the
 * number of times the requested fault was actually applied; the driver uses it
 * to refuse a PASS when a requested injection was never reached.
 */
#include "fmm/fft_iface.h"
#include <complex>
#include <cstdio>
#include <cstdlib>
#include <cstring>

static const char *mode(void){ const char *m = getenv("S4FMM_INJECT"); return m ? m : ""; }
static long nth(void){ const char *e = getenv("S4FMM_NTH"); return e ? strtol(e, NULL, 10) : 1; }
static int arm = 0;              /* 1 = inside plan creation, 2 = inside execution */
static long n_plan_alloc = 0, n_scratch = 0, n_plan_calls = 0, n_exec_calls = 0;
static long n_s4malloc = 0, n_hits = 0;

/* [P05-S4 R4-4] plancall:K:M -- two independent counters for plan injection.
 *   K = the K-th fft_plan_dft_2d call of the process (1-based).
 *   M = the M-th wrapped malloc INSIDE that call (1-based); the count is reset when call K starts.
 * The original mode "plan" (one NTH used for both counts) is kept unchanged. */
static int pc_ok = 0;
static long pc_k = 0, pc_m = 0, pc_alloc = 0;
static void pc_parse(void){
	const char *m = mode();
	long k = 0, mm = 0;
	int used = 0;
	pc_ok = 0;
	if(0 != strncmp(m, "plancall:", 9)){ return; }
	/* "%ld:%ld%n": %n records how many characters were consumed; anything after them is refused */
	if(2 != sscanf(m + 9, "%ld:%ld%n", &k, &mm, &used)){ return; }
	if('\0' != m[9 + used]){ return; }   /* trailing text after M: refuse (fail closed) */
	if(k < 1 || mm < 1){ return; }
	pc_k = k; pc_m = mm; pc_ok = 1;
}

/* Read-only view of the hit counter for the driver. */
extern "C" long s4fmm_inject_hits(void){ return n_hits; }
extern "C" int s4fmm_inject_requested(void){ return '\0' != mode()[0]; }

/* ------------------------------------------------------------------------
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

extern "C" void *__real_malloc(size_t);
extern "C" void *__wrap_malloc(size_t n){
#ifdef S4FMM_OBSERVE
	/* [S2 T10 / S3 T13] Observation only: counts every malloc that reaches the
	 * wrapper and prints size and return addresses when S4FMM_MALLOC_LOG is set.
	 * It does not change any injection decision (S3: 8 decision lines = 8). */
	static long s_malloc_calls = 0;
	s_malloc_calls++;
	if(NULL != getenv("S4FMM_MALLOC_LOG")){
		std::fprintf(stderr, "S4FMM MALLOC_CALL3 n=%zu seq=%ld arm=%d caller0=%p caller1=%p caller2=%p\n",
		             n, s_malloc_calls, arm, __builtin_return_address(0), __builtin_return_address(1), __builtin_return_address(2));
	}
#endif
	if(1 == arm && 0 == strcmp(mode(), "plan")){
		n_plan_alloc++;
		if(n_plan_alloc == nth()){
			n_hits++;
			std::fprintf(stderr, "S4FMM HIT real malloc failure: plan preparation %zu B (hit=%ld)\n", n, n_plan_alloc);
			return NULL;
		}
	}
	/* [P05-S4 R4-4] plancall: the M-th wrapped malloc inside the selected plan call (arm == 1 only). */
	if(1 == arm && pc_ok){
		pc_alloc++;
		if(pc_alloc == pc_m){
			n_hits++;
			std::fprintf(stderr, "S4FMM HIT real malloc failure: plan call %ld malloc %ld, %zu B (hit=%ld)\n", pc_k, pc_alloc, n, n_hits);
			return NULL;
		}
	}
	/* [P05-S4 R8 M2a2 R2, U244] target 2 plancall: its own armed flag and malloc counter. */
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
	if(2 == arm && 0 == strcmp(mode(), "scratch") && 16 == n){
		n_scratch++;
		if(n_scratch == nth()){
			n_hits++;
			std::fprintf(stderr, "S4FMM HIT real malloc failure: FFT execution scratch %zu B (hit=%ld)\n", n, n_scratch);
			return NULL;
		}
	}
	return __real_malloc(n);
}

/* ------------------------------------------------------------------------
 * LinearSolve call-site seam (P05-S2.6).  Active only when the driver is linked
 * against a baseline built with -DS4_TEST_LINEARSOLVE_SEAM, which testing/d003/seam
 * applies to the exported copy OUT/baseline-src.  The hook is called after the two
 * FMM call sites:  SITE 1 = fmm_FFT.cpp:204,  SITE 2 = fmm_kottke.cpp:279.
 *
 *   S4FMM_INJECT = linearsolve:SITE:K:MODE   (SITE 1|2, K >= 1, MODE info|faithful)
 *
 *   info     : *info := 1.  The LU is not re-run; Epsilon_inv keeps what the solve wrote.
 *   faithful : *info := 1 AND Epsilon_inv := identity.  This models a real singular
 *              factorisation: the generic template skips the triangular solves when
 *              iinfo != 0, so b keeps the identity that SetMatrix wrote.  Evidence:
 *              p05-s2b/faithful/ls_b_probe (info=2 gives b = identity; info=0 gives b = inv).
 *
 * Counting is per site.  A request for site S is reached only when the hook is called
 * with site S; a request for the other site, or K greater than the calls seen, leaves
 * hits = 0 and the driver reports the injection as not reached.  An unparsable value
 * is treated as a request that is never reached (fails closed, never PASS).
 * ------------------------------------------------------------------------ */
static int ls_req_ok = 0, ls_req_site = 0, ls_req_k = 0, ls_req_faithful = 0;
static long ls_calls[3] = {0, 0, 0};   /* hook calls seen per site */
static long ls_hits[3] = {0, 0, 0};    /* injections applied per site */

static void ls_parse_request(void){
	const char *m = mode();
	ls_req_ok = 0;
	if(0 != strncmp(m, "linearsolve:", 12)){ return; }
	int site = 0, k = 0;
	char tail[32] = {0};
	if(3 != sscanf(m + 12, "%d:%d:%31s", &site, &k, tail)){ return; }
	if(site != 1 && site != 2){ return; }
	if(k < 1){ return; }
	if(0 == strcmp(tail, "info")){ ls_req_faithful = 0; }
	else if(0 == strcmp(tail, "faithful")){ ls_req_faithful = 1; }
	else { return; }
	ls_req_site = site; ls_req_k = k; ls_req_ok = 1;
}

extern "C" void S4_TEST_LINEARSOLVE_AFTER(int site, int *info, std::complex<double> *b, int n){
	ls_parse_request();
	if(site < 1 || site > 2){ return; }
	ls_calls[site]++;
	if(!ls_req_ok || site != ls_req_site){ return; }
	if(ls_calls[site] != ls_req_k){ return; }
	if(NULL == info){ return; }          /* defensive: the patch passes &solve_info, never NULL */
	*info = 1;
	if(ls_req_faithful){
		for(int j = 0; j < n; ++j){
			for(int i = 0; i < n; ++i){
				b[i + j*n] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
			}
		}
	}
	ls_hits[site]++;
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT linearsolve site=%d call=%ld mode=%s (hit=%ld)\n",
	             site, ls_calls[site], ls_req_faithful ? "faithful" : "info", n_hits);
}

/* ------------------------------------------------------------------------
 * LinearSolve info==NULL seam, family B (P05-S2R, R2-B).  Independent of family A:
 * its own macro (S4_TEST_LINEARSOLVE_SEAM_NULLINFO), its own hook, its own counters.
 *
 *   S4FMM_INJECT = linearsolve_null:ID:K      (ID 11..17, K >= 1)
 *
 *   ID 11 closed.cpp:130    model 2 (RHS is the computed matrix)
 *   ID 12 closed.cpp:133    model 1 (RHS reset to identity before the solve)
 *   ID 13 closed.cpp:138    model 1
 *   ID 14 closed.cpp:235    model 1
 *   ID 15 PolBasisJones:369 model 1
 *   ID 16 PolBasisNV:260    model 1
 *   ID 17 PolBasisVL:268    model 1
 *
 * On a hit (the K-th call of that ID):
 *   model 1 : the solve's output b is overwritten with the identity.  This is the
 *             state a zero pivot would leave, because the generic template skips the
 *             triangular solves when iinfo != 0 and the RHS was the identity.
 *   model 2 : b is left as computed.  The hit is still counted.  A zero pivot leaves
 *             the computed RHS in place, so this model changes no value; its
 *             sensitivity is expected to be INSENSITIVE, and that is a finding.
 * The info==NULL status is discarded by the call site, so no status is ever set here.
 * Unparsable, unknown ID, or K never reached: hits = 0, the driver reports INVALID.
 * ------------------------------------------------------------------------ */
static int ln_req_ok = 0, ln_req_id = 0, ln_req_k = 0;
static long ln_calls[18] = {0};   /* calls seen per id (index 11..17) */
static long ln_hits[18] = {0};

static void ln_parse_request(void){
	const char *m = mode();
	ln_req_ok = 0;
	if(0 != strncmp(m, "linearsolve_null:", 17)){ return; }
	int id = 0, k = 0;
	if(2 != sscanf(m + 17, "%d:%d", &id, &k)){ return; }
	if(id < 11 || id > 17){ return; }
	if(k < 1){ return; }
	ln_req_id = id; ln_req_k = k; ln_req_ok = 1;
}

extern "C" void S4_TEST_LINEARSOLVE_NULLINFO_AFTER(int id, std::complex<double> *b, int n, int ld, int model){
	ln_parse_request();
	if(id < 11 || id > 17){ return; }
	ln_calls[id]++;
	if(!ln_req_ok || id != ln_req_id){ return; }
	if(ln_calls[id] != ln_req_k){ return; }
	if(1 == model){
		/* n x n identity with the solve's real leading dimension ld (n or n2). */
		for(int j = 0; j < n; ++j){
			for(int i = 0; i < n; ++i){
				b[i + j*ld] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
			}
		}
	}
	ln_hits[id]++;
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT linearsolve_null id=%d call=%ld model=%d (hit=%ld)\n",
	             id, ln_calls[id], model, n_hits);
}

/* ------------------------------------------------------------------------
 * Family B2 (P05-S2R3 stage 2).  Test-only hook placed AFTER each H-tree LinearSolve and
 * BEFORE its existing check.  It sets *info (solve_info) non-zero when requested, so the
 * check takes its failure return.  Independent of family B above: its own request prefix,
 * its own counters, its own ID set (the seven H-tree sites).
 *
 *   S4FMM_INJECT = linearsolve_null2:ID:K     (ID in {134,138,144,244,375,265,273}, K >= 1)
 *
 * Model: the output buffer is written by the hook as the RHS model passed by the call site
 * (1 = identity RHS, 2 = computed RHS kept).  The hook writes ONLY when requested, so an
 * unrequested run is unaffected.  An unparsable or unknown request is never reached (fails
 * closed).
 * ------------------------------------------------------------------------ */
static int b2_req_ok = 0, b2_req_id = 0, b2_req_k = 0;
static const int b2_ids[7] = {134, 138, 144, 244, 375, 265, 273};
static long b2_calls[7] = {0};
static long b2_hits[7] = {0};

static int b2_index(int id){
	for(int i = 0; i < 7; ++i){ if(b2_ids[i] == id){ return i; } }
	return -1;
}

static void b2_parse_request(void){
	const char *m = mode();
	b2_req_ok = 0;
	if(0 != strncmp(m, "linearsolve_null2:", 18)){ return; }
	int id = 0, k = 0;
	if(2 != sscanf(m + 18, "%d:%d", &id, &k)){ return; }
	if(b2_index(id) < 0){ return; }
	if(k < 1){ return; }
	b2_req_id = id; b2_req_k = k; b2_req_ok = 1;
}

static void b2_target1_hook(int id, int *info, std::complex<double> *b, int n, int ld, int model){
	b2_parse_request();
	const int ix = b2_index(id);
	if(ix < 0){ return; }
	b2_calls[ix]++;
	if(!b2_req_ok || id != b2_req_id){ return; }
	if(b2_calls[ix] != b2_req_k){ return; }
	if(NULL == info){ return; }
	*info = 1;                                  /* models a zero pivot: the existing check takes its failure return */
	if(1 == model){
		/* identity RHS with the solve's real leading dimension ld */
		for(int j = 0; j < n; ++j){
			for(int i = 0; i < n; ++i){
				b[i + j*ld] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
			}
		}
	}
	b2_hits[ix]++;
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT linearsolve_null2 id=%d call=%ld model=%d (hit=%ld)\n",
	             id, b2_calls[ix], model, n_hits);
}

/* [P05-S4 R8 M2a2 R2, U244] Target 2 for family B2.  The original hook (target 1; body unchanged, it also counts this
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

/* ------------------------------------------------------------------------
 * Family B2-buf (P05-S2R4, R4-1).  Independent of family B2 above: its own request prefix,
 * its own counters, its own hook.  It writes ONLY the output buffer, with the same rule as
 * family B (model 1 = identity RHS over the solve's real leading dimension; any other model
 * writes nothing).  It does NOT take the solve status: no *info is written and no info
 * argument exists, so the existing check at the call site reads whatever the real solve
 * left in solve_info.  This isolates the output-model effect from the status effect.
 *
 *   S4FMM_INJECT = linearsolve_null2buf:ID:K   (ID in {134,138,144,244,375,265,273}, K >= 1)
 *
 * Unrequested runs: the hook returns before any write, so no output changes.  Unparsable or
 * unknown requests are never reached (fails closed, judge INVALID).
 * ------------------------------------------------------------------------ */
static int b2b_req_ok = 0, b2b_req_id = 0, b2b_req_k = 0;
static long b2b_calls[7] = {0};
static long b2b_hits[7] = {0};

static int b2b_index(int id){
	for(int i = 0; i < 7; ++i){ if(b2_ids[i] == id){ return i; } }
	return -1;
}

static void b2b_parse_request(void){
	const char *m = mode();
	b2b_req_ok = 0;
	if(0 != strncmp(m, "linearsolve_null2buf:", 21)){ return; }
	int id = 0, k = 0;
	if(2 != sscanf(m + 21, "%d:%d", &id, &k)){ return; }
	if(b2b_index(id) < 0){ return; }
	if(k < 1){ return; }
	b2b_req_id = id; b2b_req_k = k; b2b_req_ok = 1;
}

extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER(int id, std::complex<double> *b, int n, int ld, int model){
	b2b_parse_request();
	const int ix = b2b_index(id);
	if(ix < 0){ return; }
	b2b_calls[ix]++;
	if(!b2b_req_ok || id != b2b_req_id){ return; }
	if(b2b_calls[ix] != b2b_req_k){ return; }
	if(1 == model){
		/* identity RHS with the solve's real leading dimension ld: the same write as family B */
		for(int j = 0; j < n; ++j){
			for(int i = 0; i < n; ++i){
				b[i + j*ld] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
			}
		}
	}
	b2b_hits[ix]++;
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT linearsolve_null2buf id=%d call=%ld model=%d (hit=%ld)\n",
	             id, b2b_calls[ix], model, n_hits);
}

/* ------------------------------------------------------------------------
 * Family E (P05-S2R5, R5-1).  Test-only hooks at the FMMGetEpsilon dispatch in
 * Simulation_ComputeLayerModes (S4.cpp).  Ten points, IDs 150..159 (one per dispatch call; see
 * testing/d003/seam/apply_seam_r5_fmmret.py for the anchors).
 *
 *   fmmret:ID:K   trees A and H.  S4_TEST_FMMRET_AFTER(id, ret) returns 1 for the K-th call of
 *                 the requested ID, otherwise returns ret unchanged.  The seam assigns the return
 *                 value to fmm_ret, so the existing status check sees a failure.  The FMM function
 *                 has already run; its outputs are the real ones.
 *   fmmbuf:ID:K   tree B (no status variable exists there).  S4_TEST_FMMBUF_AFTER(id, e2, einv, n)
 *                 writes NOTHING.  It counts the call and records a hit for the requested ID.
 *
 * Unrequested runs: the hook returns before any effect, so no output changes.  Unparsable or
 * unknown requests never match (fail closed).  IDs 150..159 are not used by any other family.
 * ------------------------------------------------------------------------ */
static int fe_req_ok = 0, fe_req_id = 0, fe_req_k = 0, fe_req_buf = 0;
static const int fe_ids[10] = {150, 151, 152, 153, 154, 155, 156, 157, 158, 159};
static long fe_calls[10] = {0};
static long fe_hits[10] = {0};

static int fe_index(int id){
	for(int i = 0; i < 10; ++i){ if(fe_ids[i] == id){ return i; } }
	return -1;
}

static void fe_parse_request(void){
	const char *m = mode();
	fe_req_ok = 0;
	fe_req_buf = 0;
	if(0 == strncmp(m, "fmmret:", 7)){
		fe_req_buf = 0;
		int id = 0, k = 0;
		if(2 != sscanf(m + 7, "%d:%d", &id, &k)){ return; }
		if(fe_index(id) < 0 || k < 1){ return; }
		fe_req_id = id; fe_req_k = k; fe_req_ok = 1;
	}else if(0 == strncmp(m, "fmmbuf:", 7)){
		fe_req_buf = 1;
		int id = 0, k = 0;
		if(2 != sscanf(m + 7, "%d:%d", &id, &k)){ return; }
		if(fe_index(id) < 0 || k < 1){ return; }
		fe_req_id = id; fe_req_k = k; fe_req_ok = 1;
	}
}

extern "C" int S4_TEST_FMMRET_AFTER(int id, int ret){
	fe_parse_request();
	const int ix = fe_index(id);
	if(ix < 0){ return ret; }
	fe_calls[ix]++;
	if(!fe_req_ok || fe_req_buf || id != fe_req_id){ return ret; }
	if(fe_calls[ix] != fe_req_k){ return ret; }
	fe_hits[ix]++;
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT fmmret id=%d call=%ld ret=%d->1 (hit=%ld)\n", id, fe_calls[ix], ret, n_hits);
	return 1;
}

extern "C" void S4_TEST_FMMBUF_AFTER(int id, std::complex<double> *e2, std::complex<double> *einv, int n){
	(void)e2; (void)einv; (void)n;   /* observe only: this hook writes no output */
	fe_parse_request();
	const int ix = fe_index(id);
	if(ix < 0){ return; }
	fe_calls[ix]++;
	if(!fe_req_ok || !fe_req_buf || id != fe_req_id){ return; }
	if(fe_calls[ix] != fe_req_k){ return; }
	fe_hits[ix]++;
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT fmmbuf id=%d call=%ld (hit=%ld)\n", id, fe_calls[ix], n_hits);
}

/* ------------------------------------------------------------------------
 * Family E, tree B perturbation (P05-S2R5, R5-1 correction 2; see r5-1/B_MODEL_DESIGN.txt).
 *   fmmpert:ID:K   S4_TEST_FMMPERT_AFTER(id, e2, einv, n, n2) writes the IDENTITY into the
 *                  FMM output buffers for the K-th call of the requested ID:
 *                     Epsilon_inv (n x n, ld n)        := identity
 *                     Epsilon2 diagonal blocks (ld n2) := identity  (the 2x2 block layout of the uniform branch)
 *                  This is the repository's family-B model 1 (identity buffer) applied to the FMM outputs.
 *                  It is a CHOICE with that precedent, not a value defined by the FMM source.
 * Unrequested runs: no write.  Unparsable requests never match (fail closed).
 * ------------------------------------------------------------------------ */
static int fp_req_ok = 0, fp_req_id = 0, fp_req_k = 0;
static long fp_calls[10] = {0};

static void fp_parse_request(void){
	const char *m = mode();
	fp_req_ok = 0;
	if(0 != strncmp(m, "fmmpert:", 8)){ return; }
	int id = 0, k = 0;
	if(2 != sscanf(m + 8, "%d:%d", &id, &k)){ return; }
	if(fe_index(id) < 0 || k < 1){ return; }
	fp_req_id = id; fp_req_k = k; fp_req_ok = 1;
}

extern "C" void S4_TEST_FMMPERT_AFTER(int id, std::complex<double> *e2, std::complex<double> *einv, int n, int n2){
	fp_parse_request();
	const int ix = fe_index(id);
	if(ix < 0){ return; }
	fp_calls[ix]++;
	if(!fp_req_ok || id != fp_req_id){ return; }
	if(fp_calls[ix] != fp_req_k){ return; }
	for(int j = 0; j < n; ++j){
		for(int i = 0; i < n; ++i){
			einv[i + j*n] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
		}
	}
	for(int blk = 0; blk < 4; ++blk){
		const int r0 = (blk & 1) ? n : 0, c0 = (blk & 2) ? n : 0;
		for(int j = 0; j < n; ++j){
			for(int i = 0; i < n; ++i){
				e2[(r0 + i) + (c0 + j)*n2] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
			}
		}
	}
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT fmmpert id=%d call=%ld (hit=%ld)\n", id, fp_calls[ix], n_hits);
}

/* ------------------------------------------------------------------------
 * Family F (P05-S2R5, R5-2).  Test-only hook at the three H caller checks of
 * Simulation_AddFieldToCache (fmm_PolBasisJones 340, fmm_PolBasisNV 228, fmm_PolBasisVL 237).
 *   addf:ID:K   S4_TEST_ADDFIELD_AFTER(id, ret) returns 1 for the K-th call of the requested ID
 *               (IDs 160 Jones, 161 NV, 162 VL), otherwise the real return value ret.  The function
 *               itself has already run in full; only the caller's test is affected.  This isolates the
 *               caller's check and cleanup from the function's own NULL check (S4.cpp 4010-4012).
 * Unrequested runs: returns ret unchanged.  Unparsable or unknown requests never match (fail closed).
 * ------------------------------------------------------------------------ */
static int fa_req_ok = 0, fa_req_id = 0, fa_req_k = 0;
static long fa_calls[3] = {0};
static const int fa_ids[3] = {160, 161, 162};

static int fa_index(int id){
	for(int i = 0; i < 3; ++i){ if(fa_ids[i] == id){ return i; } }
	return -1;
}

static void fa_parse_request(void){
	const char *m = mode();
	fa_req_ok = 0;
	if(0 != strncmp(m, "addf:", 5)){ return; }
	int id = 0, k = 0;
	if(2 != sscanf(m + 5, "%d:%d", &id, &k)){ return; }
	if(fa_index(id) < 0 || k < 1){ return; }
	fa_req_id = id; fa_req_k = k; fa_req_ok = 1;
}

extern "C" int S4_TEST_ADDFIELD_AFTER(int id, int ret){
	fa_parse_request();
	const int ix = fa_index(id);
	if(ix < 0){ return ret; }
	fa_calls[ix]++;
	if(!fa_req_ok || id != fa_req_id){ return ret; }
	if(fa_calls[ix] != fa_req_k){ return ret; }
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT addf id=%d call=%ld ret=%d->1 (hit=%ld)\n", id, fa_calls[ix], ret, n_hits);
	return 1;
}

/* S4_malloc, FMM callers only (see header comment).  The symbol is defined in
 * S4.o; this wrapper receives only the undefined references from fmm_*.o. */
extern "C" void *__real__Z9S4_mallocm(size_t);
extern "C" void *__wrap__Z9S4_mallocm(size_t size){
	/* [P05-S4 R8 M2a2 R2, U244] the target 2 stream index is counted before target 1 can return NULL, so a call that
	 * target 1 fails still advances target 2's index (both index the same process-wide stream of FMM S4_malloc calls). */
	t2_parse();
	const long t2_idx = (1 == t2_kind) ? ++t2_malloc_seen : 0;
	if(0 == strcmp(mode(), "s4malloc")){
		n_s4malloc++;
		if(n_s4malloc == nth()){
			n_hits++;
			std::fprintf(stderr, "S4FMM HIT real S4_malloc failure: FMM call %zu B (hit=%ld)\n", size, n_s4malloc);
			return NULL;
		}
	}
	if(1 == t2_kind && t2_idx == t2_nth){
		n_hits2++;
		n_hits++;
		std::fprintf(stderr, "S4FMM HIT dual target2 real S4_malloc failure: FMM call %zu B (stream index %ld, hit2=%ld total=%ld)\n", size, t2_idx, n_hits2, n_hits);
		return NULL;
	}
	return __real__Z9S4_mallocm(size);
}

/* ------------------------------------------------------------------------
 * Allocation seam, family C (P05-S2R, R2-C).  Applies to S4.cpp allocation sites
 * that --wrap cannot reach (same translation unit as S4_malloc).  The seam patch
 * (testing/d003/seam/apply_seam_r2.py, export copy only) makes each site call
 * s4_alloc_hook(ID, size); a non-zero return makes that allocation return NULL.
 *
 *   S4FMM_INJECT = alloc:ID:K        (ID 21..25, K >= 1; K is the K-th call of that ID)
 *
 *   ID 21 S4.cpp:2267  *layer_modes = malloc(sizeof(LayerModes))   every layer
 *   ID 22 S4.cpp:2295  pB->q = S4_malloc(...)                     every layer
 *   ID 23 S4.cpp:2408  rwork = S4_malloc(4*n)                     non-uniform layers only
 *   ID 24 S4.cpp:2425  work  = S4_malloc(lwork)                   non-uniform layers only
 *   ID 25 S4.cpp:3977  AddFieldToCache f = S4_malloc(...)         PolBasis cache install
 *
 * Each ID counts its own calls, so "K-th hit of site X" is well defined.  Unparsable,
 * unknown ID, or K never reached: hits = 0, reported as not reached (judge: INVALID).
 * ------------------------------------------------------------------------ */
static int al_req_ok = 0, al_req_id = 0, al_req_k = 0;
static long al_calls[26] = {0};
static void al_parse_request(void){
	const char *m = mode();
	al_req_ok = 0;
	if(0 != strncmp(m, "alloc:", 6)){ return; }
	int id = 0, k = 0;
	if(2 != sscanf(m + 6, "%d:%d", &id, &k)){ return; }
	if(id < 21 || id > 25){ return; }
	if(k < 1){ return; }
	al_req_id = id; al_req_k = k; al_req_ok = 1;
}
extern "C" int S4_TEST_ALLOC_HOOK(int id, size_t size){
	al_parse_request();
	if(id < 21 || id > 25){ return 0; }
	al_calls[id]++;
	if(!al_req_ok || id != al_req_id){ return 0; }
	if(al_calls[id] != al_req_k){ return 0; }
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT alloc id=%d call=%ld size=%zu (hit=%ld)\n", id, al_calls[id], size, n_hits);
	return 1;
}

/* ------------------------------------------------------------------------
 * Family D (P05-S2R2, T1): the kottke work allocation, fmm_kottke.cpp:78.
 * Independent of family C: own macro (S4_TEST_KOTTKE_SEAM), own hook
 * (S4_TEST_KOTTKE_HOOK), own request prefix (kottke_alloc:).  The seam calls this
 * hook at the one call site, so the k-th call counted is the kottke allocation only;
 * the 24 field-output fft_alloc_complex calls in rcwa.cpp are not counted.
 *
 *   S4FMM_INJECT = kottke_alloc:31:K      (K >= 1)
 *
 * On the K-th hit the seam returns NULL for the work allocation.
 * Unreached K: hits = 0, reported as not reached (judge: INVALID).
 * ------------------------------------------------------------------------ */
static int kd_req_ok = 0, kd_req_id = 0, kd_req_k = 0;
static long kd_calls[32] = {0};
static void kd_parse_request(void){
	const char *m = mode();
	kd_req_ok = 0;
	if(0 != strncmp(m, "kottke_alloc:", 13)){ return; }
	int id = 0, k = 0;
	if(2 != sscanf(m + 13, "%d:%d", &id, &k)){ return; }
	if(id != 31){ return; }
	if(k < 1){ return; }
	kd_req_id = id; kd_req_k = k; kd_req_ok = 1;
}
extern "C" int S4_TEST_KOTTKE_HOOK(int id, size_t n){
	kd_parse_request();
	if(id != 31){ return 0; }
	kd_calls[id]++;
	if(!kd_req_ok){ return 0; }
	if(kd_calls[id] != kd_req_k){ return 0; }
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT kottke_alloc id=%d call=%ld n=%zu (hit=%ld)\n", id, kd_calls[id], n, n_hits);
	return 1;
}

extern "C" fft_plan __real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(int*, std::complex<double>*, std::complex<double>*, int);
extern "C" fft_plan __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(int *n, std::complex<double>*a, std::complex<double>*b, int s){
	n_plan_calls++;
	std::fprintf(stderr, "S4FMM WITNESS plan call=%ld grid=%dx%d\n", n_plan_calls, n[0], n[1]);
	if(0 == strcmp(mode(), "plan") && n_plan_calls == nth()){
		arm = 1;
		fft_plan p = __real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(n, a, b, s);
		arm = 0;
		return p;
	}
	/* [P05-S4 R4-4] plancall:K:M -- arm only for plan call K, and restart the malloc count M there. */
	pc_parse();
	if(pc_ok && n_plan_calls == pc_k){
		pc_alloc = 0;
		arm = 1;
		fft_plan p = __real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(n, a, b, s);
		arm = 0;
		return p;
	}
	/* [P05-S4 R8 M2a2 R2, U244] target 2 plancall: arm only for its own plan call K and restart its own count there. */
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

extern "C" int __real__Z13fft_plan_execP12tag_fft_plan(fft_plan);
extern "C" int __wrap__Z13fft_plan_execP12tag_fft_plan(fft_plan p){
	n_exec_calls++;
	if(0 == strcmp(mode(), "exec") && n_exec_calls == nth()){
		n_hits++;
		std::fprintf(stderr, "S4FMM HIT exec boundary simulation (exec call=%ld)\n", n_exec_calls);
		return 1;
	}
	arm = 2;
	int r = __real__Z13fft_plan_execP12tag_fft_plan(p);
	arm = 0;
	return r;
}
