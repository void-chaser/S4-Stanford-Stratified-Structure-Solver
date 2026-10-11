#!/usr/bin/env python3
"""Insert the family-B2 LinearSolve seam into an exported copy (P05-S2R3, stage 2).

Test-only.  Edits ONLY a directory given with --root, which must be a git-archive export
(never the repository's S4/ tree).  Refuses any root inside <repo>/S4 when --repo is given.

Family B2 (independent of family A, B and C; its own macro and hook):
  macro  S4_TEST_LINEARSOLVE_SEAM_NULLINFO2
  hook   S4_TEST_LINEARSOLVE_NULLINFO2_AFTER(id, &solve_info, output, n, ld, model)
  placed AFTER the solve and BEFORE the existing check, so the check reads the hook's
  status.  The hook sets solve_info non-zero when the id is requested (models a zero
  pivot).  The output model is the hook's business and is not set here.

Sites (ids are the H-tree sites; line numbers are for the H export and are checked by
content, not trusted):
  closed134  id 134   fmm_closed.cpp          1D, first solve
  closed138  id 138   fmm_closed.cpp          1D, second solve
  closed144  id 144   fmm_closed.cpp          2D, no PolBasis
  closed244  id 244   fmm_closed.cpp          tensor branch
  pbjones375 id 375   fmm_PolBasisJones.cpp   PolBasisJones solve
  pbnv265    id 265   fmm_PolBasisNV.cpp      PolBasisNV solve
  pbvl273    id 273   fmm_PolBasisVL.cpp      PolBasisVL solve

Anchors: each site is a multi-line block copied from the file (indentation included),
matched after the CR is stripped.  The block must match EXACTLY ONCE in its file.  Zero
or several matches is a hard error and nothing is written.  No fuzzy matching.  The block
also fixes which line the hook follows: the solve is block[solve_at] and its check is
block[solve_at+1]; the hook is inserted between them.

Declaration: one extern "C" line, guarded by the same macro, after the last #include of
each file that contains a site.

Usage:
  apply_seam_b2.py --root EXPORT --repo REPO [--check-only] [--report FILE]
"""
import argparse
import difflib
import os
import sys

MACRO = "S4_TEST_LINEARSOLVE_SEAM_NULLINFO2"
HOOK = "S4_TEST_LINEARSOLVE_NULLINFO2_AFTER"
FMM = "S4/fmm/"

# Each site: file, id, the exact block (lines as in the H export, indentation included),
# and the index of the solve line inside the block.  The check is block[solve_at + 1].
SITES = [
    {"file": FMM + "fmm_closed.cpp", "id": 134, "model": 2, "solve_at": 3, "block": [
        "\t\t\t\tRNP::TBLAS::SetMatrix<'A'>(n,n, 0.,1., &Epsilon2[n+n*n2],n2);",
        "\t\t\t\t// P05-S3R D4: check each solve before the next statement overwrites or reads its result.",
        "\t\t\t\t// The check at the first solve must precede SetMatrix on Epsilon_inv, which discards the RHS.",
        "\t\t\t\tRNP::LinearSolve<'N'>(n,n, Epsilon_inv,n, &Epsilon2[n+n*n2],n2, &solve_info, NULL);",
        "\t\t\t\tif(0 != solve_info){ S4_free(ivalues); return 1; }",
    ]},
    {"file": FMM + "fmm_closed.cpp", "id": 138, "model": 1, "solve_at": 2, "block": [
        "\t\t\t\tRNP::TBLAS::SetMatrix<'A'>(n,n, 0.,1., Epsilon_inv,n);",
        "\t\t\t\tRNP::TBLAS::CopyMatrix<'A'>(n,n,&Epsilon2[0+0*n2],n2, &Epsilon2[n+0*n2],n2); // use lower block for temp storage; will be cleaned up later",
        "\t\t\t\tRNP::LinearSolve<'N'>(n,n, &Epsilon2[n+0*n2],n2, Epsilon_inv,n, &solve_info, NULL);",
        "\t\t\t\tif(0 != solve_info){ S4_free(ivalues); return 1; }",
    ]},
    {"file": FMM + "fmm_closed.cpp", "id": 144, "model": 1, "solve_at": 3, "block": [
        "				// Upper block of diagonal of Epsilon2 is already Epsilon",
        "				RNP::TBLAS::CopyMatrix<'A'>(n,n,&Epsilon2[0+0*n2],n2, &Epsilon2[n+n*n2],n2);",
        "				RNP::TBLAS::SetMatrix<'A'>(n,n, 0.,1., Epsilon_inv,n);",
        "				RNP::LinearSolve<'N'>(n,n, &Epsilon2[0+0*n2],n2, Epsilon_inv,n, &solve_info, NULL);",
        "				if(0 != solve_info){ S4_free(ivalues); return 1; }",
    ]},
    {"file": FMM + "fmm_closed.cpp", "id": 244, "model": 1, "solve_at": 3, "block": [
        "				RNP::TBLAS::SetMatrix<'A'>(n,n, 0.,1., Epsilon_inv,n);",
        "				// P05-S3R D4: the tensor branch's solution is the output of this function; a zero pivot",
        "				// leaves it unsolved, so report it instead of returning success.",
        "				RNP::LinearSolve<'N'>(n,n, &Epsilon2[0+0*n2],n2, Epsilon_inv,n, &solve_info, NULL);",
        "				if(0 != solve_info){ S4_free(ivalues); return 1; }",
    ]},
    {"file": FMM + "fmm_PolBasisJones.cpp", "id": 375, "model": 1, "solve_at": 0, "block": [
        "\tRNP::LinearSolve<'N'>(n,n, Eta,n, &Epsilon2[n+n*n2],n2, &solve_info, NULL);",
        "\tif(0 != solve_info){",
    ]},
    {"file": FMM + "fmm_PolBasisNV.cpp", "id": 265, "model": 1, "solve_at": 0, "block": [
        "\tRNP::LinearSolve<'N'>(n,n, Eta,n, mDelta,n, &solve_info, NULL);",
        "\tif(0 != solve_info){",
    ]},
    {"file": FMM + "fmm_PolBasisVL.cpp", "id": 273, "model": 1, "solve_at": 0, "block": [
        "\tRNP::LinearSolve<'N'>(n,n, Eta,n, mDelta,n, &solve_info, NULL);",
        "\tif(0 != solve_info){",
    ]},
]


def _lines(raw_bytes):
    """Split into (body, original) rows.  body has the CR stripped; original keeps its ending."""
    text = raw_bytes.decode("utf-8")
    rows = []
    for raw in text.splitlines(keepends=True):
        body = raw[:-2] if raw.endswith("\r\n") else (raw[:-1] if raw.endswith("\n") else raw)
        rows.append((body, raw))
    return rows


def _split_top(s):
    """Split a C argument list on top-level commas (brackets and parentheses respected)."""
    out, depth, cur = [], 0, ""
    for ch in s:
        if ch in "([{":
            depth += 1
        if ch in ")]}":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur.strip())
            cur = ""
        else:
            cur += ch
    out.append(cur.strip())
    return out


def _solve_output(solve_line):
    """Return (b, ldb): the right-hand-side array and its leading dimension of a LinearSolve call.

    LinearSolve(n, nRHS, a, lda, b, ldb, info, pivots): b is argument 4, ldb is argument 5."""
    body = solve_line.split("LinearSolve<'N'>(", 1)[1]
    body = body[:body.rindex(")")]
    args = _split_top(body)
    if len(args) < 6:
        raise SystemExit("PARSE ERROR: LinearSolve call has %d arguments: %r" % (len(args), solve_line))
    return args[4], args[5]


def _match_block(bodies, block):
    """Return the 0-based start indices where the whole block matches exactly."""
    n = len(block)
    return [i for i in range(len(bodies) - n + 1) if bodies[i:i + n] == block]


def _assert_under_root(path, root, repo):
    real = os.path.realpath(path)
    real_root = os.path.realpath(root)
    if not (real == real_root or real.startswith(real_root + os.sep)):
        raise SystemExit("REFUSED: %s is outside the export root %s" % (path, root))
    if repo is not None:
        real_s4 = os.path.realpath(os.path.join(repo, "S4"))
        if real == real_s4 or real.startswith(real_s4 + os.sep):
            raise SystemExit("REFUSED: %s is inside the repository S4/ tree" % path)


def plan(root, repo):
    """Validate every anchor and build the new text of each affected file.  No write here."""
    by_file = {}
    for s in SITES:
        by_file.setdefault(s["file"], []).append(s)
    results = {}
    for rel, sites in sorted(by_file.items()):
        path = os.path.join(root, rel)
        _assert_under_root(path, root, repo)
        with open(path, "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8")
        rows = _lines(raw)
        bodies = [b for b, _ in rows]
        crlf = b"\r\n" in raw
        eol = "\r\n" if crlf else "\n"

        inserts_after = {}   # 0-based row index -> list of new lines to insert after it
        for s in sites:
            hits = _match_block(bodies, s["block"])
            if len(hits) != 1:
                raise SystemExit("ANCHOR ERROR %s id=%d: block matched %d time(s); refusing to guess"
                                 % (rel, s["id"], len(hits)))
            start = hits[0]
            solve_row = start + s["solve_at"]
            # The solve line must be the LinearSolve call and the next line its check.
            if "LinearSolve<'N'>" not in bodies[solve_row]:
                raise SystemExit("ORDER ERROR %s id=%d: block[solve_at] is not the solve" % (rel, s["id"]))
            if "if(0 != solve_info)" not in bodies[solve_row + 1]:
                raise SystemExit("ORDER ERROR %s id=%d: the line after the solve is not its check" % (rel, s["id"]))
            out_b, out_ld = _solve_output(bodies[solve_row])
            s = dict(s, out_b=out_b, out_ld=out_ld)
            hook = [
                "#ifdef " + MACRO,
                "%s(%d, &solve_info, %s, n, %s, %d);" % (HOOK, s["id"], s["out_b"], s["out_ld"], s["model"]),
                "#endif",
            ]
            inserts_after.setdefault(solve_row, []).extend(hook)

        # Declaration: one guarded extern "C" line after the last #include in the file.
        includes = [i for i, b in enumerate(bodies) if b.lstrip().startswith("#include")]
        if not includes:
            raise SystemExit("ANCHOR ERROR %s: no #include to anchor the declaration" % rel)
        decl_after = includes[-1]
        decl = [
            "#ifdef " + MACRO,
            'extern "C" void %s(int id, int *info, std::complex<double> *b, int n, int ld, int model);' % HOOK,
            "#endif",
        ]
        inserts_after.setdefault(decl_after, [])
        inserts_after[decl_after] = decl + inserts_after[decl_after]

        out = []
        for i, (_, raw) in enumerate(rows):
            out.append(raw if raw.endswith(("\n", "\r\n")) else raw + eol)
            for line in inserts_after.get(i, []):
                out.append(line + eol)
        new_text = "".join(out)
        results[rel] = {"old": text, "new": new_text,
                        "sites": [(s["id"], s["solve_at"]) for s in sites],
                        "decl_after": decl_after + 1}
    return results


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--root", required=True, help="exported tree to edit (git archive copy)")
    p.add_argument("--repo", default=None, help="repository root; its S4/ tree is refused")
    p.add_argument("--check-only", action="store_true", help="validate anchors; write nothing")
    p.add_argument("--report", default=None, help="write the unified diff report here")
    args = p.parse_args(argv)

    results = plan(args.root, args.repo)
    out = ["apply_seam_b2: %s" % ("CHECK ONLY" if args.check_only else "WRITE")]
    for rel, r in sorted(results.items()):
        out.append("file: %s" % rel)
        out.append("  declaration after line %d; sites (id, solve offset): %s" % (r["decl_after"], r["sites"]))
        diff = difflib.unified_diff(r["old"].splitlines(keepends=True), r["new"].splitlines(keepends=True),
                                    fromfile="a/" + rel, tofile="b/" + rel, n=1)
        out.append("".join(diff).rstrip("\n"))
    report = "\n".join(out) + "\n"
    sys.stdout.write(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w", encoding="utf-8", newline="") as fh:
            fh.write(report)
    if not args.check_only:
        for rel, r in results.items():
            with open(os.path.join(args.root, rel), "wb") as fh:
                fh.write(r["new"].encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
