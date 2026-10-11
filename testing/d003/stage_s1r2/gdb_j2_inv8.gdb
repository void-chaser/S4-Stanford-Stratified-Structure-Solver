set pagination off
set confirm off
set $solve_k = 0
break SolveLayerEigensystem
commands
silent
set $solve_k = $solve_k + 1
printf "SOLVE_ENTER k=%d rdi_n=%lu\n", $solve_k, $rdi
printf "SOLVE_ENTER Einv_first8\n"
x/16gf $rcx
printf "SOLVE_ENTER E2_first8\n"
x/16gf $r8
continue
end
run
printf "END solve_entries=%d\n", $solve_k
quit
