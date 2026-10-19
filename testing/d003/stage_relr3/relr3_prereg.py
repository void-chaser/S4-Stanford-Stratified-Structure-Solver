#!/usr/bin/env python3
# relr3_prereg.py -- P05 delivery round REL-R3 pre-registration (task brief section 4), written BEFORE
# any push.  It writes PREREG_RELR3.tsv (status INFLUENCED) and PREREG_RELR3.tsv.sha256.txt with the UTC
# time.  The expectations are the task brief section 4 R1-R9 rows; the 'task_wording' column keeps the
# task wording verbatim, the 'expected'/'method' columns state what is actually measured.  R9 is split:
# its final empty-working-tree part is re-measured by the end gate after commit (i) (a comparison table
# cannot certify a clean status that includes the table itself); the V table records the measured
# HEAD-not-rewritten + round-files-only part and points at the gate re-measurement.
import os, sys, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r3")
OUT = os.path.join(EV, "PREREG_RELR3.tsv")
SHATXT = os.path.join(EV, "PREREG_RELR3.tsv.sha256.txt")
TAB = chr(9)
NL = chr(10)
PRODUCT_BRANCH = "p05/d003-fft-error-propagation"
ARCHIVE_BRANCH = "archive/p05-d003-full-20261019"
PROD_HEAD = "8e4c01491b6edec9eb4eaa617265ce9ca53bd548"
ARCHIVE_HEAD = "4607e969ba138f8bcaffa4fba6340dd3b2e1f25b"
F4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
MASTER = "5b72793051eb705f0e9b2e5398e1a5f0484da0cb"
TAG1_OBJ = "ef925cdea019a7cdf00acb66bc5b59d55f00d868"
TAG2_OBJ = "b42c4c16298ce644f39c3c33ae6c26ef18820a96"
REMOTE_URL = "https://github.com/void-chaser/S4-Stanford-Stratified-Structure-Solver.git"


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


ROWS = [
    ("R1", "remote refs/heads/" + PRODUCT_BRANCH + " sha",
     "after push (a); read-only git ls-remote origin refs/heads/" + PRODUCT_BRANCH,
     PROD_HEAD,
     "R1-R4: git ls-remote origin 中四个 ref 的 sha 分别等于本地 8e4c014、4607e96、tag 对象 ef925cde…、tag 对象 b42c4c16…"),
    ("R2", "remote refs/heads/" + ARCHIVE_BRANCH + " sha",
     "after push (b); read-only git ls-remote origin refs/heads/" + ARCHIVE_BRANCH,
     ARCHIVE_HEAD,
     "R1-R4: git ls-remote origin 中四个 ref 的 sha 分别等于本地 8e4c014、4607e96、tag 对象 ef925cde…、tag 对象 b42c4c16…"),
    ("R3", "remote refs/tags/p05-signed-20261019 tag object sha",
     "after push (c); read-only git ls-remote origin refs/tags/p05-signed-20261019",
     TAG1_OBJ,
     "R1-R4: git ls-remote origin 中四个 ref 的 sha 分别等于本地 8e4c014、4607e96、tag 对象 ef925cde…、tag 对象 b42c4c16…"),
    ("R4", "remote refs/tags/p05-rel-r1-20261019 tag object sha",
     "after push (d); read-only git ls-remote origin refs/tags/p05-rel-r1-20261019",
     TAG2_OBJ,
     "R1-R4: git ls-remote origin 中四个 ref 的 sha 分别等于本地 8e4c014、4607e96、tag 对象 ef925cde…、tag 对象 b42c4c16…"),
    ("R5", "remote master and the six pre-existing heads unchanged",
     "after the four pushes; read-only git ls-remote origin compared with REMOTE_BEFORE_RELR3.tsv; "
     "master=" + MASTER,
     "master=" + MASTER + "; refs/heads/checkpoint/014rf-offline-evidence-accepted-20261003, "
     "refs/heads/codex/master-integration-gate-20261010, refs/heads/codex/p04-acceptance-review-20261009, "
     "refs/heads/feature/python314-binding, refs/heads/fix/modern-linux-build, refs/heads/master keep their "
     "pre-push shas",
     "R5：远端 master 仍是 5b72793，其它 6 个旧分支 sha 不变"),
    ("R6", "fresh remote clone of the product branch",
     "git clone --branch " + PRODUCT_BRANCH + " " + REMOTE_URL + " $EV/remoteclone; "
     "then git rev-parse HEAD and HEAD:S4",
     "HEAD=" + PROD_HEAD + "; HEAD:S4=" + F4,
     "R6：用 git clone --branch p05/d003-fft-error-propagation <origin URL> $EV/remoteclone 从远端新克隆，"
     "HEAD = 8e4c014，HEAD:S4 = 589e15eb…"),
    ("R7", "make test in the R6 clone",
     "make test PYTHON=python3 in $EV/remoteclone, stderr merged into stdout before parsing; "
     "unit set compared with REL-R2 V3 (MAKETEST_UNITS_RELR1.tsv column F4_p1); rc and failure set recorded",
     "rc=0; units=265; failing=none; missing=none; extra=none",
     "R7：在 R6 的克隆里跑 make test，rc=0，单元集合等于 REL-R2 V3 的 265 个，无失败（合并 stderr 后再解析）"),
    ("R8", "Draft PR in the fork",
     "gh pr view <n> --json state,isDraft,baseRefName,headRefName,commits,changedFiles (read-only)",
     "state=OPEN; isDraft=true; baseRefName=master; headRefName=" + PRODUCT_BRANCH + "; commits=2; changedFiles=11",
     "R8：Draft PR 存在，状态 OPEN，isDraft=true，base=master，head=p05/d003-fft-error-propagation，"
     "commits=2，changedFiles=11"),
    ("R9", "main repository final state",
     "V row records the V-generation-time measurement: HEAD is not rewritten (4607e96 or a descendant) and every "
     "working-tree change is a round bookkeeping file inside checkpoints/p05/ or testing/d003/stage_relr3/; "
     "the final empty git status --short after commit (i) is re-measured by the end gate (RECORD STATUS_CLEAN_AFTER_COMMIT)",
     "HEAD unrewritten; working tree = round bookkeeping files only; final git status --short empty after commit (i)",
     "R9：主仓库 git status --short 为空，HEAD 仍是本轮的记账提交链"),
]


def main():
    if os.path.isfile(OUT):
        print("HARD_STOP " + os.path.relpath(OUT, REPO) + " already exists; pre-registration is written once")
        return 2
    os.makedirs(EV, exist_ok=True)
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = ["# PREREG_RELR3.tsv -- P05 delivery round REL-R3 pre-registration (task brief section 4). STATUS: INFLUENCED.",
             "# Written before the first push of the round; the sha256 below is recorded before the pushes start.",
             "# INFLUENCED: the expectations come from the task brief section 4 R1-R9, not from a blind trial.",
             "# No row is rewritten after this point; any correction goes to ERRATA_RELR3.txt only.",
             "# $REPO = repository root; $EV = checkpoints/p05/evidence/p05-rel-r3;",
             "# product branch HEAD = " + PROD_HEAD + "; archive branch HEAD = " + ARCHIVE_HEAD + " (current work branch tip);",
             "# F4 tree = " + F4 + "; origin = " + REMOTE_URL + ".",
             "# Columns: test_id, item, method, expected, task_wording, status",
             "# Written: " + utc]
    lines.append(TAB.join(["test_id", "item", "method", "expected", "task_wording", "status"]))
    for rid, item, method, expected, wording in ROWS:
        lines.append(TAB.join([rid, item, method, expected, wording, "INFLUENCED"]))
    body = NL.join(lines) + NL
    open(OUT, "w", encoding="utf-8").write(body)
    sha = sha_f(OUT)
    open(SHATXT, "w", encoding="utf-8").write(
        "# PREREG_RELR3.tsv.sha256.txt -- sha256 of the pre-registration written before any push\n"
        "# algorithm: sha256; unit: bytes; UTC: " + utc + NL
        + "PREREG_RELR3.tsv" + TAB + sha + TAB + "bytes=" + str(len(body.encode("utf-8"))) + TAB + "utc=" + utc + NL)
    print("WROTE PREREG rows=%d sha256=%s utc=%s" % (len(ROWS), sha, utc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
