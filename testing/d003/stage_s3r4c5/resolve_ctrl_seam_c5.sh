REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# resolve_ctrl_seam_c5.sh -- CONT5 section 3.2.  Writes the expectation BEFORE running the resolver, then runs it.
# Usage: sh testing/d003/safe_run.sh p05-s3r4c5 -- sh testing/d003/stage_s3r4c5/resolve_ctrl_seam_c5.sh
set -u
OUT="$EV/CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv"
EXP="$EV/EXPECT_RESOLUTION_C5.txt"
test -e "$OUT" && { echo "REFUSED: exists $OUT"; exit 2; }
test -e "$EXP" && { echo "REFUSED: exists $EXP"; exit 2; }
{
  echo "# EXPECT_RESOLUTION_C5 -- written BEFORE the resolver runs (CONT5 section 3.2).  Expected, not observed."
  echo "# seamF rows (CTRL-SEAM-seamF-F, CTRL-SEAM-seamF-F2): registered driver seamF-<tree>, resolved seamF-<tree>, AGREE."
  echo "# fmmret rows (CTRL-SEAM-fmmret-F, CTRL-SEAM-fmmret-F2): registered driver fmmret-<tree>, resolved seamF-<tree>, DISAGREE."
  echo "# Reason: request none -> driver_for returns seamF-<tree> (run_m2b_all_r7.py:124-131); the driver column is not read."
  echo "expect	CTRL-SEAM-seamF-F	AGREE"
  echo "expect	CTRL-SEAM-seamF-F2	AGREE"
  echo "expect	CTRL-SEAM-fmmret-F	DISAGREE	resolved=seamF-F"
  echo "expect	CTRL-SEAM-fmmret-F2	DISAGREE	resolved=seamF-F2"
  echo "# registered_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$EXP"
python3 -I -B "$REPO/testing/d003/stage_s3r4c5/resolve_ctrl_seam_c5.py" > "$OUT" 2> "$EV/tmp/resolve_ctrl_seam_c5.err"
echo "resolver rc=$?"
echo "expect sha256: $(sha256sum "$EXP" | cut -d' ' -f1)"
