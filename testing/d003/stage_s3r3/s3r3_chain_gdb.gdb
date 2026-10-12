# s3r3_chain_gdb.gdb -- P05-S3R3-2 (A2) return-code chain check (new file, revised: no finish, so the run is not stopped).
# Read-only.  Breakpoints print the entry of each function; the run continues to the driver's end.
#   env S4FMM_INJECT=rnv1:M gdb -batch -x testing/d003/stage_s3r3/s3r3_chain_gdb.gdb --args <driver> pattern both 4 3
# Expected chain (injected point): pattern_generate_flow_field returns -11 -> FMMGetEpsilon_PolBasisNV returns -11 ->
# Simulation_ComputeLayerModes returns 20.  The return values are read from the driver's "RC first" line (rc1 = 20) and
# from gdb "finish" in a separate run (s3r3_chain_finish.gdb), so that the judged run is not stopped here.
set pagination off
set confirm off
break pattern_generate_flow_field
commands 1
  silent
  printf "S3R3CHAIN enter pattern_generate_flow_field\n"
  continue
end
break FMMGetEpsilon_PolBasisNV
commands 2
  silent
  printf "S3R3CHAIN enter FMMGetEpsilon_PolBasisNV\n"
  continue
end
break Simulation_ComputeLayerModes
commands 3
  silent
  printf "S3R3CHAIN enter Simulation_ComputeLayerModes\n"
  continue
end
run
quit
