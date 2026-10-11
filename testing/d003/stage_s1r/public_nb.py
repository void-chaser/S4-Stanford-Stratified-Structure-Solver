#!/usr/bin/env python3
"""P05-S1R Q2 public-API probe (read-only; a new file, no S4/ change).

Runs VL (Default), Jones and Normal at NumBasis 1..9 through the PUBLIC Python API of a
given build (the path to the build directory is an argument; the build must be a scratch copy
made by git archive, never S4/).  The geometry and options are those of the S1 T6 script
(testing/../checkpoints/p05/evidence/t6_vl_nb1.py), so results are comparable to S1.

Each case builds a FRESH object (no SetOptions after construction).  The raw outcome is recorded:
  - 'EXC' with the exception text, or 'OK' with the flux values and finiteness.
No verdict is drawn here.  The output is a JSON file given by the second argument.

Usage:  public_nb.py BUILD_DIR OUT_JSON [NB ...]
"""
import sys, json, math, os

BUILD = sys.argv[1]
OUT = sys.argv[2]
NBS = [int(x) for x in sys.argv[3:]] or list(range(1, 10))
sys.path.insert(0, BUILD)
import S4  # noqa: E402

if not os.path.realpath(S4.__file__).startswith(os.path.realpath(BUILD)):
    raise SystemExit("REFUSED: S4 was not loaded from the given build directory: " + S4.__file__)


def build(basis, nb, freq, theta_deg):
    S = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=nb)
    opts = {"PolarizationDecomposition": True}
    if basis == "VL":
        opts["PolarizationBasis"] = "Default"
    elif basis == "Jones":
        opts["PolarizationBasis"] = "Jones"
    elif basis == "Normal":
        opts["PolarizationBasis"] = "Normal"
    S.SetOptions(**opts)
    S.SetMaterial(Name="Glass", Epsilon=complex(4.0, 0.0))
    S.SetMaterial(Name="Air", Epsilon=complex(1.0, 0.0))
    S.AddLayer(Name="Air_above", Thickness=0.0, S4_Material="Air")
    S.AddLayer(Name="Slab", Thickness=0.5, S4_Material="Air")
    S.SetRegionCircle("Slab", "Glass", (0.0, 0.0), 0.25)
    S.AddLayer(Name="Air_below", Thickness=0.0, S4_Material="Air")
    S.SetExcitationPlanewave(IncidenceAngles=(float(theta_deg), 0.0),
                             sAmplitude=complex(1.0, 0.0), pAmplitude=complex(0.0, 0.0), Order=0)
    S.SetFrequency(freq)
    return S


def finite_c(z):
    return isinstance(z, complex) and math.isfinite(z.real) and math.isfinite(z.imag)


records = []
for basis in ("VL", "Jones", "Normal"):
    for nb in NBS:
        rec = {"basis": basis, "NumBasis": nb, "freq": 0.427, "theta_deg": 0.0}
        try:
            S = build(basis, nb, 0.427, 0.0)
            top = S.GetPowerFlux(S4_Layer="Air_above")
            bot = S.GetPowerFlux(S4_Layer="Air_below")
            rec["status"] = "OK"
            rec["flux_top"] = [repr(z) for z in top]
            rec["flux_bot"] = [repr(z) for z in bot]
            rec["flux_finite"] = all(finite_c(z) for z in list(top) + list(bot))
        except Exception as exc:  # the raw exception is the outcome; nothing is hidden
            rec["status"] = "EXC"
            rec["exc_type"] = type(exc).__name__
            rec["exc_text"] = str(exc)
        records.append(rec)

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump({"S4_file": S4.__file__, "records": records}, fh, indent=1)
    fh.write("\n")
for r in records:
    print("%-7s NB=%d  %s %s" % (r["basis"], r["NumBasis"], r["status"],
          r.get("exc_text", "finite=%s" % r.get("flux_finite"))))
