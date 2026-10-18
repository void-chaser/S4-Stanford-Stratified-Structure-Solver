#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# forensic_r9m1r2.py -- Forensic analysis of r9m1 execution, prereg diff, and rejudgment (Step S-B). New file.
import base64, csv, difflib, hashlib, os, subprocess, sys
from collections import Counter

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
FORENSIC_DIR = os.path.join(EV, "forensic")
os.makedirs(FORENSIC_DIR, exist_ok=True)

# -------------------------------------------------------------
# Part 1: Recover script versions and timeline from safe_run.log
# -------------------------------------------------------------
log_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1", "safe_run.log")
with open(log_path, "r", encoding="utf-8") as f:
    log_lines = f.read().splitlines()

targets = ["prereg_r9m1.py", "run_smoke_r9m1.py", "run_formal_r9m1.py", "verdict_r9m1.py", "compare_f3_f4_r9m1.py"]

timeline_rows = []
extracted_scripts = [] # (target_name, fname, line_num, utc_ts, length, sha256, content)

for idx, line in enumerate(log_lines, 1):
    parts = line.split("\t")
    utc_ts = parts[0]
    cwd = parts[1] if len(parts) > 1 else ""
    out_dir = parts[2] if len(parts) > 2 else ""
    cmd = parts[3] if len(parts) > 3 else ""

    # Check timeline category
    cat = "EXEC"
    if "open(" in cmd and "b64decode(" in cmd:
        cat = "WRITE_SCRIPT"
    elif "git status" in cmd:
        cat = "STATUS"
    elif "gate_r9m1" in cmd:
        cat = "GATE"
    elif "run_smoke" in cmd:
        cat = "RUN_SMOKE"
    elif "run_formal" in cmd:
        cat = "RUN_FORMAL"
    elif "verdict" in cmd:
        cat = "VERDICT"
    elif "compare" in cmd:
        cat = "COMPARE"
    elif "copy_registries" in cmd:
        cat = "COPY_REGISTRIES"

    cmd_summary = cmd[:160] + ("..." if len(cmd) > 160 else "")
    timeline_rows.append([idx, utc_ts, cat, cmd_summary])

    # Extract base64 written scripts
    cursor = 0
    while True:
        pos_open = line.find("open('", cursor)
        if pos_open == -1:
            pos_open = line.find('open("', cursor)
            if pos_open == -1:
                break
            q = '"'
        else:
            q = "'"
        cursor = pos_open + 6
        end_fname = line.find(q, cursor)
        if end_fname == -1:
            break
        fpath = line[cursor:end_fname]
        cursor = end_fname + 1
        fname = os.path.basename(fpath)
        
        pos_b64 = line.find("base64.b64decode(", cursor)
        if pos_b64 == -1 or pos_b64 > cursor + 30:
            continue
        q_b64 = line[pos_b64 + 17]
        if q_b64 not in ("'", '"'):
            continue
        start_b64 = pos_b64 + 18
        end_b64 = line.find(q_b64, start_b64)
        if end_b64 == -1:
            continue
        b64_content = line[start_b64:end_b64]
        cursor = end_b64 + 1

        if fname in targets:
            data = base64.b64decode(b64_content)
            sha = hashlib.sha256(data).hexdigest()
            extracted_scripts.append((fname, idx, utc_ts, len(data), sha, data))

# Write timeline TSV
timeline_tsv_path = os.path.join(FORENSIC_DIR, "TIMELINE_R9M1R2.tsv")
with open(timeline_tsv_path, "w", encoding="utf-8") as f:
    f.write("# TIMELINE_R9M1R2.tsv -- Timeline of all operations in r9m1 safe_run.log\n")
    f.write("line_number\tutc_time\tcategory\tcommand_summary\n")
    for r in timeline_rows:
        f.write("%d\t%s\t%s\t%s\n" % (r[0], r[1], r[2], r[3]))

# Save extracted scripts and calculate diffs
script_version_rows = []
by_script = {}
for fname, line_num, utc_ts, length, sha, data in extracted_scripts:
    base_name = os.path.splitext(fname)[0]
    out_fname = f"{base_name}_line{line_num}.py"
    out_fpath = os.path.join(FORENSIC_DIR, out_fname)
    with open(out_fpath, "wb") as f:
        f.write(data)

    text_lines = data.decode("utf-8", errors="replace").splitlines(keepends=True)
    prev = by_script.get(fname)
    if prev is None:
        diff_lines = 0
        diff_note = "initial_version"
    else:
        prev_lines = prev.decode("utf-8", errors="replace").splitlines(keepends=True)
        udiff = list(difflib.unified_diff(prev_lines, text_lines))
        diff_lines = len(udiff)
        diff_note = f"{diff_lines}_diff_lines_vs_previous"

    by_script[fname] = data
    script_version_rows.append([fname, line_num, utc_ts, sha, length, diff_lines, diff_note, out_fname])

script_versions_tsv = os.path.join(FORENSIC_DIR, "SCRIPT_VERSIONS_R9M1R2.tsv")
with open(script_versions_tsv, "w", encoding="utf-8") as f:
    f.write("# SCRIPT_VERSIONS_R9M1R2.tsv -- Recovered script versions from r9m1 safe_run.log\n")
    f.write("script_name\tsafe_run_line\tutc_time\tsha256\tsize_bytes\tdiff_lines\tdiff_note\tsaved_file\n")
    for r in script_version_rows:
        f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\t{r[5]}\t{r[6]}\t{r[7]}\n")

print(f"Extracted {len(extracted_scripts)} script versions, timeline {len(timeline_rows)} entries.")

# -------------------------------------------------------------
# Part 2: Preregistration diff between 00490a7 and 56b1e43
# -------------------------------------------------------------
p_old_bytes = subprocess.check_output(["git", "show", "00490a7:checkpoints/p05/registries/s4r9/M1/PREREG_M1_F4_R9M1.tsv"])
p_new_bytes = subprocess.check_output(["git", "show", "56b1e43:checkpoints/p05/registries/s4r9/M1/PREREG_M1_F4_R9M1.tsv"])
c_old_bytes = subprocess.check_output(["git", "show", "00490a7:checkpoints/p05/registries/s4r9/M1/PREREG_M1_CITED_F2_R9M1.tsv"])
c_new_bytes = subprocess.check_output(["git", "show", "56b1e43:checkpoints/p05/registries/s4r9/M1/PREREG_M1_CITED_F2_R9M1.tsv"])

# Save copies to forensic dir
with open(os.path.join(FORENSIC_DIR, "PREREG_M1_F4_00490a7.tsv"), "wb") as f:
    f.write(p_old_bytes)
with open(os.path.join(FORENSIC_DIR, "PREREG_M1_CITED_F2_00490a7.tsv"), "wb") as f:
    f.write(c_old_bytes)

p_old_lines = p_old_bytes.decode("utf-8").splitlines()
p_new_lines = p_new_bytes.decode("utf-8").splitlines()

header = p_old_lines[1].split("\t")
prereg_diff_rows = []
for idx in range(2, len(p_old_lines)):
    lo = p_old_lines[idx].split("\t")
    ln = p_new_lines[idx].split("\t")
    if lo != ln:
        diff_fields = []
        for j in range(len(lo)):
            if lo[j] != ln[j]:
                diff_fields.append((header[j], lo[j], ln[j]))
        for fld, old_val, new_val in diff_fields:
            prereg_diff_rows.append([idx - 1, lo[0], lo[1], lo[2], fld, old_val, new_val])

prereg_diff_tsv = os.path.join(EV, "PREREG_DIFF_R9M1R2.tsv")
with open(prereg_diff_tsv, "w", encoding="utf-8") as f:
    f.write("# PREREG_DIFF_R9M1R2.tsv -- Field-by-field differences between 00490a7 and 56b1e43 preregistration\n")
    f.write("row_num\tsection\tgroup\tpoint_id\tfield\told_value\tnew_value\n")
    for r in prereg_diff_rows:
        f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\t{r[5]}\t{r[6]}\n")

# Check duplicate keys in PLAN_M1B_R8_M1b1.tsv
plan_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1b", "r8m1b1", "PLAN_M1B_R8_M1b1.tsv")
plan_pts = []
plan_pt_tree = []
with open(plan_path, "r", encoding="utf-8") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        plan_pts.append(r["point_id"])
        plan_pt_tree.append((r["point_id"], r["tree"]))

c_pts = Counter(plan_pts)
dups_pts = {k: v for k, v in c_pts.items() if v > 1}
c_pt_tree = Counter(plan_pt_tree)
dups_pt_tree = {k: v for k, v in c_pt_tree.items() if v > 1}

print(f"Prereg diff rows: {len(prereg_diff_rows)} across differing lines.")
print(f"PLAN_M1B: {len(plan_pts)} total rows, {len(dups_pts)} dup point_ids, {len(dups_pt_tree)} dup (point_id, tree) pairs.")

# -------------------------------------------------------------
# Part 3: Offline Rejudgment against Old and New Preregistration
# -------------------------------------------------------------
pass1_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1", "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1_pass1.tsv")
pass2_path = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1", "runs", "formal", "FORMAL_FACTS_M1_F4_R9M1_pass2.tsv")

def load_facts(p):
    facts = {}
    with open(p, encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if l.strip() and not l.startswith("#")]
        h = lines[0]
        for l in lines[1:]:
            r = dict(zip(h, l))
            facts[(r["section"], r["group"], r["point_id"])] = r
    return facts

facts_p1 = load_facts(pass1_path)
facts_p2 = load_facts(pass2_path)

def load_prereg_dict(lines):
    prereg = {}
    data_lines = [l.strip().split("\t") for l in lines if l.strip() and not l.startswith("#")]
    h = data_lines[0]
    for l in data_lines[1:]:
        r = dict(zip(h, l))
        prereg[(r["section"], r["group"], r["point_id"])] = r
    return prereg

prereg_old_map = load_prereg_dict(p_old_lines)
prereg_new_map = load_prereg_dict(p_new_lines)

def judge_facts(prereg_map):
    verdicts = {}
    counts = {"MATCH": 0, "NOT_REACHED_AS_EXPECTED": 0, "NOT_RUN_AS_EXPECTED": 0, "MISMATCH": 0, "FLAKY": 0}
    for key in sorted(prereg_map.keys()):
        sec, grp, pid = key
        exp = prereg_map[key]
        p1 = facts_p1[key]
        p2 = facts_p2[key]

        consistent = (
            p1["rc1"] == p2["rc1"] and p1["rc2"] == p2["rc2"] and p1["rc3"] == p2["rc3"] and
            p1["hit"] == p2["hit"] and p1["class"] == p2["class"] and
            p1["I1"] == p2["I1"] and p1["I2"] == p2["I2"] and p1["I3"] == p2["I3"] and
            p1["I4"] == p2["I4"] and p1["I5"] == p2["I5"] and p1["I6"] == p2["I6"]
        )

        diff_fields = []
        if not consistent:
            v = "FLAKY"
            diff_fields.append("pass1_vs_pass2_disagree")
        else:
            exp_eff = exp["f3_effective_verdict"]
            if exp_eff == "NOT_RUN_AS_EXPECTED":
                v = "NOT_RUN_AS_EXPECTED"
            elif exp_eff == "NOT_REACHED_AS_EXPECTED":
                if p1["hit"] == "0" and p1["class"] == "INVALID":
                    v = "NOT_REACHED_AS_EXPECTED"
                else:
                    v = "MISMATCH"
                    diff_fields.append(f"unexpected_hit({p1['hit']})")
            else:
                if exp["exp_rc1"] != "-" and p1["rc1"] != exp["exp_rc1"]:
                    diff_fields.append(f"rc1({p1['rc1']}!={exp['exp_rc1']})")
                if sec == "M1b":
                    if exp["exp_rc2"] not in ("-", "", "0") and p1["rc2"] != exp["exp_rc2"]:
                        diff_fields.append(f"rc2({p1['rc2']}!={exp['exp_rc2']})")
                else:
                    if exp["exp_rc2"] != "-" and p1["rc2"] != exp["exp_rc2"]:
                        diff_fields.append(f"rc2({p1['rc2']}!={exp['exp_rc2']})")
                if exp["exp_rc3"] != "-" and p1["rc3"] != exp["exp_rc3"]:
                    diff_fields.append(f"rc3({p1['rc3']}!={exp['exp_rc3']})")
                if exp["exp_hit"] != "-" and p1["hit"] != exp["exp_hit"]:
                    diff_fields.append(f"hit({p1['hit']}!={exp['exp_hit']})")

                exp_c = exp["exp_class"]
                if sec == "M1c":
                    exp_pv = exp["exp_point_verdict"]
                    if exp_pv == "-" and grp in ("G6c", "CTRL_AUX"):
                        exp_pv = "CONTROL_OK"
                    if p1["class"] != exp_pv:
                        diff_fields.append(f"point_verdict({p1['class']}!={exp_pv})")
                    if grp == "G5":
                        for iname in ("I1", "I2", "I3", "I4", "I5", "I6"):
                            if exp[f"exp_{iname}"] != "-" and p1[iname] != exp[f"exp_{iname}"]:
                                diff_fields.append(f"{iname}({p1[iname]}!={exp[f'exp_{iname}']})")
                else:
                    if p1["class"] != exp_c:
                        diff_fields.append(f"class({p1['class']}!={exp_c})")

                if not diff_fields:
                    v = "MATCH"
                else:
                    v = "MISMATCH"

        counts[v] += 1
        verdicts[key] = (v, ";".join(diff_fields) if diff_fields else "NONE")
    return counts, verdicts

counts_old, verdicts_old = judge_facts(prereg_old_map)
counts_new, verdicts_new = judge_facts(prereg_new_map)

# Write rejudge TSV
rejudge_tsv = os.path.join(EV, "REJUDGE_OLD_PREREG_R9M1R2.tsv")
with open(rejudge_tsv, "w", encoding="utf-8") as f:
    f.write("# REJUDGE_OLD_PREREG_R9M1R2.tsv -- Rejudgment of r9m1 formal facts against old vs new preregistration\n")
    f.write("section\tgroup\tpoint_id\told_verdict\told_diff_fields\tnew_verdict\tnew_diff_fields\tdisagreed\n")
    for key in sorted(prereg_old_map.keys()):
        sec, grp, pid = key
        vo, dfo = verdicts_old[key]
        vn, dfn = verdicts_new[key]
        disagreed = "YES" if vo != vn else "NO"
        f.write(f"{sec}\t{grp}\t{pid}\t{vo}\t{dfo}\t{vn}\t{dfn}\t{disagreed}\n")

print(f"Rejudgment: Old prereg counts = {counts_old}")
print(f"Rejudgment: New prereg counts = {counts_new}")
