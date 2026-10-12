/* inject_r6d_rnv1.cpp -- P05-S4 R6d RNV1 injector (new file; independent of inject_r4_plan.cpp).
 *
 * Test-only.  Linked only by the R6d driver build (see r6d_link_rnv1.sh).  Nothing here goes into S4/.
 *
 * Why a new injector (R6d brief 4.2): inject_r4_plan.cpp already defines __wrap_malloc.  A second __wrap_malloc
 * in the same link is a duplicate symbol.  So this file defines its own __wrap_malloc and must NOT be linked
 * together with inject_r4_plan.cpp or inject_d003.cpp.  The driver it is linked with must not need the
 * symbols of those files other than s4fmm_inject_hits and s4fmm_inject_requested, which are defined here.
 *
 * Mechanism:
 *   --wrap=Pattern_GenerateFlowField : the window opens on entry and closes on return (see the wrapper below).
 *     Wrapping pattern_generate_flow_field would NOT work (intra-object call; measured in R6d, see the comment at the wrapper).
 *   --wrap=malloc : inside the window every malloc call is counted (count_in_window, 1-based).  The M-th call returns NULL.
 *     pattern.c calls the libc malloc directly (stdlib.h, no macro), so the wrap intercepts those calls (checked in R6d).
 *   Every malloc call made inside the window is logged to stderr as
 *     "S4FMM R6D_WIN_MALLOC k=<k> n=<bytes> caller=<return address> hit=<0|1>"
 *   and the window open/close is logged as "S4FMM R6D_WIN_OPEN" / "S4FMM R6D_WIN_CLOSE rc=<return value>".
 *   With S4FMM_INJECT unset (or not rnv1:M) nothing is failed; the counting still runs (it is the "F no injection" count).
 *
 * Environment (decided by the R6d runner):
 *   S4FMM_INJECT = rnv1:M   M >= 1, the M-th window malloc returns NULL.  Any other value: no failure.
 *   S4FMM_INJECT unset      counting only (no failure).
 *
 * Hit semantics (same as the other injectors): n_hits counts failures actually applied; the driver reads it through
 * s4fmm_inject_hits().  The injector fires at most once per process.
 */
#include "fmm/fft_iface.h"
#include <complex>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstddef>

extern "C" void *__real_malloc(size_t);

static int in_window = 0;
static long count_in_window = 0;
static long m_req = 0;
static int m_ok = 0;
static long n_hits = 0;
static long n_windows = 0;
static long n_window_malloc = 0;

static void parse_request(void){
	const char *m = getenv("S4FMM_INJECT");
	m_ok = 0; m_req = 0;
	if(NULL == m){ return; }
	if(0 != strncmp(m, "rnv1:", 5)){ return; }
	char *end = NULL;
	long v = strtol(m + 5, &end, 10);
	if(end == m + 5 || '\0' != *end || v < 1){ return; }
	m_req = v; m_ok = 1;
}

extern "C" long s4fmm_inject_hits(void){ return n_hits; }
extern "C" int s4fmm_inject_requested(void){
	const char *m = getenv("S4FMM_INJECT");
	return (NULL != m && '\0' != m[0]) ? 1 : 0;
}
/* Read-only window statistics for the R6d runner (the runner reads the stderr lines; these are for gdb). */
extern "C" long r6d_window_count(void){ return n_window_malloc; }

/* Transparent forwarders for the other --wrap options of the R6b link line (LIBFLAGS).  libS4.a refers to these
 * wrapped names, so each must be defined or the link fails (found in R6d: undefined reference to
 * __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i).  They only forward to the real symbol: no counting, no failure.
 * Same forwarding as inject_r4_plan.cpp (lines 583-617, 495-505). */
extern "C" fft_plan __real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(int*, std::complex<double>*, std::complex<double>*, int);
extern "C" fft_plan __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(int *n, std::complex<double>*a, std::complex<double>*b, int s){
	return __real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(n, a, b, s);
}
extern "C" int __real__Z13fft_plan_execP12tag_fft_plan(fft_plan);
extern "C" int __wrap__Z13fft_plan_execP12tag_fft_plan(fft_plan p){
	return __real__Z13fft_plan_execP12tag_fft_plan(p);
}
extern "C" void *__real__Z9S4_mallocm(size_t);
extern "C" void *__wrap__Z9S4_mallocm(size_t size){
	return __real__Z9S4_mallocm(size);
}

extern "C" void *__wrap_malloc(size_t n){
	if(in_window){
		count_in_window++;
		n_window_malloc++;
		int hit = 0;
		/* Fire at most once per process (as the other injectors): the first window whose M-th malloc is reached.
		 * Without this, every window of a multi-window run would be failed (the header comment promises once). */
		if(m_ok && 0 == n_hits && count_in_window == m_req){
			hit = 1;
			n_hits++;
		}
		std::fprintf(stderr, "S4FMM R6D_WIN_MALLOC k=%ld n=%zu caller=%p hit=%d\n",
		             count_in_window, n, __builtin_return_address(0), hit);
		if(hit){
			/* Hit line in the protocol of the other injectors (judge_d003 / the state driver read "S4FMM HIT"). */
			std::fprintf(stderr, "S4FMM HIT real malloc failure: RNV1 window %ld malloc %ld, %zu B (hit=%ld)\n",
			             n_windows, count_in_window, n, n_hits);
			return NULL;
		}
	}
	return __real_malloc(n);
}

/* The window wraps Pattern_GenerateFlowField (pattern.h:324), NOT pattern_generate_flow_field.
 * Measured in R6d (nm of the F build): pattern_generate_flow_field and Pattern_GenerateFlowField are both defined in
 * pattern.o, so the call between them is an intra-object call that --wrap cannot intercept.  Pattern_GenerateFlowField
 * is referenced as an undefined symbol (U) from fmm_PolBasisNV.o, fmm_PolBasisJones.o and fmm_PolBasisVL.o, so
 * --wrap=Pattern_GenerateFlowField does intercept the three PolBasis callers.
 * Signature (pattern.h:324): int Pattern_GenerateFlowField(const Pattern *p, int type, const double L[4], int nu, int nv, double *value).
 * The Pattern type is not included; the pointer is const void*.  The ABI is the same. */
extern "C" int __real_Pattern_GenerateFlowField(const void *, int, const double *, int, int, double *);
extern "C" int __wrap_Pattern_GenerateFlowField(const void *p, int type, const double *L, int nu, int nv, double *value){
	/* parse_request is run once, at the first window, so that the request is read from the environment of this process. */
	static int parsed = 0;
	if(!parsed){ parse_request(); parsed = 1; }
	n_windows++;
	in_window = 1;
	count_in_window = 0;
	std::fprintf(stderr, "S4FMM R6D_WIN_OPEN k=%ld\n", n_windows);
	int rc = __real_Pattern_GenerateFlowField(p, type, L, nu, nv, value);
	in_window = 0;
	std::fprintf(stderr, "S4FMM R6D_WIN_CLOSE k=%ld malloc_in_window=%ld rc=%d\n", n_windows, count_in_window, rc);
	return rc;
}
