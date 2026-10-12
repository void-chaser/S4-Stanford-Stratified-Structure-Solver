/* driver_r6_state.cpp -- P05-S4 R6-2 (new file; copied from testing/d003/src/driver_d003.cpp and then modified).
 *
 * Purpose: observe the S4 state at a failure INSTANT (S3-4b: "a failed layer installs no modes and no cache").
 * It records a state snapshot S0..S3 (readable from the public/internal headers) and calls an empty noinline function
 * r6_probe(k) at each snapshot so that gdb can read the private state (solution->solved, field_cache nodes, modes->q)
 * at the same instant.
 *
 * Call sequence (task brief 5.1):
 *   S0 -> call1 -> S1 -> [if S4FMM_TWICE=slab: DestroyLayerModes(1) -> S1'] -> call2 -> S2 -> call3 -> S3
 *   once route  : the injection lands in call1; call2 is the retry (kept, as in the brief).
 *   twice route : the injection lands in call2; call3 is the retry.
 *   The retry call (call3 for twice, call2 for once) is NOT the injected call; it checks that the retry result is stable.
 *
 * The PASS/FAIL lines of the original driver are NOT used and NOT printed as a verdict (judge = r6_state_judge.py).
 * The original expectation "failed call returns the allocation code 1" is NOT used (S4 returns 20 in this route, E5-14).
 *
 * Output lines (machine readable, one fact per line):
 *   R6STATE <k> layer <i> modes_null <0|1> modes_ptr <hex> copy <int> nshapes <int>
 *   R6STATE <k> cache layer <i> cached_null <0|1> cached_ptr <hex>
 *   R6STATE <k> solution_null <0|1> field_cache_null <0|1> n_layers <int>
 *   R6STATE <k> rc <int>
 *   R6STATE <k> sentinel E <0|1> H <0|1>        (1 = untouched, the output buffer still holds the sentinel)
 *   R6CALLS <k> <rc>                             (k = the snapshot index that the rc belongs to)
 *
 * The injector (inject_r6.cpp) is linked with this file; the environment variables are the same as for driver_d003.
 */
#include <climits>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "S4.h"
#include "S4_internal.h"

extern "C" long s4fmm_inject_hits(void);
extern "C" int s4fmm_inject_requested(void);

static const S4_real SENTINEL = -98765.4321;
static const size_t PAD = 8;

struct Buf {
	std::vector<S4_real> data;
	size_t payload;
	Buf(size_t n) : data(n + 2*PAD, SENTINEL), payload(n) {}
	S4_real *ptr(){ return data.data() + PAD; }
	bool untouched() const {
		for(size_t i = 0; i < payload; ++i){ if(data[PAD+i] != SENTINEL){ return false; } }
		return true;
	}
};

/* Empty function: gdb breakpoint location for the private-state reads of each snapshot. */
extern "C" __attribute__((noinline)) void r6_probe(int k){
	/* Keep the call alive and visible to gdb. */
	asm volatile("" : : "r"(k) : "memory");
}

static int g_ng = 1;

/* make_stack: identical to driver_d003.cpp (FMM_MODE selection, pattern/flat stack, excitation). */
static S4_Simulation *make_stack(const char *which, double freq){
	S4_real Lr[4] = {1, 0, 0, 1};
	if(NULL != getenv("FMM_MODE") && 0 == strcmp(getenv("FMM_MODE"), "closed1d")){ Lr[0] = 1; Lr[1] = 0; Lr[2] = 0; Lr[3] = 0; }
	S4_Simulation *S = S4_Simulation_New(Lr, (unsigned int)g_ng, NULL);
	if(NULL == S){ return NULL; }
	const char *mode = getenv("FMM_MODE");
	if(mode && !strcmp(mode,"fft")) S->options.use_discretized_epsilon=1;
	if(mode && !strcmp(mode,"kottke")){S->options.use_discretized_epsilon=1;S->options.use_subpixel_smoothing=1;}
	if(mode && (!strcmp(mode,"jones")||!strcmp(mode,"nv")||!strcmp(mode,"vl"))){S->options.use_polarization_basis=1;S->options.use_jones_vector_basis=!strcmp(mode,"jones");S->options.use_normal_vector_basis=!strcmp(mode,"nv");}
	if(mode && !strcmp(mode,"experimental")){ S->options.use_experimental_fmm = 1; }
	if(mode && (!strcmp(mode,"fftjones")||!strcmp(mode,"fftnv")||!strcmp(mode,"fftvl"))){
		S->options.use_discretized_epsilon = 1; S->options.use_polarization_basis = 1;
		S->options.use_jones_vector_basis = !strcmp(mode,"fftjones"); S->options.use_normal_vector_basis = !strcmp(mode,"fftnv");
	}
	S4_real air[1] = {1.0}, glass[1] = {4.0};
	S4_real ten[5] = {4.0, 0.0, 4.0, 0.0, 4.0};
	S4_MaterialID mAir = S4_Simulation_SetMaterial(S, -1, "Air", S4_MATERIAL_TYPE_SCALAR_REAL, air);
	S4_MaterialID mGlass = (NULL != mode && 0 == strcmp(mode, "tensor"))
		? S4_Simulation_SetMaterial(S, -1, "Glass", S4_MATERIAL_TYPE_XYTENSOR_REAL, ten)
		: S4_Simulation_SetMaterial(S, -1, "Glass", S4_MATERIAL_TYPE_SCALAR_REAL, glass);
	S4_real zero = 0.0, half = 0.5;
	if(0 == strcmp(which, "pattern")){
		S4_Simulation_SetLayer(S, -1, "Above", &zero, -1, mAir);
		S4_LayerID slab = S4_Simulation_SetLayer(S, -1, "Slab", &half, -1, mAir);
		S4_real radius[2] = {0.25, 0.25}, center[2] = {0.0, 0.0}, angle_frac = 0.0;
		const int is1d = (NULL != mode && 0 == strcmp(mode, "closed1d"));
		const int rtype = is1d ? S4_REGION_TYPE_INTERVAL : S4_REGION_TYPE_CIRCLE;
		S4_real ival[2] = {0.25, 0.0};
		if(0 != S4_Layer_SetRegionHalfwidths(S, slab, mGlass, rtype,
		                                     is1d ? ival : radius, center, &angle_frac)){
			S4_Simulation_Destroy(S);
			return NULL;
		}
		S4_Simulation_SetLayer(S, -1, "Below", &zero, -1, mAir);
	}else{
		S4_Simulation_SetLayer(S, -1, "Above", &zero, -1, mAir);
		S4_Simulation_SetLayer(S, -1, "Spacer", &zero, -1, mAir);
		S4_Simulation_SetLayer(S, -1, "Below", &half, -1, mGlass);
	}
	S4_real kdir[3] = {0, 0, 1}, udir[3] = {0, 1, 0};
	{
		const char *s5_th = getenv("S4FMM_THETA");
		const char *s5_ph = getenv("S4FMM_PHI");
		if(NULL != s5_th || NULL != s5_ph){
			const double s5_t = (NULL != s5_th ? atof(s5_th) : 0.0) * 3.14159265358979323846 / 180.0;
			const double s5_p = (NULL != s5_ph ? atof(s5_ph) : 0.0) * 3.14159265358979323846 / 180.0;
			kdir[0] = (S4_real)(sin(s5_t)*cos(s5_p));
			kdir[1] = (S4_real)(sin(s5_t)*sin(s5_p));
			kdir[2] = (S4_real)(cos(s5_t));
			udir[0] = (S4_real)(-sin(s5_p));
			udir[1] = (S4_real)(cos(s5_p));
			udir[2] = 0;
		}
	}
	S4_real cu[2] = {1, 0}, cv[2] = {0, 0};
	S4_Simulation_ExcitationPlanewave(S, kdir, udir, cu, cv);
	S4_real f[2] = {freq, 0.0};
	S4_Simulation_SetFrequency(S, f);
	return S;
}

static int argi(const char *name, long lo, long hi){ const char *e = getenv(name);
	if(NULL == e){ std::fprintf(stderr, "S4FMM ARGERROR missing %s\n", name); std::exit(2); }
	char *end = NULL; long v = strtol(e, &end, 10);
	if(NULL == end || *end != 0 || v < lo || v > hi){ std::fprintf(stderr, "S4FMM ARGERROR invalid %s=%s\n", name, e); std::exit(2); }
	return (int)v; }

/* Snapshot of the state that the driver can read from the headers.  Prints R6STATE lines and calls r6_probe(k). */
static void r6_snap(const S4_Simulation *S, int k, const Buf *be, const Buf *bh, int sentinel_check){
	const int n_layers = S->n_layers;
	std::printf("R6STATE %d n_layers %d\n", k, n_layers);
	std::printf("R6STATE %d solution_null %d\n", k, (NULL == S->solution) ? 1 : 0);
	std::printf("R6STATE %d field_cache_null %d\n", k, (NULL == S->field_cache) ? 1 : 0);
	for(int i = 0; i < n_layers; ++i){
		const S4_Layer *L = &S->layer[i];
		std::printf("R6STATE %d layer %d modes_null %d modes_ptr %p copy %d nshapes %d\n",
		            k, i, (NULL == L->modes) ? 1 : 0, (void*)L->modes, (int)L->copy, (int)L->pattern.nshapes);
		std::complex<double> *P = Simulation_GetCachedField(S, L);
		std::printf("R6STATE %d cache layer %d cached_null %d cached_ptr %p\n", k, i, (NULL == P) ? 1 : 0, (void*)P);
	}
	if(sentinel_check){
		std::printf("R6STATE %d sentinel E %d H %d\n", k,
		            (NULL != be && be->untouched()) ? 1 : 0, (NULL != bh && bh->untouched()) ? 1 : 0);
	}
	r6_probe(k);
}

int main(int argc, char **argv){
	if(argc < 3){
		std::fprintf(stderr, "usage: %s <flat|pattern> <both|e|h> [nu nv]\n", argv[0]);
		return 2;
	}
	const char *stack = argv[1];
	const char *outs = argv[2];
	int nu = (argc > 3 ? atoi(argv[3]) : 4);
	int nv = (argc > 4 ? atoi(argv[4]) : 3);
	int nxy[2] = {nu, nv};
	const size_t n = 6 * (size_t)nu * (size_t)nv;
	const S4_real xyz[3] = {0.0, 0.0, 0.05};

	const char *mode = getenv("FMM_MODE");
	if(NULL == mode || (strcmp(mode,"fft") && strcmp(mode,"kottke") && strcmp(mode,"jones") && strcmp(mode,"nv") && strcmp(mode,"vl")
	    && strcmp(mode,"experimental") && strcmp(mode,"closed2d") && strcmp(mode,"closed1d") && strcmp(mode,"tensor")
	    && strcmp(mode,"fftjones") && strcmp(mode,"fftnv") && strcmp(mode,"fftvl"))){
		std::fprintf(stderr, "S4FMM ARGERROR invalid or missing FMM_MODE=%s\n", mode ? mode : "(unset)"); return 2; }
	g_ng = argi("S4FMM_NG", 1, 64);
	std::printf("S4FMM DRIVER_R6 mode=%s num_basis=%d\n", mode, g_ng);
	S4_Simulation *S = make_stack(stack, 0.999);
	if(NULL == S){ std::fprintf(stderr, "fixture failed\n"); return 2; }

	Buf both_e(n), both_h(n);
	S4_real *Ep = (0 == strcmp(outs, "h") ? NULL : both_e.ptr());
	S4_real *Hp = (0 == strcmp(outs, "e") ? NULL : both_h.ptr());

	/* S0: before the first call. */
	r6_snap(S, 0, &both_e, &both_h, 0);

	/* call1 */
	int rc1 = S4_Simulation_GetFieldPlane(S, nxy, xyz, Ep, Hp);
	std::printf("RC first %d\n", rc1);
	std::printf("R6CALLS 1 %d\n", rc1);
	std::printf("R6STATE 1 rc %d\n", rc1);
	/* S1: after call1. */
	r6_snap(S, 1, &both_e, &both_h, 1);

	/* TWICE route (identical to driver_d003.cpp): destroy the modes of layer 1 between the calls. */
	if(const char *tw = getenv("S4FMM_TWICE")){
		if(0 == strcmp(tw, "slab")){ S4_Simulation_DestroyLayerModes(S, 1); }
	}
	/* S1': after the destroy (twice route only; for once it is the same instant as S1 and is still printed). */
	r6_snap(S, 2, &both_e, &both_h, 0);

	/* call2 */
	Buf retry2_e(n), retry2_h(n);
	S4_real *Ep2 = (0 == strcmp(outs, "h") ? NULL : retry2_e.ptr());
	S4_real *Hp2 = (0 == strcmp(outs, "e") ? NULL : retry2_h.ptr());
	int rc2 = S4_Simulation_GetFieldPlane(S, nxy, xyz, Ep2, Hp2);
	std::printf("RC retry %d\n", rc2);
	std::printf("R6CALLS 2 %d\n", rc2);
	std::printf("R6STATE 2 rc %d\n", rc2);
	/* S2: after call2. */
	r6_snap(S, 3, &retry2_e, &retry2_h, 1);

	/* call3: the retry after the failure (for twice: call3 is the retry; for once: call2 was already the retry). */
	Buf retry3_e(n), retry3_h(n);
	S4_real *Ep3 = (0 == strcmp(outs, "h") ? NULL : retry3_e.ptr());
	S4_real *Hp3 = (0 == strcmp(outs, "e") ? NULL : retry3_h.ptr());
	int rc3 = S4_Simulation_GetFieldPlane(S, nxy, xyz, Ep3, Hp3);
	std::printf("R6CALLS 3 %d\n", rc3);
	std::printf("R6STATE 3 rc %d\n", rc3);
	/* S3: after call3. */
	r6_snap(S, 4, &retry3_e, &retry3_h, 1);

	/* Output dump of the call that produced the field used for the byte comparison: call3 (the retry). */
	if(const char *dpath = getenv("S4FMM_DUMP")){
		FILE *df = std::fopen(dpath, "w");
		if(df){
			if(NULL != Ep3){ for(size_t q = 0; q < n; ++q){ std::fprintf(df, "E %zu %.17g\n", q, (double)Ep3[q]); } }
			if(NULL != Hp3){ for(size_t q = 0; q < n; ++q){ std::fprintf(df, "H %zu %.17g\n", q, (double)Hp3[q]); } }
			std::fclose(df);
		}
	}

	const bool requested = (0 != s4fmm_inject_requested());
	const long hits = s4fmm_inject_hits();
	if(requested){ std::printf("S4FMM HITCOUNT %ld\n", hits); }
	S4_Simulation_Destroy(S);
	std::printf("S4FMM DRIVER_R6 DONE\n");
	return 0;
}
