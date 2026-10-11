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

/* Read-only view of the hit counter for the driver. */
extern "C" long s4fmm_inject_hits(void){ return n_hits; }
extern "C" int s4fmm_inject_requested(void){ return '\0' != mode()[0]; }

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

/* S4_malloc, FMM callers only (see header comment).  The symbol is defined in
 * S4.o; this wrapper receives only the undefined references from fmm_*.o. */
extern "C" void *__real__Z9S4_mallocm(size_t);
extern "C" void *__wrap__Z9S4_mallocm(size_t size){
	if(0 == strcmp(mode(), "s4malloc")){
		n_s4malloc++;
		if(n_s4malloc == nth()){
			n_hits++;
			std::fprintf(stderr, "S4FMM HIT real S4_malloc failure: FMM call %zu B (hit=%ld)\n", size, n_s4malloc);
			return NULL;
		}
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
