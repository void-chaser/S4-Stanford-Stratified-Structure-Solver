/* Direct calls to the public C API ``S4_Simulation_GetFieldPlane``.
 *
 * Each case runs in its own process (the Python wrapper names one case per
 * subprocess) so that a crash is observed as a signal rather than killing the
 * test run.  The driver prints structured ``CHECK`` lines and exits non-zero as
 * soon as any check fails, so "the program did not crash" is never the only
 * evidence: the return code, the contents of the output buffers and the
 * sentinel words around them are all verified before the process exits.
 *
 * Buffer contract exercised here: each non-NULL output buffer must hold
 * ``3 * nxy[0] * nxy[1]`` complex values, that is ``6 * nxy[0] * nxy[1]``
 * values of type ``S4_real`` with the real part immediately followed by the
 * imaginary part.  Element ``3 * (i + j * nxy[0]) + c`` is component ``c`` of
 * grid point ``(i, j)``, so its real part sits at S4_real index
 * ``2 * (3 * (i + j * nxy[0]) + c)``; ``i`` is the fast axis and ``j`` the slow
 * one.
 */
#include <climits>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

#include "S4.h"

static const S4_real SENTINEL = -98765.4321;
static const size_t PAD = 8;
static int g_failures = 0;

static void check(bool ok, const char *what) {
	std::printf("CHECK %-34s %s\n", what, ok ? "ok" : "FAILED");
	if (!ok) g_failures++;
}

static void report_rc(const char *what, int rc) {
	std::printf("RC %s %d\n", what, rc);
}

/* A buffer with sentinel words before and after the region the API may fill. */
struct Buf {
	std::vector<S4_real> data;
	size_t payload;
	Buf(size_t n) : data(n + 2 * PAD, SENTINEL), payload(n) {}
	S4_real *ptr() { return data.data() + PAD; }
	const S4_real *ptr() const { return data.data() + PAD; }
	bool untouched() const {
		for (size_t i = 0; i < payload; ++i) {
			if (data[PAD + i] != SENTINEL) return false;
		}
		return true;
	}
	bool sentinels_ok() const {
		for (size_t i = 0; i < PAD; ++i) {
			if (data[i] != SENTINEL) return false;
			if (data[PAD + payload + i] != SENTINEL) return false;
		}
		return true;
	}
	bool all_finite() const {
		for (size_t i = 0; i < payload; ++i) {
			if (!std::isfinite(data[PAD + i])) return false;
		}
		return true;
	}
};

static S4_Simulation *make_stack(double freq, int nG = 9) {
	S4_real Lr[4] = {1, 0, 0, 1};
	S4_Simulation *S = S4_Simulation_New(Lr, (unsigned int)nG, NULL);
	if (NULL == S) return NULL;
	S4_real air[1] = {1.0};
	S4_real glass[1] = {4.0};
	S4_MaterialID mAir = S4_Simulation_SetMaterial(S, -1, "Air", S4_MATERIAL_TYPE_SCALAR_REAL, air);
	S4_MaterialID mGlass = S4_Simulation_SetMaterial(S, -1, "Glass", S4_MATERIAL_TYPE_SCALAR_REAL, glass);
	S4_real zero = 0.0, half = 0.5;
	S4_Simulation_SetLayer(S, -1, "Above", &zero, -1, mAir);
	S4_Simulation_SetLayer(S, -1, "Spacer", &zero, -1, mAir);
	S4_Simulation_SetLayer(S, -1, "Below", &half, -1, mGlass);
	/* Equivalent to the bindings' SetExcitationPlanewave((0,0), s=1, p=0):
	 * kn = (0,0,1), un = (0,1,0), vn = kn x un = (-1,0,0), so the internal state
	 * becomes k = (0,0), hx = -root_eps, hy = 0, i.e. exactly what
	 * Simulation_MakeExcitationPlanewave produces for that angle and amplitude
	 * (root_eps = 1 for the air incidence layer). */
	S4_real kdir[3] = {0, 0, 1};
	S4_real udir[3] = {0, 1, 0};
	S4_real cu[2] = {1, 0}, cv[2] = {0, 0};
	S4_Simulation_ExcitationPlanewave(S, kdir, udir, cu, cv);
	S4_real f[2] = {freq, 0.0};
	S4_Simulation_SetFrequency(S, f);
	return S;
}

/* Air / patterned slab / air, with a Glass circle of radius 0.25 (lattice
 * coordinates) centred on the origin in the 0.5-thick slab.  This is the same
 * structure the Python binding builds with
 * SetRegionCircle("Slab", "Glass", (0,0), 0.25); the public C API reaches it
 * through S4_Layer_SetRegionHalfwidths with S4_REGION_TYPE_CIRCLE, which sets
 * shape.vtab.circle.radius = halfwidths[0] exactly as the binding's
 * Simulation_AddLayerPatternCircle does. */
static S4_Simulation *make_patterned_stack(double freq, int nG = 9) {
	S4_real Lr[4] = {1, 0, 0, 1};
	S4_Simulation *S = S4_Simulation_New(Lr, (unsigned int)nG, NULL);
	if (NULL == S) return NULL;
	S4_real air[1] = {1.0};
	S4_real glass[1] = {4.0};
	S4_MaterialID mAir = S4_Simulation_SetMaterial(S, -1, "Air", S4_MATERIAL_TYPE_SCALAR_REAL, air);
	S4_MaterialID mGlass = S4_Simulation_SetMaterial(S, -1, "Glass", S4_MATERIAL_TYPE_SCALAR_REAL, glass);
	S4_real zero = 0.0, half = 0.5;
	S4_Simulation_SetLayer(S, -1, "Above", &zero, -1, mAir);
	S4_LayerID slab = S4_Simulation_SetLayer(S, -1, "Slab", &half, -1, mAir);
	S4_real radius[2] = {0.25, 0.25};
	S4_real center[2] = {0.0, 0.0};
	S4_real angle_frac = 0.0;
	if (0 != S4_Layer_SetRegionHalfwidths(S, slab, mGlass, S4_REGION_TYPE_CIRCLE,
	                                      radius, center, &angle_frac)) {
		S4_Simulation_Destroy(S);
		return NULL;
	}
	S4_Simulation_SetLayer(S, -1, "Below", &zero, -1, mAir);
	S4_real kdir[3] = {0, 0, 1};
	S4_real udir[3] = {0, 1, 0};
	S4_real cu[2] = {1, 0}, cv[2] = {0, 0};
	S4_Simulation_ExcitationPlanewave(S, kdir, udir, cu, cv);
	S4_real f[2] = {freq, 0.0};
	S4_Simulation_SetFrequency(S, f);
	return S;
}

/* Largest max-minus-min over the grid, per component, for one output buffer. */
static double component_spread(const Buf &b, int nu, int nv, int c) {
	double lo = 0.0, hi = 0.0;
	bool first = true;
	for (int j = 0; j < nv; ++j) {
		for (int i = 0; i < nu; ++i) {
			const size_t idx = 3 * ((size_t)i + (size_t)j * (size_t)nu) + (size_t)c;
			const double v = b.data[PAD + 2 * idx];
			if (first) { lo = hi = v; first = false; }
			if (v < lo) lo = v;
			if (v > hi) hi = v;
		}
	}
	return hi - lo;
}

static S4_Simulation *make_empty(void) {
	S4_real Lr[4] = {1, 0, 0, 1};
	return S4_Simulation_New(Lr, 9, NULL);
}

static size_t payload_for(int nu, int nv) {
	return (size_t)6 * (size_t)nu * (size_t)nv; /* 3 complex = 6 reals per point */
}

int main(int argc, char **argv) {
	if (argc < 2) {
		std::fprintf(stderr, "usage: %s <case>\n", argv[0]);
		return 2;
	}
	const std::string kase = argv[1];
	const S4_real xyz[3] = {0.0, 0.0, 0.05};
	int n11[2] = {1, 1};
	int n43[2] = {4, 3};
	Buf dummy(8);

	if (kase == "null_sim") {
		int nxy[2] = {2, 2};
		Buf e(payload_for(2, 2)), h(payload_for(2, 2));
		int rc = S4_Simulation_GetFieldPlane(NULL, nxy, xyz, e.ptr(), h.ptr());
		report_rc("null_sim", rc);
		check(rc == -1, "rc == -1 (S == NULL)");
		check(e.untouched() && h.untouched(), "outputs untouched");
		check(e.sentinels_ok() && h.sentinels_ok(), "sentinels intact");
	} else if (kase == "null_nxy") {
		Buf e(payload_for(2, 2)), h(payload_for(2, 2));
		S4_Simulation *S = make_stack(0.999);
		int rc = S4_Simulation_GetFieldPlane(S, NULL, xyz, e.ptr(), h.ptr());
		report_rc("null_nxy", rc);
		check(rc == -2, "rc == -2 (nxy == NULL)");
		check(e.untouched() && h.untouched(), "outputs untouched");
		S4_Simulation_Destroy(S);
	} else if (kase == "null_xyz0") {
		Buf e(payload_for(2, 2)), h(payload_for(2, 2));
		S4_Simulation *S = make_stack(0.999);
		int rc = S4_Simulation_GetFieldPlane(S, n11, NULL, e.ptr(), h.ptr());
		report_rc("null_xyz0", rc);
		check(rc == -3, "rc == -3 (xyz0 == NULL)");
		check(e.untouched() && h.untouched(), "outputs untouched");
		S4_Simulation_Destroy(S);
	} else if (kase == "both_null") {
		S4_Simulation *S = make_stack(0.999);
		int rc = S4_Simulation_GetFieldPlane(S, n43, xyz, NULL, NULL);
		report_rc("both_null", rc);
		check(rc == 0, "rc == 0 (no-op, both outputs NULL)");
		/* Same call with an invalid grid: the no-op wins, as before. */
		int bad[2] = {0, 8};
		int rc2 = S4_Simulation_GetFieldPlane(S, bad, xyz, NULL, NULL);
		report_rc("both_null_invalid_grid", rc2);
		check(rc2 == 0, "rc == 0 (no-op precedes grid validation)");
		S4_Simulation_Destroy(S);
	} else if (kase == "zero_x" || kase == "zero_y" || kase == "neg_x" || kase == "neg_y") {
		int nxy[2] = {8, 8};
		if (kase == "zero_x") nxy[0] = 0;
		if (kase == "zero_y") nxy[1] = 0;
		if (kase == "neg_x") nxy[0] = -1;
		if (kase == "neg_y") nxy[1] = -1;
		Buf e(payload_for(8, 8)), h(payload_for(8, 8));
		S4_Simulation *S = make_stack(0.999);
		int rc = S4_Simulation_GetFieldPlane(S, nxy, xyz, e.ptr(), h.ptr());
		report_rc(kase.c_str(), rc);
		check(rc == -4, "rc == -4 (grid must be positive)");
		check(e.untouched() && h.untouched(), "outputs untouched");
		check(e.sentinels_ok() && h.sentinels_ok(), "sentinels intact");
		S4_Simulation_Destroy(S);
	} else if (kase == "huge_intmax" || kase == "huge_2p32") {
		int nxy[2] = {INT_MAX, INT_MAX};
		if (kase == "huge_2p32") { nxy[0] = 65536; nxy[1] = 65536; }
		Buf e(64), h(64);
		S4_Simulation *S = make_stack(0.999);
		int rc = S4_Simulation_GetFieldPlane(S, nxy, xyz, e.ptr(), h.ptr());
		report_rc(kase.c_str(), rc);
		check(rc == -5, "rc == -5 (grid too large)");
		check(e.untouched() && h.untouched(), "outputs untouched");
		S4_Simulation_Destroy(S);
	} else if (kase == "no_layers") {
		Buf e(payload_for(2, 2)), h(payload_for(2, 2));
		S4_Simulation *S = make_empty();
		int nxy[2] = {2, 2};
		int rc = S4_Simulation_GetFieldPlane(S, nxy, xyz, e.ptr(), h.ptr());
		report_rc("no_layers", rc);
		check(rc == 14, "rc == 14 (no layers)");
		check(e.untouched() && h.untouched(), "outputs untouched");
		S4_Simulation_Destroy(S);
	} else if (kase == "output_combinations_1x1" || kase == "output_combinations_4x3") {
		int *nxy = (kase == "output_combinations_1x1") ? n11 : n43;
		size_t n = payload_for(nxy[0], nxy[1]);
		S4_Simulation *S = make_stack(0.999);
		Buf both_e(n), both_h(n), only_e(n), only_h(n);
		int rc_both = S4_Simulation_GetFieldPlane(S, nxy, xyz, both_e.ptr(), both_h.ptr());
		const bool both_e_written = !both_e.untouched();
		const bool both_h_written = !both_h.untouched();
		int rc_e = S4_Simulation_GetFieldPlane(S, nxy, xyz, only_e.ptr(), NULL);
		const bool e_only_written = !only_e.untouched();
		int rc_h = S4_Simulation_GetFieldPlane(S, nxy, xyz, NULL, only_h.ptr());
		const bool h_only_written = !only_h.untouched();
		report_rc("both", rc_both);
		report_rc("e_only", rc_e);
		report_rc("h_only", rc_h);
		check(rc_both == 0 && rc_e == 0 && rc_h == 0, "all three combinations return 0");
		check(both_e_written && both_h_written, "both outputs written");
		check(e_only_written, "E written when H is NULL");
		check(h_only_written, "H written when E is NULL");
		check(both_e.sentinels_ok() && both_h.sentinels_ok(), "sentinels intact (both)");
		check(only_e.sentinels_ok(), "sentinels intact (E-only)");
		check(only_h.sentinels_ok(), "sentinels intact (H-only)");
		check(both_e.all_finite() && both_h.all_finite(), "all components finite");
		check(only_e.all_finite() && only_h.all_finite(), "single-output values finite");
		bool same_e = true, same_h = true;
		for (size_t i = 0; i < n; ++i) {
			if (both_e.ptr()[i] != only_e.ptr()[i]) same_e = false;
			if (both_h.ptr()[i] != only_h.ptr()[i]) same_h = false;
		}
		check(same_e && same_h, "single-output results equal the pair results");
		S4_Simulation_Destroy(S);
	} else if (kase == "dump_4x3") {
		size_t n = payload_for(4, 3);
		S4_Simulation *S = make_stack(0.999);
		Buf e(n), h(n);
		int rc = S4_Simulation_GetFieldPlane(S, n43, xyz, e.ptr(), h.ptr());
		report_rc("dump_4x3", rc);
		check(rc == 0, "rc == 0");
		for (int j = 0; j < 3; ++j) {
			for (int i = 0; i < 4; ++i) {
				for (int c = 0; c < 3; ++c) {
					const size_t idx = 3 * ((size_t)i + (size_t)j * 4) + (size_t)c;
					std::printf("E %d %d %d %.17g %.17g\n", i, j, c,
						e.ptr()[2 * idx + 0], e.ptr()[2 * idx + 1]);
					std::printf("H %d %d %d %.17g %.17g\n", i, j, c,
						h.ptr()[2 * idx + 0], h.ptr()[2 * idx + 1]);
				}
			}
		}
		S4_Simulation_Destroy(S);
	} else if (kase == "dump_1x1") {
		size_t n = payload_for(1, 1);
		S4_Simulation *S = make_stack(0.999);
		Buf e(n), h(n);
		int rc = S4_Simulation_GetFieldPlane(S, n11, xyz, e.ptr(), h.ptr());
		report_rc("dump_1x1", rc);
		check(rc == 0, "rc == 0");
		check(!e.untouched() && !h.untouched(), "both outputs written");
		check(e.sentinels_ok() && h.sentinels_ok(), "sentinels intact");
		for (int c = 0; c < 3; ++c) {
			std::printf("E 0 0 %d %.17g %.17g\n", c, e.ptr()[2 * c + 0], e.ptr()[2 * c + 1]);
			std::printf("H 0 0 %d %.17g %.17g\n", c, h.ptr()[2 * c + 0], h.ptr()[2 * c + 1]);
		}
		S4_Simulation_Destroy(S);
	} else if (kase == "fft_boundary_over" || kase == "fft_boundary_over_axis") {
		/* Just above the int dimension product: 46341^2 = 2147488281 > INT_MAX,
		 * while 46340^2 = 2147395600 <= INT_MAX, so 46341 is the first size for
		 * which the division test must reject.  The other case overflows on one
		 * axis alone. */
		int nxy[2] = {46341, 46341};
		if (kase == "fft_boundary_over_axis") { nxy[0] = 2; nxy[1] = INT_MAX; }
		Buf e(payload_for(2, 2)), h(payload_for(2, 2));
		S4_Simulation *S = make_stack(0.999);
		int rc = S4_Simulation_GetFieldPlane(S, nxy, xyz, e.ptr(), h.ptr());
		report_rc(kase.c_str(), rc);
		check(rc == -5, "rc == -5 (FFT int capacity)");
		check(e.untouched() && h.untouched(), "outputs untouched");
		check(e.sentinels_ok() && h.sentinels_ok(), "sentinels intact");
		/* The same object must still work on a small grid. */
		int small[2] = {2, 2};
		Buf e2(payload_for(2, 2)), h2(payload_for(2, 2));
		int rc2 = S4_Simulation_GetFieldPlane(S, small, xyz, e2.ptr(), h2.ptr());
		report_rc((kase + "_then_small").c_str(), rc2);
		check(rc2 == 0, "small grid succeeds on the same object");
		check(!e2.untouched() && !h2.untouched(), "small grid wrote its outputs");
		S4_Simulation_Destroy(S);
	} else if (kase == "capacity_arithmetic") {
		/* Pure arithmetic, no API call and no allocation: it documents where the
		 * -5 boundary is drawn and shows the division form does not overflow. */
		const size_t size_max = (size_t)-1;
		size_t bpp = 6 * sizeof(S4_real);
		if (sizeof(std::complex<double>) > bpp) bpp = sizeof(std::complex<double>);
		std::printf("ARITH int_max %d bytes_per_point %llu byte_limit %llu\n",
			INT_MAX, (unsigned long long)bpp, (unsigned long long)(size_max / bpp));
		check(size_max / bpp >= (size_t)INT_MAX,
			"byte limit is looser than the int limit here");
		const struct { int nu, nv, over; } table[] = {
			{46340, 46340, 0}, {46341, 46341, 1}, {1, INT_MAX, 0},
			{2, INT_MAX, 1}, {INT_MAX, 1, 0}, {INT_MAX, 2, 1}, {65536, 65536, 1},
		};
		for (size_t t = 0; t < sizeof(table) / sizeof(table[0]); ++t) {
			const size_t nu = (size_t)table[t].nu, nv = (size_t)table[t].nv;
			const int over = (nu > (size_t)INT_MAX / nv) ? 1 : 0;
			std::printf("ARITH pair %d %d over_int %d expected %d\n",
				table[t].nu, table[t].nv, over, table[t].over);
			check(over == table[t].over, "division form classifies the pair");
		}
	} else if (kase == "patterned_outputs") {
		size_t n = payload_for(4, 3);
		S4_Simulation *S = make_patterned_stack(0.999);
		check(NULL != S, "patterned structure built");
		if (NULL != S) {
			Buf both_e(n), both_h(n), only_e(n), only_h(n);
			int rc_both = S4_Simulation_GetFieldPlane(S, n43, xyz, both_e.ptr(), both_h.ptr());
			const bool both_e_written = !both_e.untouched();
			const bool both_h_written = !both_h.untouched();
			int rc_e = S4_Simulation_GetFieldPlane(S, n43, xyz, only_e.ptr(), NULL);
			const bool e_only_written = !only_e.untouched();
			int rc_h = S4_Simulation_GetFieldPlane(S, n43, xyz, NULL, only_h.ptr());
			const bool h_only_written = !only_h.untouched();
			report_rc("patterned_both", rc_both);
			report_rc("patterned_e_only", rc_e);
			report_rc("patterned_h_only", rc_h);
			check(rc_both == 0 && rc_e == 0 && rc_h == 0, "all combinations return 0");
			check(both_e_written && both_h_written, "both outputs written");
			check(e_only_written && h_only_written, "each single output written");
			check(both_e.all_finite() && both_h.all_finite(), "all components finite");
			check(both_e.sentinels_ok() && both_h.sentinels_ok(), "sentinels intact (both)");
			check(only_e.sentinels_ok() && only_h.sentinels_ok(), "sentinels intact (single)");
			bool same_e = true, same_h = true;
			for (size_t i = 0; i < n; ++i) {
				if (both_e.ptr()[i] != only_e.ptr()[i]) same_e = false;
				if (both_h.ptr()[i] != only_h.ptr()[i]) same_h = false;
			}
			check(same_e && same_h, "single-output results equal the pair results");
			/* The pattern must actually produce spatial structure, otherwise a
			 * broken fixture would pass as a uniform field. */
			double best = 0.0;
			const char *which = "none";
			for (int c = 0; c < 3; ++c) {
				const double se = component_spread(both_e, 4, 3, c);
				const double sh = component_spread(both_h, 4, 3, c);
				std::printf("SPREAD %d %.6g %.6g\n", c, se, sh);
				if (se > best) { best = se; which = "E"; }
				if (sh > best) { best = sh; which = "H"; }
			}
			std::printf("SPREAD_MAX %.6g %s\n", best, which);
			check(best > 1e-6, "at least one component varies across the grid");
			S4_Simulation_Destroy(S);
		}
	} else if (kase == "patterned_dump_4x3") {
		size_t n = payload_for(4, 3);
		S4_Simulation *S = make_patterned_stack(0.999);
		check(NULL != S, "patterned structure built");
		if (NULL != S) {
			Buf e(n), h(n);
			int rc = S4_Simulation_GetFieldPlane(S, n43, xyz, e.ptr(), h.ptr());
			report_rc("patterned_dump_4x3", rc);
			check(rc == 0, "rc == 0");
			check(e.all_finite() && h.all_finite(), "all components finite");
			for (int j = 0; j < 3; ++j) {
				for (int i = 0; i < 4; ++i) {
					for (int c = 0; c < 3; ++c) {
						const size_t idx = 3 * ((size_t)i + (size_t)j * 4) + (size_t)c;
						std::printf("E %d %d %d %.17g %.17g\n", i, j, c,
							e.ptr()[2 * idx + 0], e.ptr()[2 * idx + 1]);
						std::printf("H %d %d %d %.17g %.17g\n", i, j, c,
							h.ptr()[2 * idx + 0], h.ptr()[2 * idx + 1]);
					}
				}
			}
			S4_Simulation_Destroy(S);
		}
	} else if (kase == "patterned_1x1") {
		size_t n = payload_for(1, 1);
		S4_Simulation *S = make_patterned_stack(0.999);
		check(NULL != S, "patterned structure built");
		if (NULL != S) {
			Buf both_e(n), both_h(n), only_e(n), only_h(n);
			int rc_both = S4_Simulation_GetFieldPlane(S, n11, xyz, both_e.ptr(), both_h.ptr());
			int rc_e = S4_Simulation_GetFieldPlane(S, n11, xyz, only_e.ptr(), NULL);
			int rc_h = S4_Simulation_GetFieldPlane(S, n11, xyz, NULL, only_h.ptr());
			report_rc("patterned_1x1_both", rc_both);
			report_rc("patterned_1x1_e_only", rc_e);
			report_rc("patterned_1x1_h_only", rc_h);
			check(rc_both == 0 && rc_e == 0 && rc_h == 0, "all combinations return 0");
			check(both_e.all_finite() && both_h.all_finite(), "all components finite");
			check(both_e.sentinels_ok() && both_h.sentinels_ok(), "sentinels intact");
			bool same_e = true, same_h = true;
			for (size_t i = 0; i < n; ++i) {
				if (both_e.ptr()[i] != only_e.ptr()[i]) same_e = false;
				if (both_h.ptr()[i] != only_h.ptr()[i]) same_h = false;
			}
			check(same_e && same_h, "single-output results equal the pair results");
			for (int c = 0; c < 3; ++c) {
				std::printf("E 0 0 %d %.17g %.17g\n", c,
					both_e.ptr()[2 * c + 0], both_e.ptr()[2 * c + 1]);
				std::printf("H 0 0 %d %.17g %.17g\n", c,
					both_h.ptr()[2 * c + 0], both_h.ptr()[2 * c + 1]);
			}
			S4_Simulation_Destroy(S);
		}
	} else if (kase == "cutoff_and_recovery") {
		size_t n = payload_for(4, 3);
		S4_Simulation *S = make_stack(std::sqrt(2.0));
		Buf e1(n), h1(n);
		int rc1 = S4_Simulation_GetFieldPlane(S, n43, xyz, e1.ptr(), h1.ptr());
		report_rc("cutoff", rc1);
		check(rc1 != 0, "cutoff call reports a failure");
		std::printf("NOTE cutoff_outputs_written %d\n", e1.untouched() ? 0 : 1);
		S4_real f[2] = {0.999, 0.0};
		S4_Simulation_SetFrequency(S, f);
		Buf e2(n), h2(n);
		int rc2 = S4_Simulation_GetFieldPlane(S, n43, xyz, e2.ptr(), h2.ptr());
		report_rc("after_frequency_change", rc2);
		check(rc2 == 0, "same simulation succeeds after a frequency change");
		check(e2.all_finite() && h2.all_finite(), "recovered output is finite");
		check(!e2.untouched() && !h2.untouched(), "recovered output was written");
		S4_Simulation_Destroy(S);
	} else if (kase == "repeat_failures_and_cleanup") {
		size_t n = payload_for(2, 2);
		S4_Simulation *S = make_stack(std::sqrt(2.0));
		int n22[2] = {2, 2};
		int rc = 0;
		for (int i = 0; i < 50; ++i) {
			Buf e(n), h(n);
			rc = S4_Simulation_GetFieldPlane(S, n22, xyz, e.ptr(), h.ptr());
			if (rc == 0) break;
		}
		report_rc("repeated_failures", rc);
		check(rc != 0, "every repeated failure reports an error");
		S4_real f[2] = {0.999, 0.0};
		S4_Simulation_SetFrequency(S, f);
		Buf e(n), h(n);
		int rc2 = S4_Simulation_GetFieldPlane(S, n22, xyz, e.ptr(), h.ptr());
		report_rc("after_repeats", rc2);
		check(rc2 == 0 && !e.untouched(), "usable after repeated failures");
		S4_Simulation_Destroy(S);
	} else {
		std::fprintf(stderr, "unknown case: %s\n", kase.c_str());
		return 2;
	}

	(void)dummy;
	std::printf("RESULT %s %s\n", kase.c_str(), g_failures == 0 ? "PASS" : "FAIL");
	return g_failures == 0 ? 0 : 1;
}
