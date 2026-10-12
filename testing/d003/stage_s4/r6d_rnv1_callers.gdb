# r6d_rnv1_callers.gdb -- P05-S4 R6d-2 step 3 (new file): record the caller of each malloc made inside the RNV1 window.
# Read-only: breakpoints print a backtrace; nothing is changed in the program.
#   gdb -batch -x testing/d003/stage_s4/r6d_rnv1_callers.gdb --args <driver-r6d-rnv1> pattern both 4 3
# Environment (set by the caller): FMM_MODE=nv, S4FMM_NG=9 (or 1), no S4FMM_INJECT.
set pagination off
set confirm off
set print pretty off
break __wrap_malloc if in_window == 1
commands 1
  silent
  printf "R6DCALLER n=%lu\n", n
  bt 3
  continue
end
run
quit
