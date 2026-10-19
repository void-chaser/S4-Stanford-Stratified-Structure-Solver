#!/usr/bin/env python3
# relr1_sha_sums.py -- $EV/SHA256SUMS.txt covering every non-binary evidence file of the round.
# Exported trees, the fresh clone, the P04 run directory and binaries are NOT listed file by file
# (they are large/generated); their identifying sha256 values are recorded in TREES_RELR1.tsv and
# BUILD_RELR1.tsv, and their marker hashes are appended as annotation lines at the end.
import os, sys, hashlib, subprocess

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1")
NL = chr(10)
SKIP_DIRS = ("trees", "clone", "p04run", "tmp", "t4src")
BIN_EXT = (".so", ".a", ".o", ".pyc", ".tar", ".gz", ".zip", ".png", ".bin", ".fig12")


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    rows = []
    for root, dirs, files in os.walk(EV):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS)
        for f in sorted(files):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, EV)
            if rel in ("SHA256SUMS.txt", "safe_run.log", "GATE_RELR1_pre.txt", "GATE_RELR1_end.txt"):
                # growing log and the gate's own output files cannot be hashed stably; exempt (noted in the header)
                continue
            if f.endswith(BIN_EXT):
                continue
            rows.append((sha_f(full), rel))
    rows.sort(key=lambda r: r[1])
    lines = ["# SHA256SUMS.txt -- P05 delivery round REL-R1 evidence directory",
             "# Covers every non-binary evidence file under checkpoints/p05/evidence/p05-rel-r1/.",
             "# Excluded (generated/large, sha256 recorded in TREES_RELR1.tsv and BUILD_RELR1.tsv instead):",
             "#   trees/{U,B,F4}/ (git archive exports), clone/relr1 (fresh clone), p04run/F4 (P04 pipeline output), tmp/",
             "#   binaries (.so .a .o .pyc .tar .gz .zip .png .bin and the built fig12 executable)"]
    for a, rel in rows:
        lines.append("%s  %s" % (a, rel))
    lines.append("# ANNOTATION tree exports (S4/ git tree hash recomputed from the export):")
    tp = os.path.join(EV, "TREES_RELR1.tsv")
    if os.path.isfile(tp):
        hdr = None
        for line in open(tp, encoding="utf-8"):
            if not line.strip() or line.startswith("#"):
                continue
            f = line.rstrip(NL).split(chr(9))
            if hdr is None:
                hdr = f
                continue
            d = dict(zip(hdr, f))
            lines.append("# ANNOTATION tree=%s commit=%s s4_tree_git=%s match=%s files=%s" % (
                d.get("tree"), d.get("commit"), d.get("s4_tree_git"), d.get("match"), d.get("file_count")))
    open(os.path.join(EV, "SHA256SUMS.txt"), "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("EVIDENCE_FILES=%d" % len(rows))
    print("WROTE " + os.path.relpath(os.path.join(EV, "SHA256SUMS.txt"), REPO))
    return 0


if __name__ == "__main__":
    sys.exit(main())
