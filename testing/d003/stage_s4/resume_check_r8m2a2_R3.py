#!/usr/bin/env python3
# resume_check_r8m2a2_R3.py -- P05-S4 R8 M2a2 CONT1 section 0: read-only resume check (R3).
# Does not repeat the start gate and does not overwrite GATE_R8_M2a2_start.txt.
# Output: $EV/RESUME_CHECK_R8_M2a2_R3.tsv   columns: item, expected, actual, result
# Byte prefixes of RULINGS.tsv and ERRATA_8.txt are compared with the HEAD blobs (not with constants).
import hashlib
import os
import re
import subprocess
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
OUT = os.path.join(EV, "RESUME_CHECK_R8_M2a2_R3.tsv")
ALLOW_END = os.path.join(REPO, "testing", "d003", "stage_s4", "gate_allow_r8m2a2_end.txt")
M2A = "checkpoints/p05/registries/s4r8/M2/r8m2a/"
RUL = "checkpoints/p05/registries/RULINGS.tsv"
ERR = "checkpoints/p05/registries/s4r8/ERRATA_8.txt"
BASE = "6a4f0031afeda0a3105c9983d5a65a2d847f1488"
S4TREE = "6cff923a02baf19e01966b2339755cbf3a5deeef"
JUDGE = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
RUL_N = 92855
ERR_N = 67104


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    with open(p, "rb") as fh:
        return sha_bytes(fh.read())


def git_bytes(*a):
    return subprocess.run(["git"] + list(a), cwd=REPO, capture_output=True).stdout


def git(*a):
    return git_bytes(*a).decode("utf-8", "replace").strip()


def main():
    if os.path.exists(OUT):
        print("resume_check_r8m2a2_R3: REFUSED exists (U17)")
        return 2
    rows = []

    def chk(item, exp, act, note=""):
        ok = (str(exp) == str(act))
        rows.append((item, str(exp), str(act), "PASS" if ok else "FAIL", note))

    chk("HEAD", BASE, git("rev-parse", "HEAD"))
    chk("HEAD_S4", S4TREE, git("rev-parse", "HEAD:S4"))
    chk("JUDGE_SHA256", JUDGE, sha_file(os.path.join(REPO, "testing", "d003", "judge_d003.py")))
    chk("S4_WORKTREE_STATUS", "", git("status", "--short", "--", "S4"), "S4/ must have no change")
    chk("S4_DIFF_VS_HEAD", "", git("diff", "--name-only", "HEAD", "--", "S4"), "S4/ must have no change")

    # RULINGS and ERRATA: working-tree prefix must equal the HEAD blob prefix, byte for byte
    head_rul = git_bytes("show", "HEAD:" + RUL)
    head_err = git_bytes("show", "HEAD:" + ERR)
    work_rul = open(os.path.join(REPO, RUL), "rb").read()
    work_err = open(os.path.join(REPO, ERR), "rb").read()
    chk("RULINGS_HEAD_BYTES", RUL_N, len(head_rul), "HEAD blob size (informative)")
    chk("RULINGS_PREFIX_EQ_HEAD", sha_bytes(head_rul[:RUL_N]), sha_bytes(work_rul[:RUL_N]),
        "first %d bytes equal HEAD" % RUL_N)
    chk("RULINGS_HEAD_IS_PREFIX", True, work_rul.startswith(head_rul), "HEAD content is a prefix of the working file")
    chk("ERRATA_HEAD_BYTES", ERR_N, len(head_err), "HEAD blob size (informative)")
    chk("ERRATA_PREFIX_EQ_HEAD", sha_bytes(head_err[:ERR_N]), sha_bytes(work_err[:ERR_N]),
        "first %d bytes equal HEAD" % ERR_N)
    chk("ERRATA_HEAD_IS_PREFIX", True, work_err.startswith(head_err), "HEAD content is a prefix of the working file")

    rt = work_rul.decode("utf-8").splitlines()
    for i in range(236, 248):
        n = sum(1 for l in rt if l.split("\t")[0] == "U%d" % i)
        chk("RULINGS_U%d_ROWS" % i, 1, n)
    et = work_err.decode("utf-8").splitlines()
    for i in range(91, 96):
        n = sum(1 for l in et if re.match(r"^E8-%d\b" % i, l))
        chk("ERRATA_E8-%d_ENTRIES" % i, 1, n)

    # git status: every entry must match the end allow list (glob patterns, one per line, '#' comments)
    allow = [l.rstrip("\n") for l in open(ALLOW_END, encoding="utf-8") if l.strip() and not l.startswith("#")]
    import fnmatch
    status = [l for l in git_bytes("status", "--short", "-uall").decode("utf-8").split("\n") if l]
    for l in status:
        code, path = l[:2], l[3:]
        hit = False
        for pat in allow:
            code_pat, path_pat = pat[:2], pat[3:]
            if code_pat == code and fnmatch.fnmatch(path, path_pat):
                hit = True
                break
        rows.append(("STATUS_ENTRY", "allow-listed", l, "PASS" if hit else "FAIL", "matched end allow list" if hit else "NOT in allow list"))

    chk("TRACKED_MODIFIED", RUL + "|" + ERR,
        "|".join(sorted(git("diff", "--name-only", "HEAD").split())),
        "only RULINGS and ERRATA may be modified; STATE must be unchanged")
    chk("STATE_UNCHANGED", "", git("diff", "--name-only", "HEAD", "--", "checkpoints/p05/STATE.md"))

    # r8m2a registry: the 20 tracked files must equal their HEAD blobs
    tracked = [x for x in git("ls-files", M2A).split("\n") if x]
    chk("R8M2A_TRACKED_COUNT", 20, len(tracked))
    diffs = 0
    for p in tracked:
        head_b = git_bytes("show", "HEAD:" + p)
        if sha_bytes(head_b) != sha_file(os.path.join(REPO, p)):
            diffs += 1
    chk("R8M2A_TRACKED_SHA_DIFFS", 0, diffs, "each tracked file equals its HEAD blob")
    chk("R8M2A_PREREG_SHA", "557f568a787f3d216c0a412c597cabc41dbc46771f1404691565f3b2ae362e80",
        sha_file(os.path.join(REPO, M2A, "PREREG_M2_R8_M2a_R2.tsv")))

    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# RESUME_CHECK_R8_M2a2_R3 -- CONT1 section 0, read-only; start gate not repeated\n")
        fh.write("item\texpected\tactual\tresult\tnote\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
        fails = sum(1 for r in rows if r[3] == "FAIL")
        fh.write("ROWS=%d\nFAILS=%d\nRESUME_CHECK_R3=%s\n" % (len(rows), fails, "PASS" if fails == 0 else "FAIL"))
    print("resume_check_r8m2a2_R3: rows=%d fails=%d" % (len(rows), sum(1 for r in rows if r[3] == "FAIL")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
