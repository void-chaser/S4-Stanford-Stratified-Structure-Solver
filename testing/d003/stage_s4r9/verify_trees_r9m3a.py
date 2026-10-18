#!/usr/bin/env python3
# verify_trees_r9m3a.py -- verify the exported trees against git (F4 vs HEAD, B/S4 vs 37a82e8:S4).
# usage: python3 -I -B testing/d003/stage_s4r9/verify_trees_r9m3a.py OUT.tsv
import os, sys, subprocess, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a")
TREES = os.path.join(EV, "trees")


def git(*args):
    return subprocess.check_output(["git"] + list(args), cwd=REPO, text=True).strip()


def ls_tree(rev, prefix=""):
    out = {}
    for line in git("ls-tree", "-r", rev, prefix and "--", prefix).splitlines() if prefix else git("ls-tree", "-r", rev).splitlines():
        meta, path = line.split("\t")
        mode, typ, sha = meta.split()
        out[path] = (mode, sha)
    return out


def blob_sha(path):
    return git("hash-object", path)


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV, "TREES_R9M3A.tsv")
    rows = []
    # F4 tree vs HEAD
    head = ls_tree("HEAD")
    f4 = os.path.join(TREES, "F4")
    f4_files = []
    for root, dirs, files in os.walk(f4):
        dirs[:] = [d for d in dirs if d != ".git"]
        for f in files:
            fp = os.path.join(root, f)
            f4_files.append(os.path.relpath(fp, f4))
    f4_set = set(f4_files)
    head_set = set(head.keys())
    missing = sorted(head_set - f4_set)
    extra = sorted(f4_set - head_set)
    # blob comparison for the S4 subtree only (the full tree contains large third-party sources;
    # the path set plus the S4 blob set is the agreed identity check for this round)
    s4_head = {p: v for p, v in head.items() if p.startswith("S4/")}
    s4_bad = []
    for p, (mode, sha) in sorted(s4_head.items()):
        fp = os.path.join(f4, p)
        if not os.path.isfile(fp):
            s4_bad.append(p + ":missing")
        elif blob_sha(fp) != sha:
            s4_bad.append(p + ":blob")
    rows.append(("F4_VS_HEAD", "path_set_equal=%s missing=%d extra=%d" % (not missing and not extra, len(missing), len(extra)),
                 "S4_blobs_ok=%s bad=%d" % (not s4_bad, len(s4_bad))))
    rows.append(("F4_FILE_COUNT", str(len(f4_files)), str(len(head_set))))

    # B tree: S4 from 37a82e8
    b = os.path.join(TREES, "B")
    b_s4_head = ls_tree("37a82e8", "S4")
    b_s4_bad = []
    b_s4_files = []
    for root, dirs, files in os.walk(os.path.join(b, "S4")):
        for f in files:
            b_s4_files.append(os.path.relpath(os.path.join(root, f), b))
    for p, (mode, sha) in sorted(b_s4_head.items()):
        fp = os.path.join(b, p)
        if not os.path.isfile(fp):
            b_s4_bad.append(p + ":missing")
        elif blob_sha(fp) != sha:
            b_s4_bad.append(p + ":blob")
    rows.append(("B_VS_37a82e8_S4", "S4_blobs_ok=%s bad=%d" % (not b_s4_bad, len(b_s4_bad)),
                 "S4_files_in_tree=%d expected=%d" % (len(b_s4_files), len(b_s4_head))))
    extra_b = sorted(set(b_s4_files) - set(b_s4_head.keys()))
    rows.append(("B_S4_EXTRA_FILES", str(len(extra_b)), ",".join(extra_b[:5]) if extra_b else "none"))

    # S4 manifest hashes for both trees (documented in the report)
    for name, base in (("F4", f4), ("B", b)):
        entries = []
        for root, dirs, files in os.walk(os.path.join(base, "S4")):
            for f in files:
                fp = os.path.join(root, f)
                rel = os.path.relpath(fp, base)
                entries.append("%s %s" % (hashlib.sha256(open(fp, "rb").read()).hexdigest(), rel))
        entries.sort()
        man_sha = hashlib.sha256(("\n".join(entries) + "\n").encode()).hexdigest()
        rows.append((name + "_S4_MANIFEST_SHA256", man_sha, "files=%d" % len(entries)))

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("# TREES_R9M3A.tsv -- identity check of the two exported trees (S-C step 1)\n")
        fh.write("check\tresult\tdetail\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    for r in rows:
        print("%s\t%s\t%s" % r)
    print("WROTE " + out_path)
    ok = (not missing) and (not extra) and (not s4_bad) and (not b_s4_bad) and (not extra_b)
    print("TREES_OK=%s" % ok)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
