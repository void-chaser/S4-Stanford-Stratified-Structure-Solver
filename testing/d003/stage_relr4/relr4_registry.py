#!/usr/bin/env python3
# relr4_registry.py -- copy the round's small result tables to checkpoints/p05/registries/rel-r4/ and write
# SHA256SUMS.txt there.  Every copy is verified byte-identical (sha256) to its evidence original.
# Called twice: before commit (i) (all files available then) and, with --post-gate, after the formal end
# gate so that GATE_RELR4_end.txt is added and the manifest regenerated (commit (ii)).
import os, sys, hashlib, shutil

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r4")
REG = os.path.join(REPO, "checkpoints/p05/registries/rel-r4")
TAB = chr(9)
NL = chr(10)
MAXB = 1024 * 1024
FILES = ["PREREG_RELR4.tsv", "PREREG_RELR4.tsv.sha256.txt", "TREES_RELR4.tsv", "BUILD_RELR4.tsv",
         "WARN_DIFF_RELR4.txt", "EXPECT_SCAN_RELR4.tsv", "U_PROBE_RELR4.tsv", "U_PY_RELR4.tsv",
         "RESULTS_RELR4.tsv",
         "VERDICT_RELR4.tsv", "SUMMARY_RELR4.txt", "ATTRIB_RELR4.tsv", "MPI_RELR4.tsv", "CAPI_RELR4.tsv",
         "RULINGS_APPEND_RELR4.tsv", "TMP_SNAPSHOT_RELR4_end.tsv", "GATE_RELR4_start.txt"]
OPTIONAL = ["ERRATA_RELR4.txt", "GATE_RELR4_end.txt", "GATE_RELR4_pre.txt"]
# tables that live in evidence subdirectories but belong to the small-table registry
EXTRA = [("mpi/PRECHECK_RELR4.tsv", "PRECHECK_MPI_RELR4.tsv")]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    post_gate = "--post-gate" in sys.argv[1:]
    os.makedirs(REG, exist_ok=True)
    todo = list(FILES)
    if post_gate:
        todo.append("GATE_RELR4_end.txt")
    else:
        todo = [x for x in todo if x != "GATE_RELR4_end.txt"]
    todo += [f for f in OPTIONAL if f != "GATE_RELR4_end.txt" or post_gate]
    seen = set()
    todo = [x for x in todo if not (x in seen or seen.add(x))]
    sums, bad = [], []
    for name in todo:
        src = os.path.join(EV, name)
        if not os.path.isfile(src):
            if name in OPTIONAL or (name == "GATE_RELR4_end.txt" and not post_gate):
                continue
            bad.append(("MISSING_EVIDENCE", name))
            continue
        size = os.path.getsize(src)
        if size > MAXB:
            bad.append(("TOO_LARGE_NOT_COPIED", "%s %d bytes" % (name, size)))
            continue
        dst = os.path.join(REG, name)
        shutil.copyfile(src, dst)
        a, b = sha_f(src), sha_f(dst)
        if a != b:
            bad.append(("SHA_MISMATCH", name))
        sums.append((a, name))
        print("COPY %-40s %d bytes %s %s" % (name, size, a[:16], "OK" if a == b else "MISMATCH"))
    for src_rel, dst_name in EXTRA:
        src = os.path.join(EV, src_rel)
        if not os.path.isfile(src):
            bad.append(("MISSING_EXTRA", src_rel))
            continue
        dst = os.path.join(REG, dst_name)
        shutil.copyfile(src, dst)
        a, b = sha_f(src), sha_f(dst)
        if a != b:
            bad.append(("SHA_MISMATCH", dst_name))
        sums.append((a, dst_name))
        print("COPY %-40s (from %s) %s" % (dst_name, src_rel, "OK" if a == b else "MISMATCH"))
    with open(os.path.join(REG, "SHA256SUMS.txt"), "w", encoding="utf-8") as fh:
        fh.write("# SHA256SUMS.txt -- P05 delivery round REL-R4 registry (copies verified against the evidence originals)" + NL)
        fh.write("# post_gate=%s" % ("yes" if post_gate else "no") + NL)
        for a, name in sorted(sums, key=lambda x: x[1]):
            fh.write("%s  %s" % (a, name) + NL)
    print("REGISTRY_FILES=%d" % len(sums))
    for k, v in bad:
        print("PROBLEM" + TAB + k + TAB + v)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())