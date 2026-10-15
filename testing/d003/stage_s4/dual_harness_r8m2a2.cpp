/* dual_harness_r8m2a2.cpp -- P05-S4 R8 M2a2 R3 synthetic harness (NOT an S4 driver; does NOT link libS4).
 *
 * Links only: this file + inject_r8m2a2_dual_R3.o + dual_stubs_r8m2a2.o.  It replays a fixed synthetic event
 * stream into the injector's hook entry points and prints one result line.  The shell wrapper
 * dual_harness_r8m2a2.sh sets the environment for each case and records the line.
 *
 * Event stream (fixed):
 *   S4_malloc stream : 6 calls to __wrap__Z9S4_mallocm (stream indices 1..6)
 *   plan stream      : 3 calls to __wrap__Z15fft_plan_dft_2d; each plan call performs 4 wrapped malloc calls
 *                      inside the stand-in (M = 1..4)
 *   B2 stream        : 3 calls to S4_TEST_LINEARSOLVE_NULLINFO2_AFTER(244, ...) (K = 1..3)
 *
 * Output (stdout, one line):
 *   HARNESS_RESULT s4_null=<n> b2_info=<n> hits=<n> hits2=<n> invalid2=<n> suppressed2=<n> requested2=<n> plan_mallocs=<n>
 *   s4_null  : S4_malloc calls that returned NULL (target 1 or target 2)
 *   b2_info  : B2 calls that set info = 1 (target 1 or target 2)
 *   hits     : s4fmm_inject_hits()  (all injections, target 1 + target 2)
 *   hits2    : s4fmm_inject2_hits() (target 2 only)
 *
 * No file is read or written.  No environment variable is set here (the shell does that).
 */
#include <complex>
#include <cstdio>
#include <cstdlib>

/* same type as fmm/fft_iface.h (typedef struct tag_fft_plan *fft_plan); the header is not included here */
struct tag_fft_plan;
typedef struct tag_fft_plan *fft_plan;
extern "C" void *__wrap__Z9S4_mallocm(size_t size);
extern "C" fft_plan __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(int *n, std::complex<double> *a, std::complex<double> *b, int s);
extern "C" int __wrap__Z13fft_plan_execP12tag_fft_plan(fft_plan p);
extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2_AFTER(int id, int *info, std::complex<double> *b, int n, int ld, int model);
extern "C" long s4fmm_inject_hits(void);
extern "C" long s4fmm_inject2_hits(void);
extern "C" long s4fmm_inject2_invalid(void);
extern "C" long s4fmm_inject2_suppressed(void);
extern "C" int s4fmm_inject2_requested(void);
extern int g_plan_mallocs_per_call;   /* defined in dual_stubs_r8m2a2.cpp (C++ linkage) */

#ifdef S4FMM_DUAL_HARNESS
extern "C" void s4fmm_dual_harness_force_t2(int kind, long a, long b);
#endif

int main(void){
	const int NMALLOC = 6, NPLAN = 3, NB2 = 3, PLAN_M = 4;
	int s4_null = 0, b2_info = 0;

#ifdef S4FMM_DUAL_HARNESS
	/* SUPPRESSED case only (rule 4): HARNESS_FORCE_T2=KIND:A:B bypasses the parse-time rule 2 so that target 2 names the
	 * SAME event target 1 consumes, which the runtime fallback must catch.  Only the harness build defines this path. */
	const char *force = getenv("HARNESS_FORCE_T2");
	if(NULL != force && '\0' != force[0]){
		int kind = 0; long a = 0, b = 0;
		if(3 == std::sscanf(force, "%d:%ld:%ld", &kind, &a, &b)){ s4fmm_dual_harness_force_t2(kind, a, b); }
	}
#endif

	/* S4_malloc stream */
	for(int i = 0; i < NMALLOC; ++i){
		void *p = __wrap__Z9S4_mallocm(64);
		if(NULL == p){ s4_null++; }
		else { std::free(p); }
	}

	/* plan stream: each plan call performs PLAN_M wrapped mallocs inside the stand-in */
	int plan_mallocs = 0;
	for(int k = 0; k < NPLAN; ++k){
		int n2[2] = {8, 8};
		std::complex<double> a[1], b[1];
		g_plan_mallocs_per_call = PLAN_M;
		plan_mallocs += PLAN_M;
		fft_plan p = __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i(n2, a, b, 0);
		if(NULL != p){ (void)__wrap__Z13fft_plan_execP12tag_fft_plan(p); }
	}

	/* B2 stream: 2x2 identity-sized buffer, model 1 */
	for(int k = 0; k < NB2; ++k){
		int info = 0;
		std::complex<double> buf[4];
		for(int i = 0; i < 4; ++i){ buf[i] = std::complex<double>(0.0, 0.0); }
		S4_TEST_LINEARSOLVE_NULLINFO2_AFTER(244, &info, buf, 2, 2, 1);
		if(info != 0){ b2_info++; }
	}

	std::printf("HARNESS_RESULT s4_null=%d b2_info=%d hits=%ld hits2=%ld invalid2=%ld suppressed2=%ld requested2=%d plan_mallocs=%d\n",
	            s4_null, b2_info, s4fmm_inject_hits(), s4fmm_inject2_hits(), s4fmm_inject2_invalid(),
	            s4fmm_inject2_suppressed(), s4fmm_inject2_requested(), plan_mallocs);
	return 0;
}
