/* capi_fig12_relr4.c -- REL-R4 T4: the physical setting of examples/C_api/main.c rewritten against the
 * CURRENT public C API in S4/S4.h (P13 early check; this does not complete or fix P13).
 *
 * Structure (examples/2d/Fan_PRB_65_2002/fig12.lua, which examples/C_api/main.c also encodes):
 *   lattice {1,0;0,1}, NumG=100; air eps=1, Si eps=12; above (0, air), slab (0.5, Si) with an air circle
 *   of radius 0.2 centred at (0,0), below = a copy of above; normal incidence, s polarization only,
 *   amplitude 1.  For each frequency f it prints "f<TAB>transmitted power" where the transmitted power is
 *   the FORWARD power flux at offset 0 in the below layer (power[0] of S4_Simulation_GetPowerFlux).
 *
 * Choices confirmed against source, per task brief section 5.5.1:
 *   - circle half-widths: Lua SetLayerPatternCircle(name, material, center, radius) builds the circle with
 *     S4_REGION_TYPE_ELLIPSE and halfwidths {radius,radius} (S4/main_lua.c, S4L_Simulation_SetLayerPatternCircle),
 *     while Simulation_AddLayerPatternCircle stores shape.vtab.circle.radius = radius (S4/S4.cpp,
 *     Simulation_AddLayerPatternCircle).  The public C path S4_Layer_SetRegionHalfwidths with
 *     S4_REGION_TYPE_CIRCLE stores the same radius from halfwidths[0]; passing {0.2,0.2} gives the same
 *     shape under either reading.  The capi_field_plane_driver.cpp comment in testing/s4test documents this
 *     equivalence.
 *   - plane wave: Lua SetExcitationPlanewave({0,0},{1,0},{0,0}) means phi=theta=0 (normal incidence),
 *     s amplitude 1 phase 0, p amplitude 0.  The public C API takes kdir/udir/amp_u/amp_v; the equivalent
 *     normal-incidence s-only setting is kdir={0,0,1}, udir={0,1,0}, amp_u={1,0}, amp_v={0,0}, exactly as
 *     testing/s4test/capi_field_plane_driver.cpp::make_stack documents ("Equivalent to the bindings'
 *     SetExcitationPlanewave((0,0), s=1, p=0)").
 *   - frequency: S4_Simulation_SetFrequency takes the frequency f in cycles per unit length and stores
 *     omega = 2*pi*f (S4/S4.cpp: S4_Simulation_SetFrequency -> S->omega[0] = 2*M_PI*freq_complex[0]).
 *     The Lua SetFrequency calls the same function, so the C program passes f, not omega.
 *   - transmitted power: Lua GetPoyntingFlux('below',0) returns power[0..3] of
 *     S4_Simulation_GetPowerFlux; forward (transmitted) power is power[0] (same function, S4/S4.cpp).
 *
 * Two modes:
 *   fig12 [freq]        main mode: one frequency (default 1), prints "%g<TAB>%g" like the original main.c.
 *   fig12 --lua-sweep   positive-control mode: the fig12.lua frequency points 0.25..0.27 step 0.003,
 *                       printed with %.17g so that the comparison with the Lua run can use 1e-10 tolerance.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "S4.h"

static S4_Simulation *fig12_build(void)
{
	S4_real Lr[4] = {1.0, 0.0, 0.0, 1.0};          /* S:SetLattice({1,0},{0,1}) */
	S4_Simulation *S = S4_Simulation_New(Lr, 100u, NULL); /* S:SetNumG(100) */
	S4_MaterialID air, si;
	S4_real zero = 0.0, half = 0.5;
	S4_LayerID above, slab, below;
	S4_real hw[2] = {0.2, 0.2};                    /* circle radius 0.2 (see header) */
	S4_real center[2] = {0.0, 0.0};
	S4_real angle_frac = 0.0;
	S4_real kdir[3] = {0.0, 0.0, 1.0};
	S4_real udir[3] = {0.0, 1.0, 0.0};
	S4_real amp_u[2] = {1.0, 0.0};
	S4_real amp_v[2] = {0.0, 0.0};
	S4_real eps_air[2] = {1.0, 0.0};
	S4_real eps_si[2] = {12.0, 0.0};

	if (NULL == S) return NULL;
	air = S4_Simulation_SetMaterial(S, -1, "air", S4_MATERIAL_TYPE_SCALAR_REAL, eps_air);
	si = S4_Simulation_SetMaterial(S, -1, "Si", S4_MATERIAL_TYPE_SCALAR_REAL, eps_si);
	if (air < 0 || si < 0) goto fail;
	above = S4_Simulation_SetLayer(S, -1, "above", &zero, -1, air);
	slab = S4_Simulation_SetLayer(S, -1, "slab", &half, -1, si);
	if (above < 0 || slab < 0) goto fail;
	if (0 != S4_Layer_SetRegionHalfwidths(S, slab, air, S4_REGION_TYPE_CIRCLE, hw, center, &angle_frac)) goto fail;
	below = S4_Simulation_SetLayer(S, -1, "below", &zero, above, -1); /* AddLayerCopy('below',0,'above') */
	if (below < 0) goto fail;
	if (0 != S4_Simulation_ExcitationPlanewave(S, kdir, udir, amp_u, amp_v)) goto fail;
	return S;
fail:
	S4_Simulation_Destroy(S);
	return NULL;
}

/* transmitted (forward) power at offset 0 in the below layer for frequency f (cycles per unit length) */
static int fig12_forward(S4_Simulation *S, double f, double *forward)
{
	S4_real freq[2];
	S4_real offset = 0.0;
	S4_real power[4];
	S4_LayerID below;
	int ret;

	freq[0] = (S4_real)f;
	freq[1] = 0.0;
	if (0 != (ret = S4_Simulation_SetFrequency(S, freq))) return ret; /* S4.cpp multiplies by 2*pi */
	below = S4_Simulation_GetLayerByName(S, "below");
	if (below < 0) return -100;
	if (0 != (ret = S4_Simulation_GetPowerFlux(S, below, &offset, power))) return ret;
	*forward = power[0]; /* forward real, time averaged */
	return 0;
}

int main(int argc, char **argv)
{
	double f, forward;
	int ret;
	S4_Simulation *S;

	if (argc > 1 && 0 == strcmp(argv[1], "--lua-sweep")) {
		S = fig12_build();
		if (NULL == S) {
			fprintf(stderr, "fig12: cannot build the simulation\n");
			return 1;
		}
		/* same floating-point iteration as the Lua numeric for loop in fig12.lua */
		for (f = 0.25; f <= 0.27; f += 0.003) {
			if (0 != (ret = fig12_forward(S, f, &forward))) {
				fprintf(stderr, "fig12: frequency %g failed rc=%d\n", f, ret);
				S4_Simulation_Destroy(S);
				return 1;
			}
			printf("%.17g\t%.17g\n", f, forward);
		}
		S4_Simulation_Destroy(S);
		return 0;
	}

	f = 1.0;
	if (argc > 1) f = atof(argv[1]);
	S = fig12_build();
	if (NULL == S) {
		fprintf(stderr, "fig12: cannot build the simulation\n");
		return 1;
	}
	if (0 != (ret = fig12_forward(S, f, &forward))) {
		fprintf(stderr, "fig12: frequency %g failed rc=%d\n", f, ret);
		S4_Simulation_Destroy(S);
		return 1;
	}
	printf("%g\t%g\n", f, forward);
	S4_Simulation_Destroy(S);
	return 0;
}
