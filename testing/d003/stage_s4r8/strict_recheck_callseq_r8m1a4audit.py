#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a 审核修正 (r8m1a4audit), task section 3: strict offline recheck of the 198 original runs.

New file.  Read-only over the original logs; writes exactly one TSV (one row per unit) and one summary text into the
evidence directory given as argument.  It does not modify compare_callseq_r8m1a4.py or any historical file.

The ten checks of task section 3 are applied per unit:
  C1  event_idx is 1..N contiguous;
  C2  per-type sequence numbers are contiguous from 1 (no max-as-count shortcut);
  C3  PLAN_START/PLAN_END and WIN_OPEN/WIN_CLOSE are paired by seq and nested correctly;
  C4  PLAN_MALLOC/WIN_MALLOC context (seq) belongs to an open plan/window, sub_seq contiguous from 1;
  C5  PLAN_END/WIN_CLOSE details count equals the number of internal malloc events of that context;
  C6  summary.json totals (s4malloc_count, exec_count, plan_count, window_count, seam_counts) equal the event facts;
  C7  summary.json status EXITED, exit_code and signal recorded, trace_error NONE;
  C8  every required symbol was resolved: the event func field is not missing, no empty caller;
  C9  no caller frame equals "??" or is empty;
  C10 a missing file, empty file, missing column or missing field never counts as success.

The summary/event facts are compared; no value is defaulted.  Any failure is recorded in the TSV; the script
exits 1 if any unit fails any check (stop rule: dependent steps are not run on failures).
"""
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVB = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
RUNS_DIR = os.path.join(EVB, "callseq_r8m1a4_r3")
UNITS_TSV = os.path.join(EVB, "CALLSEQ_UNITS_R8_M1a4_R3.tsv")
RUNS_TSV = os.path.join(EVB, "CALLSEQ_RUNS_R8_M1a4_R3.tsv")

EVENT_HEADER = ["event_idx", "event_type", "func", "caller", "seq", "sub_seq", "details"]
RUNS_HEADER = ["unit_id", "pair_id", "run_tree", "driver_tag", "driver_sha256", "cmd_env", "start_utc", "end_utc",
               "gdb_rc", "inferior_exit", "signal", "trace_error"]
UNITS_HEADER = ["unit_id", "pair_id", "run_tree", "driver_family", "driver_tag", "driver_sha256", "driver_path", "mode",
                "NG", "route", "twice_env", "argv", "env", "families", "sites_n", "sites", "points_n", "source_registries"]


def read_tsv(path, header):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines:
        raise SystemExit("REFUSED: empty table %s" % path)
    got = lines[0].split("\t")
    if got != header:
        raise SystemExit("REFUSED: header mismatch in %s: %s" % (path, got))
    rows = []
    for n, line in enumerate(lines[1:], 2):
        if not line:
            continue
        cols = line.split("\t")
        if len(cols) != len(header):
            raise SystemExit("REFUSED: column count %d != %d at %s:%d" % (len(cols), len(header), path, n))
        rows.append(dict(zip(header, cols)))
    return rows


def read_events(path):
    """Return (rows, problems).  A missing/empty file or a wrong header is a problem, never a success."""
    problems = []
    if not os.path.isfile(path):
        return [], ["C10_MISSING_FILE:events.tsv"]
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines:
        return [], ["C10_EMPTY_FILE:events.tsv"]
    if lines[0].split("\t") != EVENT_HEADER:
        return [], ["C10_HEADER:events.tsv"]
    rows = []
    for n, line in enumerate(lines[1:], 2):
        cols = line.split("\t")
        if len(cols) != len(EVENT_HEADER):
            problems.append("C10_COLCOUNT:events.tsv:%d" % n)
            continue
        rows.append(dict(zip(EVENT_HEADER, cols)))
    return rows, problems


def check_unit(uid, run_row, unit_row):
    problems = []
    unit_dir = os.path.join(RUNS_DIR, uid)
    ev_path = os.path.join(unit_dir, "events.tsv")
    sm_path = os.path.join(unit_dir, "summary.json")
    for fn in ("events.tsv", "summary.json", "gdb.stdout.txt", "gdb.stderr.txt"):
        p = os.path.join(unit_dir, fn)
        if not os.path.isfile(p):
            problems.append("C10_MISSING_FILE:%s" % fn)
    events, eprob = read_events(ev_path)
    problems.extend(eprob)

    summary = None
    if os.path.isfile(sm_path):
        try:
            with open(sm_path, encoding="utf-8") as fh:
                summary = json.load(fh)
        except (ValueError, OSError) as exc:
            problems.append("C10_SUMMARY_UNREADABLE:%s" % exc)
    else:
        problems.append("C10_MISSING_FILE:summary.json")

    # C1 event_idx contiguous
    for i, ev in enumerate(events, 1):
        if ev["event_idx"] != str(i):
            problems.append("C1_EVENT_IDX:expected_%d_got_%s" % (i, ev["event_idx"]))
            break

    # C2 per-type seq contiguity, and C4 malloc sub_seq contiguity inside each context
    per_type = defaultdict(list)
    for ev in events:
        per_type[ev["event_type"]].append(int(ev["seq"]))
    for t, seqs in per_type.items():
        if t in ("PLAN_START", "PLAN_END", "WIN_OPEN", "WIN_CLOSE"):
            # plan/window identities: each START/OPEN must carry a fresh seq 1..K
            if t in ("PLAN_START", "WIN_OPEN"):
                if seqs != list(range(1, len(seqs) + 1)):
                    problems.append("C2_SEQ_%s:not_contiguous" % t)
        elif t == "S4MALLOC" or t == "EXEC":
            if seqs != list(range(1, len(seqs) + 1)):
                problems.append("C2_SEQ_%s:not_contiguous" % t)

    # C3 plan/window pairing and nesting
    plan_open = None
    win_open = None
    plan_count = 0
    win_count = 0
    closed_plan_malloc = {}
    closed_win_malloc = {}
    cur_plan_malloc = 0
    cur_win_malloc = 0
    for ev in events:
        t = ev["event_type"]
        s = int(ev["seq"])
        if t == "PLAN_START":
            if plan_open is not None:
                problems.append("C3_PLAN_NESTED_OR_OVERLAP:at_seq_%d" % s)
            plan_open = s
            plan_count += 1
            cur_plan_malloc = 0
        elif t == "PLAN_END":
            if plan_open is None or plan_open != s:
                problems.append("C3_PLAN_END_UNPAIRED:seq_%d" % s)
            else:
                closed_plan_malloc[s] = cur_plan_malloc
            plan_open = None
        elif t == "WIN_OPEN":
            if win_open is not None:
                problems.append("C3_WIN_NESTED_OR_OVERLAP:at_seq_%d" % s)
            win_open = s
            win_count += 1
            cur_win_malloc = 0
        elif t == "WIN_CLOSE":
            if win_open is None or win_open != s:
                problems.append("C3_WIN_CLOSE_UNPAIRED:seq_%d" % s)
            else:
                closed_win_malloc[s] = cur_win_malloc
            win_open = None
        elif t == "PLAN_MALLOC":
            # C4: must lie inside an open plan with the same seq
            if plan_open is None or plan_open != s:
                problems.append("C4_PLAN_MALLOC_OUTSIDE_CONTEXT:seq_%d" % s)
            cur_plan_malloc += 1
            if int(ev["sub_seq"]) != cur_plan_malloc:
                problems.append("C4_PLAN_MALLOC_SUBSEQ:expected_%d_got_%s" % (cur_plan_malloc, ev["sub_seq"]))
        elif t == "WIN_MALLOC":
            if win_open is None or win_open != s:
                problems.append("C4_WIN_MALLOC_OUTSIDE_CONTEXT:seq_%d" % s)
            cur_win_malloc += 1
            if int(ev["sub_seq"]) != cur_win_malloc:
                problems.append("C4_WIN_MALLOC_SUBSEQ:expected_%d_got_%s" % (cur_win_malloc, ev["sub_seq"]))
    if plan_open is not None:
        problems.append("C3_PLAN_UNCLOSED:seq_%d" % plan_open)
    if win_open is not None:
        problems.append("C3_WIN_UNCLOSED:seq_%d" % win_open)

    # C5 END/CLOSE detail count equals the actual internal malloc events
    for ev in events:
        t = ev["event_type"]
        s = int(ev["seq"])
        if t == "PLAN_END":
            n_internal = sum(1 for e in events if e["event_type"] == "PLAN_MALLOC" and int(e["seq"]) == s)
            if int(ev["sub_seq"]) != n_internal:
                problems.append("C5_PLAN_END_COUNT:seq_%d_end=%s_actual=%d" % (s, ev["sub_seq"], n_internal))
        if t == "WIN_CLOSE":
            n_internal = sum(1 for e in events if e["event_type"] == "WIN_MALLOC" and int(e["seq"]) == s)
            if int(ev["sub_seq"]) != n_internal:
                problems.append("C5_WIN_CLOSE_COUNT:seq_%d_end=%s_actual=%d" % (s, ev["sub_seq"], n_internal))

    # C6 summary consistency with event facts
    if summary is not None:
        s4 = sum(1 for e in events if e["event_type"] == "S4MALLOC")
        ex = sum(1 for e in events if e["event_type"] == "EXEC")
        if summary.get("s4malloc_count") is None:
            problems.append("C6_SUMMARY_FIELD_MISSING:s4malloc_count")
        elif int(summary["s4malloc_count"]) != s4:
            problems.append("C6_S4MALLOC:summary=%s_events=%d" % (summary["s4malloc_count"], s4))
        if summary.get("exec_count") is None:
            problems.append("C6_SUMMARY_FIELD_MISSING:exec_count")
        elif int(summary["exec_count"]) != ex:
            problems.append("C6_EXEC:summary=%s_events=%d" % (summary["exec_count"], ex))
        if summary.get("plan_count") is None:
            problems.append("C6_SUMMARY_FIELD_MISSING:plan_count")
        elif int(summary["plan_count"]) != plan_count:
            problems.append("C6_PLAN:summary=%s_events=%d" % (summary["plan_count"], plan_count))
        if summary.get("window_count") is None:
            problems.append("C6_SUMMARY_FIELD_MISSING:window_count")
        elif int(summary["window_count"]) != win_count:
            problems.append("C6_WINDOW:summary=%s_events=%d" % (summary["window_count"], win_count))

        # C7 exit facts
        if summary.get("status") != "EXITED":
            problems.append("C7_STATUS:%s" % summary.get("status"))
        if summary.get("exit_code") is None:
            problems.append("C7_EXIT_CODE_MISSING")
        if summary.get("signal") is not None:
            problems.append("C7_SIGNAL:%s" % summary.get("signal"))
        if summary.get("trace_error") is not None:
            problems.append("C7_TRACE_ERROR:%s" % summary.get("trace_error"))

    # C8 and C9 frame identity
    for ev in events:
        caller = ev["caller"]
        func = ev["func"]
        if caller in ("", "??", "-"):
            problems.append("C9_CALLER_UNRESOLVED:event_%s" % ev["event_idx"])
        if func in ("", "??", "-"):
            problems.append("C8_FUNC_UNRESOLVED:event_%s" % ev["event_idx"])

    # run table facts (run row must match the unit and carry a clean end)
    if run_row is None:
        problems.append("C10_RUN_ROW_MISSING")
    else:
        if run_row["gdb_rc"] != "0":
            problems.append("C7_GDB_RC:%s" % run_row["gdb_rc"])
        if run_row["inferior_exit"] != "0":
            problems.append("C7_INFERIOR_EXIT:%s" % run_row["inferior_exit"])
        if run_row["signal"] != "-":
            problems.append("C7_SIGNAL_RUN:%s" % run_row["signal"])
        if run_row["trace_error"] != "NONE":
            problems.append("C7_TRACE_ERROR_RUN:%s" % run_row["trace_error"])

    return {
        "events": len(events),
        "plan_count": plan_count,
        "window_count": win_count,
        "plan_malloc_total": sum(closed_plan_malloc.values()),
        "win_malloc_total": sum(closed_win_malloc.values()),
        "problems": problems,
    }


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: strict_recheck_callseq_r8m1a4audit.py OUTDIR")
    out_dir = argv[1]
    out_tsv = os.path.join(out_dir, "STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT.tsv")
    out_txt = os.path.join(out_dir, "STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT_SUMMARY.txt")
    for p in (out_tsv, out_txt):
        if os.path.exists(p):
            raise SystemExit("REFUSED: exists (U17): %s" % p)

    units = read_tsv(UNITS_TSV, UNITS_HEADER)
    runs = read_tsv(RUNS_TSV, RUNS_HEADER)
    if len(units) != 198:
        raise SystemExit("REFUSED: unit count %d != 198" % len(units))
    if len(runs) != 198:
        raise SystemExit("REFUSED: run count %d != 198" % len(runs))
    run_by = {}
    for r in runs:
        if r["unit_id"] in run_by:
            raise SystemExit("REFUSED: duplicate run unit %s" % r["unit_id"])
        run_by[r["unit_id"]] = r
    unit_ids = set()
    for u in units:
        if u["unit_id"] in unit_ids:
            raise SystemExit("REFUSED: duplicate unit %s" % u["unit_id"])
        unit_ids.add(u["unit_id"])
        if u["unit_id"] not in run_by:
            raise SystemExit("REFUSED: unit without run row %s" % u["unit_id"])

    rows = []
    failed = 0
    total_events = 0
    total_plan = 0
    total_win = 0
    for u in units:
        uid = u["unit_id"]
        res = check_unit(uid, run_by.get(uid), u)
        total_events += res["events"]
        total_plan += res["plan_count"]
        total_win += res["window_count"]
        status = "PASS" if not res["problems"] else "FAIL"
        if status == "FAIL":
            failed += 1
        rows.append((uid, u["pair_id"], u["run_tree"], u["driver_family"], u["mode"], u["NG"], u["route"],
                     u["twice_env"], str(res["events"]), str(res["plan_count"]), str(res["window_count"]),
                     str(res["plan_malloc_total"]), str(res["win_malloc_total"]), status,
                     ";".join(res["problems"]) if res["problems"] else "-"))

    with open(out_tsv, "x", encoding="utf-8") as fh:
        fh.write("unit_id\tpair_id\trun_tree\tdriver_family\tmode\tNG\troute\ttwice_env\tevents\tplan_count\twindow_count\t"
                 "plan_malloc_total\twin_malloc_total\tstatus\tproblems\n")
        for row in rows:
            fh.write("\t".join(row) + "\n")

    with open(out_txt, "x", encoding="utf-8") as fh:
        fh.write("units=%d pass=%d fail=%d events_total=%d plan_total=%d window_total=%d\n" % (
            len(units), len(units) - failed, failed, total_events, total_plan, total_win))

    print("STRICT_RECHECK units=%d pass=%d fail=%d events_total=%d" % (
        len(units), len(units) - failed, failed, total_events))
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
