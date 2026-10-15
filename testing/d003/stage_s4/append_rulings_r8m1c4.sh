REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c4; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_rulings_r8m1c4.sh -- P05-S4 R8 M1c4: append U223-U228 to RULINGS.tsv (brief section 3.1).
# Steps: build the append text (build_rulings_r8m1c4.py), then append with prefix verification
# (append_registry_r8m1c4.py) against the start state 86035 bytes / 82d89c5e...  No heredoc, no direct write.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- sh testing/d003/stage_s4/append_rulings_r8m1c4.sh
set -u
python3 -I -B "$REPO/testing/d003/stage_s4/build_rulings_r8m1c4.py" || { echo "append_rulings_r8m1c4: build failed" >&2; exit 2; }
python3 -I -B "$REPO/testing/d003/stage_s4/append_registry_r8m1c4.py" checkpoints/p05/registries/RULINGS.tsv "$EV/RULINGS_APPEND_R8_M1c4.tsv" 86035 82d89c5e7fba0b7f1e8b746c1e2460cf3370efa588964406541214b16fd077c1 || { echo "append_rulings_r8m1c4: append refused" >&2; exit 2; }
echo "append_rulings_r8m1c4: done"
exit 0
