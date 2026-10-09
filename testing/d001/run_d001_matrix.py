#!/usr/bin/env python3
"""D001 physical matrix: baseline / candidate S4 extensions against an Airy reference.

Scope: f = 0.427, normal incidence, s polarization, one 0.25-thick eps=4 film in
air; N in {1, 9} x representation {A scalar, B same-material circle, C isotropic
tensor} x repeat {1, 2}.  Every case runs in a fresh child process that imports
only the extension found under --s4-dir.

The reference R/T comes from oracle_d001.py, which uses the physical inputs only
and never reads S4 output.  The pass rule is fixed before any run:
    |R - R_ref| <= 1e-10  and  |T - T_ref| <= 1e-10  and all values finite
    and incident flux > 0.
R + T ~= 1 and repeat agreement are recorded as auxiliary evidence only.

Usage (parent):
    python3 -I -B run_d001_matrix.py --s4-dir DIR --out RUNDIR [--label NAME]
Exit status: 0 when every case passes, 1 otherwise (a failing baseline is expected
to exit 1; the record is the evidence).
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

import model_d001 as model  # noqa: E402  (stdlib only, does not import S4)
import oracle_d001 as oracle  # noqa: E402  (stdlib only, does not import S4)

TOL_ABS = 1e-10
CHILD_TIMEOUT_S = 120


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def child(s4_dir, case_key):
    """One fresh process: build one case through the model and read fluxes."""
    s4_dir = os.path.realpath(s4_dir)
    sys.path.insert(0, s4_dir)
    import S4  # noqa: PLC0415

    s4_file = os.path.realpath(S4.__file__)
    if not s4_file.startswith(s4_dir + os.sep):
        raise RuntimeError("S4 imported from %s, not from %s" % (s4_file, s4_dir))
    cases = model.load_cases()
    matches = [c for c in cases if c["case_key"] == case_key]
    if len(matches) != 1:
        raise RuntimeError("case key %r not found exactly once" % (case_key,))
    case = matches[0]

    sim = model.build_simulation(S4, case)
    G = [[int(g[0]), int(g[1])] for g in sim.GetBasisSet()]
    fluxes = model.read_fluxes(sim)
    rt = model.compute_RT(fluxes)
    rec = {
        "case_key": case_key,
        "s4_file": s4_file,
        "s4_sha256": sha256_file(s4_file),
        "python": sys.version.split()[0],
        "actual_G": G,
        "actual_G_count": len(G),
        "fluxes": {k: [v.real, v.imag] for k, v in fluxes.items()},
        "incident": rt["incident"],
        "R": rt["R"],
        "T": rt["T"],
        "RplusT": rt["RplusT"],
    }
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
    ref = oracle.reference_RT(oracle.F)
    cases = model.load_cases()
    problems = model.check_cases(cases)
    if problems:
        sys.exit("case table problems: %r" % (problems,))

    rows = []
    for case in cases:
        key = case["case_key"]
        cwd = os.path.join(out_dir, "cwd", key.replace("|", "_"))
        os.makedirs(cwd, exist_ok=True)
        argv = [sys.executable, "-I", "-B", os.path.join(HERE, "run_d001_matrix.py"),
                "--child", "--s4-dir", s4_dir, "--case-key", key]
        env = {"PATH": os.environ.get("PATH", ""), "LANG": "C.UTF-8",
               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONNOUSERSITE": "1"}
        start = utcnow()
        try:
            pr = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                                text=True, timeout=CHILD_TIMEOUT_S)
            rc, stdout, stderr = pr.returncode, pr.stdout, pr.stderr
        except subprocess.TimeoutExpired as exc:
            rc = "timeout"
            stdout = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = (exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stem = os.path.join(out_dir, "logs", key.replace("|", "_"))
        open(stem + ".stdout.txt", "w").write(stdout)
        open(stem + ".stderr.txt", "w").write(stderr)
        row = {"case_key": key, "requested_num_basis": case["requested_num_basis"],
               "representation": case["representation"], "repeat": case["repeat"],
               "child_rc": rc, "start_utc": start, "end_utc": utcnow()}
        rec = None
        if rc == 0 and stdout.strip():
            rec = json.loads(stdout.strip().splitlines()[-1])
            open(os.path.join(out_dir, "raw", key.replace("|", "_") + ".json"), "w").write(
                json.dumps(rec, indent=1, sort_keys=True) + "\n")
            row.update(judge(rec, ref))
            row.update({"R": rec["R"], "T": rec["T"], "incident": rec["incident"],
                        "actual_G_count": rec["actual_G_count"], "s4_sha256": rec["s4_sha256"],
                        "s4_file": rec["s4_file"]})
        else:
            row.update({"pass": False, "error": "child did not produce a record"})
        rows.append(row)

    passed = sum(1 for r in rows if r.get("pass") is True)
    summary = {
        "label": label,
        "generated_utc": utcnow(),
        "s4_dir": s4_dir,
        "reference": {"R": ref["R"], "T": ref["T"], "frequency": oracle.F,
                      "source": "oracle_d001.reference_RT (inputs only)"},
        "tolerance_abs": TOL_ABS,
        "cases_total": len(rows),
        "cases_pass": passed,
        "cases_fail": len(rows) - passed,
        "rows": rows,
    }
    with open(os.path.join(out_dir, "SUMMARY_%s.json" % label), "w") as fh:
        fh.write(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print("label=%s pass=%d fail=%d total=%d" % (label, passed, len(rows) - passed, len(rows)))
    for r in rows:
        print("%-32s rc=%s N_G=%s R=%s T=%s pass=%s" % (
            r["case_key"], r["child_rc"], r.get("actual_G_count"),
            "%.12g" % r["R"] if "R" in r else "-", "%.12g" % r["T"] if "T" in r else "-",
            r.get("pass")))
    return 0 if passed == len(rows) else 1


def main():
    ap = argparse.ArgumentParser(description="D001 physical matrix runner")
    ap.add_argument("--child", action="store_true")
    ap.add_argument("--case-key")
    ap.add_argument("--s4-dir")
    ap.add_argument("--out")
    ap.add_argument("--label", default="run")
    args = ap.parse_args()
    if args.child:
        return child(args.s4_dir, args.case_key)
    if not args.s4_dir or not args.out:
        ap.error("--s4-dir and --out are required")
    return parent(args.s4_dir, args.out, args.label)


if __name__ == "__main__":
    raise SystemExit(main())
