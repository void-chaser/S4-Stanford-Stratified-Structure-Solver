"""Isolation cases for exterior-excitation ownership.

Each case builds a simulation with an exterior excitation, optionally clones it,
and tears the objects down in a specified order. They run in a child process
because the failure mode is a heap corruption that aborts the interpreter.

``run_isolated`` reads the value of ``{"result": ...}`` from the marked line, so
each case ends by calling ``report()``.
"""

import gc
import json
import os

import S4

from s4test_common import ISOLATION_OK, ISOLATION_STARTED

CASES = {}


def report(payload):
    print(ISOLATION_STARTED, flush=True)
    print(ISOLATION_OK + json.dumps({"result": payload}), flush=True)
    os._exit(0)


def case(name):
    def register(fn):
        CASES[name] = fn
        return fn
    return register


def build_exterior():
    """Planar stack excited by an exterior planewave.

    ``SetExcitationExterior`` takes a tuple of (G index, 'x'|'y', complex
    amplitude) records; the binding allocates two arrays to hold them.
    """
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=9)
    sim.AddMaterial("Air", 1)
    sim.AddMaterial("Si", 12)
    sim.AddLayer("Above", 0, "Air")
    sim.AddLayer("Slab", 0.5, "Si")
    sim.AddLayerCopy("Below", 0, "Above")
    sim.SetFrequency(0.4)
    sim.SetExcitationExterior(((0, "x", 1 + 0j),))
    return sim


def read_rt(sim):
    inc, refl = sim.GetPowerFlux("Above", 0.0)
    trans, _ = sim.GetPowerFlux("Below", 0.0)
    if inc.real == 0.0:
        return (refl.real, trans.real)
    return (-refl.real / inc.real, trans.real / inc.real)


@case("exterior_original_only")
def _original_only():
    """Control: no clone involved."""
    sim = build_exterior()
    rt = read_rt(sim)
    del sim
    gc.collect()
    report({"rt": list(rt)})


@case("exterior_clone_then_destroy_clone")
def _clone_then_destroy_clone():
    sim = build_exterior()
    clone = sim.Clone()
    del clone
    gc.collect()
    rt = read_rt(sim)
    del sim
    gc.collect()
    report({"rt": list(rt)})


@case("exterior_clone_then_destroy_original")
def _clone_then_destroy_original():
    sim = build_exterior()
    clone = sim.Clone()
    del sim
    gc.collect()
    rt = read_rt(clone)
    del clone
    gc.collect()
    report({"rt": list(rt)})


@case("exterior_solved_clone_then_destroy_clone")
def _solved_clone_then_destroy_clone():
    """Solve first so the clone also has to cope with an existing solution."""
    sim = build_exterior()
    before = read_rt(sim)          # solves
    clone = sim.Clone()
    after_clone = read_rt(clone)
    equivalent = (abs(before[0] - after_clone[0]) <= 1e-9
                  and abs(before[1] - after_clone[1]) <= 1e-9)
    del clone
    gc.collect()
    after = read_rt(sim)
    unchanged = (abs(before[0] - after[0]) <= 1e-9
                 and abs(before[1] - after[1]) <= 1e-9)
    del sim
    gc.collect()
    report({"clone_equivalent": equivalent, "original_unchanged": unchanged,
            "rt": list(before)})


@case("exterior_solved_clone_then_destroy_original")
def _solved_clone_then_destroy_original():
    sim = build_exterior()
    before = read_rt(sim)
    clone = sim.Clone()
    after_clone = read_rt(clone)
    equivalent = (abs(before[0] - after_clone[0]) <= 1e-9
                  and abs(before[1] - after_clone[1]) <= 1e-9)
    del sim
    gc.collect()
    after = read_rt(clone)
    unchanged = (abs(before[0] - after[0]) <= 1e-9
                 and abs(before[1] - after[1]) <= 1e-9)
    del clone
    gc.collect()
    report({"clone_equivalent": equivalent, "original_unchanged": unchanged,
            "rt": list(before)})


@case("exterior_clone_twice")
def _clone_twice():
    sim = build_exterior()
    a = sim.Clone()
    b = sim.Clone()
    ra = read_rt(a)
    rb = read_rt(b)
    del a
    gc.collect()
    rb2 = read_rt(b)
    del b
    gc.collect()
    rt = read_rt(sim)
    del sim
    gc.collect()
    report({"a": list(ra), "b": list(rb), "b_after_a_freed": list(rb2),
            "original": list(rt)})
