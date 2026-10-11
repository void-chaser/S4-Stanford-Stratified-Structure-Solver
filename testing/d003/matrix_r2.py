#!/usr/bin/env python3
"""D003 supplementary matrix runner (P05-S2R, R2-E).

Runs every row of the locked expectation registry (R2D_EXPECTATIONS.tsv, 10 tab fields:
case, family, tree, request, NTH, stack, mode, NG, expected_class, basis) on one tree's
all-macro driver, records the RAW process return code and the driver facts, classifies
each run with judge_d003.classify() (facts only; the driver's PASS/FAIL verdict is not
read), and compares to the registered expectation.

Fail-closed rules:
  * a row whose driver binary is missing is recorded INVALID (never skipped);
  * a row with an unparseable field is recorded INVALID;
  * a run whose process cannot be started is recorded INVALID (rc = None).

This file does not edit the historical matrix (matrix_d003.py) or its counts.

Usage:
  matrix_r2.py run      --registry FILE --driver BIN --tree TREE --runs DIR --out DIR
  matrix_r2.py index    --registry FILE --runs DIR --tree TREE --out DIR
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import judge_d003 as J  # noqa: E402

TIMEOUT_S = 300
GRID = ["pattern", "both", "4", "3"]
ENV_ALLOW = ("PATH", "LANG", "LC_ALL")
EXPECTED_CLASSES = ("CRASH", "SILENT_SWALLOW", "REPORTED_FAILURE", "INVALID", "CONTROL_OK")
MODES = ("fft", "kottke", "jones", "nv", "vl")
STACKS = ("pattern", "flat")
REQUEST_PREFIXES = ("linearsolve:", "linearsolve_null:", "alloc:", "kottke_alloc:", "s4malloc")


def _child_env(extra):
    env = {k: os.environ[k] for k in ENV_ALLOW if k in os.environ}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.update(extra)
    return env


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_registry(path):
    """Return a list of dicts.  Raises on any malformed row (the registry is fixed input)."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line.strip() or line.startswith("#"):
                continue
            f = line.split("\t")
            if len(f) != 10:
                raise SystemExit("registry line %d has %d fields (need 10)" % (lineno, len(f)))
            case, fam, tree, req, nth, stack, mode, ng, exp, basis = f
            if tree not in ("BASE", "CUR"):
                raise SystemExit("registry line %d: bad tree %r" % (lineno, tree))
            if stack not in STACKS:
                raise SystemExit("registry line %d: bad stack %r" % (lineno, stack))
            if mode not in MODES:
                raise SystemExit("registry line %d: bad mode %r" % (lineno, mode))
            if exp not in EXPECTED_CLASSES:
                raise SystemExit("registry line %d: bad expected class %r" % (lineno, exp))
            rows.append({"case": case, "family": fam, "tree": tree, "request": req,
                         "nth": nth, "stack": stack, "mode": mode, "ng": ng,
                         "expected": exp, "basis": basis, "lineno": lineno})
    return rows


def request_ok(req):
    if req == "-" or req == "":
        return True   # control row: no request
    return req.startswith(REQUEST_PREFIXES)


def build_env(row):
    extra = {"FMM_MODE": row["mode"], "S4FMM_NG": row["ng"]}
    if row["request"] not in ("-", ""):
        extra["S4FMM_INJECT"] = row["request"]
    if row["nth"] not in ("-", ""):
        extra["S4FMM_NTH"] = row["nth"]
    # P05-S2R2 T4: cases whose id starts with "t4/" run the second-call route (the driver's
    # S4FMM_TWICE=slab destroys layer 1 modes between the two field calls).  Every other case
    # gets no S4FMM_TWICE, so the historical environment is unchanged.
    if row["case"].startswith("t4/"):
        extra["S4FMM_TWICE"] = "slab"
    return extra


def inj_call_of(row):
    """Index of the field call the injection targets: 2 for t4/ cases, else 1 (historical)."""
    return 2 if row["case"].startswith("t4/") else 1


def control_of(row):
    return row["request"] in ("-", "")


def run_row(driver, row, runs_dir):
    name = row["case"].replace("/", "__") + "__" + row["tree"]
    log_path = os.path.join(runs_dir, name + ".log")
    os.makedirs(runs_dir, exist_ok=True)
    rc = None
    out = b""
    try:
        proc = subprocess.run([driver] + GRID, env=_child_env(build_env(row)), cwd=runs_dir,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT_S)
        rc = proc.returncode
        out = proc.stdout
    except subprocess.TimeoutExpired as exc:
        rc = 124
        out = exc.stdout or b""
    except OSError as exc:
        out = ("RUNNER: could not start driver: %s\n" % exc).encode()
    if rc is not None and rc < 0:
        rc = 128 - rc     # a signal is reported as 128+n, as the shell does
    with open(log_path, "wb") as fh:
        fh.write(out)
    return rc, log_path


def _verify_driver(path, expected_sha256):
    """P05-S3R R3-0: refuse to run any driver whose sha256 is not the pinned value.

    The driver is identified by content, not by name, because two binaries with
    similar names (driver-all and driver-all-t4) produced different results in S2R2.
    Raises SystemExit before any row runs, so no raw file is written for a wrong driver.
    """
    if not (os.path.isfile(path) and os.access(path, os.X_OK)):
        raise SystemExit("REFUSED: driver missing or not executable: %s" % path)
    actual = _sha256(path)
    if actual != expected_sha256.lower():
        raise SystemExit("REFUSED: driver sha256 mismatch for %s\n  pinned: %s\n  actual: %s"
                         % (path, expected_sha256.lower(), actual))
    return actual


def _write_manifest(out_dir, driver_path, driver_sha256, tree):
    """Record the verified driver identity; refuse to overwrite a manifest for a different driver."""
    manifest_path = os.path.join(out_dir, "driver_manifest.json")
    entry = {"tree": tree, "driver": os.path.abspath(driver_path), "sha256": driver_sha256}
    if os.path.exists(manifest_path):
        with open(manifest_path, encoding="utf-8") as fh:
            prev = json.load(fh)
        if prev.get("sha256") != driver_sha256:
            raise SystemExit("REFUSED: %s already holds a run with a different driver (%s)"
                             % (out_dir, prev.get("sha256")))
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(entry, fh, indent=1, sort_keys=True)
        fh.write("\n")


def cmd_run(args):
    rows = load_registry(args.registry)
    os.makedirs(args.out, exist_ok=True)
    driver_sha = _verify_driver(args.driver, args.driver_sha256)
    _write_manifest(args.out, args.driver, driver_sha, args.tree)
    recs = []
    for row in rows:
        if row["tree"] != args.tree:
            continue
        if not request_ok(row["request"]):
            recs.append(dict(row, rc=None, facts=None, observed="INVALID",
                             reason="unparseable request %r" % row["request"], log=None))
            continue
        rc, log_path = run_row(args.driver, row, args.runs)
        with open(log_path, "rb") as fh:
            text = fh.read().decode("utf-8", errors="replace")
        facts = J.facts_from_log(text)
        cls, label, reason = J.classify(rc, facts["rc1"], facts["rc2"], facts["hit"],
                                        control=control_of(row), inj_call=inj_call_of(row))
        recs.append(dict(row, rc=rc, facts=facts, observed=cls, reason=reason,
                         label=label, log=log_path, log_sha256=_sha256(log_path)))
    with open(os.path.join(args.out, "raw_%s.json" % args.tree), "w", encoding="utf-8") as fh:
        json.dump(recs, fh, indent=1, sort_keys=True, default=str)
        fh.write("\n")
    n_match = sum(1 for r in recs if r["observed"] == r["expected"])
    print("tree=%s rows=%d matched=%d mismatched=%d" % (args.tree, len(recs), n_match, len(recs) - n_match))
    return 0


def cmd_index(args):
    # 'run' writes raw_<tree>.json into its --out directory; index reads it from there.
    raw_path = os.path.join(args.out, "raw_%s.json" % args.tree)
    with open(raw_path, encoding="utf-8") as fh:
        recs = json.load(fh)
    os.makedirs(args.out, exist_ok=True)
    lines = ["# tree\tcase\tfamily\trequest\tstack\tmode\texpected\tobserved\tmatch\trc\trc1\trc2\thit\treason"]
    for r in recs:
        f = r.get("facts") or {}
        lines.append("\t".join([args.tree, r["case"], r["family"], r["request"], r["stack"], r["mode"],
                                r["expected"], r["observed"], "yes" if r["observed"] == r["expected"] else "NO",
                                str(r["rc"]), str(f.get("rc1")), str(f.get("rc2")), str(f.get("hit")),
                                r["reason"]]))
    with open(os.path.join(args.out, "index_%s.txt" % args.tree), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    mism = [r for r in recs if r["observed"] != r["expected"]]
    print("tree=%s index rows=%d mismatches=%d" % (args.tree, len(recs), len(mism)))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--registry", required=True)
    r.add_argument("--driver", required=True)
    r.add_argument("--driver-sha256", required=True,
                   help="pinned sha256 of the driver binary; a different binary is refused (P05-S3R R3-0)")
    r.add_argument("--tree", required=True, choices=("BASE", "CUR"))
    r.add_argument("--runs", required=True)
    r.add_argument("--out", required=True)
    x = sub.add_parser("index")
    x.add_argument("--registry", required=True)
    x.add_argument("--runs", required=True)
    x.add_argument("--tree", required=True, choices=("BASE", "CUR"))
    x.add_argument("--out", required=True)
    args = p.parse_args(argv)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "index":
        return cmd_index(args)
    raise SystemExit("unrouted subcommand: %r" % args.cmd)


if __name__ == "__main__":
    sys.exit(main())
