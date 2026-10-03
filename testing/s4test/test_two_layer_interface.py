"""Two-layer bare interface: the degenerate single-interface stack.

A stack of exactly two layers models one semi-infinite medium above and another
below, i.e. a single planar interface.  For n1 = 1, n2 = 2 at normal incidence
the exact answer is

    r = (n1 - n2) / (n1 + n2) = -1/3
    R = r^2   = 1/9  = 0.111111111111...
    T = 1 - R = 8/9  = 0.888888888888...

Everything here is driven by the independent analytic reference in
``analytic.py``; no expected value is copied from what S4 happens to print.

The same physics is also checked through the three-layer route (a layer of zero
thickness inserted between the two media), which is algebraically identical.
Agreement between the two routes localises any discrepancy to the two-layer
degeneracy rather than to the solver mathematics as a whole.

The Lua frontend is exercised as well, because the failure is not necessarily
specific to the Python binding: ``examples/0d/fabry_perot/fresnel.lua`` in this
repository is exactly this configuration.
"""

import math
import os
import subprocess
import unittest

import S4

from analytic import fresnel_rt
from lua_frontend import lua_binary, parse_tsv
from s4test_common import HERE, REPO_ROOT

_TOL = 1e-12

#: Tolerance used when the analytic reference itself crosses a different
#: numerical route (the Lua frontend normalises by its own incident flux).
_LUA_TOL = 1e-9


def _two_layer(n_above, n_below):
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
    sim.AddMaterial("Above", complex(n_above) ** 2)
    sim.AddMaterial("Below", complex(n_below) ** 2)
    sim.AddLayer("Above", 0, "Above")
    sim.AddLayer("Below", 0, "Below")
    return sim


def _three_layer_spacer(n_above, n_below, spacer_n, spacer_d=0.0):
    """Algebraically the same single interface, expressed with three layers."""
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
    sim.AddMaterial("Above", complex(n_above) ** 2)
    sim.AddMaterial("Spacer", complex(spacer_n) ** 2)
    sim.AddMaterial("Below", complex(n_below) ** 2)
    sim.AddLayer("Above", 0, "Above")
    sim.AddLayer("Spacer", spacer_d, "Spacer")
    sim.AddLayer("Below", 0, "Below")
    return sim


def _rt(sim, theta_deg=0.0, polarization="s"):
    sim.SetFrequency(1.0)
    sim.SetExcitationPlanewave((theta_deg, 0),
                               1 if polarization == "s" else 0,
                               0 if polarization == "s" else 1)
    inc, refl = sim.GetPowerFlux("Above", 0.0)
    trans, _ = sim.GetPowerFlux("Below", 0.0)
    if inc.real == 0.0:
        raise AssertionError("incident power is zero")
    return -refl.real / inc.real, trans.real / inc.real


class TwoLayerBareInterfaceTests(unittest.TestCase):
    """The analytic answer for a bare interface, driven from analytic.py."""

    def test_normal_incidence_n1_to_n2(self):
        R_ref, T_ref = fresnel_rt(1.0, 2.0, 0.0, "s")
        # The analytic reference itself must give the textbook values, otherwise
        # this test would encode whatever the reference happens to do.
        self.assertAlmostEqual(R_ref, 1.0 / 9.0, delta=1e-15)
        self.assertAlmostEqual(T_ref, 8.0 / 9.0, delta=1e-15)

        R, T = _rt(_two_layer(1.0, 2.0))
        self.assertAlmostEqual(R, R_ref, delta=_TOL,
                               msg="two-layer R must equal %r, got %r" % (R_ref, R))
        self.assertAlmostEqual(T, T_ref, delta=_TOL,
                               msg="two-layer T must equal %r, got %r" % (T_ref, T))

    def test_incident_power_is_nonzero(self):
        """A zero incident flux is the signature of this defect.

        Separated from the R/T test so the failure message names the root
        symptom rather than only the ratio.
        """
        sim = _two_layer(1.0, 2.0)
        sim.SetFrequency(1.0)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        inc, refl = sim.GetPowerFlux("Above", 0.0)
        trans, _ = sim.GetPowerFlux("Below", 0.0)
        self.assertGreater(abs(inc.real), 1e-12,
                           "the incident flux must be non-zero")
        self.assertGreater(abs(refl.real) + abs(trans.real), 1e-12,
                           "the interface must reflect or transmit something; "
                           "both fluxes are identically zero")

    def test_normal_incidence_various_contrasts(self):
        for n2 in (1.5, 2.0, 3.5, 4.0):
            with self.subTest(n2=n2):
                R_ref, T_ref = fresnel_rt(1.0, n2, 0.0, "s")
                R, T = _rt(_two_layer(1.0, n2))
                self.assertAlmostEqual(R, R_ref, delta=_TOL)
                self.assertAlmostEqual(T, T_ref, delta=_TOL)

    def test_oblique_incidence_both_polarizations(self):
        for n2 in (1.5, 2.0, 3.5):
            for theta in (0.0, 15.0, 30.0, 45.0, 60.0):
                for pol, (sa, pa) in (("s", (1, 0)), ("p", (0, 1))):
                    with self.subTest(n2=n2, theta=theta, polarization=pol):
                        R_ref, T_ref = fresnel_rt(1.0, n2, theta, pol)
                        R, T = _rt(_two_layer(1.0, n2), theta, pol)
                        self.assertAlmostEqual(R, R_ref, delta=_TOL)
                        self.assertAlmostEqual(T, T_ref, delta=_TOL)

    def test_match_vacuum_has_no_reflection(self):
        """n1 == n2 must give R = 0 and T = 1; there is no interface at all."""
        R, T = _rt(_two_layer(2.0, 2.0))
        self.assertAlmostEqual(R, 0.0, delta=1e-14)
        self.assertAlmostEqual(T, 1.0, delta=1e-14)


class ThreeLayerEquivalenceTests(unittest.TestCase):
    """The three-layer route must reproduce the two-layer answer.

    This is the localisation tool: a mismatch between the two routes proves the
    problem is the two-layer degeneracy, whereas a shared mismatch would point
    at the solver as a whole.
    """

    def test_zero_thickness_spacer_matches_two_layer(self):
        for n2 in (1.5, 2.0, 3.5):
            with self.subTest(n2=n2):
                R_two, T_two = _rt(_two_layer(1.0, n2))
                R_three, T_three = _rt(_three_layer_spacer(1.0, n2, 1.0, 0.0))
                self.assertAlmostEqual(R_two, R_three, delta=_TOL,
                                       msg="the two-layer and three-layer routes "
                                           "disagree; the two-layer case is the "
                                           "suspect one")
                self.assertAlmostEqual(T_two, T_three, delta=_TOL)

    def test_three_layer_route_matches_analytic(self):
        """Establish that the three-layer route is the correct one."""
        for n2 in (1.5, 2.0, 3.5):
            with self.subTest(n2=n2):
                R_ref, T_ref = fresnel_rt(1.0, n2, 0.0, "s")
                R, T = _rt(_three_layer_spacer(1.0, n2, 1.0, 0.0))
                self.assertAlmostEqual(R, R_ref, delta=_TOL)
                self.assertAlmostEqual(T, T_ref, delta=_TOL)

    def test_spacer_refractive_index_is_irrelevant_at_zero_thickness(self):
        """With d = 0 the spacer cannot affect the optics, whatever its index."""
        base = _rt(_three_layer_spacer(1.0, 2.0, 1.0, 0.0))
        for spacer_n in (1.5, 3.0, 12.0):
            with self.subTest(spacer_n=spacer_n):
                other = _rt(_three_layer_spacer(1.0, 2.0, spacer_n, 0.0))
                self.assertAlmostEqual(base[0], other[0], delta=_TOL)
                self.assertAlmostEqual(base[1], other[1], delta=_TOL)


_LUA_PROBE = os.path.join(HERE, "probe_two_layer.lua")


class TwoLayerLuaFrontendTests(unittest.TestCase):
    """The same two-layer geometry through the Lua frontend.

    Included because the defect is not guaranteed to be Python-specific, and
    because ``examples/0d/fabry_perot/fresnel.lua`` in this repository uses
    exactly this configuration.
    """

    @classmethod
    def setUpClass(cls):
        if lua_binary() is None:
            raise AssertionError("the Lua frontend is not built; `make` must "
                                 "produce build/S4 before this test can run")
        if not os.path.isfile(_LUA_PROBE):
            raise AssertionError("missing Lua probe: %s" % _LUA_PROBE)

    def _run(self):
        proc = subprocess.run([lua_binary(), _LUA_PROBE], capture_output=True,
                              text=True, timeout=120, cwd=REPO_ROOT)
        return proc.returncode, parse_tsv(proc.stdout), proc.stderr

    def test_lua_two_layer_matches_analytic(self):
        """The Lua probe columns are n_exit, R, T -- not freq, R, T.

        probe_two_layer.lua sweeps the exit refractive index at normal incidence,
        so the first column is the index. It previously printed the literal 1.0
        there, which this test happened to read as "freq = 1" and pass by
        coincidence. The probe now prints the real index, and the row is matched
        on it.
        """
        rc, rows, err = self._run()
        self.assertEqual(rc, 0, "Lua probe failed:\n%s" % err)
        self.assertTrue(rows, "Lua probe produced no numeric output")
        seen = {}
        for row in rows:
            # n_exit, R, T
            seen[row[0]] = (row[1], row[2])
        self.assertIn(2.0, seen,
                      "expected a row for n_exit = 2.0; got keys %r"
                      % (sorted(seen),))
        R, T = seen[2.0]
        R_ref, T_ref = fresnel_rt(1.0, 2.0, 0.0, "s")
        self.assertAlmostEqual(R, R_ref, delta=_LUA_TOL,
                               msg="Lua frontend R does not match Fresnel")
        self.assertAlmostEqual(T, T_ref, delta=_LUA_TOL,
                               msg="Lua frontend T does not match Fresnel")

    def test_shipped_fresnel_example_is_not_all_zero(self):
        """The repository's own example must produce non-zero power.

        It is listed in testing/testcases.txt, so a silent all-zero output means
        a shipped example has been broken without anyone noticing.
        """
        example = os.path.join(REPO_ROOT,
                               "examples/0d/fabry_perot/fresnel.lua")
        self.assertTrue(os.path.isfile(example), example)
        proc = subprocess.run([lua_binary(), example], capture_output=True,
                              text=True, timeout=300, cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        rows = parse_tsv(proc.stdout)
        self.assertTrue(rows, "the shipped example produced no numeric output")
        # Columns are forward1 backward1 forward2 backward2, all normalised by
        # the incident power, so the first row at 0 degrees must be non-trivial.
        first = rows[0]
        self.assertGreater(
            max(abs(v) for v in first[1:]), 1e-9,
            "the shipped Fresnel example returned all zeros at normal "
            "incidence; this is the two-layer bare-interface defect")


if __name__ == "__main__":
    unittest.main()
