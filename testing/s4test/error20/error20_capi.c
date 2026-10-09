/* C API check for solution error code 20 (layer eigensystem failed).
 *
 * Built against a TEST-ONLY seam build (-DS4_TEST_EIGEN_INFO, see run_error20.py).
 * Behaviour is driven by the environment variable S4_TEST_EIGEN_INFO, read by the
 * library at each eigensolve.  This program prints one line per call:
 *   RESULT <name> rc=<int> [value=<double>]
 * and exits 0 whatever the results are; run_error20.py judges the lines.
 */
#include <stdio.h>
#include "S4.h"

static void report(const char *name, int rc, double value, int has_value)
{
	if (has_value) {
		printf("RESULT %s rc=%d value=%.17g\n", name, rc, value);
	} else {
		printf("RESULT %s rc=%d\n", name, rc);
	}
}

static S4_LayerID g_top, g_film, g_bottom;

static S4_Simulation *build(void)
{
	S4_real Lr[4] = {1, 0, 0, 1};
	S4_real eps_film[2] = {4, 0};
	S4_real eps_air[2] = {1, 0};
	S4_real thick_air = 0, thick_film = 0.25;
	S4_real freq[2] = {0.427, 0};
	S4_real kdir[3] = {0, 0, 1};
	S4_real udir[3] = {1, 0, 0};
	S4_real amp_u[2] = {1, 0};
	S4_real amp_v[2] = {0, 0};
	S4_real hw[2] = {0.2, 0.2};
	S4_real ctr[2] = {0, 0};
	S4_real ang[2] = {0, 0};
	S4_MaterialID mAir, mFilm;
	S4_LayerID lTop, lFilm, lBottom;
	S4_Simulation *S = S4_Simulation_New(Lr, 9, NULL);
	if (NULL == S) { return NULL; }
	mAir = S4_Simulation_SetMaterial(S, -1, "Air", S4_MATERIAL_TYPE_SCALAR_COMPLEX, eps_air);
	mFilm = S4_Simulation_SetMaterial(S, -1, "Film", S4_MATERIAL_TYPE_SCALAR_COMPLEX, eps_film);
	lTop = S4_Simulation_SetLayer(S, -1, "AirTop", &thick_air, -1, mAir);
	lFilm = S4_Simulation_SetLayer(S, -1, "Film", &thick_film, -1, mFilm);
	/* same-material circle: a non-uniform layer, so the eigensystem is really solved */
	S4_Layer_SetRegionHalfwidths(S, lFilm, mFilm, S4_REGION_TYPE_CIRCLE, hw, ctr, ang);
	lBottom = S4_Simulation_SetLayer(S, -1, "AirBottom", &thick_air, -1, mAir);
	g_top = lTop;
	g_film = lFilm;
	g_bottom = lBottom;
	S4_Simulation_SetFrequency(S, freq);
	S4_Simulation_ExcitationPlanewave(S, kdir, udir, amp_u, amp_v);
	return S;
}

int main(void)
{
	S4_Simulation *S;
	S4_real offset = 0;
	S4_real power[4];
	int rc;

	S = build();
	if (NULL == S) { printf("RESULT build rc=-1\n"); return 0; }

	/* 1. first call: real solve path (or injected failure, depending on env). */
	rc = S4_Simulation_GetPowerFlux(S, g_top, &offset, power);
	report("GetPowerFlux_first", rc, power[0], 1);

	/* 2. SolveLayer on the film layer: the same status must come back. */
	rc = S4_Simulation_SolveLayer(S, g_film);
	report("SolveLayer_film", rc, 0, 0);

	/* 3. GetPowerFlux on the bottom air layer after the object has been used. */
	rc = S4_Simulation_GetPowerFlux(S, g_bottom, &offset, power);
	report("GetPowerFlux_bottom", rc, power[0], 1);

	S4_Simulation_Destroy(S);

	/* 4. a fresh object, same process, same environment: independent outcome. */
	S = build();
	if (NULL == S) { printf("RESULT build2 rc=-1\n"); return 0; }
	rc = S4_Simulation_GetPowerFlux(S, g_bottom, &offset, power);
	report("GetPowerFlux_fresh", rc, power[0], 1);
	S4_Simulation_Destroy(S);
	return 0;
}
