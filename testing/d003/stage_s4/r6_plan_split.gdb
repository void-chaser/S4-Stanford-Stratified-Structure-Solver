# r6_plan_split.gdb -- P05-S4 R6-1 (new file).  Read-only count: how many fft_plan_dft_2d calls happen BEFORE the
# TWICE=slab destroy (the first GetFieldPlane call) and how many AFTER it (the second call).  No injection is requested.
# Used to fix inj_call for the K=3 control (first call) and the K=12..16 rows (second call) before the R6-1 pre-registration.
#
#   gdb -batch -x testing/d003/stage_s4/r6_plan_split.gdb --args DRIVER [grid args]
#
# Run on the -O0 -g DEBUG driver built from tree F (R5 dbg build).  Output is written to stdout by gdb; the caller
# redirects it through testing/d003/safe_run.sh into the R6 evidence directory.
set pagination off
set confirm off
set $plan_before_destroy = -1
set $plan_total = 0
break __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i
commands
  silent
  set $plan_total = $plan_total + 1
  printf "PLANSPLIT plan_call=%d\n", $plan_total
  continue
end
break S4_Simulation_DestroyLayerModes
commands
  silent
  set $plan_before_destroy = $plan_total
  printf "PLANSPLIT destroy_layer_modes_entered plan_calls_before=%d\n", $plan_total
  continue
end
run
printf "PLANSPLIT total_plan_calls=%d plan_calls_before_destroy=%d\n", $plan_total, $plan_before_destroy
quit
