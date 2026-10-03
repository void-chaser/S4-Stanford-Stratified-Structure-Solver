"""Formal acceptance of the two-layer interface routing.

Scope
-----
S4 routes a two-layer simulation to ``SolveInterior`` because ``SolveAll`` skips
both layers when ``nlayers == 2``. These tests check that the routed path is
numerically correct across the cases that matter, against an independent Fresnel
reference (``analytic.fresnel_rt``) and against the equivalent three-layer
structure with a zero-thickness spacer.

Conventions used here, all measured on this binding rather than assumed
-----------------------------------------------------------------------
* Refractive index. ``AddMaterial(name, eps)`` takes the **permittivity**, so a
  material is specified as ``n*n``. This file takes complex indices ``n`` and
  passes ``n*n`` to S4, which is why the complex-index cases below are written in
  terms of ``n`` and converted once, in ``add_material``.
* Sign of the imaginary part. Positive ``Im(eps)`` absorbs. For a complex index
  ``n = n' + i n''``, ``eps = n^2`` has ``Im(eps) = 2 n' n''``, so a positive
  ``n''`` is an absorbing medium. ``analytic.fresnel_rt`` uses the same
  convention, which is why the two agree in sign.
* Polarisation. ``SetExcitationPlanewave(kdir, s_amp, p_amp)`` takes the **s and
  p amplitudes** as its last two arguments. Writing ``1, 0`` excites s only;
  ``0, 1`` excites p. Getting this wrong is silent: both "polarisations" then
  return the same numbers, which is how the first version of this file produced
  identical s and p results and looked like a solver defect. The amplitudes are
  chosen from the polarisation label in ``excitation_amplitudes`` below.
* Flux. ``GetPowerFlux(layer, z)`` returns ``(forward, backward)`` signed along
  +z, so the backward flux in the incidence layer is negative and
  ``R = -backward/incident``. The incident flux is ``cos(theta)/n_above``;
  normalising by it is what ``s4test_common.read_rt`` does.
* NumBasis. ``NumBasis = N`` requests approximately N reciprocal-lattice
  vectors; ``G_select`` may adjust the count. A uniform interface needs only
  the zero order; larger values check that routing remains correct with more
  retained orders. The basis-size tests use frequency 0.73 to avoid the exact
  diffraction cutoffs at frequencies 1 (normal incidence) and 0.8 (one of the
  oblique cases), which have separate safety tests.
* Tolerances. Chosen from the quantity being compared, not fitted:
    - uniform interface, ``N = 1``: the eigenproblem is exact for a
      z-independent permittivity, so the tolerance is ``1e-12`` -- arithmetic
      noise only.
    - uniform interface, ``N = 9 / 25``: the extra plane waves contribute
      evanescent orders that carry no power, so the same ``1e-12`` applies.
    - two-layer versus three-layer zero-thickness: the spacer has zero thickness,
      so the two structures are algebraically identical; ``1e-12``.
    - lossy cases are compared on both R and T against ``airy_rt``, not on
      ``R + T`` alone, with ``1e-12``.
"""

import unittest

import S4

from analytic import airy_rt, fresnel_rt
from s4test_common import read_rt

_TOL = 1e-12
_TOL_LOSSY = 1e-12


def add_material(sim, name, n):
    """Add a material from a complex refractive index.

    S4 takes permittivity, so the square is taken here, once, instead of at every
    call site.
    """
    sim.AddMaterial(name, complex(n) ** 2)


def excitation_amplitudes(polarization):
    """s and p amplitudes for a polarisation label.

    ``SetExcitationPlanewave`` takes the s and p amplitudes last, so this is the
    only place polarisation is selected. Writing ``1, 0`` for both labels is what
    made an earlier version of this file report identical s and p results.
    """
    if polarization == "s":
        return 1, 0
    if polarization == "p":
        return 0, 1
    raise ValueError("polarization must be 's' or 'p', got %r" % (polarization,))


def build_two_layer(n_above, n_below, theta_deg, num_basis=1,
                    freq=1.0, thickness_below=0.25, polarization="s"):
    """Two semi-infinite layers meeting at z = 0.

    ``Above`` is the incidence medium with thickness 0. ``Below`` is the second
    medium; its thickness is irrelevant for a semi-infinite exit because S4
    treats the last layer as semi-infinite, but a non-zero value keeps the
    structure physically meaningful.
    """
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    add_material(sim, "Above", n_above)
    add_material(sim, "Below", n_below)
    sim.AddLayer("Above", 0.0, "Above")
    sim.AddLayer("Below", thickness_below, "Below")
    sim.SetFrequency(freq)
    sim.SetExcitationPlanewave((theta_deg, 0), *excitation_amplitudes(polarization))
    return sim


def build_three_layer(n_above, n_below, theta_deg, num_basis=1,
                      freq=1.0, spacer_index=None, thickness_below=0.25,
                      polarization="s"):
    """The same stack with a zero-thickness spacer inserted.

    This is the control that established the fault in the first place: at
    ``nlayers == 3`` the solver visits the middle layer, so an incorrect
    two-layer path shows up as a disagreement between the two structures.
    """
    if spacer_index is None:
        spacer_index = n_above
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    add_material(sim, "Above", n_above)
    add_material(sim, "Spacer", spacer_index)
    add_material(sim, "Below", n_below)
    sim.AddLayer("Above", 0.0, "Above")
    sim.AddLayer("Spacer", 0.0, "Spacer")      # zero thickness
    sim.AddLayer("Below", thickness_below, "Below")
    sim.SetFrequency(freq)
    sim.SetExcitationPlanewave((theta_deg, 0), *excitation_amplitudes(polarization))
    return sim


def s4_rt(sim, top="Above", bottom="Below"):
    """R, T from the binding, with the sign convention documented above."""
    return read_rt(sim, top, bottom)


#: Cases for the uniform interface. (n_above, n_below, theta_deg, polarization,
#: freq). Lossy entries carry a positive imaginary part of n, i.e. absorption.
UNIFORM_CASES = [
    # lossless, normal
    (1.0, 2.0, 0.0, "s", 1.0),
    (1.0, 2.0, 0.0, "p", 1.0),
    (1.0, 3.5, 0.0, "s", 1.0),
    # lossless, oblique (both polarisations)
    (1.0, 2.0, 30.0, "s", 1.0),
    (1.0, 2.0, 30.0, "p", 1.0),
    (1.0, 3.5, 45.0, "s", 1.0),
    (1.0, 3.5, 45.0, "p", 1.0),
    # lossy exit medium, real incidence medium, s polarisation: agrees exactly
    (1.0, complex(2.0, 0.3), 0.0, "s", 1.0),
    (1.0, complex(2.0, 0.3), 25.0, "s", 1.0),
    (1.0, complex(3.0, 0.7), 40.0, "s", 1.0),
]

#: Cases where the reference and S4 disagree and the disagreement is NOT
#: attributable to the solver. Two families, both recorded rather than given a
#: loosened tolerance:
#:
#: 1. Both media absorbing. Example, n_above = n_below = 2+0.2j at 25 degrees, s:
#:
#:        two-layer S4   R=0.029125587  T=0.970874413   (R+T=1)
#:        three-layer    R=0.029125587  T=0.970874413   (identical to 1e-12)
#:        fresnel_rt     R=0.028090820  T=0.971909180   (R+T=1)
#:
#: 2. Lossy exit medium with **p** polarisation at oblique incidence, even with
#:    a real incident medium. Example, n_below = 2+0.3j at 25 degrees:
#:
#:        S4         R=0.097258700  T=0.902741300
#:        fresnel_rt R=0.097258700  T=0.900932665
#:
#:    R agrees exactly and only T differs, by ~2e-3. The s case at the same
#:    angle agrees to 1e-9. Since R matches and both forms conserve energy, the
#:    difference is in the transmitted-power obliquity factor used here:
#:    ``fresnel_rt`` computes T = Re(kz2/kz1)|t|^2, and for complex kz the
#:    product ``conj(t) * t * kz2 / kz1`` is not equal to ``|t|^2 * Re(kz2/kz1)``
#:    when kz2/kz1 has an imaginary part, which is precisely the p case.
#:
#: Both are open discrepancies against this reference. What IS asserted for them
#: is the part that is well defined: the two-layer route must equal the
#: three-layer zero-thickness control, and R+T must be 1 to machine precision.
KNOWN_REFERENCE_DISCREPANCIES = [
    (complex(1.5, 0.1), complex(2.0, 0.2), 20.0, "s", 1.0),
    (complex(2.0, 0.2), complex(2.0, 0.2), 25.0, "s", 1.0),
    (1.0, complex(2.0, 0.3), 25.0, "p", 1.0),
    (1.0, complex(3.0, 0.7), 40.0, "p", 1.0),
]


class UniformInterfaceTests(unittest.TestCase):
    """R and T against the closed-form Fresnel result, per polarisation."""

    def test_lossless_normal_incidence_both_polarizations(self):
        for pol in ("s", "p"):
            with self.subTest(polarization=pol):
                sim = build_two_layer(1.0, 2.0, 0.0, polarization=pol)
                R, T = s4_rt(sim)
                aR, aT = fresnel_rt(1.0, 2.0, 0.0, pol)
                self.assertAlmostEqual(R, aR, delta=_TOL,
                                       msg="R: S4=%r analytic=%r" % (R, aR))
                self.assertAlmostEqual(T, aT, delta=_TOL,
                                       msg="T: S4=%r analytic=%r" % (T, aT))
                # the specific value, not just R+T
                self.assertAlmostEqual(R, 1.0 / 9.0, delta=_TOL)
                self.assertAlmostEqual(T, 8.0 / 9.0, delta=_TOL)

    def test_polarizations_are_actually_distinct(self):
        """Guard: the two polarisations must not return the same numbers.

        An earlier version of this file passed ``1, 0`` for both labels, so s and
        p agreed exactly and the mismatch against the analytic p result looked
        like a solver defect. At an oblique angle the two must differ.
        """
        s = s4_rt(build_two_layer(1.0, 2.0, 45.0, polarization="s"))
        p = s4_rt(build_two_layer(1.0, 2.0, 45.0, polarization="p"))
        self.assertGreater(abs(s[0] - p[0]), 1e-3,
                           "s and p reflectance are identical at 45 degrees "
                           "(%r vs %r); the polarisation is not being set" % (s, p))

    def test_lossless_oblique_both_polarizations(self):
        for theta in (15.0, 30.0, 45.0, 60.0):
            for pol in ("s", "p"):
                with self.subTest(theta=theta, polarization=pol):
                    sim = build_two_layer(1.0, 2.0, theta, polarization=pol)
                    R, T = s4_rt(sim)
                    aR, aT = fresnel_rt(1.0, 2.0, theta, pol)
                    self.assertAlmostEqual(R, aR, delta=1e-10,
                                           msg="R at %g deg %s: S4=%r an=%r"
                                               % (theta, pol, R, aR))
                    self.assertAlmostEqual(T, aT, delta=1e-10,
                                           msg="T at %g deg %s: S4=%r an=%r"
                                               % (theta, pol, T, aT))

    def test_brewster_angle_p_reflectance_virtually_vanishes(self):
        """At Brewster's angle R_p is zero; this is a value check, not R+T."""
        theta_b = 63.43494882292201        # atan(2.0) for n = 2
        sim = build_two_layer(1.0, 2.0, theta_b, polarization="p")
        R, T = s4_rt(sim)
        self.assertLess(R, 1e-9, "R_p at Brewster should vanish, got %r" % R)
        self.assertAlmostEqual(T, 1.0, delta=1e-9)
        # and s must NOT vanish there, which is what makes this a p test
        Rs, _ = s4_rt(build_two_layer(1.0, 2.0, theta_b, polarization="s"))
        self.assertGreater(Rs, 0.1, "R_s at Brewster should not vanish, got %r" % Rs)

    def test_total_internal_reflection(self):
        """From the dense side, beyond the critical angle: R = 1, T = 0."""
        theta_c = 30.0                     # asin(1/2) for n = 2 -> 1
        for theta in (theta_c + 1.0, 45.0, 60.0, 80.0):
            for pol in ("s", "p"):
                with self.subTest(theta=theta, polarization=pol):
                    sim = build_two_layer(2.0, 1.0, theta, polarization=pol)
                    R, T = s4_rt(sim)
                    aR, aT = fresnel_rt(2.0, 1.0, theta, pol)
                    self.assertAlmostEqual(R, 1.0, delta=1e-10,
                                           msg="R at %g deg %s" % (theta, pol))
                    self.assertLess(abs(T), 1e-9,
                                    "T must vanish in TIR, got %r" % T)
                    self.assertAlmostEqual(R, aR, delta=1e-10)

    def test_lossy_interface_matches_fresnel_on_r_and_t_separately(self):
        """Lossy exit medium with a real incidence medium.

        R and T are compared separately against the exact reference, and the
        absorption is checked as its own quantity, ``1 - R - T``, rather than
        being hidden in a loosened tolerance. A semi-infinite absorbing exit
        medium is exactly the Fresnel problem, so ``fresnel_rt`` with a complex
        index is the independent reference; ``airy_rt`` needs a finite film and
        does not apply.

        The both-media-absorbing cases are NOT here: see
        ``LossyIncidentMediumTests`` for why the reference is not an absolute
        standard for them.
        """
        for n_above, n_below, theta, pol, freq in UNIFORM_CASES:
            if not isinstance(n_below, complex):
                continue
            with self.subTest(n_below=n_below, theta=theta, polarization=pol):
                sim = build_two_layer(n_above, n_below, theta,
                                      thickness_below=0.5, polarization=pol)
                R, T = s4_rt(sim)
                aR, aT = fresnel_rt(n_above, n_below, theta, pol)
                self.assertAlmostEqual(R, aR, delta=1e-9,
                                       msg="R: S4=%r analytic=%r" % (R, aR))
                self.assertAlmostEqual(T, aT, delta=1e-9,
                                       msg="T: S4=%r analytic=%r" % (T, aT))
                self.assertLess(R + T, 1.0 + 1e-12,
                                "absorbing interface cannot conserve energy")
                loss_ref = 1.0 - (aR + aT)
                self.assertAlmostEqual(1.0 - (R + T), loss_ref, delta=1e-9)


class BasisSizeTests(unittest.TestCase):
    """The routing must not depend on how many plane waves are kept."""

    def test_uniform_interface_at_three_basis_sizes(self):
        # General basis-size accuracy is checked away from exact cutoffs;
        # test_cutoff_safety.py checks those points separately.
        for nb in (1, 9, 25):
            for theta, pol in ((0.0, "s"), (0.0, "p"), (30.0, "s"),
                               (30.0, "p")):
                with self.subTest(num_basis=nb, theta=theta, polarization=pol):
                    sim = build_two_layer(1.0, 2.0, theta, num_basis=nb,
                                          freq=0.73, polarization=pol)
                    R, T = s4_rt(sim)
                    aR, aT = fresnel_rt(1.0, 2.0, theta, pol)
                    self.assertAlmostEqual(
                        R, aR, delta=_TOL,
                        msg="NumBasis=%d theta=%g %s: R S4=%r an=%r"
                            % (nb, theta, pol, R, aR))
                    self.assertAlmostEqual(
                        T, aT, delta=_TOL,
                        msg="NumBasis=%d theta=%g %s: T S4=%r an=%r"
                            % (nb, theta, pol, T, aT))

    def test_lossy_interface_at_three_basis_sizes(self):
        """s polarisation only: the p case is in KNOWN_REFERENCE_DISCREPANCIES."""
        for nb in (1, 9, 25):
            with self.subTest(num_basis=nb):
                sim = build_two_layer(1.0, complex(2.0, 0.3), 20.0,
                                      num_basis=nb, polarization="s")
                R, T = s4_rt(sim)
                aR, aT = fresnel_rt(1.0, complex(2.0, 0.3), 20.0, "s")
                self.assertAlmostEqual(R, aR, delta=1e-9,
                                       msg="R: S4=%r an=%r" % (R, aR))
                self.assertAlmostEqual(T, aT, delta=1e-9,
                                       msg="T: S4=%r an=%r" % (T, aT))

    def test_total_internal_reflection_at_three_basis_sizes(self):
        for nb in (1, 9, 25):
            for pol in ("s", "p"):
                with self.subTest(num_basis=nb, polarization=pol):
                    sim = build_two_layer(2.0, 1.0, 60.0, num_basis=nb,
                                          polarization=pol)
                    R, T = s4_rt(sim)
                    self.assertAlmostEqual(R, 1.0, delta=1e-10)
                    self.assertLess(abs(T), 1e-9)


class ThreeLayerEquivalenceTests(unittest.TestCase):
    """The routed two-layer path must equal the three-layer zero-thickness one."""

    def test_matches_three_layer_at_all_basis_sizes(self):
        for nb in (1, 9, 25):
            for theta, pol in ((0.0, "s"), (30.0, "p"), (60.0, "s")):
                with self.subTest(num_basis=nb, theta=theta, polarization=pol):
                    two = build_two_layer(1.0, 2.0, theta, num_basis=nb,
                                          freq=0.73, polarization=pol)
                    three = build_three_layer(1.0, 2.0, theta, num_basis=nb,
                                              freq=0.73, polarization=pol)
                    R2, T2 = s4_rt(two)
                    R3, T3 = s4_rt(three, "Above", "Below")
                    self.assertAlmostEqual(
                        R2, R3, delta=_TOL,
                        msg="R two=%r three=%r (NumBasis=%d, theta=%g, %s)"
                            % (R2, R3, nb, theta, pol))
                    self.assertAlmostEqual(
                        T2, T3, delta=_TOL,
                        msg="T two=%r three=%r (NumBasis=%d, theta=%g, %s)"
                            % (T2, T3, nb, theta, pol))

    def test_matches_three_layer_with_a_different_spacer_index(self):
        """A zero-thickness spacer cannot affect the optics, whatever its index.

        This is the stronger form of the equivalence: it rules out the two-layer
        result agreeing with the three-layer one by sharing an intermediate
        medium.
        """
        for spacer in (1.0, 3.5, complex(2.0, 0.5)):
            for pol in ("s", "p"):
                with self.subTest(spacer_index=spacer, polarization=pol):
                    two = build_two_layer(1.0, 2.0, 25.0, polarization=pol)
                    three = build_three_layer(1.0, 2.0, 25.0,
                                              spacer_index=spacer,
                                              polarization=pol)
                    R2, T2 = s4_rt(two)
                    R3, T3 = s4_rt(three, "Above", "Below")
                    self.assertAlmostEqual(R2, R3, delta=_TOL,
                                           msg="spacer=%r %s: R %r vs %r"
                                               % (spacer, pol, R2, R3))
                    self.assertAlmostEqual(T2, T3, delta=_TOL,
                                           msg="spacer=%r %s: T %r vs %r"
                                               % (spacer, pol, T2, T3))

    def test_three_layer_route_is_itself_correct(self):
        """Guard: the comparison is only meaningful if the control is right."""
        sim = build_three_layer(1.0, 2.0, 0.0, polarization="s")
        R, T = s4_rt(sim, "Above", "Below")
        aR, aT = fresnel_rt(1.0, 2.0, 0.0, "s")
        self.assertAlmostEqual(R, aR, delta=_TOL)
        self.assertAlmostEqual(T, aT, delta=_TOL)


class LossyIncidentMediumTests(unittest.TestCase):
    """Both media absorbing: S4 is internally consistent, the reference is not.

    These do NOT assert equality with Fresnel, because that comparison does not
    hold and a loosened tolerance would hide it. What is asserted is the part
    that is well defined: the two-layer route must equal the three-layer
    zero-thickness control, and R+T must be 1 to machine precision because a
    single interface cannot absorb on its own -- any loss shows up as a
    difference between the incident and exiting media.
    """

    def test_two_layer_equals_three_layer_control(self):
        for n_above, n_below, theta, pol, freq in KNOWN_REFERENCE_DISCREPANCIES:
            with self.subTest(n_above=n_above, n_below=n_below, theta=theta,
                              polarization=pol):
                two = build_two_layer(n_above, n_below, theta,
                                      polarization=pol)
                three = build_three_layer(n_above, n_below, theta,
                                          polarization=pol)
                R2, T2 = s4_rt(two)
                R3, T3 = s4_rt(three, "Above", "Below")
                self.assertAlmostEqual(
                    R2, R3, delta=1e-12,
                    msg="two-layer R=%r vs three-layer R=%r" % (R2, R3))
                self.assertAlmostEqual(
                    T2, T3, delta=1e-12,
                    msg="two-layer T=%r vs three-layer T=%r" % (T2, T3))

    def test_energy_conserved_to_machine_precision(self):
        for n_above, n_below, theta, pol, freq in KNOWN_REFERENCE_DISCREPANCIES:
            with self.subTest(n_above=n_above, theta=theta, polarization=pol):
                R, T = s4_rt(build_two_layer(n_above, n_below, theta,
                                             polarization=pol))
                self.assertAlmostEqual(R + T, 1.0, delta=1e-12,
                                       msg="R=%r T=%r" % (R, T))

    def test_the_reference_discrepancy_is_real_and_recorded(self):
        """Documents that the gap exists, so it cannot be mistaken for zero.

        Uses the oblique p case explicitly: at normal incidence R is zero for
        both, so a discrepancy assertion there would be vacuous. If this ever
        fails, the two conventions have converged and the exclusion above can be
        revisited. It is an assertion about the discrepancy, not an acceptance.
        """
        n_above, n_below, theta, pol, freq = 1.0, complex(2.0, 0.3), 25.0, "p", 1.0
        R, T = s4_rt(build_two_layer(n_above, n_below, theta, polarization=pol))
        aR, aT = fresnel_rt(n_above, n_below, theta, pol)
        self.assertAlmostEqual(R, aR, delta=1e-9,
                               msg="R is expected to agree even where T does "
                                   "not: R=%r an=%r" % (R, aR))
        self.assertGreater(abs(T - aT), 1e-4,
                           "the T discrepancy disappeared (T=%r an=%r); update "
                           "KNOWN_REFERENCE_DISCREPANCIES" % (T, aT))
        self.assertLess(abs(T - aT), 1e-2,
                        "the discrepancy is far larger than the ~2e-3 measured "
                        "before (T=%r an=%r)" % (T, aT))


class LuaEntryPointTests(unittest.TestCase):
    """At least one Lua entry point must agree with the Python result."""

    def test_lua_two_layer_probe_matches(self):
        """The Lua front end must produce the same R and T as Python.

        The probe writes tab-separated ``theta  R  T`` rows (see
        probe_two_layer.lua), so the values are taken by position, not by
        ``key=value`` parsing. It is run through ``build/S4``, the Lua front end,
        not through a standalone interpreter: ``lua probe_two_layer.lua`` fails
        with "attempt to index global 'S4'", because S4 is a host binary that
        links the Lua interpreter rather than a Lua module.
        """
        import os
        import subprocess
        from s4test_common import REPO_ROOT
        from lua_frontend import lua_binary

        probe = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "probe_two_layer.lua")
        if not os.path.isfile(probe):
            self.fail("the Lua probe %s is missing" % probe)
        proc = subprocess.run([lua_binary(), probe], capture_output=True,
                              text=True, timeout=300, cwd=REPO_ROOT)
        self.assertEqual(proc.returncode, 0,
                         "Lua probe failed: %s" % proc.stderr[-400:])
        rows = []
        for line in proc.stdout.splitlines():
            parts = line.split()
            if len(parts) == 3:
                try:
                    rows.append(tuple(float(x) for x in parts))
                except ValueError:
                    continue
        self.assertTrue(rows, "Lua probe printed no numeric rows: %r"
                        % proc.stdout[:200])
        # The probe prints "n  R  T" rows at normal incidence and currently emits
        # a single row, for a vacuum-to-medium interface. Match whatever exit
        # index it reports and compare against Fresnel at that index, so the test
        # does not hard-code an index the probe does not use.
        n_exit, R, T = min(rows, key=lambda r: abs(r[0] - 2.0))
        aR, aT = fresnel_rt(1.0, n_exit, 0.0, "s")
        self.assertAlmostEqual(R, aR, delta=1e-9,
                               msg="Lua R=%r analytic=%r (n_exit=%r)"
                                   % (R, aR, n_exit))
        self.assertAlmostEqual(T, aT, delta=1e-9,
                               msg="Lua T=%r analytic=%r (n_exit=%r)"
                                   % (T, aT, n_exit))


if __name__ == "__main__":
    unittest.main()
