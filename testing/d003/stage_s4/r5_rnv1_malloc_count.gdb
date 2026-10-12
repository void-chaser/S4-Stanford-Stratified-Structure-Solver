# r5_rnv1_malloc_count.gdb -- P05-S4 R5-4 RNV1 step 1: count, read-only, the malloc calls made INSIDE
# pattern_generate_flow_field during the NV control run (no injection).  Driver: $EV/d016/driver-B or driver-F.
#   gdb -batch -x testing/d003/stage_s4/r5_rnv1_malloc_count.gdb --args DRIVER pattern both 4 3   (env FMM_MODE=nv S4FMM_NG=5)
# Counts: entries of pattern_generate_flow_field, and calls of the (wrapped) malloc issued while inside it.
# The malloc wrapper is __wrap_malloc (testing/d003/stage_s4/inject_r4_plan.cpp, linked with --wrap=malloc); pattern.c
# calls malloc directly (lines 1477, 1481, 1656, 1660 of F pattern.c).
set pagination off
set confirm off
python
import gdb

N = {"pgff_enter": 0, "pgff_ret": 0, "malloc_in_pgff": 0, "malloc_total": 0}
KEEP = []


class Enter(gdb.Breakpoint):
    def __init__(self):
        super().__init__("pattern_generate_flow_field", internal=False)
        KEEP.append(self)

    def stop(self):
        N["pgff_enter"] += 1
        return False


class Malloc(gdb.Breakpoint):
    def __init__(self):
        super().__init__("__wrap_malloc", internal=False)
        KEEP.append(self)

    def stop(self):
        N["malloc_total"] += 1
        # the caller chain (up to 6 frames) decides; no "armed" flag (a flag would count malloc calls after the return)
        try:
            f = gdb.newest_frame()
            names = []
            while f is not None and len(names) < 6:
                names.append(str(f.name()))
                f = f.older()
            if any("pattern_generate_flow_field" in str(n) for n in names):
                N["malloc_in_pgff"] += 1
        except Exception:
            pass
        return False


Enter()
Malloc()
end

run
python
print("END " + " ".join("%s=%s" % (k, v) for k, v in N.items()))
end
quit
