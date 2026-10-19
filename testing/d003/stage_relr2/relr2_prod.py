#!/usr/bin/env python3
# relr2_prod.py -- P05 delivery round REL-R2: build the product branch in an independent local clone
# under $EV/prod (task brief section 3).  The main repository is only READ (git clone source); every
# write happens inside $EV/prod or $EV/tmp.  Steps:
#   1. git clone $REPO $EV/prod                      (source read-only)
#   2. in the clone: git checkout -b p05/d003-fft-error-propagation 5b72793
#   3. in the clone: git checkout 3de6d8b -- S4       (exactly the ten-file S4 delta)
#   4. verify the staged S4 tree == 589e15eb... before committing (hard check)
#   5. commit the source change (English message; B baseline, F4 tree hash, REL-R1 conclusion)
#   6. add doc/P05_D003_SUMMARY.md (from testing/d003/stage_relr2/) and commit it separately
#   7. verify HEAD:S4, clean worktree, and that the tree has no checkpoints/, testing/d003/, AGENTS.md
# Writes: $EV/prod/**, $EV/tmp/**, $EV/PROD_RELR2.tsv.  Run through safe_run.sh.
import os, sys, subprocess, hashlib, shutil, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r2")
PROD = os.path.join(EV, "prod")
TMP = os.path.join(EV, "tmp")
STAGE = os.path.join(REPO, "testing/d003/stage_relr2")
DOC_SRC = os.path.join(STAGE, "relr2_doc_P05_D003_SUMMARY.md")
OUT = os.path.join(EV, "PROD_RELR2.tsv")
TAB = chr(9)
NL = chr(10)
BRANCH = "p05/d003-fft-error-propagation"
BASE = "5b72793051eb705f0e9b2e5398e1a5f0484da0cb"          # B
FIX = "3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505"           # F4 commit
EXP_S4 = "589e15eb11fcb04e031b524f25a443e7921946cf"        # F4 S4 tree
FILES = ["S4/S4.cpp", "S4/S4_internal.h", "S4/fmm/fmm_FFT.cpp", "S4/fmm/fmm_PolBasisJones.cpp",
         "S4/fmm/fmm_PolBasisNV.cpp", "S4/fmm/fmm_PolBasisVL.cpp", "S4/fmm/fmm_closed.cpp",
         "S4/fmm/fmm_experimental.cpp", "S4/fmm/fmm_kottke.cpp", "S4/pattern/pattern.c"]
RECORDS = []
STEPS = []

COMMIT1 = """P05 D003: propagate FMM/FFT and pattern allocation failures to the public API

Source-only port of the P05 D003 fix. The S4 tree after this commit is the frozen F4 tree
589e15eb11fcb04e031b524f25a443e7921946cf (P05 commit 3de6d8b), applied on top of the upstream
baseline B (5b72793, S4 tree 1d738e64f9864a475fdb3de34cd3601605df2c64). The ten changed files
are exactly git diff 5b72793 3de6d8b -- S4 (+311/-80): S4.cpp, S4_internal.h,
S4/fmm/fmm_FFT.cpp, S4/fmm/fmm_PolBasisJones.cpp, S4/fmm/fmm_PolBasisNV.cpp,
S4/fmm/fmm_PolBasisVL.cpp, S4/fmm/fmm_closed.cpp, S4/fmm/fmm_experimental.cpp,
S4/fmm/fmm_kottke.cpp and S4/pattern/pattern.c.

P05 delivery round REL-R1 (non-regression of F4 against B) reported SAME=317, BOTH_FAIL=12
(pre-existing failures), SKIP_DECLARED=5, NEW_FAIL=0, DIFF=0, FLAKY=0, unit_count=265,
NON_REGRESSION=PASS. This commit adds no new claim.

awaiting user review
"""

COMMIT2 = """P05 D003: add the product-branch summary document

doc/P05_D003_SUMMARY.md states the problem, lists the per-file changes, quotes the REL-R1 and
S5 R3 verification summaries with the fault-injection dependency, lists the known limitations and
the transferred items, and says where the full P05 audit records live. It is written from the
commit diff and the P05 reports only. This commit does not touch S4/, so the build inputs are
identical to the source commit.

awaiting user review
"""


def sh(args, cwd=PROD, check=True, env=None):
    e = dict(os.environ)
    if env:
        e.update(env)
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, env=e)
    if check and p.returncode != 0:
        raise SystemExit("HARD_STOP command failed rc=%d: %s\n%s\n%s" % (p.returncode, " ".join(args),
                                                                         p.stdout[-2000:], p.stderr[-2000:]))
    return p


def record(k, v):
    RECORDS.append((k, str(v)))


def step(name, fn):
    try:
        note = fn()
        STEPS.append((name, "OK", "" if note is None else str(note)))
        return note
    except SystemExit as exc:
        STEPS.append((name, "HARD_STOP", str(exc)[:400]))
        raise
    except Exception as exc:
        STEPS.append((name, "EXC", repr(exc)[:400]))
        raise


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    os.makedirs(TMP, exist_ok=True)
    if os.path.exists(PROD):
        raise SystemExit("HARD_STOP %s already exists; this script runs once (no overwrite)" % PROD)

    def do_clone():
        sh(["git", "clone", REPO, PROD], cwd=TMP)
        return "cloned"
    step("clone", do_clone)
    record("PROD_DIR", os.path.relpath(PROD, REPO))
    record("CLONE_SOURCE", REPO)

    def do_checkout():
        sh(["git", "checkout", "-b", BRANCH, BASE])
        return sh(["git", "rev-parse", "HEAD"]).stdout.strip()
    record("BRANCH", BRANCH)
    record("BASE_COMMIT", BASE)
    step("checkout_branch_at_B", do_checkout)

    def do_apply():
        sh(["git", "checkout", FIX, "--"] + FILES)
        return "checked out %d files from %s" % (len(FILES), FIX)
    step("apply_S4_delta", do_apply)
    record("FIX_COMMIT", FIX)

    def check_staged_s4():
        tree = sh(["git", "write-tree"]).stdout.strip()
        s4 = sh(["git", "rev-parse", tree + ":S4"]).stdout.strip()
        record("STAGED_S4", s4)
        if s4 != EXP_S4:
            raise SystemExit("HARD_STOP staged S4 tree %s != %s" % (s4, EXP_S4))
        return s4
    step("hard_check_staged_S4", check_staged_s4)

    def commit1():
        msgp = os.path.join(TMP, "relr2_commit1.txt")
        open(msgp, "w", encoding="utf-8").write(COMMIT1)
        sh(["git", "add", "--"] + FILES)
        sh(["git", "commit", "-F", msgp])
        return sh(["git", "rev-parse", "HEAD"]).stdout.strip()
    c1 = step("commit_source", commit1)
    record("COMMIT1", c1)

    def check_c1_s4():
        got = sh(["git", "rev-parse", "HEAD:S4"]).stdout.strip()
        if got != EXP_S4:
            raise SystemExit("HARD_STOP commit1 HEAD:S4 %s != %s" % (got, EXP_S4))
        return got
    step("hard_check_commit1_S4", check_c1_s4)

    def add_doc():
        docdir = os.path.join(PROD, "doc")
        if not os.path.isdir(docdir):
            os.makedirs(docdir)
        shutil.copyfile(DOC_SRC, os.path.join(docdir, "P05_D003_SUMMARY.md"))
        lines = sum(1 for _ in open(os.path.join(docdir, "P05_D003_SUMMARY.md"), encoding="utf-8"))
        record("DOC_LINES", lines)
        record("DOC_SHA256", sha_f(os.path.join(docdir, "P05_D003_SUMMARY.md")))
        if lines > 200:
            raise SystemExit("HARD_STOP doc has %d lines > 200" % lines)
        return "doc lines=%d" % lines
    step("add_doc", add_doc)

    def commit2():
        msgp = os.path.join(TMP, "relr2_commit2.txt")
        open(msgp, "w", encoding="utf-8").write(COMMIT2)
        sh(["git", "add", "doc/P05_D003_SUMMARY.md"])
        sh(["git", "commit", "-F", msgp])
        return sh(["git", "rev-parse", "HEAD"]).stdout.strip()
    c2 = step("commit_doc", commit2)
    record("COMMIT2", c2)
    record("PROD_HEAD", c2)

    def final_checks():
        head_s4 = sh(["git", "rev-parse", "HEAD:S4"]).stdout.strip()
        record("PROD_HEAD_S4", head_s4)
        if head_s4 != EXP_S4:
            raise SystemExit("HARD_STOP product HEAD:S4 %s != %s" % (head_s4, EXP_S4))
        st = sh(["git", "status", "--porcelain"], check=False).stdout.strip()
        record("PROD_WORKTREE_STATUS", st if st else "clean")
        if st:
            raise SystemExit("HARD_STOP product worktree not clean")
        # Baseline B itself already ships historical checkpoints/014rf and checkpoints/p04-final.
        # The product branch must not ADD any audit directory or P05 device, so the check is on the
        # paths changed above B (task brief section 3.3: no checkpoints/, testing/d003/, AGENTS.md).
        inherited = [p for p in sh(["git", "ls-tree", "-r", "--name-only", BASE]).stdout.splitlines()
                     if p.startswith("checkpoints/")]
        record("INHERITED_CHECKPOINTS_FROM_B", "%d paths: %s" % (len(inherited), ",".join(inherited[:6])))
        changed = sh(["git", "diff", "--name-only", BASE + "..HEAD"]).stdout.splitlines()
        bad = [p for p in changed if p.startswith("checkpoints/") or p.startswith("testing/d003/")
               or p == "AGENTS.md"]
        record("FORBIDDEN_PATHS_ADDED", ",".join(bad) if bad else "none")
        if bad:
            raise SystemExit("HARD_STOP forbidden paths added above B: " + ",".join(bad[:5]))
        not_s4 = [p for p in changed if not p.startswith("S4/")]
        record("NON_S4_CHANGED_PATHS", ",".join(not_s4) if not_s4 else "none")
        n = sh(["git", "rev-list", "--count", BASE + "..HEAD"]).stdout.strip()
        record("COMMITS_ABOVE_B", n)
        if n != "2":
            raise SystemExit("HARD_STOP expected 2 commits above B, got " + n)
        stat = sh(["git", "diff", "--stat", BASE + "..HEAD"]).stdout.strip()
        record("DIFF_STAT", stat.replace(NL, " | ")[:600])
        recs = sh(["git", "log", "--format=%H%x09%s", BASE + "..HEAD"]).stdout.strip()
        record("COMMIT_LIST", recs.replace(NL, " ;; "))
        tree = sh(["git", "ls-tree", "-r", "--name-only", "HEAD"]).stdout.splitlines()
        for f in FILES:
            if f not in tree:
                raise SystemExit("HARD_STOP missing " + f)
        return "ok"
    step("final_checks", final_checks)
    record("PROD_BUILT_UTC", datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))

    lines = ["# PROD_RELR2.tsv -- REL-R2 product branch construction record (task brief section 3)",
             "# Built in an independent local clone under the round evidence directory; the main repository",
             "# was only read (git clone source).  Run " + RECORDS[-1][1],
             TAB.join(["key", "value"])]
    lines += [TAB.join([k, v]) for k, v in RECORDS]
    lines += ["", "# steps", TAB.join(["step", "status", "note"])]
    lines += [TAB.join(s) for s in STEPS]
    open(OUT, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("WROTE", os.path.relpath(OUT, REPO))
    print("PROD_HEAD", c2, "S4", EXP_S4)
    return 0


if __name__ == "__main__":
    sys.exit(main())
