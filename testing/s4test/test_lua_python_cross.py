"""Lua/Python cross-frontend consistency checks.

Purpose
-------
Python and Lua are two frontends onto the *same* C++ core, so agreement between
them is an **interface consistency** check: it detects binding-level mistakes
(argument order, units, pattern setup, sign handling) but says nothing about
whether the numbers are physically right.  Physical correctness is established
separately by ``test_analytic_reference.py``.

The two frontends do not present the same sign convention for power:
``S:GetPoyntingFlux`` in Lua returns the net signed flux, whereas the Python
binding returns the ``(forward, backward)`` pair.  Comparison is therefore done
on ``T`` and ``R`` normalised by the incident power, computed inside each
language by its own mirror script.

Prerequisites
-------------
The Lua frontend must be built (``make`` produces ``build/S4``) and the Lua
examples must be present.  When ``build/S4`` is absent the tests fail loudly
rather than skipping, because a silently skipped cross-check is indistinguishable
from a passing one.
"""

import os
import unittest

from s4test_common import HERE
from lua_frontend import (lua_binary, run_lua_example, run_python_script)

#: Agreement tolerance.  Both frontends call the same core with the same
#: parameters, so the only permitted difference is double rounding in the
#: normalisation step; 1e-10 leaves ample margin while still catching a genuine
#: sign, unit, or index error (which shows up at order 1e-1 or larger).
_TOL = 1e-10

_LUA_MIRROR = os.path.join(HERE, "mirror_fig12.lua")
_PY_MIRROR = os.path.join(HERE, "mirror_fig12.py")


class Fig12CrossFrontendTests(unittest.TestCase):
    """Fan & Joannopoulos PRB 65, 235112 (2002) Fig. 12 — photonic crystal slab."""

    @classmethod
    def setUpClass(cls):
        if lua_binary() is None:
            raise AssertionError(
                "the Lua frontend is not built; `make` must produce build/S4 "
                "before this cross-check can run")
        cls.lua_rc, cls.lua_rows, cls.lua_err = run_lua_example(_LUA_MIRROR)
        cls.py_rc, cls.py_rows, cls.py_err = run_python_script(_PY_MIRROR)

    def test_lua_mirror_ran(self):
        self.assertEqual(self.lua_rc, 0, "Lua frontend failed:\n%s" % self.lua_err)
        self.assertTrue(self.lua_rows, "Lua frontend produced no numeric output")

    def test_python_mirror_ran(self):
        self.assertEqual(self.py_rc, 0, "Python mirror failed:\n%s" % self.py_err)
        self.assertTrue(self.py_rows, "Python mirror produced no numeric output")

    def test_same_number_of_frequencies(self):
        self.assertEqual(len(self.lua_rows), len(self.py_rows))
        self.assertEqual(len(self.lua_rows), 7,
                         "the 0.25..0.27 step 0.003 sweep should give 7 points")

    def test_transmission_and_reflection_agree(self):
        for lua_row, py_row in zip(self.lua_rows, self.py_rows):
            f_lua, t_lua, r_lua = lua_row
            f_py, t_py, r_py = py_row
            with self.subTest(frequency=f_lua):
                self.assertAlmostEqual(f_lua, f_py, delta=1e-12)
                self.assertAlmostEqual(t_lua, t_py, delta=_TOL,
                                       msg="T differs between frontends")
                self.assertAlmostEqual(r_lua, r_py, delta=_TOL,
                                       msg="R differs between frontends")

    def test_both_frontends_conserve_energy(self):
        """Independent of each other, both must satisfy R + T == 1."""
        for tag, rows in (("lua", self.lua_rows), ("python", self.py_rows)):
            for row in rows:
                with self.subTest(frontend=tag, frequency=row[0]):
                    self.assertAlmostEqual(row[1] + row[2], 1.0, delta=1e-9)

    def test_reflectance_has_a_guided_resonance_feature(self):
        """The sweep must show structure, not a flat line.

        Fig. 12 of the paper is a transmission spectrum across a guided
        resonance, so T must vary appreciably over this window.  This is a
        sanity check that the sweep is not degenerate.
        """
        trans = [row[1] for row in self.py_rows]
        self.assertGreater(max(trans) - min(trans), 0.05,
                           "transmission is nearly flat; the sweep or the "
                           "patterning is probably not being applied")


class ShippedExampleStillRunsTests(unittest.TestCase):
    """The unmodified shipped example must run and stay energy conserving.

    This is deliberately separate from the mirror comparison: it checks that the
    example as committed is not broken, using the example's own output format.
    """

    def test_fig12_lua_example_runs(self):
        rc, rows, err = run_lua_example("examples/2d/Fan_PRB_65_2002/fig12.lua")
        self.assertEqual(rc, 0, "shipped example failed:\n%s" % err)
        self.assertEqual(len(rows), 7)
        # The shipped example prints freq, forward, backward with backward < 0.
        for freq, forward, backward in rows:
            with self.subTest(frequency=freq):
                self.assertAlmostEqual(forward - backward, 1.0, delta=1e-9,
                                       msg="shipped example is not energy conserving")


if __name__ == "__main__":
    unittest.main()
