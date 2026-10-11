#!/usr/bin/env python3
"""Insert the LinearSolve call-site seam into an exported baseline copy (P05-S2.6).

The seam is test-only and lives entirely inside the baseline copy the harness
exports with `git archive` (OUT/baseline-src).  This script refuses to touch any
path that is not under the given baseline root, and it refuses any path that
resolves inside the repository's own S4/ tree.  It edits exactly two files and
exactly one site in each:

    S4/fmm/fmm_FFT.cpp     the LinearSolve line  ... &solve_info, NULL);  (site 1)
    S4/fmm/fmm_kottke.cpp  the LinearSolve line  ... &solve_info, NULL);  (site 2)

Each anchor must match EXACTLY ONCE after the trailing CR is removed.  Zero or
several matches is a hard error: nothing is written.  No fuzzy matching.

Inserted text is CRLF to match the sources, so that the diff contains only the
inserted lines.  Declarations go after the `#include "fft_iface.h"` line; the
hook goes on the line after the LinearSolve call.

Usage:
    apply_seam.py --root OUT/baseline-src --report OUT/seam/apply_report.txt
    apply_seam.py --check-only --root ...      (anchors only, no write)
"""
import argparse
import difflib
import os
import sys

REPO_S4 = None  # set from --repo to refuse writes into the repository's S4/

# Anchors are whole lines after the CR is removed, byte for byte.  The LinearSolve
# line carries ONE leading TAB in both sources (verified with cat -A); the include
# line carries none.  Matching is exact equality, never substring.
FILES = {
    "S4/fmm/fmm_FFT.cpp": {
        "site": 1,
        "call": "\tRNP::LinearSolve<'N'>(n,n, Epsilon2,n, Epsilon_inv,n, &solve_info, NULL);",
        "decl_anchor": '#include "fft_iface.h"',
    },
    "S4/fmm/fmm_kottke.cpp": {
        "site": 2,
        "call": "\tRNP::LinearSolve<'N'>(n,n, Epsilon2,n, Epsilon_inv,n, &solve_info, NULL);",
        "decl_anchor": '#include "fft_iface.h"',
    },
}

DECL_BLOCK = [
    "#ifdef S4_TEST_LINEARSOLVE_SEAM",
    "extern \"C\" void S4_TEST_LINEARSOLVE_AFTER(int site, int *info, std::complex<double> *b, int n);",
    "#endif",
]


def _lines(text):
    """Split keeping line endings; return list of (content_without_cr, original_line)."""
    out = []
    for raw in text.splitlines(keepends=True):
        body = raw[:-2] if raw.endswith("\r\n") else (raw[:-1] if raw.endswith("\n") else raw)
        out.append((body, raw))
    return out


def _find_once(rows, needle, label, rel):
    hits = [i for i, (body, _) in enumerate(rows) if body == needle]
    if len(hits) != 1:
        raise SystemExit("ANCHOR ERROR %s: %r matched %d time(s) in %s; refusing to guess"
                         % (label, needle, len(hits), rel))
    return hits[0]


def _assert_under_root(path, root):
    real = os.path.realpath(path)
    real_root = os.path.realpath(root)
    if not (real == real_root or real.startswith(real_root + os.sep)):
        raise SystemExit("REFUSED: %s is outside the baseline root %s" % (path, root))
    if REPO_S4 is not None:
        real_s4 = os.path.realpath(REPO_S4)
        if real == real_s4 or real.startswith(real_s4 + os.sep):
            raise SystemExit("REFUSED: %s is inside the repository S4/ tree" % path)


def apply(root, check_only=False):
    results = []
    for rel, spec in sorted(FILES.items()):
        path = os.path.join(root, rel)
        _assert_under_root(path, root)
        with open(path, "rb") as fh:
            raw_bytes = fh.read()
        text = raw_bytes.decode("utf-8")
        rows = _lines(text)

        decl_at = _find_once(rows, spec["decl_anchor"], "decl", rel)
        call_at = _find_once(rows, spec["call"], "call", rel)
        # The declaration must precede the function body that contains the call.
        if not decl_at < call_at:
            raise SystemExit("ORDER ERROR %s: declaration anchor (line %d) is not before the call (line %d)"
                             % (rel, decl_at + 1, call_at + 1))

        crlf = "\r\n" if any(raw.endswith("\r\n") for _, raw in rows) else "\n"
        decl_lines = [l + crlf for l in DECL_BLOCK]
        hook_lines = [
            "#ifdef S4_TEST_LINEARSOLVE_SEAM" + crlf,
            "S4_TEST_LINEARSOLVE_AFTER(%d, &solve_info, Epsilon_inv, n);" % spec["site"] + crlf,
            "#endif" + crlf,
        ]

        new_rows = []
        for i, (_, raw) in enumerate(rows):
            new_rows.append(raw)
            if i == decl_at:
                new_rows.extend(decl_lines)
            if i == call_at:
                new_rows.extend(hook_lines)
        new_text = "".join(new_rows)

        results.append({
            "file": rel,
            "site": spec["site"],
            "decl_insert_after_line": decl_at + 1,
            "call_line": call_at + 1,
            "hook_insert_after_line": call_at + 1,
            "old": text,
            "new": new_text,
        })

    if check_only:
        return results
    for r in results:
        with open(os.path.join(root, r["file"]), "wb") as fh:
            fh.write(r["new"].encode("utf-8"))
    return results


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--root", required=True, help="exported baseline root (OUT/baseline-src)")
    p.add_argument("--repo", default=None, help="repository root; S4/ under it is refused")
    p.add_argument("--report", default=None, help="write a text report here")
    p.add_argument("--check-only", action="store_true")
    args = p.parse_args(argv)

    global REPO_S4
    if args.repo:
        REPO_S4 = os.path.join(args.repo, "S4")

    results = apply(args.root, check_only=args.check_only)

    out = []
    out.append("apply_seam: %s" % ("CHECK ONLY (no write)" if args.check_only else "WRITTEN"))
    for r in results:
        out.append("file: %s  site=%d" % (r["file"], r["site"]))
        out.append("  declaration block inserted after line %d" % r["decl_insert_after_line"])
        out.append("  hook inserted after LinearSolve call at line %d" % r["call_line"])
        diff = difflib.unified_diff(
            r["old"].splitlines(keepends=True), r["new"].splitlines(keepends=True),
            fromfile="a/" + r["file"], tofile="b/" + r["file"], n=1)
        out.append("".join(diff).rstrip("\n"))
    report = "\n".join(out) + "\n"
    sys.stdout.write(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w", encoding="utf-8", newline="") as fh:
            fh.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
