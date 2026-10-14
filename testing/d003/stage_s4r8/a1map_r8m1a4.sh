#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# a1map_r8m1a4.sh -- P05-S4 R8 M1a CONT3a section 7 A1 map recheck on F3.  New file.
# Runs init-F3 driver with no injection under gdb -batch -nx.  3 combos: closed2d-ng1, fft-ng5, kottke-ng5.
# Usage (through safe_run):
#   sh testing/d003/stage_s4r8/a1map_r8m1a4.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "a1map_r8m1a4: first arg must be p05-s4r8" >&2; exit 2; }

DRV="$EV/drivers_r8m1/init-F3/driver"
EXPECT_DRV_SHA="ff66cfc1bf87b6c22d13e32dc6adf3c5e6b090fdcad745bf5248f74dd9510b68"
test -f "$DRV" || { echo "a1map_r8m1a4: driver missing: $DRV" >&2; exit 2; }
ACTUAL_SHA=$(sha256sum "$DRV" | cut -d' ' -f1)
[ "$ACTUAL_SHA" = "$EXPECT_DRV_SHA" ] || { echo "a1map_r8m1a4: driver sha mismatch" >&2; exit 2; }

GDBSCRIPT="$REPO/testing/d003/stage_s4r8/a1map_r8m1a4.gdb"
test -f "$GDBSCRIPT" || { echo "a1map_r8m1a4: gdb script missing: $GDBSCRIPT" >&2; exit 2; }

OUT_BASE="$EV/additions_r8m1a4"
mkdir -p "$OUT_BASE" || exit 2

# Combos: mode NG
COMBOS="closed2d:1 fft:5 kottke:5"

for C in $COMBOS; do
    MODE=$(printf '%s' "$C" | cut -d: -f1)
    NG=$(printf '%s' "$C" | cut -d: -f2)
    D="$OUT_BASE/a1map_F3_${MODE}-ng${NG}"
    if [ -e "$D" ]; then echo "a1map_r8m1a4: REFUSED: exists $D" >&2; exit 2; fi
    mkdir -p "$D" || exit 2

    # (1) Run under gdb
    env -i PATH="$PATH" LANG=C LC_ALL=C PYTHONDONTWRITEBYTECODE=1 FMM_MODE="$MODE" S4FMM_NG="$NG" S4FMM_DUMP_DIR="$D" gdb -batch -nx -x "$GDBSCRIPT" --args "$DRV" pattern both 4 3 > "$D/gdb.txt" 2>&1
    echo "gdb_rc=$?" > "$D/gdb_rc.txt"

    # (2) Extract injector lines and load base
    grep '^S4FMM S3R4_' "$D/gdb.txt" > "$D/stderr.txt"
    awk '/driver/ && $4 == "0x0" {print $1; exit}' "$D/gdb.txt" > "$D/base.txt"
    BASE=$(cat "$D/base.txt")

    # (3) Callers analysis
    sed -n 's/.*caller=\(0x[0-9a-f]*\).*/\1/p' "$D/stderr.txt" | sort -u > "$D/callers_raw.txt"
    printf 'caller\toffset\tfunction\tfile_line\n' > "$D/callers.tsv"
    while read ADDR; do
        OFF=$(printf '0x%x' $(( ADDR - BASE )))
        FN=$(addr2line -f -e "$DRV" "$OFF" | head -1)
        FL=$(addr2line -e "$DRV" "$OFF" | head -1)
        printf '%s\t%s\t%s\t%s\n' "$ADDR" "$OFF" "$FN" "$FL" >> "$D/callers.tsv"
    done < "$D/callers_raw.txt"
    echo "a1map F3 $MODE NG$NG done: $D"
done

echo "a1map_r8m1a4: all 3 combos completed successfully"
exit 0
