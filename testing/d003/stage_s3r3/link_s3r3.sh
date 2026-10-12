#!/bin/sh
# link_s3r3.sh -- P05-S3R3 self-check link (new file).  Links one driver against the -O0 -g library of tree F or F2.
#
#   sh testing/d003/safe_run.sh p05-s3r3 -- sh testing/d003/stage_s3r3/link_s3r3.sh p05-s3r3 F2 rnv1
#   sh testing/d003/safe_run.sh p05-s3r3 -- sh testing/d003/stage_s3r3/link_s3r3.sh p05-s3r3 F  tri
#
# Arguments: $1 = evidence directory (p05-s3r3), $2 = tree (F or F2), $3 = driver kind:
#   rnv1  -> testing/d003/stage_s4/driver_r6b_state.cpp + testing/d003/stage_s4/inject_r6d_rnv1.cpp   (R6d injector, unchanged)
#   tri   -> testing/d003/stage_s3r3/driver_s3r3_tri.cpp + testing/d003/stage_s4/inject_r6d_rnv1.cpp
# The library is $EV/build/trees/<tree>-dbg/build/libS4.a (built by build_s3r3.sh; sha256 recorded there).
# Output: $EV/drivers/s3r3-<kind>-<tree>/driver (only write target besides $EV/tmp).
# The link line is the R6d RNV1 link line (r6d_link_rnv1.sh) with the library and output changed.
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "link_s3r3: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: link_s3r3.sh p05-s3r3 F|F2 rnv1|tri"}
TREE=${2:?"tree F or F2"}
KIND=${3:?"kind rnv1 or tri"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
LIBDIR="$EV/build/trees/${TREE}-dbg/build"
SRCTREE="$EV/build/trees/${TREE}-dbg"
OUTDIR="$EV/drivers/s3r3-${KIND}-${TREE}"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_GenerateFlowField"

case "$KIND" in
    rnv1) DRV="$REPO/testing/d003/stage_s4/driver_r6b_state.cpp" ;;
    tri)  DRV="$REPO/testing/d003/stage_s3r3/driver_s3r3_tri.cpp" ;;
    *) echo "link_s3r3: unknown kind $KIND" >&2; exit 2 ;;
esac
INJ="$REPO/testing/d003/stage_s4/inject_r6d_rnv1.cpp"

test -f "$LIBDIR/libS4.a" || { echo "link_s3r3: library missing: $LIBDIR/libS4.a" >&2; exit 2; }
echo "library $TREE sha256 $(sha256sum "$LIBDIR/libS4.a" | cut -d' ' -f1)"

mkdir -p "$OUTDIR" || exit 2
g++ -O0 -g -Wall -Wextra -Wno-unused-parameter \
    -I "$SRCTREE/S4" -I "$SRCTREE/S4/fmm" \
    "$DRV" "$INJ" \
    -o "$OUTDIR/driver" -L "$LIBDIR" -lS4 $LIBFLAGS > "$OUTDIR/build.stdout" 2>&1
rc=$?
echo "link rc=$rc"
[ "$rc" -eq 0 ] || exit "$rc"
test -x "$OUTDIR/driver" || { echo "driver not executable" >&2; exit 2; }
sha256sum "$OUTDIR/driver" > "$OUTDIR/DRIVER.sha256"
cat "$OUTDIR/DRIVER.sha256"
exit 0
