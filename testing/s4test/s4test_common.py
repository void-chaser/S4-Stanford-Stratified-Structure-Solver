"""Shared helpers for the S4 test-suite.

Two things live here that several test modules need:

1. ``build_uniform_stack`` / ``read_rt`` -- the canonical way this suite builds
   a planar stack and converts S4's signed power fluxes into ``(R, T)``.
   Keeping this in one place means the sign convention documented in
   ``analytic.py`` is applied identically everywhere.

2. ``run_isolated`` -- runs a callable in a *separate interpreter process* so
   that a hard crash (SIGSEGV/SIGABRT) is reported as a failed test instead of
   killing the whole test run.  This is required for interface functions that
   are known to be able to abort the process; see ``test_api_robustness.py``.
"""

import base64
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def _detect_repo_root():
    """Locate the checkout that owns the built ``S4`` extension.

    ``S4`` must be importable for any test to run, and ``make S4_pyext`` places
    the extension in the repository root, so that is the authoritative source.
    Callers can override with the ``S4_TEST_REPO_ROOT`` environment variable.
    """
    override = os.environ.get("S4_TEST_REPO_ROOT")
    if override:
        return os.path.abspath(override)
    try:
        import S4
    except ImportError:
        # Fall back to assuming this file lives in <repo>/testing/s4test.
        return os.path.dirname(os.path.dirname(HERE))
    return os.path.dirname(os.path.abspath(S4.__file__))


REPO_ROOT = _detect_repo_root()

__all__ = [
    "HERE",
    "REPO_ROOT",
    "build_uniform_stack",
    "read_rt",
    "read_flux",
    "run_isolated",
    "ISOLATION_PROBE_MODULE",
    "ISOLATION_STARTED",
    "ISOLATION_OK",
    "ISOLATION_EXC",
    "ISOLATION_CRASH",
]

#: Marker printed by the isolated child once it has successfully imported S4.
ISOLATION_STARTED = "##S4-ISOLATION-STARTED##"
#: Marker printed by the isolated child when the callable returned normally.
ISOLATION_OK = "##S4-ISOLATION-OK##"
#: Marker printed by the isolated child when the callable raised a Python error.
ISOLATION_EXC = "##S4-ISOLATION-EXC##"
#: Verdict reported by run_isolated() when the child died from a signal.
ISOLATION_CRASH = "crash"
#: Probe module that holds the ``CASES`` mapping used by run_isolated().
ISOLATION_PROBE_MODULE = "isolation_cases"


def build_uniform_stack(n_above, layers, n_below, num_basis=1):
    """Create an S4 simulation of a planar (unpatterned) multilayer stack.

    Parameters
    ----------
    n_above : float or complex
        Refractive index of the semi-infinite incidence medium.
    layers : sequence of (thickness, refractive_index)
        The finite layers, ordered from the incidence side.
    n_below : float or complex
        Refractive index of the semi-infinite exit medium.
    num_basis : int
        Number of Fourier orders.  1 is exact for a planar stack.

    Returns
    -------
    (sim, name_above, name_below) : the simulation plus the two outer layer names.
    """
    import S4

    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    sim.AddMaterial("_above", complex(n_above) ** 2)
    for i, (_, n) in enumerate(layers):
        sim.AddMaterial("_film%d" % i, complex(n) ** 2)
    sim.AddMaterial("_below", complex(n_below) ** 2)

    sim.AddLayer("Above", 0, "_above")
    for i, (d, _) in enumerate(layers):
        sim.AddLayer("Film%d" % i, d, "_film%d" % i)
    sim.AddLayer("Below", 0, "_below")
    return sim, "Above", "Below"


def read_flux(sim, name_top, name_bottom, z_offset=0.0):
    """Return ``(incident, reflected, transmitted)`` real powers.

    Signed-flux convention (see ``analytic.py``): the backward flux in the
    incidence layer is negative, so the reflected power is its negation.
    """
    inc, refl = sim.GetPowerFlux(name_top, z_offset)
    trans, _ = sim.GetPowerFlux(name_bottom, z_offset)
    return inc.real, -refl.real, trans.real


def read_rt(sim, name_top, name_bottom, z_offset=0.0):
    """Return ``(R, T)`` power ratios from an already-excited simulation."""
    inc, refl, trans = read_flux(sim, name_top, name_bottom, z_offset)
    if inc == 0.0:
        raise ZeroDivisionError("incident power is zero; was an excitation set?")
    return refl / inc, trans / inc


_CHILD_TEMPLATE = r'''
import base64, json, os, sys, traceback
payload = json.loads(base64.b64decode(sys.argv[1]).decode("utf-8"))
# The built extension lives in the repo root, so that has to win over any
# stale copy of S4*.so that may exist elsewhere on sys.path (e.g. in a scratch
# directory). Insert it last so that it ends up first.
sys.path.insert(0, payload["test_dir"])
sys.path.insert(0, payload["repo_root"])
try:
    import S4
    assert os.path.dirname(os.path.abspath(S4.__file__)) == os.path.abspath(payload["repo_root"]), (
        "imported S4 from %s, expected %s" % (S4.__file__, payload["repo_root"]))
except BaseException:
    traceback.print_exc()
    sys.exit(3)
print(payload["started_marker"], flush=True)
try:
    import importlib
    mod = importlib.import_module(payload["module"])
    fn = getattr(mod, "CASES")[payload["case"]]
    result = fn()
    print(payload["ok_marker"] + json.dumps({"result": repr(result)}), flush=True)
except BaseException as exc:
    print(payload["exc_marker"] + json.dumps(
        {"type": type(exc).__name__, "message": str(exc)}), flush=True)
'''


def run_isolated(case, module=ISOLATION_PROBE_MODULE, timeout=180, python=None):
    """Run one isolation probe in a separate interpreter; classify the outcome.

    Parameters
    ----------
    case : str
        Key into ``CASES`` in the probe module (``isolation_cases.py``).
    module : str
        Probe module name; defaults to ``isolation_cases``.
    timeout : int
        Seconds before the child is declared hung.

    Returns a dict with:

    ``verdict``
        ``"ok"``, ``"exception"``, ``"crash"``, ``"timeout"`` or ``"startup"``.
        ``"crash"`` means the child died from a signal (negative return code),
        which for CPython means SIGSEGV/SIGABRT -- a native fault in the
        extension rather than a Python-level error.
    ``returncode``, ``result``, ``exception_type``, ``exception_message``,
    ``stderr_tail``
    """
    payload = {
        "repo_root": REPO_ROOT,
        "test_dir": HERE,
        "module": module,
        "case": case,
        "started_marker": ISOLATION_STARTED,
        "ok_marker": ISOLATION_OK,
        "exc_marker": ISOLATION_EXC,
    }
    blob = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join([REPO_ROOT, HERE, env.get("PYTHONPATH", "")])
    env.pop("PYTHONSTARTUP", None)

    try:
        proc = subprocess.run(
            [python or sys.executable, "-u", "-c", _CHILD_TEMPLATE, blob],
            capture_output=True, text=True, env=env, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {
            "verdict": "timeout", "returncode": None, "result": None,
            "exception_type": None, "exception_message": None,
            "stdout": "", "stderr_tail": "",
        }

    out = {
        "verdict": "startup",
        "returncode": proc.returncode,
        "result": None,
        "exception_type": None,
        "exception_message": None,
        "stdout": proc.stdout,
        "stderr_tail": "\n".join(proc.stderr.strip().splitlines()[-6:]),
    }
    started = ISOLATION_STARTED in proc.stdout
    for line in proc.stdout.splitlines():
        if line.startswith(ISOLATION_OK):
            out["verdict"] = "ok"
            out["result"] = json.loads(line[len(ISOLATION_OK):]).get("result")
        elif line.startswith(ISOLATION_EXC):
            info = json.loads(line[len(ISOLATION_EXC):])
            out["verdict"] = "exception"
            out["exception_type"] = info["type"]
            out["exception_message"] = info["message"]

    if proc.returncode < 0:
        out["verdict"] = ISOLATION_CRASH
    elif out["verdict"] == "startup" and started and proc.returncode != 0:
        # Imported fine but died before reporting a result.
        out["verdict"] = ISOLATION_CRASH
    return out


def temp_workspace():
    """A TemporaryDirectory suitable for the on-disk outputs some S4 calls write."""
    return tempfile.TemporaryDirectory(prefix="s4test-")
