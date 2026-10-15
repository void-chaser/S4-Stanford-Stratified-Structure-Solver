REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# build_r8m2a2.sh -- P05-S4 R8 M2a2 section 4.4 Build script.
# Builds apparatus libraries and drivers into $EV/build/.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2a2 -- sh testing/d003/stage_s4/build_r8m2a2.sh p05-s4r8/m2a2
set -u
refuse() { echo "build_r8m2a2: REFUSED: $1" >&2; exit 2; }
[ "${1:-}" = p05-s4r8/m2a2 ] || refuse "first argument must be p05-s4r8/m2a2"

python3 -I -B "$REPO/testing/d003/stage_s4/build_r8m2a2.py"
RC=$?
echo "build_r8m2a2: python exit rc=$RC"
exit "$RC"
