# callseq_r8m1a4_gdb.py -- P05-S4 R8 M1a CONT3a gdb in-process python tracer.  New file.
# Runs inside gdb: gdb -batch -nx -x callseq_r8m1a4_gdb.py
# Invoked via environment:
#   CALLSEQ_OUT_DIR: output directory for events.tsv and run_summary.json
#   CALLSEQ_FAMILIES: semicolon-separated required families (e.g., "s4malloc;plan;exec")
#   CALLSEQ_TREE: F2 or F3
#   CALLSEQ_UNIT_ID: U0001..
# All stop() return False (no stop of inferior).
# Captures plan/window entry/finish with FinishBreakpoint, counts per-family/site, records exit facts.
import json
import os
import sys

import gdb

OUT_DIR = os.environ.get("CALLSEQ_OUT_DIR", "")
FAMILIES_STR = os.environ.get("CALLSEQ_FAMILIES", "")
UNIT_ID = os.environ.get("CALLSEQ_UNIT_ID", "U_UNKNOWN")
TREE = os.environ.get("CALLSEQ_TREE", "")
REQUIRED_FAMILIES = set(f for f in FAMILIES_STR.split(";") if f and f != "none")

EVENTS = []
SUMMARY = {
    "unit_id": UNIT_ID,
    "tree": TREE,
    "status": "INIT",
    "exit_code": None,
    "signal": None,
    "trace_error": None,
    "plan_count": 0,
    "window_count": 0,
    "s4malloc_count": 0,
    "exec_count": 0,
    "seam_counts": {},
}

INSIDE_PLAN = False
CURRENT_PLAN_SEQ = 0
CURRENT_PLAN_MALLOC_SEQ = 0

INSIDE_WINDOW = False
CURRENT_WINDOW_SEQ = 0
CURRENT_WIN_MALLOC_SEQ = 0

GLOBAL_S4MALLOC_SEQ = 0
GLOBAL_EXEC_SEQ = 0
SEAM_SITE_COUNTS = {}


def get_caller():
    """Get frame #1 caller name if available."""
    try:
        f = gdb.selected_frame()
        if f:
            f1 = f.older()
            if f1:
                name = f1.name()
                return name if name else "??"
    except Exception:
        pass
    return "??"


def read_hook_arg(frame, arg_name="id"):
    """Read first integer argument: try DWARF variable, fallback to x86_64 $rdi at function entry."""
    try:
        val = frame.read_var(arg_name)
        return int(val)
    except Exception:
        pass
    try:
        rdi = gdb.parse_and_eval("$rdi")
        return int(rdi)
    except Exception:
        pass
    return None


class PlanFinishBP(gdb.FinishBreakpoint):
    def __init__(self, frame, plan_seq):
        super(PlanFinishBP, self).__init__(frame, internal=True)
        self.plan_seq = plan_seq

    def stop(self):
        global INSIDE_PLAN
        INSIDE_PLAN = False
        caller = get_caller()
        EVENTS.append({
            "type": "PLAN_END",
            "func": "fft_plan_dft_2d",
            "caller": caller,
            "seq": self.plan_seq,
            "sub_seq": CURRENT_PLAN_MALLOC_SEQ,
            "details": "malloc_in_plan=%d" % CURRENT_PLAN_MALLOC_SEQ,
        })
        return False

    def out_of_scope(self):
        global INSIDE_PLAN
        INSIDE_PLAN = False


class WindowFinishBP(gdb.FinishBreakpoint):
    def __init__(self, frame, win_seq):
        super(WindowFinishBP, self).__init__(frame, internal=True)
        self.win_seq = win_seq

    def stop(self):
        global INSIDE_WINDOW
        INSIDE_WINDOW = False
        caller = get_caller()
        EVENTS.append({
            "type": "WIN_CLOSE",
            "func": "Pattern_GenerateFlowField",
            "caller": caller,
            "seq": self.win_seq,
            "sub_seq": CURRENT_WIN_MALLOC_SEQ,
            "details": "malloc_in_window=%d" % CURRENT_WIN_MALLOC_SEQ,
        })
        return False

    def out_of_scope(self):
        global INSIDE_WINDOW
        INSIDE_WINDOW = False


class PlanEntryBP(gdb.Breakpoint):
    def stop(self):
        global INSIDE_PLAN, CURRENT_PLAN_SEQ, CURRENT_PLAN_MALLOC_SEQ
        CURRENT_PLAN_SEQ += 1
        CURRENT_PLAN_MALLOC_SEQ = 0
        INSIDE_PLAN = True
        SUMMARY["plan_count"] = CURRENT_PLAN_SEQ
        caller = get_caller()
        EVENTS.append({
            "type": "PLAN_START",
            "func": "fft_plan_dft_2d",
            "caller": caller,
            "seq": CURRENT_PLAN_SEQ,
            "sub_seq": 0,
            "details": "-",
        })
        try:
            PlanFinishBP(gdb.selected_frame(), CURRENT_PLAN_SEQ)
        except Exception as e:
            SUMMARY["trace_error"] = "PlanFinishBP_error: %s" % e
        return False


class WindowEntryBP(gdb.Breakpoint):
    def stop(self):
        global INSIDE_WINDOW, CURRENT_WINDOW_SEQ, CURRENT_WIN_MALLOC_SEQ
        CURRENT_WINDOW_SEQ += 1
        CURRENT_WIN_MALLOC_SEQ = 0
        INSIDE_WINDOW = True
        SUMMARY["window_count"] = CURRENT_WINDOW_SEQ
        caller = get_caller()
        EVENTS.append({
            "type": "WIN_OPEN",
            "func": "Pattern_GenerateFlowField",
            "caller": caller,
            "seq": CURRENT_WINDOW_SEQ,
            "sub_seq": 0,
            "details": "-",
        })
        try:
            WindowFinishBP(gdb.selected_frame(), CURRENT_WINDOW_SEQ)
        except Exception as e:
            SUMMARY["trace_error"] = "WindowFinishBP_error: %s" % e
        return False


class WrappedMallocBP(gdb.Breakpoint):
    def stop(self):
        global CURRENT_PLAN_MALLOC_SEQ, CURRENT_WIN_MALLOC_SEQ
        caller = get_caller()
        if INSIDE_PLAN:
            CURRENT_PLAN_MALLOC_SEQ += 1
            EVENTS.append({
                "type": "PLAN_MALLOC",
                "func": "__wrap_malloc",
                "caller": caller,
                "seq": CURRENT_PLAN_SEQ,
                "sub_seq": CURRENT_PLAN_MALLOC_SEQ,
                "details": "plan_call=%d;alloc=%d" % (CURRENT_PLAN_SEQ, CURRENT_PLAN_MALLOC_SEQ),
            })
        elif INSIDE_WINDOW:
            CURRENT_WIN_MALLOC_SEQ += 1
            EVENTS.append({
                "type": "WIN_MALLOC",
                "func": "__wrap_malloc",
                "caller": caller,
                "seq": CURRENT_WINDOW_SEQ,
                "sub_seq": CURRENT_WIN_MALLOC_SEQ,
                "details": "win_call=%d;alloc=%d" % (CURRENT_WINDOW_SEQ, CURRENT_WIN_MALLOC_SEQ),
            })
        return False


class S4MallocBP(gdb.Breakpoint):
    def stop(self):
        global GLOBAL_S4MALLOC_SEQ
        GLOBAL_S4MALLOC_SEQ += 1
        SUMMARY["s4malloc_count"] = GLOBAL_S4MALLOC_SEQ
        caller = get_caller()
        EVENTS.append({
            "type": "S4MALLOC",
            "func": "S4_malloc",
            "caller": caller,
            "seq": GLOBAL_S4MALLOC_SEQ,
            "sub_seq": 0,
            "details": "-",
        })
        return False


class ExecBP(gdb.Breakpoint):
    def stop(self):
        global GLOBAL_EXEC_SEQ
        GLOBAL_EXEC_SEQ += 1
        SUMMARY["exec_count"] = GLOBAL_EXEC_SEQ
        caller = get_caller()
        EVENTS.append({
            "type": "EXEC",
            "func": "fft_plan_exec",
            "caller": caller,
            "seq": GLOBAL_EXEC_SEQ,
            "sub_seq": 0,
            "details": "-",
        })
        return False


class SeamHookBP(gdb.Breakpoint):
    def __init__(self, spec, hook_name, arg_name="id", **kwargs):
        super(SeamHookBP, self).__init__(spec, **kwargs)
        self.hook_name = hook_name
        self.arg_name = arg_name

    def stop(self):
        frame = gdb.selected_frame()
        hook_id = read_hook_arg(frame, self.arg_name)
        if hook_id is None:
            SUMMARY["trace_error"] = "could_not_read_hook_id_for_%s" % self.hook_name
            hook_id = -1
        site_key = "%s:%s" % (self.hook_name, hook_id)
        SEAM_SITE_COUNTS[site_key] = SEAM_SITE_COUNTS.get(site_key, 0) + 1
        call_seq = SEAM_SITE_COUNTS[site_key]
        SUMMARY["seam_counts"][site_key] = call_seq
        caller = get_caller()
        EVENTS.append({
            "type": "SEAM",
            "func": self.hook_name,
            "caller": caller,
            "seq": call_seq,
            "sub_seq": hook_id,
            "details": "site=%s;k=%d" % (site_key, call_seq),
        })
        return False


def setup_breakpoints():
    # Helper to set a breakpoint if symbol exists
    def try_bp(cls, *args, **kwargs):
        req_fam = kwargs.pop("required_family", None)
        spec = args[0]
        try:
            cls(*args, internal=True, **kwargs)
            return True
        except Exception as e:
            if req_fam and req_fam in REQUIRED_FAMILIES:
                msg = "REQUIRED_SYMBOL_MISSING: %s for family %s: %s" % (spec, req_fam, e)
                SUMMARY["trace_error"] = msg
                raise SystemExit(msg)
            return False

    # plan & plancall
    try_bp(PlanEntryBP, "__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i", required_family="plan")
    # malloc inside plan/window
    try_bp(WrappedMallocBP, "__wrap_malloc", required_family="plan")
    # s4malloc
    try_bp(S4MallocBP, "__wrap__Z9S4_mallocm", required_family="s4malloc")
    # exec
    try_bp(ExecBP, "__wrap__Z13fft_plan_execP12tag_fft_plan", required_family="exec")
    # rnv1
    try_bp(WindowEntryBP, "__wrap_Pattern_GenerateFlowField", required_family="rnv1")
    # seam hooks
    try_bp(SeamHookBP, "S4_TEST_ALLOC_HOOK", "S4_TEST_ALLOC_HOOK", "id", required_family="alloc")
    try_bp(SeamHookBP, "S4_TEST_KOTTKE_HOOK", "S4_TEST_KOTTKE_HOOK", "id", required_family="kottke_alloc")
    try_bp(SeamHookBP, "S4_TEST_FMMRET_AFTER", "S4_TEST_FMMRET_AFTER", "id", required_family="fmmret")
    try_bp(SeamHookBP, "S4_TEST_LINEARSOLVE_AFTER", "S4_TEST_LINEARSOLVE_AFTER", "site", required_family="linearsolve")
    try_bp(SeamHookBP, "S4_TEST_LINEARSOLVE_NULLINFO2_AFTER", "S4_TEST_LINEARSOLVE_NULLINFO2_AFTER", "id", required_family="linearsolve_null2")
    try_bp(SeamHookBP, "S4_TEST_ADDFIELD_AFTER", "S4_TEST_ADDFIELD_AFTER", "id", required_family="alloc")


def on_exit(event):
    if hasattr(event, "exit_code"):
        SUMMARY["exit_code"] = event.exit_code
    if hasattr(event, "signal"):
        SUMMARY["signal"] = event.signal
    SUMMARY["status"] = "EXITED"


def save_results():
    if not OUT_DIR:
        return
    os.makedirs(OUT_DIR, exist_ok=True)
    events_path = os.path.join(OUT_DIR, "events.tsv")
    with open(events_path, "w", encoding="utf-8") as fh:
        fh.write("event_idx\tevent_type\tfunc\tcaller\tseq\tsub_seq\tdetails\n")
        for i, ev in enumerate(EVENTS, 1):
            fh.write("%d\t%s\t%s\t%s\t%d\t%d\t%s\n" % (
                i, ev["type"], ev["func"], ev["caller"], ev["seq"], ev["sub_seq"], ev["details"]))

    summary_path = os.path.join(OUT_DIR, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(SUMMARY, fh, indent=2)


def main():
    if not OUT_DIR:
        return
    gdb.events.exited.connect(on_exit)
    try:
        setup_breakpoints()
    except Exception as e:
        SUMMARY["trace_error"] = str(e)
        save_results()
        gdb.execute("quit 2")
        return

    try:
        gdb.execute("run")
    except Exception as e:
        SUMMARY["trace_error"] = "gdb_run_error: %s" % e

    save_results()
    gdb.execute("quit 0")


if __name__ == "__main__":
    main()
