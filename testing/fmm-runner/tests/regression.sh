#!/bin/bash
# Supplementary regression, 10 cases, covering only the two original defects.
#   regression.sh <workspace>
# Semantics are unchanged from the previous round; these are the ten cases the
# independent audit confirmed.  Evidence lives in its own directory and is
# never written by any mutation run.
cd "$(dirname "$0")/.." || exit 1
ulimit -c 0
. tests/lib.sh

WS="$1"
[ -n "$WS" ] || { echo "usage: regression.sh <workspace>" >&2; exit 2; }
OUT="$WS/evidence/regression"
CW="$WS/work"
FAKE="$WS/work/fake.sh"
rm -rf "$OUT"; mkdir -p "$OUT"

head1 "supplementary regression (10 cases)"
say "runner hash: $(sha256sum "$CW/run-one.sh" | cut -c1-16)"

run_case "$CW" "$FAKE" R1 pass-suffix         control fft 0 "$OUT/R1-pass-suffix"
run_case "$CW" "$FAKE" R2 pass-twice          control fft 0 "$OUT/R2-pass-twice"
run_case "$CW" "$FAKE" R3 witness-prefix      control fft 0 "$OUT/R3-witness-prefix"
run_case "$CW" "$FAKE" R4 witness-double      control fft 0 "$OUT/R4-witness-double"
run_case "$CW" "$FAKE" R5 hit-unbalanced      fault   fft 2 "$OUT/R5-hit-unbalanced"
run_case "$CW" "$FAKE" R6 hit-extra           fault   fft 1 "$OUT/R6-hit-extra"
run_case "$CW" "$FAKE" R7 witness-only-none   fault   fft 1 "$OUT/R7-witness-only-none"
run_case "$CW" "$FAKE" R8 witness-none-only   probe   fft 1 "$OUT/R8-witness-none-only"
run_case "$CW" "$FAKE" R9 witness-extra-none  control fft 0 "$OUT/R9-witness-extra-none"
run_case "$CW" "$FAKE" R10 probe-hit-ok       probe   fft 1 "$OUT/R10-probe-hit-ok"

check_case R1  "$OUT/R1-pass-suffix"  1 FAIL "final PASS count=0 want=1"
check_case R2  "$OUT/R2-pass-twice"   1 FAIL "final PASS count=2 want=1"
check_case R3  "$OUT/R3-witness-prefix" 1 FAIL "malformed witness=1" "no declared-branch WITNESS (declared=fft)"
check_case R4  "$OUT/R4-witness-double" 1 FAIL "malformed witness=1" "no declared-branch WITNESS (declared=fft)"
check_case R5  "$OUT/R5-hit-unbalanced" 1 FAIL "HIT branch field invalid count=2 (declared=fft)" "valid HIT branch=0 want=2"
check_case R6  "$OUT/R6-hit-extra"      1 FAIL "HIT branch field invalid count=1 (declared=fft)"
check_case R7  "$OUT/R7-witness-only-none" 1 FAIL "no declared-branch WITNESS (declared=fft)"
check_case R8  "$OUT/R8-witness-none-only" 1 FAIL "no declared-branch WITNESS (declared=fft)"
check_case R9  "$OUT/R9-witness-extra-none" 0 PASS
check_case R10 "$OUT/R10-probe-hit-ok"      0 PASS

summary "REGRESSION" 10
