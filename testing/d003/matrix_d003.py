#!/usr/bin/env python3
"""D003 harness matrix runner (P05-S2).

Runs the fixed case table against a driver binary, records each run's RAW process
return code, and classifies it with judge_d003.py.  Nothing is copied from an
older index: rc comes from the process that ran here.

Subcommands:
    run       --bin DRIVER --runs DIR --out DIR [--ref DRIVER] [--root REPO]
    classify  --runs DIR --out DIR      (judge the recorded runs; writes index.txt)

The case table is fixed here.  Its T4/T5 rows reproduce the S1B cases (22 rows).
The "new" rows are the S2 coverage items.  Expected classes are written into the
table BEFORE any run, so a mismatch is a finding, not a silent edit.

Environment: no /tmp, no /home path.  Subprocess environment is built explicitly
from a small allow-list, so the caller's FMM_*/S4FMM_* state cannot leak in.
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
GRID = ["pattern", "both", "4", "3"]          # stack, outputs, nu, nv (driver defaults)

# name, FMM_MODE, S4FMM_NG, S4FMM_INJECT, S4FMM_NTH, S4FMM_POL, control, real,
# expected class (pre-registered), group
CASES = [
    # --- T4: no-injection controls (S1B T4; 10 rows) --------------------------------
    ("t4/control-fft-ng9",    "fft",    9, None, None, None, True,  True,  "CONTROL_OK",      "S1B-T4"),
    ("t4/control-fft-ng1",    "fft",    1, None, None, None, True,  True,  "CONTROL_OK",      "S1B-T4"),
    ("t4/control-kottke-ng9", "kottke", 9, None, None, None, True,  True,  "CONTROL_OK",      "S1B-T4"),
    ("t4/control-kottke-ng1", "kottke", 1, None, None, None, True,  True,  "CONTROL_OK",      "S1B-T4"),
    ("t4/control-jones-ng9",  "jones",  9, None, None, None, True,  True,  "CONTROL_OK",      "S1B-T4"),
    ("t4/control-jones-ng1",  "jones",  1, None, None, None, True,  True,  "CONTROL_OK",      "S1B-T4"),
    ("t4/control-nv-ng9",     "nv",     9, None, None, None, True,  True,  "CONTROL_OK",      "S1B-T4"),
    ("t4/control-nv-ng1",     "nv",     1, None, None, None, True,  True,  "CONTROL_OK",      "S1B-T4"),
    ("t4/control-vl-ng9",     "vl",     9, None, None, None, True,  True,  "CONTROL_OK",      "S1B-T4"),
    ("t4/control-vl-ng1",     "vl",     1, None, None, None, True,  True,  "INVALID",        "S1B-T4"),
    # --- T5: injections (S1B T5; 12 rows) -------------------------------------------
    ("t5/plan1-fft-ng9",      "fft",    9, "plan",    "1", None, False, True,  "CRASH",          "S1B-T5"),
    ("t5/plan1-kottke-ng9",   "kottke", 9, "plan",    "1", None, False, True,  "CRASH",          "S1B-T5"),
    ("t5/plan1-jones-ng9",    "jones",  9, "plan",    "1", None, False, True,  "CRASH",          "S1B-T5"),
    ("t5/plan1-nv-ng9",       "nv",     9, "plan",    "1", None, False, True,  "CRASH",          "S1B-T5"),
    ("t5/plan1-vl-ng9",       "vl",     9, "plan",    "1", None, False, True,  "CRASH",          "S1B-T5"),
    ("t5/exec1-fft-ng9",      "fft",    9, "exec",    "1", None, False, False, "SILENT_SWALLOW", "S1B-T5"),
    ("t5/exec1-kottke-ng9",   "kottke", 9, "exec",    "1", None, False, False, "SILENT_SWALLOW", "S1B-T5"),
    ("t5/exec1-jones-ng9",    "jones",  9, "exec",    "1", None, False, False, "SILENT_SWALLOW", "S1B-T5"),
    ("t5/exec1-nv-ng9",       "nv",     9, "exec",    "1", None, False, False, "SILENT_SWALLOW", "S1B-T5"),
    ("t5/exec1-vl-ng9",       "vl",     9, "exec",    "1", None, False, False, "SILENT_SWALLOW", "S1B-T5"),
    ("t5/scratch1-fft-ng1",   "fft",    1, "scratch", "1", None, False, True,  "SILENT_SWALLOW", "S1B-T5"),
    ("t5/scratch2-fft-ng1",   "fft",    1, "scratch", "2", None, False, True,  "SILENT_SWALLOW", "S1B-T5"),
    # --- S2 coverage items -----------------------------------------------------------
    # The s4malloc rows were first observed by hand (k=1,2 crash with HIT; k=3 not
    # reached) before this table was written.  They are therefore observed
    # reproductions, not blind pre-registrations; the basis is recorded in
    # P05_S2_TEST_HARNESS.md.
    ("s2/s4malloc1-fft-ng9",  "fft",    9, "s4malloc", "1", None, False, True,  "CRASH",          "S2-NEW(observed)"),
    ("s2/s4malloc2-fft-ng9",  "fft",    9, "s4malloc", "2", None, False, True,  "CRASH",          "S2-NEW(observed)"),
    ("s2/s4malloc3-fft-ng9",  "fft",    9, "s4malloc", "3", None, False, True,  "INVALID",        "S2-NEW(observed)"),
    # --- S2.6 LinearSolve call-site seam (EXPECTATIONS REGISTERED BEFORE ANY RUN) ----
    # Registration time (UTC): 2026-10-11T02:06:37Z, recorded in
    # checkpoints/p05/evidence/p05-s2b/EXPECTATION_TIMESTAMP_UTC.txt.
    # The inject field carries "linearsolve:SITE:K:MODE"; nth is None (not used).
    # SITE 1 = fmm_FFT.cpp:204, SITE 2 = fmm_kottke.cpp:279 (set by the seam patch).
    # MODE info      : *info := 1 only.
    # MODE faithful  : *info := 1 and Epsilon_inv := identity (the generic template
    #                  leaves b untouched when info != 0; see the probe in p05-s2b/faithful/).
    # The faithful sensitivity expectation is a PREDICTION, not a verified result.
    ("s2b/ls-fft-info-k1",        "fft",    9, "linearsolve:1:1:info",     None, None, False, True, "SILENT_SWALLOW", "S2.6-pre-registered"),
    ("s2b/ls-kottke-info-k1",     "kottke", 9, "linearsolve:2:1:info",     None, None, False, True, "SILENT_SWALLOW", "S2.6-pre-registered"),
    ("s2b/ls-fft-faithful-k1",    "fft",    9, "linearsolve:1:1:faithful", None, None, False, True, "SILENT_SWALLOW", "S2.6-pre-registered"),
    ("s2b/ls-kottke-faithful-k1", "kottke", 9, "linearsolve:2:1:faithful", None, None, False, True, "SILENT_SWALLOW", "S2.6-pre-registered"),
    ("s2b/ls-fft-xsite",          "fft",    9, "linearsolve:2:1:info",     None, None, False, True, "INVALID",        "S2.6-pre-registered"),
    ("s2b/ls-kottke-xsite",       "kottke", 9, "linearsolve:1:1:info",     None, None, False, True, "INVALID",        "S2.6-pre-registered"),
    ("s2b/ls-fft-k99",            "fft",    9, "linearsolve:1:99:info",    None, None, False, True, "INVALID",        "S2.6-pre-registered"),
    ("s2b/ls-jones-s1",           "jones",  9, "linearsolve:1:1:info",     None, None, False, True, "INVALID",        "S2.6-pre-registered"),
    ("s2b/ls-jones-s2",           "jones",  9, "linearsolve:2:1:info",     None, None, False, True, "INVALID",        "S2.6-pre-registered"),
    ("s2b/ls-nv-s1",              "nv",     9, "linearsolve:1:1:info",     None, None, False, True, "INVALID",        "S2.6-pre-registered"),
    ("s2b/ls-nv-s2",              "nv",     9, "linearsolve:2:1:info",     None, None, False, True, "INVALID",        "S2.6-pre-registered"),
    ("s2b/ls-vl-s1",              "vl",     9, "linearsolve:1:1:info",     None, None, False, True, "INVALID",        "S2.6-pre-registered"),
    ("s2b/ls-vl-s2",              "vl",     9, "linearsolve:2:1:info",     None, None, False, True, "INVALID",        "S2.6-pre-registered"),
]

ENV_ALLOW = ("PATH", "LANG", "LC_ALL")


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


def _run_case(binary, case, runs_dir):
    name, mode, ng, inj, nth, pol = case[0], case[1], case[2], case[3], case[4], case[5]
    extra = {"FMM_MODE": mode, "S4FMM_NG": str(ng)}
    if inj is not None:
        extra["S4FMM_INJECT"] = inj
        # The linearsolve syntax carries its own K inside the value; NTH is not used.
        if nth is not None:
            extra["S4FMM_NTH"] = nth
    if pol is not None:
        extra["S4FMM_POL"] = pol
    log_path = os.path.join(runs_dir, name.replace("/", "__") + ".log")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    try:
        proc = subprocess.run([binary] + GRID, env=_child_env(extra), cwd=runs_dir,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=TIMEOUT_S)
        rc = proc.returncode
        out = proc.stdout
    except subprocess.TimeoutExpired as exc:
        rc = 124
        out = exc.stdout or b""
    # A negative returncode is a signal; report it as the shell does (128+n).
    if rc < 0:
        rc = 128 - rc
    with open(log_path, "wb") as fh:
        fh.write(out)
    return rc, log_path


def cmd_run(args):
    os.makedirs(args.runs, exist_ok=True)
    records = []
    for case in CASES:
        # LinearSolve-seam cases need the seam-built driver.  When no seam driver is
        # given they run on the default (unseamed) driver, which must answer INVALID.
        if case[3] is not None and str(case[3]).startswith("linearsolve:"):
            binary = args.seam_bin if getattr(args, "seam_bin", None) else args.bin
        else:
            binary = args.bin
        rc, log_path = _run_case(binary, case, args.runs)
        records.append({"name": case[0], "rc": rc, "log": log_path,
                        "sha256": _sha256(log_path)})
    with open(os.path.join(args.runs, "raw_rc.json"), "w", encoding="utf-8") as fh:
        json.dump(records, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("ran %d cases" % len(records))
    return 0


# Output-sensitivity cases (S2.3).  Each row: name, FMM_MODE, NG, POL_base, POL_changed,
# expected class, basis of the expectation.  NOT failure classes: they ask whether a
# known polarisation input reaches the first-call E/H.  The 'mix' row carries a
# corrected expectation, recorded with its basis; the others are pre-registered.
SENS_CASES = [
    ("sens/pb-vl-s-p",     "vl",     9, "s", "p",   "SENSITIVE",   "pre-registered"),
    ("sens/pb-jones-s-p",  "jones",  9, "s", "p",   "SENSITIVE",   "pre-registered"),
    ("sens/pb-nv-s-p",     "nv",     9, "s", "p",   "SENSITIVE",   "pre-registered"),
    ("sens/fft-nb1-s-p",   "fft",    1, "s", "p",   "SENSITIVE",   "pre-registered"),
    ("sens/fft-nb1-s-mix", "fft",    1, "s", "mix", "MIXED",       "corrected: S5b digest mix-phi0 n_diff=72"),
    ("sens/fft-nb1-s-s",   "fft",    1, "s", "s",   "INSENSITIVE", "control"),
]
SENS_THETA = "30"

# S2.6 injection-type sensitivity (added after SENS_CASES; SENS_CASES itself is unchanged).
# Each row compares the first-call E/H of a LinearSolve-seam injection with the matched
# un-injected control (base=None).  Registration time: see
# checkpoints/p05/evidence/p05-s2b/INJ_SENS_REGISTRATION_UTC.txt.
# Status of every expectation below: OBSERVED REPRODUCTION.  A single probe run was made
# before this table existed (fft faithful: SENSITIVE 144/144; fft info: INSENSITIVE), so
# these rows check that the observed behaviour reproduces inside the harness.  They are
# not blind pre-registrations.
INJ_SENS_CASES = [
    ("inj-sens/fft-info",        "fft",    9, None, "linearsolve:1:1:info",     "INSENSITIVE", "observed reproduction (probe)"),
    ("inj-sens/fft-faithful",    "fft",    9, None, "linearsolve:1:1:faithful", "SENSITIVE",   "observed reproduction (probe)"),
    ("inj-sens/kottke-faithful", "kottke", 9, None, "linearsolve:2:1:faithful", "SENSITIVE",   "PREDICTION (kottke faithful E/H never compared before this row)"),
]


def _first_dump(binary, mode, ng, pol, dump_path):
    extra = {"FMM_MODE": mode, "S4FMM_NG": str(ng), "S4FMM_THETA": SENS_THETA,
             "S4FMM_POL": pol, "S4FMM_DUMP1": dump_path}
    proc = subprocess.run([binary] + GRID, env=_child_env(extra),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=TIMEOUT_S)
    return proc.returncode


def cmd_sensitivity(args):
    os.makedirs(args.runs, exist_ok=True)
    dumps = {}
    rcs = {}
    for name, mode, ng, base, changed, _, _ in SENS_CASES:
        for pol in sorted({base, changed}):
            key = "%s-%s-%s" % (mode, ng, pol)
            if key not in dumps:
                path = os.path.join(args.runs, "dump-%s.txt" % key)
                rcs[key] = _first_dump(args.bin, mode, ng, pol, path)
                dumps[key] = path
    lines = ["# case\tclass\texpected\tmatch\tn\tn_over_1e-12\tmax_abs\tbasis"]
    bad = 0
    for name, mode, ng, base, changed, want, basis in SENS_CASES:
        kb = "%s-%s-%s" % (mode, ng, base)
        kc = "%s-%s-%s" % (mode, ng, changed)
        if rcs.get(kb) != 0 or rcs.get(kc) != 0:
            lines.append("\t".join([name, "INVALID", want, "NO", "-", "-", "-",
                                    "dump run rc=%s/%s" % (rcs.get(kb), rcs.get(kc))]))
            bad += 1
            continue
        with open(dumps[kb], encoding="utf-8") as fh:
            vb = J.read_dump(fh.read())
        with open(dumps[kc], encoding="utf-8") as fh:
            vc = J.read_dump(fh.read())
        cls, n, nover, mx = J.sensitivity(vb, vc)
        ok = cls == want
        bad += 0 if ok else 1
        lines.append("\t".join([name, cls, want, "yes" if ok else "NO", str(n), str(nover),
                                "%.4e" % mx, basis]))
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "sensitivity.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("sensitivity cases=%d mismatches=%d" % (len(SENS_CASES), bad))
    return 0


def _seam_dump(binary, mode, ng, inj, dump_path):
    """First-call E/H dump with an optional LinearSolve injection (inj=None: control)."""
    extra = {"FMM_MODE": mode, "S4FMM_NG": str(ng), "S4FMM_THETA": SENS_THETA,
             "S4FMM_DUMP1": dump_path}
    if inj is not None:
        extra["S4FMM_INJECT"] = inj
    proc = subprocess.run([binary] + GRID, env=_child_env(extra),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          timeout=TIMEOUT_S)
    return proc.returncode


def cmd_inj_sensitivity(args):
    """Injection-type output sensitivity (S2.6).  Control and injected runs use the SAME
    seam-built driver, so the only difference between them is the injection itself."""
    if not args.seam_bin:
        raise SystemExit("inj-sensitivity needs --seam-bin (the seam-built driver)")
    os.makedirs(args.runs, exist_ok=True)
    lines = ["# case\tclass\texpected\tmatch\tn\tn_over_1e-12\tmax_abs\tbasis"]
    bad = 0
    for name, mode, ng, base, changed, want, basis in INJ_SENS_CASES:
        ctl = os.path.join(args.runs, "injsens-%s-%s-ctl.txt" % (mode, ng))
        inj = os.path.join(args.runs, "injsens-%s-%s-%s.txt" % (mode, ng, name.split("/")[1]))
        rc_c = _seam_dump(args.seam_bin, mode, ng, base, ctl)
        rc_i = _seam_dump(args.seam_bin, mode, ng, changed, inj)
        if rc_c != 0 or rc_i not in (0, 1):
            lines.append("\t".join([name, "INVALID", want, "NO", "-", "-", "-",
                                    "dump run rc control=%s injected=%s" % (rc_c, rc_i)]))
            bad += 1
            continue
        with open(ctl, encoding="utf-8") as fh:
            vc = J.read_dump(fh.read())
        with open(inj, encoding="utf-8") as fh:
            vi = J.read_dump(fh.read())
        cls, n, nover, mx = J.sensitivity(vc, vi)
        ok = cls == want
        bad += 0 if ok else 1
        lines.append("\t".join([name, cls, want, "yes" if ok else "NO", str(n), str(nover),
                                "%.4e" % mx, basis]))
    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "inj_sensitivity.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("inj-sensitivity cases=%d mismatches=%d" % (len(INJ_SENS_CASES), bad))
    return 0


def _facts(log_path):
    with open(log_path, "rb") as fh:
        text = fh.read().decode("utf-8", errors="replace")
    return J.facts_from_log(text)


def cmd_classify(args):
    with open(os.path.join(args.runs, "raw_rc.json"), encoding="utf-8") as fh:
        raw = {r["name"]: r for r in json.load(fh)}
    os.makedirs(args.out, exist_ok=True)
    lines = ["# case\tclass\texpected\tmatch\trc\trc1\trc2\thit\tlabel\tlog_sha256"]
    mismatch = 0
    for case in CASES:
        name, control, real, want = case[0], case[6], case[7], case[8]
        rec = raw[name]
        f = _facts(rec["log"])
        cls, label, reason = J.classify(rec["rc"], f["rc1"], f["rc2"], f["hit"],
                                        control=control, real=real)
        ok = (cls == want)
        mismatch += 0 if ok else 1
        lines.append("\t".join([name, cls, want, "yes" if ok else "NO", str(rec["rc"]),
                                str(f["rc1"]), str(f["rc2"]), str(f["hit"]),
                                label or "-", rec["sha256"]]))
    with open(os.path.join(args.out, "index.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("cases=%d expectation_mismatches=%d" % (len(CASES), mismatch))
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--bin", required=True)
    r.add_argument("--seam-bin", default=None,
                   help="seam-built driver for linearsolve cases (default: use --bin)")
    r.add_argument("--ref", default=None)
    r.add_argument("--runs", required=True)
    r.add_argument("--root", default=None)
    r.add_argument("--out", required=True)
    c = sub.add_parser("classify")
    c.add_argument("--runs", required=True)
    c.add_argument("--out", required=True)
    s = sub.add_parser("sensitivity")
    s.add_argument("--bin", required=True)
    s.add_argument("--runs", required=True)
    s.add_argument("--out", required=True)
    isn = sub.add_parser("inj-sensitivity")
    isn.add_argument("--seam-bin", required=True)
    isn.add_argument("--runs", required=True)
    isn.add_argument("--out", required=True)
    args = p.parse_args(argv)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "sensitivity":
        return cmd_sensitivity(args)
    if args.cmd == "inj-sensitivity":
        return cmd_inj_sensitivity(args)
    if args.cmd == "classify":
        return cmd_classify(args)
    # Never fall through to a default command: an unrouted subcommand must fail loudly.
    raise SystemExit("unrouted subcommand: %r" % args.cmd)


if __name__ == "__main__":
    sys.exit(main())
