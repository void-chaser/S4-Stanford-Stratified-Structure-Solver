REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_rec_r8m1a3c_B.sh -- P05-S4 R8 M1a CONT2c section 6: B-segment record commit.  New file.  Runs only after gate8 endB FAILS=0.
# Steps: (1) endB last line FAILS=0 and HEAD still equals HEAD_B recorded in the startB gate; (2) copy the endB gate to
# registries/s4r8/M1a and cmp; (3) write SHA256SUMS_M1a3c_B_END.txt for the endB copy and check it with sha256sum -c
# (SHA256SUMS_M1a3c_B.txt is not touched); (4) list git status, refuse any path outside checkpoints/p05/ and
# testing/d003/stage_s4r8/, add each path by name (no -A, no .); (5) commit with the message of section 6 (or the stopped form);
# (6) write FINAL_GIT_R8_M1a3c_B.txt.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/commit_rec_r8m1a3c_B.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "commit_rec_r8m1a3c_B: first argument must be p05-s4r8" >&2; exit 2; }
ENDB="$EV/GATE_R8_M1a3c_ENDB.txt"
STARTB="$EV/GATE_R8_M1a3c_STARTB.txt"
DST=checkpoints/p05/registries/s4r8/M1a
FINAL="$EV/FINAL_GIT_R8_M1a3c_B.txt"
SUMS="$DST/SHA256SUMS_M1a3c_B_END.txt"
test ! -e "$FINAL" || { echo "commit_rec_r8m1a3c_B: REFUSED: exists (U17): $FINAL" >&2; exit 2; }
test ! -e "$SUMS" || { echo "commit_rec_r8m1a3c_B: REFUSED: exists (U17): $SUMS" >&2; exit 2; }
test -f "$ENDB" || { echo "commit_rec_r8m1a3c_B: REFUSED: endB gate missing" >&2; exit 2; }

# ---- (1) endB last line and HEAD = HEAD_B ----
[ "$(tail -n 1 "$ENDB")" = "FAILS=0" ] || { echo "commit_rec_r8m1a3c_B: REFUSED: endB last line is not FAILS=0" >&2; exit 2; }
HEAD_B=$(grep '^RECORD	HEAD_B	' "$STARTB" | cut -f3 | sed -e 's/^value=//')
[ "$(git rev-parse HEAD)" = "$HEAD_B" ] || { echo "commit_rec_r8m1a3c_B: REFUSED: HEAD is not HEAD_B" >&2; exit 2; }

# ---- (2) copy the endB gate and compare ----
cp "$ENDB" "$DST/GATE_R8_M1a3c_ENDB.txt" || { echo "commit_rec_r8m1a3c_B: COPY FAIL endB" >&2; exit 2; }
cmp -s "$ENDB" "$DST/GATE_R8_M1a3c_ENDB.txt" || { echo "commit_rec_r8m1a3c_B: CMP FAIL endB" >&2; exit 2; }

# ---- (3) SHA256SUMS_M1a3c_B_END.txt: the endB copy only; check with sha256sum -c ----
(cd "$DST" && sha256sum GATE_R8_M1a3c_ENDB.txt) > "$SUMS"
(cd "$DST" && sha256sum -c SHA256SUMS_M1a3c_B_END.txt) > "$EV/tmp/sums_b_end_check.txt" 2>&1
[ "$(grep -c ': OK$' "$EV/tmp/sums_b_end_check.txt")" = 1 ] || { echo "commit_rec_r8m1a3c_B: SHA256SUMS_M1a3c_B_END FAIL" >&2; exit 2; }

# ---- (4) paths: every changed path must be under checkpoints/p05/ or testing/d003/stage_s4r8/ ----
PATHS=$(git status --porcelain --untracked-files=all | sed -e 's/^...//')
BAD=""
for p in $PATHS; do
    case "$p" in
        checkpoints/p05/*|testing/d003/stage_s4r8/*) ;;
        *) BAD="$BAD $p" ;;
    esac
done
[ -z "$BAD" ] || { echo "commit_rec_r8m1a3c_B: REFUSED: path outside allowed prefixes:$BAD" >&2; exit 2; }
for p in $PATHS; do
    git add -- "$p" || { echo "commit_rec_r8m1a3c_B: ADD FAIL $p" >&2; exit 2; }
done

# ---- (5) commit (section 6 message; the stopped form is not used: no stop) ----
MSG='P05-S4 R8 M1a cont2c: F2-F3 line map v3c (attribute-aware parser with driver self-check, used_in_m1 BP_LINE/REGISTRY_ONLY/NO without self-reference, EXPECT parse guard); call-sequence map deferred to cont3a (U166). awaiting user review'
git commit -q -m "$MSG" || { echo "commit_rec_r8m1a3c_B: COMMIT FAIL" >&2; exit 2; }

# ---- (6) final git record ----
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '== git log -3 --oneline\n'
    git log -3 --oneline
    printf '== git rev-parse HEAD HEAD^ HEAD^^\n'
    git rev-parse HEAD HEAD^ HEAD^^
    printf '== git log -1 --format=%%s\n'
    git log -1 --format=%s
    printf '== git status --short\n'
    git status --short
} > "$FINAL"
echo "commit_rec_r8m1a3c_B: committed -> $FINAL"
exit 0
