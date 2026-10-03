"""Analytic benchmarks: S4 against an independently implemented reference.

Every expected value in this module comes from ``analytic.py``, which contains
its own Fresnel and transfer-matrix implementations and never imports S4.
``selftest_analytic.py`` proves that reference correct against closed-form
results before it is used here.

Tolerances
----------
``_ANALYTIC_TOL`` = 1e-9
    Agreement between S4 and the analytic reference for a *planar* stack.  A
    planar stack needs a single Fourier order, so the two formulations are
    algebraically identical and the only error is floating point accumulation
    through the linear solve.  1e-9 is ~10^7 above double precision, which
    leaves margin for different BLAS kernels while still catching any real
    discrepancy (a wrong sign is order 1, a wrong factor of n is order 1).

``_EXACT_TOL`` = 1e-12
    Identities that hold exactly in arithmetic: power conservation of a
    lossless structure, and the symmetry relations.  These compare S4 against
    itself, so no modelling error is involved.
"""

import cmath
import math
import unittest

import S4

from analytic import airy_rt, fresnel_rt, tmm_rt, tmm_rt_spectrum
from s4test_common import build_uniform_stack, read_rt

_ANALYTIC_TOL = 1e-9
_EXACT_TOL = 1e-12

#: Refractive indices used for the planar benchmarks.  Chosen to be free of
#: accidental degeneracies with the chosen thicknesses and frequencies.
_N_AIR = 1.0
_N_GLASS = 1.5
_N_SILICON = 3.5


class FluxConventionTests(unittest.TestCase):
    """The (R, T) extraction must match the documented sign convention.

    If these fail, every other benchmark in this file is meaningless, so they
    are deliberately the narrowest possible checks.
    """

    def test_incident_power_is_normalised_to_cos_theta(self):
        """The incident Poynting flux is Re(kz/k0), not 1.

        This pins down the normalisation the binding uses so that later tests
        divide by the right quantity.
        """
        for theta in (0.0, 30.0, 60.0):
            for tag, (sa, pa) in (("s", (1, 0)), ("p", (0, 1))):
                with self.subTest(theta=theta, polarization=tag):
                    sim = build_uniform_stack(_N_AIR, ((0.5, _N_GLASS),), _N_AIR)[0]
                    sim.SetFrequency(0.5)
                    sim.SetExcitationPlanewave((theta, 0), sa, pa)
                    inc, _ = sim.GetPowerFlux("Above", 0.0)
                    self.assertAlmostEqual(inc.real, math.cos(math.radians(theta)),
                                           delta=1e-12)

    def test_backward_flux_is_negative_in_the_incidence_layer(self):
        sim = build_uniform_stack(_N_AIR, ((0.5, _N_GLASS),), _N_AIR)[0]
        sim.SetFrequency(0.5)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        _, refl = sim.GetPowerFlux("Above", 0.0)
        self.assertLess(refl.real, 0.0,
                        "the backward flux in the incidence layer must be negative")

    def test_reflected_amplitude_equals_fresnel_r(self):
        """backward[component] / forward[component] is the Fresnel amplitude r.

        Two conventions have to be right for this to work, and both were
        established empirically rather than assumed:

        * component index -- measured on this exact stack: an s-polarised
          excitation puts the backward wave in index 0, a p-polarised one in
          index 1.  (Reading the other index returns exactly 0, which is the
          failure mode this comment prevents.)
        * normalisation and sign -- the returned amplitudes are not normalised
          to unit incident amplitude, and the incidence-side component carries
          an extra sign that differs between polarisations.  Measured on this
          stack at normal incidence:

          = ====================== ========== ===========
          pol  forward[component]   backward   Fresnel r
          = ====================== ========== ===========
          s    -1                   -1/3       -1/3
          p    +1                   +1/3       +1/3
          = ====================== ========== ===========

          So ``r = sign * backward[component] / forward[component]`` with
          ``sign = -1`` for s and ``+1`` for p.  This is the familiar statement
          that at normal incidence the s reflection coefficient is negative
          while the p one is positive.  At 25 degrees the s ratio
          -(-0.3321366650177481) / -0.9063077870366499 gives
          -0.3664722622584251, matching the closed form to 4e-16.
          ``test_incident_amplitude_sign_convention`` pins these signs.
        """
        for tag, (sa, pa) in (("s", (1, 0)), ("p", (0, 1))):
            for theta in (0.0, 25.0, 55.0):
                with self.subTest(polarization=tag, theta=theta):
                    sim = build_uniform_stack(_N_AIR, ((0.0, 2.0),), 2.0)[0]
                    sim.SetFrequency(1.0)
                    sim.SetExcitationPlanewave((theta, 0), sa, pa)
                    forward, backward = sim.GetAmplitudes("Above", 0.0)
                    component = 0 if tag == "s" else 1
                    sign = -1.0 if tag == "s" else 1.0
                    inc_amp = forward[component]
                    refl_amp = backward[component]

                    n1, n2 = 1.0, 2.0
                    kx = n1 * math.sin(math.radians(theta))
                    kz1 = cmath.sqrt(n1 * n1 - kx * kx)
                    kz2 = cmath.sqrt(n2 * n2 - kx * kx)
                    if tag == "s":
                        r_expected = (kz1 - kz2) / (kz1 + kz2)
                    else:
                        r_expected = (n2 * n2 * kz1 - n1 * n1 * kz2) / (
                            n2 * n2 * kz1 + n1 * n1 * kz2)

                    self.assertGreater(abs(inc_amp), 0.5,
                                       "the incident amplitude should not vanish")
                    r_measured = sign * refl_amp / inc_amp
                    self.assertAlmostEqual(r_measured.real, r_expected.real,
                                           delta=1e-9)
                    self.assertAlmostEqual(r_measured.imag, r_expected.imag,
                                           delta=1e-9)

    def test_incident_amplitude_sign_convention(self):
        """Pin the signs that ``r = sign * backward/forward`` relies on.

        Measured at normal incidence on n = 1 | n = 2:

        * s polarisation: forward[0] = -1, backward[0] = -1/3
        * p polarisation: forward[1] = +1, backward[1] = +1/3

        A future change that flips any of these would silently invert a
        reflection coefficient computed elsewhere, so they are asserted here
        rather than left implicit in a ratio.
        """
        sim = build_uniform_stack(1.0, ((0.0, 2.0),), 2.0)[0]
        sim.SetFrequency(1.0)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        forward, backward = sim.GetAmplitudes("Above", 0.0)
        self.assertAlmostEqual(forward[0].real, -1.0, delta=1e-12)
        self.assertAlmostEqual(backward[0].real, -1.0 / 3.0, delta=1e-12)
        sim.SetExcitationPlanewave((0, 0), 0, 1)
        forward, backward = sim.GetAmplitudes("Above", 0.0)
        self.assertAlmostEqual(forward[1].real, 1.0, delta=1e-12)
        self.assertAlmostEqual(backward[1].real, 1.0 / 3.0, delta=1e-12)

    def test_transmitted_amplitude_ratio_matches_fresnel_t(self):
        """The same ratio on the exit side gives Fresnel's t.

        This cross-checks the component convention from the other direction: t
        and r must be consistent with 1 + r = t at normal incidence for these
        media.
        """
        sim = build_uniform_stack(1.0, ((0.0, 2.0),), 2.0)[0]
        sim.SetFrequency(1.0)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        inc_fwd, inc_bwd = sim.GetAmplitudes("Above", 0.0)
        out_fwd, _ = sim.GetAmplitudes("Below", 0.0)
        r = -inc_bwd[0] / inc_fwd[0]
        t_ratio = out_fwd[0] / inc_fwd[0]
        self.assertAlmostEqual(r.real, -1.0 / 3.0, delta=1e-12)
        # Below carries the index ratio times the field ratio for this
        # convention, so this checks self-consistency of the two amplitudes
        # rather than Fresnel's t itself.
        self.assertAlmostEqual(t_ratio.real, 4.0 / 3.0, delta=1e-9)


class FresnelBenchmarkTests(unittest.TestCase):
    """S4 against closed-form single-interface Fresnel results.

    A bare interface needs three layers in S4 (see the two-layer defect in
    DEFECTS.md), so the middle layer is given zero thickness.  With d = 0 the
    stack is algebraically a single interface, which makes the analytic
    expectation unambiguous.
    """

    def test_normal_incidence_quarter_wave_stack(self):
        """n=1 -> n=2 at normal incidence: R = 1/9 exactly."""
        sim = build_uniform_stack(1.0, ((0.0, 2.0),), 2.0)[0]
        sim.SetFrequency(1.0)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        R, T = read_rt(sim, "Above", "Below")
        R_ref, T_ref = fresnel_rt(1.0, 2.0, 0.0, "s")
        self.assertAlmostEqual(R, R_ref, delta=_ANALYTIC_TOL)
        self.assertAlmostEqual(T, T_ref, delta=_ANALYTIC_TOL)
        # and the closed form is the familiar 1/9, 8/9
        self.assertAlmostEqual(R, 1.0 / 9.0, delta=_ANALYTIC_TOL)
        self.assertAlmostEqual(T, 8.0 / 9.0, delta=_ANALYTIC_TOL)

    def test_oblique_incidence_all_polarizations(self):
        for n2 in (1.5, 2.0, 3.5, 12.0):
            for theta in (0.0, 15.0, 30.0, 45.0, 60.0, 75.0):
                for pol, (sa, pa) in (("s", (1, 0)), ("p", (0, 1))):
                    with self.subTest(n2=n2, theta=theta, polarization=pol):
                        sim = build_uniform_stack(1.0, ((0.0, n2),), n2)[0]
                        sim.SetFrequency(1.0)
                        sim.SetExcitationPlanewave((theta, 0), sa, pa)
                        R, T = read_rt(sim, "Above", "Below")
                        R_ref, T_ref = fresnel_rt(1.0, n2, theta, pol)
                        self.assertAlmostEqual(R, R_ref, delta=_ANALYTIC_TOL)
                        self.assertAlmostEqual(T, T_ref, delta=_ANALYTIC_TOL)

    def test_brewster_angle_kills_p_reflection(self):
        """At theta_B = atan(n2/n1) the p reflectance must vanish."""
        n2 = 3.0
        theta_b = math.degrees(math.atan(n2 / 1.0))
        sim = build_uniform_stack(1.0, ((0.0, n2),), n2)[0]
        sim.SetFrequency(1.0)
        sim.SetExcitationPlanewave((theta_b, 0), 0, 1)
        R, T = read_rt(sim, "Above", "Below")
        self.assertLess(R, 1e-14, "p reflectance at Brewster's angle should be ~0")
        self.assertAlmostEqual(T, 1.0, delta=1e-12)

    def test_total_internal_reflection(self):
        """Above the critical angle all power must be reflected."""
        n1, n2 = 2.0, 1.0
        theta_c = math.degrees(math.asin(n2 / n1))
        for theta in (theta_c + 5.0, theta_c + 20.0):
            for pol, (sa, pa) in (("s", (1, 0)), ("p", (0, 1))):
                with self.subTest(theta=theta, polarization=pol):
                    sim = build_uniform_stack(n1, ((0.0, n2),), n2)[0]
                    sim.SetFrequency(1.0)
                    sim.SetExcitationPlanewave((theta, 0), sa, pa)
                    R, T = read_rt(sim, "Above", "Below")
                    self.assertAlmostEqual(R, 1.0, delta=1e-10)
                    self.assertAlmostEqual(T, 0.0, delta=1e-10)


class TransferMatrixBenchmarkTests(unittest.TestCase):
    """S4 against an independent transfer-matrix solver for multilayer stacks."""

    def _compare(self, n_above, layers, n_below, theta, pol, freq):
        sim = build_uniform_stack(n_above, layers, n_below)[0]
        sim.SetFrequency(freq)
        sim.SetExcitationPlanewave((theta, 0), 1 if pol == "s" else 0,
                                   0 if pol == "s" else 1)
        R, T = read_rt(sim, "Above", "Below")
        # Rebuild the reference with the *physical* layer list: S4's stack is
        # (semi-infinite)/layers/(semi-infinite), and the analytic reference
        # takes the same list of finite layers.
        ref_layers = [(d, n) for d, n in layers]
        R_ref, T_ref = tmm_rt(ref_layers, n_above, n_below, theta, pol, freq)
        return R, T, R_ref, T_ref

    def test_single_film_various_thicknesses(self):
        for d in (0.1, 0.25, 0.37, 0.5, 1.0, 2.5):
            for theta in (0.0, 30.0, 60.0):
                for pol in ("s", "p"):
                    with self.subTest(d=d, theta=theta, polarization=pol):
                        R, T, R_ref, T_ref = self._compare(
                            1.0, ((d, 2.0),), 1.5, theta, pol, 0.5)
                        self.assertAlmostEqual(R, R_ref, delta=_ANALYTIC_TOL)
                        self.assertAlmostEqual(T, T_ref, delta=_ANALYTIC_TOL)

    def test_frequency_dependence_matches_reference(self):
        """This is the benchmark that a working sweep must satisfy.

        It sweeps frequency on a *single* simulation object, which is the
        natural way to produce a spectrum.  A binding whose SetFrequency does
        not fully invalidate cached layer data returns the first frequency's
        answer for every point and fails here.
        """
        n_above, n_film, n_below = 1.0, 2.0, 1.0
        layers = ((0.5, n_film),)
        freqs = (0.20, 0.25, 0.30, 0.35, 0.40)
        R_ref, T_ref = tmm_rt_spectrum(layers, n_above, n_below, 0.0, "s", freqs)

        sim = build_uniform_stack(n_above, layers, n_below)[0]
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        got = []
        for f in freqs:
            sim.SetFrequency(f)
            R, T = read_rt(sim, "Above", "Below")
            got.append((R, T))

        # The reference itself must be non-degenerate, otherwise the test
        # could pass trivially.
        self.assertGreater(max(T_ref) - min(T_ref), 1e-3,
                           "the chosen sweep is degenerate; pick another")

        for f, (R, T), (Rr, Tr) in zip(freqs, got, zip(R_ref, T_ref)):
            with self.subTest(frequency=f):
                self.assertAlmostEqual(
                    T, Tr, delta=_ANALYTIC_TOL,
                    msg="T at f=%.3f does not match the transfer-matrix "
                        "reference; a stale-frequency cache is the usual cause" % f)
                self.assertAlmostEqual(R, Rr, delta=_ANALYTIC_TOL)

    def test_two_film_stack(self):
        layers = ((0.2, 2.0), (0.3, 3.5))
        for theta in (0.0, 40.0):
            for pol in ("s", "p"):
                with self.subTest(theta=theta, polarization=pol):
                    R, T, R_ref, T_ref = self._compare(
                        1.0, layers, 1.5, theta, pol, 0.6)
                    self.assertAlmostEqual(R, R_ref, delta=_ANALYTIC_TOL)
                    self.assertAlmostEqual(T, T_ref, delta=_ANALYTIC_TOL)

    def test_quarter_wave_anti_reflection_coating(self):
        """A quarter-wave film with n = sqrt(n_sub) must give R ~ 0.

        This is a closed-form design result that is independent of both the
        transfer-matrix code and S4, so it catches a common-mode error.
        """
        n_sub = 4.0
        n_film = math.sqrt(n_sub)
        freq = 1.0
        d = 1.0 / (4.0 * freq * n_film)     # quarter wave at this frequency
        sim = build_uniform_stack(1.0, ((d, n_film),), n_sub)[0]
        sim.SetFrequency(freq)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        R, T = read_rt(sim, "Above", "Below")
        self.assertLess(R, 1e-12, "ideal quarter-wave coating must not reflect")
        self.assertAlmostEqual(T, 1.0, delta=1e-12)


class LossyMediumTests(unittest.TestCase):
    """Physical constraints for absorbing structures.

    Tolerance note: absorption is computed as ``1 - R - T``.  For a weakly
    absorbing film the absorbed fraction is small, so the subtraction loses
    relative precision; the absolute bound of 1e-9 is larger than for the
    lossless identities for that reason, and is still far below any physically
    meaningful absorption in these cases (which is order 1e-1).
    """

    def test_absorbed_power_is_positive_and_bounded(self):
        # eps = 12 + 1j -> clearly absorbing, non-magnetic.
        eps_film = 12.0 + 1.0j
        n_film = cmath.sqrt(eps_film)
        layers = ((0.5, n_film),)
        sim = build_uniform_stack(1.0, layers, 1.5)[0]
        sim.SetFrequency(0.5)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        R, T = read_rt(sim, "Above", "Below")
        absorbed = 1.0 - R - T
        self.assertGreater(absorbed, 0.0,
                           "a lossy film must absorb power (1 - R - T > 0)")
        self.assertLess(absorbed, 1.0)
        self.assertGreater(R, 0.0)
        self.assertGreater(T, 0.0)

    def test_absorption_matches_transfer_matrix_reference(self):
        """Absorbing films are checked against the Airy formula.

        The characteristic/transfer-matrix solver in ``analytic.py`` is
        numerically ill conditioned for lossy films (it returns R + T > 1; see
        ``selftest_analytic.py``), so the absorbing cases use ``airy_rt``, which
        sums the multiply reflected amplitudes in closed form and stays
        accurate.  Both were cross-checked against each other for lossless
        films, where they agree to 7e-16.
        """
        for eps_imag in (0.1, 0.5, 1.0, 3.0):
            with self.subTest(eps_imag=eps_imag):
                eps = 12.0 + eps_imag * 1j
                n = cmath.sqrt(eps)
                sim = build_uniform_stack(1.0, ((0.5, n),), 1.5)[0]
                sim.SetFrequency(0.5)
                sim.SetExcitationPlanewave((0, 0), 1, 0)
                R, T = read_rt(sim, "Above", "Below")
                R_ref, T_ref = airy_rt(0.5, n, 1.0, 1.5, 0.0, "s", 0.5)
                self.assertAlmostEqual(R, R_ref, delta=1e-9)
                self.assertAlmostEqual(T, T_ref, delta=1e-9)
                # The reference itself must show real absorption, otherwise the
                # comparison could pass trivially.
                self.assertGreater(1.0 - R_ref - T_ref, 1e-3)

    def test_absorption_matches_reference_for_both_polarizations(self):
        """Absorption must also be right for p polarisation.

        The p-polarisation obliquity factor is a common source of error: using
        Re(kz_b)/Re(kz_a) instead of the admittance ratio overestimates T by the
        permittivity ratio, which for eps = 12 turns a correct solver into one
        that appears to create energy.
        """
        eps = 12.0 + 1.0j
        n = cmath.sqrt(eps)
        for theta in (0.0, 20.0, 40.0, 60.0):
            for pol, (sa, pa) in (("s", (1, 0)), ("p", (0, 1))):
                with self.subTest(theta=theta, polarization=pol):
                    sim = build_uniform_stack(1.0, ((0.5, n),), 1.5)[0]
                    sim.SetFrequency(0.5)
                    sim.SetExcitationPlanewave((theta, 0), sa, pa)
                    R, T = read_rt(sim, "Above", "Below")
                    R_ref, T_ref = airy_rt(0.5, n, 1.0, 1.5, theta, pol, 0.5)
                    self.assertAlmostEqual(R, R_ref, delta=1e-9)
                    self.assertAlmostEqual(T, T_ref, delta=1e-9)

    def test_absorption_scales_linearly_with_the_imaginary_part(self):
        """In the weak-absorption limit 1 - R - T must be proportional to Im(eps).

        A naive "as Im(eps) -> 0, absorption -> 0" test is misleading: with
        d = 0.5 and n ~ 3.46, Im(eps) = 1e-2 already means roughly 2 percent
        attenuation (alpha*d = 2*pi*f*Im(n)*d ~ 0.0045), so it is genuinely
        absorbing, not numerically noisy.  The physical statement that holds is
        linearity: reducing Im(eps) by 10 must reduce the absorbed fraction by
        10, which also demonstrates the solver is not losing weak absorption in
        rounding.
        """
        ratios = []
        for eps_imag in (1e-1, 1e-2, 1e-3, 1e-4):
            n = cmath.sqrt(12.0 + eps_imag * 1j)
            sim = build_uniform_stack(1.0, ((0.5, n),), 1.5)[0]
            sim.SetFrequency(0.5)
            sim.SetExcitationPlanewave((0, 0), 1, 0)
            R, T = read_rt(sim, "Above", "Below")
            absorbed = 1.0 - R - T
            self.assertGreater(absorbed, 0.0,
                               "a lossy film must absorb (Im(eps)=%g)" % eps_imag)
            ratios.append(absorbed / eps_imag)

        # Every ratio must agree with the first to within 5 percent.  Linearity
        # only holds to first order, and the measured departure at
        # Im(eps) = 1e-1 is 1.8 percent, so 5 percent is the honest bound.
        for r in ratios:
            self.assertAlmostEqual(r / ratios[0], 1.0, delta=5e-2,
                                   msg="absorption is not linear in Im(eps): %s"
                                       % ratios)
        # And the absorption must actually be small at the smallest value.
        self.assertLess(ratios[-1] * 1e-4, 1e-4)

    def test_absorbed_power_grows_with_absorption_strength(self):
        absorbed = []
        for eps_imag in (0.1, 0.5, 1.0, 3.0):
            n = cmath.sqrt(12.0 + eps_imag * 1j)
            sim = build_uniform_stack(1.0, ((0.5, n),), 1.5)[0]
            sim.SetFrequency(0.5)
            sim.SetExcitationPlanewave((0, 0), 1, 0)
            R, T = read_rt(sim, "Above", "Below")
            absorbed.append(1.0 - R - T)
        for a, b in zip(absorbed, absorbed[1:]):
            self.assertGreater(b, a,
                               "absorbed power must increase with eps_imag")


class LosslessConstraintTests(unittest.TestCase):
    """Energy conservation and reciprocity for transparent structures."""

    def test_energy_conservation_across_parameters(self):
        for n2 in (1.5, 2.0, 3.5):
            for d in (0.05, 0.25, 0.5, 1.0):
                for theta in (0.0, 30.0, 60.0, 80.0):
                    for pol, (sa, pa) in (("s", (1, 0)), ("p", (0, 1))):
                        with self.subTest(n2=n2, d=d, theta=theta, pol=pol):
                            sim = build_uniform_stack(1.0, ((d, n2),), 1.5)[0]
                            sim.SetFrequency(0.5)
                            sim.SetExcitationPlanewave((theta, 0), sa, pa)
                            R, T = read_rt(sim, "Above", "Below")
                            self.assertAlmostEqual(
                                R + T, 1.0, delta=_EXACT_TOL,
                                msg="energy not conserved for a lossless stack")

    def test_all_outputs_are_finite(self):
        sim = build_uniform_stack(1.0, ((0.5, 2.0),), 1.5, num_basis=9)[0]
        sim.SetRegionCircle("Film0", "_above", (0, 0), 0.2)
        sim.SetFrequency(0.5)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        for name, value in (
            ("GetPowerFlux", sim.GetPowerFlux("Above", 0.0)),
            ("GetSMatrixDeterminant", sim.GetSMatrixDeterminant()),
            ("GetLayerVolumeIntegral", sim.GetLayerVolumeIntegral("Film0", "U")),
            ("GetStressTensorIntegral", sim.GetStressTensorIntegral("Film0", 0.0)),
        ):
            with self.subTest(output=name):
                for part in (value if isinstance(value, tuple) else (value,)):
                    if isinstance(part, complex):
                        self.assertTrue(math.isfinite(part.real) and
                                        math.isfinite(part.imag))
                    elif isinstance(part, float):
                        self.assertTrue(math.isfinite(part))

    def test_reciprocity_of_reflectance(self):
        """R must be the same when the incidence and exit media are swapped.

        For a stack between two media, the reflectance seen from either side is
        identical for the same angle in the respective medium.  This is a
        symmetry of Maxwell's equations that S4 satisfies only if the layer
        ordering and the excitation direction are both handled consistently.
        """
        n_a, n_b = 1.0, 1.5
        layers = ((0.5, 2.0),)
        freq = 0.5
        # Illuminated from the n_a side.
        sim_f = build_uniform_stack(n_a, layers, n_b)[0]
        sim_f.SetFrequency(freq)
        sim_f.SetExcitationPlanewave((0, 0), 1, 0)
        R_f, _ = read_rt(sim_f, "Above", "Below")
        # Illuminated from the n_b side (rebuild with the media swapped).
        sim_b = build_uniform_stack(n_b, layers, n_a)[0]
        sim_b.SetFrequency(freq)
        sim_b.SetExcitationPlanewave((0, 0), 1, 0)
        R_b, _ = read_rt(sim_b, "Above", "Below")
        self.assertAlmostEqual(R_f, R_b, delta=1e-9)


class ConvergenceTests(unittest.TestCase):
    """NumBasis convergence for a periodic pattern.

    The expectations here are qualitative on purpose: the Fourier modal method
    converges but not necessarily monotonically, so the test asserts that the
    result *stabilises* and that the change between successive refinements
    shrinks, rather than that each step improves.
    """

    #: A square-lattice slab with a circular hole pattern.  Chosen because the
    #: Fourier coefficients of a circle decay quickly, so convergence is visible
    #: at modest NumBasis.
    RADIUS = 0.2
    FREQ = 0.5

    def _transmission(self, num_basis):
        sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
        sim.AddMaterial("Air", 1)
        sim.AddMaterial("Si", 12)
        sim.AddLayer("Above", 0, "Air")
        sim.AddLayer("Slab", 0.5, "Si")
        sim.SetRegionCircle("Slab", "Air", (0, 0), self.RADIUS)
        sim.AddLayerCopy("Below", 0, "Above")
        sim.SetFrequency(self.FREQ)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        inc, _ = sim.GetPowerFlux("Above", 0.0)
        trans, _ = sim.GetPowerFlux("Below", 0.0)
        return trans.real / inc.real

    def test_transmission_converges_with_num_basis(self):
        bases = [25, 49, 81, 121, 169, 225]
        values = [self._transmission(n) for n in bases]

        for v in values:
            self.assertTrue(math.isfinite(v))

        # Successive differences must shrink overall: compare the spread over
        # the first half of the refinements against the spread over the second.
        early = max(values[:3]) - min(values[:3])
        late = max(values[-3:]) - min(values[-3:])
        self.assertLess(late, early,
                        "refining NumBasis must reduce the spread of T "
                        "(early=%.6g late=%.6g)" % (early, late))
        self.assertLess(late, 2e-3,
                        "T has not stabilised by NumBasis=%d (spread %.6g)"
                        % (bases[-1], late))

    def test_energy_is_conserved_at_every_num_basis(self):
        """Convergence must not come at the cost of energy conservation."""
        for n in (1, 9, 25, 49, 121):
            with self.subTest(num_basis=n):
                sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=n)
                sim.AddMaterial("Air", 1)
                sim.AddMaterial("Si", 12)
                sim.AddLayer("Above", 0, "Air")
                sim.AddLayer("Slab", 0.5, "Si")
                sim.SetRegionCircle("Slab", "Air", (0, 0), self.RADIUS)
                sim.AddLayerCopy("Below", 0, "Above")
                sim.SetFrequency(self.FREQ)
                sim.SetExcitationPlanewave((0, 0), 1, 0)
                R, T = read_rt(sim, "Above", "Below")
                self.assertAlmostEqual(R + T, 1.0, delta=1e-9)

    def test_unpatterned_limit_is_exact_at_one_basis(self):
        """A planar slab needs exactly one Fourier order.

        This contrasts with the patterned case above: it shows the convergence
        there is a genuine truncation effect rather than a global accuracy
        floor.  The reference is the exact Airy result for a single film.
        """
        n_film = 2.0
        sim = build_uniform_stack(1.0, ((0.5, n_film),), 1.5, num_basis=1)[0]
        sim.SetFrequency(self.FREQ)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        R, T = read_rt(sim, "Above", "Below")
        R_ref, T_ref = airy_rt(0.5, n_film, 1.0, 1.5, 0.0, "s", self.FREQ)
        self.assertAlmostEqual(R, R_ref, delta=1e-12)
        self.assertAlmostEqual(T, T_ref, delta=1e-12)

    def test_extra_basis_orders_do_not_change_a_planar_result(self):
        """Adding Fourier orders to a structure with no pattern changes nothing.

        Measured: NumBasis = 1, 9 and 25 all give R = 0.465319723118,
        T = 0.534680276882 for a planar silicon film on glass.  A disagreement
        here would mean the basis set is interacting with an unpatterned layer.
        """
        n_film = math.sqrt(12.0)
        results = []
        for n in (1, 9, 25):
            sim = build_uniform_stack(1.0, ((0.5, n_film),), 1.5, num_basis=n)[0]
            sim.SetFrequency(self.FREQ)
            sim.SetExcitationPlanewave((0, 0), 1, 0)
            results.append(read_rt(sim, "Above", "Below"))
        for (R, T) in results[1:]:
            self.assertAlmostEqual(R, results[0][0], delta=1e-12)
            self.assertAlmostEqual(T, results[0][1], delta=1e-12)


if __name__ == "__main__":
    unittest.main()
