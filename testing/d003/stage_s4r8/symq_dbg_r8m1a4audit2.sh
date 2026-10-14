#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# symq_dbg_r8m1a4audit2.sh -- read-only debug-information query (section 4): whether a driver carries DWARF debug
# sections (argument source of the seam hooks: DWARF variable or the x86_64 $rdi fallback of callseq_r8m1a4_gdb.py).
# New file.  Uses readelf only.  Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit2 -- sh testing/d003/stage_s4r8/symq_dbg_r8m1a4audit2.sh DRIVER_PATH OUT_NAME
# OUT_NAME must be SYMQ_DBG_R8_M1a4AUDIT2_<name>.txt and must not exist (U17).
set -u
DRV=${1:?"driver path"}
OUT_NAME=${2:?"out name"}
case "$OUT_NAME" in
    SYMQ_DBG_R8_M1a4AUDIT2_*.txt) ;;
    *) echo "symq_dbg: OUT_NAME must be SYMQ_DBG_R8_M1a4AUDIT2_<name>.txt" >&2; exit 2 ;;
esac
test -f "$DRV" || { echo "symq_dbg: driver missing: $DRV" >&2; exit 2; }
test ! -e "$EV/$OUT_NAME" || { echo "symq_dbg: exists (U17): $OUT_NAME" >&2; exit 2; }
OUT="$EV/$OUT_NAME"
{
    echo "# readelf -S section names with 'debug' and the count of DWARF sections for $DRV"
    readelf -SW "$DRV" | awk '{for(i=1;i<=NF;i++) if ($i ~ /^\.debug_/) print $i}' | LC_ALL=C sort | uniq -c
    echo "DEBUG_SECTION_COUNT=$(readelf -SW "$DRV" | awk '{for(i=1;i<=NF;i++) if ($i ~ /^\.debug_/) n++} END{print n+0}')"
} > "$OUT"
echo "symq_dbg: wrote $OUT"
exit 0
