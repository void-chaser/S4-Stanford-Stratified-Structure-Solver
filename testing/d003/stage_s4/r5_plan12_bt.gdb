# r5_plan12_bt.gdb -- P05-S4 R5-2: backtrace of plan call 12 (the injected one, twice NTH 12) and of the
# plan calls around it, on the -O0 -g DEBUG driver built from F.  Read-only.  Companion of r5_plan_twice.gdb.
#   gdb -batch -x testing/d003/stage_s4/r5_plan12_bt.gdb --args DRIVER [grid args]
set pagination off
set confirm off
python
import gdb

N = {"plan": 0}
KEEP = []


class PlanBT(gdb.Breakpoint):
    def __init__(self):
        super().__init__("__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i", internal=False)
        KEEP.append(self)

    def stop(self):
        N["plan"] += 1
        if N["plan"] in (5, 6, 11, 12):
            print("=== PLAN CALL %d: backtrace ===" % N["plan"])
            gdb.execute("bt 8", to_string=False)
        return False


PlanBT()
end

run
quit
