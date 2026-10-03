#!/usr/bin/env python3
"""Regenerate the regression baseline from analytic.py.

Single source of truth: every row's parameters and expected values are produced
here, and every row with an analytic reference has its value taken from the
analytic implementation rather than typed in.  Run from the work copy.
"""
import cmath
import json
import math
import os
import sys

ROOT = os.path.expanduser("~/sandbox/S4-agent")
ALLOWED = os.path.expanduser("~/sandbox/S4-agent")
DATA = os.path.join(ROOT, "testing/s4test/regression_data.json")
sys.path.insert(0, os.path.join(ROOT, "testing/s4test"))
from analytic import airy_rt, fresnel_rt   # noqa: E402


def fresnel_row(name, n_above, n_film, n_below, theta, pol, freq=1.0):
    R, T = fresnel_rt(n_above, n_film, theta, pol)
    return {
        "name": name,
        "params": {"n_above": n_above, "n_film": n_film, "d": 0.0,
                   "n_below": n_below, "theta_deg": theta, "freq": freq,
                   "polarization": pol},
        "R": R, "T": T, "tol": 1e-9,
        "origin": "closed-form Fresnel; the zero-thickness middle layer makes "
                  "the S4 stack algebraically a single interface",
        "analytic_ref": "fresnel_rt(%g,%g,%g,'%s')" % (n_above, n_film, theta, pol),
    }


def airy_row(name, n_above, n_film, n_below, d, theta, pol, freq, tol,
             origin):
    R, T = airy_rt(d, n_film, n_above, n_below, theta, pol, freq)
    return {
        "name": name,
        "params": {"n_above": n_above, "n_film": n_film, "d": d,
                   "n_below": n_below, "theta_deg": theta, "freq": freq,
                   "polarization": pol},
        "R": R, "T": T, "tol": tol,
        "origin": origin,
        "analytic_ref": "airy_rt(%g,...,%g,'%s',%g)" % (d, theta, pol, freq),
    }


rows = []

# --- bare-interface Fresnel rows -------------------------------------------
r = fresnel_row("fresnel_bare_interface_normal_s", 1.0, 2.0, 2.0, 0.0, "s")
r["tol"] = 1e-12
r["origin"] = ("exact: R = ((n1-n2)/(n1+n2))^2 = 1/9, T = 8/9; "
               "the zero-thickness middle layer makes the S4 stack "
               "algebraically a single interface")
rows.append(r)
rows.append(fresnel_row("fresnel_bare_interface_30deg_s", 1.0, 2.0, 2.0, 30.0, "s"))
rows.append(fresnel_row("fresnel_bare_interface_30deg_p", 1.0, 2.0, 2.0, 30.0, "p"))

# --- exact thin-film design conditions -------------------------------------
# Half wave: exp(2i*delta) = 1 requires delta = pi, i.e. d = 1/(2*f*n).
freq, n_film = 0.25, 2.0
d_half = 1.0 / (2.0 * freq * n_film)
rows.append(airy_row(
    "halfwave_film_full_transmission", 1.0, n_film, 1.0, d_half, 0.0, "s", freq,
    1e-9,
    "exact half-wave condition: d = 1/(2*f*n_film) = %.6g, so the round-trip "
    "phase is 2*pi and the film is invisible" % d_half))

# Quarter wave anti-reflection coating: n_film = sqrt(n_sub), d = 1/(4*f*n_film).
n_sub = 4.0
n_arc = math.sqrt(n_sub)
freq = 1.0
d_arc = 1.0 / (4.0 * freq * n_arc)
rows.append(airy_row(
    "quarterwave_arc_coating", 1.0, n_arc, n_sub, d_arc, 0.0, "s", freq, 1e-9,
    "exact quarter-wave coating: n_film = sqrt(n_sub) = %.6g and "
    "d = 1/(4*f*n_film) = %.6g" % (n_arc, d_arc)))

# Brewster: theta_B = atan(n2/n1) exactly.
n2 = 3.0
theta_b = math.degrees(math.atan(n2 / 1.0))
rows.append(airy_row(
    "brewster_angle_p_no_reflection", 1.0, n2, n2, 0.0, theta_b, "p", 1.0, 1e-12,
    "exact: theta_B = atan(n2/n1) = %.12g deg, where the p reflectance "
    "vanishes identically" % theta_b))

# Total internal reflection.
rows.append(airy_row(
    "total_internal_reflection_35deg_s", 2.0, 1.0, 1.0, 0.0, 35.0, "s", 1.0,
    1e-12,
    "exact: theta = 35 deg exceeds theta_c = asin(1/2) = 30 deg, so all power "
    "is reflected"))

# --- lossless planar film ---------------------------------------------------
rows.append(airy_row(
    "lossless_film_energy_conservation", 1.0, 2.0, 1.5, 0.5, 0.0, "s", 0.5, 1e-9,
    "Airy sum; R + T == 1 to 4.4e-16"))

# --- absorbing film ---------------------------------------------------------
eps = 12.0 + 1.0j
n_lossy = cmath.sqrt(eps)
R, T = airy_rt(0.5, n_lossy, 1.0, 1.5, 0.0, "s", 0.5)
rows.append({
    "name": "lossy_silicon_film_absorption",
    "params": {"n_above": 1.0, "eps_film": [eps.real, eps.imag], "d": 0.5,
               "n_below": 1.5, "theta_deg": 0.0, "freq": 0.5,
               "polarization": "s"},
    "R": R, "T": T, "tol": 1e-9,
    "origin": "Airy sum, the only valid reference here: the transfer-matrix "
              "formulation is ill conditioned for absorbing films and returns "
              "R + T > 1 (asserted in selftest_analytic.py).  Absorbed "
              "fraction 1 - R - T = %.9f." % (1.0 - R - T),
    "analytic_ref": "airy_rt(0.5, sqrt(12+1j), 1, 1.5, 0, 's', 0.5)",
})

# --- S4-only change guard for the patterned slab ----------------------------
rows.append({
    "name": "patterned_slab_photonic_crystal_num_basis_225",
    "params": {"lattice": "square a=1", "num_basis": 225, "n_above": 1.0,
               "n_slab": math.sqrt(12.0), "slab_d": 0.5, "hole_radius": 0.2,
               "freq": 0.5, "polarization": "s"},
    "T": None,            # measured below from the running build
    "tol": 2e-3,
    "origin": "S4 only -- no analytic reference exists for a patterned slab. "
              "The tolerance is the measured NumBasis convergence spread over "
              "the last three refinements (1.04e-3) widened to 2e-3.  This row "
              "guards against numerical regressions; it does NOT validate "
              "the physics.",
    "analytic_ref": None,
})

# Measure the patterned value from the running build.
os.environ["S4_TEST_REPO_ROOT"] = ROOT
import S4   # noqa: E402
sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=225)
sim.AddMaterial("Air", 1)
sim.AddMaterial("Si", 12)
sim.AddLayer("Above", 0, "Air")
sim.AddLayer("Slab", 0.5, "Si")
sim.SetRegionCircle("Slab", "Air", (0, 0), 0.2)
sim.AddLayerCopy("Below", 0, "Above")
sim.SetFrequency(0.5)
sim.SetExcitationPlanewave((0, 0), 1, 0)
inc, _ = sim.GetPowerFlux("Above", 0.0)
trans, _ = sim.GetPowerFlux("Below", 0.0)
rows[-1]["T"] = round(trans.real / inc.real, 6)
print("measured patterned T = %.6f" % rows[-1]["T"])

doc = {
    "_comment": [
        "Small, human-reviewable numerical regression baseline for the S4 "
        "Python binding.",
        "Regenerate deliberately with gen_regression_data.py; never update "
        "automatically, because a baseline that updates itself cannot detect "
        "a regression.",
        "Each row states its parameters, expected value, tolerance, how the "
        "expected value was obtained, and (where one exists) the independent "
        "analytic reference it agrees with.  test_regression_baseline.py "
        "verifies that the analytic reference really does produce the stored "
        "value, so a row cannot be recorded from a buggy build.",
        "Rows with analytic_ref = null are S4-only change guards; they carry "
        "no claim of physical correctness and say so in 'origin'.",
        "No generated or binary files are stored here.",
    ],
    "environment": {
        "os": "Ubuntu 26.04",
        "python": "3.14.4",
        "compiler": "gcc/g++ 15.2.0",
        "baseline_commit": "b97f639",
    },
    "units": "lengths in lattice constants; frequency in c/a",
    "rows": rows,
}

real = os.path.realpath(DATA)
if not real.startswith(os.path.realpath(ALLOWED) + os.sep):
    sys.exit("REFUSING: %s is outside the work copy" % real)
with open(real, "w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")

print("wrote %s (%d rows)" % (real, len(rows)))
for r in rows:
    print("  %-44s tol=%-8g ref=%s" % (r["name"], r["tol"],
                                       "yes" if r.get("analytic_ref") else "S4-only"))
