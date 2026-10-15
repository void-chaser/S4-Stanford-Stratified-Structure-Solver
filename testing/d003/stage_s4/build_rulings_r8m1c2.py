#!/usr/bin/env python3
# build_rulings_r8m1c2.py -- builds the RULINGS.tsv append block for P05-S4 R8 M1c2 (U209-U217).
# U209-U214 summaries are read verbatim from briefs/P05_S4R8_BRIEF_M1c1.md section 3.1.
# Usage: python3 -I -B build_rulings_r8m1c2.py BRIEF1 OUT
import sys

brief, out = sys.argv[1], sys.argv[2]
with open(brief, encoding="utf-8") as fh:
    src = fh.read().splitlines()
want = ["U209", "U210", "U211", "U212", "U213", "U214"]
texts = {}
for line in src:
    for uid in want:
        head = "- **%s**：" % uid
        if line.startswith(head):
            texts[uid] = line[len(head):].strip()
missing = sorted(set(want) - set(texts))
if missing:
    print("MISSING_IN_BRIEF %s" % missing)
    sys.exit(3)

rows = []
for uid in want:
    rows.append((uid, "P05-S4 R8 M1c1 任务书 §3（于 r8m1c2 登记）", texts[uid], "P05-S4 R8 M1c1 任务书 §3.1", "生效"))
rows.append(("U215", "P05-S4 R8 M1c2 任务书 §3",
             "接受 r8m1c1（f913b57）停在开工门禁。三次 bash heredoc 写入（两份允许列表、gate_check_r8m1c1.py、报告）未经 safe_run，按执行偏离接受，不追认为合规；文件内容经规划者事后核查无禁止项，保留原样。r8m1c1 的门禁文件和 *r8m1c1* 脚本冻结、不再运行。M1c 在 r8m1c2 重新开始。",
             "P05-S4 R8 M1c2 任务书 §3.1", "生效"))
rows.append(("U216", "P05-S4 R8 M1c2 任务书 §3",
             "写入途径澄清（自 r8m1c2 起适用）。新建脚本、允许列表、报告、STATE.md、任务书副本可以用 write/edit 工具；证据产物、RULINGS/ERRATA 追加、registries 复制、提交只能经 safe_run 运行的本轮脚本。bash 中直接写文件（含 heredoc）和 safe_run -- sh -c 内联写入一律禁止。§1.3 检查适用于包括门禁在内的每个新脚本，须在运行前做。",
             "P05-S4 R8 M1c2 任务书 §3.1", "生效"))
rows.append(("U217", "P05-S4 R8 M1c2 任务书 §3",
             "M1c 分两轮。r8m1c2 做 U209–U214 登记、事实期望冻结、预检、F2 基线运行、F2 比较、阳性对照；F3 运行与比较、逐行判定、M1 总表放到 r8m1c3。U214“F2 0 差异才跑 F3”保持不变。",
             "P05-S4 R8 M1c2 任务书 §3.1", "生效"))

with open(out, "w", encoding="utf-8") as fh:
    for uid, src_col, summ, rec, st in rows:
        assert "\t" not in summ and "\n" not in summ, uid
        fh.write("%s\t%s\t%s\t%s\t%s\n" % (uid, src_col, summ, rec, st))
print("ROWS=%d" % len(rows))
