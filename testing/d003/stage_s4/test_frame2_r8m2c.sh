REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
set -u
DRV="$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2/build_R3/drivers/init-F3-dbg"
GDB_SCRIPT="$REPO/testing/d003/stage_s4/malloc_map_r8m2c.gdb"

FMM_MODE=closed2d S4FMM_NG=1 gdb -batch -x "$GDB_SCRIPT" --args "$DRV" pattern both 4 3 | grep -E "(MALLOC_MAP_ENTRY|#[1-3] .* at )" | head -n 45
