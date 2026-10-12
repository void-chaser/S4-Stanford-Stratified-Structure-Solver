# r5_plan_mcount.gdb -- P05-S4 R5-3 step 1 (DISCOVERY, no injection): m(K) = number of __wrap_malloc calls made
# INSIDE the K-th fft_plan_dft_2d call of the process.  Read-only (gdb counts; the driver is not modified).
# Driver: a PLAIN driver with the R4 injector (inject_r4_plan.cpp, so __wrap__Z15fft_plan_dft_2d is present).
#   gdb -batch -x testing/d003/stage_s4/r5_plan_mcount.gdb --args DRIVER pattern both 4 3
#   env: FMM_MODE, S4FMM_NG=9, S4FMM_TWICE (slab or unset), NO S4FMM_INJECT.
# Output lines:  MCOUNT k=<K> m=<malloc count inside plan K>   and   END plan_calls=<n>
set pagination off
set confirm off
python
import gdb

ST = {"k": 0, "in_plan": False, "m": 0, "plan_calls": 0}
KEEP = []


class PlanRet(gdb.FinishBreakpoint):
    def __init__(self):
        super().__init__(gdb.newest_frame(), internal=True)
        KEEP.append(self)

    def stop(self):
        print("MCOUNT k=%d m=%d" % (ST["k"], ST["m"]))
        ST["in_plan"] = False
        return False


class PlanEnter(gdb.Breakpoint):
    def __init__(self):
        super().__init__("__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i", internal=False)
        KEEP.append(self)

    def stop(self):
        ST["plan_calls"] += 1
        ST["k"] = ST["plan_calls"]
        ST["m"] = 0
        ST["in_plan"] = True
        PlanRet()
        return False


class MallocHit(gdb.Breakpoint):
    def __init__(self):
        super().__init__("__wrap_malloc", internal=False)
        KEEP.append(self)

    def stop(self):
        if ST["in_plan"]:
            ST["m"] += 1
        return False


PlanEnter()
MallocHit()
end

run
python
print("END plan_calls=%d" % ST["plan_calls"])
end
quit
