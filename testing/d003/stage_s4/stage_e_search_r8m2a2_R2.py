#!/usr/bin/env python3
# stage_e_search_r8m2a2_R2.py -- P05-S4 R8 M2a2 CONT1 section 4: stage e search table, version R2 (M2-02).
# Replaces (does not overwrite) STAGE_E_SEARCH_R8_M2a2.tsv (R1, kept, SUPERSEDED: hard-coded strings, summary row, wrong line numbers).
# Part A: one output row per registered request (U2_STAGE_R6d.tsv 202 rows + SEAM_SITE_STAGE_R6d.tsv 25 rows = 227).
# Part B: candidates outside ComputeLayerModes found by scanning the exported F3 tree (fft/alloc/plan/S4_malloc/AddFieldToCache).
# Output: $EV/STAGE_E_SEARCH_R8_M2a2_R2.tsv
import os
import re
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
TREE = os.path.join(EV, "tree_F3", "S4")
OUT = os.path.join(EV, "STAGE_E_SEARCH_R8_M2a2_R2.tsv")
U2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r6d", "U2_STAGE_R6d.tsv")
SEAM = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r6d", "SEAM_SITE_STAGE_R6d.tsv")
U2_EXPECT = {"a": 2, "b": 197, "c": 1, "d": 2}
SEAM_EXPECT = {"a": 2, "b": 20, "c": 1, "d": 2}
PATTERNS = ["fft_plan_dft_2d", "fft_plan_exec", "fft_alloc_complex", "S4_malloc", "Simulation_AddFieldToCache"]


def data_rows(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    return head, [dict(zip(head, l.split("\t"))) for l in lines[1:]], lines


def function_range(lines, header_line):
    """1-based (start, end) of the function whose header is at header_line, by brace matching."""
    depth = 0
    seen = False
    for i in range(header_line - 1, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
                seen = True
            elif ch == "}":
                depth -= 1
        if seen and depth == 0:
            return header_line, i + 1
    return header_line, len(lines)


def enclosing_function(lines, lineno):
    """Nearest preceding line that looks like a function header (name(...) with '{' on the same or next line)."""
    hdr = re.compile(r"^[A-Za-z_][\w \t\*&:<>,]*[\s\*&]([A-Za-z_][\w:]*)\s*\([^;]*$")
    for i in range(lineno - 1, -1, -1):
        l = lines[i]
        if l[:1] in (" ", "\t", "#", "/", "}", "{") or not l.strip():
            continue
        m = hdr.match(l)
        if m and not re.match(r"^\s*(if|for|while|switch|return)\b", l):
            return m.group(1), i + 1
    return "?", 0


def main():
    if os.path.exists(OUT):
        print("stage_e_search_r8m2a2_R2: REFUSED exists (U17)")
        return 2
    rows = []
    fails = []

    # ---------- Part A ----------
    _, u2, _ = data_rows(U2)
    _, seam, _ = data_rows(SEAM)
    a_u2_counts = {}
    a_rows_out = []
    for idx, r in enumerate(u2):
        a_u2_counts[r["stage"]] = a_u2_counts.get(r["stage"], 0) + 1
        is_e = (r["stage"] == "e")
        a_rows_out.append([r["point_id"], "U2_STAGE_R6d.tsv", "line %d" % (idx + 3), r["stage"],
                           r["basis"][:200], "YES" if is_e else "NO", "IN_SCOPE_D003_REGISTERED",
                           "registered request (U2); stage column of the source table"])
    a_seam_counts = {}
    for idx, r in enumerate(seam):
        a_seam_counts[r["stage"]] = a_seam_counts.get(r["stage"], 0) + 1
        is_e = (r["stage"] == "e")
        a_rows_out.append([r["point_id"], "SEAM_SITE_STAGE_R6d.tsv", "line %d" % (idx + 3), r["stage"],
                           "%s:%s" % (r["file"], r["line"]), "YES" if is_e else "NO", "IN_SCOPE_D003_REGISTERED",
                           "registered seam site (SEAM); stage column of the source table"])
    rows.extend(a_rows_out)
    a_rows = len(u2) + len(seam)
    check = []
    for k in ("a", "b", "c", "d"):
        check.append(("U2_" + k, a_u2_counts.get(k, 0) == U2_EXPECT[k]))
        check.append(("SEAM_" + k, a_seam_counts.get(k, 0) == SEAM_EXPECT[k]))
    for name, ok in check:
        if not ok:
            fails.append("A-count " + name)
    if a_rows != 227:
        fails.append("A rows %d != 227" % a_rows)
    stage_e_a = a_u2_counts.get("e", 0) + a_seam_counts.get("e", 0)
    if stage_e_a != 0:
        fails.append("A stage e count %d != 0" % stage_e_a)

    # ---------- Part B ----------
    s4 = open(os.path.join(TREE, "S4.cpp"), encoding="utf-8", errors="replace").read().split("\n")
    clm_hdr = next((i for i, l in enumerate(s4, 1) if re.match(r"^int Simulation_ComputeLayerModes\(.*\)\s*\{", l)), 0)
    if clm_hdr == 0:
        fails.append("CLM header not found")
        clm_start, clm_end = 0, 0
    else:
        clm_start, clm_end = function_range(s4, clm_hdr)
    b_rows = 0
    src_files = []
    for root, _dirs, files in os.walk(TREE):
        for f in files:
            if f.endswith((".cpp", ".c")) and "kiss_fft" not in root and "RNP" not in root:
                src_files.append(os.path.join(root, f))
    src_files.sort()
    b_out = []
    for path in src_files:
        if not (path.endswith("rcwa.cpp") or path.endswith("S4.cpp") or "/fmm/" in path):
            continue
        lines = open(path, encoding="utf-8", errors="replace").read().split("\n")
        rel = os.path.relpath(path, EV)
        for i, l in enumerate(lines, 1):
            if re.match(r"^\s*(//|\*|/\*)", l):
                continue
            for pat in PATTERNS:
                if not re.search(r"\b%s\s*\(" % pat, l):
                    continue
                # a definition or declaration has the return type before the name at column 0 and no call-site '='
                if re.match(r"^[A-Za-z_][\w\s\*&:<>,]*\s\*?\s*%s\s*\(" % pat, l) and "=" not in l:
                    continue
                if re.match(r"^\s*(extern|static)\b", l) and "=" not in l:
                    continue
                fn, _fn_line = enclosing_function(lines, i)
                in_clm = (path.endswith("S4.cpp") and clm_start <= i <= clm_end)
                b_out.append((pat, rel, i, fn, in_clm, path, l.strip()[:160]))
                b_rows += 1

    # scope of each B row (rule text; each class is determined by the call location, not by a list of verdicts):
    #   IN_CLM_BODY        : inside Simulation_ComputeLayerModes body -> stage a-d (not e)
    #   FMM_CALLED_FROM_CLM: inside fmm/*.cpp; fmm_* functions are only reached from CLM (stage a-d), see the grep in the report
    #   GETFIELD_E6_4      : rcwa.cpp GetFieldOnGrid (E6-4: outside D003 scope, U5b)
    #   NON_FMM_S5         : S4.cpp outside CLM, non-FMM S4_malloc (out of D003 scope, destination S5)
    #   GETFIELD_CALLER    : S4.cpp Simulation_GetFieldPlane / S4_Simulation_GetPowerFlux / InitSolution (outside CLM, not FMM failure path)
    b_stage_e = 0
    b_in_scope = 0
    for pat, rel, i, fn, in_clm, path, text in b_out:
        if in_clm:
            cls = "IN_CLM_BODY"
        elif "/fmm/" in path:
            cls = "FMM_CALLED_FROM_CLM"
        elif path.endswith("rcwa.cpp"):
            cls = "GETFIELD_E6_4"          # GetFieldOnGrid (E6-4, U5b): the FFT plan / alloc / exec of the field grid
        else:
            cls = "NON_FMM_S5"             # S4.cpp outside CLM: field/power/solution buffers, not on the FMM failure path
        # stage e = failure outside every ENTER/RETURN window of ComputeLayerModes AND on the FMM failure path.
        # IN_CLM_BODY and FMM_CALLED_FROM_CLM are stage a-d by construction; the other classes are not on the FMM failure
        # path of the layer modes (E6-4, U5b; non-FMM S4_malloc -> S5).  Hence stage e count = 0 by these rules.
        if cls in ("IN_CLM_BODY", "FMM_CALLED_FROM_CLM"):
            in_scope = "IN_SCOPE_STAGE_A_TO_D"
        elif cls == "GETFIELD_E6_4":
            in_scope = "OUT_OF_SCOPE_D003_E6-4"
        else:
            in_scope = "OUT_OF_SCOPE_D003_S5"
        stage = "NOT_E"
        if in_scope == "IN_SCOPE_STAGE_A_TO_D":
            b_in_scope += 1
        rows.append(["B:" + pat, rel, str(i), fn, "YES" if in_clm else "NO", cls, in_scope, text])
        if stage == "E":
            b_stage_e += 1

    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# STAGE_E_SEARCH_R8_M2a2_R2 -- P05-S4 R8 M2a2 CONT1 section 4 (M2-02)\n")
        fh.write("# Part A: 227 registered requests (U2_STAGE_R6d 202 + SEAM_SITE_STAGE_R6d 25); stage taken from the source table.\n")
        fh.write("# Part B: calls to fft_plan_dft_2d / fft_plan_exec / fft_alloc_complex / S4_malloc / Simulation_AddFieldToCache\n")
        fh.write("#         found by scan of tree F3; CLM body = S4.cpp:%d-%d (brace matched).  Definition: ERRATA_6d.txt E6d-3.\n" % (clm_start, clm_end))
        fh.write("# CHECK_FAILS=%d\n" % len(fails))
        for x in fails:
            fh.write("# CHECK_FAIL %s\n" % x)
        fh.write("# PART_A\n")
        fh.write("\t".join(["candidate_id", "source_table_or_file", "row_or_line", "stage", "location_or_basis", "stage_e",
                            "in_scope_d003", "basis"]) + "\n")
        for r in a_rows_out:
            fh.write("\t".join(str(x) for x in r) + "\n")
        fh.write("# PART_B\n")
        fh.write("\t".join(["candidate_id", "file", "line", "function", "in_CLM", "reached_by", "scope", "source_text_or_basis"]) + "\n")
        for r in rows:
            if not r[0].startswith("B:"):
                continue
            fh.write("\t".join(str(x) for x in r) + "\n")
        stage_e_a = sum(1 for r in a_rows_out if r[5] == "YES")
        in_scope_b = sum(1 for r in rows if r[0].startswith("B:") and r[6] == "IN_SCOPE_STAGE_A_TO_D")
        b_stage_e_n = sum(1 for r in rows if r[0].startswith("B:") and r[5] == "STAGE_E")
        fh.write("# SUMMARY: A_ROWS=%d B_ROWS=%d STAGE_E_IN_SCOPE=%d\n" % (a_rows, b_rows, stage_e_a + b_stage_e_n))
        fh.write("# B_IN_SCOPE_COUNT=%d (calls inside CLM or the fmm_* path; stage a-d, not stage e)\n" % in_scope_b)
        fh.write("# M2_02=%s\n" % ("NOT_FOUND_IN_SCOPE" if (stage_e_a + b_stage_e_n) == 0 else "FOUND"))
    print("stage_e_search_r8m2a2_R2: A_ROWS=%d B_ROWS=%d fails=%d" % (a_rows, b_rows, len(fails)))
    return 0 if not fails else 3


if __name__ == "__main__":
    sys.exit(main())
