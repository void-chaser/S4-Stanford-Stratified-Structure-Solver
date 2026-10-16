# win64_diag_r8m2b.gdb -- GDB script for win:64 diagnosis (Section 5 S-F).
set pagination off
set confirm off

break r6_probe
commands
  silent
  printf "WIN64_DIAG_PROBE: k=%d\n", $rdi
  continue
end

break S4/S4.cpp:1894
commands
  silent
  printf "WIN64_DIAG_CLM_RET: line 1894 rc=%d\n", $rax
  continue
end

run
quit
