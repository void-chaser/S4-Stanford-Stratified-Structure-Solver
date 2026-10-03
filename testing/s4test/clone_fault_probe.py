#!/usr/bin/env python3
"""Child-process probe for allocation-failure injection in Clone().

Run with S4_FAIL_ALLOC_AT=k and S4_CLONE_FIXTURE=<name>. Selects one of the
fixtures below, attempts a clone, and reports whether the clone succeeded or
failed, whether the original survived unchanged and destroyable, and whether a
successful clone is numerically equivalent.

A failed clone must raise; if ownership is wrong it crashes instead, which is why
this runs in its own interpreter.
"""
import gc
import json
import os
import sys

sys.path.insert(0, os.environ["S4_TEST_REPO_ROOT"])
sys.path.insert(0, os.path.join(os.environ["S4_TEST_REPO_ROOT"], "testing/s4test"))

from s4test_common import ISOLATION_EXC, ISOLATION_OK, ISOLATION_STARTED
import S4

#: Fixtures. Each reaches different allocation sites inside the clone:
#:   planewave  materials, a circle and a polygon, a layer copy
#:   exterior   adds the two exterior-excitation buffers
#:   polygon    two layers with 3, 4 and 5 vertex polygons, so several shape
#:              arrays and vertex arrays exist
FIXTURES = ("planewave", "exterior", "polygon")


def report(payload):
    print(ISOLATION_STARTED, flush=True)
    print(ISOLATION_OK + json.dumps({"result": payload}), flush=True)
    os._exit(0)


def build_planewave(nb=25):
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=nb)
    sim.AddMaterial("Air", 1)
    sim.AddMaterial("Si", 12)
    sim.AddMaterial("Lossy", 12 + 0.5j)
    sim.AddMaterial("Aniso", ((12 + 0j, 0.5 + 0j, 0j),
                              (0.5 + 0j, 12 + 0j, 0j),
                              (0j, 0j, 4 + 0j)))
    sim.AddLayer("Top", 0, "Air")
    sim.AddLayer("Mid", 0.5, "Aniso")
    sim.SetRegionCircle("Mid", "Si", (0.0, 0.0), 0.2)
    sim.SetRegionPolygon("Mid", "Lossy", (0.0, 0.0), 0,
                         ((0.15, 0.0), (0.3, 0.1), (0.2, 0.28)))
    sim.AddLayerCopy("Bot", 0, "Top")
    sim.SetFrequency(0.4)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    return sim


def build_exterior(nb=25):
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=nb)
    sim.AddMaterial("Air", 1)
    sim.AddMaterial("Si", 12)
    sim.AddLayer("Top", 0, "Air")
    sim.AddLayer("Slab", 0.5, "Si")
    sim.AddLayerCopy("Bot", 0, "Top")
    sim.SetFrequency(0.4)
    sim.SetExcitationExterior(((0, "x", 1 + 0j),))
    return sim


def build_polygon(nb=25):
    """Several polygons with distinct vertex counts, across two layers."""
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=nb)
    sim.AddMaterial("Air", 1)
    sim.AddMaterial("Si", 12)
    sim.AddLayer("Top", 0, "Air")
    sim.AddLayer("L1", 0.4, "Si")
    sim.AddLayer("L2", 0.4, "Si")
    sim.AddLayerCopy("Bot", 0, "Top")
    sim.SetRegionPolygon("L1", "Air", (0.0, 0.0), 0,
                         ((0.0, 0.0), (0.3, 0.0), (0.3, 0.3), (0.0, 0.3)))
    sim.SetRegionPolygon("L1", "Air", (0.55, 0.55), 45,
                         ((0.0, 0.0), (0.2, 0.0), (0.25, 0.15),
                          (0.1, 0.25), (0.0, 0.2)))
    sim.SetRegionPolygon("L2", "Air", (0.0, 0.0), 15,
                         ((0.0, 0.0), (0.25, 0.05), (0.2, 0.25)))
    sim.SetFrequency(0.4)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    return sim


BUILDERS = {
    "planewave": build_planewave,
    "exterior": build_exterior,
    "polygon": build_polygon,
}


def rt(sim):
    inc, refl = sim.GetPowerFlux("Top", 0.0)
    trans, _ = sim.GetPowerFlux("Bot", 0.0)
    if inc.real == 0.0:
        return (refl.real, trans.real)
    return (-refl.real / inc.real, trans.real / inc.real)


def main():
    name = os.environ.get("S4_CLONE_FIXTURE", "planewave")
    if name not in BUILDERS:
        print(ISOLATION_STARTED, flush=True)
        print(ISOLATION_EXC + json.dumps(
            {"type": "ValueError", "message": "unknown fixture %r" % name}),
            flush=True)
        return 1
    count_path = os.environ.get("S4_ALLOC_COUNT")
    payload = {"fixture": name, "clone_succeeded": False,
               "clone_equivalent": False, "original_unchanged": False,
               "original_destroyed_cleanly": False, "allocations_seen": 0}
    try:
        sim = BUILDERS[name]()
        before = rt(sim)          # solve first, so a solution exists

        clone = None
        try:
            clone = sim.Clone()
            payload["clone_succeeded"] = True
        except Exception as exc:                    # noqa: BLE001
            payload["clone_error"] = "%s: %s" % (type(exc).__name__, exc)

        # The scope guard writes this on every return path of the clone.
        if count_path and os.path.isfile(count_path):
            try:
                payload["allocations_seen"] = int(
                    open(count_path).read().strip() or 0)
            except (OSError, ValueError):
                pass

        after = rt(sim)
        payload["original_before"] = list(before)
        payload["original_after"] = list(after)
        payload["original_unchanged"] = (
            abs(before[0] - after[0]) <= 1e-12
            and abs(before[1] - after[1]) <= 1e-12)

        if clone is not None:
            c = rt(clone)
            payload["clone_equivalent"] = (
                abs(before[0] - c[0]) <= 1e-12
                and abs(before[1] - c[1]) <= 1e-12)
            del clone
            gc.collect()

        del sim
        gc.collect()
        payload["original_destroyed_cleanly"] = True

        probe = BUILDERS[name]()
        del probe
        gc.collect()
    except BaseException as exc:                    # noqa: BLE001
        print(ISOLATION_STARTED, flush=True)
        print(ISOLATION_EXC + json.dumps(
            {"type": type(exc).__name__, "message": str(exc)}), flush=True)
        return 1

    report(payload)


if __name__ == "__main__":
    sys.exit(main())
