#!/usr/bin/env python3
# r6d_gate.py -- P05-S4 R6d-0 gate (new file; copied from r6c2_gate.py and changed for R6d).
# Read-only checks of the repository and of the top level of /tmp, written to $EV/GATE_R6d.txt (start) or
# $EV/GATE_R6d_END.txt (end).  Every comparison is computed here.  Nothing is typed by hand.
#
# Changes against r6c2_gate.py (recorded in the R6d report):
#   * EXPECT_HEAD = 053f1c3 (R6d opening baseline, the report-only commit after the R6c2 closeout 43ef3a8).
#   * the last commit that modified checkpoints/p05/STATE.md must be 43ef3a8 (053f1c3 changed only the report).
#   * registries/s4r6c SHA256SUMS_closeout.txt: every entry must be OK (new in R6c2).
#   * registries/s4r6c SHA256SUMS_seam.txt: every entry must be OK.
#   * the ERRATA_6c.txt entry of SHA256SUMS.txt is still checked by E6c-6 facts (prefix of 64 lines at 6bba0bd).
#   * the working tree must be clean: the only untracked file allowed is this round's gate script.
#   * the /tmp top-level snapshot is recorded at start and end (not a failure).
#
# Usage: python3 -I -B testing/d003/stage_s4/r6d_gate.py EVDIR start|end
import hashlib
import os
import subprocess
import sys

EXPECT_BRANCH = "codex/p05-d003-fft-error-propagation"
EXPECT_HEAD = "053f1c30eece85781dc6aadc12f4580d5c0f3d28"
EXPECT_STATE_LAST = "43ef3a8e4bd8fbc173b9e9c4144aba16996cec76"
EXPECT_S4 = "4a6f64927a30537740dd0c8f11f9a5aae5e46ba4"
EXPECT_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
OWN_GATE = "testing/d003/stage_s4/r6d_gate.py"
ERRATA_REL = "checkpoints/p05/registries/s4r6c/ERRATA_6c.txt"
ERRATA_COMMIT = "6bba0bd"
ERRATA_PREFIX_LINES = 64


def git(*args):
    return subprocess.run(["git"] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False).stdout.decode("utf-8", "replace").strip()


def git_bytes(*args):
    p = subprocess.run(["git"] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.returncode, p.stdout


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


def verify_sums(regdir, sums_name="SHA256SUMS.txt", skip=()):
    path = os.path.join(regdir, sums_name)
    ok, bad, skipped = 0, [], []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            want, name = line.split(None, 1)
            name = name.strip()
            if name in skip:
                skipped.append(name)
                continue
            fp = os.path.join(regdir, name)
            got = sha256_file(fp) if os.path.isfile(fp) else "MISSING"
            if got == want:
                ok += 1
            else:
                bad.append("%s(got=%s)" % (name, got[:12]))
    return ok, bad, skipped


def errata_prefix_ok(repo):
    """E6c-6: the first 64 lines of the current ERRATA_6c.txt equal the 64-line version committed at 6bba0bd."""
    with open(os.path.join(repo, ERRATA_REL), "rb") as fh:
        cur = fh.read().splitlines(keepends=True)
    rc, old = git_bytes("show", "%s:%s" % (ERRATA_COMMIT, ERRATA_REL))
    old_l = old.splitlines(keepends=True) if rc == 0 else []
    ok = rc == 0 and len(old_l) == ERRATA_PREFIX_LINES and len(cur) >= ERRATA_PREFIX_LINES and \
        cur[:ERRATA_PREFIX_LINES] == old_l
    return ok, "lines_now=%d prefix_identical=%s" % (len(cur), ok)


def main(argv):
    if len(argv) != 3 or argv[2] not in ("start", "end"):
        raise SystemExit("usage: r6d_gate.py EVDIR start|end")
    ev, phase = argv[1], argv[2]
    repo = git("rev-parse", "--show-toplevel")
    branch = git("rev-parse", "--abbrev-ref", "HEAD")
    head = git("rev-parse", "HEAD")
    state_last = git("log", "-1", "--format=%H", "--", "checkpoints/p05/STATE.md")
    s4 = git("rev-parse", "HEAD:S4")
    judge = sha256_file(os.path.join(repo, "testing", "d003", "judge_d003.py"))
    status = git("status", "--short", "--untracked-files=all")
    n_tmp, tmp_sha = tmp_snapshot()
    reg_c = os.path.join(repo, "checkpoints", "p05", "registries", "s4r6c")
    n_cl, bad_cl, _ = verify_sums(reg_c, sums_name="SHA256SUMS_closeout.txt")
    n_seam, bad_seam, _ = verify_sums(reg_c, sums_name="SHA256SUMS_seam.txt")
    pref_ok, pref_obs = errata_prefix_ok(repo)

    rows = []
    rows.append(("branch", branch, EXPECT_BRANCH, branch == EXPECT_BRANCH))
    rows.append(("HEAD", head, EXPECT_HEAD, head == EXPECT_HEAD))
    rows.append(("STATE.md last commit", state_last, EXPECT_STATE_LAST, state_last == EXPECT_STATE_LAST))
    rows.append(("HEAD:S4", s4, EXPECT_S4, s4 == EXPECT_S4))
    rows.append(("judge_d003.py sha256", judge, EXPECT_JUDGE, judge == EXPECT_JUDGE))
    rows.append(("registries/s4r6c SHA256SUMS_closeout.txt entries OK",
                 "%d OK; bad=%s" % (n_cl, bad_cl if bad_cl else "none"),
                 "all entries OK", len(bad_cl) == 0 and n_cl > 0))
    rows.append(("registries/s4r6c SHA256SUMS_seam.txt entries OK",
                 "%d OK; bad=%s" % (n_seam, bad_seam if bad_seam else "none"),
                 "all entries OK", len(bad_seam) == 0 and n_seam > 0))
    rows.append(("E6c-6 ERRATA_6c.txt first 64 lines identical to 6bba0bd", pref_obs, "prefix_identical=True", pref_ok))
    own = "?? " + OWN_GATE
    lines = [ln.strip() for ln in status.splitlines() if ln.strip()]
    others = [ln for ln in lines if ln != own]
    if phase == "start":
        rows.append(("git status --short --untracked-files=all", status if status else "(empty)",
                     "(empty) or only: " + own + " (this round's gate script; the one allowed exception)",
                     len(others) == 0))
        rows.append(("/tmp top-level entry count (start snapshot)", str(n_tmp), "recorded", True))
        rows.append(("/tmp listing sha256 (start snapshot)", tmp_sha, "recorded", True))
    else:
        rows.append(("git status --short --untracked-files=all (end)", status if status else "(empty)",
                     "only r6d files under testing/d003/stage_s4/ and checkpoints/p05/ (uncommitted)",
                     all(ln.split(None, 1)[1].startswith(("checkpoints/p05/", "testing/d003/stage_s4/r6d"))
                         for ln in lines if ln.split(None, 1)[0] in ("??", "M", "A") and len(ln.split(None, 1)) > 1)))
        base_cnt, base_sha = None, None
        gp = os.path.join(ev, "GATE_R6d.txt")
        if os.path.isfile(gp):
            with open(gp, encoding="utf-8") as fh:
                for raw in fh:
                    parts = raw.rstrip("\n").split("\t")
                    if parts[0] == "/tmp top-level entry count (start snapshot)":
                        base_cnt = parts[1]
                    elif parts[0] == "/tmp listing sha256 (start snapshot)":
                        base_sha = parts[1]
        rows.append(("/tmp top-level entry count (end snapshot)", str(n_tmp),
                     "recorded; start snapshot = %s" % (base_cnt or "NO BASELINE"), True))
        rows.append(("/tmp listing sha256 (end snapshot)", tmp_sha,
                     "recorded; start snapshot = %s" % ((base_sha or "NO BASELINE")[:16] + "..."), True))
    ok = all(r[3] for r in rows)
    out = os.path.join(ev, "GATE_R6d.txt" if phase == "start" else "GATE_R6d_END.txt")
    if os.path.exists(out):
        raise SystemExit("REFUSED: gate file exists, never overwritten (U17): %s" % out)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# R6d gate (%s) -- written by testing/d003/stage_s4/r6d_gate.py (read-only checks)\n" % phase)
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
