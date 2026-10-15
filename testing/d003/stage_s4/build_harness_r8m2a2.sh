REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_harness_r8m2a2.sh -- P05-S4 R8 M2a2 R3: synthetic harness for the dual injector (NOT an S4 driver).
# Compiles the R3 injector object and the harness with the stub file only.  libS4 is NOT linked.
# Outputs under $EV/build/harness/ only.  Run through safe_run:
#   sh testing/d003/safe_run.sh p05-s4r8/m2a2 -- sh testing/d003/stage_s4/build_harness_r8m2a2.sh
# The injector includes "fmm/fft_iface.h": the header is read from the exported F3 tree (read only).
set -u
# usage: ... -- sh testing/d003/stage_s4/build_harness_r8m2a2.sh [OUT_SUBDIR]   (default harness_try2; must not exist: U17)
SUB=${1:-harness_try2}
case "$SUB" in
    harness_try*) ;;
    *) echo "build_harness_r8m2a2: REFUSED OUT_SUBDIR must start with harness_try: $SUB" >&2; exit 2;;
esac
H=$EV/build/$SUB
if [ -e "$H" ]; then
    echo "build_harness_r8m2a2: REFUSED exists (U17): $H" >&2
    exit 2
fi
mkdir -p "$H" || exit 2
ST=$REPO/testing/d003/stage_s4
INC=$EV/trees_R3/F3/S4
rc_all=0
CXXFLAGS="-O0 -g -Wall -Wno-unused-parameter -std=c++11 -I$INC -I$INC/fmm"

echo "build_harness_r8m2a2: start $(date -u +%FT%TZ) out=$H"
g++ $CXXFLAGS -c "$ST/inject_r8m2a2_dual_R3.cpp" -o "$H/inject_r8m2a2_dual_R3.o"
rc=$?; echo "compile inject_r8m2a2_dual_R3.o rc=$rc"; [ $rc -eq 0 ] || rc_all=1
g++ $CXXFLAGS -c "$ST/dual_stubs_r8m2a2.cpp" -o "$H/dual_stubs_r8m2a2.o"
rc=$?; echo "compile dual_stubs_r8m2a2.o rc=$rc"; [ $rc -eq 0 ] || rc_all=1
g++ $CXXFLAGS -c "$ST/dual_harness_r8m2a2.cpp" -o "$H/dual_harness_r8m2a2.o"
rc=$?; echo "compile dual_harness_r8m2a2.o rc=$rc"; [ $rc -eq 0 ] || rc_all=1
if [ $rc_all -eq 0 ]; then
    g++ "$H/dual_harness_r8m2a2.o" "$H/inject_r8m2a2_dual_R3.o" "$H/dual_stubs_r8m2a2.o" -Wl,--wrap=malloc -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -o "$H/dual_harness_r8m2a2"
    rc=$?; echo "link dual_harness_r8m2a2 rc=$rc"; [ $rc -eq 0 ] || rc_all=1
fi
# Second build: the harness-only variant (-DS4FMM_DUAL_HARNESS) used by the SUPPRESSED case (rule 4).  It is a
# separate object and executable (suffix _suppress); the production object above is not rebuilt with the macro.
if [ $rc_all -eq 0 ]; then
    g++ $CXXFLAGS -DS4FMM_DUAL_HARNESS -c "$ST/inject_r8m2a2_dual_R3.cpp" -o "$H/inject_r8m2a2_dual_R3_harness.o"
    rc=$?; echo "compile inject_r8m2a2_dual_R3_harness.o (-DS4FMM_DUAL_HARNESS) rc=$rc"; [ $rc -eq 0 ] || rc_all=1
fi
if [ $rc_all -eq 0 ]; then
    g++ $CXXFLAGS -DS4FMM_DUAL_HARNESS -c "$ST/dual_harness_r8m2a2.cpp" -o "$H/dual_harness_r8m2a2_suppress.o"
    rc=$?; echo "compile dual_harness_r8m2a2_suppress.o rc=$rc"; [ $rc -eq 0 ] || rc_all=1
fi
if [ $rc_all -eq 0 ]; then
    g++ "$H/dual_harness_r8m2a2_suppress.o" "$H/inject_r8m2a2_dual_R3_harness.o" "$H/dual_stubs_r8m2a2.o" -Wl,--wrap=malloc -Wl,--wrap=_Z9S4_mallocm -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -o "$H/dual_harness_r8m2a2_suppress"
    rc=$?; echo "link dual_harness_r8m2a2_suppress rc=$rc"; [ $rc -eq 0 ] || rc_all=1
fi
echo "build_harness_r8m2a2: end rc_all=$rc_all $(date -u +%FT%TZ)"
exit $rc_all
