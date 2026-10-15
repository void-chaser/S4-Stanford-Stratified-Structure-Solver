REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1c3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_errata_r8m1c3.sh -- P05-S4 R8 M1c3: append E8-81 and E8-82 to ERRATA_8.txt (brief section 3.2).
# Steps: build the append text (build_errata_r8m1c3.py), then append with prefix verification
# (append_registry_r8m1c3.py) against the start state 63754 bytes / fcbfe6b8...  No heredoc, no direct write.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1c3 -- sh testing/d003/stage_s4/append_errata_r8m1c3.sh
set -u
python3 -I -B "$REPO/testing/d003/stage_s4/build_errata_r8m1c3.py" || { echo "append_errata_r8m1c3: build failed" >&2; exit 2; }
python3 -I -B "$REPO/testing/d003/stage_s4/append_registry_r8m1c3.py" checkpoints/p05/registries/s4r8/ERRATA_8.txt "$EV/ERRATA_APPEND_R8_M1c3.txt" 63754 fcbfe6b8cf3ab201c8bcd3dda86a59ecd6e3a9d4393fb81b1cd6950a2fb2be02 || { echo "append_errata_r8m1c3: append refused" >&2; exit 2; }
echo "append_errata_r8m1c3: done"
exit 0
