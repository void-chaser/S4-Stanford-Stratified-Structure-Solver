#!/usr/bin/env python3
# s5r4_apply_patch.py -- U384 registry patch: append one S5R4/ES5-9 sentence to exactly three lines
# (ISSUE_REGISTRY.md D016 row; PROJECT_ROADMAP.md P05 row and D016 sub-item) and assert with a unified diff
# that no other line changed. It also asserts the R3->R4 chain of custody: the "before" sha256 of each file
# equals the sha256 recorded by the S5R3 registry patch (REGISTRY_APPLY_DIFF_S5R3.txt in the R3 evidence).
# usage: s5r4_apply_patch.py formal [--ev-root DIR] [--ev3-root DIR] [--stage-repo DIR]
import os, sys, re, hashlib, difflib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV4_REAL = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r4")
EV3 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)
SENT_ISSUE = "；ES5-9/S5R4 收口：独立重判 DIFFS=0（E2E 42 点 / D016 33 行为点 SAME），S5R3 end 门禁 8 项 FAIL 全部消解（数据 sha 不变）、readiness GAP=0、S5R3 registry 覆盖 26/26；见 checkpoints/p05/registries/s5r4/ 与 P05_S5R4_REPORT.md（ES5-10..ES5-14）"
SENT_P05 = "；（ES5-9）S5R4 收口补齐：独立重判 DIFFS=0（E2E 42 点、D016 33 行为点 + ROOT_CAUSE_RC 记 NOT_JUDGED_SOURCE_RECORD）、S5R3 end 门禁 8 项 FAIL 全消解、readiness GAP=0、S5R3 registry 26/26，见 checkpoints/p05/P05_S5R4_REPORT.md 与 registries/s5r4/（等待用户审核）"
SENT_D016 = "；（ES5-9）2026-10-18 P05-S5 R4 独立重判（U379）对该判定表重判 DIFFS=0（33 行为点全 SAME，ROOT_CAUSE_RC 记 NOT_JUDGED_SOURCE_RECORD），S5R3 数据 sha 不变；见 checkpoints/p05/registries/s5r4/REJUDGE_S5R4.tsv。"


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def r3_after():
    d = {}
    p = os.path.join(EV3, "REGISTRY_APPLY_DIFF_S5R3.txt")
    for line in open(p, encoding="utf-8"):
        m = re.match(r"FILE (testing/s4test/ISSUE_REGISTRY.md|PROJECT_ROADMAP.md) .* after_sha256=([0-9a-f]{64})", line)
        if m:
            d[m.group(1)] = m.group(2)
    return d


def patch_table_line(line, sent):
    idx = line.rstrip().rfind(" |")
    if idx < 0:
        return line.rstrip() + sent
    return line.rstrip()[:idx] + sent + line.rstrip()[idx:]


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "formal":
        print("usage: s5r4_apply_patch.py formal [--ev-root DIR] [--ev3-root DIR] [--stage-repo DIR]", file=sys.stderr)
        return 2
    def arg(n, d):
        return os.path.abspath(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
    EV = arg("--ev-root", EV4_REAL)
    STAGE = arg("--stage-repo", REPO)
    before_ok = r3_after()
    specs = [
        ("testing/s4test/ISSUE_REGISTRY.md", ["| D016 / P1（P05-S5 R2 核对完成"], [SENT_ISSUE]),
        ("PROJECT_ROADMAP.md", ["| P05 | Phase 2 A：D003", "    - **D016**（已实施，归 D003"],
         [SENT_P05, SENT_D016]),
    ]
    out = ["# REGISTRY_APPLY_DIFF_S5R4.txt -- U384 approved registry patch (only the scripted lines change)",
           "# chain of custody: before_sha256 must equal the after_sha256 of the S5R3 patch (EV3/REGISTRY_APPLY_DIFF_S5R3.txt)"]
    ok = True
    for rel, markers, sents in specs:
        p = os.path.join(STAGE, rel)
        old = open(p, encoding="utf-8").read()
        lines = old.splitlines()
        idx = []
        for m in markers:
            hits = [i for i, l in enumerate(lines) if m in l]
            if len(hits) != 1:
                print("HARD_STOP marker %r in %s hits=%d" % (m, rel, len(hits)))
                return 2
            idx.append(hits[0])
        new_lines = list(lines)
        for i, sent in zip(idx, sents):
            if "|" in lines[i] and lines[i].rstrip().endswith("|"):
                new_lines[i] = patch_table_line(lines[i], sent)
            else:
                new_lines[i] = lines[i].rstrip() + sent
        new = NL.join(new_lines) + NL
        # assert: only the listed line indices changed
        changed = [i for i, (a, b) in enumerate(zip(lines, new_lines)) if a != b]
        diff = list(difflib.unified_diff(lines, new_lines, fromfile=rel + " (before)", tofile=rel + " (after)", lineterm="", n=1))
        listed_ok = (changed == idx)
        chain_ok = (before_ok.get(rel) == sha_f(p))
        if not listed_ok or not chain_ok:
            ok = False
        out.append("FILE %s before_bytes=%d after_bytes=%d before_sha256=%s after_sha256=%s" % (
            rel, len(old.encode("utf-8")), len(new.encode("utf-8")), sha_f(p), hashlib.sha256(new.encode("utf-8")).hexdigest()))
        out.append("# LISTED_LINE_INDICES=%s CHANGED=%s LISTED_ONLY=%s R3_TO_R4_CHAIN=%s" % (
            ",".join(str(i + 1) for i in idx), ",".join(str(i + 1) for i in changed),
            "PASS" if listed_ok else "FAIL", "PASS" if chain_ok else "FAIL"))
        out.append("# unchanged lines=%d changed lines=%d" % (len(lines) - len(changed), len(changed)))
        out += diff
        open(p, "w", encoding="utf-8").write(new)
    out.append("# ASSERT_ONLY_LISTED_LINES_CHANGED: %s" % ("PASS" if ok else "FAIL"))
    path = os.path.join(EV, "REGISTRY_APPLY_DIFF_S5R4.txt")
    open(path, "w", encoding="utf-8").write(NL.join(out) + NL)
    print("REGISTRY_PATCH ok=%s" % ok)
    print("WROTE " + os.path.relpath(path, REPO))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
