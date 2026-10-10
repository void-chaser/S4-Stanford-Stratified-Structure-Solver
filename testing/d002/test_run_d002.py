#!/usr/bin/env python3
"""Negative and positive tests for the D002 judge (run_d002.py).

A complete, valid saved run (schema 2, the final 2026-10-09 pipeline run, extracted from
testing/d002/tests/fixtures/p04_schema2_control.tar.gz) is copied into a temporary
directory.  Each negative test changes exactly one condition of that run and checks that
the judge rejects it for the stated reason.  The positive tests show that the unchanged
run is accepted.  Legacy schema-1 runs are tested separately, with the explicit request.

Run:  python3 -I -B testing/d002/test_run_d002.py -v
"""

import copy
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import run_d002 as d002  # noqa: E402

FIXTURES = os.path.join(HERE, "tests", "fixtures")
CONTROL_ARCHIVE = os.path.join(FIXTURES, "p04_schema2_control.tar.gz")
ORD = "ord_candidate"
SEAM = "seam_asan_candidate"
PLAN = d002.load_plan()
MATS = d002.load_matrices()
ALL_IDS = [c["case_id"] for c in PLAN["cases"]]


def read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


class FixtureTest(unittest.TestCase):
    """Extracts one variant of the schema-2 control run into a fresh temporary tree.

    The control run (tests/fixtures/p04_schema2_control.tar.gz) is real saved evidence of the
    final 2026-10-09 pipeline run: RUN_INDEX (schema 2, scope full) plus the .out, .stderr and
    .stdout record of every case.  Subclasses change the variant; LegacyRunTests reads the
    schema-1 archives instead.
    """

    variant = ORD
    legacy = False

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="d002-judge-")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.vdir = os.path.join(self.tmp, self.variant)
        os.makedirs(os.path.join(self.vdir, "outs"))
        if self.legacy:
            archive = os.path.join(FIXTURES, "%s_legacy_run.tar.gz" % self.variant)
            prefix = ""
        else:
            archive = CONTROL_ARCHIVE
            prefix = "d002/run/%s/" % self.variant
        with tarfile.open(archive, "r:gz") as tf:
            # Only regular members of the expected names are extracted.
            members = []
            for m in tf.getmembers():
                if not m.isfile() or not m.name.startswith(prefix):
                    continue
                rel = m.name[len(prefix):]
                if rel == "RUN_INDEX.json" or rel.startswith("outs/"):
                    if os.path.isabs(m.name) or ".." in m.name.split("/"):
                        raise RuntimeError("unsafe member %r" % m.name)
                    members.append((m, rel))
            for m, rel in members:
                with tf.extractfile(m) as src, open(os.path.join(self.vdir, rel), "wb") as out:
                    out.write(src.read())

    # helpers -------------------------------------------------------------
    def index(self):
        with open(os.path.join(self.vdir, "RUN_INDEX.json"), encoding="utf-8") as fh:
            return json.load(fh)

    def save_index(self, idx):
        write(os.path.join(self.vdir, "RUN_INDEX.json"), json.dumps(idx))

    def out_path(self, cid, kind="out"):
        return os.path.join(self.vdir, "outs", "%s.%s" % (cid, kind))

    def judge(self):
        return d002.judge_variant(self.tmp, self.variant, PLAN, MATS, allow_legacy=self.legacy)

    def case(self, summary, cid):
        for r in summary["results"]:
            if r["case_id"] == cid:
                return r
        self.fail("case %s not in results" % cid)

    def assert_run_rejected(self, summary, fragment):
        self.assertEqual(summary["integrity"], "fatal", summary)
        self.assertIn(fragment, summary["fatal"])
        self.assertFalse(summary["accepted"])

    def assert_case_rejected(self, summary, cid, fragment):
        r = self.case(summary, cid)
        self.assertFalse(r["pass"], r)
        self.assertIn(fragment, r["detail"] + " " + r["integrity"])
        self.assertFalse(summary["accepted"])
        self.assertFalse(summary["all_judged_pass"])

    def assert_not_the_defect(self, s, cid, kind, fragment):
        """A damaged or unregistered record of a signature case: the defect is not shown."""
        self.assertEqual(self.case(s, cid)["integrity_kind"], kind)
        self.assertIn(fragment, self.case(s, cid)["integrity"])
        self.assertIn(cid, s["signature"]["not_failing"])
        self.assertFalse(s["signature"]["ok"])
        self.assertFalse(s["accepted"])


class PositiveTests(FixtureTest):
    def test_complete_valid_run_is_accepted(self):
        s = self.judge()
        self.assertEqual(s["integrity"], "ok", s.get("fatal"))
        self.assertEqual(s["cases_judged"], 53)
        self.assertEqual(s["cases_pass"], 53)
        self.assertEqual(s["cases_recorded_probe"], 1)
        self.assertEqual(s["cases_not_applicable"], 5)
        self.assertTrue(s["complete_run"])
        self.assertTrue(s["accepted"])
        self.assertEqual(s["integrity_failures"], [])

    def test_probe_failure_is_recorded_not_judged(self):
        s = self.judge()
        probe = self.case(s, "A-10r")
        self.assertEqual(probe["status"], "recorded")
        self.assertIsNone(probe["pass"])
        self.assertIn("rc=-11", probe["detail"])

    def test_subset_run_is_never_complete(self):
        idx = self.index()
        keep = ["A-01", "A-02"]
        idx["schema"] = 2
        idx["scope"] = "subset"
        idx["expected_case_ids"] = keep
        idx["cases"] = [c for c in idx["cases"] if c["case_id"] in keep]
        self.save_index(idx)
        for cid in ALL_IDS:
            if cid not in keep:
                os.remove(self.out_path(cid))
                os.remove(self.out_path(cid, "stderr"))
        write(self.out_path("A-01", "stdout"), "")
        write(self.out_path("A-02", "stdout"), "")
        s = self.judge()
        self.assertEqual(s["integrity"], "ok", s.get("fatal"))
        self.assertTrue(s["all_judged_pass"])
        self.assertFalse(s["complete_run"])
        self.assertFalse(s["accepted"])

    def test_subset_judges_only_the_expected_ids(self):
        idx = self.index()
        idx["schema"] = 2
        idx["scope"] = "subset"
        idx["expected_case_ids"] = ["A-02"]
        idx["cases"] = [c for c in idx["cases"] if c["case_id"] == "A-02"]
        self.save_index(idx)
        s = self.judge()
        self.assertEqual([r["case_id"] for r in s["results"]], ["A-02"])


class RunIndexTests(FixtureTest):
    def test_empty_case_list_is_refused(self):
        idx = self.index()
        idx["cases"] = []
        self.save_index(idx)
        self.assert_run_rejected(self.judge(), "no case entries")

    def test_missing_case_is_refused(self):
        idx = self.index()
        idx["cases"] = [c for c in idx["cases"] if c["case_id"] != "A-05"]
        self.save_index(idx)
        self.assert_run_rejected(self.judge(), "missing RUN_INDEX entries")

    def test_duplicate_case_is_refused_not_overwritten(self):
        idx = self.index()
        dup = [c for c in idx["cases"] if c["case_id"] == "A-05"][0]
        idx["cases"].append(dict(dup, rc=-6))
        self.save_index(idx)
        self.assert_run_rejected(self.judge(), "duplicate RUN_INDEX entry A-05")

    def test_unknown_case_is_refused(self):
        idx = self.index()
        idx["cases"].append({"case_id": "Z-99", "rc": 0})
        self.save_index(idx)
        self.assert_run_rejected(self.judge(), "unknown case_id Z-99")

    def test_variant_mismatch_is_refused(self):
        idx = self.index()
        idx["variant"] = "asan_candidate"
        self.save_index(idx)
        self.assert_run_rejected(self.judge(), "does not match")

    def test_malformed_entry_is_refused(self):
        idx = self.index()
        idx["cases"][3] = {"case_id": "A-04"}
        self.save_index(idx)
        self.assert_run_rejected(self.judge(), "malformed RUN_INDEX entry")

    def test_unreadable_index_is_refused(self):
        write(os.path.join(self.vdir, "RUN_INDEX.json"), "{not json")
        self.assert_run_rejected(self.judge(), "RUN_INDEX unreadable")

    def test_unknown_schema_is_refused(self):
        idx = self.index()
        idx["schema"] = 99
        self.save_index(idx)
        self.assert_run_rejected(self.judge(), "RUN_INDEX schema 99 is not accepted")

    def test_schema_downgrade_is_refused_without_an_explicit_request(self):
        # A formal run cannot pass by declaring the legacy schema and dropping stdout records.
        idx = self.index()
        idx["schema"] = 1
        self.save_index(idx)
        for cid in ALL_IDS:
            os.remove(self.out_path(cid, "stdout"))
        self.assert_run_rejected(self.judge(), "legacy schema 1 needs an explicit re-judging request")

    def test_missing_schema_field_is_treated_as_legacy_and_refused(self):
        # Only the legacy runs lack the field, so a formal run without it is not accepted.
        idx = self.index()
        del idx["schema"]
        self.save_index(idx)
        self.assert_run_rejected(self.judge(), "legacy schema 1 needs an explicit re-judging request")


class LegacyRunTests(FixtureTest):
    """The 2026-10-09 schema-1 runs: judged only when the caller asks for it explicitly."""

    legacy = True

    def test_legacy_run_is_refused_without_the_request(self):
        s = d002.judge_variant(self.tmp, self.variant, PLAN, MATS)
        self.assert_run_rejected(s, "legacy schema 1 needs an explicit re-judging request")

    def test_legacy_run_is_judged_when_requested(self):
        s = self.judge()
        self.assertEqual(s["integrity"], "ok", s.get("fatal"))
        self.assertEqual(s["run_schema"], 1)
        self.assertTrue(s["accepted"], s["integrity_failures"])

    def test_legacy_run_has_no_stdout_requirement(self):
        self.assertFalse(os.path.exists(self.out_path("A-04", "stdout")))
        self.assertTrue(self.judge()["accepted"])


class ProcessAndRecordTests(FixtureTest):
    def test_segfault_rc_fails_the_case(self):
        idx = self.index()
        for c in idx["cases"]:
            if c["case_id"] == "A-12":
                c["rc"] = -11
        self.save_index(idx)
        self.assert_case_rejected(self.judge(), "A-12", "abnormal exit rc=-11")

    def test_timeout_rc_fails_the_case(self):
        idx = self.index()
        for c in idx["cases"]:
            if c["case_id"] == "A-12":
                c["rc"] = "timeout"
        self.save_index(idx)
        s = self.judge()
        self.assert_case_rejected(s, "A-12", "runner failure rc='timeout'")
        self.assertEqual(self.case(s, "A-12")["integrity_kind"], "runner")

    def test_missing_stderr_fails_the_case(self):
        os.remove(self.out_path("A-04", "stderr"))
        s = self.judge()
        self.assertEqual(self.case(s, "A-04")["integrity"], "missing record")
        self.assertFalse(s["accepted"])

    def test_missing_out_fails_the_case(self):
        os.remove(self.out_path("A-04"))
        s = self.judge()
        self.assertEqual(self.case(s, "A-04")["integrity"], "missing record")
        self.assertFalse(s["accepted"])

    def test_missing_stdout_in_schema2_fails_the_case(self):
        os.remove(self.out_path("A-04", "stdout"))
        s = self.judge()
        self.assertEqual(self.case(s, "A-04")["integrity"], "missing record")
        self.assertFalse(s["accepted"])

    def test_unexpected_stdout_fails_the_case(self):
        write(self.out_path("A-04", "stdout"), "printed something\n")
        self.assert_case_rejected(self.judge(), "A-04", "unexpected stdout")

    def test_sanitizer_in_stderr_fails_the_case(self):
        write(self.out_path("A-04", "stderr"), "runtime error: signed integer overflow\n")
        self.assert_case_rejected(self.judge(), "A-04", "sanitizer report")

    def test_nonzero_info_fails_the_case(self):
        text = read(self.out_path("A-04")).replace("info 0\n", "info 1\n")
        write(self.out_path("A-04"), text)
        self.assert_case_rejected(self.judge(), "A-04", "info=1, expected 0")

    def test_wrong_identity_fails_the_case(self):
        text = read(self.out_path("A-04")).replace("case_id A-04\n", "case_id A-05\n", 1)
        write(self.out_path("A-04"), text)
        self.assert_case_rejected(self.judge(), "A-04", "case_id=A-05, expected A-04")

    def test_wrong_variant_fails_the_case(self):
        text = read(self.out_path("A-04")).replace("variant ord_candidate", "variant asan_candidate", 1)
        write(self.out_path("A-04"), text)
        self.assert_case_rejected(self.judge(), "A-04", "variant=asan_candidate")


class OutputGrammarTests(FixtureTest):
    def test_nan_real_part_is_rejected(self):
        text = read(self.out_path("A-04"))
        lines = text.split("\n")
        i = next(k for k, ln in enumerate(lines) if ln.startswith("w "))
        parts = lines[i].split(" ")
        parts[2] = "nan"
        lines[i] = " ".join(parts)
        write(self.out_path("A-04"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "A-04", "non-finite value 'nan'")

    def test_inf_imaginary_part_is_rejected(self):
        text = read(self.out_path("A-04"))
        lines = text.split("\n")
        i = next(k for k, ln in enumerate(lines) if ln.startswith("vr_flat "))
        parts = lines[i].split(" ")
        parts[3] = "inf"
        lines[i] = " ".join(parts)
        write(self.out_path("A-04"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "A-04", "non-finite value 'inf'")

    def test_nonnumeric_token_is_rejected(self):
        text = read(self.out_path("A-04")).replace("elapsed_s ", "elapsed_s zero", 1)
        write(self.out_path("A-04"), text)
        self.assert_case_rejected(self.judge(), "A-04", "malformed")

    def test_wrong_n_is_rejected(self):
        text = read(self.out_path("A-04")).replace("\nn 3\n", "\nn 2\n", 1)
        write(self.out_path("A-04"), text)
        self.assert_case_rejected(self.judge(), "A-04", "n=2, expected 3")

    def test_zero_n_is_rejected(self):
        text = read(self.out_path("A-04")).replace("\nn 3\n", "\nn 0\n", 1)
        write(self.out_path("A-04"), text)
        self.assert_case_rejected(self.judge(), "A-04", "n=0, expected 3")

    def test_duplicate_scalar_is_rejected(self):
        text = read(self.out_path("A-04")).replace("info 0\n", "info 0\ninfo 0\n", 1)
        write(self.out_path("A-04"), text)
        self.assert_case_rejected(self.judge(), "A-04", "duplicate scalar record info")

    def test_truncated_mid_record_is_rejected(self):
        text = read(self.out_path("A-04"))
        write(self.out_path("A-04"), text[: len(text) - 7])
        self.assert_case_rejected(self.judge(), "A-04", "does not end with a newline")

    def test_truncated_before_driver_rc_is_rejected(self):
        text = read(self.out_path("A-04"))
        cut = text[: text.rindex("driver_rc ")]
        write(self.out_path("A-04"), cut)
        self.assert_case_rejected(self.judge(), "A-04", "output truncated")

    def test_unknown_record_is_rejected(self):
        text = read(self.out_path("A-04")).replace("driver_rc 0\n", "bogus 1\ndriver_rc 0\n")
        write(self.out_path("A-04"), text)
        self.assert_case_rejected(self.judge(), "A-04", "unexpected record")

    def test_driver_error_is_rejected(self):
        write(self.out_path("A-04"), "case_id A-04\nerror cannot_open_matrix_file\ndriver_rc 3\n")
        self.assert_case_rejected(self.judge(), "A-04", "driver error")

    def test_wrong_scale_producer_is_rejected(self):
        text = read(self.out_path("H-09"))
        lines = text.split("\n")
        i = next(k for k, ln in enumerate(lines) if ln.startswith("scale "))
        vals = lines[i].split(" ")[1:]
        vals[0] = "0"          # position 1 is inside [ilo,ihi] for this producer output
        lines[i] = " ".join(["scale"] + vals)
        write(self.out_path("H-09"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "H-09", "not a positive scaling factor")

    def test_ilo_out_of_zgebal_range_is_rejected(self):
        text = read(self.out_path("H-09")).replace("ilo_1based ", "ilo_1based 99", 1)
        write(self.out_path("H-09"), text)
        self.assert_case_rejected(self.judge(), "H-09", "outside the zgebal range")


class IndexShapeTests(FixtureTest):
    def test_extra_vr_record_is_rejected(self):
        text = read(self.out_path("A-04"))
        extra = "vr_flat 9 0 0\n"
        write(self.out_path("A-04"), text.replace("driver_rc 0\n", extra + "driver_rc 0\n"))
        self.assert_case_rejected(self.judge(), "A-04", "out of range")

    def test_duplicate_vr_index_is_rejected(self):
        text = read(self.out_path("A-04"))
        lines = text.split("\n")
        i = next(k for k, ln in enumerate(lines) if ln.startswith("vr_flat 1 "))
        lines.insert(i, lines[i])
        write(self.out_path("A-04"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "A-04", "duplicate index 1")

    def test_missing_vr_index_is_rejected(self):
        text = read(self.out_path("A-04"))
        lines = [ln for ln in text.split("\n") if not ln.startswith("vr_flat 2 ")]
        write(self.out_path("A-04"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "A-04", "missing e.g. [2]")

    def test_missing_w_index_is_rejected(self):
        text = read(self.out_path("A-04"))
        lines = [ln for ln in text.split("\n") if not ln.startswith("w 0 ")]
        write(self.out_path("A-04"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "A-04", "missing e.g. [0]")

    def test_w_out_of_range_is_rejected(self):
        text = read(self.out_path("A-04"))
        write(self.out_path("A-04"), text.replace("\nw 2 ", "\nw 3 ", 1))
        self.assert_case_rejected(self.judge(), "A-04", "w index 3 out of range")

    def test_vr_capacity_mismatch_is_rejected(self):
        text = read(self.out_path("A-04")).replace("vr_capacity_elems 9", "vr_capacity_elems 8", 1)
        write(self.out_path("A-04"), text)
        self.assert_case_rejected(self.judge(), "A-04", "vr_capacity_elems=8")

    def test_unrequested_vl_output_is_rejected(self):
        text = read(self.out_path("A-04")).replace("driver_rc 0\n", "vl_flat 0 1 0\ndriver_rc 0\n")
        write(self.out_path("A-04"), text)
        self.assert_case_rejected(self.judge(), "A-04", "vl_flat index 0 out of range")

    def test_zero_n_case_with_stray_record_is_rejected(self):
        text = read(self.out_path("A-01")).replace("driver_rc 0\n", "w 0 1 0\ndriver_rc 0\n")
        write(self.out_path("A-01"), text)
        self.assert_case_rejected(self.judge(), "A-01", "w index 0 out of range [0,0)")

    def test_helper_buffer_in_an_api_record_is_rejected(self):
        # v_flat is the helper-only buffer; an API case must not carry any of its records.
        text = read(self.out_path("A-01")).replace("driver_rc 0\n", "v_flat 0 12345 6789\ndriver_rc 0\n")
        write(self.out_path("A-01"), text)
        self.assert_case_rejected(self.judge(), "A-01", "v_flat has 1 records, expected none in a API case")

    def test_api_buffer_in_a_helper_record_is_rejected(self):
        text = read(self.out_path("H-01")).replace("driver_rc 0\n", "w 0 1 0\ndriver_rc 0\n")
        write(self.out_path("H-01"), text)
        self.assert_case_rejected(self.judge(), "H-01", "w has 1 records, expected none in a helper case")

    def test_padding_change_is_rejected(self):
        # A-12: ldvr = 5 > n = 3; column 0 row 3 is padding and must stay 0+0j.
        text = read(self.out_path("A-12"))
        lines = text.split("\n")
        i = next(k for k, ln in enumerate(lines) if ln.startswith("vr_flat 3 "))
        lines[i] = "vr_flat 3 1 0"
        write(self.out_path("A-12"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "A-12", "padding element 3 changed")


class EigenvalueAndVectorTests(FixtureTest):
    def test_wrong_eigenvalue_is_rejected(self):
        text = read(self.out_path("A-04"))
        lines = text.split("\n")
        i = next(k for k, ln in enumerate(lines) if ln.startswith("w 0 "))
        parts = lines[i].split(" ")
        parts[2] = "7.0"
        lines[i] = " ".join(parts)
        write(self.out_path("A-04"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "A-04", "eigenvalue error")

    def test_wrong_vector_is_rejected(self):
        text = read(self.out_path("A-04"))
        lines = text.split("\n")
        i = next(k for k, ln in enumerate(lines) if ln.startswith("vr_flat 0 "))
        parts = lines[i].split(" ")
        parts[2] = "0.5"
        lines[i] = " ".join(parts)
        write(self.out_path("A-04"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "A-04", "right vectors residual")


class HelperTests(FixtureTest):
    def test_pure_imaginary_contamination_of_helper_is_rejected(self):
        # The old comparator read only the real part, so this passed there.
        text = read(self.out_path("H-01"))
        lines = []
        for ln in text.split("\n"):
            if ln.startswith("v_flat "):
                parts = ln.split(" ")
                parts[3] = str(float(parts[3]) + 1000000.0)
                ln = " ".join(parts)
            lines.append(ln)
        write(self.out_path("H-01"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "H-01", "v_flat[0]")

    def test_helper_real_value_error_is_rejected(self):
        text = read(self.out_path("H-01"))
        lines = text.split("\n")
        i = next(k for k, ln in enumerate(lines) if ln.startswith("v_flat 2 "))
        lines[i] = "v_flat 2 1500 0"
        write(self.out_path("H-01"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "H-01", "v_flat[2]")

    def test_helper_missing_index_is_rejected(self):
        text = read(self.out_path("H-01"))
        lines = [ln for ln in text.split("\n") if not ln.startswith("v_flat 4 ")]
        write(self.out_path("H-01"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "H-01", "missing e.g. [4]")

    def test_helper_padding_change_is_rejected(self):
        text = read(self.out_path("H-08"))
        lines = text.split("\n")
        i = next(k for k, ln in enumerate(lines) if ln.startswith("v_flat 3 "))
        lines[i] = "v_flat 3 0 0"
        write(self.out_path("H-08"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "H-08", "v_flat[3]")


class QueryTests(FixtureTest):
    def test_query_work0_wrong_value_is_rejected(self):
        text = read(self.out_path("A-08")).replace("work0 0 6 0", "work0 0 7 0", 1)
        write(self.out_path("A-08"), text)
        self.assert_case_rejected(self.judge(), "A-08", "work0 = (7+0j), expected exactly 2n = 6")

    def test_query_work0_imaginary_is_rejected(self):
        text = read(self.out_path("A-08")).replace("work0 0 6 0", "work0 0 6 0.5", 1)
        write(self.out_path("A-08"), text)
        self.assert_case_rejected(self.judge(), "A-08", "expected exactly 2n")

    def test_query_missing_work0_is_rejected(self):
        text = read(self.out_path("A-08"))
        lines = [ln for ln in text.split("\n") if not ln.startswith("work0 ")]
        write(self.out_path("A-08"), "\n".join(lines))
        self.assert_case_rejected(self.judge(), "A-08", "missing e.g. [0]")


class SeamTests(FixtureTest):
    variant = SEAM

    def test_seam_candidate_is_accepted(self):
        s = self.judge()
        self.assertEqual(s["integrity"], "ok", s.get("fatal"))
        self.assertEqual(s["cases_judged"], 58)
        self.assertTrue(s["accepted"], s["integrity_failures"])

    def test_forced_status_not_propagated_is_rejected(self):
        text = read(self.out_path("C-01")).replace("info 1\n", "info 0\n", 1)
        write(self.out_path("C-01"), text)
        self.assert_case_rejected(self.judge(), "C-01", "info=0 forced=1")

    def test_seam_mode_identity_is_rejected(self):
        text = read(self.out_path("C-02")).replace("seam_mode_used 1", "seam_mode_used 0", 1)
        write(self.out_path("C-02"), text)
        self.assert_case_rejected(self.judge(), "C-02", "seam_mode_used=0, expected 1")

    def test_c03_onlyvalues_real_status_is_checked(self):
        text = read(self.out_path("C-03")).replace("seam_onlyvalues_real_info 0", "seam_onlyvalues_real_info 16", 1)
        write(self.out_path("C-03"), text)
        self.assert_case_rejected(self.judge(), "C-03", "seam_onlyvalues_real_info=16")


class SeamFreeVariantTests(FixtureTest):
    def test_non_seam_variant_carries_no_seam_records(self):
        text = read(self.out_path("C-01"))
        write(self.out_path("C-01"), text.replace("seam_enabled 0\n", "seam_enabled 0\nseam_mode_used 1\n"))
        s = self.judge()
        self.assertIn("seam record seam_mode_used present in a non-seam variant",
                      self.case(s, "C-01")["integrity"])
        self.assertFalse(s["accepted"])


class BaselineSignatureTests(FixtureTest):
    """ord_baseline: the defect signature is shown by judged failures and registered mechanisms
    only.  A damaged record never reproduces the defect (a missing file is not a defect)."""

    variant = "ord_baseline"

    def test_complete_baseline_reproduces_the_defect(self):
        s = self.judge()
        self.assertEqual(s["integrity"], "ok", s.get("fatal"))
        self.assertTrue(s["complete_run"])
        self.assertTrue(s["signature"]["ok"], s["signature"])
        self.assertEqual(s["signature"]["damaged"], [])
        self.assertEqual(self.case(s, "H-01")["integrity_kind"], "exit")      # abort, rc -6
        self.assertEqual(self.case(s, "H-04")["integrity_kind"], "ok")        # verdict failure
        self.assertFalse(s["accepted"])

    def test_missing_stderr_of_a_must_fail_case_is_not_a_reproduced_defect(self):
        # The reviewed counterexample: H-01 with its stderr removed still "failed".
        os.remove(self.out_path("H-01", "stderr"))
        s = self.judge()
        self.assertEqual(s["integrity_kinds"]["H-01"], "missing")
        self.assertFalse(s["signature"]["ok"])
        self.assertIn("H-01", s["signature"]["not_failing"])
        self.assertIn("H-01", s["signature"]["damaged"])

    def test_driver_error_in_a_verdict_case_is_not_a_reproduced_defect(self):
        write(self.out_path("H-04"), "case_id H-04\nerror cannot_open_matrix_file\ndriver_rc 3\n")
        s = self.judge()
        self.assertEqual(s["integrity_kinds"]["H-04"], "driver")
        self.assertIn("H-04", s["signature"]["not_failing"])
        self.assertFalse(s["signature"]["ok"])

    def test_truncated_verdict_case_is_not_a_reproduced_defect(self):
        text = read(self.out_path("H-04"))
        write(self.out_path("H-04"), text[: len(text) - 7])
        s = self.judge()
        self.assertEqual(s["integrity_kinds"]["H-04"], "evidence")
        self.assertIn("H-04", s["signature"]["not_failing"])

    def test_wrong_identity_in_a_verdict_case_is_not_a_reproduced_defect(self):
        text = read(self.out_path("H-04")).replace("case_id H-04\n", "case_id H-05\n", 1)
        write(self.out_path("H-04"), text)
        s = self.judge()
        self.assertEqual(s["integrity_kinds"]["H-04"], "evidence")
        self.assertIn("H-04", s["signature"]["not_failing"])

    def test_missing_out_of_a_must_pass_control_fails_the_signature(self):
        os.remove(self.out_path("A-01"))
        s = self.judge()
        self.assertIn("A-01", s["signature"]["not_passing"])
        self.assertIn("A-01", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])

    def test_damage_outside_the_signature_is_an_integrity_failure(self):
        write(self.out_path("C-01", "stdout"), "unexpected\n")
        s = self.judge()
        self.assertIn("C-01", s["integrity_failures"])
        self.assertFalse(s["accepted"])


class AsanBaselineSignatureTests(FixtureTest):
    variant = "asan_baseline"

    def test_sanitizer_report_on_a_normal_exit_is_a_registered_mechanism(self):
        s = self.judge()
        self.assertEqual(self.case(s, "A-38")["integrity_kind"], "sanitizer")
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def test_may_fail_case_with_a_missing_record_is_damage(self):
        # A-37 may fail or pass; if its record is damaged the signature is not met.
        os.remove(self.out_path("A-37", "stderr"))
        s = self.judge()
        self.assertIn("A-37", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])

    def test_may_fail_case_that_passes_keeps_the_signature(self):
        s = self.judge()
        self.assertTrue(self.case(s, "A-37")["pass"])
        self.assertTrue(s["signature"]["ok"])

    # rc 0 sanitizer lines: only the registered UBSan report forms are the defect -------------
    def test_rc0_ubsan_report_with_other_addresses_is_the_same_registered_form(self):
        text = read(self.out_path("A-38", "stderr"))
        text = text.replace("to non-null pointer 0xfffffffffffffb30 produced",
                            "to non-null pointer 0x7ffe12340000 produced")
        write(self.out_path("A-38", "stderr"), text)
        s = self.judge()
        self.assertEqual(self.case(s, "A-38")["integrity_kind"], "sanitizer")
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def test_rc0_marker_only_sanitizer_text_is_unsupported(self):
        # Round-4 counterexample B4: the record is complete and real, only stderr is replaced.
        write(self.out_path("A-38", "stderr"), "AddressSanitizer: bananas\n")
        s = self.judge()
        self.assertEqual(self.case(s, "A-38")["integrity_kind"], "unsupported_sanitizer")
        self.assertIn("unsupported sanitizer report", self.case(s, "A-38")["integrity"])
        self.assertIn("A-38", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])

    def test_rc0_unregistered_ubsan_kind_is_unsupported(self):
        write(self.out_path("A-38", "stderr"),
              "/src/S4/RNP/Eigensystems.cpp:3834:6: runtime error: signed integer overflow\n")
        s = self.judge()
        self.assertEqual(self.case(s, "A-38")["integrity_kind"], "unsupported_sanitizer")
        self.assertFalse(s["signature"]["ok"])

    def test_rc0_registered_report_mixed_with_unsupported_text_is_unsupported(self):
        text = read(self.out_path("A-38", "stderr"))
        write(self.out_path("A-38", "stderr"), text + "AddressSanitizer: bananas\n")
        s = self.judge()
        self.assertEqual(self.case(s, "A-38")["integrity_kind"], "unsupported_sanitizer")
        self.assertFalse(s["signature"]["ok"])

    # A-07: the frozen observation is allowed to pass or fail in asan_baseline only ----------
    def set_a07_info(self, value):
        """Only the info record of the A-07 observation changes; the rest of the real record stays."""
        text = re.sub(r"^info -?\d+$", "info %d" % value, read(self.out_path("A-07")), flags=re.M)
        write(self.out_path("A-07"), text)

    def test_a07_info_zero_observation_passes_within_the_signature(self):
        self.set_a07_info(0)
        s = self.judge()
        r = self.case(s, "A-07")
        self.assertEqual((r["integrity_kind"], r["pass"]), ("ok", True))
        self.assertTrue(r["detail"].startswith("info=0 "), r["detail"])
        self.assertTrue(s["signature"]["ok"], s["signature"])
        self.assertIn("A-07", s["signature"]["may_fail"])

    def test_a07_nonzero_info_observation_fails_within_the_signature(self):
        # 18807 is one of the saved non-zero values of this case (round-4 diagnostics); the test
        # checks that the may_fail allowance covers a complete non-zero observation.
        self.set_a07_info(18807)
        s = self.judge()
        r = self.case(s, "A-07")
        self.assertEqual((r["integrity_kind"], r["pass"]), ("ok", False))
        self.assertIn("info=18807, expected 0", r["detail"])
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def test_a07_observation_with_wrong_identity_is_damage(self):
        write(self.out_path("A-07"), read(self.out_path("A-07")).replace("case_id A-07\n",
                                                                         "case_id A-08\n", 1))
        s = self.judge()
        self.assertEqual(self.case(s, "A-07")["integrity_kind"], "evidence")
        self.assertIn("A-07", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])

    def test_a07_truncated_observation_is_damage(self):
        text = read(self.out_path("A-07"))
        write(self.out_path("A-07"), text[: text.rindex("driver_rc")])
        s = self.judge()
        self.assertEqual(self.case(s, "A-07")["integrity_kind"], "evidence")
        self.assertIn("A-07", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])

    def test_a07_unregistered_exit_is_damage(self):
        idx = self.index()
        for c in idx["cases"]:
            if c["case_id"] == "A-07":
                c["rc"] = 127
        self.save_index(idx)
        write(self.out_path("A-07", "stderr"), "")
        s = self.judge()
        self.assertEqual(self.case(s, "A-07")["integrity_kind"], "exit_unknown")
        self.assertIn("A-07", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])


class SeamAsanBaselineTests(FixtureTest):
    """seam_asan_baseline: the real crash record and the seam identity of a crash record.

    The saved H-01 record of this variant is empty (ASan report only), so the identity cases
    write their own short records.  The A-07 exception of round 5 is asan_baseline only: here A-07
    must still show the defect, so a passing observation breaks the signature."""

    variant = "seam_asan_baseline"

    def case_of(self, cid):
        return next(c for c in PLAN["cases"] if c["case_id"] == cid)

    def test_real_seam_crash_with_an_empty_record_is_the_registered_asan_report(self):
        s = self.judge()
        self.assertEqual(self.case(s, "H-01")["integrity_kind"], "exit")
        self.assertIn("AddressSanitizer report", self.case(s, "H-01")["integrity"])
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def test_seam_crash_with_seam_enabled_0_is_not_masked(self):
        # Round-4 counterexample B2 (the saved record was empty, so the line is inserted).
        write(self.out_path("H-01"), "seam_enabled 0\n")
        self.assert_not_the_defect(self.judge(), "H-01", "evidence", "seam_enabled=0, expected 1")

    def test_seam_crash_with_a_cut_seam_enabled_0_is_not_masked(self):
        write(self.out_path("H-01"), "case_id H-01\nseam_enabled 0")
        self.assert_not_the_defect(self.judge(), "H-01", "evidence", "seam_enabled=0, expected 1")

    def test_seam_crash_with_a_wrong_forced_info_is_not_masked(self):
        wrong = int(self.case_of("H-01").get("seam_info", 0)) + 1
        write(self.out_path("H-01"), "seam_enabled 1\nseam_forced_info %d\n" % wrong)
        self.assert_not_the_defect(self.judge(), "H-01", "evidence", "seam_forced_info=%d, expected" % wrong)

    def test_seam_crash_with_a_wrong_mode_is_not_masked(self):
        wrong = int(self.case_of("H-01").get("seam_mode", 0)) + 1
        write(self.out_path("H-01"), "seam_enabled 1\nseam_mode_used %d\n" % wrong)
        self.assert_not_the_defect(self.judge(), "H-01", "evidence", "seam_mode_used=%d, expected" % wrong)

    def test_seam_crash_with_a_cut_consistent_seam_value_is_still_the_registered_abort(self):
        write(self.out_path("H-01"), "case_id H-01\nseam_enabled 1")
        s = self.judge()
        self.assertEqual(self.case(s, "H-01")["integrity_kind"], "exit")
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def test_a07_stays_a_defect_in_the_seam_variant(self):
        s = self.judge()
        self.assertIn("A-07", s["signature"]["must_fail"])
        self.assertNotIn("A-07", s["signature"]["may_fail"])
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def test_a07_passing_in_the_seam_variant_breaks_the_signature(self):
        write(self.out_path("A-07"), re.sub(r"^info \d+$", "info 0", read(self.out_path("A-07")), flags=re.M))
        s = self.judge()
        self.assertTrue(self.case(s, "A-07")["pass"])
        self.assertIn("A-07", s["signature"]["not_failing"])
        self.assertFalse(s["signature"]["ok"])


class AbnormalExitBaselineTests(FixtureTest):
    """ord_baseline: an abnormal exit counts as the defect only when it is a registered mechanism
    (SIGABRT with its glibc diagnostic, or SIGSEGV after a complete record).  Any other status,
    any invalid rc type, and any contradictory identity record is not the defect.  The cases
    start from the saved control: H-01 (complete record, SIGABRT) and A-17 (empty .out, SIGABRT)."""

    variant = "ord_baseline"

    def set_rc(self, cid, rc):
        idx = self.index()
        for c in idx["cases"]:
            if c["case_id"] == cid:
                c["rc"] = rc
        self.save_index(idx)

    # runner and rc type ----------------------------------------------------
    def test_timeout_is_a_runner_failure_not_the_defect(self):
        self.set_rc("H-01", "timeout")
        self.assert_not_the_defect(self.judge(), "H-01", "runner", "runner failure rc='timeout'")

    def test_exec_error_is_a_runner_failure_not_the_defect(self):
        self.set_rc("H-01", "exec_error: Permission denied")
        self.assert_not_the_defect(self.judge(), "H-01", "runner", "runner failure")

    def test_status_127_is_not_a_registered_mechanism(self):
        self.set_rc("H-01", 127)
        self.assert_not_the_defect(self.judge(), "H-01", "exit_unknown", "not a registered mechanism")

    def test_null_rc_is_an_invalid_record(self):
        self.set_rc("H-01", None)
        self.assert_not_the_defect(self.judge(), "H-01", "evidence", "not a process status")

    def test_bool_rc_is_an_invalid_record(self):
        self.set_rc("H-01", True)
        self.assert_not_the_defect(self.judge(), "H-01", "evidence", "not a process status")

    def test_string_zero_rc_is_an_invalid_record(self):
        self.set_rc("H-01", "0")
        self.assert_not_the_defect(self.judge(), "H-01", "evidence", "not a process status")

    # abnormal exit with contradictory or missing evidence -------------------
    def test_crash_with_wrong_identity_is_not_masked(self):
        write(self.out_path("A-17"), "case_id WRONG\n")
        self.assert_not_the_defect(self.judge(), "A-17", "evidence", "case_id=WRONG, expected A-17")

    def test_crash_with_wrong_variant_is_not_masked(self):
        write(self.out_path("A-17"), "case_id A-17\nvariant asan_baseline\n")
        self.assert_not_the_defect(self.judge(), "A-17", "evidence", "variant=asan_baseline")

    def test_crash_with_an_unregistered_abort_message_is_not_the_defect(self):
        write(self.out_path("A-17", "stderr"), "double free or corruption (out)\n")
        self.assert_not_the_defect(self.judge(), "A-17", "exit_unknown", "not a registered mechanism")

    def test_crash_with_empty_stderr_is_not_the_registered_abort(self):
        write(self.out_path("A-17", "stderr"), "")
        self.assert_not_the_defect(self.judge(), "A-17", "exit_unknown", "not a registered mechanism")

    def test_crash_with_a_driver_error_record_is_a_driver_failure(self):
        write(self.out_path("A-17"), "case_id A-17\nerror boom\n")
        self.assert_not_the_defect(self.judge(), "A-17", "driver", "driver error: boom")

    def test_crash_with_an_empty_record_is_still_the_registered_abort(self):
        s = self.judge()
        r = self.case(s, "A-17")
        self.assertEqual((r["integrity_kind"], r["pass"]), ("exit", False))
        self.assertIn("SIGABRT with a glibc heap-check diagnostic", r["integrity"])
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def test_crash_with_a_partial_record_is_still_the_registered_abort(self):
        write(self.out_path("A-17"), "case_id A-17\nentry API\nmatrix A3p2\n")
        s = self.judge()
        self.assertEqual(self.case(s, "A-17")["integrity_kind"], "exit")
        self.assertTrue(s["signature"]["ok"], s["signature"])

    # SIGSEGV: no judged case has a registered SIGSEGV mechanism (the A-10r probe is recorded only)
    def test_sigsegv_after_the_complete_record_is_not_registered(self):
        self.set_rc("H-01", -11)
        write(self.out_path("H-01", "stderr"), "")
        self.assert_not_the_defect(self.judge(), "H-01", "exit_unknown", "not a registered mechanism")

    def test_sigsegv_with_only_a_driver_rc_record_is_not_the_defect(self):
        # The round-4 reviewed counterexample: no identity at all, a last line of driver_rc only.
        self.set_rc("H-01", -11)
        write(self.out_path("H-01", "stderr"), "")
        write(self.out_path("H-01"), "driver_rc 0\n")
        self.assert_not_the_defect(self.judge(), "H-01", "exit_unknown", "not a registered mechanism")

    def test_sigsegv_with_a_partial_record_is_not_registered(self):
        self.set_rc("A-17", -11)
        write(self.out_path("A-17", "stderr"), "")
        self.assert_not_the_defect(self.judge(), "A-17", "exit_unknown", "not a registered mechanism")

    def test_sigsegv_with_a_stderr_diagnostic_is_not_registered(self):
        self.set_rc("H-01", -11)
        self.assert_not_the_defect(self.judge(), "H-01", "exit_unknown", "not a registered mechanism")

    def test_contract_probe_sigsegv_stays_recorded_and_does_not_affect_the_signature(self):
        # A-10r exits -11 with no diagnostic in the saved ord_baseline: recorded, never judged.
        s = self.judge()
        probe = self.case(s, "A-10r")
        self.assertEqual((probe["status"], probe["pass"]), ("recorded", None))
        self.assertIn("rc=-11", probe["detail"])
        self.assertNotIn("A-10r", s["signature"]["damaged"])
        self.assertTrue(s["signature"]["ok"], s["signature"])

    # Identity of a crash record: an unterminated last line is judged only as far as it goes ----
    def test_crash_with_a_wrong_identity_without_a_newline_is_not_masked(self):
        # Round-4 counterexample B1: the line is incomplete, but "WRONG" is not a prefix of A-17.
        write(self.out_path("A-17"), "case_id WRONG")
        self.assert_not_the_defect(self.judge(), "A-17", "evidence", "case_id=WRONG, expected A-17")

    def test_crash_with_a_cut_identity_value_is_still_the_registered_abort(self):
        write(self.out_path("A-17"), "case_id A-1")
        s = self.judge()
        self.assertEqual(self.case(s, "A-17")["integrity_kind"], "exit")
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def test_crash_with_a_wrong_complete_matrix_line_is_not_masked(self):
        write(self.out_path("A-17"), "case_id A-17\nentry API\nmatrix A3q2\n")
        self.assert_not_the_defect(self.judge(), "A-17", "evidence", "matrix=A3q2, expected A3p2")

    def test_crash_with_a_wrong_reported_layout_is_not_masked(self):
        # Layout records are identity too, now that the abnormal path checks them.
        write(self.out_path("A-17"), "case_id A-17\nentry API\nmatrix A3p2\nldvr 9\n")
        self.assert_not_the_defect(self.judge(), "A-17", "evidence", "ldvr=9, expected")

    def test_helper_crash_with_a_wrong_reported_capacity_is_not_masked(self):
        text = read(self.out_path("H-01"))
        write(self.out_path("H-01"), re.sub(r"^v_capacity_elems \d+$", "v_capacity_elems 1",
                                            text, flags=re.M))
        self.assert_not_the_defect(self.judge(), "H-01", "evidence", "v_capacity_elems=1, expected 9")

    def test_non_seam_crash_carrying_a_seam_record_is_not_masked(self):
        write(self.out_path("A-17"), "case_id A-17\nseam_mode_used 0\n")
        self.assert_not_the_defect(self.judge(), "A-17", "evidence",
                                   "seam record seam_mode_used present in a non-seam variant")


class AbnormalExitAsanTests(FixtureTest):
    """asan_baseline: the ASan exit (rc 1) is a registered mechanism only with a registered
    report kind.  A-37 may fail or pass (undefined behaviour); its unknown exits must not pass."""

    variant = "asan_baseline"

    def test_registered_asan_report_is_the_defect(self):
        s = self.judge()
        self.assertEqual(self.case(s, "A-17")["integrity_kind"], "exit")
        self.assertIn("AddressSanitizer report", self.case(s, "A-17")["integrity"])
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def test_unregistered_asan_report_kind_is_not_the_defect(self):
        path = self.out_path("A-17", "stderr")
        write(path, read(path).replace("heap-buffer-overflow", "stack-buffer-overflow"))
        s = self.judge()
        self.assertEqual(self.case(s, "A-17")["integrity_kind"], "exit_unknown")
        self.assertIn("A-17", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])

    def test_may_fail_case_with_an_unknown_exit_is_damage(self):
        # A-37 passes in this saved run.  If it exits abnormally for an unregistered reason, the
        # may_fail allowance does not cover it: the signature fails.
        idx = self.index()
        for c in idx["cases"]:
            if c["case_id"] == "A-37":
                c["rc"] = 127
        self.save_index(idx)
        write(self.out_path("A-37", "stderr"), "")
        s = self.judge()
        self.assertEqual(self.case(s, "A-37")["integrity_kind"], "exit_unknown")
        self.assertIn("A-37", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])

    def test_rc0_ubsan_report_with_a_truncated_record_is_evidence(self):
        text = read(self.out_path("A-38"))
        self.assertTrue(text.endswith("driver_rc 0\n"))
        write(self.out_path("A-38"), text[: text.rindex("driver_rc")])
        s = self.judge()
        self.assertEqual(self.case(s, "A-38")["integrity_kind"], "evidence")
        self.assertIn("A-38", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])

    def test_rc0_ubsan_report_with_wrong_identity_is_evidence(self):
        text = read(self.out_path("A-38")).replace("case_id A-38\n", "case_id A-39\n", 1)
        write(self.out_path("A-38"), text)
        s = self.judge()
        self.assertEqual(self.case(s, "A-38")["integrity_kind"], "evidence")
        self.assertFalse(s["signature"]["ok"])


class A36AsanBaselineTests(FixtureTest):
    """A-36 (values-only + scalea) in asan_baseline is may_fail: its uninitialised info is 0 in
    some runs (pass) and a wild index in others (ASan SEGV at REGISTERED_SITES).  Evidence:
    testing/d002/evidence/A36_RULE_CORRECTION.md.  The crash record is the real native-run stderr
    of 2026-10-10; any other ASan crash of A-36 is damage, not the defect."""

    variant = "asan_baseline"
    SITE_STDERR = os.path.join(FIXTURES, "a36_asan_baseline_segv.stderr.txt")

    def crash_a36(self, stderr_text=None, rc=1, out_text=""):
        idx = self.index()
        for c in idx["cases"]:
            if c["case_id"] == "A-36":
                c["rc"] = rc
        self.save_index(idx)
        write(self.out_path("A-36"), out_text)
        write(self.out_path("A-36", "stderr"),
              read(self.SITE_STDERR) if stderr_text is None else stderr_text)

    def assert_a36_damage(self, s, fragment):
        r = self.case(s, "A-36")
        self.assertEqual(r["integrity_kind"], "exit_unknown", r)
        self.assertIn(fragment, r["integrity"])
        self.assertIn("A-36", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])
        self.assertFalse(s["accepted"])

    def test_a36_is_may_fail_not_must_pass_in_asan_baseline(self):
        s = self.judge()
        self.assertIn("A-36", s["signature"]["may_fail"])
        self.assertNotIn("A-36", s["signature"]["must_pass"])

    def test_a36_saved_pass_with_info_zero_keeps_the_signature(self):
        s = self.judge()
        r = self.case(s, "A-36")
        self.assertEqual((r["integrity_kind"], r["pass"]), ("ok", True))
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def set_a36_info(self, value):
        """Only the info record of the saved A-36 observation changes (the verdict stops at info)."""
        text = re.sub(r"^info -?\d+$", "info %d" % value, read(self.out_path("A-36")), flags=re.M)
        write(self.out_path("A-36"), text)

    def test_a36_nonzero_info_inside_the_window_is_the_registered_outcome(self):
        # n = 2 and the scaled loop touches w[info..n-1] only for 1 <= info <= n (see the constants).
        for value in (1, 2):
            with self.subTest(info=value):
                self.set_a36_info(value)
                s = self.judge()
                r = self.case(s, "A-36")
                self.assertEqual((r["integrity_kind"], r["pass"], r["basis"]),
                                 ("ok", False, "nonzero_info_window"), r)
                self.assertIn("info=%d, expected 0" % value, r["detail"])
                self.assertTrue(s["signature"]["ok"], s["signature"])
                self.assertEqual(s["signature"]["damaged"], [])

    def test_a36_nonzero_info_outside_the_window_is_unregistered(self):
        # A value outside [1, n] makes the baseline's scaled loop leave w: not a clean outcome.
        for value in (-1, 3, 8):
            with self.subTest(info=value):
                self.set_a36_info(value)
                s = self.judge()
                r = self.case(s, "A-36")
                self.assertEqual((r["integrity_kind"], r["pass"], r["basis"]),
                                 ("outcome_unregistered", False, ""), r)
                self.assertIn("A-36", s["signature"]["damaged"])
                self.assertFalse(s["signature"]["ok"])
                self.assertFalse(s["accepted"])

    def test_a36_info_zero_with_a_wrong_eigenvalue_fails_the_signature(self):
        # Review counterexample 1: a finite but wrong eigenvalue with info 0 is not the mechanism.
        text = re.sub(r"^w 0 .*$", "w 0 1 0", read(self.out_path("A-36")), count=1, flags=re.M)
        write(self.out_path("A-36"), text)
        s = self.judge()
        r = self.case(s, "A-36")
        self.assertEqual((r["integrity_kind"], r["pass"], r["basis"]), ("outcome_unregistered", False, ""))
        self.assertIn("eigenvalue error", r["detail"])
        self.assertIn("A-36", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])
        self.assertFalse(s["accepted"])

    def test_a36_info_zero_with_a_severe_but_finite_eigenvalue_error_fails_the_signature(self):
        # Relative error 1e-3 against the frozen 1e-10 tolerance: finite, wrong, not registered.
        def scale_w0(match):
            re_part, im_part = float(match.group(1)), float(match.group(2))
            return "w 0 %r %r" % (re_part * 1.001, im_part * 1.001)
        text = re.sub(r"^w 0 (\S+) (\S+)$", scale_w0, read(self.out_path("A-36")), count=1, flags=re.M)
        write(self.out_path("A-36"), text)
        s = self.judge()
        self.assertEqual(self.case(s, "A-36")["integrity_kind"], "outcome_unregistered")
        self.assertFalse(s["signature"]["ok"])

    def test_a36_info_zero_within_the_frozen_tolerance_keeps_the_signature(self):
        # A perturbation of 1e-13 relative is inside eig_rel_tol 1e-10: the verdict still passes.
        def nudge(match):
            re_part, im_part = float(match.group(1)), float(match.group(2))
            return "w 1 %r %r" % (re_part * (1 + 1e-13), im_part * (1 + 1e-13))
        text = re.sub(r"^w 1 (\S+) (\S+)$", nudge, read(self.out_path("A-36")), count=1, flags=re.M)
        write(self.out_path("A-36"), text)
        s = self.judge()
        r = self.case(s, "A-36")
        self.assertEqual((r["integrity_kind"], r["pass"]), ("ok", True), r)
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def test_a36_missing_eigenvalue_record_is_damage(self):
        text = re.sub(r"^w 1 .*\n", "", read(self.out_path("A-36")), count=1, flags=re.M)
        write(self.out_path("A-36"), text)
        s = self.judge()
        self.assertEqual(self.case(s, "A-36")["integrity_kind"], "evidence")
        self.assertIn("A-36", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])

    def test_a36_crash_at_the_registered_site_is_the_registered_defect(self):
        self.crash_a36()
        s = self.judge()
        r = self.case(s, "A-36")
        self.assertEqual((r["integrity_kind"], r["pass"], r["basis"]), ("exit", False, "registered_site"))
        self.assertIn("abnormal exit rc=1 (AddressSanitizer report)", r["integrity"])
        self.assertTrue(s["signature"]["ok"], s["signature"])
        self.assertEqual(s["signature"]["damaged"], [])

    def test_a36_asan_crash_at_another_line_is_damage(self):
        text = read(self.SITE_STDERR).replace("Eigensystems.cpp:4715", "Eigensystems.cpp:4700")
        self.crash_a36(text)
        self.assert_a36_damage(self.judge(), "is not at the registered site of A-36")

    def test_a36_asan_crash_through_another_caller_is_damage(self):
        text = read(self.SITE_STDERR).replace("in RNP::Eigensystem(", "in RNP::Eigensystem_other(")
        self.crash_a36(text)
        self.assert_a36_damage(self.judge(), "is not at the registered site of A-36")

    def test_a36_heap_overflow_at_the_registered_site_is_damage(self):
        text = read(self.SITE_STDERR).replace(
            "ERROR: AddressSanitizer: SEGV on unknown address",
            "ERROR: AddressSanitizer: heap-buffer-overflow on address")
        self.crash_a36(text)
        self.assert_a36_damage(self.judge(), "is not at the registered site of A-36")

    def test_a36_unsanitized_sigsegv_is_damage(self):
        self.crash_a36(stderr_text="", rc=-11)
        self.assert_a36_damage(self.judge(), "abnormal exit rc=-11 is not a registered mechanism")

    def test_a36_crash_with_a_wrong_identity_partial_record_is_damage(self):
        self.crash_a36(out_text="case_id A-07\n")
        s = self.judge()
        self.assertEqual(self.case(s, "A-36")["integrity_kind"], "evidence")
        self.assertIn("A-36", s["signature"]["damaged"])
        self.assertFalse(s["signature"]["ok"])


    def test_a36_registered_report_plus_an_unrelated_asan_report_is_damage(self):
        # Review counterexample 2: the registered SEGV report followed by an unrelated ASan report.
        extra = ("ERROR: AddressSanitizer: heap-buffer-overflow on address 0x123\n"
                 "    #0 0x123 in unrelated_bug other.cpp:1\n")
        self.crash_a36(read(self.SITE_STDERR) + extra)
        self.assert_a36_damage(self.judge(), "is not at the registered site of A-36")

    def test_a36_repeated_registered_report_is_damage(self):
        seg = read(self.SITE_STDERR)
        self.crash_a36(seg + seg)
        self.assert_a36_damage(self.judge(), "is not at the registered site of A-36")

    def test_a36_summary_of_another_kind_is_damage(self):
        text = read(self.SITE_STDERR).replace("SUMMARY: AddressSanitizer: SEGV ",
                                              "SUMMARY: AddressSanitizer: heap-buffer-overflow ")
        self.crash_a36(text)
        self.assert_a36_damage(self.judge(), "is not at the registered site of A-36")

    def test_a36_other_sanitizer_token_in_the_report_is_damage(self):
        self.crash_a36(read(self.SITE_STDERR) + "runtime error: signed integer overflow\n")
        self.assert_a36_damage(self.judge(), "is not at the registered site of A-36")

    def test_a36_unsymbolised_site_frames_are_damage(self):
        # Fail closed: without the function names and source line the site cannot be matched.
        text = re.sub(r" in RNP::[^\n]*", " (d002_asan_baseline+0x9bde4)", read(self.SITE_STDERR))
        self.crash_a36(text)
        self.assert_a36_damage(self.judge(), "is not at the registered site of A-36")


class A36RuleFunctionTests(unittest.TestCase):
    """The A-36 outcome rule and the single-report site check, as functions (real saved text)."""

    def test_nonzero_info_rule_is_the_asan_baseline_window_only(self):
        rule = d002.registered_verdict_failure
        by_info = (lambda info: {"info": str(info)})
        info_reason = d002.Reject("info=1, expected 0", reason="info")
        numeric = d002.Reject("eigenvalue error 1 > 1e-10", reason="numeric")
        self.assertTrue(rule("asan_baseline", "A-36", info_reason, by_info(1), 2))
        self.assertTrue(rule("asan_baseline", "A-36", info_reason, by_info(2), 2))
        self.assertFalse(rule("asan_baseline", "A-36", info_reason, by_info(0), 2))
        self.assertFalse(rule("asan_baseline", "A-36", info_reason, by_info(3), 2))
        self.assertFalse(rule("asan_baseline", "A-36", numeric, by_info(1), 2))
        self.assertFalse(rule("seam_asan_baseline", "A-36", info_reason, by_info(1), 2))
        self.assertFalse(rule("seam_asan_baseline", "A-36", numeric, by_info(1), 2))
        # candidates and every other case keep their judged verdict unchanged
        self.assertTrue(rule("asan_candidate", "A-36", numeric, by_info(0), 2))
        self.assertTrue(rule("asan_baseline", "A-07", numeric, by_info(0), 3))

    def test_site_check_accepts_one_whole_registered_report_only(self):
        seg = read(os.path.join(FIXTURES, "a36_asan_baseline_segv.stderr.txt"))
        other = ("ERROR: AddressSanitizer: heap-buffer-overflow on address 0x123\n"
                 "    #0 0x123 in unrelated_bug other.cpp:1\n")
        self.assertTrue(d002.site_registered("asan_baseline", "A-36", seg))
        self.assertTrue(d002.site_registered("seam_asan_baseline", "A-36", seg))
        self.assertFalse(d002.site_registered("asan_baseline", "A-36", seg + other))
        self.assertFalse(d002.site_registered("asan_baseline", "A-36", other + seg))
        self.assertFalse(d002.site_registered("asan_baseline", "A-36", seg + seg))
        self.assertFalse(d002.site_registered("asan_baseline", "A-36", seg.replace("SEGV on", "BUS on")))
        # A case without a registered site is not constrained by this check
        self.assertTrue(d002.site_registered("ord_baseline", "A-36", other))
        self.assertTrue(d002.site_registered("asan_candidate", "A-36", other))


class SeamBaselineA36Tests(FixtureTest):
    """A-36 in seam_asan_baseline is must_fail: the saved control crashes at REGISTERED_SITES
    (20 of 20 repeats on 2026-10-10 as well).  A crash elsewhere does not show the seam defect."""

    variant = "seam_asan_baseline"

    def test_a36_registered_site_crash_is_the_seam_defect(self):
        s = self.judge()
        r = self.case(s, "A-36")
        self.assertEqual((r["integrity_kind"], r["pass"]), ("exit", False))
        self.assertNotIn("A-36", s["signature"]["not_failing"])
        self.assertTrue(s["signature"]["ok"], s["signature"])

    def test_a36_crash_at_another_line_does_not_show_the_seam_defect(self):
        text = read(self.out_path("A-36", "stderr")).replace("Eigensystems.cpp:4715",
                                                              "Eigensystems.cpp:4700")
        write(self.out_path("A-36", "stderr"), text)
        s = self.judge()
        self.assertEqual(self.case(s, "A-36")["integrity_kind"], "exit_unknown")
        self.assertIn("A-36", s["signature"]["not_failing"])
        self.assertFalse(s["signature"]["ok"])


class AsanCandidateA36Tests(FixtureTest):
    """The candidate has no registered site: the baseline's A-36 crash is a failure of the
    candidate, not an accepted defect (the judge is strict for candidates)."""

    variant = "asan_candidate"

    def test_candidate_with_the_baseline_crash_is_not_accepted(self):
        idx = self.index()
        for c in idx["cases"]:
            if c["case_id"] == "A-36":
                c["rc"] = 1
        self.save_index(idx)
        write(self.out_path("A-36"), "")
        write(self.out_path("A-36", "stderr"),
              read(os.path.join(FIXTURES, "a36_asan_baseline_segv.stderr.txt")))
        s = self.judge()
        self.assertFalse(self.case(s, "A-36")["pass"])
        self.assertFalse(s["all_judged_pass"])
        self.assertFalse(s["accepted"])

    def test_candidate_numeric_failure_with_info_zero_is_not_accepted(self):
        text = re.sub(r"^w 0 .*$", "w 0 1 0", read(self.out_path("A-36")), count=1, flags=re.M)
        write(self.out_path("A-36"), text)
        s = self.judge()
        r = self.case(s, "A-36")
        self.assertEqual((r["integrity_kind"], r["pass"], r["basis"]), ("ok", False, ""), r)
        self.assertFalse(s["accepted"])

    def test_candidate_nonzero_info_inside_the_window_is_not_accepted(self):
        text = re.sub(r"^info -?\d+$", "info 1", read(self.out_path("A-36")), flags=re.M)
        write(self.out_path("A-36"), text)
        s = self.judge()
        r = self.case(s, "A-36")
        self.assertEqual((r["integrity_kind"], r["pass"], r["basis"]), ("ok", False, ""), r)
        self.assertFalse(s["accepted"])


class BaselineA36ClassTests(unittest.TestCase):
    """The per-identity classes of A-36 (2026-10-10 evidence, see A36_RULE_CORRECTION.md)."""

    def test_a36_classes_per_identity(self):
        table = d002.BASELINE_SIGNATURE
        self.assertIn("A-36", table["ord_baseline"]["must_pass"])
        self.assertIn("A-36", table["asan_baseline"]["may_fail"])
        self.assertNotIn("A-36", table["asan_baseline"]["must_pass"])
        self.assertIn("A-36", table["seam_asan_baseline"]["must_fail"])
        self.assertEqual(set(d002.REGISTERED_SITES),
                         {("asan_baseline", "A-36"), ("seam_asan_baseline", "A-36")})


class SelectCasesTests(unittest.TestCase):
    def test_unknown_subset_id_is_refused(self):
        with self.assertRaises(SystemExit):
            d002.select_cases(PLAN, "A-01,Z-99")

    def test_repeated_subset_id_is_refused(self):
        with self.assertRaises(SystemExit):
            d002.select_cases(PLAN, "A-01,A-01")

    def test_default_is_full(self):
        ids, scope = d002.select_cases(PLAN, None)
        self.assertEqual((len(ids), scope), (59, "full"))

    def test_subset_keeps_plan_order(self):
        ids, scope = d002.select_cases(PLAN, "A-02,A-01")
        self.assertEqual((ids, scope), (["A-01", "A-02"], "subset"))


if __name__ == "__main__":
    unittest.main()
