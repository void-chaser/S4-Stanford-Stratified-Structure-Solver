#!/usr/bin/env python3
# posctrl_m1c_r8m1c3.py -- P05-S4 R8 M1c3 positive controls (brief section 6.3, U220 counting rule). New file.
# A. comparison positive control: copy the F3 STATE/SEAM run files into $EV/tmp/posctrl/ (shutil), change one
#    point row gdb_rc2 in copy A; copy B is unchanged.  The same comparison used by compare_m1c_f3_r8m1c3.py is applied
#    to the copies against the R8 F2 committed copies (fact tuples, same columns and rule as the comparison script).
#    Expected: copy A DIFFS>0 and the changed point id appears in a DIFF line; copy B DIFFS=0.  Exact counts recorded.
# B. judge positive control: copy the frozen M1c table to $EV/tmp/posctrl/, change one F3 point row exp_rc1, and run
#    verdict_m1c_r8m1c3.py on the copy (it writes to tmp only); the changed row must give MISMATCH.
# Output: $EV/POSCTRL_M1C_R8_M1c3.txt, ending with POSCTRL=PASS or POSCTRL=FAIL.
# Usage: python3 -I -B posctrl_m1c_r8m1c3.py
import os, shutil, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1c", "r8m1c2")
PC = os.path.join(EV, "tmp", "posctrl")
os.makedirs(PC, exist_ok=True)
OUT = os.path.join(EV, "POSCTRL_M1C_R8_M1c3.txt")
if os.path.exists(OUT):
    raise SystemExit("REFUSED exists (U17): %s" % OUT)

STATE_FACT = ["rc_gdb", "rc_nogdb", "gdb_rc1", "gdb_rc2", "gdb_rc3", "gdb_hit", "gdb_done",
              "nogdb_rc1", "nogdb_rc2", "nogdb_rc3", "nogdb_hit", "nogdb_done"]
SEAM_FACT = ["rc_gdb", "rc_nogdb", "gdb_rc1", "gdb_rc2", "gdb_hit", "gdb_done",
             "nogdb_rc1", "nogdb_rc2", "nogdb_hit", "nogdb_done"]
F3FILES = ["STATE_R6c_pass1.tsv", "STATE_R6c_pass2.tsv", "STATE_SEAM_R6c_pass1.tsv", "STATE_SEAM_R6c_pass2.tsv",
           "RESULTS_R6c_STATE.tsv", "RESULTS_R6c_SEAM.tsv"]
F2FILES = {
    "STATE_R6c_pass1.tsv": "M1C_F2_STATE_R6c_pass1.tsv",
    "STATE_R6c_pass2.tsv": "M1C_F2_STATE_R6c_pass2.tsv",
    "STATE_SEAM_R6c_pass1.tsv": "M1C_F2_STATE_SEAM_R6c_pass1.tsv",
    "STATE_SEAM_R6c_pass2.tsv": "M1C_F2_STATE_SEAM_R6c_pass2.tsv",
}
F3DIR = os.path.join(EV, "m1c_F3")
lines = []


def read_rows_path(path):
    with open(path, encoding="utf-8") as fh:
        ls = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = ls[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in ls[1:]]


def fact_diffs(f3_rows_by_id, f2_rows_by_id, cols):
    diffs = []
    for pid in sorted(set(f3_rows_by_id) | set(f2_rows_by_id)):
        if pid not in f3_rows_by_id or pid not in f2_rows_by_id:
            diffs.append(pid)
            continue
        a = tuple(f3_rows_by_id[pid].get(c, "") for c in cols)
        b = tuple(f2_rows_by_id[pid].get(c, "") for c in cols)
        if a != b:
            diffs.append(pid)
    return diffs


def compare_copy(state_pass1_path):
    """The comparison used on the copy: fact tuples of pass1 STATE and SEAM vs the R8 F2 committed copies."""
    f3s = {r["id"]: r for r in read_rows_path(state_pass1_path)}
    f2s = {r["id"]: r for r in read_rows_path(os.path.join(REG, F2FILES["STATE_R6c_pass1.tsv"]))}
    d = fact_diffs(f3s, f2s, STATE_FACT)
    return d


# ---- A. comparison positive control ----
copyA = os.path.join(PC, "copyA_STATE_R6c_pass1.tsv")
copyB = os.path.join(PC, "copyB_STATE_R6c_pass1.tsv")
shutil.copyfile(os.path.join(F3DIR, "STATE_R6c_pass1.tsv"), copyA)
shutil.copyfile(os.path.join(F3DIR, "STATE_R6c_pass1.tsv"), copyB)

# change one point row's gdb_rc2 in copy A (pick the first point row of kind 'point')
with open(copyA, encoding="utf-8") as fh:
    raw = fh.readlines()
hdr_idx = None
for i, l in enumerate(raw):
    if l.startswith("kind\t"):
        hdr_idx = i
        break
head = raw[hdr_idx].rstrip("\n").split("\t")
col = head.index("gdb_rc2")
target_pid = None
for i in range(hdr_idx + 1, len(raw)):
    parts = raw[i].rstrip("\n").split("\t")
    if len(parts) == len(head) and parts[0] == "point":
        parts[col] = "7" if parts[col] != "7" else "8"
        target_pid = parts[head.index("id")]
        raw[i] = "\t".join(parts) + "\n"
        break
with open(copyA, "w", encoding="utf-8") as fh:
    fh.writelines(raw)

dA = compare_copy(copyA)
dB = compare_copy(copyB)
hit_in_diff = target_pid in dA
lines.append("A_COPY_CHANGED_POINT\t%s" % target_pid)
lines.append("A_DIFFS\t%d" % len(dA))
lines.append("A_DIFF_IDS\t%s" % ",".join(dA))
lines.append("A_CHANGED_POINT_IN_DIFF\t%s" % hit_in_diff)
lines.append("B_DIFFS\t%d" % len(dB))
ok_a = (len(dA) > 0) and hit_in_diff
ok_b = (len(dB) == 0)
lines.append("A_RESULT\t%s" % ("PASS" if ok_a else "FAIL"))
lines.append("B_RESULT\t%s" % ("PASS" if ok_b else "FAIL"))

# ---- B. judge positive control: frozen copy with changed exp_rc1 for one F3 point row ----
frozen_src = os.path.join(REG, "PREREG_M1C_FACTS_R8_M1c2.tsv")
frozen_copy = os.path.join(PC, "frozen_copy.tsv")
with open(frozen_src, encoding="utf-8") as fh:
    fl = fh.readlines()
fhead = None
for i, l in enumerate(fl):
    if l.startswith("row_kind\t"):
        fhead = i
        break
fcols = fl[fhead].rstrip("\n").split("\t")
e_rc1 = fcols.index("exp_rc1")
tree_i = fcols.index("tree")
grp_i = fcols.index("group")
changed_row = None
for i in range(fhead + 1, len(fl)):
    p = fl[i].rstrip("\n").split("\t")
    if len(p) == len(fcols) and p[tree_i] == "F3" and p[grp_i] == "G5":
        orig = p[e_rc1]
        p[e_rc1] = "7" if orig != "7" else "8"
        changed_row = (p[fcols.index("point_id_r8")], orig, p[e_rc1])
        fl[i] = "\t".join(p) + "\n"
        break
with open(frozen_copy, "w", encoding="utf-8") as fh:
    fh.writelines(fl)

# run the verdict on the copy (writes only under tmp via the override path argument)
rc = subprocess.run([sys.executable, "-I", "-B", os.path.join(REPO, "testing", "d003", "stage_s4", "verdict_m1c_r8m1c3.py"),
                     frozen_copy], capture_output=True, text=True, cwd=REPO)
ov_out = rc.stdout.strip()
ov_rows_path = os.path.join(EV, "tmp", "verdict_override.tsv")
mismatch_on_changed = False
if os.path.isfile(ov_rows_path):
    with open(ov_rows_path, encoding="utf-8") as fh:
        for l in fh:
            p = l.rstrip("\n").split("\t")
            if len(p) >= 5 and changed_row and p[1] == changed_row[0] and p[3] == "F3" and p[4] == "MISMATCH":
                mismatch_on_changed = True
lines.append("B_CHANGED_ROW\t%s\torig_exp_rc1=%s\tnew_exp_rc1=%s" % (
    changed_row[0] if changed_row else "-", changed_row[1] if changed_row else "-", changed_row[2] if changed_row else "-"))
lines.append("B_JUDGE_OUTPUT\t%s" % ov_out.replace("\n", " | "))
lines.append("B_CHANGED_ROW_MISMATCH\t%s" % mismatch_on_changed)
ok_judge = mismatch_on_changed
lines.append("B_RESULT\t%s" % ("PASS" if ok_judge else "FAIL"))

overall = ok_a and ok_b and ok_judge
lines.append("POSCTRL=%s" % ("PASS" if overall else "FAIL"))
with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("# POSCTRL_M1C_R8_M1c3 -- positive controls (U220 counting rule).\n")
    fh.write("\n".join(lines) + "\n")
print("POSCTRL=%s" % ("PASS" if overall else "FAIL"))
sys.exit(0 if overall else 1)
