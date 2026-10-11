/* P05-S1R2 J2 probe: kottke divisor safety through the public C API only.
 *
 * Builds a pattern stack (background Air, patterned Glass circle) whose patterned material is
 * chosen by the environment, runs S4_Simulation_GetFieldPlane in FMM_MODE=kottke, and reports:
 *   - the return code of the call
 *   - the number of non-finite values in the output E and H
 *   - the return code of a second call on the same object
 * It does not change any file in the repository and does not read the driver's PASS/FAIL line.
 *
 * Environment:
 *   J2_MAT   = scalar_real | tensor_real     (type of the patterned material)
 *   J2_EPS   = real value for scalar_real    (e.g. 0)
 *   J2_TENS  = five values for tensor_real, comma separated: e11,e12,e21,e22,ezz
 *   J2_NG    = number of plane waves (default 9)
 *   FMM_MODE = kottke (the probe does not set it; the caller must)
 */
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "S4.h"

static long count_nonfinite(const S4_real *p, size_t n){
	long c = 0;
	for(size_t i = 0; i < n; ++i){ if(!std::isfinite(p[i])){ ++c; } }
	return c;
}

int main(int argc, char **argv){
	(void)argc; (void)argv;
	const char *mode = getenv("FMM_MODE");
	if(NULL == mode || 0 != strcmp(mode, "kottke")){
		std::fprintf(stderr, "J2 ARGERROR FMM_MODE must be kottke\n");
		return 2;
	}
	const char *mat = getenv("J2_MAT");
	if(NULL == mat){ std::fprintf(stderr, "J2 ARGERROR J2_MAT unset\n"); return 2; }
	int ng = (NULL != getenv("J2_NG") ? atoi(getenv("J2_NG")) : 9);

	S4_real Lr[4] = {1, 0, 0, 1};
	S4_Simulation *S = S4_Simulation_New(Lr, (unsigned int)ng, NULL);
	if(NULL == S){ std::fprintf(stderr, "J2 FIXTURE S4_Simulation_New failed\n"); return 2; }
	/* the same option set as the harness for kottke (driver make_stack, mode kottke) */
	S->options.use_discretized_epsilon = 1;
	S->options.use_subpixel_smoothing = 1;

	S4_real air[1] = {1.0};
	S4_MaterialID mAir = S4_Simulation_SetMaterial(S, -1, "Air", S4_MATERIAL_TYPE_SCALAR_REAL, air);
	S4_MaterialID mPat;
	if(0 == strcmp(mat, "scalar_real")){
		S4_real e = (NULL != getenv("J2_EPS") ? (S4_real)atof(getenv("J2_EPS")) : 4.0);
		mPat = S4_Simulation_SetMaterial(S, -1, "Glass", S4_MATERIAL_TYPE_SCALAR_REAL, &e);
		std::printf("J2 MATERIAL scalar_real eps=%.17g id=%d\n", (double)e, (int)mPat);
	}else if(0 == strcmp(mat, "tensor_real")){
		S4_real t[5] = {4.0, 0.0, 0.0, 4.0, 4.0};
		const char *s = getenv("J2_TENS");
		if(NULL != s){
			char *end = NULL;
			for(int i = 0; i < 5; ++i){
				t[i] = (S4_real)strtod(s, &end);
				if(NULL == end || *end == '\0'){ if(i < 4){ std::fprintf(stderr, "J2 ARGERROR J2_TENS needs 5 values\n"); return 2; } }
				s = (NULL != end && *end == ',') ? end + 1 : end;
			}
		}
		mPat = S4_Simulation_SetMaterial(S, -1, "Glass", S4_MATERIAL_TYPE_XYTENSOR_REAL, t);
		std::printf("J2 MATERIAL tensor_real e11=%.17g e12=%.17g e21=%.17g e22=%.17g ezz=%.17g id=%d\n",
		            (double)t[0], (double)t[1], (double)t[2], (double)t[3], (double)t[4], (int)mPat);
	}else{
		std::fprintf(stderr, "J2 ARGERROR J2_MAT must be scalar_real or tensor_real\n");
		return 2;
	}

	S4_real zero = 0.0, half = 0.5;
	S4_Simulation_SetLayer(S, -1, "Above", &zero, -1, mAir);
	S4_LayerID slab = S4_Simulation_SetLayer(S, -1, "Slab", &half, -1, mAir);
	S4_real radius[2] = {0.25, 0.25}, center[2] = {0.0, 0.0}, angle_frac = 0.0;
	if(0 != S4_Layer_SetRegionHalfwidths(S, slab, mPat, S4_REGION_TYPE_CIRCLE, radius, center, &angle_frac)){
		std::fprintf(stderr, "J2 FIXTURE SetRegionHalfwidths failed\n");
		S4_Simulation_Destroy(S);
		return 2;
	}
	S4_Simulation_SetLayer(S, -1, "Below", &zero, -1, mAir);

	S4_real kdir[3] = {0, 0, 1}, udir[3] = {0, 1, 0};
	S4_real cu[2] = {1, 0}, cv[2] = {0, 0};
	S4_Simulation_ExcitationPlanewave(S, kdir, udir, cu, cv);
	S4_real f[2] = {0.999, 0.0};
	S4_Simulation_SetFrequency(S, f);

	int nxy[2] = {4, 3};
	const size_t n = 6 * (size_t)nxy[0] * (size_t)nxy[1];
	const S4_real xyz[3] = {0.0, 0.0, 0.05};
	std::vector<S4_real> E(n, -98765.4321), H(n, -98765.4321);

	int rc1 = S4_Simulation_GetFieldPlane(S, nxy, xyz, E.data(), H.data());
	std::printf("J2 RC first %d\n", rc1);
	std::printf("J2 NONFINITE first E=%ld H=%ld of %zu\n", count_nonfinite(E.data(), n), count_nonfinite(H.data(), n), n);
	std::printf("J2 FIRST_E0 %.17g %.17g\n", (double)E[0], (double)E[1]);

	std::vector<S4_real> E2(n, -98765.4321), H2(n, -98765.4321);
	int rc2 = S4_Simulation_GetFieldPlane(S, nxy, xyz, E2.data(), H2.data());
	std::printf("J2 RC retry %d\n", rc2);
	std::printf("J2 NONFINITE retry E=%ld H=%ld of %zu\n", count_nonfinite(E2.data(), n), count_nonfinite(H2.data(), n), n);

	S4_Simulation_Destroy(S);
	std::printf("J2 DONE\n");
	return 0;
}
