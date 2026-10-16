#!/usr/bin/env python3
# verdict_m2_r8m2d.py -- P05-S4 R8 M2d verdict engine v5.
# Enhancements:
#  - exp="-" does not judge (skips comparison for that column)
#  - Adds strict equality for exp_crash_call in {1, 2, 3, NONE}
#  - Adds strict equality for exp_crash_site (supporting normalized compare for [源码]推断)
#  - Adds strict equality for exp_post_call1_solution in {NULL, NONNULL}
#  - Retains all v4 rules (INIT_CLEAN, SAN_CRASH, NATIVE_FAIL_CONTROL, BASELINE_ONLY, SUPERSEDED_BY, etc.)
#  - Strict priority: GDB_DIVERGENT > MISMATCH > FLAKY > UNJUDGED_MISSING > UNJUDGED_BY_DESIGN > MATCH
import argparse
import csv
import os
import re
import sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003 as judge


def load_tsv_by_key(path, key_col="point_id"):
    if not path or not os.path.isfile(path):
        return {}
    out = {}
    with open(path, "r", encoding="utf-8") as fh:
        r = csv.DictReader((line for line in fh if not line.startswith("#")), delimiter="\t")
        for row in r:
            out[row[key_col]] = row
    return out


def int_or_none(val):
    if val is None or val == "" or val == "MISSING" or val == "-":
        return None
    try:
        return int(val)
    except ValueError:
        return None


def normalize_site(site_str):
    if not site_str or site_str == "-":
        return "-"
    # Strip annotations like （[源码] 推断） or ([源码] 推断) or [源码]
    s = re.sub(r"[（\(].*?[）\)]", "", site_str).strip()
    s = re.sub(r"\[.*?\]", "", s).strip()
    return s


def main():
    parser = argparse.ArgumentParser(description="P05-S4 verdict engine v5")
    parser.add_argument("--prereg", required=True, help="Path to effective preregistration table")
    parser.add_argument("--facts1", required=True, help="Path to pass 1 facts TSV")
    parser.add_argument("--facts2", required=True, help="Path to pass 2 facts TSV")
    parser.add_argument("--state1", default=None, help="Path to pass 1 state TSV")
    parser.add_argument("--state2", default=None, help="Path to pass 2 state TSV")
    parser.add_argument("--out-verdict", required=True, help="Output VERDICT TSV path")
    parser.add_argument("--out-summary", required=True, help="Output SUMMARY TXT path")
    parser.add_argument("--control-map", default=None, help="Path to CONTROL_MAPPING tsv")
    parser.add_argument("--assert-total", type=int, default=None, help="Assert total evaluated points equals this count")
    parser.add_argument("--expected-total", type=int, default=None, help="Alias for --assert-total")

    args = parser.parse_args()
    if args.assert_total is None and args.expected_total is not None:
        args.assert_total = args.expected_total

    if os.path.exists(args.out_verdict):
        sys.exit(f"REFUSED: {args.out_verdict} already exists (U17)")
    if os.path.exists(args.out_summary):
        sys.exit(f"REFUSED: {args.out_summary} already exists (U17)")

    with open(args.prereg, encoding="utf-8") as fh:
        prereg_rows = list(csv.DictReader((line for line in fh if not line.startswith("#")), delimiter="\t"))

    facts1_rows = load_tsv_by_key(args.facts1)
    facts2_rows = load_tsv_by_key(args.facts2)

    state1_rows = {}
    if args.state1 and os.path.isfile(args.state1):
        with open(args.state1, encoding="utf-8") as fh:
            for r in csv.DictReader((line for line in fh if not line.startswith("#")), delimiter="\t"):
                if r.get("pass") == "1" or "pass" not in r:
                    state1_rows[r["point_id"]] = r

    state2_rows = {}
    if args.state2 and os.path.isfile(args.state2):
        with open(args.state2, encoding="utf-8") as fh:
            for r in csv.DictReader((line for line in fh if not line.startswith("#")), delimiter="\t"):
                if r.get("pass") == "2" or "pass" not in r:
                    state2_rows[r["point_id"]] = r

    counts = {
        "MATCH": 0,
        "MISMATCH": 0,
        "FLAKY": 0,
        "GDB_DIVERGENT": 0,
        "UNJUDGED_MISSING": 0,
        "UNJUDGED_BY_DESIGN": 0,
        "SCHEMA_ERROR": 0,
    }

    item_stats = {}
    verdict_rows = []
    superseded_count = 0

    for e in prereg_rows:
        pid = e["point_id"]
        item = e.get("item", "-")
        if item not in item_stats:
            item_stats[item] = {k: 0 for k in counts}

        superseded_by = e.get("SUPERSEDED_BY") or e.get("superseded_by") or "-"
        if superseded_by not in ("-", "", None):
            superseded_count += 1

        r1 = facts1_rows.get(pid)
        r2 = facts2_rows.get(pid)
        s1 = state1_rows.get(pid)
        s2 = state2_rows.get(pid)

        # Check schema / presence
        schema_issues = []
        if r1 is None or r1.get("status") == "MISSING_DIR":
            schema_issues.append("MISSING_IN_PASS1")
        if r2 is None or r2.get("status") == "MISSING_DIR":
            schema_issues.append("MISSING_IN_PASS2")

        exp_tree = e.get("tree", "-")
        if exp_tree not in (None, "", "-"):
            if r1 and r1.get("tree") != exp_tree:
                schema_issues.append(f"TREE_MISMATCH_PASS1({r1.get('tree')}!={exp_tree})")
            if r2 and r2.get("tree") != exp_tree:
                schema_issues.append(f"TREE_MISMATCH_PASS2({r2.get('tree')}!={exp_tree})")

        if schema_issues:
            counts["SCHEMA_ERROR"] += 1
            item_stats[item]["SCHEMA_ERROR"] += 1
            verdict_rows.append([
                pid, item, "SCHEMA_ERROR", "SCHEMA_ERROR",
                ",".join(schema_issues), "-", "-", "-", superseded_by, "schema error detected"
            ])
            continue

        mismatches1 = []
        mismatches2 = []
        unjudged_missing_reasons = []
        unjudged_design_reasons = []

        is_gdb_divergent = (r1.get("gdb_divergent") == "1" or r2.get("gdb_divergent") == "1")

        is_ctrl = (e.get("control_group") == "YES" or e.get("exp_class") == "CONTROL_OK")
        c1, _, _ = judge.classify(int_or_none(r1.get("rc")), int_or_none(r1.get("rc1")),
                                  int_or_none(r1.get("rc2")), int_or_none(r1.get("hit", 0)),
                                  control=is_ctrl)
        c2, _, _ = judge.classify(int_or_none(r2.get("rc")), int_or_none(r2.get("rc1")),
                                  int_or_none(r2.get("rc2")), int_or_none(r2.get("hit", 0)),
                                  control=is_ctrl)

        class_rule = e.get("class_rule", "JUDGE_D003")

        # 1. Return codes comparison (exp="-" not judged)
        for f, exp_k in [("rc1", "exp_rc1"), ("rc2", "exp_rc2"), ("rc3", "exp_rc3")]:
            exp_val = e.get(exp_k, "-")
            if exp_val not in (None, "", "-"):
                if exp_val == "NZ":
                    if r1.get(f) in ("0", "MISSING"):
                        mismatches1.append(f"{exp_k}({r1.get(f)}==0_or_missing)")
                    if r2.get(f) in ("0", "MISSING"):
                        mismatches2.append(f"{exp_k}({r2.get(f)}==0_or_missing)")
                else:
                    if str(r1.get(f)) != str(exp_val):
                        mismatches1.append(f"{exp_k}({r1.get(f)}!={exp_val})")
                    if str(r2.get(f)) != str(exp_val):
                        mismatches2.append(f"{exp_k}({r2.get(f)}!={exp_val})")

        # 2. Signal and hit (exp="-" not judged)
        if e.get("exp_signal") not in (None, "", "-"):
            if str(r1.get("signal")) != str(e.get("exp_signal")):
                mismatches1.append(f"exp_signal({r1.get('signal')}!={e.get('exp_signal')})")
            if str(r2.get("signal")) != str(e.get("exp_signal")):
                mismatches2.append(f"exp_signal({r2.get('signal')}!={e.get('exp_signal')})")

        if e.get("exp_hit") not in (None, "", "-"):
            if str(r1.get("hit")) != str(e.get("exp_hit")):
                mismatches1.append(f"exp_hit({r1.get('hit')}!={e.get('exp_hit')})")
            if str(r2.get("hit")) != str(e.get("exp_hit")):
                mismatches2.append(f"exp_hit({r2.get('hit')}!={e.get('exp_hit')})")

        if e.get("exp_hit1") not in (None, "", "-"):
            if str(r1.get("hit1")) != str(e.get("exp_hit1")):
                mismatches1.append(f"exp_hit1({r1.get('hit1')}!={e.get('exp_hit1')})")
            if str(r2.get("hit1")) != str(e.get("exp_hit1")):
                mismatches2.append(f"exp_hit1({r2.get('hit1')}!={e.get('exp_hit1')})")

        # 3. Crash call, crash site, post_call1_solution (U272, exp="-" not judged)
        if e.get("exp_crash_call") not in (None, "", "-"):
            if str(r1.get("crash_call")) != str(e.get("exp_crash_call")):
                mismatches1.append(f"exp_crash_call({r1.get('crash_call')}!={e.get('exp_crash_call')})")
            if str(r2.get("crash_call")) != str(e.get("exp_crash_call")):
                mismatches2.append(f"exp_crash_call({r2.get('crash_call')}!={e.get('exp_crash_call')})")

        if e.get("exp_crash_site") not in (None, "", "-"):
            exp_site_norm = normalize_site(e.get("exp_crash_site"))
            act_site1_norm = normalize_site(r1.get("crash_site"))
            act_site2_norm = normalize_site(r2.get("crash_site"))
            if exp_site_norm != act_site1_norm:
                mismatches1.append(f"exp_crash_site({r1.get('crash_site')}!={e.get('exp_crash_site')})")
            if exp_site_norm != act_site2_norm:
                mismatches2.append(f"exp_crash_site({r2.get('crash_site')}!={e.get('exp_crash_site')})")

        if e.get("exp_post_call1_solution") not in (None, "", "-"):
            if str(r1.get("post_call1_solution")) != str(e.get("exp_post_call1_solution")):
                mismatches1.append(f"exp_post_call1_solution({r1.get('post_call1_solution')}!={e.get('exp_post_call1_solution')})")
            if str(r2.get("post_call1_solution")) != str(e.get("exp_post_call1_solution")):
                mismatches2.append(f"exp_post_call1_solution({r2.get('post_call1_solution')}!={e.get('exp_post_call1_solution')})")

        # 4. Dual failure specific fields (M2-04)
        if e.get("item") == "M2-04":
            for f, exp_k in [("hit2", "exp_hit2"),
                             ("inject2_invalid", "exp_inject2_invalid"),
                             ("inject2_suppressed", "exp_inject2_suppressed")]:
                exp_val = e.get(exp_k, "-")
                if exp_val not in (None, "", "-"):
                    if str(r1.get(f)) != str(exp_val):
                        mismatches1.append(f"{exp_k}({r1.get(f)}!={exp_val})")
                    if str(r2.get(f)) != str(exp_val):
                        mismatches2.append(f"{exp_k}({r2.get(f)}!={exp_val})")

            exp_fl1 = e.get("fail_layer1", "-")
            if exp_fl1 not in (None, "", "-"):
                act_fl1_p1 = s1.get("failing_layer") if s1 else None
                act_fl1_p2 = s2.get("failing_layer") if s2 else None
                if act_fl1_p1 != exp_fl1:
                    mismatches1.append(f"fail_layer1({act_fl1_p1}!={exp_fl1})")
                if act_fl1_p2 != exp_fl1:
                    mismatches2.append(f"fail_layer1({act_fl1_p2}!={exp_fl1})")

        # 5. Class comparison & SAN_CRASH (U269)
        exp_cls = e.get("exp_class", "-")
        san_crash1 = (r1.get("san_crash") == "1")
        san_crash2 = (r2.get("san_crash") == "1")

        if exp_cls == "SAN_CRASH":
            if not san_crash1:
                mismatches1.append("exp_class(no_san_crash!=SAN_CRASH)")
            if not san_crash2:
                mismatches2.append("exp_class(no_san_crash!=SAN_CRASH)")
        elif class_rule == "NATIVE_FAIL_CONTROL":
            for p_num, r_cur, c_cur, mismatches_cur in [(1, r1, c1, mismatches1), (2, r2, c2, mismatches2)]:
                if r_cur.get("rc1") != "20":
                    mismatches_cur.append(f"native_fail_rc1({r_cur.get('rc1')}!=20)")
                if r_cur.get("rc2") != "20":
                    mismatches_cur.append(f"native_fail_rc2({r_cur.get('rc2')}!=20)")
                if r_cur.get("signal") != "0":
                    mismatches_cur.append(f"native_fail_signal({r_cur.get('signal')}!=0)")
                if r_cur.get("hit") != "0":
                    mismatches_cur.append(f"native_fail_hit({r_cur.get('hit')}!=0)")
                if c_cur != "INVALID":
                    mismatches_cur.append(f"native_fail_class({c_cur}!=INVALID)")
        elif class_rule == "BASELINE_ONLY_RULE":
            for p_num, r_cur, mismatches_cur in [(1, r1, mismatches1), (2, r2, mismatches2)]:
                if r_cur.get("rc1") != "20":
                    mismatches_cur.append(f"baseline_rc1({r_cur.get('rc1')}!=20)")
                if r_cur.get("signal") != "0":
                    mismatches_cur.append(f"baseline_signal({r_cur.get('signal')}!=0)")
                m_hits = r_cur.get("m210_hits", "-")
                if m_hits in (None, "", "-", "0", "NONE"):
                    mismatches_cur.append(f"baseline_m210_hits_none({m_hits})")
        elif exp_cls not in (None, "", "-"):
            if c1 != exp_cls:
                mismatches1.append(f"exp_class({c1}!={exp_cls})")
            if c2 != exp_cls:
                mismatches2.append(f"exp_class({c2}!={exp_cls})")
            if san_crash1:
                mismatches1.append("san_crash(1!=0)")
            if san_crash2:
                mismatches2.append("san_crash(1!=0)")

        # 6. Sanitizer checks (M2-03, U257)
        if e.get("item") == "M2-03":
            if e.get("exp_san") not in (None, "", "-"):
                if str(r1.get("san_reports")) != str(e.get("exp_san")):
                    mismatches1.append(f"exp_san({r1.get('san_reports')}!={e.get('exp_san')})")
                if str(r2.get("san_reports")) != str(e.get("exp_san")):
                    mismatches2.append(f"exp_san({r2.get('san_reports')}!={e.get('exp_san')})")

            san_ref = e.get("san_ref_point_id", "-")
            if san_ref in ("NO_REF", ""):
                unjudged_design_reasons.append("san_ref_unspecified(NO_REF)")
            elif san_ref not in (None, "-"):
                ref_r1 = facts1_rows.get(san_ref)
                ref_r2 = facts2_rows.get(san_ref)
                if not ref_r1 or not ref_r2:
                    unjudged_missing_reasons.append(f"san_ref_point_missing({san_ref})")
                else:
                    ref_c1, _, _ = judge.classify(int_or_none(ref_r1.get("rc")), int_or_none(ref_r1.get("rc1")),
                                                  int_or_none(ref_r1.get("rc2")), int_or_none(ref_r1.get("hit", 0)),
                                                  control=False)
                    ref_c2, _, _ = judge.classify(int_or_none(ref_r2.get("rc")), int_or_none(ref_r2.get("rc1")),
                                                  int_or_none(ref_r2.get("rc2")), int_or_none(ref_r2.get("hit", 0)),
                                                  control=False)
                    if r1.get("rc1") != ref_r1.get("rc1"):
                        mismatches1.append(f"san_ref_rc1({r1.get('rc1')}!={ref_r1.get('rc1')})")
                    if r2.get("rc1") != ref_r2.get("rc1"):
                        mismatches2.append(f"san_ref_rc1({r2.get('rc1')}!={ref_r2.get('rc1')})")
                    if exp_cls != "SAN_CRASH":
                        if c1 != ref_c1:
                            mismatches1.append(f"san_ref_class({c1}!={ref_c1})")
                        if c2 != ref_c2:
                            mismatches2.append(f"san_ref_class({c2}!={ref_c2})")

        # 7. Invariants I1..I6 from state analyzer (U267: strict equality)
        if e.get("state_analyzer") not in (None, "", "-"):
            if not s1:
                unjudged_missing_reasons.append("MISSING_STATE_PASS1")
            if not s2:
                unjudged_missing_reasons.append("MISSING_STATE_PASS2")

            if s1 and s2:
                for inv in ("I1", "I2", "I3", "I4", "I5", "I6"):
                    exp_inv = e.get(f"exp_{inv}", "-")
                    if exp_inv in ("HOLD", "VIOLATED", "N/A"):
                        v1 = s1.get(inv, "UNJUDGED")
                        v2 = s2.get(inv, "UNJUDGED")
                        if v1 == "UNJUDGED":
                            unjudged_missing_reasons.append(f"{inv}_UNJUDGED_PASS1")
                        elif v1 != exp_inv:
                            mismatches1.append(f"{inv}({v1}!={exp_inv})")

                        if v2 == "UNJUDGED":
                            unjudged_missing_reasons.append(f"{inv}_UNJUDGED_PASS2")
                        elif v2 != exp_inv:
                            mismatches2.append(f"{inv}({v2}!={exp_inv})")

        # 8. INIT_CLEAN assertion (U268; only applicable if gdb_script is present)
        exp_ic = e.get("exp_init_clean", "-")
        if exp_ic in ("HOLD", "VIOLATED", "N/A") and e.get("gdb_script") not in (None, "", "-"):
            ic1 = r1.get("init_clean", "-")
            ic2 = r2.get("init_clean", "-")
            if ic1 == "-":
                unjudged_missing_reasons.append("init_clean_MISSING_PASS1")
            elif ic1 != exp_ic:
                mismatches1.append(f"init_clean({ic1}!={exp_ic})")
            if ic2 == "-":
                unjudged_missing_reasons.append("init_clean_MISSING_PASS2")
            elif ic2 != exp_ic:
                mismatches2.append(f"init_clean({ic2}!={exp_ic})")

        # 9. Output call comparison (I6)
        out_assert = e.get("output_assertion", "NONE")
        if out_assert == "I6_ONLY" and e.get("control_point_id") not in (None, "", "-"):
            ctrl_id = e.get("control_point_id")
            ctrl_r1 = facts1_rows.get(ctrl_id)
            ctrl_r2 = facts2_rows.get(ctrl_id)
            if ctrl_r1 and ctrl_r2:
                ret_call = e.get("retry_call", "2")
                ctrl_out_call = e.get("control_output_call", "2")
                pt_call_sha_p1 = r1.get(f"call{ret_call}_sha256", "-")
                pt_call_sha_p2 = r2.get(f"call{ret_call}_sha256", "-")
                ctrl_call_sha_p1 = ctrl_r1.get(f"call{ctrl_out_call}_sha256", "-")
                ctrl_call_sha_p2 = ctrl_r2.get(f"call{ctrl_out_call}_sha256", "-")

                if pt_call_sha_p1 in ("-", "MISSING") or ctrl_call_sha_p1 in ("-", "MISSING"):
                    unjudged_missing_reasons.append("OUTPUT_SHA_MISSING_PASS1")
                elif pt_call_sha_p1 != ctrl_call_sha_p1:
                    mismatches1.append(f"I6_OUTPUT_DIFF({pt_call_sha_p1[:8]}!={ctrl_call_sha_p1[:8]})")

                if pt_call_sha_p2 in ("-", "MISSING") or ctrl_call_sha_p2 in ("-", "MISSING"):
                    unjudged_missing_reasons.append("OUTPUT_SHA_MISSING_PASS2")
                elif pt_call_sha_p2 != ctrl_call_sha_p2:
                    mismatches2.append(f"I6_OUTPUT_DIFF({pt_call_sha_p2[:8]}!={ctrl_call_sha_p2[:8]})")

        # Flaky detection
        flaky_fields = []
        for f in (
            "rc", "rc1", "rc2", "rc3", "signal", "hit", "hit1", "hit2",
            "san_reports", "san_crash", "crash_call", "crash_site", "post_call1_solution"
        ):
            if r1.get(f) != r2.get(f):
                flaky_fields.append(f"{f}(p1={r1.get(f)},p2={r2.get(f)})")
        if c1 != c2:
            flaky_fields.append(f"class(p1={c1},p2={c2})")
        if s1 and s2:
            for inv in ("I1", "I2", "I3", "I4", "I5", "I6"):
                if s1.get(inv) != s2.get(inv):
                    flaky_fields.append(f"{inv}(p1={s1.get(inv)},p2={s2.get(inv)})")

        all_mismatches = sorted(set(mismatches1) | set(mismatches2))

        # Priority: GDB_DIVERGENT > MISMATCH > FLAKY > UNJUDGED_MISSING > UNJUDGED_BY_DESIGN > MATCH
        if is_gdb_divergent:
            v_primary = "GDB_DIVERGENT"
            v_detail = "GDB_DIVERGENT"
            counts["GDB_DIVERGENT"] += 1
            item_stats[item]["GDB_DIVERGENT"] += 1
        elif mismatches1 and mismatches2:
            v_primary = "MISMATCH"
            v_detail = "MISMATCH"
            counts["MISMATCH"] += 1
            item_stats[item]["MISMATCH"] += 1
        elif mismatches1 or mismatches2 or flaky_fields:
            v_primary = "FLAKY"
            v_detail = "FLAKY"
            counts["FLAKY"] += 1
            item_stats[item]["FLAKY"] += 1
        elif unjudged_missing_reasons:
            v_primary = "UNJUDGED"
            v_detail = "UNJUDGED_MISSING"
            counts["UNJUDGED_MISSING"] += 1
            item_stats[item]["UNJUDGED_MISSING"] += 1
        elif unjudged_design_reasons:
            v_primary = "UNJUDGED"
            v_detail = "UNJUDGED_BY_DESIGN"
            counts["UNJUDGED_BY_DESIGN"] += 1
            item_stats[item]["UNJUDGED_BY_DESIGN"] += 1
        else:
            v_primary = "MATCH"
            v_detail = "MATCH"
            counts["MATCH"] += 1
            item_stats[item]["MATCH"] += 1

        notes_parts = []
        if is_gdb_divergent:
            notes_parts.append(f"GDB_DIVERGENT(p1={r1.get('gdb_divergent')},p2={r2.get('gdb_divergent')})")
        if mismatches1 or mismatches2:
            notes_parts.append(f"p1_diffs={','.join(mismatches1) or 'none'};p2_diffs={','.join(mismatches2) or 'none'}")
        if not notes_parts:
            notes_parts.append("all verified")

        verdict_rows.append([
            pid,
            item,
            v_primary,
            v_detail,
            ",".join(all_mismatches) if all_mismatches else "-",
            ",".join(flaky_fields) if flaky_fields else "-",
            ",".join(unjudged_missing_reasons) if unjudged_missing_reasons else "-",
            ",".join(unjudged_design_reasons) if unjudged_design_reasons else "-",
            superseded_by,
            "; ".join(notes_parts)
        ])

    headers = [
        "point_id", "item", "verdict", "verdict_detail",
        "mismatches", "flaky_fields", "unjudged_missing", "unjudged_by_design", "superseded_by", "notes"
    ]
    os.makedirs(os.path.dirname(os.path.abspath(args.out_verdict)), exist_ok=True)
    with open(args.out_verdict, "w", encoding="utf-8") as fh:
        fh.write("\t".join(headers) + "\n")
        for vr in verdict_rows:
            fh.write("\t".join(vr) + "\n")

    total_unjudged = counts["UNJUDGED_BY_DESIGN"] + counts["UNJUDGED_MISSING"]
    total_points = (counts["MATCH"] + counts["MISMATCH"] + counts["FLAKY"] +
                    counts["GDB_DIVERGENT"] + total_unjudged + counts["SCHEMA_ERROR"])

    effective_points = total_points - superseded_count

    if args.assert_total is not None and total_points != args.assert_total:
        sys.exit(f"ASSERTION FAILED: total evaluated {total_points} != assert_total {args.assert_total}")

    # Write SUMMARY TXT
    sum_lines = [
        "# VERDICT_SUMMARY_R8_M2d -- P05-S4 R8 M2d verdict summary",
        f"total_points: {total_points}",
        f"superseded_points: {superseded_count}",
        f"effective_points: {effective_points}",
        f"MATCH: {counts['MATCH']}",
        f"MISMATCH: {counts['MISMATCH']}",
        f"FLAKY: {counts['FLAKY']}",
        f"GDB_DIVERGENT: {counts['GDB_DIVERGENT']}",
        f"UNJUDGED_MISSING: {counts['UNJUDGED_MISSING']}",
        f"UNJUDGED_BY_DESIGN: {counts['UNJUDGED_BY_DESIGN']}",
        f"SCHEMA_ERROR: {counts['SCHEMA_ERROR']}",
        "\n# By item:",
    ]
    for it, st in sorted(item_stats.items()):
        sum_lines.append(f"{it}\tMATCH={st['MATCH']}\tMISMATCH={st['MISMATCH']}\tFLAKY={st['FLAKY']}\tGDB_DIV={st['GDB_DIVERGENT']}\tUNJ_MISS={st['UNJUDGED_MISSING']}\tUNJ_DES={st['UNJUDGED_BY_DESIGN']}\tSCHEMA={st['SCHEMA_ERROR']}")

    os.makedirs(os.path.dirname(os.path.abspath(args.out_summary)), exist_ok=True)
    with open(args.out_summary, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sum_lines) + "\n")

    print(f"Generated verdict for {total_points} points (effective {effective_points}) -> {args.out_verdict}")
    print(f"Summary -> {args.out_summary}")


if __name__ == "__main__":
    main()
