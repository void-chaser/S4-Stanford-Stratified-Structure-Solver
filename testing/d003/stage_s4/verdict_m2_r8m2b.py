#!/usr/bin/env python3
# verdict_m2_r8m2b.py -- P05-S4 R8 M2b verdict engine (v3).
# Enforces:
#  - U255: M2-07-CTRL-vl-ng1-F3 class_rule=NATIVE_FAIL_CONTROL; checks rc1=20, rc2=20, signal=0, hit=0, classify==INVALID.
#          No hardcoded point_id special-casing.
#  - U256: GDB_DIVERGENT is a primary mutually exclusive category; has highest precedence.
#  - U257: M2-03 non-sanitizer reference points comparison (rc1 and classify match reference).
#  - A7: Asserts exp_hit1 and fail_layer1.
#  - A8: BASELINE_ONLY_RULE requires rc1=20, signal=0, and at least one return 20 breakpoint hit in m210_hits.
#  - Precedence: GDB_DIVERGENT > MISMATCH > FLAKY > UNJUDGED_MISSING > UNJUDGED_BY_DESIGN > MATCH.
#  - Total points strictly asserted against expected total (default 150 for main, 19 for sanref, 5 for win64).
import argparse
import csv
import hashlib
import os
import sys
from collections import Counter, OrderedDict

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EXPECTED_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
JUDGE_PY = os.path.join(REPO, "testing", "d003", "judge_d003.py")

with open(JUDGE_PY, "rb") as fh:
    j_sha = hashlib.sha256(fh.read()).hexdigest()
if j_sha != EXPECTED_JUDGE_SHA:
    sys.exit(f"FATAL: judge_d003.py sha256 mismatch: {j_sha} != {EXPECTED_JUDGE_SHA}")

sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003 as judge  # noqa: E402


def read_tsv_dict(path, key_col="point_id"):
    rows = OrderedDict()
    if not path or not os.path.isfile(path):
        return rows
    with open(path, encoding="utf-8") as fh:
        r = csv.DictReader((line for line in fh if not line.startswith("#")), delimiter="\t")
        for row in r:
            k = row.get(key_col)
            if k:
                rows[k] = row
    return rows


def int_or_none(v):
    if v in (None, "", "-", "NA", "None", "MISSING", "TIMEOUT"):
        return None
    try:
        return int(v)
    except ValueError:
        return None


def rc_matches(exp_val, obs_val):
    if exp_val in (None, "", "-"):
        return True
    if exp_val == "NZ":
        obs_i = int_or_none(obs_val)
        return obs_i is not None and obs_i != 0
    exp_i = int_or_none(exp_val)
    obs_i = int_or_none(obs_val)
    if exp_i is not None and obs_i is not None:
        return exp_i == obs_i
    return str(exp_val) == str(obs_val)


def main():
    parser = argparse.ArgumentParser(description="P05-S4 verdict v3")
    parser.add_argument("--prereg", required=True, help="Path to effective preregistration table")
    parser.add_argument("--facts1", required=True, help="Path to FACTS pass 1 tsv")
    parser.add_argument("--facts2", required=True, help="Path to FACTS pass 2 tsv")
    parser.add_argument("--state1", default=None, help="Path to STATE pass 1 tsv")
    parser.add_argument("--state2", default=None, help="Path to STATE pass 2 tsv")
    parser.add_argument("--control-map", default=None, help="Path to CONTROL_MAPPING tsv")
    parser.add_argument("--out-verdict", required=True, help="Output VERDICT tsv path")
    parser.add_argument("--out-summary", required=True, help="Output SUMMARY txt path")
    parser.add_argument("--expected-total", type=int, default=None, help="Expected total points (default: len of prereg)")

    args = parser.parse_args()

    if os.path.exists(args.out_verdict) or os.path.exists(args.out_summary):
        sys.exit(f"REFUSED: output files exist (U17): {args.out_verdict} or {args.out_summary}")

    prereg_rows = read_tsv_dict(args.prereg, "point_id")
    facts1_rows = read_tsv_dict(args.facts1, "point_id")
    facts2_rows = read_tsv_dict(args.facts2, "point_id")

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

    exp_total = args.expected_total if args.expected_total is not None else len(prereg_rows)

    verdict_rows = []
    item_stats = OrderedDict()

    counts = {
        "MATCH": 0,
        "MISMATCH": 0,
        "FLAKY": 0,
        "GDB_DIVERGENT": 0,
        "UNJUDGED_BY_DESIGN": 0,
        "UNJUDGED_MISSING": 0,
        "SCHEMA_ERROR": 0,
    }

    for pid, e in prereg_rows.items():
        item = e.get("item", "OTHER")
        if item not in item_stats:
            item_stats[item] = Counter()

        r1 = facts1_rows.get(pid)
        r2 = facts2_rows.get(pid)
        s1 = state1_rows.get(pid)
        s2 = state2_rows.get(pid)

        schema_issues = []
        if r1 is None or r1.get("status") == "MISSING_DIR":
            schema_issues.append("MISSING_IN_PASS1")
        if r2 is None or r2.get("status") == "MISSING_DIR":
            schema_issues.append("MISSING_IN_PASS2")
        if r1 and r1.get("tree") != e.get("tree"):
            schema_issues.append(f"TREE_MISMATCH_PASS1({r1.get('tree')}!={e.get('tree')})")
        if r2 and r2.get("tree") != e.get("tree"):
            schema_issues.append(f"TREE_MISMATCH_PASS2({r2.get('tree')}!={e.get('tree')})")

        if schema_issues:
            v_primary = "SCHEMA_ERROR"
            counts["SCHEMA_ERROR"] += 1
            item_stats[item]["SCHEMA_ERROR"] += 1
            verdict_rows.append([
                pid, item, v_primary, "SCHEMA_ERROR",
                ",".join(schema_issues), "-", "-", "-", "schema error detected"
            ])
            continue

        # Check GDB divergence (U256)
        div1 = (r1.get("gdb_divergent") == "1")
        div2 = (r2.get("gdb_divergent") == "1")
        is_gdb_divergent = (div1 or div2)

        # Classification via judge_d003
        class_rule = e.get("class_rule", "JUDGE_D003")
        is_ctrl = (e.get("control_group") == "YES" or e.get("exp_class") == "CONTROL_OK")

        if class_rule == "BASELINE_ONLY_RULE":
            c1 = "BASELINE_ONLY"
            c2 = "BASELINE_ONLY"
        else:
            c1_t = judge.classify(int_or_none(r1.get("rc")), int_or_none(r1.get("rc1")),
                                  int_or_none(r1.get("rc2")), int_or_none(r1.get("hit", 0)), control=is_ctrl)
            c2_t = judge.classify(int_or_none(r2.get("rc")), int_or_none(r2.get("rc1")),
                                  int_or_none(r2.get("rc2")), int_or_none(r2.get("hit", 0)), control=is_ctrl)
            c1 = c1_t[0]
            c2 = c2_t[0]

        # Field comparisons
        mismatches1 = []
        mismatches2 = []
        unjudged_missing_reasons = []
        unjudged_design_reasons = []

        # 1. rc1, rc2, rc3
        for f, exp_k in [("rc1", "exp_rc1"), ("rc2", "exp_rc2"), ("rc3", "exp_rc3")]:
            exp_val = e.get(exp_k, "-")
            if exp_val not in (None, "", "-"):
                if not rc_matches(exp_val, r1.get(f)):
                    mismatches1.append(f"{exp_k}({r1.get(f)}!={exp_val})")
                if not rc_matches(exp_val, r2.get(f)):
                    mismatches2.append(f"{exp_k}({r2.get(f)}!={exp_val})")

        # 2. signal and hit
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

        # A7: check exp_hit1
        if e.get("exp_hit1") not in (None, "", "-"):
            if str(r1.get("hit1")) != str(e.get("exp_hit1")):
                mismatches1.append(f"exp_hit1({r1.get('hit1')}!={e.get('exp_hit1')})")
            if str(r2.get("hit1")) != str(e.get("exp_hit1")):
                mismatches2.append(f"exp_hit1({r2.get('hit1')}!={e.get('exp_hit1')})")

        # 3. Dual failure specific fields (M2-04)
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

            # A7 / U258: assert fail_layer1
            exp_fl1 = e.get("fail_layer1", "-")
            if exp_fl1 not in (None, "", "-"):
                act_fl1_p1 = s1.get("failing_layer") if s1 else None
                act_fl1_p2 = s2.get("failing_layer") if s2 else None
                if act_fl1_p1 != exp_fl1:
                    mismatches1.append(f"fail_layer1({act_fl1_p1}!={exp_fl1})")
                if act_fl1_p2 != exp_fl1:
                    mismatches2.append(f"fail_layer1({act_fl1_p2}!={exp_fl1})")

        # 4. Class comparison
        if class_rule == "NATIVE_FAIL_CONTROL":
            # U255: strict equality: rc1=20, rc2=20, signal=0, hit=0, classify==INVALID
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
            # U254 / A8: rc1=20, signal=0, and at least one return 20 breakpoint hit in m210_hits
            for p_num, r_cur, mismatches_cur in [(1, r1, mismatches1), (2, r2, mismatches2)]:
                if r_cur.get("rc1") != "20":
                    mismatches_cur.append(f"baseline_rc1({r_cur.get('rc1')}!=20)")
                if r_cur.get("signal") != "0":
                    mismatches_cur.append(f"baseline_signal({r_cur.get('signal')}!=0)")
                m_hits = r_cur.get("m210_hits", "-")
                if m_hits in (None, "", "-", "0", "NONE"):
                    mismatches_cur.append(f"baseline_m210_hits_none({m_hits})")

        elif e.get("exp_class") not in (None, "", "-"):
            if c1 != e.get("exp_class"):
                mismatches1.append(f"exp_class({c1}!={e.get('exp_class')})")
            if c2 != e.get("exp_class"):
                mismatches2.append(f"exp_class({c2}!={e.get('exp_class')})")

        # 5. Sanitizer checks (M2-03, U257)
        if e.get("item") == "M2-03":
            if e.get("exp_san") not in (None, "", "-"):
                if str(r1.get("san_reports")) != str(e.get("exp_san")):
                    mismatches1.append(f"exp_san({r1.get('san_reports')}!={e.get('exp_san')})")
                if str(r2.get("san_reports")) != str(e.get("exp_san")):
                    mismatches2.append(f"exp_san({r2.get('san_reports')}!={e.get('exp_san')})")

            # Reference comparison (U257)
            san_ref = e.get("san_ref_point_id", "-")
            if san_ref == "NO_REF":
                unjudged_design_reasons.append("san_ref=NO_REF")
            elif san_ref not in (None, "", "-"):
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
                    if c1 != ref_c1:
                        mismatches1.append(f"san_ref_class({c1}!={ref_c1})")
                    if c2 != ref_c2:
                        mismatches2.append(f"san_ref_class({c2}!={ref_c2})")

        # 6. Invariants I1..I6 from state analyzer
        if e.get("state_analyzer") not in (None, "", "-"):
            if not s1:
                unjudged_missing_reasons.append("MISSING_STATE_PASS1")
            if not s2:
                unjudged_missing_reasons.append("MISSING_STATE_PASS2")

            if s1 and s2:
                for inv in ("I1", "I2", "I3", "I4", "I5", "I6"):
                    exp_inv = e.get(f"exp_{inv}", "-")
                    if exp_inv == "HOLD":
                        v1 = s1.get(inv, "UNJUDGED")
                        v2 = s2.get(inv, "UNJUDGED")
                        if v1 == "VIOLATED":
                            mismatches1.append(f"{inv}=VIOLATED")
                        elif v1 == "UNJUDGED":
                            unjudged_missing_reasons.append(f"{inv}_UNJUDGED_PASS1")

                        if v2 == "VIOLATED":
                            mismatches2.append(f"{inv}=VIOLATED")
                        elif v2 == "UNJUDGED":
                            unjudged_missing_reasons.append(f"{inv}_UNJUDGED_PASS2")

        # Flaky detection
        flaky_fields = []
        for f in ("rc", "rc1", "rc2", "rc3", "signal", "hit", "hit1", "hit2", "san_reports"):
            if r1.get(f) != r2.get(f):
                flaky_fields.append(f"{f}(p1={r1.get(f)},p2={r2.get(f)})")
        if c1 != c2:
            flaky_fields.append(f"class(p1={c1},p2={c2})")
        if s1 and s2:
            for inv in ("I1", "I2", "I3", "I4", "I5", "I6"):
                if s1.get(inv) != s2.get(inv):
                    flaky_fields.append(f"{inv}(p1={s1.get(inv)},p2={s2.get(inv)})")

        all_mismatches = sorted(set(mismatches1) | set(mismatches2))

        # Precedence: GDB_DIVERGENT > MISMATCH > FLAKY > UNJUDGED_MISSING > UNJUDGED_BY_DESIGN > MATCH
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
            "; ".join(notes_parts)
        ])

    # Write VERDICT TSV
    headers = [
        "point_id", "item", "verdict", "verdict_detail",
        "mismatches", "flaky_fields", "unjudged_missing", "unjudged_by_design", "notes"
    ]
    os.makedirs(os.path.dirname(os.path.abspath(args.out_verdict)), exist_ok=True)
    with open(args.out_verdict, "w", encoding="utf-8") as fh:
        fh.write("\t".join(headers) + "\n")
        for vr in verdict_rows:
            fh.write("\t".join(vr) + "\n")

    total_unjudged = counts["UNJUDGED_BY_DESIGN"] + counts["UNJUDGED_MISSING"]
    total_points = (counts["MATCH"] + counts["MISMATCH"] + counts["FLAKY"] +
                    counts["GDB_DIVERGENT"] + total_unjudged + counts["SCHEMA_ERROR"])

    # Write SUMMARY TXT
    sum_lines = [
        "# VERDICT_SUMMARY_R8_M2b -- P05-S4 R8 M2b verdict summary",
        f"total_points: {total_points}",
        f"MATCH: {counts['MATCH']}",
        f"MISMATCH: {counts['MISMATCH']}",
        f"FLAKY: {counts['FLAKY']}",
        f"GDB_DIVERGENT: {counts['GDB_DIVERGENT']}",
        f"UNJUDGED: {total_unjudged} (by_design={counts['UNJUDGED_BY_DESIGN']}, missing={counts['UNJUDGED_MISSING']})",
        f"SCHEMA_ERROR: {counts['SCHEMA_ERROR']}",
        f"partition_assertion_{exp_total}: {'PASSED' if total_points == exp_total else 'FAILED'}",
        "\n## Breakdown by item:",
        "item\tMATCH\tMISMATCH\tFLAKY\tGDB_DIVERGENT\tUNJUDGED_DESIGN\tUNJUDGED_MISSING\tSCHEMA_ERROR\tTOTAL"
    ]
    for it, st in item_stats.items():
        it_tot = sum(st.values())
        sum_lines.append(f"{it}\t{st['MATCH']}\t{st['MISMATCH']}\t{st['FLAKY']}\t{st['GDB_DIVERGENT']}\t{st['UNJUDGED_BY_DESIGN']}\t{st['UNJUDGED_MISSING']}\t{st['SCHEMA_ERROR']}\t{it_tot}")

    with open(args.out_summary, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sum_lines) + "\n")

    print("\n".join(sum_lines))

    if total_points != exp_total:
        sys.exit(f"FATAL: Total points evaluated {total_points} != expected {exp_total}!")


if __name__ == "__main__":
    main()
