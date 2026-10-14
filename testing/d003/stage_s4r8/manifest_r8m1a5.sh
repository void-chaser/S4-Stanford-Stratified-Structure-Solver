#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# manifest_r8m1a5.sh -- writes $EV/SHA256SUMS.txt over the round's evidence files (brief section 6.1).  New file.
# Covers every non-binary file directly in $EV (not tmp/, not the manifest itself).  The file list is sorted.
# Refuses to overwrite an existing manifest (U17).
set -u
OUT="$EV/SHA256SUMS.txt"
test ! -e "$OUT" || { echo "manifest: exists (U17)" >&2; exit 2; }
cd "$EV" || exit 2
{
  for f in $(ls -1 | sort); do
    case "$f" in
        SHA256SUMS.txt|tmp|safe_run.log) continue ;;
    esac
    test -f "$f" || continue
    sha256sum "$f"
  done
} > "$OUT"
echo "manifest_r8m1a5: $(wc -l < "$OUT") lines -> $OUT"
exit 0
