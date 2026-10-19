#!/usr/bin/env python3
# relr4_sha_sums.py -- $EV/SHA256SUMS.txt covering every non-binary evidence file of the round.
# Excluded (generated/large, sha256 recorded in TREES_RELR4.tsv / BUILD_RELR4.tsv instead):
#   upstream/ (network U clone), trees/ (B, F4, M, M2, M3 clones), run/ (T1/T2 cwds), tmp/, mpi/run/;
#   binaries (.o .a .so .pyc and the fig12 / mpi_probe_relr4 executables).
# Excluded as unstable: SHA256SUMS.txt itself, safe_run.log, GATE_RELR4_pre.txt, GATE_RELR4_end.txt.
import os, sys, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
NL = chr(10)
SKIP_TOP = ("upstream", "trees", "run", "tmp")
BIN_NAMES = ("fig12", "mpi_probe_relr4", "main_lua_no_override.o")
BIN_EXT = (".so", ".a", ".o", ".pyc", ".tar", ".gz", ".zip", ".png", ".bin")
EXEMPT = ("SHA256SUMS.txt", "safe_run.log", "GATE_RELR4_pre.txt", "GATE_RELR4_end.txt",
          "GATE_RELR4_check_start.txt", "GATE_RELR4_pre_firstrun.txt")


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    rows = []
    for root, dirs, files in os.walk(EV):
        relroot = os.path.relpath(root, EV)
        parts = [] if relroot == "." else relroot.split(os.sep)
        if parts and parts[0] in SKIP_TOP:
            dirs[:] = []
            continue
        if parts and parts[0] == "mpi" and len(parts) >= 2:
            dirs[:] = []
            continue
        if parts and parts[0] == "mpi":
            dirs[:] = []  # only the mpi/ level tables/logs are kept; mpi/run/ products are not
        for f in sorted(files):
            full = os.path.join(root, f)
            rel = os.path.relpath(full, EV)
            if rel in EXEMPT or f in BIN_NAMES or f.endswith(BIN_EXT):
                continue
            rows.append((sha_f(full), rel))
    rows.sort(key=lambda r: r[1])
    lines = ["# SHA256SUMS.txt -- P05 delivery round REL-R4 evidence directory",
             "# Covers every non-binary evidence file under checkpoints/p05/evidence/p05-rel-r4/",
             "# (directories skipped entirely: upstream/ trees/ run/ tmp/ mpi/run/; every binary skipped;",
             "#  sha256 of the clones and binaries are recorded in TREES_RELR4.tsv and BUILD_RELR4.tsv).",
             "# Excluded as unstable: SHA256SUMS.txt itself, safe_run.log, GATE_RELR4_pre.txt, GATE_RELR4_end.txt."]
    for a, rel in rows:
        lines.append("%s  %s" % (a, rel))
    lines.append("# ANNOTATION tree facts (S4/ tree hash recomputed from the clone files):")
    tp = os.path.join(EV, "TREES_RELR4.tsv")
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
            lines.append("# ANNOTATION tree=%s commit=%s s4_tree_git=%s match=%s lua=%s" % (
                d.get("tree"), d.get("commit"), d.get("s4_tree_git"), d.get("match"), d.get("lua_count")))
    open(os.path.join(EV, "SHA256SUMS.txt"), "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("EVIDENCE_FILES=%d" % len(rows))
    print("WROTE checkpoints/p05/evidence/p05-rel-r4/SHA256SUMS.txt")
    return 0


if __name__ == "__main__":
    sys.exit(main())