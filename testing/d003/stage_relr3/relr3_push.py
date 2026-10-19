#!/usr/bin/env python3
# relr3_push.py -- P05 delivery round REL-R3: create the archive branch and push exactly the four refs
# authorised by U393, in order (a)->(d), each exactly once (task brief section 5 steps 1-2).
# Every push output is captured with stderr merged into stdout (no 2>/dev/null); after each push a
# read-only git ls-remote is recorded immediately.  On any refusal, timeout or non-fast-forward the
# script stops and does NOT retry and does NOT add any force option.  Only these .git writes happen:
# the local archive branch creation (U394) and the push-updated refs/remotes/origin/* (U394).
import os, re, sys, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r3")
TAB = chr(9)
NL = chr(10)
BASE = "4607e969ba138f8bcaffa4fba6340dd3b2e1f25b"
F4 = "589e15eb11fcb04e031b524f25a443e7921946cf"
PROD_HEAD = "8e4c01491b6edec9eb4eaa617265ce9ca53bd548"
ARCHIVE_HEAD = BASE
TAG1, TAG2 = "p05-signed-20261019", "p05-rel-r1-20261019"
TAG1_OBJ = "ef925cdea019a7cdf00acb66bc5b59d55f00d868"
TAG2_OBJ = "b42c4c16298ce644f39c3c33ae6c26ef18820a96"
PRODUCT_BRANCH = "p05/d003-fft-error-propagation"
ARCHIVE_BRANCH = "archive/p05-d003-full-20261019"


def run(args, timeout=300):
    return subprocess.run(args, cwd=REPO, capture_output=True, text=True, timeout=timeout)


def run_merged(args, timeout=300):
    return subprocess.run(args, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, timeout=timeout)


def git(args):
    p = run(["git"] + args)
    if p.returncode != 0:
        return None
    return p.stdout.strip()


def clip(text, head=6, tail=6):
    lines = text.rstrip(NL).splitlines()
    if len(lines) <= head + tail:
        return " || ".join(l.replace(TAB, " ") for l in lines)
    return " || ".join([l.replace(TAB, " ") for l in lines[:head]] + ["..."] +
                       [l.replace(TAB, " ") for l in lines[-tail:]])


def read_before():
    path = os.path.join(EV, "REMOTE_BEFORE_RELR3.tsv")
    rows = {}
    header = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if header is None:
            header = f
            continue
        if len(f) == len(header):
            d = dict(zip(header, f))
            rows[d["ref"]] = d["sha"]
    return rows


def read_prereg_sha():
    path = os.path.join(EV, "PREREG_RELR3.tsv.sha256.txt")
    for line in open(path, encoding="utf-8"):
        f = line.rstrip(NL).split(TAB)
        if len(f) >= 2 and f[0] == "PREREG_RELR3.tsv":
            return f[1]
    return None


def sha_f(p):
    import hashlib
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def prereqs():
    bad = []
    if git(["rev-parse", "HEAD"]) != BASE:
        bad.append("HEAD != 4607e96")
    if git(["rev-parse", "HEAD:S4"]) != F4:
        bad.append("HEAD:S4 != F4")
    if git(["show-ref", "--verify", "--quiet", "refs/heads/" + ARCHIVE_BRANCH]) is not None:
        bad.append("local archive branch already exists")
    st = run(["git", "status", "--porcelain=v1", "-uall"]).stdout
    for line in st.splitlines():
        if not line.strip():
            continue
        p = line[3:]
        if " -> " in p:
            p = p.split(" -> ")[-1].strip()
        if not (p.startswith("checkpoints/p05/") or p.startswith("testing/d003/stage_relr3/")):
            bad.append("unexpected working-tree path: " + p)
    if git(["rev-parse", "refs/heads/" + PRODUCT_BRANCH]) != PROD_HEAD:
        bad.append("product branch ref changed")
    if git(["rev-parse", TAG1]) != TAG1_OBJ or git(["rev-parse", TAG2]) != TAG2_OBJ:
        bad.append("tag object sha changed")
    if git(["rev-parse", TAG1 + "^{commit}"]) != "3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505":
        bad.append("tag1 peel changed")
    if git(["rev-parse", TAG2 + "^{commit}"]) != "c88bf30954a356e1cbdd49cf7a53218778c0ae3e":
        bad.append("tag2 peel changed")
    pf = os.path.join(EV, "PREREG_RELR3.tsv")
    if not os.path.isfile(pf):
        bad.append("PREREG_RELR3.tsv missing")
    else:
        rec = read_prereg_sha()
        if rec != sha_f(pf):
            bad.append("PREREG sha256 record mismatch")
    before = read_before()
    p = run(["git", "ls-remote", "origin"], timeout=120)
    if p.returncode != 0:
        bad.append("git ls-remote origin failed")
    else:
        refs = dict((l.split(TAB)[1], l.split(TAB)[0]) for l in p.stdout.splitlines() if len(l.split(TAB)) == 2)
        for r in ("refs/heads/" + PRODUCT_BRANCH, "refs/heads/" + ARCHIVE_BRANCH,
                  "refs/tags/" + TAG1, "refs/tags/" + TAG2):
            if r in refs:
                bad.append("remote already has " + r)
        if refs.get("refs/heads/master") != "5b72793051eb705f0e9b2e5398e1a5f0484da0cb":
            bad.append("remote master changed since REL-R2")
        for r, s in before.items():
            if r == "HEAD" or r.startswith("refs/pull/"):
                continue
            if refs.get(r) != s:
                bad.append("remote ref changed since the round opening: " + r)
    return bad


def main():
    utc0 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if "--snapshot-only" in sys.argv[1:]:
        return write_after()
    bad = prereqs()
    rows = []
    if bad:
        rows.append({"action": "HARD_STOP_PREREQ", "seq": "", "order_spec": "", "ref": "",
                     "command": "", "rc": "", "local_sha": "", "remote_sha": "", "match": "NO",
                     "output": clip("; ".join(bad))})
        write_log(rows, utc0)
        print("HARD_STOP prerequisites failed: " + "; ".join(bad))
        return 2

    # ---- step 1: create the local archive branch (U394; no -f, stop if it exists)
    p = run_merged(["git", "branch", ARCHIVE_BRANCH, BASE])
    local = git(["rev-parse", "refs/heads/" + ARCHIVE_BRANCH])
    s4 = git(["rev-parse", "refs/heads/" + ARCHIVE_BRANCH + ":S4"])
    ok = (p.returncode == 0 and local == ARCHIVE_HEAD and s4 == F4)
    rows.append({"action": "branch_create", "seq": "0", "order_spec": "", "ref": "refs/heads/" + ARCHIVE_BRANCH,
                 "command": "git branch " + ARCHIVE_BRANCH + " " + BASE,
                 "rc": str(p.returncode), "local_sha": local or "", "remote_sha": "", "match": "YES" if ok else "NO",
                 "output": clip(p.stdout)})
    if not ok:
        write_log(rows, utc0)
        print("HARD_STOP archive branch creation failed")
        return 2
    print("archive branch created: " + local + " S4=" + s4)

    # ---- step 2: push (a)->(d), each once
    pushes = [
        ("(a)", "refs/heads/" + PRODUCT_BRANCH, PRODUCT_BRANCH + ":refs/heads/" + PRODUCT_BRANCH,
         ["git", "push", "origin", "refs/heads/" + PRODUCT_BRANCH + ":refs/heads/" + PRODUCT_BRANCH], PROD_HEAD),
        ("(b)", "refs/heads/" + ARCHIVE_BRANCH, ARCHIVE_BRANCH + ":refs/heads/" + ARCHIVE_BRANCH,
         ["git", "push", "origin", "refs/heads/" + ARCHIVE_BRANCH + ":refs/heads/" + ARCHIVE_BRANCH], ARCHIVE_HEAD),
        ("(c)", "refs/tags/" + TAG1, "refs/tags/" + TAG1,
         ["git", "push", "origin", "refs/tags/" + TAG1], TAG1_OBJ),
        ("(d)", "refs/tags/" + TAG2, "refs/tags/" + TAG2,
         ["git", "push", "origin", "refs/tags/" + TAG2], TAG2_OBJ),
    ]
    for seq, ref, _label, argv, expected in pushes:
        p = run_merged(argv)
        rows.append({"action": "push", "seq": seq, "order_spec": seq, "ref": ref,
                     "command": " ".join(argv), "rc": str(p.returncode), "local_sha": expected,
                     "remote_sha": "", "match": "", "output": clip(p.stdout)})
        print("push %s rc=%d" % (seq, p.returncode))
        if p.returncode != 0:
            write_log(rows, utc0)
            print("HARD_STOP push " + seq + " failed; no retry, no force option")
            return 2
        q = run(["git", "ls-remote", "origin", ref], timeout=120)
        remote_shas = [l.split(TAB)[0] for l in q.stdout.splitlines() if len(l.split(TAB)) == 2]
        match = expected in remote_shas
        rows.append({"action": "ls_remote", "seq": seq, "order_spec": seq, "ref": ref,
                     "command": "git ls-remote origin " + ref, "rc": str(q.returncode),
                     "local_sha": expected, "remote_sha": ",".join(remote_shas),
                     "match": "YES" if match else "NO", "output": clip(q.stdout)})
        print("  ls-remote %s -> %s match=%s" % (seq, ",".join(remote_shas), match))
        if q.returncode != 0 or not match:
            write_log(rows, utc0)
            print("HARD_STOP pushed ref sha does not match after push " + seq)
            return 2
    write_log(rows, utc0)
    write_after()
    return 0


def write_after():
    """Read-only full git ls-remote snapshot after the four pushes (peeled ^{} lines excluded)."""
    p = run(["git", "ls-remote", "origin"], timeout=120)
    after = {}
    for l in p.stdout.splitlines():
        f = l.split(TAB)
        if len(f) == 2 and not f[1].endswith("^{}"):
            after[f[1]] = f[0]
    before = read_before()
    lines = ["# REMOTE_AFTER_RELR3.tsv -- read-only git ls-remote origin after the four pushes",
             "# status: NEW = ref absent before / present after; UNCHANGED = same sha; CHANGED = different sha.",
             "# annotated-tag peeled ^{} lines are not refs and are omitted.",
             TAB.join(["ref", "sha", "sha_before", "status"])]
    for r in sorted(after):
        if r not in before:
            status = "NEW"
        elif before[r] == after[r]:
            status = "UNCHANGED"
        else:
            status = "CHANGED"
        lines.append(TAB.join([r, after[r], before.get(r, "absent"), status]))
    for r in sorted(before):
        if r not in after:
            lines.append(TAB.join([r, "absent", before[r], "DISAPPEARED"]))
    lines.append("# written " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))
    open(os.path.join(EV, "REMOTE_AFTER_RELR3.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("post-push remote refs=%d" % len(after))
    return 0


def write_log(rows, utc):
    cols = ["action", "seq", "order_spec", "ref", "command", "rc", "local_sha", "remote_sha", "match", "output"]
    lines = ["# PUSH_LOG_RELR3.tsv -- P05 delivery round REL-R3 push log (U393 refs only, in order, each once)",
             "# stderr is merged into stdout for every command (no 2>/dev/null).  output shows up to 6 head and",
             "# 6 tail lines; the full command line is in the 'command' column.",
             "# started " + utc,
             TAB.join(cols)]
    for r in rows:
        lines.append(TAB.join([r.get(c, "") for c in cols]))
    open(os.path.join(EV, "PUSH_LOG_RELR3.tsv"), "w", encoding="utf-8").write(NL.join(lines) + NL)


if __name__ == "__main__":
    sys.exit(main())
