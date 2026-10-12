#!/bin/sh
# link_drivers_s4r7.sh -- P05-S4 R7-1 step 4: drivers for the R7 regression, linked against the R7 libraries (new file).
#
#   sh testing/d003/safe_run.sh p05-s4r7 -- sh testing/d003/stage_s4r7/link_drivers_s4r7.sh p05-s4r7
#
# Driver/injector pairs follow the history of each matrix (ERRATA_4/5/6/6c; no historical file is changed):
#   d003      : driver_d003.cpp + inject_d003.cpp       (R3 matrix, G1)
#   d003plan  : driver_d003.cpp + inject_r4_plan.cpp     (R4 plancall, R5 plan/M=2, R6-1 twice; G2, G3, G4)
#   r6bstate  : driver_r6b_state.cpp + inject_r4_plan.cpp (R6c state 177 points; G5)
#   r6dnv1    : driver_r6b_state.cpp + inject_r6d_rnv1.cpp (RNV1 window and tri; G7, G8, 4.2)
# Libraries: $EV/build_r7/{F,F2}-{dbg,plain}/build/libS4.a (built by build_s4r7.sh).
# Link flags: plain libraries with -O1, dbg libraries with -O0 -g (as the historical drivers).
# Output: $EV/drivers_r7/<DRV>-<TREE>-<MODE>/driver ; $EV/DRIVERS_R7.tsv (driver, tree, mode, lib sha256, driver sha256, script).
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "link_drivers_s4r7: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: link_drivers_s4r7.sh p05-s4r7"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
TMPDIR="$EV/tmp"
export TMPDIR
SAFE="$REPO/testing/d003/safe_run.sh"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
LIBFLAGS_RNV1="$LIBFLAGS -Wl,--wrap=Pattern_GenerateFlowField"
SRC="$REPO/testing/d003/src"
ST4="$REPO/testing/d003/stage_s4"
ST3R3="$REPO/testing/d003/stage_s3r3"

sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1/drivers_r7" && : > "$1/DRIVERS_R7.tsv"' sh "$EV" || exit 2

# link DRV TREE MODE : DRV selects the sources and the wraps; TREE is F or F2; MODE is dbg or plain
link() {
    D=$1; T=$2; M=$3
    LIB="$EV/build_r7/$T-$M/build/libS4.a"
    SRCTREE="$EV/build_r7/$T-$M"
    OUTDIR="$EV/drivers_r7/$D-$T-$M"
    test -f "$LIB" || { echo "missing library $LIB" >&2; return 1; }
    case "$D" in
        d003)     DSRC="$SRC/driver_d003.cpp";            ISRC="$SRC/inject_d003.cpp";        LF="$LIBFLAGS" ;;
        d003plan) DSRC="$SRC/driver_d003.cpp";            ISRC="$ST4/inject_r4_plan.cpp";     LF="$LIBFLAGS" ;;
        r6bstate) DSRC="$ST4/driver_r6b_state.cpp";       ISRC="$ST4/inject_r4_plan.cpp";     LF="$LIBFLAGS" ;;
        r6dnv1)   DSRC="$ST4/driver_r6b_state.cpp";       ISRC="$ST4/inject_r6d_rnv1.cpp";    LF="$LIBFLAGS_RNV1" ;;
        *) echo "unknown driver $D" >&2; return 1 ;;
    esac
    if [ "$M" = dbg ]; then OPT="-O0 -g"; else OPT="-O1"; fi
    sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && g++ $2 -Wall -Wextra -Wno-unused-parameter -I "$3/S4" -I "$3/S4/fmm" "$4" "$5" -o "$1/driver" -L "$3/build" -lS4 $6 > "$1/build.stdout" 2>&1' \
        sh "$OUTDIR" "$OPT" "$SRCTREE" "$DSRC" "$ISRC" "$LF" || { echo "link FAILED $D $T $M (see $OUTDIR/build.stdout)" >&2; return 1; }
    test -x "$OUTDIR/driver" || return 1
    LSHA=$(sha256sum "$LIB" | cut -d' ' -f1)
    DSHA=$(sha256sum "$OUTDIR/driver" | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" "$5" "$6" >> "$7/DRIVERS_R7.tsv"' sh "$D" "$T" "$M" "$LSHA" "$DSHA" "$OUTDIR/driver" "$EV" || return 1
    echo "$D $T $M driver_sha256=$DSHA lib_sha256=$LSHA"
}

for T in F F2; do
    for M in dbg plain; do
        link d003     "$T" "$M" || exit 1
        link d003plan "$T" "$M" || exit 1
        link r6bstate "$T" "$M" || exit 1
        link r6dnv1   "$T" "$M" || exit 1
    done
done
echo "link_drivers_s4r7: done"
exit 0
