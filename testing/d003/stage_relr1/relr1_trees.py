#!/usr/bin/env python3
# relr1_trees.py -- export the three reference trees of REL-R1 with git archive and verify each
# exported S4/ directory against the git tree object of the same commit, by recomputing the git
# tree hash (sha1) from the exported files.  Writes only under $EV.
#   U  <- 7fd00a2 (upstream original master, record only)
#   B  <- 5b72793 (origin/master; S4/ tree identical to 37a82e8)
#   F4 <- HEAD    (3de6d8b; S4/ tree 589e15eb..)
import os, sys, subprocess, hashlib, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1")
TREES = os.path.join(EV, "trees")
TAB = chr(9)
NL = chr(10)
JOBS = (("U", "7fd00a231610bff51f5c7de5f723e3956eab7453", "06553f72e93aaef1a5c9294f358a7f5afbd42bb1"),
        ("B", "5b72793051eb705f0e9b2e5398e1a5f0484da0cb", "1d738e64f9864a475fdb3de34cd3601605df2c64"),
        ("F4", "3de6d8bc7a35f036bf5ff6e508f5cdb5ef025505", "589e15eb11fcb04e031b524f25a443e7921946cf"))


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sh(cmd):
    return subprocess.check_output(cmd, text=True, cwd=REPO).strip()


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
            raise SystemExit("HARD_STOP symlink in exported tree: " + full)
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


def main():
    os.makedirs(TREES, exist_ok=True)
    rows = ["# TREES_RELR1.tsv -- P05 delivery round REL-R1 reference trees exported with git archive",
            "# S4 tree hash is recomputed from the exported files with the git tree-object algorithm (sha1)",
            "# and compared with 'git rev-parse <commit>:S4'.  U = upstream original master (record only).",
            TAB.join(["tree", "commit", "commit_subject", "s4_tree_git", "s4_tree_export_recomputed",
                      "match", "export", "file_count", "makefile_sha256", "export_command"])]
    bad = 0
    for name, commit, exp in JOBS:
        got = sh(["git", "rev-parse", commit + ":S4"])
        tdir = os.path.join(TREES, name)
        export_cmd = "git archive %s | tar -x -C %s" % (commit, os.path.relpath(tdir, REPO))
        if os.path.isdir(os.path.join(tdir, "S4")) and os.path.isfile(os.path.join(tdir, "Makefile")):
            export = "exists"
        else:
            os.makedirs(tdir, exist_ok=True)
            p = subprocess.run("git archive " + commit + " | tar -x -C " + tdir, shell=True,
                               cwd=REPO, capture_output=True, text=True)
            if p.returncode != 0:
                print("HARD_STOP export failed %s rc=%d %s" % (name, p.returncode, p.stderr[:300]))
                return 2
            with open(os.path.join(tdir, "EXPORT_COMMAND.txt"), "w", encoding="utf-8") as fh:
                fh.write(export_cmd + NL)
            export = "ok"
        rec = git_tree_hash(os.path.join(tdir, "S4")).hex()
        match = "YES" if rec == exp else "NO"
        if match != "YES" or got != exp:
            bad += 1
        n = sum(len(fs) for _, _, fs in os.walk(tdir))
        subj = sh(["git", "log", "-1", "--format=%s", commit])[:100]
        rows.append(TAB.join([name, commit, subj, got, rec, match, export, str(n),
                              sha_f(os.path.join(tdir, "Makefile")), export_cmd]))
        print("TREE %s commit=%s files=%d s4_git=%s recomputed=%s match=%s" % (name, commit, n, got, rec, match))
    out = os.path.join(EV, "TREES_RELR1.tsv")
    if not os.path.realpath(out).startswith(os.path.join(REPO, "checkpoints/p05") + os.sep):
        raise SystemExit("WRITE_OUTSIDE " + out)
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("WROTE " + os.path.relpath(out, REPO))
    return bad


if __name__ == "__main__":
    sys.exit(main())
