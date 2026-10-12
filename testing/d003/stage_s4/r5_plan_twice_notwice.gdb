# r5_plan_twice_notwice.gdb -- P05-S4 R5-2 gdb batch script for the R4 ACTUAL twice condition (S4FMM_TWICE UNSET),
# F tree (1c11905), -O0 -g DEBUG driver ($EV/dbg/drivers/dbg-F/driver-d003).  Read-only.
# Companion of r5_plan_twice.gdb (which uses S4FMM_TWICE=slab).
#
#   gdb -batch -x testing/d003/stage_s4/r5_plan_twice_notwice.gdb --args DRIVER [grid args]   (env: FMM_MODE=fft
#       S4FMM_NG=9 S4FMM_INJECT=plancall:12:1, S4FMM_TWICE UNSET)
# Without S4FMM_TWICE, plan call 12 is made by GetFieldOnGrid (rcwa.cpp:2209), not by FMMGetEpsilon_FFT.
#   rcwa.cpp:2209  plan[i] = fft_plan_dft_2d(inxy_rev, from[i], to[i], 1);
#   rcwa.cpp:2211  if(NULL == plan[i]){ ret = 1; goto cleanup; }   (the NULL check of the GetFieldOnGrid plan)
set pagination off
set confirm off
python
import gdb

COUNT = {"plan": 0, "rcwa_null": 0, "gofg": 0, "gfp": 0, "fftE": 0, "clm": 0, "ab1": 0, "clm_fmmret": 0}
KEEP = []


class RetBP(gdb.FinishBreakpoint):
    def __init__(self, tag):
        super().__init__(gdb.newest_frame(), internal=True)
        self.tag = tag
        KEEP.append(self)

    def stop(self):
        try:
            v = self.return_value
        except Exception:
            v = None
        print("%s_RET value=%s" % (self.tag, "<unknown>" if v is None else str(v)))
        return False


class EntryBP(gdb.Breakpoint):
    def __init__(self, spec, key, tag):
        super().__init__(spec, internal=False)
        self.key = key
        self.tag = tag
        KEEP.append(self)

    def stop(self):
        COUNT[self.key] += 1
        print("%s_ENTER k=%d" % (self.tag, COUNT[self.key]))
        RetBP("%s k=%d" % (self.tag, COUNT[self.key]))
        return False


class LineBP(gdb.Breakpoint):
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


# the injected plan (any caller) -- entry and return value
EntryBP("__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i", "plan", "PLAN")
# GetFieldOnGrid plan line (rcwa.cpp:2209): print the NULL-ness of plan[i] right after the call
# the cleanup label (rcwa.cpp:2265) is reached by goto from every error path, including the plan NULL check (2211);
# the line 2211 breakpoint is NOT used for the result because gdb maps it imprecisely at -O0 (it read garbage in run 1)
# address breakpoint at the cleanup label: GetFieldOnGrid + 3730 (rcwa.cpp:2265; the only exit of GetFieldOnGrid).
# A line breakpoint fired only once at -O0 (run 2), so an offset from the function symbol is used instead.
class AddrBP(gdb.Breakpoint):
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
AddrBP("*(_Z14GetFieldOnGridmPiPKdS1_St7complexIdEPKS3_S5_S5_S5_iS5_PKmS1_PS3_S8_+3730)", "rcwa_null", "RCWA_CLEANUP_L2265", ["ret"])
# GetFieldOnGrid: entry and return value
EntryBP("GetFieldOnGrid", "gofg", "GOFG")
# S4_Simulation_GetFieldPlane: entry and return value
EntryBP("S4_Simulation_GetFieldPlane", "gfp", "GFP")
# FMMGetEpsilon_FFT and ComputeLayerModes (to confirm that no FMM failure happens in the second call)
EntryBP("FMMGetEpsilon_FFT", "fftE", "FFT_EPS")
EntryBP("Simulation_ComputeLayerModes", "clm", "CLM")
# S4.cpp:2413 fmm_ret check (F)
LineBP("S4.cpp:2413", "clm_fmmret", "CLM_FMMRET_L2413", ["fmm_ret"])
# S4.cpp:4334 GetFieldPlane ab allocation check
LineBP("S4.cpp:4334", "ab1", "GFP_AB_NULL_L4334", ["ab"])
end

run
python
print("END " + " ".join("%s=%d" % (k, v) for k, v in COUNT.items()))
end
quit
