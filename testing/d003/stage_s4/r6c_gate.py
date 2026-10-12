#!/usr/bin/env python3
# r6c_gate.py -- P05-S4 R6c-0 gate (new file; copied from r6b_gate.py and modified for R6c).
# Read-only checks of the repository and of the top level of the temporary area, written to
# $EV/GATE_R6c.txt (start) or $EV/GATE_R6c_END.txt (end).  Every comparison is computed here; nothing is typed by hand.
#
# Changes against r6b_gate.py (recorded in ERRATA_6c):
#   * EXPECT_HEAD is the R6c opening baseline b9fbe00 (R6b milestone-free partial commit).
#   * registries/s4r6b SHA256SUMS.txt is re-verified entry by entry (sha256 computed here).
#   * the R6b preregistration v1 (REGISTRY_S4_PRE_R6b_STATE.tsv) sha256 is checked (v1 is not edited).
#   * the /tmp top-level snapshot (count and listing sha256) is RECORDED at start and end; the end gate compares
#     the end snapshot with the start snapshot.  A non-zero count is recorded, not treated as a failure by itself.
#   * the end gate accepts HEAD = b9fbe00 or a commit whose parent is b9fbe00 and whose subject contains "R6c milestone".
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c_gate.py EVDIR start|end
import hashlib
import os
import subprocess
import sys

EXPECT_BRANCH = "codex/p05-d003-fft-error-propagation"
EXPECT_HEAD = "b9fbe00f577e64a92c57522369ba7a0ab6ece316"
EXPECT_S4 = "4a6f64927a30537740dd0c8f11f9a5aae5e46ba4"
EXPECT_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECT_PREREG_V1 = "f2523d146e7e5adbf80cf99fdc35ba7b64b0e22ac5e4cc1409e97203cba0c358"
OWN_GATE = "testing/d003/stage_s4/r6c_gate.py"
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


def verify_sums(regdir):
    """Return (n_ok, bad list) for a SHA256SUMS.txt in regdir (format: '<sha>  <name>')."""
    path = os.path.join(regdir, "SHA256SUMS.txt")
    ok, bad = 0, []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            want, name = line.split(None, 1)
            name = name.strip()
            fp = os.path.join(regdir, name)
            got = sha256_file(fp) if os.path.isfile(fp) else "MISSING"
            if got == want:
                ok += 1
            else:
                bad.append("%s(got=%s)" % (name, got[:12]))
    return ok, bad


def read_tmp_baseline(ev):
    """Return (count, listing_sha) recorded by the start gate in GATE_R6c.txt, or None."""
    p = os.path.join(ev, "GATE_R6c.txt")
    if not os.path.isfile(p):
        return None
    cnt, sha = None, None
    with open(p, encoding="utf-8") as fh:
        for raw in fh:
            parts = raw.rstrip("\n").split("\t")
            if parts[0] == "/tmp top-level entry count":
                cnt = int(parts[1])
            elif parts[0] == "/tmp listing sha256":
                sha = parts[1]
    if cnt is None or sha is None:
        return None
    return cnt, sha


def main(argv):
    if len(argv) != 3 or argv[2] not in ("start", "end"):
        raise SystemExit("usage: r6c_gate.py EVDIR start|end")
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
    reg = os.path.join(repo, "checkpoints", "p05", "registries", "s4r6b")
    n_ok, bad = verify_sums(reg)
    prereg_v1 = sha256_file(os.path.join(reg, "REGISTRY_S4_PRE_R6b_STATE.tsv"))

    rows.append(("branch", branch, EXPECT_BRANCH, branch == EXPECT_BRANCH))
    if phase == "start":
        rows.append(("HEAD", head, EXPECT_HEAD, head == EXPECT_HEAD))
        rows.append(("STATE.md last commit == HEAD", state_last, head, state_last == head))
        rows.append(("HEAD:S4", s4, EXPECT_S4, s4 == EXPECT_S4))
        rows.append(("judge_d003.py sha256", judge, EXPECT_JUDGE, judge == EXPECT_JUDGE))
        rows.append(("registries/s4r6b SHA256SUMS entries OK", "%d OK; bad=%s" % (n_ok, bad if bad else "none"),
                     "all entries OK", len(bad) == 0 and n_ok > 0))
        rows.append(("REGISTRY_S4_PRE_R6b_STATE.tsv (v1) sha256", prereg_v1, EXPECT_PREREG_V1,
                     prereg_v1 == EXPECT_PREREG_V1))
        own = "?? " + OWN_GATE
        lines = [ln.strip() for ln in status.splitlines() if ln.strip()]
        others = [ln for ln in lines if ln != own]
        rows.append(("git status --short --untracked-files=all", status if status else "(empty)",
                     "(empty) or only: " + own + " (this round's gate script; the one allowed exception)",
                     len(others) == 0))
    else:
        head_parent = git("rev-parse", "HEAD~1")
        head_subj = git("log", "-1", "--format=%s", "HEAD")
        head_ok = (head == EXPECT_HEAD) or (head_parent == EXPECT_HEAD and "R6c milestone" in head_subj)
        rows.append(("HEAD", head, "b9fbe00 or R6c milestone commit (parent b9fbe00)", head_ok))
        rows.append(("HEAD:S4", s4, EXPECT_S4, s4 == EXPECT_S4))
        rows.append(("judge_d003.py sha256", judge, EXPECT_JUDGE, judge == EXPECT_JUDGE))
        rows.append(("registries/s4r6b SHA256SUMS entries OK", "%d OK; bad=%s" % (n_ok, bad if bad else "none"),
                     "all entries OK", len(bad) == 0 and n_ok > 0))
        lines = [ln.strip() for ln in status.splitlines() if ln.strip()]
        others = []
        for ln in lines:
            parts = ln.split(None, 1)
            code = parts[0] if parts else ""
            path = parts[1].strip() if len(parts) > 1 else ""
            if code == "??" and path.startswith("testing/d003/stage_s4/") and "r6c" in os.path.basename(path):
                continue
            if code == "M" and path.startswith("checkpoints/p05/"):
                continue
            if code == "??" and path.startswith("checkpoints/p05/"):
                continue
            others.append(ln)
        rows.append(("git status --short --untracked-files=all (end)", status if status else "(empty)",
                     "only r6c files under testing/d003/stage_s4/ and checkpoints/p05/ (uncommitted)", len(others) == 0))
    # /tmp is a snapshot only (AGENTS.md section 3): both gates RECORD it; neither gate fails on its content.
    if phase == "start":
        rows.append(("/tmp top-level entry count (start snapshot)", str(n_tmp), "recorded", True))
        rows.append(("/tmp listing sha256 (start snapshot)", tmp_sha, "recorded", True))
    else:
        base = read_tmp_baseline(ev)
        rows.append(("/tmp top-level entry count (end snapshot)", str(n_tmp),
                     "recorded; start snapshot = %s" % (base[0] if base else "NO BASELINE"), True))
        rows.append(("/tmp listing sha256 (end snapshot)", tmp_sha,
                     "recorded; start snapshot = %s" % (base[1][:16] + "..." if base else "NO BASELINE"), True))
    ok = all(r[3] for r in rows)
    out = os.path.join(ev, "GATE_R6c.txt" if phase == "start" else "GATE_R6c_END.txt")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# R6c gate (%s) -- written by testing/d003/stage_s4/r6c_gate.py (read-only checks)\n" % phase)
        fh.write("# UTC %s\n" % subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], stdout=subprocess.PIPE,
                                                 check=False).stdout.decode().strip())
        fh.write("# Exception recorded: %s is untracked at the start gate (this round's own gate script).\n" % OWN_GATE)
        fh.write("item\tobserved\texpected\tmatch\n")
        for name, obs, exp, m in rows:
            fh.write("%s\t%s\t%s\t%s\n" % (name, obs, exp, "OK" if m else "MISMATCH"))
        fh.write("RESULT\t%s\n" % ("PASS" if ok else "FAIL"))
    print("gate %s: %s -> %s" % (phase, "PASS" if ok else "FAIL", out))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
