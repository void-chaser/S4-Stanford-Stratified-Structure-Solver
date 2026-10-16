/* inject_r8m2e_aligned.cpp -- P05-S4 R8 M2e injector (aligned malloc interceptor).
 *
 * Test-only. Linked only by init-F3-san-AL. Nothing here goes into S4/.
 *
 * Based on inject_s3r4_init.cpp:
 *   - retains all transparent wrap forwardings:
 *       --wrap=malloc
 *       --wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i
 *       --wrap=_Z13fft_plan_execP12tag_fft_plan
 *       --wrap=_Z9S4_mallocm
 *       --wrap=Pattern_GetContainmentTree
 *   - adds:
 *       --wrap=malloc_aligned
 *
 * Environment request:
 *   S4FMM_INJECT = aligned:K   the K-th malloc_aligned call returns NULL (fails at most once per process).
 *   S4FMM_INJECT = win:M       the M-th malloc inside Pattern_GetContainmentTree window returns NULL.
 *   S4FMM_INJECT = init:K      the K-th malloc outside windows returns NULL.
 *   S4FMM_INJECT unset         counting only (no failure).
 */
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstddef>
#include "fmm/fft_iface.h"
#include <complex>

extern "C" void *__real_malloc(size_t);
extern "C" void *__real_malloc_aligned(size_t size, size_t alignment);

static int in_window = 0;
static long count_window = 0;
static long count_outside = 0;
static long count_aligned = 0;
static long n_hits = 0;
static int mode_win = 0;      /* 1 = win:M requested */
static int mode_init = 0;     /* 1 = init:K requested */
static int mode_aligned = 0;  /* 1 = aligned:K requested */
static long m_req = 0;
static int parsed = 0;

static void parse_request(void){
	const char *m = getenv("S4FMM_INJECT");
	mode_win = 0; mode_init = 0; mode_aligned = 0; m_req = 0;
	if(NULL == m){ return; }
	char *end = NULL;
	if(0 == strncmp(m, "aligned:", 8)){
		long v = strtol(m + 8, &end, 10);
		if(end != m + 8 && '\0' == *end && v >= 1){ mode_aligned = 1; m_req = v; }
	}else if(0 == strncmp(m, "win:", 4)){
		long v = strtol(m + 4, &end, 10);
		if(end != m + 4 && '\0' == *end && v >= 1){ mode_win = 1; m_req = v; }
	}else if(0 == strncmp(m, "init:", 5)){
		long v = strtol(m + 5, &end, 10);
		if(end != m + 5 && '\0' == *end && v >= 1){ mode_init = 1; m_req = v; }
	}
}

static void ensure_parsed(void){
	if(!parsed){
		parse_request();
		parsed = 1;
	}
}

extern "C" long s4fmm_inject_hits(void){ return n_hits; }
extern "C" int s4fmm_inject_requested(void){
	const char *m = getenv("S4FMM_INJECT");
	return (NULL != m && '\0' != m[0]) ? 1 : 0;
}

extern "C" void *__wrap_malloc_aligned(size_t size, size_t alignment){
	ensure_parsed();
	count_aligned++;
	int hit = 0;
	if(mode_aligned && 0 == n_hits && count_aligned == m_req){
		hit = 1;
		n_hits++;
	}
	std::fprintf(stderr, "S4FMM S4_MALLOC_ALIGNED k=%ld size=%zu alignment=%zu caller=%p hit=%d\n",
	             count_aligned, size, alignment, __builtin_return_address(0), hit);
	if(hit){
		std::fprintf(stderr, "S4FMM HIT real malloc failure: malloc_aligned %ld, %zu B (hit=%ld)\n",
		             count_aligned, size, n_hits);
		return NULL;
	}
	return __real_malloc_aligned(size, alignment);
}

extern "C" void *__wrap_malloc(size_t n){
	ensure_parsed();
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
