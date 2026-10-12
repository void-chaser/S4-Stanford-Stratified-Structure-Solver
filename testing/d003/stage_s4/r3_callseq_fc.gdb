# r3_callseq_fc.gdb -- P05-S4 R3-1 discovery, with field-call boundaries (new file, R3).  NO injection.
# Same counters and output as r3_callseq.gdb, plus one line per entry of S4_Simulation_GetFieldPlane:
#   R3FC k=<field call index>
# so that every R3EV line can be assigned to the first or the second field call of the driver.
# The breakpoints are read-only: no return value is changed and no request is set.
#
# Usage: sh testing/d003/stage_s4/run_r3_discovery_fc.sh   (the wrapper runs this script for B and F)
set pagination off
set confirm off
set print demangle on
set print asm-demangle on
set $n_malloc = 0
set $n_plan = 0
set $n_exec = 0
set $n_fc = 0

break S4_Simulation_GetFieldPlane
commands
silent
set $n_fc = $n_fc + 1
printf "R3FC k=%d\n", $n_fc
continue
end

break *__wrap__Z9S4_mallocm
commands
silent
set $n_malloc = $n_malloc + 1
set $ra = *(unsigned long *)$rsp
printf "R3EV cat=malloc nth=%d size=%lu grid=- ra=0x%lx\n", $n_malloc, (unsigned long)$rdi, $ra
info symbol $ra
continue
end

break *__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i
commands
silent
set $n_plan = $n_plan + 1
set $ra = *(unsigned long *)$rsp
printf "R3EV cat=plan nth=%d size=- grid=%dx%d ra=0x%lx\n", $n_plan, *(int *)$rdi, *(int *)((char *)$rdi + 4), $ra
info symbol $ra
continue
end

break *__wrap__Z13fft_plan_execP12tag_fft_plan
commands
silent
set $n_exec = $n_exec + 1
set $ra = *(unsigned long *)$rsp
printf "R3EV cat=exec nth=%d size=- grid=- ra=0x%lx\n", $n_exec, $ra
info symbol $ra
continue
end

run
printf "R3END malloc=%d plan=%d exec=%d fc=%d\n", $n_malloc, $n_plan, $n_exec, $n_fc
quit
