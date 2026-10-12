#!/usr/bin/env python3
# r6c2_gate.py -- P05-S4 R6c2-0 gate (new file; copied from r6c_gate.py and changed for R6c2).
# Read-only checks of the repository and of the top level of /tmp, written to $EV/GATE_R6c2.txt (start) or
# $EV/GATE_R6c2_END.txt (end).  Every comparison is computed here.  Nothing is typed by hand.
#
# Changes against r6c_gate.py (recorded in ERRATA_6c E6c-6 and in the R6c2 report):
#   * EXPECT_HEAD = fa7a247 (R6c2 opening baseline).
#   * registries/s4r6c SHA256SUMS_seam.txt: every entry must be OK.
#   * registries/s4r6c SHA256SUMS.txt: every entry must be OK EXCEPT ERRATA_6c.txt.  For that entry the gate
#     checks the E6c-6 facts: (a) the manifest value equals the sha256 of the 64-line version in commit 6bba0bd
#     (read with git show, no file written); (b) the first 64 lines of the current file are byte-identical to that
#     64-line version; (c) the current file has at least 64 lines.
#   * the seam pre-registration REGISTRY_S4_PRE_R6c_SEAM.tsv: sha256 must start with 093c68a8 and end with d576c.
#   * the working tree must be clean: the only untracked file allowed is this round's gate script.
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c2_gate.py EVDIR start|end
import hashlib
import os
import subprocess
import sys

EXPECT_BRANCH = "codex/p05-d003-fft-error-propagation"
EXPECT_HEAD = "fa7a247ff6d6b92c824b7774d4032cdbdd814bab"
EXPECT_S4 = "4a6f64927a30537740dd0c8f11f9a5aae5e46ba4"
EXPECT_JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
EXPECT_PREREG_V1 = "f2523d146e7e5adbf80cf99fdc35ba7b64b0e22ac5e4cc1409e97203cba0c358"
EXPECT_SEAM_PREFIX = "093c68a8"
EXPECT_SEAM_SUFFIX = "d576c"
ERRATA_REL = "checkpoints/p05/registries/s4r6c/ERRATA_6c.txt"
ERRATA_COMMIT = "6bba0bd"
ERRATA_PREFIX_LINES = 64
ERRATA_OLD_SHA_PREFIX = "7875959f"
OWN_GATE = "testing/d003/stage_s4/r6c2_gate.py"


def git(*args):
    return subprocess.run(["git"] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False).stdout.decode("utf-8", "replace").strip()


def git_bytes(*args):
    p = subprocess.run(["git"] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    return p.returncode, p.stdout


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


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


def verify_sums(regdir, skip=(), sums_name="SHA256SUMS.txt"):
    """Return (n_ok, bad list, skipped list) for the sums file in regdir (format: '<sha>  <name>')."""
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


def manifest_value(regdir, name):
    with open(os.path.join(regdir, "SHA256SUMS.txt"), encoding="utf-8") as fh:
        for raw in fh:
            parts = raw.rstrip("\n").split(None, 1)
            if len(parts) == 2 and parts[1].strip() == name:
                return parts[0]
    return None


def errata_checks(repo, regdir):
    """E6c-6 facts for ERRATA_6c.txt.  Returns list of (label, observed, expected, ok)."""
    rows = []
    cur_path = os.path.join(repo, ERRATA_REL)
    with open(cur_path, "rb") as fh:
        cur = fh.read()
    cur_lines = cur.splitlines(keepends=True)
    rc, old = git_bytes("show", "%s:%s" % (ERRATA_COMMIT, ERRATA_REL))
    old_lines = old.splitlines(keepends=True) if rc == 0 else []
    man = manifest_value(regdir, "ERRATA_6c.txt")
    rows.append(("ERRATA_6c.txt manifest sha256 (SHA256SUMS.txt)", man or "NONE",
                 "starts with %s (64-line version, E6c-6)" % ERRATA_OLD_SHA_PREFIX,
                 bool(man) and man.startswith(ERRATA_OLD_SHA_PREFIX)))
    old_sha = sha256_bytes(old) if rc == 0 else "NONE"
    rows.append(("ERRATA_6c.txt at %s: git show exit code and line count" % ERRATA_COMMIT,
                 "rc=%d lines=%d" % (rc, len(old_lines)), "rc=0 lines=%d" % ERRATA_PREFIX_LINES,
                 rc == 0 and len(old_lines) == ERRATA_PREFIX_LINES))
    rows.append(("sha256 of the 64-line version at %s" % ERRATA_COMMIT, old_sha,
                 "equals manifest value (prefix %s)" % ERRATA_OLD_SHA_PREFIX,
                 bool(man) and old_sha == man))
    prefix_same = (len(cur_lines) >= ERRATA_PREFIX_LINES and
                   cur_lines[:ERRATA_PREFIX_LINES] == old_lines[:ERRATA_PREFIX_LINES])
    rows.append(("current ERRATA_6c.txt first 64 lines byte-identical to %s version" % ERRATA_COMMIT,
                 "lines_now=%d prefix_identical=%s" % (len(cur_lines), prefix_same),
                 "prefix_identical=True", prefix_same))
    rows.append(("current ERRATA_6c.txt sha256 (for the record; expected to differ, E6c-6)",
                 sha256_file(cur_path), "differs from manifest value (E6c-6)",
                 sha256_file(cur_path) != man))
    return rows


def main(argv):
    if len(argv) != 3 or argv[2] not in ("start", "end"):
        raise SystemExit("usage: r6c2_gate.py EVDIR start|end")
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
    reg_b = os.path.join(repo, "checkpoints", "p05", "registries", "s4r6b")
    reg_c = os.path.join(repo, "checkpoints", "p05", "registries", "s4r6c")
    n_ok_b, bad_b, _ = verify_sums(reg_b)
    prereg_v1 = sha256_file(os.path.join(reg_b, "REGISTRY_S4_PRE_R6b_STATE.tsv"))
    n_ok_seam, bad_seam, _ = verify_sums(reg_c, sums_name="SHA256SUMS_seam.txt")
    n_ok_c, bad_c, skipped_c = verify_sums(reg_c, skip=("ERRATA_6c.txt",))
    seam_pre = sha256_file(os.path.join(reg_c, "REGISTRY_S4_PRE_R6c_SEAM.tsv"))

    rows.append(("branch", branch, EXPECT_BRANCH, branch == EXPECT_BRANCH))
    if phase == "start":
        rows.append(("HEAD", head, EXPECT_HEAD, head == EXPECT_HEAD))
        rows.append(("STATE.md last commit == HEAD", state_last, head, state_last == head))
        rows.append(("HEAD:S4", s4, EXPECT_S4, s4 == EXPECT_S4))
        rows.append(("judge_d003.py sha256", judge, EXPECT_JUDGE, judge == EXPECT_JUDGE))
        rows.append(("registries/s4r6b SHA256SUMS entries OK", "%d OK; bad=%s" % (n_ok_b, bad_b if bad_b else "none"),
                     "all entries OK", len(bad_b) == 0 and n_ok_b > 0))
        rows.append(("REGISTRY_S4_PRE_R6b_STATE.tsv (v1) sha256", prereg_v1, EXPECT_PREREG_V1,
                     prereg_v1 == EXPECT_PREREG_V1))
        rows.append(("registries/s4r6c SHA256SUMS_seam.txt entries OK",
                     "%d OK; bad=%s" % (n_ok_seam, bad_seam if bad_seam else "none"),
                     "all entries OK", len(bad_seam) == 0 and n_ok_seam > 0))
        rows.append(("registries/s4r6c SHA256SUMS.txt entries OK except ERRATA_6c.txt",
                     "%d OK; bad=%s; skipped=%s" % (n_ok_c, bad_c if bad_c else "none", skipped_c),
                     "all entries OK except ERRATA_6c.txt (E6c-6)", len(bad_c) == 0 and n_ok_c > 0))
        for r in errata_checks(repo, reg_c):
            rows.append(("E6c-6: " + r[0], r[1], r[2], r[3]))
        rows.append(("REGISTRY_S4_PRE_R6c_SEAM.tsv sha256 prefix/suffix", seam_pre,
                     "%s...%s" % (EXPECT_SEAM_PREFIX, EXPECT_SEAM_SUFFIX),
                     seam_pre.startswith(EXPECT_SEAM_PREFIX) and seam_pre.endswith(EXPECT_SEAM_SUFFIX)))
        own = "?? " + OWN_GATE
        lines = [ln.strip() for ln in status.splitlines() if ln.strip()]
        others = [ln for ln in lines if ln != own]
        rows.append(("git status --short --untracked-files=all", status if status else "(empty)",
                     "(empty) or only: " + own + " (this round's gate script; the one allowed exception)",
                     len(others) == 0))
    else:
        head_parent = git("rev-parse", "HEAD~1")
        head_subj = git("log", "-1", "--format=%s", "HEAD")
        head_ok = (head == EXPECT_HEAD) or (head_parent == EXPECT_HEAD and "R6c2" in head_subj)
        rows.append(("HEAD", head, "fa7a247 or an R6c2 commit (parent fa7a247)", head_ok))
        rows.append(("HEAD:S4", s4, EXPECT_S4, s4 == EXPECT_S4))
        rows.append(("judge_d003.py sha256", judge, EXPECT_JUDGE, judge == EXPECT_JUDGE))
        rows.append(("registries/s4r6c SHA256SUMS_seam.txt entries OK",
                     "%d OK; bad=%s" % (n_ok_seam, bad_seam if bad_seam else "none"),
                     "all entries OK", len(bad_seam) == 0 and n_ok_seam > 0))
        rows.append(("REGISTRY_S4_PRE_R6c_SEAM.tsv sha256 prefix/suffix", seam_pre,
                     "%s...%s" % (EXPECT_SEAM_PREFIX, EXPECT_SEAM_SUFFIX),
                     seam_pre.startswith(EXPECT_SEAM_PREFIX) and seam_pre.endswith(EXPECT_SEAM_SUFFIX)))
        lines = [ln.strip() for ln in status.splitlines() if ln.strip()]
        others = []
        for ln in lines:
            parts = ln.split(None, 1)
            code = parts[0] if parts else ""
            path = parts[1].strip() if len(parts) > 1 else ""
            if code == "??" and path.startswith("testing/d003/stage_s4/") and "r6c2" in os.path.basename(path):
                continue
            if code in ("M", "??", "A") and path.startswith("checkpoints/p05/"):
                continue
            others.append(ln)
        rows.append(("git status --short --untracked-files=all (end)", status if status else "(empty)",
                     "only r6c2 files under testing/d003/stage_s4/ and checkpoints/p05/ (uncommitted)",
                     len(others) == 0))
    # /tmp is a snapshot only (AGENTS.md section 3): both gates RECORD it; neither gate fails on its content.
    if phase == "start":
        rows.append(("/tmp top-level entry count (start snapshot)", str(n_tmp), "recorded", True))
        rows.append(("/tmp listing sha256 (start snapshot)", tmp_sha, "recorded", True))
    else:
        base_cnt, base_sha = None, None
        gp = os.path.join(ev, "GATE_R6c2.txt")
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
    out = os.path.join(ev, "GATE_R6c2.txt" if phase == "start" else "GATE_R6c2_END.txt")
    if os.path.exists(out):
        raise SystemExit("REFUSED: gate file exists, never overwritten (U17): %s" % out)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# R6c2 gate (%s) -- written by testing/d003/stage_s4/r6c2_gate.py (read-only checks)\n" % phase)
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
