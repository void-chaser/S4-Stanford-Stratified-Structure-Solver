#!/usr/bin/env python3
"""Insert the family-F seam (AddFieldToCache caller check) into an H export copy.  Test-only (P05-S2R5, R5-2).

Edits ONLY a directory given with --root, which must be a git-archive export (never the repository's S4/
tree).  Refuses any root inside <repo>/S4 when --repo is given.  Each anchor must match exactly one line
(indentation plus the full statement text).  Any anchor that matches zero or several lines is a hard
error, and nothing is written.

Family F isolates the CALLER's check of Simulation_AddFieldToCache in the three PolBasis functions of
tree H (fmm_PolBasisJones.cpp, fmm_PolBasisNV.cpp, fmm_PolBasisVL.cpp).  The seam wraps the call
expression so that the caller sees the value returned by the hook.  The hook returns 1 for the
requested point (addf:ID:K) and otherwise returns the real return value.  The function itself runs in
full: its allocation path and its own NULL check (S4.cpp 4010-4012) are untouched.  This is what separates
the caller's check and cleanup from the function's internal check, which the existing family C point 25
(alloc:25:1) exercises.

Tree A and tree B are NOT patched by this writer: in both trees Simulation_AddFieldToCache is void
(A 876181c and B 37a82e8, S4.cpp declaration line 226), so no return value exists to force.  Their
column is 'no equivalent point (void function)'.

Macro: S4_TEST_ADDFIELD_SEAM.  Hook: S4_TEST_ADDFIELD_AFTER(int id, int ret) -> int.
Point IDs: 160 (Jones), 161 (NV), 162 (VL).

Usage:
  apply_seam_r5_addfield.py --root EXPORT --repo REPO [--check-only] [--report FILE]
"""
import argparse
import difflib
import os
import sys

MACRO = "S4_TEST_ADDFIELD_SEAM"
HOOK = "S4_TEST_ADDFIELD_AFTER"
DECL = 'extern "C" int %s(int id, int ret);' % HOOK

# (file, point id, the exact statement line in H; the call is wrapped in place)
SITES = [
    ("S4/fmm/fmm_PolBasisJones.cpp", 160,
     "\t\tif(0 != Simulation_AddFieldToCache((S4_Simulation*)S, L, S->n_G, P, 4*nn+2*n)){"),
    ("S4/fmm/fmm_PolBasisNV.cpp", 161,
     "\t\tif(0 != Simulation_AddFieldToCache((S4_Simulation*)S, L, S->n_G, P, 4*nn)){"),
    ("S4/fmm/fmm_PolBasisVL.cpp", 162,
     "\t\tif(0 != Simulation_AddFieldToCache((S4_Simulation*)S, L, S->n_G, P, 4*nn)){"),
]


def _lines(raw_bytes):
    text = raw_bytes.decode("utf-8")
    rows = []
    for raw in text.splitlines(keepends=True):
        body = raw[:-2] if raw.endswith("\r\n") else (raw[:-1] if raw.endswith("\n") else raw)
        rows.append((body, raw))
    return rows


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
    results = {}
    by_file = {}
    for rel, pid, stmt in SITES:
        by_file.setdefault(rel, []).append((pid, stmt))
    for rel, items in sorted(by_file.items()):
        path = os.path.join(root, rel)
        _assert_under_root(path, root, repo)
        with open(path, "rb") as fh:
            raw = fh.read()
        text = raw.decode("utf-8")
        if MACRO in text:
            raise SystemExit("REFUSED: %s already carries %s" % (rel, MACRO))
        rows = _lines(raw)
        bodies = [b for b, _ in rows]
        eol = "\r\n" if b"\r\n" in raw else "\n"
        replaced = {}
        for pid, stmt in items:
            hits = [i for i, b in enumerate(bodies) if b == stmt]
            if len(hits) != 1:
                raise SystemExit("ANCHOR ERROR %s point=%d: matched %d time(s); nothing written"
                                 % (rel, pid, len(hits)))
            replaced[hits[0]] = pid
        includes = [i for i, b in enumerate(bodies) if b.lstrip().startswith("#include")]
        if not includes:
            raise SystemExit("ANCHOR ERROR %s: no #include to anchor the declaration" % rel)
        decl_after = includes[-1]
        out = []
        for i, (body, raw_line) in enumerate(rows):
            if i in replaced:
                pid = replaced[i]
                # The statement becomes: if(0 != (<hook>(pid, Simulation_AddFieldToCache(...)))){
                # The guard keeps the original text; only the call inside the test is wrapped.
                head = body.split("if(0 != ", 1)[0]
                call = body.split("if(0 != ", 1)[1]
                assert call.endswith("){"), call
                inner = call[:-2]
                wrapped = "%sif(0 != %s(%d, %s)){" % (head, HOOK, pid, inner)
                ending = raw_line[len(body):]
                if not ending.endswith(("\n", "\r\n")):
                    ending = eol
                out.append(("#ifdef " + MACRO) + eol)
                out.append(wrapped + eol)
                out.append("#else" + eol)
                out.append(body + eol)
                out.append("#endif" + eol)
                continue
            out.append(raw_line if raw_line.endswith(("\n", "\r\n")) else raw_line + eol)
            if i == decl_after:
                out.append("#ifdef " + MACRO + eol)
                out.append(DECL + eol)
                out.append("#endif" + eol)
        results[rel] = {"old": text, "new": "".join(out), "points": sorted(pid for pid, _ in items),
                        "decl_after": decl_after + 1}
    return results


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--root", required=True, help="exported H tree to edit (git archive copy)")
    p.add_argument("--repo", default=None, help="repository root; its S4/ tree is refused")
    p.add_argument("--check-only", action="store_true", help="validate anchors; write nothing")
    p.add_argument("--report", default=None, help="write the unified diff report here")
    args = p.parse_args(argv)
    results = plan(args.root, args.repo)
    out = ["apply_seam_r5_addfield: %s" % ("CHECK ONLY" if args.check_only else "WRITE")]
    for rel, r in sorted(results.items()):
        out.append("file: %s  points: %s  declaration after line %d" % (rel, r["points"], r["decl_after"]))
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
