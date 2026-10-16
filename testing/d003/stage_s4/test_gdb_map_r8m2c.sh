REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# test_gdb_map_r8m2c.sh
set -u
DRV="$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2/build_R3/drivers/init-F3-dbg"
GDB_SCRIPT="$EV/tmp/test.gdb"

cat << 'EOF' > "$GDB_SCRIPT"
set pagination off
set confirm off
break inject_s3r4_init.cpp:79
commands
silent
printf "OUT_MALLOC k=%ld n=%zu\n", count_outside, n
up
info line
down
continue
end
run pattern both 4 3
quit
EOF

FMM_MODE=closed2d S4FMM_NG=1 gdb -batch -x "$GDB_SCRIPT" --args "$DRV" pattern both 4 3 | head -n 30
