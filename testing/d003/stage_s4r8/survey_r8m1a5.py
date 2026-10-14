#!/usr/bin/env python3
# survey_r8m1a5.py -- read-only survey of the committed input tables for the CONT3b1 pre-registration (r8m1a5).
# Writes one text summary to the evidence directory; reads only committed tables.  New file.
import csv, os, sys, hashlib

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a5")
REG7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
REG8 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
REG3C2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c2")
REG3C3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c3")

def read_tsv(path):
    rows = []
    with open(path, encoding="utf-8", newline="") as fh:
        lines = [l.rstrip("\n") for l in fh if not l.startswith("#") and l.strip() != ""]
    if not lines:
        return [], []
    header = lines[0].split("\t")
    for l in lines[1:]:
        cells = l.split("\t")
        rows.append(dict(zip(header, cells)))
    return header, rows

def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()

out = []
def w(s):
    out.append(s)

w("# survey_r8m1a5 (read-only).  Input tables and counts for the CONT3b1 pre-registration.")
for name, p in [
    ("REG_M1", os.path.join(REG7, "REGISTRY_S4_PRE_R7_M1.tsv")),
    ("REG_M2", os.path.join(REG7, "REGISTRY_S4_PRE_R7_M2.tsv")),
    ("REG_M2_ADD_v3", os.path.join(REG7, "REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv")),
    ("REG_M2_CTRL_SEAM", os.path.join(REG7, "REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv")),
    ("REG_M3", os.path.join(REG7, "REGISTRY_S4_PRE_R7_M3.tsv")),
    ("REQ_TARGETS_AUDIT3", os.path.join(REG8, "REQUEST_TARGETS_R8_M1a4AUDIT3.tsv")),
    ("CALLSEQ_F2_F3_R2", os.path.join(REG8, "CALLSEQ_F2_F3_R8_M1a4_R2.tsv")),
    ("ADD_MAP_22_RUN2", os.path.join(REG8, "ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN2.tsv")),
    ("DRIVERS_R8_M1a", os.path.join(REG8, "DRIVERS_R8_M1a.tsv")),
    ("DRIVERS_F2_REUSED", os.path.join(REG8, "DRIVERS_R8_M1a_F2_REUSED.tsv")),
    ("K_SOURCE_G5F2", os.path.join(REG8, "K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv")),
    ("REG_S3R4C2_A", os.path.join(REG3C2, "REGISTRY_S3R4C2_A.tsv")),
    ("REG_S3R4C2_C_POLY", os.path.join(REG3C2, "REGISTRY_S3R4C2_C_POLY.tsv")),
    ("REG_S3R4C3_A_CTRL", os.path.join(REG3C3, "REGISTRY_S3R4C3_A_CTRL.tsv")),
    ("REG_S3R4C3_B", os.path.join(REG3C3, "REGISTRY_S3R4C3_B.tsv")),
    ("RESULTS_M1_REJUDGE", os.path.join(REG7, "RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv")),
]:
    if os.path.isfile(p):
        h, r = read_tsv(p)
        w("%s\trows=%d\tsha256=%s\tcols=%s" % (name, len(r), sha(p), ",".join(h)))
    else:
        w("%s\tMISSING\t%s" % (name, p))

# R7 results: counts per group and F2 two-pass agreement
groups = [
    ("M1", "RESULTS_R7_M1_pass1_run2.tsv", "RESULTS_R7_M1_pass2_run2.tsv"),
    ("G1", "RESULTS_R7_G1_pass1_run7.tsv", "RESULTS_R7_G1_pass2_run7.tsv"),
    ("G2a", "RESULTS_R7_G2a_pass1_run7.tsv", "RESULTS_R7_G2a_pass2_run7.tsv"),
    ("G2b", "RESULTS_R7_G2b_pass1_run4.tsv", "RESULTS_R7_G2b_pass2_run4.tsv"),
    ("G2c", "RESULTS_R7_G2c_pass1_run7.tsv", "RESULTS_R7_G2c_pass2_run7.tsv"),
    ("G3", "RESULTS_R7_G3_pass1_run4.tsv", "RESULTS_R7_G3_pass2_run4.tsv"),
    ("G4", "RESULTS_R7_G4_pass1_run4.tsv", "RESULTS_R7_G4_pass2_run4.tsv"),
    ("CTRL_SEAM", "RESULTS_R7_CTRL_SEAM_pass1_run7.tsv", "RESULTS_R7_CTRL_SEAM_pass2_run7.tsv"),
]
for g, a, b in groups:
    _, ra = read_tsv(os.path.join(REG7, a))
    _, rb = read_tsv(os.path.join(REG7, b))
    ida = [x["point_id"] for x in ra]
    idb = [x["point_id"] for x in rb]
    diff_cls = sum(1 for x, y in zip(ra, rb) if x["class"] != y["class"] or x["rc1"] != y["rc1"])
    w("GROUP %s\trows_p1=%d\trows_p2=%d\tsame_order=%s\tclass_or_rc1_diff=%d\tdup_ids_p1=%d" % (
        g, len(ra), len(rb), ida == idb, diff_cls, len(ida) - len(set(ida))))

os.makedirs(EV, exist_ok=True)
dst = os.path.join(EV, "SURVEY_R8_M1a5.txt")
if os.path.exists(dst):
    sys.exit("survey: exists (U17): " + dst)
with open(dst, "w", encoding="utf-8") as fh:
    fh.write("\n".join(out) + "\n")
print("survey_r8m1a5: wrote", dst, "lines", len(out))
