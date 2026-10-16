#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m0; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# gdb_audit_r9.py -- Audit all file:line breakpoints in GDB scripts and Python files for P05-S4 R9.
import os, re, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m0"))
os.makedirs(EV, exist_ok=True)
OUT_TSV = os.path.join(EV, "GDB_LINE_AUDIT_R9.tsv")

# R9 used gdb scripts in effective set / plan:
# - testing/d003/stage_s4/r6c_state_r8m2a3.gdb (38 rows on F3/F4)
# - testing/d003/stage_s4/r6c_state_bt_r8m2d.gdb (18 rows on F3/F4)
# - testing/d003/stage_s4/m210_b_r8m2a2_R2.gdb (1 row cited on B tree)
R9_USED_SCRIPTS = {
    "testing/d003/stage_s4/r6c_state_r8m2a3.gdb",
    "testing/d003/stage_s4/r6c_state_bt_r8m2d.gdb",
    "testing/d003/stage_s4/m210_b_r8m2a2_R2.gdb",
}

def map_f4_line(filename, line_num):
    # F4 linemap rule (LINEMAP_F3_F4_S3R5.tsv):
    # In S4/S4.cpp: lines 1..1759 -> offset 0
    # lines 1760..1773 -> MODIFIED_BY_FIX (14 lines in F3 -> 27 lines in F4)
    # lines 1774+ -> offset +13
    # Other files (fmm_*.cpp, rcwa.cpp, etc.) -> unmodified (offset 0)
    base = os.path.basename(filename)
    if base == "S4.cpp":
        if line_num <= 1759:
            return str(line_num)
        elif line_num <= 1773:
            return f"MODIFIED_BY_FIX({line_num})"
        else:
            return str(line_num + 13)
    else:
        return str(line_num) + "(file_unmodified)"

bp_regex = re.compile(r'(?:break|b)\s+([a-zA-Z0-9_/\.\-]+\.(?:cpp|c|h)):(\d+)')

audit_rows = []
unmapped_r9_used = 0

scan_roots = [os.path.join(REPO, "testing", "d003")]
for root_dir in scan_roots:
    for root, dirs, files in os.walk(root_dir):
        if "__pycache__" in dirs:
            dirs.remove("__pycache__")
        for f in files:
            if not (f.endswith(".gdb") or f.endswith(".py")):
                continue
            fpath = os.path.join(root, f)
            rel_path = os.path.relpath(fpath, REPO)
            
            try:
                content = open(fpath, encoding="utf-8", errors="ignore").readlines()
            except Exception:
                continue

            for lno, line in enumerate(content, 1):
                m = bp_regex.search(line)
                if m:
                    target_file = m.group(1)
                    target_line = int(m.group(2))
                    target_str = f"{target_file}:{target_line}"

                    # Determine tree
                    tree = "F3"
                    if "m210_b" in rel_path:
                        tree = "B"
                    elif "_r7" in rel_path or "stage_s4r7" in rel_path:
                        tree = "F2/F"
                    elif "stage_s1r" in rel_path:
                        tree = "HISTORICAL_S1"

                    mapped = map_f4_line(target_file, target_line) if tree not in ("B", "HISTORICAL_S1") else "N/A(non-F4_tree)"

                    used = "YES" if rel_path in R9_USED_SCRIPTS else "NO"
                    
                    if used == "YES":
                        if tree == "B":
                            action = "B_TREE_SAFE(cited_on_B_not_run_on_F4)"
                        else:
                            action = f"F4_MAPPED({mapped})"
                    else:
                        action = "NOT_USED_IN_R9"

                    audit_rows.append([
                        rel_path,
                        str(lno),
                        target_str,
                        tree,
                        mapped,
                        used,
                        action
                    ])

# Also verify function breakpoints in R9 gdb scripts:
r6c_path = os.path.join(REPO, "testing", "d003", "stage_s4", "r6c_state_r8m2a3.gdb")
r6c_bt_path = os.path.join(REPO, "testing", "d003", "stage_s4", "r6c_state_bt_r8m2d.gdb")
for p in (r6c_path, r6c_bt_path):
    txt = open(p, encoding="utf-8").read()
    m = bp_regex.search(txt)
    if m:
        raise AssertionError(f"Script {p} unexpectedly contains line breakpoint: {m.group(0)}")

# Write TSV
headers = ["script", "script_line", "target", "tree", "F4_mapped_line", "R9_used", "action"]
with open(OUT_TSV, "w", encoding="utf-8") as fh:
    fh.write("# GDB_LINE_AUDIT_R9.tsv -- Full audit of file:line breakpoints in testing/d003/ (Section 4 S-E)\n")
    fh.write("\t".join(headers) + "\n")
    for row in audit_rows:
        fh.write("\t".join(row) + "\n")

print(f"SUCCESS: Audited {len(audit_rows)} file:line breakpoints across testing/d003/ -> {OUT_TSV}")
print(f"  R9 used scripts: {len(R9_USED_SCRIPTS)} (r6c_state_r8m2a3.gdb, r6c_state_bt_r8m2d.gdb, m210_b_r8m2a2_R2.gdb)")
print("  All F4 scripts used in R9 rely exclusively on function breakpoints; 0 unmapped line breakpoints.")
