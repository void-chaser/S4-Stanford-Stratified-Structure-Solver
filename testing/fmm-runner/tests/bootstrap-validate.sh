#!/bin/bash
# Input integrity and syntax preconditions.
#   bootstrap-validate.sh <workspace> <runid>
#
# Fails (non-zero), and refuses to prepare the run workspace, if the two input
# files do not match the recorded hashes, if the input manifest does not
# verify, or if either delivered script fails a syntax check.  Because the
# prepared runner copies are what every dependent stage runs against, refusing
# to prepare them is what blocks the dependent stages.
cd "$(dirname "$0")/.." || exit 1
ulimit -c 0
. tests/lib.sh

WS="$1"; RUNID="$2"
if [ -z "$WS" ] || [ -z "$RUNID" ]; then
  echo "usage: bootstrap-validate.sh <workspace> <runid>" >&2
  exit 2
fi
# the workspace itself is created first, so a failure leaves an empty workspace
# with no prepared runner copies in it
mkdir -p "$WS" || { echo "cannot create workspace: $WS" >&2; exit 1; }

head1 "input integrity and syntax preconditions"
say "run id:    $RUNID"
say "workspace: $WS"

blocked() {  # blocked <reason>
  echo
  say "PRECONDITIONS: BLOCKED - $1"
  say "run workspace was not prepared; dependent stages must not start"
  exit 1
}

# ---- delivered inputs against the frozen input manifest ---------------------
if [ ! -s inputs.sha256 ]; then
  assert_eq "input manifest present" yes no
  blocked "inputs.sha256 is missing or empty"
fi
assert_eq "input manifest present" yes yes
if ! sha256sum -c inputs.sha256 > "$WS/input-verify.out" 2>&1; then
  say "  FAIL  input manifest verification"
  sed 's/^/        /' "$WS/input-verify.out"
  LIBN_CHECKS=$((LIBN_CHECKS + 1))
  LIBN_FAIL=$((LIBN_FAIL + 1))
  blocked "input manifest verification failed"
fi
say "  ok    input manifest verification ($(grep -c ': OK$' "$WS/input-verify.out") entries)"
LIBN_CHECKS=$((LIBN_CHECKS + 1))

# ---- the two delivered files, explicitly -----------------------------------
for f in work/run-one.sh work/fake.sh; do
  want=$(grep " $f\$" inputs.sha256 | awk '{print $1}')
  got=$(sha256sum "$f" | awk '{print $1}')
  assert_eq "delivered $f hash" "$want" "$got"
  if [ "$want" != "$got" ]; then
    blocked "delivered $f does not match its recorded hash"
  fi
done

# ---- syntax check both delivered scripts -----------------------------------
if ! bash -n work/run-one.sh 2>"$WS/syntax-run-one.out"; then
  assert_eq "delivered run-one.sh syntax" ok "FAILED"
  sed 's/^/        /' "$WS/syntax-run-one.out"
  blocked "delivered run-one.sh fails its syntax check"
fi
assert_eq "delivered run-one.sh syntax" ok ok
if ! bash -n work/fake.sh 2>"$WS/syntax-fake.out"; then
  assert_eq "delivered fake.sh syntax" ok "FAILED"
  sed 's/^/        /' "$WS/syntax-fake.out"
  blocked "delivered fake.sh fails its syntax check"
fi
assert_eq "delivered fake.sh syntax" ok ok

# ---- prepare the run workspace as byte copies ------------------------------
# Reached only when every precondition passed.  cp -p preserves content
# exactly; the delivered work/ files are left untouched.
mkdir -p "$WS/work/logs" "$WS/work-operator/logs"
cp -p work/run-one.sh "$WS/work/run-one.sh"
cp -p work/fake.sh    "$WS/work/fake.sh"
cp -p work/run-one.sh "$WS/work-operator/run-one.sh"
cp -p work/fake.sh    "$WS/work-operator/fake.sh"
chmod +x "$WS/work/run-one.sh" "$WS/work/fake.sh"
chmod +x "$WS/work-operator/run-one.sh" "$WS/work-operator/fake.sh"

assert_eq "run workspace runner is a byte copy" \
  "$(sha256sum work/run-one.sh | awk '{print $1}')" \
  "$(sha256sum "$WS/work/run-one.sh" | awk '{print $1}')"
assert_eq "operator workspace runner is a byte copy" \
  "$(sha256sum work/run-one.sh | awk '{print $1}')" \
  "$(sha256sum "$WS/work-operator/run-one.sh" | awk '{print $1}')"

echo
say "PRECONDITIONS: OK  checks=$LIBN_CHECKS"
exit 0
