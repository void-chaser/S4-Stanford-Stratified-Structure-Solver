REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_r8m1c3.sh -- P05-S4 R8 M1c3 record commit (brief 9.6). New file.
# Checks git status against the end allow list (refuses if any entry is not allowed), then stages the named paths only
# (no git add -A) and commits with the brief's subject line.  The subject is passed in as the first argument.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c3 -- sh testing/d003/stage_s4/commit_r8m1c3.sh "<commit subject>"
set -u
refuse() { echo "commit_r8m1c3: REFUSED: $1" >&2; exit 2; }
SUBJ=${1:-}
[ -n "$SUBJ" ] || refuse "commit subject required"
case "$SUBJ" in
    *"awaiting user review") ;;
    *) refuse "subject must end with 'awaiting user review'" ;;
esac
ALLOW="$REPO/testing/d003/stage_s4/gate_allow_r8m1c3_end.txt"
test -f "$ALLOW" || refuse "end allow list missing"
ST="$EV/tmp/commit_status_r8m1c3.txt"
git status --short -uall > "$ST"
bad=0
while IFS= read -r l; do
    [ -n "$l" ] || continue
    ok=no
    while IFS= read -r p; do
        case "$p" in ''|'#'*) continue ;; esac
        case "$l" in $p) ok=yes; break ;; esac
    done < "$ALLOW"
    if [ "$ok" != yes ]; then bad=$((bad + 1)); echo "NOT_ALLOWED: $l" >&2; fi
done < "$ST"
[ "$bad" -eq 0 ] || refuse "status has $bad entries not in the end allow list"
cd "$REPO" || refuse "cannot cd to repo"
git add -- checkpoints/p05/STATE.md \
    checkpoints/p05/registries/RULINGS.tsv \
    checkpoints/p05/registries/s4r8/ERRATA_8.txt \
    checkpoints/p05/P05_S4R8_M1C3_REPORT.md \
    checkpoints/p05/briefs/P05_S4R8_BRIEF_M1c3.md \
    checkpoints/p05/registries/s4r8/M1c/r8m1c3 \
    testing/d003/stage_s4/postcommit_r8m1c2.py || refuse "git add failed"
# the round's own scripts and gate files (names carry the r8m1c3 tag); globbed by the shell, not by git
for f in testing/d003/stage_s4/*r8m1c3*; do
    [ -e "$f" ] || continue
    git add -- "$f" || refuse "git add failed for $f"
done
git commit -m "$SUBJ" || refuse "git commit failed"
echo "commit_r8m1c3: committed"
exit 0
