#!/usr/bin/env python3
# r6b_gate.py -- P05-S4 R6b-0 gate (new file).  Read-only checks of the repository and /tmp, written to
# $EV/GATE_R6b.txt.  The script does not compare by hand: every comparison below is computed here.
# Usage: python3 -I -B testing/d003/stage_s4/r6b_gate.py EVDIR PHASE   (PHASE = start | end)
import hashlib
import os
import subprocess
import sys

EXPECT_BRANCH = "codex/p05-d003-fft-error-propagation"
EXPECT_HEAD = "20b3411ec52c50e40b158486778063db034f0141"
EXPECT_S4 = "4a6f64927a30537740dd0c8f11f9a5aae5e46ba4"
EXPECT_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EMPTY_SHA = hashlib.sha256(b"").hexdigest()


def git(*args):
    return subprocess.run(["git"] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False).stdout.decode("utf-8", "replace").strip()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def tmp_snapshot():
    names = sorted(os.listdir("/tmp"))
    listing = "\n".join(names) + ("\n" if names else "")
    return len(names), hashlib.sha256(listing.encode("utf-8")).hexdigest()


def main(argv):
    if len(argv) != 3 or argv[2] not in ("start", "end"):
        raise SystemExit("usage: r6b_gate.py EVDIR start|end")
    ev, phase = argv[1], argv[2]
    repo = git("rev-parse", "--show-toplevel")
    rows = []
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    head = git("rev-parse", "HEAD")
    state_last = git("log", "-1", "--format=%H", "--", "checkpoints/p05/STATE.md")
    s4 = git("rev-parse", "HEAD:S4")
    judge = sha256_file(os.path.join(repo, "testing", "d003", "judge_d003.py"))
    status = git("status", "--short", "--untracked-files=all")
    n_tmp, tmp_sha = tmp_snapshot()
    rows.append(("branch", branch, EXPECT_BRANCH, branch == EXPECT_BRANCH))
    rows.append(("HEAD", head, EXPECT_HEAD, head == EXPECT_HEAD))
    rows.append(("STATE.md last commit == HEAD", state_last, head, state_last == head))
    rows.append(("HEAD:S4", s4, EXPECT_S4, s4 == EXPECT_S4))
    rows.append(("judge_d003.py sha256", judge, EXPECT_JUDGE, judge == EXPECT_JUDGE))
    # Start gate: the status must be empty except this round's own gate script (written before its first run).
    # End gate: the only allowed status lines are new r6b files under testing/d003/stage_s4/ (not yet committed).
    own = "?? testing/d003/stage_s4/r6b_gate.py"
    lines = [ln.strip() for ln in status.splitlines() if ln.strip()]
    if phase == "start":
        others = [ln for ln in lines if ln != own]
        expected_text = "(empty) or only: " + own
    else:
        others = []
        for ln in lines:
            parts = ln.split(None, 1)
            code = parts[0] if parts else ""
            path = parts[1].strip() if len(parts) > 1 else ""
            if code == "??" and path.startswith("testing/d003/stage_s4/") and "r6b" in os.path.basename(path):
                continue
            if code == "M" and path.startswith("checkpoints/p05/"):
                continue
            others.append(ln)
        expected_text = "only new r6b files under testing/d003/stage_s4/ (uncommitted) and modified STATE/report"
    rows.append(("git status --short --untracked-files=all", status if status else "(empty)", expected_text, len(others) == 0))
    rows.append(("/tmp top-level entry count", str(n_tmp), "0 (phase start)", n_tmp == 0))
    rows.append(("/tmp listing sha256", tmp_sha, EMPTY_SHA + " (empty listing)", tmp_sha == EMPTY_SHA or n_tmp > 0))
    ok = all(r[3] for r in rows)
    out = os.path.join(ev, "GATE_R6b.txt" if phase == "start" else "GATE_R6b_END.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# R6b gate (%s) -- written by testing/d003/stage_s4/r6b_gate.py (read-only checks)\n" % phase)
        fh.write("# UTC %s\n" % subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], stdout=subprocess.PIPE,
                                                 check=False).stdout.decode().strip())
        fh.write("item\tobserved\texpected\tmatch\n")
        for name, obs, exp, m in rows:
            fh.write("%s\t%s\t%s\t%s\n" % (name, obs, exp, "OK" if m else "MISMATCH"))
        fh.write("RESULT\t%s\n" % ("PASS" if ok else "FAIL"))
    print("gate %s: %s -> %s" % (phase, "PASS" if ok else "FAIL", out))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
