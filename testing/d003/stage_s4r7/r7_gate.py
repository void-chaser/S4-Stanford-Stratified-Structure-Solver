#!/usr/bin/env python3
"""P05-S4 R7-0 gate (new file).  Read-only checks; prints a report to stdout.

Run through safe_run (the caller redirects stdout into $EV/GATE_R7.txt):
  sh testing/d003/safe_run.sh p05-s4r7 -- sh -c 'python3 -I -B testing/d003/stage_s4r7/r7_gate.py > "$1/GATE_R7.txt" 2>&1' sh "$EV"

Checks (brief section 2):
  - HEAD == 8e13729635c20dc658abc2a35e8195b26e3b9bec
  - HEAD:S4 == a07b5ac:S4 == F2 e124925f5b242486a913b813fa181664f665b048
  - 1c11905:S4 == F 4a6f64927a30537740dd0c8f11f9a5aae5e46ba4
  - git diff --name-only 1c11905 a07b5ac -- S4/ == {S4/pattern/pattern.c, S4/S4_internal.h}
  - judge_d003.py sha256 == d2d04145...209eb
  - registries s3r3 and s4r6d SHA256SUMS.txt: every line OK
  - worktree clean except briefs/P05_S4R7_BRIEF.md and this gate script (untracked)
  - /tmp top-level snapshot (entry count and sha256 of the sorted listing)
Exit 0 only if every check passes.
"""
import hashlib
import os
import subprocess
import sys

EXPECT_HEAD = "8e13729635c20dc658abc2a35e8195b26e3b9bec"
EXPECT_F2_TREE = "e124925f5b242486a913b813fa181664f665b048"
EXPECT_F_TREE = "4a6f64927a30537740dd0c8f11f9a5aae5e46ba4"
EXPECT_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECT_S4_DIFF = {"S4/pattern/pattern.c", "S4/S4_internal.h"}
ALLOWED_UNTRACKED = {
    "checkpoints/p05/briefs/P05_S4R7_BRIEF.md",
    "testing/d003/stage_s4r7/r7_gate.py",
}


def git(*args):
    out = subprocess.run(["git", *args], capture_output=True, text=True, check=False)
    return out.returncode, out.stdout.strip(), out.stderr.strip()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_sums(path):
    base = os.path.dirname(path)
    ok = bad = 0
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            want, name = line.split(None, 1)
            name = name.strip()
            got = sha256_file(os.path.join(base, name))
            if got == want:
                ok += 1
            else:
                bad += 1
                print("SUMS_BAD", path, name)
    return ok, bad


def main():
    failures = []
    rc, repo, _ = git("rev-parse", "--show-toplevel")
    if rc != 0:
        print("FAIL: not in a git work tree")
        return 1
    os.chdir(repo)
    print("REPO", repo)

    _, head, _ = git("rev-parse", "HEAD")
    print("HEAD", head)
    if head != EXPECT_HEAD:
        failures.append("HEAD != 8e13729")

    _, s4head, _ = git("rev-parse", "HEAD:S4")
    _, s4f2, _ = git("rev-parse", "a07b5ac:S4")
    _, s4f, _ = git("rev-parse", "1c11905:S4")
    print("HEAD:S4", s4head)
    print("a07b5ac:S4", s4f2)
    print("1c11905:S4", s4f)
    if s4head != EXPECT_F2_TREE:
        failures.append("HEAD:S4 != F2")
    if s4f2 != EXPECT_F2_TREE:
        failures.append("a07b5ac:S4 != F2")
    if s4f != EXPECT_F_TREE:
        failures.append("1c11905:S4 != F")

    _, diff, _ = git("diff", "--name-only", "1c11905", "a07b5ac", "--", "S4/")
    names = {ln.strip() for ln in diff.splitlines() if ln.strip()}
    print("F->F2 S4 names", sorted(names))
    if names != EXPECT_S4_DIFF:
        failures.append("F->F2 S4 diff is not exactly pattern.c and S4_internal.h")

    judge_sha = sha256_file("testing/d003/judge_d003.py")
    print("judge_d003.py sha256", judge_sha)
    if judge_sha != EXPECT_JUDGE_SHA:
        failures.append("judge sha256 mismatch")

    for sums in ("checkpoints/p05/registries/s3r3/SHA256SUMS.txt",
                 "checkpoints/p05/registries/s4r6d/SHA256SUMS.txt"):
        ok, bad = check_sums(sums)
        print("SHA256SUMS", sums, "OK", ok, "BAD", bad)
        if bad or ok == 0:
            failures.append("SHA256SUMS not all OK: " + sums)

    _, st, _ = git("status", "--short", "--untracked-files=all")
    lines = [ln for ln in st.splitlines() if ln.strip()]
    print("git status --short (count)", len(lines))
    for ln in lines:
        print("  STATUS", ln)
    extra = [ln for ln in lines if not (ln[:2] == "??" and ln[3:] in ALLOWED_UNTRACKED)]
    if extra:
        failures.append("worktree not clean: " + "; ".join(extra))

    tmp_entries = sorted(os.listdir("/tmp"))
    listing = "\n".join(tmp_entries).encode("utf-8")
    print("/tmp top-level entries", len(tmp_entries))
    print("/tmp top-level listing sha256", hashlib.sha256(listing).hexdigest())
    for name in tmp_entries[:50]:
        print("  TMP", name)

    if failures:
        print("GATE RESULT: FAIL")
        for f in failures:
            print("  FAILURE:", f)
        return 1
    print("GATE RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
