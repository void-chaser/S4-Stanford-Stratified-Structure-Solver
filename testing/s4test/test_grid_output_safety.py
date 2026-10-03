"""GetFieldsOnGrid resource management, error propagation and recovery.

Covers the paths the grid accessor can fail on: an invalid grid size, an output
file that cannot be opened or written, a core solve failure, a non-finite
result, and reuse of the same simulation object afterwards.

The pre-fix binding fails several of these: it returns NaN arrays and writes NaN
files, it raises SystemError for a negative size, it leaks three allocations per
failing call, and it crashes the interpreter (SIGSEGV through fprintf(NULL), and
SIGFPE/SIGSEGV for zero or out-of-range sizes).
"""

import math
import os
import tempfile
import unittest

import S4

ARRAY_FORMATS = ("text", "bin", "hdf5", "mat", "vtk", "silo")


def flat3(num_basis=9, frequency=0.999):
    """Air / spacer / glass.

    ``frequency = sqrt(2)`` puts a retained order exactly on a diffraction
    cutoff and makes the interface solve singular in every build we test;
    ``frequency = 1.0`` is singular in some optimisation levels only, so the
    tests below deliberately do not rely on it.
    """
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    sim.AddMaterial("Air", 1.0)
    sim.AddMaterial("Glass", 4.0)
    sim.AddLayer("Above", 0.0, "Air")
    sim.AddLayer("Spacer", 0.0, "Air")
    sim.AddLayer("Below", 0.5, "Glass")
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    sim.SetFrequency(frequency)
    return sim


def patterned(num_basis=9, frequency=0.999):
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    sim.AddMaterial("Air", 1.0)
    sim.AddMaterial("Glass", 4.0)
    sim.AddLayer("Above", 0.0, "Air")
    sim.AddLayer("Slab", 0.5, "Air")
    sim.SetRegionCircle("Slab", "Glass", (0.0, 0.0), 0.25)
    sim.AddLayer("Below", 0.0, "Air")
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    sim.SetFrequency(frequency)
    return sim


def zero_permittivity(frequency=0.5, num_basis=9):
    """A layer whose permittivity is exactly zero.

    Its longitudinal wavevector is then exactly zero, so the field on the grid
    is an exact 0/0 rather than an approximately singular value.  That makes the
    non-finite case reproducible at every optimisation level, unlike the
    ``f = 0.5`` glass case, which is only non-finite in some builds.
    """
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    sim.AddMaterial("Air", 1.0)
    sim.AddMaterial("Zero", 0.0)
    sim.AddLayer("Above", 0.0, "Air")
    sim.AddLayer("Spacer", 0.0, "Air")
    sim.AddLayer("Below", 0.5, "Zero")
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    sim.SetFrequency(frequency)
    return sim


def components(value):
    if isinstance(value, (tuple, list)):
        for item in value:
            for number in components(item):
                yield number
    else:
        yield value


class GridArrayTests(unittest.TestCase):
    def test_ordinary_grid_returns_finite_nested_arrays(self):
        sim = patterned()
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            out = sim.GetFieldsOnGrid(0.0, (4, 3), "text", os.path.join(tmp, "f"))
            self.assertEqual(os.listdir(tmp), [])
        self.assertIsInstance(out, tuple)
        self.assertEqual(len(out), 2)
        for field in out:
            self.assertEqual(len(field), 4)
            for column in field:
                self.assertEqual(len(column), 3)
                for cell in column:
                    self.assertEqual(len(cell), 3)
        numbers = list(components(out))
        self.assertEqual(len(numbers), 2 * 4 * 3 * 3)
        for number in numbers:
            self.assertIsInstance(number, complex)
            self.assertTrue(math.isfinite(number.real))
            self.assertTrue(math.isfinite(number.imag))

    def test_every_non_file_format_returns_arrays_and_writes_nothing(self):
        sim = patterned()
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            for fmt in ARRAY_FORMATS:
                with self.subTest(format=fmt):
                    out = sim.GetFieldsOnGrid(0.0, (2, 2), fmt, os.path.join(tmp, "g_" + fmt))
                    self.assertEqual(len(out), 2)
            self.assertEqual(os.listdir(tmp), [])

    def test_filewrite_writes_both_files_and_matches_the_array_result(self):
        sim = patterned()
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            arrays = sim.GetFieldsOnGrid(0.0, (2, 3), "text", os.path.join(tmp, "f"))
            result = sim.GetFieldsOnGrid(0.0, (2, 3), "FileWrite", os.path.join(tmp, "g"))
            self.assertIsNone(result)
            self.assertEqual(sorted(os.listdir(tmp)), ["g.E", "g.H"])
            for name, expected in (("g.E", arrays[0]), ("g.H", arrays[1])):
                with open(os.path.join(tmp, name)) as handle:
                    rows = [line for line in handle.read().split("\n") if line.strip()]
                self.assertEqual(len(rows), 2 * 3)
                for row in rows:
                    fields = row.split("\t")
                    self.assertEqual(len(fields), 8)
                    i, j = int(fields[0]), int(fields[1])
                    cell = expected[i][j]
                    for t in range(3):
                        self.assertAlmostEqual(float(fields[2 + 2 * t]), cell[t].real, places=12)
                        self.assertAlmostEqual(float(fields[3 + 2 * t]), cell[t].imag, places=12)

    def test_fileappend_keeps_existing_content_and_adds_the_z_column(self):
        sim = patterned()
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            base = os.path.join(tmp, "g")
            sim.GetFieldsOnGrid(0.0, (2, 2), "FileWrite", base)
            before = {}
            for name in sorted(os.listdir(tmp)):
                with open(os.path.join(tmp, name), "rb") as handle:
                    before[name] = handle.read()
            sim.GetFieldsOnGrid(0.25, (2, 2), "FileAppend", base)
            for name in sorted(os.listdir(tmp)):
                with open(os.path.join(tmp, name), "rb") as handle:
                    after = handle.read()
                self.assertTrue(after.startswith(before[name]),
                                "%s was not appended to" % name)
                self.assertGreater(len(after), len(before[name]))
                rows = [line for line in after[len(before[name]):].decode().split("\n")
                        if line.strip()]
                self.assertEqual(len(rows), 2 * 2)
                for row in rows:
                    fields = row.split("\t")
                    self.assertEqual(len(fields), 9)
                    self.assertAlmostEqual(float(fields[2]), 0.25, places=12)


class GridErrorTests(unittest.TestCase):
    def test_core_failure_propagates_and_writes_nothing(self):
        sim = flat3(frequency=math.sqrt(2.0))
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            for fmt in ("text", "FileWrite", "FileAppend"):
                with self.subTest(format=fmt):
                    with self.assertRaises(RuntimeError) as ctx:
                        sim.GetFieldsOnGrid(0.1, (4, 4), fmt, os.path.join(tmp, "f"))
                    self.assertIn("singular interface system", str(ctx.exception))
            self.assertEqual(os.listdir(tmp), [])

    def test_non_finite_grid_is_reported_not_returned_or_written(self):
        sim = zero_permittivity(frequency=0.5)
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            with self.assertRaises(RuntimeError) as ctx:
                sim.GetFieldsOnGrid(0.1, (4, 4), "text", os.path.join(tmp, "f"))
            self.assertIn("non-finite", str(ctx.exception))
            with self.assertRaises(RuntimeError) as ctx:
                sim.GetFieldsOnGrid(0.1, (4, 4), "FileWrite", os.path.join(tmp, "g"))
            self.assertIn("non-finite", str(ctx.exception))
            self.assertEqual(os.listdir(tmp), [])

    def test_unwritable_output_path_raises_instead_of_crashing(self):
        sim = patterned()
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            missing = os.path.join(tmp, "no_such_dir", "g")
            with self.assertRaises(OSError) as ctx:
                sim.GetFieldsOnGrid(0.0, (2, 2), "FileWrite", missing)
            self.assertIn("g.E", str(ctx.exception))
            os.mkdir(os.path.join(tmp, "d.E"))
            os.mkdir(os.path.join(tmp, "d.H"))
            with self.assertRaises(OSError) as ctx:
                sim.GetFieldsOnGrid(0.0, (2, 2), "FileWrite", os.path.join(tmp, "d"))
            self.assertIn("d.E", str(ctx.exception))

    def test_invalid_num_samples_is_rejected(self):
        sim = patterned()
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            for samples in ((0, 8), (8, 0), (-1, 8), (8, -1)):
                with self.subTest(num_samples=samples):
                    with self.assertRaises(ValueError):
                        sim.GetFieldsOnGrid(0.0, samples, "text", os.path.join(tmp, "f"))
            with self.subTest(num_samples="2**40"):
                with self.assertRaises(ValueError):
                    sim.GetFieldsOnGrid(0.0, (2 ** 40, 2), "text", os.path.join(tmp, "f"))
            # A product that cannot be sized has to be refused before allocating.
            with self.subTest(num_samples="INT_MAX squared"):
                with self.assertRaises((OverflowError, ValueError, MemoryError)):
                    sim.GetFieldsOnGrid(0.0, (2 ** 31 - 1, 2 ** 31 - 1), "text",
                                        os.path.join(tmp, "f"))
            self.assertEqual(os.listdir(tmp), [])

    def test_object_is_reusable_after_a_grid_failure(self):
        sim = flat3(frequency=math.sqrt(2.0))
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            with self.assertRaises(RuntimeError):
                sim.GetFieldsOnGrid(0.1, (4, 4), "text", os.path.join(tmp, "f"))
            sim.SetFrequency(0.999)
            out = sim.GetFieldsOnGrid(0.05, (3, 2), "text", os.path.join(tmp, "f"))
            for number in components(out):
                self.assertTrue(math.isfinite(number.real))
                self.assertTrue(math.isfinite(number.imag))
            self.assertIsNone(
                sim.GetFieldsOnGrid(0.05, (3, 2), "FileWrite", os.path.join(tmp, "g")))
            self.assertEqual(sorted(os.listdir(tmp)), ["g.E", "g.H"])

    def test_repeated_failures_keep_raising(self):
        sim = flat3(frequency=math.sqrt(2.0))
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            for _ in range(50):
                with self.assertRaises(RuntimeError):
                    sim.GetFieldsOnGrid(0.1, (4, 4), "text", os.path.join(tmp, "f"))
            self.assertEqual(os.listdir(tmp), [])


class GridPartialFileTests(unittest.TestCase):
    """The two files are written one after the other, with no rollback."""

    def test_full_device_raises_for_both_write_modes_and_object_survives(self):
        if not os.path.exists("/dev/full"):
            self.skipTest("/dev/full is not available on this host")
        sim = patterned()
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            base = os.path.join(tmp, "full")
            # The E file cannot accept the data; the write or the close fails.
            os.symlink("/dev/full", base + ".E")
            for fmt in ("FileWrite", "FileAppend"):
                with self.subTest(format=fmt):
                    with self.assertRaises(OSError) as ctx:
                        sim.GetFieldsOnGrid(0.0, (2, 2), fmt, base)
                    self.assertIn(base + ".E", str(ctx.exception))
            # The object is still usable for an ordinary array call.
            out = sim.GetFieldsOnGrid(0.0, (2, 2), "text", os.path.join(tmp, "f"))
            self.assertEqual(len(out), 2)

    def test_second_file_failure_keeps_the_first_and_object_survives(self):
        sim = patterned()
        with tempfile.TemporaryDirectory(prefix="s4grid-") as tmp:
            base = os.path.join(tmp, "partial")
            # Make only the H destination impossible, so E is written first.
            os.mkdir(base + ".H")
            with self.assertRaises(OSError) as ctx:
                sim.GetFieldsOnGrid(0.0, (2, 2), "FileWrite", base)
            self.assertIn(base + ".H", str(ctx.exception))
            # Declared semantics: E was written before H failed and is not rolled
            # back, so it is present and non-empty.
            self.assertTrue(os.path.isfile(base + ".E"))
            self.assertGreater(os.path.getsize(base + ".E"), 0)
            out = sim.GetFieldsOnGrid(0.0, (2, 2), "text", os.path.join(tmp, "f"))
            self.assertEqual(len(out), 2)

if __name__ == "__main__":
    unittest.main()
