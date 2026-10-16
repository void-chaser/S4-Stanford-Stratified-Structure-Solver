# r6c_state_r8m2a3.gdb -- P05-S4 R8 M2a3 state collection gdb script.
# Sources r6c_state_gdb_r8m2a3.py to collect private state at r6_probe(k), CLM, and req.
# Used with -O0 -g debug builds.
set pagination off
set confirm off
set print pretty off
source testing/d003/stage_s4/r6c_state_gdb_r8m2a3.py
run
bt 24
quit
