#!/bin/bash
# Fixed 20-case acceptance matrix (TASK.md), with real assertions.
#   matrix.sh <workspace>
# Runs entirely inside the run workspace; the delivered work/ is never touched
# and normal-case evidence is never overwritten by a mutation.
cd "$(dirname "$0")/.." || exit 1
ulimit -c 0
. tests/lib.sh

WS="$1"
[ -n "$WS" ] || { echo "usage: matrix.sh <workspace>" >&2; exit 2; }
OUT="$WS/evidence/matrix"
CW="$WS/work"
FAKE="$WS/work/fake.sh"
rm -rf "$OUT"; mkdir -p "$OUT"

head1 "fixed 20-case matrix"
say "runner hash: $(sha256sum "$CW/run-one.sh" | cut -c1-16)"

run_case "$CW" "$FAKE" 01 exit77            fault    fft 1 "$OUT/01-fault-exit77"
run_case "$CW" "$FAKE" 02 nohit             fault    fft 1 "$OUT/02-fault-nohit"
run_case "$CW" "$FAKE" 03 rc1zero           fault    fft 1 "$OUT/03-fault-rc1zero"
run_case "$CW" "$FAKE" 04 nomarker          fault    fft 1 "$OUT/04-fault-nomarker"
run_case "$CW" "$FAKE" 05 san               fault    fft 1 "$OUT/05-fault-san"
run_case "$CW" "$FAKE" 06 hang              fault    fft 1 "$OUT/06-fault-hang"
run_case "$CW" "$FAKE" 07 signal            fault    fft 1 "$OUT/07-fault-signal"
run_case "$CW" "$FAKE" 08 no-final-pass     fault    fft 1 "$OUT/08-fault-no-final-pass"
run_case "$CW" "$FAKE" 09 wrong-branch      fault    fft 1 "$OUT/09-fault-wrong-branch"
run_case "$CW" "$FAKE" 10 nohit-first-error probe    fft 1 "$OUT/10-probe-nohit-first-error"
run_case "$CW" "$FAKE" 11 nohit-exit77      probe    fft 1 "$OUT/11-probe-nohit-exit77"
run_case "$CW" "$FAKE" 12 nohit-timeout     probe    fft 1 "$OUT/12-probe-nohit-timeout"
run_case "$CW" "$FAKE" 13 nohit-signal      probe    fft 1 "$OUT/13-probe-nohit-signal"
run_case "$CW" "$FAKE" 14 probe-hit-extra   probe    fft 1 "$OUT/14-probe-probe-hit-extra"
run_case "$CW" "$FAKE" 15 baseline-nohit    baseline fft 1 "$OUT/15-baseline-baseline-nohit"
run_case "$CW" "$FAKE" 16 clean-nohit       probe    fft 1 "$OUT/16-probe-clean-nohit"
run_case "$CW" "$FAKE" 17 baseline-hit-ignored      baseline fft 1 "$OUT/17-baseline-baseline-hit-ignored"
run_case "$CW" "$FAKE" 18 baseline-hit-target-crash baseline fft 1 "$OUT/18-baseline-baseline-hit-target-crash"
run_case "$CW" "$FAKE" 19 clean-nohit       control  fft 0 "$OUT/19-control-clean-nohit"
run_case "$CW" "$FAKE" 20 clean-hit         fault    fft 1 "$OUT/20-fault-clean-hit"

check_case 01 "$OUT/01-fault-exit77"       1 FAIL "exit=77"
check_case 02 "$OUT/02-fault-nohit"        1 FAIL "hits=0 want=1"
check_case 03 "$OUT/03-fault-rc1zero"      1 FAIL "rc1=0" "want=1"
check_case 04 "$OUT/04-fault-nomarker"     1 FAIL "marker=0"
check_case 05 "$OUT/05-fault-san"          1 FAIL "sanitizer="
check_case 06 "$OUT/06-fault-hang"         1 FAIL "exit=124" "timeout"
check_case 07 "$OUT/07-fault-signal"       1 FAIL "exit=139" "signal"
check_case 08 "$OUT/08-fault-no-final-pass" 1 FAIL "final PASS count=0 want=1"
check_case 09 "$OUT/09-fault-wrong-branch"  1 FAIL "HIT branch field invalid count=1 (declared=fft)" "valid HIT branch=0 want=1"
check_case 10 "$OUT/10-probe-nohit-first-error" 1 FAIL "no-hit but rc1=1"
check_case 11 "$OUT/11-probe-nohit-exit77"      1 FAIL "exit=77"
check_case 12 "$OUT/12-probe-nohit-timeout"     1 FAIL "exit=124" "timeout"
check_case 13 "$OUT/13-probe-nohit-signal"      1 FAIL "exit=139" "signal"
check_case 14 "$OUT/14-probe-probe-hit-extra"   1 FAIL "hits=2 want=1"
check_case 15 "$OUT/15-baseline-baseline-nohit" 1 FAIL "no hit: proves nothing"
check_case 16 "$OUT/16-probe-clean-nohit"       3 INAPPLICABLE
check_case 17 "$OUT/17-baseline-baseline-hit-ignored"      0 PASS
check_case 18 "$OUT/18-baseline-baseline-hit-target-crash" 0 PASS
check_case 19 "$OUT/19-control-clean-nohit" 0 PASS
check_case 20 "$OUT/20-fault-clean-hit"     0 PASS

summary "MATRIX" 20
