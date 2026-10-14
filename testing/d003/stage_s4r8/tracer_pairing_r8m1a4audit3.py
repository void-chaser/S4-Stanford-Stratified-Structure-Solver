#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 3 (r8m1a4audit3), section 3: tracer pairing under U190.  New file.  Read only.

U190: for each unit (198 units of the 99 pairs of run _R3), out_of_scope did not happen if and only if the direct evidence holds:
  (a) the set of seq values of PLAN_START equals the set of seq values of PLAN_END   (per unit), and
  (b) the set of seq values of WIN_OPEN equals the set of seq values of WIN_CLOSE     (per unit), and
  (c) summary.json trace_error is null.
Basis (callseq_r8m1a4_gdb.py): each PLAN_START creates one FinishBreakpoint (PlanFinishBP); a creation failure writes trace_error.
The stop writes PLAN_END; out_of_scope only clears the flag and writes no event.  So stop and out_of_scope cannot both occur for one entry.
Output: one row per unit: unit_id, pair_id, plan_start_n, plan_end_n, plan_seq_eq, win_open_n, win_close_n, win_seq_eq, trace_error, verdict.
verdict = NO_OUT_OF_SCOPE_PROVEN when (a), (b) and (c) all hold; otherwise GAP.
Pair verdict: a pair is ALL_UNITS_PROVEN only when both units are NO_OUT_OF_SCOPE_PROVEN.  Otherwise the pair stays in the rerun scope.
Gap table: every GAP unit and its pair.  If the gap table is empty, the rerun pre-registration is WITHDRAWN (U190); otherwise only the scope is updated.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/tracer_pairing_r8m1a4audit3.py TRACER_PAIRING_R8_M1a4AUDIT3.tsv GAP_TABLE_R8_M1a4AUDIT3.tsv
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVR = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
EV = os.path.join(EVR, "m1a4audit3")
RAW = os.path.join(EVR, "callseq_r8m1a4_r3")
UNITS = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a", "CALLSEQ_UNITS_R8_M1a4_R3.tsv")
OUT_RE = re.compile(r"^(TRACER_PAIRING_R8_M1a4AUDIT3|GAP_TABLE_R8_M1a4AUDIT3)(_[A-Za-z0-9_]+)?\.tsv$")


def read_units():
    with open(UNITS, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    out = []
    for ln in lines[1:]:
        if not ln:
            continue
        cols = ln.split("\t")
        if len(cols) != len(hdr):
            raise SystemExit("REFUSED: units table column count")
        out.append(dict(zip(hdr, cols)))
    return out


def events_of(uid):
    path = os.path.join(RAW, uid, "events.tsv")
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    return [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln]


def main(argv):
    if len(argv) != 3 or not OUT_RE.match(argv[1]) or not OUT_RE.match(argv[2]):
        raise SystemExit("usage: tracer_pairing_r8m1a4audit3.py TRACER_PAIRING_R8_M1a4AUDIT3.tsv GAP_TABLE_R8_M1a4AUDIT3.tsv")
    out_t = os.path.join(EV, argv[1])
    out_g = os.path.join(EV, argv[2])
    if os.path.exists(out_t) or os.path.exists(out_g):
        raise SystemExit("REFUSED: exists (U17)")
    units = read_units()
    if len(units) != 198:
        raise SystemExit("REFUSED: units %d != 198" % len(units))

    rows = []
    gaps = []
    per_unit_ok = {}
    for u in units:
        uid = u["unit_id"]
        pid = u["pair_id"]
        ev = events_of(uid)
        with open(os.path.join(RAW, uid, "summary.json"), encoding="utf-8") as fh:
            summ = json.load(fh)
        ps = {int(e["seq"]) for e in ev if e["event_type"] == "PLAN_START"}
        pe = {int(e["seq"]) for e in ev if e["event_type"] == "PLAN_END"}
        wo = {int(e["seq"]) for e in ev if e["event_type"] == "WIN_OPEN"}
        wc = {int(e["seq"]) for e in ev if e["event_type"] == "WIN_CLOSE"}
        te = summ.get("trace_error")
        plan_eq = ps == pe
        win_eq = wo == wc
        te_ok = te is None
        ok = plan_eq and win_eq and te_ok
        verdict = "NO_OUT_OF_SCOPE_PROVEN" if ok else "GAP"
        per_unit_ok[uid] = ok
        rows.append((uid, pid, u["run_tree"], len(ps), len(pe), "yes" if plan_eq else "no",
                     len(wo), len(wc), "yes" if win_eq else "no", "NONE" if te is None else str(te), verdict))
        if not ok:
            gaps.append((uid, pid, u["run_tree"], len(ps), len(pe), len(wo), len(wc), str(te),
                         "plan_seq_eq=%s win_seq_eq=%s trace_error_none=%s" % (plan_eq, win_eq, te_ok)))

    # pairing: a pair is proven only when both its units are proven
    pairs = {}
    for u in units:
        pairs.setdefault(u["pair_id"], []).append(u["unit_id"])
    pair_rows = []
    pair_gaps = []
    for pid in sorted(pairs):
        us = pairs[pid]
        if len(us) != 2:
            raise SystemExit("REFUSED: pair %s has %d units" % (pid, len(us)))
        proven = all(per_unit_ok[x] for x in us)
        pair_rows.append((pid, us[0], us[1], "ALL_UNITS_PROVEN" if proven else "RERUN_IN_SCOPE"))
        if not proven:
            pair_gaps.append(pid)

    with open(out_t, "x", encoding="utf-8") as fh:
        fh.write("unit_id\tpair_id\trun_tree\tplan_start_n\tplan_end_n\tplan_seq_eq\twin_open_n\twin_close_n\t"
                 "win_seq_eq\ttrace_error\tverdict\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
        fh.write("#PAIRS\n")
        fh.write("pair_id\tunit_F2\tunit_F3\tpair_status\n")
        for p in pair_rows:
            fh.write("\t".join(p) + "\n")
    with open(out_g, "x", encoding="utf-8") as fh:
        fh.write("unit_id\tpair_id\trun_tree\tplan_start_n\tplan_end_n\twin_open_n\twin_close_n\ttrace_error\treason\n")
        for g in gaps:
            fh.write("\t".join(str(x) for x in g) + "\n")
        fh.write("#PAIR_GAPS\t%d\n" % len(pair_gaps))
    print("units=%d proven=%d gap=%d" % (len(rows), sum(1 for r in rows if r[-1] == "NO_OUT_OF_SCOPE_PROVEN"), len(gaps)))
    print("pairs=%d all_units_proven=%d rerun_in_scope=%d" % (len(pair_rows), len(pair_rows) - len(pair_gaps), len(pair_gaps)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
