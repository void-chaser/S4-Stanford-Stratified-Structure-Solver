#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a section 6: compare F2 vs F3 callseqs, check validity and point-level K/M reachability.  New file.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/compare_callseq_r8m1a4.py OUTDIR [SUBDIR_NAME]
Reads CALLSEQ_UNITS_R8_M1a4_R3.tsv, CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv, and OUTDIR/<SUBDIR_NAME>/<unit_id>/events.tsv.
Produces:
  CALLSEQ_F2_F3_R8_M1a4.tsv
  CALLSEQ_VALIDITY_R8_M1a4.tsv
  CALLSEQ_KMAX_R8_M1a4.tsv
  CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4.tsv
"""
import json
import os
import re
import sys
from collections import OrderedDict

RENAME_MAP = {
    "shape_get_intersection_area_quad": "shape_get_intersection_area_quad_st",
}


def read_table(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if not line or line.startswith("#"):
            continue
        rows.append(dict(zip(hdr, line.split("\t"))))
    return hdr, rows


def read_events(path):
    if not os.path.isfile(path):
        return []
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines or len(lines) <= 1:
        return []
    hdr = lines[0].split("\t")
    events = []
    for line in lines[1:]:
        if not line:
            continue
        events.append(dict(zip(hdr, line.split("\t"))))
    return events


def normalize_caller(caller):
    return RENAME_MAP.get(caller, caller)


def compare_events(events_f2, events_f3):
    """Compare two event sequences.

    Returns (status, diff_details, normalized_match):
      status: IDENTICAL / IDENTICAL_AFTER_RENAME / DIFFERENT
    """
    if len(events_f2) != len(events_f3):
        return "DIFFERENT", "length_mismatch: F2=%d, F3=%d" % (len(events_f2), len(events_f3))

    exact_match = True
    norm_match = True
    first_diff = None

    for idx, (e2, e3) in enumerate(zip(events_f2, events_f3), 1):
        # Type, seq, sub_seq, details must match exactly
        if (e2["event_type"] != e3["event_type"] or
                e2["seq"] != e3["seq"] or
                e2["sub_seq"] != e3["sub_seq"] or
                e2["details"] != e3["details"]):
            return "DIFFERENT", "event_%d_mismatch: F2=(%s,%s,%s) vs F3=(%s,%s,%s)" % (
                idx, e2["event_type"], e2["seq"], e2["details"], e3["event_type"], e3["seq"], e3["details"])

        c2 = e2["caller"]
        c3 = e3["caller"]
        if c2 != c3:
            exact_match = False
            if normalize_caller(c2) != normalize_caller(c3):
                norm_match = False
                if first_diff is None:
                    first_diff = "event_%d_caller_diff: F2=%s vs F3=%s" % (idx, c2, c3)

    if exact_match:
        return "IDENTICAL", "exact_match"
    if norm_match:
        return "IDENTICAL_AFTER_RENAME", "shape_get_intersection_area_quad -> shape_get_intersection_area_quad_st"
    return "DIFFERENT", first_diff or "caller_mismatch"


def check_validity(events, summary):
    """Check event sequence validity: ordering, closure, and summary consistency."""
    if not events:
        # Check if truly 0 calls expected and no trace error
        if summary.get("trace_error") != "NONE":
            return False, "empty_with_trace_error"
        if summary.get("exit_code") != 0:
            return False, "empty_with_nonzero_exit"
        return True, "VALID_EMPTY"

    plan_stack = 0
    win_stack = 0
    plan_seqs = set()
    win_seqs = set()

    for idx, ev in enumerate(events, 1):
        t = ev["event_type"]
        seq = int(ev["seq"])
        if t == "PLAN_START":
            plan_stack += 1
            plan_seqs.add(seq)
        elif t == "PLAN_END":
            plan_stack -= 1
            if plan_stack < 0:
                return False, "unbalanced_plan_end_at_%d" % idx
        elif t == "WIN_OPEN":
            win_stack += 1
            win_seqs.add(seq)
        elif t == "WIN_CLOSE":
            win_stack -= 1
            if win_stack < 0:
                return False, "unbalanced_win_close_at_%d" % idx

    if plan_stack != 0:
        return False, "unclosed_plan_start"
    if win_stack != 0:
        return False, "unclosed_win_open"

    return True, "VALID"


def extract_kmax(events):
    """Extract Kmax facts from an event sequence."""
    facts = {
        "s4malloc_max": 0,
        "exec_max": 0,
        "plan_max": 0,
        "plan_allocs": {},    # plan_seq -> count
        "win_max": 0,
        "win_allocs": {},     # win_seq -> count
        "seam_counts": {},    # site_key -> count
    }

    for ev in events:
        t = ev["event_type"]
        seq = int(ev["seq"])
        sub = int(ev["sub_seq"]) if ev["sub_seq"] != "-" else 0

        if t == "S4MALLOC":
            if seq > facts["s4malloc_max"]:
                facts["s4malloc_max"] = seq
        elif t == "EXEC":
            if seq > facts["exec_max"]:
                facts["exec_max"] = seq
        elif t == "PLAN_START":
            if seq > facts["plan_max"]:
                facts["plan_max"] = seq
        elif t == "PLAN_MALLOC":
            facts["plan_allocs"][seq] = max(facts["plan_allocs"].get(seq, 0), sub)
        elif t == "WIN_OPEN":
            if seq > facts["win_max"]:
                facts["win_max"] = seq
        elif t == "WIN_MALLOC":
            facts["win_allocs"][seq] = max(facts["win_allocs"].get(seq, 0), sub)
        elif t == "SEAM":
            # func and sub_seq form site_key
            site_key = "%s:%s" % (ev["func"], ev["sub_seq"])
            facts["seam_counts"][site_key] = max(facts["seam_counts"].get(site_key, 0), seq)

    return facts


def check_reachability(req, facts):
    """Check reachability of request against observed Kmax facts."""
    if req in ("", "-", "none"):
        return "N/A", "no_injection"

    # s4malloc
    if req == "s4malloc":
        # Any positive allocation reached
        return ("REACHED" if facts["s4malloc_max"] >= 1 else "UNEXPECTED_NOT_REACHED"), "s4malloc_max=%d" % facts["s4malloc_max"]

    # exec
    if req == "exec":
        return ("REACHED" if facts["exec_max"] >= 1 else "UNEXPECTED_NOT_REACHED"), "exec_max=%d" % facts["exec_max"]

    # plan or plan:N
    if req == "plan":
        total_plan_allocs = sum(facts["plan_allocs"].values())
        if total_plan_allocs >= 1:
            return "REACHED", "total_plan_allocs=%d" % total_plan_allocs
        return "UNEXPECTED_NOT_REACHED", "total_plan_allocs=0"

    m = re.match(r"^plan:(\d+)$", req)
    if m:
        n = int(m.group(1))
        # requires plan n exists and plan n has at least n mallocs
        if n in facts["plan_allocs"] and facts["plan_allocs"][n] >= n:
            return "REACHED", "plan_%d_allocs=%d" % (n, facts["plan_allocs"][n])
        return "UNEXPECTED_NOT_REACHED", "plan_%d_allocs=%s" % (n, facts["plan_allocs"].get(n, 0))

    # plancall:K:M
    m = re.match(r"^plancall:(\d+):(\d+)$", req)
    if m:
        k = int(m.group(1))
        mm = int(m.group(2))
        allocs = facts["plan_allocs"].get(k, 0)
        if allocs >= mm:
            return "REACHED", "plan_%d_allocs=%d>=%d" % (k, allocs, mm)
        return "UNEXPECTED_NOT_REACHED", "plan_%d_allocs=%d<%d" % (k, allocs, mm)

    # rnv1:M
    m = re.match(r"^rnv1:(\d+)$", req)
    if m:
        target_m = int(m.group(1))
        # check if any window reached target_m
        max_in_any_win = max(facts["win_allocs"].values()) if facts["win_allocs"] else 0
        if max_in_any_win >= target_m:
            return "REACHED", "max_win_malloc=%d>=%d" % (max_in_any_win, target_m)
        return "UNEXPECTED_NOT_REACHED", "max_win_malloc=%d<%d" % (max_in_any_win, target_m)

    # alloc:ID:K
    m = re.match(r"^alloc:(\d+):(\d+)$", req)
    if m:
        hid = m.group(1)
        k = int(m.group(2))
        site = "S4_TEST_ALLOC_HOOK:%s" % hid
        cnt = facts["seam_counts"].get(site, 0)
        if cnt >= k:
            return "REACHED", "%s_calls=%d>=%d" % (site, cnt, k)
        return "UNEXPECTED_NOT_REACHED", "%s_calls=%d<%d" % (site, cnt, k)

    # kottke_alloc:31:K
    m = re.match(r"^kottke_alloc:(\d+):(\d+)$", req)
    if m:
        hid = m.group(1)
        k = int(m.group(2))
        site = "S4_TEST_KOTTKE_HOOK:%s" % hid
        cnt = facts["seam_counts"].get(site, 0)
        if cnt >= k:
            return "REACHED", "%s_calls=%d>=%d" % (site, cnt, k)
        return "UNEXPECTED_NOT_REACHED", "%s_calls=%d<%d" % (site, cnt, k)

    # fmmret:ID:K
    m = re.match(r"^fmmret:(\d+):(\d+)$", req)
    if m:
        hid = m.group(1)
        k = int(m.group(2))
        site = "S4_TEST_FMMRET_AFTER:%s" % hid
        cnt = facts["seam_counts"].get(site, 0)
        if cnt >= k:
            return "REACHED", "%s_calls=%d>=%d" % (site, cnt, k)
        return "UNEXPECTED_NOT_REACHED", "%s_calls=%d<%d" % (site, cnt, k)

    # linearsolve:SITE:K:MODE
    m = re.match(r"^linearsolve:(\d+):(\d+):([a-z]+)$", req)
    if m:
        site_id = m.group(1)
        k = int(m.group(2))
        site = "S4_TEST_LINEARSOLVE_AFTER:%s" % site_id
        cnt = facts["seam_counts"].get(site, 0)
        if cnt >= k:
            return "REACHED", "%s_calls=%d>=%d" % (site, cnt, k)
        return "UNEXPECTED_NOT_REACHED", "%s_calls=%d<%d" % (site, cnt, k)

    # linearsolve_null2:ID:K
    m = re.match(r"^linearsolve_null2:(\d+):(\d+)$", req)
    if m:
        hid = m.group(1)
        k = int(m.group(2))
        site = "S4_TEST_LINEARSOLVE_NULLINFO2_AFTER:%s" % hid
        cnt = facts["seam_counts"].get(site, 0)
        if cnt >= k:
            return "REACHED", "%s_calls=%d>=%d" % (site, cnt, k)
        return "UNEXPECTED_NOT_REACHED", "%s_calls=%d<%d" % (site, cnt, k)

    return "UNKNOWN_REQUEST", req


def main(argv):
    if len(argv) not in (2, 3, 4):
        raise SystemExit("usage: compare_callseq_r8m1a4.py OUTDIR [SUBDIR_NAME] [SUFFIX]")
    out_dir = argv[1]
    subdir_name = argv[2] if len(argv) >= 3 else "callseq_r8m1a4_r3"
    suffix = argv[3] if len(argv) >= 4 else "_R2"
    callseq_dir = os.path.join(out_dir, subdir_name)

    units_file = os.path.join(out_dir, "CALLSEQ_UNITS_R8_M1a4_R3.tsv")
    cov_file = os.path.join(out_dir, "CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv")

    def outpath(base):
        return os.path.join(out_dir, base.replace("_R8_M1a4", "_R8_M1a4" + suffix))

    out_cmp = outpath("CALLSEQ_F2_F3_R8_M1a4.tsv")
    out_val = outpath("CALLSEQ_VALIDITY_R8_M1a4.tsv")
    out_kmax = outpath("CALLSEQ_KMAX_R8_M1a4.tsv")
    out_cov_chk = outpath("CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4.tsv")

    for f in (out_cmp, out_val, out_kmax, out_cov_chk):
        if os.path.exists(f):
            raise SystemExit("REFUSED: exists (U17): %s" % f)

    _, units = read_table(units_file)
    _, coverage = read_table(cov_file)

    # Group units by pair_id
    pairs = OrderedDict()
    for u in units:
        pid = u["pair_id"]
        pairs.setdefault(pid, {})[u["run_tree"]] = u

    cmp_rows = []
    val_rows = []
    kmax_rows = []
    unit_facts = {}

    identical_count = 0
    rename_count = 0
    different_count = 0

    for pid, pair in pairs.items():
        u_f2 = pair["F2"]
        u_f3 = pair["F3"]

        ev_f2 = read_events(os.path.join(callseq_dir, u_f2["unit_id"], "events.tsv"))
        ev_f3 = read_events(os.path.join(callseq_dir, u_f3["unit_id"], "events.tsv"))

        # Validity check
        with open(os.path.join(callseq_dir, u_f2["unit_id"], "summary.json"), encoding="utf-8") as fh:
            s_f2 = json.load(fh)
        with open(os.path.join(callseq_dir, u_f3["unit_id"], "summary.json"), encoding="utf-8") as fh:
            s_f3 = json.load(fh)

        v2_ok, v2_msg = check_validity(ev_f2, s_f2)
        v3_ok, v3_msg = check_validity(ev_f3, s_f3)

        val_rows.append({
            "pair_id": pid,
            "unit_f2": u_f2["unit_id"],
            "unit_f3": u_f3["unit_id"],
            "events_f2": len(ev_f2),
            "events_f3": len(ev_f3),
            "f2_valid": "VALID" if v2_ok else "INVALID",
            "f2_reason": v2_msg,
            "f3_valid": "VALID" if v3_ok else "INVALID",
            "f3_reason": v3_msg,
        })

        if not v2_ok or not v3_ok:
            raise SystemExit("TRACE_ERROR / VALIDITY_FAIL in pair %s: F2=(%s,%s), F3=(%s,%s)" % (
                pid, v2_ok, v2_msg, v3_ok, v3_msg))

        # Compare sequences
        cmp_status, cmp_note = compare_events(ev_f2, ev_f3)
        if cmp_status == "IDENTICAL":
            identical_count += 1
        elif cmp_status == "IDENTICAL_AFTER_RENAME":
            rename_count += 1
        else:
            different_count += 1

        cmp_rows.append({
            "pair_id": pid,
            "unit_f2": u_f2["unit_id"],
            "unit_f3": u_f3["unit_id"],
            "driver_family": u_f2["driver_family"],
            "mode": u_f2["mode"],
            "ng": u_f2["NG"],
            "route": u_f2["route"],
            "twice_env": u_f2["twice_env"],
            "events_f2": len(ev_f2),
            "events_f3": len(ev_f3),
            "status": cmp_status,
            "note": cmp_note,
        })

        # Extract Kmax facts
        facts_f2 = extract_kmax(ev_f2)
        facts_f3 = extract_kmax(ev_f3)
        unit_facts[u_f2["unit_id"]] = facts_f2
        unit_facts[u_f3["unit_id"]] = facts_f3

        kmax_rows.append({
            "pair_id": pid,
            "unit_f2": u_f2["unit_id"],
            "unit_f3": u_f3["unit_id"],
            "s4malloc_f2": facts_f2["s4malloc_max"],
            "s4malloc_f3": facts_f3["s4malloc_max"],
            "exec_f2": facts_f2["exec_max"],
            "exec_f3": facts_f3["exec_max"],
            "plan_f2": facts_f2["plan_max"],
            "plan_f3": facts_f3["plan_max"],
            "win_f2": facts_f2["win_max"],
            "win_f3": facts_f3["win_max"],
            "seam_sites_f2": len(facts_f2["seam_counts"]),
            "seam_sites_f3": len(facts_f3["seam_counts"]),
        })

    # Point coverage reachability check
    cov_chk_rows = []
    reached_count = 0
    unexp_count = 0
    unknown_count = 0
    for c in coverage:
        ccls = c["coverage_class"]
        uid = c["unit_id"]
        req = c["request"]
        pid = c["point_id"]

        if ccls == "N/A":
            reach_status, reach_note = "N/A", "no_injection_control"
        elif ccls == "ADDITION_REVIEW_SECTION7":
            reach_status, reach_note = "DEFERRED_TO_SECTION7", "S3R4_addition"
        else:
            facts = unit_facts[uid]
            reach_status, reach_note = check_reachability(req, facts)
            if reach_status == "REACHED":
                reached_count += 1
            elif reach_status == "UNEXPECTED_NOT_REACHED":
                unexp_count += 1
            elif reach_status == "UNKNOWN_REQUEST":
                unknown_count += 1

        cov_chk_rows.append({
            "source_registry": c["source_registry"],
            "source_row": c["source_row"],
            "point_id": pid,
            "pair_id": c["pair_id"],
            "group": c["group"],
            "source_tree": c["source_tree"],
            "run_tree": c["run_tree"],
            "request": req,
            "unit_id": uid,
            "coverage_class": ccls,
            "reach_status": reach_status,
            "details": reach_note,
        })

    # Write output files
    with open(out_cmp, "w", encoding="utf-8") as fh:
        fh.write("pair_id\tunit_f2\tunit_f3\tdriver_family\tmode\tng\troute\ttwice_env\tevents_f2\tevents_f3\tstatus\tnote\n")
        for r in cmp_rows:
            fh.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%d\t%s\t%s\n" % (
                r["pair_id"], r["unit_f2"], r["unit_f3"], r["driver_family"], r["mode"],
                r["ng"], r["route"], r["twice_env"], r["events_f2"], r["events_f3"], r["status"], r["note"]))

    with open(out_val, "w", encoding="utf-8") as fh:
        fh.write("pair_id\tunit_f2\tunit_f3\tevents_f2\tevents_f3\tf2_valid\tf2_reason\tf3_valid\tf3_reason\n")
        for r in val_rows:
            fh.write("%s\t%s\t%s\t%d\t%d\t%s\t%s\t%s\t%s\n" % (
                r["pair_id"], r["unit_f2"], r["unit_f3"], r["events_f2"], r["events_f3"],
                r["f2_valid"], r["f2_reason"], r["f3_valid"], r["f3_reason"]))

    with open(out_kmax, "w", encoding="utf-8") as fh:
        fh.write("pair_id\tunit_f2\tunit_f3\ts4malloc_f2\ts4malloc_f3\texec_f2\texec_f3\tplan_f2\tplan_f3\twin_f2\twin_f3\tseam_sites_f2\tseam_sites_f3\n")
        for r in kmax_rows:
            fh.write("%s\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%d\n" % (
                r["pair_id"], r["unit_f2"], r["unit_f3"], r["s4malloc_f2"], r["s4malloc_f3"],
                r["exec_f2"], r["exec_f3"], r["plan_f2"], r["plan_f3"], r["win_f2"], r["win_f3"],
                r["seam_sites_f2"], r["seam_sites_f3"]))

    with open(out_cov_chk, "w", encoding="utf-8") as fh:
        fh.write("source_registry\tsource_row\tpoint_id\tpair_id\tgroup\tsource_tree\trun_tree\trequest\tunit_id\tcoverage_class\treach_status\tdetails\n")
        for r in cov_chk_rows:
            fh.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                r["source_registry"], r["source_row"], r["point_id"], r["pair_id"], r["group"],
                r["source_tree"], r["run_tree"], r["request"], r["unit_id"], r["coverage_class"],
                r["reach_status"], r["details"]))

    print("COMPARE SUMMARY:")
    print("  Pairs compared: %d" % len(cmp_rows))
    print("    IDENTICAL: %d" % identical_count)
    print("    IDENTICAL_AFTER_RENAME: %d" % rename_count)
    print("    DIFFERENT: %d" % different_count)
    print("  Reachability check on %d coverage points:" % len(cov_chk_rows))
    print("    REACHED: %d" % reached_count)
    print("    N/A (control): %d" % len([r for r in cov_chk_rows if r["reach_status"] == "N/A"]))
    print("    ADDITIONS (section 7): %d" % len([r for r in cov_chk_rows if r["reach_status"] == "DEFERRED_TO_SECTION7"]))
    print("    UNKNOWN_REQUEST: %d" % unknown_count)
    print("    UNEXPECTED_NOT_REACHED: %d" % unexp_count)

    if different_count > 0:
        raise SystemExit("DIFFERENT count > 0 (technical stop per section 8)")
    if unknown_count > 0:
        raise SystemExit("UNKNOWN_REQUEST count > 0 (technical stop per section 8)")
    if unexp_count > 0:
        raise SystemExit("UNEXPECTED_NOT_REACHED count > 0 (technical stop per section 8)")

    print("ALL CHECKS PASSED: 0 DIFFERENT, 0 UNKNOWN, 0 UNEXPECTED_NOT_REACHED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
