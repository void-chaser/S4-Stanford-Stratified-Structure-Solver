#!/usr/bin/env python3
# posctrl_m1c_r8m1c2.py -- P05-S4 R8 M1c2 positive control for the F2 comparison (brief section 6).
# Copies the R8 F2 result tables into $EV/tmp/posctrl/ (shutil, copies only), then:
#   copy A: one gdb_rc2 changed in STATE_R6c_pass1.tsv  -> compare must report DIFFS=1 (detect)
#   copy B: unchanged                                   -> compare must report DIFFS=0 (no false alarm)
# Writes $EV/POSCTRL_M1C_R8_M1c2.txt.  Originals in $EV/m1c_F2 are never modified.
# Usage: python3 -I -B posctrl_m1c_r8m1c2.py
import os, shutil, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c2")
SRC = os.path.join(EV, "m1c_F2")
PC = os.path.join(EV, "tmp", "posctrl")
os.makedirs(PC, exist_ok=True)
OUT = os.path.join(EV, "POSCTRL_M1C_R8_M1c2.txt")
COMPARE = os.path.join(REPO, "testing", "d003", "stage_s4", "compare_m1c_f2_r8m1c2.py")

FILES = ["STATE_R6c_pass1.tsv", "STATE_R6c_pass2.tsv", "STATE_SEAM_R6c_pass1.tsv",
         "STATE_SEAM_R6c_pass2.tsv", "RESULTS_R6c_STATE.tsv", "RESULTS_R6c_SEAM.tsv"]

if os.path.exists(OUT):
    print("REFUSED exists (U17): %s" % OUT)
    sys.exit(2)

A = os.path.join(PC, "copyA_changed")
B = os.path.join(PC, "copyB_unchanged")
for d in (A, B):
    if os.path.exists(d):
        print("REFUSED exists (U17): %s" % d)
        sys.exit(2)
    os.makedirs(d)
    for f in FILES:
        shutil.copyfile(os.path.join(SRC, f), os.path.join(d, f))

# copy A: flip one gdb_rc2 value in the first data row of STATE_R6c_pass1.tsv (0 -> 1)
pathA = os.path.join(A, "STATE_R6c_pass1.tsv")
with open(pathA, encoding="utf-8") as fh:
    lines = fh.read().split("\n")
hdr_idx = None
for i, l in enumerate(lines):
    if l.startswith("kind\t"):
        hdr_idx = i
        break
cols = lines[hdr_idx].split("\t")
c = cols.index("gdb_rc2")
changed = False
for i in range(hdr_idx + 1, len(lines)):
    p = lines[i].split("\t")
    if len(p) == len(cols) and p[0] == "point":
        old = p[c]
        p[c] = "1" if old != "1" else "0"
        lines[i] = "\t".join(p)
        changed = True
        break
if not changed:
    print("POSCTRL_BUILD_FAIL no point row to change")
    sys.exit(1)
with open(pathA, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))

rel_A = os.path.relpath(A, EV)
rel_B = os.path.relpath(B, EV)
resA = subprocess.run([sys.executable, "-I", "-B", COMPARE, rel_A, "POSCTRL_CMP_A_R8_M1c2.tsv"],
                      capture_output=True, text=True)
resB = subprocess.run([sys.executable, "-I", "-B", COMPARE, rel_B, "POSCTRL_CMP_B_R8_M1c2.tsv"],
                      capture_output=True, text=True)
outA = (resA.stdout or "").strip()
outB = (resB.stdout or "").strip()
# Detection criterion: copy A must produce at least one difference (DIFFS>0). The brief's literal
# "DIFFS=1" assumed one difference per changed value, but one changed gdb_rc2 also breaks the
# pass1==pass2 check for the same point, so the actual count is recorded as found, not forced.
def parse_diffs(s):
    for tok in s.split():
        if tok.startswith("DIFFS="):
            try:
                return int(tok.split("=", 1)[1])
            except ValueError:
                return None
    return None
dA = parse_diffs(outA)
detected = dA is not None and dA > 0
clean = outB == "DIFFS=0 GDB_DIVERGENT=0"
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("# POSCTRL_M1C_R8_M1c2 -- positive control for compare_m1c_f2_r8m1c2.py\n")
    fh.write("copyA_changed: one gdb_rc2 flipped in STATE_R6c_pass1.tsv (first point row)\n")
    fh.write("copyA_result: %s rc=%s\n" % (outA, resA.returncode))
    fh.write("copyA_detected_criterion: DIFFS>0 (brief literal DIFFS=1 not forced; see report)\n")
    fh.write("copyA_detected: %s (DIFFS=%s)\n" % (detected, dA))
    fh.write("copyB_unchanged_result: %s rc=%s\n" % (outB, resB.returncode))
    fh.write("copyB_expected: DIFFS=0 GDB_DIVERGENT=0\n")
    fh.write("copyB_clean: %s\n" % clean)
    fh.write("POSCTRL=%s\n" % ("PASS" if (detected and clean) else "FAIL"))
print("POSCTRL A=%s B=%s -> %s" % (outA, outB, "PASS" if (detected and clean) else "FAIL"))
sys.exit(0 if (detected and clean) else 1)
