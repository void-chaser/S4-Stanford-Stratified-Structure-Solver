"""Spectral sweeps on a single simulation object.

Why this test exists
--------------------
A sweep built by calling ``SetFrequency`` repeatedly on one object used to
return the *first* frequency's answer at every later point.  The binding
destroyed the solution but left the per-layer eigenmode cache
(``S4_Layer::modes``) in place, and those cached modes are frequency dependent.
Layer modes are only recomputed when ``L->modes`` is NULL, so the stale modes
were reused silently.

Measured before the fix, for a film with n = 2, d = 0.5 between vacuum and
vacuum (three layers, NumBasis = 1):

    ascending  sweep  T = 0.662784504 0.662784504 0.662784504 0.662784504 0.662784504
    descending sweep  T = 0.662784504 0.662784504 0.662784504 0.662784504 0.662784504
    analytic          T = 0.662784504 0.640000000 0.662784504 0.730908116 0.837283238

The descending sweep starts at f = 0.40, and its first point was correct while
every later point repeated it -- which is why the defect is order dependent and
was invisible to a test that builds a fresh object per frequency.

The expected values come from the closed-form Airy sum implemented in
``analytic.py``; nothing is copied from what S4 prints.  ``airy_rt`` is used
rather than ``tmm_rt`` because it is the numerically stable form, though for a
lossless film the two agree to 7e-16 (asserted in ``selftest_analytic.py``).

Tolerances
----------
1e-9  -- S4 against the independent analytic reference.  The two formulations
         are algebraically identical for a planar stack, so only floating-point
         accumulation differs; measured agreement after the fix is <= 1.1e-16.
         The bound is set ~10^7 above that to stay robust across BLAS kernels
         while still catching a stale-frequency error, which is order 1e-1.
1e-12 -- comparisons between two S4 runs (ascending vs descending vs fresh
         object).  These must agree to rounding; measured difference is exactly
         0.0 after the fix and 1.7e-1 before it.
"""

import unittest

import S4

from analytic import airy_rt

_ANALYTIC_TOL = 1e-9
_EXACT_TOL = 1e-12

_FREQS = (0.20, 0.25, 0.30, 0.35, 0.40)
_D = 0.5
_N_FILM = 2.0
_N_OUTER = 1.0


def _build(n_film=_N_FILM, d=_D, n_above=_N_OUTER, n_below=_N_OUTER):
    """Planar film.  Three layers are used because a two-layer (bare interface)
    stack exercises a separate code path; see test_two_layer_interface.py."""
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
    sim.AddMaterial("Above", complex(n_above) ** 2)
    sim.AddMaterial("Film", complex(n_film) ** 2)
    sim.AddMaterial("Below", complex(n_below) ** 2)
    sim.AddLayer("Above", 0, "Above")
    sim.AddLayer("Film", d, "Film")
    sim.AddLayer("Below", 0, "Below")
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    return sim


def _rt(sim):
    inc, refl = sim.GetPowerFlux("Above", 0.0)
    trans, _ = sim.GetPowerFlux("Below", 0.0)
    return -refl.real / inc.real, trans.real / inc.real


def _reference(freq):
    return airy_rt(_D, _N_FILM, _N_OUTER, _N_OUTER, 0.0, "s", freq)


class SweepRegressionTests(unittest.TestCase):

    def test_reference_is_non_degenerate(self):
        """Guard: if the analytic curve were flat, every test below would pass
        trivially and prove nothing."""
        trans = [_reference(f)[1] for f in _FREQS]
        self.assertGreater(max(trans) - min(trans), 1e-3,
                           "the chosen sweep does not vary; pick another")

    def test_fresh_object_per_frequency_matches_analytic(self):
        """Control case: this worked even before the fix."""
        for f in _FREQS:
            with self.subTest(frequency=f):
                sim = _build()
                sim.SetFrequency(f)
                R, T = _rt(sim)
                R_ref, T_ref = _reference(f)
                self.assertAlmostEqual(R, R_ref, delta=_ANALYTIC_TOL)
                self.assertAlmostEqual(T, T_ref, delta=_ANALYTIC_TOL)

    def test_ascending_sweep_on_one_object(self):
        sim = _build()
        for f in _FREQS:
            with self.subTest(frequency=f):
                sim.SetFrequency(f)
                R, T = _rt(sim)
                R_ref, T_ref = _reference(f)
                self.assertAlmostEqual(
                    R, R_ref, delta=_ANALYTIC_TOL,
                    msg="ascending sweep R at f=%.2f does not match analytic; a "
                        "stale eigenmode cache is the usual cause" % f)
                self.assertAlmostEqual(T, T_ref, delta=_ANALYTIC_TOL)

    def test_descending_sweep_on_one_object(self):
        sim = _build()
        for f in reversed(_FREQS):
            with self.subTest(frequency=f):
                sim.SetFrequency(f)
                R, T = _rt(sim)
                R_ref, T_ref = _reference(f)
                self.assertAlmostEqual(R, R_ref, delta=_ANALYTIC_TOL)
                self.assertAlmostEqual(T, T_ref, delta=_ANALYTIC_TOL)

    def test_ascending_equals_descending_equals_fresh(self):
        """Order independence, compared directly between S4 runs."""
        asc = {}
        sim = _build()
        for f in _FREQS:
            sim.SetFrequency(f)
            asc[f] = _rt(sim)

        desc = {}
        sim = _build()
        for f in reversed(_FREQS):
            sim.SetFrequency(f)
            desc[f] = _rt(sim)

        for f in _FREQS:
            with self.subTest(frequency=f):
                fresh = _build()
                fresh.SetFrequency(f)
                fresh_rt = _rt(fresh)
                self.assertAlmostEqual(asc[f][0], fresh_rt[0], delta=_EXACT_TOL,
                                       msg="ascending sweep differs from a fresh "
                                           "object at f=%.2f" % f)
                self.assertAlmostEqual(asc[f][1], fresh_rt[1], delta=_EXACT_TOL)
                self.assertAlmostEqual(asc[f][0], desc[f][0], delta=_EXACT_TOL,
                                       msg="sweep direction changes the result "
                                           "at f=%.2f" % f)
                self.assertAlmostEqual(asc[f][1], desc[f][1], delta=_EXACT_TOL)

    def test_repeating_a_frequency_is_idempotent(self):
        sim = _build()
        sim.SetFrequency(0.30)
        first = _rt(sim)
        for _ in range(3):
            sim.SetFrequency(0.30)
            self.assertAlmostEqual(_rt(sim)[0], first[0], delta=_EXACT_TOL)

    def test_returning_to_a_frequency_reproduces_it(self):
        """A round trip must land on the same answer, not a cached neighbour."""
        sim = _build()
        sim.SetFrequency(0.20)
        start = _rt(sim)
        for f in (0.40, 0.25, 0.35):
            sim.SetFrequency(f)
            _rt(sim)
        sim.SetFrequency(0.20)
        again = _rt(sim)
        self.assertAlmostEqual(again[0], start[0], delta=_EXACT_TOL)
        self.assertAlmostEqual(again[1], start[1], delta=_EXACT_TOL)

    def test_sweep_over_a_changing_material(self):
        """Change the material *and* the frequency between points."""
        sim = _build()
        for n, f in ((2.0, 0.20), (2.5, 0.25), (3.0, 0.30), (3.5, 0.35)):
            with self.subTest(n=n, frequency=f):
                sim.SetMaterial("Film", n * n)
                sim.SetFrequency(f)
                R, T = _rt(sim)
                R_ref, T_ref = airy_rt(_D, n, _N_OUTER, _N_OUTER, 0.0, "s", f)
                self.assertAlmostEqual(R, R_ref, delta=_ANALYTIC_TOL)
                self.assertAlmostEqual(T, T_ref, delta=_ANALYTIC_TOL)

    def test_energy_conserved_at_every_sweep_point(self):
        sim = _build()
        for f in _FREQS:
            with self.subTest(frequency=f):
                sim.SetFrequency(f)
                R, T = _rt(sim)
                self.assertAlmostEqual(R + T, 1.0, delta=1e-12)

    def test_oblique_sweep_both_polarizations(self):
        """The invalidation must also be complete for p polarisation."""
        for theta in (0.0, 30.0, 60.0):
            for pol, (sa, pa) in (("s", (1, 0)), ("p", (0, 1))):
                with self.subTest(theta=theta, polarization=pol):
                    sim = _build()
                    sim.SetExcitationPlanewave((theta, 0), sa, pa)
                    for f in _FREQS:
                        sim.SetFrequency(f)
                        inc, refl = sim.GetPowerFlux("Above", 0.0)
                        trans, _ = sim.GetPowerFlux("Below", 0.0)
                        R = -refl.real / inc.real
                        T = trans.real / inc.real
                        R_ref, T_ref = airy_rt(_D, _N_FILM, _N_OUTER, _N_OUTER,
                                               theta, pol, f)
                        self.assertAlmostEqual(R, R_ref, delta=_ANALYTIC_TOL)
                        self.assertAlmostEqual(T, T_ref, delta=_ANALYTIC_TOL)


class SetFrequencyWarningTests(unittest.TestCase):
    """The warning behaviour must survive the delegation to the C API."""

    def test_non_positive_frequency_warns(self):
        sim = _build()
        for bad in (0.0, -1.0):
            with self.subTest(frequency=bad):
                with self.assertWarns(RuntimeWarning):
                    sim.SetFrequency(bad)

    def test_positive_imaginary_part_warns(self):
        sim = _build()
        with self.assertWarns(RuntimeWarning):
            sim.SetFrequency(1.0 + 0.1j)

    def test_ordinary_frequency_does_not_warn(self):
        import warnings
        sim = _build()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sim.SetFrequency(0.5)
        self.assertEqual([w for w in caught
                          if issubclass(w.category, RuntimeWarning)], [])

    def test_complex_frequency_is_accepted(self):
        """A negative imaginary part is the physical lossy convention: no warn."""
        import warnings
        sim = _build()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            sim.SetFrequency(0.5 - 0.01j)
        self.assertEqual([w for w in caught
                          if issubclass(w.category, RuntimeWarning)], [])


if __name__ == "__main__":
    unittest.main()
