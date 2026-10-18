#!/usr/bin/env python3
# e2e_python_r9m3a.py -- one Python-side E2E point: clean reference, injection, same-object retry, fresh-object retry.
# usage: python3 -I -B e2e_python_r9m3a.py SPEC   (SPEC in fft|jones|nv|vl)
# env: S4FMM_INJECT / S4FMM_NTH are set by the driver for step 2 only.
import os, sys, json

def build(spec):
    import S4
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=25)
    sim.AddMaterial("Air", 1)
    sim.AddMaterial("Slab", 12)
    sim.AddLayer("Top", 0, "Air")
    sim.AddLayer("Middle", 0.5, "Slab")
    sim.SetRegionCircle("Middle", "Air", (0, 0), 0.2)
    sim.AddLayerCopy("Bottom", 0, "Top")
    sim.SetFrequency(0.4)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    if spec in ("fft",):
        sim.SetOptions(DiscretizedEpsilon=True, DiscretizationResolution=8, PolarizationDecomposition=True, PolarizationBasis="Normal")
    elif spec == "jones":
        sim.SetOptions(PolarizationDecomposition=True, PolarizationBasis="Jones", DiscretizedEpsilon=True, DiscretizationResolution=8)
    elif spec == "nv":
        sim.SetOptions(PolarizationDecomposition=True, PolarizationBasis="Normal", DiscretizedEpsilon=True, DiscretizationResolution=8)
    elif spec == "vl":
        sim.SetOptions(PolarizationDecomposition=True, PolarizationBasis="Default", DiscretizedEpsilon=True, DiscretizationResolution=8)
    return sim


def solve(sim):
    f, b = sim.GetPowerFlux("Bottom")
    return [f.real, f.imag, b.real, b.imag]


def emit(obj):
    sys.stdout.write(json.dumps(obj) + chr(10))
    sys.stdout.flush()


def attempt(sim):
    try:
        return {"ok": True, "values": solve(sim), "error_type": None, "error_msg": None}
    except BaseException as exc:
        return {"ok": False, "values": None, "error_type": type(exc).__name__, "error_msg": str(exc)[:400]}


def main():
    spec = sys.argv[1] if len(sys.argv) > 1 else "fft"
    res = {"spec": spec, "steps": {}}
    # step 1: clean reference (no injection env present)
    ref_sim = build(spec)
    res["steps"]["1_clean_ref"] = attempt(ref_sim)
    # step 2: injection (driver has exported S4FMM_INJECT / S4FMM_NTH)
    inj_sim = build(spec)
    res["steps"]["2_inject"] = attempt(inj_sim)
    # step 3: retry on the same object, injection env removed
    for k in ("S4FMM_INJECT", "S4FMM_NTH"):
        os.environ.pop(k, None)
    res["steps"]["3_retry_same"] = attempt(inj_sim)
    # step 4: retry on a fresh object
    fresh = build(spec)
    res["steps"]["4_retry_fresh"] = attempt(fresh)
    emit(res)
    return 0


if __name__ == "__main__":
    sys.exit(main())
