#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# link_drivers_r8.sh -- P05-S4 R8 M0 step 3.4: F3 drivers, linked against the R8 F3 libraries (new file).
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/link_drivers_r8.sh p05-s4r8
# Copied from link_drivers_s4r7.sh (drivers d003, d003plan, r6bstate; plain only) and link_seam_drivers_r7.sh (seam
# drivers seamF-F3, fmmret-F3), and from the tri link command of p05-s4r7/safe_run.log (line 122, tree F2, plain),
# applied to F3.  Changes (RUNNER_DIFF_R8_M0.txt): standard first line; tree F3 only; libraries from build_r8;
# the seam libraries from build_r8/seam_plain; output directory drivers_r8; existence checks before creation (U17).
# The compile and link flags are those of the R7 scripts.  Outputs (new): $EV/drivers_r8/<NAME>/driver,
# $EV/DRIVERS_R8.tsv (driver, tree, mode, library sha256, driver sha256, library path).  Nothing is overwritten.
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "link_drivers_r8: first argument must be p05-s4r8" >&2; exit 2; }
SAFE="$REPO/testing/d003/safe_run.sh"
SRC="$REPO/testing/d003/src"
ST4="$REPO/testing/d003/stage_s4"
ST3R3="$REPO/testing/d003/stage_s3r3"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
LIBFLAGS_RNV1="$LIBFLAGS -Wl,--wrap=Pattern_GenerateFlowField"
OUTD="$EV/drivers_r8"
F3_PLAIN_LIB="$EV/build_r8/F3-plain/build/libS4.a"
SEAMF_LIB="$EV/build_r8/seam_plain/seamF-F3-plain/build/libS4.a"
FMMRET_LIB="$EV/build_r8/seam_plain/fmmret-F3-plain/build/libS4.a"
# inputs first (brief section 0.2: confirm every input before a directory is created)
for f in "$SRC/driver_d003.cpp" "$SRC/inject_d003.cpp" "$ST4/driver_r6b_state.cpp" "$ST4/inject_r4_plan.cpp" "$ST3R3/driver_s3r3_tri.cpp" "$ST4/inject_r6d_rnv1.cpp" "$F3_PLAIN_LIB" "$SEAMF_LIB" "$FMMRET_LIB"; do
    test -f "$f" || { echo "link_drivers_r8: REFUSED: input missing: $f" >&2; exit 2; }
done
test ! -e "$OUTD" || { echo "link_drivers_r8: REFUSED exists: $OUTD" >&2; exit 2; }
test ! -e "$EV/DRIVERS_R8.tsv" || { echo "link_drivers_r8: REFUSED exists: DRIVERS_R8.tsv" >&2; exit 2; }
mkdir -p "$OUTD" || exit 2
printf 'driver\ttree\tmode\tlib_sha256\tdriver_sha256\tlib_path\tdriver_path\n' > "$EV/DRIVERS_R8.tsv"

# link NAME TREE MODE LIB DRIVER_SRC INJECT_SRC LIBFLAGS OPT : one driver, one link command, one record line
link() {
    N=$1; T=$2; M=$3; LIB=$4; DSRC=$5; ISRC=$6; LF=$7; OPT=$8
    OD="$OUTD/$N"
    sh "$SAFE" p05-s4r8 -- sh -c 'test ! -e "$1" && mkdir -p "$1" && g++ $2 -Wall -Wextra -Wno-unused-parameter -I "$3/S4" -I "$3/S4/fmm" "$4" "$5" -o "$1/driver" -L "$3/build" -lS4 $6 > "$1/build.stdout" 2>&1' \
        sh "$OD" "$OPT" "$(dirname "$(dirname "$LIB")")" "$DSRC" "$ISRC" "$LF" || { echo "link FAILED $N (see $OD/build.stdout)" >&2; return 1; }
    test -x "$OD/driver" || { echo "link: no driver produced for $N" >&2; return 1; }
    LSHA=$(sha256sum "$LIB" 2>&1 | cut -d' ' -f1)
    DSHA=$(sha256sum "$OD/driver" 2>&1 | cut -d' ' -f1)
    sh "$SAFE" p05-s4r8 -- sh -c 'printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" "$5" "$6" "$7" >> "$8/DRIVERS_R8.tsv"' sh "$N" "$T" "$M" "$LSHA" "$DSHA" "$LIB" "$OD/driver" "$EV" || return 1
    echo "$N tree=$T mode=$M lib_sha256=$LSHA driver_sha256=$DSHA"
}

# plain drivers on the F3 plain library (-O1, as the R7 plain drivers)
link d003-F3-plain     F3 plain "$F3_PLAIN_LIB" "$SRC/driver_d003.cpp"     "$SRC/inject_d003.cpp"     "$LIBFLAGS" "-O1" || exit 1
link d003plan-F3-plain F3 plain "$F3_PLAIN_LIB" "$SRC/driver_d003.cpp"     "$ST4/inject_r4_plan.cpp"   "$LIBFLAGS" "-O1" || exit 1
link r6bstate-F3-plain F3 plain "$F3_PLAIN_LIB" "$ST4/driver_r6b_state.cpp" "$ST4/inject_r4_plan.cpp"  "$LIBFLAGS" "-O1" || exit 1
# tri (R7 safe_run.log line 122, F2 plain -> F3 plain): driver_s3r3_tri.cpp + inject_r6d_rnv1.cpp with the RNV1 wrap
link tri-F3-plain     F3 plain "$F3_PLAIN_LIB" "$ST3R3/driver_s3r3_tri.cpp" "$ST4/inject_r6d_rnv1.cpp" "$LIBFLAGS_RNV1" "-O1" || exit 1
# seam drivers (R7 link_seam_drivers_r7.sh: driver_d003.cpp + inject_d003.cpp, -O1, LIBFLAGS)
link seam-seamF-F3  F3 seamF-plain  "$SEAMF_LIB"  "$SRC/driver_d003.cpp" "$SRC/inject_d003.cpp" "$LIBFLAGS" "-O1" || exit 1
link seam-fmmret-F3 F3 fmmret-plain "$FMMRET_LIB" "$SRC/driver_d003.cpp" "$SRC/inject_d003.cpp" "$LIBFLAGS" "-O1" || exit 1
echo "link_drivers_r8: done"
exit 0
