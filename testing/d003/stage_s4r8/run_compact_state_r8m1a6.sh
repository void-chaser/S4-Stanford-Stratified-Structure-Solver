#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a6; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_compact_state_r8m1a6.sh -- wrapper to invoke compact_state_and_crosswalk_r8m1a6.py
set -u
python3 -I -B "$REPO/testing/d003/stage_s4r8/compact_state_and_crosswalk_r8m1a6.py" "$@"
