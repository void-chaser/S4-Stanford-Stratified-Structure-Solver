# a1map_c2.gdb -- P05-S3R4 CONT2 A1 map (revised): the counting run and the base address are taken in ONE gdb session
# (ASLR off), so that the caller addresses printed by the injector and the load base share one address space.
# Break at exit, print the mappings (base = the segment with file offset 0x0), then quit.
# Used by a1map_c2.sh:  gdb -batch -x a1map_c2.gdb --args <driver> pattern both 4 3
set pagination off
set disable-randomization on
break exit
run
info proc mappings
quit
