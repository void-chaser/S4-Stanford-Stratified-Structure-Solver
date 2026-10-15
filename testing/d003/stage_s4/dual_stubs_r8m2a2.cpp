/* dual_stubs_r8m2a2.cpp -- P05-S4 R8 M2a2 R3 synthetic harness stubs (NOT S4 code, NOT linked with libS4).
 *
 * The injector object refers to the real functions through --wrap: __real_<sym> resolves to <sym>.  The stubs below
 * define exactly those C++ symbols (same mangled names as the S4 library provides) with trivial bodies:
 *   S4_malloc(size_t)                     -> _Z9S4_mallocm       : plain malloc (its malloc call goes through __wrap_malloc)
 *   fft_plan_dft_2d(int*, complex*, complex*, int) -> _Z15fft_plan_dft_2dPiPSt7complexIdES2_i
 *                                           : performs g_plan_mallocs_per_call wrapped mallocs, returns a dummy plan
 *   fft_plan_exec(fft_plan)               -> _Z13fft_plan_execP12tag_fft_plan : returns 0 (success)
 * __real_malloc is resolved to libc malloc through --wrap=malloc.
 * The signatures come from fmm/fft_iface.h (read from the exported F3 tree; declarations only).
 * No file is read or written by this file. */
#include <complex>
#include <cstddef>
#include <cstdlib>
#include "fmm/fft_iface.h"

struct tag_fft_plan { int dummy; };
static struct tag_fft_plan g_dummy_plan = {0};

/* set by the harness before each plan call: number of malloc calls the stand-in plan performs (wrapped) */
int g_plan_mallocs_per_call = 0;

void *S4_malloc(size_t n){
	return std::malloc(n);
}

fft_plan fft_plan_dft_2d(int n[2], std::complex<double> *in, std::complex<double> *out, int sign){
	(void)n; (void)in; (void)out; (void)sign;
	for(int i = 0; i < g_plan_mallocs_per_call; ++i){
		void *p = std::malloc(16);
		if(NULL != p){ std::free(p); }
	}
	return &g_dummy_plan;
}

int fft_plan_exec(const fft_plan plan){
	(void)plan;
	return 0;
}
