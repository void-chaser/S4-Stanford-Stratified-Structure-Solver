#!/usr/bin/env python3
"""Failure-injection tests for testing/p04_aggregate.py.

The control is real evidence, not a summary written by hand: the saved schema-2 run of the
final pipeline (testing/d002/tests/fixtures/p04_schema2_control.tar.gz) holds the six D002
driver outputs and the four D001 summaries, and the D002 judgements are produced by the
judge itself.  Every artifact in the manifest is a file written by the test with its real
SHA-256.  Each negative test changes one thing, re-judges where the judge would be re-run,
and checks the aggregate verdict and the reason of the affected step.  Only the STEPS.txt
return codes (raw by design) are written by hand.  Nothing is written outside a temporary
directory.

Run:  python3 -I -B testing/p04_aggregate_test.py -v
"""

import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("p04_aggregate", os.path.join(HERE, "p04_aggregate.py"))
agg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agg)
d2 = agg.d2

CONTROL = os.path.join(HERE, "d002", "tests", "fixtures", "p04_schema2_control.tar.gz")
ROOT_LINE = "root_commit=0000000000000000000000000000000000000000"
CAND_D2 = ["ord_candidate", "asan_candidate", "seam_asan_candidate"]
BASE_D2 = ["ord_baseline", "asan_baseline", "seam_asan_baseline"]

TEMPLATE = {}


def setUpModule():
    """Extract the control run once and judge it with the real judge (the template)."""
    root = tempfile.mkdtemp(prefix="p04-agg-template-")
    TEMPLATE["root"] = root
    out = os.path.join(root, "out")
    os.makedirs(out)
    with tarfile.open(CONTROL, "r:gz") as tf:
        for m in tf.getmembers():
            if not m.isfile() or os.path.isabs(m.name) or ".." in m.name.split("/"):
                raise RuntimeError("unsafe control member %r" % m.name)
        tf.extractall(out, members=[m for m in tf.getmembers() if m.isfile()])
    for v in CAND_D2 + BASE_D2:
        summary = d2.judge_variant(os.path.join(out, "d002", "run"), v)
        d2.write_json_atomic(os.path.join(out, "d002", "run", v, "JUDGE_%s.json" % v), summary)


def tearDownModule():
    shutil.rmtree(TEMPLATE["root"], True)


def write_text(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def read_json(path):
    return json.loads(read_text(path))


def write_json(path, obj):
    write_text(path, json.dumps(obj))


class ControlTests(unittest.TestCase):
    """Each test starts from a fresh copy of the real control with a complete, true manifest."""

    def setUp(self):
        self.work = tempfile.mkdtemp(prefix="p04-agg-")
        self.addCleanup(shutil.rmtree, self.work, True)
        self.out = os.path.join(self.work, "out")
        shutil.copytree(os.path.join(TEMPLATE["root"], "out"), self.out)
        self.rc = {}
        self.extra_lines = []
        self.write_steps()
        self.write_artifacts()

    # --------------------------------------------------------------- writers
    def default_rc(self, name):
        if name in ("d001_frozen_baseline", "d001_ext_baseline"):
            return 1
        if name.startswith("d002_judge_") and name[len("d002_judge_"):] in BASE_D2:
            return 1
        return 0

    def write_steps(self):
        lines = [ROOT_LINE]
        for name in agg.expected_steps():
            lines.append("%s rc=%d" % (name, self.rc.get(name, self.default_rc(name))))
        lines += self.extra_lines
        write_text(os.path.join(self.out, "STEPS.txt"), "\n".join(lines) + "\n")

    def write_artifacts(self):
        """Real files with real hashes, one per label, in the work directory."""
        adir = os.path.join(self.work, "artifacts")
        records = []
        for label in agg.ARTIFACT_LABELS:
            path = os.path.join(adir, label)
            write_text(path, "artifact " + label + "\n")
            records.append((agg.sha256_file(path), label, path))
        self.artifacts = records
        self.write_manifest([("%s\t%s\t%s" % r) for r in records])

    def write_manifest(self, lines):
        write_text(os.path.join(self.out, "ARTIFACTS.sha256"), "\n".join(lines) + "\n")

    def manifest_lines(self):
        return read_text(os.path.join(self.out, "ARTIFACTS.sha256")).splitlines()

    def judge_path(self, v):
        return os.path.join(self.out, "d002", "run", v, "JUDGE_%s.json" % v)

    def rejudge(self, v):
        """What the judge CLI does: judge the saved evidence and write the judgement file."""
        d2.write_json_atomic(self.judge_path(v), d2.judge_variant(os.path.join(self.out, "d002", "run"), v))

    def run_path(self, v, *parts):
        return os.path.join(self.out, "d002", "run", v, *parts)

    def edit_json(self, path, fn):
        obj = read_json(path)
        fn(obj)
        write_json(path, obj)

    def aggregate(self):
        return agg.aggregate(self.out)

    def step(self, result, name):
        for r in result["steps"]:
            if r["step"] == name:
                return r
        self.fail("step %s not in result" % name)


class PassingTests(ControlTests):
    def test_real_control_passes(self):
        r = self.aggregate()
        self.assertEqual(r["overall"], "PASS", r["problems"])
        self.assertEqual(r["unexpected"], [])
        self.assertEqual(self.step(r, "d002_judge_ord_baseline")["classification"], "expected_defect")
        self.assertEqual(self.step(r, "d002_judge_ord_candidate")["classification"], "ok")
        self.assertEqual(self.step(r, "d002_judge_seam_asan_candidate")["reason"], "accepted 58/58")
        self.assertEqual(self.step(r, "d001_ext_baseline")["classification"], "expected_defect")
        self.assertEqual(self.step(r, "d001_ext_candidate")["classification"], "ok")
        self.assertEqual(self.step(r, "d002_positives")["classification"], "ok")
        self.assertEqual(self.step(r, "ARTIFACTS.sha256")["classification"], "ok")

    def test_raw_rc_is_preserved_in_the_record(self):
        self.rc["d002_judge_ord_baseline"] = 1
        self.assertEqual(self.step(self.aggregate(), "d002_judge_ord_baseline")["rc"], 1)


class CandidateFailureTests(ControlTests):
    def test_candidate_build_failure_fails_the_run(self):
        self.rc["build_candidate_lib"] = 2
        self.write_steps()
        r = self.aggregate()
        self.assertEqual(r["overall"], "FAIL")
        self.assertEqual(self.step(r, "build_candidate_lib")["rc"], 2)
        self.assertEqual(self.step(r, "build_candidate_lib")["classification"], "unexpected")

    def test_regression_and_error20_failures_fail_the_run(self):
        for name in ("lua_regression", "error20"):
            with self.subTest(step=name):
                self.rc[name] = 1
                self.write_steps()
                self.assertEqual(self.aggregate()["overall"], "FAIL")
                self.rc.pop(name)
                self.write_steps()

    def test_candidate_judge_rc1_fails_the_run(self):
        self.rc["d002_judge_ord_candidate"] = 1
        self.write_steps()
        r = self.aggregate()
        self.assertEqual(self.step(r, "d002_judge_ord_candidate")["classification"], "unexpected")
        self.assertEqual(r["overall"], "FAIL")

    def test_candidate_d001_failure_fails_the_run(self):
        path = os.path.join(self.out, "d001", "frozen-candidate", "SUMMARY_candidate.json")
        self.edit_json(path, lambda o: o["rows"][0].update({"pass": False}))
        r = self.aggregate()
        self.assertEqual(self.step(r, "d001_frozen_candidate")["classification"], "unexpected")
        self.assertEqual(r["overall"], "FAIL")

    def test_candidate_d001_summary_from_baseline_tree_fails(self):
        self.edit_json(os.path.join(self.out, "d001", "ext-candidate", "SUMMARY_candidate.json"),
                       lambda o: o.update(s4_dir="/x/baseline-src"))
        self.assertEqual(self.step(self.aggregate(), "d001_ext_candidate")["classification"], "unexpected")


class DefectSignatureTests(ControlTests):
    """G1: a baseline counts as reproducing the defect only through raw, complete evidence."""

    def test_missing_stderr_of_a_must_fail_case_fails_even_when_rejudged(self):
        os.remove(self.run_path("ord_baseline", "outs", "H-01.stderr"))
        self.rejudge("ord_baseline")
        s = self.step(self.aggregate(), "d002_judge_ord_baseline")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("signature not met", s["reason"])
        self.assertIn("H-01", s["reason"])

    def test_recorded_signature_claim_is_not_trusted(self):
        # The evidence is damaged but the judgement file claims the signature is met.
        os.remove(self.run_path("ord_baseline", "outs", "H-01.stderr"))
        def forge(o):
            o["signature"]["ok"] = True
            o["signature"]["not_failing"] = []
            o["signature"]["damaged"] = []
            o["integrity_failures"] = []
            o["integrity_kinds"] = {}
        self.edit_json(self.judge_path("ord_baseline"), forge)
        s = self.step(self.aggregate(), "d002_judge_ord_baseline")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("disagrees with its raw evidence", s["reason"])

    def test_damaged_may_fail_case_fails_the_signature(self):
        os.remove(self.run_path("asan_baseline", "outs", "A-37.stderr"))
        self.rejudge("asan_baseline")
        s = self.step(self.aggregate(), "d002_judge_asan_baseline")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("A-37", s["reason"])

    def test_damaged_control_fails_the_signature(self):
        os.remove(self.run_path("ord_baseline", "outs", "A-01.out"))
        self.rejudge("ord_baseline")
        s = self.step(self.aggregate(), "d002_judge_ord_baseline")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("A-01", s["reason"])

    def test_driver_error_in_a_verdict_case_is_not_the_defect(self):
        write_text(self.run_path("ord_baseline", "outs", "H-04.out"),
                   "case_id H-04\nerror cannot_open_matrix_file\ndriver_rc 3\n")
        self.rejudge("ord_baseline")
        s = self.step(self.aggregate(), "d002_judge_ord_baseline")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("H-04", s["reason"])

    def test_sanitizer_mechanism_is_still_a_defect(self):
        self.assertEqual(self.step(self.aggregate(), "d002_judge_asan_baseline")["classification"],
                         "expected_defect")

    def test_baseline_judge_rc0_means_defect_not_reproduced(self):
        self.rc["d002_judge_ord_baseline"] = 0
        self.write_steps()
        self.assertEqual(self.step(self.aggregate(), "d002_judge_ord_baseline")["classification"],
                         "unexpected")

    def test_baseline_judge_crash_rc_is_unexpected(self):
        self.rc["d002_judge_seam_asan_baseline"] = -11
        self.write_steps()
        s = self.step(self.aggregate(), "d002_judge_seam_asan_baseline")
        self.assertEqual((s["rc"], s["classification"]), (-11, "unexpected"))

    def test_baseline_integrity_failure_outside_signature_fails(self):
        write_text(self.run_path("ord_baseline", "outs", "A-01.stdout"), "printed\n")
        self.rejudge("ord_baseline")
        s = self.step(self.aggregate(), "d002_judge_ord_baseline")
        self.assertEqual(s["classification"], "unexpected")

    def test_d001_frozen_baseline_wrong_failures_fails(self):
        path = os.path.join(self.out, "d001", "frozen-baseline", "SUMMARY_baseline.json")
        self.edit_json(path, lambda o: o["rows"][0].update({"pass": False}))
        r = self.aggregate()
        self.assertIn("outside the defect set", self.step(r, "d001_frozen_baseline")["reason"])
        self.assertEqual(r["overall"], "FAIL")


def set_rc(index, cid, rc):
    for row in index["cases"]:
        if row["case_id"] == cid:
            row["rc"] = rc


class AbnormalExitTests(ControlTests):
    """G1 (round 3): an abnormal exit is the defect only when it is a registered mechanism, as in
    testing/d002.  A timeout, an unregistered status, an invalid rc type, or a crash record that
    contradicts its case must make the baseline step unexpected, through the raw evidence."""

    def baseline_step(self):
        self.rejudge("ord_baseline")
        return self.step(self.aggregate(), "d002_judge_ord_baseline")

    def test_timeout_on_a_must_fail_case_is_unexpected(self):
        self.edit_json(self.run_path("ord_baseline", "RUN_INDEX.json"),
                       lambda o: set_rc(o, "H-01", "timeout"))
        s = self.baseline_step()
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("H-01", s["reason"])
        self.assertIn("signature not met", s["reason"])

    def test_unregistered_exit_status_on_a_must_fail_case_is_unexpected(self):
        self.edit_json(self.run_path("ord_baseline", "RUN_INDEX.json"),
                       lambda o: set_rc(o, "H-01", 127))
        s = self.baseline_step()
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("H-01", s["reason"])

    def test_invalid_rc_type_on_a_must_fail_case_is_unexpected(self):
        for bad in (None, True):
            with self.subTest(rc=bad):
                self.edit_json(self.run_path("ord_baseline", "RUN_INDEX.json"),
                               lambda o, bad=bad: set_rc(o, "H-01", bad))
                s = self.baseline_step()
                self.assertEqual(s["classification"], "unexpected")
                self.assertIn("H-01", s["reason"])

    def test_crash_record_with_wrong_identity_is_unexpected(self):
        write_text(self.run_path("ord_baseline", "outs", "A-17.out"), "case_id WRONG\n")
        s = self.baseline_step()
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("A-17", s["reason"])

    def test_crash_without_its_registered_diagnostic_is_unexpected(self):
        write_text(self.run_path("ord_baseline", "outs", "A-17.stderr"), "")
        s = self.baseline_step()
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("A-17", s["reason"])

    def test_registered_crash_control_still_reproduces_the_defect(self):
        s = self.baseline_step()
        self.assertEqual(s["classification"], "expected_defect", s)


class CandidateEvidenceTests(ControlTests):
    """G2: the API record may not carry the helper buffer; the candidate is then not accepted."""

    def test_helper_buffer_in_an_api_record_fails_the_candidate(self):
        path = self.run_path("ord_candidate", "outs", "A-01.out")
        text = read_text(path).replace("driver_rc 0\n", "v_flat 0 12345 6789\ndriver_rc 0\n")
        write_text(path, text)
        self.rejudge("ord_candidate")
        s = self.step(self.aggregate(), "d002_judge_ord_candidate")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("A-01", s["reason"])

    def test_schema_downgrade_of_a_candidate_fails(self):
        idx_path = self.run_path("ord_candidate", "RUN_INDEX.json")
        self.edit_json(idx_path, lambda o: o.update(schema=1))
        for name in os.listdir(self.run_path("ord_candidate", "outs")):
            if name.endswith(".stdout"):
                os.remove(self.run_path("ord_candidate", "outs", name))
        self.rejudge("ord_candidate")
        s = self.step(self.aggregate(), "d002_judge_ord_candidate")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("legacy schema 1", s["reason"])

    def test_judgement_file_claiming_acceptance_of_a_failing_run_fails(self):
        path = self.run_path("ord_candidate", "outs", "H-04.out")
        write_text(path, "case_id H-04\nerror x\ndriver_rc 3\n")
        self.edit_json(self.judge_path("ord_candidate"), lambda o: o.update(accepted=True))
        s = self.step(self.aggregate(), "d002_judge_ord_candidate")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("disagrees with its raw evidence", s["reason"])

    def test_judgement_from_an_older_judge_is_rejected(self):
        self.edit_json(self.judge_path("ord_candidate"), lambda o: o.pop("integrity_kinds"))
        s = self.step(self.aggregate(), "d002_judge_ord_candidate")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("older judge", s["reason"])

    def test_missing_judgement_file_fails(self):
        os.remove(self.judge_path("asan_baseline"))
        s = self.step(self.aggregate(), "d002_judge_asan_baseline")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("cannot read", s["reason"])

    def test_judgement_file_of_the_wrong_type_fails_without_traceback(self):
        write_text(self.judge_path("asan_baseline"), "[1, 2]")
        s = self.step(self.aggregate(), "d002_judge_asan_baseline")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("not an object", s["reason"])

    def test_truncated_judgement_file_fails_without_traceback(self):
        write_text(self.judge_path("asan_baseline"), "{\"variant\": ")
        s = self.step(self.aggregate(), "d002_judge_asan_baseline")
        self.assertEqual(s["classification"], "unexpected")


class D001SetTests(ControlTests):
    """G3: the D001 summaries must be the complete, exact case set with the right identities."""

    def frozen(self, label):
        return os.path.join(self.out, "d001", "frozen-%s" % label, "SUMMARY_%s.json" % label)

    def ext(self, label):
        return os.path.join(self.out, "d001", "ext-%s" % label, "SUMMARY_%s.json" % label)

    def test_duplicate_row_replacing_an_expected_case_fails(self):
        def dup(o):
            o["rows"][1] = dict(o["rows"][0])
        self.edit_json(self.frozen("candidate"), dup)
        s = self.step(self.aggregate(), "d001_frozen_candidate")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("duplicate case key", s["reason"])

    def test_unknown_case_key_fails(self):
        self.edit_json(self.frozen("candidate"), lambda o: o["rows"][0].update(case_key="N7|A_SCALAR|r1"))
        s = self.step(self.aggregate(), "d001_frozen_candidate")
        self.assertIn("unknown case key 'N7|A_SCALAR|r1'", s["reason"])

    def test_identity_mismatch_fails(self):
        self.edit_json(self.frozen("candidate"), lambda o: o["rows"][2].update(repeat=2))
        s = self.step(self.aggregate(), "d001_frozen_candidate")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("identity", s["reason"])

    def test_missing_case_row_fails(self):
        self.edit_json(self.frozen("candidate"), lambda o: o.update(rows=o["rows"][:-1]))
        s = self.step(self.aggregate(), "d001_frozen_candidate")
        self.assertEqual(s["classification"], "unexpected")

    def test_extension_candidate_with_duplicate_row_fails(self):
        def dup(o):
            o["rows"][5] = dict(o["rows"][4])
        self.edit_json(self.ext("candidate"), dup)
        self.assertIn("duplicate case key", self.step(self.aggregate(), "d001_ext_candidate")["reason"])

    def test_extension_baseline_missing_one_defect_row_fails(self):
        def drop_defect(o):
            for r in o["rows"]:
                if r["N"] == 9 and r["rep"] == "B" and r["pass"] is False:
                    r["pass"] = True
                    return
        self.edit_json(self.ext("baseline"), drop_defect)
        s = self.step(self.aggregate(), "d001_ext_baseline")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("defect set not reproduced", s["reason"])

    def test_extension_baseline_control_failure_fails(self):
        def fail_control(o):
            for r in o["rows"]:
                if r["rep"] == "A":
                    r["pass"] = False
                    return
        self.edit_json(self.ext("baseline"), fail_control)
        s = self.step(self.aggregate(), "d001_ext_baseline")
        self.assertIn("outside the defect set", s["reason"])
        self.assertEqual(s["classification"], "unexpected")

    def test_extension_baseline_one_row_is_not_a_signature(self):
        # A baseline that fails at least one N9 B/C row is not enough; the whole set must match.
        def only_one(o):
            for r in o["rows"]:
                r["pass"] = True
            o["rows"][0]["pass"] = False
        self.edit_json(self.ext("baseline"), only_one)
        self.assertEqual(self.step(self.aggregate(), "d001_ext_baseline")["classification"], "unexpected")


class BaselineBoundaryTests(ControlTests):
    """Round-4 boundary counterexamples through the whole aggregate, on the real control.

    Each damaged baseline record is re-judged and the baseline step must then be unexpected and
    the run FAIL.  The real partial crash record of the same case stays a registered defect.
    """

    def judged(self, variant, cid_text_edit):
        cid_text_edit()
        self.rejudge(variant)
        r = self.aggregate()
        return r, self.step(r, "d002_judge_" + variant)

    def test_real_partial_crash_record_stays_the_registered_defect(self):
        def edit():
            write_text(self.run_path("ord_baseline", "outs", "A-17.out"), "case_id A-17\nmat")
        r, step = self.judged("ord_baseline", edit)
        self.assertEqual((step["classification"], r["overall"]), ("expected_defect", "PASS"))

    def test_wrong_identity_without_a_newline_fails_the_run(self):
        def edit():
            write_text(self.run_path("ord_baseline", "outs", "A-17.out"), "case_id WRONG")
        r, step = self.judged("ord_baseline", edit)
        self.assertEqual((step["classification"], r["overall"]), ("unexpected", "FAIL"))

    def test_wrong_seam_identity_in_a_crash_record_fails_the_run(self):
        def edit():
            write_text(self.run_path("seam_asan_baseline", "outs", "H-01.out"), "seam_enabled 0\n")
        r, step = self.judged("seam_asan_baseline", edit)
        self.assertEqual((step["classification"], r["overall"]), ("unexpected", "FAIL"))

    def test_sigsegv_with_only_a_driver_rc_record_fails_the_run(self):
        def edit():
            self.rc_index("ord_baseline", "H-01", -11)
            write_text(self.run_path("ord_baseline", "outs", "H-01.out"), "driver_rc 0\n")
            write_text(self.run_path("ord_baseline", "outs", "H-01.stderr"), "")
        r, step = self.judged("ord_baseline", edit)
        self.assertEqual((step["classification"], r["overall"]), ("unexpected", "FAIL"))

    def test_rc0_sanitizer_text_that_is_not_a_registered_report_fails_the_run(self):
        def edit():
            write_text(self.run_path("asan_baseline", "outs", "A-38.stderr"),
                       "AddressSanitizer: bananas\n")
        r, step = self.judged("asan_baseline", edit)
        self.assertEqual((step["classification"], r["overall"]), ("unexpected", "FAIL"))

    def test_a07_passing_in_the_seam_variant_fails_the_run(self):
        # The A-07 correction is asan_baseline only: the seam baseline still needs its defect.
        def edit():
            path = self.run_path("seam_asan_baseline", "outs", "A-07.out")
            write_text(path, re.sub(r"^info \d+$", "info 0", read_text(path), flags=re.M))
        r, step = self.judged("seam_asan_baseline", edit)
        self.assertEqual((step["classification"], r["overall"]), ("unexpected", "FAIL"))

    def rc_index(self, variant, cid, value):
        path = self.run_path(variant, "RUN_INDEX.json")
        data = read_json(path)
        next(row for row in data["cases"] if row["case_id"] == cid)["rc"] = value
        write_json(path, data)


class PositiveControlTests(ControlTests):
    """G4: the three sanitizer controls must each be present once and show their signature."""

    def positives(self):
        return os.path.join(self.out, "d002", "positives", "POSITIVES.json")

    def test_only_the_first_control_fails(self):
        self.edit_json(self.positives(), lambda o: o.__setitem__(slice(1, None), []))
        s = self.step(self.aggregate(), "d002_positives")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("control pos_ubsan missing", s["reason"])

    def test_duplicate_control_fails(self):
        self.edit_json(self.positives(), lambda o: o.append(dict(o[0])))
        self.assertIn("duplicate control", self.step(self.aggregate(), "d002_positives")["reason"])

    def test_unknown_control_fails(self):
        self.edit_json(self.positives(), lambda o: o.append({"control": "pos_msan", "pass": True}))
        self.assertIn("unknown control", self.step(self.aggregate(), "d002_positives")["reason"])

    def test_control_absent_from_its_own_stderr_fails(self):
        write_text(os.path.join(self.out, "d002", "positives", "pos_asan.stderr"), "clean run\n")
        s = self.step(self.aggregate(), "d002_positives")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("absent from its own stderr", s["reason"])

    def test_control_recorded_as_not_passing_fails(self):
        self.edit_json(self.positives(), lambda o: o[0].update({"pass": False}))
        self.assertEqual(self.step(self.aggregate(), "d002_positives")["classification"], "unexpected")

    def test_asan_control_that_did_not_exit_abnormally_fails(self):
        self.edit_json(self.positives(), lambda o: o[0].update({"exit": 0}))
        self.assertIn("did not exit abnormally", self.step(self.aggregate(), "d002_positives")["reason"])

    def set_exit(self, control, value, missing=False):
        def edit(o):
            row = next(r for r in o if r["control"] == control)
            if missing:
                del row["exit"]
            else:
                row["exit"] = value
        self.edit_json(self.positives(), edit)
        return self.step(self.aggregate(), "d002_positives")

    def test_ubsan_control_null_exit_fails(self):
        s = self.set_exit("pos_ubsan", None)
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("pos_ubsan exit is not an integer status: None", s["reason"])

    def test_ubsan_control_missing_exit_fails(self):
        s = self.set_exit("pos_ubsan", None, missing=True)
        self.assertIn("pos_ubsan exit is not an integer status: None", s["reason"])

    def test_ubsan_control_boolean_exit_fails(self):
        s = self.set_exit("pos_ubsan", False)
        self.assertIn("pos_ubsan exit is not an integer status: False", s["reason"])

    def test_ubsan_control_nonzero_exit_fails_for_its_recoverable_build(self):
        s = self.set_exit("pos_ubsan", 1)
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("pos_ubsan exited 1", s["reason"])

    def test_asan_control_null_exit_fails(self):
        s = self.set_exit("pos_asan_ubsan", None)
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("pos_asan_ubsan exit is not an integer status: None", s["reason"])


class ArtifactManifestTests(ControlTests):
    """G5: the manifest must record every artifact, and each recorded file must be present and
    hash to the recorded value."""

    def test_empty_manifest_fails(self):
        self.write_manifest([])
        r = self.aggregate()
        self.assertEqual(self.step(r, "ARTIFACTS.sha256")["classification"], "unexpected")
        self.assertEqual(r["overall"], "FAIL")

    def test_comment_only_manifest_fails(self):
        self.write_manifest(["# artifacts"])
        self.assertEqual(self.step(self.aggregate(), "ARTIFACTS.sha256")["classification"], "unexpected")

    def test_missing_label_fails(self):
        self.write_manifest(self.manifest_lines()[1:])
        s = self.step(self.aggregate(), "ARTIFACTS.sha256")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("no record for 1 artifact", s["reason"])

    def test_duplicate_label_fails(self):
        self.write_manifest(self.manifest_lines() + [self.manifest_lines()[0]])
        self.assertIn("recorded twice", self.step(self.aggregate(), "ARTIFACTS.sha256")["reason"])

    def test_hash_mismatch_fails(self):
        path = os.path.join(self.work, "artifacts", "candidate-lib")
        write_text(path, "replaced after the manifest was written\n")
        s = self.step(self.aggregate(), "ARTIFACTS.sha256")
        self.assertEqual(s["classification"], "unexpected")
        self.assertIn("candidate-lib hash differs", s["reason"])

    def test_recorded_missing_artifact_fails(self):
        lines = self.manifest_lines()
        lines[0] = "# MISSING\t%s" % "\t".join(lines[0].split("\t")[1:])
        self.write_manifest(lines)
        self.assertIn("not present", self.step(self.aggregate(), "ARTIFACTS.sha256")["reason"])

    def test_absent_file_fails(self):
        os.remove(os.path.join(self.work, "artifacts", "seam-cli"))
        self.assertIn("seam-cli absent", self.step(self.aggregate(), "ARTIFACTS.sha256")["reason"])

    def test_malformed_record_fails(self):
        self.write_manifest(self.manifest_lines() + ["not-a-hash candidate-cli /x"])
        self.assertIn("is not a SHA256 record", self.step(self.aggregate(), "ARTIFACTS.sha256")["reason"])

    def test_unknown_label_fails(self):
        self.write_manifest(self.manifest_lines() + ["%s\tsurprise\t%s" % (self.artifacts[0][0], self.artifacts[0][2])])
        self.assertIn("unknown artifact label surprise", self.step(self.aggregate(), "ARTIFACTS.sha256")["reason"])

    def test_complete_true_manifest_is_accepted(self):
        self.assertEqual(self.step(self.aggregate(), "ARTIFACTS.sha256")["classification"], "ok")


class StructureTests(ControlTests):
    def test_missing_step_fails(self):
        lines = [l for l in read_text(os.path.join(self.out, "STEPS.txt")).splitlines()
                 if not l.startswith("lua_regression ")]
        write_text(os.path.join(self.out, "STEPS.txt"), "\n".join(lines) + "\n")
        r = self.aggregate()
        self.assertIn("missing step lua_regression", r["problems"])
        self.assertEqual(r["overall"], "FAIL")

    def test_duplicated_step_fails(self):
        self.extra_lines = ["error20 rc=0"]
        self.write_steps()
        r = self.aggregate()
        self.assertIn("duplicated step error20", r["problems"])
        self.assertEqual(r["overall"], "FAIL")

    def test_unknown_step_fails(self):
        self.extra_lines = ["surprise_step rc=0"]
        self.write_steps()
        self.assertIn("unknown step surprise_step", self.aggregate()["problems"])

    def test_missing_artifact_manifest_fails(self):
        os.remove(os.path.join(self.out, "ARTIFACTS.sha256"))
        self.assertIn("artifact manifest missing", self.aggregate()["problems"])

    def test_malformed_steps_line_is_an_input_error(self):
        with open(os.path.join(self.out, "STEPS.txt"), "a") as fh:
            fh.write("export_baseline rc=zero\n")
        with self.assertRaises(agg.AggregateInputError):
            self.aggregate()

    def test_cli_exit_codes(self):
        quiet = io.StringIO()
        with contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
            self.assertEqual(agg.main(["aggregate.py", self.out]), 0)
            self.rc["build_seam_lib"] = 3
            self.write_steps()
            self.assertEqual(agg.main(["aggregate.py", self.out]), 1)
            self.assertEqual(agg.main(["aggregate.py"]), 2)
            os.remove(os.path.join(self.out, "STEPS.txt"))
            self.assertEqual(agg.main(["aggregate.py", self.out]), 2)


if __name__ == "__main__":
    unittest.main()
