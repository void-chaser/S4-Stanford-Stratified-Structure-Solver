#!/bin/sh
# link_c2.sh -- P05-S3R4 CONT2: link one driver against the plain library of tree F2 or F3 (copy of
# testing/d003/stage_s3r4/link_s3r4.sh with the driver source given as argument; only the output directory
# and the library paths of the copy are the new ones).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/link_c2.sh p05-s3r4c2 F2 poly
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/link_c2.sh p05-s3r4c2 F3 poly
#   (kind state: state driver; kind tri: tri driver; kind poly: polygon driver of this round)
#
# Libraries are read from the S3R4 evidence (read only): F2 -> evidence/p05-s3r4/build/F2-plain/build/libS4.a ;
# F3 -> evidence/p05-s3r4/build_f3/plain/build/libS4.a.  Output: $EV/drivers/<kind>-<TREE>/driver.
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "link_c2: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: link_c2.sh p05-s3r4c2 F2|F3 state|tri|poly"}
TREE=${2:?"tree F2 or F3"}
KIND=${3:?"kind state, tri or poly"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
SRCEV="$REPO/checkpoints/p05/evidence/p05-s3r4"
case "$TREE" in
    F2) LIBDIR="$SRCEV/build/F2-plain/build"; SRCTREE="$SRCEV/build/F2-plain" ;;
    F3) LIBDIR="$SRCEV/build_f3/plain/build"; SRCTREE="$SRCEV/build_f3/plain" ;;
    *) echo "link_c2: unknown tree $TREE" >&2; exit 2 ;;
esac
OUTDIR="$EV/drivers/${KIND}-${TREE}"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
case "$KIND" in
    state) DRV="$REPO/testing/d003/stage_s4/driver_r6b_state.cpp" ;;
    tri)   DRV="$REPO/testing/d003/stage_s3r3/driver_s3r3_tri.cpp" ;;
    poly)  DRV="$REPO/testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp" ;;
    *) echo "link_c2: unknown kind $KIND" >&2; exit 2 ;;
esac
INJ="$REPO/testing/d003/stage_s4/inject_r4_plan.cpp"

test -f "$LIBDIR/libS4.a" || { echo "link_c2: library missing: $LIBDIR/libS4.a" >&2; exit 2; }
echo "library $TREE sha256 $(sha256sum "$LIBDIR/libS4.a" | cut -d' ' -f1)"

sh "$REPO/testing/d003/safe_run.sh" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$2/S4" -I "$2/S4/fmm" "$3" "$4" -o "$1/driver" -L "$5" -lS4 $6 > "$1/build.stdout" 2>&1' \
    sh "$OUTDIR" "$SRCTREE" "$DRV" "$INJ" "$LIBDIR" "$LIBFLAGS"
rc=$?
echo "link rc=$rc"
[ "$rc" -eq 0 ] || exit "$rc"
test -x "$OUTDIR/driver" || { echo "driver not executable" >&2; exit 2; }
sha256sum "$OUTDIR/driver"
exit 0
