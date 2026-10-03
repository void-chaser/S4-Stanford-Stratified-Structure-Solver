"""Exact diffraction cutoff must produce a valid result or an explicit error.

At frequency 1 on a unit square lattice, the first diffraction orders have
zero longitudinal wavevector. This is a numerical edge case: depending on
floating point optimization, their computed wavevectors may be exactly zero
or only very close to zero. A reported Fresnel result and an explicit singular
system error are both acceptable until cutoff modes have a physical treatment.
NaN, incorrect finite flux, and a cached failed solution are not acceptable.
"""

import math
import unittest

import S4
from analytic import fresnel_rt


def _interface(layers, theta=0.0, num_basis=9):
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    sim.AddMaterial("Air", 1.0)
    sim.AddMaterial("Glass", 4.0)
    sim.AddLayer("Above", 0.0, "Air")
    if layers == 3:
        sim.AddLayer("Spacer", 0.0, "Air")
    sim.AddLayer("Below", 0.5, "Glass")
    sim.SetExcitationPlanewave((theta, 0), 1, 0)
    return sim


def _rt(sim):
    incident, reflected = sim.GetPowerFlux("Above", 0.0)
    transmitted, _ = sim.GetPowerFlux("Below", 0.0)
    if not all(math.isfinite(x.real) for x in (incident, reflected, transmitted)):
        raise AssertionError("cutoff produced non-finite power flux")
    if incident.real == 0.0:
        raise AssertionError("cutoff produced zero incident power")
    return -reflected.real / incident.real, transmitted.real / incident.real



def _all_finite(value):
    """True when a (possibly nested) tuple of numbers contains no NaN or Inf."""
    if isinstance(value, (tuple, list)):
        return all(_all_finite(item) for item in value)
    if isinstance(value, complex):
        return math.isfinite(value.real) and math.isfinite(value.imag)
    if isinstance(value, float):
        return math.isfinite(value)
    return True



def _finite_scan(value):
    """Return (all_finite, n_numbers, n_unchecked_types) for a nested value.

    An unrecognised type is reported as unchecked rather than assumed finite.
    """
    if isinstance(value, (tuple, list)):
        fin, num, unch = True, 0, 0
        for item in value:
            a, b, c = _finite_scan(item)
            fin = fin and a
            num += b
            unch += c
        return fin, num, unch
    if isinstance(value, bool):
        return True, 0, 1
    if isinstance(value, int):
        return True, 0, 0
    if isinstance(value, float):
        return math.isfinite(value), 1, 0
    if isinstance(value, complex):
        return (math.isfinite(value.real) and math.isfinite(value.imag)), 2, 0
    return False, 0, 1


# The only error reasons the cutoff is allowed to report.  Anything else is a
# defect, not an acceptable safety behaviour.
CUTOFF_ERROR_REASONS = ("singular interface", "non-finite")

ACCESSORS = (
    ("GetPowerFlux/Above", lambda s: s.GetPowerFlux("Above", 0.0)),
    ("GetPowerFlux/Below", lambda s: s.GetPowerFlux("Below", 0.0)),
    ("GetPowerFluxByOrder/Above", lambda s: s.GetPowerFluxByOrder("Above", 0.0)),
    ("GetPowerFluxByOrder/Below", lambda s: s.GetPowerFluxByOrder("Below", 0.0)),
    ("GetAmplitudes/Above", lambda s: s.GetAmplitudes("Above", 0.0)),
    ("GetAmplitudes/Below", lambda s: s.GetAmplitudes("Below", 0.0)),
    ("GetSMatrixDeterminant", lambda s: s.GetSMatrixDeterminant()),
    ("GetPoyntingFlux/Above", lambda s: s.GetPoyntingFlux("Above", 0.0)),
    ("GetFields/Above", lambda s: s.GetFields(0.0, 0.0, 0.0)),
    # z = 0.1 addresses the interior layer, which for the flat stack is the
    # exit medium.  At f = 0.5 that medium has an order exactly at cutoff, so
    # these are the accessors that used to return NaN silently.
    ("GetFields/exit", lambda s: s.GetFields(0.0, 0.0, 0.1)),
    ("GetLayerZIntegral/Above", lambda s: s.GetLayerZIntegral("Above", (0.0, 0.0))),
    ("GetLayerZIntegral/Below", lambda s: s.GetLayerZIntegral("Below", (0.0, 0.0))),
    ("GetLayerVolumeIntegral/Below", lambda s: s.GetLayerVolumeIntegral("Below", "E")),
    ("GetStressTensorIntegral/Below", lambda s: s.GetStressTensorIntegral("Below", 0.0)),
)

SQRT2 = 2.0 ** 0.5

# (kind, layers, num_basis, frequency, theta).  f = sqrt(2) and f = 2 put air
# orders at cutoff; f = 1 puts an air order at cutoff and f = 0.5 a glass one.
CASE_MATRIX = tuple(
    [("flat", l, nb, f, 0.0)
     for l in (2, 3) for nb in (9, 25)
     for f in (0.5, 1.0, 2.0, SQRT2, 0.999, 1.001, 1.25)]
    + [("pattern", 3, nb, f, 0.0)
       for nb in (9, 25) for f in (1.0, 1.0 - 1e-10, 1.0 + 1e-10, 1.25)]
    + [("flat", 2, 25, 0.8, 30.0)]
)

# Frequencies that put no retained order at a cutoff, so a flat stack must
# reproduce the closed-form Fresnel answer for every one of them.
ORDINARY = (0.999, 1.001, 1.25)


def _case_sim(kind, layers, num_basis, frequency, theta):
    if kind == "pattern":
        return _patterned(num_basis, frequency)
    sim = _interface(layers, theta=theta, num_basis=num_basis)
    sim.SetFrequency(frequency)
    return sim


def _accessor_table():
    return dict(ACCESSORS)


def _shape_of(value):
    """Nested type names of a returned value, used to pin the return shape."""
    if isinstance(value, (tuple, list)):
        return tuple(_shape_of(item) for item in value)
    return type(value).__name__


def _expected_shape(name, num_basis):
    two_n = 2 * num_basis
    pair = ("complex", "complex")
    if name in ("GetPowerFlux/Above", "GetPowerFlux/Below", "GetPoyntingFlux/Above"):
        return pair
    if name in ("GetPowerFluxByOrder/Above", "GetPowerFluxByOrder/Below"):
        return tuple(pair for _ in range(num_basis))
    if name in ("GetAmplitudes/Above", "GetAmplitudes/Below"):
        return (tuple("complex" for _ in range(two_n)),) * 2
    if name == "GetSMatrixDeterminant":
        return ("complex", "float", "int")
    if name in ("GetFields/Above", "GetFields/exit"):
        return (("complex",) * 3,) * 2
    if name in ("GetLayerZIntegral/Above", "GetLayerZIntegral/Below"):
        return (("float",) * 3,) * 2
    if name == "GetLayerVolumeIntegral/Below":
        return "complex"
    if name == "GetStressTensorIntegral/Below":
        return ("complex",) * 3
    raise KeyError("no expected shape recorded for %s" % name)


def _retained_orders(num_basis):
    half = int(round(num_basis ** 0.5)) // 2
    return [(m, n) for m in range(-half, half + 1) for n in range(-half, half + 1)]


# An order sits exactly at a cutoff in a medium of permittivity eps when
# (f sin(theta) + m)^2 + n^2 == eps f^2.  The tolerance only has to separate an
# exact hit (a floating point residual, ~1e-16) from a deliberately offset
# frequency such as 1 +- 1e-10, so it is far tighter than any physical scale.
def _at_cutoff(frequency, theta, num_basis, permittivities=(1.0, 4.0)):
    sine = math.sin(math.radians(theta))  # S4 takes the polar angle in degrees
    for eps in permittivities:
        rhs = eps * frequency * frequency
        for (m, n) in _retained_orders(num_basis):
            if (m, n) == (0, 0):
                continue
            lhs = (frequency * sine + m) ** 2 + n * n
            if abs(lhs - rhs) <= 1e-12 * max(1.0, abs(rhs)):
                return True
    return False


def _expectation(case):
    """'must_succeed' for valid parameters, 'cutoff' at a diffraction cutoff.

    Only the second kind may report an error; the first kind has a defined
    answer and a broken accessor there is a defect, not an acceptable safety
    behaviour.
    """
    (kind, layers, num_basis, frequency, theta) = case
    return "cutoff" if _at_cutoff(frequency, theta, num_basis) else "must_succeed"


def _case_label(case, name):
    (kind, layers, num_basis, frequency, theta) = case
    return "%s[%s layers=%d nb=%d f=%r theta=%r]" % (
        name, kind, layers, num_basis, frequency, theta)


class _FresnelAssertions:
    """Shared assertion: a flat interface must reproduce the Fresnel answer."""

    def assert_fresnel(self, sim):
        reflectance, transmittance = _rt(sim)
        self.assertAlmostEqual(reflectance, 1.0 / 9.0, delta=1e-10)
        self.assertAlmostEqual(transmittance, 8.0 / 9.0, delta=1e-10)


class CutoffSafetyTests(_FresnelAssertions, unittest.TestCase):
    def test_exact_cutoff_is_explicit_or_correct(self):
        for layers in (2, 3):
            with self.subTest(layers=layers):
                sim = _interface(layers)
                sim.SetFrequency(1.0)
                try:
                    self.assert_fresnel(sim)
                except RuntimeError as exc:
                    self.assertIn("singular interface", str(exc))
                    with self.assertRaisesRegex(RuntimeError, "singular interface"):
                        sim.GetPowerFlux("Above", 0.0)
                    with self.assertRaisesRegex(RuntimeError, "singular interface"):
                        sim.GetSMatrixDeterminant()
                sim.SetFrequency(1.01)
                self.assert_fresnel(sim)

    def test_neighbors_match_fresnel(self):
        sim = _interface(3)
        for frequency in (0.999, 1.001):
            with self.subTest(frequency=frequency):
                sim.SetFrequency(frequency)
                self.assert_fresnel(sim)

    def test_oblique_cutoff_is_explicit_or_correct(self):
        # At 30 degrees, frequency 0.8 puts a retained order at the exit
        # medium's cutoff when NumBasis is 25. Check the physical zero order
        # in repeated fresh simulations because this case has produced a NaN
        # only during a complete -O1 suite run, not in isolated runs.
        expected_r, expected_t = fresnel_rt(1.0, 2.0, 30.0, "s")
        for attempt in range(30):
            with self.subTest(attempt=attempt):
                sim = _interface(2, theta=30.0, num_basis=25)
                sim.SetFrequency(0.8)
                try:
                    reflectance, transmittance = _rt(sim)
                except RuntimeError as exc:
                    self.assertTrue(
                        "singular interface" in str(exc) or
                        "non-finite" in str(exc), str(exc))
                    if "non-finite" in str(exc):
                        with self.assertRaisesRegex(RuntimeError,
                                                    "non-finite"):
                            sim.GetPowerFluxByOrder("Below", 0.0)
                else:
                    self.assertAlmostEqual(reflectance, expected_r, delta=1e-10)
                    self.assertAlmostEqual(transmittance, expected_t, delta=1e-10)


def _patterned(num_basis, frequency):
    """A patterned slab (glass cylinder in air) whose cutoff orders are excited.

    Unlike the flat interface, the +/-1 orders couple to the incident wave here,
    so the cutoff order actually carries (or fails to carry) power.
    """
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


# The one-sided approach used to bracket the exact point.  At an exact cutoff
# the diffraction efficiency varies like sqrt(|f - 1|), so the two one-sided
# values differ by O(1e-8) at 1 ulp and the exact value must lie between them
# up to that scale; 1e-6 is a deliberately loose bracket.
NEIGHBOUR = 1e-14
BRACKET = 1e-6


class CutoffNeighbourhoodTests(_FresnelAssertions, unittest.TestCase):
    """Coverage for ordinary frequencies, both sides, and NumBasis 1/9/25."""

    def test_num_basis_one_has_no_cutoff_order(self):
        # With a single Fourier order the +/-1 orders are not retained at all,
        # so the exact point is an ordinary Fresnel problem and must be exact.
        for layers in (2, 3):
            with self.subTest(layers=layers):
                sim = _interface(layers, num_basis=1)
                sim.SetFrequency(1.0)
                self.assert_fresnel(sim)

    def test_neighbours_are_exact_for_every_num_basis(self):
        for num_basis in (1, 9, 25):
            for frequency in (1.0 - NEIGHBOUR, 1.0 + NEIGHBOUR):
                with self.subTest(num_basis=num_basis, frequency=frequency):
                    sim = _interface(3, num_basis=num_basis)
                    sim.SetFrequency(frequency)
                    self.assert_fresnel(sim)

    def test_ordinary_frequencies_are_unaffected(self):
        # Frequencies that put no retained order at an exact cutoff.
        for num_basis in (1, 9, 25):
            for frequency in (0.25, 0.75, 0.9, 1.1, 1.25, 1.5):
                with self.subTest(num_basis=num_basis, frequency=frequency):
                    sim = _interface(3, num_basis=num_basis)
                    sim.SetFrequency(frequency)
                    self.assert_fresnel(sim)


# Every frequency where sqrt(m^2 + n^2) == f * sqrt(eps) for a retained order
# and one of the two media is an exact cutoff, so the same singular subsystem
# appears more than once across the spectrum.  For a flat interface the answer
# at each of them is the same Fresnel result, which makes the failure mode
# unambiguous: an explicit error, or the exact Fresnel value.
EXACT_CUTOFFS = (
    (9, 0.5, "glass (1,0)"),
    (25, 0.5, "glass (1,0)"),
    (9, 1.0, "air (1,0)"),
    (25, 1.0, "air (1,0)"),
    (25, 2.0, "air (2,0)"),
    (25, 2.0 ** 0.5, "air (1,1)"),
)


class ExactCutoffFamilyTests(_FresnelAssertions, unittest.TestCase):
    """A flat interface has an exact reference at every exact cutoff."""

    def test_every_exact_cutoff_is_explicit_or_exact(self):
        for num_basis, frequency, why in EXACT_CUTOFFS:
            for layers in (2, 3):
                with self.subTest(num_basis=num_basis, frequency=frequency,
                                  layers=layers, cutoff=why):
                    sim = _interface(layers, num_basis=num_basis)
                    sim.SetFrequency(frequency)
                    try:
                        self.assert_fresnel(sim)
                    except RuntimeError as exc:
                        self.assertTrue(
                            "singular interface" in str(exc) or
                            "non-finite" in str(exc),
                            "unexpected error at an exact cutoff: %s" % exc)

    def test_cutoff_neighbourhood_of_the_family_is_exact(self):
        for num_basis, frequency, why in EXACT_CUTOFFS:
            with self.subTest(num_basis=num_basis, frequency=frequency, cutoff=why):
                sim = _interface(3, num_basis=num_basis)
                sim.SetFrequency(frequency * (1.0 - 1e-12))
                self.assert_fresnel(sim)
                sim.SetFrequency(frequency * (1.0 + 1e-12))
                self.assert_fresnel(sim)


class PatternedCutoffTests(_FresnelAssertions, unittest.TestCase):
    """A patterned structure must not be forced onto the flat Fresnel answer."""

    def rt(self, num_basis, frequency):
        reflectance, transmittance = _rt(_patterned(num_basis, frequency))
        self.assertAlmostEqual(reflectance + transmittance, 1.0, delta=1e-10,
                               msg="lossless patterned slab must conserve energy")
        return reflectance, transmittance

    def test_exact_patterned_cutoff_is_explicit_or_bracketed(self):
        for num_basis in (9, 25):
            with self.subTest(num_basis=num_basis):
                low_r, _ = self.rt(num_basis, 1.0 - NEIGHBOUR)
                high_r, _ = self.rt(num_basis, 1.0 + NEIGHBOUR)
                sim = _patterned(num_basis, 1.0)
                try:
                    reflectance, transmittance = _rt(sim)
                except RuntimeError as exc:
                    self.assertIn("singular interface", str(exc))
                    continue
                self.assertAlmostEqual(reflectance + transmittance, 1.0, delta=1e-10)
                self.assertLessEqual(min(low_r, high_r) - BRACKET, reflectance)
                self.assertLessEqual(reflectance, max(low_r, high_r) + BRACKET)

    def test_patterned_cutoff_neighbourhood_is_smooth(self):
        # The one-sided values must approach each other as the cutoff is neared,
        # otherwise the exact point could not have a two-sided limit at all.
        for num_basis in (9, 25):
            with self.subTest(num_basis=num_basis):
                gaps = []
                for delta in (1e-4, 1e-6, 1e-8):
                    low_r, _ = self.rt(num_basis, 1.0 - delta)
                    high_r, _ = self.rt(num_basis, 1.0 + delta)
                    gaps.append(abs(low_r - high_r))
                # The one-sided gap shrinks as the cutoff is approached, which
                # is what makes a two-sided limit plausible.  The residual gap
                # is O(sqrt(delta)) with a large constant, hence the loose bound.
                self.assertLess(gaps[1], gaps[0])
                self.assertLess(gaps[2], gaps[1])
                self.assertLess(gaps[2], 1e-2)

    def test_patterned_repeats_are_deterministic(self):
        for num_basis in (9, 25):
            with self.subTest(num_basis=num_basis):
                sim = _patterned(num_basis, 1.0)
                outcomes = []
                for _ in range(4):
                    try:
                        outcomes.append(("value",) + _rt(sim))
                    except RuntimeError as exc:
                        outcomes.append(("error", str(exc)))
                self.assertEqual(len(set(map(str, outcomes))), 1,
                                 "repeated calls at the cutoff must agree")
                # Not raising is only acceptable when the flux is finite.
                if outcomes[0][0] == "value":
                    self.assertTrue(all(math.isfinite(x) for x in outcomes[0][1:]))

    def test_failed_cutoff_is_not_cached(self):
        # After the exact point fails, a neighbouring frequency on the same
        # simulation object must still return the correct answer.
        for num_basis in (9, 25):
            with self.subTest(num_basis=num_basis):
                sim = _patterned(num_basis, 1.0)
                try:
                    _rt(sim)
                except RuntimeError:
                    pass
                sim.SetFrequency(1.0 - NEIGHBOUR)
                first = _rt(sim)
                sim.SetFrequency(1.0 + NEIGHBOUR)
                second = _rt(sim)
                fresh_low = _rt(_patterned(num_basis, 1.0 - NEIGHBOUR))
                fresh_high = _rt(_patterned(num_basis, 1.0 + NEIGHBOUR))
                self.assertAlmostEqual(first[0], fresh_low[0], delta=1e-12)
                self.assertAlmostEqual(second[0], fresh_high[0], delta=1e-12)

    def test_cutoff_never_reports_a_non_finite_number(self):
        # At an exact cutoff an accessor may raise, or it may return a value
        # that agrees with the limit when the rounding happens to avoid the
        # zero pivot. What it must never do is hand back a NaN or an infinity.
        accessors = (
            ("GetPowerFlux", lambda sim: sim.GetPowerFlux("Above", 0.0)),
            ("GetPowerFluxByOrder", lambda sim: sim.GetPowerFluxByOrder("Below", 0.0)),
            ("GetAmplitudes", lambda sim: sim.GetAmplitudes("Below", 0.0)),
            ("GetSMatrixDeterminant", lambda sim: sim.GetSMatrixDeterminant()),
        )
        for num_basis in (9, 25):
            for name, accessor in accessors:
                with self.subTest(num_basis=num_basis, accessor=name):
                    sim = _patterned(num_basis, 1.0)
                    try:
                        value = accessor(sim)
                    except RuntimeError as exc:
                        self.assertTrue("singular interface" in str(exc) or
                                        "non-finite" in str(exc), str(exc))
                        continue
                    self.assertTrue(_all_finite(value),
                                    "%s returned a non-finite number at the cutoff" % name)


class AccessorAuditTests(_FresnelAssertions, unittest.TestCase):
    """Every accessor, on a fresh object, for every case in the matrix.

    A fresh object per accessor means an earlier failure or a cached result
    cannot mask the behaviour of a later call.  Cases are split by whether a
    retained order sits exactly at a cutoff: on valid parameters an accessor
    must return a correctly shaped finite result, while at a cutoff a finite
    result or one of the two known errors is acceptable.
    """

    def _check_result(self, case, name, value, num_basis):
        label = _case_label(case, name)
        expected = _expected_shape(name, num_basis)
        actual = _shape_of(value)
        self.assertEqual(actual, expected,
                         "%s returned shape %s, expected %s"
                         % (label, str(actual)[:90], str(expected)[:90]))
        finite, numbers, unchecked = _finite_scan(value)
        self.assertEqual(unchecked, 0, "%s returned a value of an unchecked type" % label)
        self.assertGreater(numbers, 0, "%s returned no numbers" % label)
        self.assertTrue(finite, "%s returned a non-finite component" % label)

    def _run_subset(self, expectation):
        visited = set()
        for case in CASE_MATRIX:
            if _expectation(case) != expectation:
                continue
            (kind, layers, num_basis, frequency, theta) = case
            for name, accessor in ACCESSORS:
                label = _case_label(case, name)
                with self.subTest(kind=kind, layers=layers, num_basis=num_basis,
                                  frequency=frequency, theta=theta, accessor=name):
                    sim = _case_sim(kind, layers, num_basis, frequency, theta)
                    try:
                        value = accessor(sim)
                    except RuntimeError as exc:
                        if expectation == "must_succeed":
                            self.fail("%s raised on valid parameters: %s" % (label, exc))
                        else:
                            self.assertTrue(
                                any(reason in str(exc) for reason in CUTOFF_ERROR_REASONS),
                                "%s raised an unrecognised error: %s" % (label, exc))
                    else:
                        self._check_result(case, name, value, num_basis)
                visited.add(case + (name,))
        return visited

    def _expected_visited(self, expectation):
        return set(case + (name,) for case in CASE_MATRIX
                   if _expectation(case) == expectation for name, _ in ACCESSORS)

    def test_ordinary_cases_succeed_for_every_accessor(self):
        expected = self._expected_visited("must_succeed")
        self.assertTrue(expected, "the must-succeed subset of the matrix is empty")
        self.assertEqual(self._run_subset("must_succeed"), expected,
                         "not every must-succeed case/accessor combination ran")

    def test_cutoff_cases_are_finite_or_a_known_error(self):
        expected = self._expected_visited("cutoff")
        self.assertTrue(expected, "the cutoff subset of the matrix is empty")
        self.assertEqual(self._run_subset("cutoff"), expected,
                         "not every cutoff case/accessor combination ran")

    def test_flat_successes_match_the_closed_form(self):
        expected, matched = set(), set()
        for case in CASE_MATRIX:
            (kind, layers, num_basis, frequency, theta) = case
            if kind != "flat" or _expectation(case) != "must_succeed":
                continue
            expected.add(case)
            expected_r, expected_t = fresnel_rt(1.0, 2.0, theta, "s")
            sim = _case_sim(kind, layers, num_basis, frequency, theta)
            with self.subTest(layers=layers, num_basis=num_basis,
                              frequency=frequency, theta=theta):
                incident, reflected = sim.GetPowerFlux("Above", 0.0)
                transmitted, _ = sim.GetPowerFlux("Below", 0.0)
                for value in (incident, reflected, transmitted):
                    self.assertTrue(math.isfinite(value.real) and
                                    math.isfinite(value.imag))
                self.assertAlmostEqual(-reflected.real / incident.real,
                                       expected_r, delta=1e-10)
                self.assertAlmostEqual(transmitted.real / incident.real,
                                       expected_t, delta=1e-10)
                matched.add(case)
        self.assertTrue(expected, "no flat case on valid parameters")
        self.assertEqual(matched, expected,
                         "every flat case on valid parameters must reproduce Fresnel")

    def test_patterned_ordinary_cases_succeed_and_conserve_energy(self):
        expected, matched = set(), set()
        for case in CASE_MATRIX:
            (kind, layers, num_basis, frequency, theta) = case
            if kind != "pattern" or _expectation(case) != "must_succeed":
                continue
            expected.add(case)
            sim = _case_sim(kind, layers, num_basis, frequency, theta)
            with self.subTest(num_basis=num_basis, frequency=frequency):
                incident, reflected = sim.GetPowerFlux("Above", 0.0)
                transmitted, _ = sim.GetPowerFlux("Below", 0.0)
                balance = (-reflected.real / incident.real
                           + transmitted.real / incident.real)
                self.assertAlmostEqual(balance, 1.0, delta=1e-10)
                matched.add(case)
        self.assertTrue(expected, "no patterned case on valid parameters")
        self.assertEqual(matched, expected,
                         "every patterned case on valid parameters must conserve energy")



class FailureRecoveryTests(unittest.TestCase):
    """A failed solve must not be cached and must not poison the object."""

    def _flux(self, sim):
        incident, reflected = sim.GetPowerFlux("Above", 0.0)
        transmitted, _ = sim.GetPowerFlux("Below", 0.0)
        return (-reflected.real / incident.real, transmitted.real / incident.real)

    def test_every_accessor_works_again_after_a_failed_cutoff(self):
        cases = (("flat", 3, 9, 1.0, 0.0),
                 ("flat", 2, 25, 1.0, 0.0),
                 ("pattern", 3, 9, 1.0, 0.0))
        for case in cases:
            (kind, layers, num_basis, frequency, theta) = case
            sim = _case_sim(kind, layers, num_basis, frequency, theta)
            # Provoke the failure through every accessor on the same object.
            for name, accessor in ACCESSORS:
                try:
                    accessor(sim)
                except RuntimeError:
                    pass
            # The same object, at a frequency with a defined answer, must be
            # fully usable again.
            sim.SetFrequency(1.25)
            for name, accessor in ACCESSORS:
                with self.subTest(kind=kind, num_basis=num_basis, accessor=name):
                    value = accessor(sim)
                    finite, numbers, unchecked = _finite_scan(value)
                    self.assertEqual(unchecked, 0,
                                     "%s returned an unchecked type after recovery" % name)
                    self.assertGreater(numbers, 0)
                    self.assertTrue(finite,
                                    "%s returned a non-finite value after recovery" % name)
            fresh = _case_sim(kind, layers, num_basis, 1.25, theta)
            recovered = self._flux(sim)
            reference = self._flux(fresh)
            self.assertAlmostEqual(recovered[0], reference[0], delta=1e-12)
            self.assertAlmostEqual(recovered[1], reference[1], delta=1e-12)


class AccessorOrderTests(unittest.TestCase):
    """An accessor outcome must not depend on which accessor ran first."""

    def outcomes(self, sim, names):
        table = _accessor_table()
        out = {}
        for name in names:
            try:
                value = table[name](sim)
            except RuntimeError as exc:
                out[name] = ("error", str(exc)[:70])
            else:
                finite, numbers, unchecked = _finite_scan(value)
                out[name] = ("ok", finite, numbers, unchecked, repr(value))
        return out

    def test_call_order_does_not_change_the_outcome(self):
        names = [name for name, _ in ACCESSORS]
        for (kind, layers, num_basis, frequency, theta) in (
                ("flat", 3, 9, 1.0, 0.0),
                ("flat", 3, 9, 0.5, 0.0),
                ("flat", 2, 25, 1.0, 0.0),
                ("flat", 2, 25, 0.8, 30.0),
                ("pattern", 3, 9, 1.0, 0.0),
                ("pattern", 3, 25, 1.0, 0.0)):
            with self.subTest(kind=kind, layers=layers, num_basis=num_basis,
                              frequency=frequency, theta=theta):
                forward = self.outcomes(
                    _case_sim(kind, layers, num_basis, frequency, theta), names)
                backward = self.outcomes(
                    _case_sim(kind, layers, num_basis, frequency, theta),
                    list(reversed(names)))
                self.assertEqual(forward, backward,
                                 "accessor outcome depends on call order")

    def test_repeated_reads_on_one_object_agree(self):
        for (kind, layers, num_basis, frequency, theta) in (
                ("flat", 3, 9, 1.0, 0.0),
                ("flat", 3, 9, 0.5, 0.0),
                ("pattern", 3, 9, 1.0, 0.0)):
            with self.subTest(kind=kind, num_basis=num_basis, frequency=frequency):
                sim = _case_sim(kind, layers, num_basis, frequency, theta)
                names = [name for name, _ in ACCESSORS]
                self.assertEqual(self.outcomes(sim, names),
                                 self.outcomes(sim, names),
                                 "repeated reads on one object disagree")


if __name__ == "__main__":
    unittest.main()
