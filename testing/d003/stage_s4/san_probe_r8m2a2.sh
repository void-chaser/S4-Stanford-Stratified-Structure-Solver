REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# san_probe_r8m2a2.sh -- P05-S4 R8 M2a2 section 4.5: sanitizer toolchain probe.  NOT an S4 driver (does not link S4).
# Compiles testing/d003/stage_s4/san_probe_r8m2a2.cpp with -fsanitize=address,undefined into $EV/build/san/,
# runs it clean and with an overflow argument, and checks that ASan reports the deliberate heap overflow.
# Output: $EV/SAN_PROBE_R8_M2a2.txt.  Refuses to overwrite (U17).
set -u
refuse() { echo "san_probe_r8m2a2: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8/m2a2 ] || refuse "first argument must be p05-s4r8/m2a2"
OUTF="$EV/SAN_PROBE_R8_M2a2.txt"
test ! -e "$OUTF" || refuse "exists (U17): $OUTF"
mkdir -p "$EV/build/san" || refuse "cannot create build/san"
SRC="$REPO/testing/d003/stage_s4/san_probe_r8m2a2.cpp"
EXE="$EV/build/san/san_probe_r8m2a2"
LOG="$EV/build/san/san_probe_r8m2a2.compile.log"
CC_RC=0
g++ -std=c++11 -g -O0 -fsanitize=address,undefined -fno-omit-frame-pointer -o "$EXE" "$SRC" > "$LOG" 2>&1 || CC_RC=$?
RUN_CLEAN_RC=99
RUN_OVF_RC=99
ASAN_OVF=NO
if [ "$CC_RC" -eq 0 ]; then
    "$EXE" > "$EV/build/san/run_clean.log" 2>&1
    RUN_CLEAN_RC=$?
    "$EXE" overflow > "$EV/build/san/run_ovf.log" 2>&1
    RUN_OVF_RC=$?
    if grep -q "AddressSanitizer" "$EV/build/san/run_ovf.log"; then ASAN_OVF=YES; fi
fi
{
    echo "# SAN_PROBE_R8_M2a2 -- sanitizer toolchain probe (P05-S4 R8 M2a2 section 4.5; no S4 linked)"
    echo "compile_rc=$CC_RC"
    echo "run_clean_rc=$RUN_CLEAN_RC"
    echo "run_overflow_rc=$RUN_OVF_RC"
    echo "asan_reports_overflow=$ASAN_OVF"
    echo "probe_src=testing/d003/stage_s4/san_probe_r8m2a2.cpp"
    echo "probe_exe=checkpoints/p05/evidence/p05-s4r8/m2a2/build/san/san_probe_r8m2a2"
    if [ "$CC_RC" -eq 0 ] && [ "$ASAN_OVF" = YES ]; then echo "SAN_TOOLCHAIN=USABLE"; else echo "SAN_TOOLCHAIN=BUILD_FAILED_OR_NOT_REPORTED"; fi
} > "$OUTF"
echo "san_probe_r8m2a2: wrote $OUTF"
exit 0
