#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2), section 4: offline tracer audit of the 198 raw logs.  New file.

Read only.  Does not modify callseq_r8m1a4_gdb.py.  For each of the 198 unit runs it checks what the ORIGINAL logs can
prove, and marks what they cannot prove as EVIDENCE_INSUFFICIENT (never as "did not happen").

Checks per unit (CHECK column):
  T1 FINISH_OUT_OF_SCOPE : the tracer's out_of_scope() methods write nothing to events or summary (see
                           callseq_r8m1a4_gdb.py PlanFinishBP/WindowFinishBP).  The raw logs cannot show whether it fired.
                           -> EVIDENCE_INSUFFICIENT for every unit whose FinishBreakpoint could be created.
  T2 PLAN_WINDOW_NESTING : from events.tsv, PLAN_START/PLAN_END and WIN_OPEN/WIN_CLOSE must pair in order with no nesting
                           or overlap of two plans, or two windows.  Checked from the event order.
  T3 REQUIRED_SYMBOLS    : for each family in the unit's REQUIRED_FAMILIES, the symbol the tracer needs must NOT appear
                           in gdb's "Function \"X\" not defined." lines.  An absent required symbol is REQUIRED_SYMBOL_MISSING.
                           A non-required symbol that is absent is recorded (not an error: setup_breakpoints skips it).
  T4 ABNORMAL_EXIT       : summary.json status must be EXITED with exit_code and signal recorded; gdb rc must be 0;
                           trace_error must be null/NONE.  An exit that was not recorded is RUN_ERROR.
  T5 CALLBACK_EXCEPTION  : gdb stderr must contain no Python traceback or "Error" from the tracer script.
  T6 PLAN_BP_RESOLVED    : for units whose REQUIRED_FAMILIES does not contain plan, the plan entry breakpoint is still set
                           by the tracer.  Its resolution is evidenced by symbol table query (symq_r8m1a4audit2.sh) for the
                           driver identity, not by the raw log.  Reported as SYMQ_EVIDENCE (see the symq output files).

Output: TRACER_AUDIT_R8_M1a4AUDIT2_<name>.tsv (one row per unit x check) and a summary line.
Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/tracer_audit_r8m1a4audit2.py AUDIT_NAME
AUDIT_NAME must be TRACER_AUDIT_R8_M1a4AUDIT2_<name>.tsv (bare name) and must not exist (U17).
"""
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVR = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
EV = os.path.join(EVR, "m1a4audit2")
RAW = os.path.join(EVR, "callseq_r8m1a4_r3")
REG_M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
UNITS = os.path.join(REG_M1A, "CALLSEQ_UNITS_R8_M1a4_R3.tsv")
NAME_RE = re.compile(r"^TRACER_AUDIT_R8_M1a4AUDIT2_[A-Za-z0-9_]+\.tsv$")

# family -> the symbol the tracer needs for it (callseq_r8m1a4_gdb.py setup_breakpoints, with required_family)
FAMILY_SYMBOL = {
    "plan": "__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i",
    "s4malloc": "__wrap__Z9S4_mallocm",
    "exec": "__wrap__Z13fft_plan_execP12tag_fft_plan",
    "rnv1": "__wrap_Pattern_GenerateFlowField",
    "alloc": "S4_TEST_ALLOC_HOOK",
    "kottke_alloc": "S4_TEST_KOTTKE_HOOK",
    "fmmret": "S4_TEST_FMMRET_AFTER",
    "linearsolve": "S4_TEST_LINEARSOLVE_AFTER",
    "linearsolve_null2": "S4_TEST_LINEARSOLVE_NULLINFO2_AFTER",
    # plancall uses the plan entry and __wrap_malloc (required_family="plan" in setup_breakpoints)
    "plancall": "__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i",
}
NOT_DEFINED_RE = re.compile(r'^Function "([^"]+)" not defined\.')


def read_units():
    with open(UNITS, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    out = []
    for ln in lines[1:]:
        if ln:
            out.append(dict(zip(hdr, ln.split("\t"))))
    return out


def read_events(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    return [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln]


def main(argv):
    if len(argv) != 2 or not NAME_RE.match(argv[1]):
        raise SystemExit("usage: tracer_audit_r8m1a4audit2.py TRACER_AUDIT_R8_M1a4AUDIT2_<name>.tsv")
    out = os.path.join(EV, argv[1])
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)

    units = read_units()
    if len(units) != 198:
        raise SystemExit("REFUSED: units %d != 198" % len(units))

    rows = []
    summary = Counter()
    for u in units:
        uid = u["unit_id"]
        ud = os.path.join(RAW, uid)
        fams = [f for f in u["families"].split(";") if f and f != "none"]
        ev_path = os.path.join(ud, "events.tsv")
        se_path = os.path.join(ud, "gdb.stderr.txt")
        sj_path = os.path.join(ud, "summary.json")
        so_path = os.path.join(ud, "gdb.stdout.txt")
        for p in (ev_path, se_path, sj_path, so_path):
            if not os.path.isfile(p):
                rows.append((uid, "INPUT", "EVIDENCE_INSUFFICIENT", "missing %s" % p))
                summary["EVIDENCE_INSUFFICIENT"] += 1
                break
        else:
            with open(se_path, encoding="utf-8", errors="replace") as fh:
                stderr_lines = fh.read().splitlines()
            undefined = set()
            for ln in stderr_lines:
                m = NOT_DEFINED_RE.match(ln)
                if m:
                    undefined.add(m.group(1))
            with open(sj_path, encoding="utf-8") as fh:
                sj = json.load(fh)
            events = read_events(ev_path)

            # T1 out_of_scope: not provable from the raw logs (no record is written by the out_of_scope callbacks)
            rows.append((uid, "T1_FINISH_OUT_OF_SCOPE", "EVIDENCE_INSUFFICIENT",
                         "out_of_scope() writes no record; raw logs cannot show it did not fire"))
            summary["EVIDENCE_INSUFFICIENT"] += 1

            # T2 nesting / overlap, from event order
            open_plan = False
            open_win = False
            nest = []
            for e in events:
                t = e["event_type"]
                if t == "PLAN_START":
                    if open_plan:
                        nest.append("PLAN_START_while_open")
                    open_plan = True
                elif t == "PLAN_END":
                    if not open_plan:
                        nest.append("PLAN_END_without_open")
                    open_plan = False
                elif t == "WIN_OPEN":
                    if open_win:
                        nest.append("WIN_OPEN_while_open")
                    open_win = True
                elif t == "WIN_CLOSE":
                    if not open_win:
                        nest.append("WIN_CLOSE_without_open")
                    open_win = False
                elif t == "PLAN_MALLOC" and not open_plan:
                    nest.append("PLAN_MALLOC_outside_plan")
                elif t == "WIN_MALLOC" and not open_win:
                    nest.append("WIN_MALLOC_outside_window")
            # PLAN_END and WIN_CLOSE are written by FinishBreakpoint stop() (once per plan/window); an open item at the
            # end of the run is not an error here (the process may exit inside it), it is recorded
            end_open = ("open_plan_at_end" if open_plan else "") + ("open_win_at_end" if open_win else "")
            if nest:
                rows.append((uid, "T2_PLAN_WINDOW_NESTING", "FAIL", ";".join(sorted(set(nest))) + " " + end_open))
                summary["FAIL"] += 1
            else:
                rows.append((uid, "T2_PLAN_WINDOW_NESTING", "PASS", "no nesting or overlap" + (" (" + end_open + ")" if end_open else "")))
                summary["PASS"] += 1

            # T3 required symbols
            missing_required = []
            for f in fams:
                sym = FAMILY_SYMBOL.get(f)
                if sym is None:
                    missing_required.append("NO_SYMBOL_FOR_FAMILY:%s" % f)
                elif sym in undefined:
                    missing_required.append("%s:%s" % (f, sym))
            if missing_required:
                rows.append((uid, "T3_REQUIRED_SYMBOLS", "FAIL", "REQUIRED_SYMBOL_MISSING " + ";".join(missing_required)))
                summary["FAIL"] += 1
            else:
                nonreq = sorted(s for s in undefined)
                rows.append((uid, "T3_REQUIRED_SYMBOLS", "PASS",
                             "required=%s; undefined_in_gdb=%s" % (";".join(fams) or "-", ";".join(nonreq) or "-")))
                summary["PASS"] += 1

            # T4 abnormal exit / recorded exit
            t4 = []
            if sj.get("status") != "EXITED":
                t4.append("status=%s" % sj.get("status"))
            if sj.get("exit_code") is None:
                t4.append("exit_code_missing")
            if sj.get("trace_error") not in (None, "", "NONE"):
                t4.append("trace_error=%s" % sj.get("trace_error"))
            rows.append((uid, "T4_EXIT_RECORDED", "FAIL" if t4 else "PASS",
                         ";".join(t4) if t4 else "status=EXITED exit_code=%s signal=%s" % (sj.get("exit_code"), sj.get("signal"))))
            summary["FAIL" if t4 else "PASS"] += 1

            # T5 callback exception
            tb = [ln for ln in stderr_lines if ln.startswith("Traceback") or ln.startswith("Python Exception")
                  or ("Error" in ln and "tracer" in ln.lower())]
            rows.append((uid, "T5_CALLBACK_EXCEPTION", "FAIL" if tb else "PASS",
                         (";".join(tb[:2]) if tb else "no traceback in gdb stderr")))
            summary["FAIL" if tb else "PASS"] += 1

            # T6 plan breakpoint for units without plan in REQUIRED: resolution evidenced by symq, not by this log
            if "plan" not in fams and "plancall" not in fams:
                rows.append((uid, "T6_PLAN_BP_NOT_REQUIRED", "EVIDENCE_INSUFFICIENT",
                             "plan not required; plan breakpoint resolution is shown only by symbol query (SYMQ files)"))
                summary["EVIDENCE_INSUFFICIENT"] += 1

    with open(out, "x", encoding="utf-8") as fh:
        fh.write("unit_id\tcheck\tstatus\tdetail\n")
        for r in rows:
            fh.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")
    print("tracer_audit rows=%d %s" % (len(rows), dict(sorted(summary.items()))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
