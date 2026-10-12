#!/bin/sh
# r6c2_link_fmmret.sh -- P05-S4 R6c2-2 step 1 (new file): link driver-r6b-fmmret-F against the -O0 -g fmmret-F library.
# Same construction as the driver-r6b-seamF step recorded in ERRATA_6c E6c-3 (driver_r6b_state.cpp + inject_r4_plan.cpp,
# same LIBFLAGS).  Only the library directory and the output name differ.  The library is NOT rebuilt here; its sha256 is
# recorded from the existing -O0 -g build (seam_dbg/libS4-dbg-fmmret-F.sha256 is checked to match first).
#
#   sh testing/d003/safe_run.sh p05-s4r6c -- sh testing/d003/stage_s4/r6c2_link_fmmret.sh p05-s4r6c
#
# Outputs: $EV/seam_dbg/drivers/r6b-fmmret-F/driver-r6b-fmmret-F, build.stdout, DRIVER_R6b_FMMRET_F.sha256
set -u
REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "r6c2_link_fmmret: not in a git work tree" >&2; exit 2; }
OUT_ARG=${1:?"usage: r6c2_link_fmmret.sh p05-s4r6c"}
EV="$REPO/checkpoints/p05/evidence/$OUT_ARG"
DBG="$EV/seam_dbg"
LIB="$DBG/fmmret-F/src/build"
OUTDIR="$DBG/drivers/r6b-fmmret-F"
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"

# 1) the library must be the recorded -O0 -g build
want=$(cut -d' ' -f1 "$DBG/libS4-dbg-fmmret-F.sha256") || { echo "r6c2_link_fmmret: no recorded library sha256" >&2; exit 2; }
got=$(sha256sum "$LIB/libS4.a" | cut -d' ' -f1) || exit 2
if [ "$want" != "$got" ]; then
    echo "r6c2_link_fmmret: library sha256 mismatch want=$want got=$got" >&2
    exit 2
fi
echo "library sha256 ok $got"

# 2) link (writes only inside $OUTDIR, which is under $EV)
mkdir -p "$OUTDIR" || exit 2
g++ -O0 -g -Wall -Wextra -Wno-unused-parameter \
    -I "$DBG/fmmret-F/src/S4" -I "$DBG/fmmret-F/src/S4/fmm" \
    "$REPO/testing/d003/stage_s4/driver_r6b_state.cpp" "$REPO/testing/d003/stage_s4/inject_r4_plan.cpp" \
    -o "$OUTDIR/driver-r6b-fmmret-F" -L "$DBG/fmmret-F/src/build" -lS4 $LIBFLAGS > "$OUTDIR/build.stdout" 2>&1
rc=$?
echo "link rc=$rc"
[ "$rc" -eq 0 ] || exit "$rc"
test -x "$OUTDIR/driver-r6b-fmmret-F" || { echo "r6c2_link_fmmret: driver not executable" >&2; exit 2; }
sha256sum "$OUTDIR/driver-r6b-fmmret-F" > "$OUTDIR/DRIVER_R6b_FMMRET_F.sha256"
cat "$OUTDIR/DRIVER_R6b_FMMRET_F.sha256"
exit 0
