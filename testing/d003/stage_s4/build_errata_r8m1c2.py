#!/usr/bin/env python3
# build_errata_r8m1c2.py -- builds the ERRATA_8.txt append block for P05-S4 R8 M1c2 (E8-79, E8-80).
# E8-79 (a)-(d) read verbatim from briefs/P05_S4R8_BRIEF_M1c1.md section 3.2;
# (e) numbers are read from the recomputed R7 F2 distribution table, not from the brief.
# Usage: python3 -I -B build_errata_r8m1c2.py BRIEF1 DIST OUT
import sys

brief, dist, out = sys.argv[1], sys.argv[2], sys.argv[3]
with open(brief, encoding="utf-8") as fh:
    src = fh.read().splitlines()
want = ["(a)", "(b)", "(c)", "(d)"]
items = {}
in32 = False
for line in src:
    if line.startswith("### 3.2"):
        in32 = True
        continue
    if in32 and line.startswith("## "):
        break
    if in32:
        body = line.lstrip("- ").strip()
        for w in want:
            if body.startswith(w) and w not in items:
                items[w] = body
missing = sorted(set(want) - set(items))
if missing:
    print("MISSING_IN_BRIEF_3_2 %s" % missing)
    sys.exit(3)

d = {}
with open(dist, encoding="utf-8") as fh:
    for line in fh:
        p = line.rstrip("\n").split("\t")
        if len(p) == 2 and p[0] != "key":
            d[p[0]] = p[1]
e_text = (
    "(e) U213 的内容，R7 F2 实际事实分布（由 count_r7_f2_facts_r8m1c2.py 从已提交表中重新计算，"
    "见 R7_F2_FACT_DIST_R8_M1c2.tsv；以下数字以表为准，与任务书数字的差异另行写明）："
    "G5 point rc1=20/rc2=0/hit=1 为 %s 点；G5 point rc1=0/rc2=20/hit=1 为 %s 点；"
    "G6 point rc1=20/rc2=0/hit=1 为 %s 点；G5 control（rc1=0/rc2=0/hit=0）为 %s 点；"
    "G6c control（rc1=0/rc2=0/hit=0）为 %s 点。"
    % (d.get("G5_rc1_20_rc2_0_hit1", "?"), d.get("G5_rc1_0_rc2_20_hit1", "?"),
       d.get("G6_rc1_20_rc2_0_hit1", "?"), d.get("G5_control_zero", "?"), d.get("G6c_control_zero", "?"))
)
lines = []
lines.append("E8-79\tP05-S4 R8 M1c2 更正（只追加；依据 AGENTS.md 第 2、5 节与 P05-S4 R8 M1c1 任务书 §3.2）。")
lines.append("        " + items["(a)"])
lines.append("        " + items["(b)"])
lines.append("        " + items["(c)"])
lines.append("        " + items["(d)"])
lines.append("        " + e_text)
lines.append("")
lines.append("E8-80\tP05-S4 R8 M1c1 报告瑕疵记录（只追加；原报告不改）。")
lines.append("        (a) r8m1c1 报告 §1 写“两次违规”，实际表二列出三次（两份允许列表、gate_check_r8m1c1.py、报告本身均为 heredoc 写入），以表二为准。")
lines.append("        (b) r8m1c1 报告表二第 2 行称 gate_check_r8m1c1.py 由 heredoc 写入，第 4 行称由 write 工具生成，二者矛盾。以 safe_run.log 无对应记录、报告自述 heredoc 为准：gate_check_r8m1c1.py 为 heredoc 写入，未经 safe_run。")
lines.append("        (c) r8m1c1 报告缺提交后的 git log -1 与 git status --short。r8m1c2 开工时核实 HEAD = f913b57、git status --short 为空，以此补记；见 POSTCOMMIT_R8_M1c2.txt。")
lines.append("")
with open(out, "w", encoding="utf-8") as fh:
    fh.write("\n".join(lines))
print("ERRATA_BLOCK_OK")
