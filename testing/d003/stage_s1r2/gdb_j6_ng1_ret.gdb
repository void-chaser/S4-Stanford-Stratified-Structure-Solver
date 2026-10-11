set pagination off
set confirm off
set $flow_k = 0
break *(pattern_generate_flow_field + 422)
commands
silent
set $flow_k = $flow_k + 1
printf "NG1_FLOW_RET k=%d eax=%d\n", $flow_k, $eax
continue
end
run pattern both 4 3
printf "END flow_rets=%d\n", $flow_k
quit
