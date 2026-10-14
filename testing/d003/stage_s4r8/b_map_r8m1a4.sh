#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# b_map_r8m1a4.sh -- P05-S4 R8 M1a CONT3a section 7 B map recheck on F3.  New file.
# Runs polyinj-F3 driver with no injection under gdb -batch -nx.  6 combos: {fft, kottke} x NG {1, 5, 9}.
# Usage (through safe_run):
#   sh testing/d003/stage_s4r8/b_map_r8m1a4.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "b_map_r8m1a4: first arg must be p05-s4r8" >&2; exit 2; }

DRV="$EV/drivers_r8m1/polyinj-F3/driver"
EXPECT_DRV_SHA="419cfb727932cc8d9417fd3a873c578f2f1f597f57e501041d9dd3b221ad30a9"
test -f "$DRV" || { echo "b_map_r8m1a4: driver missing: $DRV" >&2; exit 2; }
ACTUAL_SHA=$(sha256sum "$DRV" | cut -d' ' -f1)
[ "$ACTUAL_SHA" = "$EXPECT_DRV_SHA" ] || { echo "b_map_r8m1a4: driver sha mismatch" >&2; exit 2; }

GDBSCRIPT="$REPO/testing/d003/stage_s4r8/b_map_r8m1a4.gdb"
test -f "$GDBSCRIPT" || { echo "b_map_r8m1a4: gdb script missing: $GDBSCRIPT" >&2; exit 2; }

OUT_BASE="$EV/additions_r8m1a4"
mkdir -p "$OUT_BASE" || exit 2

for M in fft kottke; do
    for NG in 1 5 9; do
        D="$OUT_BASE/b_map_F3_${M}-ng${NG}"
        if [ -e "$D" ]; then echo "b_map_r8m1a4: REFUSED: exists $D" >&2; exit 2; fi
        mkdir -p "$D" || exit 2

        env -i PATH="$PATH" LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 FMM_MODE="$M" S4FMM_NG="$NG" gdb -batch -nx -x "$GDBSCRIPT" --args "$DRV" pattern both 4 3 > "$D/gdb.txt" 2>&1
        echo "gdb_rc=$?" > "$D/gdb_rc.txt"

        grep -E '^\$[0-9]+ = |RC first|RC retry|HITCOUNT|S4FMM S3R4C3_WIN_MALLOC' "$D/gdb.txt" > "$D/counts.txt"
        grep 'S4FMM S3R4C3_WIN_MALLOC' "$D/gdb.txt" > "$D/stderr.txt"
        echo "b_map F3 $M NG$NG done: $D"
    done
done

echo "b_map_r8m1a4: all 6 combos completed successfully"
exit 0
