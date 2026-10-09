#!/usr/bin/env python3
"""Aggregate the P04 D001/D002 verification pipeline (testing/p04_run_all.sh).

Usage:  python3 -I -B testing/p04_aggregate.py OUT_DIR

Reads OUT_DIR/STEPS.txt (one "NAME rc=N" line per step, as written by the pipeline) and
the evidence each step produced.  Every step is classified as:

  ok               it was expected to pass and passed (rc 0 and its judgement agrees);
  expected_defect  a baseline step that is expected to reproduce the original defect:
                   rc 1 AND the defect signature is met by the raw evidence (see below);
  unexpected       anything else (non-zero rc, a missing or inconsistent judgement, a
                   baseline that did not reproduce the defect, a duplicated or unknown step).

Judgements are not trusted as recorded.  The D002 judgement is recomputed from the saved
driver output by testing/d002/run_d002.py (schema 2 only), and the recorded judgement file
must agree with that recomputation field by field.  The D001 summaries are checked as a
complete set: every expected case key exactly once, with its identity, and the failures
must be exactly the registered defect set for a baseline.  The sanitizer positive controls
are checked against their own stderr files and recorded exit status.  The artifact manifest
must list every artifact of the pipeline, and each listed artifact must exist and hash to the
recorded value.

The raw return codes are never rewritten.  Writes OUT_DIR/AGGREGATE.json and exits 0 only
when every expected step is present and classified ok or expected_defect.  Exit 2 means the
aggregator itself could not read the pipeline output.
"""

import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "d002"))
sys.path.insert(0, os.path.join(HERE, "d001"))
import run_d002 as d2  # noqa: E402  (stdlib only; the same judge the pipeline runs)
import model_d001 as d1model  # noqa: E402  (stdlib only; frozen 12-case table)
import run_d001_extension as d1ext  # noqa: E402  (stdlib only; 113-case extension table)

D2_VARIANTS = ["ord_candidate", "asan_candidate", "seam_asan_candidate",
               "ord_baseline", "asan_baseline", "seam_asan_baseline"]
D2_BASELINES = {"ord_baseline", "asan_baseline", "seam_asan_baseline"}
D001_FROZEN_BASE_FAIL = {
    "N9|B_SAME_MATERIAL_CIRCLE|r1", "N9|B_SAME_MATERIAL_CIRCLE|r2",
    "N9|C_ISOTROPIC_TENSOR|r1", "N9|C_ISOTROPIC_TENSOR|r2",
}
D001_FROZEN_CASES = 12
D001_EXT_CASES = 113
ARTIFACT_LABELS = (
    ["candidate-lib", "candidate-cli", "candidate-rcwa", "candidate-pyext",
     "candidate-Eigensystems.cpp",
     "seam-lib", "seam-cli", "seam-pyext",
     "baseline-lib", "baseline-cli", "baseline-pyext", "baseline-Eigensystems.cpp"]
    + ["d002-bin-%s" % v for v in D2_VARIANTS]
)
SHA_RE = re.compile(r"^[0-9a-f]{64}$")


class AggregateInputError(Exception):
    pass


def load_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as exc:
        raise AggregateInputError("cannot read %s: %s" % (path, exc))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_steps(out_dir):
    path = os.path.join(out_dir, "STEPS.txt")
    steps = []
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        raise AggregateInputError("cannot read %s: %s" % (path, exc))
    for ln in lines:
        if not ln.strip() or ln.startswith("#") or "=" not in ln:
            continue
        head, _, rc_text = ln.rpartition(" rc=")
        if not head or not rc_text.lstrip("-").isdigit():
            if ln.startswith("root"):
                continue
            raise AggregateInputError("malformed STEPS line %r" % ln)
        steps.append((head, int(rc_text)))
    return steps


def expected_steps():
    names = ["export_baseline", "build_candidate_lib", "build_candidate_pyext",
             "build_baseline_lib", "build_baseline_pyext", "build_seam_lib", "build_seam_pyext",
             "d001_frozen_candidate", "d001_frozen_baseline", "d001_ext_candidate",
             "d001_ext_baseline", "d001_oracle_selfcheck", "d002_unit_tests",
             "p04_aggregate_selftest"]
    for v in D2_VARIANTS:
        names += ["d002_build_%s" % v, "d002_run_%s" % v, "d002_judge_%s" % v]
    names += ["d002_positives", "error20", "s4test_candidate", "s4test_baseline",
              "lua_regression", "python_binding_smoke"]
    return names


# ------------------------------------------------------------------ D001

def ext_defect(case):
    """Registered extension defect: representation B or C at N=9 or N=25 (memory mode rows
    are all N=9 B/C).  Every other extension row is a control that must pass."""
    return case["N"] in (9, 25) and case["rep"] in ("B", "C")


def d001_expected(which):
    """Returns (key field name, {key: case entry}, identity fields, expected defect keys)."""
    if which == "frozen":
        cases = d1model.load_cases()
        by_key = {c["case_key"]: c for c in cases}
        return "case_key", by_key, None, D001_FROZEN_BASE_FAIL
    cases = d1ext.build_cases()
    by_key = {c["key"]: c for c in cases}
    defect = {k for k, c in by_key.items() if ext_defect(c)}
    return "key", by_key, ("f", "theta", "pol", "N", "rep", "mem"), defect


def frozen_identity_problems(row, case):
    want = {"requested_num_basis": case["requested_num_basis"],
            "representation": case["representation"], "repeat": case["repeat"]}
    return ["%s=%r, expected %r" % (k, row.get(k), v) for k, v in want.items() if row.get(k) != v]


def ext_identity_problems(row, case):
    want = {"f": case["f"], "theta": case["theta"], "pol": case["pol"], "N": case["N"],
            "rep": case["rep"], "mem": case["mem"]}
    return ["%s=%r, expected %r" % (k, row.get(k), v) for k, v in want.items() if row.get(k) != v]


def check_d001(out_dir, label_dir, label, which, baseline):
    """Returns (ok, reason, failing keys) for one D001 summary."""
    path = os.path.join(out_dir, "d001", label_dir, "SUMMARY_%s.json" % label)
    d = load_json(path)
    if not isinstance(d, dict):
        return False, "summary is not an object", []
    rows = d.get("rows")
    if not isinstance(rows, list):
        return False, "summary has no rows list", []
    key_field, by_key, ident_fields, defect = d001_expected(which)
    expect_total = D001_FROZEN_CASES if which == "frozen" else D001_EXT_CASES
    problems = []
    if d.get("cases_total") != expect_total or len(rows) != expect_total:
        problems.append("cases_total=%s rows=%d expected %d" % (d.get("cases_total"), len(rows), expect_total))
    seen = {}
    fails = []
    for row in rows:
        key = row.get(key_field) if isinstance(row, dict) else None
        if key not in by_key:
            problems.append("unknown case key %r" % (key,))
            continue
        if key in seen:
            problems.append("duplicate case key %s" % key)
            continue
        seen[key] = row
        case = by_key[key]
        ident = (frozen_identity_problems if which == "frozen" else ext_identity_problems)(row, case)
        if ident:
            problems.append("%s identity: %s" % (key, "; ".join(ident)))
        if row.get("pass") is not True:
            fails.append(key)
    missing = [k for k in by_key if k not in seen]
    if missing:
        problems.append("missing case keys (%d): %s" % (len(missing), ", ".join(sorted(missing)[:5])))
    s4 = os.path.basename(str(d.get("s4_dir", "")).rstrip("/"))
    if baseline and s4 != "baseline-src":
        problems.append("baseline summary built from %r" % s4)
    if not baseline and s4 == "baseline-src":
        problems.append("candidate summary built from baseline-src")
    if not baseline:
        if fails:
            problems.append("candidate fails %d of %d: %s" % (len(fails), expect_total, sorted(fails)[:5]))
    else:
        unexpected_fail = sorted(set(fails) - defect)
        not_failing = sorted(defect - set(fails))
        if unexpected_fail:
            problems.append("baseline failures outside the defect set: %s" % ", ".join(unexpected_fail[:5]))
        if not_failing:
            problems.append("defect set not reproduced: %s" % ", ".join(not_failing[:5]))
    if problems:
        return False, "; ".join(problems[:4]), fails
    if baseline:
        return True, "%d/%d fail, exactly the registered defect set" % (len(fails), expect_total), fails
    return True, "%d/%d pass" % (expect_total - len(fails), expect_total), fails


def judge_d001(out_dir, which):
    """Returns (ok, reason) for a D001 step after its rc was checked."""
    if which == "frozen_candidate":
        ok, why, _ = check_d001(out_dir, "frozen-candidate", "candidate", "frozen", False)
        return ok, "frozen candidate " + why
    if which == "ext_candidate":
        ok, why, _ = check_d001(out_dir, "ext-candidate", "candidate", "ext", False)
        return ok, "extension candidate " + why
    if which == "frozen_baseline":
        ok, why, _ = check_d001(out_dir, "frozen-baseline", "baseline", "frozen", True)
        return ok, ("frozen baseline reproduces N9 B/C (4 rows)" if ok else why)
    if which == "ext_baseline":
        ok, why, _ = check_d001(out_dir, "ext-baseline", "baseline", "ext", True)
        return ok, ("extension baseline " + why) if ok else why
    raise AssertionError(which)


# ------------------------------------------------------------------ D002

JUDGEMENT_FIELDS = ("variant", "integrity", "fatal", "complete_run", "accepted", "all_judged_pass",
                    "cases_total", "cases_judged", "cases_pass", "cases_fail",
                    "cases_not_applicable", "cases_recorded_probe", "integrity_failures",
                    "integrity_kinds")


def judgement_mismatch(recorded, fresh):
    """First field where the recorded judgement disagrees with the raw-evidence judgement."""
    if "integrity_kinds" not in recorded:
        return "the file was written by an older judge (no integrity_kinds); it must be re-judged"
    for k in JUDGEMENT_FIELDS:
        if recorded.get(k) != fresh.get(k):
            return "%s recorded %r, raw evidence %r" % (k, recorded.get(k), fresh.get(k))
    rec_sig = recorded.get("signature")
    fresh_sig = fresh.get("signature")
    if (rec_sig or {}).get("ok") != (fresh_sig or {}).get("ok"):
        return "signature.ok recorded %r, raw evidence %r" % ((rec_sig or {}).get("ok"),
                                                              (fresh_sig or {}).get("ok"))
    rec_results = recorded.get("results")
    if not isinstance(rec_results, list):
        return "results is not a list"
    rec_by = {r.get("case_id"): r for r in rec_results if isinstance(r, dict)}
    if len(rec_by) != len(rec_results):
        return "results contain a non-object or duplicate case"
    fresh_by = {r["case_id"]: r for r in fresh["results"]}
    if set(rec_by) != set(fresh_by):
        return "case coverage differs from the run index"
    for cid, fr in fresh_by.items():
        rr = rec_by[cid]
        for k in ("status", "pass", "integrity_kind"):
            if rr.get(k) != fr.get(k):
                return "%s %s recorded %r, raw evidence %r" % (cid, k, rr.get(k), fr.get(k))
    return None


def judge_d002(out_dir, variant):
    path = os.path.join(out_dir, "d002", "run", variant, "JUDGE_%s.json" % variant)
    recorded = load_json(path)
    if not isinstance(recorded, dict):
        return False, "judgement file is not an object"
    fresh = d2.judge_variant(os.path.join(out_dir, "d002", "run"), variant)
    if fresh["integrity"] == "fatal":
        return False, "judge fatal: %s" % fresh["fatal"]
    mismatch = judgement_mismatch(recorded, fresh)
    if mismatch:
        return False, "recorded judgement disagrees with its raw evidence: %s" % mismatch
    if variant in D2_BASELINES:
        sig = fresh["signature"]
        if not sig["ok"]:
            return False, "signature not met: not_failing=%s not_passing=%s damaged=%s" % (
                sig["not_failing"], sig["not_passing"], sig["damaged"])
        if not fresh["complete_run"]:
            return False, "baseline run is not a complete run"
        allowed = set(sig["must_fail"]) | set(sig["may_fail"])
        if fresh["integrity_failures"] and not set(fresh["integrity_failures"]) <= allowed:
            return False, "integrity failure outside the defect signature: %s" % fresh["integrity_failures"]
        return True, "defect reproduced: %d/%d judged pass, signature ok" % (
            fresh["cases_pass"], fresh["cases_judged"])
    if not fresh["accepted"]:
        return False, "candidate not accepted (pass=%s/%s complete=%s integrity_failures=%s)" % (
            fresh["cases_pass"], fresh["cases_judged"], fresh["complete_run"],
            fresh["integrity_failures"])
    return True, "accepted %d/%d" % (fresh["cases_pass"], fresh["cases_judged"])


def judge_positives(out_dir):
    pdir = os.path.join(out_dir, "d002", "positives")
    rows = load_json(os.path.join(pdir, "POSITIVES.json"))
    if not isinstance(rows, list) or not rows:
        return False, "POSITIVES.json empty or not a list"
    seen = {}
    problems = []
    for r in rows:
        name = r.get("control") if isinstance(r, dict) else None
        if name not in d2.POSITIVE_SIGNATURES:
            problems.append("unknown control %r" % (name,))
        elif name in seen:
            problems.append("duplicate control %s" % name)
        else:
            seen[name] = r
    for name in d2.POSITIVE_SIGNATURES:
        if name not in seen:
            problems.append("control %s missing" % name)
    for name, r in seen.items():
        signature = d2.POSITIVE_SIGNATURES[name]
        if r.get("pass") is not True or r.get("signature") != signature or r.get("signature_seen") is not True:
            problems.append("%s record does not report its signature" % name)
            continue
        try:
            with open(os.path.join(pdir, name + ".stderr"), encoding="utf-8", errors="replace") as fh:
                stderr = fh.read()
        except OSError:
            problems.append("%s stderr missing" % name)
            continue
        if signature not in stderr:
            problems.append("%s signature absent from its own stderr" % name)
        # The exit status must be recorded as an integer and must match the build: pos_ubsan is
        # compiled without -fno-sanitize-recover, so UBSan reports and the program exits 0; the
        # ASan controls abort on their report (ASan's default exit code is 1).
        exit_status = r.get("exit")
        if type(exit_status) is not int:
            problems.append("%s exit is not an integer status: %r" % (name, exit_status))
        elif name == "pos_ubsan" and exit_status != 0:
            problems.append("pos_ubsan exited %d; this build recovers from UBSan reports (exit 0)"
                            % exit_status)
        elif name != "pos_ubsan" and exit_status == 0:
            problems.append("%s did not exit abnormally" % name)
    if problems:
        return False, "; ".join(problems)
    return True, "all %d sanitizer controls report their signature in their stderr" % len(seen)


# ------------------------------------------------------------------ classification

def classify(out_dir, name, rc):
    """Returns (classification, expectation, reason)."""
    if name.startswith("d001_frozen_baseline") or name == "d001_ext_baseline":
        which = "frozen_baseline" if name.startswith("d001_frozen") else "ext_baseline"
        if rc != 1:
            return "unexpected", "expected defect rc=1", "rc=%d" % rc
        ok, why = judge_d001(out_dir, which)
        return ("expected_defect" if ok else "unexpected"), "expected defect rc=1", why
    if name in ("d001_frozen_candidate", "d001_ext_candidate"):
        which = "frozen_candidate" if "frozen" in name else "ext_candidate"
        if rc != 0:
            return "unexpected", "must pass", "rc=%d" % rc
        ok, why = judge_d001(out_dir, which)
        return ("ok" if ok else "unexpected"), "must pass", why
    if name.startswith("d002_judge_"):
        v = name[len("d002_judge_"):]
        if v in D2_BASELINES:
            if rc != 1:
                return "unexpected", "expected defect rc=1", "rc=%d" % rc
            ok, why = judge_d002(out_dir, v)
            return ("expected_defect" if ok else "unexpected"), "expected defect rc=1", why
        if rc != 0:
            return "unexpected", "must pass", "rc=%d" % rc
        ok, why = judge_d002(out_dir, v)
        return ("ok" if ok else "unexpected"), "must pass", why
    if name == "d002_positives":
        if rc != 0:
            return "unexpected", "must pass", "rc=%d" % rc
        ok, why = judge_positives(out_dir)
        return ("ok" if ok else "unexpected"), "must pass", why
    if rc != 0:
        return "unexpected", "must pass", "rc=%d" % rc
    return "ok", "must pass", "rc=0"


# ------------------------------------------------------------------ artifacts

def check_manifest(path):
    """Returns the list of problems with ARTIFACTS.sha256 (empty when it is complete and true).

    Each record is "SHA256<TAB>LABEL<TAB>PATH"; a failed hashing step is written as
    "# MISSING<TAB>LABEL<TAB>PATH".  Every label in ARTIFACT_LABELS must be recorded exactly
    once, and each recorded file must exist and hash to the recorded value now.
    """
    problems = []
    seen = {}
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for lineno, ln in enumerate(lines, 1):
        if not ln.strip():
            continue
        parts = ln.split("\t")
        if ln.startswith("# MISSING\t") and len(parts) == 3:
            problems.append("%s not present (%s)" % (parts[1], parts[2]))
            continue
        if len(parts) != 3 or not SHA_RE.match(parts[0]):
            problems.append("line %d is not a SHA256 record" % lineno)
            continue
        digest, label, fpath = parts
        if label not in ARTIFACT_LABELS:
            problems.append("line %d: unknown artifact label %s" % (lineno, label))
            continue
        if label in seen:
            problems.append("artifact %s recorded twice" % label)
            continue
        seen[label] = digest
        if not os.path.isfile(fpath):
            problems.append("%s absent at %s" % (label, fpath))
        elif sha256_file(fpath) != digest:
            problems.append("%s hash differs from the manifest" % label)
    absent = [label for label in ARTIFACT_LABELS if label not in seen]
    if absent:
        problems.append("no record for %d artifact(s): %s" % (len(absent), ", ".join(absent[:6])))
    return problems


# ------------------------------------------------------------------ aggregate

def aggregate(out_dir):
    steps = read_steps(out_dir)
    expected = expected_steps()
    records = []
    problems = []
    for name, rc in steps:
        if name not in expected:
            records.append({"step": name, "rc": rc, "classification": "unexpected",
                            "expectation": "unknown step", "reason": "not part of the pipeline"})
            problems.append("unknown step %s" % name)
    for name in expected:
        hits = [rc for n, rc in steps if n == name]
        if not hits:
            records.append({"step": name, "rc": None, "classification": "unexpected",
                            "expectation": "must run", "reason": "step not recorded"})
            problems.append("missing step %s" % name)
            continue
        if len(hits) > 1:
            records.append({"step": name, "rc": hits, "classification": "unexpected",
                            "expectation": "run once", "reason": "step recorded %d times" % len(hits)})
            problems.append("duplicated step %s" % name)
            continue
        rc = hits[0]
        try:
            cls, exp, why = classify(out_dir, name, rc)
        except Exception as exc:  # any unreadable or malformed judgement is a failed step
            cls, exp, why = "unexpected", "judgement readable", "judgement unreadable: %s: %s" % (
                type(exc).__name__, exc)
        records.append({"step": name, "rc": rc, "classification": cls,
                        "expectation": exp, "reason": why})
    manifest = os.path.join(out_dir, "ARTIFACTS.sha256")
    if not os.path.isfile(manifest):
        records.append({"step": "ARTIFACTS.sha256", "rc": None, "classification": "unexpected",
                        "expectation": "written", "reason": "artifact manifest missing"})
        problems.append("artifact manifest missing")
    else:
        try:
            manifest_problems = check_manifest(manifest)
        except (OSError, UnicodeDecodeError) as exc:
            manifest_problems = ["manifest unreadable: %s" % exc]
        if manifest_problems:
            records.append({"step": "ARTIFACTS.sha256", "rc": None, "classification": "unexpected",
                            "expectation": "every artifact present and hashed",
                            "reason": "; ".join(manifest_problems[:4])})
            problems.append("artifact manifest: %s" % manifest_problems[0])
        else:
            records.append({"step": "ARTIFACTS.sha256", "rc": None, "classification": "ok",
                            "expectation": "every artifact present and hashed",
                            "reason": "all %d artifacts present and hashed" % len(ARTIFACT_LABELS)})
    unexpected = [r["step"] for r in records if r["classification"] == "unexpected"]
    overall = "PASS" if not unexpected else "FAIL"
    return {"overall": overall, "unexpected": unexpected, "problems": problems,
            "steps": records, "steps_recorded": len(steps)}


def main(argv):
    if len(argv) != 2:
        sys.stderr.write("usage: p04_aggregate.py OUT_DIR\n")
        return 2
    out_dir = os.path.realpath(argv[1])
    try:
        result = aggregate(out_dir)
    except AggregateInputError as exc:
        sys.stderr.write("aggregate: %s\n" % exc)
        return 2
    with open(os.path.join(out_dir, "AGGREGATE.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1, sort_keys=True)
    for r in result["steps"]:
        print("%-28s rc=%-4s %-16s %s" % (r["step"], r["rc"], r["classification"], r["reason"]))
    print("overall %s (%d steps recorded, %d unexpected)" % (
        result["overall"], result["steps_recorded"], len(result["unexpected"])))
    return 0 if result["overall"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
