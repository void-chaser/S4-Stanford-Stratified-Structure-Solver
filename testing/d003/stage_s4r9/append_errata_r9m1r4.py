#!/usr/bin/env python3
# append_errata_r9m1r4.py -- Append errata E9-29..E9-34 to ERRATA_9.txt (Step S-C). New file.
import os, sys, subprocess

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ERR_PATH = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "ERRATA_9.txt")

def main():
    if not os.path.isfile(ERR_PATH):
        print(f"ERRATA_9.txt missing at {ERR_PATH}", file=sys.stderr)
        sys.exit(1)

    old_content = open(ERR_PATH, "r", encoding="utf-8").read()

    # Assert git prefix
    head_content = subprocess.check_output(["git", "show", "HEAD:checkpoints/p05/registries/s4r9/ERRATA_9.txt"], cwd=REPO, text=True)
    if not old_content.startswith(head_content):
        print("Prefix assertion failed: ERRATA_9.txt diverged from HEAD", file=sys.stderr)
        sys.exit(1)

    # Assert last E number is E9-28
    if "E9-28" not in old_content or "E9-29" in old_content:
        print("Assertion failed: ERRATA_9.txt does not end cleanly at E9-28", file=sys.stderr)
        sys.exit(1)

    new_errata = """
E9-29
- 事实：gate_r9m1r3_v2.sh 首行残留 m1r2 路径，导致在 03:34:41Z 与 03:36:26Z 运行两次 start 门禁时越界写入 checkpoints/p05/evidence/p05-s4r9/m1r2/tmp/ 下的 py_checks_start.txt、status_now_start.txt、tmp_snap_start.txt。报告 §5（第 123 行）及 §12.2（第 258 行）声称"立即执行恢复并还原原始文件"，但 safe_run.log 中无任何恢复命令，恢复手段原因未查明。
- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m1r3/safe_run.log:L25,L44,L45；checkpoints/p05/evidence/p05-s4r9/m1r2/SHA256SUMS.txt:8136,8138,8142；checkpoints/p05/P05_S4R9_M1R3_REPORT.md:123,258。
- 影响范围：越界污染历史证据目录，属于硬停止违规；现存文件经核对内容与清单一致，按 U324 接受不再处理。
- 处理方式：登记勘误 E9-29，遵循 U324 裁决接受现状，并在本轮门禁与报告中全面披露。

E9-30
- 事实：m1r3 的 EVENTS_R9M1R3.tsv 与证据 SHA256SUMS.txt mtime 为 15:42:45/15:42:46(+1100)，落入 04:38:25Z 至 04:44:56Z 无日志窗口。EVENTS 行号跳过空行，与冻结版 events_r9m1r3.py 的物理行号逻辑不一致；证据 SHA256SUMS.txt 第 2 行声称截断至第 143 行（哈希 94dc58e3…），实际等于前 162 个物理行的哈希。
- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m1r3/safe_run.log:L160,L162,L163；checkpoints/p05/registries/s4r9/M1R3/EVENTS_R9M1R3.tsv:8；checkpoints/p05/evidence/p05-s4r9/m1r3/SHA256SUMS.txt:2。
- 影响范围：r9m1r3 已提交的 EVENTS 表及证据 SHA256SUMS.txt 存在溯源与口径偏差。
- 处理方式：登记勘误 E9-30，已提交原件不改，按 U325 由本轮重算的 EVENTS_RECALC_R9M1R3.tsv 与 SHA_RECHECK_R9M1R3.tsv 作为更正件。

E9-31
- 事实：gate_check_r9m1r3_v5.py 在 end 模式下硬编码读取 FROZEN_SCRIPTS_R9M1R2.tsv，导致 frozen_map 未定义抛出 NameError 崩溃，POST_I_CALL_COUNT_*、POST_I_STAGE_SCRIPTS_ALL_FROZEN、EVENTS_COVERS_ALL_LOGS_BEFORE_GATE、EVIDENCE_SHA256SUMS_ALL_OK 等关键断言全未执行。报告第 126 行声称 v5"绑定 start_v4 基线"，但 gate_r9m1r3_v5.sh:37 实际绑定未完成版 start.txt（ALLOW_START 仅 5 项，TMP 均为空）；且日志物理第 82 行 gate_r9m1r3_v4.sh start _v5 产生 FAILS=1（STRAY_BASELINE_NOT_PRESENT_BEFORE_START），报告未予披露。报告附录 A 仅列"3 项 FAIL"，未披露门禁中断导致的多项断言未执行。
- 证据文件与行号：testing/d003/stage_s4r9/gate_check_r9m1r3_v5.py:290,292,384；testing/d003/stage_s4r9/gate_r9m1r3_v5.sh:37；checkpoints/p05/evidence/p05-s4r9/m1r3/GATE_R9M1R3_start.txt:7,24,25；checkpoints/p05/evidence/p05-s4r9/m1r3/GATE_R9M1R3_start_v5.txt:48,63；checkpoints/p05/P05_S4R9_M1R3_REPORT.md:126,310-330。
- 影响范围：r9m1r3 end 门禁失去有效核验效力，报告对门禁断言覆盖及启动状态披露失实。
- 处理方式：登记勘误 E9-31，原门禁产物保持原样，按 U326 由本轮 recert 脚本只读补做全部断言并输出 RECERT_R9M1R3.tsv。

E9-32
- 事实：r9m1r3 收尾阶段违反任务书 §1-6"每步调用一次，中间不插其他命令"纪律，report_check 运行 3 次（04:35:20Z、04:36:15Z、04:36:52Z），events 运行 2 次（04:37:30Z、04:37:57Z），并在 04:38:11Z 执行内联 cp 命令复制 EVENTS。
- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m1r3/safe_run.log:L155,L156,L157,L158,L160,L161；checkpoints/p05/briefs/P05_S4R9_BRIEF_M1R3.md:§1-6。
- 影响范围：收尾流程违反单向纪律与幂等性要求。
- 处理方式：登记勘误 E9-32，在本轮中重申并严格落实单向收尾纪律。

E9-33
- 事实：16a7897..4e9ff8b 提交的 testing/d003/stage_s4r9/*r9m1r3* 36 个脚本中，大部分未通过 safe_run.sh 包裹，而系编辑器工具直接写入仓库；P05_S4R9_M1R3_REPORT.md（mtime 15:47:10，晚于 finalize 04:46:06Z）与 STATE.md（15:34:03）在日志中均无对应写入命令。
- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m1r3/safe_run.log；checkpoints/p05/evidence/p05-s4r9/m1r4/UNLOGGED_WRITES_R9M1R3.tsv；checkpoints/p05/P05_S4R9_M1R3_REPORT.md；checkpoints/p05/STATE.md。
- 影响范围：文件修改缺乏安全包裹与日志审计，违反执行纪律。
- 处理方式：登记勘误 E9-33，由 unlogged 脚本产出 UNLOGGED_WRITES_R9M1R3.tsv 彻底审计，本轮强制一切写入经 safe_run base64 解码。

E9-34
- 事实：K_COUNT_R9M1R3.tsv 与 K_INHERIT_R9M1R2.tsv 在 13 个组上存在命中数差异（KGRP-M1-007/012/014 等）；旧表 hits 记录的是截取的 min(总数, k_max+2) 次断点数，而非 GDB 实际计数的总命中数，两表统计口径不一致且未在报告中做对账说明。
- 证据文件与行号：checkpoints/p05/registries/s4r9/M1R3/K_COUNT_R9M1R3.tsv；checkpoints/p05/registries/s4r9/M1R2/K_INHERIT_R9M1R2.tsv；testing/d003/stage_s4r9/k_inherit_r9m1r2.py:60-72；checkpoints/p05/evidence/p05-s4r9/m1r4/K_RECON_R9M1R4.tsv。
- 影响范围：K 映射与命中数统计口径存在混淆。
- 处理方式：登记勘误 E9-34，按 U327 以 K_COUNT_R9M1R3 总数为准，由 kmatch 脚本输出 K_RECON_R9M1R4.tsv 逐组明确说明对应关系。
""".strip() + "\n"

    new_content = old_content + "\n" + new_errata
    assert new_content.startswith(old_content)

    with open(ERR_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Appended errata E9-29..E9-34. New bytes: {len(new_content.encode('utf-8'))}.")

if __name__ == "__main__":
    main()
