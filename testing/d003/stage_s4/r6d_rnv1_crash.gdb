# r6d_rnv1_crash.gdb -- P05-S4 R6d-2 (new file): backtrace at a fatal signal of an injected RNV1 run.
# Read-only: the program is not changed.  The run continues to the signal; gdb prints the backtrace there.
#   gdb -batch -x testing/d003/stage_s4/r6d_rnv1_crash.gdb --args <driver-r6d-rnv1> pattern both 4 3
# Environment (set by the caller): FMM_MODE, S4FMM_NG, S4FMM_INJECT=rnv1:M.
set pagination off
set confirm off
set print pretty off
handle SIGSEGV stop print
handle SIGBUS stop print
handle SIGABRT stop print
run
bt 12
info registers rip
quit
