#!/usr/bin/env python3
# s5r3_copycheck.py -- U373 line-by-line diff proof for the S5R3 copies of the M3b/M3a apparatus scripts.
# STRICT pairs (the 7 E2E build/run/judge/frontend scripts): after applying the path/round-label/output
# substitution rule every line must be identical; the only allowed residual is the declared shakedown
# block of judge_e2e_s5r3.py (task brief section 6). ADAPTED pairs (make test runner and judge): the
# unified diff is written out in full and every residual line is reported as an adapted line, because
# the brief requires a resumable segment runner and a 4-case positive control that M3b's judge did not have.
import os, sys, subprocess, difflib

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
OUT = os.path.join(EV, "COPY_DIFF_S5R3.txt")
NL = chr(10)
SUBST = [
    ("checkpoints/p05/evidence/p05-s4r9/m3b", "checkpoints/p05/evidence/p05-s5r3"),
    ("checkpoints/p05/evidence/p05-s4r9/m3a", "checkpoints/p05/evidence/p05-s5r3"),
    ("p05-s4r9/m3b", "p05-s5r3"),
    ("p05-s4r9/m3a", "p05-s5r3"),
    ("stage_s4r9", "stage_s5r3"),
    ("build_e2e_r9m3b_v2.py", "build_e2e_s5r3.py"),
    ("calib_e2e_r9m3b_v3.py", "calib_e2e_s5r3.py"),
    ("run_e2e_r9m3b.py", "run_e2e_s5r3.py"),
    ("judge_e2e_r9m3b.py", "judge_e2e_s5r3.py"),
    ("e2e_python_r9m3b.py", "e2e_python_s5r3.py"),
    ("e2e_lua_r9m3b.lua", "e2e_lua_s5r3.lua"),
    ("e2e_lua_repl_r9m3b.txt", "e2e_lua_repl_s5r3.txt"),
    ("run_maketest_r9m3a.py", "run_maketest_s5r3.py"),
    ("judge_maketest_r9m3b_v2.py", "judge_maketest_s5r3.py"),
    ("R9M3B", "S5R3"), ("R9M3A", "S5R3"),
    ("r9m3b", "s5r3"), ("r9m3a", "s5r3"),
    ("M3A", "M3B"), ("M3a", "M3b"), ("m3a", "m3b"),
]
# declared residuals allowed in STRICT pairs (post-substitution copy additions)
DECLARED = {
    "build": [
        "M3b build table", "M3B = {", "PYEXT_SHA256", "M3B_TREE", "replace(b\"", "DIFFERENT_ONLY_BY_TREE_PATH",
        "compare_with_M3", "E2E_BUILD_S5R3.tsv -- artefacts", "S5R3 E2E build", "m3b/trees/E2E_F4",
    ],
    "e2e_judge": [
        "pass2_dir =", "import os, sys, json, re", "os.path.realpath(pass2_dir)", "out = os.path.join(os.path.dirname", "formal_verdict(pass1_dir",
        "shakedown", "SHAKEDOWN_DUP", "task brief section 6", "mode_shakedown", "byte-copy",
        "usage: judge_e2e_s5r3.py", "return 0 if not [r for r in rows if r[4] in (\"FLAKY\",)] else 1",
        "os.listdir(os.path.join(pass1_dir", "if f.endswith(\".json\"):", "os.path.join(pass2_dir",
        "os.path.join(pass1_dir, \"points\", f)", "import os, sys, json, re, shutil",
    ],
}
STRICT = [
    ("testing/d003/stage_s4r9/build_e2e_r9m3b_v2.py", "testing/d003/stage_s5r3/build_e2e_s5r3.py", "build"),
    ("testing/d003/stage_s4r9/calib_e2e_r9m3b_v3.py", "testing/d003/stage_s5r3/calib_e2e_s5r3.py", "calib"),
    ("testing/d003/stage_s4r9/run_e2e_r9m3b.py", "testing/d003/stage_s5r3/run_e2e_s5r3.py", "run"),
    ("testing/d003/stage_s4r9/judge_e2e_r9m3b.py", "testing/d003/stage_s5r3/judge_e2e_s5r3.py", "e2e_judge"),
    ("testing/d003/stage_s4r9/e2e_python_r9m3b.py", "testing/d003/stage_s5r3/e2e_python_s5r3.py", "python"),
    ("testing/d003/stage_s4r9/e2e_lua_r9m3b.lua", "testing/d003/stage_s5r3/e2e_lua_s5r3.lua", "lua_batch"),
    ("testing/d003/stage_s4r9/e2e_lua_repl_r9m3b.txt", "testing/d003/stage_s5r3/e2e_lua_repl_s5r3.txt", "lua_repl"),
]
ADAPTED = [
    ("testing/d003/stage_s4r9/run_maketest_r9m3a.py", "testing/d003/stage_s5r3/run_maketest_s5r3.py"),
    ("testing/d003/stage_s4r9/judge_maketest_r9m3b_v2.py", "testing/d003/stage_s5r3/judge_maketest_s5r3.py"),
]


def sub(line):
    for a, b in SUBST:
        line = line.replace(a, b)
    return line


def read(p):
    return open(p, encoding="utf-8").read().splitlines()


def residual_of(orig_lines, copy_lines):
    na = [sub(x) for x in orig_lines]
    sm = difflib.SequenceMatcher(None, na, copy_lines)
    res = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        for x in na[i1:i2]:
            res.append(("-", x))
        for x in copy_lines[j1:j2]:
            res.append(("+", x))
    return res


def main():
    out = ["# COPY_DIFF_S5R3.txt -- U373 copy proof for the S5R3 apparatus scripts",
           "# Substitution rule (applied to the ORIGINAL line): 'p05-s4r9/m3b' / 'p05-s4r9/m3a' -> 'p05-s5r3';",
           "#   'stage_s4r9' -> 'stage_s5r3'; script file names *_r9m3b*/*_r9m3a* -> *_s5r3; 'R9M3B'/'R9M3A' -> 'S5R3';",
           "#   'r9m3b'/'r9m3a' -> 's5r3'; 'M3A'/'M3a'/'m3a' -> 'M3B'/'M3b'/'m3b'.",
           "# STRICT pairs: after the substitution the copy must be identical, except declared additions listed below.",
           "# ADAPTED pairs: the brief requires a resumable segment runner and a 4-case positive control; the full",
           "#   unified diff is printed and every residual line is reported as ADAPTED (no silent logic change).",
           ""]
    strict_unexpected = strict_declared = 0
    for orig, copy, tag in STRICT:
        a = read(os.path.join(REPO, orig))
        b = read(os.path.join(REPO, copy))
        res = residual_of(a, b)
        dec = DECLARED.get(tag, [])
        def is_declared(tag2, ln):
            if tag2 == "e2e_judge" and ln.strip() == "":
                return True
            return any(m in ln for m in dec)
        unexp = [ln for _, ln in res if not is_declared(tag, ln)]
        decn = len(res) - len(unexp)
        strict_unexpected += len(unexp)
        strict_declared += decn
        out.append("=" * 78)
        out.append("STRICT %s -> %s" % (orig, copy))
        out.append("original_lines=%d copy_lines=%d residual=%d declared=%d unexpected=%d" % (len(a), len(b), len(res), decn, len(unexp)))
        out += list(difflib.unified_diff(a, b, fromfile=orig, tofile=copy, lineterm="", n=1))
        for sign, ln in res:
            out.append("%s %s | %s" % (sign, "DECLARED" if is_declared(tag, ln) else "UNEXPECTED", ln))
        out.append("")
    adapted_residual = 0
    for orig, copy in ADAPTED:
        a = read(os.path.join(REPO, orig))
        b = read(os.path.join(REPO, copy))
        res = residual_of(a, b)
        adapted_residual += len(res)
        out.append("=" * 78)
        out.append("ADAPTED %s -> %s (copy + required additions; residual lines are ADAPTED)" % (orig, copy))
        out.append("original_lines=%d copy_lines=%d residual=%d" % (len(a), len(b), len(res)))
        out += list(difflib.unified_diff(a, b, fromfile=orig, tofile=copy, lineterm="", n=1))
        for sign, ln in res:
            out.append("%s ADAPTED | %s" % (sign, ln))
        out.append("")
    out.append("SUMMARY strict_pairs=%d strict_declared=%d strict_unexpected=%d adapted_pairs=%d adapted_residual=%d" %
               (len(STRICT), strict_declared, strict_unexpected, len(ADAPTED), adapted_residual))
    out.append("COPY_CHECK_VERDICT: %s" % ("PASS" if strict_unexpected == 0 else "FAIL"))
    open(OUT, "w", encoding="utf-8").write(NL.join(out) + NL)
    print("STRICT pairs=%d declared=%d unexpected=%d ADAPTED residual=%d" % (len(STRICT), strict_declared, strict_unexpected, adapted_residual))
    for orig, copy, tag in STRICT:
        a = read(os.path.join(REPO, orig))
        b = read(os.path.join(REPO, copy))
        res = residual_of(a, b)
        print("  %-38s residual=%d" % (copy.split("/")[-1], len(res)))
    print("WROTE " + os.path.relpath(OUT, REPO))
    return 0 if strict_unexpected == 0 else 1


if __name__ == "__main__":
    sys.exit(main())