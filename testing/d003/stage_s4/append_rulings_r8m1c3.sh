REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_rulings_r8m1c3.sh -- P05-S4 R8 M1c3: append U218-U222 to RULINGS.tsv (brief section 3.1).
# Steps: build the append text (build_rulings_r8m1c3.py), then append with prefix verification
# (append_registry_r8m1c3.py) against the start state 84298 bytes / 9e9f4c74...  No heredoc, no direct write.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c3 -- sh testing/d003/stage_s4/append_rulings_r8m1c3.sh
set -u
python3 -I -B "$REPO/testing/d003/stage_s4/build_rulings_r8m1c3.py" || { echo "append_rulings_r8m1c3: build failed" >&2; exit 2; }
python3 -I -B "$REPO/testing/d003/stage_s4/append_registry_r8m1c3.py" checkpoints/p05/registries/RULINGS.tsv "$EV/RULINGS_APPEND_R8_M1c3.tsv" 84298 9e9f4c748544354adfd4b640147c25466de27b4a3ef6ee2752d8963c3d8361e2 || { echo "append_rulings_r8m1c3: append refused" >&2; exit 2; }
echo "append_rulings_r8m1c3: done"
exit 0
