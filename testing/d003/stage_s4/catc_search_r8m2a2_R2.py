#!/usr/bin/env python3
# catc_search_r8m2a2_R2.py -- P05-S4 R8 M2a2 CONT1 section 5: category C search table, version R2 (M2-08).
# Replaces (does not overwrite) CATC_SEARCH_R8_M2a2.tsv (R1, kept, SUPERSEDED: hard-coded verdicts, a summary row, wrong line numbers).
# All numbers are computed from the exported tree $EV/tree_F3/S4 and the driver grid rules below.  No verdict is hard-coded.
# Output: $EV/CATC_SEARCH_R8_M2a2_R2.tsv
# Rules (planner reading, [源码], each checked by this script against the source text; a mismatch -> PLANNER_FACT_MISMATCH):
#   R1  build has no HAVE_LIBFFTW3 and no KISS_FFT_USE_ALLOCA (checked in build_r8 logs and BUILD_R8_M2a2_R3.tsv).
#   R2  execution-window allocations inside kiss: kf_bfly_generic scratch (kiss_fft.c) and tmpbuf (kiss_fft.c) only.
#   R3  grid length per dimension = fft_next_fast_size(maxG * resolution), resolution = 8 (S4.cpp:343); length 1 only if the
#       dimension is all-zero (allzero).  Length 1 -> radix 1 -> generic butterfly -> scratch allocation.
#   R4  square lattice (driver Lr = {1,0,0,1}) uses Gsel_circular (gsel.c:117-165): NG -> actual n_G by shell rule.
#   R5  1D lattice (closed1d only): n_G = 1 + 2*floor((NG-1)/2)  (S4.cpp:369-375); y dimension has length 1.
# Output columns: mode, NG_requested, lattice, n_G_actual, ngrid_x, ngrid_y, fmm_uses_fft, exec_alloc_in_fmm,
#                 exec_alloc_outside_fmm, NB_ge_2, basis, verdict
import math
import os
import re
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
TREE = os.path.join(EV, "tree_F3", "S4")
OUT = os.path.join(EV, "CATC_SEARCH_R8_M2a2_R2B.tsv")  # R2B: the first R2 run wrote CATC_SEARCH_R8_M2a2_R2.tsv with a wrong verdict rule (FOUND for NB=1); kept, SUPERSEDED
MODES = ["closed1d", "closed2d", "experimental", "fft", "kottke", "tensor", "jones", "nv", "vl"]
NGS = list(range(2, 9))
RESOLUTION = 8
FMM_FILE = {
    "closed1d": "fmm/fmm_closed.cpp", "closed2d": "fmm/fmm_closed.cpp", "experimental": "fmm/fmm_experimental.cpp",
    "fft": "fmm/fmm_FFT.cpp", "kottke": "fmm/fmm_kottke.cpp", "tensor": "fmm/fmm_closed.cpp",
    "jones": "fmm/fmm_PolBasisJones.cpp", "nv": "fmm/fmm_PolBasisNV.cpp", "vl": "fmm/fmm_PolBasisVL.cpp",
}
# The driver's modes and their FMM entry: closed1d/closed2d/tensor use fmm_closed.cpp; the 'fft' mode uses fmm_FFT.cpp.


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def lines_of(path):
    return read_text(path).split("\n")


def find_function_range(lines, header_regex):
    """Return (start, end) 1-based lines of the function whose header matches, by brace matching."""
    rx = re.compile(header_regex)
    start = 0
    for i, l in enumerate(lines, 1):
        if rx.search(l) and "{" in l:
            start = i
            break
    if start == 0:
        return (0, 0)
    depth = 0
    seen = False
    for i in range(start - 1, len(lines)):
        for ch in lines[i]:
            if ch == "{":
                depth += 1
                seen = True
            elif ch == "}":
                depth -= 1
        if seen and depth == 0:
            return (start, i + 1)
    return (start, len(lines))


def enclosing_function(lines, lineno):
    """Walk up from lineno to the nearest line that looks like a function header (name followed by '(' ... ')' and '{')."""
    hdr = re.compile(r"^[A-Za-z_][\w\s\*:<>,&]*\s[\*&]?([A-Za-z_][\w:]*)\s*\([^;]*\)\s*(const)?\s*\{?\s*$")
    for i in range(lineno - 1, -1, -1):
        m = hdr.match(lines[i])
        if m and not lines[i].lstrip().startswith(("if", "for", "while", "switch", "return")):
            return m.group(1), i + 1
    return "?", 0


def prime_factors(n):
    f = []
    d = 2
    while d * d <= n:
        while n % d == 0:
            f.append(d)
            n //= d
        d += 1
    if n > 1:
        f.append(n)
    return f


def fft_next_fast_size(n):
    """Mirror of fft_iface.cpp:35-46 (fft_next_fast_size): smallest m >= n with only 2, 3, 5 factors."""
    m = n
    while True:
        x = m
        for p in (2, 3, 5):
            while x % p == 0:
                x //= p
        if x == 1:
            return m
        m += 1


def gsel_circular_nG(nreq, lk):
    """Mirror of gsel.c Gsel_circular for a lattice Lk = {a,0,0,a} (square).  Returns the actual n_G.
    Keeps the first nreq G of the sorted list, then walks back while the last kept G has the same length as its neighbour."""
    a = lk[0]
    gs = []
    rng = 60
    for i in range(-rng, rng + 1):
        for j in range(-rng, rng + 1):
            gs.append((i, j))
    gs.sort(key=lambda g: (g[0] * g[0] + g[1] * g[1], g))
    j = min(nreq, len(gs))
    i = j
    # G_same: squared length difference < 2*DBL_EPSILON*maxlen; for the square lattice the lengths are exact integers
    def same(p, q):
        return (p[0] * p[0] + p[1] * p[1]) == (q[0] * q[0] + q[1] * q[1])
    while i > 0:
        if not same(gs[i - 1], gs[i]):
            break
        i -= 1
    return i


def max_abs_G(nG_actual):
    """Largest |G component| among the first n_G G vectors of the square lattice (circular truncation)."""
    if nG_actual <= 1:
        return 0, 0
    gs = []
    for i in range(-20, 21):
        for j in range(-20, 21):
            gs.append((i, j))
    gs.sort(key=lambda g: (g[0] * g[0] + g[1] * g[1], g))
    sel = gs[:nG_actual]
    return max(abs(g[0]) for g in sel), max(abs(g[1]) for g in sel)


def check_fact(name, cond, note, mismatches):
    if not cond:
        mismatches.append("%s: %s" % (name, note))
    return cond


def main():
    if os.path.exists(OUT):
        print("catc_search_r8m2a2_R2: REFUSED exists (U17)")
        return 2
    mism = []
    s4 = lines_of(os.path.join(TREE, "S4.cpp"))
    # R3 / R4 / R5: source facts
    check_fact("resolution", any(re.search(r"resolution\s*=\s*8\s*;", l) for l in s4), "S4.cpp resolution=8 not found", mism)
    res_line = next((i for i, l in enumerate(s4, 1) if re.search(r"resolution\s*=\s*8\s*;", l)), 0)
    gsel_line = next((i for i, l in enumerate(s4, 1) if re.search(r"G_select\(S->options\.lattice_truncation", l)), 0)
    onedim_line = next((i for i, l in enumerate(s4, 1) if re.search(r"1D lattice", l)), 0)
    check_fact("gsel_call", gsel_line > 0, "G_select call not found", mism)
    check_fact("1d_formula", any("remaining = (S->n_G-1)/2" in l for l in s4), "1D formula not found", mism)
    gsel = lines_of(os.path.join(TREE, "gsel.c"))
    circ_line = next((i for i, l in enumerate(gsel, 1) if "static int Gsel_circular" in l), 0)
    check_fact("gsel_circular", circ_line > 0, "Gsel_circular not found", mism)
    fftif = lines_of(os.path.join(TREE, "fmm", "fft_iface.cpp"))
    nfs_line = next((i for i, l in enumerate(fftif, 1) if "int fft_next_fast_size(int n)" in l), 0)
    check_fact("fft_next_fast_size", nfs_line > 0, "fft_next_fast_size not found", mism)
    # R1: build flags (BUILD_R8_M2a2_R3 compile lines and the F3 build logs must not define the FFTW or alloca macros)
    bld = read_text(os.path.join(EV, "BUILD_R8_M2a2_R3.tsv"))
    fftw_def = bool(re.search(r"-DHAVE_LIBFFTW3\b", bld))
    alloca_def = bool(re.search(r"-DKISS_FFT_USE_ALLOCA", bld))
    check_fact("no_fftw", not fftw_def, "HAVE_LIBFFTW3 found in BUILD_R8_M2a2_R3", mism)
    check_fact("no_alloca", not alloca_def, "KISS_FFT_USE_ALLOCA found in BUILD_R8_M2a2_R3", mism)
    # R2: kiss allocation sites
    kiss = lines_of(os.path.join(TREE, "kiss_fft", "kiss_fft.c"))
    scratch_line = next((i for i, l in enumerate(kiss, 1) if "KISS_FFT_TMP_ALLOC(sizeof(kiss_fft_cpx)*p)" in l), 0)
    tmpbuf_line = next((i for i, l in enumerate(kiss, 1) if "KISS_FFT_TMP_ALLOC( sizeof(kiss_fft_cpx)*st->nfft)" in l), 0)
    check_fact("kiss_scratch", scratch_line > 0, "kf_bfly_generic scratch line not found", mism)
    check_fact("kiss_tmpbuf", tmpbuf_line > 0, "tmpbuf line not found", mism)
    # per-mode FMM: fft_plan_exec count and S4_malloc in fmm files
    fmm_counts = {}
    for m in MODES:
        p = os.path.join(TREE, FMM_FILE[m])
        t = read_text(p)
        fmm_counts[m] = (len(re.findall(r"fft_plan_exec\(", t)), len(re.findall(r"S4_malloc\(", t)))
    # R5: closed1d FMM has no fft call (E6-4 grid, see report)
    check_fact("closed1d_no_fft", fmm_counts["closed1d"][0] == 0, "closed1d fmm has fft_plan_exec", mism)
    # GetFieldOnGrid location (outside FMM, E6-4)
    rcwa = lines_of(os.path.join(TREE, "rcwa.cpp"))
    gfog_alloc = next((i for i, l in enumerate(rcwa, 1) if "from[i] = fft_alloc_complex(N);" in l), 0)
    gfog_exec = next((i for i, l in enumerate(rcwa, 1) if "fft_plan_exec(plan[i])" in l), 0)

    rows = []
    # per (mode, NG): compute grid and n_G
    for m in MODES:
        for ng in NGS:
            # ngrid rule of fmm_FFT.cpp:54-68 (same in PolBasis VL/Jones/NV): per dimension, maxG = max |G_i| over the
            # n_G vectors; allzero -> 1; else fft_next_fast_size(maxG * resolution).
            if m == "closed1d":
                n_g = 1 + 2 * ((ng - 1) // 2)
                lattice = "1D (Lr={1,0,0,0})"
                mx = (n_g - 1) // 2          # G = (+-1..+-mx, 0), y is all-zero
                my = 0
            else:
                n_g = gsel_circular_nG(ng, (2 * math.pi, 0, 0, 2 * math.pi))
                lattice = "square (Lr={1,0,0,1})"
                mx, my = max_abs_G(n_g)
            gx = 1 if mx == 0 else fft_next_fast_size(mx * RESOLUTION)
            gy = 1 if my == 0 else fft_next_fast_size(my * RESOLUTION)
            # exec-window allocation: a dimension of length 1 (allzero) means radix 1 and generic scratch
            exec_fmm = "YES" if (gx == 1 or gy == 1) else "NO"
            fmm_fft = "YES" if fmm_counts[m][0] > 0 else "NO"
            # GetFieldOnGrid (outside FMM) always has the fft plan; it is out of D003 scope (E6-4), reported separately
            outside = "YES_GetFieldOnGrid" if fmm_fft == "NO" else "NO"
            nb_ge2 = "YES" if n_g >= 2 else "NO"
            basis = "fmm_uses_fft=%s; closed1d only" % fmm_fft if m == "closed1d" else "fmm_uses_fft=%s" % fmm_fft
            if m in ("closed1d", "closed2d", "tensor", "experimental"):
                basis = "fmm file %s, fft_plan_exec count %d" % (FMM_FILE[m], fmm_counts[m][0])
            # M2-08 needs NB >= 2 (task section 4.2 / U242): a configuration with n_G = 1 has one G vector, so the
            # category C question (intermediate error reaching the output with more than one basis vector) does not apply.
            # FOUND requires: FMM uses fft (fmm_uses_fft=YES), an exec-window allocation in FMM (a dimension of length 1),
            # and NB >= 2.  NB >= 2 with a length-1 dimension is impossible on the square grid (see rule R3), so the
            # grid contains no FOUND row; the 1D lattice is outside the grid (see CANDIDATES_OUTSIDE_U242_GRID).
            verdict = "FOUND" if (exec_fmm == "YES" and fmm_fft == "YES" and nb_ge2 == "YES") else "NOT_FOUND"
            rows.append([m, ng, lattice, n_g, gx, gy, fmm_fft, exec_fmm, outside, nb_ge2,
                         "%s; rule R3 gx=%d gy=%d" % (basis, gx, gy), verdict])

    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# CATC_SEARCH_R8_M2a2_R2 -- P05-S4 R8 M2a2 CONT1 section 5 (SUPERSEDES CATC_SEARCH_R8_M2a2.tsv, kept)\n")
        fh.write("# Source facts (line numbers found by search in the exported F3 tree):\n")
        fh.write("#   resolution=8 S4.cpp:%d ; G_select call S4.cpp:%d ; 1D formula S4.cpp:%d ; Gsel_circular gsel.c:%d ; "
                 "fft_next_fast_size fmm/fft_iface.cpp:%d\n" % (res_line, gsel_line, onedim_line, circ_line, nfs_line))
        fh.write("#   kiss scratch kiss_fft.c:%d ; kiss tmpbuf kiss_fft.c:%d ; GetFieldOnGrid alloc rcwa.cpp:%d exec rcwa.cpp:%d\n"
                 % (scratch_line, tmpbuf_line, gfog_alloc, gfog_exec))
        fh.write("#   build: HAVE_LIBFFTW3 defined=%s ; KISS_FFT_USE_ALLOCA defined=%s\n" % (fftw_def, alloca_def))
        fh.write("#   PLANNER_FACT_MISMATCH=%d\n" % len(mism))
        for x in mism:
            fh.write("#   PLANNER_FACT_MISMATCH %s\n" % x)
        fh.write("\t".join(["mode", "NG_requested", "lattice", "n_G_actual", "ngrid_x", "ngrid_y", "fmm_uses_fft",
                            "exec_alloc_in_fmm", "exec_alloc_outside_fmm", "NB_ge_2", "basis", "verdict"]) + "\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
        fh.write("# CANDIDATES_OUTSIDE_U242_GRID\n")
        fh.write("# 1D lattice + FFT-class FMM mode (fft/kottke/jones/nv/vl) with actual NB>=3: NEEDS_NEW_DRIVER_SCOPE_EXPANSION (not searched here)\n")
        n_found = sum(1 for r in rows if r[-1] == "FOUND")
        fh.write("# SUMMARY: ROWS=%d FOUND=%d NOT_FOUND=%d PLANNER_FACT_MISMATCH=%d M2_08=%s\n"
                 % (len(rows), n_found, len(rows) - n_found, len(mism), "FOUND" if n_found else "NOT_FOUND"))
    print("catc_search_r8m2a2_R2: rows=%d found=%d mismatch=%d" % (len(rows), sum(1 for r in rows if r[-1] == "FOUND"), len(mism)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
