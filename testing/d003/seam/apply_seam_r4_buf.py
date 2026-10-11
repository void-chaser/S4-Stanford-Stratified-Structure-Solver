#!/usr/bin/env python3
"""Insert the family-B2-buf output-only seam into an exported copy (P05-S2R4, R4-1).

Test-only.  Edits ONLY a directory given with --root, which must be a git-archive export
(never the repository's S4/ tree).  Refuses any root inside <repo>/S4 when --repo is given.

Family B2-buf: the SAME seven H-tree sites as family B2 (apply_seam_b2.py), the SAME anchors and
the SAME insertion position (after the solve line, before its check), but the hook it calls
writes ONLY the output buffer, with the family-B rule (model 1 = identity RHS).  It does not take
the solve status: the call passes no &solve_info.  The original H solve still writes solve_info
through its own &solve_info argument, exactly as in the H tree.

  macro  S4_TEST_LINEARSOLVE_SEAM_NULLINFO2BUF
  hook   S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER(id, output, n, ld, model)

apply_seam_b2.py is NOT edited.  This script imports its SITES table and helpers, so the anchors
are the single source of truth.  It refuses to run if the export already contains the B2 macro
(the two families must not be mixed in one copy).

Usage:
  apply_seam_r4_buf.py --root EXPORT --repo REPO [--check-only] [--report FILE]
"""
import argparse
import difflib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import apply_seam_b2 as B2  # noqa: E402  (SITES, _lines, _match_block, _solve_output, _assert_under_root)

MACRO = "S4_TEST_LINEARSOLVE_SEAM_NULLINFO2BUF"
HOOK = "S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER"
DECL = 'extern "C" void %s(int id, std::complex<double> *b, int n, int ld, int model);' % HOOK


def plan(root, repo):
    """Validate every B2 anchor and build the new text.  No write here."""
    by_file = {}
    for s in B2.SITES:
        by_file.setdefault(s["file"], []).append(s)
    results = {}
    for rel, sites in sorted(by_file.items()):
        path = os.path.join(root, rel)
        B2._assert_under_root(path, root, repo)
        with open(path, "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8")
        if "S4_TEST_LINEARSOLVE_SEAM_NULLINFO2" in text and "S4_TEST_LINEARSOLVE_SEAM_NULLINFO2BUF" not in text:
            # a B2 seam is already present in this copy: refuse to mix the two families
            raise SystemExit("REFUSED: %s already carries the B2 seam; use a clean export" % rel)
        rows = B2._lines(raw)
        bodies = [b for b, _ in rows]
        eol = "\r\n" if b"\r\n" in raw else "\n"
        inserts_after = {}
        for s in sites:
            hits = B2._match_block(bodies, s["block"])
            if len(hits) != 1:
                raise SystemExit("ANCHOR ERROR %s id=%d: block matched %d time(s); refusing to guess"
                                 % (rel, s["id"], len(hits)))
            start = hits[0]
            solve_row = start + s["solve_at"]
            if "LinearSolve<'N'>" not in bodies[solve_row]:
                raise SystemExit("ORDER ERROR %s id=%d: block[solve_at] is not the solve" % (rel, s["id"]))
            if "if(0 != solve_info)" not in bodies[solve_row + 1]:
                raise SystemExit("ORDER ERROR %s id=%d: the line after the solve is not its check" % (rel, s["id"]))
            out_b, out_ld = B2._solve_output(bodies[solve_row])
            hook = [
                "#ifdef " + MACRO,
                "%s(%d, %s, n, %s, %d);" % (HOOK, s["id"], out_b, out_ld, s["model"]),
                "#endif",
            ]
            inserts_after.setdefault(solve_row, []).extend(hook)
        includes = [i for i, b in enumerate(bodies) if b.lstrip().startswith("#include")]
        if not includes:
            raise SystemExit("ANCHOR ERROR %s: no #include to anchor the declaration" % rel)
        decl_after = includes[-1]
        decl = ["#ifdef " + MACRO, DECL, "#endif"]
        inserts_after[decl_after] = decl + inserts_after.get(decl_after, [])
        out = []
        for i, (_, raw_line) in enumerate(rows):
            out.append(raw_line if raw_line.endswith(("\n", "\r\n")) else raw_line + eol)
            for line in inserts_after.get(i, []):
                out.append(line + eol)
        results[rel] = {"old": text, "new": "".join(out),
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
    out = ["apply_seam_r4_buf: %s" % ("CHECK ONLY" if args.check_only else "WRITE")]
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
