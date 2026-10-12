#!/usr/bin/env python3
"""P05-S3R3 gate (S3R3-0). Read-only checks; prints a report to stdout.

Run as:  python3 -I -B testing/d003/stage_s3r3/s3r3_gate.py
(the caller redirects stdout into the round's evidence directory through safe_run.sh)

Checks (brief section 2):
  - HEAD == cadf258 (full hash below)
  - HEAD:S4 == F (4a6f649...)
  - judge_d003.py sha256 == d2d04145...209eb
  - registries/s4r6d/SHA256SUMS.txt: every line OK
  - git status --short: only the brief and this gate script may be untracked
  - /tmp top-level snapshot (entry count and sha256 of the sorted listing)
Exit status 0 only when every check passes; otherwise 1.
"""
import hashlib
import os
import subprocess
import sys

EXPECT_HEAD = "cadf25809c80fec1887d07485dc641bbd1693610"
EXPECT_S4_TREE = "4a6f64927a30537740dd0c8f11f9a5aae5e46ba4"
EXPECT_JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
ALLOWED_UNTRACKED = {
    "checkpoints/p05/briefs/P05_S3R3_BRIEF.md",
    "testing/d003/stage_s3r3/s3r3_gate.py",
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


def main():
    failures = []
    rc, repo, _ = git("rev-parse", "--show-toplevel")
    if rc != 0:
        print("FAIL: not in a git work tree")
        return 1
    os.chdir(repo)
    print("REPO", repo)

    rc, head, _ = git("rev-parse", "HEAD")
    print("HEAD", head)
    if head != EXPECT_HEAD:
        failures.append("HEAD != cadf258")

    rc, s4tree, _ = git("rev-parse", "HEAD:S4")
    print("HEAD:S4", s4tree)
    if s4tree != EXPECT_S4_TREE:
        failures.append("HEAD:S4 != F")

    judge = "testing/d003/judge_d003.py"
    jsha = sha256_file(judge)
    print("judge_d003.py sha256", jsha)
    if jsha != EXPECT_JUDGE_SHA:
        failures.append("judge sha256 mismatch")

    sums = "checkpoints/p05/registries/s4r6d/SHA256SUMS.txt"
    base = os.path.dirname(sums)
    ok = bad = 0
    with open(sums, "r", encoding="utf-8") as fh:
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
                print("SUMS_BAD", name, want, got)
    print("s4r6d SHA256SUMS OK", ok, "BAD", bad)
    if bad or ok == 0:
        failures.append("s4r6d SHA256SUMS not all OK")

    rc, st, _ = git("status", "--short", "--untracked-files=all")
    lines = [ln for ln in st.splitlines() if ln.strip()]
    print("git status --short (count)", len(lines))
    for ln in lines:
        print("  STATUS", ln)
    extra = []
    for ln in lines:
        code, path = ln[:2], ln[3:]
        if code == "??" and path in ALLOWED_UNTRACKED:
            continue
        extra.append(ln)
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
