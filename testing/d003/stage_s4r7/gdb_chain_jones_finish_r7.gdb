# gdb_chain_jones_finish_r7.gdb -- P05-S4 R7 M1 section 5, RETURN-VALUE variant (new file; separate run).
# 'finish' stops the program at the first return of each breakpoint.  That is why this variant is NOT the judged run:
# it is used only to read the return values of the first call of the chain.  Layers whose value does not appear are
# recorded as "未读到" by the caller of this script.
#   env FMM_MODE=jones S4FMM_NG=9 S4FMM_INJECT=rnv1:M gdb -batch -x testing/d003/stage_s4r7/gdb_chain_jones_finish_r7.gdb --args <driver> pattern both 4 3
set pagination off
set confirm off
break pattern_generate_flow_field
commands 1
  silent
  printf "R7RET enter pattern_generate_flow_field\n"
  finish
end
break FMMGetEpsilon_PolBasisJones
commands 2
  silent
  printf "R7RET enter FMMGetEpsilon_PolBasisJones\n"
  finish
end
run
quit
