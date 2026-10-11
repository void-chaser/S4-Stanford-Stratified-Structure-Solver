set pagination off
set confirm off
set $solve_k = 0
break SolveLayerEigensystem
commands
silent
set $solve_k = $solve_k + 1
printf "SOLVE_ENTER k=%d\n", $solve_k
bt 4
continue
end
run
printf "END solve_entries=%d\n", $solve_k
bt 8
quit
