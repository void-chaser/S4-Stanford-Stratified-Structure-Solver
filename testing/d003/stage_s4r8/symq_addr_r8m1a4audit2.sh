#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# symq_addr_r8m1a4audit2.sh -- read-only breakpoint address query (section 4): for each tracer symbol, the address gdb
# would place the breakpoint at, compared with the function entry (readelf st_value).  New file.  Only nm, readelf and
# gdb -batch -nx are used.  Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit2 -- sh testing/d003/stage_s4r8/symq_addr_r8m1a4audit2.sh DRIVER_PATH OUT_NAME
# OUT_NAME must be SYMQ_ADDR_R8_M1a4AUDIT2_<name>.txt and must not exist (U17).
set -u
DRV=${1:?"driver path"}
OUT_NAME=${2:?"out name"}
case "$OUT_NAME" in
    SYMQ_ADDR_R8_M1a4AUDIT2_*.txt) ;;
    *) echo "symq_addr: OUT_NAME must be SYMQ_ADDR_R8_M1a4AUDIT2_<name>.txt" >&2; exit 2 ;;
esac
test -f "$DRV" || { echo "symq_addr: driver missing: $DRV" >&2; exit 2; }
test ! -e "$EV/$OUT_NAME" || { echo "symq_addr: exists (U17): $OUT_NAME" >&2; exit 2; }
OUT="$EV/$OUT_NAME"
GDBSCRIPT=$EV/tmp/symq_addr_gdb_$$.py
{
    echo "import gdb"
    echo "names = ['__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i', '__wrap_malloc', '__wrap__Z9S4_mallocm', '__wrap__Z13fft_plan_execP12tag_fft_plan', '__wrap_Pattern_GenerateFlowField', 'S4_TEST_ALLOC_HOOK', 'S4_TEST_KOTTKE_HOOK', 'S4_TEST_FMMRET_AFTER', 'S4_TEST_LINEARSOLVE_AFTER', 'S4_TEST_LINEARSOLVE_NULLINFO2_AFTER', 'S4_TEST_ADDFIELD_AFTER']"
    echo "for n in names:"
    echo "    try:"
    echo "        b = gdb.Breakpoint(n, internal=True)"
    echo "        locs = b.locations"
    echo "        addr = hex(locs[0].address) if locs else 'NONE'"
    echo "        print('ADDR %s locations=%d pending=%s address=%s' % (n, len(locs), b.pending, addr))"
    echo "        b.delete()"
    echo "    except Exception as e:"
    echo "        print('ADDR %s error=%s' % (n, e))"
} > "$GDBSCRIPT"
{
    echo "# breakpoint address of each tracer symbol under gdb (no run)"
    PYTHONDONTWRITEBYTECODE=1 gdb -batch -nx -ex "file $DRV" -x "$GDBSCRIPT" | grep '^ADDR '
    echo "# readelf st_value of the same names (function entry)"
    for SYM in __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i __wrap_malloc __wrap__Z9S4_mallocm __wrap__Z13fft_plan_execP12tag_fft_plan __wrap_Pattern_GenerateFlowField S4_TEST_ALLOC_HOOK S4_TEST_KOTTKE_HOOK S4_TEST_FMMRET_AFTER S4_TEST_LINEARSOLVE_AFTER S4_TEST_LINEARSOLVE_NULLINFO2_AFTER S4_TEST_ADDFIELD_AFTER; do
        RL=$(readelf -sW "$DRV" | awk -v s="$SYM" '$8==s {print $2}' | head -n 1)
        if [ -n "$RL" ]; then echo "ENTRY $SYM st_value=0x$RL"; else echo "ENTRY $SYM not-found"; fi
    done
} > "$OUT"
rm -f "$GDBSCRIPT"
echo "symq_addr: wrote $OUT"
exit 0
