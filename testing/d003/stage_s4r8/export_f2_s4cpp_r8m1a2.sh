#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# export_f2_s4cpp_r8m1a2.sh -- P05-S4 R8 M1a CONT1: export F2 (a07b5ac) S4/S4.cpp to a new evidence file for reading only.  New file.
# git show writes its output to stdout only; the redirection into $EV/F2_S4.cpp.txt is the single write of this script.
#   sh testing/d003/safe_run.sh p05-s4r8 -- sh testing/d003/stage_s4r8/export_f2_s4cpp_r8m1a2.sh p05-s4r8
set -u
[ "${1:-}" = p05-s4r8 ] || { echo "export_f2_s4cpp_r8m1a2: first argument must be p05-s4r8" >&2; exit 2; }
OUT="$EV/F2_S4.cpp.txt"
test ! -e "$OUT" || { echo "export_f2_s4cpp_r8m1a2: REFUSED exists (U17): $OUT" >&2; exit 2; }
if git show a07b5ac:S4/S4.cpp > "$OUT"; then
    echo "export_f2_s4cpp_r8m1a2: done -> $OUT"
else
    echo "export_f2_s4cpp_r8m1a2: git show failed" >&2
    exit 2
fi
exit 0
