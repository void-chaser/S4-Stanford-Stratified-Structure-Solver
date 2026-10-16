# malloc_map_r8m2c.gdb -- P05-S4 R8 M2c GDB mapping script for outside malloc calls in init drivers.
set pagination off
set confirm off

break inject_s3r4_init.cpp:79
commands
silent
printf "MALLOC_MAP_ENTRY k=%ld n=%zu\n", count_outside, n
backtrace 4
continue
end

run pattern both 4 3
quit
