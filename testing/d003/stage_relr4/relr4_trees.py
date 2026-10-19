#!/usr/bin/env python3
# relr4_trees.py -- materialise the reference trees of REL-R4 as INDEPENDENT CLONES (task brief section 3;
# REL-R1 lesson: never use 'git archive' of a checkout to stand in for a tree):
#   U  = upstream original master, cloned from https://github.com/victorliu/S4 into $EV/upstream/S4
#        (kept as evidence, not committed; network read-only clone).
#   B  = independent local clone of THIS repository at commit 5b72793, in $EV/trees/B.
#   F4 = independent local clone of THIS repository at commit 3de6d8b, in $EV/trees/F4.
# Each clone is materialised with a single 'git clone' invocation (--revision <commit> for B/F4), so no
# main-repository ref or index is touched.  The S4/ directory of every clone is re-hashed with the git
# tree-object algorithm and compared with 'git rev-parse <commit>:S4' computed in the main repository.
# Writes only under $EV.
import os, sys, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
TMP = os.path.join(EV, "tmp")
TAB = chr(9)
NL = chr(10)
U_CLONE = os.path.join(EV, "upstream", "S4")
U_URL = "https://github.com/victorliu/S4.git"
JOBS = (("U", U_CLONE, "7fd00a231610bff51f5c7de5f723e3956eab7453",
         "06553f72e93aaef1a5c9294f358a7f5afbd42bb1", U_URL),
        ("B", os.path.join(EV, "trees", "B"), "5b72793051eb705f0e9b2e5398e1a5f0484da0cb",
         "1d738e64f9864a475fdb3de34cd3601605df2c64", REPO),
        ("F4", os.path.join(EV, "trees", "F4"), "3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505",
         "589e15eb11fcb04e031b524f25a443e7921946cf", REPO))


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sh(cmd, cwd=None):
    return subprocess.run(cmd, cwd=cwd or REPO, capture_output=True, text=True)


def git_out(args):
    p = sh(["git"] + args)
    if p.returncode != 0:
        raise SystemExit("HARD_STOP git %s rc=%d %s" % (" ".join(args), p.returncode, p.stderr[:300]))
    return p.stdout.strip()


def git_obj_hash(kind, data):
    h = hashlib.sha1()
    h.update(("%s %d" % (kind, len(data))).encode() + b"\x00")
    h.update(data)
    return h.digest()


def git_blob_hash(path):
    h = hashlib.sha1()
    size = os.path.getsize(path)
    h.update(("blob %d" % size).encode() + b"\x00")
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.digest()


def git_tree_hash(path):
    entries = []
    for name in os.listdir(path):
        full = os.path.join(path, name)
        if os.path.islink(full):
            raise SystemExit("HARD_STOP symlink in clone: " + full)
        if os.path.isdir(full):
            entries.append((name + "/", b"40000", name, git_tree_hash(full)))
        else:
            st = os.stat(full)
            mode = b"100755" if (st.st_mode & 0o111) else b"100644"
            entries.append((name, mode, name, git_blob_hash(full)))
    entries.sort(key=lambda e: e[0].encode())
    body = b""
    for _, mode, name, h in entries:
        body += mode + b" " + name.encode() + b"\x00" + h
    return git_obj_hash("tree", body)


def clone_one(name, dst, commit, src):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.isdir(os.path.join(dst, ".git")):
        # remove the in-clone command record left by an earlier attempt of this same script
        stray = os.path.join(dst, "CLONE_COMMAND.txt")
        if os.path.isfile(stray):
            sh(["rm", "-f", stray])
        return "exists"
    cmd = ["git", "clone", "--quiet"]
    if src == REPO:
        cmd += ["--revision", commit]
    cmd += [src, dst]
    t0 = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    p = sh(cmd)
    if p.returncode != 0:
        print("CLONE_FAILED %s rc=%d" % (name, p.returncode))
        print((p.stdout + p.stderr)[-2000:])
        return "FAILED:" + (p.stderr or p.stdout).strip().splitlines()[-1][:200] if (p.stderr or p.stdout).strip() else "FAILED"
    # the clone command record is kept NEXT TO the clone, never inside it, so the clone itself
    # stays a pristine independent checkout (git status --porcelain empty)
    with open(dst + "_CLONE_COMMAND.txt", "w", encoding="utf-8") as fh:
        fh.write("utc=%s" % t0 + NL + "cwd=%s" % REPO + NL + "cmd=" + " ".join(cmd) + NL)
    return "cloned"


def main():
    # remove the throw-away --revision probe clone of the previous step (inside $EV/tmp only)
    probe = os.path.join(TMP, "testclone")
    if os.path.isdir(probe) and os.path.realpath(probe).startswith(os.path.realpath(EV) + os.sep):
        sh(["rm", "-rf", probe])
    rows = ["# TREES_RELR4.tsv -- P05 delivery round REL-R4 reference trees, each an independent clone",
            "# S4 tree hash is recomputed from the clone files with the git tree-object algorithm (sha1) and",
            "# compared with 'git rev-parse <commit>:S4' in the main repository.  U = upstream original master.",
            "# U's clone is evidence only and is not committed; B and F4 are clones of this repository.",
            TAB.join(["tree", "commit", "commit_subject", "clone_dir", "clone_source", "clone_command",
                      "clone_result", "clone_head", "s4_tree_git", "s4_tree_export_recomputed", "match",
                      "head_tree", "main_repo_head_tree", "file_count", "lua_count", "clone_status_clean",
                      "makefile_linux_sha256"])]
    bad = 0
    for name, dst, commit, exp_s4, src in JOBS:
        res = clone_one(name, dst, commit, src)
        if res.startswith("FAILED"):
            print("HARD_STOP clone failed for %s: %s" % (name, res))
            return 2
        head = git_out(["-C", dst, "rev-parse", "HEAD"])
        head_ok = (head == commit)
        s4 = git_out(["-C", dst, "rev-parse", "HEAD:S4"])
        rec = git_tree_hash(os.path.join(dst, "S4")).hex()
        match = "YES" if (rec == exp_s4 == s4) else "NO"
        head_tree = git_out(["-C", dst, "rev-parse", "HEAD^{tree}"])
        main_tree = git_out(["-C", REPO, "rev-parse", commit + "^{tree}"])
        # the clone of this repository must contain exactly the same commit object as the main repository
        if name != "U":
            main_commit = git_out(["-C", REPO, "rev-parse", commit])
            if main_commit != head:
                head_ok = False
        clean = git_out(["-C", dst, "status", "--porcelain"])
        nfiles = sum(len(fs) for _, _, fs in os.walk(dst))
        n_lua = 0
        ex = os.path.join(dst, "examples")
        if os.path.isdir(ex):
            for root, dirs, files in os.walk(ex):
                n_lua += sum(1 for f in files if f.endswith(".lua"))
        mk = os.path.join(dst, "Makefile.Linux")
        if not (head_ok and match == "YES" and clean == "" and head_tree == main_tree and n_lua == 51):
            bad += 1
        subj = git_out(["-C", REPO, "log", "-1", "--format=%s", commit])[:100]
        cmd = "git clone --quiet" + (" --revision " + commit if src == REPO else "") + " " + src + " " + dst
        rows.append(TAB.join([name, commit, subj, os.path.relpath(dst, REPO), src, cmd, res, head, s4, rec,
                              match, head_tree, main_tree, str(nfiles), str(n_lua),
                              "YES" if clean == "" else "NO:" + clean[:80],
                              sha_f(mk) if os.path.isfile(mk) else "MISSING"]))
        print("TREE %-2s clone=%s head=%s s4_git=%s recomputed=%s match=%s files=%d lua=%d clean=%s tree_eq_main=%s"
              % (name, res, head[:10], s4[:10], rec[:10], match, nfiles, n_lua, "yes" if clean == "" else "NO",
                 "yes" if head_tree == main_tree else "NO"))
    out = os.path.join(EV, "TREES_RELR4.tsv")
    if not os.path.realpath(out).startswith(os.path.join(REPO, "checkpoints/p05") + os.sep):
        raise SystemExit("WRITE_OUTSIDE " + out)
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())