# r5_plan_twice_B.gdb -- P05-S4 R5-2 gdb batch script, B TREE (37a82e8).  Read-only investigation, TWICE=slab.
# NO-TWICE companion (R4 actual condition).  S4FMM_TWICE is UNSET.  Run on the -O0 -g DEBUG driver built from B.
#   gdb -batch -x testing/d003/stage_s4/r5_plan_twice_B_notwice.gdb --args DRIVER [grid args]  (env: FMM_MODE=fft
#       S4FMM_NG=9 S4FMM_INJECT=plancall:12:1; S4FMM_TWICE unset)
# B-tree lines: fmm/fmm_FFT.cpp:85 plans[i] = fft_plan_dft_2d(...)  (NO NULL check after it)
#               fmm/fmm_FFT.cpp:183 fft_plan_exec(plans[4]) (return ignored); :212 fft_plan_exec(plans[w]) (ignored)
# The return values are read with gdb.FinishBreakpoint (see r5_plan_twice.gdb for why "finish" in commands is not used).
set pagination off
set confirm off
python
import gdb

COUNT = {"plan": 0, "exec": 0, "fftE": 0, "clm": 0, "gfp": 0, "gofg": 0}
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
    def __init__(self, spec, key, tag, arg_exprs=()):
        super().__init__(spec, internal=False)
        self.key = key
        self.tag = tag
        self.arg_exprs = arg_exprs
        KEEP.append(self)

    def stop(self):
        COUNT[self.key] += 1
        args = []
        for e in self.arg_exprs:
            try:
                args.append("%s=%s" % (e, str(gdb.parse_and_eval(e))))
            except Exception as ex:
                args.append("%s=<err %s>" % (e, ex))
        print("%s_ENTER k=%d %s" % (self.tag, COUNT[self.key], " ".join(args)))
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


EntryBP("__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i", "plan", "PLAN")
EntryBP("__wrap__Z13fft_plan_execP12tag_fft_plan", "exec", "EXEC", ("$rdi",))
EntryBP("FMMGetEpsilon_FFT", "fftE", "FFT_EPS")
EntryBP("Simulation_ComputeLayerModes", "clm", "CLM")
# B has NO fmm_ret check in ComputeLayerModes (the FMMGetEpsilon return is discarded, S4.cpp:2368-2374 in B),
# so there is no 2413 breakpoint for B.
EntryBP("S4_Simulation_GetFieldPlane", "gfp", "GFP")
EntryBP("GetFieldOnGrid", "gofg", "GOFG")
end

run
python
print("END " + " ".join("%s=%d" % (k, v) for k, v in COUNT.items()))
end
quit
