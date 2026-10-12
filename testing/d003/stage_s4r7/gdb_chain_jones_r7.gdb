# gdb_chain_jones_r7.gdb -- P05-S4 R7 M1 section 5 gdb chain (new file).  Read-only: finish prints each return value.
#   env FMM_MODE=jones S4FMM_NG=9 S4FMM_INJECT=rnv1:M gdb -batch -x testing/d003/stage_s4r7/gdb_chain_jones_r7.gdb --args <driver> pattern both 4 3
# Layers read: pattern_generate_flow_field (the PolBasis window's callee), FMMGetEpsilon_PolBasisJones (the layer caller),
# Simulation_ComputeLayerModes.  A layer whose return value does not appear in the log is recorded as "未读到" (not inferred).
# Each 'finish' prints "Value returned is $1 = <n>" for the frame it leaves.
set pagination off
set confirm off
break pattern_generate_flow_field
commands 1
  silent
  printf "R7CHAIN enter pattern_generate_flow_field\n"
  finish
end
break FMMGetEpsilon_PolBasisJones
commands 2
  silent
  printf "R7CHAIN enter FMMGetEpsilon_PolBasisJones\n"
  finish
end
break Simulation_ComputeLayerModes
commands 3
  silent
  printf "R7CHAIN enter Simulation_ComputeLayerModes\n"
  finish
end
run
quit
