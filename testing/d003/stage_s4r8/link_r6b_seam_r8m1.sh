#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# link_r6b_seam_r8m1.sh -- P05-S4 R8 M1a, section 5.2: the G6 state drivers r6bseam-seamF-F3 and r6bseam-fmmret-F3,
# linked against the F3 seam debug libraries of this round (build_r8m1/seam_dbg).  New file.
# Copy of testing/d003/stage_s4r7/link_r6b_seam_r7.sh (committed, not modified).  Changes against the original:
#   (1) the standard first line (brief section 0.2) replaces the R7 first line;
#   (2) the two libraries are the F3 seam debug libraries of build_r8m1/seam_dbg (not the R7 F tree libraries);
#   (3) the outputs are $EV/drivers_r8m1/r6bseam-<NAME>-F3/driver and $EV/DRIVER_R6B_SEAM_R8_M1a.tsv;
#   (4) an existing driver is refused (U17), not overwritten.
# Compile line and LIBFLAGS are those of the R7 script (driver_r6b_state.cpp + inject_r4_plan.cpp, -O0 -g).
#
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/link_r6b_seam_r8m1.sh p05-s4r8
set -u
OUT_ARG=${1:?"usage: link_r6b_seam_r8m1.sh p05-s4r8"}
[ "$OUT_ARG" = p05-s4r8 ] || { echo "link_r6b_seam_r8m1: first argument must be p05-s4r8" >&2; exit 2; }
SAFE="$REPO/testing/d003/safe_run.sh"
ST4="$REPO/testing/d003/stage_s4"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
OUTROOT="$EV/drivers_r8m1"
TSV="$EV/DRIVER_R6B_SEAM_R8_M1a.tsv"

# every input must exist before the output is created (brief 0.2)
for L in "$EV/build_r8m1/seam_dbg/seamF-F3/build/libS4.a" "$EV/build_r8m1/seam_dbg/fmmret-F3/build/libS4.a" \
         "$EV/build_r8m1/seam_dbg/seamF-F3/S4" "$EV/build_r8m1/seam_dbg/fmmret-F3/S4" \
         "$ST4/driver_r6b_state.cpp" "$ST4/inject_r4_plan.cpp"; do
    test -e "$L" || { echo "link_r6b_seam_r8m1: missing input $L" >&2; exit 2; }
done
test ! -e "$TSV" || { echo "REFUSED: exists (U17): $TSV" >&2; exit 2; }
sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && : > "$2"' sh "$OUTROOT" "$TSV" || exit 2

link() {
    NAME=$1; TREEDIR=$2
    LIB="$TREEDIR/build/libS4.a"
    OUTDIR="$OUTROOT/r6bseam-$NAME-F3"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'test ! -e "$1/driver" && mkdir -p "$1" && g++ -O0 -g -Wall -Wextra -Wno-unused-parameter -I "$2/S4" -I "$2/S4/fmm" "$3/driver_r6b_state.cpp" "$3/inject_r4_plan.cpp" -o "$1/driver" -L "$2/build" -lS4 '"$LIBFLAGS"' > "$1/build.stdout" 2>&1' \
        sh "$OUTDIR" "$TREEDIR" "$ST4" || { echo "link FAILED $NAME (see $OUTDIR/build.stdout)" >&2; return 1; }
    test -x "$OUTDIR/driver" || { echo "driver not executable: $NAME" >&2; return 1; }
    LSHA=$(sha256sum "$LIB" 2>&1 | cut -d' ' -f1)
    DSHA=$(sha256sum "$OUTDIR/driver" 2>&1 | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" >> "$5"' sh "r6bseam-$NAME-F3" "$LSHA" "$DSHA" "$LIB" "$TSV" || return 1
    echo "r6bseam-$NAME-F3 lib_sha256=$LSHA driver_sha256=$DSHA"
}

link seamF   "$EV/build_r8m1/seam_dbg/seamF-F3"   || exit 1
link fmmret  "$EV/build_r8m1/seam_dbg/fmmret-F3"  || exit 1
echo "link_r6b_seam_r8m1: done"
exit 0
