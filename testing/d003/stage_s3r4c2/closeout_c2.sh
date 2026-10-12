#!/bin/sh
# closeout_c2.sh -- P05-S3R4 CONT2 closeout: end gate record and evidence SHA256SUMS (new file).
#
#   sh testing/d003/safe_run.sh p05-s3r4c2 -- sh testing/d003/stage_s3r4c2/closeout_c2.sh
#
# Writes $EV/SHA256SUMS.txt over all non-binary evidence files (*.txt *.tsv *.md *.log *.gdb *.sh), except
# safe_run.log, which is listed separately as "appended after the manifest" and is not checked.
# Binary files (libraries, drivers, build objects) are not listed.
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
cd "$EV" || exit 2
find . -path ./tmp -prune -o -path ./drivers -prune -o -path ./c_poly -prune -o -path ./c_poly_run2 -prune -o -path ./a_c2 -prune -o -path ./build -prune -o -path ./build_f3 -prune -o \( -type f \( -name '*.txt' -o -name '*.tsv' -o -name '*.md' -o -name '*.gdb' -o -name '*.sh' -o -name '*.log' -o -name '*.tsv' \) -print \) \
    | grep -v '^./safe_run.log$' | sort > "$EV/tmp/evlist.txt"
xargs sha256sum < "$EV/tmp/evlist.txt" > "$EV/SHA256SUMS.txt"
{
printf '# safe_run.log is appended after this manifest and is NOT part of the check (listed separately).\n'
printf 'appended_after_manifest\tsafe_run.log\tlines=%s\n' "$(wc -l < "$EV/safe_run.log")"
} >> "$EV/SHA256SUMS.txt"
echo "closeout_c2: manifest written with $(wc -l < "$EV/tmp/evlist.txt") entries"
exit 0
