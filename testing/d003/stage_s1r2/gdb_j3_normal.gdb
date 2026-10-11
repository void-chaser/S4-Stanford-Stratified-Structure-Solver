set pagination off
set confirm off
set $sg_k = 0
break shape_get_normal
commands
silent
set $sg_k = $sg_k + 1
printf "SGN k=%d shape_ptr=%p\n", $sg_k, $rdi
continue
end
run
printf "END shape_get_normal_calls=%d\n", $sg_k
quit
