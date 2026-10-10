#!/usr/bin/env python3
"""D002 native RNP contract runner: real Eigensystems.cpp, frozen PLAN.json.

The driver (tools/d002_driver.cpp) #includes the real S4/RNP/Eigensystems.cpp from
a chosen source tree (-DD002_SRC) and calls the real RNP entry points.  This runner
only compiles, feeds the frozen case table, and judges the raw output against the
frozen thresholds in PLAN.json (eig_rel_tol, residual_tol, vector_norm_tol,
padding_init_value).  Thresholds are never changed here.

Variants (source tree x build identity):
  ord_*   project flags (-O3 -march=native ...), production-like
  asan_*  ASan+UBSan diagnostic build (-O1 -g)
  seam_*  asan build plus -DD002_TEST_SEAM (RNP-level zhseqr_ status override,
          test-only; never present in a normal build)

Judging is two-stage per case.
  Integrity (applies to every non-probe case, applicable or not), by process status:
    - rc 0 (normal exit): stdout is empty (schema 2 runs), the .out file parses under the
      strict grammar (no duplicate scalar, no unknown record, every number finite, last
      line is driver_rc, file ends with newline), and identities match the case: case_id,
      entry, matrix, variant, n, lda, seam fields, the reported ldvl/ldvr/lwork/work/rwork/
      want layout, capacities, and the vector index sets for every output the case
      requested or did not request.  Only then is a sanitizer line on stderr or stdout
      (UBSan continues after its report, so rc is still 0) a registered defect, and only
      when every sanitizer line is one of the registered UBSan report forms (UBSAN_REPORT_RE).
      Any other sanitizer text is an unsupported report: evidence, not the defect.
    - rc non-zero integer (abnormal exit, signal as a negative number): the .out file may be
      empty or partial.  Every complete line must parse, and every identity or layout record
      present must match the case (check_identity).  An unterminated last line is judged only
      as far as it goes (check_partial_tail).  The exit must be a registered mechanism (see
      abnormal_mechanism).  Any other status is not a defect.
    - rc "timeout" or "exec_error: ...": a runner failure, not a process status; not a defect.
    - any other rc type (bool, null, number as a string, ...): an invalid record.
  Verdict (only for judged cases, after integrity passed):
    API cases, seam_mode 0:
      info == 0; eigenvalues match the analytic reference as a multiset with
      error / max|lambda_ref| <= eig_rel_tol; right vectors residual
      max|A v - lambda v| / (max|A| * ||v||_2) <= residual_tol; left vectors
      residual max|A^H y - conj(lambda) y| / (max|A| * ||y||_2) <= residual_tol;
      | ||v||_2 - 1 | <= vector_norm_tol; padding rows keep the initial value.
      C-03 (seam variant) additionally requires seam_onlyvalues_real_info == 0.
    API query (A-08): info == 0 and work[0] == 2n exactly (imaginary part 0).
    API cases, seam_mode != 0: info == forced status and seam_last_real_info == 0.
      Only in seam variants; other variants mark these not_applicable.
    HELPER_GEBAK: every element of v (complex, including padding and columns >= m)
      equals the independent 1-based LAPACK zgebak model applied to the zgebal
      ilo/ihi/scale that the driver reports, within relative tolerance 1e-12.
      The ilo/ihi/scale producer output is checked against the zgebal convention
      first.  The model for ilo > ihi (empty active interval) is RNP's behaviour as
      documented in the case table; it is not certified as LAPACK behaviour.
    CONTRACT PROBES (A-10r): recorded with rc and sanitizer state; never pass/fail.

Baseline signature: a must_fail or may_fail case shows the defect only through a judged
verdict failure or a registered mechanism (abnormal exit, sanitizer report; DEFECT_KINDS).
A missing, malformed, truncated or otherwise damaged record never shows the defect.

Usage:
  python3 -I -B run_d002.py build --src-root SRC --variant NAME --out-dir DIR
  python3 -I -B run_d002.py run   --variant NAME --bin BIN --run-dir DIR [--cases all|ID,ID]
  python3 -I -B run_d002.py judge --variant NAME --run-dir DIR [--allow-legacy-schema1]
  python3 -I -B run_d002.py positives --out-dir DIR

`run --cases` writes scope "subset" with its expected ids; such a run is a targeted
diagnostic and the judge reports complete_run=false for it.  Only scope "full"
(the default) and schema 2 can yield a complete acceptance.  Schema 1 (legacy) runs are
judged only with --allow-legacy-schema1, for re-judging historical data.
"""

import argparse
import datetime
import hashlib
import json
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DRIVER = os.path.join(HERE, "tools", "d002_driver.cpp")
PLAN_PATH = os.path.join(HERE, "PLAN.json")
MATRICES_PATH = os.path.join(HERE, "cases", "matrices.json")

PROJ_FLAGS = ["-O3", "-Wall", "-march=native", "-fcx-limited-range", "-fno-exceptions", "-fPIC"]
SAN_FLAGS = ["-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
             "-fcx-limited-range"]

VARIANTS = {
    "ord": (PROJ_FLAGS, []),
    "asan": (SAN_FLAGS, []),
    "seam_asan": (SAN_FLAGS, ["-DD002_TEST_SEAM"]),
}
SANITIZER_MARKERS = ("AddressSanitizer", "runtime error:", "LeakSanitizer")
CASE_TIMEOUT_S = 60
# Registered in PLAN.json as contract-boundary probes: recorded, not judged.
CONTRACT_PROBES = {"A-10r"}
SCHEMA = 2  # RUN_INDEX schema written by cmd_run; formal judging accepts only this schema
LEGACY_SCHEMA = 1  # the 2026-10-09 runs; judged only with allow_legacy (explicit re-judging)

# Failure kinds of a case record (see verify_integrity and judge_case).
#   ok           evidence complete and clean; a verdict failure is judged with kind ok
#   exit          abnormal exit that is a registered mechanism (abnormal_mechanism)
#                 -- defect mechanism
#   sanitizer     sanitizer report on a normal exit (UBSan runtime error) on a complete,
#                 consistent record, in a registered report form -- defect mechanism
#   unsupported_sanitizer  sanitizer text on a normal exit that is not a registered report form
#                 -- not a mechanism
#   exit_unknown  abnormal exit that is not a registered mechanism (other signal, other exit
#                 status, or a registered signal without its diagnostic) -- not a mechanism
#   runner        the runner recorded timeout or exec_error, not a process status -- not a mechanism
#   driver        the driver itself reported an error or driver_rc != 0 -- not a registered mechanism
#   missing       a required record file is absent -- evidence failure
#   evidence      malformed, truncated, wrong identity, invalid rc type -- evidence failure
# Only exit and sanitizer are registered baseline defect mechanisms (observed in the saved
# baseline runs); the others never satisfy a defect signature, and a damaged record in any
# signature case fails the signature.
DEFECT_KINDS = ("exit", "sanitizer")

# Abnormal exits that are registered mechanisms of the baseline defect (abnormal_mechanism).
# Each rule states the evidence the saved baseline runs show for that exit, and nothing wider:
#   rc -6 (SIGABRT): stderr has a line equal to a GLIBC_ABORT_LINES entry.  Seen in every saved
#       ord_baseline abort (glibc heap-metadata check).  The .out may be empty or partial.
#   rc -11 (SIGSEGV): not a registered mechanism for any judged case.  The only SIGSEGV in the
#       saved runs is the contract probe A-10r (no diagnostic, complete record), which is
#       recorded and never judged.  A judged case that exits this way is exit_unknown, whatever
#       its record says.
#   rc 1 (ASan default exitcode): an AddressSanitizer report of a kind seen in the saved
#       asan_baseline and seam_asan_baseline runs (ASAN_REPORT_RE).  A case listed in
#       REGISTERED_SITES must also crash at its registered site (site_registered); any other
#       ASan report of that case is exit_unknown, not the defect.
# Any other exit status or signal is not a registered mechanism, whatever the signature says.
GLIBC_ABORT_LINES = ("free(): invalid size",)
ASAN_REPORT_RE = re.compile(r"ERROR: AddressSanitizer: (?:heap-buffer-overflow|SEGV)\b"
                            r"|AddressSanitizer:DEADLYSIGNAL")
# Registered crash sites (site_registered).  A-36 (values-only + scalea) in asan_baseline and
# seam_asan_baseline: the baseline discards zhseqr_'s return on the values-only branch, so `info`
# is read uninitialised, and RescaleMatrix(&w[info], n-info) at Eigensystems.cpp:4715 can read far
# outside w.  The registered crash is an ASan SEGV in RescaleMatrix called from RNP::Eigensystem at
# that line.  Evidence: testing/d002/evidence/A36_RULE_CORRECTION.md.
SEGV_REPORT_RE = re.compile(r"ERROR: AddressSanitizer: SEGV on unknown address")
A36_SITE_RE = re.compile(r"\s#\d+ [^\n]*in RNP::TLASupport::RescaleMatrix<[^\n]*\n"
                         r"\s+#\d+ [^\n]*in RNP::Eigensystem\([^\n]*Eigensystems\.cpp:4715\b")
REGISTERED_SITES = {
    ("asan_baseline", "A-36"): (SEGV_REPORT_RE, A36_SITE_RE),
    ("seam_asan_baseline", "A-36"): (SEGV_REPORT_RE, A36_SITE_RE),
}
# Sanitizer lines on a normal exit (rc 0; UBSan continues after its report).  Only the two forms
# that the saved asan_baseline runs show for A-38 (RNP pointer offsets) are registered.  The
# source path, line, column, offsets and addresses are not bound.
UBSAN_REPORT_RE = re.compile(r"[^\n]+?:\d+:\d+: runtime error: applying non-zero offset "
                             r"(?:\d+ to null pointer"
                             r"|to non-null pointer 0x[0-9a-fA-F]+ produced null pointer)$")

# Sanitizer positive controls: each must report exactly this signature in its own stderr.
POSITIVE_SIGNATURES = {
    "pos_asan": "AddressSanitizer: heap-buffer-overflow",
    "pos_ubsan": "runtime error: signed integer overflow",
    "pos_asan_ubsan": "AddressSanitizer: heap-buffer-overflow",
}

# Baseline defect signature (S1 inverse-balance boundary/layout, S2 only-values status).
# Derived from the four saved runs of each baseline variant (the 2026-10-09 executor and
# independent runs, the run-orig rerun and the 91b30a9 pipeline run).  Cases in must_fail
# failed in every run; cases in must_pass passed in every run; cases in may_fail are
# undefined-behaviour dependent (they failed in some runs and passed in others) and are
# allowed to fail, but are not required to.
S1_DEFECT_FAIL = ["A-15", "A-16", "A-17", "A-18", "A-19", "A-20", "A-21", "A-22", "A-23", "A-24",
                  "A-32", "A-33", "A-39", "A-40", "H-01", "H-02", "H-03", "H-04", "H-05", "H-06",
                  "H-08", "H-11"]
ORD_CONTROL_PASS = ["A-01", "A-02", "A-03", "A-04", "A-05", "A-06", "A-07", "A-08", "A-09",
                    "A-10", "A-11", "A-12", "A-13", "A-14", "A-25", "A-26", "A-27", "A-28",
                    "A-29", "A-30", "A-31", "A-34", "A-35", "A-36", "A-37", "A-38", "A-41",
                    "H-07", "H-09", "H-10"]
BASELINE_SIGNATURE = {
    "ord_baseline": {"must_fail": S1_DEFECT_FAIL, "may_fail": [], "must_pass": ORD_CONTROL_PASS},
    "asan_baseline": {
        # Round-5 correction, asan_baseline only: A-07's value branch never receives zhseqr_'s
        # info (uninitialised), so the saved observations are info 0 (pass) and non-zero (fail).
        # The frozen observation of round 4 was a failure; the evidence is in the round-4 report.
        # A-36 is the same values-only branch with scalea (w[info], n-info): its uninitialised info
        # is either 0 (pass) or a wild index that crashes at REGISTERED_SITES.  It was must_pass
        # before 2026-10-10; that was wrong: in the 2026-10-10 reruns 17 of 26 asan_baseline A-36
        # runs crashed at the site and 9 passed with info 0.  Evidence:
        # testing/d002/evidence/A36_RULE_CORRECTION.md.
        "must_fail": S1_DEFECT_FAIL + ["A-38", "A-41"],
        "may_fail": ["A-07", "A-36", "A-37", "C-03"],
        "must_pass": [c for c in ORD_CONTROL_PASS
                      if c not in ("A-07", "A-36", "A-37", "A-38", "A-41")],
    },
    "seam_asan_baseline": {
        # A-36 crashes at REGISTERED_SITES in every recorded run (20 of 20 repeats, 2026-10-10).
        "must_fail": S1_DEFECT_FAIL + ["A-07", "A-36", "A-37", "A-38", "A-41",
                                       "C-01", "C-02", "C-03", "C-04"],
        "may_fail": [],
        "must_pass": [c for c in ORD_CONTROL_PASS if c not in ("A-07", "A-36", "A-37", "A-38", "A-41")]
                     + ["C-05", "C-06"],
    },
}


VEC_KEYS = ("w", "vl_flat", "vr_flat", "v_flat", "work0")
SCALAR_KEYS = {
    "case_id", "entry", "matrix", "variant", "pid", "n", "lda", "anrm", "scalea", "cscale",
    "smlnum", "bignum", "ilo_1based", "ihi_1based", "ldvl", "ldvr", "lwork_passed",
    "work_mode", "rwork_mode", "want", "a_capacity_elems", "vl_capacity_elems",
    "vr_capacity_elems", "work_capacity_elems", "rwork_capacity_elems", "elapsed_s", "info",
    "side", "job", "m", "ldv", "v_capacity_elems",
    "seam_enabled", "seam_mode_used", "seam_forced_info", "seam_calls_total",
    "seam_calls_onlyvalues", "seam_calls_schur", "seam_last_real_info",
    "seam_onlyvalues_real_info", "driver_rc", "error",
}
SEAM_KEYS = ("seam_mode_used", "seam_forced_info", "seam_calls_total", "seam_calls_onlyvalues",
             "seam_calls_schur", "seam_last_real_info", "seam_onlyvalues_real_info")
API_KEYS = ("ldvl", "ldvr", "lwork_passed", "work_mode", "rwork_mode", "want",
            "a_capacity_elems", "vl_capacity_elems", "vr_capacity_elems",
            "work_capacity_elems", "rwork_capacity_elems", "elapsed_s", "info")
HELPER_KEYS = ("side", "job", "m", "ldv", "v_capacity_elems")

INT_RE = re.compile(r"^[+-]?[0-9]+$")
FLOAT_RE = re.compile(r"^[+-]?(?:[0-9]+\.?[0-9]*|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")
NONFINITE_RE = re.compile(r"^[+-]?(?:nan|inf|infinity)$", re.IGNORECASE)


class Reject(Exception):
    """A check failed; the message is the human-readable reason and kind says which class
    of failure it is (see DEFECT_KINDS and the kinds listed above)."""

    def __init__(self, msg, kind="evidence"):
        Exception.__init__(self, msg)
        self.kind = kind


class RunFatal(Exception):
    """The run as a whole is not a valid input for judging."""


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8", "replace")


def load_plan():
    with open(PLAN_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def load_matrices():
    with open(MATRICES_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def cplx_of(pair):
    return complex(float(pair[0]), float(pair[1]))


def matrix_of(mats, mid):
    m = mats["matrices"][mid]
    n, lda = m["n"], m["lda"]
    vals = [cplx_of(v) for v in m["values"]]
    A = [[0j] * n for _ in range(n)]
    for j in range(n):
        for i in range(n):
            A[i][j] = vals[i + j * lda]
    return A, n, lda


def variant_kind(variant):
    for kind in ("seam_asan", "asan", "ord"):
        if variant == kind or variant.startswith(kind + "_"):
            return kind
    return None


def cmd_build(args):
    src_root = os.path.realpath(args.src_root)
    cpp = os.path.join(src_root, "S4", "RNP", "Eigensystems.cpp")
    if variant_kind(args.variant) is None:
        sys.exit("unknown variant %r" % args.variant)
    flags, defs = VARIANTS[variant_kind(args.variant)]
    os.makedirs(args.out_dir, exist_ok=True)
    out = os.path.join(args.out_dir, "d002_%s" % args.variant)
    src_for_build = cpp
    derived = None
    if "-DD002_TEST_SEAM" in defs:
        # Seam tree: only the single file-scope DEFINITION is renamed; the three
        # call sites keep the name zhseqr_, which the driver's wrapper provides.
        raw = open(cpp, "rb").read()
        needle = b"static int zhseqr_(char job, char compz"
        if raw.count(needle) != 1:
            sys.exit("seam derivation: expected exactly one zhseqr_ definition, found %d"
                     % raw.count(needle))
        derived_bytes = raw.replace(needle, b"static int d002_inner_zhseqr_(char job, char compz")
        seam_dir = os.path.join(args.out_dir, "seam_src_%s" % args.variant)
        os.makedirs(seam_dir, exist_ok=True)
        src_for_build = os.path.join(seam_dir, "Eigensystems.cpp")
        open(src_for_build, "wb").write(derived_bytes)
        derived = {"derived_from": cpp, "derived_path": src_for_build,
                   "derived_sha256": sha256_file(src_for_build),
                   "rule": "rename the single definition zhseqr_ -> d002_inner_zhseqr_"}
    argv = (["g++"] + flags +
            ["-I", os.path.join(src_root, "S4", "RNP"), "-I", os.path.join(src_root, "S4"),
             '-DD002_SRC="%s"' % src_for_build] + defs + [DRIVER, "-o", out])
    pr = subprocess.run(argv, capture_output=True, text=True)
    rec = {"variant": args.variant, "src_root": src_root, "eigensystems": cpp,
           "eigensystems_sha256": sha256_file(cpp), "argv": argv, "exit": pr.returncode,
           "stderr": pr.stderr, "built_utc": utcnow(), "seam_derivation": derived}
    if pr.returncode == 0:
        rec["binary"] = out
        rec["binary_sha256"] = sha256_file(out)
    with open(os.path.join(args.out_dir, "BUILD_%s.json" % args.variant), "w") as fh:
        json.dump(rec, fh, indent=1, sort_keys=True)
    print("build %s exit=%d sha=%s" % (args.variant, pr.returncode, rec.get("binary_sha256", "-")))
    return pr.returncode


def write_spec(path, case, matrix_file, variant):
    lines = ["case_id %s" % case["case_id"], "entry %s" % case["entry"],
             "matrix %s" % case["matrix"], "matrix_file %s" % matrix_file,
             "variant %s" % variant]
    if case["entry"] == "API":
        n = case.get("_n")
        lines += ["want %s" % case["want"], "work_mode %s" % case["work_mode"],
                  "rwork_mode %s" % case["rwork_mode"],
                  "seam_mode %s" % case.get("seam_mode", 0),
                  "seam_info %s" % case.get("seam_info", 0),
                  "ldvl %d" % (case.get("ldvl") or n), "ldvr %d" % (case.get("ldvr") or n)]
    else:
        lines += ["side %s" % case["side"], "job %s" % case["job"],
                  "m %d" % case["m"], "ldv %d" % case["ldv"]]
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_matrix_file(path, mid, mats):
    m = mats["matrices"][mid]
    lines = ["matrix %s" % mid, "%d %d" % (m["n"], m["lda"])]
    for v in m["values"]:
        lines.append("%s %s" % (v[0], v[1]))
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_json_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, sort_keys=True)
    os.replace(tmp, path)


def select_cases(plan, cases_arg):
    """Return (selected ids in plan order, scope).  Unknown or repeated ids are refused."""
    plan_ids = [c["case_id"] for c in plan["cases"]]
    if cases_arg in (None, "all"):
        return plan_ids, "full"
    wanted = [x.strip() for x in cases_arg.split(",")]
    if any(not x for x in wanted):
        sys.exit("--cases contains an empty id")
    if len(set(wanted)) != len(wanted):
        sys.exit("--cases contains a repeated id")
    unknown = [x for x in wanted if x not in plan_ids]
    if unknown:
        sys.exit("--cases contains unknown ids: %s" % ",".join(unknown))
    return [x for x in plan_ids if x in set(wanted)], "subset"


def cmd_run(args):
    plan = load_plan()
    mats = load_matrices()
    selected, scope = select_cases(plan, args.cases)
    run_dir = os.path.realpath(args.run_dir)
    vdir = os.path.join(run_dir, args.variant)
    if os.path.exists(os.path.join(vdir, "RUN_INDEX.json")):
        sys.exit("refusing to overwrite an existing run: %s" % vdir)
    for sub in ("specs", "outs", "matrices"):
        os.makedirs(os.path.join(vdir, sub), exist_ok=True)
    cases_by_id = {c["case_id"]: c for c in plan["cases"]}
    summary = []
    for cid in selected:
        case = dict(cases_by_id[cid])
        mid = case["matrix"]
        mfile = os.path.join(vdir, "matrices", "%s.txt" % mid)
        write_matrix_file(mfile, mid, mats)
        case["_n"] = mats["matrices"][mid]["n"]
        spec = os.path.join(vdir, "specs", "%s.spec" % cid)
        out = os.path.join(vdir, "outs", "%s.out" % cid)
        err_path = os.path.join(vdir, "outs", "%s.stderr" % cid)
        so_path = os.path.join(vdir, "outs", "%s.stdout" % cid)
        write_spec(spec, case, mfile, args.variant)
        for stale in (out, err_path, so_path):
            if os.path.exists(stale):
                os.remove(stale)
        stdout = stderr = ""
        try:
            pr = subprocess.run([args.bin, spec, out], capture_output=True, text=True,
                                timeout=CASE_TIMEOUT_S, cwd=vdir)
            rc, stdout, stderr = pr.returncode, pr.stdout or "", pr.stderr or ""
        except subprocess.TimeoutExpired as exc:
            rc = "timeout"
            stdout = exc.stdout.decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        except OSError as exc:
            rc = "exec_error: %s" % exc
        with open(err_path, "w", encoding="utf-8", errors="replace") as fh:
            fh.write(stderr)
        with open(so_path, "w", encoding="utf-8", errors="replace") as fh:
            fh.write(stdout)
        summary.append({"case_id": cid, "rc": rc})
    index = {"schema": SCHEMA, "variant": args.variant, "scope": scope,
             "expected_case_ids": selected, "bin": args.bin,
             "bin_sha256": sha256_file(args.bin) if os.path.isfile(args.bin) else None,
             "run_utc": utcnow(), "cases": summary}
    write_json_atomic(os.path.join(vdir, "RUN_INDEX.json"), index)
    print("run %s: %d cases executed (scope=%s)" % (args.variant, len(summary), scope))
    return 0


# ----------------------------------------------------------------- parsing

def int_strict(s, what):
    if not INT_RE.match(s):
        raise Reject("%s: not an integer %r" % (what, s[:40]))
    return int(s)


def float_strict(s, what):
    if NONFINITE_RE.match(s):
        raise Reject("%s: non-finite value %r" % (what, s[:40]))
    if not FLOAT_RE.match(s):
        raise Reject("%s: malformed number %r" % (what, s[:40]))
    v = float(s)
    if not math.isfinite(v):
        raise Reject("%s: non-finite value %r" % (what, s[:40]))
    return v


def split_partial(text):
    """An abnormal exit may stop anywhere.  Returns (complete lines, unterminated tail)."""
    cut = text.rfind("\n") + 1
    return text[:cut], text[cut:]


def parse_output(text):
    """Strict grammar of complete output lines.  Returns (scalars, vec, scale, last_key).

    The caller decides what a complete record is: a normal exit must end with driver_rc, an
    abnormal exit passes only the complete lines given by split_partial.  Empty text is an
    empty record here.
    """
    scalars = {}
    vec = {k: [] for k in VEC_KEYS}
    scale = None
    last_key = None
    lines = text[:-1].split("\n") if text else []
    for lineno, line in enumerate(lines, 1):
        parts = line.split(" ")
        key = parts[0]
        last_key = key
        if key in VEC_KEYS:
            if len(parts) != 4:
                raise Reject("line %d: %s record has %d fields, expected 4" % (lineno, key, len(parts)))
            idx = int_strict(parts[1], "line %d index" % lineno)
            vec[key].append((idx, complex(float_strict(parts[2], key + " re"),
                                          float_strict(parts[3], key + " im"))))
        elif key == "scale":
            if scale is not None:
                raise Reject("duplicate scale record")
            vals = parts[1:]
            if vals == [""]:
                vals = []
            scale = [float_strict(v, "scale") for v in vals]
        elif key in SCALAR_KEYS and len(parts) == 2 and parts[1] != "":
            if key in scalars:
                raise Reject("duplicate scalar record %s" % key)
            scalars[key] = parts[1]
        elif key == "error" and len(parts) >= 2:
            scalars["error"] = " ".join(parts[1:])
        else:
            raise Reject("line %d: unexpected record %r" % (lineno, line[:60]))
    return scalars, vec, scale, last_key


def need(sc, key):
    if key not in sc:
        raise Reject("missing record %s" % key)
    return sc[key]


def expect_str(sc, key, want):
    got = need(sc, key)
    if got != want:
        raise Reject("%s=%s, expected %s" % (key, got, want))


def expect_int(sc, key, want):
    got = int_strict(need(sc, key), key)
    if got != want:
        raise Reject("%s=%d, expected %d" % (key, got, want))
    return got


def expect_float(sc, key):
    return float_strict(need(sc, key), key)


def index_set(records, cap, what):
    """Records must be exactly the indices 0..cap-1, each once.  Returns idx -> value."""
    seen = {}
    for idx, z in records:
        if idx < 0 or idx >= cap:
            raise Reject("%s index %d out of range [0,%d)" % (what, idx, cap))
        if idx in seen:
            raise Reject("%s duplicate index %d" % (what, idx))
        seen[idx] = z
    if len(seen) != cap:
        missing = [i for i in range(cap) if i not in seen][:5]
        raise Reject("%s has %d records, expected %d (missing e.g. %s)" % (what, len(seen), cap, missing))
    return seen


def expect_no_records(vec, keys, where):
    """Buffers that a case kind does not use must carry no record at all."""
    for key in keys:
        if vec[key]:
            raise Reject("%s has %d records, expected none in a %s" % (key, len(vec[key]), where))


def check_eigs(w_vals, ref_vals, tol):
    ref = [complex(float(a), float(b)) for a, b in ref_vals]
    scale = max([abs(z) for z in ref] + [1e-300])
    left = list(w_vals)
    worst = 0.0
    for r in ref:
        best = min(range(len(left)), key=lambda k: abs(left[k] - r))
        worst = max(worst, abs(left[best] - r) / scale)
        del left[best]
    return worst <= tol, worst


def check_vectors(arr, n, ld, w, A, side, tol_res, tol_norm):
    """arr: idx -> value, complete for the column-major buffer with leading dimension ld."""
    if n == 0:
        return True, 0.0, 0.0
    amax = max(abs(A[i][j]) for i in range(n) for j in range(n)) or 1e-300
    worst_res = 0.0
    worst_norm = 0.0
    for j in range(n):
        v = [arr[i + j * ld] for i in range(n)]
        nv = math.sqrt(sum(abs(x) ** 2 for x in v))
        worst_norm = max(worst_norm, abs(nv - 1.0))
        lam = w[j]
        if side == "R":
            r = [sum(A[i][k] * v[k] for k in range(n)) - lam * v[i] for i in range(n)]
        else:
            r = [sum(A[k][i].conjugate() * v[k] for k in range(n)) - lam.conjugate() * v[i]
                 for i in range(n)]
        worst_res = max(worst_res, max(abs(x) for x in r) / (amax * max(nv, 1e-300)))
    return (worst_res <= tol_res and worst_norm <= tol_norm), worst_res, worst_norm


def check_padding(arr, n, ld, init):
    """Rows n..ld-1 of every column are padding; they must keep the initial value."""
    want = complex(init[0], init[1])
    for idx, z in arr.items():
        if idx % ld >= n and z != want:
            raise Reject("padding element %d changed to %r" % (idx, z))


def lapack_helper_model(n, ilo, ihi, scale, side, job, v_init, m, ldv):
    """Independent 1-based zgebak model of RNP's convention: scaling, then permutation.

    scale is 1-based (scale[0] unused).  Returns V as a list of n rows, m columns each.
    """
    V = [[v_init(i) for _ in range(m)] for i in range(n)]
    if ilo != ihi and job in ("S", "B"):
        for i in range(ilo, ihi + 1):
            f = scale[i] if side == "R" else 1.0 / scale[i]
            V[i - 1] = [x * f for x in V[i - 1]]
    if job in ("P", "B"):
        for ii in range(1, n + 1):
            i = ii
            if ilo <= i <= ihi:
                continue
            if i < ilo:
                i = ilo - ii
            k = int(scale[i])
            if k != i:
                V[i - 1], V[k - 1] = V[k - 1], V[i - 1]
    return V


# ----------------------------------------------------------------- judging

def api_caps(case, n, lda):
    """Expected reported layout and buffer capacities of an API case."""
    want = case["want"]
    ldvl = max(case.get("ldvl") or n, n)
    ldvr = max(case.get("ldvr") or n, n)
    wmode, rmode = case["work_mode"], case["rwork_mode"]
    if wmode == "exact":
        lw, wcap = str(2 * n), 2 * n
    elif wmode == "short":
        lw, wcap = str(2 * n - 1), 2 * n - 1
    elif wmode == "query":
        lw, wcap = "SIZE_MAX", 8
    elif wmode == "null_lwork":
        lw, wcap = str(2 * n), 0
    else:
        lw, wcap = "0", 0
    if rmode == "exact":
        rcap = 2 * n
    elif rmode == "short":
        rcap = n
    else:
        rcap = 0
    vl_cap = n * ldvl if want in ("vl", "both") else 0
    vr_cap = n * ldvr if want in ("vr", "both") else 0
    return {"ldvl": ldvl, "ldvr": ldvr, "lwork_passed": lw, "work_mode": wmode,
            "rwork_mode": rmode, "want": want, "a_capacity_elems": n * lda,
            "vl_capacity_elems": vl_cap, "vr_capacity_elems": vr_cap,
            "work_capacity_elems": wcap, "rwork_capacity_elems": rcap,
            "w_cap": n, "work0_cap": 1 if wmode == "query" else 0}


def check_scale_producer(ilo, ihi, scale, n):
    """zgebal convention: scale[i] for i outside [ilo,ihi] is a permutation partner in 1..n;
    inside the active interval it is a positive finite scaling factor."""
    if not (1 <= ilo <= n + 1 and ilo - 1 <= ihi <= n):
        raise Reject("ilo=%d ihi=%d outside the zgebal range for n=%d" % (ilo, ihi, n))
    if len(scale) != n:
        raise Reject("scale has %d values, expected %d" % (len(scale), n))
    for i in range(1, n + 1):
        v = scale[i - 1]
        if ilo <= i <= ihi:
            if not v > 0.0:
                raise Reject("scale[%d]=%r is not a positive scaling factor" % (i, v))
        else:
            if v != int(v) or not (1 <= int(v) <= n):
                raise Reject("scale[%d]=%r is not a permutation index in 1..%d" % (i, v, n))


def process_status(rc):
    """'zero', 'abnormal' (non-zero exit status or signal) or 'runner' (timeout, exec_error).
    Any other recorded value is not a process status: it is an invalid record."""
    if type(rc) is int:
        return "zero" if rc == 0 else "abnormal"
    if rc == "timeout" or (type(rc) is str and rc.startswith("exec_error: ")):
        return "runner"
    raise Reject("rc %r is not a process status" % (rc,), "evidence")


def abnormal_mechanism(rc, err_text):
    """The registered mechanism that explains this abnormal exit (rules above), or None."""
    if rc == -6:
        if any(line in GLIBC_ABORT_LINES for line in err_text.splitlines()):
            return "SIGABRT with a glibc heap-check diagnostic"
    elif rc == 1:
        if ASAN_REPORT_RE.search(err_text):
            return "AddressSanitizer report"
    return None


def site_registered(variant, cid, err_text):
    """False when (variant, cid) has a registered crash site that this stderr does not show."""
    sites = REGISTERED_SITES.get((variant, cid))
    return sites is None or all(rx.search(err_text) for rx in sites)


API_LAYOUT_KEYS = ("ldvl", "ldvr", "lwork_passed", "work_mode", "rwork_mode", "want",
                   "a_capacity_elems", "vl_capacity_elems", "vr_capacity_elems",
                   "work_capacity_elems", "rwork_capacity_elems")


def identity_expectations(case, variant, n, lda):
    """The value that every identity, seam-state or layout record must have when it is present.

    These are the records the normal-exit check requires for a complete record; here they are
    checked wherever the record carries them, so that a crash record cannot contradict the case.
    Keys that the record does not carry are not required (partial or crash records).
    """
    exp = {"case_id": case["case_id"], "entry": case["entry"], "matrix": case["matrix"],
           "variant": variant, "n": n, "lda": lda}
    if "seam" in variant:
        exp["seam_enabled"] = "1"
        exp["seam_mode_used"] = int(case.get("seam_mode", 0))
        exp["seam_forced_info"] = int(case.get("seam_info", 0))
    else:
        exp["seam_enabled"] = "0"
    if case["entry"] == "API":
        caps = api_caps(case, n, lda)
        exp.update((key, caps[key]) for key in API_LAYOUT_KEYS)
    elif case["entry"] == "HELPER_GEBAK":
        ldv = max(case["ldv"], n)
        exp.update({"side": case["side"], "job": case["job"], "m": case["m"], "ldv": ldv,
                    "v_capacity_elems": max(n, 1) * ldv})
    return exp


def same_identity(got, want):
    """Integers are compared as the driver prints them (decimal); everything else as text."""
    if isinstance(want, int):
        return INT_RE.match(got) is not None and int(got) == want
    return got == want


def check_identity(sc, case, variant, n, lda):
    """Each identity, seam or layout record that is present must match this case."""
    for key, want in identity_expectations(case, variant, n, lda).items():
        if key in sc and not same_identity(sc[key], want):
            raise Reject("%s=%s, expected %s" % (key, sc[key], want))
    if "seam" not in variant:
        for key in SEAM_KEYS:
            if key in sc:
                raise Reject("seam record %s present in a non-seam variant" % key)


def check_partial_tail(tail, case, variant, n, lda):
    """The unterminated last line of an abnormal record, judged only as far as it goes.

    A value that is a prefix of the expected value may be a record cut short, so it is accepted.
    Any other value is a wrong identity even though the line is incomplete.
    """
    parts = tail.split(" ", 1)
    if len(parts) < 2:
        return
    key, got = parts
    exp = identity_expectations(case, variant, n, lda)
    if key in exp and not str(exp[key]).startswith(got):
        raise Reject("%s=%s, expected %s" % (key, got, exp[key]))
    if "seam" not in variant and key in SEAM_KEYS:
        raise Reject("seam record %s present in a non-seam variant" % key)


def verify_integrity(case, variant, n, lda, rc, out_text, err_text, stdout_text, schema):
    """Process, grammar and identity checks.  Returns the parsed bundle.

    The recorded process status decides how strict the record check is (see the module
    docstring): a normal exit needs a complete record; an abnormal exit needs only that the
    record present is consistent and that the exit is a registered mechanism.
    """
    cid = case["case_id"]
    status = process_status(rc)
    if status == "runner":
        raise Reject("runner failure rc=%r" % (rc,), "runner")
    if status == "abnormal":
        complete, tail = split_partial(out_text)
        sc, _, _, _ = parse_output(complete)
        check_identity(sc, case, variant, n, lda)
        check_partial_tail(tail, case, variant, n, lda)
        if "error" in sc:
            raise Reject("driver error: %s" % sc["error"], "driver")
        if sc.get("driver_rc", "0") != "0":
            raise Reject("driver_rc=%s" % sc["driver_rc"], "driver")
        mech = abnormal_mechanism(rc, err_text)
        if mech is None:
            raise Reject("abnormal exit rc=%d is not a registered mechanism" % rc, "exit_unknown")
        if not site_registered(variant, cid, err_text):
            raise Reject("abnormal exit rc=%d (%s) is not at the registered site of %s"
                         % (rc, mech, cid), "exit_unknown")
        raise Reject("abnormal exit rc=%d (%s)" % (rc, mech), "exit")
    if schema >= 2 and stdout_text != "":
        raise Reject("unexpected stdout output")
    if out_text == "":
        raise Reject("empty output file")
    if not out_text.endswith("\n"):
        raise Reject("output does not end with a newline (truncated record)")
    sc, vec, scale, last_key = parse_output(out_text)
    if "error" in sc:
        raise Reject("driver error: %s" % sc["error"], "driver")
    if scale is None:
        raise Reject("missing scale record")
    if last_key != "driver_rc":
        raise Reject("output truncated: last record is %s, not driver_rc" % last_key)
    if sc.get("driver_rc") != "0":
        raise Reject("driver_rc=%s" % sc.get("driver_rc"), "driver")
    expect_str(sc, "case_id", cid)
    expect_str(sc, "entry", case["entry"])
    expect_str(sc, "matrix", case["matrix"])
    expect_str(sc, "variant", variant)
    expect_int(sc, "n", n)
    expect_int(sc, "lda", lda)
    if int_strict(need(sc, "pid"), "pid") < 1:
        raise Reject("pid is not a positive process id")
    for key in ("anrm", "cscale", "smlnum", "bignum"):
        if expect_float(sc, key) < 0.0:
            raise Reject("%s is negative" % key)
    if expect_float(sc, "smlnum") <= 0.0 or expect_float(sc, "bignum") <= 0.0:
        raise Reject("non-positive smlnum/bignum")
    if need(sc, "scalea") not in ("0", "1"):
        raise Reject("scalea must be 0 or 1")
    ilo = int_strict(need(sc, "ilo_1based"), "ilo_1based")
    ihi = int_strict(need(sc, "ihi_1based"), "ihi_1based")
    check_scale_producer(ilo, ihi, scale, n)

    seam_variant = "seam" in variant
    if seam_variant:
        expect_str(sc, "seam_enabled", "1")
        expect_int(sc, "seam_mode_used", int(case.get("seam_mode", 0)))
        expect_int(sc, "seam_forced_info", int(case.get("seam_info", 0)))
        for key in SEAM_KEYS[2:]:
            int_strict(need(sc, key), key)
    else:
        expect_str(sc, "seam_enabled", "0")
        for key in SEAM_KEYS:
            if key in sc:
                raise Reject("seam record %s present in a non-seam variant" % key)

    entry = case["entry"]
    info = None
    if entry == "API":
        for key in API_KEYS:
            need(sc, key)
        caps = api_caps(case, n, lda)
        expect_str(sc, "lwork_passed", caps["lwork_passed"])
        expect_str(sc, "work_mode", caps["work_mode"])
        expect_str(sc, "rwork_mode", caps["rwork_mode"])
        expect_str(sc, "want", caps["want"])
        expect_int(sc, "ldvl", caps["ldvl"])
        expect_int(sc, "ldvr", caps["ldvr"])
        expect_int(sc, "a_capacity_elems", caps["a_capacity_elems"])
        expect_int(sc, "vl_capacity_elems", caps["vl_capacity_elems"])
        expect_int(sc, "vr_capacity_elems", caps["vr_capacity_elems"])
        expect_int(sc, "work_capacity_elems", caps["work_capacity_elems"])
        expect_int(sc, "rwork_capacity_elems", caps["rwork_capacity_elems"])
        expect_float(sc, "elapsed_s")
        info = int_strict(need(sc, "info"), "info")
        for key in ("side", "job", "m", "ldv", "v_capacity_elems"):
            if key in sc:
                raise Reject("helper record %s in an API case" % key)
        expect_no_records(vec, ("v_flat",), "API case")
        index_sets = {
            "w": index_set(vec["w"], caps["w_cap"], "w"),
            "vl_flat": index_set(vec["vl_flat"], caps["vl_capacity_elems"], "vl_flat"),
            "vr_flat": index_set(vec["vr_flat"], caps["vr_capacity_elems"], "vr_flat"),
            "work0": index_set(vec["work0"], caps["work0_cap"], "work0"),
        }
        if caps["work0_cap"] and index_sets["work0"][0] != complex(2 * n, 0):
            raise Reject("work0 = %r, expected exactly 2n = %d" % (index_sets["work0"][0], 2 * n))
    elif entry == "HELPER_GEBAK":
        for key in HELPER_KEYS:
            need(sc, key)
        side, job = case["side"], case["job"]
        m, ldv = case["m"], max(case["ldv"], n)
        expect_str(sc, "side", side)
        expect_str(sc, "job", job)
        expect_int(sc, "m", m)
        expect_int(sc, "ldv", ldv)
        v_cap = max(n, 1) * ldv
        expect_int(sc, "v_capacity_elems", v_cap)
        index_sets = {"v_flat": index_set(vec["v_flat"], v_cap, "v_flat")}
        expect_no_records(vec, ("w", "vl_flat", "vr_flat", "work0"), "helper case")
        for key in API_KEYS:
            if key in sc:
                raise Reject("API record %s in a helper case" % key)
    else:
        raise Reject("unknown entry %s" % entry)
    # A sanitizer line on a normal exit is the registered UBSan mechanism only when the record it
    # came with is complete and consistent, as checked above, and every such line is a registered
    # report form.  A damaged record is evidence; any other sanitizer text is not a defect.
    marker_lines = [ln for ln in (err_text + "\n" + stdout_text).splitlines()
                    if any(mk in ln for mk in SANITIZER_MARKERS)]
    if marker_lines:
        unsupported = [ln for ln in marker_lines if not UBSAN_REPORT_RE.match(ln)]
        if unsupported:
            raise Reject("unsupported sanitizer report: %r" % unsupported[0][:80],
                         "unsupported_sanitizer")
        marks = [mk for mk in SANITIZER_MARKERS if any(mk in ln for ln in marker_lines)]
        raise Reject("sanitizer report: %s" % ",".join(marks), "sanitizer")
    return {"sc": sc, "vec": vec, "scale": scale, "ilo": ilo, "ihi": ihi,
            "index_sets": index_sets, "info": info}


def verdict(case, variant, mats, th, bundle, n):
    """Pass/fail judgement of an integrity-clean, applicable case.  Returns detail text."""
    sc = bundle["sc"]
    entry = case["entry"]
    seam_mode = int(case.get("seam_mode", 0))
    if entry == "HELPER_GEBAK":
        return judge_helper(case, bundle, n)
    info = int(bundle["info"])
    if seam_mode != 0 and "seam" in variant:
        exp_info = int(case.get("seam_info", 0))
        if info != exp_info or sc["seam_last_real_info"] != "0":
            raise Reject("info=%d forced=%d seam_last_real=%s" % (info, exp_info, sc["seam_last_real_info"]))
        return "info=%d forced=%d real_last=0" % (info, exp_info)
    if case["work_mode"] == "query":
        if info != 0:
            raise Reject("info=%d, expected 0" % info)
        return "info=0 work0=2n"
    if info != 0:
        raise Reject("info=%d, expected 0" % info)
    caps = api_caps(case, n, mats_lda(mats, case))
    if "seam" in variant and case["case_id"] == "C-03":
        if sc["seam_onlyvalues_real_info"] != "0":
            raise Reject("seam_onlyvalues_real_info=%s, expected 0" % sc["seam_onlyvalues_real_info"])
    ref = mats["eigenvalue_reference"][case["matrix"]]["values"]
    A, _, _ = matrix_of(mats, case["matrix"])
    idx = bundle["index_sets"]
    w_vals = [idx["w"][i] for i in range(n)]
    ok_e, err_e = check_eigs(w_vals, ref, th["eig_rel_tol"])
    detail = "info=%d eig_rel_err=%.3g" % (info, err_e)
    failures = []
    if not ok_e:
        failures.append("eigenvalue error %.3g > %g" % (err_e, th["eig_rel_tol"]))
    want = case["want"]
    init = th["padding_init_value"]
    if want in ("vr", "both"):
        check_padding(idx["vr_flat"], n, caps["ldvr"], init)
        ok_r, rr, rn = check_vectors(idx["vr_flat"], n, caps["ldvr"], w_vals, A, "R",
                                     th["residual_tol"], th["vector_norm_tol"])
        detail += " vr_res=%.3g vr_norm_err=%.3g" % (rr, rn)
        if not ok_r:
            failures.append("right vectors residual %.3g / norm %.3g" % (rr, rn))
    if want in ("vl", "both"):
        check_padding(idx["vl_flat"], n, caps["ldvl"], init)
        ok_l, lr, ln = check_vectors(idx["vl_flat"], n, caps["ldvl"], w_vals, A, "L",
                                     th["residual_tol"], th["vector_norm_tol"])
        detail += " vl_res=%.3g vl_norm_err=%.3g" % (lr, ln)
        if not ok_l:
            failures.append("left vectors residual %.3g / norm %.3g" % (lr, ln))
    if failures:
        raise Reject("; ".join(failures) + " [" + detail + "]")
    return detail


def judge_helper(case, bundle, n):
    scale = [0.0] + bundle["scale"]
    ilo, ihi = bundle["ilo"], bundle["ihi"]
    m = case["m"]
    ldv = max(case["ldv"], n)
    got = bundle["index_sets"]["v_flat"]
    ref_V = lapack_helper_model(n, ilo, ihi, scale, case["side"], case["job"],
                                lambda i: 1000.0 + i, m, ldv)
    worst = 0.0
    for idx in range(max(n, 1) * ldv):
        col, row = divmod(idx, ldv)
        if row < n and col < m:
            expect = complex(ref_V[row][col], 0.0)
        else:
            expect = complex(-777.0, 0.0)
        g = got[idx]
        rel = abs(g - expect) / max(1.0, abs(expect))
        if rel > worst:
            worst = rel
        if rel > 1e-12:
            raise Reject("v_flat[%d]=%r expected %r (rel %.3g)" % (idx, g, expect, rel))
    return "max_rel_err=%.3g" % worst


def mats_lda(mats, case):
    return mats["matrices"][case["matrix"]]["lda"]


def judge_case(case, variant, mats, th, rc, out_text, err_text, stdout_text, schema):
    cid = case["case_id"]
    n = mats["matrices"][case["matrix"]]["n"]
    seam_variant = "seam" in variant
    seam_mode = int(case.get("seam_mode", 0))
    applicable = seam_variant or seam_mode == 0
    probe = cid in CONTRACT_PROBES
    rec = {"case_id": cid, "entry": case["entry"], "matrix": case["matrix"],
           "group": case["group"], "rc": rc, "status": "judged", "pass": False,
           "detail": "", "integrity": "ok", "integrity_kind": "ok"}
    bundle = None
    try:
        bundle = verify_integrity(case, variant, n, mats_lda(mats, case), rc, out_text, err_text,
                                  stdout_text, schema)
    except Reject as exc:
        rec["integrity"] = str(exc)
        rec["integrity_kind"] = exc.kind
    if probe:
        rec["status"] = "recorded"
        rec["pass"] = None
        rec["detail"] = "contract probe; rc=%s sanitizer=%s integrity=%s" % (
            rc, ",".join(m for m in SANITIZER_MARKERS if m in err_text) or "none", rec["integrity"])
        return rec
    if not applicable:
        rec["status"] = "not_applicable"
        rec["pass"] = None
        rec["detail"] = "seam case; this build has no seam (integrity=%s)" % rec["integrity"]
        return rec
    if bundle is None:
        rec["detail"] = "integrity: " + rec["integrity"]
        return rec
    try:
        rec["detail"] = verdict(case, variant, mats, th, bundle, n)
        rec["pass"] = True
    except Reject as exc:
        rec["detail"] = str(exc)
    return rec


def shows_defect(rec):
    """The registered defect is visible in this record: the case was judged failing, and its
    evidence is complete and either a verdict failure or a registered defect mechanism."""
    return (rec is not None and rec["status"] == "judged" and rec["pass"] is False
            and rec["integrity_kind"] in ("ok",) + DEFECT_KINDS)


def check_signature(variant, results):
    """For a baseline variant: do the defect cases show the defect, the controls pass, and is
    no case of the signature damaged?  None for other variants.

    A damaged record (missing file, malformed or truncated output, wrong identity, driver
    error) never counts as a reproduced defect, whatever the case's classification.
    """
    if variant not in BASELINE_SIGNATURE:
        return None
    sig = BASELINE_SIGNATURE[variant]
    by_id = {r["case_id"]: r for r in results}
    not_failing = [c for c in sig["must_fail"] if not shows_defect(by_id.get(c))]
    not_passing = [c for c in sig["must_pass"] if by_id.get(c, {}).get("pass") is not True]
    damaged = [c for c in sig["must_fail"] + sig["may_fail"] + sig["must_pass"]
               if c in by_id and by_id[c]["integrity_kind"] not in ("ok",) + DEFECT_KINDS]
    return {"must_fail": sig["must_fail"], "may_fail": sig["may_fail"],
            "must_pass": sig["must_pass"],
            "not_failing": not_failing, "not_passing": not_passing, "damaged": damaged,
            "ok": not not_failing and not not_passing and not damaged}


def load_run(vdir, variant, plan, allow_legacy=False):
    """Validate RUN_INDEX.  Returns (index dict, expected ids, scope, schema, rc map).

    Formal judging accepts only SCHEMA.  The legacy schema-1 runs are judged only when the
    caller asks for it explicitly (allow_legacy), so that a new run cannot pass by declaring
    an older schema and dropping the records that schema 2 requires.
    """
    plan_ids = [c["case_id"] for c in plan["cases"]]
    plan_set = set(plan_ids)
    path = os.path.join(vdir, "RUN_INDEX.json")
    try:
        with open(path, encoding="utf-8") as fh:
            idx = json.load(fh)
    except (OSError, ValueError) as exc:
        raise RunFatal("RUN_INDEX unreadable: %s" % exc)
    if not isinstance(idx, dict):
        raise RunFatal("RUN_INDEX is not an object")
    if idx.get("variant") != variant:
        raise RunFatal("RUN_INDEX variant %r does not match %r" % (idx.get("variant"), variant))
    # The legacy runs predate the schema field; a missing field therefore means schema 1.
    schema = idx.get("schema", LEGACY_SCHEMA)
    if schema == LEGACY_SCHEMA and allow_legacy:
        pass
    elif schema != SCHEMA:
        raise RunFatal("RUN_INDEX schema %r is not accepted here (formal schema %d%s)" % (
            schema, SCHEMA, "; legacy schema 1 needs an explicit re-judging request"
            if schema == LEGACY_SCHEMA else ""))
    scope = idx.get("scope", "full") if schema >= 2 else "full"
    if scope not in ("full", "subset"):
        raise RunFatal("unknown scope %r" % (scope,))
    cases = idx.get("cases")
    if not isinstance(cases, list):
        raise RunFatal("RUN_INDEX cases is not a list")
    rc_by_id = {}
    for ent in cases:
        if not isinstance(ent, dict) or not isinstance(ent.get("case_id"), str) or "rc" not in ent:
            raise RunFatal("malformed RUN_INDEX entry %r" % (ent,))
        cid = ent["case_id"]
        if cid not in plan_set:
            raise RunFatal("unknown case_id %s in RUN_INDEX" % cid)
        if cid in rc_by_id:
            raise RunFatal("duplicate RUN_INDEX entry %s" % cid)
        rc_by_id[cid] = ent["rc"]
    if scope == "subset":
        exp = idx.get("expected_case_ids")
        if not isinstance(exp, list) or not exp or not all(isinstance(x, str) for x in exp):
            raise RunFatal("subset run without a valid expected_case_ids list")
        if len(set(exp)) != len(exp) or not set(exp) <= plan_set:
            raise RunFatal("subset expected_case_ids repeated or unknown")
        exp = [x for x in plan_ids if x in set(exp)]
    else:
        exp = plan_ids
    if not rc_by_id:
        raise RunFatal("RUN_INDEX has no case entries")
    missing = [c for c in exp if c not in rc_by_id]
    if missing:
        raise RunFatal("missing RUN_INDEX entries (%d): %s" % (len(missing), ",".join(missing[:8])))
    extra = [c for c in rc_by_id if c not in set(exp)]
    if extra:
        raise RunFatal("RUN_INDEX entries outside the expected set: %s" % ",".join(extra[:8]))
    return idx, exp, scope, schema, rc_by_id


def judge_variant(run_dir, variant, plan=None, mats=None, allow_legacy=False):
    """Judge one variant's saved run.  Returns the summary dict (not written to disk)."""
    plan = plan or load_plan()
    mats = mats or load_matrices()
    th = plan["thresholds"]
    vdir = os.path.join(os.path.realpath(run_dir), variant)
    summary = {"variant": variant, "judged_utc": utcnow(), "thresholds": th,
               "integrity": "ok", "fatal": None, "complete_run": False,
               "all_judged_pass": False, "accepted": False, "results": [],
               "signature": None}
    try:
        idx, exp, scope, schema, rc_by_id = load_run(vdir, variant, plan, allow_legacy)
    except RunFatal as exc:
        summary["integrity"] = "fatal"
        summary["fatal"] = str(exc)
        return summary
    summary.update({"run_schema": schema, "scope": scope, "run_bin_sha256": idx.get("bin_sha256"),
                    "cases_expected": len(exp)})
    by_id = {c["case_id"]: c for c in plan["cases"]}
    results = []
    for cid in exp:
        case = by_id[cid]
        outs = os.path.join(vdir, "outs")
        out_path = os.path.join(outs, "%s.out" % cid)
        err_path = os.path.join(outs, "%s.stderr" % cid)
        so_path = os.path.join(outs, "%s.stdout" % cid)
        missing = [p for p in (out_path, err_path) if not os.path.isfile(p)]
        if schema >= 2 and not os.path.isfile(so_path):
            missing.append(so_path)
        if missing:
            rec = {"case_id": cid, "entry": case["entry"], "matrix": case["matrix"],
                   "group": case["group"], "rc": rc_by_id[cid], "status": "judged",
                   "pass": False, "integrity": "missing record", "integrity_kind": "missing",
                   "detail": "missing: " + ", ".join(os.path.basename(p) for p in missing)}
            if cid in CONTRACT_PROBES:
                rec["status"] = "recorded"
                rec["pass"] = None
            results.append(rec)
            continue
        out_text = read_text(out_path)
        err_text = read_text(err_path)
        stdout_text = read_text(so_path) if schema >= 2 else ""
        results.append(judge_case(case, variant, mats, th, rc_by_id[cid], out_text, err_text,
                                  stdout_text, schema))
    judged = [r for r in results if r["status"] == "judged"]
    integrity_bad = [r["case_id"] for r in results
                     if r["status"] != "recorded" and r["integrity_kind"] != "ok"]
    all_pass = bool(judged) and all(r["pass"] for r in judged) and not integrity_bad
    summary["cases_total"] = len(results)
    summary["cases_judged"] = len(judged)
    summary["cases_pass"] = sum(1 for r in judged if r["pass"])
    summary["cases_fail"] = len(judged) - summary["cases_pass"]
    summary["cases_not_applicable"] = sum(1 for r in results if r["status"] == "not_applicable")
    summary["cases_recorded_probe"] = sum(1 for r in results if r["status"] == "recorded")
    summary["integrity_failures"] = integrity_bad
    summary["integrity_kinds"] = {r["case_id"]: r["integrity_kind"] for r in results
                                  if r["case_id"] in integrity_bad}
    summary["complete_run"] = scope == "full" and len(results) == len(plan["cases"])
    summary["all_judged_pass"] = all_pass
    summary["accepted"] = summary["complete_run"] and all_pass
    summary["signature"] = check_signature(variant, results)
    summary["results"] = results
    return summary


def cmd_judge(args):
    summary = judge_variant(args.run_dir, args.variant, allow_legacy=args.allow_legacy_schema1)
    vdir = os.path.join(os.path.realpath(args.run_dir), args.variant)
    if summary["integrity"] == "fatal":
        print("judge %s: FATAL %s" % (args.variant, summary["fatal"]))
        write_json_atomic(os.path.join(vdir, "JUDGE_%s.json" % args.variant), summary)
        return 1
    write_json_atomic(os.path.join(vdir, "JUDGE_%s.json" % args.variant), summary)
    print("judge %s: scope=%s pass=%d fail=%d judged=%d not_applicable=%d probes_recorded=%d accepted=%s" % (
        args.variant, summary["scope"], summary["cases_pass"], summary["cases_fail"],
        summary["cases_judged"], summary["cases_not_applicable"], summary["cases_recorded_probe"],
        summary["accepted"]))
    for r in summary["results"]:
        if r["status"] == "judged" and not r["pass"]:
            print("  FAIL %-6s %-8s %s" % (r["case_id"], r["entry"], r["detail"]))
    if summary["integrity_failures"]:
        print("  INTEGRITY %s" % ",".join(summary["integrity_failures"]))
    if summary["signature"] is not None:
        print("  baseline signature ok=%s not_failing=%s" % (
            summary["signature"]["ok"], summary["signature"]["not_failing"]))
    return 0 if summary["all_judged_pass"] else 1


def cmd_positives(args):
    """Sanitizer positive controls: each must report its registered signature."""
    os.makedirs(args.out_dir, exist_ok=True)
    cases = [
        ("pos_asan", ["-O1", "-g", "-fsanitize=address", "-fno-omit-frame-pointer"],
         os.path.join(HERE, "tools", "pos_asan.cpp")),
        ("pos_ubsan", ["-O1", "-g", "-fsanitize=undefined", "-fno-omit-frame-pointer"],
         os.path.join(HERE, "tools", "pos_ubsan.cpp")),
        ("pos_asan_ubsan", SAN_FLAGS, os.path.join(HERE, "tools", "pos_asan.cpp")),
    ]
    results = []
    for name, flags, src in cases:
        signature = POSITIVE_SIGNATURES[name]
        exe = os.path.join(args.out_dir, name)
        pr = subprocess.run(["g++"] + flags + [src, "-o", exe], capture_output=True, text=True)
        if pr.returncode != 0:
            results.append({"control": name, "pass": False, "detail": "build failed"})
            continue
        try:
            run = subprocess.run([exe], capture_output=True, text=True, timeout=CASE_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            results.append({"control": name, "pass": False, "detail": "timeout"})
            continue
        hit = signature in run.stderr
        results.append({"control": name, "signature": signature, "exit": run.returncode,
                        "signature_seen": hit, "pass": bool(hit and run.returncode != 0 or
                                                           (name == "pos_ubsan" and hit))})
        open(os.path.join(args.out_dir, name + ".stderr"), "w").write(run.stderr)
    with open(os.path.join(args.out_dir, "POSITIVES.json"), "w") as fh:
        json.dump(results, fh, indent=1, sort_keys=True)
    ok = all(r["pass"] for r in results)
    print("positives: %s" % ("PASS" if ok else "FAIL"))
    for r in results:
        print("  %-16s pass=%s exit=%s signature_seen=%s" % (
            r["control"], r["pass"], r.get("exit"), r.get("signature_seen")))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="D002 native RNP contract runner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--src-root", required=True)
    b.add_argument("--variant", required=True)
    b.add_argument("--out-dir", required=True)
    r = sub.add_parser("run")
    r.add_argument("--variant", required=True)
    r.add_argument("--bin", required=True)
    r.add_argument("--run-dir", required=True)
    r.add_argument("--cases", default="all")
    pz = sub.add_parser("positives")
    pz.add_argument("--out-dir", required=True)
    j = sub.add_parser("judge")
    j.add_argument("--variant", required=True)
    j.add_argument("--run-dir", required=True)
    j.add_argument("--allow-legacy-schema1", action="store_true",
                   help="re-judge a legacy schema-1 run (historical data only, never acceptance)")
    args = ap.parse_args()
    if args.cmd == "build":
        return cmd_build(args)
    if args.cmd == "run":
        return cmd_run(args)
    if args.cmd == "positives":
        return cmd_positives(args)
    return cmd_judge(args)


if __name__ == "__main__":
    raise SystemExit(main())
