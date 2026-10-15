REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_r8m2a2_r4.sh -- P05-S4 R8 M2a2 R4 (brief 4.4 rebuild): relink the two dual-target drivers against the R3 injector.
# BUILD_R8_M2a2_R3 linked dual-F3-dbg and layers-dual-F3-dbg with inject_r8m2a2_dual_R2.cpp; that is superseded by the
# R3 rule set (U244).  This script only LINKS new executables under $EV/build_R4/.  It does not overwrite any file
# (refuses if the output directory exists, U17), does not rebuild any library, and does NOT run any driver.
# Reused, not rebuilt: F3 dbg library (BUILD_R8.tsv row F3 dbg, sha 56f72c58...), R3 layers object.
set -u
OUTD=$EV/build_R4
if [ -e "$OUTD" ]; then
    echo "build_r8m2a2_r4: REFUSED exists (U17): $OUTD" >&2
    exit 2
fi
mkdir -p "$OUTD" || exit 2
ST=$REPO/testing/d003/stage_s4
LIB=$REPO/checkpoints/p05/evidence/p05-s4r8/build_r8/F3-dbg/build/libS4.a
INC=$EV/trees_R3/F3/S4
CXXFLAGS="-O0 -g -Wall -Wno-unused-parameter -I$INC -I$INC/fmm"
WRAPS="-Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"
rc_all=0
echo "build_r8m2a2_r4: start $(date -u +%FT%TZ) out=$OUTD"
# 1) injector object (R3 production build, no harness macro)
g++ $CXXFLAGS -c "$ST/inject_r8m2a2_dual_R3.cpp" -o "$OUTD/inject_r8m2a2_dual_R3.o"
rc=$?; echo "compile inject_r8m2a2_dual_R3.o rc=$rc"; [ $rc -eq 0 ] || rc_all=1
# 2) dual-F3-dbg (M2-04 (a): call1 fails, retry call2 fails, call3 recovers; same layer driver = driver_r6b_state)
if [ $rc_all -eq 0 ]; then
    g++ $CXXFLAGS "$ST/driver_r6b_state.cpp" "$OUTD/inject_r8m2a2_dual_R3.o" "$LIB" -llapack -lblas $WRAPS -o "$OUTD/dual-F3-dbg-R4"
    rc=$?; echo "link dual-F3-dbg-R4 rc=$rc"; [ $rc -eq 0 ] || rc_all=1
fi
# 3) layers-dual-F3-dbg (M2-05 / M2-04 (b): multi-layer driver with the R3 dual injector)
if [ $rc_all -eq 0 ]; then
    g++ $CXXFLAGS "$ST/driver_r8m2a2_layers_R2.cpp" "$OUTD/inject_r8m2a2_dual_R3.o" "$LIB" -llapack -lblas $WRAPS -o "$OUTD/layers-dual-F3-dbg-R4"
    rc=$?; echo "link layers-dual-F3-dbg-R4 rc=$rc"; [ $rc -eq 0 ] || rc_all=1
fi
echo "build_r8m2a2_r4: end rc_all=$rc_all $(date -u +%FT%TZ)"
exit $rc_all
