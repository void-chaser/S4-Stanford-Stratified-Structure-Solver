/* P05-S1R2 J3 probe: shape_get_normal index bounds.
 *
 * Builds a pattern layer with NSHAPES regions through the PUBLIC API only
 * (one S4_Layer_SetRegionHalfwidths call per region; each call appends one shape, see
 * S4.cpp S4_Layer_SetRegionHalfwidths: n = nshapes++).  Runs S4_Simulation_GetFieldPlane in
 * FMM_MODE=kottke.  It reads the internal shapes base address (read only, through
 * S4_internal.h) and prints it, so that the gdb breakpoint on shape_get_normal can convert the
 * pointer it receives into a shape index.  It does not modify any repository file.
 *
 * Environment:
 *   J3_NSHAPES = 1 or 2 (default 2)
 *   J3_LAYOUT  = concentric  (region k: circle radius 0.2 + 0.1*k, material k+1; nested, parent/child)
 *                 two_disjoint (region 0 at center (-0.2,0), region 1 at (+0.2,0), radius 0.12; no overlap)
 *                 overlap      (region 0 at (-0.08,0), region 1 at (+0.08,0), radius 0.15; siblings that intersect)
 *   FMM_MODE   = kottke (must be set by the caller)
 *   J3_NG      = number of plane waves (default 9)
 */
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "S4.h"
#include "S4_internal.h"
#include "pattern/pattern.h"

int main(int argc, char **argv){
	(void)argc; (void)argv;
	const char *mode = getenv("FMM_MODE");
	if(NULL == mode || 0 != strcmp(mode, "kottke")){
		std::fprintf(stderr, "J3 ARGERROR FMM_MODE must be kottke\n");
		return 2;
	}
	int nshapes = (NULL != getenv("J3_NSHAPES") ? atoi(getenv("J3_NSHAPES")) : 2);
	const char *layout = (NULL != getenv("J3_LAYOUT") ? getenv("J3_LAYOUT") : "concentric");
	int ng = (NULL != getenv("J3_NG") ? atoi(getenv("J3_NG")) : 9);
	if(nshapes < 1 || nshapes > 2){ std::fprintf(stderr, "J3 ARGERROR J3_NSHAPES must be 1 or 2\n"); return 2; }

	S4_real Lr[4] = {1, 0, 0, 1};
	S4_Simulation *S = S4_Simulation_New(Lr, (unsigned int)ng, NULL);
	if(NULL == S){ std::fprintf(stderr, "J3 FIXTURE S4_Simulation_New failed\n"); return 2; }
	S->options.use_discretized_epsilon = 1;
	S->options.use_subpixel_smoothing = 1;

	S4_real air[1] = {1.0};
	S4_real mat1[1] = {4.0};
	S4_real mat2[1] = {9.0};
	S4_MaterialID mAir = S4_Simulation_SetMaterial(S, -1, "Air", S4_MATERIAL_TYPE_SCALAR_REAL, air);
	S4_MaterialID m1 = S4_Simulation_SetMaterial(S, -1, "Glass1", S4_MATERIAL_TYPE_SCALAR_REAL, mat1);
	S4_MaterialID m2 = S4_Simulation_SetMaterial(S, -1, "Glass2", S4_MATERIAL_TYPE_SCALAR_REAL, mat2);

	S4_real zero = 0.0, half = 0.5;
	S4_Simulation_SetLayer(S, -1, "Above", &zero, -1, mAir);
	S4_LayerID slab = S4_Simulation_SetLayer(S, -1, "Slab", &half, -1, mAir);

	for(int k = 0; k < nshapes; ++k){
		S4_real radius[2] = {0.2, 0.2};
		S4_real center[2] = {0.0, 0.0};
		S4_real angle_frac = 0.0;
		S4_MaterialID mk = (0 == k ? m1 : m2);
		if(0 == strcmp(layout, "concentric")){
			radius[0] = 0.2 + 0.1*k;
			radius[1] = radius[0];
		}else if(0 == strcmp(layout, "overlap")){
			/* two sibling circles that intersect (neither contains the other) */
			radius[0] = 0.15;
			radius[1] = 0.15;
			center[0] = (0 == k ? -0.08 : 0.08);
			center[1] = 0.0;
		}else if(0 == strcmp(layout, "two_disjoint")){
			radius[0] = 0.12;
			radius[1] = 0.12;
			center[0] = (0 == k ? -0.2 : 0.2);
			center[1] = 0.0;
		}else{
			std::fprintf(stderr, "J3 ARGERROR J3_LAYOUT unknown\n");
			return 2;
		}
		if(0 != S4_Layer_SetRegionHalfwidths(S, slab, mk, S4_REGION_TYPE_CIRCLE, radius, center, &angle_frac)){
			std::fprintf(stderr, "J3 FIXTURE SetRegionHalfwidths k=%d failed\n", k);
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

	/* internal, read-only: the layer index of the patterned slab and its shapes array */
	const S4_Layer *Lp = &S->layer[slab];
	std::printf("J3 LAYER slab_index=%d nshapes=%d shapes_base=%p\n", (int)slab, Lp->pattern.nshapes, (const void*)Lp->pattern.shapes);
	for(int k = 0; k < Lp->pattern.nshapes; ++k){
		std::printf("J3 SHAPE k=%d addr=%p tag=%d\n", k, (const void*)&Lp->pattern.shapes[k], (int)Lp->pattern.shapes[k].tag);
	}

	int nxy[2] = {8, 8};
	const size_t n = 6 * (size_t)nxy[0] * (size_t)nxy[1];
	const S4_real xyz[3] = {0.0, 0.0, 0.05};
	std::vector<S4_real> E(n), H(n);
	int rc1 = S4_Simulation_GetFieldPlane(S, nxy, xyz, E.data(), H.data());
	std::printf("J3 RC first %d\n", rc1);
	S4_Simulation_Destroy(S);
	std::printf("J3 DONE\n");
	return 0;
}
