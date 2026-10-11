# P05-S1R Q2 read-only probe (gdb).  Runs on a DEBUG build made by git archive (never S4/).
# Usage (run from an evidence directory; the driver writes its own outputs there):
#   env FMM_MODE=vl S4FMM_NG=<n> gdb -q -batch -x nb_probe.gdb --args DRIVER pattern both 4 3
# No S4FMM_INJECT is set (control run).  Breakpoints only: nothing is modified.
#
# Probe points (verified to resolve in the debug build, S4/S4.cpp and S4/rcwa.cpp):
#   A  S4.cpp:2274   entry of Simulation_ComputeLayerModes.  Reads S->n_G (a struct field; the local 'n' is
#                    <optimized out> on the H debug build, verified).  S->n_G is the eigensystem size.
#   B  rcwa.cpp:883  the fprintf of "Layer eigensystem returned info" (the complex branch).  Its address
#                    is multi-location and 'info' is not in scope at every location, so only the fact that the
#                    site is reached is printed here.  The value of info is recorded from the driver's own stderr.
#   C  SolveLayerEigensystem entry: prints n (the eigensystem size).  omega is not printed: 'omega.real()' is
#                    not an lvalue at -O1 (verified), so it was removed rather than left to fail.
#
# Note: rcwa.cpp:666 (real branch) is NOT in the default library (HAVE_LAPACK undefined), so it is not probed.

set pagination off
set confirm off

break S4.cpp:2274
commands
  silent
  printf "PROBE A ComputeLayerModes n_G=%d\n", S->n_G
  continue
end

break SolveLayerEigensystem
commands
  silent
  printf "PROBE C SolveLayerEigensystem entry n=%lu\n", n
  continue
end

break rcwa.cpp:883
commands
  silent
  printf "PROBE B fprintf-site rcwa.cpp:883 reached\n"
  continue
end

run
quit
