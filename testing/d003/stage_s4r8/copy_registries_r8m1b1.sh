#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1b1; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_registries_r8m1b1.sh -- copy small tables to registries directory (brief §7). New file.
set -eu

DEST="$REPO/checkpoints/p05/registries/s4r8/M1b/r8m1b1"
mkdir -p "$DEST"

FILES="PLAN_M1B_R8_M1b1.tsv RESULTS_M1B_R8_M1b1.tsv VERDICT_M1B_R8_M1b1.tsv CONSISTENCY_M1B_R8_M1b1.tsv F2_F3_DIFF_M1B_R8_M1b1.tsv COVERAGE_M1B_R8_M1b1.tsv ANOMALIES_M1B_R8_M1b1.tsv GATE_R8_M1b1_START.txt"

for f in $FILES; do
    if [ -f "$EV/$f" ]; then
        cp "$EV/$f" "$DEST/$f"
        sha_ev=$(sha256sum "$EV/$f" | cut -d' ' -f1)
        sha_dest=$(sha256sum "$DEST/$f" | cut -d' ' -f1)
        if [ "$sha_ev" != "$sha_dest" ]; then
            echo "ERROR: SHA mismatch copying $f" >&2
            exit 1
        fi
        echo "Copied $f: $sha_dest OK"
    else
        echo "WARNING: $EV/$f not found" >&2
    fi
done

# If GATE_R8_M1b1_END.txt exists, copy it too
if [ -f "$EV/GATE_R8_M1b1_END.txt" ]; then
    cp "$EV/GATE_R8_M1b1_END.txt" "$DEST/GATE_R8_M1b1_END.txt"
    sha_ev=$(sha256sum "$EV/GATE_R8_M1b1_END.txt" | cut -d' ' -f1)
    sha_dest=$(sha256sum "$DEST/GATE_R8_M1b1_END.txt" | cut -d' ' -f1)
    if [ "$sha_ev" != "$sha_dest" ]; then
        echo "ERROR: SHA mismatch copying GATE_R8_M1b1_END.txt" >&2
        exit 1
    fi
    echo "Copied GATE_R8_M1b1_END.txt: $sha_dest OK"
fi

cd "$DEST"
rm -f SHA256SUMS.txt
sha256sum *.tsv *.txt > SHA256SUMS.txt
echo "SHA256SUMS.txt generated in $DEST"
sha256sum -c SHA256SUMS.txt

cd "$EV"
rm -f SHA256SUMS.txt
find . -type f \( -name "*.tsv" -o -name "*.txt" -o -name "*.log" -o -name "*.out" \) | sort | xargs sha256sum > SHA256SUMS.txt
echo "Evidence SHA256SUMS.txt generated in $EV: $(wc -l < SHA256SUMS.txt) files"
