# s3r3_chain_finish.gdb -- P05-S3R3-2 (A2) return values of the chain (new file; separate run from s3r3_chain_gdb.gdb).
# Read-only.  Each 'finish' prints the value returned by that function to the first call that the injection reaches.
#   env S4FMM_INJECT=rnv1:M gdb -batch -x testing/d003/stage_s3r3/s3r3_chain_finish.gdb --args <driver> pattern both 4 3
set pagination off
set confirm off
break pattern_generate_flow_field
commands 1
  silent
  printf "S3R3CHAIN return-point pattern_generate_flow_field\n"
  finish
end
break FMMGetEpsilon_PolBasisNV
commands 2
  silent
  printf "S3R3CHAIN return-point FMMGetEpsilon_PolBasisNV\n"
  finish
end
run
quit
