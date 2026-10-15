REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# reuse_check_r8m2a2.sh -- P05-S4 R8 M2a2 section 4.1: recompute sha256 of the reusable R8/R7 artifacts and compare
# with the recorded values (BUILD_R8.tsv, DRIVERS_R8.tsv, DRIVERS_R7_SEAM.tsv, the drivers_r8m1 record).
# Output: $EV/REUSE_CHECK_R8_M2a2.tsv.  Refuses to overwrite (U17).  Read-only on the artifacts.
set -u
refuse() { echo "reuse_check_r8m2a2: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8/m2a2 ] || refuse "first argument must be p05-s4r8/m2a2"
OUTF="$EV/REUSE_CHECK_R8_M2a2.tsv"
test ! -e "$OUTF" || refuse "exists (U17): $OUTF"
EVR=$REPO/checkpoints/p05/evidence
REG=$REPO/checkpoints/p05/registries
{
    echo "# REUSE_CHECK_R8_M2a2 -- sha256 recomputed now vs recorded (P05-S4 R8 M2a2 section 4.1)"
    echo "# columns: artifact	path	recorded_sha256	actual_sha256	verdict	record_source"
    # F3 dbg library (BUILD_R8.tsv row 'F3 dbg')
    p="$EVR/p05-s4r8/build_r8/F3-dbg/build/libS4.a"
    rec=56f72c5882d4293bbb2d45a272d7c7727e401085b900854b1f49b851effd897a
    act=$(sha256sum "$p" | cut -d' ' -f1)
    echo "F3-dbg-lib	$p	$rec	$act	$([ "$rec" = "$act" ] && echo SAME || echo DIFFERENT)	registries/s4r8/BUILD_R8.tsv:4"
    # F3 plain library (BUILD_R8.tsv row 'F3 plain')
    p="$EVR/p05-s4r8/build_r8/F3-plain/build/libS4.a"
    rec=abbc01c78f0a422f3494556bb43e212e397fbbf49d03370132ae45e2c268e5de
    act=$(sha256sum "$p" | cut -d' ' -f1)
    echo "F3-plain-lib	$p	$rec	$act	$([ "$rec" = "$act" ] && echo SAME || echo DIFFERENT)	registries/s4r8/BUILD_R8.tsv:3"
    # DRIVERS_R8.tsv rows (driver_sha256 column 5)
    for d in d003-F3-plain:afd4adb303acf06ddb0d34ed5e8a8de211f54d81a2c649ce946bba5c4ff7cb5c d003plan-F3-plain:be478d9063e5c49a6d703110bd89875499287f8a5d1a2de97def2ec3df5f2faf seam-fmmret-F3:f7d445cc2a48ef9d7fae2118c3cd3c715bffaff2de89ab795dd74613f2ea585c seam-seamF-F3:c691acd71db3d4aabdc08f999058033228513f7049e19c3715720aab55df4ae6; do
        name=${d%%:*}
        rec=${d#*:}
        p="$EVR/p05-s4r8/drivers_r8/$name/driver"
        act=$(sha256sum "$p" | cut -d' ' -f1)
        echo "driver-$name	$p	$rec	$act	$([ "$rec" = "$act" ] && echo SAME || echo DIFFERENT)	registries/s4r8/DRIVERS_R8.tsv"
    done
    # drivers_r8m1 drivers (recorded in the r8m1 registry; the sha is read from the DRIVERS_R8_M1a_LINKED.tsv record)
    for name in init-F3 polyinj-F3 r6bstate-F3-dbg; do
        p="$EVR/p05-s4r8/drivers_r8m1/$name/driver"
        act=$(sha256sum "$p" | cut -d' ' -f1)
        echo "driver-m1-$name	$p	RECORD_IN_LINKED	$act	CHECK_BY_HAND_IN_REPORT	registries/s4r8/M1a/DRIVERS_R8_M1a_LINKED.tsv"
    done
    # F2 fmmret driver (DRIVERS_R7_SEAM.tsv row fmmret-F2: column 4 is the driver sha)
    p="$EVR/p05-s4r7/drivers_r7/seam-fmmret-F2/driver"
    rec=$(grep -E '^fmmret-F2' "$REG/s4r7/DRIVERS_R7_SEAM.tsv" | head -n 1 | cut -f4)
    act=$(sha256sum "$p" | cut -d' ' -f1)
    echo "driver-seam-fmmret-F2	$p	$rec	$act	$([ "$rec" = "$act" ] && echo SAME || echo DIFFERENT)	registries/s4r7/DRIVERS_R7_SEAM.tsv:4"
} > "$OUTF"
echo "reuse_check_r8m2a2: wrote $OUTF"
exit 0
