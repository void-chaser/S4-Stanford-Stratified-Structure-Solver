REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s3r4c5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gate_c5.sh -- P05-S3R4 CONT5 gate (read-only checks; writes only $EV/GATE_CONT5*.txt).
# Usage: sh testing/d003/safe_run.sh p05-s3r4c5 -- sh testing/d003/stage_s3r4c5/gate_c5.sh start|end COUNT LISTSHA
# COUNT and LISTSHA are the top-level snapshot of the system temporary area, read by the caller (read only) and passed in.
MODE=${1:-start}
TMPCOUNT=${2:-unknown}
TMPSHA=${3:-unknown}
if [ "$MODE" = "start" ]; then OUT="$EV/GATE_CONT5.txt"; else OUT="$EV/GATE_CONT5_END.txt"; fi
{
  echo "gate_mode=$MODE utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "HEAD=$(git rev-parse HEAD)"
  echo "HEAD:S4=$(git rev-parse HEAD:S4)"
  sha256sum "$REPO/testing/d003/judge_d003.py"
  echo "--- git status --short"
  git status --short
  echo "--- evidence libs and drivers"
  sha256sum "$REPO/checkpoints/p05/evidence/p05-s3r4/build/F2-plain/build/libS4.a"
  sha256sum "$REPO/checkpoints/p05/evidence/p05-s3r4/build_f3/plain/build/libS4.a"
  sha256sum "$REPO/checkpoints/p05/evidence/p05-s3r4c2/drivers/init-F2/driver"
  sha256sum "$REPO/checkpoints/p05/evidence/p05-s3r4c2/drivers/init-F3/driver"
  sha256sum "$REPO/checkpoints/p05/evidence/p05-s3r4c2/REGISTRY_S3R4C2_A.tsv"
  echo "--- system temporary area top-level snapshot (read only)"
  echo "entries=$TMPCOUNT"
  echo "listing_sha256=$TMPSHA"
} > "$OUT" 2>&1
echo "gate written: $OUT"
