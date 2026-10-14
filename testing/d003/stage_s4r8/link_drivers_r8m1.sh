#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# link_drivers_r8m1.sh -- P05-S4 R8 M1a, section 5.2: F3 drivers that M1b/M1c need and M0 does not have.  New file.
# Copies of the R7 link commands (committed, not modified):
#   link_drivers_s4r7.sh  link()          -> r6dnv1-F3-plain (plain, -O1), d003-F3-dbg, d003plan-F3-dbg, r6bstate-F3-dbg (-O0 -g)
#   safe_run.log lines 117-126 and 145-155 -> tri-F3-dbg (-O0 -g; the plain tri-F3-plain is in M0 already)
# Changes against the R7 commands: the library (F3 plain or F3 dbg of M0), the tree tag, and the output directory
# $EV/drivers_r8m1/; an existing driver is refused (U17).  The R7 link flags are kept.  Nothing is overwritten.
# Output: $EV/drivers_r8m1/<NAME>/driver ; $EV/DRIVERS_R8_M1a_LINKED.tsv (name, tree, mode, lib sha256, driver sha256, library path)
#
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/link_drivers_r8m1.sh p05-s4r8
set -u
OUT_ARG=${1:?"usage: link_drivers_r8m1.sh p05-s4r8"}
[ "$OUT_ARG" = p05-s4r8 ] || { echo "link_drivers_r8m1: first argument must be p05-s4r8" >&2; exit 2; }
SAFE="$REPO/testing/d003/safe_run.sh"
SRC="$REPO/testing/d003/src"
ST4="$REPO/testing/d003/stage_s4"
ST3R3="$REPO/testing/d003/stage_s3r3"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
LIBFLAGS_RNV1="$LIBFLAGS -Wl,--wrap=Pattern_GenerateFlowField"
OUTROOT="$EV/drivers_r8m1"
LINKED="$EV/DRIVERS_R8_M1a_LINKED.tsv"

# every input must exist before the output is created (brief 0.2)
for L in "$EV/build_r8/F3-plain/build/libS4.a" "$EV/build_r8/F3-dbg/build/libS4.a" "$EV/build_r8/F3-plain/S4" "$EV/build_r8/F3-dbg/S4" "$SRC/driver_d003.cpp" "$SRC/inject_d003.cpp" "$ST4/driver_r6b_state.cpp" "$ST4/inject_r4_plan.cpp" "$ST4/inject_r6d_rnv1.cpp" "$ST3R3/driver_s3r3_tri.cpp"; do
    test -e "$L" || { echo "link_drivers_r8m1: missing input $L" >&2; exit 2; }
done
test ! -e "$LINKED" || { echo "REFUSED: exists (U17): $LINKED" >&2; exit 2; }
sh "$SAFE" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && : > "$2"' sh "$OUTROOT" "$LINKED" || exit 2

# link NAME TREE MODE DRVSRC INJSRC LIBFLAGS_TO_USE OPT : the library is the M0 build of that tree and mode
link() {
    N=$1; T=$2; M=$3; DSRC=$4; ISRC=$5; LF=$6; OPT=$7
    LIB="$EV/build_r8/$T-$M/build/libS4.a"
    SRCTREE="$EV/build_r8/$T-$M"
    OUTDIR="$OUTROOT/$N"
    sh "$SAFE" "$OUT_ARG" -- sh -c 'test ! -e "$1/driver" && mkdir -p "$1" && g++ $2 -Wall -Wextra -Wno-unused-parameter -I "$3/S4" -I "$3/S4/fmm" "$4" "$5" -o "$1/driver" -L "$3/build" -lS4 $6 > "$1/build.stdout" 2>&1' \
        sh "$OUTDIR" "$OPT" "$SRCTREE" "$DSRC" "$ISRC" "$LF" || { echo "link FAILED $N (see $OUTDIR/build.stdout)" >&2; return 1; }
    test -x "$OUTDIR/driver" || { echo "driver not executable: $N" >&2; return 1; }
    LSHA=$(sha256sum "$LIB" 2>&1 | cut -d' ' -f1)
    DSHA=$(sha256sum "$OUTDIR/driver" 2>&1 | cut -d' ' -f1)
    sh "$SAFE" "$OUT_ARG" -- sh -c 'printf "%s\t%s\t%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" "$5" "$6" >> "$7"' sh "$N" "$T" "$M" "$LSHA" "$DSHA" "$LIB" "$LINKED" || return 1
    echo "$N tree=$T mode=$M lib_sha256=$LSHA driver_sha256=$DSHA"
    return 0
}

# R7 link_drivers_s4r7.sh: dbg uses -O0 -g; plain uses -O1 (the same two options as the R7 link())
link r6dnv1-F3-plain  F3 plain "$ST4/driver_r6b_state.cpp" "$ST4/inject_r6d_rnv1.cpp" "$LIBFLAGS_RNV1" "-O1"  || exit 1
link d003-F3-dbg      F3 dbg   "$SRC/driver_d003.cpp"       "$SRC/inject_d003.cpp"     "$LIBFLAGS"      "-O0 -g" || exit 1
link d003plan-F3-dbg  F3 dbg   "$SRC/driver_d003.cpp"       "$ST4/inject_r4_plan.cpp"  "$LIBFLAGS"      "-O0 -g" || exit 1
link r6bstate-F3-dbg  F3 dbg   "$ST4/driver_r6b_state.cpp"  "$ST4/inject_r4_plan.cpp"  "$LIBFLAGS"      "-O0 -g" || exit 1
# R7 safe_run.log lines 150-152 (tri dbg): -O0 -g with the RNV1 wrap set, driver_s3r3_tri.cpp + inject_r6d_rnv1.cpp
link tri-F3-dbg      F3 dbg   "$ST3R3/driver_s3r3_tri.cpp"  "$ST4/inject_r6d_rnv1.cpp" "$LIBFLAGS_RNV1" "-O0 -g" || exit 1
echo "link_drivers_r8m1: done"
exit 0
