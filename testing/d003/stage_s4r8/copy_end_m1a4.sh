#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# copy_end_m1a4.sh -- copy end gate files to registries/s4r8/M1a/ and create SHA256SUMS_M1a4_END.txt.  New file.
# Usage (through safe_run):
#   sh testing/d003/stage_s4r8/copy_end_m1a4.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "copy_end_m1a4: first arg must be p05-s4r8" >&2; exit 2; }

REG="$REPO/checkpoints/p05/registries/s4r8/M1a"
test -d "$REG" || { echo "copy_end_m1a4: registry dir missing" >&2; exit 2; }

ENDFILES="GATE_R8_M1a4_END.txt S4R7_RECHECK_GATE_R8_M1A4_END.tsv"

for f in $ENDFILES; do
    src="$EV/$f"
    dst="$REG/$f"
    test -f "$src" || { echo "copy_end_m1a4: source missing: $src" >&2; exit 2; }
    if [ -e "$dst" ]; then
        cmp -s "$src" "$dst" || { echo "copy_end_m1a4: differs: $dst" >&2; exit 2; }
    else
        cp "$src" "$dst" || { echo "copy_end_m1a4: cp failed: $f" >&2; exit 2; }
        cmp -s "$src" "$dst" || { echo "copy_end_m1a4: cmp failed: $f" >&2; exit 2; }
        echo "copy_end_m1a4: copied $f"
    fi
done

MAN="$REG/SHA256SUMS_M1a4_END.txt"
test ! -e "$MAN" || { echo "copy_end_m1a4: manifest exists: $MAN" >&2; exit 2; }

(
    cd "$REG"
    for f in $ENDFILES; do
        sha256sum "$f"
    done
) > "$MAN"

(
    cd "$REG"
    sha256sum -c SHA256SUMS_M1a4_END.txt
) || { echo "copy_end_m1a4: check failed" >&2; exit 2; }

echo "copy_end_m1a4: end files copied and SHA256SUMS_M1a4_END.txt verified OK"
exit 0
