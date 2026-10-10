/* TEST-ONLY fault injection for the FMM epsilon path.  It lives only in this
 * harness; nothing here is compiled into the candidate or the real tree.
 *
 *   S4FMM_INJECT=scratch|plan|exec   S4FMM_NTH=k   (1-based)
 *
 *   scratch : the k-th 16-byte allocation made inside fft_plan_exec really fails.
 *             That temporary is kf_bfly_generic's scratch buffer for a length-1
 *             transform, so the failure happens at the real allocation site.
 *   plan    : the k-th allocation made inside fft_plan_dft_2d really fails
 *             (configuration / twiddles / plan wrapper - preparation stage).
 *   exec    : the k-th fft_plan_exec returns non-zero without running the
 *             transform.  BOUNDARY SIMULATION: on that configuration no
 *             execution-time allocation exists, so it is not a real failure.
 */
#include "fmm/fft_iface.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>

static const char *mode(void){ const char *m = getenv("S4FMM_INJECT"); return m ? m : ""; }
static long nth(void){ const char *e = getenv("S4FMM_NTH"); return e ? strtol(e, NULL, 10) : 1; }
static int arm = 0;              /* 1 = inside plan creation, 2 = inside execution */
static long n_plan_alloc = 0, n_scratch = 0, n_plan_calls = 0, n_exec_calls = 0;

extern "C" void *__real_malloc(size_t);
extern "C" void *__wrap_malloc(size_t n){
	if(1 == arm && 0 == strcmp(mode(), "plan")){
		n_plan_alloc++;
		if(n_plan_alloc == nth()){
			std::fprintf(stderr, "S4FMM HIT real malloc failure: plan preparation %zu B (hit=%ld)\n", n, n_plan_alloc);
			return NULL;
		}
	}
	if(2 == arm && 0 == strcmp(mode(), "scratch") && 16 == n){
		n_scratch++;
		if(n_scratch == nth()){
			std::fprintf(stderr, "S4FMM HIT real malloc failure: FFT execution scratch %zu B (hit=%ld)\n", n, n_scratch);
			return NULL;
		}
	}
	return __real_malloc(n);
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
		std::fprintf(stderr, "S4FMM HIT exec boundary simulation (exec call=%ld)\n", n_exec_calls);
		return 1;
	}
	arm = 2;
	int r = __real__Z13fft_plan_execP12tag_fft_plan(p);
	arm = 0;
	return r;
}
