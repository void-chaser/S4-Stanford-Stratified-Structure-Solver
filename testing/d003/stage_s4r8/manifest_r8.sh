#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# manifest_r8.sh -- P05-S4 R8 M0 closing: SHA256SUMS.txt of the round evidence (AGENTS section 7 item 2).  New file.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/manifest_r8.sh p05-s4r8
# Covered (text and logs only; binaries and source trees are excluded, brief section 6):
#   $EV/*.txt, $EV/*.tsv                               top level
#   $EV/build_r8/*.tsv, $EV/build_r8/build-*.log        top level
#   $EV/build_r8/seam_plain/build-*.log                 seam build logs
#   $EV/seam_r8/*.txt, $EV/seam_r8/*.log, $EV/seam_r8/diff_F3_*.raw   apply reports and logs
#   $EV/drivers_r8/*/build.stdout                       link logs
#   $EV/noinject_r8/run1/*/*/*                          dump files and stdout/stderr of the no-injection runs (depth 3)
# Excluded: trees/, build_r8/*/ (copies and libraries), seam_r8/F3-*/ (source trees), drivers_r8/*/driver (binaries),
# tmp/, safe_run.log, SHA256SUMS.txt itself.  The excluded classes and their file counts are written to
# SHA256SUMS_EXCLUDED_R8_M0.txt.  Output: $EV/SHA256SUMS.txt (new, refused if it exists).
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "manifest_r8: first argument must be p05-s4r8" >&2; exit 2; }
test ! -e "$EV/SHA256SUMS.txt" || { echo "manifest_r8: REFUSED exists: SHA256SUMS.txt" >&2; exit 2; }
test ! -e "$EV/SHA256SUMS_EXCLUDED_R8_M0.txt" || { echo "manifest_r8: REFUSED exists: SHA256SUMS_EXCLUDED_R8_M0.txt" >&2; exit 2; }
LIST="$EV/tmp/manifest_list_r8.txt"
{
    find "$EV" -maxdepth 1 -type f \( -name '*.txt' -o -name '*.tsv' \)
    find "$EV/build_r8" -maxdepth 1 -type f \( -name '*.tsv' -o -name 'build-*.log' \)
    find "$EV/build_r8/seam_plain" -maxdepth 1 -type f -name 'build-*.log'
    find "$EV/seam_r8" -maxdepth 1 -type f \( -name '*.txt' -o -name '*.log' -o -name 'diff_F3_*.raw' \)
    find "$EV/drivers_r8" -mindepth 2 -maxdepth 2 -type f -name 'build.stdout'
    find "$EV/noinject_r8/run1" -mindepth 3 -maxdepth 3 -type f
} | LC_ALL=C sort > "$LIST"
# excluded: safe_run.log and the manifest itself are not listed above; count the excluded classes for the record
EXCL="$EV/SHA256SUMS_EXCLUDED_R8_M0.txt"
{
    printf '# SHA256SUMS_EXCLUDED_R8_M0.txt -- classes excluded from SHA256SUMS.txt (brief section 6).  Counts at the time of the manifest.\n'
    printf 'class\tcount\n'
    printf 'trees/ (exported source trees)\t%s\n' "$(find "$EV/trees" -type f | wc -l)"
    printf 'build_r8/ copies and libraries (not build-*.log, not *.tsv at top level)\t%s\n' "$(find "$EV/build_r8" -mindepth 2 -type f ! -name 'build-*.log' | wc -l)"
    printf 'seam_r8/F3-*/ source trees\t%s\n' "$(find "$EV/seam_r8/F3-seamF" "$EV/seam_r8/F3-fmmret" -type f | wc -l)"
    printf 'drivers_r8/*/driver (binaries; sha256 in DRIVERS_R8.tsv)\t%s\n' "$(find "$EV/drivers_r8" -name driver -type f | wc -l)"
    printf 'tmp/ (round temporary directory)\t%s\n' "$(find "$EV/tmp" -type f | wc -l)"
    printf 'safe_run.log (safe_run call log)\t1\n'
    printf 'noinject_r8 runs other than run1\t%s\n' "$(find "$EV/noinject_r8" -mindepth 1 -maxdepth 1 ! -name run1 | wc -l)"
} > "$EXCL"
# the manifest: sha256 of every listed file, path relative to the evidence directory
{
    while read -r f; do
        rel=${f#"$EV"/}
        h=$(sha256sum "$f" | cut -d' ' -f1)
        printf '%s  %s\n' "$h" "$rel"
    done < "$LIST"
} > "$EV/SHA256SUMS.txt"
echo "manifest_r8: listed $(wc -l < "$LIST") files -> SHA256SUMS.txt; excluded classes -> SHA256SUMS_EXCLUDED_R8_M0.txt"
exit 0
