/* P05-S3R2 R2-1 probe: D-138 geometric consequence, FFT path (fmm_FFT.cpp line 138).
 *
 * Builds a two-shape pattern layer through the PUBLIC API only (one
 * S4_Layer_SetRegionHalfwidths call per region; each call appends one shape).  Runs
 * S4_Simulation_GetFieldPlane.  The caller selects the mode through FMM_MODE (fft).
 * It writes the field to a file given by D138_OUT (E and H, %.17g), and prints rc.
 * It does not read or print any PASS/FAIL line; the judgement uses the field data and rc.
 *
 * Environment:
 *   FMM_MODE  = fft                     (required)
 *   D138_LAYOUT = overlap | concentric  (default overlap)
 *   D138_NG   = plane waves (default 9)
 *   D138_OUT  = output file for the field (required)
 */
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "S4.h"

int main(int argc, char **argv){
	(void)argc; (void)argv;
	const char *mode = getenv("FMM_MODE");
	if(NULL == mode || 0 != strcmp(mode, "fft")){
		std::fprintf(stderr, "D138 ARGERROR FMM_MODE must be fft\n");
		return 2;
	}
	const char *out = getenv("D138_OUT");
	if(NULL == out){ std::fprintf(stderr, "D138 ARGERROR D138_OUT unset\n"); return 2; }
	const char *layout = (NULL != getenv("D138_LAYOUT") ? getenv("D138_LAYOUT") : "overlap");
	int ng = (NULL != getenv("D138_NG") ? atoi(getenv("D138_NG")) : 9);

	S4_real Lr[4] = {1, 0, 0, 1};
	S4_Simulation *S = S4_Simulation_New(Lr, (unsigned int)ng, NULL);
	if(NULL == S){ std::fprintf(stderr, "D138 FIXTURE S4_Simulation_New failed\n"); return 2; }
	/* the same option set as the driver for mode fft (driver make_stack, mode fft) */
	S->options.use_discretized_epsilon = 1;

	S4_real air[1] = {1.0};
	S4_real mat1[1] = {4.0};
	S4_real mat2[1] = {9.0};
	S4_MaterialID mAir = S4_Simulation_SetMaterial(S, -1, "Air", S4_MATERIAL_TYPE_SCALAR_REAL, air);
	S4_MaterialID m1 = S4_Simulation_SetMaterial(S, -1, "Glass1", S4_MATERIAL_TYPE_SCALAR_REAL, mat1);
	S4_MaterialID m2 = S4_Simulation_SetMaterial(S, -1, "Glass2", S4_MATERIAL_TYPE_SCALAR_REAL, mat2);

	S4_real zero = 0.0, half = 0.5;
	S4_Simulation_SetLayer(S, -1, "Above", &zero, -1, mAir);
	S4_LayerID slab = S4_Simulation_SetLayer(S, -1, "Slab", &half, -1, mAir);

	for(int k = 0; k < 2; ++k){
		S4_real radius[2] = {0.15, 0.15};
		S4_real center[2] = {0.0, 0.0};
		S4_real angle_frac = 0.0;
		S4_MaterialID mk = (0 == k ? m1 : m2);
		if(0 == strcmp(layout, "overlap")){
			center[0] = (0 == k ? -0.08 : 0.08);
		}else if(0 == strcmp(layout, "bigoverlap")){
			/* AMENDMENT_2: large mutually overlapping circles, so that the background is absent
			 * over part of the cell and imat[0] can be >= 1 */
			radius[0] = 0.8;
			radius[1] = 0.8;
			center[0] = (0 == k ? -0.3 : 0.3);
		}else if(0 == strcmp(layout, "concentric")){
			radius[0] = 0.2 + 0.1*k;
			radius[1] = radius[0];
		}else{
			std::fprintf(stderr, "D138 ARGERROR D138_LAYOUT unknown\n");
			return 2;
		}
		if(0 != S4_Layer_SetRegionHalfwidths(S, slab, mk, S4_REGION_TYPE_CIRCLE, radius, center, &angle_frac)){
			std::fprintf(stderr, "D138 FIXTURE SetRegionHalfwidths k=%d failed\n", k);
			S4_Simulation_Destroy(S);
			return 2;
		}
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
	int rc = S4_Simulation_GetFieldPlane(S, nxy, xyz, E.data(), H.data());
	std::printf("D138 RC %d\n", rc);

	FILE *df = std::fopen(out, "w");
	if(NULL == df){
		std::fprintf(stderr, "D138 cannot open output\n");
		S4_Simulation_Destroy(S);
		return 2;
	}
	for(size_t q = 0; q < n; ++q){ std::fprintf(df, "E %zu %.17g\n", q, (double)E[q]); }
	for(size_t q = 0; q < n; ++q){ std::fprintf(df, "H %zu %.17g\n", q, (double)H[q]); }
	std::fclose(df);
	S4_Simulation_Destroy(S);
	return 0;
}
