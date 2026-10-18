#!/usr/bin/env python3
# e2e_python_r9m3b.py -- Python public-API E2E harness for one option group.
# usage: python3 -B e2e_python_r9m3b.py MODE SPEC      (MODE: calib|ref|inject|fresh)
#   calib : build + one solve, no injection (used by calib_e2e_r9m3b.py)
#   ref   : clean reference in its own process (no injection env)
#   inject: A = first solve of this process with the injection env present,
#           B = same object retried after the injection env is popped,
#           C = brand-new object in the same process
#   fresh : new process, new object (R2)
# Output is one JSON line on stdout: values are [f.real, f.imag, b.real, b.imag] of
# GetPowerFlux("Bottom"), plus the exception type and text when the solve fails.
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
    if spec == "cf":
        pass  # default options: ClosedForm path
    elif spec == "fft":
        sim.SetOptions(DiscretizedEpsilon=True, DiscretizationResolution=8, PolarizationDecomposition=False)
    elif spec == "kt":
        sim.SetOptions(DiscretizedEpsilon=True, DiscretizationResolution=8, SubpixelSmoothing=True, PolarizationDecomposition=False)
    elif spec == "jones":
        sim.SetOptions(DiscretizedEpsilon=True, DiscretizationResolution=8, PolarizationDecomposition=True, PolarizationBasis="Jones")
    elif spec == "nv":
        sim.SetOptions(DiscretizedEpsilon=True, DiscretizationResolution=8, PolarizationDecomposition=True, PolarizationBasis="Normal")
    elif spec == "vl":
        sim.SetOptions(DiscretizedEpsilon=True, DiscretizationResolution=8, PolarizationDecomposition=True, PolarizationBasis="Default")
    else:
        raise SystemExit("e2e_python_r9m3b: unknown spec " + spec)
    return sim


def solve(sim):
    f, b = sim.GetPowerFlux("Bottom")
    return [f.real, f.imag, b.real, b.imag]


def attempt(sim):
    try:
        return {"ok": True, "values": solve(sim), "error_type": None, "error_msg": None}
    except BaseException as exc:
        return {"ok": False, "values": None, "error_type": type(exc).__name__, "error_msg": str(exc)[:400]}


def main():
    if len(sys.argv) < 3:
        raise SystemExit("usage: e2e_python_r9m3b.py MODE SPEC")
    mode, spec = sys.argv[1], sys.argv[2]
    out = {"mode": mode, "spec": spec, "steps": {}}
    if mode == "calib":
        out["steps"]["calib"] = attempt(build(spec))
    elif mode == "ref":
        out["steps"]["ref"] = attempt(build(spec))
    elif mode == "fresh":
        out["steps"]["fresh"] = attempt(build(spec))
    elif mode == "inject":
        sim = build(spec)
        out["steps"]["A_inject"] = attempt(sim)
        for k in ("S4FMM_INJECT", "S4FMM_NTH"):
            os.environ.pop(k, None)
        out["steps"]["B_retry_same"] = attempt(sim)
        out["steps"]["C_retry_fresh_obj"] = attempt(build(spec))
    else:
        raise SystemExit("e2e_python_r9m3b: unknown mode " + mode)
    sys.stdout.write(json.dumps(out) + chr(10))
    return 0


if __name__ == "__main__":
    sys.exit(main())
