REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# check_seam_anchor_c3.sh -- read-only anchor check of the historical seam apply scripts on the F3 export (--check-only).
# Writes only the check output into $EV.  No seam tree is created.
ROOT="$EV/f3_export"
OUT="$EV/SEAM_ANCHOR_CHECK_F3_C3.txt"
{
  echo "seam anchor check (check-only) utc=$(date -u +%Y-%m-%dT%H:%M:%SZ) root=$ROOT"
  echo "--- apply_seam_r5_fmmret.py --tree A --check-only"
  python3 "$REPO/testing/d003/seam/apply_seam_r5_fmmret.py" --tree A --root "$ROOT" --repo "$REPO" --check-only
  echo "rc=$?"
  echo "--- apply_seam_r2.py --families A,C,D --check-only"
  python3 "$REPO/testing/d003/seam/apply_seam_r2.py" --root "$ROOT" --repo "$REPO" --families A,C,D --check-only
  echo "rc=$?"
} > "$OUT" 2>&1
echo "anchor check written: $OUT"
