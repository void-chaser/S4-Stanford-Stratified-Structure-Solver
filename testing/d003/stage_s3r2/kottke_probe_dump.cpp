/* P05-S3R2 R2-4c probe: kottke, scalar material, public API only, full field dump.
 *
 * A copy of testing/d003/stage_s1r2/kottke_probe.cpp with one addition: the complete
 * field (E and H, %.17g) of the first call is written to KPD_OUT when it is set.  The S1R2
 * probe is not modified.  The probe does not read or print any PASS/FAIL line.
 *
 * Environment:
 *   J2_MAT  = scalar_real
 *   J2_EPS  = real value of the patterned material eps
 *   FMM_MODE= kottke (required)
 *   KPD_OUT = output file for the first-call field (optional)
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
	if(NULL == mode || 0 != strcmp(mode, "kottke")){
		std::fprintf(stderr, "KPD ARGERROR FMM_MODE must be kottke\n");
		return 2;
	}
	const char *mat = getenv("J2_MAT");
	if(NULL == mat || 0 != strcmp(mat, "scalar_real")){
		std::fprintf(stderr, "KPD ARGERROR J2_MAT must be scalar_real\n");
		return 2;
	}
	S4_real Lr[4] = {1, 0, 0, 1};
	S4_Simulation *S = S4_Simulation_New(Lr, 9u, NULL);
	if(NULL == S){ std::fprintf(stderr, "KPD FIXTURE failed\n"); return 2; }
	S->options.use_discretized_epsilon = 1;
	S->options.use_subpixel_smoothing = 1;

	S4_real air[1] = {1.0};
	S4_MaterialID mAir = S4_Simulation_SetMaterial(S, -1, "Air", S4_MATERIAL_TYPE_SCALAR_REAL, air);
	S4_real e = (NULL != getenv("J2_EPS") ? (S4_real)atof(getenv("J2_EPS")) : 4.0);
	S4_MaterialID mPat = S4_Simulation_SetMaterial(S, -1, "Glass", S4_MATERIAL_TYPE_SCALAR_REAL, &e);
	std::printf("KPD MATERIAL scalar_real eps=%.17g id=%d\n", (double)e, (int)mPat);

	S4_real zero = 0.0, half = 0.5;
	S4_Simulation_SetLayer(S, -1, "Above", &zero, -1, mAir);
	S4_LayerID slab = S4_Simulation_SetLayer(S, -1, "Slab", &half, -1, mAir);
	S4_real radius[2] = {0.25, 0.25}, center[2] = {0.0, 0.0}, angle_frac = 0.0;
	if(0 != S4_Layer_SetRegionHalfwidths(S, slab, mPat, S4_REGION_TYPE_CIRCLE, radius, center, &angle_frac)){
		std::fprintf(stderr, "KPD FIXTURE SetRegionHalfwidths failed\n");
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
	std::printf("KPD RC first %d\n", rc1);
	if(const char *dp = getenv("KPD_OUT")){
		FILE *df = std::fopen(dp, "w");
		if(NULL != df){
			for(size_t q = 0; q < n; ++q){ std::fprintf(df, "E %zu %.17g\n", q, (double)E[q]); }
			for(size_t q = 0; q < n; ++q){ std::fprintf(df, "H %zu %.17g\n", q, (double)H[q]); }
			std::fclose(df);
		}
	}
	std::vector<S4_real> E2(n, -98765.4321), H2(n, -98765.4321);
	int rc2 = S4_Simulation_GetFieldPlane(S, nxy, xyz, E2.data(), H2.data());
	std::printf("KPD RC retry %d\n", rc2);
	S4_Simulation_Destroy(S);
	std::printf("KPD DONE\n");
	return 0;
}
