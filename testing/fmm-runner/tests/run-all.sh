#!/bin/bash
# run-all.sh [run-id]
#
# Single entry point.  It records each stage's REAL exit status, propagates any
# failure to its own exit status, and still collects the remaining independent
# evidence.  A later successful command (sha256sum, tail, echo) can never mask
# an earlier failing stage because the status is accumulated in a file and used
# as the final exit code.
#
#   exit 0 = every stage passed, every case count/file/verdict/reason matched,
#            the mutants were all detected, and the manifests verified
#   exit 1 = at least one stage failed
#   exit 2 = usage / run id already exists (refuses to overwrite evidence)
#
# Re-running: pass a new run id, e.g.  bash tests/run-all.sh run-002
set -u
ROOT=$(cd "$(dirname "$0")/.." && pwd) || exit 2
cd "$ROOT" || exit 2

RUNID="${1:-run-001}"
WS="$ROOT/runs/$RUNID"

if [ -e "$WS" ]; then
  echo "REFUSING TO OVERWRITE: $WS already exists" >&2
  echo "pass a new run id: bash tests/run-all.sh <new-run-id>" >&2
  exit 2
fi
mkdir -p "$WS/evidence" "$WS/logs"
STATUS="$WS/stage-status.txt"
: > "$STATUS"

record() {  # record <stage> <rc>
  printf '%s rc=%s\n' "$1" "$2" | tee -a "$STATUS"
}

echo "run id:    $RUNID"
echo "workspace: $WS"
echo "started:   $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# ---------------------------------------------------------------- stage 1
bash tests/bootstrap-validate.sh "$WS" "$RUNID" > "$WS/logs/00-bootstrap.log" 2>&1
rc=$?; record bootstrap "$rc"
if [ "$rc" != 0 ]; then
  echo "PRECONDITIONS FAILED - stopping before dependent stages" | tee -a "$STATUS"
  cat "$WS/logs/00-bootstrap.log" >> "$STATUS"
  echo "TOTAL: FAILED (bootstrap rc=$rc)"
  exit 1
fi

# ---------------------------------------------------------------- stage 2
bash tests/direct-fake.sh "$WS" > "$WS/logs/01-direct.log" 2>&1
rc=$?; record direct "$rc"

# ---------------------------------------------------------------- stage 3
bash tests/matrix.sh "$WS" > "$WS/logs/02-matrix.log" 2>&1
rc=$?; record matrix "$rc"
# freeze a hash baseline of the normal matrix evidence, to prove afterwards
# that the mutation runs did not touch it.  Paths are absolute so the later
# verification does not depend on the current directory.
( cd "$WS" && find evidence/matrix -type f -print0 | sort -z | xargs -0 -r sha256sum ) \
  | sed "s|  evidence/|  $WS/evidence/|" > "$WS/evidence/matrix-hashes.before" 2>/dev/null
record matrix-evidence-freeze "$?"

# ---------------------------------------------------------------- stage 4
bash tests/regression.sh "$WS" > "$WS/logs/03-regression.log" 2>&1
rc=$?; record regression "$rc"

# ---------------------------------------------------------------- stage 5
bash tests/regression-new.sh "$WS" > "$WS/logs/04-regression-new.log" 2>&1
rc=$?; record regression-new "$rc"

# ---------------------------------------------------------------- stage 6
bash tests/mutants.sh "$WS" > "$WS/logs/05-mutants.log" 2>&1
rc=$?; record mutants "$rc"

# ---------------------------------------------------------------- stage 7
bash tests/fault-propagation.sh "$WS" > "$WS/logs/06-fault-propagation.log" 2>&1
rc=$?; record fault-propagation "$rc"

# ---------------------------------------------------------------- stage 8
# normal evidence must be byte-identical after the mutation stage
if sha256sum -c "$WS/evidence/matrix-hashes.before" > "$WS/logs/07-evidence-isolation.log" 2>&1; then
  record evidence-isolation 0
else
  record evidence-isolation 1
fi

# ---------------------------------------------------------------- stage 8
# The delivered artifacts must be unchanged by this run.  Absolute paths, so a
# bad path is a hard failure rather than a cwd-dependent silent pass.
#
# The frozen baseline covers exactly the two delivered device files and their
# pre-change byte copies.  The test scripts are deliberately NOT part of the
# frozen baseline: they are this round's tools, and a baseline over tests/ would
# mean that editing a test (a normal part of the work) reports as if the
# delivered runner had changed.  The run's own sources manifest still records
# the test hashes for the run in question.
bash tests/manifest-generate.sh "$WS/evidence/run-sources.sha256" \
  "$ROOT/work" "$ROOT/tests" "$ROOT/before" > "$WS/logs/08-run-sources.log" 2>&1
rc=$?; record run-sources-manifest "$rc"
if [ "$rc" = 0 ]; then
  bash tests/verify-manifest.sh "$ROOT/inputs.sha256" > "$WS/logs/09-input-verify.log" 2>&1
  rc=$?; record inputs-verify "$rc"
  # Freeze the delivered baseline on the first run, then require it unchanged.
  #
  # Creating the baseline is itself a step that can fail.  Its real rc is
  # recorded, and success is claimed only after the baseline exists, is
  # non-empty, and actually verifies.  A failed creation must NOT be recorded
  # as a created baseline, and must not let the run reach ALL STAGES PASSED.
  if [ -s "$ROOT/delivered-frozen.sha256" ]; then
    bash tests/verify-manifest.sh "$ROOT/delivered-frozen.sha256" > "$WS/logs/09-deliverable-verify.log" 2>&1
    rc=$?; record deliverable-verify "$rc"
  else
    bash tests/manifest-generate.sh "$ROOT/delivered-frozen.sha256" \
      "$ROOT/work" "$ROOT/before" >> "$WS/logs/09-deliverable-verify.log" 2>&1
    BASE_RC=$?
    record deliverable-baseline-created "$BASE_RC"
    if [ "$BASE_RC" != 0 ]; then
      echo "frozen delivered baseline creation FAILED (rc=$BASE_RC); baseline is NOT valid" \
        >> "$WS/logs/09-deliverable-verify.log"
      record deliverable-verify 1
    elif [ ! -s "$ROOT/delivered-frozen.sha256" ]; then
      echo "frozen delivered baseline creation reported success but produced no file; baseline is NOT valid" \
        >> "$WS/logs/09-deliverable-verify.log"
      record deliverable-verify 1
    else
      bash tests/verify-manifest.sh "$ROOT/delivered-frozen.sha256" \
        >> "$WS/logs/09-deliverable-verify.log" 2>&1
      rc=$?
      if [ "$rc" = 0 ]; then
        echo "frozen delivered baseline created and verified: delivered-frozen.sha256" \
          >> "$WS/logs/09-deliverable-verify.log"
      else
        echo "frozen delivered baseline created but does NOT verify (rc=$rc); baseline is NOT valid" \
          >> "$WS/logs/09-deliverable-verify.log"
      fi
      record deliverable-verify "$rc"
    fi
  fi
else
  record inputs-verify 1
  record deliverable-verify 1
fi

# ---------------------------------------------------------------- stage 9
# Per-run evidence manifest.
#
# Ordering note: the run's own status record (stage-status.txt) states whether
# the manifest verified.  Such a file cannot be hashed and then written to
# without invalidating its own recorded hash, so it is deliberately NOT part of
# the manifest; it is the run's mutable status log.  Every evidence file and
# every stage log IS manifested and verified byte-for-byte, and the manifest's
# own sha256 is recorded in the run directory afterwards.
bash tests/manifest-generate.sh "$WS/SHA256SUMS" \
  "$WS/evidence" "$WS/logs" > "$WS/logs/11-evidence-manifest.log" 2>&1
rc=$?; record evidence-manifest "$rc"
if [ "$rc" = 0 ]; then
  bash tests/verify-manifest.sh "$WS/SHA256SUMS" "$WS/evidence-verify.log"
  EVRC=$?
else
  EVRC=1
fi
printf 'evidence-verify rc=%s\n' "$EVRC" >> "$STATUS"
sha256sum "$WS/SHA256SUMS" > "$WS/manifest-sha256.txt"
printf 'stage-status.txt is intentionally unmanifested (it records the verification verdict)\n' \
  > "$WS/MANIFEST-NOTES.txt"

# ---------------------------------------------------------------- summary
echo
echo "=== stage results ($RUNID) ==="
cat "$STATUS"
echo
echo "=== suite summaries ==="
for f in 01-direct 02-matrix 03-regression 04-regression-new 05-mutants 06-fault-propagation; do
  [ -s "$WS/logs/$f.log" ] && tail -1 "$WS/logs/$f.log"
done

FAILED=$(awk -F'rc=' '$2 != 0 {n++} END {print n+0}' "$STATUS")
echo
if [ "$FAILED" = 0 ]; then
  echo "TOTAL ($RUNID): ALL STAGES PASSED"
  exit 0
fi
echo "TOTAL ($RUNID): FAILED stages=$FAILED"
echo "failing stages:"
awk -F'rc=' '$2 != 0 {print "  " $1 " rc=" $2}' "$STATUS"
exit 1
