#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# symq_r8m1a4audit2.sh -- read-only symbol query for the tracer audit (section 4).  New file.  Uses only nm, readelf and
# gdb -batch -nx.  Writes into the round evidence directory only.  Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit2 -- sh testing/d003/stage_s4r8/symq_r8m1a4audit2.sh DRIVER_PATH OUT_NAME
# OUT_NAME is a bare name (SYMQ_R8_M1a4AUDIT2_<name>.txt) and must not exist (U17).
set -u
DRV=${1:?"driver path"}
OUT_NAME=${2:?"out name"}
case "$OUT_NAME" in
    SYMQ_R8_M1a4AUDIT2_*.txt) ;;
    *) echo "symq: OUT_NAME must be SYMQ_R8_M1a4AUDIT2_<name>.txt" >&2; exit 2 ;;
esac
test -f "$DRV" || { echo "symq: driver missing: $DRV" >&2; exit 2; }
test ! -e "$EV/$OUT_NAME" || { echo "symq: exists (U17): $OUT_NAME" >&2; exit 2; }
OUT="$EV/$OUT_NAME"
{
    echo "# symq for driver $DRV"
    echo "# nm: exact-name lookup of the tracer's breakpoint names:"
    for SYM in __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i __wrap_malloc __wrap__Z9S4_mallocm __wrap__Z13fft_plan_execP12tag_fft_plan __wrap_Pattern_GenerateFlowField S4_TEST_ALLOC_HOOK S4_TEST_KOTTKE_HOOK S4_TEST_FMMRET_AFTER S4_TEST_LINEARSOLVE_AFTER S4_TEST_LINEARSOLVE_NULLINFO2_AFTER S4_TEST_ADDFIELD_AFTER _Z15fft_plan_dft_2dPiPSt7complexIdES2_i _Z9S4_mallocm _Z13fft_plan_execP12tag_fft_plan Pattern_GenerateFlowField; do
        LINE=$(nm "$DRV" | awk -v s="$SYM" '$3==s {print $1" "$2" "$3}' | head -n 1)
        if [ -n "$LINE" ]; then
            echo "SYM $SYM present: $LINE"
        else
            echo "SYM $SYM absent-from-nm"
        fi
    done
    echo "# readelf -sW: symbol table entry (value, size, type, bind, shndx, name) for the same names:"
    for SYM in __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i __wrap_malloc __wrap__Z9S4_mallocm __wrap__Z13fft_plan_execP12tag_fft_plan __wrap_Pattern_GenerateFlowField S4_TEST_ALLOC_HOOK S4_TEST_KOTTKE_HOOK S4_TEST_FMMRET_AFTER S4_TEST_LINEARSOLVE_AFTER S4_TEST_LINEARSOLVE_NULLINFO2_AFTER S4_TEST_ADDFIELD_AFTER; do
        RL=$(readelf -sW "$DRV" | awk -v s="$SYM" '$8==s {print $2" "$3" "$4" "$5" "$7" "$8}' | head -n 1)
        if [ -n "$RL" ]; then
            echo "READELF $SYM value_size_type_bind_ndx_shndx_name: $RL"
        else
            echo "READELF $SYM not-found"
        fi
    done
    echo "# gdb -batch -nx: breakpoint resolution of each name (no run)"
    GDBSCRIPT=$EV/tmp/symq_gdb_$$.gdb
    : > "$GDBSCRIPT"
    for SYM in __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i __wrap_malloc __wrap__Z9S4_mallocm __wrap__Z13fft_plan_execP12tag_fft_plan __wrap_Pattern_GenerateFlowField S4_TEST_ALLOC_HOOK S4_TEST_KOTTKE_HOOK S4_TEST_FMMRET_AFTER S4_TEST_LINEARSOLVE_AFTER S4_TEST_LINEARSOLVE_NULLINFO2_AFTER S4_TEST_ADDFIELD_AFTER; do
        echo "set breakpoint pending off" >> "$GDBSCRIPT"
        echo "python" >> "$GDBSCRIPT"
        echo "import gdb" >> "$GDBSCRIPT"
        echo "try:" >> "$GDBSCRIPT"
        echo "    b = gdb.Breakpoint('$SYM', internal=True)" >> "$GDBSCRIPT"
        echo "    print('GDB $SYM locations=%d pending=%s' % (len(b.locations) if b.locations is not None else -1, b.pending))" >> "$GDBSCRIPT"
        echo "    b.delete()" >> "$GDBSCRIPT"
        echo "except Exception as e:" >> "$GDBSCRIPT"
        echo "    print('GDB $SYM error=%s' % e)" >> "$GDBSCRIPT"
        echo "end" >> "$GDBSCRIPT"
    done
    PYTHONDONTWRITEBYTECODE=1 gdb -batch -nx -ex "file $DRV" -x "$GDBSCRIPT" 2>&1 | grep '^GDB '
    rm -f "$GDBSCRIPT"
} > "$OUT"
echo "symq: wrote $OUT"
exit 0
