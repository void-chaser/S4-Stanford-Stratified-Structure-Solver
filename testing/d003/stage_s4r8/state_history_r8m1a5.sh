#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# state_history_r8m1a5.sh -- writes the verbatim text of the STATE sections that CONT3b1 compacts into
# checkpoints/p05/registries/s4r8/M1a/STATE_HISTORY_R8_M1a5.md (brief section 4).  New file.
# The source is the STATE.md of the start-gate baseline (HEAD abf3e42), read with git show (read only), so the copy
# is exact and independent of the edit.  The output is append-only and must not exist (U17).
set -u
OUT="$REPO/checkpoints/p05/registries/s4r8/M1a/STATE_HISTORY_R8_M1a5.md"
test ! -e "$OUT" || { echo "state_history: exists (U17)" >&2; exit 2; }
SRC="$EV/tmp/STATE_BASE_abf3e42.md"
git show "abf3e420f5ba3600e079ecf213612bc1fc2a0aad:checkpoints/p05/STATE.md" > "$SRC" || exit 2
[ "$(sha256sum "$SRC" | cut -d' ' -f1)" = "0412369e148a045862403446ba59161983b33e71e8d84e9187b43d7489de59d4" ] || { echo "state_history: base STATE sha mismatch" >&2; exit 2; }
{
  printf '# STATE_HISTORY_R8_M1a5 -- verbatim text of P05/STATE.md sections removed or rewritten by CONT3b1 (brief section 4)\n'
  printf '# Source: checkpoints/p05/STATE.md at HEAD abf3e42 (sha256 0412369e148a045862403446ba59161983b33e71e8d84e9187b43d7489de59d4).\n'
  printf '# Append-only.  Text is copied exactly; it is not rewritten.  Written by testing/d003/stage_s4r8/state_history_r8m1a5.sh.\n\n'
  printf '## Section 1 (current position, previous rows), lines 5-17\n\n'
  sed -n '5,17p' "$SRC"
  printf '\n## Section 2 (key numbers), lines 19-35\n\n'
  sed -n '19,35p' "$SRC"
  printf '\n## Section 3 (open questions), lines 36-62\n\n'
  sed -n '36,62p' "$SRC"
  printf '\n## Section 4 (evidence locations), lines 64-66\n\n'
  sed -n '64,66p' "$SRC"
} > "$OUT"
echo "state_history_r8m1a5: wrote $OUT lines $(wc -l < "$OUT")"
exit 0
