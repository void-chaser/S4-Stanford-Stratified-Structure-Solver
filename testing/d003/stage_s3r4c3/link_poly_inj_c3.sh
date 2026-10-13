REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# link_poly_inj_c3.sh -- P05-S3R4 CONT3 self-check (B): link the polygon driver with inject_s3r4c3_poly.cpp (new file).
# Template: testing/d003/stage_s3r4/link_init_s3r4.sh (the REPO line is replaced by the standard first line, brief 0.2).
# Only changes against the template: wrap Pattern_GetContainmentTree -> Pattern_DiscretizeCell; driver and injector;
# output directory drivers/polyinj-<TREE>.
#
#   sh testing/d003/safe_run.sh p05-s3r4c3 -- sh testing/d003/stage_s3r4c3/link_poly_inj_c3.sh p05-s3r4c3 F2
#   sh testing/d003/safe_run.sh p05-s3r4c3 -- sh testing/d003/stage_s3r4c3/link_poly_inj_c3.sh p05-s3r4c3 F3
#
# Driver: testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp (read only, not copied).
# Injector: testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp.
# Libraries: F2 -> p05-s3r4/build/F2-plain/build/libS4.a ; F3 -> p05-s3r4/build_f3/plain/build/libS4.a (read only).
set -u
OUT_ARG=${1:?"usage: link_poly_inj_c3.sh p05-s3r4c3 F2|F3"}
TREE=${2:?"tree F2 or F3"}
SRCEV="$REPO/checkpoints/p05/evidence/p05-s3r4"
case "$TREE" in
    F2) LIBDIR="$SRCEV/build/F2-plain/build"; SRCTREE="$SRCEV/build/F2-plain" ;;
    F3) LIBDIR="$SRCEV/build_f3/plain/build"; SRCTREE="$SRCEV/build_f3/plain" ;;
    *) echo "link_poly_inj_c3: unknown tree $TREE" >&2; exit 2 ;;
esac
OUTDIR="$EV/drivers/polyinj-${TREE}"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=Pattern_DiscretizeCell"
DRV="$REPO/testing/d003/stage_s3r4c2/driver_s3r4c2_poly.cpp"
INJ="$REPO/testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp"

test -f "$LIBDIR/libS4.a" || { echo "link_poly_inj_c3: library missing: $LIBDIR/libS4.a" >&2; exit 2; }
echo "library $TREE sha256 $(sha256sum "$LIBDIR/libS4.a" | cut -d' ' -f1)"

sh "$REPO/testing/d003/safe_run.sh" "$OUT_ARG" -- sh -c 'mkdir -p "$1" && g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$2/S4" -I "$2/S4/fmm" "$3" "$4" -o "$1/driver" -L "$5" -lS4 $6 > "$1/build.stdout" 2>&1' \
    sh "$OUTDIR" "$SRCTREE" "$DRV" "$INJ" "$LIBDIR" "$LIBFLAGS"
rc=$?
echo "link rc=$rc"
[ "$rc" -eq 0 ] || exit "$rc"
test -x "$OUTDIR/driver" || { echo "driver not executable" >&2; exit 2; }
sha256sum "$OUTDIR/driver"
exit 0
