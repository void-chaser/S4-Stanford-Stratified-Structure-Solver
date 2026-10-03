"""Lua ``S4_Simulation:GetFieldPlane``: output contract, error propagation, recovery.

The Lua frontend had no coverage at all for this entry point.  These tests pin
the behaviour that has to survive the resource-management fix:

* the two success shapes and the exact layout: ``Array`` returns **two** tables
  ``E[i][j][component][real, imaginary]`` indexed ``1..nu``, ``1..nv``, ``1..3``,
  ``1..2``, while ``FileWrite``/``FileAppend`` return **zero** values - a
  single-variable assignment then yields ``nil``, which is call semantics rather
  than a returned ``nil``;
* that both written files agree, component by component, with both array tables;
* that an append keeps every earlier byte and adds rows carrying ``z``;
* that a failure is a *Lua error* (catchable by ``pcall``), not a process exit,
  not a silent success and above all not a signal;
* that the two output files keep their declared semantics (``.E`` may survive a
  ``.H`` failure, no rollback).

What these tests deliberately do **not** claim:

* The "the object still works afterwards" assertions prove only that the
  simulation object stays usable.  They are **not** a leak check.  Per-call leak
  behaviour is established separately, by the LeakSanitizer scenarios recorded
  in ``DEFECTS.md`` D13: the empty script, 3 successes, 300 successes, and 300
  caught failures at each of the three allocation points, all inside a single
  process, with a positive control proving the detector was live.
* Failures this binding controls (input validation, allocation, the core
  solution, a non-finite grid, file open/write/close) release the native buffers
  and only then raise.  A memory error raised by Lua *itself* while the result
  tables are built cannot be released before the raise; the owner userdata frees
  those buffers when it is collected.  That path needs a test-only Lua allocator
  and is **not** automatically verified here, so it is not counted as passing.
* A non-finite grid can arise for several reasons, a retained order landing
  exactly on a diffraction cutoff being one of them.  The tests assert only that
  such a grid is reported instead of being returned or written; they make no
  general claim about which physical configurations are defined.

The pre-fix frontend crashes with SIGSEGV on an unopenable output path, silently
returns NaN tables and silently writes NaN files, silently truncates a
fractional grid count, hangs on a grid whose byte size overflows ``size_t``, and
exits the whole process on a core failure so that ``pcall`` cannot catch it.

Lua source is assembled with ``str.replace`` on ``__NAME__`` placeholders rather
than ``%`` formatting, because the scripts legitimately contain ``%s`` and
``%.17g`` format specifiers of their own.
"""

import os
import subprocess
import unittest

from s4test_common import REPO_ROOT, temp_workspace
from lua_frontend import lua_binary

#: A flat Air / spacer / Below stack.  ``frequency = sqrt(2)`` puts a retained
#: order exactly on a diffraction cutoff and makes the interface solve singular
#: in every optimisation level we test; ``below = 0`` gives a layer whose
#: longitudinal wavevector is exactly zero, so the sampled grid is an exact 0/0
#: rather than an approximately singular value.
PREAMBLE = """
local function stack(freq, below)
  local S = S4.NewSimulation()
  S:SetLattice({1,0},{0,1})
  S:SetNumG(9)
  S:AddMaterial("Air", {1,0})
  S:AddMaterial("Below", {below,0})
  S:AddLayer('Above', 0, 'Air')
  S:AddLayer('Spacer', 0, 'Air')
  S:AddLayer('Bottom', 0.5, 'Below')
  S:SetExcitationPlanewave({0,0}, {1,0}, {0,0})
  S:SetFrequency(freq)
  return S
end
local CUTOFF = math.sqrt(2.0)
local function finite(v)
  if type(v) == 'table' then
    for _, x in ipairs(v) do if not finite(x) then return false end end
    return true
  end
  return v == v and v ~= math.huge and v ~= -math.huge
end
"""


def fill(template, **values):
    for key, value in values.items():
        template = template.replace("__%s__" % key, str(value))
    return template


def run_lua(source, workspace, timeout=90, script_name="case.lua"):
    """Run a Lua script with the repo's ``build/S4``; return (rc, out, err).

    ``returncode`` is negative when the child died from a signal, which is how
    the tests tell a crash apart from a reported failure.  ``script_name`` lets
    one test make several separate invocations in the same workspace.
    """
    binary = lua_binary()
    if binary is None:
        raise AssertionError(
            "the Lua frontend is not built; `make` must produce build/S4 "
            "before these Lua tests can run")
    script = os.path.join(workspace, script_name)
    with open(script, "w") as handle:
        handle.write(source)
    proc = subprocess.run([binary, script], capture_output=True, text=True,
                          timeout=timeout, cwd=REPO_ROOT)
    return proc.returncode, proc.stdout, proc.stderr


def produced_files(workspace):
    """Everything the run left behind apart from the generated scripts."""
    return sorted(name for name in os.listdir(workspace) if not name.endswith(".lua"))


class FieldPlaneSuccessTests(unittest.TestCase):
    def test_array_shape_and_finiteness_for_1x1_and_4x3(self):
        for nu, nv in ((1, 1), (4, 3)):
            with self.subTest(num_samples=(nu, nv)), temp_workspace() as tmp:
                rc, out, err = run_lua(fill(PREAMBLE + """
local E, H = stack(0.999, 4):GetFieldPlane(0.0, {__NU__,__NV__}, 'Array')
print('shape', #E, #E[1], #E[1][1], #E[1][1][1])
print('finite', tostring(finite(E) and finite(H)))
local n = 0
for i=1,#E do for j=1,#E[i] do for c=1,#E[i][j] do n = n + #E[i][j][c] end end end
print('components', n)
""", NU=nu, NV=nv), tmp)
                self.assertEqual(rc, 0, err)
                self.assertIn("shape\t%d\t%d\t3\t2" % (nu, nv), out)
                self.assertIn("finite\ttrue", out)
                reported = int([l for l in out.splitlines()
                                if l.startswith("components")][0].split()[1])
                self.assertEqual(nu * nv * 3 * 2, reported)
                self.assertEqual(produced_files(tmp), [])

    def test_filewrite_rows_match_both_array_tables(self):
        """Both files are checked against the array result, component by component."""
        with temp_workspace() as tmp:
            base = os.path.join(tmp, "g")
            rc, out, err = run_lua(fill(PREAMBLE + """
local S1 = stack(0.999, 4)
local E, H = S1:GetFieldPlane(0.0, {4,3}, 'Array')
print('shape', #E, #E[1], #E[1][1], #E[1][1][1], #H, #H[1], #H[1][1], #H[1][1][1])
for _, pair in ipairs({{'E', E}, {'H', H}}) do
  local tag, field = pair[1], pair[2]
  for i=1,#field do for j=1,#field[i] do for c=1,#field[i][j] do
    local p = field[i][j][c]
    print(string.format('%s %d %d %d %.17g %.17g', tag, i-1, j-1, c-1, p[1], p[2]))
  end end end
end
S1:GetFieldPlane(0.0, {4,3}, 'FileWrite', '__BASE__')
""", BASE=base), tmp)
            self.assertEqual(rc, 0, err)
            # Both returned tables must have the complete shape, not just E.
            self.assertIn("shape\t4\t3\t3\t2\t4\t3\t3\t2", out)
            expected = {"E": {}, "H": {}}
            for line in out.splitlines():
                parts = line.split()
                if parts and parts[0] in ("E", "H"):
                    expected[parts[0]][(int(parts[1]), int(parts[2]), int(parts[3]))] = (
                        float(parts[4]), float(parts[5]))
            for tag in ("E", "H"):
                self.assertEqual(len(expected[tag]), 4 * 3 * 3, "%s components" % tag)
            for tag in ("E", "H"):
                with self.subTest(field=tag):
                    with open(base + "." + tag) as handle:
                        rows = [line for line in handle.read().split("\n") if line.strip()]
                    self.assertEqual(len(rows), 12,
                                     "a 4x3 grid has 12 non-empty data rows")
                    seen = set()
                    for row in rows:
                        fields = row.split("\t")
                        self.assertEqual(len(fields), 8, "FileWrite writes 8 fields")
                        i, j = int(fields[0]), int(fields[1])
                        self.assertTrue(0 <= i < 4 and 0 <= j < 3,
                                        "grid coordinate out of range: %s" % row)
                        seen.add((i, j))
                        for c in range(3):
                            re_, im_ = expected[tag][(i, j, c)]
                            self.assertAlmostEqual(float(fields[2 + 2 * c]), re_,
                                                   places=12)
                            self.assertAlmostEqual(float(fields[3 + 2 * c]), im_,
                                                   places=12)
                    self.assertEqual(len(seen), 12,
                                     "every (i, j) appears exactly once")

    def test_fileappend_preserves_the_existing_bytes_and_adds_z(self):
        """The append must keep every earlier byte, not merely make the file longer."""
        with temp_workspace() as tmp:
            base = os.path.join(tmp, "g")
            rc, out, err = run_lua(fill(PREAMBLE + """
stack(0.999, 4):GetFieldPlane(0.0, {4,3}, 'FileWrite', '__BASE__')
print('written')
""", BASE=base), tmp, script_name="write.lua")
            self.assertEqual(rc, 0, err)
            before = {}
            for tag in ("E", "H"):
                with open(base + "." + tag, "rb") as handle:
                    before[tag] = handle.read()
                self.assertGreater(len(before[tag]), 0, "%s was not written" % tag)
            # A separate invocation appends, which is also the real use case.
            rc, out, err = run_lua(fill(PREAMBLE + """
stack(0.999, 4):GetFieldPlane(0.25, {4,3}, 'FileAppend', '__BASE__')
print('appended')
""", BASE=base), tmp, script_name="append.lua")
            self.assertEqual(rc, 0, err)
            for tag in ("E", "H"):
                with self.subTest(field=tag):
                    with open(base + "." + tag, "rb") as handle:
                        after = handle.read()
                    self.assertTrue(after.startswith(before[tag]),
                                    "the append changed earlier bytes of %s" % tag)
                    added = after[len(before[tag]):]
                    self.assertGreater(len(added), 0, "the append added nothing")
                    rows = [line for line in added.decode().split("\n") if line.strip()]
                    self.assertEqual(len(rows), 12,
                                     "an append adds 12 data rows for a 4x3 grid")
                    for row in rows:
                        fields = row.split("\t")
                        self.assertEqual(len(fields), 9, "an appended row carries z")
                        self.assertAlmostEqual(float(fields[2]), 0.25, places=12)

    def test_file_formats_return_no_values(self):
        """'No values' means zero results, not a single nil result."""
        with temp_workspace() as tmp:
            base = os.path.join(tmp, "g")
            rc, out, err = run_lua(fill(PREAMBLE + """
local S1 = stack(0.999, 4)
local nwrite = select('#', S1:GetFieldPlane(0.0, {2,2}, 'FileWrite', '__BASE__'))
local nappend = select('#', S1:GetFieldPlane(0.0, {2,2}, 'FileAppend', '__BASE__'))
-- A one-variable assignment from a zero-result call yields nil; that is
-- assignment semantics, so it is recorded but not asserted as a return value.
local single = S1:GetFieldPlane(0.0, {2,2}, 'FileWrite', '__BASE__')
print('counts', nwrite, nappend)
print('single', tostring(single))
""", BASE=base), tmp)
            self.assertEqual(rc, 0, err)
            self.assertIn("counts\t0\t0", out)
            self.assertIn("single\tnil", out)


class FieldPlaneFailureTests(unittest.TestCase):
    def test_missing_parent_directory_is_a_reported_error(self):
        with temp_workspace() as tmp:
            missing = os.path.join(tmp, "no_such_dir", "g")
            rc, out, err = run_lua(fill(PREAMBLE + """
stack(0.999, 4):GetFieldPlane(0.0, {4,3}, 'FileWrite', '__BASE__')
print('NO-ERROR-RAISED')
""", BASE=missing), tmp)
            self.assertGreater(rc, 0, "must fail rather than crash; stderr=%r" % err[-200:])
            self.assertNotIn("NO-ERROR-RAISED", out)
            self.assertIn("GetFieldPlane", err)
            self.assertIn("could not open", err)
            self.assertIn("no_such_dir", err)
            self.assertEqual(produced_files(tmp), [])

    def test_e_and_h_open_failures_are_reported_separately(self):
        for blocked, kept in (("g.E", None), ("g.H", "g.E")):
            with self.subTest(blocked=blocked), temp_workspace() as tmp:
                base = os.path.join(tmp, "g")
                os.mkdir(base + "." + blocked[-1])
                rc, out, err = run_lua(fill(PREAMBLE + """
stack(0.999, 4):GetFieldPlane(0.0, {4,3}, 'FileWrite', '__BASE__')
print('NO-ERROR-RAISED')
""", BASE=base), tmp)
                self.assertGreater(rc, 0, "must fail rather than crash; stderr=%r" % err[-200:])
                self.assertNotIn("NO-ERROR-RAISED", out)
                self.assertIn("could not open", err)
                self.assertIn(blocked, err)
                if kept is not None:
                    # .E was written before .H failed; there is no rollback.
                    self.assertGreater(os.path.getsize(os.path.join(tmp, kept)), 0)

    def test_write_failure_on_a_full_device_is_reported(self):
        if not os.path.exists("/dev/full"):
            self.skipTest("/dev/full is not available on this host")
        for fmt in ("FileWrite", "FileAppend"):
            with self.subTest(format=fmt), temp_workspace() as tmp:
                base = os.path.join(tmp, "full")
                os.symlink("/dev/full", base + ".E")
                rc, out, err = run_lua(fill(PREAMBLE + """
stack(0.999, 4):GetFieldPlane(0.0, {4,3}, '__FMT__', '__BASE__')
print('NO-ERROR-RAISED')
""", FMT=fmt, BASE=base), tmp)
                self.assertGreater(rc, 0, "must fail rather than crash; stderr=%r" % err[-200:])
                self.assertNotIn("NO-ERROR-RAISED", out)
                self.assertIn("full.E", err)

    def test_core_failure_is_catchable_and_writes_nothing(self):
        with temp_workspace() as tmp:
            base = os.path.join(tmp, "g")
            rc, out, err = run_lua(fill(PREAMBLE + """
local S1 = stack(CUTOFF, 4)
local ok, msg = pcall(function() return S1:GetFieldPlane(0.1, {4,3}, 'Array') end)
print('array-caught', tostring(ok), tostring(tostring(msg):find('GetFieldPlane') ~= nil))
local ok2, msg2 = pcall(function() return S1:GetFieldPlane(0.1, {4,3}, 'FileWrite', '__BASE__') end)
print('file-caught', tostring(ok2), tostring(tostring(msg2):find('GetFieldPlane') ~= nil))
""", BASE=base), tmp)
            self.assertEqual(rc, 0, err)
            self.assertIn("array-caught\tfalse\ttrue", out)
            self.assertIn("file-caught\tfalse\ttrue", out)
            self.assertEqual(produced_files(tmp), [])

    def test_non_finite_grid_is_rejected_and_writes_nothing(self):
        with temp_workspace() as tmp:
            base = os.path.join(tmp, "g")
            rc, out, err = run_lua(fill(PREAMBLE + """
local S1 = stack(0.5, 0)
local ok, msg = pcall(function() return S1:GetFieldPlane(0.1, {4,3}, 'Array') end)
print('array', tostring(ok), tostring(tostring(msg):find('non%-finite') ~= nil))
local ok2, msg2 = pcall(function() return S1:GetFieldPlane(0.1, {4,3}, 'FileWrite', '__BASE__') end)
print('file', tostring(ok2), tostring(tostring(msg2):find('non%-finite') ~= nil))
""", BASE=base), tmp)
            self.assertEqual(rc, 0, err)
            self.assertIn("array\tfalse\ttrue", out)
            self.assertIn("file\tfalse\ttrue", out)
            self.assertEqual(produced_files(tmp), [])

    def test_invalid_grid_sizes_are_rejected_without_hanging(self):
        cases = (("{0,8}", "integers"), ("{-1,8}", "integers"), ("{2^40,2}", "integers"),
                 ("{2.5,2}", "integers"), ("{2^31-1,2^31-1}", "too large"))
        for spec, needle in cases:
            with self.subTest(num_samples=spec), temp_workspace() as tmp:
                try:
                    rc, out, err = run_lua(fill(PREAMBLE + """
stack(0.999, 4):GetFieldPlane(0.0, __SPEC__, 'Array')
print('NO-ERROR-RAISED')
""", SPEC=spec), tmp, timeout=45)
                except subprocess.TimeoutExpired:
                    self.fail("GetFieldPlane(%s) hung instead of rejecting the grid" % spec)
                self.assertGreater(rc, 0, "must reject rather than crash; stderr=%r" % err[-200:])
                self.assertNotIn("NO-ERROR-RAISED", out)
                self.assertIn(needle, err)

    def test_uncaught_failure_exits_nonzero_without_a_signal(self):
        with temp_workspace() as tmp:
            rc, out, err = run_lua(PREAMBLE + """
stack(CUTOFF, 4):GetFieldPlane(0.1, {4,3}, 'Array')
print('NO-ERROR-RAISED')
""", tmp)
            self.assertGreater(rc, 0, "an uncaught batch failure must exit non-zero")
            self.assertLess(rc, 128, "it must not die from a signal")
            self.assertIn("GetFieldPlane", err)
            self.assertNotIn("NO-ERROR-RAISED", out)

    def test_object_recovers_after_a_failure(self):
        with temp_workspace() as tmp:
            base = os.path.join(tmp, "g")
            rc, out, err = run_lua(fill(PREAMBLE + """
local S1 = stack(CUTOFF, 4)
local ok = pcall(function() return S1:GetFieldPlane(0.1, {4,3}, 'Array') end)
print('first-call-caught', tostring(not ok))
S1:SetFrequency(0.999)
local E, H = S1:GetFieldPlane(0.0, {4,3}, 'Array')
print('array-after', #E, tostring(finite(E)))
local r = S1:GetFieldPlane(0.0, {2,2}, 'FileWrite', '__BASE__')
print('file-after', tostring(r))
""", BASE=base), tmp)
            self.assertEqual(rc, 0, err)
            self.assertIn("first-call-caught\ttrue", out)
            self.assertIn("array-after\t4\ttrue", out)
            self.assertIn("file-after\tnil", out)
            self.assertGreater(os.path.getsize(base + ".E"), 0)

    def test_repeated_failures_never_report_success(self):
        with temp_workspace() as tmp:
            base = os.path.join(tmp, "g")
            rc, out, err = run_lua(fill(PREAMBLE + """
local S1 = stack(CUTOFF, 4)
local caught, succeeded = 0, 0
for n=1,25 do
  local ok = pcall(function() return S1:GetFieldPlane(0.1, {4,3}, 'FileWrite', '__BASE__') end)
  if ok then succeeded = succeeded + 1 else caught = caught + 1 end
end
print('caught', caught, 'succeeded', succeeded)
S1:SetFrequency(0.999)
local E = S1:GetFieldPlane(0.0, {2,2}, 'Array')
print('final-ok', tostring(#E == 2))
""", BASE=base), tmp)
            self.assertEqual(rc, 0, err)
            self.assertIn("caught\t25\tsucceeded\t0", out)
            self.assertIn("final-ok\ttrue", out)
            self.assertEqual(produced_files(tmp), [])

    def test_argument_type_errors_are_reported(self):
        cases = (
            ("stack(0.999, 4):GetFieldPlane(0.0, {2,2})", "string expected"),
            ("stack(0.999, 4):GetFieldPlane(0.0, 'not_a_table', 'Array')",
             "pair of grid sample counts"),
            ("stack(0.999, 4):GetFieldPlane(0.0, {'a','b'}, 'Array')", "must be numbers"),
        )
        for call, needle in cases:
            with self.subTest(call=call), temp_workspace() as tmp:
                rc, out, err = run_lua(PREAMBLE + call + "\nprint('NO-ERROR-RAISED')\n", tmp)
                self.assertGreater(rc, 0, "must reject rather than crash; stderr=%r" % err[-200:])
                self.assertNotIn("NO-ERROR-RAISED", out)
                self.assertIn(needle, err)


if __name__ == "__main__":
    unittest.main()
