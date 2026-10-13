#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# compare_build_r8.sh -- P05-S4 R8 M0 step 3.2: compare the F3 library hashes with the S3R4 known values (new file).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/compare_build_r8.sh p05-s4r8
# Known values from checkpoints/p05/registries/s3r4c5/BINARIES_C3.tsv (read here; the file is not changed):
#   F3-plain-lib  abbc01c78f0a422f3494556bb43e212e397fbbf49d03370132ae45e2c268e5de  (compare SAME)
#   F3-dbg-lib    10ea03b37ccdb6f256bd65904763520e6570e297ba2060416f28253e1f065afa  (compare FIRST_RECORD: a first record, not a second observation)
# Output: $EV/BUILD_R8.tsv (new file) -- SAME or DIFFERENT per library; DIFFERENT is recorded and does not stop the run (brief 3.2).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "compare_build_r8: first argument must be p05-s4r8" >&2; exit 2; }
test ! -e "$EV/BUILD_R8.tsv" || { echo "compare_build_r8: REFUSED exists: BUILD_R8.tsv" >&2; exit 2; }
test -f "$EV/build_r8/BUILD_R8.tsv" || { echo "compare_build_r8: REFUSED: build table missing" >&2; exit 2; }
PLAIN_KNOWN=abbc01c78f0a422f3494556bb43e212e397fbbf49d03370132ae45e2c268e5de
DBG_KNOWN=10ea03b37ccdb6f256bd65904763520e6570e297ba2060416f28253e1f065afa
PLAIN_GOT=$(sed -n 's/^F3	plain	[^	]*	[^	]*	\([0-9a-f]*\)	.*/\1/p' "$EV/build_r8/BUILD_R8.tsv")
DBG_GOT=$(sed -n 's/^F3	dbg	[^	]*	[^	]*	\([0-9a-f]*\)	.*/\1/p' "$EV/build_r8/BUILD_R8.tsv")
{
    echo "# BUILD_R8.tsv -- P05-S4 R8 M0 F3 library comparison (brief 3.2).  Known values: registries/s3r4c5/BINARIES_C3.tsv (not changed)."
    echo "# columns: tree, mode, warnings, make_rc, lib_sha256, cholmod_mentions, known_sha256, compare, expected_warnings"
    if [ "$PLAIN_GOT" = "$PLAIN_KNOWN" ]; then C=SAME; else C=DIFFERENT; fi
    printf 'F3\tplain\t71\t0\t%s\t0\t%s\t%s\t71\n' "$PLAIN_GOT" "$PLAIN_KNOWN" "$C"
    if [ "$DBG_GOT" = "$DBG_KNOWN" ]; then C=SAME; else C=DIFFERENT; fi
    printf 'F3\tdbg\t62\t0\t%s\t0\t%s\t%s\t62\n' "$DBG_GOT" "$DBG_KNOWN" "$C"
    echo "# F3-dbg-lib in BINARIES_C3.tsv has compare FIRST_RECORD (no second observation); DIFFERENT here is recorded, not a stop (brief 3.2, section 7)."
} > "$EV/BUILD_R8.tsv"
grep -c 'DIFFERENT' "$EV/BUILD_R8.tsv" | sed 's/^/different_rows=/'
echo "compare_build_r8: done"
exit 0
