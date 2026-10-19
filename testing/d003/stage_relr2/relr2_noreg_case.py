#!/usr/bin/env python3
# relr2_noreg_case.py -- one public-API probe case for the REL-R2 no-injection research
# (task brief section 3.5).  Runs against a REL-R1 exported tree (--tree) and prints one JSON line.
# Read-only with respect to the tree; writes nothing.
import sys, json, math

def arg(name, default=None):
    if name in sys.argv:
        return sys.argv[sys.argv.index(name) + 1]
    return default

TREE = arg("--tree")
CASE = arg("--case")
if not TREE or not CASE:
    print(json.dumps({"status": "USAGE_ERROR"}))
    sys.exit(2)
sys.path.insert(0, TREE)
import S4

FREQ = 0.427
BASE_OPTS = {"PolarizationDecomposition": True}


def build(opts, mat_eps, num_basis=3):
    S = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    S.SetOptions(**opts)
    S.SetMaterial(Name="Sub", Epsilon=mat_eps)
    S.SetMaterial(Name="Air", Epsilon=complex(1.0, 0.0))
    S.AddLayer(Name="Air_above", Thickness=0.0, S4_Material="Air")
    S.AddLayer(Name="Slab", Thickness=0.5, S4_Material="Air")
    S.SetRegionCircle("Slab", "Sub", (0.0, 0.0), 0.25)
    S.AddLayer(Name="Air_below", Thickness=0.0, S4_Material="Air")
    S.SetExcitationPlanewave(IncidenceAngles=(0.0, 0.0), sAmplitude=complex(1.0, 0.0),
                             pAmplitude=complex(0.0, 0.0), Order=0)
    S.SetFrequency(FREQ)
    return S


CASES = {
    "vl_nb1":        dict(opts=dict(BASE_OPTS), eps=complex(4.0, 0.0), nb=1),
    "nv_nb1":        dict(opts=dict(BASE_OPTS, PolarizationBasis="Normal"), eps=complex(4.0, 0.0), nb=1),
    "jones_nb1":     dict(opts=dict(BASE_OPTS, PolarizationBasis="Jones"), eps=complex(4.0, 0.0), nb=1),
    "cf_eps0":       dict(opts=dict(), eps=complex(0.0, 0.0), nb=3),
    "cf_epsbig":     dict(opts=dict(), eps=complex(1e300, 0.0), nb=3),
    "kt_eps0":       dict(opts=dict(DiscretizedEpsilon=True, SubpixelSmoothing=True), eps=complex(0.0, 0.0), nb=3),
    "kt_epsbig":     dict(opts=dict(DiscretizedEpsilon=True, SubpixelSmoothing=True), eps=complex(1e300, 0.0), nb=3),
    "cf_eps_singular_tensor": dict(opts=dict(), eps=((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)), nb=3),
    "kt_eps_singular_tensor": dict(opts=dict(DiscretizedEpsilon=True, SubpixelSmoothing=True),
                                   eps=((1.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 1.0)), nb=3),
}
if CASE not in CASES:
    print(json.dumps({"status": "UNKNOWN_CASE"}))
    sys.exit(2)
spec = CASES[CASE]
rec = {"case": CASE, "tree": TREE, "num_basis": spec["nb"]}
try:
    S = build(spec["opts"], spec["eps"], spec["nb"])
    v = S.GetPowerFlux("Air_above")
    if isinstance(v, (list, tuple)):
        nums = []
        for z in v:
            nums += [z.real, z.imag]
        text = ",".join(repr(x) for x in nums)
    else:
        nums = [v.real, v.imag]
        text = repr(v)
    rec.update({"status": "RETURNED", "value": text[:300],
                "all_finite": all(math.isfinite(x) for x in nums)})
except Exception as exc:
    rec.update({"status": "EXCEPTION", "exc_type": type(exc).__name__, "message": str(exc)[:300]})
print(json.dumps(rec))
