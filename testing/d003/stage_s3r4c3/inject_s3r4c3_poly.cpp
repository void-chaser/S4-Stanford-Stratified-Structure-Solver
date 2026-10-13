/* inject_s3r4c3_poly.cpp -- P05-S3R4 CONT3 self-check (B) injector (new file).
 *
 * Copied from testing/d003/stage_s3r4/inject_s3r4_init.cpp and renamed (CONT3 brief section 3.2).  Differences
 * from the original are listed in checkpoints/p05/evidence/p05-s3r4c3/INJECTOR_DIFF_POLY_C3.txt.
 *
 * Test-only.  Linked only by the S3R4 CONT3 polygon drivers.  Nothing here goes into S4/.
 *
 * Window: --wrap=Pattern_DiscretizeCell.  The window is the whole process: the counter is NOT reset on entry, so
 * win:M means the M-th window malloc of the whole process (cumulative count).  Every window malloc prints
 *   S4FMM S3R4C3_WIN_MALLOC k=<cumulative> n=<bytes> caller=<addr> hit=<0|1>
 * and a hit prints "S4FMM HIT real malloc failure: ..." (the driver's HITCOUNT reads n_hits).
 *
 * Environment:
 *   S4FMM_INJECT = win:M   the M-th window malloc of the process returns NULL (415 point).
 *   S4FMM_INJECT unset     counting only (no failure).
 *
 * For gdb: s4fmm_poly_window_count() returns the cumulative window malloc count at the moment of the call.
 */
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstddef>

extern "C" void *__real_malloc(size_t);

static int in_window = 0;
static long count_window = 0;   /* cumulative over the whole process (not reset per call) */
static long n_hits = 0;
static int mode_win = 0;
static long m_req = 0;

static void parse_request(void){
	const char *m = getenv("S4FMM_INJECT");
	mode_win = 0; m_req = 0;
	if(NULL == m){ return; }
	char *end = NULL;
	if(0 == strncmp(m, "win:", 4)){
		long v = strtol(m + 4, &end, 10);
		if(end != m + 4 && '\0' == *end && v >= 1){ mode_win = 1; m_req = v; }
	}
}

extern "C" long s4fmm_inject_hits(void){ return n_hits; }
extern "C" int s4fmm_inject_requested(void){
	const char *m = getenv("S4FMM_INJECT");
	return (NULL != m && '\0' != m[0]) ? 1 : 0;
}
extern "C" long s4fmm_poly_window_count(void){ return count_window; }

extern "C" void *__wrap_malloc(size_t n){
	static int parsed = 0;
	if(!parsed){ parse_request(); parsed = 1; }
	if(in_window){
		count_window++;
		int hit = 0;
		if(mode_win && 0 == n_hits && count_window == m_req){ hit = 1; n_hits++; }
		std::fprintf(stderr, "S4FMM S3R4C3_WIN_MALLOC k=%ld n=%zu caller=%p hit=%d\n",
		             count_window, n, __builtin_return_address(0), hit);
		if(hit){
			std::fprintf(stderr, "S4FMM HIT real malloc failure: S3R4C3 poly window malloc %ld, %zu B (hit=%ld)\n",
			             count_window, n, n_hits);
			return NULL;
		}
		return __real_malloc(n);
	}
	return __real_malloc(n);
}

/* Transparent forwarders for the other --wrap options of the link line (same as inject_s3r4_init.cpp). */
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

/* The window wraps Pattern_DiscretizeCell (pattern.h:258).  The count is cumulative; the window flag only tells
 * the malloc wrapper that a call to Pattern_DiscretizeCell is in progress. */
struct Pattern;
extern "C" int __real_Pattern_DiscretizeCell(const Pattern *p, const double L[4], int nu, int nv, int iu, int iv, double *value);
extern "C" int __wrap_Pattern_DiscretizeCell(const Pattern *p, const double L[4], int nu, int nv, int iu, int iv, double *value){
	in_window = 1;
	int rc = __real_Pattern_DiscretizeCell(p, L, nu, nv, iu, iv, value);
	in_window = 0;
	return rc;
}
