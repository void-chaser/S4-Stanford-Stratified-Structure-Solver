# r6_plan14_caller.gdb -- P05-S4 R6-1 sample (new file).  Read-only.  For ONE K != 12 point (K = 14) on tree F, under
# S4FMM_TWICE=slab with S4FMM_INJECT=plancall:14:1 (inj_call 2), confirm:
#   (a) the caller of the 14th fft_plan_dft_2d is FMMGetEpsilon_* (backtrace), and
#   (b) the NULL check of the plan (fmm_FFT.cpp:90 for fft, fmm_kottke.cpp:94 for kottke) is EXECUTED after the 14th plan call.
# The mode is selected by the environment (FMM_MODE=fft or kottke), not by this script.
#
#   gdb -batch -x testing/d003/stage_s4/r6_plan14_caller.gdb --args DRIVER pattern both 4 3
#
# Build: the R5 debug build of tree F (-O0 -g), checkpoints/p05/evidence/p05-s4r5/dbg/drivers/dbg-F/driver-d003
# (sha256 349795624a56ddc15de1ae9f7ead73bad868ab148f1c6a8b89f93f92105fdcb0, recorded in DRIVERS_DBG.tsv).
# Output: stdout of gdb (the caller redirects it through safe_run into the R6 evidence directory).
set pagination off
set confirm off
set $n_plan = 0
set $target_k = 14
break __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i
commands
  silent
  set $n_plan = $n_plan + 1
  if $n_plan == $target_k
    printf "R6CALLER plan_call=%d (target)\n", $n_plan
    bt 12
  end
  continue
end
break fmm_FFT.cpp:90
commands
  silent
  printf "R6NULLCHK site=fmm_FFT.cpp:90 plan_call=%d plans_i_is_null=%d\n", $n_plan, (int)(plans[i] == 0)
  continue
end
break fmm_kottke.cpp:94
commands
  silent
  printf "R6NULLCHK site=fmm_kottke.cpp:94 plan_call=%d plans_i_is_null=%d\n", $n_plan, (int)(plans[i] == 0)
  continue
end
run
printf "R6CALLER summary total_plan_calls=%d\n", $n_plan
quit
