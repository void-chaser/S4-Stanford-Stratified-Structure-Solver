#!/bin/sh
# link_r6b_seam_r7.sh -- P05-S4 R7 cont9 (U80, section 2.1 G6): link the two G6 state drivers against the R7 -O0 -g seam
# libraries (new file).  Same construction as the R6c drivers driver-r6b-seamF and driver-r6b-fmmret-F:
# driver_r6b_state.cpp + inject_r4_plan.cpp, same LIBFLAGS as r6c2_link_fmmret.sh.  The libraries are NOT rebuilt here.
#
#   sh testing/d003/safe_run.sh p05-s4r7 -- sh testing/d003/stage_s4r7/link_r6b_seam_r7.sh p05-s4r7
#
# Outputs (new names only, U17):
#   $EV/drivers_r7/r6bseam-seamF-F/driver        (library build_r7/seam/seamF-F)
#   $EV/drivers_r7/r6bseam-fmmret-F/driver       (library build_r7/seam/fmmret-F)
# plus $EV/drivers_r7/r6bseam-<NAME>/build.stdout and DRIVER_R6B_SEAM_R7.tsv (lib sha256, driver sha256, compile command).
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "link_r6b_seam_r7: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: link_r6b_seam_r7.sh p05-s4r7"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
SAFE="$REPO/testing/d003/safe_run.sh"
ST4="$REPO/testing/d003/stage_s4"
TMPDIR="$EV/tmp"
export TMPDIR
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
TSV="$EV/drivers_r7/DRIVER_R6B_SEAM_R7.tsv"

[ -e "$TSV" ] && { echo "REFUSED: $TSV exists (U17)" >&2; exit 2; }
sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/drivers_r7" && : > "$2"' sh "$EV" "$TSV" || exit 2

link() {
    NAME=$1; TREEDIR=$2
    LIB="$TREEDIR/build/libS4.a"
    OUTDIR="$EV/drivers_r7/r6bseam-$NAME"
    test -f "$LIB" || { echo "missing library $LIB" >&2; return 1; }
    sh "$SAFE" "$OUT_ARG" -- sh -c 'test ! -e "$1/driver" && mkdir -p "$1" && g++ -O0 -g -Wall -Wextra -Wno-unused-parameter -I "$2/S4" -I "$2/S4/fmm" "$3/driver_r6b_state.cpp" "$3/inject_r4_plan.cpp" -o "$1/driver" -L "$2/build" -lS4 '"$LIBFLAGS"' > "$1/build.stdout" 2>&1' \
        sh "$OUTDIR" "$TREEDIR" "$ST4" || { echo "link FAILED $NAME (see $OUTDIR/build.stdout)" >&2; return 1; }
    test -x "$OUTDIR/driver" || return 1
    LSHA=$(sha256sum "$LIB" | cut -d' ' -f1)
    DSHA=$(sha256sum "$OUTDIR/driver" | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" >> "$5"' sh "r6bseam-$NAME" "$LSHA" "$DSHA" "$LIB" "$TSV" || return 1
    echo "r6bseam-$NAME lib_sha256=$LSHA driver_sha256=$DSHA"
}

link seamF-F   "$EV/build_r7/seam/seamF-F"   || exit 1
link fmmret-F  "$EV/build_r7/seam/fmmret-F"  || exit 1
echo "link_r6b_seam_r7: done (F-tree drivers; the F2-tree drivers are linked by link_r6b_seam_r7_f2.sh, U17)"
exit 0
