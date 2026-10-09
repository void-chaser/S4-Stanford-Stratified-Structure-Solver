#!/usr/bin/env python3
"""P01 independent Airy / characteristic-matrix reference for the D001 film.

Standard library only.  This module never imports S4 and never reads any
baseline/candidate output; every number below is computed from the physical
inputs (f, n = sqrt(4) = 2, d = 0.25, air in / air out, normal incidence).

Three independent derivations are computed and cross-checked:

  1. closed-form Airy transmittance
       delta = 2*pi*f*n*d
       T = 1 / (1 + ((n*n - 1)**2 / (4*n*n)) * sin(delta)**2),   R = 1 - T
  2. characteristic-matrix (transfer-matrix) transmittance
       B = cos(delta) + i*(ns/nf)*sin(delta)
       C = i*nf*sin(delta) + ns*cos(delta)
       T = 4*n0*ns / |n0*B + C|**2
  3. multiple-reflection (Fresnel) geometric series
       r01 = (n0-nf)/(n0+nf), r12 = (nf-ns)/(nf+ns)
       r = (r01 + r12*exp(2j*delta)) / (1 + r01*r12*exp(2j*delta))
       R = |r|**2, T = 1 - R

Thresholds (fixed before looking at any result, not tuned):
  * cross-derivation agreement: absolute 1e-14
  * closed-form identities (d = 0, n = 1) and analytic spot values: 1e-12

The value 0.65213267631441896 quoted in the historical prompt is recorded only
as an advisory cross-reference; it is never used as an input to the reference.
"""

import cmath
import json
import math
import os
import sys

N_F = math.sqrt(4.0)
D = 0.25
F = 0.427
N0 = 1.0
NS = 1.0

TOL_XDERIV = 1e-14
TOL_IDENTITY = 1e-12

HISTORICAL_PROMPT_HINT = {"T": 0.65213267631441896, "R": 0.34786732368558104}


def airy_T(f, n=N_F, d=D):
    delta = 2.0 * math.pi * f * n * d
    return 1.0 / (1.0 + ((n * n - 1.0) ** 2 / (4.0 * n * n)) * math.sin(delta) ** 2)


def airy_delta(f, n=N_F, d=D):
    return 2.0 * math.pi * f * n * d


def tmm_T(f, n_f=N_F, d=D, n0=N0, ns=NS):
    delta = airy_delta(f, n_f, d)
    B = math.cos(delta) + 1j * (ns / n_f) * math.sin(delta)
    C = 1j * n_f * math.sin(delta) + ns * math.cos(delta)
    denom = n0 * B + C
    return 4.0 * n0 * ns / (denom * denom.conjugate()).real


def fresnel_RT(f, n_f=N_F, d=D, n0=N0, ns=NS):
    delta = airy_delta(f, n_f, d)
    r01 = (n0 - n_f) / (n0 + n_f)
    r12 = (n_f - ns) / (n_f + ns)
    r = (r01 + r12 * cmath.exp(2j * delta)) / (1.0 + r01 * r12 * cmath.exp(2j * delta))
    R = abs(r) ** 2
    return R, 1.0 - R


def reference_RT(f=F):
    T = airy_T(f)
    return {"frequency": f, "T": T, "R": 1.0 - T, "delta": airy_delta(f)}


def _identity_checks():
    checks = []

    def add(label, got, exp, tol):
        checks.append({"check": label, "value": got, "expected": exp,
                       "abs_error": abs(got - exp), "tolerance": tol,
                       "pass": abs(got - exp) <= tol})

    add("transparent limit d=0 -> T=1", airy_T(F, d=0.0), 1.0, TOL_IDENTITY)
    add("transparent limit n=1 -> T=1", airy_T(F, n=1.0), 1.0, TOL_IDENTITY)
    add("quarter-wave-ish f=0.5,n=2,d=0.25 -> 0.64", airy_T(0.5), 0.64, TOL_IDENTITY)
    add("f=1.0,n=2,d=0.25 (delta=pi) -> 1.0", airy_T(1.0), 1.0, TOL_IDENTITY)
    add("f=0.25 (delta=pi/4) closed form", airy_T(0.25), 1.0 / (1.0 + (9.0 / 16.0) * 0.5),
        TOL_IDENTITY)
    # R + T = 1 is an exact algebraic consequence here, not a physical claim.
    add("R+T=1 at f=0.427", (1.0 - airy_T(F)) + airy_T(F), 1.0, TOL_IDENTITY)
    return checks


def _cross_checks():
    t1 = airy_T(F)
    t2 = tmm_T(F)
    r3, t3 = fresnel_RT(F)
    return {
        "airy_T": t1,
        "tmm_T": t2,
        "fresnel_R": r3,
        "fresnel_T": t3,
        "abs_diff_airy_vs_tmm": abs(t1 - t2),
        "abs_diff_airy_vs_fresnel": abs(t1 - t3),
        "abs_diff_R_airy_vs_fresnel": abs((1.0 - t1) - r3),
        "tolerance": TOL_XDERIV,
        "pass": (abs(t1 - t2) <= TOL_XDERIV
                 and abs(t1 - t3) <= TOL_XDERIV
                 and abs((1.0 - t1) - r3) <= TOL_XDERIV),
    }


def build_report():
    identities = _identity_checks()
    cross = _cross_checks()
    ref = reference_RT(F)
    report = {
        "module": "oracle_d001.py",
        "kind": "independent_airy_tmm_reference",
        "imports_S4": "S4" in sys.modules,
        "reads_subject_output": False,
        "scenario": {
            "ambient_epsilon": 1.0,
            "film_epsilon": 4.0,
            "n_f": N_F,
            "film_thickness": D,
            "frequency": F,
            "incidence": "normal",
            "polarization": "s",
        },
        "derivation_1_closed_form_airy": {
            "formula": "T = 1/(1 + ((n^2-1)^2/(4 n^2)) sin^2(delta)), delta = 2 pi f n d, R = 1 - T",
            "T": ref["T"], "R": ref["R"], "delta": ref["delta"],
        },
        "derivation_2_characteristic_matrix": {
            "formula": "T = 4 n0 ns / |n0 B + C|^2, B = cos d + i (ns/nf) sin d, C = i nf sin d + ns cos d",
            "T": tmm_T(F), "R": 1.0 - tmm_T(F),
        },
        "derivation_3_fresnel_geometric_series": {
            "formula": "r = (r01 + r12 e^{2i d})/(1 + r01 r12 e^{2i d}), R = |r|^2, T = 1 - R",
            "R": fresnel_RT(F)[0], "T": fresnel_RT(F)[1],
        },
        "cross_derivation": cross,
        "identity_checks": identities,
        "all_identity_checks_pass": all(c["pass"] for c in identities),
        "reference_for_d001_first_matrix": {"frequency": F, "R": ref["R"], "T": ref["T"]},
        "historical_prompt_hint_advisory_only": HISTORICAL_PROMPT_HINT,
        "abs_diff_vs_historical_hint_T": abs(ref["T"] - HISTORICAL_PROMPT_HINT["T"]),
    }
    report["reference_pass"] = bool(cross["pass"] and report["all_identity_checks_pass"])
    return report


def main():
    import argparse
    ap = argparse.ArgumentParser(description="P01 independent Airy/TMM reference self-check")
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    report = build_report()
    text = json.dumps(report, indent=2)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)
    return 0 if report["reference_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
