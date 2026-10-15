#!/usr/bin/env python3
# apparatus_manifest_r8m2a2.py -- P05-S4 R8 M2a2 CONT1 section 3: apparatus manifest.
# For every testing/d003/stage_s4/*r8m2a2* file: path, sha256, role, the BUILD rows that use it (matched by source sha256,
# not by name), and the file that supersedes it.  Asserts that each prereg driver has exactly one ACTIVE source combination.
# Output: $EV/APPARATUS_MANIFEST_R8_M2a2.tsv
import glob
import hashlib
import os
import re
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
ST4 = os.path.join(REPO, "testing", "d003", "stage_s4")
OUT = os.path.join(EV, "APPARATUS_MANIFEST_R8_M2a2_R2.tsv")  # R2: roles corrected (ACTIVE_SOURCE_UNUSED of superseded families; harness rows); the first manifest is kept, SUPERSEDED
BUILD_TABLES = [os.path.join(EV, "BUILD_R8_M2a2_R3.tsv"), os.path.join(EV, "BUILD_OBJECTS_R8_M2a2_R3.tsv")]
PREREG_DRIVERS = ["init-F3-dbg", "polyinj-F3-dbg", "dual-F3-dbg", "layers-F3-dbg", "layers-dual-F3-dbg", "nan-F3",
                  "r6bstate-B-dbg", "init-F3-san", "polyinj-F3-san", "r6bstate-F3-san", "seamF-F3-san", "fmmret-F3-san"]


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def role_of(name):
    """Role from the file name; ACTIVE is then confirmed by the BUILD usage (see below)."""
    if "SUPERSEDED" in name:
        return "SUPERSEDED"
    if "DRAFT" in name:
        return "DRAFT"
    if name.endswith((".sh", ".py", ".gdb")):
        return "ACTIVE_SCRIPT"
    if name.endswith((".cpp", ".c", ".inc", ".h")) or name.endswith(".cpp.txt"):
        return "ACTIVE_SOURCE"
    return "INCLUDE"


def superseded_by(name, all_names):
    """The later version of the same stem, if any (e.g. *_R2 supersedes the base name)."""
    base = re.sub(r"(_SUPERSEDED|_DRAFT_SUPERSEDED|_GEN\d_SUPERSEDED|_R\d)?(\.\w+)?(\.txt)?$", "", name)
    cands = [n for n in all_names if n != name and n.startswith(base) and n != base]
    return ";".join(sorted(cands)[:3]) or "-"


def main():
    if os.path.exists(OUT):
        print("apparatus_manifest_r8m2a2: REFUSED exists (U17)")
        return 2
    files = sorted(glob.glob(os.path.join(ST4, "*r8m2a2*")))
    names = [os.path.basename(f) for f in files]
    src_sha = {}
    for f in files:
        src_sha.setdefault(sha256_file(f), []).append(os.path.basename(f))
    build_text = ""
    for t in BUILD_TABLES:
        with open(t, encoding="utf-8") as fh:
            build_text += fh.read()
    rows = []
    for f in files:
        name = os.path.basename(f)
        digest = sha256_file(f)
        role = role_of(name)
        used = []
        for bt in build_text.split("\n"):
            if digest in bt and not bt.startswith("#"):
                used.append(bt.split("\t")[0])
        related = superseded_by(name, names)
        # a source that no BUILD row uses, but that has a later version of the same family, is SUPERSEDED.
        # The dual harness (dual_harness_r8m2a2*.cpp, dual_stubs_r8m2a2.cpp) is built by its own script, not by the
        # BUILD tables; its evidence is DUAL_HARNESS_R8_M2a2.tsv and HARNESS_NM_R8_M2a2.tsv.
        if name.startswith("dual_harness_r8m2a2") or name.startswith("dual_stubs_r8m2a2"):
            if role in ("ACTIVE_SOURCE", "ACTIVE_SOURCE_UNUSED"):
                role = "ACTIVE_HARNESS"
                used = ["DUAL_HARNESS_R8_M2a2.tsv"]
        elif role in ("ACTIVE_SOURCE", "ACTIVE_SOURCE_UNUSED") and not used:
            if re.search(r"_R\d", related):
                role = "SUPERSEDED_BY_LATER_VERSION"
            else:
                role = "ACTIVE_SOURCE_UNUSED"
        rows.append([os.path.relpath(f, REPO), digest, role, ";".join(sorted(set(used))) or "-", related])
    # assertion: each prereg driver name appears in BUILD_FINAL with exactly one source combination (drv/inj sha pair)
    all_one = True
    detail = []
    with open(os.path.join(EV, "BUILD_R8_M2a2_R3.tsv"), encoding="utf-8") as fh:
        build_rows = [l.rstrip("\n").split("\t") for l in fh if l.strip() and not l.startswith("#")]
    for d in PREREG_DRIVERS:
        combos = set()
        for br in build_rows:
            if br and br[0] == d:
                combos.add(br[3])     # src_sha256 column holds the drv/inj combination
        n = len(combos)
        detail.append((d, n))
        if n != 1:
            all_one = False
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# APPARATUS_MANIFEST_R8_M2a2 -- P05-S4 R8 M2a2 CONT1 section 3\n")
        fh.write("path\tsha256\trole\tbuild_rows_using_this_source_sha\tsuperseded_by_or_related\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
        for d, n in detail:
            fh.write("# PREREG_DRIVER %s SOURCE_COMBINATIONS=%d\n" % (d, n))
        fh.write("# ONE_ACTIVE_COMBINATION_PER_PREREG_DRIVER=%s\n" % ("PASS" if all_one else "FAIL"))
        fh.write("# FILES=%d\n" % len(rows))
    print("apparatus_manifest_r8m2a2: files=%d one_combination=%s" % (len(rows), "PASS" if all_one else "FAIL"))
    return 0 if all_one else 3


if __name__ == "__main__":
    sys.exit(main())
