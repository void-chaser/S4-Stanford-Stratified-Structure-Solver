#!/usr/bin/env python3
# name_map_r8m1c4.py -- P05-S4 R8 M1c4 registry name map (brief 4.5, U226). New file.
# Output: $EV/REGISTRY_NAME_MAP_R8_M1c3.tsv
#   part 1: each file of registries/s4r8/M1c/r8m1c3 (27 files): name, sha256, the m1c3 evidence file(s) with the
#           same sha256 (or NONE), the sha256 of the same-named evidence file (or NONE), equal flag.
#   part 2: every file in the m1c3 evidence directory whose name carries _R2 or _R3, and whether a copy exists in
#           registries/s4r8/M1c/r8m1c3 (by name; by content).
# Read only: the evidence m1c3 and the registries; writes only the output above.
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
EV3 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
R3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c3")
OUT = os.path.join(EV, "REGISTRY_NAME_MAP_R8_M1c3.tsv")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_files(root):
    out = []
    for dp, dns, fns in os.walk(root):
        # the evidence m1c3 subtrees (dump/, state/, tmp/) are large; the name map only needs the top level
        # and the m1c_F3 tree top level (the r8m1c3 registries are flat)
        for f in fns:
            full = os.path.join(dp, f)
            out.append(os.path.relpath(full, root))
    return sorted(out)


def top_level_files(root):
    return sorted(f for f in os.listdir(root) if os.path.isfile(os.path.join(root, f)))


reg_files = top_level_files(R3)
# The brief (section 4.5) says 27 files; the directory holds 29 top-level files (the list is the directory itself,
# so it covers every file; the discrepancy is recorded in the report, not hidden). Expected count recorded here.
EXPECTED_REG_FILES = 29
if len(reg_files) != EXPECTED_REG_FILES:
    print("FAIL registries r8m1c3 file count %d != %d" % (len(reg_files), EXPECTED_REG_FILES))
    sys.exit(1)

ev_top = top_level_files(EV3)
ev_sha = {f: sha(os.path.join(EV3, f)) for f in ev_top}
ev_by_sha = {}
for f, h in ev_sha.items():
    ev_by_sha.setdefault(h, []).append(f)

lines = []
lines.append("# REGISTRY_NAME_MAP_R8_M1c3 -- registries r8m1c3 names vs m1c3 evidence names (U226). Written by name_map_r8m1c4.py.")
lines.append("part\tregistry_file\tregistry_sha256\tevidence_same_content_names\tevidence_same_name_sha256\tsame_name_equal")
for f in reg_files:
    rsh = sha(os.path.join(R3, f))
    same_content = ";".join(sorted(ev_by_sha.get(rsh, []))) or "NONE"
    esh = ev_sha.get(f, "NONE")
    eq = "YES" if esh == rsh else ("NONE" if esh == "NONE" else "NO")
    lines.append("1\t%s\t%s\t%s\t%s\t%s" % (f, rsh, same_content, esh, eq))

lines.append("part\tevidence_file\tevidence_sha256\tregistry_copy_by_name\tregistry_copy_by_content")
r2r3 = [f for f in ev_top if ("_R2" in f or "_R3" in f)]
reg_sha = {f: sha(os.path.join(R3, f)) for f in reg_files}
reg_by_sha = {}
for f, h in reg_sha.items():
    reg_by_sha.setdefault(h, []).append(f)
for f in r2r3:
    h = ev_sha[f]
    by_name = "YES" if f in reg_sha else "NO"
    by_content = ";".join(sorted(reg_by_sha.get(h, []))) or "NONE"
    lines.append("2\t%s\t%s\t%s\t%s" % (f, h, by_name, by_content))
lines.append("COUNT\tregistry_files\t%d" % len(reg_files))
lines.append("COUNT\tevidence_top_files\t%d" % len(ev_top))
lines.append("COUNT\tevidence_R2_R3_files\t%d" % len(r2r3))

if os.path.exists(OUT):
    print("REFUSED exists (U17): %s" % OUT)
    sys.exit(2)
with open(OUT, "x", encoding="utf-8") as fh:
    fh.write("\n".join(lines) + "\n")
print("NAME_MAP rows=%d registry=%d evidence_R2R3=%d" % (len(lines), len(reg_files), len(r2r3)))
