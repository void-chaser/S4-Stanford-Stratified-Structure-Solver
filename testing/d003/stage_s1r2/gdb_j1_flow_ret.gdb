set pagination off
set confirm off
set $flow_calls = 0
break *(pattern_generate_flow_field + OFFSET_RET)
commands
silent
set $flow_calls = $flow_calls + 1
printf "FLOW_RET k=%d eax=%d\n", $flow_calls, $eax
continue
end
run pattern both 4 3
printf "END flow_rets=%d\n", $flow_calls
quit
