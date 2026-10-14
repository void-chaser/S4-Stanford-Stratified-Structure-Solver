REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# commit_rec_r8m1a3c_A.sh -- P05-S4 R8 M1a CONT2c A4: A-segment record commit (brief CONT2c A4).  New file.
# Steps: (1) endA gate last line FAILS=0; (2) copy the endA gate to registries/s4r8/M1a and cmp;
# (3) write SHA256SUMS_M1a3c_A.txt for the files added by this segment and check it with sha256sum -c;
# (4) recompute the two stored aggregates and compare with the endA record; (5) list git status and refuse any path outside
# checkpoints/p05/ and testing/d003/stage_s4r8/; add each path by name (no -A, no .); (6) commit with the brief's message;
# (7) write FINAL_GIT_R8_M1a3c_A.txt.  Runs only after gate8 endA FAILS=0.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/commit_rec_r8m1a3c_A.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "commit_rec_r8m1a3c_A: first argument must be p05-s4r8" >&2; exit 2; }
ENDA="$EV/GATE_R8_M1a3c_ENDA.txt"
DST=checkpoints/p05/registries/s4r8/M1a
FINAL="$EV/FINAL_GIT_R8_M1a3c_A.txt"
test ! -e "$FINAL" || { echo "commit_rec_r8m1a3c_A: REFUSED: exists (U17): $FINAL" >&2; exit 2; }
test -f "$ENDA" || { echo "commit_rec_r8m1a3c_A: REFUSED: endA gate missing" >&2; exit 2; }

# ---- (1) endA last line ----
[ "$(tail -n 1 "$ENDA")" = "FAILS=0" ] || { echo "commit_rec_r8m1a3c_A: REFUSED: endA last line is not FAILS=0" >&2; exit 2; }
[ "$(git rev-parse HEAD)" = e2589cbc2b470ae88286d582ee62699e7c0d9e4c ] || { echo "commit_rec_r8m1a3c_A: REFUSED: HEAD is not e2589cb" >&2; exit 2; }

# ---- (2) copy the endA gate and compare ----
cp "$ENDA" "$DST/GATE_R8_M1a3c_ENDA.txt" || { echo "commit_rec_r8m1a3c_A: COPY FAIL endA" >&2; exit 2; }
cmp -s "$ENDA" "$DST/GATE_R8_M1a3c_ENDA.txt" || { echo "commit_rec_r8m1a3c_A: CMP FAIL endA" >&2; exit 2; }

# ---- (3) SHA256SUMS_M1a3c_A.txt: all files added by this segment (A2 and A3 outputs plus the copies and the endA gate) ----
SUMS="$DST/SHA256SUMS_M1a3c_A.txt"
test ! -e "$SUMS" || { echo "commit_rec_r8m1a3c_A: REFUSED: exists (U17): $SUMS" >&2; exit 2; }
(cd "$DST" && for x in STRIP_EQUIV_R8_M1a.tsv GATE_R8_M1a3c_START.txt S4R7_RECHECK_GATE_R8_M1A3C_START.tsv APPEND_R8_M1a3c.txt GATE_R8_M1a3c_ENDA.txt; do sha256sum "$x"; done) > "$SUMS"
CHECK=$(cd "$DST" && sha256sum -c SHA256SUMS_M1a3c_A.txt 2>&1)
NOK=$(printf '%s\n' "$CHECK" | grep -c ': OK$')
NLINES=$(grep -c . "$SUMS")
[ "$NOK" = "$NLINES" ] || { echo "commit_rec_r8m1a3c_A: SHA256SUMS FAIL" >&2; printf '%s\n' "$CHECK" >&2; exit 2; }

# ---- (4) stored aggregates: recompute and compare with the endA record ----
AG_STAGE_H=$(git ls-files -o --exclude-standard -- testing/d003/stage_s4r8 | LC_ALL=C sort | grep -v -i r8m1a3c | xargs sha256sum | sha256sum | cut -d' ' -f1)
AG_M1A_H=$(git ls-files -o --exclude-standard -- checkpoints/p05/registries/s4r8/M1a | LC_ALL=C sort | grep -v -i -e m1a3c -e '/STRIP_EQUIV_R8_M1a\.tsv$' | xargs sha256sum | sha256sum | cut -d' ' -f1)
[ "$AG_STAGE_H" = c7010af5fb76af5b1502d786c4ed0025c08eaf2681d935761886c506886cacd1 ] || { echo "commit_rec_r8m1a3c_A: REFUSED: stage aggregate changed" >&2; exit 2; }
[ "$AG_M1A_H" = 907954c694d3bc2e4cf7a7b916025efe81d09beb346949af30f67439de2349bc ] || { echo "commit_rec_r8m1a3c_A: REFUSED: M1a aggregate changed" >&2; exit 2; }

# ---- (5) paths: every changed path must be under checkpoints/p05/ or testing/d003/stage_s4r8/ ----
PATHS=$(git status --porcelain --untracked-files=all | sed -e 's/^...//')
BAD=""
for p in $PATHS; do
    case "$p" in
        checkpoints/p05/*|testing/d003/stage_s4r8/*) ;;
        *) BAD="$BAD $p" ;;
    esac
done
[ -z "$BAD" ] || { echo "commit_rec_r8m1a3c_A: REFUSED: path outside allowed prefixes:$BAD" >&2; exit 2; }
for p in $PATHS; do
    git add -- "$p" || { echo "commit_rec_r8m1a3c_A: ADD FAIL $p" >&2; exit 2; }
done

# ---- (6) commit ----
MSG='P05-S4 R8 M1a records (cont1+cont2+cont2b, map v3 stopped at conditions 12/13): dbg strip equivalence closes E8-9, drivers, F2-F3 line map v3 stop record, gate7 end FAILS=1 kept as stop record (U169), new gate8; rulings U137-U175; errata to E8-52; M0 report wording (U137). awaiting user review'
git commit -q -m "$MSG" || { echo "commit_rec_r8m1a3c_A: COMMIT FAIL" >&2; exit 2; }

# ---- (7) final git record ----
{
    printf 'utc=%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    printf '== git log -3 --oneline\n'
    git log -3 --oneline
    printf '== git rev-parse HEAD HEAD^\n'
    git rev-parse HEAD HEAD^
    printf '== git log -1 --format=%%s\n'
    git log -1 --format=%s
    printf '== git status --short\n'
    git status --short
} > "$FINAL"
echo "commit_rec_r8m1a3c_A: committed -> $FINAL"
exit 0
