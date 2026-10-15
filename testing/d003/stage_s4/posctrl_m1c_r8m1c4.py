#!/usr/bin/env python3
# posctrl_m1c_r8m1c4.py -- P05-S4 R8 M1c4 positive controls (brief section 4.4, U227, U220 counting rule). New file.
# A  : copy the F3 STATE/RESULTS files of m1c3 into the EV scratch area (tmp/posctrl_A); change gdb_rc2 of one G5 point row in
#      BOTH pass1 and pass2 files; run the formal comparison compare_m1c_f3_r8m1c4.py on the copy.
#      Pass: VS_FROZEN DIFFS>0 and the changed point id appears in a DIFF line.
# A2 : as A, but change gdb_rc2 in pass1 only (checks the pass-to-pass consistency item).
#      Pass: same condition as A.
# B  : copy unchanged into the EV scratch area (tmp/posctrl_B); formal comparison. Pass: DIFFS=0.
# J  : judge positive control: copy the frozen M1c table into the EV scratch area, change one F3 G5 exp_rc1,
#      run verdict_m1c_r8m1c3.py on the copy (override path: it writes only under tmp) -> the changed row must be MISMATCH.
# The shutil copies do not include dump/ or state/ subdirectories. If the formal comparison needs them, the script
# stops and reports (brief 4.4 stop rule 7); this is recorded as POSCTRL=FAIL with reason.
# Output: $EV/POSCTRL_M1C_R8_M1c4.txt, last line POSCTRL=PASS or POSCTRL=FAIL.
# Usage: python3 -I -B testing/d003/stage_s4/posctrl_m1c_r8m1c4.py
import os
import shutil
import subprocess
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
EV3 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
F3SRC = os.path.join(EV3, "m1c_F3")  # read only
STAGE = os.path.join(REPO, "testing", "d003", "stage_s4")
PA = os.path.join(EV, "tmp", "posctrl_A")
PA2 = os.path.join(EV, "tmp", "posctrl_A2")
PB = os.path.join(EV, "tmp", "posctrl_B")
OUT = os.path.join(EV, "POSCTRL_M1C_R8_M1c4.txt")
F3FILES = ["STATE_R6c_pass1.tsv", "STATE_R6c_pass2.tsv", "STATE_SEAM_R6c_pass1.tsv", "STATE_SEAM_R6c_pass2.tsv",
           "RESULTS_R6c_STATE.tsv", "RESULTS_R6c_SEAM.tsv"]
if os.path.exists(OUT):
    raise SystemExit("REFUSED exists (U17): %s" % OUT)

lines = []
counts = {}


def rel(p):
    return os.path.relpath(p, REPO)


def stage_copy(dst):
    if os.path.exists(dst):
        shutil.rmtree(dst)  # tmp scratch area only (not evidence); removes this script's own previous copy
    os.makedirs(dst)
    for f in F3FILES:
        shutil.copyfile(os.path.join(F3SRC, f), os.path.join(dst, f))


def change_gdb_rc2(path, which_point_row=None):
    """Change gdb_rc2 of the first G5 point row (kind 'point', id not starting with 'C-') to a different value.
    Returns (changed id, old value, new value)."""
    with open(path, encoding="utf-8") as fh:
        raw = fh.readlines()
    hdr = None
    for i, l in enumerate(raw):
        if l.startswith("kind\t"):
            hdr = i
            break
    head = raw[hdr].rstrip("\n").split("\t")
    col = head.index("gdb_rc2")
    idc = head.index("id")
    kc = head.index("kind")
    for i in range(hdr + 1, len(raw)):
        parts = raw[i].rstrip("\n").split("\t")
        if len(parts) == len(head) and parts[kc] == "point":
            old = parts[col]
            new = "7" if old != "7" else "8"
            parts[col] = new
            raw[i] = "\t".join(parts) + "\n"
            with open(path, "w", encoding="utf-8") as fh:
                fh.writelines(raw)
            return parts[idc], old, new
    raise SystemExit("no point row found in %s" % path)


def run_compare(dirname, prefix):
    rc = subprocess.run([sys.executable, "-I", "-B", os.path.join(STAGE, "compare_m1c_f3_r8m1c4.py"),
                         rel(dirname), "REG", prefix],
                        capture_output=True, text=True, cwd=REPO)
    return rc.returncode, rc.stdout.strip(), rc.stderr.strip()


def diff_lines_of(prefix):
    """Return (DIFFS, list of mismatching lines) read back from the formal output VS_FROZEN.
    Data lines are: group, point_id, item, expected, actual. A mismatching line is one with expected != actual
    (the formal script writes only the checks; a DIFF is a check whose expected and actual differ)."""
    path = os.path.join(EV, "%s_VS_FROZEN.tsv" % prefix)
    with open(path, encoding="utf-8") as fh:
        body = fh.read().split("\n")
    last = [l for l in body if l.startswith("DIFFS=")]
    d = int(last[-1].split("=")[1].split()[0]) if last else -1
    diffs = []
    for l in body:
        p = l.split("\t")
        if len(p) == 5 and p[0] not in ("group",) and not l.startswith("#") and p[3] != p[4]:
            diffs.append(l)
    return d, diffs


# ---- A: change pass1 and pass2 ----
stage_copy(PA)
pid_a, old_a, new_a = change_gdb_rc2(os.path.join(PA, "STATE_R6c_pass1.tsv"))
pid_a2, old_a2, new_a2 = change_gdb_rc2(os.path.join(PA, "STATE_R6c_pass2.tsv"))
lines.append("A_CHANGED_POINT\t%s\tpass1 gdb_rc2 %s->%s\tpass2 gdb_rc2 %s->%s" % (pid_a, old_a, new_a, old_a2, new_a2))
rcA, outA, errA = run_compare(PA, "POSCTRL_A_R8_M1c4")
lines.append("A_COMPARE_RC\t%d" % rcA)
if rcA != 0 and not os.path.exists(os.path.join(EV, "POSCTRL_A_R8_M1c4_VS_FROZEN.tsv")):
    lines.append("A_STOP_RULE7\tcompare_m1c_f3_r8m1c4.py did not produce output on the copy: %s" % errA[:300])
    lines.append("POSCTRL=FAIL")
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# POSCTRL_M1C_R8_M1c4 -- positive controls (brief 4.4; formal comparison compare_m1c_f3_r8m1c4.py)\n")
        fh.write("\n".join(lines) + "\n")
    print("POSCTRL=FAIL (stop rule 7)")
    sys.exit(1)
dA, difA = diff_lines_of("POSCTRL_A_R8_M1c4")
hit_A = any(pid_a in l for l in difA)
lines.append("A_DIFFS\t%d\tA_DIFF_LINES\t%d\tA_CHANGED_POINT_IN_DIFF\t%s" % (dA, len(difA), hit_A))
resA = (dA > 0) and hit_A
lines.append("A_RESULT\t%s" % ("PASS" if resA else "FAIL"))

# ---- A2: change pass1 only ----
stage_copy(PA2)
pid_b2, old_b2, new_b2 = change_gdb_rc2(os.path.join(PA2, "STATE_R6c_pass1.tsv"))
lines.append("A2_CHANGED_POINT\t%s\tpass1 gdb_rc2 %s->%s" % (pid_b2, old_b2, new_b2))
rcA2, outA2, errA2 = run_compare(PA2, "POSCTRL_A2_R8_M1c4")
lines.append("A2_COMPARE_RC\t%d" % rcA2)
dA2, difA2 = diff_lines_of("POSCTRL_A2_R8_M1c4")
hit_A2 = any(pid_b2 in l for l in difA2)
lines.append("A2_DIFFS\t%d\tA2_DIFF_LINES\t%d\tA2_CHANGED_POINT_IN_DIFF\t%s" % (dA2, len(difA2), hit_A2))
resA2 = (dA2 > 0) and hit_A2
lines.append("A2_RESULT\t%s" % ("PASS" if resA2 else "FAIL"))

# ---- B: unchanged copy ----
stage_copy(PB)
rcB, outB, errB = run_compare(PB, "POSCTRL_B_R8_M1c4")
lines.append("B_COMPARE_RC\t%d" % rcB)
dB, difB = diff_lines_of("POSCTRL_B_R8_M1c4")
lines.append("B_DIFFS\t%d\tB_DIFF_LINES\t%d" % (dB, len(difB)))
resB = (dB == 0)
lines.append("B_RESULT\t%s" % ("PASS" if resB else "FAIL"))

# ---- J: judge positive control (verdict script, override path, writes only tmp) ----
src_frozen = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c2", "PREREG_M1C_FACTS_R8_M1c2.tsv")
fz = os.path.join(EV, "tmp", "posctrl_frozen_copy.tsv")
with open(src_frozen, encoding="utf-8") as fh:
    fl = fh.readlines()
fhd = None
for i, l in enumerate(fl):
    if l.startswith("row_kind\t"):
        fhd = i
        break
fc = fl[fhd].rstrip("\n").split("\t")
e_rc1 = fc.index("exp_rc1")
tr = fc.index("tree")
gr = fc.index("group")
pr = fc.index("point_id_r8")
changed = None
for i in range(fhd + 1, len(fl)):
    p = fl[i].rstrip("\n").split("\t")
    if len(p) == len(fc) and p[tr] == "F3" and p[gr] == "G5":
        orig = p[e_rc1]
        p[e_rc1] = "7" if orig != "7" else "8"
        changed = (p[pr], orig, p[e_rc1])
        fl[i] = "\t".join(p) + "\n"
        break
with open(fz, "w", encoding="utf-8") as fh:
    fh.writelines(fl)
rcJ = subprocess.run([sys.executable, "-I", "-B", os.path.join(STAGE, "verdict_m1c_r8m1c3.py"), rel(fz)],
                     capture_output=True, text=True, cwd=REPO)
ov_path = os.path.join(EV3, "tmp", "verdict_override.tsv")  # the r8m1c3 script writes its override output under m1c3/tmp
mis = False
if os.path.isfile(ov_path):
    with open(ov_path, encoding="utf-8") as fh:
        for l in fh:
            p = l.rstrip("\n").split("\t")
            if len(p) >= 5 and changed and p[1] == changed[0] and p[3] == "F3" and p[4] == "MISMATCH":
                mis = True
lines.append("J_CHANGED_ROW\t%s\torig_exp_rc1=%s\tnew_exp_rc1=%s" % (changed[0], changed[1], changed[2]))
lines.append("J_VERDICT_RC\t%d\tJ_OUTPUT\t%s" % (rcJ.returncode, rcJ.stdout.strip().replace("\n", " | ")))
lines.append("J_CHANGED_ROW_MISMATCH\t%s" % mis)
resJ = mis
lines.append("J_RESULT\t%s" % ("PASS" if resJ else "FAIL"))

overall = resA and resA2 and resB and resJ
lines.append("POSCTRL=%s" % ("PASS" if overall else "FAIL"))
with open(OUT, "x", encoding="utf-8") as fh:
    fh.write("# POSCTRL_M1C_R8_M1c4 -- positive controls A, A2, B (formal comparison) and J (judge). U220 counting rule.\n")
    fh.write("\n".join(lines) + "\n")
print("POSCTRL=%s" % ("PASS" if overall else "FAIL"))
sys.exit(0 if overall else 1)
