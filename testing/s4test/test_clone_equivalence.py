"""Clone() must produce a numerically equivalent, fully independent simulation.

The defect this covers
----------------------
``S4_Simulation_Clone`` used to alias heap blocks between the original and the
clone (the material and layer arrays, ``G``, ``kx``/``ky``, pattern polygon
vertex arrays, and the excitation's layer pointer), and it passed the *internal*
material discriminator (0 = scalar, 1 = tensor) straight to
``S4_Simulation_SetMaterial``, which expects the public ``S4_MATERIAL_TYPE_*``
constants (2..5).  That function's ``default:`` branch silently drops the
material, leaving the clone's freshly allocated material array uninitialised, so
the clone later ``strdup``'d garbage name pointers.  The result was an abort or
segfault that depended on allocator state and only reproduced reliably in
optimised builds.

What is checked here
--------------------
* scalar, complex-scalar and anisotropic-tensor materials survive
* all four pattern shapes survive, with parameters chosen so that the shapes are
  *not* optically equivalent (a shared parameter set would let a missing shape
  copy pass unnoticed)
* materials, geometry and R/T agree between original and clone
* destroying either object first leaves the other fully usable
* changing frequency or material on one object does not affect the other

Tolerances
----------
Everything here compares two S4 runs on the same structure, so the expected
difference is exactly zero; 1e-12 is used throughout to allow for the
possibility that a rebuild reorders a floating-point reduction.  Measured
difference is 0.0 for every case.
"""

import gc
import math
import unittest

import S4

from s4test_common import run_isolated
from test_structures import (DISTINCT_SHAPES, SHAPES, build_patterned_slab,
                             build_scalar_stack, build_tensor_stack, read_rt)

_TOL = 1e-12


def _sample_epsilons(sim, points):
    return [complex(sim.GetEpsilon(x, y, z)) for (x, y, z) in points]


class CloneMaterialEquivalenceTests(unittest.TestCase):

    def test_scalar_and_complex_materials_survive(self):
        sim = build_scalar_stack()
        clone = sim.Clone()
        points = [(0.0, 0.0, -0.1), (0.0, 0.0, 0.25), (0.3, 0.0, 0.25)]
        self.assertEqual(_sample_epsilons(sim, points),
                         _sample_epsilons(clone, points))
        self.assertEqual(read_rt(sim, "Top", "Bot"), read_rt(clone, "Top", "Bot"))

    def test_tensor_material_survives(self):
        """A tensor material is the case the internal/public type mismatch broke.

        The scalar case still worked by accident under some builds; the tensor
        case needs the type mapped to S4_MATERIAL_TYPE_XYTENSOR_COMPLEX.
        """
        sim = build_tensor_stack()
        clone = sim.Clone()
        points = [(0.05, 0.05, 0.25), (-0.2, 0.1, 0.25), (0.4, 0.4, -0.1)]
        original = _sample_epsilons(sim, points)
        copied = _sample_epsilons(clone, points)
        for a, b in zip(original, copied):
            self.assertAlmostEqual(abs(a - b), 0.0, delta=_TOL,
                                   msg="tensor permittivity differs: %r vs %r"
                                       % (a, b))
        self.assertEqual(read_rt(sim, "Top", "Bot"), read_rt(clone, "Top", "Bot"))

    def test_many_materials_all_survive(self):
        sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=9)
        for i in range(8):
            sim.AddMaterial("M%d" % i, complex(1 + i, 0.1 * i))
        sim.AddLayer("L0", 0, "M0")
        sim.AddLayer("L1", 0.3, "M1")
        sim.AddLayer("L2", 0.2, "M2")
        sim.SetRegionCircle("L1", "M3", (0, 0), 0.2)
        sim.AddLayerCopy("L3", 0, "L0")
        sim.SetFrequency(0.5)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        clone = sim.Clone()
        points = [(0.0, 0.0, -0.1), (0.0, 0.0, 0.15), (0.0, 0.0, 0.4)]
        self.assertEqual(_sample_epsilons(sim, points),
                         _sample_epsilons(clone, points))


class ClonePatternEquivalenceTests(unittest.TestCase):

    def test_shapes_are_optically_distinct(self):
        """Guard against the shapes being interchangeable in this geometry.

        If two shapes gave the same R, a test that only compared clone against
        original could pass even if the shape data were dropped entirely.
        """
        plain = read_rt(build_patterned_slab(None), "Above", "Below")
        values = {}
        for name in SHAPES:
            values[name] = read_rt(build_patterned_slab(name), "Above", "Below")
            self.assertGreater(
                abs(values[name][0] - plain[0]), 1e-6,
                "%s does not change the response versus an unpatterned slab" % name)
        for a, b in (("circle", "polygon"), ("ellipse", "rectangle"),
                     ("circle", "ellipse"), ("rectangle", "polygon")):
            self.assertGreater(
                abs(values[a][0] - values[b][0]), 1e-6,
                "%s and %s are optically equivalent here; the shape parameters "
                "must be chosen so the shapes can be told apart" % (a, b))

    def test_every_shape_survives_clone(self):
        for name in SHAPES:
            with self.subTest(shape=name):
                sim = build_patterned_slab(name)
                clone = sim.Clone()
                self.assertEqual(read_rt(sim, "Above", "Below"),
                                 read_rt(clone, "Above", "Below"))

    def test_shape_geometry_is_sampled_not_just_the_response(self):
        """Compare the permittivity field, which is independent of the solver."""
        for name in DISTINCT_SHAPES:
            with self.subTest(shape=name):
                sim = build_patterned_slab(name)
                clone = sim.Clone()
                pts = [(x, y, 0.25) for x in (-0.3, -0.1, 0.0, 0.1, 0.3)
                       for y in (-0.3, -0.1, 0.0, 0.1, 0.3)]
                self.assertEqual(_sample_epsilons(sim, pts),
                                 _sample_epsilons(clone, pts))

    def test_polygon_vertices_are_deep_copied(self):
        """Mutating one object's polygon must not disturb the other.

        The polygon vertex array is the only pattern allocation that is not
        inline, so it is the one that a shallow copy would share.
        """
        sim = build_patterned_slab("polygon")
        clone = sim.Clone()
        before = read_rt(clone, "Above", "Below")
        # Re-pattern the original with a different polygon.
        sim.RemoveLayerRegions("Slab")
        sim.SetRegionPolygon("Slab", "Air", (0.0, 0.0), 0,
                             ((0.0, 0.0), (0.45, 0.0), (0.45, 0.45), (0.0, 0.45)))
        after = read_rt(clone, "Above", "Below")
        self.assertAlmostEqual(before[0], after[0], delta=_TOL,
                               msg="editing the original changed the clone; the "
                                   "polygon vertices are shared")
        self.assertAlmostEqual(before[1], after[1], delta=_TOL)

    def test_unpatterned_layer_stays_unpatterned(self):
        sim = build_patterned_slab(None)
        clone = sim.Clone()
        self.assertEqual(_sample_epsilons(sim, [(0.0, 0.0, 0.25)]),
                         _sample_epsilons(clone, [(0.0, 0.0, 0.25)]))


class CloneIndependenceTests(unittest.TestCase):

    def test_clone_then_destroy_clone(self):
        sim = build_tensor_stack()
        clone = sim.Clone()
        expected = read_rt(sim, "Top", "Bot")
        del clone
        gc.collect()
        self.assertEqual(read_rt(sim, "Top", "Bot"), expected)

    def test_clone_then_destroy_original(self):
        clone = build_tensor_stack().Clone()
        expected = read_rt(clone, "Top", "Bot")
        gc.collect()
        self.assertEqual(read_rt(clone, "Top", "Bot"), expected)

    def test_destroy_original_first_then_use_clone(self):
        sim = build_patterned_slab("circle")
        clone = sim.Clone()
        expected = read_rt(clone, "Above", "Below")
        del sim
        gc.collect()
        self.assertEqual(read_rt(clone, "Above", "Below"), expected)

    def test_clone_is_usable_after_original_material_change(self):
        sim = build_scalar_stack()
        clone = sim.Clone()
        expected = read_rt(clone, "Top", "Bot")
        sim.SetMaterial("Si", 4.0)
        self.assertEqual(read_rt(clone, "Top", "Bot"), expected)
        self.assertNotEqual(read_rt(sim, "Top", "Bot"), expected)

    def test_clone_is_usable_after_original_frequency_change(self):
        sim = build_scalar_stack()
        clone = sim.Clone()
        expected = read_rt(clone, "Top", "Bot")
        sim.SetFrequency(0.9)
        self.assertEqual(read_rt(clone, "Top", "Bot"), expected)

    def test_original_is_usable_after_clone_modification(self):
        sim = build_scalar_stack()
        clone = sim.Clone()
        expected = read_rt(sim, "Top", "Bot")
        clone.SetMaterial("Si", 4.0)
        clone.SetFrequency(0.9)
        self.assertEqual(read_rt(sim, "Top", "Bot"), expected)

    def test_two_clones_are_independent(self):
        sim = build_scalar_stack()
        a = sim.Clone()
        b = sim.Clone()
        ref_a = read_rt(a, "Top", "Bot")
        ref_b = read_rt(b, "Top", "Bot")
        self.assertEqual(ref_a, ref_b)
        a.SetMaterial("Si", 3.0)
        self.assertEqual(read_rt(b, "Top", "Bot"), ref_b)
        self.assertNotEqual(read_rt(a, "Top", "Bot"), ref_a)

    def test_repeated_cloning_is_stable(self):
        """Cloning a clone must not degrade or leak into the chain."""
        sim = build_tensor_stack()
        expected = read_rt(sim, "Top", "Bot")
        current = sim
        for depth in range(4):
            current = current.Clone()
            with self.subTest(depth=depth + 1):
                self.assertEqual(read_rt(current, "Top", "Bot"), expected)

    def test_many_clones_do_not_corrupt_each_other(self):
        """Exercise allocator reuse, which is what exposed the original bug."""
        sim = build_patterned_slab("ellipse", num_basis=25)
        expected = read_rt(sim, "Above", "Below")
        clones = [sim.Clone() for _ in range(8)]
        for i, clone in enumerate(clones):
            with self.subTest(clone=i):
                self.assertEqual(read_rt(clone, "Above", "Below"), expected)
        # Release every other clone and keep the rest alive, so allocator
        # reuse is exercised while surviving clones are still in use.
        for i in range(0, len(clones), 2):
            clones[i] = None
            gc.collect()
        survivors = [c for c in clones if c is not None]
        self.assertTrue(survivors, "the loop above should have kept some clones")
        for clone in survivors:
            self.assertEqual(read_rt(clone, "Above", "Below"), expected)


class CloneIsolatedTests(unittest.TestCase):
    """The destructive scenarios, each in its own interpreter.

    These are the cases that used to abort the process.  Running them under
    isolation means a regression is reported as one failing test instead of
    destroying the remaining results, and the R/T comparison still happens --
    inside the child, where both objects are alive.
    """

    CASES = (
        "scalar_destroy_clone_first",
        "scalar_destroy_original_first",
        "tensor_destroy_clone_first",
        "tensor_destroy_original_first",
        "polygon_destroy_original_first",
        "clone_then_modify_frequency",
        "clone_then_modify_material",
        "many_clones_interleaved",
        "repeated_cloning_chain",
    )

    def _run(self, case):
        res = run_isolated(case, module="clone_isolation")
        self.assertNotEqual(
            res["verdict"], "crash",
            "isolated case %r aborted the interpreter (rc=%s, %s)"
            % (case, res["returncode"], res["stderr_tail"]))
        self.assertEqual(res["verdict"], "ok", res)
        return res

    def test_isolated_cases_are_all_registered(self):
        import clone_isolation
        missing = [c for c in self.CASES if c not in clone_isolation.CASES]
        self.assertEqual(missing, [], "unregistered isolation cases: %s" % missing)

    def test_isolated_clone_scenarios(self):
        for case in self.CASES:
            with self.subTest(case=case):
                self._run(case)


if __name__ == "__main__":
    unittest.main()
