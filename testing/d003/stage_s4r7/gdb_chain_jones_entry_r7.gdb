# gdb_chain_jones_entry_r7.gdb -- P05-S4 R7 M1 section 5, ENTRY-ONLY variant (new file).  No finish: the run is not stopped,
# so the injection path is reached.  Records which chain functions are entered, in order.  Return values are read in a
# separate run with gdb_chain_jones_finish_r7.gdb (the S3R3 method: finish stops the program at the first return).
#   env FMM_MODE=jones S4FMM_NG=9 S4FMM_INJECT=rnv1:M gdb -batch -x testing/d003/stage_s4r7/gdb_chain_jones_entry_r7.gdb --args <driver> pattern both 4 3
set pagination off
set confirm off
break pattern_generate_flow_field
commands 1
  silent
  printf "R7CHAIN enter pattern_generate_flow_field\n"
  continue
end
break FMMGetEpsilon_PolBasisJones
commands 2
  silent
  printf "R7CHAIN enter FMMGetEpsilon_PolBasisJones\n"
  continue
end
break Simulation_ComputeLayerModes
commands 3
  silent
  printf "R7CHAIN enter Simulation_ComputeLayerModes\n"
  continue
end
run
quit
