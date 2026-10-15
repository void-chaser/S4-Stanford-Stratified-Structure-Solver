#!/usr/bin/env python3
# build_rulings_r8m1c3.py -- P05-S4 R8 M1c3 RULINGS builder (brief section 3.1). New file.
# Writes the text to append to checkpoints/p05/registries/RULINGS.tsv as the file
# $EV/RULINGS_APPEND_R8_M1c3.tsv (5 columns, status 生效, source P05-S4 R8 M1c3 任务书 §3).
# Called by append_rulings_r8m1c3.sh.  Does not touch RULINGS.tsv itself.
# Usage: python3 -I -B build_rulings_r8m1c3.py
import os

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)
OUT = os.path.join(EV, "RULINGS_APPEND_R8_M1c3.tsv")
if os.path.exists(OUT):
    raise SystemExit("REFUSED exists (U17): %s" % OUT)

SRC = "P05-S4 R8 M1c3 任务书 §3"
ROWS = [
    ("U218", "P05-S4 R8 M1c3 任务书 §3（于 r8m1c3 登记）",
     "接受 r8m1c2（`3661416`）的结果与全部披露：事实冻结 472 行（`58ce1241…`），F2 基线 DIFFS=0、GDB_DIVERGENT=0（1112 条比较记录），阳性对照通过。按 U214，准许在 r8m1c3 运行 F3。这不是 M1、R8 或 P05-S4 的签收。",
     "P05-S4 R8 M1c3 任务书 §3.1"),
    ("U219", "P05-S4 R8 M1c3 任务书 §3（于 r8m1c3 登记）",
     "r8m1c2 的输出目录 `m1c_F2`（大写；任务书写作 `m1c_f2`）按执行偏离接受，不移动（U17）。自 r8m1c3 起，目录名一律以运行脚本实际生成的 `m1c_<TREE>`（`m1c_F2`、`m1c_F3`）为准，预检须检查实际名。",
     "P05-S4 R8 M1c3 任务书 §3.1"),
    ("U220", "P05-S4 R8 M1c3 任务书 §3（于 r8m1c3 登记）",
     "r8m1c2 阳性对照的\"DIFFS=1\"是任务书的计数错误：改动一个 `gdb_rc2` 必然同时破坏 STATE_FACT 与 TWO_PASS 两项，并使 GDB_DIVERGENT=1。接受\"DIFFS>0，且被改动的 point_id 出现在 DIFF 行中；未改副本 DIFFS=0\"为阳性对照判定口径。自本轮起，确切计数如实记录，不作期望。",
     "P05-S4 R8 M1c3 任务书 §3.1"),
    ("U221", "P05-S4 R8 M1c3 任务书 §3（于 r8m1c3 登记）",
     "r8m1c2 中白名单外的只读内联命令（`ls`、`wc`、`head`、`tail`、`cut`、`awk`、`sed -n`、`git show`、`git diff`）按执行偏离接受，不追认为合规。",
     "P05-S4 R8 M1c3 任务书 §3.1"),
    ("U222", "P05-S4 R8 M1c3 任务书 §3（于 r8m1c3 登记）",
     "`postcommit_r8m1c2.py`（提交后创建，未跟踪）随 r8m1c3 记录提交纳入，不修改、不再运行。自本轮起，提交后记录脚本必须在提交前写好并通过 §1.3 检查，提交后只运行、不新建。",
     "P05-S4 R8 M1c3 任务书 §3.1"),
]

with open(OUT, "w", encoding="utf-8") as fh:
    for rid, given, summary, record in ROWS:
        fh.write("\t".join([rid, given, summary, record, "生效"]) + "\n")
print("BUILT_RULINGS_ROWS=%d -> %s" % (len(ROWS), OUT))
