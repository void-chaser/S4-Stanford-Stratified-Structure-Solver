#!/usr/bin/env python3
# copy_registries_r8m1c2.py -- copies the small R8 M1c2 tables into checkpoints/p05/registries/s4r8/M1c/r8m1c2/,
# writes SHA256SUMS.txt there, and verifies every copy's sha256 against its original (brief section 8.1).
# The F2 state/seam tables and summaries are copied with the M1C_F2_ prefix; gdb logs and dumps are not copied.
# GATE_R8_M1c2_END.txt is NOT copied here (it does not exist until the end gate runs); see the report.
# Usage: python3 -I -B copy_registries_r8m1c2.py
import hashlib, os, shutil, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c2")
DST = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c2")

if os.path.exists(DST):
    print("REFUSED exists (U17): %s" % DST)
    sys.exit(2)
os.makedirs(DST)

PLAIN = [
    "PREREG_M1C_FACTS_R8_M1c2.tsv",
    "PREREG_M1C_FACTS_RECORD_R8_M1c2.txt",
    "R7_F2_FACT_DIST_R8_M1c2.tsv",
    "R7_F2_FACT_DIST_R8_M1c2_R2.tsv",
    "PREFLIGHT_M1C_R8_M1c2.txt",
    "DRIVER_RUN_RECORD_R8_M1c2.tsv",
    "COMPARE_M1C_F2_R8_M1c2.tsv",
    "POSCTRL_M1C_R8_M1c2.txt",
    "GATE_DIFF_R8_M1c2.txt",
    "GATE_R8_M1c2_START.txt",
]
F2_DIR = os.path.join(EV, "m1c_F2")
F2 = [
    "STATE_R6c_pass1.tsv",
    "STATE_R6c_pass2.tsv",
    "STATE_SEAM_R6c_pass1.tsv",
    "STATE_SEAM_R6c_pass2.tsv",
    "RESULTS_R6c_STATE.tsv",
    "RESULTS_R6c_SEAM.tsv",
    "STATE_SUMMARY_R6c.txt",
    "STATE_SUMMARY_R6c_SEAM.txt",
]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


pairs = []
for f in PLAIN:
    pairs.append((os.path.join(EV, f), f))
for f in F2:
    pairs.append((os.path.join(F2_DIR, f), "M1C_F2_" + f))

bad = []
sums = []
for src, name in pairs:
    if not os.path.isfile(src):
        bad.append("missing source: %s" % src)
        continue
    dst = os.path.join(DST, name)
    shutil.copyfile(src, dst)
    s1, s2 = sha256_file(src), sha256_file(dst)
    if s1 != s2:
        bad.append("copy sha256 mismatch: %s" % name)
    sums.append((s2, name))

with open(os.path.join(DST, "SHA256SUMS.txt"), "w", encoding="utf-8") as fh:
    for s, n in sorted(sums, key=lambda x: x[1]):
        fh.write("%s  %s\n" % (s, n))

# verify SHA256SUMS against the copies (every listed file, and the listed set equals the directory set)
listed = {}
with open(os.path.join(DST, "SHA256SUMS.txt"), encoding="utf-8") as fh:
    for line in fh:
        s, n = line.rstrip("\n").split("  ", 1)
        listed[n] = s
dir_names = sorted(n for n in os.listdir(DST) if n != "SHA256SUMS.txt")
if sorted(listed) != dir_names:
    bad.append("SHA256SUMS list differs from directory")
for n, s in listed.items():
    if sha256_file(os.path.join(DST, n)) != s:
        bad.append("SHA256SUMS mismatch: %s" % n)

print("COPIED=%d" % len(sums))
print("BAD=%d" % len(bad))
for b in bad:
    print("BAD\t%s" % b)
sys.exit(1 if bad else 0)
