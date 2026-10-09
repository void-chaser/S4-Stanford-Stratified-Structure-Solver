#!/usr/bin/env python3
"""Independent Fresnel reference for the D001 film at arbitrary incidence (s and p).

Standard library only; never imports S4 and never reads solver output.  The film is
a lossless slab of index n_f = 2 (eps = 4) and thickness d = 0.25 between identical
ambient media (n0 = 1).  Lattice period 1, so the vacuum wavenumber is k0 = 2*pi*f.

Geometric-series (Fresnel) form:
    kz0 = cos(theta0),  kzf = sqrt(n_f^2 - sin^2(theta0))
    eta_s = kz,  eta_p = kz / eps          (admittances for TE and TM)
    r01 = (eta0 - etaf) / (eta0 + etaf),   r12 = -r01  (identical ambient)
    delta = k0 * d * kzf
    r = (r01 + r12 e^{2i delta}) / (1 + r01 r12 e^{2i delta})
    R = |r|^2,  T = 1 - R                  (lossless, identical ambient)

Cross-check (fixed threshold 1e-14): at theta0 = 0 the oblique result must equal the
normal-incidence Airy transmittance of oracle_d001.airy_T, for both polarizations.
"""

import cmath
import math
import os
import sys

N_F = 2.0
N0 = 1.0
D = 0.25
TOL_NORMAL_LIMIT = 1e-14


def fresnel_RT(f, theta_deg, pol, n_f=N_F, d=D, n0=N0):
    if pol not in ("s", "p"):
        raise ValueError("pol must be 's' or 'p'")
    th = math.radians(theta_deg)
    sin0 = n0 * math.sin(th)
    kz0 = math.sqrt(n0 * n0 - sin0 * sin0)
    kzf = cmath.sqrt(n_f * n_f - sin0 * sin0)
    if pol == "s":
        eta0, etaf = kz0, kzf
    else:
        eta0, etaf = kz0 / (n0 * n0), kzf / (n_f * n_f)
    k0 = 2.0 * math.pi * f
    delta = k0 * d * kzf
    r01 = (eta0 - etaf) / (eta0 + etaf)
    r12 = -r01
    e2 = cmath.exp(2j * delta)
    r = (r01 + r12 * e2) / (1.0 + r01 * r12 * e2)
    R = abs(r) ** 2
    return {"R": R, "T": 1.0 - R, "kzf_real": kzf.real, "kzf_imag": kzf.imag, "delta": delta}


def self_check():
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import oracle_d001 as normal  # noqa: PLC0415  (stdlib only)
    worst = 0.0
    for f in (0.173, 0.427, 0.733):
        t_ref = normal.airy_T(f)
        for pol in ("s", "p"):
            worst = max(worst, abs(fresnel_RT(f, 0.0, pol)["T"] - t_ref))
    return {"normal_limit_worst_abs_diff": worst, "tolerance": TOL_NORMAL_LIMIT,
            "pass": worst <= TOL_NORMAL_LIMIT}


if __name__ == "__main__":
    import json  # noqa: PLC0415
    res = self_check()
    print(json.dumps(res, indent=1))
    sys.exit(0 if res["pass"] else 1)
