set pagination off
set confirm off
set $solve_calls = 0
set $clm_calls = 0
break *(Simulation_ComputeLayerModes + 1087)
commands
silent
set $clm_calls = $clm_calls + 1
printf "CLM_RET k=%d eax=%d solve_calls_so_far=%d\n", $clm_calls, $eax, $solve_calls
continue
end
break SolveLayerEigensystem
commands
silent
set $solve_calls = $solve_calls + 1
printf "SOLVE_CALL n=%d\n", $solve_calls
continue
end
run pattern both 4 3
printf "END clm_rets=%d solve_calls=%d\n", $clm_calls, $solve_calls
quit
