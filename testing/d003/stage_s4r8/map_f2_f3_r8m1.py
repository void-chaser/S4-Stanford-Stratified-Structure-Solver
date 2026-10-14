#!/usr/bin/env python3
"""P05-S4 R8 M1a, section 6.1 (U140): static map of the injection sites from F2 (a07b5ac) to F3 (8d8202a).  New file.

Every site is a (file, F2 line) pair that the R7 scripts or gdb files cite (the list below is taken from the committed
R7 maps: LINEMAP_F_F2_R7.tsv, LINEMAP_M3_R7.tsv (Parts A and B), LINEMAP_A1_R7.tsv, gdb_chain_jones_line_r7.gdb).
The F2 text of the line is read with git show (read only) and used as the key.  The key is then searched in the F3
file (git show 8d8202a:<file>, read only).  Status:
  SAME_LINE   the key is found exactly once in F3, on the same line number;
  SHIFTED     the key is found exactly once in F3, on a different line number (the new number is recorded);
  MISSING     the key is not found in F3 (the script stops, brief section 6.1);
  AMBIGUOUS   the key is found more than once in F3 (the script stops; a human decides).
A site whose F2 text does not contain its own key on the F2 line (AUDIT) also stops the script.
Output (new file, refused if it exists): $EV/LINEMAP_F2_F3_R8_M1a.tsv
Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r8/map_f2_f3_r8m1.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
OUT = os.path.join(EV, "LINEMAP_F2_F3_R8_M1a.tsv")
F2 = "a07b5ac"
F3 = "8d8202a"

# (source of the citation, file, F2 line, role).  Source is the committed R7 table or script that cites the line.
SITES = [
    ("LINEMAP_F_F2_R7.tsv malloc_cg_work", "S4/pattern/pattern.c", 1253, "RNV1 window malloc (cg work)"),
    ("LINEMAP_F_F2_R7.tsv solve_rect", "S4/pattern/pattern.c", 1643, "rect solver call"),
    ("LINEMAP_F_F2_R7.tsv malloc_rect_work", "S4/pattern/pattern.c", 1489, "RNV1 window malloc (rect work)"),
    ("LINEMAP_F_F2_R7.tsv malloc_rect_iwork", "S4/pattern/pattern.c", 1499, "RNV1 window malloc (rect iwork)"),
    ("LINEMAP_F_F2_R7.tsv solve_tri", "S4/pattern/pattern.c", 2089, "tri solver call"),
    ("LINEMAP_F_F2_R7.tsv malloc_tri_work", "S4/pattern/pattern.c", 1679, "RNV1 window malloc (tri work)"),
    ("LINEMAP_F_F2_R7.tsv malloc_tri_iwork", "S4/pattern/pattern.c", 1689, "RNV1 window malloc (tri iwork)"),
    ("LINEMAP_F_F2_R7.tsv fn_cg", "S4/pattern/pattern.c", 1247, "static definition of cg"),
    ("LINEMAP_F_F2_R7.tsv fn_rect", "S4/pattern/pattern.c", 1476, "definition of pattern_generate_flow_field_rect"),
    ("LINEMAP_F_F2_R7.tsv fn_tri", "S4/pattern/pattern.c", 1666, "definition of pattern_generate_flow_field_tri"),
    ("LINEMAP_F_F2_R7.tsv fn_pattern_generate_flow_field", "S4/pattern/pattern.c", 2123,
     "definition of pattern_generate_flow_field"),
    ("LINEMAP_F_F2_R7.tsv note_cg_call_in_sparse", "S4/pattern/pattern.c", 1416, "cg call inside sparse_linsolve_d"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 415", "S4/pattern/pattern.c", 415, "malloc of shape_get_intersection_area_quad"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 528", "S4/pattern/pattern.c", 528, "malloc of shape_get_intersection_area"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 806", "S4/pattern/pattern.c", 806, "malloc of pattern_get_containment_tree (area)"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 1164", "S4/pattern/pattern.c", 1164, "malloc of fprint_double"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 1251 (F2 column 1253)", "S4/pattern/pattern.c", 1253,
     "malloc of cg work (F2 line; F line is 1251)"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 1481 (F2 column 1499)", "S4/pattern/pattern.c", 1499,
     "malloc of rect iwork (F2 line; F line is 1481)"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 1660 (F2 column 1689)", "S4/pattern/pattern.c", 1689,
     "malloc of tri iwork (F2 line; F line is 1660)"),
    ("LINEMAP_M3_R7.tsv Part A (FUNC)", "S4/S4.cpp", 23, "declaration of Simulation_ComputeLayerModes"),
    ("LINEMAP_M3_R7.tsv Part A (FUNC)", "S4/S4.cpp", 32, "declaration of Simulation_GetLayerSolution"),
    ("LINEMAP_M3_R7.tsv Part A (FUNC)", "S4/S4.cpp", 4210, "definition of S4_Simulation_GetFieldPlane"),
    ("LINEMAP_A1_R7.tsv / gdb_chain_jones_line_r7.gdb", "S4/S4.cpp", 2413, "FMM epsilon status check (if(0 != fmm_ret){)"),
    ("LINEMAP_A1_R7.tsv / gdb_chain_jones_line_r7.gdb", "S4/fmm/fmm_PolBasisJones.cpp", 192,
     "failure branch after Pattern_GenerateFlowField (return error;)"),
    ("LINEMAP_A1_R7.tsv", "S4/fmm/fmm_PolBasisJones.cpp", 185, "call of Pattern_GenerateFlowField (context)"),
    ("r5_rnv1_malloc_count.gdb comment (F lines)", "S4/fmm/fmm_FFT.cpp", 98, "FMMGetEpsilon_FFT epsilon call site (Pattern_DiscretizeCell)"),
    ("r5_rnv1_malloc_count.gdb comment (F lines)", "S4/fmm/fmm_kottke.cpp", 102, "FMMGetEpsilon_Kottke epsilon call site"),
    ("LINEMAP_M3_R7.tsv Part A (FUNC) driver", "testing/d003/stage_s4/driver_r6b_state.cpp", 73,
     "r6_probe (driver source; not in S4/, identical in F2 and F3)"),
]


def git_show(rev, path):
    """File text at a commit, read only (git show writes nothing to the work tree or to a file)."""
    p = subprocess.run(["git", "show", "%s:%s" % (rev, path)], cwd=REPO, capture_output=True)
    if p.returncode != 0:
        return None
    return p.stdout.decode("utf-8", errors="replace").split("\n")


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: map_f2_f3_r8m1.py  (no arguments)")
    if os.path.exists(OUT):
        raise SystemExit("REFUSED: exists (U17): %s" % OUT)
    rows = []
    stop = []
    cache = {}
    for src, path, line_f2, role in SITES:
        key_name = (F2, path)
        if key_name not in cache:
            cache[key_name] = git_show(F2, path)
        f2_lines = cache[key_name]
        if f2_lines is None:
            stop.append("F2 file missing: %s" % path)
            rows.append([src, path, str(line_f2), "-", "-", "MISSING_F2_FILE", role])
            continue
        if not (1 <= line_f2 <= len(f2_lines)):
            stop.append("F2 line out of range: %s:%d" % (path, line_f2))
            rows.append([src, path, str(line_f2), "-", "-", "AUDIT_OUT_OF_RANGE", role])
            continue
        key = f2_lines[line_f2 - 1].strip()
        if key == "":
            stop.append("F2 line is blank: %s:%d" % (path, line_f2))
            rows.append([src, path, str(line_f2), "", "-", "AUDIT_BLANK", role])
            continue
        # AUDIT: the key occurs in F2 on the stated line, and only there, is not required (a function body line may repeat);
        # the key is taken from the stated line itself, so the audit is that the line is non-blank and in range.
        f3_key_name = (F3, path)
        if f3_key_name not in cache:
            cache[f3_key_name] = git_show(F3, path)
        f3_lines = cache[f3_key_name]
        if f3_lines is None:
            stop.append("F3 file missing: %s" % path)
            rows.append([src, path, str(line_f2), key, "-", "MISSING_F3_FILE", role])
            continue
        hits = [i for i, t in enumerate(f3_lines, 1) if t.strip() == key]
        if len(hits) == 0:
            status = "MISSING"
            stop.append("MISSING: %s:%d '%s'" % (path, line_f2, key[:70]))
            f3_where = "-"
        elif len(hits) > 1:
            status = "AMBIGUOUS"
            stop.append("AMBIGUOUS: %s:%d '%s' occurs at F3 lines %s" % (path, line_f2, key[:70],
                                                                     ",".join(str(h) for h in hits)))
            f3_where = ",".join(str(h) for h in hits)
        else:
            f3_where = str(hits[0])
            status = "SAME_LINE" if hits[0] == line_f2 else "SHIFTED"
        rows.append([src, path, str(line_f2), key.replace("\t", " ")[:120], f3_where, status, role])

    lines = ["# LINEMAP_F2_F3_R8_M1a.tsv -- P05-S4 R8 M1a section 6.1 (U140).  Written by map_f2_f3_r8m1.py (read only, git show).",
             "# F2 = a07b5ac (S4 e124925f5b242486a913b813fa181664f665b048), F3 = 8d8202a (S4 6cff923a02baf19e01966b2339755cbf3a5deeef).",
             "# Key = the F2 text of the cited line (stripped); F3 position = the line of the same text in the F3 file.",
             "# Status: SAME_LINE, SHIFTED, MISSING, AMBIGUOUS (stop), AUDIT_* (stop).",
             "\t".join(["cited_by", "file", "F2_line", "F2_text_key", "F3_line", "status", "role"])]
    for r in rows:
        lines.append("\t".join(r))
    counts = {}
    for r in rows:
        counts[r[5]] = counts.get(r[5], 0) + 1
    lines.append("# counts: " + ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    lines.append("# stops: %d" % len(stop))
    for s in stop:
        lines.append("# STOP: " + s)
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("LINEMAP sites=%d counts=%s stops=%d -> %s" % (len(rows), ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)),
                                                       len(stop), OUT))
    return 0 if not stop else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
