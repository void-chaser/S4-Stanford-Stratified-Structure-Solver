# r6b_state.gdb -- P05-S4 R6b-1: read-only private-state snapshots at each r6_probe(k) and ComputeLayerModes counts.
# New file.  Used with the R5 debug build (trees/F or trees/B, built with -O0 -g).
# Environment (set by the runner, not here): FMM_MODE, S4FMM_NG, S4FMM_INJECT, S4FMM_NTH, S4FMM_TWICE,
# S4FMM_DUMP_RETRY (optional).  The program is not modified: breakpoints only read memory.
#
#   gdb -batch -x testing/d003/stage_s4/r6b_state.gdb --args <driver> pattern both 4 3
set pagination off
set confirm off
set print pretty off
source testing/d003/stage_s4/r6b_state_gdb.py
run
quit
