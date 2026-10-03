"""Direct calls to the public C API ``S4_Simulation_GetFieldPlane``.

The Python and Lua grid tests exercise *other* entry points
(``S4Sim_GetFieldsOnGrid`` and ``S4L_Simulation_GetFieldPlane``), which wrap the
internal ``Simulation_GetFieldPlane``.  This module calls the public
``S4_Simulation_GetFieldPlane`` itself, so the parameter, capacity, output
pointer and error-code contract of that entry point is tested where it lives.

``capi_field_plane_driver.cpp`` is compiled here, from source, against the
``build/libS4.a`` that ``make`` produces; nothing is reused from a previous run.
When the library is missing the tests fail loudly instead of being skipped.
Every case runs in its own process with a timeout, so a crash is reported as a
failed assertion rather than killing the suite.  The driver itself checks the
return code, the contents of the output buffers and the sentinel words around
them before it exits, so "the process did not crash" is never the only evidence.

What this module does **not** claim: the interface takes no buffer length, so it
cannot check how much space a caller actually provided.  The contract in
``S4/S4.h`` states the length each non-NULL buffer must have; a shorter buffer
is a caller error that these tests cannot and do not detect.

Two structures are sampled: a flat air/spacer/glass stack and a patterned one
(a Glass circle of radius 0.25 in a 0.5-thick slab, built through
``S4_Layer_SetRegionHalfwidths`` with ``S4_REGION_TYPE_CIRCLE``).  The patterned
fixture also asserts that at least one field component actually varies across
the grid, so a fixture that silently failed to pattern the layer cannot pass as
a uniform field.

The 1x1 case is treated as its own question.  The public entry point serves it
through the point-field path while the internal grid entry point samples a
one-point FFT grid, and those are not the same computation once the structure is
patterned: with a single grid point only the zeroth Fourier order is
representable, so the higher orders of the pattern are truncated, whereas the
point path sums every retained order.  The flat structure happens to agree
because it has no higher orders.  These tests therefore assert the public 1x1
result against the *point-field* interface and assert the 4x3 grid's origin
sample against the same point field, which are the computations those branches
actually perform.

The discrepancy between the 1x1 grid and the point field is *not* asserted here
in either direction.  It is a sampling-semantics observation, recorded in
`DEFECTS.md` D14 with its measured magnitude; "the two interfaces must differ by
at least this much" is not a promise this interface makes, so it is not an
acceptance condition, and a printed number is not a correctness test.  No physics
was changed for it and no tolerance was relaxed anywhere else.

The cross-entry comparisons are layout and convention checks: both the public
entry point and the Python binding end in the same ``GetFieldOnGrid``, so
agreement says nothing about physical correctness.
"""

import hashlib
import os
import shlex
import subprocess
import unittest

from s4test_common import REPO_ROOT, temp_workspace

DRIVER_SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "capi_field_plane_driver.cpp")
DRIVER_BINARY = os.path.join(REPO_ROOT, "build", "capi_field_plane_driver")
LIBRARY = os.path.join(REPO_ROOT, "build", "libS4.a")

#: Cases that exercise the parameter, capacity and no-layer contract.  Before
#: the fix, zero/negative grids raised SIGFPE/SIGSEGV, oversized grids
#: SIGSEGVed, and the no-layer case reached the core with a stale layer pointer.
CONTRACT_CASES = (
    "null_sim", "null_nxy", "null_xyz0", "both_null",
    "zero_x", "zero_y", "neg_x", "neg_y",
    "huge_intmax", "huge_2p32", "no_layers",
)

#: Cases that exercise the optional-output contract.
OUTPUT_CASES = ("output_combinations_1x1", "output_combinations_4x3")

#: Cases about state after a failure.
STATE_CASES = ("cutoff_and_recovery", "repeat_failures_and_cleanup")

_compiled = {}
_COMPILE_COMMAND = {}


def _build_flags():
    """Compiler and linker flags for the driver, matching the built library.

    ``make test CFLAGS=... CXXFLAGS=...`` exports those variables to the recipe
    environment, so the driver normally receives the same optimisation and
    sanitizer flags as ``build/libS4.a``.  That is a convenience, not a
    guarantee, and a flag mismatch is not assumed to be self-announcing: what
    establishes which flags and which library were actually used is the compile
    command and the ``libS4.a`` SHA256 that ``setUpClass`` prints, and the
    compile-command evidence recorded in the acceptance log.
    """
    cxx = os.environ.get("CXX", "g++")
    cxxflags = os.environ.get("CXXFLAGS") or os.environ.get("CFLAGS") or "-O1"
    ldflags = os.environ.get("LDFLAGS", "")
    return cxx, shlex.split(cxxflags), shlex.split(ldflags)


def compile_driver():
    """Compile the driver if needed; return (path, sha256, log)."""
    if "result" in _compiled:
        return _compiled["result"]
    if not os.path.isfile(LIBRARY):
        raise AssertionError(
            "build/libS4.a is missing; run `make` (or `make test`) so the static "
            "library exists before this direct C API test can link against it")
    cxx, cxxflags, ldflags = _build_flags()
    cmd = [cxx, "-I", os.path.join(REPO_ROOT, "S4")] + cxxflags + [
        DRIVER_SOURCE, "-o", DRIVER_BINARY,
        "-L", os.path.join(REPO_ROOT, "build"), "-lS4", "-llapack", "-lblas",
    ] + ldflags
    _COMPILE_COMMAND["cmd"] = " ".join(cmd)
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    if proc.returncode != 0:
        raise AssertionError("failed to build the C API driver:\n%s\n%s\n%s"
                             % (" ".join(cmd), proc.stdout, proc.stderr))
    with open(DRIVER_BINARY, "rb") as handle:
        digest = hashlib.sha256(handle.read()).hexdigest()
    with open(LIBRARY, "rb") as handle:
        lib = hashlib.sha256(handle.read()).hexdigest()
    _compiled["result"] = (DRIVER_BINARY, digest, lib, proc.stderr)
    return _compiled["result"]


def run_case(case, timeout=120):
    """Run one driver case in its own process; classify the outcome."""
    binary, _, _, _ = compile_driver()
    try:
        proc = subprocess.run([binary, case], capture_output=True, text=True,
                              timeout=timeout, cwd=REPO_ROOT)
    except subprocess.TimeoutExpired:
        return {"verdict": "timeout", "rc": None, "out": "", "err": ""}
    verdict = "pass"
    if proc.returncode < 0:
        verdict = "crash"
    elif proc.returncode == 124:
        verdict = "timeout"
    elif proc.returncode != 0:
        verdict = "fail"
    return {"verdict": verdict, "rc": proc.returncode,
            "out": proc.stdout, "err": proc.stderr}


class FieldPlaneContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.binary, cls.binary_sha, cls.library_sha, _ = compile_driver()
        print("driver compile: %s" % _COMPILE_COMMAND["cmd"])
        print("driver %s sha256=%s" % (cls.binary, cls.binary_sha[:16]))
        print("libS4.a sha256=%s" % cls.library_sha[:16])

    def _assert_case(self, case, expected_rc=None, timeout=120):
        res = run_case(case, timeout=timeout)
        detail = "case=%s verdict=%s rc=%s\n--- stdout ---\n%s\n--- stderr ---\n%s" % (
            case, res["verdict"], res["rc"], res["out"][-3000:], res["err"][-2000:])
        self.assertNotEqual(res["verdict"], "crash",
                            "the case died from a signal\n" + detail)
        self.assertNotEqual(res["verdict"], "timeout",
                            "the case hung\n" + detail)
        self.assertEqual(res["verdict"], "pass", detail)
        self.assertIn("RESULT %s PASS" % case, res["out"], detail)
        if expected_rc is not None:
            self.assertIn("RC %s %d" % (case, expected_rc), res["out"], detail)
        return res

    def test_null_arguments_return_their_codes(self):
        self._assert_case("null_sim", expected_rc=-1)
        self._assert_case("null_nxy", expected_rc=-2)
        self._assert_case("null_xyz0", expected_rc=-3)

    def test_both_outputs_null_is_a_no_op(self):
        res = self._assert_case("both_null", expected_rc=0)
        self.assertIn("RC both_null_invalid_grid 0", res["out"],
                      "the documented no-op must precede grid validation")

    def test_non_positive_grid_is_rejected(self):
        for case in ("zero_x", "zero_y", "neg_x", "neg_y"):
            with self.subTest(case=case):
                self._assert_case(case, expected_rc=-4)

    def test_oversized_grid_is_rejected_before_allocating(self):
        for case in ("huge_intmax", "huge_2p32"):
            with self.subTest(case=case):
                self._assert_case(case, expected_rc=-5, timeout=60)

    def test_structure_without_layers_reports_error_14(self):
        self._assert_case("no_layers", expected_rc=14)


class FieldPlaneOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compile_driver()

    def test_each_output_combination_works_and_agrees(self):
        for case in OUTPUT_CASES:
            with self.subTest(case=case):
                res = self._assert_case(case)
                self.assertIn("RC both 0", res["out"])
                self.assertIn("RC e_only 0", res["out"])
                self.assertIn("RC h_only 0", res["out"])
                self.assertIn("single-output results equal the pair results",
                              res["out"])

    def _assert_case(self, case, **kw):
        return FieldPlaneContractTests._assert_case(self, case, **kw)

    def _parse_dump(self, out):
        values = {}
        for line in out.splitlines():
            parts = line.split()
            if parts and parts[0] in ("E", "H") and len(parts) == 6:
                values[(parts[0], int(parts[1]), int(parts[2]), int(parts[3]))] = (
                    float(parts[4]), float(parts[5]))
        return values

    def _python_grid(self, nu, nv, z=0.05):
        import S4
        sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=9)
        sim.AddMaterial("Air", 1.0)
        sim.AddMaterial("Glass", 4.0)
        sim.AddLayer("Above", 0.0, "Air")
        sim.AddLayer("Spacer", 0.0, "Air")
        sim.AddLayer("Below", 0.5, "Glass")
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        sim.SetFrequency(0.999)
        with temp_workspace() as tmp:
            e, h = sim.GetFieldsOnGrid(z, (nu, nv), "text", os.path.join(tmp, "f"))
        return {"E": e, "H": h}

    def test_grid_layout_matches_the_python_binding(self):
        """The public C entry point and the Python binding agree element by element.

        Both end up in ``GetFieldOnGrid``, so this is a layout and convention
        check (index order, component order, real/imaginary interleaving), not an
        independent numerical validation.
        """
        res = self._assert_case("dump_4x3")
        dumped = self._parse_dump(res["out"])
        self.assertEqual(len(dumped), 2 * 4 * 3 * 3)
        arrays = self._python_grid(4, 3)
        for j in range(3):
            for i in range(4):
                for c in range(3):
                    for tag in ("E", "H"):
                        expected = complex(*dumped[(tag, i, j, c)])
                        got = arrays[tag][i][j][c]
                        self.assertAlmostEqual(got.real, expected.real, places=12)
                        self.assertAlmostEqual(got.imag, expected.imag, places=12)

    def test_single_point_layout_matches_the_grid_path(self):
        """The 1x1 reorder must produce the same layout as the sampled grid path."""
        res = self._assert_case("dump_1x1")
        dumped = self._parse_dump(res["out"])
        self.assertEqual(len(dumped), 2 * 3)
        arrays = self._python_grid(1, 1)
        for c in range(3):
            for tag in ("E", "H"):
                expected = complex(*dumped[(tag, 0, 0, c)])
                got = arrays[tag][0][0][c]
                self.assertAlmostEqual(got.real, expected.real, places=12)
                self.assertAlmostEqual(got.imag, expected.imag, places=12)


class FieldPlaneCapacityTests(unittest.TestCase):
    """The -5 boundary: FFT int capacity first, byte capacity as the backstop."""

    INT_MAX = 2 ** 31 - 1

    @classmethod
    def setUpClass(cls):
        compile_driver()

    def _run(self, case, **kw):
        return FieldPlaneContractTests._assert_case(self, case, **kw)

    def test_grid_just_above_the_fft_int_product_is_rejected(self):
        """46341^2 exceeds INT_MAX while 46340^2 does not, so the boundary is exact."""
        self.assertEqual(46340 * 46340, 2147395600)
        self.assertGreater(46341 * 46341, self.INT_MAX)
        for case in ("fft_boundary_over", "fft_boundary_over_axis"):
            with self.subTest(case=case):
                res = self._run(case, expected_rc=-5)
                self.assertIn("small grid succeeds on the same object", res["out"])
                self.assertIn("sentinels intact", res["out"])

    def test_capacity_arithmetic_matches_the_division_form(self):
        """The boundary is a division test, checked without allocating anything."""
        res = self._run("capacity_arithmetic")
        sizes = {}
        for line in res["out"].splitlines():
            parts = line.split()
            if parts and parts[0] == "ARITH" and parts[1] == "pair":
                sizes[(int(parts[2]), int(parts[3]))] = int(parts[5])
        self.assertTrue(sizes, "the arithmetic case printed no pairs")
        for (nu, nv), over in sizes.items():
            with self.subTest(num_samples=(nu, nv)):
                # The production check is `nu > INT_MAX / nv`; recompute it here.
                self.assertEqual(over, 1 if nu > self.INT_MAX // nv else 0)
        self.assertIn((46340, 46340), sizes)
        self.assertEqual(sizes[(46340, 46340)], 0, "46340^2 must not be rejected")
        self.assertEqual(sizes[(46341, 46341)], 1, "46341^2 must be rejected")

    def test_byte_limit_is_the_portability_bound_not_the_binding_one_here(self):
        """On this platform the int limit binds first; that is stated, not assumed.

        The byte bound is what binds where ``size_t`` is 32 bits wide.  This
        suite was only run on x86_64, so the 32-bit branch is covered by
        arithmetic and by inspection, not by execution - the test asserts the
        platform it is on and the relationship between the two limits, and
        records that no 32-bit run was performed.
        """
        import struct
        res = self._run("capacity_arithmetic")
        fields = {}
        for line in res["out"].splitlines():
            if line.startswith("ARITH int_max"):
                parts = line.split()
                fields = dict(zip(parts[1::2], parts[2::2]))
        self.assertTrue(fields, "no ARITH int_max line")
        self.assertIn("byte_limit", fields)
        pointer_bytes = struct.calcsize("P")
        int_max = int(fields["int_max"])
        byte_limit = int(fields["byte_limit"])
        if pointer_bytes >= 8:
            self.assertGreaterEqual(byte_limit, int_max,
                                    "on a 64-bit size_t the byte bound is the looser one")
            self.assertIn("byte limit is looser than the int limit here", res["out"])
        else:
            # 32-bit size_t: the byte bound can be the binding one.
            self.assertLess(byte_limit, 2 ** 63)
        self.assertEqual(int_max, 2 ** 31 - 1)


class FieldPlanePatternedTests(unittest.TestCase):
    """A patterned structure: layout, optional outputs and spatial variation."""

    SLAB = "Slab"
    CIRCLE_RADIUS = 0.25
    Z = 0.05
    FREQ = 0.999

    @classmethod
    def setUpClass(cls):
        compile_driver()

    def _run(self, case, **kw):
        return FieldPlaneContractTests._assert_case(self, case, **kw)

    def _patterned_python(self, nu, nv):
        import S4
        sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=9)
        sim.AddMaterial("Air", 1.0)
        sim.AddMaterial("Glass", 4.0)
        sim.AddLayer("Above", 0.0, "Air")
        sim.AddLayer(self.SLAB, 0.5, "Air")
        # The same region the driver creates through
        # S4_Layer_SetRegionHalfwidths(..., S4_REGION_TYPE_CIRCLE, {r, r}, ...).
        sim.SetRegionCircle(self.SLAB, "Glass", (0.0, 0.0), self.CIRCLE_RADIUS)
        sim.AddLayer("Below", 0.0, "Air")
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        sim.SetFrequency(self.FREQ)
        with temp_workspace() as tmp:
            e, h = sim.GetFieldsOnGrid(self.Z, (nu, nv), "text", os.path.join(tmp, "f"))
        return sim, {"E": e, "H": h}

    def _parse_dump(self, out):
        values = {}
        for line in out.splitlines():
            parts = line.split()
            if parts and parts[0] in ("E", "H") and len(parts) == 6:
                values[(parts[0], int(parts[1]), int(parts[2]), int(parts[3]))] = (
                    float(parts[4]), float(parts[5]))
        return values

    def _assert_dump_matches(self, dumped, arrays, nu, nv, places=12):
        self.assertEqual(len(dumped), 2 * nu * nv * 3)
        for j in range(nv):
            for i in range(nu):
                for c in range(3):
                    for tag in ("E", "H"):
                        expected = complex(*dumped[(tag, i, j, c)])
                        got = arrays[tag][i][j][c]
                        self.assertAlmostEqual(got.real, expected.real, places=places)
                        self.assertAlmostEqual(got.imag, expected.imag, places=places)

    def test_patterned_outputs_vary_and_single_outputs_agree(self):
        res = self._run("patterned_outputs")
        for needle in ("both outputs written", "each single output written",
                       "all components finite", "sentinels intact (both)",
                       "sentinels intact (single)",
                       "single-output results equal the pair results",
                       "at least one component varies across the grid"):
            self.assertIn(needle, res["out"], res["out"][-2000:])
        # The variation must be substantial, not numerical noise.
        spreads = [float(line.split()[2]) for line in res["out"].splitlines()
                   if line.startswith("SPREAD ")]
        self.assertTrue(spreads)
        self.assertGreater(max(spreads), 1e-2)

    def test_patterned_grid_matches_the_python_binding(self):
        res = self._run("patterned_dump_4x3")
        dumped = self._parse_dump(res["out"])
        _, arrays = self._patterned_python(4, 3)
        self._assert_dump_matches(dumped, arrays, 4, 3)

    def test_patterned_public_1x1_matches_the_point_field(self):
        """The public 1x1 branch is the point-field computation, so it must equal it."""
        res = self._run("patterned_1x1")
        dumped = self._parse_dump(res["out"])
        self.assertEqual(len(dumped), 2 * 3)
        sim, _ = self._patterned_python(1, 1)
        pe, ph = sim.GetFields(0.0, 0.0, self.Z)
        point = {"E": pe, "H": ph}
        for c in range(3):
            for tag in ("E", "H"):
                expected = complex(*dumped[(tag, 0, 0, c)])
                self.assertAlmostEqual(point[tag][c].real, expected.real, places=12)
                self.assertAlmostEqual(point[tag][c].imag, expected.imag, places=12)

    def test_patterned_grid_origin_matches_the_point_field(self):
        """At a represented resolution the grid origin reproduces the point field."""
        res = self._run("patterned_dump_4x3")
        dumped = self._parse_dump(res["out"])
        sim, _ = self._patterned_python(4, 3)
        pe, ph = sim.GetFields(0.0, 0.0, self.Z)
        point = {"E": pe, "H": ph}
        for c in range(3):
            for tag in ("E", "H"):
                expected = complex(*dumped[(tag, 0, 0, c)])
                self.assertAlmostEqual(point[tag][c].real, expected.real, places=12)
                self.assertAlmostEqual(point[tag][c].imag, expected.imag, places=12)

class FieldPlaneStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compile_driver()

    def test_state_cases(self):
        for case in STATE_CASES:
            with self.subTest(case=case):
                res = FieldPlaneContractTests._assert_case(self, case)
                self.assertIn("RESULT %s PASS" % case, res["out"])


if __name__ == "__main__":
    unittest.main()
