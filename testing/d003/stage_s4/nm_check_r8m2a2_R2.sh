REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# nm_check_r8m2a2_R2.sh -- P05-S4 R8 M2a2 section 4.1 (R2 of nm_check_r8m2a2.sh).
# Same checks.  The first version used 2>/dev/null, which the brief forbids (section 1.3); that version ran
# and wrote NM_CHECK_R8_M2a2.tsv, which is kept (U17).  This R2 writes NM_CHECK_R8_M2a2_R2.tsv without stderr redirection.
set -u
refuse() { echo "nm_check_r8m2a2_R2: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8/m2a2 ] || refuse "first argument must be p05-s4r8/m2a2"
OUTF="$EV/NM_CHECK_R8_M2a2_R2.tsv"
test ! -e "$OUTF" || refuse "exists (U17): $OUTF"
EVR=$REPO/checkpoints/p05/evidence/p05-s4r8
SEAMF=$EVR/build_r8/seam_plain/seamF-F3-plain/build/libS4.a
DBG=$EVR/build_r8/F3-dbg/build/libS4.a
PLAIN=$EVR/build_r8/F3-plain/build/libS4.a
{
    echo "# NM_CHECK_R8_M2a2_R2 -- symbol checks (P05-S4 R8 M2a2 section 4.1, R2)"
    echo "# columns: check	library	probe	result	detail"
    for sym in S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER S4_TEST_LINEARSOLVE_NULLINFO2_AFTER; do
        n=$(nm -C "$SEAMF" | grep -c "$sym")
        if [ "$n" -gt 0 ]; then r=PRESENT; else r=ABSENT; fi
        echo "SYMBOL	seamF-F3-plain	$sym	$r	nm_count=$n"
    done
    for sym in S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER S4_TEST_LINEARSOLVE_NULLINFO2_AFTER; do
        n=$(nm -C "$PLAIN" | grep -c "$sym")
        if [ "$n" -gt 0 ]; then r=PRESENT; else r=ABSENT; fi
        echo "SYMBOL	F3-plain	$sym	$r	nm_count=$n"
    done
    d=$(readelf -S "$DBG" | grep -c '\.debug_info')
    if [ "$d" -gt 0 ]; then r=HAS_DEBUG_INFO; else r=NO_DEBUG_INFO; fi
    echo "DEBUG	F3-dbg	.debug_info	$r	section_lines=$d"
    d=$(readelf -S "$PLAIN" | grep -c '\.debug_info')
    if [ "$d" -gt 0 ]; then r=HAS_DEBUG_INFO; else r=NO_DEBUG_INFO; fi
    echo "DEBUG	F3-plain	.debug_info	$r	section_lines=$d"
} > "$OUTF"
echo "nm_check_r8m2a2_R2: wrote $OUTF"
exit 0
