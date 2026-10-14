#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT1, section 4.3 (U145, U146, U147, U149(b)): static map v2 of the injection sites, F2 (a07b5ac) to F3 (8d8202a).

New file.  Copy of map_f2_f3_r8m1.py (committed in M1a, not modified) with these changes:
  (a) U149(b): the source of the FFT and kottke sites is PATTERN_MALLOC_CLASS_R7.tsv row 415 and U94 (not the r5 comment);
  (b) the two sites of testing/d003/stage_s4/r6_plan14_caller.gdb (fmm_FFT.cpp:90, fmm_kottke.cpp:94) are added;
  (c) breakpoint forms "break F:N", "tbreak F:N", LineBP("F:N", ...) and gdb.Breakpoint("F:N", ...) are scanned in every
      .gdb and .py file under stage_s4, stage_s4r7, stage_s3r4c2 and stage_s3r4c3; each such F:N becomes a site with
      anchor_use GDB_LINE_BP (the citing file and line are written); a site with no citation has anchor_use CLASSIFICATION_ONLY;
  (d) the function of each site is resolved in both trees by FUNCTION_RULE (below);
  (e) status: MODIFIED_BY_FIX only for U145/U146's three named sites, and only if all three U147 checks pass;
      otherwise a unique F3 text in the same function (or the U145 rename) gives SAME_LINE / SHIFTED;
      several F3 hits are disambiguated by function; if still not unique, AMBIGUOUS; if absent, MISSING.

Trees are read with git show (read only).  The output is a NEW file in $EV (refused if it exists, U17).
Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r8/map_f2_f3_r8m1a2.py
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
OUT = os.path.join(EV, "LINEMAP_F2_F3_R8_M1a2.tsv")
F2 = "a07b5ac"
F3 = "8d8202a"

FUNCTION_RULE = ("function of a line = the identifier of the most recent function head at brace depth 0 whose body "
                 "'{' opens at depth 0; a head is a line at depth 0 matching ^ident(...) that is not a control keyword; "
                 "lines before any head = FILE_SCOPE. Brace counting ignores // comments only.")
RENAME_F2_TO_F3 = {"shape_get_intersection_area_quad": "shape_get_intersection_area_quad_st"}  # U145, U148 (the only rename)

# (cited_by, file, F2 line, role)
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
    ("LINEMAP_M3_R7.tsv Part A (FUNC)", "S4/S4.cpp", 23, "declaration of Simulation_ComputeLayerModes"),
    ("LINEMAP_M3_R7.tsv Part A (FUNC)", "S4/S4.cpp", 32, "declaration of Simulation_GetLayerSolution"),
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

# U145/U146 named sites: (file, F2 line) -> spec.  core = the F2 expression that must be a substring of the F3 line (U147 ii).
MODIFIED_BY_FIX_SITES = {
    ("S4/pattern/pattern.c", 415): dict(f3_line=418, f3_func="shape_get_intersection_area_quad_st",
                                        core="malloc(sizeof(int)*3*(s->vtab.polygon.n_vertices-2))"),
    ("S4/fmm/fmm_FFT.cpp", 98): dict(f3_line=101, f3_func="FMMGetEpsilon_FFT",
                                     core="Pattern_DiscretizeCell(&L->pattern,S->Lr,ngrid[0],ngrid[1],ii[0],ii[1],discval)"),
    ("S4/fmm/fmm_kottke.cpp", 102): dict(f3_line=105, f3_func="FMMGetEpsilon_Kottke",
                                         core="Pattern_DiscretizeCell(&L->pattern,S->Lr,ngrid[0],ngrid[1],ii[0],ii[1],discval)"),
}

# the four F2-side functions named by U145 for line 415 (for the F2 function column check)
CONTROL_KEYWORDS = {"if", "for", "while", "switch", "return", "else", "do", "sizeof"}


def git_show(rev, path):
    p = subprocess.run(["git", "show", "%s:%s" % (rev, path)], cwd=REPO, capture_output=True)
    if p.returncode != 0:
        return None
    return p.stdout.decode("utf-8", errors="replace").split("\n")


def function_table(lines):
    """Return a list t with t[n] = function name of 1-based line n (FILE_SCOPE if none), by FUNCTION_RULE."""
    t = ["FILE_SCOPE"] * (len(lines) + 2)
    depth = 0
    pending = None
    body = None  # (name, depth at which the body was opened)
    for no, raw in enumerate(lines, 1):
        text = raw.split("//")[0]
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
                if body is not None and depth == body[1]:
                    body = None
            elif ch == ";" and depth == 0:
                pending = None
        t[no] = body[0] if body is not None else "FILE_SCOPE"
    return t


def collect_gdb_citations():
    """All F:N citations in the four stage directories (gdb and py), four forms of brief 4.3."""
    dirs = ["testing/d003/stage_s4", "testing/d003/stage_s4r7", "testing/d003/stage_s3r4c2", "testing/d003/stage_s3r4c3"]
    pat = re.compile(r"(?:\bt?break\s+|LineBP\(\"|gdb\.Breakpoint\(\")([A-Za-z0-9_./-]+\.(?:cpp|cc|c|h|hpp))\s*:\s*(\d+)")
    out = []
    for d in dirs:
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
                segs.append((start, start))  # pure deletion: the line after the deletion point
            else:
                segs.append((start, start + count - 1))
    return any(a - 1 <= f3_line <= b + 1 for a, b in segs)


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: map_f2_f3_r8m1a2.py  (no arguments)")
    if os.path.exists(OUT):
        raise SystemExit("REFUSED: exists (U17): %s" % OUT)

    citations = collect_gdb_citations()
    # gdb citations are keyed by (basename, line); a citation of a file not in S4 (driver) is a driver-source anchor
    cite_by_key = {}
    for rel, no, base, line in citations:
        cite_by_key.setdefault((base, line), []).append("%s:%d" % (rel, no))

    # the site list = the committed sites above + every gdb citation (as an F2 line of its file)
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
            rows.append([cited_by, path, str(line_f2), "-", "-", "-", "-", "-", "MISSING", role, "-"])
            continue
        if not (1 <= line_f2 <= len(f2_lines)):
            stop.append("F2 line out of range: %s:%d" % (path, line_f2))
            rows.append([cited_by, path, str(line_f2), "-", "-", "-", "-", "-", "AUDIT_OUT_OF_RANGE", role, "-"])
            continue
        key = f2_lines[line_f2 - 1].strip()
        if key == "":
            stop.append("F2 line is blank: %s:%d" % (path, line_f2))
            rows.append([cited_by, path, str(line_f2), "", "-", "-", "-", "-", "AUDIT_BLANK", role, "-"])
            continue
        if (F2, path) not in fn_cache:
            fn_cache[(F2, path)] = function_table(f2_lines)
        f2_fn = fn_cache[(F2, path)][line_f2]
        if (F3, path) not in cache:
            cache[(F3, path)] = git_show(F3, path)
        f3_lines = cache[(F3, path)]
        if f3_lines is None:
            stop.append("F3 file missing: %s" % path)
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, "-", "-", "-", "MISSING", role, "-"])
            continue
        if (F3, path) not in fn_cache:
            fn_cache[(F3, path)] = function_table(f3_lines)
        f3_fn = fn_cache[(F3, path)]
        anchor_hits = cite_by_key.get((os.path.basename(path), line_f2), [])
        anchor_use = ("GDB_LINE_BP " + ";".join(anchor_hits)) if anchor_hits else "CLASSIFICATION_ONLY"

        mod = MODIFIED_BY_FIX_SITES.get((path, line_f2))
        if mod is not None:
            n = mod["f3_line"]
            i_ok = in_added_segment(path, n)
            f3_text = f3_lines[n - 1] if 1 <= n <= len(f3_lines) else ""
            ii_ok = mod["core"] in f3_text.replace(" ", "")
            iii_ok = f3_fn[n] == mod["f3_func"]
            # the F2 function of the site must be the function U145/U146 names (F2 side); 415 is in shape_get_intersection_area_quad
            f2_expected = "shape_get_intersection_area_quad" if path.endswith("pattern.c") else f2_fn
            f2_ok = f2_fn == f2_expected
            if i_ok and ii_ok and iii_ok and f2_ok:
                status = "MODIFIED_BY_FIX"
            else:
                status = "MISSING"
                stop.append("U147 check failed %s:%d (i=%s ii=%s iii=%s f2fn_ok=%s f3fn=%s)" % (
                    path, line_f2, i_ok, ii_ok, iii_ok, f2_ok, f3_fn[n]))
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, str(n), f3_fn[n],
                         "U147(i=%s,ii=%s,iii=%s,f2=%s)" % (i_ok, ii_ok, iii_ok, f2_ok), status, role, anchor_use])
            continue

        hits = [i for i, t in enumerate(f3_lines, 1) if t.strip() == key]
        f2_renamed = RENAME_F2_TO_F3.get(f2_fn, f2_fn)
        if len(hits) == 0:
            stop.append("MISSING: %s:%d '%s'" % (path, line_f2, key[:70]))
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, "-", "-", "-", "MISSING", role, anchor_use])
            continue
        if len(hits) == 1:
            h = hits[0]
            hf = f3_fn[h]
            if hf not in (f2_fn, f2_renamed) and f2_fn != "FILE_SCOPE":
                stop.append("AMBIGUOUS (function differs, unique text): %s:%d F2 fn=%s F3 fn=%s" % (path, line_f2, f2_fn, hf))
                rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, str(h), hf, "-", "AMBIGUOUS", role, anchor_use])
                continue
            status = "SAME_LINE" if h == line_f2 else "SHIFTED"
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, str(h), hf, "-", status, role, anchor_use])
            continue
        same = [h for h in hits if f3_fn[h] in (f2_fn, f2_renamed)]
        if len(same) == 1:
            h = same[0]
            status = "SAME_LINE" if h == line_f2 else "SHIFTED"
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, str(h), f3_fn[h], "disambig_by_fn",
                         status, role, anchor_use])
        else:
            stop.append("AMBIGUOUS: %s:%d '%s' F3 lines %s; after function disambiguation %s" % (
                path, line_f2, key[:70], ",".join(map(str, hits)), ",".join(map(str, same)) or "none"))
            rows.append([cited_by, path, str(line_f2), key[:120], f2_fn, ",".join(map(str, hits)), "-",
                         "-", "AMBIGUOUS", role, anchor_use])

    counts = {}
    for r in rows:
        counts[r[8]] = counts.get(r[8], 0) + 1
    lines = [
        "# LINEMAP_F2_F3_R8_M1a2.tsv -- P05-S4 R8 M1a CONT1 section 4.3 (map v2; U145-U147, U149(b)).  Written by map_f2_f3_r8m1a2.py (read only, git show).",
        "# F2 = a07b5ac (S4 e124925f5b242486a913b813fa181664f665b048), F3 = 8d8202a (S4 6cff923a02baf19e01966b2339755cbf3a5deeef).",
        "# Function rule: " + FUNCTION_RULE,
        "# Rename (U145, U148): F2 shape_get_intersection_area_quad == F3 shape_get_intersection_area_quad_st.",
        "# MODIFIED_BY_FIX only for U145/U146's three sites after U147 (i) diff segment, (ii) core substring, (iii) F3 function.",
        "\t".join(["cited_by", "file", "F2_line", "F2_text_key", "F2_function", "F3_line", "F3_function", "note",
                  "status", "role", "anchor_use"]),
    ]
    for r in rows:
        lines.append("\t".join(r))
    lines.append("# counts: " + ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)))
    lines.append("# sites: %d; gdb_citations_scanned: %d" % (len(rows), len(citations)))
    lines.append("# stops: %d" % len(stop))
    for s in stop:
        lines.append("# STOP: " + s)
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("LINEMAP_V2 sites=%d counts=%s stops=%d -> %s" % (
        len(rows), ", ".join("%s=%d" % (k, counts[k]) for k in sorted(counts)), len(stop), OUT))
    return 0 if not stop else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
