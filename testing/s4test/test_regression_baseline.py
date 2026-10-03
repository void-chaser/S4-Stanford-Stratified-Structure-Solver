"""Stored numerical regression baseline.

The baseline lives in ``regression_data.json`` and is deliberately small (10
rows) and human-reviewable.  Each row records its physical parameters, the
expected value, a tolerance, how the expected value was produced, and -- for the
nine rows that have one -- the independent analytic reference it agrees with.

This module does two things:

1. replays every row against the current build;
2. cross-checks the rows that claim an analytic reference against
   ``analytic.py``, so a row cannot silently drift into being an
   S4-agrees-with-itself assertion.

The single row without an analytic reference
(``patterned_slab_photonic_crystal_num_basis_225``) is explicitly labelled as an
S4-only change guard in the JSON itself.  It detects regressions; it carries no
claim about physical correctness, and the test says so in its failure message.

Regenerating the baseline is a deliberate act: ``gen_regression_data.py``
rewrites it.  It is never updated automatically, because a baseline that updates
itself cannot detect anything.
"""

import json
import math
import os
import unittest

import S4

from analytic import airy_rt, fresnel_rt
from s4test_common import HERE

_BASELINE = os.path.join(HERE, "regression_data.json")


def _load():
    with open(_BASELINE, encoding="utf-8") as fh:
        return json.load(fh)


_BASELINE_DOC = _load()


def _n(value):
    """Refractive index from a scalar or [real, imag] permittivity."""
    if isinstance(value, list):
        return complex(value[0], value[1]) ** 0.5
    return complex(value)


def _rt_for_row(row):
    """Build and solve the structure described by a baseline row."""
    p = row["params"]
    if "lattice" in p:
        # Patterned case.
        sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=p["num_basis"])
        sim.AddMaterial("Above", 1)
        sim.AddMaterial("Slab", p["n_slab"] ** 2)
        sim.AddLayer("Above", 0, "Above")
        sim.AddLayer("Slab", p["slab_d"], "Slab")
        sim.SetRegionCircle("Slab", "Above", (0, 0), p["hole_radius"])
        sim.AddLayerCopy("Below", 0, "Above")
        sim.SetFrequency(p["freq"])
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        inc, refl = sim.GetPowerFlux("Above", 0.0)
        trans, _ = sim.GetPowerFlux("Below", 0.0)
        return inc.real, -refl.real, trans.real

    n_film = _n(p.get("n_film", 1.0)) if "eps_film" not in p else _n(p["eps_film"])
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=1)
    sim.AddMaterial("Above", complex(p["n_above"]) ** 2)
    sim.AddMaterial("Film", n_film ** 2)
    sim.AddMaterial("Below", complex(p["n_below"]) ** 2)
    sim.AddLayer("Above", 0, "Above")
    sim.AddLayer("Film", p["d"], "Film")
    sim.AddLayer("Below", 0, "Below")
    sim.SetFrequency(p["freq"])
    sim.SetExcitationPlanewave((p["theta_deg"], 0),
                               1 if p["polarization"] == "s" else 0,
                               0 if p["polarization"] == "s" else 1)
    inc, refl = sim.GetPowerFlux("Above", 0.0)
    trans, _ = sim.GetPowerFlux("Below", 0.0)
    return inc.real, -refl.real, trans.real


def _analytic_for_row(row):
    """The analytic reference named by the row, or None."""
    ref = row.get("analytic_ref")
    if not ref:
        return None
    p = row["params"]
    if ref.startswith("fresnel_rt"):
        return fresnel_rt(p["n_above"], _n(p["n_film"]), p["theta_deg"],
                          p["polarization"])
    if ref.startswith("airy_rt"):
        return airy_rt(p["d"], _n(p.get("n_film", 1.0)) if "eps_film" not in p
                       else _n(p["eps_film"]),
                       p["n_above"], p["n_below"], p["theta_deg"],
                       p["polarization"], p["freq"])
    raise AssertionError("unknown analytic_ref %r in row %s" % (ref, row["name"]))


class BaselineIntegrityTests(unittest.TestCase):
    """The baseline file itself must stay well-formed and self-describing."""

    def test_baseline_is_small_and_reviewable(self):
        rows = _BASELINE_DOC["rows"]
        self.assertLessEqual(len(rows), 20,
                             "keep the stored baseline small enough to review")
        self.assertGreaterEqual(len(rows), 5)

    def test_every_row_documents_its_provenance(self):
        for row in _BASELINE_DOC["rows"]:
            with self.subTest(row=row["name"]):
                for key in ("name", "params", "tol", "origin"):
                    self.assertIn(key, row)
                self.assertGreater(row["tol"], 0)
                self.assertTrue(row["origin"].strip(),
                                "each row must state how its value was obtained")

    def test_rows_without_an_analytic_reference_are_labelled(self):
        """A row with no independent reference must say so explicitly.

        This prevents an S4-only change guard from being mistaken for a
        physical validation.
        """
        for row in _BASELINE_DOC["rows"]:
            if row.get("analytic_ref"):
                continue
            with self.subTest(row=row["name"]):
                self.assertIn("S4 only", row["origin"],
                              "a row without an analytic reference must state "
                              "in 'origin' that it is an S4-only guard")
                self.assertIn("does NOT validate", row["origin"])

    def test_baseline_records_its_environment(self):
        env = _BASELINE_DOC["environment"]
        for key in ("os", "python", "compiler", "baseline_commit"):
            self.assertIn(key, env)


class BaselineReplayTests(unittest.TestCase):
    """Replay every stored row against the current build."""

    def test_replay_all_rows(self):
        for row in _BASELINE_DOC["rows"]:
            with self.subTest(row=row["name"]):
                inc, refl, trans = _rt_for_row(row)
                # S4's incident Poynting flux is cos(theta)/n_above, measured
                # over 24 combinations of n_above in {1, 1.5, 2, 3.5} and
                # theta in {0, 30, 60} degrees for both polarisations.  It is
                # neither cos(theta) (wrong whenever n_above != 1, by a factor
                # of exactly n_above) nor n_above*cos(theta) (which even the
                # sign of the error gets wrong).  Asserting either of those was
                # the bug this comment prevents.
                n_above = row["params"].get("n_above", 1.0)
                theta = row["params"].get("theta_deg", 0.0)
                self.assertAlmostEqual(
                    inc, math.cos(math.radians(theta)) / n_above, delta=1e-12)
                got_R = refl / inc
                got_T = trans / inc
                if "R" in row:
                    self.assertAlmostEqual(
                        got_R, row["R"], delta=row["tol"],
                        msg="R changed for baseline row %r (%s)"
                            % (row["name"], row["origin"]))
                if "T" in row:
                    self.assertAlmostEqual(
                        got_T, row["T"], delta=row["tol"],
                        msg="T changed for baseline row %r (%s)"
                            % (row["name"], row["origin"]))

    def test_rows_claiming_an_analytic_reference_really_have_one(self):
        """Verify the analytic value, not just S4's repeatability.

        Without this, a row could be recorded from a buggy build and then
        'pass' forever afterwards.
        """
        checked = 0
        for row in _BASELINE_DOC["rows"]:
            ref = _analytic_for_row(row)
            if ref is None:
                continue
            checked += 1
            with self.subTest(row=row["name"]):
                R_ref, T_ref = ref
                if "R" in row:
                    self.assertAlmostEqual(R_ref, row["R"], delta=row["tol"],
                                           msg="the analytic reference disagrees "
                                               "with the stored R for %r" % row["name"])
                if "T" in row:
                    self.assertAlmostEqual(T_ref, row["T"], delta=row["tol"],
                                           msg="the analytic reference disagrees "
                                               "with the stored T for %r" % row["name"])
        self.assertGreaterEqual(checked, 8,
                                "at least 8 rows should carry an analytic reference")


if __name__ == "__main__":
    unittest.main()
