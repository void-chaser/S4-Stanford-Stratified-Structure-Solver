#!/bin/bash
# fault-propagation.sh <workspace>
#
# Failure-propagation checks for the REAL tools.  Earlier versions proved a
# home-made mirror wrapper and a hash check that only failed because of a
# missing relative path; both are replaced here.
#
#   T1  real generator: normal generation then verification -> 0
#   T2  real generator: output path is an existing directory -> non-zero
#   T3  real run-all.sh, byte-identical, with ONLY the baseline-generation
#       invocation forced to fail -> total non-zero, status records the
#       failure and never a created baseline
#   T4  the same real entry, with a child stage forced to 7 -> total non-zero,
#       the real statuses recorded, and the stubs prove the real entry ran them
#   T5  input hash tampered from the correct cwd -> untampered verifies 0,
#       tampered fails with an explicit hash FAILED (not a missing path)
#   T6  syntax error -> the real bootstrap refuses and prepares no workspace
#   T7  manifest-covered file verifies 0, then tampering -> non-zero + FAILED
#
# Everything runs in isolated copies under the tool-test subdirectory; the
# frozen delivery is never modified.
cd "$(dirname "$0")/.." || exit 1
ulimit -c 0
. tests/lib.sh

W="$1"
[ -n "$W" ] || { echo "usage: fault-propagation.sh <workspace>" >&2; exit 2; }
F="$W/tool-tests"
rm -rf "$F"; mkdir -p "$F"

ROOT=$(cd "$(dirname "$0")/.." && pwd)
ENTRY_HASH_BEFORE=$(sha256sum "$ROOT/tests/run-all.sh" | awk '{print $1}')
GEN_HASH_BEFORE=$(sha256sum "$ROOT/tests/manifest-generate.sh" | awk '{print $1}')
DEV_RUN_HASH_BEFORE=$(sha256sum "$ROOT/work/run-one.sh" | awk '{print $1}')
DEV_FAKE_HASH_BEFORE=$(sha256sum "$ROOT/work/fake.sh" | awk '{print $1}')
say "real run-all.sh        sha256: $ENTRY_HASH_BEFORE"
say "real manifest-generate sha256: $GEN_HASH_BEFORE"

# make_entry_sandbox <dir>
#   A copy of the REAL run-all.sh (bytes recorded and compared unchanged) plus
#   the real verify-manifest.sh and a real, unmodified manifest-generate.sh.
#   The child suite stages are fast stubs that record their invocation, so the
#   real entry's orchestration and status accumulation are exercised without
#   recursively re-running the whole acceptance suite.  The runner devices are
#   real byte copies, so the baseline generation hashes real artifacts.
make_entry_sandbox() {
  local d="$1"
  rm -rf "$d"
  mkdir -p "$d/tests" "$d/work" "$d/before" "$d/runs"
  cp -p "$ROOT/tests/run-all.sh"            "$d/tests/run-all.sh"
  cp -p "$ROOT/tests/verify-manifest.sh"    "$d/tests/verify-manifest.sh"
  cp -p "$ROOT/tests/manifest-generate.sh"  "$d/tests/manifest-generate.sh"
  cp -p "$ROOT/inputs.sha256"               "$d/inputs.sha256"
  cp -p "$ROOT/work/run-one.sh"             "$d/work/run-one.sh"
  cp -p "$ROOT/work/fake.sh"                "$d/work/fake.sh"
  cp -p "$ROOT/before/run-one.sh"           "$d/before/run-one.sh"
  cp -p "$ROOT/before/fake.sh"              "$d/before/fake.sh"
  cat > "$d/tests/bootstrap-validate.sh" <<BOOTEOF
#!/bin/bash
echo "STUB-INVOKED bootstrap" >> "$d/invocations.txt"
ws="\$1"
mkdir -p "\$ws/work/logs" "\$ws/work-operator/logs"
cp -p "$d/work/run-one.sh" "\$ws/work/run-one.sh"
cp -p "$d/work/fake.sh"    "\$ws/work/fake.sh"
cp -p "$d/work/run-one.sh" "\$ws/work-operator/run-one.sh"
cp -p "$d/work/fake.sh"    "\$ws/work-operator/fake.sh"
chmod +x "\$ws/work/"*.sh "\$ws/work-operator/"*.sh
# carry the sandbox's current evidence fixture into the run workspace, so the
# real entry's evidence-freeze and evidence-isolation stages operate on real
# content (the stub suite stages do not produce evidence of their own)
if [ -d "$d/evidence" ]; then
  ( cd "\$ws" && mkdir -p evidence && cp -rp "$d/evidence/." evidence/ )
fi
exit 0
BOOTEOF
  local stage
  for stage in direct-fake matrix regression regression-new mutants fault-propagation; do
    cat > "$d/tests/$stage.sh" <<STUBEOF
#!/bin/bash
echo "STUB-INVOKED $stage" >> "$d/invocations.txt"
if [ -f "$d/fail-stage" ] && [ "\$(cat "$d/fail-stage")" = "$stage" ]; then
  exit 7
fi
mkdir -p "$(dirname "$d")/stub"
echo "stub evidence for $stage" > "$d/stub-$stage.txt"
exit 0
STUBEOF
  done
  chmod +x "$d"/tests/*.sh "$d"/work/*.sh
  # a current, self-consistent matrix-evidence baseline so the real entry's
  # evidence-isolation stage has a fixture to freeze and re-verify.  The paths
  # are stored relative to the sandbox (as the real run does), so the check
  # works whether it is run from the sandbox or from the repository root.
  mkdir -p "$d/evidence/matrix/sample"
  echo "sandbox sample evidence" > "$d/evidence/matrix/sample/runner.out"
  ( cd "$d/evidence" && find matrix -type f -print0 | sort -z | xargs -0 -r sha256sum ) \
    > "$d/evidence/matrix-hashes.before"
  say "  (sandbox fixture) matrix-hashes.before:"
  sed 's/^/    /' "$d/evidence/matrix-hashes.before"
}

# ------------------------------------------------------------------ T1
head1 "T1 real generator: normal generation verifies"
T1="$F/T1-normal"
mkdir -p "$T1/work"
cp -p "$ROOT/work/run-one.sh" "$T1/work/run-one.sh"
cp -p "$ROOT/work/fake.sh"    "$T1/work/fake.sh"
"$ROOT/tests/manifest-generate.sh" "$T1/m.sha256" "$T1/work" > "$T1/gen.out" 2>&1
T1RC=$?
say "  generator rc=$T1RC"
cat "$T1/m.sha256"
assert_eq "T1 generator succeeds" 0 "$T1RC"
assert_eq "T1 manifest lists both devices" 2 "$(grep -c . "$T1/m.sha256")"
( cd "$T1" && "$ROOT/tests/verify-manifest.sh" "$T1/m.sha256" ) > "$T1/verify.out" 2>&1
assert_eq "T1 generated manifest verifies" 0 "$?"

# --- T1 self-exclusion: the output manifest must never list itself ----------
# The output lives INSIDE the scanned input directory and is not named
# SHA256SUMS, so it can only be excluded by its real path.  A manifest that
# listed itself would record its own stale hash and fail verification on the
# next generation.
head1 "T1 self-exclusion: output manifest inside the scanned input directory"
T1S="$F/T1-self-exclusion"
rm -rf "$T1S"; mkdir -p "$T1S/input"
printf 'payload contents for the self-exclusion check\n' > "$T1S/input/payload"
PAYLOAD_HASH=$(sha256sum "$T1S/input/payload" | awk '{print $1}')

# (1) first generation, output inside the scanned directory, custom name
"$ROOT/tests/manifest-generate.sh" "$T1S/input/m.sha256" "$T1S/input" > "$T1S/first-generate.out" 2>&1
T1FGEN=$?
echo "$T1FGEN" > "$T1S/first-generate.exit"
cp -p "$T1S/input/m.sha256" "$T1S/first-manifest.sha256"
cat "$T1S/first-generate.out"
say "  first generation rc=$T1FGEN; manifest entries=$(grep -c . "$T1S/first-manifest.sha256")"
cat "$T1S/first-manifest.sha256"
assert_eq "T1s first generation succeeds" 0 "$T1FGEN"
assert_eq "T1s first manifest has exactly one record" 1 "$(grep -c . "$T1S/first-manifest.sha256")"
assert_eq "T1s first manifest has no self record" 0 \
  "$(grep -c 'input/m\.sha256$' "$T1S/first-manifest.sha256")"
assert_eq "T1s first manifest records the payload" 1 \
  "$(grep -c "$PAYLOAD_HASH" "$T1S/first-manifest.sha256")"
( cd "$T1S" && "$ROOT/tests/verify-manifest.sh" "$T1S/input/m.sha256" ) > "$T1S/first-verify.out" 2>&1
T1FVER=$?
echo "$T1FVER" > "$T1S/first-verify.exit"
cat "$T1S/first-verify.out"
assert_eq "T1s first manifest verifies" 0 "$T1FVER"

# (2) regenerate with the same path and arguments: the existing manifest must
# still be excluded, so the manifest stays stable and keeps verifying
"$ROOT/tests/manifest-generate.sh" "$T1S/input/m.sha256" "$T1S/input" > "$T1S/second-generate.out" 2>&1
T1SGEN=$?
echo "$T1SGEN" > "$T1S/second-generate.exit"
cp -p "$T1S/input/m.sha256" "$T1S/second-manifest.sha256"
cat "$T1S/second-generate.out"
say "  second generation rc=$T1SGEN; manifest entries=$(grep -c . "$T1S/second-manifest.sha256")"
cat "$T1S/second-manifest.sha256"
assert_eq "T1s regeneration succeeds" 0 "$T1SGEN"
assert_eq "T1s second manifest has exactly one record" 1 "$(grep -c . "$T1S/second-manifest.sha256")"
assert_eq "T1s second manifest has no self record" 0 \
  "$(grep -c 'input/m\.sha256$' "$T1S/second-manifest.sha256")"
assert_eq "T1s second manifest records the payload" 1 \
  "$(grep -c "$PAYLOAD_HASH" "$T1S/second-manifest.sha256")"
( cd "$T1S" && "$ROOT/tests/verify-manifest.sh" "$T1S/input/m.sha256" ) > "$T1S/second-verify.out" 2>&1
T1SVER=$?
echo "$T1SVER" > "$T1S/second-verify.exit"
cat "$T1S/second-verify.out"
assert_eq "T1s regenerated manifest verifies" 0 "$T1SVER"
assert_eq "T1s regenerated manifest is byte-identical to the first" yes \
  "$([ "$(sha256sum "$T1S/first-manifest.sha256" | awk '{print $1}')" \
      = "$(sha256sum "$T1S/second-manifest.sha256" | awk '{print $1}')" ] && echo yes || echo no)"

# (3) the same checks reached through a normal RELATIVE path form, so a
# different way of naming the same output cannot break the exclusion
T1R="$F/T1-self-exclusion-relative"
rm -rf "$T1R"; mkdir -p "$T1R/input"
printf 'payload contents for the self-exclusion check\n' > "$T1R/input/payload"
( cd "$T1R" && "$ROOT/tests/manifest-generate.sh" input/m.sha256 input ) \
  > "$T1R/first-generate.out" 2>&1
T1RGEN=$?
echo "$T1RGEN" > "$T1R/first-generate.exit"
cp -p "$T1R/input/m.sha256" "$T1R/first-manifest.sha256"
assert_eq "T1r relative-path generation succeeds" 0 "$T1RGEN"
assert_eq "T1r first manifest has exactly one record" 1 "$(grep -c . "$T1R/first-manifest.sha256")"
assert_eq "T1r first manifest has no self record" 0 \
  "$(grep -c 'input/m\.sha256$' "$T1R/first-manifest.sha256")"
( cd "$T1R" && "$ROOT/tests/verify-manifest.sh" input/m.sha256 ) > "$T1R/first-verify.out" 2>&1
assert_eq "T1r first manifest verifies" 0 "$?"
( cd "$T1R" && "$ROOT/tests/manifest-generate.sh" input/m.sha256 input ) \
  > "$T1R/second-generate.out" 2>&1
T1RGEN2=$?
echo "$T1RGEN2" > "$T1R/second-generate.exit"
cp -p "$T1R/input/m.sha256" "$T1R/second-manifest.sha256"
assert_eq "T1r relative-path regeneration succeeds" 0 "$T1RGEN2"
assert_eq "T1r second manifest has exactly one record" 1 "$(grep -c . "$T1R/second-manifest.sha256")"
assert_eq "T1r second manifest has no self record" 0 \
  "$(grep -c 'input/m\.sha256$' "$T1R/second-manifest.sha256")"
( cd "$T1R" && "$ROOT/tests/verify-manifest.sh" input/m.sha256 ) > "$T1R/second-verify.out" 2>&1
assert_eq "T1r regenerated manifest verifies" 0 "$?"
cat "$T1R/second-verify.out"

# ------------------------------------------------------------------ T2
head1 "T2 real generator: output path is an existing directory"
T2="$F/T2-output-is-directory"
mkdir -p "$T2/work" "$T2/output-directory"
cp -p "$ROOT/work/run-one.sh" "$T2/work/run-one.sh"
"$ROOT/tests/manifest-generate.sh" "$T2/output-directory" "$T2/work" > "$T2/actual.out" 2>&1
T2RC=$?
cat "$T2/actual.out"
assert_eq "T2 generator fails when the output is a directory" yes \
  "$([ "$T2RC" != 0 ] && echo yes || echo no)"
assert_contains "T2 error output states the directory problem" "$T2/actual.out" "output path is a directory"

# ------------------------------------------------------------------ T3
# Force ONLY the baseline-generation call to fail.  The wrapper fails only when
# the requested output is exactly the delivered baseline path, so no other
# stage is affected; all other calls are forwarded to the real generator.
head1 "T3 real entry: baseline creation fails"
T3="$F/T3-baseline-failure"
# The real entry orchestrates; the child suites are fast recorded stubs, so the
# injected baseline-generation failure is the ONLY stage that fails.
make_entry_sandbox "$T3"
cat > "$T3/tests/manifest-generate.sh" <<'GENEOF'
#!/bin/bash
# injection wrapper: fails only for the delivered baseline path
out="$1"
case "$out" in
  */delivered-frozen.sha256)
    echo "INJECTED baseline-generation failure (rc=7) for $out" >&2
    exit 7 ;;
esac
exec "$(dirname "$0")/manifest-generate.real.sh" "$@"
GENEOF
cp -p "$ROOT/tests/manifest-generate.sh" "$T3/tests/manifest-generate.real.sh"
chmod +x "$T3/tests/manifest-generate.sh" "$T3/tests/manifest-generate.real.sh"
"$T3/tests/manifest-generate.sh" "$T3/delivered-frozen.sha256" x >/dev/null 2>&1
inj=$?
"$T3/tests/manifest-generate.sh" "$T3/other.sha256" "$T3/work" >/dev/null 2>&1
fwd=$?
say "  injected baseline path rc=$inj (want 7); forwarded normal path rc=$fwd (want 0)"
assert_eq "T3 injection is targeted and returns 7" 7 "$inj"
assert_eq "T3 other paths still reach the real generator" 0 "$fwd"
rm -f "$T3/other.sha256"
( cd "$T3" && bash tests/run-all.sh baseline-probe ) > "$T3/actual.out" 2>/dev/null
T3RC=$?
printf '%s\n' "$T3RC" > "$T3/actual.exit"
cat "$T3/actual.out"
T3STATUS="$T3/runs/baseline-probe/stage-status.txt"
say "  total entry exit=$T3RC (want non-zero)"
assert_eq "T3 total entry fails when baseline creation fails" yes \
  "$([ "$T3RC" != 0 ] && echo yes || echo no)"
assert_eq "T3 status records baseline-created rc=7" 1 \
  "$(grep -c '^deliverable-baseline-created rc=7$' "$T3STATUS")"
assert_eq "T3 status records deliverable-verify non-zero" 1 \
  "$(grep -c '^deliverable-verify rc=[1-9]' "$T3STATUS")"
assert_eq "T3 never records a successfully created baseline" 0 \
  "$(grep -c '^deliverable-baseline-created rc=0$' "$T3STATUS")"
# Every stage other than the injected baseline failure, and the deliverable
# check that is consequential to it, must have really succeeded.  This proves
# the injected failure is the sole cause of the non-zero total.
assert_eq "T3 all other stages report rc=0" 0 \
  "$(grep -vE '^deliverable-(baseline-created|verify) rc=' "$T3STATUS" \
     | grep -cE 'rc=[1-9]' )"
assert_eq "T3 output does not claim ALL STAGES PASSED" 0 \
  "$(grep -c 'ALL STAGES PASSED' "$T3/actual.out")"
assert_eq "T3 no valid baseline left behind" yes \
  "$([ -s "$T3/delivered-frozen.sha256" ] && echo no || echo yes)"
assert_eq "T3 entry bytes unchanged" "$ENTRY_HASH_BEFORE" \
  "$(sha256sum "$T3/tests/run-all.sh" | awk '{print $1}')"

# ------------------------------------------------------------------ T4
head1 "T4 real entry: child stage returns 7"
T4="$F/T4-child-failure"
make_entry_sandbox "$T4"
printf 'direct-fake\n' > "$T4/fail-stage"
( cd "$T4" && bash tests/run-all.sh child-probe ) > "$T4/actual.out" 2>&1
T4RC=$?
printf '%s\n' "$T4RC" > "$T4/actual.exit"
cat "$T4/actual.out"
T4STATUS="$T4/runs/child-probe/stage-status.txt"
say "  total entry exit=$T4RC (want non-zero)"
assert_eq "T4 total entry fails on a child stage failure" yes \
  "$([ "$T4RC" != 0 ] && echo yes || echo no)"
assert_eq "T4 records the failing stage with its real rc=7" 1 \
  "$(grep -c '^direct rc=7$' "$T4STATUS")"
assert_eq "T4 records the following stage as rc=0" 1 \
  "$(grep -c '^matrix rc=0$' "$T4STATUS")"
assert_eq "T4 real entry actually invoked the stub stages" yes \
  "$([ -s "$T4/invocations.txt" ] && echo yes || echo no)"
say "  stub invocations recorded by the real entry:"
sed 's/^/    /' "$T4/invocations.txt"
assert_eq "T4 output does not claim ALL STAGES PASSED" 0 \
  "$(grep -c 'ALL STAGES PASSED' "$T4/actual.out")"
assert_eq "T4 entry bytes unchanged" "$ENTRY_HASH_BEFORE" \
  "$(sha256sum "$T4/tests/run-all.sh" | awk '{print $1}')"

# ------------------------------------------------------------------ T5
head1 "T5 input hash tampering detected from the correct cwd"
T5="$F/T5-input-tamper"
mkdir -p "$T5/work"
cp -p "$ROOT/work/run-one.sh" "$T5/work/run-one.sh"
cp -p "$ROOT/work/fake.sh"    "$T5/work/fake.sh"
( cd "$T5" && "$ROOT/tests/manifest-generate.sh" "$T5/inputs.sha256" work ) > "$T5/gen.out" 2>&1
say "  generator rc=$?"
( cd "$T5" && sha256sum -c inputs.sha256 ) > "$T5/verify-clean.out" 2>&1
CLEANRC=$?
cat "$T5/verify-clean.out"
assert_eq "T5 untampered copy verifies cleanly" 0 "$CLEANRC"
printf '# tamper: appended after the manifest was generated\n' >> "$T5/work/run-one.sh"
LISTED=$(grep ' work/run-one.sh$' "$T5/inputs.sha256" | awk '{print $1}')
ACTUAL=$(sha256sum "$T5/work/run-one.sh" | awk '{print $1}')
say "  listed=$LISTED"
say "  actual=$ACTUAL"
assert_eq "T5 tamper really changed the file" yes \
  "$([ "$LISTED" != "$ACTUAL" ] && echo yes || echo no)"
( cd "$T5" && sha256sum -c inputs.sha256 ) > "$T5/verify-bad.out" 2>&1
BADRC=$?
cat "$T5/verify-bad.out"
assert_eq "T5 tampered input fails verification" 1 "$BADRC"
assert_contains "T5 failure is an explicit hash FAILED" "$T5/verify-bad.out" "work/run-one.sh: FAILED"
assert_eq "T5 failure is not a missing-path error" 0 \
  "$(grep -c 'No such file' "$T5/verify-bad.out")"

head1 "T5b real bootstrap refuses the tampered input and starts nothing"
T5B="$F/T5b-bootstrap-blocks"
mkdir -p "$T5B/tests" "$T5B/work" "$T5B/ws"
cp -p "$ROOT/tests/bootstrap-validate.sh" "$T5B/tests/bootstrap-validate.sh"
cp -p "$ROOT/tests/lib.sh"               "$T5B/tests/lib.sh"
cp -p "$T5/inputs.sha256"                "$T5B/inputs.sha256"
cp -p "$T5/work/run-one.sh"              "$T5B/work/run-one.sh"
cp -p "$T5/work/fake.sh"                 "$T5B/work/fake.sh"
( cd "$T5B" && bash tests/bootstrap-validate.sh "$T5B/ws" t5b ) > "$T5B/actual.out" 2>&1
T5BRC=$?
cat "$T5B/actual.out"
assert_eq "T5b bootstrap rejects the tampered input" yes \
  "$([ "$T5BRC" != 0 ] && echo yes || echo no)"
# the gate is real: no run workspace was prepared, so no dependent stage could
# have started against it
assert_eq "T5b bootstrap prepared no run workspace" 0 \
  "$([ -d "$T5B/ws/work" ] && echo 1 || echo 0)"
assert_eq "T5b bootstrap wrote no operator workspace" 0 \
  "$([ -d "$T5B/ws/work-operator" ] && echo 1 || echo 0)"

# ------------------------------------------------------------------ T6
head1 "T6 real bootstrap refuses a syntax error and starts nothing"
T6="$F/T6-syntax"
mkdir -p "$T6/tests" "$T6/work" "$T6/ws"
cp -p "$ROOT/tests/bootstrap-validate.sh" "$T6/tests/bootstrap-validate.sh"
cp -p "$ROOT/tests/lib.sh"               "$T6/tests/lib.sh"
{ head -20 "$ROOT/work/run-one.sh"; printf 'if [ "$x" = 1 ; then\n'; } > "$T6/work/run-one.sh"
cp -p "$ROOT/work/fake.sh" "$T6/work/fake.sh"
# refresh the manifest so the syntax failure is the blocking cause, not a hash drift
( cd "$T6" && "$ROOT/tests/manifest-generate.sh" "$T6/inputs.sha256" work ) > "$T6/gen.out" 2>&1
( cd "$T6" && bash tests/bootstrap-validate.sh "$T6/ws" t6 ) > "$T6/actual.out" 2>&1
T6RC=$?
cat "$T6/actual.out"
assert_eq "T6 bootstrap rejects the syntax error" yes \
  "$([ "$T6RC" != 0 ] && echo yes || echo no)"
assert_eq "T6 bootstrap prepared no run workspace" 0 \
  "$([ -d "$T6/ws/work" ] && echo 1 || echo 0)"
assert_eq "T6 bootstrap wrote no operator workspace" 0 \
  "$([ -d "$T6/ws/work-operator" ] && echo 1 || echo 0)"

# ------------------------------------------------------------------ T7
head1 "T7 manifest tamper detected by the real verifier"
T7="$F/T7-manifest-tamper"
mkdir -p "$T7/work"
cp -p "$ROOT/work/run-one.sh" "$T7/work/run-one.sh"
cp -p "$ROOT/work/fake.sh"    "$T7/work/fake.sh"
( cd "$T7" && "$ROOT/tests/manifest-generate.sh" "$T7/m.sha256" work ) > "$T7/gen.out" 2>&1
say "  generator rc=$?"
( cd "$T7" && "$ROOT/tests/verify-manifest.sh" "$T7/m.sha256" ) > "$T7/verify-clean.out" 2>&1
assert_eq "T7 untampered manifest verifies" 0 "$?"
printf '# tamper\n' >> "$T7/work/fake.sh"
( cd "$T7" && "$ROOT/tests/verify-manifest.sh" "$T7/m.sha256" ) > "$T7/verify-bad.out" 2>&1
T7BAD=$?
cat "$T7/verify-bad.out"
assert_eq "T7 tampered manifest fails verification" 1 "$T7BAD"
assert_contains "T7 failure is an explicit hash FAILED" "$T7/verify-bad.out" "work/fake.sh: FAILED"

# ------------------------------------------------------------ delivered state
head1 "T8 real entry: reusing an existing run id is refused"
T8="$F/T8-duplicate-id"
make_entry_sandbox "$T8"
( cd "$T8" && bash tests/run-all.sh dup-probe ) > "$T8/first.out" 2>&1
T8FIRST=$?
say "  first run rc=$T8FIRST (want 0)"
cat "$T8/first.out"
assert_eq "T8 first run succeeds" 0 "$T8FIRST"
BEFORE=$(find "$T8/runs/dup-probe" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')
( cd "$T8" && bash tests/run-all.sh dup-probe ) > "$T8/second.out" 2>&1
T8SECOND=$?
cat "$T8/second.out"
say "  duplicate run rc=$T8SECOND (want 2)"
assert_eq "T8 reusing a successful run id returns 2" 2 "$T8SECOND"
assert_contains "T8 refusal message is explicit" "$T8/second.out" "REFUSING TO OVERWRITE"
AFTER=$(find "$T8/runs/dup-probe" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')
assert_eq "T8 old evidence unchanged by the refused attempt" "$BEFORE" "$AFTER"

head1 "frozen delivery untouched by all tool tests"
assert_eq "real run-all.sh unchanged"        "$ENTRY_HASH_BEFORE"    "$(sha256sum "$ROOT/tests/run-all.sh" | awk '{print $1}')"
assert_eq "real manifest-generate unchanged" "$GEN_HASH_BEFORE"      "$(sha256sum "$ROOT/tests/manifest-generate.sh" | awk '{print $1}')"
assert_eq "delivered run-one.sh unchanged"   "$DEV_RUN_HASH_BEFORE"  "$(sha256sum "$ROOT/work/run-one.sh" | awk '{print $1}')"
assert_eq "delivered fake.sh unchanged"      "$DEV_FAKE_HASH_BEFORE" "$(sha256sum "$ROOT/work/fake.sh" | awk '{print $1}')"

summary "TOOL-TESTS" 0
