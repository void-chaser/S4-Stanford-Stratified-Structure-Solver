#!/usr/bin/env python3
"""Insert the LinearSolve call-site seams into an exported copy (P05-S2R, R2-B).

Test-only.  This script edits ONLY a directory it is given with --root, which must
be a git-archive export (never the repository's S4/ tree).  It refuses any root that
resolves inside <repo>/S4 when --repo is given.  Production S4/ is never touched.

Two INDEPENDENT seam families, each with its own compile-time macro and hook, so a
build that defines one never activates the other:

  family A  S4_TEST_LINEARSOLVE_SEAM            (solve_info sites, info != NULL)
            hook  S4_TEST_LINEARSOLVE_AFTER(site, &solve_info, output, n)
            sites: fmm_FFT.cpp:209 (site 1), fmm_kottke.cpp:284 (site 2)
            Same anchors and same hook as the S2.6 seam (testing/d003/seam/
            linearsolve_seam.patch).  This script reproduces that patch's effect.

  family B  S4_TEST_LINEARSOLVE_SEAM_NULLINFO   (info == NULL sites)
            hook  S4_TEST_LINEARSOLVE_NULLINFO_AFTER(site, output, n, model)
            sites (site ids 11..17):
              fmm_closed.cpp:130  id 11  model 2 (computed RHS, not identity)
              fmm_closed.cpp:133  id 12  model 1 (identity RHS)
              fmm_closed.cpp:138  id 13  model 1
              fmm_closed.cpp:235  id 14  model 1
              fmm_PolBasisJones.cpp:369  id 15  model 1
              fmm_PolBasisNV.cpp:260     id 16  model 1
              fmm_PolBasisVL.cpp:268     id 17  model 1
            The output pointer and dimension are the solve's REAL output at each site
            (see testing/d003 evidence R2B_LINEARSOLVE_SITE_MODEL.txt).

Anchors are matched on CR-stripped lines and must match EXACTLY ONCE.  Zero or several
matches is a hard error: nothing is written.  No fuzzy matching.  Duplicate call text
(closed.cpp:138 and :235) is disambiguated by the following line, which is also an
exact match that must be unique.

Usage:
  apply_seam_r2.py --root EXPORT --repo REPO [--families A,B] [--check-only] [--report FILE]
"""
import argparse
import difflib
import os
import sys

FMM = "S4/fmm/"

# family A: the two solve_info sites (identical to the S2.6 seam).
FAMILY_A_SITES = [
    {"file": FMM + "fmm_FFT.cpp",    "site": 1,
     "call": "\tRNP::LinearSolve<'N'>(n,n, Epsilon2,n, Epsilon_inv,n, &solve_info, NULL);",
     "next": None},
    {"file": FMM + "fmm_kottke.cpp", "site": 2,
     "call": "\tRNP::LinearSolve<'N'>(n,n, Epsilon2,n, Epsilon_inv,n, &solve_info, NULL);",
     "next": None},
]

# family B: the seven info==NULL sites.  output/n/model describe the real solve.
#   out : C expression of the matrix the solve writes; n : dimension expression
#   model: 1 = RHS reset to identity immediately before the solve (zero pivot => identity)
#          2 = RHS is the computed matrix (zero pivot => computed value kept)
FAMILY_B_SITES = [
    {"file": FMM + "fmm_closed.cpp", "id": 11, "model": 2,
     "call": "\t\t\t\tRNP::LinearSolve<'N'>(n,n, Epsilon_inv,n, &Epsilon2[n+n*n2],n2, NULL, NULL);",
     "next": None, "out": "&Epsilon2[n+n*n2]", "ld": "n2"},
    {"file": FMM + "fmm_closed.cpp", "id": 12, "model": 1,
     "call": "\t\t\t\tRNP::LinearSolve<'N'>(n,n, &Epsilon2[n+0*n2],n2, Epsilon_inv,n, NULL, NULL);",
     "next": None, "out": "Epsilon_inv", "ld": "n"},
    {"file": FMM + "fmm_closed.cpp", "id": 13, "model": 1,
     "call": "\t\t\t\tRNP::LinearSolve<'N'>(n,n, &Epsilon2[0+0*n2],n2, Epsilon_inv,n, NULL, NULL);",
     "next": "\t\t\t\tRNP::TBLAS::CopyMatrix<'A'>(n,n,&Epsilon2[n+n*n2],n2, &Epsilon2[0+0*n2],n2);",
     "out": "Epsilon_inv", "ld": "n"},
    {"file": FMM + "fmm_closed.cpp", "id": 14, "model": 1,
     "call": "\t\t\t\tRNP::LinearSolve<'N'>(n,n, &Epsilon2[0+0*n2],n2, Epsilon_inv,n, NULL, NULL);",
     "next": "\t\t\t}else{",
     "out": "Epsilon_inv", "ld": "n"},
    {"file": FMM + "fmm_PolBasisJones.cpp", "id": 15, "model": 1,
     "call": "\tRNP::LinearSolve<'N'>(n,n, Eta,n, &Epsilon2[n+n*n2],n2, NULL, NULL);",
     "next": None, "out": "&Epsilon2[n+n*n2]", "ld": "n2"},
    {"file": FMM + "fmm_PolBasisNV.cpp", "id": 16, "model": 1,
     "call": "\tRNP::LinearSolve<'N'>(n,n, Eta,n, mDelta,n, NULL, NULL);",
     "next": None, "out": "mDelta", "ld": "n"},
    {"file": FMM + "fmm_PolBasisVL.cpp", "id": 17, "model": 1,
     "call": "\tRNP::LinearSolve<'N'>(n,n, Eta,n, mDelta,n, NULL, NULL);",
     "next": None, "out": "mDelta", "ld": "n"},
]

DECL_ANCHOR = '#include "fmm.h"'          # family B declaration anchor (unique, precedes use)
DECL_ANCHOR_A = '#include "fft_iface.h"'  # family A declaration anchor (as in the S2.6 seam)

DECL_A = [
    "#ifdef S4_TEST_LINEARSOLVE_SEAM",
    'extern "C" void S4_TEST_LINEARSOLVE_AFTER(int site, int *info, std::complex<double> *b, int n);',
    "#endif",
]
DECL_B = [
    "#ifdef S4_TEST_LINEARSOLVE_SEAM_NULLINFO",
    'extern "C" void S4_TEST_LINEARSOLVE_NULLINFO_AFTER(int site, std::complex<double> *b, int n, int ld, int model);',
    "#endif",
]


def _rows(text):
    """(stripped_body, raw_line) for each line; CR is removed for matching only."""
    out = []
    for raw in text.splitlines(keepends=True):
        body = raw[:-2] if raw.endswith("\r\n") else (raw[:-1] if raw.endswith("\n") else raw)
        out.append((body, raw))
    return out


def _find_once(rows, needle, label, rel):
    hits = [i for i, (b, _) in enumerate(rows) if b == needle]
    if len(hits) != 1:
        raise SystemExit("ANCHOR ERROR %s %s: %r matched %d time(s); refusing to guess"
                         % (rel, label, needle, len(hits)))
    return hits[0]


def _find_pair_once(rows, call, nxt, label, rel):
    hits = [i for i in range(len(rows) - 1)
            if rows[i][0] == call and rows[i + 1][0] == nxt]
    if len(hits) != 1:
        raise SystemExit("ANCHOR ERROR %s %s: call+next matched %d time(s); refusing to guess"
                         % (rel, label, len(hits)))
    return hits[0]


def _assert_under_root(path, root, repo):
    real = os.path.realpath(path)
    real_root = os.path.realpath(root)
    if not (real == real_root or real.startswith(real_root + os.sep)):
        raise SystemExit("REFUSED: %s is outside root %s" % (path, root))
    if repo is not None:
        real_s4 = os.path.realpath(os.path.join(repo, "S4"))
        if real == real_s4 or real.startswith(real_s4 + os.sep):
            raise SystemExit("REFUSED: %s is inside the repository S4/ tree" % path)


S4CPP = "S4/S4.cpp"

# family C: allocation sites in S4.cpp that --wrap cannot reach.  Each entry replaces
# the exact source lines (CR-stripped, must match exactly once) with an #ifdef block
# whose #else branch is the ORIGINAL text, so the default output is unchanged.
#   old   : list of exact source lines being replaced (old[0] is the anchor)
#   new   : list of lines emitted under S4_TEST_ALLOC_SEAM (the injected form)
#   id    : hook id passed to S4_TEST_ALLOC_HOOK
FAMILY_C_SITES = [
    {"id": 21, "old": [
        "\t*layer_modes = (LayerModes*)malloc(sizeof(LayerModes));"],
     "new": [
        "\t*layer_modes = (LayerModes*)(S4_TEST_ALLOC_HOOK(21, sizeof(LayerModes)) ? NULL : malloc(sizeof(LayerModes)));"]},
    {"id": 22, "old": [
        "\tpB->q = (std::complex<double>*)S4_malloc(sizeof(std::complex<double>)*(",
        "\t\t2*n + // for q",
        "\t\tkp_size + phi_size + Epsilon_inv_size + Epsilon2_size",
        "\t\t));"],
     "new": [
        "\tpB->q = (std::complex<double>*)(S4_TEST_ALLOC_HOOK(22, sizeof(std::complex<double>)*(2*n + kp_size + phi_size + Epsilon_inv_size + Epsilon2_size)) ? NULL : S4_malloc(sizeof(std::complex<double>)*(",
        "\t\t2*n + // for q",
        "\t\tkp_size + phi_size + Epsilon_inv_size + Epsilon2_size",
        "\t\t)));"]},
    {"id": 23, "old": [
        "\t\t\tdouble *rwork = (double*)S4_malloc(sizeof(double) * 4*n);"],
     "new": [
        "\t\t\tdouble *rwork = (double*)(S4_TEST_ALLOC_HOOK(23, sizeof(double) * 4*n) ? NULL : S4_malloc(sizeof(double) * 4*n));"]},
    {"id": 24, "old": [
        "\t\t\twork = (std::complex<double>*)S4_malloc(sizeof(std::complex<double>) * lwork);"],
     "new": [
        "\t\t\twork = (std::complex<double>*)(S4_TEST_ALLOC_HOOK(24, sizeof(std::complex<double>) * lwork) ? NULL : S4_malloc(sizeof(std::complex<double>) * lwork));"]},
    {"id": 25, "old": [
        "\tFieldCache *f = (FieldCache*)S4_malloc(sizeof(FieldCache)+sizeof(std::complex<double>)*Plen);"],
     "new": [
        "\tFieldCache *f = (FieldCache*)(S4_TEST_ALLOC_HOOK(25, sizeof(FieldCache)+sizeof(std::complex<double>)*Plen) ? NULL : S4_malloc(sizeof(FieldCache)+sizeof(std::complex<double>)*Plen));"]},
]
DECL_C = [
    "#ifdef S4_TEST_ALLOC_SEAM",
    'extern "C" int S4_TEST_ALLOC_HOOK(int id, size_t size);',
    "#endif",
]


def plan_replace(root, repo, rel, sites, macro, decl, fam, base_text=None):
    """Replace exact source lines under #ifdef <macro>, keeping the original as #else.

    Generic engine shared by families C and D (P05-S2R2).  Every site must match exactly
    once in <rel>; the declaration goes after the last #include, which precedes all uses.
    base_text: if given, the replacement is applied on top of this in-memory text (the output
    of an earlier family on the same file) instead of the file on disk.  This prevents a later
    family from silently overwriting an earlier family's changes to the same file.
    Returns (old_text, new_text, log).  Writes nothing.
    """
    path = os.path.join(root, rel)
    _assert_under_root(path, root, repo)
    with open(path, "rb") as fh:
        disk_text = fh.read().decode("utf-8")
    # the text being edited: the on-disk file, or the layered output of an earlier family
    text = disk_text if base_text is None else base_text
    rows = _rows(text)
    crlf = "\r\n" if any(raw.endswith("\r\n") for _, raw in rows) else "\n"
    # locate and validate every site first, so a single bad anchor writes nothing
    spans = []
    log = []
    for s in sites:
        old = s["old"]
        hits = [i for i in range(len(rows) - len(old) + 1)
                if all(rows[i + k][0] == old[k] for k in range(len(old)))]
        if len(hits) != 1:
            raise SystemExit("ANCHOR ERROR family %s id %d in %s: matched %d time(s); refusing to guess"
                             % (fam, s["id"], rel, len(hits)))
        spans.append((hits[0], hits[0] + len(old), s))
        log.append("family %s id %d: lines %d..%d replaced under %s"
                   % (fam, s["id"], hits[0] + 1, hits[0] + len(old), macro))
    spans.sort(key=lambda t: t[0])
    for a, b in zip(spans, spans[1:]):
        if a[1] > b[0]:
            raise SystemExit("OVERLAP ERROR family %s ids %d and %d" % (fam, a[2]["id"], b[2]["id"]))
    # the declaration anchor: last #include line in the file, which precedes every site
    incl = [i for i, (b, _) in enumerate(rows) if b.startswith("#include ")]
    if not incl or max(incl) >= spans[0][0]:
        raise SystemExit("ORDER ERROR family %s: no #include before the first site" % fam)
    decl_at = max(incl)
    out = []
    site_at = {a: (b, s) for a, b, s in spans}
    i = 0
    n_lines = len(rows)
    while i < n_lines:
        if i in site_at:
            b, s = site_at[i]
            out.append("#ifdef %s" % macro + crlf)
            for line in s["new"]:
                out.append(line + crlf)
            out.append("#else" + crlf)
            for k in range(b - i):
                out.append(rows[i + k][1])
            out.append("#endif" + crlf)
            i = b
            continue
        out.append(rows[i][1])
        if i == decl_at:
            for line in decl:
                out.append(line + crlf)
        i += 1
    new_text = "".join(out)
    log.append("family %s declaration after line %d" % (fam, decl_at + 1))
    return disk_text, new_text, log


def plan_c(root, repo):
    """Family C: replace exact S4.cpp allocation lines under #ifdef S4_TEST_ALLOC_SEAM."""
    return plan_replace(root, repo, S4CPP, FAMILY_C_SITES, "S4_TEST_ALLOC_SEAM", DECL_C, "C")


# family D (P05-S2R2 T1): the kottke work allocation in fmm_kottke.cpp:78.  It is a call to
# fft_alloc_complex, which --wrap cannot target without also hitting the 24 field-output calls
# in rcwa.cpp (GetFieldOnGrid, out of scope).  The seam is therefore placed at this one call
# site only.  Independent macro and hook from family C.  Default output: the original line.
FAMILY_D_FILE = FMM + "fmm_kottke.cpp"
FAMILY_D_SITES = [
    {"id": 31, "old": [
        "\tstd::complex<double> *work = fft_alloc_complex(6*ng2);"],
     "new": [
        "\tstd::complex<double> *work = (S4_TEST_KOTTKE_HOOK(31, 6*ng2) ? NULL : fft_alloc_complex(6*ng2));"]},
]
DECL_D = [
    "#ifdef S4_TEST_KOTTKE_SEAM",
    'extern "C" int S4_TEST_KOTTKE_HOOK(int id, size_t n);',
    "#endif",
]


def plan_d(root, repo, base_text=None):
    """Family D: replace the kottke fft_alloc_complex call under #ifdef S4_TEST_KOTTKE_SEAM.

    base_text: the already-patched text of FAMILY_D_FILE from families A/B, if any.
    Returns (original_disk_text, new_text, log) so that diffs show the cumulative change.
    """
    old_disk, new_text, log = plan_replace(root, repo, FAMILY_D_FILE, FAMILY_D_SITES,
                                           "S4_TEST_KOTTKE_SEAM", DECL_D, "D", base_text=base_text)
    return old_disk, new_text, log


def plan(root, repo, families):
    """Return {relpath: (new_text, [log lines])} without writing anything."""
    per_file = {}
    for fam in families:
        sites = FAMILY_A_SITES if fam == "A" else FAMILY_B_SITES
        for s in sites:
            per_file.setdefault(s["file"], []).append((fam, s))
    result = {}
    for rel in sorted(per_file):
        path = os.path.join(root, rel)
        _assert_under_root(path, root, repo)
        with open(path, "rb") as fh:
            text = fh.read().decode("utf-8")
        rows = _rows(text)
        crlf = "\r\n" if any(raw.endswith("\r\n") for _, raw in rows) else "\n"
        inserts = {}      # index -> list of lines to insert AFTER that index
        log = []
        need_decl = {"A": False, "B": False}
        for fam, s in per_file[rel]:
            decl_key = DECL_ANCHOR_A if fam == "A" else DECL_ANCHOR
            if s["next"] is None:
                call_at = _find_once(rows, s["call"], "call(%s)" % s.get("site", s.get("id")), rel)
            else:
                call_at = _find_pair_once(rows, s["call"], s["next"],
                                          "call+next(%s)" % s.get("site", s.get("id")), rel)
            if fam == "A":
                hook = ["#ifdef S4_TEST_LINEARSOLVE_SEAM",
                        "S4_TEST_LINEARSOLVE_AFTER(%d, &solve_info, Epsilon_inv, n);" % s["site"],
                        "#endif"]
                log.append("family A site %d: call at line %d, hook after it" % (s["site"], call_at + 1))
            else:
                hook = ["#ifdef S4_TEST_LINEARSOLVE_SEAM_NULLINFO",
                        "S4_TEST_LINEARSOLVE_NULLINFO_AFTER(%d, %s, n, %s, %d);" % (s["id"], s["out"], s["ld"], s["model"]),
                        "#endif"]
                log.append("family B id %d (model %d): call at line %d, hook after it" % (s["id"], s["model"], call_at + 1))
            inserts.setdefault(call_at, []).extend([h for h in hook])
            # declaration: once per file per family, before the first use
            decl_needed = DECL_A if fam == "A" else DECL_B
            key = (fam, rel)
            if key not in need_decl:
                need_decl[key] = True
                anchor_at = _find_once(rows, decl_key, "decl(%s)" % fam, rel)
                if anchor_at >= call_at:
                    raise SystemExit("ORDER ERROR %s: family %s declaration anchor (%d) is not before its call (%d)"
                                     % (rel, fam, anchor_at + 1, call_at + 1))
                inserts.setdefault(anchor_at, []).extend(decl_needed)
                log.append("family %s declaration after line %d" % (fam, anchor_at + 1))
        out = []
        for i, (_, raw) in enumerate(rows):
            out.append(raw)
            if i in inserts:
                for line in inserts[i]:
                    out.append(line + crlf)
        new_text = "".join(out)
        result[rel] = (text, new_text, log)
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--root", required=True)
    p.add_argument("--repo", default=None)
    p.add_argument("--families", default="A,B,C")
    p.add_argument("--check-only", action="store_true")
    p.add_argument("--report", default=None)
    args = p.parse_args(argv)
    fams = [f.strip() for f in args.families.split(",") if f.strip()]
    for f in fams:
        if f not in ("A", "B", "C", "D"):
            raise SystemExit("unknown family %r" % f)
    ab = [f for f in fams if f in ("A", "B")]
    res = plan(args.root, args.repo, ab) if ab else {}
    if "C" in fams:
        old_c, new_c, log_c = plan_c(args.root, args.repo)
        if S4CPP in res:
            raise SystemExit("INTERNAL ERROR: family C file already planned by A/B")
        res[S4CPP] = (old_c, new_c, log_c)
    if "D" in fams:
        # family D edits fmm_kottke.cpp, which families A also edit.  Layer D on top of A/B's
        # output so neither family silently drops the other's changes (P05-S2R2 probe).
        base = res[FAMILY_D_FILE][1] if FAMILY_D_FILE in res else None
        old_d, new_d, log_d = plan_d(args.root, args.repo, base_text=base)
        if FAMILY_D_FILE in res:
            old_disk, _, log_ab = res[FAMILY_D_FILE]
            res[FAMILY_D_FILE] = (old_disk, new_d, log_ab + log_d)
        else:
            res[FAMILY_D_FILE] = (old_d, new_d, log_d)
    out_lines = ["apply_seam_r2: %s  families=%s" % ("CHECK ONLY (no write)" if args.check_only else "WRITTEN", ",".join(fams))]
    for rel in sorted(res):
        old, new, log = res[rel]
        out_lines.append("file: " + rel)
        out_lines.extend("  " + l for l in log)
        diff = difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                    fromfile="a/" + rel, tofile="b/" + rel, n=0)
        out_lines.append("".join(diff).rstrip("\n"))
    report = "\n".join(out_lines) + "\n"
    sys.stdout.write(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w", encoding="utf-8", newline="") as fh:
            fh.write(report)
    if not args.check_only:
        for rel in sorted(res):
            old, new, _ = res[rel]
            with open(os.path.join(args.root, rel), "wb") as fh:
                fh.write(new.encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
