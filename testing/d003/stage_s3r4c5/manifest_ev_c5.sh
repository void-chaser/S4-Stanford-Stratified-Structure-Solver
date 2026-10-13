REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# manifest_ev_c5.sh -- SHA256SUMS.txt for $EV (AGENTS section 7.2): every non-binary evidence file of p05-s3r4c5.
# Excludes SHA256SUMS.txt itself and safe_run.log (appended log; listed in the note file, not verified).
# Runs the check from inside $EV.  Refuses to overwrite.
set -u
test -e "$EV/SHA256SUMS.txt" && { echo "REFUSED: exists $EV/SHA256SUMS.txt"; exit 2; }
cd "$EV" || exit 2
find . -type f ! -name SHA256SUMS.txt ! -name safe_run.log | sed 's|^\./||' | LC_ALL=C sort > "$EV/tmp/manifest_list_c5.txt"
xargs -d '\n' sha256sum < "$EV/tmp/manifest_list_c5.txt" > "$EV/SHA256SUMS.txt"
echo "lines=$(wc -l < "$EV/SHA256SUMS.txt")"
sha256sum -c "$EV/SHA256SUMS.txt" > "$EV/tmp/manifest_check_c5.txt" 2>&1
echo "check rc=$?"
{
  echo "# SHA256SUMS_NOTE_C5 -- note on SHA256SUMS.txt (p05-s3r4c5, CONT5)."
  echo "safe_run.log: appended after the manifest; NOT part of the manifest; not verified (AGENTS section 7.2)."
  echo "SHA256SUMS.txt: itself excluded from the manifest."
  echo "drivers and libraries are not in \$EV; their hashes are in BINARIES_C3.tsv (sha256 recorded, not copied into git)."
} > "$EV/SHA256SUMS_NOTE_C5.txt"
echo "note written"
