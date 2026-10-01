#!/bin/bash
# run-case.sh <casedir> <fake> <variant> <type> <branch> <hits> <outdir>
# Runs one case against an explicit runner/fake pair in an explicit directory.
# The caller decides which copy to target, so no case ever runs against the
# delivered work/ directory or writes into another suite's evidence tree.
set -u
ulimit -c 0
casedir="$1"; fake="$2"; variant="$3"; type="$4"; br="$5"; hits="$6"; out="$7"
mkdir -p "$out"
( ulimit -c 0; timeout 2 "$fake" "$variant" "$br" ) > "$out/fake.out" 2>&1
echo "$?" > "$out/fake.exit"
log="$casedir/logs/one-$type-$br-4-scratch-1-1-1-$variant.log"
rm -f "$log"
( cd "$casedir" && ulimit -c 0 && S4FMM_FAKE="$variant" S4FMM_TIMEOUT=2 \
    "$casedir/run-one.sh" "$type" "$br" 4 scratch 1 1 1 "$hits" ) > "$out/runner.out" 2>&1
echo "$?" > "$out/runner.exit"
cp "$log" "$out/driver.log" 2>/dev/null || : > "$out/driver.log"
printf '%s\n' "$variant" > "$out/variant"
printf '%s\n' "$type"    > "$out/type"
printf '%s\n' "$hits"    > "$out/hits"
printf '%s\n' "$br"      > "$out/branch"
