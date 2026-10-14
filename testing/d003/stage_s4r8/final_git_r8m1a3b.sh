REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# final_git_r8m1a3b.sh -- P05-S4 R8 M1a CONT2b section 6: record the git state after the round (read only, git commands only).  New file.
# Writes $EV/FINAL_GIT_R8_M1a3b.txt (refused if it exists, U17).  If nothing was committed, the file says so.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/final_git_r8m1a3b.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "final_git_r8m1a3b: first argument must be p05-s4r8" >&2; exit 2; }
OUT="$EV/FINAL_GIT_R8_M1a3b.txt"
test ! -e "$OUT" || { echo "final_git_r8m1a3b: REFUSED: exists (U17): $OUT" >&2; exit 2; }
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '== git log -3 --oneline\n'
    git log -3 --oneline
    printf '== git rev-parse HEAD^\n'
    git rev-parse HEAD^
    printf '== git log -1 --format=%%s\n'
    git log -1 --format=%s
    printf '== git status --short\n'
    git status --short
    printf '== note\n'
    printf 'COMMIT_MADE=no (end gate FAILS=1; see GATE_R8_M1a3b_END.txt and report section 2.1; U158)\n'
} > "$OUT"
echo "final_git_r8m1a3b: -> $OUT"
exit 0
