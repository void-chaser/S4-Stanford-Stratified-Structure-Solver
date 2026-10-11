set pagination off
set confirm off
set $solve_k = 0
break SolveLayerEigensystem
commands
silent
set $solve_k = $solve_k + 1
printf "SOLVE_ENTER k=%d rdi_n=%lu rcx_Einv=%p r8_E2=%p r9_epstype=%d\n", $solve_k, $rdi, $rcx, $r8, $r9d
printf "SOLVE_ENTER Einv_first4\n"
x/8gf $rcx
printf "SOLVE_ENTER E2_first4\n"
x/8gf $r8
continue
end
run
printf "END solve_entries=%d\n", $solve_k
quit
