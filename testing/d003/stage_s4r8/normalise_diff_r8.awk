# normalise_diff_r8.awk -- P05-S4 R8 M0 seam diff normalisation (new file; used by compare_seam_r8.sh).
#   awk -f testing/d003/stage_s4r8/normalise_diff_r8.awk INPUT.diff > OUTPUT
# Rules:
#   1. a line that starts with "diff -ru " is a file header: it is removed, and so are the next "--- " line and the
#      next "+++ " line (the file header of a unified diff).  Content lines that happen to start with "---" or "+++"
#      are NOT removed, because they are not preceded by a "diff -ru " header.
#   2. every line that starts with "@@" is replaced by "@@" (line offsets differ between F3 and F2, brief 3.3).
#   3. every other line is copied unchanged.
# The rules are applied the same way to the R7 reference diffs and to the F3 raw diffs.
BEGIN { hdr = 0 }
/^diff -ru / { hdr = 1; next }
hdr == 1 && /^--- / { hdr = 2; next }
hdr == 2 && /^\+\+\+ / { hdr = 0; next }
/^@@/ { print "@@"; next }
{ hdr = 0; print }
