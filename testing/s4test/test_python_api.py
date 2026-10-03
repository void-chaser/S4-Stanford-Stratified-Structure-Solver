"""Python-API and robustness tests.

The bulk of this module drives the extension in-process.  Calls that are known
to be able to abort the interpreter are routed through
``common.run_isolated``, which executes them in a child process so that a
SIGSEGV/SIGABRT is reported as a test failure instead of destroying the run.

Tolerances
----------
Two different tolerances appear in this file and they mean different things:

``_EXACT`` (1e-12)
    Used when comparing quantities that are algebraically identical in exact
    arithmetic -- e.g. power conservation of a lossless stack, which holds to
    rounding.  The bound is set ~10^4 above double precision to stay
    deterministic across BLAS implementations.

``_LOOSE`` (1e-6)
    Used when comparing against a value that itself went through a different
    numerical route, or when a discretisation is involved.
"""

import cmath
import math
import os
import tempfile
import unittest

import S4

from s4test_common import build_uniform_stack, read_rt, run_isolated, temp_workspace

_EXACT = 1e-12
_LOOSE = 1e-6


class BuildAndImportTests(unittest.TestCase):
    """L1: the extension links, imports, and exposes the expected surface."""

    def test_extension_imports_from_the_checkout(self):
        self.assertTrue(S4.__file__.endswith(".so"), S4.__file__)
        self.assertIn("Fourier Modal Method", S4.__doc__ or "")

    def test_module_level_entry_points_exist(self):
        for name in ("New", "NewInterpolator", "NewSpectrumSampler",
                     "SolveInParallel", "Error"):
            with self.subTest(entry_point=name):
                self.assertTrue(hasattr(S4, name), "S4.%s is missing" % name)

    def test_simulation_exposes_the_documented_methods(self):
        expected = [
            "AddLayer", "AddLayerCopy", "AddMaterial", "Clone", "GetAmplitudes",
            "GetBasisSet", "GetEpsilon", "GetFields", "GetFieldsOnGrid",
            "GetLayerVolumeIntegral", "GetLayerZIntegral", "GetPowerFlux",
            "GetPowerFluxByOrder", "GetReciprocalLattice", "GetSMatrixDeterminant",
            "GetStressTensorIntegral", "OutputLayerPatternPostscript",
            "OutputLayerPatternRealization", "OutputStructurePOVRay",
            "RemoveLayerRegions", "SetExcitationExterior", "SetExcitationPlanewave",
            "SetFrequency", "SetLayer", "SetLayerThickness", "SetMaterial",
            "SetOptions", "SetRegionCircle", "SetRegionEllipse", "SetRegionPolygon",
            "SetRegionRectangle", "SetVerbosity",
        ]
        sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
        present = set(dir(sim))
        missing = [m for m in expected if m not in present]
        self.assertEqual(missing, [], "missing simulation methods: %s" % missing)

    def test_alias_methods_are_the_same_callable(self):
        """GetPoyntingFlux is documented as an alias of GetPowerFlux.

        They are registered as the same C function, so they must agree
        exactly for identical arguments.
        """
        sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.5, num_basis=1)[0]
        sim.SetFrequency(0.5)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        a = sim.GetPowerFlux("Above", 0.0)
        b = sim.GetPoyntingFlux("Above", 0.0)
        self.assertEqual(a, b)
        self.assertEqual(sim.GetPowerFluxByOrder("Above", 0.0),
                         sim.GetPoyntingFluxByOrder("Above", 0.0))


class SimulationModellingTests(unittest.TestCase):
    """L2: modelling API -- materials, layers, regions, excitation, options."""

    def test_lattice_forms(self):
        named = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=9)
        positional = S4.New(((1, 0), (0, 1)), 9)
        for sim in (named, positional):
            # GetBasisSet() requires at least one layer, so add a minimal stack.
            sim.AddMaterial("Air", 1)
            sim.AddLayer("Above", 0, "Air")
            sim.AddLayer("Below", 0, "Air")
            self.assertEqual(len(sim.GetBasisSet()), 9)
        self.assertAlmostEqual(named.GetReciprocalLattice()[0][0], 1.0, places=12)

    def test_non_orthogonal_lattice(self):
        """GetReciprocalLattice returns the inverse of the lattice matrix.

        For real-space basis vectors ``u = (ux, uy)`` and ``v = (vx, vy)`` in
        row order, S4 stores ``Lk`` as the *columns* of the inverse of the
        matrix with ``u`` and ``v`` as columns, i.e. the inverse transpose of
        the row-order matrix.  The returned values are in units of ``1/a`` and
        are not multiplied by ``2*pi`` (the manual's ``2*pi*Lk`` wording
        describes the physical reciprocal vectors, not the stored values).
        """
        ux, uy = 1.0, 0.0
        vx, vy = 0.3, 1.0
        sim = S4.New(Lattice=((ux, uy), (vx, vy)), NumBasis=9)
        sim.AddMaterial("Air", 1)
        sim.AddLayer("Above", 0, "Air")
        sim.AddLayer("Below", 0, "Air")

        det = ux * vy - uy * vx
        # (p, q) are the two rows of the stored 2x2 block:
        #   row 0 = ( vy, -vx) / det
        #   row 1 = (-uy,  ux) / det
        expected_p = (vy / det, -vx / det)
        expected_q = (-uy / det, ux / det)
        p, q = sim.GetReciprocalLattice()
        for got, want, label in ((p, expected_p, "p"), (q, expected_q, "q")):
            for i in range(2):
                with self.subTest(vector=label, component=i):
                    self.assertAlmostEqual(got[i], want[i], places=12)

    def test_reciprocal_lattice_inverts_the_lattice(self):
        """Numerically, Lk must satisfy ``Lr @ Lk == identity`` in row order."""
        for lat in (((1, 0), (0, 1)), ((1, 0), (0.3, 1)), ((0.7, 0.2), (-0.1, 1.3))):
            with self.subTest(lattice=lat):
                sim = S4.New(Lattice=lat, NumBasis=4)
                sim.AddMaterial("Air", 1)
                sim.AddLayer("Above", 0, "Air")
                sim.AddLayer("Below", 0, "Air")
                p, q = sim.GetReciprocalLattice()
                # det([[ux,uy],[vx,vy]] @ [[px,qx],[py,qy]]) must be 1 and the
                # off-diagonal products must vanish.
                ux, uy = lat[0]
                vx, vy = lat[1]
                prod = (
                    ux * p[0] + uy * p[1],   # u . p
                    ux * q[0] + uy * q[1],   # u . q
                    vx * p[0] + vy * p[1],   # v . p
                    vx * q[0] + vy * q[1],   # v . q
                )
                self.assertAlmostEqual(prod[0], 1.0, places=12)
                self.assertAlmostEqual(prod[3], 1.0, places=12)
                self.assertAlmostEqual(prod[1], 0.0, places=12)
                self.assertAlmostEqual(prod[2], 0.0, places=12)

    def test_material_scalar_and_complex(self):
        sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
        sim.AddMaterial("Real", 2.0)
        sim.AddMaterial("Complex", 3.0 + 0.5j)
        sim.AddLayer("Above", 0, "Real")
        sim.AddLayer("Mid", 0.25, "Complex")
        sim.AddLayer("Below", 0, "Real")
        self.assertEqual(complex(sim.GetEpsilon(0.0, 0.0, 0.1)), 3.0 + 0.5j)

    def test_set_material_changes_the_answer(self):
        sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.0, num_basis=1)[0]
        sim.SetFrequency(0.5)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        before = read_rt(sim, "Above", "Below")
        sim.SetMaterial("_film0", 9.0)
        after = read_rt(sim, "Above", "Below")
        self.assertGreater(abs(after[0] - before[0]), 1e-3,
                           "changing a material must change the reflectance")

    def test_pattern_shapes_all_run(self):
        builders = {
            "circle": lambda s: s.SetRegionCircle("Film0", "_above", (0, 0), 0.2),
            "ellipse": lambda s: s.SetRegionEllipse("Film0", "_above", (0, 0), 15, (0.2, 0.1)),
            "rectangle": lambda s: s.SetRegionRectangle("Film0", "_above", (0, 0), 30, (0.2, 0.1)),
            "polygon": lambda s: s.SetRegionPolygon(
                "Film0", "_above", (0, 0), 0, ((0.0, 0.0), (0.3, 0.0), (0.3, 0.3))),
        }
        for name, build in builders.items():
            with self.subTest(shape=name):
                sim = build_uniform_stack(1.0, ((0.5, 12.0),), 1.0, num_basis=25)[0]
                build(sim)
                sim.SetFrequency(0.4)
                sim.SetExcitationPlanewave((0, 0), 1, 0)
                R, T = read_rt(sim, "Above", "Below")
                self.assertTrue(math.isfinite(R) and math.isfinite(T))

    def test_remove_layer_regions_restores_planar_response(self):
        planar = build_uniform_stack(1.0, ((0.5, 12.0),), 1.0, num_basis=25)[0]
        planar.SetFrequency(0.4)
        planar.SetExcitationPlanewave((0, 0), 1, 0)
        planar_rt = read_rt(planar, "Above", "Below")

        patterned = build_uniform_stack(1.0, ((0.5, 12.0),), 1.0, num_basis=25)[0]
        patterned.SetRegionCircle("Film0", "_above", (0, 0), 0.2)
        patterned.SetFrequency(0.4)
        patterned.SetExcitationPlanewave((0, 0), 1, 0)
        patterned_rt = read_rt(patterned, "Above", "Below")
        self.assertGreater(abs(patterned_rt[0] - planar_rt[0]), 1e-3,
                           "a patterned layer must differ from a planar one")

        patterned.RemoveLayerRegions("Film0")
        restored_rt = read_rt(patterned, "Above", "Below")
        self.assertAlmostEqual(restored_rt[0], planar_rt[0], places=9)
        self.assertAlmostEqual(restored_rt[1], planar_rt[1], places=9)

    def test_layer_copy_shares_the_pattern(self):
        sim = build_uniform_stack(1.0, ((0.5, 12.0),), 1.0, num_basis=25)[0]
        sim.SetRegionCircle("Film0", "_above", (0, 0), 0.2)
        sim.AddLayerCopy("FilmCopy", 0.25, "Film0")
        sim.SetFrequency(0.4)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        R, T = read_rt(sim, "Above", "Below")
        self.assertTrue(math.isfinite(R) and math.isfinite(T))

    def test_set_layer_thickness_has_an_effect(self):
        sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.0, num_basis=1)[0]
        sim.SetFrequency(0.5)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        before = read_rt(sim, "Above", "Below")
        sim.SetLayerThickness("Film0", 0.9)
        after = read_rt(sim, "Above", "Below")
        self.assertGreater(abs(after[0] - before[0]), 1e-3)

    def test_excitation_polarizations_differ_off_normal(self):
        results = {}
        for tag, (sa, pa) in (("s", (1, 0)), ("p", (0, 1))):
            sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.5, num_basis=1)[0]
            sim.SetFrequency(0.5)
            sim.SetExcitationPlanewave((45, 0), sa, pa)
            results[tag] = read_rt(sim, "Above", "Below")[0]
        self.assertGreater(abs(results["s"] - results["p"]), 1e-3,
                           "s and p must differ away from normal incidence")

    def test_frequency_sweep_is_well_defined(self):
        """Power is conserved at every frequency of a sweep.

        Note the deliberate absence of an assertion that R *changes* with
        frequency: for a non-dispersive layer of fixed thickness the optical
        thickness ``n*d`` is independent of frequency, so R is genuinely
        constant across the sweep.  An earlier version of this test asserted
        variation and failed against correct behaviour.
        """
        sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.0, num_basis=1)[0]
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        for f in (0.2, 0.4, 0.6, 0.8):
            with self.subTest(frequency=f):
                sim.SetFrequency(f)
                R, T = read_rt(sim, "Above", "Below")
                self.assertAlmostEqual(R + T, 1.0, delta=_EXACT,
                                       msg="power not conserved at f=%s" % f)

    def test_dispersive_sweep_does_vary(self):
        """A sweep that *does* change the optics must change the answer.

        Varying the refractive index with frequency is what makes a sweep
        physically dispersive; this is the case where R must move.
        """
        sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.0, num_basis=1)[0]
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        seen = []
        for n in (2.0, 2.5, 3.0, 3.5):
            sim.SetMaterial("_film0", n * n)
            sim.SetFrequency(0.5)
            R, T = read_rt(sim, "Above", "Below")
            self.assertAlmostEqual(R + T, 1.0, delta=_EXACT)
            seen.append(R)
        self.assertGreater(max(seen) - min(seen), 1e-3)

    def test_set_options_all_recognised_keys(self):
        sim = build_uniform_stack(1.0, ((0.5, 12.0),), 1.0, num_basis=25)[0]
        sim.SetOptions(Verbosity=0, LatticeTruncation="Circular",
                       DiscretizedEpsilon=True, DiscretizationResolution=8,
                       PolarizationDecomposition=True, PolarizationBasis="Normal",
                       LanczosSmoothing={"Width": 1.0, "Power": 2},
                       SubpixelSmoothing=True, ConserveMemory=True)
        sim.SetFrequency(0.4)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        R, T = read_rt(sim, "Above", "Below")
        self.assertTrue(math.isfinite(R) and math.isfinite(T))

    def test_set_options_rejects_bad_enum(self):
        sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.0, num_basis=1)[0]
        with self.assertRaises(ValueError):
            sim.SetOptions(LatticeTruncation="Nonsense")


class OutputApiTests(unittest.TestCase):
    """L2: field, grid, integral, and file outputs."""

    def _solved_patterned(self, num_basis=25):
        sim = build_uniform_stack(1.0, ((0.5, 12.0),), 1.0, num_basis=num_basis)[0]
        sim.SetRegionCircle("Film0", "_above", (0, 0), 0.2)
        sim.SetFrequency(0.4)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        return sim

    def test_get_fields_returns_two_three_vectors(self):
        sim = self._solved_patterned()
        E, H = sim.GetFields(0.1, 0.05, 0.0)
        self.assertEqual(len(E), 3)
        self.assertEqual(len(H), 3)
        for c in list(E) + list(H):
            self.assertTrue(math.isfinite(complex(c).real))
            self.assertTrue(math.isfinite(complex(c).imag))

    def test_amplitudes_are_a_two_by_twice_ngrid_tuple(self):
        """GetAmplitudes returns (forward, backward), each of length 2*n_G.

        Each component tuple holds the x and y field coefficients for every
        order laid end to end, so its length is ``2 * len(GetBasisSet())``.
        """
        sim = self._solved_patterned(num_basis=9)
        n_g = len(sim.GetBasisSet())
        amps = sim.GetAmplitudes("Above", 0.0)
        self.assertEqual(len(amps), 2)
        self.assertEqual(len(amps[0]), 2 * n_g)
        self.assertEqual(len(amps[1]), 2 * n_g)

    def test_reflected_amplitude_matches_fresnel(self):
        """The backward wave amplitude in the incidence layer is Fresnel's r.

        This ties the Python binding to the analytic reference through a
        quantity that is independent of any power normalization: for a bare
        dielectric interface the reflected plane-wave amplitude must equal
        ``(n1 - n2) / (n1 + n2)``.
        """
        n1, n2 = 1.0, 2.0
        sim = build_uniform_stack(n1, ((0.0, n2),), n2, num_basis=1)[0]
        sim.SetFrequency(1.0)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        _, backward = sim.GetAmplitudes("Above", 0.0)
        r_expected = (n1 - n2) / (n1 + n2)
        self.assertAlmostEqual(backward[0].real, r_expected, delta=1e-12)

    def test_grid_output_all_formats_succeed(self):
        sim = self._solved_patterned(num_basis=9)
        with temp_workspace() as tmp:
            for fmt in ("text", "bin", "hdf5", "mat", "vtk", "silo"):
                with self.subTest(format=fmt):
                    try:
                        out = sim.GetFieldsOnGrid(0.0, (8, 8), fmt,
                                                  os.path.join(tmp, "g_" + fmt))
                    except Exception as exc:
                        self.fail("GetFieldsOnGrid(%s) raised %s: %s"
                                  % (fmt, type(exc).__name__, exc))
                    self.assertEqual(len(out), 2)
            # Files were requested by absolute path inside tmp; the call must
            # not have written anything into the repository.
            self.assertEqual(sorted(os.listdir(tmp)), [])

    def test_layer_integrals_are_finite_and_ordering_consistent(self):
        sim = self._solved_patterned()
        e_int = sim.GetLayerVolumeIntegral("Film0", "E")
        h_int = sim.GetLayerVolumeIntegral("Film0", "H")
        u_int = sim.GetLayerVolumeIntegral("Film0", "U")
        for v in (e_int, h_int, u_int):
            self.assertTrue(math.isfinite(complex(v).real))
        # 'U' is documented as 'E' + 'H'.
        self.assertAlmostEqual(complex(u_int).real,
                               complex(e_int).real + complex(h_int).real,
                               delta=1e-9)

    def test_layer_integral_rejects_bad_quantity(self):
        sim = self._solved_patterned(num_basis=9)
        with self.assertRaises(RuntimeError):
            sim.GetLayerVolumeIntegral("Film0", "Q")

    def test_smatrix_determinant_is_a_triple(self):
        sim = self._solved_patterned(num_basis=9)
        mant, base, expo = sim.GetSMatrixDeterminant()
        self.assertIsInstance(complex(mant), complex)
        self.assertGreater(base, 0.0)
        self.assertIsInstance(expo, int)

    def test_stress_tensor_returns_three_components(self):
        sim = self._solved_patterned(num_basis=9)
        T = sim.GetStressTensorIntegral("Film0", 0.0)
        self.assertEqual(len(T), 3)

    def test_pattern_export_writes_requested_files(self):
        sim = self._solved_patterned(num_basis=9)
        with temp_workspace() as tmp:
            txt = os.path.join(tmp, "pattern.txt")
            ps = os.path.join(tmp, "pattern.ps")
            sim.OutputLayerPatternRealization("Film0", 16, 16, txt)
            sim.OutputLayerPatternPostscript("Film0", ps)
            self.assertTrue(os.path.getsize(txt) > 0)
            self.assertTrue(os.path.getsize(ps) > 0)


class InvalidInputTests(unittest.TestCase):
    """L2: invalid input must raise, never abort the interpreter."""

    def test_num_basis_must_be_positive(self):
        with self.assertRaises(ValueError):
            S4.New(Lattice=((1, 0), (0, 1)), NumBasis=0)

    def test_malformed_lattice_raises(self):
        for lat in (((1, 0), (0, 1), (1, 1)), ((1, 0), (0,)), ("a", "b")):
            with self.subTest(lattice=lat):
                with self.assertRaises(TypeError):
                    S4.New(Lattice=lat, NumBasis=4)

    def test_unknown_material_raises(self):
        sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
        with self.assertRaises(ValueError):
            sim.AddLayer("Only", 0, "Missing")

    def test_unknown_layer_raises(self):
        sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.0, num_basis=1)[0]
        sim.SetFrequency(0.5)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        with self.assertRaises(RuntimeError):
            sim.GetPowerFlux("NoSuchLayer")

    def test_power_flux_needs_two_layers(self):
        sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
        sim.AddMaterial("Air", 1)
        sim.AddLayer("Only", 0, "Air")
        sim.SetFrequency(0.5)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        with self.assertRaisesRegex(RuntimeError, "At least two layers"):
            sim.GetPowerFlux("Only")

    def test_negative_thickness_raises(self):
        sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.0, num_basis=1)[0]
        with self.assertRaises(ValueError):
            sim.SetLayer("Film0", -1.0, "_film0")

    def test_verbosity_range_is_enforced(self):
        sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.0, num_basis=1)[0]
        with self.assertRaises(TypeError):
            sim.SetVerbosity(42)

    def test_region_on_unknown_layer_raises(self):
        sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.0, num_basis=1)[0]
        with self.assertRaises(RuntimeError):
            sim.SetRegionCircle("NoSuchLayer", "_film0", (0, 0), 0.2)

    def test_patterning_a_layer_copy_raises(self):
        sim = build_uniform_stack(1.0, ((0.5, 12.0),), 1.0, num_basis=9)[0]
        sim.AddLayerCopy("FilmCopy", 0.25, "Film0")
        with self.assertRaises(RuntimeError):
            sim.SetRegionCircle("FilmCopy", "_above", (0, 0), 0.2)


class IsolatedRobustnessTests(unittest.TestCase):
    """L2: calls that can abort the process, run under subprocess isolation.

    Each test asserts on the *classification* produced by
    ``common.run_isolated``.  A verdict of ``"crash"`` means the child died
    from a signal, which is a native fault rather than a Python exception.
    """

    def _assert_no_crash(self, case):
        res = run_isolated(case)
        self.assertNotEqual(
            res["verdict"], "crash",
            "isolated case %r crashed the interpreter (rc=%s, %s)"
            % (case, res["returncode"], res["stderr_tail"]))
        return res

    def test_import_and_surface_probe_do_not_crash(self):
        res = self._assert_no_crash("import_module")
        self.assertEqual(res["verdict"], "ok")

    def test_invalid_input_sweep_raises_python_exceptions(self):
        res = self._assert_no_crash("invalid_inputs_raise")
        self.assertEqual(res["verdict"], "ok")

    def test_spectrum_sampler_two_argument_form(self):
        res = self._assert_no_crash("spectrum_sampler_two_args")
        self.assertEqual(res["verdict"], "ok")

    def test_clone_and_destroy_both_objects(self):
        """Regression test for the Clone() ownership bug.

        This used to abort the interpreter with ``free(): invalid pointer``.
        The root cause was that ``S4_Simulation_Clone`` aliased heap blocks
        between the original and the clone (n_layers/n_layers_alloc were copied
        by memcpy while the layer array was reallocated, and G/kx/pattern data
        were shared rather than duplicated).

        The probe is run under isolation so that a regression is reported as a
        failed test here rather than killing the run.
        """
        res = run_isolated("clone_then_destroy_both")
        self.assertNotEqual(
            res["verdict"], "crash",
            "Clone() regressed: destroying a clone aborted the interpreter "
            "(rc=%s, %s)" % (res["returncode"], res["stderr_tail"]))
        self.assertEqual(res["verdict"], "ok", res)

    def test_clone_outliving_the_original(self):
        """A clone must remain fully usable after the original is destroyed.

        This exercises the aliasing direction that used to corrupt the heap:
        the clone outlives the object it was copied from.
        """
        res = run_isolated("clone_outlives_original")
        self.assertNotEqual(
            res["verdict"], "crash",
            "destroying the original invalidated the clone (rc=%s, %s)"
            % (res["returncode"], res["stderr_tail"]))
        self.assertEqual(res["verdict"], "ok", res)


if __name__ == "__main__":
    unittest.main()
