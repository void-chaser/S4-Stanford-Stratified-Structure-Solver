#!/bin/sh
# r6d_link_rnv1.sh -- P05-S4 R6d-2 (new file): link the RNV1 driver against the -O0 -g build of the frozen tree F.
#
#   sh testing/d003/safe_run.sh p05-s4r6d -- sh testing/d003/stage_s4/r6d_link_rnv1.sh p05-s4r6d
#
# Inputs (read only):
#   driver source     testing/d003/stage_s4/driver_r6b_state.cpp      (R6b/R6c state driver, unchanged)
#   injector          testing/d003/stage_s4/inject_r6d_rnv1.cpp       (R6d, new; does NOT link inject_r4_plan.cpp)
#   library           checkpoints/p05/evidence/p05-s4r5/dbg/trees/F/build/libS4.a
#                     (-O0 -g build of tree F; sha256 b95712a4...2876 recorded in libS4-dbg-F.sha256 of R5;
#                      the source files pattern.c and fmm_PolBasisNV.cpp of that tree equal HEAD:S4 (checked in R6d))
# Outputs (in $EV, which is the only write target):
#   $EV/drivers/r6d-rnv1/driver-r6d-rnv1, build.stdout, DRIVER_R6d_RNV1.sha256
#
# The link uses the same LIBFLAGS as the R6b driver (-Wl,--wrap=malloc and the FFT/S4_malloc wraps) PLUS
# -Wl,--wrap=Pattern_GenerateFlowField (the RNV1 window; NOT pattern_generate_flow_field, see inject_r6d_rnv1.cpp).
# The wrapped malloc here is the one of inject_r6d_rnv1.cpp.
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "r6d_link_rnv1: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: r6d_link_rnv1.sh p05-s4r6d"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
LIBDIR="$REPO/checkpoints/p05/evidence/p05-s4r5/dbg/trees/F/build"
OUTDIR="$EV/drivers/r6d-rnv1"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_GenerateFlowField"
SRCTREE="$REPO/checkpoints/p05/evidence/p05-s4r5/dbg/trees/F"

# 1) the library must be the recorded -O0 -g build of tree F
want=$(cut -d' ' -f1 "$REPO/checkpoints/p05/evidence/p05-s4r5/dbg/libS4-dbg-F.sha256") || { echo "no record" >&2; exit 2; }
got=$(sha256sum "$LIBDIR/libS4.a" | cut -d' ' -f1) || exit 2
if [ "$want" != "$got" ]; then echo "r6d_link_rnv1: library sha256 mismatch want=$want got=$got" >&2; exit 2; fi
echo "library sha256 ok $got"

# 2) link (writes only inside $OUTDIR, under $EV)
mkdir -p "$OUTDIR" || exit 2
g++ -O0 -g -Wall -Wextra -Wno-unused-parameter \
    -I "$SRCTREE/S4" -I "$SRCTREE/S4/fmm" \
    "$REPO/testing/d003/stage_s4/driver_r6b_state.cpp" "$REPO/testing/d003/stage_s4/inject_r6d_rnv1.cpp" \
    -o "$OUTDIR/driver-r6d-rnv1" -L "$LIBDIR" -lS4 $LIBFLAGS > "$OUTDIR/build.stdout" 2>&1
rc=$?
echo "link rc=$rc"
[ "$rc" -eq 0 ] || exit "$rc"
test -x "$OUTDIR/driver-r6d-rnv1" || { echo "driver not executable" >&2; exit 2; }
sha256sum "$OUTDIR/driver-r6d-rnv1" > "$OUTDIR/DRIVER_R6d_RNV1.sha256"
cat "$OUTDIR/DRIVER_R6d_RNV1.sha256"
exit 0
