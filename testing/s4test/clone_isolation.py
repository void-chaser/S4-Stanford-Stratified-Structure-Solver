"""Run one Clone equivalence scenario in a separate interpreter.

Why isolated
------------
The original Clone defect aborted the process (SIGABRT from ``free()``) or
segfaulted rather than raising.  A crash inside the test process would destroy
every remaining test result, so the destructive scenarios run in a child
process and report a verdict instead.  ``s4test_common.run_isolated`` classifies
the outcome as ok / exception / crash / timeout.

Each scenario returns the numbers it compared, so the parent test can assert on
them as well as on the absence of a crash.  The comparison itself happens inside
the child, where both objects are alive.
"""

import gc
import os

import S4

from test_structures import (build_patterned_slab, build_scalar_stack,
                             build_tensor_stack, read_rt)

CASES = {}

_TOL = 1e-12


def case(name):
    def register(fn):
        CASES[name] = fn
        return fn
    return register


def _same(a, b, tol=_TOL):
    return len(a) == len(b) and all(abs(x - y) <= tol for x, y in zip(a, b))


def _compare(tag, sim, clone, top, bottom):
    """Assert equivalence inside the child and return the compared values."""
    a = read_rt(sim, top, bottom)
    b = read_rt(clone, top, bottom)
    if not _same(a, b):
        raise AssertionError("%s: R/T differ, %r vs %r" % (tag, a, b))
    return {"R": a[0], "T": a[1]}


@case("scalar_destroy_clone_first")
def _scalar_destroy_clone_first():
    sim = build_scalar_stack()
    clone = sim.Clone()
    out = _compare("scalar", sim, clone, "Top", "Bot")
    del clone
    gc.collect()
    after = read_rt(sim, "Top", "Bot")
    if not _same((out["R"], out["T"]), after):
        raise AssertionError("original changed after destroying the clone")
    return out


@case("scalar_destroy_original_first")
def _scalar_destroy_original_first():
    sim = build_scalar_stack()
    clone = sim.Clone()
    out = _compare("scalar", sim, clone, "Top", "Bot")
    del sim
    gc.collect()
    after = read_rt(clone, "Top", "Bot")
    if not _same((out["R"], out["T"]), after):
        raise AssertionError("clone changed after destroying the original")
    del clone
    gc.collect()
    return out


@case("tensor_destroy_clone_first")
def _tensor_destroy_clone_first():
    sim = build_tensor_stack()
    clone = sim.Clone()
    out = _compare("tensor", sim, clone, "Top", "Bot")
    del clone
    gc.collect()
    after = read_rt(sim, "Top", "Bot")
    if not _same((out["R"], out["T"]), after):
        raise AssertionError("original changed after destroying the clone")
    return out


@case("tensor_destroy_original_first")
def _tensor_destroy_original_first():
    sim = build_tensor_stack()
    clone = sim.Clone()
    out = _compare("tensor", sim, clone, "Top", "Bot")
    del sim
    gc.collect()
    after = read_rt(clone, "Top", "Bot")
    if not _same((out["R"], out["T"]), after):
        raise AssertionError("clone changed after destroying the original")
    return out


@case("polygon_destroy_original_first")
def _polygon_destroy_original_first():
    sim = build_patterned_slab("polygon", num_basis=25)
    clone = sim.Clone()
    out = _compare("polygon", sim, clone, "Above", "Below")
    del sim
    gc.collect()
    after = read_rt(clone, "Above", "Below")
    if not _same((out["R"], out["T"]), after):
        raise AssertionError("clone changed after destroying the original")
    return out


@case("clone_then_modify_frequency")
def _clone_then_modify_frequency():
    sim = build_scalar_stack()
    clone = sim.Clone()
    before = read_rt(sim, "Top", "Bot")
    clone.SetFrequency(0.9)
    after = read_rt(sim, "Top", "Bot")
    if not _same(before, after):
        raise AssertionError("changing the clone's frequency affected the original")
    return {"R": before[0], "T": before[1]}


@case("clone_then_modify_material")
def _clone_then_modify_material():
    sim = build_scalar_stack()
    clone = sim.Clone()
    before = read_rt(sim, "Top", "Bot")
    clone.SetMaterial("Si", 4.0)
    after = read_rt(sim, "Top", "Bot")
    if not _same(before, after):
        raise AssertionError("changing the clone's material affected the original")
    changed = read_rt(clone, "Top", "Bot")
    if _same(before, changed):
        raise AssertionError("the material change had no effect on the clone")
    return {"R": before[0], "T": before[1]}


@case("many_clones_interleaved")
def _many_clones_interleaved():
    sim = build_patterned_slab("ellipse", num_basis=25)
    expected = read_rt(sim, "Above", "Below")
    clones = [sim.Clone() for _ in range(8)]
    for i, clone in enumerate(clones):
        got = read_rt(clone, "Above", "Below")
        if not _same(expected, got):
            raise AssertionError("clone %d differs: %r vs %r" % (i, expected, got))
    for i in range(0, len(clones), 2):
        clones[i] = None
        gc.collect()
    for clone in clones:
        if clone is not None:
            got = read_rt(clone, "Above", "Below")
            if not _same(expected, got):
                raise AssertionError("a surviving clone differs after GC")
    return {"R": expected[0], "T": expected[1]}


@case("repeated_cloning_chain")
def _repeated_cloning_chain():
    sim = build_tensor_stack()
    expected = read_rt(sim, "Top", "Bot")
    current = sim
    for _ in range(4):
        current = current.Clone()
        got = read_rt(current, "Top", "Bot")
        if not _same(expected, got):
            raise AssertionError("a clone in the chain differs: %r vs %r"
                                 % (expected, got))
    return {"R": expected[0], "T": expected[1]}
