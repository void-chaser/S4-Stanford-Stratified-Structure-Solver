REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c4; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_errata_r8m1c4.sh -- P05-S4 R8 M1c4: append E8-83 to E8-87 to ERRATA_8.txt (brief section 3.2).
# Steps: build the append text (build_errata_r8m1c4.py), then append with prefix verification
# (append_registry_r8m1c4.py) against the start state 64662 bytes / c8d5a1c1...  No heredoc, no direct write.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- sh testing/d003/stage_s4/append_errata_r8m1c4.sh
set -u
python3 -I -B "$REPO/testing/d003/stage_s4/build_errata_r8m1c4.py" || { echo "append_errata_r8m1c4: build failed" >&2; exit 2; }
python3 -I -B "$REPO/testing/d003/stage_s4/append_registry_r8m1c4.py" checkpoints/p05/registries/s4r8/ERRATA_8.txt "$EV/ERRATA_APPEND_R8_M1c4.txt" 64662 c8d5a1c11617729f8649528f01ad5194098fc52a8614342661d17a981c346b6f || { echo "append_errata_r8m1c4: append refused" >&2; exit 2; }
echo "append_errata_r8m1c4: done"
exit 0
