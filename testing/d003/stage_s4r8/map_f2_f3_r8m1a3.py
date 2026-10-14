#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT2 section 4 (U153-U155, U154 rules): static map v3 of the injection sites, F2 (a07b5ac) to F3 (8d8202a).

New file.  Copy of map_f2_f3_r8m1a2.py (committed in CONT1, not modified) with these changes (U154):
  (a) before parsing, the text of each line is blanked: // comments, /* */ block comments (across lines), string literals and
      character literals (with \\ escapes) become spaces; line breaks are kept.  Lines whose first non-blank character is #
      do not take part in function-head recognition.  Brace depth is computed only on the blanked text.
  (b) PARSER SELF-CHECK: S4.cpp, pattern.c, fmm_FFT.cpp, fmm_kottke.cpp and fmm_PolBasisJones.cpp are parsed in both trees;
      the depth at end of file must be 0 and the depth must never go below 0; the listed functions of the expected lines are
      checked (from [source]).  Result: PARSER_SELFCHECK_R8_M1a3.tsv (OK / BAD).
  (c) DIFF OFFSET CROSS-CHECK: cumulative offset from the hunk headers of git diff -U0 a07b5ac 8d8202a for each file (run inside
      this script with subprocess, read only, not saved).  For each non-MODIFIED_BY_FIX site the F3 line = F2 line + offset
      when the F2 line is outside every '-' segment; that value is compared with the F3 line found by text and function
      (AGREE / DISAGREE).  MODIFIED_BY_FIX sites are not checked this way (U147 checks instead).
  (d) columns: used_in_m1 = YES (the file:line of each R7 / S3R4 / R8 runner or registry that cites the site) or NO (no citation;
      the searched directories are written); diff_offset_check = AGREE / DISAGREE / N/A(MODIFIED_BY_FIX).
  (e) U155: the function-name breakpoints of LINEMAP_M3_R7.tsv Part A are checked by FUNC_BP_SYMBOLS_R8_M1a3.tsv
      (each symbol must have exactly one function head in each tree: PRESENT; none: MISSING; several: MULTIPLE).

The status rules are those of map v2 (SAME_LINE / SHIFTED / AMBIGUOUS / MISSING / MODIFIED_BY_FIX); the U145-U148 rename and
the U147 checks are unchanged.  Trees are read with git show / git diff (read only).  Outputs are NEW files in $EV
(refused if they exist, U17).
Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r8/map_f2_f3_r8m1a3.py
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
OUT = os.path.join(EV, "LINEMAP_F2_F3_R8_M1a3.tsv")
OUT_PARSER = os.path.join(EV, "PARSER_SELFCHECK_R8_M1a3.tsv")
OUT_SYM = os.path.join(EV, "FUNC_BP_SYMBOLS_R8_M1a3.tsv")
OUT_CHECK = os.path.join(EV, "LINEMAP_CHECK_R8_M1a3.txt")
OUT_DIFF = os.path.join(EV, "LINEMAP_V2_V3_DIFF_R8_M1a3.txt")
EXPECT = os.path.join(EV, "EXPECT_LINEMAP_R8_M1a3.txt")
V2 = os.path.join(EV, "LINEMAP_F2_F3_R8_M1a2.tsv")
F2 = "a07b5ac"
F3 = "8d8202a"

FUNCTION_RULE = ("text is first blanked (// and /* */ comments, string and character literals become spaces; "
                 "lines whose first non-blank character is # are not heads). Function of a line = the identifier of the most "
                 "recent function head at brace depth 0 whose body '{' opens at depth 0; a head is a depth-0 line matching "
                 "^ident( or a depth-0 line with a type, identifier and '(' that does not end with ';' and is not a control "
                 "keyword; lines before any head = FILE_SCOPE.")
RENAME_F2_TO_F3 = {"shape_get_intersection_area_quad": "shape_get_intersection_area_quad_st"}  # U145, U148 (the only rename)
CONTROL_KEYWORDS = {"if", "for", "while", "switch", "return", "else", "do", "sizeof"}

# Sites: (cited_by, file, F2 line, role).  The v2 list (committed in CONT1) plus S4.cpp 4334 and 4210 (U153, U155).
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
    ("LINEMAP_F_F2_R7.tsv fn_pattern_generate_flow_field", "S4/pattern/pattern.c", 2123, "definition of pattern_generate_flow_field"),
    ("LINEMAP_F_F2_R7.tsv note_cg_call_in_sparse", "S4/pattern/pattern.c", 1416, "cg call inside sparse_linsolve_d"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 415", "S4/pattern/pattern.c", 415, "malloc of shape_get_intersection_area_quad (U145)"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 528", "S4/pattern/pattern.c", 528, "malloc of shape_get_intersection_area (U145)"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 806", "S4/pattern/pattern.c", 806, "malloc of pattern_get_containment_tree (area)"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 1164", "S4/pattern/pattern.c", 1164, "malloc of fprint_double"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 1251 (F2 column 1253)", "S4/pattern/pattern.c", 1253, "malloc of cg work (F2 line; F line is 1251)"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 1481 (F2 column 1499)", "S4/pattern/pattern.c", 1499, "malloc of rect iwork (F2 line; F line is 1481)"),
    ("LINEMAP_M3_R7.tsv Part B (U38) 1660 (F2 column 1689)", "S4/pattern/pattern.c", 1689, "malloc of tri iwork (F2 line; F line is 1660)"),
    ("LINEMAP_M3_R7.tsv Part A (FUNC)", "S4/S4.cpp", 23, "R7 line of Simulation_ComputeLayerModes (E8-33: #include line)"),
    ("LINEMAP_M3_R7.tsv Part A (FUNC)", "S4/S4.cpp", 32, "R7 line of Simulation_GetLayerSolution (E8-33: include line)"),
    ("LINEMAP_M3_R7.tsv Part A (FUNC)", "S4/S4.cpp", 4210, "definition of S4_Simulation_GetFieldPlane"),
    ("LINEMAP_A1_R7.tsv / gdb_chain_jones_line_r7.gdb", "S4/S4.cpp", 2413, "FMM epsilon status check (if(0 != fmm_ret){)"),
    ("LINEMAP_A1_R7.tsv / gdb_chain_jones_line_r7.gdb", "S4/fmm/fmm_PolBasisJones.cpp", 192, "failure branch after Pattern_GenerateFlowField (return error;)"),
    ("LINEMAP_A1_R7.tsv", "S4/fmm/fmm_PolBasisJones.cpp", 185, "call of Pattern_GenerateFlowField (context)"),
    ("PATTERN_MALLOC_CLASS_R7.tsv row 415 and U94 (U149(b))", "S4/fmm/fmm_FFT.cpp", 98, "Pattern_DiscretizeCell call in FMMGetEpsilon_FFT (U146)"),
    ("PATTERN_MALLOC_CLASS_R7.tsv row 415 and U94 (U149(b))", "S4/fmm/fmm_kottke.cpp", 102, "Pattern_DiscretizeCell call in FMMGetEpsilon_Kottke (U146)"),
    ("r6_plan14_caller.gdb line 26 (break fmm_FFT.cpp:90)", "S4/fmm/fmm_FFT.cpp", 90, "NULL check of the plan (R6 caller, U147)"),
    ("r6_plan14_caller.gdb line 32 (break fmm_kottke.cpp:94)", "S4/fmm/fmm_kottke.cpp", 94, "NULL check of the plan (R6 caller, U147)"),
    ("driver_r6b_state.cpp:73 (LINEMAP_M3_R7.tsv Part A)", "testing/d003/stage_s4/driver_r6b_state.cpp", 73,
     "r6_probe (driver source; not in S4/, identical in F2 and F3)"),
]

# U145/U146 named sites (F2 file, F2 line) -> F3 line, F3 function, and the core expression that must be a substring of the F3 line
MODIFIED_BY_FIX_SITES = {
    ("S4/pattern/pattern.c", 415): dict(f3_line=418, f3_func="shape_get_intersection_area_quad_st",
                                        core="malloc(sizeof(int)*3*(s->vtab.polygon.n_vertices-2))"),
    ("S4/fmm/fmm_FFT.cpp", 98): dict(f3_line=101, f3_func="FMMGetEpsilon_FFT",
                                     core="Pattern_DiscretizeCell(&L->pattern,S->Lr,ngrid[0],ngrid[1],ii[0],ii[1],discval)"),
    ("S4/fmm/fmm_kottke.cpp", 102): dict(f3_line=105, f3_func="FMMGetEpsilon_Kottke",
                                         core="Pattern_DiscretizeCell(&L->pattern,S->Lr,ngrid[0],ngrid[1],ii[0],ii[1],discval)"),
}

# U155: the function-name breakpoints of LINEMAP_M3_R7.tsv Part A (symbol, F2 expected line, F3 expected line)
SYMBOLS = [
    ("Simulation_GetLayerSolution", "S4/S4.cpp", 1778, 1787),
    ("Simulation_ComputeLayerModes", "S4/S4.cpp", 2250, 2259),
    ("S4_Simulation_GetFieldPlane", "S4/S4.cpp", 4210, 4219),
    ("r6_probe", "testing/d003/stage_s4/driver_r6b_state.cpp", 73, 73),
]

PARSED_FILES = ["S4/S4.cpp", "S4/pattern/pattern.c", "S4/fmm/fmm_FFT.cpp", "S4/fmm/fmm_kottke.cpp", "S4/fmm/fmm_PolBasisJones.cpp"]
# [source] function of each expected line, both trees (self-check of the parser): (file, line, function)
SELFCHECK_F2 = [("S4/S4.cpp", 4210, "S4_Simulation_GetFieldPlane"), ("S4/S4.cpp", 4334, "S4_Simulation_GetFieldPlane"),
                ("S4/S4.cpp", 2413, "Simulation_ComputeLayerModes"), ("S4/pattern/pattern.c", 415, "shape_get_intersection_area_quad"),
                ("S4/pattern/pattern.c", 528, "shape_get_intersection_area"), ("S4/pattern/pattern.c", 1253, "cg"),
                ("S4/S4.cpp", 2413, "Simulation_ComputeLayerModes")]
SELFCHECK_F3 = [("S4/S4.cpp", 4219, "S4_Simulation_GetFieldPlane"), ("S4/S4.cpp", 4343, "S4_Simulation_GetFieldPlane"),
                ("S4/S4.cpp", 2422, "Simulation_ComputeLayerModes"), ("S4/pattern/pattern.c", 418, "shape_get_intersection_area_quad_st"),
                ("S4/pattern/pattern.c", 545, "shape_get_intersection_area"), ("S4/pattern/pattern.c", 1279, "cg")]

# directories searched for the used_in_m1 column (U154(d))
USE_DIRS = ["testing/d003/stage_s4r7", "testing/d003/stage_s3r4c2", "testing/d003/stage_s3r4c3", "testing/d003/stage_s4r8",
            "checkpoints/p05/registries/s4r7", "checkpoints/p05/registries/s3r4c2", "checkpoints/p05/registries/s3r4c3"]
# gdb / runner citation forms of brief CONT2 section 4.3 (four forms), in the four stage directories of map v2
CITE_DIRS = ["testing/d003/stage_s4", "testing/d003/stage_s4r7", "testing/d003/stage_s3r4c2", "testing/d003/stage_s3r4c3"]


def git_show(rev, path):
    p = subprocess.run(["git", "show", "%s:%s" % (rev, path)], cwd=REPO, capture_output=True)
    if p.returncode != 0:
        return None
    return p.stdout.decode("utf-8", errors="replace").split("\n")


def blank_text(lines):
    """U154(a): return the same number of lines with comments and literals blanked (line breaks kept)."""
    out = []
    in_block = False
    for raw in lines:
        s = list(raw)
        i = 0
        n = len(s)
        in_str = None
        while i < n:
            c = s[i]
            if in_block:
                if c == "*" and i + 1 < n and s[i + 1] == "/":
                    s[i] = s[i + 1] = " "
                    in_block = False
                    i += 2
                    continue
                s[i] = " "
                i += 1
                continue
            if in_str is not None:
                if c == "\\" and i + 1 < n:
                    s[i] = s[i + 1] = " "
                    i += 2
                    continue
                if c == in_str:
                    s[i] = " "
                    in_str = None
                    i += 1
                    continue
                s[i] = " "
                i += 1
                continue
            if c == "/" and i + 1 < n and s[i + 1] == "/":
                for j in range(i, n):
                    s[j] = " "
                break
            if c == "/" and i + 1 < n and s[i + 1] == "*":
                s[i] = s[i + 1] = " "
                in_block = True
                i += 2
                continue
            if c in ("'", '"'):
                in_str = c
                s[i] = " "
                i += 1
                continue
            i += 1
        out.append("".join(s))
    return out


def function_table(lines):
    """Return (t, depth_end, min_depth): t[n] = function of 1-based line n (FILE_SCOPE if none), by FUNCTION_RULE on the blanked text."""
    blank = blank_text(lines)
    t = ["FILE_SCOPE"] * (len(lines) + 2)
    depth = 0
    min_depth = 0
    pending = None
    body = None  # (name, depth at which the body was opened)
    for no, text in enumerate(blank, 1):
        stripped = text.lstrip()
        if stripped.startswith("#"):
            t[no] = body[0] if body is not None else "FILE_SCOPE"
            continue
        if body is None and depth == 0:
            m = re.match(r"^([A-Za-z_]\w*)\s*\(", text) or re.match(
                r"^(?:[A-Za-z_][\w\s\*&:<>,]*?[\s\*&])([A-Za-z_]\w*)\s*\(", text)
            if m and m.group(1) not in CONTROL_KEYWORDS and not text.rstrip().endswith(";"):
                pending = m.group(1)
        for ch in text:
            if ch == "{":
                if body is None and depth == 0 and pending is not None:
                    body = (pending, depth)
                    pending = None
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth < min_depth:
                    min_depth = depth
                if body is not None and depth == body[1]:
                    body = None
            elif ch == ";" and depth == 0:
                pending = None
        t[no] = body[0] if body is not None else "FILE_SCOPE"
    return t, depth, min_depth


def collect_citations():
    """All F:N citations in the four stage directories (gdb and py), the four forms of CONT2 section 4.3."""
    pat = re.compile(r"(?:\bt?break\s+|LineBP\(\"|gdb\.Breakpoint\(\")([A-Za-z0-9_./-]+\.(?:cpp|cc|c|h|hpp))\s*:\s*(\d+)")
    out = []
    for d in CITE_DIRS:
        base = os.path.join(REPO, d)
        for root, _dirs, files in os.walk(base):
            for fn in sorted(files):
                if not (fn.endswith(".gdb") or fn.endswith(".py")):
                    continue
                p = os.path.join(root, fn)
                with open(p, encoding="utf-8", errors="replace") as fh:
                    for no, text in enumerate(fh, 1):
                        for m in pat.finditer(text):
                            out.append((os.path.relpath(p, REPO), no, os.path.basename(m.group(1)), int(m.group(2))))
    return out


def use_hits(basename, line):
    """U154(d): the R7/S3R4/R8 runner or registry files (and lines) that cite basename:line, in the USE_DIRS trees."""
    hits = []
    for d in USE_DIRS:
        base = os.path.join(REPO, d)
        if not os.path.isdir(base):
            continue
        for root, _dirs, files in os.walk(base):
            for fn in sorted(files):
                p = os.path.join(root, fn)
                if fn.endswith(".sh") or fn.endswith(".gdb") or fn.endswith(".py") or fn.endswith(".tsv") or fn.endswith(".txt"):
                    with open(p, encoding="utf-8", errors="replace") as fh:
                        for no, text in enumerate(fh, 1):
                            if re.search(r"(?<![0-9])%d(?![0-9])" % line, text) and basename in text:
                                hits.append("%s:%d" % (os.path.relpath(p, REPO), no))
    return hits


def in_added_segment(path, f3_line):
    """U147(i): F3 line inside a '+' segment of git diff -U0 a07b5ac 8d8202a for the file, or adjacent (distance 1)."""
    p = subprocess.run(["git", "diff", "-U0", F2, F3, "--", path], cwd=REPO, capture_output=True)
    segs = []
    for t in p.stdout.decode("utf-8", errors="replace").split("\n"):
        m = re.match(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", t)
        if m:
            start = int(m.group(1))
            count = int(m.group(2)) if m.group(2) is not None else 1
            if count == 0:
                segs.append((start, start))
            else:
                segs.append((start, start + count - 1))
    return any(a - 1 <= f3_line <= b + 1 for a, b in segs)


def hunks(path):
    """U154(c): (f2_start, f2_count, f3_start, f3_count) of each hunk of git diff -U0 a07b5ac 8d8202a for path (read only)."""
    p = subprocess.run(["git", "diff", "-U0", F2, F3, "--", path], cwd=REPO, capture_output=True)
    out = []
    for t in p.stdout.decode("utf-8", errors="replace").split("\n"):
        m = re.match(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", t)
        if m:
            a = int(m.group(1))
            ca = int(m.group(2)) if m.group(2) is not None else 1
            b = int(m.group(3))
            cb = int(m.group(4)) if m.group(4) is not None else 1
            out.append((a, ca, b, cb))
    return out


def offset_for(path, f2_line):
    """Return (F3 line by offset, True) if f2_line is outside every '-' segment; else (None, False)."""
    hs = hunks(path)
    off = 0
    for a, ca, b, cb in hs:
        # hunk covers F2 lines a .. a+ca-1 (for ca == 0 the insertion is after line a)
        if ca == 0:
            if f2_line > a:
                off += cb - ca
            continue
        if a <= f2_line <= a + ca - 1:
            return None, False
        if f2_line > a + ca - 1:
            off += cb - ca
    return f2_line + off, True


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: map_f2_f3_r8m1a3.py  (no arguments)")
    for p in (OUT, OUT_PARSER, OUT_SYM, OUT_CHECK, OUT_DIFF):
        if os.path.exists(p):
            raise SystemExit("REFUSED: exists (U17): %s" % p)

    # ---- (b) parser self-check ----
    parser_rows = []
    parser_bad = 0
    tree_fn = {}
    for path in PARSED_FILES:
        for rev in (F2, F3):
            lines = git_show(rev, path)
            if lines is None:
                parser_rows.append([rev, path, "-", "-", "BAD", "file missing"])
                parser_bad += 1
                continue
            t, depth_end, min_depth = function_table(lines)
            tree_fn[(rev, path)] = (t, lines)
            ok = depth_end == 0 and min_depth >= 0
            if not ok:
                parser_bad += 1
            parser_rows.append([rev, path, str(depth_end), str(min_depth), "OK" if ok else "BAD",
                                "end-depth 0 and min-depth >= 0"])
    for rev, expect_list in ((F2, SELFCHECK_F2), (F3, SELFCHECK_F3)):
        for path, n, want in expect_list:
            t, lines = tree_fn[(rev, path)]
            got = t[n]
            ok = got == want
            if not ok:
                parser_bad += 1
            parser_rows.append([rev, path, "line %d" % n, got, "OK" if ok else "BAD", "expected %s" % want])

    with open(OUT_PARSER, "x", encoding="utf-8") as fh:
        fh.write("# PARSER_SELFCHECK_R8_M1a3.tsv -- P05-S4 R8 M1a CONT2 section 4.2 (U154(b)). Written by map_f2_f3_r8m1a3.py (read only).\n")
        fh.write("# rule: " + FUNCTION_RULE + "\n")
        fh.write("\t".join(["tree", "file", "end_depth_or_line", "min_depth_or_function", "result", "note"]) + "\n")
        for r in parser_rows:
            fh.write("\t".join(r) + "\n")
        fh.write("# BAD count: %d\n" % parser_bad)

    # ---- sites ----
    citations = collect_citations()
    cite_by_key = {}
    for rel, no, base, line in citations:
        cite_by_key.setdefault((base, line), []).append("%s:%d" % (rel, no))
    sites = list(SITES)
    seen = {(s[1], s[2]) for s in sites}
    unmapped = []
    for rel, no, base, line in citations:
        cand = None
        for pref in ("S4/fmm/", "S4/", "S4/pattern/", "testing/d003/stage_s4/"):
            if git_show(F2, pref + base) is not None:
                cand = pref + base
                break
        if cand is None:
            unmapped.append("%s:%d -> %s:%d" % (rel, no, base, line))
            continue
        if (cand, line) not in seen:
            seen.add((cand, line))
            sites.append(("gdb citation %s:%d" % (rel, no), cand, line, "breakpoint cited by a gdb/py file"))
    stop = []
    for u in unmapped:
        stop.append("UNMAPPED gdb citation (no S4 path for basename): %s" % u)

    cache = {}
    fn_cache = {}
    rows = []
    for cited_by, path, line_f2, role in sites:
        if (F2, path) not in cache:
            cache[(F2, path)] = git_show(F2, path)
        f2_lines = cache[(F2, path)]
        if f2_lines is None:
            stop.append("F2 file missing: %s" % path)
            rows.append([cited_by, path, str(line_f2), "-", "-", "-", "-", "-", "MISSING", role, "-", "-", "-"])
            continue
        if not (1 <= line_f2 <= len(f2_lines)):
            stop.append("F2 line out of range: %s:%d" % (path, line_f2))
            rows.append([cited_by, path, str(line_f2), "-", "-", "-", "-", "-", "AUDIT_OUT_OF_RANGE", role, "-", "-", "-"])
            continue
        key = f2_lines[line_f2 - 1].strip()
        if key == "":
            stop.append("F2 line is blank: %s:%d" % (path, line_f2))
            rows.append([cited_by, path, str(line_f2), "", "-", "-", "-", "-", "AUDIT_BLANK", role, "-", "-", "-"])
            continue
        if (F2, path) not in fn_cache:
            t2, _d, _m = function_table(f2_lines)
            fn_cache[(F2, path)] = t2
        f2_fn = fn_cache[(F2, path)][line_f2]
        if (F3, path) not in cache:
            cache[(F3, path)] = git_show(F3, path)
        f3_lines = cache[(F3, path)]
        if f3_lines is None:
            stop.append("F3 file missing: %s" % path)
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, "-", "-", "-", "MISSING", role, "-", "-", "-"])
            continue
        if (F3, path) not in fn_cache:
            t3, _d, _m = function_table(f3_lines)
            fn_cache[(F3, path)] = t3
        f3_fn = fn_cache[(F3, path)]
        anchor_hits = cite_by_key.get((os.path.basename(path), line_f2), [])
        anchor_use = ("GDB_LINE_BP " + ";".join(anchor_hits)) if anchor_hits else "CLASSIFICATION_ONLY"
        uses = use_hits(os.path.basename(path), line_f2)
        used_in_m1 = ("YES " + ";".join(uses)) if uses else "NO (searched: " + ", ".join(USE_DIRS) + ")"

        mod = MODIFIED_BY_FIX_SITES.get((path, line_f2))
        if mod is not None:
            n = mod["f3_line"]
            i_ok = in_added_segment(path, n)
            f3_text = f3_lines[n - 1] if 1 <= n <= len(f3_lines) else ""
            ii_ok = mod["core"] in f3_text.replace(" ", "")
            iii_ok = f3_fn[n] == mod["f3_func"]
            f2_expected = "shape_get_intersection_area_quad" if path.endswith("pattern.c") else f2_fn
            f2_ok = f2_fn == f2_expected
            if i_ok and ii_ok and iii_ok and f2_ok:
                status = "MODIFIED_BY_FIX"
            else:
                status = "MISSING"
                stop.append("U147 check failed %s:%d (i=%s ii=%s iii=%s f2fn_ok=%s f3fn=%s)" % (
                    path, line_f2, i_ok, ii_ok, iii_ok, f2_ok, f3_fn[n]))
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, str(n), f3_fn[n],
                         "U147(i=%s,ii=%s,iii=%s,f2=%s)" % (i_ok, ii_ok, iii_ok, f2_ok), status, role, anchor_use,
                         used_in_m1, "N/A(MODIFIED_BY_FIX)"])
            continue

        off_line, off_ok = offset_for(path, line_f2)
        hits = [i for i, t in enumerate(f3_lines, 1) if t.strip() == key]
        f2_renamed = RENAME_F2_TO_F3.get(f2_fn, f2_fn)
        if len(hits) == 0:
            stop.append("MISSING: %s:%d '%s'" % (path, line_f2, key[:70]))
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, "-", "-", "-", "MISSING", role, anchor_use,
                         used_in_m1, "-"])
            continue
        if len(hits) == 1:
            h = hits[0]
            hf = f3_fn[h]
            if hf not in (f2_fn, f2_renamed) and f2_fn != "FILE_SCOPE":
                stop.append("AMBIGUOUS (function differs, unique text): %s:%d F2 fn=%s F3 fn=%s" % (path, line_f2, f2_fn, hf))
                rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, str(h), hf, "-", "AMBIGUOUS", role, anchor_use,
                             used_in_m1, "-"])
                continue
            status = "SAME_LINE" if h == line_f2 else "SHIFTED"
            chk = ("AGREE" if off_ok and off_line == h else ("DISAGREE" if off_ok else "N/A(F2 line inside a - segment)"))
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, str(h), hf, "-", status, role, anchor_use,
                         used_in_m1, chk])
            continue
        same = [h for h in hits if f3_fn[h] in (f2_fn, f2_renamed)]
        if len(same) == 1:
            h = same[0]
            status = "SAME_LINE" if h == line_f2 else "SHIFTED"
            chk = ("AGREE" if off_ok and off_line == h else ("DISAGREE" if off_ok else "N/A(F2 line inside a - segment)"))
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, str(h), f3_fn[h], "disambig_by_fn",
                         status, role, anchor_use, used_in_m1, chk])
        else:
            stop.append("AMBIGUOUS: %s:%d '%s' F3 lines %s; after function disambiguation %s" % (
                path, line_f2, key[:70], ",".join(map(str, hits)), ",".join(map(str, same)) or "none"))
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, ",".join(map(str, hits)), "-",
                         "-", "AMBIGUOUS", role, anchor_use, used_in_m1, "-"])

    counts = {}
    for r in rows:
        counts[r[8]] = counts.get(r[8], 0) + 1
    diff_counts = {}
    for r in rows:
        diff_counts[r[12]] = diff_counts.get(r[12], 0) + 1
    lines = [
        "# LINEMAP_F2_F3_R8_M1a3.tsv -- P05-S4 R8 M1a CONT2 section 4 (map v3; U153-U155, U154 rules).  Written by map_f2_f3_r8m1a3.py (read only, git show / git diff).",
        "# F2 = a07b5ac (S4 e124925f5b242486a913b813fa181664f665b048), F3 = 8d8202a (S4 6cff923a02baf19e01966b2339755cbf3a5deeef).",
        "# Function rule: " + FUNCTION_RULE,
        "# Rename (U145, U148): F2 shape_get_intersection_area_quad == F3 shape_get_intersection_area_quad_st.",
        "# MODIFIED_BY_FIX only for U145/U146's three sites after U147 (i) diff segment, (ii) core substring, (iii) F3 function.",
        "# diff_offset_check (U154(c)): for non-MODIFIED_BY_FIX sites, F3 line from the hunk offsets of git diff -U0 a07b5ac 8d8202a.",
        "\t".join(["cited_by", "file", "F2_line", "F2_text_key", "F2_function", "F3_line", "F3_function", "note",
                  "status", "role", "anchor_use", "used_in_m1", "diff_offset_check"]),
    ]
    for r in rows:
        lines.append("\t".join(r))
    lines.append("# counts: " + ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    lines.append("# diff_offset_check counts: " + ", ".join("%s=%d" % (k, diff_counts[k]) for k in sorted(diff_counts)))
    lines.append("# sites: %d; gdb_citations_scanned: %d" % (len(rows), len(citations)))
    lines.append("# stops: %d" % len(stop))
    for s in stop:
        lines.append("# STOP: " + s)
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")

    # ---- U155: function-name symbol check (FUNC_BP_SYMBOLS_R8_M1a3.tsv) ----
    sym_rows = []
    sym_fail = 0
    for sym, path, want2, want3 in SYMBOLS:
        f2 = git_show(F2, path) or []
        f3 = git_show(F3, path) or []
        def heads(lines, name):
            hs = []
            t, _d, _m = function_table(lines)
            for i in range(1, len(lines) + 1):
                if t[i] == name and (i == 1 or t[i - 1] != name):
                    hs.append(i)
            return hs
        h2 = heads(f2, sym)
        h3 = heads(f3, sym)
        st2 = "PRESENT" if len(h2) == 1 else ("MISSING" if not h2 else "MULTIPLE")
        st3 = "PRESENT" if len(h3) == 1 else ("MISSING" if not h3 else "MULTIPLE")
        ok = (st2 == "PRESENT" and st3 == "PRESENT" and (h2[0] == want2) and (h3[0] == want3)) if (h2 and h3) else False
        if not ok:
            sym_fail += 1
        sym_rows.append([sym, path, str(h2[0]) if h2 else "-", str(h3[0]) if h3 else "-", st2, st3,
                         "expected F2 %d F3 %d" % (want2, want3), "OK" if ok else "CHECK"])
    with open(OUT_SYM, "x", encoding="utf-8") as fh:
        fh.write("# FUNC_BP_SYMBOLS_R8_M1a3.tsv -- U155: function-name breakpoints of LINEMAP_M3_R7.tsv Part A, each symbol checked in both trees.\n")
        fh.write("\t".join(["symbol", "file", "F2_definition_line", "F3_definition_line", "F2_status", "F3_status",
                            "expected", "result"]) + "\n")
        for r in sym_rows:
            fh.write("\t".join(r) + "\n")
        fh.write("# not OK: %d\n" % sym_fail)

    # ---- LINEMAP_CHECK: compare with EXPECT_LINEMAP_R8_M1a3.txt, item by item ----
    mismatch = []
    res = []
    counts_all = counts
    def expect_value(key_line):
        return key_line
    exp_lines = [l.rstrip("\n") for l in open(EXPECT, encoding="utf-8")]
    exp = [l for l in exp_lines if l and not l.startswith("#") and not l.startswith("status ")]
    def got_for(key):
        if key == "MISSING":
            return str(counts_all.get("MISSING", 0))
        if key == "AMBIGUOUS":
            return str(counts_all.get("AMBIGUOUS", 0))
        if key == "MODIFIED_BY_FIX":
            return str(counts_all.get("MODIFIED_BY_FIX", 0))
        if key == "PARSER_SELFCHECK BAD":
            return str(parser_bad)
        if key == "DIFF_OFFSET DISAGREE":
            return str(diff_counts.get("DISAGREE", 0))
        return None
    for e in exp:
        parts = e.split()
        if parts[0] in ("MISSING", "AMBIGUOUS", "MODIFIED_BY_FIX") and len(parts) == 2:
            want = parts[1]
            got = got_for(parts[0])
            ok = got == want
            res.append("%s\t%s\texpected=%s\tactual=%s" % ("MATCH" if ok else "MISMATCH", parts[0], want, got))
            if not ok:
                mismatch.append(parts[0])
        elif parts[0] == "PARSER_SELFCHECK" and len(parts) == 3:
            got = got_for("PARSER_SELFCHECK BAD")
            ok = got == parts[2]
            res.append("%s\tPARSER_SELFCHECK_BAD\texpected=%s\tactual=%s" % ("MATCH" if ok else "MISMATCH", parts[2], got))
            if not ok:
                mismatch.append("PARSER_SELFCHECK")
        elif parts[0] == "DIFF_OFFSET" and len(parts) == 3:
            got = got_for("DIFF_OFFSET DISAGREE")
            ok = got == parts[2]
            res.append("%s\tDIFF_OFFSET_DISAGREE\texpected=%s\tactual=%s" % ("MATCH" if ok else "MISMATCH", parts[2], got))
            if not ok:
                mismatch.append("DIFF_OFFSET")
        elif parts[0] == "S4/S4.cpp" and len(parts) >= 4 and parts[3] == "used_in_m1":
            # site used_in_m1 check: expected NO
            sel = [r for r in rows if r[1] == "S4/S4.cpp" and r[2] == parts[2]]
            got = sel[0][11].split(" ")[0] if sel else "-"
            ok = got == parts[4]
            res.append("%s\tUSED_IN_M1 S4.cpp %s\texpected=%s\tactual=%s" % ("MATCH" if ok else "MISMATCH", parts[2], parts[4], got))
            if not ok:
                mismatch.append("USED_IN_M1 " + parts[2])
        elif parts[0] == "SYMBOL":
            sym = parts[1]
            sel = [r for r in sym_rows if r[0] == sym]
            ok = bool(sel) and sel[0][7] == "OK"
            res.append("%s\tSYMBOL %s\texpected=PRESENT\tactual=%s" % ("MATCH" if ok else "MISMATCH", sym,
                                                                     (sel[0][4] + "/" + sel[0][5]) if sel else "-"))
            if not ok:
                mismatch.append("SYMBOL " + sym)
        else:
            # site rows: "S4/file LINE F3 N STATUS"
            if len(parts) >= 5 and parts[2] == "F3":
                file_, line_, _f3, n_, status_ = parts[0], parts[1], parts[2], parts[3], parts[4]
                sel = [r for r in rows if r[1] == file_ and r[2] == line_]
                got_n = sel[0][5] if sel else "-"
                got_s = sel[0][8] if sel else "-"
                ok = (got_n == n_) and (got_s == status_)
                res.append("%s\t%s:%s\texpected=F3 %s %s\tactual=F3 %s %s" % ("MATCH" if ok else "MISMATCH", file_, line_, n_, status_, got_n, got_s))
                if not ok:
                    mismatch.append("%s:%s" % (file_, line_))
    with open(OUT_CHECK, "x", encoding="utf-8") as fh:
        fh.write("# LINEMAP_CHECK_R8_M1a3.txt -- item by item comparison with EXPECT_LINEMAP_R8_M1a3.txt (written by map_f2_f3_r8m1a3.py)\n")
        for r in res:
            fh.write(r + "\n")
        fh.write("# MISMATCH count: %d\n" % len(mismatch))

    # ---- (c) V2 vs V3 diff (LINEMAP_V2_V3_DIFF_R8_M1a3.txt): record only ----
    v2 = {}
    with open(V2, encoding="utf-8") as fh:
        for l in fh:
            if l.startswith("#") or l.startswith("cited_by\t"):
                continue
            f = l.rstrip("\n").split("\t")
            if len(f) >= 9:
                v2[(f[1], f[2])] = f
    v3 = {}
    for r in rows:
        v3[(r[1], r[2])] = r
    dl = ["# LINEMAP_V2_V3_DIFF_R8_M1a3.txt -- v2 (LINEMAP_F2_F3_R8_M1a2.tsv) against v3 (LINEMAP_F2_F3_R8_M1a3.tsv), per site.  Record only, no judgement (CONT2b section 4.3).",
          "\t".join(["file", "F2_line", "v2_F3_line", "v3_F3_line", "v2_F3_function", "v3_F3_function", "v2_status", "v3_status",
                     "changed"])]
    changed = 0
    for k in sorted(set(v2) | set(v3)):
        a = v2.get(k)
        b = v3.get(k)
        a_line = a[5] if a else "-"
        b_line = b[5] if b else "-"
        a_fn = a[6] if a else "-"
        b_fn = b[6] if b else "-"
        a_st = a[8] if a else "-"
        b_st = b[8] if b else "-"
        ch = (a_line != b_line) or (a_fn != b_fn) or (a_st != b_st)
        if ch:
            changed += 1
        dl.append("\t".join([k[0], k[1], a_line, b_line, a_fn, b_fn, a_st, b_st, "CHANGED" if ch else "same"]))
    dl.append("# changed sites: %d" % changed)
    with open(OUT_DIFF, "x", encoding="utf-8") as fh:
        fh.write("\n".join(dl) + "\n")

    print("MAP_V3 sites=%d counts=%s diff_check=%s parser_bad=%d symbols_not_ok=%d check_mismatch=%d stops=%d" % (
        len(rows), ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)),
        ", ".join("%s=%d" % (k, diff_counts[k]) for k in sorted(diff_counts)), parser_bad, sym_fail, len(mismatch), len(stop)))
    return 0 if (not stop and parser_bad == 0 and sym_fail == 0 and not mismatch) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
