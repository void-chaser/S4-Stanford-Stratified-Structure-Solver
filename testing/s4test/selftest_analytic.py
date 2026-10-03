#!/usr/bin/env python3
"""Self-validation of s4test.analytic -- run before trusting any benchmark.

Checks, in order of increasing subtlety:
  1. tmm_rt with a zero-thickness layer reproduces closed-form Fresnel;
  2. R + T == 1 for lossless stacks;
  3. airy_rt agrees with tmm_rt for LOSSLESS films (both are valid there);
  4. airy_rt stays physical (R + T <= 1) for LOSSY films, where the
     characteristic-matrix formulation is numerically ill conditioned --
     and that tmm_rt really does break down there, so the reason for having
     two implementations is documented by a test rather than a comment;
  5. closed-form design results: Brewster, total internal reflection, and a
     quarter-wave anti-reflection coating.
"""
import os
import sys
import cmath
import math

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analytic import (airy_rt, fresnel_coefficients, fresnel_rt, tmm_rt,
                      tmm_rt_spectrum)

failures = []


def check(tag, condition, detail=""):
    print("  [%s] %s %s" % ("ok  " if condition else "FAIL", tag, detail))
    if not condition:
        failures.append(tag)


print("1. TMM zero-thickness layer == closed-form Fresnel")
worst = 0.0
for n2 in (1.5, 2.0, 3.5, 12.0):
    for theta in (0, 15, 30, 45, 60, 75, 85):
        for pol in ("s", "p"):
            Rt, Tt = tmm_rt([(0.0, n2)], 1.0, n2, theta, pol)
            Rf, Tf = fresnel_rt(1.0, n2, theta, pol)
            worst = max(worst, abs(Rt - Rf), abs(Tt - Tf))
check("max |TMM - Fresnel| < 1e-12", worst < 1e-12, "worst=%.3e" % worst)

print("2. Lossless stacks conserve energy")
worst_sum = 0.0
for d in (0.1, 0.37, 1.0, 2.5):
    for theta in (0, 30, 60):
        for pol in ("s", "p"):
            R, T = tmm_rt([(d, 3.0)], 1.0, 1.5, theta, pol)
            worst_sum = max(worst_sum, abs(R + T - 1.0))
for theta in (0, 30, 60):
    for pol in ("s", "p"):
        R, T = tmm_rt([(0.2, 2.0), (0.3, 3.5), (0.15, 1.2)], 1.0, 1.5, theta, pol)
        worst_sum = max(worst_sum, abs(R + T - 1.0))
check("max |R + T - 1| < 1e-12", worst_sum < 1e-12, "worst=%.3e" % worst_sum)

print("3. airy_rt == tmm_rt for lossless films")
worst_airy = 0.0
for n_film in (1.5, 2.0, 3.5):
    for d in (0.1, 0.5, 1.3):
        for theta in (0, 30, 60):
            for pol in ("s", "p"):
                Ra, Ta = airy_rt(d, n_film, 1.0, 1.5, theta, pol, 0.5)
                Rt, Tt = tmm_rt([(d, n_film)], 1.0, 1.5, theta, pol, 0.5)
                worst_airy = max(worst_airy, abs(Ra - Rt), abs(Ta - Tt))
check("max |airy - tmm| (lossless) < 1e-12", worst_airy < 1e-12,
      "worst=%.3e" % worst_airy)

print("4. Lossy films: airy_rt physical, tmm_rt is not")
worst_airy_lossy = 0.0
worst_tmm_lossy = 0.0
for eps_imag in (0.1, 0.5, 1.0, 3.0):
    n = cmath.sqrt(12.0 + eps_imag * 1j)
    Ra, Ta = airy_rt(0.5, n, 1.0, 1.5, 0.0, "s", 0.5)
    Rt, Tt = tmm_rt([(0.5, n)], 1.0, 1.5, 0.0, "s", 0.5)
    worst_airy_lossy = max(worst_airy_lossy, Ra + Ta)
    worst_tmm_lossy = max(worst_tmm_lossy, Rt + Tt)
    print("      Im(eps)=%.1f  airy R=%.9f T=%.9f R+T=%.9f | tmm R+T=%.9f"
          % (eps_imag, Ra, Ta, Ra + Ta, Rt + Tt))
check("airy: R + T <= 1 for every lossy case", worst_airy_lossy <= 1.0 + 1e-12,
      "max R+T=%.9f" % worst_airy_lossy)
check("tmm: breaks down for lossy media (why airy_rt exists)",
      worst_tmm_lossy > 1.0, "max R+T=%.9f" % worst_tmm_lossy)

print("5. Closed-form design results")
R, T = fresnel_rt(1.0, 2.0, 0.0, "s")
check("normal n=1->2 gives R=1/9, T=8/9",
      abs(R - 1 / 9) < 1e-15 and abs(T - 8 / 9) < 1e-15,
      "R=%.15f T=%.15f" % (R, T))

n2 = 3.0
R_b, T_b = fresnel_rt(1.0, n2, math.degrees(math.atan(n2)), "p")
check("p reflectance vanishes at Brewster's angle", R_b < 1e-30,
      "R_p=%.3e" % R_b)

crit = math.degrees(math.asin(1.0 / 2.0))
R_tir, T_tir = fresnel_rt(2.0, 1.0, crit + 5.0, "s")
check("total internal reflection gives R=1, T=0",
      abs(R_tir - 1.0) < 1e-12 and T_tir == 0.0,
      "R=%.12f T=%.3e" % (R_tir, T_tir))

n_sub = 4.0
n_film = math.sqrt(n_sub)
d = 1.0 / (4.0 * n_film)
R_a, T_a = airy_rt(d, n_film, 1.0, n_sub, 0.0, "s", 1.0)
check("ideal quarter-wave coating does not reflect", R_a < 1e-20,
      "R=%.3e T=%.12f" % (R_a, T_a))

print()
if failures:
    print("ANALYTIC MODULE SELF-CHECK: FAIL -> %s" % ", ".join(failures))
    sys.exit(1)
print("ANALYTIC MODULE SELF-CHECK: PASS")
sys.exit(0)
