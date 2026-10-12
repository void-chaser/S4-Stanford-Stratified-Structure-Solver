#!/usr/bin/env python3
"""P05-S4 R7 continuation gate (part 1, section 2 item 1).  New file; r7_gate.py is not changed.

Read-only checks, printed to stdout (the caller redirects into $EV/GATE_R7_CONT1.txt through safe_run):
  - HEAD == 8e13729635c20dc658abc2a35e8195b26e3b9bec
  - HEAD:S4 == a07b5ac:S4 == F2 e124925f5b242486a913b813fa181664f665b048
  - judge_d003.py sha256 == d2d04145...209eb
  - git status --short: only the R7 untracked files are allowed
  - RULINGS.tsv: count of rows U34..U43 (expected 0 before this part, recorded only)
  - /tmp top-level snapshot
Exit 0 only if every check that is a gate passes.
"""
import hashlib
import os
import subprocess
import sys

EXPECT_HEAD = "8e13729635c20dc658abc2a35e8195b26e3b9bec"
EXPECT_F2 = "e124925f5b242486a913b813fa181664f665b048"
EXPECT_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
ALLOWED_UNTRACKED_PREFIX = (
    "checkpoints/p05/briefs/P05_S4R7_BRIEF.md",
    "checkpoints/p05/briefs/P05_S4R7_BRIEF_CONT1.md",
    "checkpoints/p05/registries/s4r7/",
    "testing/d003/stage_s4r7/",
)


def git(*args):
    out = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return out.stdout.strip()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    failures = []
    repo = git("rev-parse", "--show-toplevel")
    os.chdir(repo)
    print("REPO", repo)
    head = git("rev-parse", "HEAD")
    print("HEAD", head)
    if head != EXPECT_HEAD:
        failures.append("HEAD != 8e13729")
    s4head = git("rev-parse", "HEAD:S4")
    s4f2 = git("rev-parse", "a07b5ac:S4")
    print("HEAD:S4", s4head)
    print("a07b5ac:S4", s4f2)
    if s4head != EXPECT_F2 or s4f2 != EXPECT_F2:
        failures.append("HEAD:S4 or a07b5ac:S4 != F2")
    j = sha256_file("testing/d003/judge_d003.py")
    print("judge_d003.py sha256", j)
    if j != EXPECT_JUDGE:
        failures.append("judge sha256 mismatch")
    st = [ln for ln in git("status", "--short", "--untracked-files=all").splitlines() if ln.strip()]
    print("git status --short (count)", len(st))
    for ln in st:
        print("  STATUS", ln)
    extra = []
    for ln in st:
        code, path = ln[:2], ln[3:]
        if code == "??" and any(path == p or path.startswith(p) for p in ALLOWED_UNTRACKED_PREFIX):
            continue
        extra.append(ln)
    if extra:
        failures.append("worktree has unexpected entries: " + "; ".join(extra))
    with open("checkpoints/p05/registries/RULINGS.tsv", encoding="utf-8") as fh:
        n_u34 = sum(1 for ln in fh if ln.split("\t", 1)[0] in {"U%d" % k for k in range(34, 44)})
    print("RULINGS rows U34-U43 before this part (informational)", n_u34)
    tmp = sorted(os.listdir("/tmp"))
    print("/tmp top-level entries", len(tmp))
    print("/tmp top-level listing sha256", hashlib.sha256("\n".join(tmp).encode("utf-8")).hexdigest())
    if failures:
        print("GATE RESULT: FAIL")
        for f in failures:
            print("  FAILURE:", f)
        return 1
    print("GATE RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
