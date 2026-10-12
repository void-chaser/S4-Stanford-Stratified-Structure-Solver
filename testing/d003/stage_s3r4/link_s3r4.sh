#!/bin/sh
# link_s3r4.sh -- P05-S3R4 link step (new file).  Links one driver against the plain library of tree F2 or F3.
#
#   sh testing/d003/safe_run.sh p05-s3r4 -- sh testing/d003/stage_s3r4/link_s3r4.sh p05-s3r4 F2 state
#   sh testing/d003/safe_run.sh p05-s3r4 -- sh testing/d003/stage_s3r4/link_s3r4.sh p05-s3r4 F3 tri
#
# Arguments: $1 = evidence directory (p05-s3r4); $2 = tree (F2 or F3); $3 = driver kind:
#   state -> testing/d003/stage_s4/driver_r6b_state.cpp + testing/d003/stage_s4/inject_r4_plan.cpp   (no injection used)
#   tri   -> testing/d003/stage_s3r3/driver_s3r3_tri.cpp + testing/d003/stage_s4/inject_r4_plan.cpp  (no injection used)
# Library: F2 -> $EV/build/F2-plain/build/libS4.a ; F3 -> $EV/build_f3/plain/build/libS4.a (from git archive, build_f3_s3r4.sh).
# Output: $EV/drivers/<kind>-<tree>/driver ; the link flags are those of link_drivers_s4r7.sh (plain: -O1).
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "link_s3r4: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: link_s3r4.sh p05-s3r4 F2|F3 state|tri"}
TREE=${2:?"tree F2 or F3"}
KIND=${3:?"kind state or tri"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
case "$TREE" in
    F2) LIBDIR="$EV/build/F2-plain/build"; SRCTREE="$EV/build/F2-plain" ;;
    F3) LIBDIR="$EV/build_f3/plain/build"; SRCTREE="$EV/build_f3/plain" ;;
    *) echo "link_s3r4: unknown tree $TREE" >&2; exit 2 ;;
esac
OUTDIR="$EV/drivers/${KIND}-${TREE}"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
case "$KIND" in
    state) DRV="$REPO/testing/d003/stage_s4/driver_r6b_state.cpp" ;;
    tri)   DRV="$REPO/testing/d003/stage_s3r3/driver_s3r3_tri.cpp" ;;
    *) echo "link_s3r4: unknown kind $KIND" >&2; exit 2 ;;
esac
INJ="$REPO/testing/d003/stage_s4/inject_r4_plan.cpp"

test -f "$LIBDIR/libS4.a" || { echo "link_s3r4: library missing: $LIBDIR/libS4.a" >&2; exit 2; }
echo "library $TREE sha256 $(sha256sum "$LIBDIR/libS4.a" | cut -d' ' -f1)"

sh "$REPO/testing/d003/safe_run.sh" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$2/S4" -I "$2/S4/fmm" "$3" "$4" -o "$1/driver" -L "$5" -lS4 $6 > "$1/build.stdout" 2>&1' \
    sh "$OUTDIR" "$SRCTREE" "$DRV" "$INJ" "$LIBDIR" "$LIBFLAGS"
rc=$?
echo "link rc=$rc"
[ "$rc" -eq 0 ] || exit "$rc"
test -x "$OUTDIR/driver" || { echo "driver not executable" >&2; exit 2; }
sha256sum "$OUTDIR/driver"
exit 0
