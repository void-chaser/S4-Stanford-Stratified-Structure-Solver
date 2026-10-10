/* Direct public C API grid calls under allocation fault injection.
 *
 * One injection point per process (the injector is armed through the
 * environment and fires once), so the same process also demonstrates that the
 * object recovers: the first call must fail cleanly, the second must succeed.
 */
#include <climits>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "S4.h"
#include "S4_internal.h"

static const S4_real SENTINEL = -98765.4321;
static const size_t PAD = 8;
static int failures = 0;

static void check(bool ok, const char *what){
	std::printf("CHECK %-40s %s\n", what, ok ? "ok" : "FAILED");
	if(!ok){ failures++; }
}

struct Buf {
	std::vector<S4_real> data;
	size_t payload;
	Buf(size_t n) : data(n + 2*PAD, SENTINEL), payload(n) {}
	S4_real *ptr(){ return data.data() + PAD; }
	bool untouched() const {
		for(size_t i = 0; i < payload; ++i){ if(data[PAD+i] != SENTINEL){ return false; } }
		return true;
	}
	bool sentinels_ok() const {
		for(size_t i = 0; i < PAD; ++i){
			if(data[i] != SENTINEL){ return false; }
			if(data[PAD+payload+i] != SENTINEL){ return false; }
		}
		return true;
	}
	bool all_finite() const {
		for(size_t i = 0; i < payload; ++i){ if(!std::isfinite(data[PAD+i])){ return false; } }
		return true;
	}
};

static int g_ng = 1;
static S4_Simulation *make_stack(const char *which, double freq){
	S4_real Lr[4] = {1, 0, 0, 1};
	S4_Simulation *S = S4_Simulation_New(Lr, (unsigned int)g_ng, NULL);
	if(NULL == S){ return NULL; }
 const char *mode=getenv("FMM_MODE");
 if(mode && !strcmp(mode,"fft")) S->options.use_discretized_epsilon=1;
 if(mode && !strcmp(mode,"kottke")){S->options.use_discretized_epsilon=1;S->options.use_subpixel_smoothing=1;}
 if(mode && (!strcmp(mode,"jones")||!strcmp(mode,"nv")||!strcmp(mode,"vl"))){S->options.use_polarization_basis=1;S->options.use_jones_vector_basis=!strcmp(mode,"jones");S->options.use_normal_vector_basis=!strcmp(mode,"nv");}

	S4_real air[1] = {1.0}, glass[1] = {4.0};
	S4_MaterialID mAir = S4_Simulation_SetMaterial(S, -1, "Air", S4_MATERIAL_TYPE_SCALAR_REAL, air);
	S4_MaterialID mGlass = S4_Simulation_SetMaterial(S, -1, "Glass", S4_MATERIAL_TYPE_SCALAR_REAL, glass);
	S4_real zero = 0.0, half = 0.5;
	if(0 == strcmp(which, "pattern")){
		S4_Simulation_SetLayer(S, -1, "Above", &zero, -1, mAir);
		S4_LayerID slab = S4_Simulation_SetLayer(S, -1, "Slab", &half, -1, mAir);
		S4_real radius[2] = {0.25, 0.25}, center[2] = {0.0, 0.0}, angle_frac = 0.0;
		if(0 != S4_Layer_SetRegionHalfwidths(S, slab, mGlass, S4_REGION_TYPE_CIRCLE,
		                                     radius, center, &angle_frac)){
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
	if(NULL == mode || (strcmp(mode,"fft") && strcmp(mode,"kottke") && strcmp(mode,"jones") && strcmp(mode,"nv") && strcmp(mode,"vl"))){
		std::fprintf(stderr, "S4FMM ARGERROR invalid or missing FMM_MODE=%s\n", mode ? mode : "(unset)"); return 2; }
	g_ng = argi("S4FMM_NG", 1, 64);
	std::printf("S4FMM DRIVER actual mode=%s num_basis=%d stage=%s plan_call=%s alloc=%s exec=%s\n",
		mode, g_ng,
		getenv("S4FMM_STAGE") ? getenv("S4FMM_STAGE") : "none",
		getenv("S4FMM_PLAN_CALL") ? getenv("S4FMM_PLAN_CALL") : "0",
		getenv("S4FMM_ALLOC") ? getenv("S4FMM_ALLOC") : "0",
		getenv("S4FMM_EXEC") ? getenv("S4FMM_EXEC") : "0");
	S4_Simulation *S = make_stack(stack, 0.999);
	if(NULL == S){ std::fprintf(stderr, "fixture failed\n"); return 2; }

	Buf both_e(n), both_h(n);
	S4_real *Ep = (0 == strcmp(outs, "h") ? NULL : both_e.ptr());
	S4_real *Hp = (0 == strcmp(outs, "e") ? NULL : both_h.ptr());

	/* First call: the injector may make one allocation fail inside it. */
	int rc1 = S4_Simulation_GetFieldPlane(S, nxy, xyz, Ep, Hp);
	std::printf("RC first %d\n", rc1);

	/* Second call: the injection has already fired, so this must succeed. */
	Buf retry_e(n), retry_h(n);
	S4_real *Ep2 = (0 == strcmp(outs, "h") ? NULL : retry_e.ptr());
	S4_real *Hp2 = (0 == strcmp(outs, "e") ? NULL : retry_h.ptr());
	int rc2 = S4_Simulation_GetFieldPlane(S, nxy, xyz, Ep2, Hp2);
	std::printf("RC retry %d\n", rc2);

	const bool E_checked = (NULL != Ep);
	const bool H_checked = (NULL != Hp);

	if(0 != rc1){
		check(1 == rc1, "failed call returns the allocation code 1");
		if(E_checked){ check(both_e.untouched(), "failed call left E untouched"); }
		if(H_checked){ check(both_h.untouched(), "failed call left H untouched"); }
		if(E_checked){ check(both_e.sentinels_ok(), "sentinels around E intact"); }
		if(H_checked){ check(both_h.sentinels_ok(), "sentinels around H intact"); }
		check(0 == rc2, "retry on the same object succeeds");
		check((!E_checked || !retry_e.untouched()) && (!H_checked || !retry_h.untouched()),
		      "retry wrote its outputs");
		check((!E_checked || retry_e.all_finite()) && (!H_checked || retry_h.all_finite()),
		      "retry output is finite");
		/* the failed layer must keep no partial modes and no field-cache entry */
		int partial_modes = 0, partial_cache = 0;
		for(int i = 0; i < S->n_layers; ++i){
			if(S->layer[i].pattern.nshapes != 0 && NULL != S->layer[i].modes){ partial_modes++; }
		}
		for(FieldCache *f = S->field_cache; NULL != f; f = f->next){
			if(NULL != f->layer && f->layer->pattern.nshapes != 0 && f->n == (size_t)S->n_G){ partial_cache++; }
		}
		check(0 == partial_modes, "failed layer kept no partial modes");
		std::printf("S4FMM WITNESS resource partial_modes=%d constructed_cache_entries=%d\n", partial_modes, partial_cache);
		std::printf("RESULT injected failure observed\n");
	}else{
		check(0 == rc2, "second call also succeeds");
		check((!E_checked || !both_e.untouched()) && (!H_checked || !both_h.untouched()),
		      "successful call wrote its outputs");
		check((!E_checked || both_e.all_finite()) && (!H_checked || both_h.all_finite()),
		      "successful output is finite");
		std::printf("RESULT no injection fired\n");
	}
	S4_Simulation_Destroy(S);
	std::printf("S4FMM DRIVER DONE\n");
	std::printf("RESULT %s %s %s\n", stack, outs, failures == 0 ? "PASS" : "FAIL");
	return failures == 0 ? 0 : 1;
}
