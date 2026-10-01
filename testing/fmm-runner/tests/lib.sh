#!/bin/bash
# Shared assertion helpers for this round's suites.
# Every check records want/got and increments FAILN on mismatch; nothing is
# reported as passing merely because a command exited 0.

LIBN_FAIL=0
LIBN_CHECKS=0
LIBN_CASES=0

say()   { printf '%s\n' "$*"; }
head1() { printf '\n=== %s ===\n' "$*"; }

# assert_eq <label> <want> <got>
assert_eq() {
  LIBN_CHECKS=$((LIBN_CHECKS + 1))
  if [ "$2" = "$3" ]; then
    printf '  ok    %-46s want=%s got=%s\n' "$1" "$2" "$3"
  else
    printf '  FAIL  %-46s want=%s got=%s\n' "$1" "$2" "$3"
    LIBN_FAIL=$((LIBN_FAIL + 1))
  fi
}

# assert_in <label> <allowed-list-space-separated> <got>
assert_in() {
  LIBN_CHECKS=$((LIBN_CHECKS + 1))
  local a
  for a in $2; do
    if [ "$a" = "$3" ]; then
      printf '  ok    %-46s got=%s in [%s]\n' "$1" "$3" "$2"
      return 0
    fi
  done
  printf '  FAIL  %-46s got=%s not in [%s]\n' "$1" "$3" "$2"
  LIBN_FAIL=$((LIBN_FAIL + 1))
}

# assert_contains <label> <file> <needle>
assert_contains() {
  LIBN_CHECKS=$((LIBN_CHECKS + 1))
  if grep -qF -- "$3" "$2"; then
    printf '  ok    %-46s contains %s\n' "$1" "$3"
  else
    printf '  FAIL  %-46s missing %s\n' "$1" "$3"
    LIBN_FAIL=$((LIBN_FAIL + 1))
  fi
}

# assert_file <path>
assert_file() {
  LIBN_CHECKS=$((LIBN_CHECKS + 1))
  if [ -s "$1" ]; then
    printf '  ok    %-46s present\n' "$(basename "$1")"
  else
    printf '  FAIL  %-46s missing/empty\n' "$1"
    LIBN_FAIL=$((LIBN_FAIL + 1))
  fi
}

# val <file> <key>
val() { sed -n "s/^$2=//p" "$1" | head -1; }

# status_for <verdict>
status_for() {
  case "$1" in
    PASS) echo 0 ;;
    FAIL) echo 1 ;;
    INAPPLICABLE) echo 3 ;;
    *) echo "unknown" ;;
  esac
}

# run_case <casework> <fake> <id> <variant> <type> <branch> <hits> <outdir>
#   The runner is invoked from the case's own work copy, so its log path is
#   deterministic and needs no ls -t guessing.
run_case() {
  local cw="$1" fake="$2" id="$3" variant="$4" type="$5" br="$6" hits="$7" out="$8"
  mkdir -p "$out"
  ( ulimit -c 0; timeout 2 "$fake" "$variant" "$br" ) > "$out/fake.out" 2>&1
  echo "$?" > "$out/fake.exit"
  local log="$cw/logs/one-$type-$br-4-scratch-1-1-1-$variant.log"
  rm -f "$log"    # never let a previous run's log be read as this case's log
  ( cd "$cw" && ulimit -c 0 && S4FMM_FAKE="$variant" S4FMM_TIMEOUT=2 \
      "$cw/run-one.sh" "$type" "$br" 4 scratch 1 1 1 "$hits" ) > "$out/runner.out" 2>&1
  echo "$?" > "$out/runner.exit"
  cp "$log" "$out/driver.log" 2>/dev/null || : > "$out/driver.log"
  printf '%s\n' "$variant" > "$out/variant"
  printf '%s\n' "$type"    > "$out/type"
  printf '%s\n' "$hits"    > "$out/hits"
  printf '%s\n' "$br"      > "$out/branch"
  printf '%s\n' "$id"      > "$out/case_id"
}

# check_case <id> <outdir> <want_exit> <want_verdict> <reason-needle>...
check_case() {
  local id="$1" out="$2" want_exit="$3" want_verdict="$4"
  shift 4
  LIBN_CASES=$((LIBN_CASES + 1))
  local got_exit got_verdict got_status
  got_exit=$(cat "$out/runner.exit" 2>/dev/null || echo missing)
  got_verdict=$(val "$out/runner.out" verdict)
  got_status=$(status_for "$got_verdict")
  echo
  printf '%-4s %-20s %-8s hits=%-2s expect exit=%s verdict=%s\n' \
    "$id" "$(cat "$out/variant")" "$(cat "$out/type")" "$(cat "$out/hits")" \
    "$want_exit" "$want_verdict"
  assert_file "$out/fake.out"
  assert_file "$out/runner.out"
  assert_file "$out/driver.log"
  assert_eq "$id runner exit code"  "$want_exit"    "$got_exit"
  assert_eq "$id runner verdict"    "$want_verdict" "$got_verdict"
  assert_eq "$id verdict->status"   "$want_exit"    "$got_status"
  assert_eq "$id verdict records"   1 "$(grep -c '^verdict=' "$out/runner.out")"
  local r
  for r in "$@"; do assert_contains "$id reason" "$out/runner.out" "$r"; done
  printf '  reason: %s\n' "$(val "$out/runner.out" reason)"
}

# summary <label> <expected-cases>
summary() {
  local label="$1" want="$2"
  echo
  assert_eq "$label case count" "$want" "$LIBN_CASES"
  echo
  if [ "$LIBN_FAIL" = 0 ]; then
    say "$label: ALL CHECKS PASSED  checks=$LIBN_CHECKS cases=$LIBN_CASES"
    return 0
  fi
  say "$label: FAILURES=$LIBN_FAIL  checks=$LIBN_CHECKS cases=$LIBN_CASES"
  return 1
}
