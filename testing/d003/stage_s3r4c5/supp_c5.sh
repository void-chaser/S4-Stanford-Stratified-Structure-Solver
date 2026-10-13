REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# supp_c5.sh -- CONT5 section 3.1: complete the CONT3 deliverables by read-only computation (U120).
# Writes only to $EV.  Every output is refused if it already exists.  diff rc=1 means "differences found", not failure.
set -u
C3EV="$REPO/checkpoints/p05/evidence/p05-s3r4c3"
ref() { test -e "$1" && { echo "REFUSED: exists $1"; exit 2; }; }
for OUT in DIFF_INJECT_C3.txt DIFF_LINK_C3.txt PREREG_D_RECORD_C3.txt BINARIES_C3.tsv \
           SHA256SUMS_P05-S3R4C3.txt SHA256SUMS_P05-S3R4C3_EXCLUDED.txt SHA256SUMS_P05-S3R4C3_CHECK.txt; do
  ref "$EV/$OUT"
done

# --- 1. injector and link diffs (read-only comparisons, output into $EV) ---
diff -u "$REPO/testing/d003/stage_s3r4/inject_s3r4_init.cpp" "$REPO/testing/d003/stage_s3r4c3/inject_s3r4c3_poly.cpp" > "$EV/DIFF_INJECT_C3.txt" 2>&1
echo "diff inject rc=$?" >> "$EV/DIFF_INJECT_C3.txt"
diff -u "$REPO/testing/d003/stage_s3r4/link_init_s3r4.sh" "$REPO/testing/d003/stage_s3r4c3/link_poly_inj_c3.sh" > "$EV/DIFF_LINK_C3.txt" 2>&1
echo "diff link rc=$?" >> "$EV/DIFF_LINK_C3.txt"

# --- 2. D pre-registration record (hash, rows, mtime; NOT a registry record) ---
{
  echo "# PREREG_D_RECORD_C3 -- read-only record of REGISTRY_S3R4C3_D.tsv (CONT5 section 3.1)."
  echo "# Note: the modification time below is the file's mtime, NOT a registration record; CONT3 did not write a registration record."
  echo "file	$C3EV/REGISTRY_S3R4C3_D.tsv"
  echo "sha256	$(sha256sum "$C3EV/REGISTRY_S3R4C3_D.tsv" | cut -d' ' -f1)"
  echo "rows_total_lines	$(wc -l < "$C3EV/REGISTRY_S3R4C3_D.tsv")"
  echo "mtime_utc	$(stat -c %y "$C3EV/REGISTRY_S3R4C3_D.tsv")"
  echo "repo_copy_sha256	$(sha256sum "$REPO/checkpoints/p05/registries/s3r4c3/REGISTRY_S3R4C3_D.tsv" | cut -d' ' -f1)"
} > "$EV/PREREG_D_RECORD_C3.txt"

# --- 3. binary records: sha256 recorded; SAME/DIFFERENT decided here against the CONT3 known prefix (brief 3.1) ---
# bin_row NAME PATH EXPECTED_PREFIX_OR_DASH  (PATH is relative to REPO; "-" prefix = FIRST_RECORD, no comparison)
bin_row() {
  _h=$(sha256sum "$REPO/$2" | cut -d' ' -f1)
  if [ "$3" = "-" ]; then _v=FIRST_RECORD; else
    case "$_h" in "$3"*) _v=SAME;; *) _v=DIFFERENT;; esac
  fi
  printf '%s\t%s\t%s\t%s\t%s\n' "$1" "$2" "$_h" "$_v" "$3"
}
{
  printf 'name\tpath\tsha256\tcompare\texpected_prefix\n'
  bin_row F2-plain-lib checkpoints/p05/evidence/p05-s3r4/build/F2-plain/build/libS4.a c63d180a
  bin_row F3-plain-lib checkpoints/p05/evidence/p05-s3r4/build_f3/plain/build/libS4.a abbc01c7
  bin_row F3-dbg-lib checkpoints/p05/evidence/p05-s3r4/build_f3/dbg/build/libS4.a -
  bin_row init-F2-driver checkpoints/p05/evidence/p05-s3r4c2/drivers/init-F2/driver 29bb377c
  bin_row init-F3-driver checkpoints/p05/evidence/p05-s3r4c2/drivers/init-F3/driver ff66cfc1
  bin_row polyinj-F2-driver checkpoints/p05/evidence/p05-s3r4c3/drivers/polyinj-F2/driver -
  bin_row polyinj-F3-driver checkpoints/p05/evidence/p05-s3r4c3/drivers/polyinj-F3/driver -
} > "$EV/BINARIES_C3.tsv"

# --- 4. manifest of p05-s3r4c3 (non-binary evidence files, standard format, relative to p05-s3r4c3) ---
# Excluded: safe_run.log, tmp/, f3_export/, drivers/*/driver (binaries).  Listed in SHA256SUMS_P05-S3R4C3_EXCLUDED.txt.
cd "$C3EV" || exit 2
find . \( -name tmp -o -name f3_export \) -prune -o -type f ! -name safe_run.log ! -path './drivers/*/driver' -print | sed 's|^\./||' | LC_ALL=C sort > "$EV/tmp/listed_c5.txt"
xargs -d '\n' sha256sum < "$EV/tmp/listed_c5.txt" > "$EV/SHA256SUMS_P05-S3R4C3.txt"
{
  echo "# excluded from SHA256SUMS_P05-S3R4C3.txt (CONT5 section 3.1)"
  echo "safe_run.log (appended log; recorded as excluded)"
  echo "tmp/ (scratch directory)"
  echo "f3_export/ (copy of the F3 export; reproduced from the git tree, not hashed here)"
  echo "drivers/*/driver (binaries; hashes recorded in BINARIES_C3.tsv)"
} > "$EV/SHA256SUMS_P05-S3R4C3_EXCLUDED.txt"

# --- 5. verify the manifest from inside p05-s3r4c3 ---
cd "$C3EV" || exit 2
sha256sum -c "$EV/SHA256SUMS_P05-S3R4C3.txt" > "$EV/SHA256SUMS_P05-S3R4C3_CHECK.txt" 2>&1
echo "check rc=$?" >> "$EV/SHA256SUMS_P05-S3R4C3_CHECK.txt"
echo "supp done"
