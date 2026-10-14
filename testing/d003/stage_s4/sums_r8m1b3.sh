#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1b3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# sums_r8m1b3.sh -- write SHA256SUMS.txt for the evidence dir and for the registries copy. New file.
# Usage: sh sums_r8m1b3.sh evidence|registry
set -u
MODE=${1:-}
case "$MODE" in
    evidence)
        cd "$EV" || exit 2
        ( for f in $(ls -A | sort); do
            case "$f" in
                SHA256SUMS.txt|tmp) continue ;;
            esac
            [ -f "$f" ] && sha256sum "$f"
          done
          for f in $(ls -A tmp | sort); do
            sha256sum "tmp/$f"
          done ) > "$EV/SHA256SUMS.txt"
        ;;
    registry)
        D="$REPO/checkpoints/p05/registries/s4r8/M1b/r8m1b3"
        cd "$D" || exit 2
        ( for f in $(ls -A | sort); do
            case "$f" in
                SHA256SUMS.txt) continue ;;
            esac
            sha256sum "$f"
          done ) > "$D/SHA256SUMS.txt"
        ;;
    *) echo "mode must be evidence or registry" >&2; exit 2 ;;
esac
echo "wrote $MODE SHA256SUMS"
