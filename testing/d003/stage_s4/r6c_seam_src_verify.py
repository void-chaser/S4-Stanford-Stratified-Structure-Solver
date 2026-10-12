#!/usr/bin/env python3
# r6c_seam_src_verify.py -- P05-S4 R6c-2 source check before the seam debug rebuild (new file; read-only).
#
# Checks that the R4 seam export trees used for the 25 seam points are the same sources as recorded in R4:
#   (1) every file of seam/F-seamF and seam/F-fmmret listed in the R4 manifest (p05-s4r4/SHA256SUMS.txt) has the recorded
#       sha256 (computed here);
#   (2) for the files that differ from the frozen tree F (1c11905:S4), the set of differing files equals the set named by
#       SEAMDIFF_R4.tsv (seamF: 7 files, fmmret-F: 1 file).  Files not named there must equal F exactly (git hash-object, no -w).
# Writes EVDIR/SEAM_SRC_VERIFY_R6c.tsv (one row per check) and a summary line.  Refuses to overwrite.
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c_seam_src_verify.py EVDIR
import hashlib
import os
import subprocess
import sys

COMMIT_F = "1c11905"
HASH_F_S4 = "4a6f64927a30537740dd0c8f11f9a5aae5e46ba4"
R4_DIR = os.path.join("checkpoints", "p05", "evidence", "p05-s4r4")
TREES = ["seam/F-seamF", "seam/F-fmmret"]
SEAMDIFF_FILES = {
    "seam/F-seamF": {"S4.cpp", "fmm/fmm_FFT.cpp", "fmm/fmm_closed.cpp", "fmm/fmm_PolBasisJones.cpp",
                     "fmm/fmm_PolBasisVL.cpp", "fmm/fmm_kottke.cpp", "fmm/fmm_PolBasisNV.cpp"},
    "seam/F-fmmret": {"S4.cpp"},
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def git(repo, *args):
    return subprocess.run(["git", "-C", repo] + list(args), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          check=False).stdout.decode("utf-8", "replace")


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: r6c_seam_src_verify.py EVDIR")
    ev = argv[1]
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
    out = os.path.join(ev, "SEAM_SRC_VERIFY_R6c.tsv")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists: %s" % out)
    manifest = os.path.join(repo, R4_DIR, "SHA256SUMS.txt")
    entries = {}
    with open(manifest, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            sha, name = line.split(None, 1)
            entries[name.strip()] = sha
    rows = []
    n_ok = n_bad = 0
    for tree in TREES:
        prefix = tree + "/"
        for name in sorted(k for k in entries if k.startswith(prefix)):
            p = os.path.join(repo, R4_DIR, name)
            got = sha256_file(p) if os.path.isfile(p) else "MISSING"
            ok = (got == entries[name])
            n_ok += ok
            n_bad += (not ok)
            rows.append(("manifest", tree, name[len(prefix):], entries[name], got, "OK" if ok else "MISMATCH"))
    # (2) differing files versus F: git hash-object of each file in the seam tree vs the F blob at the same path
    for tree in TREES:
        # the export root is the repository root of the commit; the library source is its S4/ directory
        base = os.path.join(repo, R4_DIR, tree, "S4")
        if not os.path.isdir(base):
            raise SystemExit("REFUSED: S4 directory missing under %s" % tree)
        listing = git(repo, "ls-tree", "-r", "--full-tree", COMMIT_F, "S4")
        f_blobs = {}
        for ln in listing.splitlines():
            meta, path = ln.split("\t", 1)
            _, _, sha = meta.split()
            f_blobs[path[len("S4/"):]] = sha
        differing = set()
        for dirpath, _, files in os.walk(base):
            for fn in files:
                full = os.path.join(dirpath, fn)
                rel = os.path.relpath(full, base).replace(os.sep, "/")
                if rel not in f_blobs:
                    continue
                got = subprocess.run(["git", "hash-object", "--", full], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                     check=False).stdout.decode().strip()
                if got != f_blobs[rel]:
                    differing.add(rel)
        expect = SEAMDIFF_FILES[tree]
        same = (differing == expect)
        rows.append(("diff_vs_F", tree, "differing files: " + ",".join(sorted(differing)),
                     "expect: " + ",".join(sorted(expect)), "equal" if same else "NOT-EQUAL",
                     "OK" if same else "MISMATCH"))
        if not same:
            n_bad += 1
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# SEAM_SRC_VERIFY_R6c.tsv -- R6c-2 source check of the seam export trees (read-only).\n")
        fh.write("kind\ttree\tfile\texpected\tobserved\tmatch\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
        fh.write("# summary: manifest_ok=%d bad=%d\n" % (n_ok, n_bad))
    print("manifest_ok=%d bad=%d -> %s" % (n_ok, n_bad, out))
    return 0 if n_bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
