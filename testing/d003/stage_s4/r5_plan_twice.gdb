# r5_plan_twice.gdb -- P05-S4 R5-2 gdb batch script, F TREE (1c11905).  Read-only investigation.
# Run on the -O0 -g DEBUG driver built from F ($EV/dbg/drivers/dbg-F/driver-d003).
#
#   gdb -batch -x testing/d003/stage_s4/r5_plan_twice.gdb --args DRIVER [grid args]
#
# Design: "finish" inside a breakpoint "commands" list did not return control in batch mode (R5 probe), so the
# return values are read with gdb.FinishBreakpoint (Python), which stops at the return of each call.
# Source lines are the F-tree lines (the B tree has different lines; see r5_plan_twice_B.gdb):
#   fmm/fmm_FFT.cpp:90   if(NULL == plans[i]){ ret = 1; goto cleanup; }
#   S4.cpp:2413          if(0 != fmm_ret){ ... return 20; }           (Simulation_ComputeLayerModes)
#   S4.cpp:4334          if(NULL == ab){ ...; return 1; }             (S4_Simulation_GetFieldPlane)
set pagination off
set confirm off
python
import gdb

COUNT = {"plan": 0, "nullchk": 0, "exec": 0, "fftE": 0, "kotE": 0, "clm": 0, "gfp": 0, "ab1": 0, "clm_fmmret": 0}


KEEP = []

class RetBP(gdb.FinishBreakpoint):
    """Stops when the frame returns; prints the function's return value."""
    def __init__(self, tag, kind):
        super().__init__(gdb.newest_frame(), internal=True)
        self.tag = tag
        self.kind = kind
        KEEP.append(self)

    def stop(self):
        try:
            v = self.return_value
        except Exception:
            v = None
        if v is None:
            print("%s_RET value=<void-or-unknown>" % self.tag)
        else:
            print("%s_RET value=%s" % (self.tag, str(v)))
        return False  # do not stop the program: keep running after printing


class EntryBP(gdb.Breakpoint):
    """Entry breakpoint: count, print, and arm a FinishBreakpoint for the return value."""
    def __init__(self, spec, key, tag, arm_finish=True):
        super().__init__(spec, internal=False)
        self.key = key
        self.tag = tag
        self.arm_finish = arm_finish
        KEEP.append(self)

    def stop(self):
        COUNT[self.key] += 1
        k = COUNT[self.key]
        print("%s_ENTER k=%d" % (self.tag, k))
        if self.arm_finish:
            RetBP("%s k=%d" % (self.tag, k), self.key)
        return False


class LineBP(gdb.Breakpoint):
    """Line breakpoint: count and print the given expressions, then keep running."""
    def __init__(self, spec, key, tag, exprs):
        super().__init__(spec, internal=False)
        self.key = key
        self.tag = tag
        self.exprs = exprs
        KEEP.append(self)

    def stop(self):
        COUNT[self.key] += 1
        vals = []
        for e in self.exprs:
            try:
                vals.append("%s=%s" % (e, str(gdb.parse_and_eval(e))))
            except Exception as ex:
                vals.append("%s=<err %s>" % (e, ex))
        print("%s k=%d %s" % (self.tag, COUNT[self.key], " ".join(vals)))
        return False


# fft_plan_dft_2d (the R4 injector wrapper): entry, then return value (plan pointer; NULL = failure)
EntryBP("__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i", "plan", "PLAN")
# F fmm_FFT.cpp:90 -- the NULL check after the plan
LineBP("fmm_FFT.cpp:90", "nullchk", "FFT_NULLCHK_L90", ["i", "plans[i]", "ret"])
# fft_plan_exec (the R4 injector wrapper): entry and return value
EntryBP("__wrap__Z13fft_plan_execP12tag_fft_plan", "exec", "EXEC")
# FMMGetEpsilon_FFT / _Kottke: entry and return value
EntryBP("FMMGetEpsilon_FFT", "fftE", "FFT_EPS")
EntryBP("FMMGetEpsilon_Kottke", "kotE", "KOT_EPS")
# Simulation_ComputeLayerModes: entry and return value
EntryBP("Simulation_ComputeLayerModes", "clm", "CLM")
# S4.cpp:2413 -- the fmm_ret check inside ComputeLayerModes (F)
LineBP("S4.cpp:2413", "clm_fmmret", "CLM_FMMRET_L2413", ["fmm_ret"])
# S4_Simulation_GetFieldPlane: entry and return value (one per field call)
EntryBP("S4_Simulation_GetFieldPlane", "gfp", "GFP")
# S4.cpp:4334 -- the GetFieldPlane allocation check (reached only if ab == NULL)
LineBP("S4.cpp:4334", "ab1", "GFP_AB_NULL_L4334", ["ab"])
end

run
python
print("END " + " ".join("%s=%d" % (k, v) for k, v in COUNT.items()))
end
quit
