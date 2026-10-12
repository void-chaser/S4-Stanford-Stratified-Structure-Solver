#!/bin/sh
# gate_c2.sh -- P05-S3R4 CONT2 gate record (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/gate_c2.sh START <tmp_entries> <tmp_listing_sha256>
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/gate_c2.sh END <tmp_entries> <tmp_listing_sha256>
#
# <tmp_entries> and <tmp_listing_sha256> are the read-only snapshot of the /tmp top level, taken by the caller
# (ls -A | wc -l and ls -A | sha256sum). This script only reads the repository and writes into $EV.
# START -> $EV/GATE_CONT2.txt ; END -> $EV/GATE_CONT2_END.txt
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
PHASE=${1:?"usage: gate_c2.sh START|END entries sha"}
TC=${2:?"tmp entries"}
TS=${3:?"tmp listing sha256"}
if [ "$PHASE" = START ]; then OUT="$EV/GATE_CONT2.txt"; else OUT="$EV/GATE_CONT2_END.txt"; fi
{
printf 'phase\t%s\n' "$PHASE"
printf 'utc\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf 'HEAD\t%s\n' "$(git rev-parse HEAD)"
printf 'HEAD:S4\t%s\n' "$(git rev-parse HEAD:S4)"
printf 'judge_d003_sha256\t%s\n' "$(sha256sum testing/d003/judge_d003.py | cut -d' ' -f1)"
printf 'tmp_top_entries\t%s\n' "$TC"
printf 'tmp_top_listing_sha256\t%s\n' "$TS"
printf 'stage_s3r4c1_ls_d:\n'
ls -d testing/d003/stage_s3r4c1
printf 'stage_s3r4c1_entries\t%s\n' "$(ls -A testing/d003/stage_s3r4c1 | wc -l)"
printf 'git_status_short:\n'
git status --short
printf 'git_log_3:\n'
git log -3 --oneline
} > "$OUT" 2>&1
echo "gate_c2 $PHASE written: $OUT"
exit 0
