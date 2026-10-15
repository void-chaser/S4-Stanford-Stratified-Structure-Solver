#!/usr/bin/env python3
# verdict_m2_r8m2a3.py -- P05-S4 R8 M2a3 Section 7: formal verdict of M2 results against effective prereg.
# Reads: RESULTS_DIR (RESULTS_pass1.tsv, RESULTS_pass2.tsv), PREREG, CONTROL_MAPPING
# Writes: OUT_DIR/OUT_PREFIX_VERDICT.tsv, OUT_DIR/OUT_PREFIX_SUMMARY.txt
# Strict fact-based judging with judge_d003 (sha256 verified read-only import):
#   - Compares pass 1 and pass 2 independently against prereg;
#   - Detects MISMATCH and FLAKY separately;
#   - Checks rc1, rc2, rc3, signal, hit, class, I1..I7, san_reports;
#   - Checks for duplicate IDs, missing/extra IDs, tree mismatches;
#   - Checks missing values/evidence (cannot default to 0 or HOLD);
#   - Validates control mappings and field output dumps (if dumps_dir provided);
#   - Refuses to overwrite existing files (U17).
import argparse
import hashlib
import importlib.util
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
JUDGE_PATH = os.path.join(REPO, "testing", "d003", "judge_d003.py")
JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"

FIELDS_TO_COMPARE = [
    ("exp_rc1", "rc1"),
    ("exp_rc2", "rc2"),
    ("exp_rc3", "rc3"),
    ("exp_signal", "signal"),
    ("exp_hit", "hit"),
    ("exp_class", "class"),
    ("exp_san", "san_reports"),
] + [("exp_I%d" % i, "I%d" % i) for i in range(1, 8)]


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load_judge():
    if not os.path.isfile(JUDGE_PATH):
        raise SystemExit("verdict_m2_r8m2a3: REFUSED missing judge_d003.py")
    if sha256_file(JUDGE_PATH) != JUDGE_SHA:
        raise SystemExit("verdict_m2_r8m2a3: REFUSED judge sha256 mismatch")
    spec = importlib.util.spec_from_file_location("judge_d003", JUDGE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_tsv(path):
    with open(path, "r", encoding="utf-8") as fh:
        lines = [l.rstrip("\r\n") for l in fh if l.strip() and not l.startswith("#")]
    if not lines:
        return [], []
    head = lines[0].split("\t")
    rows = []
    for l in lines[1:]:
        f = l.split("\t")
        rows.append(dict(zip(head, f)))
    return head, rows


def rc_matches(expected, observed):
    if expected in ("", "-"):
        return True
    if expected == "NZ":
        return observed not in ("", "-", None) and int(observed) != 0
    if observed in ("", "-", None):
        return False
    return str(int(observed)) == str(int(expected))


def int_or_none(val):
    if val in ("", "-", None):
        return None
    return int(val)


def main():
    parser = argparse.ArgumentParser(description="P05-S4 R8 M2a3 Formal Verdict")
    parser.add_argument("results_dir", help="Directory with RESULTS_pass1.tsv and RESULTS_pass2.tsv")
    parser.add_argument("prereg", help="Path to effective preregistration TSV")
    parser.add_argument("control_mapping", help="Path to CONTROL_MAPPING TSV")
    parser.add_argument("out_dir", help="Output directory")
    parser.add_argument("out_prefix", help="Output file prefix")
    parser.add_argument("--dumps-dir", default=None, help="Optional directory with field dump subdirectories")

    args = parser.parse_args()

    results_dir = os.path.realpath(args.results_dir)
    prereg_path = os.path.realpath(args.prereg)
    ctrl_map_path = os.path.realpath(args.control_mapping)
    out_dir = os.path.realpath(args.out_dir)
    out_prefix = args.out_prefix

    out_v = os.path.join(out_dir, out_prefix + "_VERDICT.tsv")
    out_s = os.path.join(out_dir, out_prefix + "_SUMMARY.txt")

    if os.path.exists(out_v) or os.path.exists(out_s):
        sys.stderr.write("verdict_m2_r8m2a3: REFUSED output exists (U17): %s\n" % out_prefix)
        return 2

    judge = load_judge()

    # Read prereg
    p_head, p_rows = read_tsv(prereg_path)
    pre = {}
    for r in p_rows:
        pid = r["point_id"]
        if pid in pre:
            sys.stderr.write("verdict_m2_r8m2a3: duplicate point_id in prereg: %s\n" % pid)
            return 2
        pre[pid] = r

    # Read control mapping
    c_head, c_rows = read_tsv(ctrl_map_path)
    ctrl_map = {r["point_id"]: r for r in c_rows}

    # Read results pass 1 & 2
    p1_path = os.path.join(results_dir, "RESULTS_pass1.tsv")
    p2_path = os.path.join(results_dir, "RESULTS_pass2.tsv")
    if not os.path.isfile(p1_path) or not os.path.isfile(p2_path):
        sys.stderr.write("verdict_m2_r8m2a3: missing RESULTS_pass1.tsv or RESULTS_pass2.tsv in %s\n" % results_dir)
        return 2

    _, rows1 = read_tsv(p1_path)
    _, rows2 = read_tsv(p2_path)

    p1 = {}
    p1_dups = set()
    for r in rows1:
        pid = r.get("point_id", "")
        if pid in p1:
            p1_dups.add(pid)
        p1[pid] = r

    p2 = {}
    p2_dups = set()
    for r in rows2:
        pid = r.get("point_id", "")
        if pid in p2:
            p2_dups.add(pid)
        p2[pid] = r

    schema_errors = []
    if p1_dups:
        schema_errors.append("Duplicate point_id in pass 1: %s" % sorted(p1_dups))
    if p2_dups:
        schema_errors.append("Duplicate point_id in pass 2: %s" % sorted(p2_dups))

    p1_missing = set(pre.keys()) - set(p1.keys())
    p2_missing = set(pre.keys()) - set(p2.keys())
    p1_extra = set(p1.keys()) - set(pre.keys())
    p2_extra = set(p2.keys()) - set(pre.keys())

    if p1_missing:
        schema_errors.append("Missing point_id in pass 1: %s" % sorted(p1_missing))
    if p2_missing:
        schema_errors.append("Missing point_id in pass 2: %s" % sorted(p2_missing))
    if p1_extra:
        schema_errors.append("Extra point_id in pass 1: %s" % sorted(p1_extra))
    if p2_extra:
        schema_errors.append("Extra point_id in pass 2: %s" % sorted(p2_extra))

    # Verify control mappings valid
    for pid, cm in ctrl_map.items():
        c_pid = cm["control_point_id"]
        if c_pid != "-" and c_pid not in pre:
            schema_errors.append("Control mapping for %s points to non-existent control_point_id: %s" % (pid, c_pid))

    verdict_rows = []
    total_mismatch = 0
    total_flaky = 0
    total_match = 0
    total_schema = len(schema_errors)

    all_pids = sorted(set(pre.keys()) | set(p1.keys()) | set(p2.keys()))

    for pid in all_pids:
        e = pre.get(pid)
        r1 = p1.get(pid)
        r2 = p2.get(pid)

        point_issues = []
        if pid in p1_dups or pid in p2_dups:
            point_issues.append("DUPLICATE_ID")
        if e is None:
            point_issues.append("EXTRA_ID_NOT_IN_PREREG")
        if r1 is None:
            point_issues.append("MISSING_IN_PASS1")
        if r2 is None:
            point_issues.append("MISSING_IN_PASS2")

        if point_issues:
            verdict_rows.append([pid, "SCHEMA_ERROR", ",".join(point_issues), "-", "-"])
            continue

        # Check tree
        if r1.get("tree") != e["tree"]:
            point_issues.append("TREE_MISMATCH_PASS1(%s!=%s)" % (r1.get("tree"), e["tree"]))
        if r2.get("tree") != e["tree"]:
            point_issues.append("TREE_MISMATCH_PASS2(%s!=%s)" % (r2.get("tree"), e["tree"]))

        if point_issues:
            verdict_rows.append([pid, "SCHEMA_ERROR", ",".join(point_issues), "-", "-"])
            continue

        # Classify independently using judge_d003
        is_ctrl = (e.get("control_group") == "YES" or e.get("exp_class") == "CONTROL_OK")
        c1, _, _ = judge.classify(int_or_none(r1.get("rc")), int_or_none(r1.get("rc1")), int_or_none(r1.get("rc2")),
                                  int_or_none(r1.get("hit", 0)), control=is_ctrl)
        c2, _, _ = judge.classify(int_or_none(r2.get("rc")), int_or_none(r2.get("rc1")), int_or_none(r2.get("rc2")),
                                  int_or_none(r2.get("hit", 0)), control=is_ctrl)

        # Build observed dicts
        obs1 = {
            "rc1": r1.get("rc1", ""),
            "rc2": r1.get("rc2", ""),
            "rc3": r1.get("rc3", ""),
            "signal": r1.get("signal", ""),
            "hit": r1.get("hit", ""),
            "class": c1,
            "san_reports": r1.get("san_reports", ""),
        }
        obs2 = {
            "rc1": r2.get("rc1", ""),
            "rc2": r2.get("rc2", ""),
            "rc3": r2.get("rc3", ""),
            "signal": r2.get("signal", ""),
            "hit": r2.get("hit", ""),
            "class": c2,
            "san_reports": r2.get("san_reports", ""),
        }
        for i in range(1, 8):
            obs1["I%d" % i] = r1.get("I%d" % i, "")
            obs2["I%d" % i] = r2.get("I%d" % i, "")

        # Check missing gdb state for dbg points expecting HOLD
        if e.get("gdb_script") not in ("", "-"):
            for inv_k in ("I1", "I2", "I4", "I5", "I6"):
                if e.get("exp_" + inv_k) == "HOLD":
                    if obs1[inv_k] in ("", "-", None):
                        point_issues.append("MISSING_GDB_STATE_PASS1(%s)" % inv_k)
                    if obs2[inv_k] in ("", "-", None):
                        point_issues.append("MISSING_GDB_STATE_PASS2(%s)" % inv_k)

        if point_issues:
            verdict_rows.append([pid, "SCHEMA_ERROR", ",".join(point_issues), "-", "-"])
            continue

        # Check field output dumps if requested
        if args.dumps_dir and pid in ctrl_map:
            cm = ctrl_map[pid]
            t_call = cm["test_output_call"]
            c_pid = cm["control_point_id"]
            c_call = cm["control_output_call"]
            if t_call not in ("", "-") and c_pid not in ("", "-") and c_call not in ("", "-"):
                for p_idx, d_name in enumerate(["pass1", "pass2"], start=1):
                    p_test = os.path.join(args.dumps_dir, d_name, pid, "call%s.txt" % t_call)
                    p_ctrl = os.path.join(args.dumps_dir, d_name, c_pid, "call%s.txt" % c_call)
                    if not os.path.isfile(p_test):
                        point_issues.append("MISSING_TEST_DUMP_%s(call%s.txt)" % (d_name, t_call))
                    elif not os.path.isfile(p_ctrl):
                        point_issues.append("MISSING_CTRL_DUMP_%s(call%s.txt)" % (d_name, c_call))
                    else:
                        with open(p_test, "rb") as fh:
                            b_t = fh.read()
                        with open(p_ctrl, "rb") as fh:
                            b_c = fh.read()
                        if b_t != b_c:
                            point_issues.append("OUTPUT_DIFF_%s(call%s!=call%s)" % (d_name, t_call, c_call))

        if point_issues:
            verdict_rows.append([pid, "SCHEMA_ERROR", ",".join(point_issues), "-", "-"])
            continue

        # Compare pass 1 against expectation
        mismatches1 = []
        for exp_f, obs_f in FIELDS_TO_COMPARE:
            exp_val = e.get(exp_f, "-")
            if exp_val in ("", "-"):
                continue
            obs_val = obs1.get(obs_f, "")
            if exp_f in ("exp_rc1", "exp_rc2", "exp_rc3"):
                if not rc_matches(exp_val, obs_val):
                    mismatches1.append(exp_f)
            else:
                if str(obs_val) != str(exp_val):
                    mismatches1.append(exp_f)

        # Compare pass 2 against expectation
        mismatches2 = []
        for exp_f, obs_f in FIELDS_TO_COMPARE:
            exp_val = e.get(exp_f, "-")
            if exp_val in ("", "-"):
                continue
            obs_val = obs2.get(obs_f, "")
            if exp_f in ("exp_rc1", "exp_rc2", "exp_rc3"):
                if not rc_matches(exp_val, obs_val):
                    mismatches2.append(exp_f)
            else:
                if str(obs_val) != str(exp_val):
                    mismatches2.append(exp_f)

        # Compare pass 1 against pass 2 for flaky detection
        flaky_fields = []
        for exp_f, obs_f in FIELDS_TO_COMPARE:
            exp_val = e.get(exp_f, "-")
            if exp_val in ("", "-"):
                continue
            if obs1.get(obs_f) != obs2.get(obs_f):
                flaky_fields.append(obs_f)

        all_mismatch = sorted(set(mismatches1) | set(mismatches2))
        if all_mismatch:
            total_mismatch += 1
        if flaky_fields:
            total_flaky += 1

        if all_mismatch and flaky_fields:
            v_label = "MISMATCH_AND_FLAKY"
        elif all_mismatch:
            v_label = "MISMATCH"
        elif flaky_fields:
            v_label = "FLAKY"
        else:
            v_label = "MATCH"
            total_match += 1

        verdict_rows.append([
            pid,
            v_label,
            ",".join(all_mismatch) if all_mismatch else "-",
            ",".join(flaky_fields) if flaky_fields else "-",
            "p1_diffs=%s;p2_diffs=%s" % (",".join(mismatches1) or "none", ",".join(mismatches2) or "none")
        ])

    os.makedirs(out_dir, exist_ok=True)
    with open(out_v, "x", encoding="utf-8") as fh:
        fh.write("point_id\tverdict\tmismatch_fields\tflaky_fields\tdetail\n")
        for r in verdict_rows:
            fh.write("\t".join(r) + "\n")

    summary_lines = [
        "VERDICT_M2 points=%d MATCH=%d MISMATCH=%d FLAKY=%d SCHEMA_ERRORS=%d" % (
            len(pre), total_match, total_mismatch, total_flaky, total_schema
        ),
        "judge_sha256=%s" % JUDGE_SHA,
        "prereg=%s" % prereg_path,
        "control_mapping=%s" % ctrl_map_path,
        "results_dir=%s" % results_dir,
    ]
    if schema_errors:
        summary_lines.append("SCHEMA_ERROR_DETAILS:")
        for se in schema_errors:
            summary_lines.append("  - " + se)

    with open(out_s, "x", encoding="utf-8") as fh:
        fh.write("\n".join(summary_lines) + "\n")

    print(summary_lines[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
