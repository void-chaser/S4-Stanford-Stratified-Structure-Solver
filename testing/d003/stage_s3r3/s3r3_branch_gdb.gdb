# s3r3_branch_gdb.gdb -- P05-S3R3 self-check (C) step 1 (new file): which branch runs, and where each window malloc is.
# Read-only: breakpoints print lines; the program is not changed.
#   gdb -batch -x testing/d003/stage_s3r3/s3r3_branch_gdb.gdb --args <driver> pattern both 4 3
# Environment (set by the caller): FMM_MODE, S4FMM_NG, no S4FMM_INJECT (counting only).
# Records: entry of pattern_generate_flow_field_rect / _tri (tri = pattern.c:1643), and the caller of each malloc
# made inside the window (__wrap_malloc, in_window is static, so the breakpoint is set on the wrapped name only).
set pagination off
set confirm off
set print pretty off
break pattern_generate_flow_field_rect
commands 1
  silent
  printf "S3R3BRANCH rect\n"
  continue
end
break pattern_generate_flow_field_tri
commands 2
  silent
  printf "S3R3BRANCH tri\n"
  continue
end
break cg
commands 3
  silent
  printf "S3R3BRANCH cg\n"
  continue
end
run
quit
