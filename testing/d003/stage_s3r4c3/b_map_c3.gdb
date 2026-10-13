set pagination off
set confirm off
set disable-randomization on
break S4_Simulation_GetFieldPlane
run
finish
print (long)s4fmm_poly_window_count()
delete
break exit
continue
print (long)s4fmm_poly_window_count()
print (long)s4fmm_inject_hits()
continue
