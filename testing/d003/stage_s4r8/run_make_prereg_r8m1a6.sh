#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a6; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# run_make_prereg_r8m1a6.sh -- wrapper to invoke python3 -I -B on make_prereg_r8m1a6.py
set -u
python3 -I -B "$REPO/testing/d003/stage_s4r8/make_prereg_r8m1a6.py" "$@"
