set pagination off
set confirm off
set $pgff_k = 0
set $solve_k = 0
break *(pattern_generate_flow_field + RET_OFF)
commands
silent
set $pgff_k = $pgff_k + 1
printf "PGFF_RET k=%d eax=%d\n", $pgff_k, $eax
continue
end
break SolveLayerEigensystem
commands
silent
set $solve_k = $solve_k + 1
printf "SOLVE_CALL n=%d\n", $solve_k
continue
end
run
printf "END pgff_rets=%d solve_calls=%d\n", $pgff_k, $solve_k
quit
