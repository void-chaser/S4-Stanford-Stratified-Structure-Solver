# gdb_chain_jones_line_r7.gdb -- P05-S4 R7 M1a (U45): read the PolBasisJones return value and the S4.cpp fmm_ret, by LINE
# breakpoints, WITHOUT finish (new file).  Continue-only: the run is not stopped, so the injection path is reached.
#   env FMM_MODE=jones S4FMM_NG=9 S4FMM_INJECT=rnv1:M gdb -batch -x testing/d003/stage_s4r7/gdb_chain_jones_line_r7.gdb --args <driver> pattern both 4 3
# Lines (F2 = a07b5ac; see checkpoints/p05/evidence/p05-s4r7/LINEMAP_A1_R7.tsv):
#   fmm_PolBasisJones.cpp:192  "return error;" (failure branch after Pattern_GenerateFlowField; error holds its return value)
#   S4.cpp:2413                "if(0 != fmm_ret){" (fmm_ret holds the value from the epsilon routine)
# At each hit the value is printed.  A line that is never hit is recorded as "未读到" by the caller of this script.
set pagination off
set confirm off
break fmm_PolBasisJones.cpp:192
commands 1
  silent
  printf "R7LINE fmm_PolBasisJones.cpp:192 error=%d\n", error
  continue
end
break S4.cpp:2413
commands 2
  silent
  printf "R7LINE S4.cpp:2413 fmm_ret=%d\n", fmm_ret
  continue
end
run
quit
