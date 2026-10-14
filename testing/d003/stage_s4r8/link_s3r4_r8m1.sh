#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# link_s3r4_r8m1.sh -- P05-S4 R8 M1a, section 5.2 (U142): the F3 drivers of the 22-row additions and the polygon group,
# linked against the R8 F3 plain library (build_r8/F3-plain).  New file.
# Copies of the S3R4 link commands (committed, not modified):
#   init-F3  : testing/d003/stage_s3r4c2/link_init_c2.sh   (driver_r6b_state.cpp + inject_s3r4_init.cpp, wrap Pattern_GetContainmentTree)
#   polyinj-F3: testing/d003/stage_s3r4c3/link_poly_inj_c3.sh (driver_s3r4c2_poly.cpp + inject_s3r4c3_poly.cpp, wrap Pattern_DiscretizeCell)
#   poly-F3  : testing/d003/stage_s3r4c2/link_c2.sh kind poly (driver_s3r4c2_poly.cpp + inject_r4_plan.cpp)
# Changes against the originals: the library (R8 F3 plain of M0, not the S3R4 F3 library), the output directory
# $EV/drivers_r8m1/, the compile line -O1 as in the originals, and an existing driver is refused (U17).
# The S3R4 F2 drivers are NOT linked here; they are reused read only (DRIVERS_R8_M1a_F2_REUSED.tsv, section 5.3).
# Output: $EV/drivers_r8m1/<NAME>/driver ; $EV/DRIVERS_S3R4_R8_M1a_F3.tsv
#
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/link_s3r4_r8m1.sh p05-s4r8
set -u
OUT_ARG=${1:?"usage: link_s3r4_r8m1.sh p05-s4r8"}
[ "$OUT_ARG" = p05-s4r8 ] || { echo "link_s3r4_r8m1: first argument must be p05-s4r8" >&2; exit 2; }
SAFE="$REPO/testing/d003/safe_run.sh"
LIB="$EV/build_r8/F3-plain/build/libS4.a"
SRCTREE="$EV/build_r8/F3-plain"
OUTROOT="$EV/drivers_r8m1"
TSV="$EV/DRIVERS_S3R4_R8_M1a_F3.tsv"
LF_INIT="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_GetContainmentTree"
LF_POLY="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_DiscretizeCell"
LF_BASE="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
ST4="$REPO/testing/d003/stage_s4"
DRV_STATE="$ST4/driver_r6b_state.cpp"
DRV_POLY="$REPO/testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp"
INJ_INIT="$REPO/testing/d003/stage_s3r4/inject_s3r4_init.cpp"
INJ_POLY="$REPO/testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp"
INJ_R4="$ST4/inject_r4_plan.cpp"

# every input must exist before the output is created (brief 0.2)
for F in "$LIB" "$SRCTREE/S4" "$DRV_STATE" "$DRV_POLY" "$INJ_INIT" "$INJ_POLY" "$INJ_R4"; do
    test -e "$F" || { echo "link_s3r4_r8m1: missing input $F" >&2; exit 2; }
done
test ! -e "$TSV" || { echo "REFUSED: exists (U17): $TSV" >&2; exit 2; }
sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && : > "$2"' sh "$OUTROOT" "$TSV" || exit 2

# link NAME DRIVER INJECTOR LIBFLAGS
link() {
    N=$1; D=$2; I=$3; LF=$4
    OUTDIR="$OUTROOT/$N"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'test ! -e "$1/driver" && mkdir -p "$1" && g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$2/S4" -I "$2/S4/fmm" "$3" "$4" -o "$1/driver" -L "$2/build" -lS4 '"$LF"' > "$1/build.stdout" 2>&1' \
        sh "$OUTDIR" "$SRCTREE" "$D" "$I" || { echo "link FAILED $N (see $OUTDIR/build.stdout)" >&2; return 1; }
    test -x "$OUTDIR/driver" || { echo "driver not executable: $N" >&2; return 1; }
    LSHA=$(sha256sum "$LIB" 2>&1 | cut -d' ' -f1)
    DSHA=$(sha256sum "$OUTDIR/driver" 2>&1 | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" >> "$5"' sh "$N" "$LSHA" "$DSHA" "$LIB" "$TSV" || return 1
    echo "$N lib_sha256=$LSHA driver_sha256=$DSHA"
}

link init-F3     "$DRV_STATE" "$INJ_INIT" "$LF_INIT" || exit 1
link polyinj-F3  "$DRV_POLY"  "$INJ_POLY" "$LF_POLY" || exit 1
link poly-F3     "$DRV_POLY"  "$INJ_R4"   "$LF_BASE" || exit 1
echo "link_s3r4_r8m1: done"
exit 0
