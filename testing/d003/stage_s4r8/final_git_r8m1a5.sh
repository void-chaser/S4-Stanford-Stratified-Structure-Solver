#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# final_git_r8m1a5.sh -- writes the git record that audit3 report section 12 promised but did not contain (E8-69(3)).  New file.
# Mode PRE  : writes $EV/FINAL_GIT_R8_M1a4AUDIT3_POST.txt  (git log -3 --oneline and git status --short, at the time of the call).
# Mode POST : writes $EV/FINAL_GIT_R8_M1a5.txt            (the same after the round's record commit).
# Both files must not exist (U17).  Read-only git commands only.
set -u
MODE=${1:-}
case "$MODE" in
    PRE) OUT="$EV/FINAL_GIT_R8_M1a4AUDIT3_POST.txt" ;;
    POST) OUT="$EV/FINAL_GIT_R8_M1a5.txt" ;;
    *) echo "final_git: mode must be PRE or POST" >&2; exit 2 ;;
esac
test ! -e "$OUT" || { echo "final_git: exists (U17): $OUT" >&2; exit 2; }
{
  printf '# git record (%s), utc=%s\n' "$MODE" "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  printf '## git log -3 --oneline\n'
  git log -3 --oneline
  printf '## git status --short\n'
  git status --short
  printf '## end\n'
} > "$OUT"
echo "final_git_r8m1a5: $MODE -> $OUT"
exit 0
