/* inject_s3r4_init.cpp -- P05-S3R4 self-check (A) injector (new file; structure of inject_r6d_rnv1.cpp).
 *
 * Test-only.  Linked only by the S3R4 drivers.  Nothing here goes into S4/.
 *
 * Two windows / sites:
 *   --wrap=Pattern_GetContainmentTree : window opens on entry and closes on return (806 area malloc is inside).
 *   --wrap=malloc                     : every malloc is counted; inside the window it is the window count;
 *                                       outside the window it is the init count (S4.cpp:1729 layer parent malloc is
 *                                       one of the outside calls).
 *
 * Environment (decided by the S3R4 runner):
 *   S4FMM_INJECT = win:M   the M-th malloc inside the Pattern_GetContainmentTree window returns NULL (806 point).
 *   S4FMM_INJECT = init:K  the K-th malloc OUTSIDE every window (global outside index) returns NULL.
 *                          Which outside index is the S4.cpp:1729 parent allocation is fixed by the counting map
 *                          (section A1), not assumed.
 *   S4FMM_INJECT unset     counting only (no failure).
 *
 * Hit semantics as in the other injectors: n_hits counts failures actually applied (at most one per process).
 * The driver reads it through s4fmm_inject_hits().
 *
 * NOTE (checked before use): the injection by malloc order is a mapping result, not an assumption; the map is produced
 * by the counting run in section A1 of the S3R4 self-check and written to the map registry before any injection run.
 */
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstddef>

extern "C" void *__real_malloc(size_t);

static int in_window = 0;
static long count_window = 0;
static long count_outside = 0;
static long n_hits = 0;
static int mode_win = 0;   /* 1 = win:M requested */
static int mode_init = 0;  /* 1 = init:K requested */
static long m_req = 0;

static void parse_request(void){
	const char *m = getenv("S4FMM_INJECT");
	mode_win = 0; mode_init = 0; m_req = 0;
	if(NULL == m){ return; }
	char *end = NULL;
	if(0 == strncmp(m, "win:", 4)){
		long v = strtol(m + 4, &end, 10);
		if(end != m + 4 && '\0' == *end && v >= 1){ mode_win = 1; m_req = v; }
	}else if(0 == strncmp(m, "init:", 5)){
		long v = strtol(m + 5, &end, 10);
		if(end != m + 5 && '\0' == *end && v >= 1){ mode_init = 1; m_req = v; }
	}
}

extern "C" long s4fmm_inject_hits(void){ return n_hits; }
extern "C" int s4fmm_inject_requested(void){
	const char *m = getenv("S4FMM_INJECT");
	return (NULL != m && '\0' != m[0]) ? 1 : 0;
}

extern "C" void *__wrap_malloc(size_t n){
	static int parsed = 0;
	if(!parsed){ parse_request(); parsed = 1; }
	if(in_window){
		count_window++;
		int hit = 0;
		if(mode_win && 0 == n_hits && count_window == m_req){ hit = 1; n_hits++; }
		std::fprintf(stderr, "S4FMM S3R4_WIN_MALLOC k=%ld n=%zu caller=%p hit=%d\n",
		             count_window, n, __builtin_return_address(0), hit);
		if(hit){
			std::fprintf(stderr, "S4FMM HIT real malloc failure: S3R4 window malloc %ld, %zu B (hit=%ld)\n",
			             count_window, n, n_hits);
			return NULL;
		}
		return __real_malloc(n);
	}
	count_outside++;
	int hit = 0;
	/* init:K selects the K-th malloc outside every window (global outside index, fixed by the counting map). */
	if(mode_init && 0 == n_hits && count_outside == m_req){ hit = 1; n_hits++; }
	std::fprintf(stderr, "S4FMM S3R4_OUT_MALLOC k=%ld n=%zu caller=%p hit=%d\n",
	             count_outside, n, __builtin_return_address(0), hit);
	if(hit){
		std::fprintf(stderr, "S4FMM HIT real malloc failure: S3R4 outside malloc %ld, %zu B (hit=%ld)\n",
		             count_outside, n, n_hits);
		return NULL;
	}
	return __real_malloc(n);
}

/* Transparent forwarders for the other --wrap options of the link line (LIBFLAGS).  libS4.a refers to these wrapped
 * names, so each must be defined or the link fails (same forwarding as inject_r6d_rnv1.cpp lines 66-78).  They only
 * forward to the real symbol: no counting, no failure. */
#include "fmm/fft_iface.h"
#include <complex>
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

/* The window wraps Pattern_GetContainmentTree (pattern.h:124) */
extern "C" int __real_Pattern_GetContainmentTree(void *p);
extern "C" int __wrap_Pattern_GetContainmentTree(void *p){
	in_window = 1;
	count_window = 0;
	std::fprintf(stderr, "S4FMM S3R4_WIN_OPEN\n");
	int rc = __real_Pattern_GetContainmentTree(p);
	in_window = 0;
	std::fprintf(stderr, "S4FMM S3R4_WIN_CLOSE malloc_in_window=%ld rc=%d\n", count_window, rc);
	return rc;
}
