#!/bin/sh
# r6d_link_rnv1_B.sh -- P05-S4 R6d-2 (new file): the RNV1 driver against the -O0 -g build of the UNREPAIRED baseline B.
# Copy of r6d_link_rnv1.sh with the tree changed from F to B only.
#
#   sh testing/d003/safe_run.sh p05-s4r6d -- sh testing/d003/stage_s4/r6d_link_rnv1_B.sh p05-s4r6d
#
# Library: checkpoints/p05/evidence/p05-s4r5/dbg/trees/B/build/libS4.a
#   sha256 980c5f8feb2b2de4c029888afda5c3002a86b1cd191013c6ef07742cc2b2886f (libS4-dbg-B.sha256 of R5)
#   pattern.c of that tree equals 37a82e8:S4/pattern/pattern.c (checked in R6d).
# Output: $EV/drivers/r6d-rnv1-B/driver-r6d-rnv1-B, build.stdout, DRIVER_R6d_RNV1_B.sha256
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "r6d_link_rnv1_B: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: r6d_link_rnv1_B.sh p05-s4r6d"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
LIBDIR="$REPO/checkpoints/p05/evidence/p05-s4r5/dbg/trees/B/build"
OUTDIR="$EV/drivers/r6d-rnv1-B"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_GenerateFlowField"
SRCTREE="$REPO/checkpoints/p05/evidence/p05-s4r5/dbg/trees/B"

want=$(cut -d' ' -f1 "$REPO/checkpoints/p05/evidence/p05-s4r5/dbg/libS4-dbg-B.sha256") || { echo "no record" >&2; exit 2; }
got=$(sha256sum "$LIBDIR/libS4.a" | cut -d' ' -f1) || exit 2
if [ "$want" != "$got" ]; then echo "r6d_link_rnv1_B: library sha256 mismatch want=$want got=$got" >&2; exit 2; fi
echo "library sha256 ok $got"

mkdir -p "$OUTDIR" || exit 2
g++ -O0 -g -Wall -Wextra -Wno-unused-parameter \
    -I "$SRCTREE/S4" -I "$SRCTREE/S4/fmm" \
    "$REPO/testing/d003/stage_s4/driver_r6b_state.cpp" "$REPO/testing/d003/stage_s4/inject_r6d_rnv1.cpp" \
    -o "$OUTDIR/driver-r6d-rnv1-B" -L "$LIBDIR" -lS4 $LIBFLAGS > "$OUTDIR/build.stdout" 2>&1
rc=$?
echo "link rc=$rc"
[ "$rc" -eq 0 ] || exit "$rc"
test -x "$OUTDIR/driver-r6d-rnv1-B" || { echo "driver not executable" >&2; exit 2; }
sha256sum "$OUTDIR/driver-r6d-rnv1-B" > "$OUTDIR/DRIVER_R6d_RNV1_B.sha256"
cat "$OUTDIR/DRIVER_R6d_RNV1_B.sha256"
exit 0
