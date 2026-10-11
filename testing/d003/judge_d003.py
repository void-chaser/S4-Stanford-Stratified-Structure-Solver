#!/usr/bin/env python3
"""D003 baseline failure judge (P05-S2).

Turns one run's raw facts into one class.  The rules are the S1B appendix b.2
rules, fixed before any S2 run, and are restated in CLASSES below.  The judge
never reads the PASS/FAIL verdict line of the driver: for an injection run that
verdict has no discriminating power (S1B appendix b.1).

Inputs (per run):
    rc        process exit status; a signal is reported as 128+signal by the
              shell, a timeout as 124.
    rc1, rc2  first and retry return codes printed by the driver, or None.
    hit       number of times the requested fault was reached.  Taken from the
              driver line "S4FMM HITCOUNT n" when present, otherwise counted from
              "S4FMM HIT" lines.
    control   True for a run with no injection requested.
    real      True when the injected site is a real allocation; False for the
              boundary simulation (exec).  Only affects labels, never the class.

Classes (first match wins):
    INVALID          control run that is not clean (hit != 0, or rc1 != 0, or rc != 0
                     without a signal); or an injection run that was never reached
                     (hit == 0).  Not evidence about the code under test.
    CRASH            injection reached and the process was killed by a signal (rc >= 128).
    SILENT_SWALLOW   injection reached, rc1 == 0, not killed by a signal: the failure
                     did not reach the caller.  The driver's own PASS/FAIL exit code
                     is NOT used (the driver marks an unreported injection as FAIL).
    REPORTED_FAILURE injection reached and rc1 != 0 (the failure was reported).
    CONTROL_OK       control run, rc == 0, rc1 == 0, hit == 0.

Usage:
    judge_d003.py classify --rc N --rc1 N|none --rc2 N|none --hit N [--control] [--real|--boundary]
    judge_d003.py selftest
"""
import argparse
import json
import os
import re
import sys

CLASSES = ("INVALID", "CRASH", "SILENT_SWALLOW", "REPORTED_FAILURE", "CONTROL_OK")

_HIT_LINE = re.compile(r"^S4FMM HIT ", re.M)
_HITCOUNT = re.compile(r"^S4FMM HITCOUNT (-?\d+)\s*$", re.M)
_RC1 = re.compile(r"^RC first (-?\d+)\s*$", re.M)
_RC2 = re.compile(r"^RC retry (-?\d+)\s*$", re.M)


def _opt_int(text):
    if text is None or text == "none":
        return None
    return int(text)


def classify(rc, rc1, rc2, hit, control, real=True):
    """Return (class, label, reason).  Pure function; no I/O."""
    label = "" if real else "(boundary simulation)"
    if rc is None:
        return "INVALID", label, "rc missing: the run did not complete"
    if control:
        if hit != 0:
            return "INVALID", label, "control run reached an injection (hit=%d)" % hit
        if rc == 0 and rc1 == 0:
            return "CONTROL_OK", label, "clean control"
        return "INVALID", label, "control run not clean (rc=%d rc1=%s)" % (rc, rc1)
    if hit == 0:
        return "INVALID", label, "injection never reached (hit=0)"
    if rc >= 128:
        return "CRASH", label, "killed by signal %d (rc=%d)" % (rc - 128, rc)
    # The driver's own PASS/FAIL exit code is a verdict about the driver, not about
    # the code under test.  Only "not killed by a signal" and the first-call return
    # value decide this class; rc == 1 from the driver's else-branch does not.
    if rc1 == 0:
        return "SILENT_SWALLOW", label, "reached, first call returned 0 (rc=%d)" % rc
    if rc1 is not None and rc1 != 0:
        return "REPORTED_FAILURE", label, "reached, first call returned %d" % rc1
    return "INVALID", label, "unclassified state (rc=%d rc1=%s)" % (rc, rc1)


def facts_from_log(text):
    """Extract the judge inputs from a driver log.  Missing lines give None."""
    m1 = _RC1.search(text)
    m2 = _RC2.search(text)
    hc = _HITCOUNT.search(text)
    hit = int(hc.group(1)) if hc else len(_HIT_LINE.findall(text))
    return {
        "rc1": int(m1.group(1)) if m1 else None,
        "rc2": int(m2.group(1)) if m2 else None,
        "hit": hit,
    }


def _cli_classify(args):
    cls, label, reason = classify(
        args.rc, _opt_int(args.rc1), _opt_int(args.rc2), args.hit,
        control=args.control, real=not args.boundary)
    print(json.dumps({"class": cls, "label": label, "reason": reason}))
    return 0


# ---------------------------------------------------------------------------
# Self-test fixtures.  One fixture per class, plus sensitivity checks that show
# a tampered input is detected (the judge must not be insensitive).
# ---------------------------------------------------------------------------
def selftest():
    fails = []

    def expect(name, got, want):
        ok = got == want
        print("%-44s %-18s want=%-18s %s" % (name, got, want, "ok" if ok else "FAILED"))
        if not ok:
            fails.append(name)

    # One fixture per class (values are the S1B observed values).
    expect("fixture: plan1 fft (crash, hit 1)",
           classify(139, None, None, 1, control=False)[0], "CRASH")
    expect("fixture: exec1 fft (silent, boundary)",
           classify(0, 0, 0, 1, control=False, real=False)[0], "SILENT_SWALLOW")
    expect("fixture: scratch1 fft (silent, real)",
           classify(0, 0, 0, 1, control=False, real=True)[0], "SILENT_SWALLOW")
    # Driver verdict FAIL (rc=1) in the else-branch with hit>=1 and rc1=0 is still a
    # swallowed failure: the class must come from the facts, not from the verdict code.
    expect("fixture: driver verdict FAIL, swallowed",
           classify(1, 0, 0, 1, control=False, real=True)[0], "SILENT_SWALLOW")
    expect("fixture: driver verdict FAIL, boundary",
           classify(1, 0, 0, 1, control=False, real=False)[0], "SILENT_SWALLOW")
    expect("fixture: reported failure (rc1=1, hit 1)",
           classify(1, 1, 0, 1, control=False)[0], "REPORTED_FAILURE")
    expect("fixture: control fft ng9 (clean)",
           classify(0, 0, 0, 0, control=True)[0], "CONTROL_OK")
    expect("fixture: injection never reached (hit 0)",
           classify(0, 0, 0, 0, control=False)[0], "INVALID")
    expect("fixture: control vl ng1 (native failure)",
           classify(1, 20, 20, 0, control=True)[0], "INVALID")

    # Sensitivity: tamper with one input at a time; the class must change.
    base = dict(rc=0, rc1=0, rc2=0, hit=1, control=False, real=True)
    expect("sensitivity: rc 0->139 changes class",
           classify(**dict(base, rc=139))[0] != classify(**base)[0], True)
    expect("sensitivity: rc1 0->1 changes class",
           classify(**dict(base, rc1=1))[0] != classify(**base)[0], True)
    expect("sensitivity: hit 1->0 changes class",
           classify(**dict(base, hit=0))[0] != classify(**base)[0], True)
    expect("sensitivity: boundary flag changes label only",
           classify(**dict(base, real=False))[0] == classify(**base)[0], True)
    # A reported failure (rc1!=0) and a swallowed one (rc1==0) must never be confused,
    # whatever the driver's exit code says.
    expect("sensitivity: rc1 decides reported vs swallowed",
           classify(1, 1, 0, 1, control=False)[0] != classify(1, 0, 0, 1, control=False)[0], True)

    # Log parsing: the judge must read the real driver text, not a guess.
    sample = ("S4FMM HIT real malloc failure: FFT execution scratch 16 B (hit=1)\n"
              "RC first 0\nRC retry 0\nS4FMM HITCOUNT 1\nRESULT no injection fired\n")
    f = facts_from_log(sample)
    expect("parse: hit from HITCOUNT", f["hit"], 1)
    expect("parse: rc1 from RC first", f["rc1"], 0)
    expect("parse: rc2 from RC retry", f["rc2"], 0)
    tampered = sample.replace("S4FMM HITCOUNT 1", "S4FMM HITCOUNT 0")
    expect("sensitivity: tampered HITCOUNT detected",
           facts_from_log(tampered)["hit"] != f["hit"], True)
    no_hitcount = "RC first 1\nRC retry 0\nS4FMM HIT x (hit=1)\n"
    expect("parse: HIT lines counted when no HITCOUNT",
           facts_from_log(no_hitcount)["hit"], 1)

    # R2 new-category fixtures (P05-S2R).  Each row is an observed fact pattern for a
    # point category added in this round; the class is decided by the same rules as above.
    # Crash: killed by a signal after the hook fired (no summary line is printed).
    expect("R2 new: alloc crash (S4.cpp sites 21/22/25, reached, SIGSEGV)",
           classify(139, None, None, 1, control=False)[0], "CRASH")
    # Silent: a NULL workspace is accepted and the call returns 0 (S4.cpp sites 23/24).
    expect("R2 new: alloc silent (sites 23/24, rc1 0)",
           classify(1, 0, 0, 1, control=False)[0], "SILENT_SWALLOW")
    # Correct failure: the reported solve_info path returns the existing code 20 (family A).
    expect("R2 new: solve_info reported (family A, rc1 20)",
           classify(1, 20, 0, 1, control=False)[0], "REPORTED_FAILURE")
    # Not reached: the requested point was never hit, so the run is INVALID, never a pass.
    expect("R2 new: unreached point (hit 0)",
           classify(1, 0, 0, 0, control=False)[0], "INVALID")
    # A control with the new families linked but no request must stay CONTROL_OK.
    expect("R2 new: control with seam linked (clean)",
           classify(0, 0, 0, 0, control=True)[0], "CONTROL_OK")
    # Sensitivity: swapping a reported failure for a swallowed one must change the class.
    expect("R2 new sensitivity: rc1 20 vs 0 changes class",
           classify(1, 20, 0, 1, control=False)[0] != classify(1, 0, 0, 1, control=False)[0], True)

    if fails:
        print("SELFTEST FAILED: %d" % len(fails))
        return 1
    print("SELFTEST PASSED")
    return 0


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("classify")
    c.add_argument("--rc", type=int, required=True)
    c.add_argument("--rc1", default="none")
    c.add_argument("--rc2", default="none")
    c.add_argument("--hit", type=int, required=True)
    c.add_argument("--control", action="store_true")
    c.add_argument("--boundary", action="store_true",
                   help="exec boundary simulation (label only)")
    sub.add_parser("selftest")
    sub.add_parser("selftest-sensitivity")
    args = p.parse_args(argv)
    if args.cmd == "classify":
        return _cli_classify(args)
    if args.cmd == "selftest-sensitivity":
        return selftest_sensitivity()
    return selftest()


# ---------------------------------------------------------------------------
# Output-sensitivity judge (P05-S2 section S2.3).  These checks are NOT failure
# classes: they ask whether a known input change reaches the output.  Threshold
# 1e-12 matches S5 and S5b.
# ---------------------------------------------------------------------------
SENSITIVITY_THRESHOLD = 1e-12


def read_dump(text):
    """Parse a driver E/H dump ("E|H index value" lines).  Malformed input raises."""
    values = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        if len(parts) != 3 or parts[0] not in ("E", "H"):
            raise ValueError("malformed dump line: %r" % line)
        key = (parts[0], int(parts[1]))
        if key in values:
            raise ValueError("duplicate dump key: %r" % (key,))
        values[key] = float(parts[2])
    return values


def sensitivity(base, changed, threshold=SENSITIVITY_THRESHOLD):
    """Compare two dumps on identical keys.  Returns (class, n, n_over, max_abs).

    SENSITIVE   every element differs by more than the threshold somewhere
    INSENSITIVE no element differs by more than the threshold
    MIXED       otherwise (reported, never silently merged)
    """
    if set(base) != set(changed):
        raise ValueError("dumps do not share the same keys")
    diffs = [abs(base[k] - changed[k]) for k in base]
    n_over = sum(1 for x in diffs if x > threshold)
    max_abs = max(diffs) if diffs else 0.0
    if n_over == 0:
        cls = "INSENSITIVE"
    elif n_over == len(diffs):
        cls = "SENSITIVE"
    else:
        cls = "MIXED"
    return cls, len(diffs), n_over, max_abs


def selftest_sensitivity():
    fails = []

    def expect(name, got, want):
        ok = got == want
        print("%-44s %-14s want=%-14s %s" % (name, got, want, "ok" if ok else "FAILED"))
        if not ok:
            fails.append(name)

    base = {("E", i): float(i) for i in range(6)}
    same = dict(base)
    moved = dict(base)
    moved[("E", 0)] = base[("E", 0)] + 1.0
    expect("output: identical dumps are INSENSITIVE",
           sensitivity(base, same)[0], "INSENSITIVE")
    expect("output: every element moved is SENSITIVE",
           sensitivity(base, {k: v + 1.0 for k, v in base.items()})[0], "SENSITIVE")
    expect("output: one element moved is MIXED",
           sensitivity(base, moved)[0], "MIXED")
    # Tamper test: silently swallowing the polarisation input must be detected.
    # A changed run that equals the control is INSENSITIVE, which the caller treats
    # as a failed sensitivity check, never as a pass.
    expect("tamper: swallowed input is detected (INSENSITIVE)",
           sensitivity(base, dict(base))[0], "INSENSITIVE")
    # Sub-threshold noise must not count as a change.
    noisy = {k: v + 1e-15 for k, v in base.items()}
    expect("noise below 1e-12 is INSENSITIVE",
           sensitivity(base, noisy)[0], "INSENSITIVE")
    # Parser must reject malformed and duplicated records instead of guessing.
    try:
        read_dump("E 0 1.0\nE 0 2.0\n")
        expect("parse: duplicate key rejected", "accepted", "rejected")
    except ValueError:
        expect("parse: duplicate key rejected", "rejected", "rejected")
    try:
        read_dump("X 0 1.0\n")
        expect("parse: unknown tag rejected", "accepted", "rejected")
    except ValueError:
        expect("parse: unknown tag rejected", "rejected", "rejected")
    # R2 new-category sensitivity (P05-S2R).  A seam whose injection changes no value must
    # read INSENSITIVE (e.g. the RHS-computed model, id 11); an injection that changes every
    # element must read SENSITIVE; one changed element must read MIXED.  Same mechanics as
    # above, on the new family's dump shape (E and H, 144-element plane).
    rbase = {("E", i): float(i) for i in range(144)}
    rall = {k: v + 1.0 for k, v in rbase.items()}
    expect("R2 new sensitivity: model-2 (no value change) is INSENSITIVE",
           sensitivity(rbase, dict(rbase))[0], "INSENSITIVE")
    expect("R2 new sensitivity: model-1 full overwrite is SENSITIVE",
           sensitivity(rbase, rall)[0], "SENSITIVE")
    rone_base = dict(rbase)
    rone_base[("H", 0)] = 0.0
    rone = dict(rbase)
    rone[("H", 0)] = 5.0
    expect("R2 new sensitivity: one H element moved is MIXED",
           sensitivity(rone_base, rone)[0], "MIXED")
    if fails:
        print("SENSITIVITY SELFTEST FAILED: %d" % len(fails))
        return 1
    print("SENSITIVITY SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
