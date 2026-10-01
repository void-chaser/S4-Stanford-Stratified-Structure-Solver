#!/bin/bash
# New regressions for the three problems this round fixes (3 cases).
#   regression-new.sh <workspace>
#
# N1  control, no HIT, first attempt fails  -> runner must reject on rc1
# N2  control, no HIT, retry attempt fails  -> runner must reject on rc2
# N3  control, WITNESS branch=*, with a controlled file literally named
#     "branch=fft" present in the test cwd -> must still be rejected on the
#     branch field; a directory entry must not be able to change the verdict.
cd "$(dirname "$0")/.." || exit 1
ulimit -c 0
. tests/lib.sh

WS="$1"
[ -n "$WS" ] || { echo "usage: regression-new.sh <workspace>" >&2; exit 2; }
OUT="$WS/evidence/regression-new"
CW="$WS/work"
FAKE="$WS/work/fake.sh"
rm -rf "$OUT"; mkdir -p "$OUT"

head1 "new regressions (3 cases)"
say "runner hash: $(sha256sum "$CW/run-one.sh" | cut -c1-16)"

# ---------------------------------------------------------------- N1 and N2
run_case "$CW" "$FAKE" N1 control-first-error control fft 0 "$OUT/N1-control-first-error"
run_case "$CW" "$FAKE" N2 control-retry-error control fft 0 "$OUT/N2-control-retry-error"

# ---------------------------------------------------------------------- N3
# The controlled cwd holds a file whose name is a valid branch field.  If the
# parser glob-expanded an unquoted field, branch=* would match that file name
# and be accepted.
N3DIR="$WS/controlled-cwd"
rm -rf "$N3DIR"; mkdir -p "$N3DIR"
printf 'controlled file named exactly like a branch field\n' > "$N3DIR/branch=fft"
printf 'controlled cwd: %s\ncontrolled entry: branch=fft\n' "$N3DIR" > "$OUT/N3-controlled-cwd.txt"
ls -la "$N3DIR" >> "$OUT/N3-controlled-cwd.txt"
N3O="$OUT/N3-control-branch-glob"
mkdir -p "$N3O"
( ulimit -c 0; timeout 2 "$FAKE" branch-glob fft ) > "$N3O/fake.out" 2>&1
echo "$?" > "$N3O/fake.exit"
cp -p "$N3DIR/branch=fft" "$N3O/controlled-cwd-entry"
N3LOG="$CW/logs/one-control-fft-4-scratch-1-1-1-branch-glob.log"
rm -f "$N3LOG"
( cd "$N3DIR" && ulimit -c 0 && S4FMM_FAKE=branch-glob S4FMM_TIMEOUT=2 \
    "$CW/run-one.sh" control fft 4 scratch 1 1 1 0 ) > "$N3O/runner.out" 2>&1
echo "$?" > "$N3O/runner.exit"
cp "$N3LOG" "$N3O/driver.log" 2>/dev/null || : > "$N3O/driver.log"
printf 'branch-glob\n' > "$N3O/variant"; printf 'control\n' > "$N3O/type"
printf '0\n' > "$N3O/hits"; printf 'fft\n' > "$N3O/branch"; printf 'N3\n' > "$N3O/case_id"

# the controlled file must exist at verdict time and still afterwards
assert_file "$N3DIR/branch=fft"
assert_eq "N3 controlled cwd entry still present after run" yes \
  "$([ -e "$N3DIR/branch=fft" ] && echo yes || echo no)"

check_case N1 "$OUT/N1-control-first-error" 1 FAIL "rc1=1 want=0"
check_case N2 "$OUT/N2-control-retry-error" 1 FAIL "rc2=1 want=0"
check_case N3 "$N3O" 1 FAIL "malformed witness=1" "no declared-branch WITNESS (declared=fft)"

# The same invalid branch value must not become acceptable just because a
# matching file exists: compare against the same variant run without it.
N3B="$WS/controlled-cwd-empty"
rm -rf "$N3B"; mkdir -p "$N3B"
N3O2="$OUT/N3b-control-branch-glob-noentry"
mkdir -p "$N3O2"
rm -f "$N3LOG"
( cd "$N3B" && ulimit -c 0 && S4FMM_FAKE=branch-glob S4FMM_TIMEOUT=2 \
    "$CW/run-one.sh" control fft 4 scratch 1 1 1 0 ) > "$N3O2/runner.out" 2>&1
echo "$?" > "$N3O2/runner.exit"
cp "$N3LOG" "$N3O2/driver.log" 2>/dev/null || : > "$N3O2/driver.log"
printf 'branch-glob\n' > "$N3O2/variant"; printf 'control\n' > "$N3O2/type"
printf '0\n' > "$N3O2/hits"; printf 'fft\n' > "$N3O2/branch"; printf 'N3b\n' > "$N3O2/case_id"
head1 "N3 control: verdict must not depend on directory contents"
assert_eq "N3 with controlled entry: exit" 1 "$(cat "$N3O/runner.exit")"
assert_eq "N3 without controlled entry: exit" 1 "$(cat "$N3O2/runner.exit")"
assert_eq "N3 verdict identical with/without entry" \
  "$(val "$N3O/runner.out" verdict)/$(val "$N3O/runner.out" reason)" \
  "$(val "$N3O2/runner.out" verdict)/$(val "$N3O2/runner.out" reason)"
LIBN_CASES=$((LIBN_CASES + 1))   # N3b counts as its own case record

summary "REGRESSION-NEW" 4
