#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT2c section 5 (U170, U171): static map v3c of the injection sites, F2 (a07b5ac) to F3 (8d8202a).

New file.  Copy of map_f2_f3_r8m1a3.py (committed in CONT2b, not modified) with the six classes of change of CONT2c 5.2:
  (1) output names and this description (the *_r8m1a3c / *_M1a3c names);
  (2) U170: the __attribute__((...)) text of a function head is replaced by spaces of the same length before the head regex;
  (3) self-check: driver_r6b_state.cpp added to PARSED_FILES; both trees: end depth 0, min depth >= 0, line 73 = r6_probe;
      no function table may contain __attribute__, extern, static, inline or const (any such name is BAD);
  (4) U171: used_in_m1 is three-valued (BP_LINE / REGISTRY_ONLY / NO), with at most three file:line references per value;
  (5) EXPECT comparator: the six line formats of CONT2c 5.1; a line that cannot be parsed is UNPARSED and counted as MISMATCH;
  (6) the diff file compares v3 with v3c (F3 line, function, status, used_in_m1 per site; record only).
The site table, the status rules, the rename table, the U147 checks and the diff-offset algorithm are unchanged.

Description of the v3 parts that are kept (CONT2 section 4.2, U154 rules):
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
# (1) CONT2c output names
OUT = os.path.join(EV, "LINEMAP_F2_F3_R8_M1a3c.tsv")
OUT_PARSER = os.path.join(EV, "PARSER_SELFCHECK_R8_M1a3c.tsv")
OUT_SYM = os.path.join(EV, "FUNC_BP_SYMBOLS_R8_M1a3c.tsv")
OUT_CHECK = os.path.join(EV, "LINEMAP_CHECK_R8_M1a3c.txt")
OUT_DIFF = os.path.join(EV, "LINEMAP_V3_V3C_DIFF_R8_M1a3c.txt")
EXPECT = os.path.join(EV, "EXPECT_LINEMAP_R8_M1a3c.txt")
V3_TSV = os.path.join(EV, "LINEMAP_F2_F3_R8_M1a3.tsv")   # (6) v3 result (committed as a stop record; read only)
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

PARSED_FILES = ["S4/S4.cpp", "S4/pattern/pattern.c", "S4/fmm/fmm_FFT.cpp", "S4/fmm/fmm_kottke.cpp", "S4/fmm/fmm_PolBasisJones.cpp",
                "testing/d003/stage_s4/driver_r6b_state.cpp"]  # (3) CONT2c: driver added
FORBIDDEN_FUNC_NAMES = {"__attribute__", "extern", "static", "inline", "const"}  # (3) CONT2c: no function table may contain these
DRIVER = "testing/d003/stage_s4/driver_r6b_state.cpp"
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


ATTR_RE = re.compile(r"__attribute__\s*\((?:[^()]|\([^()]*\))*\)")


def mask_attributes(text):
    """U170(2): replace __attribute__((...)) (one level of nested brackets allowed) by spaces of the same length.
    Used only for function-head recognition; brace depth is still computed on the unmasked blanked text."""
    return ATTR_RE.sub(lambda m: " " * len(m.group(0)), text)


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
            head = mask_attributes(text)
            m = re.match(r"^([A-Za-z_]\w*)\s*\(", head) or re.match(
                r"^(?:[A-Za-z_][\w\s\*&:<>,]*?[\s\*&])([A-Za-z_]\w*)\s*\(", head)
            if m and m.group(1) not in CONTROL_KEYWORDS and not head.rstrip().endswith(";"):
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


USED_BP_DIRS = ["testing/d003/stage_s4r7", "testing/d003/stage_s3r4c2", "testing/d003/stage_s3r4c3"]   # (4) U171 BP_LINE, first rule
USED_REG_DIRS = ["checkpoints/p05/registries/s4r7", "checkpoints/p05/registries/s3r4c2", "checkpoints/p05/registries/s3r4c3"]
USED_S4_DIR = "testing/d003/stage_s4"                                                                # (4) U171 BP_LINE, second rule
USED_TEXT_EXT = (".py", ".sh", ".gdb", ".tsv", ".txt")
BP_RE = re.compile(r"(?:\bt?break\s+|LineBP\(\"|gdb\.Breakpoint\(\")([A-Za-z0-9_./-]+\.(?:cpp|cc|c|h|hpp))\s*:\s*(\d+)")


def _files_under(rel, exts):
    base = os.path.join(REPO, rel)
    out = []
    if not os.path.isdir(base):
        return out
    for root, _dirs, files in os.walk(base):
        for fn in sorted(files):
            if fn.endswith(exts):
                out.append(os.path.join(root, fn))
    return out


def used_class(basename, line):
    """(4) U171: three-valued used_in_m1 for the site basename:line.
    BP_LINE: a break/tbreak/LineBP/gdb.Breakpoint reference file:line in stage_s4r7, stage_s3r4c2, stage_s3r4c3 (.gdb/.py);
             or such a reference in stage_s4 (.gdb/.py) when the file name (whole word) occurs in one of the three stage
             directories or in registries/{s4r7,s3r4c2,s3r4c3} (.py/.sh/.gdb/.tsv/.txt).
    REGISTRY_ONLY: not BP_LINE, but a non-comment line of a .tsv in registries/{s4r7,s3r4c2,s3r4c3} contains the file name and the
             line number (whole words).
    NO: neither.  stage_s4r8 and every r8m1 file are outside the search (U171, E8-51(c)).
    Returns (class, refs) where refs are at most three 'file:line' strings."""
    word = re.compile(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(basename))
    num = re.compile(r"(?<![0-9])%d(?![0-9])" % line)
    bp_refs = []
    stage_hits = []
    for d in USED_BP_DIRS:
        for p in _files_under(d, (".gdb", ".py")):
            with open(p, encoding="utf-8", errors="replace") as fh:
                for no, text in enumerate(fh, 1):
                    for m in BP_RE.finditer(text):
                        if os.path.basename(m.group(1)) == basename and int(m.group(2)) == line:
                            bp_refs.append("%s:%d" % (os.path.relpath(p, REPO), no))
                            stage_hits.append(p)
    # stage_s4 (.gdb/.py): counted only when the file name (whole word) occurs in a text file of the three stage
    # directories or of the three registry directories (.py/.sh/.gdb/.tsv/.txt)
    known_texts = []
    for d in USED_BP_DIRS + USED_REG_DIRS:
        for p in _files_under(d, USED_TEXT_EXT):
            with open(p, encoding="utf-8", errors="replace") as fh:
                known_texts.append(fh.read())
    s4_files = _files_under(USED_S4_DIR, (".gdb", ".py"))
    for p in s4_files:
        fn = os.path.basename(p)
        fn_word = re.compile(r"(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])" % re.escape(fn))
        if not any(fn_word.search(t) for t in known_texts):
            continue
        with open(p, encoding="utf-8", errors="replace") as fh:
            for no, text in enumerate(fh, 1):
                for m in BP_RE.finditer(text):
                    if os.path.basename(m.group(1)) == basename and int(m.group(2)) == line:
                        bp_refs.append("%s:%d" % (os.path.relpath(p, REPO), no))
    if bp_refs:
        return "BP_LINE", bp_refs[:3]
    reg_refs = []
    for d in USED_REG_DIRS:
        for p in _files_under(d, (".tsv",)):
            with open(p, encoding="utf-8", errors="replace") as fh:
                for no, text in enumerate(fh, 1):
                    if text.lstrip().startswith("#"):
                        continue
                    if word.search(text) and num.search(text):
                        reg_refs.append("%s:%d" % (os.path.relpath(p, REPO), no))
    if reg_refs:
        return "REGISTRY_ONLY", reg_refs[:3]
    return "NO", []


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
            # (3) CONT2c: no forbidden name may be a function-table entry; the driver's line 73 must be r6_probe
            names = set(t[1:len(lines) + 1])
            bad_names = sorted(names & FORBIDDEN_FUNC_NAMES)
            if bad_names:
                parser_bad += 1
                parser_rows.append([rev, path, "forbidden", ",".join(bad_names), "BAD", "forbidden function name in table"])
            if path == DRIVER:
                okd = t[73] == "r6_probe"
                if not okd:
                    parser_bad += 1
                parser_rows.append([rev, path, "line 73", t[73], "OK" if okd else "BAD", "expected r6_probe (driver self-check)"])
    for rev, expect_list in ((F2, SELFCHECK_F2), (F3, SELFCHECK_F3)):
        for path, n, want in expect_list:
            t, lines = tree_fn[(rev, path)]
            got = t[n]
            ok = got == want
            if not ok:
                parser_bad += 1
            parser_rows.append([rev, path, "line %d" % n, got, "OK" if ok else "BAD", "expected %s" % want])

    with open(OUT_PARSER, "x", encoding="utf-8") as fh:
        fh.write("# PARSER_SELFCHECK_R8_M1a3c.tsv -- P05-S4 R8 M1a CONT2c section 5 (U170 driver self-check; U154(b)). Written by map_f2_f3_r8m1a3c.py (read only).\n")
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
        ucls, urefs = used_class(os.path.basename(path), line_f2)   # (4) U171 three-valued column
        used_in_m1 = ucls + ((" " + ";".join(urefs)) if urefs else "")

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
        "# LINEMAP_F2_F3_R8_M1a3c.tsv -- P05-S4 R8 M1a CONT2c section 5 (map v3c; U170, U171).  Written by map_f2_f3_r8m1a3c.py (read only, git show / git diff).",
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
    # (5) CONT2c 5.1 formats; a line that matches none of them is UNPARSED and counts as MISMATCH
    FMT_COUNT = re.compile(r"^COUNT (MISSING|AMBIGUOUS|MODIFIED_BY_FIX|SAME_LINE|SHIFTED) (\d+)$")
    FMT_CHECK = re.compile(r"^CHECK (PARSER_SELFCHECK_BAD|DIFF_OFFSET_DISAGREE) (\d+)$")
    FMT_USEDCOUNT = re.compile(r"^USED_COUNT (BP_LINE|REGISTRY_ONLY|NO) (\d+)$")
    FMT_SITE = re.compile(r"^SITE (\S+) (\d+) F3 (\d+) (MISSING|AMBIGUOUS|MODIFIED_BY_FIX|SAME_LINE|SHIFTED) (\S+)$")
    FMT_USED = re.compile(r"^USED (\S+) (\d+) (BP_LINE|REGISTRY_ONLY|NO)$")
    FMT_SYMBOL = re.compile(r"^SYMBOL (\S+) F2 (\d+) F3 (\d+) PRESENT$")
    def got_count(status):
        return str(sum(1 for r in rows if r[8] == status))
    def got_check(name):
        if name == "PARSER_SELFCHECK_BAD":
            return str(parser_bad)
        return str(diff_counts.get("DISAGREE", 0))
    def got_usedcount(cls):
        return str(sum(1 for r in rows if r[11].split(" ")[0] == cls))
    for e in exp:
        m = FMT_COUNT.match(e)
        if m:
            want, got = m.group(2), got_count(m.group(1))
            ok = got == want
            res.append("%s\tCOUNT %s\texpected=%s\tactual=%s" % ("MATCH" if ok else "MISMATCH", m.group(1), want, got))
            if not ok:
                mismatch.append("COUNT " + m.group(1))
            continue
        m = FMT_CHECK.match(e)
        if m:
            want, got = m.group(2), got_check(m.group(1))
            ok = got == want
            res.append("%s\tCHECK %s\texpected=%s\tactual=%s" % ("MATCH" if ok else "MISMATCH", m.group(1), want, got))
            if not ok:
                mismatch.append("CHECK " + m.group(1))
            continue
        m = FMT_USEDCOUNT.match(e)
        if m:
            want, got = m.group(2), got_usedcount(m.group(1))
            ok = got == want
            res.append("%s\tUSED_COUNT %s\texpected=%s\tactual=%s" % ("MATCH" if ok else "MISMATCH", m.group(1), want, got))
            if not ok:
                mismatch.append("USED_COUNT " + m.group(1))
            continue
        m = FMT_SITE.match(e)
        if m:
            file_, line_, n_, status_, fn_ = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
            sel = [r for r in rows if r[1] == file_ and r[2] == line_]
            got_n = sel[0][5] if sel else "-"
            got_s = sel[0][8] if sel else "-"
            got_f = sel[0][6] if sel else "-"
            ok = (got_n == n_) and (got_s == status_) and (got_f == fn_)
            res.append("%s\tSITE %s:%s\texpected=F3 %s %s %s\tactual=F3 %s %s %s" % (
                "MATCH" if ok else "MISMATCH", file_, line_, n_, status_, fn_, got_n, got_s, got_f))
            if not ok:
                mismatch.append("SITE %s:%s" % (file_, line_))
            continue
        m = FMT_USED.match(e)
        if m:
            file_, line_, want = m.group(1), m.group(2), m.group(3)
            sel = [r for r in rows if r[1] == file_ and r[2] == line_]
            got = sel[0][11].split(" ")[0] if sel else "-"
            ok = got == want
            res.append("%s\tUSED %s:%s\texpected=%s\tactual=%s" % ("MATCH" if ok else "MISMATCH", file_, line_, want, got))
            if not ok:
                mismatch.append("USED %s:%s" % (file_, line_))
            continue
        m = FMT_SYMBOL.match(e)
        if m:
            sym = m.group(1)
            sel = [r for r in sym_rows if r[0] == sym]
            ok = bool(sel) and sel[0][7] == "OK" and sel[0][4] == "PRESENT" and sel[0][5] == "PRESENT" \
                and sel[0][2] == m.group(2) and sel[0][3] == m.group(3)
            res.append("%s\tSYMBOL %s\texpected=F2 %s F3 %s PRESENT\tactual=%s" % (
                "MATCH" if ok else "MISMATCH", sym, m.group(2), m.group(3),
                ("F2 %s F3 %s %s/%s" % (sel[0][2], sel[0][3], sel[0][4], sel[0][5])) if sel else "-"))
            if not ok:
                mismatch.append("SYMBOL " + sym)
            continue
        # (5) not one of the six formats: UNPARSED, counted as MISMATCH
        res.append("MISMATCH\tUNPARSED\texpected=six formats only\tactual=%s" % e)
        mismatch.append("UNPARSED")
    with open(OUT_CHECK, "x", encoding="utf-8") as fh:
        fh.write("# LINEMAP_CHECK_R8_M1a3c.txt -- item by item comparison with EXPECT_LINEMAP_R8_M1a3c.txt (written by map_f2_f3_r8m1a3c.py)\n")
        for r in res:
            fh.write(r + "\n")
        fh.write("# MISMATCH count: %d\n" % len(mismatch))

    # ---- (c) V2 vs V3 diff (LINEMAP_V2_V3_DIFF_R8_M1a3.txt): record only ----
    # (6) CONT2c: v3 (LINEMAP_F2_F3_R8_M1a3.tsv) against v3c (this run), per site: F3 line, function, status, used_in_m1.  Record only.
    v3old = {}
    with open(V3_TSV, encoding="utf-8") as fh:
        for l in fh:
            if l.startswith("#") or l.startswith("cited_by\t"):
                continue
            f = l.rstrip("\n").split("\t")
            if len(f) >= 12:
                v3old[(f[1], f[2])] = f
    v3c = {}
    for r in rows:
        v3c[(r[1], r[2])] = r
    dl = ["# LINEMAP_V3_V3C_DIFF_R8_M1a3c.txt -- v3 (LINEMAP_F2_F3_R8_M1a3.tsv) against v3c (LINEMAP_F2_F3_R8_M1a3c.tsv), per site.  Record only, no judgement (CONT2c 5.2 (6)).",
          "\t".join(["file", "F2_line", "v3_F3_line", "v3c_F3_line", "v3_F3_function", "v3c_F3_function", "v3_status", "v3c_status",
                     "v3_used_in_m1", "v3c_used_in_m1", "changed_columns"])]
    changed = 0
    chg_cols = {"F3_line": 0, "F3_function": 0, "status": 0, "used_in_m1": 0}
    for k in sorted(set(v3old) | set(v3c)):
        a = v3old.get(k)
        b = v3c.get(k)
        a_line = a[5] if a else "-"
        b_line = b[5] if b else "-"
        a_fn = a[6] if a else "-"
        b_fn = b[6] if b else "-"
        a_st = a[8] if a else "-"
        b_st = b[8] if b else "-"
        a_u = a[11] if a else "-"
        b_u = b[11] if b else "-"
        cols = []
        if a_line != b_line:
            cols.append("F3_line")
            chg_cols["F3_line"] += 1
        if a_fn != b_fn:
            cols.append("F3_function")
            chg_cols["F3_function"] += 1
        if a_st != b_st:
            cols.append("status")
            chg_cols["status"] += 1
        if a_u.split(" ")[0] != b_u.split(" ")[0]:
            cols.append("used_in_m1")
            chg_cols["used_in_m1"] += 1
        if cols:
            changed += 1
        dl.append("\t".join([k[0], k[1], a_line, b_line, a_fn, b_fn, a_st, b_st, a_u, b_u, ",".join(cols) if cols else "none"]))
    dl.append("# changed sites: %d; per column: %s" % (changed, ", ".join("%s=%d" % (k, chg_cols[k]) for k in chg_cols)))
    with open(OUT_DIFF, "x", encoding="utf-8") as fh:
        fh.write("\n".join(dl) + "\n")

    print("MAP_V3 sites=%d counts=%s diff_check=%s parser_bad=%d symbols_not_ok=%d check_mismatch=%d stops=%d" % (
        len(rows), ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)),
        ", ".join("%s=%d" % (k, diff_counts[k]) for k in sorted(diff_counts)), parser_bad, sym_fail, len(mismatch), len(stop)))
    return 0 if (not stop and parser_bad == 0 and sym_fail == 0 and not mismatch) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
