#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a4audit3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# symq_r8m1a4audit3.sh -- U190 T6: read-only symbol query for EVERY distinct driver used by the 198 units (r8m1a4audit3).
# New file (symq_r8m1a4audit2.sh is not modified).  It takes the distinct driver list from the units table
# (CALLSEQ_UNITS_R8_M1a4_R3.tsv, driver_sha256 and driver_path), checks each file's sha256 against the table, and writes one
# SYMQ_R8_M1a4AUDIT3_<sha12>.txt per distinct driver (sha256 de-duplicated; 18 drivers).  Tools: sha256sum, nm, readelf, gdb -batch -nx.
# Nothing is executed from the driver: no run, only symbol and breakpoint resolution.  Writes into the round evidence directory only.
# Usage (through safe_run):
#   sh testing/d003/safe_run.sh p05-s4r8/m1a4audit3 -- sh testing/d003/stage_s4r8/symq_r8m1a4audit3.sh
# Output: SYMQ_INDEX_R8_M1a4AUDIT3.tsv (one row per distinct driver: sha256, tag, path, sha_ok, count of units) and one SYMQ file each.
# The script refuses if any SYMQ or the index already exists (U17).
set -u
UNITS=checkpoints/p05/registries/s4r8/M1a/CALLSEQ_UNITS_R8_M1a4_R3.tsv
IDX="$EV/SYMQ_INDEX_R8_M1a4AUDIT3.tsv"
test ! -e "$IDX" || { echo "symq3: exists (U17): $IDX" >&2; exit 2; }
test -f "$UNITS" || { echo "symq3: units table missing" >&2; exit 2; }

# distinct drivers: sha256 -> path (first path seen); unit count per sha
awk -F'\t' 'NR>1 { c[$6]++; if (!($6 in p)) p[$6]=$7 } END { for (s in p) print s "\t" c[s] "\t" p[s] }' "$UNITS" | LC_ALL=C sort > "$EV/tmp/symq3_distinct.txt"
NDIST=$(wc -l < "$EV/tmp/symq3_distinct.txt" | tr -d ' ')
[ "$NDIST" = 18 ] || { echo "symq3: distinct drivers $NDIST != 18" >&2; exit 2; }

printf 'driver_sha256\tsymq_file\tunits\tpath\tsha_ok\tsha_actual\n' > "$IDX"
while IFS='	' read -r SHA CNT DRV; do
    TAG=$(printf '%s' "$SHA" | cut -c1-12)
    SYMF="SYMQ_R8_M1a4AUDIT3_$TAG.txt"
    test ! -e "$EV/$SYMF" || { echo "symq3: exists (U17): $SYMF" >&2; exit 2; }
    test -f "$DRV" || { echo "symq3: driver missing: $DRV" >&2; exit 2; }
    ACT=$(sha256sum "$DRV" | cut -d' ' -f1)
    if [ "$ACT" = "$SHA" ]; then OK=yes; else OK=no; fi
    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$SHA" "$SYMF" "$CNT" "$DRV" "$OK" "$ACT" >> "$IDX"
    OUT="$EV/$SYMF"
    {
        echo "# symq3 (U190 T6) for driver $DRV"
        echo "# driver_sha256 expected=$SHA actual=$ACT sha_ok=$OK units=$CNT"
        echo "# nm: exact-name lookup of the tracer breakpoint names:"
        for S in __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i __wrap_malloc __wrap__Z9S4_mallocm __wrap__Z13fft_plan_execP12tag_fft_plan __wrap_Pattern_GenerateFlowField S4_TEST_ALLOC_HOOK S4_TEST_KOTTKE_HOOK S4_TEST_FMMRET_AFTER S4_TEST_LINEARSOLVE_AFTER S4_TEST_LINEARSOLVE_NULLINFO2_AFTER S4_TEST_ADDFIELD_AFTER _Z15fft_plan_dft_2dPiPSt7complexIdES2_i _Z9S4_mallocm _Z13fft_plan_execP12tag_fft_plan Pattern_GenerateFlowField; do
            L=$(nm "$DRV" | awk -v s="$S" '$3==s {print $1" "$2" "$3}' | head -n 1)
            if [ -n "$L" ]; then echo "SYM $S present: $L"; else echo "SYM $S absent-from-nm"; fi
        done
        echo "# readelf -sW: symbol table entry for the same names:"
        for S in __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i __wrap_malloc __wrap__Z9S4_mallocm __wrap__Z13fft_plan_execP12tag_fft_plan __wrap_Pattern_GenerateFlowField S4_TEST_ALLOC_HOOK S4_TEST_KOTTKE_HOOK S4_TEST_FMMRET_AFTER S4_TEST_LINEARSOLVE_AFTER S4_TEST_LINEARSOLVE_NULLINFO2_AFTER S4_TEST_ADDFIELD_AFTER; do
            RL=$(readelf -sW "$DRV" | awk -v s="$S" '$8==s {print $2" "$3" "$4" "$5" "$7" "$8}' | head -n 1)
            if [ -n "$RL" ]; then echo "READELF $S value_size_type_bind_ndx_name: $RL"; else echo "READELF $S not-found"; fi
        done
        echo "# gdb -batch -nx: breakpoint resolution of each name (no run)"
        GDBSCRIPT="$EV/tmp/symq3_gdb_$TAG.gdb"
        : > "$GDBSCRIPT"
        for S in __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i __wrap_malloc __wrap__Z9S4_mallocm __wrap__Z13fft_plan_execP12tag_fft_plan __wrap_Pattern_GenerateFlowField S4_TEST_ALLOC_HOOK S4_TEST_KOTTKE_HOOK S4_TEST_FMMRET_AFTER S4_TEST_LINEARSOLVE_AFTER S4_TEST_LINEARSOLVE_NULLINFO2_AFTER S4_TEST_ADDFIELD_AFTER; do
            echo "set breakpoint pending off" >> "$GDBSCRIPT"
            echo "python" >> "$GDBSCRIPT"
            echo "import gdb" >> "$GDBSCRIPT"
            echo "try:" >> "$GDBSCRIPT"
            echo "    b = gdb.Breakpoint('$S', internal=True)" >> "$GDBSCRIPT"
            echo "    print('GDB $S locations=%d pending=%s' % (len(b.locations) if b.locations is not None else -1, b.pending))" >> "$GDBSCRIPT"
            echo "    b.delete()" >> "$GDBSCRIPT"
            echo "except Exception as e:" >> "$GDBSCRIPT"
            echo "    print('GDB $S error=%s' % e)" >> "$GDBSCRIPT"
            echo "end" >> "$GDBSCRIPT"
        done
        PYTHONDONTWRITEBYTECODE=1 gdb -batch -nx -ex "file $DRV" -x "$GDBSCRIPT" 2>&1 | grep '^GDB '
        rm -f "$GDBSCRIPT"
    } > "$OUT"
done < "$EV/tmp/symq3_distinct.txt"
rm -f "$EV/tmp/symq3_distinct.txt"
echo "symq3: wrote $NDIST symq files and $IDX"
exit 0
