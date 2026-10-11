#!/usr/bin/env python3
"""Insert the family-E seams into an exported copy (P05-S2R5, R5-1).  Test-only.

Edits ONLY a directory given with --root, which must be a git-archive export (never the
repository's S4/ tree).  Refuses any root inside <repo>/S4 when --repo is given.  Every anchor
must match exactly one line (indentation plus the full statement text).  Any anchor that
matches zero or several lines is a hard error, and nothing is written.

Family E (fmmret), trees A and H.  The seam is inserted immediately AFTER each real statement
    fmm_ret = FMMGetEpsilon_X(S, L, n, pB->Epsilon2, pB->Epsilon_inv);
and replaces its status with the hook's result:
    fmm_ret = S4_TEST_FMMRET_AFTER(ID, fmm_ret);
The hook returns 1 when the request matches (fmmret:ID:K, K-th call of that ID), otherwise it returns
the status unchanged.  The FMM function itself is still called, so its outputs are the real ones.
Behaviour: A and H both test fmm_ret once after the dispatch (A line 2400, H line 2413), so a forced
1 reaches 'return 20' with the layer modes discarded.  See the R5-1 facts file.

Family E for tree B (fmmbuf).  Tree B has NO fmm_ret variable and no status check (the return
of each FMMGetEpsilon_X is discarded), so a status cannot be forced.  The seam is inserted after
each bare call statement and only observes the output buffers:
    S4_TEST_FMMBUF_AFTER(ID, Epsilon2, Epsilon_inv, n)
The hook writes NOTHING.  It only counts the call and reports the buffers it sees (for the
block-level comparison).  The B column is therefore a different model and is labelled so.

Macros: S4_TEST_FMMRET_SEAM (A, H) and S4_TEST_FMMBUF_SEAM (B).  Both are independent of the
existing S4_TEST_LINEARSOLVE_* and S4_TEST_ALLOC_* / S4_TEST_KOTTKE_* macros.

Usage:
  apply_seam_r5_fmmret.py --tree {A,H,B} --root EXPORT --repo REPO [--check-only] [--report FILE]
"""
import argparse
import difflib
import os
import sys

FMM_CALLS = [
    ("FMMGetEpsilon_Experimental", 3),
    ("FMMGetEpsilon_Kottke", 5),
    ("FMMGetEpsilon_FFT", 5),
    ("FMMGetEpsilon_PolBasisJones", 7),
    ("FMMGetEpsilon_PolBasisNV", 7),
    ("FMMGetEpsilon_PolBasisVL", 7),
    ("FMMGetEpsilon_PolBasisJones", 6),
    ("FMMGetEpsilon_PolBasisNV", 6),
    ("FMMGetEpsilon_PolBasisVL", 6),
    ("FMMGetEpsilon_ClosedForm", 4),
]
# Point IDs.  The first ID of each point is 150 + index, so they cannot collide with the family
# B / B2 / C / D IDs (11..25, 134..273) that the injector already defines.
POINT_IDS = {name + "@" + str(tabs): 150 + i for i, (name, tabs) in enumerate(FMM_CALLS)}

MACRO_AH = "S4_TEST_FMMRET_SEAM"
HOOK_AH = "S4_TEST_FMMRET_AFTER"
MACRO_B = "S4_TEST_FMMBUF_SEAM"
HOOK_B = "S4_TEST_FMMBUF_AFTER"
FILE = "S4/S4.cpp"


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


def _statement(name, tabs, with_capture):
    """The exact anchor line.  with_capture: H and A carry 'fmm_ret = '; B carries no capture."""
    call = "%s(S, L, n, pB->Epsilon2, pB->Epsilon_inv);" % name
    return ("\t" * tabs) + ("fmm_ret = " if with_capture else "") + call


def plan(root, repo, tree):
    path = os.path.join(root, FILE)
    _assert_under_root(path, root, repo)
    with open(path, "rb") as fh:
        raw = fh.read()
    text = raw.decode("utf-8")
    rows = _lines(raw)
    bodies = [b for b, _ in rows]
    eol = "\r\n" if b"\r\n" in raw else "\n"
    with_capture = tree in ("A", "H")
    macro = MACRO_AH if with_capture else MACRO_B
    hook = HOOK_AH if with_capture else HOOK_B
    if macro in text:
        raise SystemExit("REFUSED: %s already carries %s" % (FILE, macro))

    inserts_after = {}
    plan_rows = []
    for name, tabs in FMM_CALLS:
        anchor = _statement(name, tabs, with_capture)
        hits = [i for i, b in enumerate(bodies) if b == anchor]
        if len(hits) != 1:
            raise SystemExit("ANCHOR ERROR tree=%s %s tabs=%d: matched %d time(s); nothing written"
                             % (tree, name, tabs, len(hits)))
        at = hits[0]
        pid = POINT_IDS[name + "@" + str(tabs)]
        if with_capture:
            block = [
                "#ifdef " + macro,
                "%sfmm_ret = %s(%d, fmm_ret);" % ("\t" * tabs, hook, pid),
                "#endif",
            ]
        else:
            # B: observe the buffers the call just wrote; the hook writes nothing (no status exists in B).
            block = [
                "#ifdef " + macro,
                "%s%s(%d, pB->Epsilon2, pB->Epsilon_inv, n);" % ("\t" * tabs, hook, pid),
                "#endif",
            ]
        inserts_after.setdefault(at, []).extend(block)
        plan_rows.append((pid, name, tabs, at + 1))

    # Declaration: one guarded extern "C" line after the last #include.
    includes = [i for i, b in enumerate(bodies) if b.lstrip().startswith("#include")]
    if not includes:
        raise SystemExit("ANCHOR ERROR %s: no #include to anchor the declaration" % FILE)
    decl_after = includes[-1]
    if with_capture:
        decl = 'extern "C" int %s(int id, int ret);' % hook
    else:
        decl = 'extern "C" void %s(int id, std::complex<double> *e2, std::complex<double> *einv, int n);' % hook
    inserts_after[decl_after] = ["#ifdef " + macro, decl, "#endif"] + inserts_after.get(decl_after, [])

    out = []
    for i, (_, raw_line) in enumerate(rows):
        out.append(raw_line if raw_line.endswith(("\n", "\r\n")) else raw_line + eol)
        for line in inserts_after.get(i, []):
            out.append(line + eol)
    return {"old": text, "new": "".join(out), "points": plan_rows, "decl_after": decl_after + 1,
            "macro": macro, "hook": hook}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--tree", required=True, choices=("A", "H", "B"))
    p.add_argument("--root", required=True, help="exported tree to edit (git archive copy)")
    p.add_argument("--repo", default=None, help="repository root; its S4/ tree is refused")
    p.add_argument("--check-only", action="store_true", help="validate anchors; write nothing")
    p.add_argument("--report", default=None, help="write the unified diff report here")
    args = p.parse_args(argv)
    r = plan(args.root, args.repo, args.tree)
    out = ["apply_seam_r5_fmmret: tree=%s %s" % (args.tree, "CHECK ONLY" if args.check_only else "WRITE")]
    out.append("file: %s  macro: %s  hook: %s" % (FILE, r["macro"], r["hook"]))
    out.append("  declaration after line %d" % r["decl_after"])
    for pid, name, tabs, line in r["points"]:
        out.append("  point id=%d  %s  tabs=%d  anchor line=%d" % (pid, name, tabs, line))
    diff = difflib.unified_diff(r["old"].splitlines(keepends=True), r["new"].splitlines(keepends=True),
                                fromfile="a/" + FILE, tofile="b/" + FILE, n=1)
    out.append("".join(diff).rstrip("\n"))
    report = "\n".join(out) + "\n"
    sys.stdout.write(report)
    if args.report:
        os.makedirs(os.path.dirname(os.path.abspath(args.report)), exist_ok=True)
        with open(args.report, "w", encoding="utf-8", newline="") as fh:
            fh.write(report)
    if not args.check_only:
        with open(os.path.join(args.root, FILE), "wb") as fh:
            fh.write(r["new"].encode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
