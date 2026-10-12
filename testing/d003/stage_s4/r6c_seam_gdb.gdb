# r6c_seam_gdb.gdb -- P05-S4 R6c-2: measure inj_call of a seam point (new file; read-only).
# Breakpoint at S4_Simulation_GetFieldPlane entry: prints "R6SEAMCALL <n>" for the n-th call of the process
# (n = 1, 2, ...).  The injection HIT line of the driver (stderr, same stream, same order) is placed after the R6SEAMCALL
# line of the call in which it occurs; the judge (run_r6c_seam_gdb.py) takes the last R6SEAMCALL before each HIT line.
# The program is not modified: the breakpoint only reads and counts.
#
#   gdb -batch -x testing/d003/stage_s4/r6c_seam_gdb.gdb --args <driver> pattern both 4 3
set pagination off
set confirm off
set print pretty off
set $r6seam_n = 0
break S4_Simulation_GetFieldPlane
commands
  silent
  set $r6seam_n = $r6seam_n + 1
  printf "R6SEAMCALL %d\n", $r6seam_n
  continue
end
run
quit
