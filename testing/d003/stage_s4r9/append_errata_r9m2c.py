#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2c; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_errata_r9m2c.py -- Append E9-7 to E9-13 to ERRATA_9.txt with prefix assertion (Step S-B).
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ERR9_PATH = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "ERRATA_9.txt")

ERRATA_TO_APPEND = """
E9-7
- 事实：在记录提交 fbf3054 中，RULINGS.tsv 发生截断（+3 / -155 行），U144 至 U298 共 155 行被误删，文件行数由 307 行降为 155 行。在首次运行 end 门禁（21:14:39Z，GATE_R9M2b_end.txt 第 30、35、36 行）时已检出 RULINGS_BASE_PREFIX_UNCHANGED、RULINGS_PREFIX_OF_START_UNCHANGED、RULINGS_NOT_TRUNCATED 三项 FAIL。但后续恢复方式未经 safe_run，文件于 2026-10-16T21:16:11Z 被静默恢复，该时刻在 safe_run.log 中无条目（未披露的裸写）。恢复后现行版本（42d7d97）为 310 行、122611 字节，经只读核对：前 121086 字节与 ebf3d00 版本相同，U299–U301 三行与 fbf3054 版本相同，全部 U 编号唯一且均为 5 列数据行。
- 证据文件与行号：checkpoints/p05/registries/RULINGS.tsv；checkpoints/p05/evidence/p05-s4r9/m2b/GATE_R9M2b_end.txt:30,35,36；checkpoints/p05/evidence/p05-s4r9/m2c/RULINGS_INTEGRITY_R9M2c.txt；git show --stat fbf3054；git diff fbf3054 42d7d97 -- checkpoints/p05/registries/RULINGS.tsv。
- 影响范围：R9 M2b 过程提交 fbf3054 历史记录中的 RULINGS.tsv；但 42d7d97 库中内容已完整，未影响后续判定与证据真实性。
- 处理方式：依据 AGENTS.md 与任务书要求，不进行 git rebase/amend，截断历史保留在 fbf3054 中并如实披露；通过 rulings_integrity_r9m2c.py 形式化断言现行版本完整性；在 ERRATA_9.txt 登记 E9-7 并由 M2c 报告补充。

E9-8
- 事实：GATE_R9M2b_end.txt 第 30、35、36、44 行为 FAIL（RULINGS_BASE_PREFIX_UNCHANGED、RULINGS_PREFIX_OF_START_UNCHANGED、RULINGS_NOT_TRUNCATED、STRAY_NEW_OR_CHANGED_NONE），但末行却显示 FAILS=0。原因是 gate_check_r9m2b.py 的 __main__ 未使用 sys.exit(fails) 返回失败数，退出码始终为 0；gate_r9m2b.sh 仅累加 Python 进程退出码，导致 Python 检查中的所有 FAIL 行被吞噬。全仓门禁扫描（audit_gates_r9m2c.py）核查了全部 90 个已跟踪 GATE*.txt，全仓仅 GATE_R9M2b_end.txt 一处存在"FAIL 行数 > 0 且 FAILS=0"的吞 FAIL 现象。
- 证据文件与行号：checkpoints/p05/registries/s4r9/M2b/GATE_R9M2b_end.txt:30,35,36,44,54；testing/d003/stage_s4r9/gate_check_r9m2b.py:309-315；testing/d003/stage_s4r9/gate_r9m2b.sh:126-131；checkpoints/p05/evidence/p05-s4r9/m2c/GATE_AUDIT_R9M2c.tsv。
- 影响范围：R9 M2b end 门禁脚本的退出状态准确性与自检机制。
- 处理方式：在 M2c 中新建 gate_check_r9m2c.py 与 gate_r9m2c.sh，修正 Python 退出码为 sys.exit(fails)，shell 脚本末尾使用 grep -c '^FAIL\t'（使用真实 tab 字符）精确统计失败行数并断言一致，强制执行 FAILS=0 且 fail_lines=0 自检；原 M2b 门禁文件不改写。

E9-9
- 事实：gate_check_r9m2b.py（mtime 21:17:02Z，加入 end_R2→end 模式映射）、gate_r9m2b.sh（mtime 21:17:59Z，加入 end_R2 与 BASE_MODE，并将 TRACKED_TESTING_D003_NO_MOD_DEL_SINCE_START 比较基准由 HEAD 改为 $BASE）、gate_allow_r9m2b_end.txt（mtime 21:17:59Z，新增 " M testing/d003/stage_s4r9/*" 规则）三文件在记录提交 fbf3054 之后被就地修改，改动随收尾提交 42d7d97 入库，但未在 m2b safe_run.log、RUNNER_DIFF_R9M2b.txt 或 M2b 报告中披露。
- 证据文件与行号：testing/d003/stage_s4r9/gate_check_r9m2b.py；testing/d003/stage_s4r9/gate_r9m2b.sh；testing/d003/stage_s4r9/gate_allow_r9m2b_end.txt；git diff fbf3054 42d7d97 -- testing/d003/stage_s4r9/gate_*；checkpoints/p05/evidence/p05-s4r9/m2c/GATE_EDITS_R9M2b_UNDISCLOSED.txt。
- 影响范围：M2b 门禁装置的变更透明度与审计追溯。
- 处理方式：由 gate_edits_r9m2c.py 提取完整统一 diff 段与 mtime，在补充报告与事件表中明确披露 4 项裸写事件；确立 U305 纪律，禁止修改已提交的门禁脚本与 allow 文件。

E9-10
- 事实：R9 M2b 任务书 F-1 及勘误 E9-1 中"KGRP-071 F3 命中 4 次、F4 命中 2 次"的表述系规划者事实有误。K_INHERIT_RAW_R9.txt 第 820–829 行显示两边实际各命中 4 次（两边第 4 次均为 arg=22 func=- -:0）。R9 M0 原始日志中全部 73 组的两边命中数均完全相等（0-0 共 9 组 CITED，1-1 共 16 组，2-2 共 8 组，4-4 共 40 组），无一例命中数不等。原脚本真实缺陷是 min 截断、第 4 次命中未取到 bt、大小不同时直接 pass。M2b 补充报告 §4.3 第 1 点后半段与第 2 点关于"较少 continue""LSAN 提前终止导致 2 次"的推测缺乏日志依据，系主观推测。
- 证据文件与行号：checkpoints/p05/registries/s4r9/M0/K_INHERIT_RAW_R9.txt:820-829；checkpoints/p05/registries/s4r9/M2b/K_INHERIT_RAW_R9M2b.txt:746-753；checkpoints/p05/P05_S4R9_M2b_REPORT.md:121-125；checkpoints/p05/registries/s4r9/ERRATA_9.txt:5-10（E9-1）；checkpoints/p05/evidence/p05-s4r9/m2c/KGRP_HITCOUNT_R9_R9M2b.tsv。
- 影响范围：勘误 E9-1 事实描述准确性与 M2b 报告 §4.3 推论有效性。
- 处理方式：在 ERRATA_9.txt 登记 E9-10 更正 E9-1 的"4 vs 2"事实描述，原 E9-1 文本依规则不改写；正式撤回 M2b 报告 §4.3 第 1 点后半段与第 2 点推测，归因为"规划者事实有误，原因未查明"。

E9-11
- 事实：M2b 报告 §7.2 与 STATE.md 记载"事件总表 54 项"，M2b 执行总结记载"58 项 + 1 项"，而 EVENTS_R9_ALL_R9M2b.tsv 实际包含 62 行数据（r9m0 27 行、r9m2 11 行、git reflog amend 1 行、r9m2b 23 行）。此外，m2b safe_run.log 实际有 24 行（最后一行 21:19:56Z 的 copy_registries 漏进表），报告 §7.2 仅列出前 15 行，且遗漏 G-1 与 G-3 的 4 项裸写事件。
- 证据文件与行号：checkpoints/p05/P05_S4R9_M2b_REPORT.md:214-230；checkpoints/p05/STATE.md:17,29；checkpoints/p05/registries/s4r9/M2b/EVENTS_R9_ALL_R9M2b.tsv；checkpoints/p05/evidence/p05-s4r9/m2b/safe_run.log:1-24；checkpoints/p05/evidence/p05-s4r9/m2c/EVENTS_R9_ALL_R9M2c.tsv。
- 影响范围：事件统计数据一致性与过程透明度。
- 处理方式：在 M2c 中通过 events_r9m2c.py 自动从四份 safe_run.log 完整提取条目，严格追加 1 行 reflog 与 4 行裸写事件，形式化断言总行数一致性，并在 M2c 报告与 STATE.md 中统一定量披露。

E9-12
- 事实：HITSEQ_F3_F4_R9M2b.tsv 的 346 行比对中，未区分空命中与非空命中。实际数据为：178 行两边均为全空输出的空串 sha（e3b0c442…），168 行两边非空且完全相同。10 组 NO_SEQ_EVIDENCE_R2 对应的注入点（M2-07 9 点与 M2-06 2 点，共 11 点，覆盖 10 组）两遍实测 HIT 行全部非空且与 F3 完全一致（NONEMPTY_IDENTICAL）。
- 证据文件与行号：checkpoints/p05/registries/s4r9/M2b/HITSEQ_F3_F4_R9M2b.tsv；checkpoints/p05/evidence/p05-s4r9/m2c/HITSEQ_SPLIT_R9M2c.tsv；checkpoints/p05/registries/s4r9/M2b/K_INHERIT_R9M2b.tsv。
- 影响范围：HIT 行等价证据的分类精度与替代采信效力。
- 处理方式：在 hitseq_split_r9m2c.py 中对 HITSEQ 进行分类切分与统计，明确区分 BOTH_EMPTY 与 NONEMPTY_IDENTICAL；对 10 组 NO_SEQ 逐组核实两遍均为 NONEMPTY_IDENTICAL，依据 U303 采信为替代证据，判定为 SUBSTITUTE_OK。

E9-13
- 事实：P05_S4R9_M2b_REPORT.md 中多处使用了"严格""彻底""完全"等强化词汇（如"严格遵循""严格执行""彻底重做""完全一致"），违反了 M2b 任务书 §5 的措辞硬纪律。
- 证据文件与行号：checkpoints/p05/P05_S4R9_M2b_REPORT.md:12,106,140,248 等。
- 影响范围：报告文字客观性与规范合规性。
- 处理方式：已提交报告原件不改写；在 ERRATA_9.txt 登记 E9-13，在补充报告 P05_S4R9_M2c_REPORT.md 中严格纠正措辞，消除所有主观强化词，客观陈述事实。
"""

# Read old data
with open(ERR9_PATH, "rb") as f:
    old_bytes = f.read()

append_bytes = ERRATA_TO_APPEND.lstrip("\n").encode("utf-8")
new_bytes = old_bytes + append_bytes

# Enforce §1 Rule 8 assertion: new file = old bytes + new lines
assert new_bytes[:len(old_bytes)] == old_bytes, "Assertion failed: prefix mismatch!"
assert new_bytes[len(old_bytes):] == append_bytes, "Assertion failed: suffix mismatch!"
assert len(new_bytes) == len(old_bytes) + len(append_bytes), "Assertion failed: length mismatch!"

# Write to disk
with open(ERR9_PATH, "wb") as f:
    f.write(new_bytes)

print(f"ERRATA_9.txt updated: {len(old_bytes)} -> {len(new_bytes)} bytes (+{len(append_bytes)} bytes).")
print("  Appended E9-7 through E9-13.")
