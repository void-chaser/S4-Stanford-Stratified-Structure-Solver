REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# nm_check_r4_r8m2a2.sh -- P05-S4 R8 M2a2 R4: static symbol check of the R4 dual drivers (read only; nothing is run).
# Confirms that the R4 drivers carry the R3 injector symbols (s4fmm_inject2_invalid etc.), which the R2 build did not have,
# and records the defined/undefined status of the --wrap symbols.  Output: $EV/NM_CHECK_R4_R8_M2a2.tsv.  Refuses to overwrite (U17).
set -u
OUTF=$EV/NM_CHECK_R4_R8_M2a2.tsv
if [ -e "$OUTF" ]; then echo "nm_check_r4_r8m2a2: REFUSED exists (U17): $OUTF" >&2; exit 2; fi
D=$EV/build_R4
{
    echo "# NM_CHECK_R4_R8_M2a2 -- static symbols of the R4 dual drivers (no driver run)"
    echo "# columns: driver	symbol	defined_T_or_W	count_in_driver"
    for drv in dual-F3-dbg-R4 layers-dual-F3-dbg-R4; do
        for sym in s4fmm_inject2_invalid s4fmm_inject2_suppressed s4fmm_inject2_hits s4fmm_inject2_requested s4fmm_inject_hits S4_TEST_LINEARSOLVE_NULLINFO2_AFTER __wrap__Z9S4_mallocm __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i __wrap__Z13fft_plan_execP12tag_fft_plan __wrap_malloc; do
            n=$(nm "$D/$drv" | grep -c " [TtWw] $sym\$")
            if [ "$n" -gt 0 ]; then st=DEFINED; else st=ABSENT; fi
            printf '%s\t%s\t%s\t%s\n' "$drv" "$sym" "$st" "$n"
        done
    done
} > "$OUTF"
echo "nm_check_r4_r8m2a2: wrote $OUTF"
exit 0
