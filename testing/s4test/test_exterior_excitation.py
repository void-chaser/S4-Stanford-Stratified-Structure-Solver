"""Exterior-excitation ownership across create / clone / destroy.

Reproduces the reported failure:

    S4.SetExcitationExterior(((0, 'x', 1+0j),))
    clone = sim.Clone()
    del clone            -> double free or corruption

The excitation record owns two heap buffers (``exc.sub.exterior.Gindex1`` and
``exc.sub.exterior.coeff``) which are released by
``Simulation_SetExcitationType`` when the type changes and by
``S4_Simulation_Destroy``. Cloning must give the clone private buffers; sharing
them makes the second destructor free memory the first already released.

The four combinations that matter are covered explicitly: destroy clone first,
destroy original first, and for each of those, clone before and after the
original has been solved. A crash kills the interpreter, so every combination
runs in its own process via the isolation helper.
"""

import unittest

from s4test_common import run_isolated

#: Cases are registered in exterior_excitation_isolation.py
CASES = (
    "exterior_clone_then_destroy_clone",
    "exterior_clone_then_destroy_original",
    "exterior_solved_clone_then_destroy_clone",
    "exterior_solved_clone_then_destroy_original",
    "exterior_original_only",
    "exterior_clone_twice",
)


class ExteriorExcitationOwnershipTests(unittest.TestCase):

    def _run(self, case):
        res = run_isolated(case, module="exterior_excitation_isolation")
        self.assertNotEqual(
            res["verdict"], "crash",
            "isolated case %r aborted the interpreter (rc=%s, %s)"
            % (case, res["returncode"], res["stderr_tail"]))
        self.assertEqual(res["verdict"], "ok", res)
        return res

    def test_cases_are_registered(self):
        import exterior_excitation_isolation
        missing = [c for c in CASES
                   if c not in exterior_excitation_isolation.CASES]
        self.assertEqual(missing, [], "unregistered cases: %s" % missing)

    def test_destroy_clone_first(self):
        self._run("exterior_clone_then_destroy_clone")

    def test_destroy_original_first(self):
        self._run("exterior_clone_then_destroy_original")

    def test_solved_then_destroy_clone_first(self):
        self._run("exterior_solved_clone_then_destroy_clone")

    def test_solved_then_destroy_original_first(self):
        self._run("exterior_solved_clone_then_destroy_original")

    def test_original_alone_is_clean(self):
        """Control: without a clone the teardown must already be correct."""
        self._run("exterior_original_only")

    def test_two_clones(self):
        self._run("exterior_clone_twice")


class ExteriorExcitationValueTests(unittest.TestCase):
    """The clone must reproduce the excitation, not merely survive teardown."""

    def test_clone_matches_original_response(self):
        res = run_isolated("exterior_solved_clone_then_destroy_clone",
                           module="exterior_excitation_isolation")
        payload = res.get("result") or {}
        self.assertTrue(payload.get("clone_equivalent", False),
                        "clone response differs from the original: %r" % (payload,))


if __name__ == "__main__":
    unittest.main()
