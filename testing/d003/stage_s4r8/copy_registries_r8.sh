#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_r8.sh -- P05-S4 R8 M0 closing: copy the small result tables to registries/s4r8 (new file).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/copy_registries_r8.sh p05-s4r8
# Order (brief section 3; U121): (1) every input is confirmed to exist, (2) the destination directory is confirmed, (3) no
# destination file may exist (U17), (4) copy, (5) cmp of every copy against its original, (6) SHA256SUMS.txt in the
# destination directory (covers the copies and ERRATA_8.txt; ERRATA_8.txt must be final before this step), (7) sha256sum -c
# inside the destination directory.  Results: $EV/COPY_CHECK_R8_M0.txt (new).  A file larger than 1 MB is not copied and is
# reported as SKIPPED_OVER_1MB.
# The copy list maps each copy name to its original in the round evidence directory.  BUILD_R8.tsv comes from the top level
# $EV/BUILD_R8.tsv (the comparison table with SAME/DIFFERENT), not from build_r8/.
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "copy_registries_r8: first argument must be p05-s4r8" >&2; exit 2; }
DST="$REPO/checkpoints/p05/registries/s4r8"
RES="$EV/COPY_CHECK_R8_M0.txt"
test ! -e "$RES" || { echo "copy_registries_r8: REFUSED exists: COPY_CHECK_R8_M0.txt" >&2; exit 2; }
test -d "$DST" || { echo "copy_registries_r8: REFUSED: destination directory missing" >&2; exit 2; }
test -f "$DST/ERRATA_8.txt" || { echo "copy_registries_r8: REFUSED: ERRATA_8.txt missing" >&2; exit 2; }
test ! -e "$DST/SHA256SUMS.txt" || { echo "copy_registries_r8: REFUSED exists: destination SHA256SUMS.txt" >&2; exit 2; }

# name in the destination  <-  original in $EV
COPY_LIST="GATE_R8_M0.txt GATE_R8_M0_R2.txt GATE_R8_M0_R2_END.txt GATE_R8_M0_R3_END.txt GATE3_VS_GATE2_DIFF_R8.txt S4R7_MANIFEST_CHECK_R8_R2.tsv S4R7_MANIFEST_CHECK_R8_R2_END.tsv S4R7_RECHECK_R8_R3_END.txt PRERUN_CHECKS_R8_M0.txt TREE_CHECK_R8.txt BUILD_R8.tsv SEAM_DIFF_F2_vs_F3_R8.txt DRIVERS_R8.tsv DRIVERS_R8_F2_REUSED.tsv DRIVER_MAP_R8_D.tsv D_PREPARE_CHECK_R8.tsv EXPECT_R8_D.txt RESULTS_R8_D_pass1.tsv RESULTS_R8_D_pass2.tsv D_SUMMARY_R8.txt EXPECT_R8_NOINJECT.txt RESULTS_R8_NOINJECT_run1.tsv RUNNER_DIFF_R8_M0.txt status_before_rec_r8.txt"

# (1) inputs
for f in $COPY_LIST; do
    if [ "$f" = BUILD_R8.tsv ]; then src="$EV/BUILD_R8.tsv"; else src="$EV/$f"; fi
    test -f "$src" || { echo "copy_registries_r8: REFUSED: input missing: $src" >&2; exit 2; }
done
# (3) destinations must not exist
for f in $COPY_LIST; do
    test ! -e "$DST/$f" || { echo "copy_registries_r8: REFUSED exists: $DST/$f" >&2; exit 2; }
done
# (4) copy, (5) cmp, size rule
{
    printf '# COPY_CHECK_R8_M0.txt -- copy of the round tables to registries/s4r8 (closing brief section 3).\n'
    printf 'name\tsize_bytes\tresult\n'
    for f in $COPY_LIST; do
        if [ "$f" = BUILD_R8.tsv ]; then src="$EV/BUILD_R8.tsv"; else src="$EV/$f"; fi
        sz=$(wc -c < "$src")
        if [ "$sz" -gt 1048576 ]; then
            printf '%s\t%s\tSKIPPED_OVER_1MB\n' "$f" "$sz"
            continue
        fi
        cp "$src" "$DST/$f" || { printf '%s\t%s\tCOPY_FAILED\n' "$f" "$sz"; continue; }
        if cmp -s "$src" "$DST/$f"; then r=COPY_IDENTICAL; else r=COPY_DIFFERENT; fi
        printf '%s\t%s\t%s\n' "$f" "$sz" "$r"
    done
} > "$RES"
# (6) SHA256SUMS.txt in the destination (copies and ERRATA_8.txt), (7) sha256sum -c inside the destination directory
{
    for f in $COPY_LIST ERRATA_8.txt; do
        if [ -f "$DST/$f" ]; then printf '%s  %s\n' "$(sha256sum "$DST/$f" | cut -d' ' -f1)" "$f"; fi
    done
} > "$DST/SHA256SUMS.txt"
{
    printf '# sha256sum -c inside registries/s4r8 (SHA256SUMS.txt): \n'
    cd "$DST" && sha256sum -c SHA256SUMS.txt
    printf 'check_rc=%s\n' "$?"
} >> "$RES" 2>&1
echo "copy_registries_r8: done -> $RES"
exit 0
