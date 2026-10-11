# P05-S1R Q2 read-only layer probe (gdb).  Debug build from git archive (never S4/).  Breakpoints only.
# Usage: env FMM_MODE=vl S4FMM_NG=<n> gdb -q -batch -x layer_probe.gdb --args DRIVER pattern both 4 3
# Records, in order: which layer enters Simulation_ComputeLayerModes (name, pattern shape count),
# the first eigensystem inputs at each SolveLayerEigensystem entry, and each hit of the complex-branch
# error print (rcwa.cpp:883; 'info' is not in scope at every location, so only the fact is printed).

set pagination off
set confirm off

break S4.cpp:2274
commands
  silent
  printf "LAYER name=%s nshapes=%d\n", L->name, L->pattern.nshapes
  continue
end

break SolveLayerEigensystem
commands
  silent
  printf "EIG n=%lu inv0=(%g,%g) inv1=(%g,%g) eps2_0=(%g,%g) eps2_1=(%g,%g)\n", n, Epsilon_inv[0].real(), Epsilon_inv[0].imag(), Epsilon_inv[1].real(), Epsilon_inv[1].imag(), Epsilon2[0].real(), Epsilon2[0].imag(), Epsilon2[1].real(), Epsilon2[1].imag()
  continue
end

break rcwa.cpp:883
commands
  silent
  printf "FAILSITE rcwa.cpp:883 error print reached\n"
  continue
end

run
quit
