#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate_r8.sh -- P05-S4 R8 opening (start) and closing (end) gate, brief section 0.1.
# Writes one record file under $EV/ only.  Every check is one PASS or FAIL line.  The script exits 0 after
# writing the file, so the verdict is read from the FAILS= line of that file.
#   start: sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate_r8.sh p05-s4r8 GATE_R8_M0.txt start <tmp_count> <tmp_sha256>
#   end:   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/gate_r8.sh p05-s4r8 GATE_R8_M0_END.txt end <tmp_count> <tmp_sha256> <start_tmp_count> <start_tmp_sha256>
# The temp-directory snapshot is taken by the caller with an inline read-only command and passed in as arguments.
set -u
OUT="$EV/${2:?out name}"
MODE=${3:?start or end}
TC=${4:?tmp count}
TS=${5:?tmp sha256}
test ! -e "$OUT" || { echo "gate_r8: REFUSED exists: $OUT" >&2; exit 2; }
: > "$OUT"
FAILS=0
check() {
    if [ "$2" = "$3" ]; then R=PASS; else R=FAIL; FAILS=$((FAILS + 1)); fi
    printf '%s\t%s\texpected=%s\tactual=%s\n' "$R" "$1" "$2" "$3" >> "$OUT"
}
printf '# P05-S4 R8 gate (%s), utc=%s\n' "$MODE" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$OUT"
check HEAD 3ab56801e697910bdff9fbe6056807c2e41841b5 "$(git rev-parse HEAD)"
check S4_TREE_HEAD 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse HEAD:S4)"
check S4_TREE_8d8202a 6cff923a02baf19e01966b2339755cbf3a5deeef "$(git rev-parse 8d8202a:S4)"
check S4_TREE_a07b5ac e124925f5b242486a913b813fa181664f665b048 "$(git rev-parse a07b5ac:S4)"
check S4_DIFF_a07b5ac_8d8202a "S4/S4.cpp S4/fmm/fmm_FFT.cpp S4/fmm/fmm_kottke.cpp S4/pattern/pattern.c " "$(git diff --name-only a07b5ac 8d8202a -- S4/ | sort | tr '\n' ' ')"
check JUDGE_SHA256 d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb "$(sha256sum testing/d003/judge_d003.py | cut -d' ' -f1)"
check REGISTRY_S3R4C3_D_SHA256 a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5 "$(sha256sum checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv | cut -d' ' -f1)"
if [ "$MODE" = start ]; then WANT_ST="?? checkpoints/p05/briefs/P05_S4R8_BRIEF_M0.md"; else WANT_ST=""; fi
check GIT_STATUS_EXCEPT_R8_SCRIPTS "$WANT_ST" "$(git status --short | grep -v 'testing/d003/stage_s4r8/')"
check S3R4C5_SHA256SUMS_non_OK 0 "$(cd checkpoints/p05/registries/s3r4c5 && sha256sum -c SHA256SUMS.txt 2>&1 | grep -v ': OK$' | grep -c .)"
for F in checkpoints/p05/registries/s4r7/SHA256SUMS*.txt; do
    N=$(basename "$F")
    check "S4R7_$N" 0 "$(cd checkpoints/p05/registries/s4r7 && sha256sum -c "$N" 2>&1 | grep -v ': OK$' | grep -c .)"
done
if [ -n "${6:-}" ]; then
    check TMP_COUNT_VS_START "${6}" "$TC"
    check TMP_SHA256_VS_START "${7:-}" "$TS"
fi
printf 'tmp_count=%s\ttmp_sha256=%s\n' "$TC" "$TS" >> "$OUT"
printf 'FAILS=%s\n' "$FAILS" >> "$OUT"
echo "gate_r8: $MODE FAILS=$FAILS -> $OUT"
exit 0
