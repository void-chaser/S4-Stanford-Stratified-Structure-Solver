"""Helpers for running the Lua frontend and comparing it against Python.

The Lua frontend prints sign conventions differently from Python:
``S:GetPoyntingFlux(layer, z)`` in the two-value form used by
``examples/2d/Fan_PRB_65_2002/fig12.lua`` returns the *net* flux along +z, which
is negative when the backward wave dominates.  The Python binding instead
returns the ``(forward, backward)`` pair.  Agreement between the two frontends
therefore has to be checked on a quantity both can express unambiguously --
the transmitted power ``T`` and the reflected power ``R`` normalised by the
incident power -- and never by comparing the raw printed numbers.

The Lua frontend is only an *interface consistency* check.  Python and Lua both
drive the same C++ core, so agreement between them says nothing about numerical
correctness; the analytic benchmarks in ``test_analytic_reference.py`` are what
establish that.  This is stated here so nobody later mistakes the cross-check
for a physical validation.
"""

import os
import subprocess

from s4test_common import REPO_ROOT

__all__ = ["lua_binary", "run_lua_example", "run_python_script", "parse_tsv"]

LUA_BINARY = os.path.join(REPO_ROOT, "build", "S4")


def lua_binary():
    """Absolute path to the compiled Lua frontend, or None if not built."""
    return LUA_BINARY if os.path.isfile(LUA_BINARY) else None


def run_lua_example(relative_path, timeout=300):
    """Run ``build/S4`` on a Lua file inside the repo and capture stdout.

    Returns ``(returncode, rows, stderr)`` where ``rows`` is a list of float
    tuples parsed from tab-separated numeric lines.  Comment lines and blank
    lines are ignored.
    """
    binary = lua_binary()
    if binary is None:
        raise RuntimeError("Lua frontend not built; run `make` to produce "
                           "build/S4")
    script = os.path.join(REPO_ROOT, relative_path)
    if not os.path.isfile(script):
        raise RuntimeError("example not found: %s" % script)
    proc = subprocess.run([binary, script], capture_output=True, text=True,
                          timeout=timeout, cwd=REPO_ROOT)
    return proc.returncode, parse_tsv(proc.stdout), proc.stderr


def run_python_script(script_path, timeout=300, env_extra=None):
    """Run a standalone Python script with the repo on sys.path.

    Returns ``(returncode, rows, stderr)``.
    """
    import sys
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [REPO_ROOT, os.path.dirname(os.path.abspath(script_path)),
         env.get("PYTHONPATH", "")])
    env["S4_TEST_REPO_ROOT"] = REPO_ROOT
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run([sys.executable, "-u", script_path],
                          capture_output=True, text=True, timeout=timeout,
                          env=env, cwd=REPO_ROOT)
    return proc.returncode, parse_tsv(proc.stdout), proc.stderr


def parse_tsv(text):
    """Parse tab-separated float rows, skipping blanks and ``#`` comments."""
    rows = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        try:
            rows.append(tuple(float(p) for p in parts))
        except ValueError:
            # Non-numeric output (a Lua error, say) is not a data row.
            continue
    return rows
