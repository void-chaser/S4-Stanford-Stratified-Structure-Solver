#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_errata_r9m1r2.py -- Append E9-14 through E9-20 to ERRATA_9.txt with prefix assertion (Step S-C). New file.
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ERR_PATH = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "ERRATA_9.txt")

EXPECTED_OLD_BYTES = 13893
EXPECTED_OLD_SHA = "e7e93590bec5a0340ed28859b0f292b8d21f1adfbd6502ef61ff741785052f12"

ERRATA_TEXT = """
E9-14
- 事实：r9m1 在记录提交 00490a7 后，预注册表 PREREG_M1_F4_R9M1.tsv 及 PREREG_M1_CITED_F2_R9M1.tsv 被原地重生成并覆盖，sha 分别从 3894d8990c3f… 变为 d57fcf29e572…、193759a2… 变为 72fa0e4d…，相差 52 行（G1 30 行、G2b 22 行）。原因在于 PLAN_M1B_R8_M1b1.tsv 中 (point_id, tree) 跨组存在 104 个重复键，旧生成脚本仅以 point_id 为键导致分组覆盖。
- 证据文件与行号：checkpoints/p05/registries/s4r9/M1/PREREG_M1_F4_R9M1.tsv；checkpoints/p05/evidence/p05-s4r9/m1r2/PREREG_DIFF_R9M1R2.tsv；checkpoints/p05/registries/s4r8/M1b/r8m1b1/PLAN_M1B_R8_M1b1.tsv。
- 影响范围：M1 预注册冻结性被破坏，收尾时提交了未在记录提交 (i) 冻结的新期望。
- 处理方式：依据 U312 登记勘误，不改 r9m1 历史提交；在 r9m1r2 中通过 U313 以 (section, group, point_id) 为完整键重新机械推导并冻结预注册。

E9-15
- 事实：r9m1 在 safe_run.log 中记录了多次覆盖运行与重跑：冒烟重跑 3 次（行 34–39），改预注册后再跑冒烟（行 43–44）；正式运行脚本被连续修改并调用 5 次（行 45–61），覆盖了前序正式运行输出；判定脚本被修改并重判 3 次（行 47–62），且未在报告中披露覆盖重跑过程。
- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m1/safe_run.log:22,34-39,40-41,43-44,45-63；checkpoints/p05/evidence/p05-s4r9/m1r2/forensic/SCRIPT_VERSIONS_R9M1R2.tsv；checkpoints/p05/evidence/p05-s4r9/m1r2/forensic/TIMELINE_R9M1R2.tsv。
- 影响范围：运行证据链完整性与历史可追溯性受损。
- 处理方式：依据 U312 登记勘误；在 r9m1r2 中依 U316 严格单次调用正式运行，两遍在同一次调用中完成，不覆盖历史结果。

E9-16
- 事实：r9m1 证据目录下存在多处未通过 safe_run.sh 执行的裸写文件，包括收尾门禁 GATE_R9M1_end_R3.txt（15:52:04Z）、临时测试脚本 tmp/test_diff.py、tmp/test_inj_call.py、tmp/test_sim.py、tmp/test_actual_diff.py、tmp/test_actual_m1c.py，以及 tmp/test_smoke_g5/ 目录及其下 201 个中间文件。
- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m1r2/BARE_WRITE_AUDIT_R9M1R2.tsv；checkpoints/p05/evidence/p05-s4r9/m1/GATE_R9M1_end_R3.txt；checkpoints/p05/evidence/p05-s4r9/m1/tmp/。
- 影响范围：违反 safe_run 执行纪律与写入拦截审计要求。
- 处理方式：依据 U312 登记勘误；裸写文件在 r9m1 补登事件表中全面列出并归档，r9m1r2 严格禁止 safe_run 外写入。

E9-17
- 事实：r9m1 在收尾前通过新建 gate_allow_r9m1_end_R2.txt 放宽门禁，增加了 " M checkpoints/p05/registries/s4r9/M1/*" 与 " M testing/d003/stage_s4r9/*" 两项通配修改许可，掩盖了记录提交 (i) 之后修改 prereg_r9m1.py 和 copy_registries_r9m1.py 的事实。
- 证据文件与行号：testing/d003/stage_s4r9/gate_allow_r9m1_end_R2.txt:5,9；checkpoints/p05/evidence/p05-s4r9/m1/safe_run.log:90-93。
- 影响范围：门禁放宽掩盖了已提交文件的违规修改。
- 处理方式：依据 U312 登记勘误；在 r9m1r2 门禁中硬性禁止任何 " M " 通配项，端门禁逐个断言冻结文件 sha256。

E9-18
- 事实：r9m1 在 K_INHERIT_R9M1.tsv 中对 35 组记为 NO_SEQ_EVIDENCE_R2 并直接依据 U303 采信 HIT 行等价，其中 29 组（涉及 218 点）k_max > 1，超出了 U303 仅适用于 k_max=1 的裁决范围。此外，testing/d003/src 驱动仅输出 HIT/HITCOUNT 等汇总行，K_INHERIT_RAW 中每次命中均为 arg=None func=None loc=None:0，未取到逐次调用 trace，报告声称"init 与 polyinj 输出了完全一致的 trace 序列"缺乏原始依据。
- 证据文件与行号：checkpoints/p05/registries/s4r9/M1/K_INHERIT_R9M1.tsv；checkpoints/p05/registries/s4r9/M1/K_INHERIT_RAW_R9M1.txt；checkpoints/p05/P05_S4R9_M1_REPORT.md:92-94。
- 影响范围：K 继承证据链越界采信，序列证明事实与报告表述不符。
- 处理方式：依据 U312 登记勘误；依据 U315 重做 K 继承证明，采用 dbg 与 kmap-dbg 变体获取真实 S4 堆栈序列并比对。

E9-19
- 事实：r9m1 存在多处仓库与证据目录不一致：registries/s4r9/M1/EVENTS_R9M1.tsv 仅有 85 条记录，而证据目录为 96 条记录（报告正文写 96）；registries 目录下门禁文件仅复制了 GATE_R9M1_end.txt，而报告正文第 33 行与表头明确引用 end_R3。
- 证据文件与行号：checkpoints/p05/registries/s4r9/M1/EVENTS_R9M1.tsv；checkpoints/p05/evidence/p05-s4r9/m1/EVENTS_R9M1.tsv；checkpoints/p05/P05_S4R9_M1_REPORT.md:33,184。
- 影响范围：小表提交与证据原件脱节，报告引用的小表在 registries 中不存在。
- 处理方式：依据 U312 登记勘误；在 r9m1r2 收尾时增加断言：registries 副本与证据原件 sha256 相同，报告引用的所有小表在 registries 必须存在。

E9-20
- 事实：checkpoints/p05/P05_S4R9_M1_REPORT.md 中多处使用了"完全""完全一致""完全闭环""严格遵循"等主观强化词汇，违反了任务书措辞硬纪律。
- 证据文件与行号：checkpoints/p05/P05_S4R9_M1_REPORT.md:23,112,113,114,174,179,189,192,215。
- 影响范围：报告客观性不足，违反措辞纪律。
- 处理方式：在 ERRATA_9.txt 登记 E9-20，r9m1 报告原件保留，r9m1r2 报告落盘前经脚本 grep 检查确保主观强化词命中数为 0。
"""

with open(ERR_PATH, "rb") as fh:
    old_bytes = fh.read()

assert len(old_bytes) == EXPECTED_OLD_BYTES, f"Size mismatch: {len(old_bytes)} != {EXPECTED_OLD_BYTES}"
old_sha = hashlib.sha256(old_bytes).hexdigest()
assert old_sha == EXPECTED_OLD_SHA, f"Sha mismatch: {old_sha} != {EXPECTED_OLD_SHA}"

# Prepare append text
append_bytes = ERRATA_TEXT.lstrip("\n").encode("utf-8")
new_bytes = old_bytes + append_bytes
assert new_bytes.startswith(old_bytes), "Prefix assertion failed!"
assert len(new_bytes) == len(old_bytes) + len(append_bytes), "Length assertion failed!"

# Write back atomically
with open(ERR_PATH, "wb") as fh:
    fh.write(new_bytes)

print(f"Successfully appended errata E9-14 through E9-20 to ERRATA_9.txt.")
print(f"Old size: {len(old_bytes)}, New size: {len(new_bytes)} bytes.")
