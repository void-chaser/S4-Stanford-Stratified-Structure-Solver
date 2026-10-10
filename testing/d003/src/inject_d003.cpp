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
