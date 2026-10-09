#!/usr/bin/env python3
"""Error code 20 propagation check: rcwa -> S4 -> Python / Lua / C.

Requires a TEST-ONLY seam build (compiled with -DS4_TEST_EIGEN_INFO and the header
testing/s4test/test_seams/seam.h on the include path).  The seam is driven by the
environment variable S4_TEST_EIGEN_INFO, read at each eigensolve:
  * unset / empty / malformed / zero   -> no injection, the real solve is used
  * a valid non-zero integer           -> a SUCCESSFUL solve is reported as that status
  * a real non-zero solver status      -> always wins (never rewritten by the seam)

Expected public behaviour when an injected layer eigensystem fails:
  Python : RuntimeError "<fname>: The layer eigensystem could not be solved ..."
  Lua    : Lua error with the same text
  C      : return code 20 from the S4_Simulation_* call
and no layer modes or solution are installed, so a retry after the environment is
cleared on the same object gives the same result as a fresh object.

Usage:
  python3 -I -B run_error20.py --seam-py-dir DIR --seam-lua EXE --seam-lib LIBS4_A \
      --src-include DIR_S4 --normal-py-dir DIR --out-dir RUNDIR
Exit status 0 when every check passes.
"""

import argparse
import datetime
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
D001_DIR = os.path.join(HERE, "..", "..", "d001")
ENV = "S4_TEST_EIGEN_INFO"
INVALID_VALUES = ["", "0", "abc", "1x", " 1", "+", "-", "1.0", "2147483648", "-2147483649"]
FAIL_TEXT = "could not be solved"


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def set_env(value):
    if value is None:
        os.environ.pop(ENV, None)
    else:
        os.environ[ENV] = value


def sha256_file(path):
    import hashlib  # noqa: PLC0415
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def python_checks(py_dir, out_dir):
    sys.path.insert(0, D001_DIR)
    import model_d001 as model  # noqa: PLC0415
    sys.path.insert(0, os.path.realpath(py_dir))
    import S4  # noqa: PLC0415

    s4_file = os.path.realpath(S4.__file__)
    if not s4_file.startswith(os.path.realpath(py_dir) + os.sep):
        raise RuntimeError("S4 imported from %s, not from %s" % (s4_file, py_dir))
    cases = {c["representation"]: c for c in model.load_cases()}
    case_b = cases["B_SAME_MATERIAL_CIRCLE"]
    case_b = dict(case_b, requested_num_basis=9)
    case_a = dict(cases["A_SCALAR"], requested_num_basis=9)  # uniform: no RNP solve

    def fluxes(sim):
        top = sim.GetPowerFlux(S4_Layer="AirTop", zOffset=0.0)
        bot = sim.GetPowerFlux(S4_Layer="AirBottom", zOffset=0.0)
        return [complex(x).real for x in (top[0], top[1], bot[0], bot[1])]

    checks = []

    def check(name, ok, detail):
        checks.append({"check": name, "pass": bool(ok), "detail": detail})

    def expect_failure(label, fn):
        try:
            fn()
        except RuntimeError as exc:
            msg = str(exc)
            return msg, (FAIL_TEXT in msg)
        return "no exception", False

    # reference: no injection
    set_env(None)
    ref_sim = model.build_simulation(S4, case_b)
    ref = fluxes(ref_sim)
    check("unset_reference_solves", all(math.isfinite(x) for x in ref), ref)

    # ---- injection on a fresh object (non-uniform layer, circle region) --------
    set_env("1")
    fresh = model.build_simulation(S4, case_b)
    msg, ok = expect_failure("inject1_flux", lambda: fluxes(fresh))
    check("inject_1_power_flux_raises_20", ok, msg)
    check("inject_1_message_names_entry", "GetPowerFlux" in msg, msg)

    # same object retried after clearing the environment: recovery, no stale modes
    set_env(None)
    retry = fluxes(fresh)
    diff = max(abs(a - b) for a, b in zip(retry, ref))
    check("same_object_retry_matches_reference", diff <= 1e-12, {"max_abs_diff": diff})

    # GetAmplitudes on a failing object (uniform layer, no region)
    set_env("1")
    sim_a = model.build_simulation(S4, case_b)
    msg_a, ok_a = expect_failure("inject1_amplitudes", lambda: sim_a.GetAmplitudes("AirTop", 0.0))
    check("inject_1_amplitudes_raises_20", ok_a, msg_a)
    set_env("-3")
    msg_n, ok_n = expect_failure("inject_neg3_flux", lambda: fluxes(model.build_simulation(S4, case_b)))
    check("inject_negative_3_raises_20", ok_n, msg_n)

    # invalid / zero request strings must not inject anything
    for value in INVALID_VALUES:
        set_env(value)
        sim = model.build_simulation(S4, case_b)
        try:
            got = fluxes(sim)
            diff = max(abs(a - b) for a, b in zip(got, ref))
            check("invalid_value_no_injection[%r]" % value, diff <= 1e-12, {"max_abs_diff": diff})
        except RuntimeError as exc:
            check("invalid_value_no_injection[%r]" % value, False, str(exc))

    set_env(None)
    result = {"python_ext": s4_file, "python_ext_sha256": sha256_file(s4_file),
              "checks": checks, "reference_flux": ref, "run_utc": utcnow()}
    with open(os.path.join(out_dir, "python_checks.json"), "w") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    return checks, ref


def normal_flux(py_dir):
    """Flux of the reference case from a NORMAL build, printed as JSON for comparison."""
    code = (
        "import sys, json; sys.path.insert(0, %r); sys.path.insert(0, %r); "
        "import model_d001 as m, S4; "
        "c=[x for x in m.load_cases() if x['representation']=='B_SAME_MATERIAL_CIRCLE'][0]; "
        "c=dict(c, requested_num_basis=9); s=m.build_simulation(S4, c); "
        "t=s.GetPowerFlux(S4_Layer='AirTop', zOffset=0.0); b=s.GetPowerFlux(S4_Layer='AirBottom', zOffset=0.0); "
        "print(json.dumps([complex(t[0]).real, complex(t[1]).real, complex(b[0]).real, complex(b[1]).real]))"
    ) % (D001_DIR, os.path.realpath(py_dir))
    env = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1"}
    pr = subprocess.run([sys.executable, "-I", "-B", "-c", code], capture_output=True, text=True,
                        env=env, cwd=os.path.realpath(py_dir), timeout=120)
    if pr.returncode != 0:
        raise RuntimeError("normal flux failed: %s" % pr.stderr)
    return json.loads(pr.stdout.strip().splitlines()[-1])


def run_lua(lua_exe, value, out_dir, tag):
    env = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8"}
    if value is not None:
        env[ENV] = value
    script = os.path.join(HERE, "error20_lua.lua")
    pr = subprocess.run([lua_exe, script], capture_output=True, text=True, env=env, timeout=120,
                        cwd=out_dir)
    with open(os.path.join(out_dir, "lua_%s.stdout" % tag), "w") as fh:
        fh.write(pr.stdout)
    with open(os.path.join(out_dir, "lua_%s.stderr" % tag), "w") as fh:
        fh.write(pr.stderr)
    rows = {}
    for line in pr.stdout.splitlines():
        if line.startswith("RESULT "):
            parts = line.split(" ", 3)
            rows[parts[1]] = {"status": parts[2], "text": parts[3] if len(parts) > 3 else ""}
    return pr.returncode, rows


def lua_checks(lua_exe, out_dir):
    """Non-interactive Lua frontend: S4L_error prints and exits(1), so the injected
    failure aborts the script (pcall does not catch it).  The contract checked here:
    non-zero exit, the public message on stderr, no result line printed, and a clean
    run with the environment unset."""
    checks = []
    rc, rows = run_lua(lua_exe, "1", out_dir, "inject1")
    err = open(os.path.join(out_dir, "lua_inject1.stderr")).read()
    checks.append({"check": "lua_inject1_exits_nonzero", "pass": rc != 0,
                   "detail": {"rc": rc}})
    checks.append({"check": "lua_inject1_message_on_stderr",
                   "pass": (FAIL_TEXT in err and "GetPoyntingFlux:" in err),
                   "detail": err.strip().splitlines()[-1:] if err.strip() else []})
    checks.append({"check": "lua_inject1_no_result_printed", "pass": not rows,
                   "detail": rows})
    rc2, rows2 = run_lua(lua_exe, None, out_dir, "unset")
    for name in ("GetPowerFlux_first", "GetPowerFlux_again", "GetPowerFlux_fresh"):
        row = rows2.get(name, {})
        checks.append({"check": "lua_unset_%s_solves" % name,
                       "pass": row.get("status") == "ok", "detail": row})
    checks.append({"check": "lua_unset_script_exit_zero", "pass": rc2 == 0,
                   "detail": {"unset_rc": rc2}})
    return checks


def compile_c(include_dir, lib, out_dir):
    src = os.path.join(HERE, "error20_capi.c")
    exe = os.path.join(out_dir, "error20_capi")
    argv = ["gcc", "-O1", "-g", "-Wall", "-I", os.path.realpath(include_dir), src, lib,
            "-llapack", "-lblas", "-lstdc++", "-lm", "-o", exe]
    pr = subprocess.run(argv, capture_output=True, text=True)
    with open(os.path.join(out_dir, "c_build.stderr"), "w") as fh:
        fh.write(pr.stderr)
    if pr.returncode != 0:
        raise RuntimeError("C build failed: %s" % pr.stderr)
    return exe


def c_run(exe, value, out_dir, tag):
    env = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8"}
    if value is not None:
        env[ENV] = value
    pr = subprocess.run([exe], capture_output=True, text=True, env=env, timeout=120, cwd=out_dir)
    with open(os.path.join(out_dir, "c_%s.stdout" % tag), "w") as fh:
        fh.write(pr.stdout)
    rows = {}
    for line in pr.stdout.splitlines():
        if line.startswith("RESULT "):
            parts = line.split()
            rows[parts[1]] = int(parts[2].split("=")[1])
    return pr.returncode, rows


def c_checks(include_dir, lib, out_dir):
    exe = compile_c(include_dir, lib, out_dir)
    checks = []
    rc, rows = c_run(exe, "1", out_dir, "inject1")
    for name in ("GetPowerFlux_first", "SolveLayer_film", "GetPowerFlux_bottom", "GetPowerFlux_fresh"):
        checks.append({"check": "c_inject1_%s_rc20" % name, "pass": rows.get(name) == 20,
                       "detail": rows.get(name)})
    rc2, rows2 = c_run(exe, None, out_dir, "unset")
    for name in ("GetPowerFlux_first", "SolveLayer_film", "GetPowerFlux_bottom", "GetPowerFlux_fresh"):
        checks.append({"check": "c_unset_%s_rc0" % name, "pass": rows2.get(name) == 0,
                       "detail": rows2.get(name)})
    checks.append({"check": "c_program_exit_zero", "pass": rc == 0 and rc2 == 0,
                   "detail": {"inject_rc": rc, "unset_rc": rc2}})
    return checks


def main():
    ap = argparse.ArgumentParser(description="error code 20 propagation check")
    ap.add_argument("--seam-py-dir", required=True)
    ap.add_argument("--seam-lua", required=True)
    ap.add_argument("--seam-lib", required=True)
    ap.add_argument("--src-include", required=True)
    ap.add_argument("--normal-py-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    py, seam_ref = python_checks(args.seam_py_dir, args.out_dir)
    normal = normal_flux(args.normal_py_dir)
    # the seam build without injection must match the normal build of the same source
    diff = max(abs(a - b) for a, b in zip(seam_ref, normal))
    cross = {"check": "normal_vs_seam_unset_flux_equal", "pass": diff <= 1e-12,
             "detail": {"max_abs_diff": diff, "normal": normal, "seam_unset": seam_ref}}
    lua = lua_checks(args.seam_lua, args.out_dir)
    cc = c_checks(args.src_include, args.seam_lib, args.out_dir)
    checks = py + [cross] + lua + cc
    failed = [c for c in checks if not c["pass"]]
    summary = {"generated_utc": utcnow(), "checks_total": len(checks),
               "checks_pass": len(checks) - len(failed), "checks_fail": len(failed),
               "checks": checks}
    with open(os.path.join(args.out_dir, "ERROR20_SUMMARY.json"), "w") as fh:
        json.dump(summary, fh, indent=1, sort_keys=True)
    print("error20 checks: pass=%d fail=%d total=%d" % (len(checks) - len(failed), len(failed), len(checks)))
    for c in failed:
        print("  FAIL %s %s" % (c["check"], c["detail"]))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
