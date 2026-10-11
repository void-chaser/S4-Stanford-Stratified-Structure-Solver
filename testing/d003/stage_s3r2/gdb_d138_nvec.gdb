set pagination off
set confirm off
set $sg_k = 0
set $sg_entry_n = 0
break shape_get_normal
commands
silent
set $sg_k = $sg_k + 1
set $sg_entry_n = $rdx
printf "SGN_ENTER k=%d shape_ptr=%p x=%.17g,%.17g\n", $sg_k, $rdi, *(double*)$rsi, *(double*)($rsi+8)
continue
end
break *(shape_get_normal + RET_OFF_1)
commands
silent
printf "SGN_RET nvec=%.17g,%.17g\n", *(double*)$sg_entry_n, *(double*)($sg_entry_n+8)
continue
end
break *(shape_get_normal + RET_OFF_2)
commands
silent
printf "SGN_RET nvec=%.17g,%.17g\n", *(double*)$sg_entry_n, *(double*)($sg_entry_n+8)
continue
end
break *(shape_get_normal + RET_OFF_3)
commands
silent
printf "SGN_RET nvec=%.17g,%.17g\n", *(double*)$sg_entry_n, *(double*)($sg_entry_n+8)
continue
end
break *(shape_get_normal + RET_OFF_4)
commands
silent
printf "SGN_RET nvec=%.17g,%.17g\n", *(double*)$sg_entry_n, *(double*)($sg_entry_n+8)
continue
end
break *(shape_get_normal + RET_OFF_5)
commands
silent
printf "SGN_RET nvec=%.17g,%.17g\n", *(double*)$sg_entry_n, *(double*)($sg_entry_n+8)
continue
end
run
printf "END shape_get_normal_calls=%d\n", $sg_k
quit
