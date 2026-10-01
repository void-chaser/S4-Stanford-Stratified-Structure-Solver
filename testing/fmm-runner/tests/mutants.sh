#!/bin/bash
# Apparatus verification: three mutation devices, each fully self-contained.
#   mutants.sh <workspace>
#
# Every mutant owns its runner, fake, logs directory and evidence directory.
# The delivered runner is never copied over, never temporarily replaced and
# never restored by a trap: mutants/A/work/run-one.sh is a separate file.  All
# three mutants are built first, then tested, so the normal evidence produced
# by matrix.sh / regression.sh cannot be touched at any point.
cd "$(dirname "$0")/.." || exit 1
ulimit -c 0
. tests/lib.sh

WS="$1"
[ -n "$WS" ] || { echo "usage: mutants.sh <workspace>" >&2; exit 2; }
DELIVERED_HASH=$(sha256sum work/run-one.sh | awk '{print $1}')
FAKE_HASH=$(sha256sum work/fake.sh | awk '{print $1}')
mkdir -p "$WS/mutants"

head1 "apparatus verification: three mutation devices"
say "delivered run-one.sh sha256: $DELIVERED_HASH"
say "delivered fake.sh    sha256: $FAKE_HASH"

# --------------------------------------------------------------- build phase
build_mutant() {  # build_mutant <A|B|D>
  local m="$1" d="$WS/mutants/$m"
  rm -rf "$d"; mkdir -p "$d/work/logs" "$d/evidence"
  cp -p work/fake.sh "$d/work/fake.sh"
  chmod +x "$d/work/fake.sh"
  case "$m" in
    A)
      cp -p work/run-one.sh "$d/work/run-one.sh"
      chmod +x "$d/work/run-one.sh"
      tests/line-replace.py "$d/work/run-one.sh" \
        'final_pass=$(grep -cxF '"'"'RESULT pattern both PASS'"'"' "$LOG")' \
        'final_pass=1' > "$d/build.log" 2>&1
      printf '%s\n' "$?" > "$d/build.exit"
      ;;
    B)
      cp -p work/run-one.sh "$d/work/run-one.sh"
      chmod +x "$d/work/run-one.sh"
      tests/line-replace.py "$d/work/run-one.sh" \
        '[ -n "$hit_summary" ] || hit_summary="none"' \
        '[ -n "$hit_summary" ] || hit_summary="none"; hit_bad=0; hit_valid=$hit' \
        > "$d/build.log" 2>&1
      printf '%s\n' "$?" > "$d/build.exit"
      ;;
    D)
      printf '#!/bin/bash\n# always-exit-1 stand-in\nexit 1\n' > "$d/work/run-one.sh"
      chmod +x "$d/work/run-one.sh"
      printf 'no anchors: unconditional exit 1\n' > "$d/build.log"
      printf '0\n' > "$d/build.exit"
      ;;
  esac
}

for m in A B D; do build_mutant "$m"; done

# A and B must have applied their anchor exactly once; anything else is a
# silently mis-targeted mutation and is a hard failure.
assert_eq "mutant A mutation applied (anchored exactly once)" 0 "$(cat "$WS/mutants/A/build.exit")"
assert_eq "mutant B mutation applied (anchored exactly once)" 0 "$(cat "$WS/mutants/B/build.exit")"

for m in A B D; do
  d="$WS/mutants/$m"
  local_hash=$(sha256sum "$d/work/run-one.sh" | awk '{print $1}')
  say "mutant $m sha256=${local_hash:0:16}"
  assert_eq "mutant $m runner file present and executable" yes \
    "$([ -x "$d/work/run-one.sh" ] && echo yes || echo no)"
  assert_eq "mutant $m hash differs from delivered" yes \
    "$([ "$local_hash" != "$DELIVERED_HASH" ] && echo yes || echo no)"
  if [ "$m" != D ]; then
    # the mutation must have matched its anchor, not silently no-opped
    if [ "$m" = A ]; then
      assert_eq "mutant A anchor applied" yes \
        "$(grep -qx 'final_pass=1' "$d/work/run-one.sh" && echo yes || echo no)"
    else
      assert_eq "mutant B anchor applied" yes \
        "$(grep -qF 'hit_bad=0; hit_valid=$hit' "$d/work/run-one.sh" && echo yes || echo no)"
    fi
    if bash -n "$d/work/run-one.sh" 2>/dev/null; then
      assert_eq "mutant $m parses" yes yes
    else
      assert_eq "mutant $m parses" yes no
    fi
  fi
  cp -p "$d/work/run-one.sh" "$d/evidence/runner-mutated.sh"
  cp -p "$d/work/fake.sh"    "$d/evidence/fake-used.sh"
done

# --------------------------------------------------------------- test phase
# Full 20-case matrix against each mutant's own runner, in the mutant's own
# workspace and output directory.
run_mutant_matrix() {  # run_mutant_matrix <A|B|D>
  local m="$1" d="$WS/mutants/$m" out="$WS/mutants/$m/evidence/matrix"
  local -a IDS=(01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16 17 18 19 20)
  local -a VAR=(exit77 nohit rc1zero nomarker san hang signal no-final-pass wrong-branch
                nohit-first-error nohit-exit77 nohit-timeout nohit-signal probe-hit-extra
                baseline-nohit clean-nohit baseline-hit-ignored baseline-hit-target-crash
                clean-nohit clean-hit)
  local -a TYP=(fault fault fault fault fault fault fault fault fault
                probe probe probe probe probe baseline probe baseline baseline
                control fault)
  local -a HIT=(1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 0 1)
  local -a WANT=(1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 3 0 0 0 0)
  local i
  rm -rf "$out"; mkdir -p "$out"
  for i in $(seq 0 19); do
    tests/run-case.sh "$d/work" "$d/work/fake.sh" "${VAR[$i]}" "${TYP[$i]}" fft "${HIT[$i]}" \
      "$out/${IDS[$i]}-${TYP[$i]}-${VAR[$i]}"
    echo "${WANT[$i]}" > "$out/${IDS[$i]}-${TYP[$i]}-${VAR[$i]}/expected.exit"
  done
}

mismatch_list() {  # mismatch_list <dir> -> "id:want:got" lines
  local out="$1" d want got id
  for d in "$out"/*/; do
    want=$(cat "$d/expected.exit" 2>/dev/null || echo "?")
    got=$(cat "$d/runner.exit" 2>/dev/null || echo "?")
    id=$(basename "$d")
    [ "$want" = "$got" ] || printf '%s want=%s got=%s\n' "$id" "$want" "$got"
  done
}

for m in A B D; do
  run_mutant_matrix "$m"
  d="$WS/mutants/$m"
  mismatch_list "$d/evidence/matrix" > "$d/evidence/mismatches.txt"
  say "mutant $m matrix mismatches: $(grep -c . "$d/evidence/mismatches.txt" 2>/dev/null || echo 0)"
done

head1 "mutant A: final-PASS rule disabled"
A="$WS/mutants/A"
assert_eq "A changes the matrix result (case 08 now passes)" yes \
  "$([ "$(cat "$A/evidence/matrix/08-fault-no-final-pass/runner.exit")" = 0 ] && echo yes || echo no)"
assert_eq "A case 08 unmutated expectation" 1 "$(cat "$A/evidence/matrix/08-fault-no-final-pass/expected.exit")"
assert_contains "A mismatch list names case 08" "$A/evidence/mismatches.txt" "08-fault-no-final-pass"
assert_eq "A mismatch list non-empty" yes "$([ -s "$A/evidence/mismatches.txt" ] && echo yes || echo no)"

head1 "mutant B: HIT-branch-field rule disabled"
B="$WS/mutants/B"
assert_eq "B changes the matrix result (case 09 now passes)" yes \
  "$([ "$(cat "$B/evidence/matrix/09-fault-wrong-branch/runner.exit")" = 0 ] && echo yes || echo no)"
assert_eq "B case 09 unmutated expectation" 1 "$(cat "$B/evidence/matrix/09-fault-wrong-branch/expected.exit")"
assert_contains "B mismatch list names case 09" "$B/evidence/mismatches.txt" "09-fault-wrong-branch"
assert_eq "B mismatch list non-empty" yes "$([ -s "$B/evidence/mismatches.txt" ] && echo yes || echo no)"

head1 "mutant D: always-exit-1 stand-in"
D="$WS/mutants/D"
assert_eq "D returns 1 for the positive control (case 19)" 1 "$(cat "$D/evidence/matrix/19-control-clean-nohit/runner.exit")"
assert_eq "D returns 1 for the positive fault (case 20)"   1 "$(cat "$D/evidence/matrix/20-fault-clean-hit/runner.exit")"
assert_eq "D case 19 unmutated expectation" 0 "$(cat "$D/evidence/matrix/19-control-clean-nohit/expected.exit")"
assert_eq "D case 20 unmutated expectation" 0 "$(cat "$D/evidence/matrix/20-fault-clean-hit/expected.exit")"
assert_contains "D mismatch list names case 19" "$D/evidence/mismatches.txt" "19-control-clean-nohit"
assert_contains "D mismatch list names case 20" "$D/evidence/mismatches.txt" "20-fault-clean-hit"

head1 "delivered files untouched by mutation testing"
assert_eq "delivered run-one.sh unchanged" "$DELIVERED_HASH" "$(sha256sum work/run-one.sh | awk '{print $1}')"
assert_eq "delivered fake.sh unchanged"    "$FAKE_HASH"    "$(sha256sum work/fake.sh | awk '{print $1}')"
assert_eq "delivered work dir has no stray logs" yes \
  "$([ -z "$(find work -maxdepth 2 -name 'logs' -print -quit)" ] && echo yes || echo no)"
assert_eq "delivered work dir holds exactly the two files" 2 "$(find work -type f | wc -l)"

# normal evidence must be byte-identical to what the normal suites produced
if [ -f "$WS/evidence/matrix-hashes.before" ]; then
  if sha256sum -c "$WS/evidence/matrix-hashes.before" > "$WS/mutants/normal-evidence-verify.out" 2>&1; then
    assert_eq "normal matrix evidence unchanged after mutants" ok ok
  else
    assert_eq "normal matrix evidence unchanged after mutants" ok "CHANGED"
    sed 's/^/        /' "$WS/mutants/normal-evidence-verify.out"
  fi
else
  assert_eq "normal matrix evidence baseline present" yes no
fi

summary "APPARATUS" 0
