# m210_b_r8m2a2.gdb -- P05-S4 R8 M2a2 section 4.3 (M2-10).
# Breakpoint at tree_B/S4/S4.cpp:2432 (where Simulation_ComputeLayerModes returns 20 on eigen_info != 0).
# Usage: gdb -batch -x testing/d003/stage_s4/m210_b_r8m2a2.gdb --args <driver> pattern both 4 3
set pagination off
set confirm off
break S4/S4.cpp:2432
commands
  printf "M210_HIT: Simulation_ComputeLayerModes line 2432 eigen_info=%d returning 20\n", eigen_info
  continue
end
run
quit
