#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1b2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_r8m1b2.sh -- Copy small result tables to registries and generate checksums.
set -eu

REG_DIR="$REPO/checkpoints/p05/registries/s4r8/M1b/r8m1b2"
mkdir -p "$REG_DIR"

FILES="ENV_AUDIT_M1B_R8_M1b2.tsv ENV_AUDIT_M1C_R8_M1b2.tsv ROOTCAUSE_R8_M1b2.txt TIMING_CHECK_R8_M1b2.txt GATE_R8_M1b2_START.txt GATE_R8_M1b2_END.txt"

for f in $FILES; do
    test -f "$EV/$f" || { echo "Missing in EV: $f" >&2; exit 1; }
    cp -p "$EV/$f" "$REG_DIR/$f"
done

# Generate SHA256SUMS.txt in registries dir
cd "$REG_DIR"
sha256sum $FILES > SHA256SUMS.txt
sha256sum -c SHA256SUMS.txt

# Generate SHA256SUMS.txt in evidence dir covering non-binary files
cd "$EV"
find . -maxdepth 1 -type f ! -name "SHA256SUMS.txt" ! -name ".*" | sort | xargs sha256sum > SHA256SUMS.txt
sha256sum -c SHA256SUMS.txt

echo "copy_registries_r8m1b2: OK"
