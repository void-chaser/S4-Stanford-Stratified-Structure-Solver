#!/usr/bin/env python3
# k1_anchor_r8m2a2.py -- P05-S4 R8 M2a2 section 4.1: [source] anchor check for K-1 (tensor branch, id 244).
# New file. Reads the exported F3 tree and the seam definition (testing/d003/seam/apply_seam_b2.py), checks that
#  - the block for id 244 matches exactly once in S4/fmm/fmm_closed.cpp (1-based lines 244-245 expected: solve + check),
#  - the solve line is LinearSolve<'N'> and the next line is the if(0 != solve_info) check,
#  - fmm_closed.cpp contains no isfinite (K-1 premise),
#  - fmm_kottke.cpp contains isfinite at 312/315 (comparison point).
# Output: $EV/K1_ANCHOR_R8_M2a2.tsv.  Refuses to overwrite (U17).
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
TREE = os.path.join(EV, "tree_F3", "S4")
SEAM = os.path.join(REPO, "testing", "d003", "seam", "apply_seam_b2.py")
OUT = os.path.join(EV, "K1_ANCHOR_R8_M2a2.tsv")


def rows(path):
    with open(path, "rb") as fh:
        raw = fh.read().decode("utf-8")
    out = []
    for line in raw.splitlines():
        out.append(line[:-1] if line.endswith("\r") else line)
    return out


def main():
    if os.path.exists(OUT):
        print("k1_anchor_r8m2a2: REFUSED exists (U17): %s" % OUT)
        return 2
    lines = []
    closed = rows(os.path.join(TREE, "fmm", "fmm_closed.cpp"))
    kottke = rows(os.path.join(TREE, "fmm", "fmm_kottke.cpp"))
    seam_lines = rows(SEAM)

    # Seam definition: find the 244 site block in apply_seam_b2.py (the id is a literal in SITES).
    seam_hit = [i + 1 for i, l in enumerate(seam_lines) if '"id": 244' in l]
    lines.append("SEAM_ID244_LINE\t%s:%s\tfound=%d" % (os.path.relpath(SEAM, REPO), seam_hit, len(seam_hit)))

    # The block from apply_seam_b2.py (the tensor-branch site): 4 lines starting at the SetMatrix line.
    block = [
        "\t\t\t\tRNP::TBLAS::SetMatrix<'A'>(n,n, 0.,1., Epsilon_inv,n);",
        "\t\t\t\t// P05-S3R D4: the tensor branch's solution is the output of this function; a zero pivot",
        "\t\t\t\t// leaves it unsolved, so report it instead of returning success.",
        "\t\t\t\tRNP::LinearSolve<'N'>(n,n, &Epsilon2[0+0*n2],n2, Epsilon_inv,n, &solve_info, NULL);",
        "\t\t\t\tif(0 != solve_info){ S4_free(ivalues); return 1; }",
    ]
    hits = [i for i in range(len(closed) - len(block) + 1) if closed[i:i + len(block)] == block]
    lines.append("CLOSED_BLOCK_244_MATCH_COUNT\tfmm_closed.cpp\t%d" % len(hits))
    if len(hits) == 1:
        s = hits[0]
        solve_line = s + 3  # 0-based index of the LinearSolve line
        lines.append("CLOSED_SOLVE_LINE\tfmm_closed.cpp:%d\t%s" % (solve_line + 1, closed[solve_line].strip()))
        lines.append("CLOSED_CHECK_LINE\tfmm_closed.cpp:%d\t%s" % (solve_line + 2, closed[solve_line + 1].strip()))
        lines.append("CLOSED_BLOCK_LINES\tfmm_closed.cpp:%d-%d\t[source]" % (s + 1, s + len(block)))
    else:
        lines.append("CLOSED_BLOCK_244_ANCHOR\tfmm_closed.cpp\tUNRESOLVED")

    isf_closed = [i + 1 for i, l in enumerate(closed) if "isfinite" in l]
    lines.append("CLOSED_ISFINITE_LINES\tfmm_closed.cpp\t%s\t[source]" % (isf_closed if isf_closed else "NONE"))
    isf_kottke = [i + 1 for i, l in enumerate(kottke) if "isfinite" in l]
    lines.append("KOTTKE_ISFINITE_LINES\tfmm_kottke.cpp\t%s\t[source]" % (isf_kottke if isf_kottke else "NONE"))

    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# K1_ANCHOR_R8_M2a2 -- [source] anchors for K-1 (P05-S4 R8 M2a2 section 4.1)\n")
        fh.write("# columns: check\tlocation\tvalue\t[label]\n")
        for l in lines:
            fh.write(l + "\n")
    print("k1_anchor_r8m2a2: wrote %s" % OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
