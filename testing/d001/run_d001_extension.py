#!/usr/bin/env python3
"""D001 extension matrix: frequency, incidence, polarization, basis and memory mode.

The frozen 12-case matrix (run_d001_matrix.py) is not changed.  This extension adds:
  f in {0.173, 0.427, 0.733} x theta in {0, 30} deg x pol in {s, p}
  x N in {1, 9, 25} x representation in {A, B, C}                 (108 cases)
  plus ConserveMemory=True (use_less_memory) cases at f=0.427, theta=30, N=9
  for pol in {s, p} and representations {B, C}, and one at f=0.733 (s, B).

Reference: oracle_d001_ext.fresnel_RT, from the physical inputs only.  The pass rule
is fixed before any run, identical to the frozen matrix: absolute |R - R_ref| and
|T - T_ref| <= 1e-10, all values finite, incident flux > 0.  The film is the same
eps = 4 slab; same-material regions are physically uniform, so the same reference
applies to the B representation.

Usage (parent):
    python3 -I -B run_d001_extension.py --s4-dir DIR --out RUNDIR --label NAME
"""

import argparse
import datetime
import hashlib
import json
import math
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import model_d001 as model  # noqa: E402  (stdlib only)
import oracle_d001_ext as oracle  # noqa: E402  (stdlib only)

TOL_ABS = 1e-10
CHILD_TIMEOUT_S = 120
REP_NAME = {"A": "A_SCALAR", "B": "B_SAME_MATERIAL_CIRCLE", "C": "C_ISOTROPIC_TENSOR"}


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_cases():
    cases = []
    for f in (0.173, 0.427, 0.733):
        for theta in (0.0, 30.0):
            for pol in ("s", "p"):
                for n in (1, 9, 25):
                    for rep in ("A", "B", "C"):
                        cases.append({"f": f, "theta": theta, "pol": pol, "N": n,
                                      "rep": rep, "mem": False})
    for pol in ("s", "p"):
        for rep in ("B", "C"):
            cases.append({"f": 0.427, "theta": 30.0, "pol": pol, "N": 9, "rep": rep, "mem": True})
    cases.append({"f": 0.733, "theta": 30.0, "pol": "s", "N": 9, "rep": "B", "mem": True})
    for c in cases:
        c["key"] = "f%.3f|th%g|%s|N%d|%s|%s" % (c["f"], c["theta"], c["pol"], c["N"], c["rep"],
                                               "mem" if c["mem"] else "std")
    return cases


def child(s4_dir, spec_json):
    spec = json.loads(spec_json)
    s4_dir = os.path.realpath(s4_dir)
    sys.path.insert(0, s4_dir)
    import S4  # noqa: PLC0415

    s4_file = os.path.realpath(S4.__file__)
    if not s4_file.startswith(s4_dir + os.sep):
        raise RuntimeError("S4 imported from %s, not from %s" % (s4_file, s4_dir))
    model.INCIDENCE_ANGLES = (spec["theta"], 0.0)
    if spec["pol"] == "s":
        model.S_AMPLITUDE, model.P_AMPLITUDE = complex(1.0, 0.0), complex(0.0, 0.0)
    else:
        model.S_AMPLITUDE, model.P_AMPLITUDE = complex(0.0, 0.0), complex(1.0, 0.0)
    case = {"representation": REP_NAME[spec["rep"]], "requested_num_basis": spec["N"],
            "frequency": spec["f"], "repeat": 1}
    sim = model.build_simulation(S4, case)
    if spec["mem"]:
        sim.SetOptions(ConserveMemory=True)
    G = [[int(g[0]), int(g[1])] for g in sim.GetBasisSet()]
    fluxes = model.read_fluxes(sim)
    rt = model.compute_RT(fluxes)
    rec = {"key": spec["key"], "s4_file": s4_file, "s4_sha256": sha256_file(s4_file),
           "python": sys.version.split()[0], "actual_G_count": len(G), "actual_G": G,
           "fluxes": {k: [v.real, v.imag] for k, v in fluxes.items()},
           "incident": rt["incident"], "R": rt["R"], "T": rt["T"], "RplusT": rt["RplusT"]}
    sys.stdout.write(json.dumps(rec, sort_keys=True) + "\n")
    return 0


def judge(rec, ref):
    vals = [rec["R"], rec["T"], rec["incident"]]
    finite = all(math.isfinite(v) for v in vals)
    dR = abs(rec["R"] - ref["R"])
    dT = abs(rec["T"] - ref["T"])
    ok = finite and rec["incident"] > 0 and dR <= TOL_ABS and dT <= TOL_ABS
    return {"abs_err_R": dR, "abs_err_T": dT, "finite": finite, "pass": ok}


def parent(s4_dir, out_dir, label):
    s4_dir = os.path.realpath(s4_dir)
    out_dir = os.path.realpath(out_dir)
    os.makedirs(os.path.join(out_dir, "raw"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "logs"), exist_ok=True)
    rows = []
    for c in build_cases():
        spec = dict(c)
        spec_json = json.dumps(spec, sort_keys=True)
        safe = c["key"].replace("|", "_")
        cwd = os.path.join(out_dir, "cwd", safe)
        os.makedirs(cwd, exist_ok=True)
        argv = [sys.executable, "-I", "-B", os.path.join(HERE, "run_d001_extension.py"),
                "--child", "--s4-dir", s4_dir, "--spec", spec_json]
        env = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8",
               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
        start = utcnow()
        try:
            pr = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                                timeout=CHILD_TIMEOUT_S)
            rc, stdout, stderr = pr.returncode, pr.stdout, pr.stderr
        except subprocess.TimeoutExpired:
            rc, stdout, stderr = "timeout", "", ""
        open(os.path.join(out_dir, "logs", safe + ".stdout.txt"), "w").write(stdout)
        open(os.path.join(out_dir, "logs", safe + ".stderr.txt"), "w").write(stderr)
        row = {"key": c["key"], "f": c["f"], "theta": c["theta"], "pol": c["pol"], "N": c["N"],
               "rep": c["rep"], "mem": c["mem"], "child_rc": rc, "start_utc": start,
               "end_utc": utcnow()}
        if rc == 0 and stdout.strip():
            rec = json.loads(stdout.strip().splitlines()[-1])
            open(os.path.join(out_dir, "raw", safe + ".json"), "w").write(
                json.dumps(rec, indent=1, sort_keys=True) + "\n")
            ref = oracle.fresnel_RT(c["f"], c["theta"], c["pol"])
            row.update(judge(rec, ref))
            row.update({"R": rec["R"], "T": rec["T"], "R_ref": ref["R"], "T_ref": ref["T"],
                        "incident": rec["incident"], "actual_G_count": rec["actual_G_count"],
                        "s4_sha256": rec["s4_sha256"], "s4_file": rec["s4_file"]})
        else:
            row.update({"pass": False, "error": "child did not produce a record"})
        rows.append(row)
    passed = sum(1 for r in rows if r.get("pass") is True)
    summary = {"label": label, "generated_utc": utcnow(), "s4_dir": s4_dir,
               "tolerance_abs": TOL_ABS, "reference": "oracle_d001_ext.fresnel_RT (inputs only)",
               "cases_total": len(rows), "cases_pass": passed, "cases_fail": len(rows) - passed,
               "rows": rows}
    with open(os.path.join(out_dir, "SUMMARY_%s.json" % label), "w") as fh:
        fh.write(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print("label=%s pass=%d fail=%d total=%d" % (label, passed, len(rows) - passed, len(rows)))
    for r in rows:
        if r.get("pass") is not True:
            print("  FAIL %-30s rc=%s R=%s R_ref=%s T=%s T_ref=%s" % (
                r["key"], r["child_rc"], r.get("R"), r.get("R_ref"), r.get("T"), r.get("T_ref")))
    return 0 if passed == len(rows) else 1


def main():
    ap = argparse.ArgumentParser(description="D001 extension matrix runner")
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--spec")
    ap.add_argument("--s4-dir")
    ap.add_argument("--out")
    ap.add_argument("--label", default="run")
    args = ap.parse_args()
    if args.child:
        return child(args.s4_dir, args.spec)
    if not args.s4_dir or not args.out:
        ap.error("--s4-dir and --out are required")
    return parent(args.s4_dir, args.out, args.label)


if __name__ == "__main__":
    raise SystemExit(main())
