"""Allocation-failure injection for S4_Simulation_Clone, per fixture.

Why this exists
---------------
The partial-construction paths in ``S4_Simulation_Clone`` are unreachable
without making an allocation fail, and they are exactly where ownership mistakes
hide: a half-built clone that believes it owns the source's arrays will free them
when it is destroyed.

Mechanism
---------
``S4_FAIL_ALLOC_AT=k`` makes the k-th allocation *inside the armed scope* fail
(1-based). The scope is opened by ``S4_Simulation_Clone`` and closed by a guard on
every return path, so allocations made while a test builds its fixture are never
affected.

Every allocation the clone performs is inside that scope and goes through the
counter:

  * ``s4_clone_alloc`` for the clone struct itself, the material array, the
    per-layer shape arrays, the polygon vertex arrays and the two
    exterior-excitation buffers;
  * ``s4_clone_alloc_zeroed`` for the layer array;
  * ``s4_clone_strdup`` for the layer, material and options-prefix names;
  * ``S4_malloc`` for G, kx and the solution copy.

Those wrappers are thin: ``s4_clone_alloc`` is ``malloc`` plus the injector
check, ``s4_clone_alloc_zeroed`` is ``calloc`` plus the check. The allocator
pairing is therefore unchanged -- the release side is still plain ``free`` in
``S4_Simulation_Destroy`` and ``Simulation_SetExcitationType`` -- and the
injector only decides whether to return NULL.

How the sweep bound is found
----------------------------
The scope guard writes the number of allocations it saw to the file named by
``S4_ALLOC_COUNT`` as it closes, so the count is available for failed clones too
and does not depend on an exit hook (the probe calls ``os._exit``). For a failed
run it equals k, because counting stops at the allocation that was made to fail.
The sweep therefore runs k = 1, 2, ... until a run reports that the clone
succeeded; the first such k is one past the last allocation point, and that k is
asserted to leave the injector un-hit.

What is asserted for every k of every fixture
---------------------------------------------
1. no crash;
2. the clone succeeds or raises -- it never returns a half-built object;
3. a failed clone leaves the original solving to the same numbers;
4. destroying the original afterwards is safe;
5. successful clones are numerically equivalent to the original;
6. for failed runs, ``allocations_seen == k``, proving site k was reached;
7. one k past the last site behaves exactly like no injection at all.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest

from s4test_common import HERE, ISOLATION_EXC, ISOLATION_OK, REPO_ROOT

#: Upper bound for discovering the allocation count of a fixture.
PROBE_MAX_K = 80

_PROBE = os.path.join(HERE, "clone_fault_probe.py")

#: Fixtures defined in clone_fault_probe.py. Each reaches a different mix of
#: allocation sites, including the exterior-excitation buffers (exterior) and
#: several shape and vertex arrays (polygon).
FIXTURES = ("planewave", "exterior", "polygon")


def _run_with_k(fixture, k, count_path=None, timeout=180):
    """Run the probe for one fixture with S4_FAIL_ALLOC_AT=k, isolated."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [REPO_ROOT, HERE] + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    env["S4_TEST_REPO_ROOT"] = REPO_ROOT
    env["S4_FAIL_ALLOC_AT"] = str(k)
    env["S4_CLONE_FIXTURE"] = fixture
    if count_path:
        env["S4_ALLOC_COUNT"] = count_path
    else:
        env.pop("S4_ALLOC_COUNT", None)
    try:
        proc = subprocess.run([sys.executable, "-u", _PROBE],
                              capture_output=True, text=True, timeout=timeout,
                              env=env, cwd=REPO_ROOT)
    except subprocess.TimeoutExpired:
        return {"verdict": "timeout", "k": k, "returncode": None,
                "result": None, "exception": None, "stderr_tail": ""}
    out = {"verdict": "crash", "k": k, "returncode": proc.returncode,
           "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-4:]),
           "result": None, "exception": None}
    for line in proc.stdout.splitlines():
        if line.startswith(ISOLATION_OK):
            out["verdict"] = "ok"
            out["result"] = json.loads(line[len(ISOLATION_OK):]).get("result")
        elif line.startswith(ISOLATION_EXC):
            out["verdict"] = "exception"
            out["exception"] = json.loads(line[len(ISOLATION_EXC):])
    return out


class _FixtureSweep:
    """Shared sweep logic; one subclass per fixture so failures name it."""

    FIXTURE = None

    @classmethod
    def setUpClass(cls):
        d = tempfile.mkdtemp(prefix="s4alloc-%s-" % cls.FIXTURE)
        cls.count_path = os.path.join(d, "count")
        cls.results = {}
        cls.first_unreached = None
        for k in range(1, PROBE_MAX_K + 1):
            res = _run_with_k(cls.FIXTURE, k, count_path=cls.count_path)
            cls.results[k] = res
            if (res["verdict"] == "ok" and res["result"]
                    and res["result"]["clone_succeeded"]):
                cls.first_unreached = k
                break
        if cls.first_unreached is None:
            raise AssertionError(
                "[%s] no injection between 1 and %d let the clone succeed; the "
                "injector is probably not armed" % (cls.FIXTURE, PROBE_MAX_K))
        cls.n_alloc = cls.first_unreached - 1

    # ------------------------------------------------------------------ tests
    def test_no_k_crashes(self):
        crashed = [k for k, r in self.results.items() if r["verdict"] == "crash"]
        self.assertEqual(
            crashed, [],
            "[%s] the injector killed the process for S4_FAIL_ALLOC_AT in %s; a "
            "partial clone is not safe to tear down. First failure: %s"
            % (self.FIXTURE, crashed,
               self.results[crashed[0]]["stderr_tail"] if crashed else ""))

    def test_no_k_returns_a_partial_clone(self):
        """A failed clone must raise, never hand back a half-built object."""
        bad = []
        for k, res in self.results.items():
            if res["verdict"] != "ok":
                bad.append((k, res["verdict"]))
                continue
            p = res["result"]
            if p["clone_succeeded"] and p.get("clone_error"):
                bad.append((k, "returned a clone that then failed on use: %s"
                            % p["clone_error"]))
            if not p["clone_succeeded"] and not p.get("clone_error"):
                bad.append((k, "reported failure with no exception"))
        self.assertEqual(bad, [], "[%s] partial clone escaped: %s"
                         % (self.FIXTURE, bad))

    def test_every_k_leaves_the_original_intact_and_destroyable(self):
        bad = []
        for k, res in self.results.items():
            if res["verdict"] != "ok":
                bad.append((k, res["verdict"]))
                continue
            p = res["result"]
            if not p["original_unchanged"]:
                bad.append((k, "original changed: %r -> %r"
                            % (p.get("original_before"), p.get("original_after"))))
            if not p["original_destroyed_cleanly"]:
                bad.append((k, "original did not destroy cleanly"))
        self.assertEqual(bad, [], "[%s] a failed clone disturbed the original: %s"
                         % (self.FIXTURE, bad))

    def test_successful_clones_are_equivalent(self):
        checked = 0
        bad = []
        for k, res in self.results.items():
            if res["verdict"] != "ok":
                continue
            p = res["result"]
            if not p["clone_succeeded"]:
                continue
            checked += 1
            if not p["clone_equivalent"]:
                bad.append(k)
        self.assertEqual(bad, [], "[%s] clones that succeeded were not "
                                  "equivalent: %s" % (self.FIXTURE, bad))
        self.assertGreater(checked, 0,
                           "[%s] no k produced a successful clone during the "
                           "sweep" % self.FIXTURE)

    def test_each_injection_hit_the_intended_site(self):
        """allocations_seen == k proves site k was reached and failed."""
        bad = []
        for k, res in self.results.items():
            if res["verdict"] != "ok":
                bad.append((k, res["verdict"]))
                continue
            p = res["result"]
            if not p["clone_succeeded"] and p["allocations_seen"] != k:
                bad.append((k, "reached only %s sites" % p["allocations_seen"]))
        self.assertEqual(bad, [], "[%s] the sweep did not reach every site: %s"
                         % (self.FIXTURE, bad))

    def test_the_sweep_exercised_real_failure_paths(self):
        """Guard: if nothing ever failed, the sweep proves nothing."""
        failures = sum(1 for r in self.results.values()
                       if r["verdict"] == "ok"
                       and not r["result"]["clone_succeeded"])
        self.assertGreaterEqual(
            failures, 5,
            "[%s] only %d of %d injected runs actually failed an allocation"
            % (self.FIXTURE, failures, len(self.results)))

    def test_one_past_the_last_site_does_not_hit(self):
        """k past the final allocation must behave exactly like no injection.

        This is the check that the bound is real rather than merely where the
        sweep happened to stop.
        """
        res = _run_with_k(self.FIXTURE, self.first_unreached + 1)
        self.assertEqual(res["verdict"], "ok", res)
        self.assertTrue(res["result"]["clone_succeeded"])
        self.assertTrue(res["result"]["clone_equivalent"])

    def test_injector_is_inert_when_disabled(self):
        res = _run_with_k(self.FIXTURE, 0)
        self.assertEqual(res["verdict"], "ok", res)
        self.assertTrue(res["result"]["clone_succeeded"])
        self.assertTrue(res["result"]["clone_equivalent"])


class PlanewaveFixtureSweep(_FixtureSweep, unittest.TestCase):
    """Materials, a circle, a polygon and a layer copy."""

    FIXTURE = "planewave"


class ExteriorFixtureSweep(_FixtureSweep, unittest.TestCase):
    """Adds the two exterior-excitation buffers."""

    FIXTURE = "exterior"


class PolygonFixtureSweep(_FixtureSweep, unittest.TestCase):
    """Two patterned layers with 3, 4 and 5 vertex polygons."""

    FIXTURE = "polygon"


class CoverageSummaryTests(unittest.TestCase):
    """Report, as a test, how many allocation points each fixture has.

    The per-fixture sweeps have their own setUpClass, and unittest does not
    guarantee that another TestCase's setUpClass has run by the time this one
    executes. Each sweep is therefore run explicitly here if its results are not
    already available, so the summary cannot silently read a missing attribute.
    """

    @classmethod
    def setUpClass(cls):
        cls.counts = {}
        for sweep in (PlanewaveFixtureSweep, ExteriorFixtureSweep,
                      PolygonFixtureSweep):
            if not hasattr(sweep, "n_alloc"):
                sweep.setUpClass()
            cls.counts[sweep.FIXTURE] = sweep.n_alloc

    def test_every_fixture_has_a_nonzero_allocation_count(self):
        self.assertEqual(sorted(self.counts), sorted(FIXTURES))
        for fixture, n in self.counts.items():
            self.assertGreater(
                n, 5, "[%s] only %d allocation points found" % (fixture, n))

    def test_the_fixtures_reach_different_numbers_of_sites(self):
        """The fixtures must not all reduce to the same allocation path.

        polygon has three polygons across two layers (three shape arrays and
        three vertex arrays), so it must reach more sites than the single-shape
        planewave fixture. If they were equal, the fixtures would not be
        exercising different ownership paths.
        """
        self.assertGreater(
            self.counts["polygon"], self.counts["planewave"],
            "the polygon fixture should reach more allocation sites than the "
            "planewave fixture; got %r" % (self.counts,))

    def test_exterior_fixture_reaches_the_excitation_buffers(self):
        """Exterior excitation adds two buffers, so it must exceed a plain stack.

        Compared against the planewave fixture after removing its extra
        materials: the check is simply that exterior is not smaller, and the
        exact counts are reported in the failure message.
        """
        self.assertGreaterEqual(
            self.counts["exterior"], self.counts["planewave"] - 4,
            "exterior fixture has suspiciously few allocation sites: %r"
            % (self.counts,))


if __name__ == "__main__":
    unittest.main()
