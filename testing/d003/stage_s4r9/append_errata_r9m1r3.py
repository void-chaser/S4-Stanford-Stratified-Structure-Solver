#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_errata_r9m1r3.py -- Append E9-21 through E9-28 to ERRATA_9.txt with prefix assertion (Step S-C). New file.
import hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
ERR_PATH = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "ERRATA_9.txt")

EXPECTED_OLD_BYTES = 19322
EXPECTED_OLD_SHA = "0e416f01a52f652a80dd4b34abea9ea7264459dece0297149025a94253a0a745"

ERRATA_TEXT = """
E9-21
- 事实：r9m1r2 记录提交 a413db0 之后写入 compare_f3_f4_r9m1r2_R2.py、posctrl_r9m1r2_R2.py、run_smoke_r9m1r2_R2.py、run_formal_r9m1r2_R2.py、run_formal_r9m1r2_R3.py 等新脚本，最终有效正式事实来自未列入冻结清单的 _R3 与 _R2 脚本，FROZEN_SCRIPTS_R9M1R2.tsv 中列出的原件没有产出最终结果。
- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m1r2/safe_run.log:L29,L30,L33,L34,L39,L40,L37,L44；checkpoints/p05/registries/s4r9/M1R2/FROZEN_SCRIPTS_R9M1R2.tsv。
- 影响范围：违背记录提交后脚本冻结纪律，被测事实脱离冻结清单。
- 处理方式：在 ERRATA_9.txt 登记 E9-21，按 U318 r9m1r2 提交文件全部保留，其结论降级为'参考结果二'，在 r9m1r3 重新冻结并单次调用正式脚本。

E9-22
- 事实：r9m1r2 在记录提交后多次调用 posctrl（2 次）、smoke（3 次）、formal（2 次）；首次正式运行 runs/formal 因 run_formal_r9m1r2_R2.py:228 中将 point_id 误写为 id 发生 KeyError 中断，无 FORMAL_FACTS 输出；报告 §8.1 记载'依据 §1-11，正式运行脚本仅调用 1 次'与实际日志严重不符。
- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m1r2/safe_run.log:L28,L31,L32,L35,L37,L38,L40；checkpoints/p05/P05_S4R9_M1R2_REPORT.md:175-179。
- 影响范围：违反"单次调用"纪律，报告陈述失实。
- 处理方式：在 ERRATA_9.txt 登记 E9-22，核实 runs/formal 中断根因，r9m1r3 门禁强制断言冻结期调用计数精确等于 1。

E9-23
- 事实：r9m1r2 中 L36 原地改写 run_smoke_r9m1r2_R2.py 后 L37 重跑；L43 原地改写 compare_f3_f4_r9m1r2_R2.py 后 L44 重跑并覆盖 F3_F4_EQUIV_R9M1R2.tsv；L31 运行的阳性对照使用的是 L29 版本的 compare，未覆盖 L43 原地改写后的最终比对逻辑。
- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m1r2/safe_run.log:L31,L36,L37,L43,L44；checkpoints/p05/registries/s4r9/M1R2/F3_F4_EQUIV_R9M1R2.tsv。
- 影响范围：违反已执行脚本不得原地改写纪律，阳性对照有效性未闭环。
- 处理方式：在 ERRATA_9.txt 登记 E9-23，r9m1r3 引入试跑期并要求改写换文件名进事件表，阳性对照覆盖最终冻结版比对脚本。

E9-24
- 事实：r9m1r2 存在多处未受 safe_run.log 记录的裸写产物：tmp/test_plain_g 等 7 个调试构建产物（01:31-01:35Z，介于 L13 与 L14 之间）及 posctrl_tampered_* 等 6 个篡改表（01:49:05Z，早于 L24）；报告 §11 记载越界写入次数为 0 并声称全部写入经 safe_run.sh 运行，遗漏披露裸写。
- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m1r2/tmp/test_plain_g, test_dbg_g, gdb_test.cmd, count.cmd, d003-F3-test-dbg, d003plan-F3-test-dbg, d003plan-F4-test-dbg, posctrl_tampered_pass1/pass2/verdict/agg.tsv, posctrl_case3_verdict/agg.tsv；checkpoints/p05/P05_S4R9_M1R2_REPORT.md:235-245。
- 影响范围：过程透明性不足，报告披露不实。
- 处理方式：在 ERRATA_9.txt 登记 E9-24，经 BARE_WRITE_AUDIT_R9M1R3.tsv 补登裸写台账，r9m1r3 坚决禁止任何裸写。

E9-25
- 事实：r9m1r2 收尾阶段 events_r9m1r2.py 于 L52 运行，未收录 L53-L65 共 13 条日志；end 门禁运行 4 次，中间穿插多条内联 exec 脚本改写报告 §13、registries 及 SHA256SUMS；当前 m1r2/SHA256SUMS.txt 校验有 2 项 FAILED（safe_run.log, tmp/status_now_end.txt），且 GATE_R9M1R2_end_R4.txt 漏列清单。
- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m1r2/safe_run.log:L52-L65；checkpoints/p05/evidence/p05-s4r9/m1r2/SHA256SUMS.txt；checkpoints/p05/P05_S4R9_M1R2_REPORT.md:255-290。
- 影响范围：证据清单自洽性受损，收尾纪律执行不力。
- 处理方式：在 ERRATA_9.txt 登记 E9-25，r9m1r3 规范收尾单向固定顺序，门禁之后禁止改写任何交付物。

E9-26
- 事实：run_formal_r9m1r2_R3.py:90-97 对 G2c_control 组 3 个未运行行（f3_effective_verdict=NOT_RUN_AS_EXPECTED）未真实调用驱动，却人工填入 rc=0、rc1=0、rc2=0、class=CONTROL_OK；预注册中这 3 行期望类别为 NOT_RUN_REGISTRY_ERROR；报告 §9.2 错误地将合成的 0/CONTROL_OK 称为'本轮事实'。
- 证据文件与行号：testing/d003/stage_s4r9/run_formal_r9m1r2_R3.py:90-97；checkpoints/p05/registries/s4r9/M1R2/PREREG_M1_F4_R9M1R2.tsv；checkpoints/p05/P05_S4R9_M1R2_REPORT.md:207。
- 影响范围：歪曲物理事实，人为伪造控制通过状态。
- 处理方式：在 ERRATA_9.txt 登记 E9-26，按 U319 未运行行一律保持 rc='-'、class=NOT_RUN_REGISTRY_ERROR、verdict=NOT_RUN_AS_EXPECTED，比对单列为 NOT_RUN。

E9-27
- 事实：verdict_r9m1r2.py:133 显式限制 if grp == 'G5':，M1c G6 的 I1–I6 完全未进入判定；compare_f3_f4_r9m1r2_R2.py:91-132 错误读取了全为 '-' 的 STATE_SEAM 表，并在任一侧为 '-' 时跳过比对，导致 F3_F4_EQUIV 中 G6 25 行 f3_I* 均为 '-'；报告 §9.1 虚假声称逐字段核对了 I1..I6 并达成 0 DIFFS。
- 证据文件与行号：testing/d003/stage_s4r9/verdict_r9m1r2.py:133；testing/d003/stage_s4r9/compare_f3_f4_r9m1r2_R2.py:91-132,183；checkpoints/p05/registries/s4r9/M1R2/F3_F4_EQUIV_R9M1R2.tsv；checkpoints/p05/P05_S4R9_M1R2_REPORT.md:194-201。
- 影响范围：核心不变量判定与比对出现实质性逻辑漏洞，报告结论失实。
- 处理方式：在 ERRATA_9.txt 登记 E9-27，按 U320 将 G6 的 I1–I6 接入 RESULTS_R6c_SEAM 进行判定，并在比对中与 r8m1c3 冻结事实及预注册三方逐字段严格比对。

E9-28
- 事实：build_kmap_r9m1r2.py:175-184 仅在 8 个预设 FMM 模式下粗粒度比较 malloc 命中总数，未按 26 个 d003/d003plan 组各自的 clean_env 与断点符号逐一比对命中数；K_INHERIT_R9M1R2.tsv 统计 416 点未给出与 651 点逐行映射关系；报告 §12 声称需用户裁决项为'无'，掩盖了核对不充分问题。
- 证据文件与行号：testing/d003/stage_s4r9/build_kmap_r9m1r2.py:175-184；checkpoints/p05/registries/s4r9/M1R2/K_INHERIT_R9M1R2.tsv；checkpoints/p05/P05_S4R9_M1R2_REPORT.md:248-251。
- 影响范围：K 继承证据链完整性存在瑕疵。
- 处理方式：在 ERRATA_9.txt 登记 E9-28，按 U321 编写 kcount 脚本按 26 组独立 env/断点补核命中数，并产出 K_COVERAGE 覆盖映射总表对账。
"""

def main():
    with open(ERR_PATH, "rb") as f:
        old_bytes = f.read()
    
    assert len(old_bytes) == EXPECTED_OLD_BYTES, f"Bytes mismatch: {len(old_bytes)} != {EXPECTED_OLD_BYTES}"
    actual_old_sha = hashlib.sha256(old_bytes).hexdigest()
    assert actual_old_sha == EXPECTED_OLD_SHA, f"SHA mismatch: {actual_old_sha} != {EXPECTED_OLD_SHA}"

    new_content = old_bytes.decode("utf-8") + ERRATA_TEXT
    assert new_content.startswith(old_bytes.decode("utf-8")), "Prefix assertion failed"

    with open(ERR_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    with open(ERR_PATH, "rb") as f:
        final_bytes = f.read()
    final_sha = hashlib.sha256(final_bytes).hexdigest()
    print(f"Appended errata E9-21..E9-28. New bytes={len(final_bytes)}, sha={final_sha}.")

if __name__ == "__main__":
    main()
