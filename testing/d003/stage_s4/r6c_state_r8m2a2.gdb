# r6c_state.gdb -- P05-S4 R6c-1: the R6b state script with one addition (R6CREQ at Simulation_GetLayerSolution entry, U14).
# Copy of r6b_state.gdb (R6b, unchanged); sources r6c_state_gdb_r8m2a2.py (copy of r6b_state_gdb.py + R6CReqTrace).
# Used with the R5 debug build (trees/F, -O0 -g).  Environment (set by the runner): FMM_MODE, S4FMM_NG, S4FMM_INJECT,
# S4FMM_NTH, S4FMM_TWICE, S4FMM_DUMP_DIR.  The program is not modified: breakpoints only read memory.
#
#   gdb -batch -x testing/d003/stage_s4/r6c_state.gdb --args <driver> pattern both 4 3
set pagination off
set confirm off
set print pretty off
source testing/d003/stage_s4/r6c_state_gdb_r8m2a2.py
run
quit
