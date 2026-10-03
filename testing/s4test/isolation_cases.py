"""Isolation probes: one process per case, so a native crash is contained.

Every probe is executed by ``common.run_isolated`` in a fresh interpreter.  This
exists because parts of the S4 extension can abort the process (SIGABRT from
``free()``) instead of raising a Python exception, which would otherwise take
down the whole test run and hide every subsequent result.

Probes return a small JSON-serialisable value describing what happened.
"""

import gc
import math
import os
import tempfile

import S4

CASES = {}


def case(name):
    def register(fn):
        CASES[name] = fn
        return fn
    return register


def _uniform_stack(n_above=1.0, layers=((0.5, 2.0),), n_below=1.0, num_basis=1):
    """Planar stack with the middle layers included (3+ layers total)."""
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    sim.AddMaterial("_above", complex(n_above) ** 2)
    for i, (_, n) in enumerate(layers):
        sim.AddMaterial("_film%d" % i, complex(n) ** 2)
    sim.AddMaterial("_below", complex(n_below) ** 2)
    sim.AddLayer("Above", 0, "_above")
    for i, (d, _) in enumerate(layers):
        sim.AddLayer("Film%d" % i, d, "_film%d" % i)
    sim.AddLayer("Below", 0, "_below")
    return sim


# --------------------------------------------------------------------------
# Build / import
# --------------------------------------------------------------------------

@case("import_module")
def _import_module():
    return {
        "file": S4.__file__,
        "doc_first_line": (S4.__doc__ or "").strip().splitlines()[0],
        "attrs": sorted(n for n in dir(S4) if not n.startswith("__")),
    }


@case("module_surface")
def _module_surface():
    required = ["New", "NewInterpolator", "NewSpectrumSampler", "SolveInParallel", "Error"]
    missing = [n for n in required if not hasattr(S4, n)]
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
    methods = sorted(n for n in dir(sim) if not n.startswith("__"))
    return {"missing_module_attrs": missing, "n_methods": len(methods), "methods": methods}


# --------------------------------------------------------------------------
# Core numerically-checkable behaviour
# --------------------------------------------------------------------------

@case("energy_conservation_lossless")
def _energy_conservation_lossless():
    sim = _uniform_stack(1.0, ((0.5, 2.0),), 1.0)
    sim.SetFrequency(0.5)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    inc, refl = sim.GetPowerFlux("Above", 0.0)
    trans, _ = sim.GetPowerFlux("Below", 0.0)
    R = -refl.real / inc.real
    T = trans.real / inc.real
    return {"R": R, "T": T, "sum": R + T, "finite": math.isfinite(R) and math.isfinite(T)}


@case("bare_interface_two_layers")
def _bare_interface_two_layers():
    """A two-layer (single, semi-infinite/semi-infinite) stack.

    Known defect: S4 returns identically zero flux here.  The probe documents
    whatever the running build does so the test can assert on the real result
    rather than silently skipping.
    """
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
    sim.AddMaterial("_above", 1.0)
    sim.AddMaterial("_below", 4.0)
    sim.AddLayer("Above", 0, "_above")
    sim.AddLayer("Below", 0, "_below")
    sim.SetFrequency(1.0)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    inc, refl = sim.GetPowerFlux("Above", 0.0)
    trans, _ = sim.GetPowerFlux("Below", 0.0)
    return {
        "incident": inc.real,
        "reflected_power": -refl.real,
        "transmitted_power": trans.real,
        "sum": (-refl.real) + trans.real,
        # Analytic expectation for n=1 -> n=2 at normal incidence:
        "analytic_R": 1.0 / 9.0,
        "analytic_T": 8.0 / 9.0,
    }


@case("clone_then_destroy_both")
def _clone_then_destroy_both():
    """Clone a patterned stack, destroy both objects explicitly."""
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=9)
    sim.AddMaterial("Air", 1)
    sim.AddMaterial("Si", 12)
    sim.AddLayer("Top", 0, "Air")
    sim.AddLayer("Slab", 0.5, "Si")
    sim.SetRegionCircle("Slab", "Air", (0, 0), 0.2)
    sim.AddLayerCopy("Bot", 0, "Top")
    sim.SetFrequency(0.4)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    clone = sim.Clone()
    flux_before = clone.GetPowerFlux("Bot")[0].real
    del clone
    gc.collect()
    del sim
    gc.collect()
    return {"clone_flux_before_destroy": flux_before}


@case("clone_outlives_original")
def _clone_outlives_original():
    """Clone of a temporary: the original is released before the clone."""
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=9)
    sim.AddMaterial("Air", 1)
    sim.AddMaterial("Si", 12)
    sim.AddLayer("Top", 0, "Air")
    sim.AddLayer("Slab", 0.5, "Si")
    sim.SetRegionCircle("Slab", "Air", (0, 0), 0.2)
    sim.AddLayerCopy("Bot", 0, "Top")
    sim.SetFrequency(0.4)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    clone = sim.Clone()
    del sim            # original destroyed while the clone is still alive
    gc.collect()
    flux = clone.GetPowerFlux("Bot")[0].real
    del clone
    gc.collect()
    return {"clone_flux": flux}


# --------------------------------------------------------------------------
# Interfaces that are known to be broken / hazardous
# --------------------------------------------------------------------------

@case("interpolator_cubic_spline")
def _interpolator_cubic_spline():
    table = ((0.0, (0.0,)), (0.5, (0.25,)), (1.0, (1.0,)))
    obj = S4.NewInterpolator("cubic spline", table)
    return {"value_at_0.75": repr(obj.Get(0.75))}


@case("interpolator_cublic_spline_typo")
def _interpolator_cublic_spline_typo():
    """The literal string accepted by the implementation ('cublic spline')."""
    table = ((0.0, (0.0,)), (0.5, (0.25,)), (1.0, (1.0,)))
    obj = S4.NewInterpolator("cublic spline", table)
    return {"value_at_0.75": repr(obj.Get(0.75))}


@case("spectrum_sampler_three_args")
def _spectrum_sampler_three_args():
    sampler = S4.NewSpectrumSampler(0.3, 0.5, 5)
    return {"IsDone": sampler.IsDone()}


@case("spectrum_sampler_two_args")
def _spectrum_sampler_two_args():
    sampler = S4.NewSpectrumSampler(0.3, 0.5)
    return {"IsDone": sampler.IsDone()}


@case("invalid_inputs_raise")
def _invalid_inputs_raise():
    """Every one of these must raise a Python exception, not abort the process."""
    outcomes = {}

    def attempt(tag, fn):
        try:
            fn()
            outcomes[tag] = "returned"
        except BaseException as exc:
            outcomes[tag] = "%s" % type(exc).__name__

    attempt("New_num_basis_zero", lambda: S4.New(Lattice=((1, 0), (0, 1)), NumBasis=0))
    attempt("New_bad_lattice", lambda: S4.New(Lattice=((1, 0), (0, 1), (1, 1)), NumBasis=4))
    attempt("AddLayer_unknown_material", lambda: _add_layer_missing_material())
    attempt("GetPowerFlux_unknown_layer", lambda: _flux_unknown_layer())
    attempt("GetPowerFlux_onelesslayer", lambda: _flux_single_layer())
    attempt("SetLayer_negative_thickness", lambda: _negative_thickness())
    attempt("SetVerbosity_out_of_range", lambda: _bad_verbosity())
    attempt("SetRegionCircle_unknown_layer", lambda: _region_unknown_layer())
    attempt("GetEpsilon_before_layers", lambda: _epsilon_no_layers())
    return outcomes


def _add_layer_missing_material():
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
    sim.AddLayer("Only", 0, "DoesNotExist")


def _flux_unknown_layer():
    sim = _uniform_stack(1.0, ((0.5, 2.0),), 2.0)
    sim.SetFrequency(0.5)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    sim.GetPowerFlux("NoSuchLayer")


def _flux_single_layer():
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
    sim.AddMaterial("Air", 1)
    sim.AddLayer("Only", 0, "Air")
    sim.SetFrequency(0.5)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    sim.GetPowerFlux("Only")


def _negative_thickness():
    sim = _uniform_stack(1.0, ((0.5, 2.0),), 2.0)
    sim.SetLayer("Film0", -1.0, "_film0")


def _bad_verbosity():
    sim = _uniform_stack(1.0, ((0.5, 2.0),), 2.0)
    sim.SetVerbosity(42)


def _region_unknown_layer():
    sim = _uniform_stack(1.0, ((0.5, 2.0),), 2.0)
    sim.SetRegionCircle("NoSuchLayer", "_film0", (0, 0), 0.2)


def _epsilon_no_layers():
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
    sim.GetEpsilon(0.0, 0.0, 0.0)


@case("grid_output_all_formats")
def _grid_output_all_formats():
    sim = _uniform_stack(1.0, ((0.5, 3.0),), 1.0, num_basis=9)
    sim.SetRegionCircle("Film0", "_above", (0, 0), 0.2)
    sim.SetFrequency(0.5)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    results = {}
    with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
        for fmt in ("text", "bin", "hdf5", "mat", "vtk", "silo"):
            try:
                out = sim.GetFieldsOnGrid(0.0, (8, 8), fmt, os.path.join(tmp, "g_" + fmt))
                results[fmt] = "ok:len=%d" % len(out)
            except BaseException as exc:
                results[fmt] = "%s: %s" % (type(exc).__name__, exc)
        results["_files"] = sorted(os.listdir(tmp))
    return results


@case("eigensolver_small_basis")
def _eigensolver_small_basis():
    """Solve a patterned slab at the smallest Fourier bases.

    Minimal input for the eigensolver workspace defect: one GetPowerFlux on a
    freshly built simulation, with no Clone involved. The out-of-bounds write is
    visible only to AddressSanitizer, so this reports whether the solve completed
    and what it produced; the sanitizer run is what detects the write itself.
    """
    results = {}
    for nb in (1, 2, 4):
        sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=nb)
        sim.AddMaterial("Air", 1)
        sim.AddMaterial("Si", 12)
        sim.AddLayer("Top", 0, "Air")
        sim.AddLayer("Slab", 0.5, "Si")
        sim.SetRegionCircle("Slab", "Air", (0.0, 0.0), 0.2)
        sim.AddLayerCopy("Bot", 0, "Top")
        sim.SetFrequency(0.5)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        inc, refl = sim.GetPowerFlux("Top", 0.0)
        trans, _ = sim.GetPowerFlux("Bot", 0.0)
        results["T@%d" % nb] = trans.real / inc.real
    return {"solved": len(results) == 3, "table": results}
