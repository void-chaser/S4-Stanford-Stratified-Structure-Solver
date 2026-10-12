# r3_callseq.gdb -- P05-S4 R3-1 discovery script (new file, R3).  Records the call sequence of
# S4_malloc, fft_plan_dft_2d and fft_plan_exec in one driver run.  NO injection is requested
# (S4FMM_INJECT must be unset).  Read-only with respect to the program: no return value is changed.
#
# Method.  The driver is linked with --wrap for these three symbols (build_tree_r2.sh LIBFLAGS).  A
# breakpoint at the entry of each __wrap_ function sees every call that reaches the wrapper, in order.
# The counters below equal the counters of inject_d003.cpp (n_s4malloc, n_plan_calls, n_exec_calls) for the
# same run, so the NTH printed here is the NTH that S4FMM_NTH selects.
# The binary is not stripped but carries no debug information (no .debug_* sections), so the caller is
# identified by the symbol that contains the return address (function name and offset), never by line.
#
# Output lines (parsed by r3_callseq_parse.py):
#   R3EV cat=<malloc|plan|exec> nth=<k> size=<bytes or -> grid=<n0x n1 or -> ra=<hex return address>
#   <the next line is the output of "info symbol" for the return address: the caller>
#   R3END malloc=<n> plan=<n> exec=<n>
#
# Usage (see run_r3_discovery.sh):
#   env -i PATH=... LANG=C LC_ALL=C FMM_MODE=<mode> S4FMM_NG=9 [S4FMM_TWICE=slab] \
#       gdb -batch -nx -x testing/d003/stage_s4/r3_callseq.gdb --args <driver> pattern both 4 3
set pagination off
set confirm off
set print demangle on
set print asm-demangle on
set $n_malloc = 0
set $n_plan = 0
set $n_exec = 0

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
printf "R3END malloc=%d plan=%d exec=%d\n", $n_malloc, $n_plan, $n_exec
quit
