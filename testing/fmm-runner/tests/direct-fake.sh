#!/bin/bash
# Direct fake-driver verification for this round's fixture.
#   direct-fake.sh <workspace>
# Runs every variant used this round, standalone, and asserts its observable
# behaviour independently of run-one.sh.
cd "$(dirname "$0")/.." || exit 1
ulimit -c 0
. tests/lib.sh

WS="$1"
[ -n "$WS" ] || { echo "usage: direct-fake.sh <workspace>" >&2; exit 2; }
mkdir -p "$WS/direct"
D="$WS/direct"
FAKE="$WS/work/fake.sh"
TMP="$WS/direct-current.out"
CHECKS=0
FAIL=0

ck() {
  CHECKS=$((CHECKS + 1))
  if [ "$2" = "$3" ]; then printf '  ok    %-40s %s\n' "$1" "$3"
  else printf '  FAIL  %-40s want=%s got=%s\n' "$1" "$2" "$3"; FAIL=$((FAIL + 1)); fi
}

run() { : > "$TMP"; "$FAKE" "$@" > "$TMP" 2>&1; RC=$?; cp "$TMP" "$D/$1.out"; echo "$RC" > "$D/$1.exit"; }

n_hit()    { grep -c '^S4FMM HIT' "$TMP"; }
n_pass()   { grep -cxF 'RESULT pattern both PASS' "$TMP"; }
n_suffix() { grep -c '^RESULT pattern both PASS-extra' "$TMP"; }
n_diag()   { grep -cxF 'RESULT injected failure observed' "$TMP"; }
n_mark()   { grep -c '^S4FMM DRIVER DONE' "$TMP"; }
n_wit()    { grep -c '^S4FMM WITNESS' "$TMP"; }
n_rc1()    { grep -c '^RC first 1$' "$TMP"; }
n_rc1z()   { grep -c '^RC first 0$' "$TMP"; }
n_rc2()    { grep -c '^RC retry 1$' "$TMP"; }
n_witbranch() { sed -n 's/^S4FMM WITNESS //p' "$TMP" | tr ' ' '\n' | grep -c '^branch='; }

head1 "direct fake-driver: exit codes"
run exit77 fft;          ck "exit77 exit" 77 "$RC"
run nohit fft;           ck "nohit exit" 0 "$RC"
run rc1zero fft;         ck "rc1zero exit" 0 "$RC"
run nomarker fft;        ck "nomarker exit" 0 "$RC"
run san fft;             ck "san exit" 0 "$RC"
run no-final-pass fft;   ck "no-final-pass exit" 0 "$RC"
run wrong-branch fft;    ck "wrong-branch exit" 0 "$RC"
run nohit-first-error fft; ck "nohit-first-error exit" 0 "$RC"
run nohit-exit77 fft;    ck "nohit-exit77 exit" 77 "$RC"
run probe-hit-extra fft; ck "probe-hit-extra exit" 0 "$RC"
run baseline-nohit fft;  ck "baseline-nohit exit" 0 "$RC"
run baseline-hit-ignored fft; ck "baseline-hit-ignored exit" 0 "$RC"
run clean-nohit fft;     ck "clean-nohit exit" 0 "$RC"
run clean-hit fft;       ck "clean-hit exit" 0 "$RC"
run probe-hit-ok fft;    ck "probe-hit-ok exit" 0 "$RC"
run pass-suffix fft;     ck "pass-suffix exit" 0 "$RC"
run pass-twice fft;      ck "pass-twice exit" 0 "$RC"
run witness-prefix fft;  ck "witness-prefix exit" 0 "$RC"
run witness-double fft;  ck "witness-double exit" 0 "$RC"
run hit-unbalanced fft;  ck "hit-unbalanced exit" 0 "$RC"
run hit-extra fft;       ck "hit-extra exit" 0 "$RC"
run witness-only-none fft; ck "witness-only-none exit" 0 "$RC"
run witness-none-only fft; ck "witness-none-only exit" 0 "$RC"
run witness-extra-none fft; ck "witness-extra-none exit" 0 "$RC"
run control-first-error fft; ck "control-first-error exit" 0 "$RC"
run control-retry-error fft; ck "control-retry-error exit" 0 "$RC"
run branch-glob fft;     ck "branch-glob exit" 0 "$RC"
run unknown-variant-xyz fft; ck "unknown variant exit" 2 "$RC"

head1 "direct fake-driver: distinguishing behaviour"
run nohit fft;           ck "nohit HIT lines" 0 "$(n_hit)"; ck "nohit final PASS" 1 "$(n_pass)"
run rc1zero fft;         ck "rc1zero RC first 0" 1 "$(n_rc1z)"
run nomarker fft;        ck "nomarker no marker" 0 "$(n_mark)"; ck "nomarker final PASS" 1 "$(n_pass)"
run san fft;             ck "san sanitizer line" 1 "$(grep -c AddressSanitizer "$TMP")"
run probe-hit-extra fft; ck "probe-hit-extra HIT lines" 2 "$(n_hit)"
run clean-hit fft;       ck "clean-hit HIT lines" 1 "$(n_hit)"; ck "clean-hit RC first 1" 1 "$(n_rc1)"
run probe-hit-ok fft;    ck "probe-hit-ok HIT lines" 1 "$(n_hit)"
run probe-hit-ok fft;    ck "probe-hit-ok final PASS" 1 "$(n_pass)"; ck "probe-hit-ok marker" 1 "$(n_mark)"
run no-final-pass fft;   ck "no-final-pass final PASS" 0 "$(n_pass)"
run no-final-pass fft;   ck "no-final-pass diagnostic" 1 "$(n_diag)"; ck "no-final-pass marker" 1 "$(n_mark)"
run wrong-branch fft;    ck "wrong-branch WITNESS fft" 1 "$(grep -c '^S4FMM WITNESS branch=fft ' "$TMP")"
run wrong-branch fft;    ck "wrong-branch HIT branch=vl" 1 "$(grep '^S4FMM HIT' "$TMP" | grep -c 'branch=vl ')"
run pass-suffix fft;     ck "pass-suffix complete PASS" 0 "$(n_pass)"; ck "pass-suffix PASS-extra" 1 "$(n_suffix)"
run pass-twice fft;      ck "pass-twice complete PASS" 2 "$(n_pass)"
run witness-prefix fft;  ck "witness-prefix branch fields" 1 "$(n_witbranch)"
run witness-double fft;  ck "witness-double WITNESS lines" 1 "$(n_wit)"
run hit-unbalanced fft;  ck "hit-unbalanced HIT lines" 2 "$(n_hit)"
run hit-extra fft;       ck "hit-extra branch=fft-extra" 1 "$(grep '^S4FMM HIT' "$TMP" | grep -c 'branch=fft-extra')"
run witness-only-none fft; ck "witness-only-none WITNESS none" 1 "$(grep -c '^S4FMM WITNESS branch=none ' "$TMP")"
run witness-none-only fft; ck "witness-none-only HIT lines" 0 "$(n_hit)"
run witness-extra-none fft; ck "witness-extra-none WITNESS lines" 2 "$(n_wit)"
# the three new regressions
run control-first-error fft; ck "control-first-error RC first 1" 1 "$(n_rc1)"
run control-first-error fft; ck "control-first-error HIT lines" 0 "$(n_hit)"
run control-first-error fft; ck "control-first-error final PASS" 1 "$(n_pass)"
run control-retry-error fft; ck "control-retry-error RC first 0" 1 "$(n_rc1z)"
run control-retry-error fft; ck "control-retry-error RC retry 1" 1 "$(n_rc2)"
run control-retry-error fft; ck "control-retry-error HIT lines" 0 "$(n_hit)"
run branch-glob fft;     ck "branch-glob WITNESS branch=*" 1 "$(grep -c '^S4FMM WITNESS branch=\* ' "$TMP")"
run branch-glob fft;     ck "branch-glob final PASS" 1 "$(n_pass)"; ck "branch-glob marker" 1 "$(n_mark)"

head1 "timeout / signal variants with a short 2s timeout"
t0=$(date +%s); timeout 2 "$FAKE" hang fft > "$D/hang.out" 2>&1; rc=$?; t1=$(date +%s)
ck "hang under 2s timeout" 124 "$rc"; echo 124 > "$D/hang.exit"
ck "hang wallclock < 10s" yes "$([ $((t1-t0)) -lt 10 ] && echo yes || echo no)"
t0=$(date +%s); timeout 2 "$FAKE" nohit-timeout fft > "$D/nohit-timeout.out" 2>&1; rc=$?; t1=$(date +%s)
ck "nohit-timeout under 2s" 124 "$rc"; echo 124 > "$D/nohit-timeout.exit"
ck "nohit-timeout wallclock < 10s" yes "$([ $((t1-t0)) -lt 10 ] && echo yes || echo no)"
timeout 2 "$FAKE" signal fft > "$D/signal.out" 2>&1; rc=$?; echo "$rc" > "$D/signal.exit"
ck "signal killed by signal" 139 "$rc"
timeout 2 "$FAKE" nohit-signal fft > "$D/nohit-signal.out" 2>&1; rc=$?; echo "$rc" > "$D/nohit-signal.exit"
ck "nohit-signal killed by signal" 139 "$rc"
timeout 2 "$FAKE" baseline-hit-target-crash fft > "$D/baseline-hit-target-crash.out" 2>&1; rc=$?
echo "$rc" > "$D/baseline-hit-target-crash.exit"
ck "baseline-hit-target-crash by signal" 139 "$rc"

rm -f "$TMP"
echo
echo "DIRECT: checks=$CHECKS failures=$FAIL"
[ "$FAIL" = 0 ] || exit 1
exit 0
