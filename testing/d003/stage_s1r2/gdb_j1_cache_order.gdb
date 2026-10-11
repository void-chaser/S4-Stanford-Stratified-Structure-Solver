set pagination off
set confirm off
set $cache_calls = 0
set $clm_rets = 0
break Simulation_AddFieldToCache
commands
silent
set $cache_calls = $cache_calls + 1
printf "ORDER ADDCACHE k=%d clm_rets_so_far=%d\n", $cache_calls, $clm_rets
continue
end
break *(Simulation_ComputeLayerModes + 1087)
commands
silent
set $clm_rets = $clm_rets + 1
printf "ORDER CLM_RET k=%d eax=%d\n", $clm_rets, $eax
continue
end
run pattern both 4 3
printf "END addcache=%d clm_rets=%d\n", $cache_calls, $clm_rets
quit
