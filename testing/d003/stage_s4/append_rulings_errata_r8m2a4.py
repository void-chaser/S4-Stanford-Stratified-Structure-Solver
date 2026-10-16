#!/usr/bin/env python3
# append_rulings_errata_r8m2a4.py -- Append U248-U252 and E8-101-E8-103.
import os, sys

REPO = os.environ.get("REPO", os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..")))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a4"))
RUL_FILE = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")
ERR_FILE = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "ERRATA_8.txt")

EV_RUL_APP = os.path.join(EV, "RULINGS_APPEND_R8_M2a4.tsv")
EV_ERR_APP = os.path.join(EV, "ERRATA_APPEND_R8_M2a4.txt")

RULINGS_TEXT = """U248\tP05-S4 R8 M2a4 任务书 §3\tM2-02（阶段 e）：接受 r8m2a2 搜索结论 NOT_FOUND_IN_SCOPE；M2-02 在 S4 内不出点，转 S5。\tP05-S4 R8 M2a4 任务书 §3\t生效
U249\tP05-S4 R8 M2a4 任务书 §3\tM2-08（类别 C）：接受原网格 NOT_FOUND；1D+FFT 候选（NEEDS_NEW_DRIVER_SCOPE_EXPANSION）不在 S4 扩驱动范围，转 S5 登记。\tP05-S4 R8 M2a4 任务书 §3\t生效
U250\tP05-S4 R8 M2a4 任务书 §3\tr8m2a2 已披露的 14 项 safe_run 偏离按执行偏离接受，不追认为合规。\tP05-S4 R8 M2a4 任务书 §3\t生效
U251\tP05-S4 R8 M2a4 任务书 §3\t五个 win:64 行（UNRESOLVED_INDEX）：M2b 中先做诊断运行（标 INFLUENCED，不得回填为事前验证）→ 确认索引 → 补预注册冻结 sha256 → 正式两遍运行。本轮只写设计（§7），不运行。\tP05-S4 R8 M2a4 任务书 §3\t生效
U252\tP05-S4 R8 M2a4 任务书 §3\tr8m2a3 的结果按以下口径接受：原预注册未变；M2-04 call3 恢复索引、rc3 列、sanitizer UNOBSERVED、I7 与 exp_san 关系等修正有效；但 r8m2a3 的 COMPLETENESS「150/150 PASS / Complete end-to-end evidence chain verified」不成立（无运行器、无事实提取、无 gdb→I 值分析器），由本轮 COMPLETENESS v2 取代；Case J 把 I6 输出差异定为 SCHEMA_ERROR 是设计错误，由本轮更正。\tP05-S4 R8 M2a4 任务书 §3\t生效
"""

ERRATA_TEXT = """
E8-101	P05-S4 R8 M2a4 更正（只追加；依据 AGENTS.md 第 2、5 节与 P05-S4 R8 M2a4 任务书 §3、§5）。原条目不改。
        r8m2a3 判定缺陷审计（VERDICT_AUDIT_R8_M2a4.tsv）检出 11 项核心缺陷：(a) D1 verdict_m2_r8m2a3.py:234-236、279-303 中 I1–I6 仅做字符串比对，缺乏 gdb.log 解析至私有状态 I 值的分析器；(b) D2 verdict_m2_r8m2a3.py:252-271 对控制映射 28 对全部做逐字节比较，致 M2-06 与 M2-07 注入行（失败调用）必然 OUTPUT_DIFF，且 d003plan 驱动写 S4FMM_DUMP1/S4FMM_DUMP 不产出 callN.txt 致必然 MISSING_DUMP；(c) D3 Case J 将 I6 输出差异定为 SCHEMA_ERROR 系设计错误，应为 I6=VIOLATED -> MISMATCH；(d) D4 M2-10 exp_class=BASELINE_ONLY 与 judge_d003.classify 输出集合不交致必然 MISMATCH；(e) D5 M2-04 双失败仅核 exp_hit=2 总数，缺 hit1/hit2 分项、缺 INJECT2 INVALID/SUPPRESSED 检查与第二失败层断言；(f) D6 r6c_judge 仅支持 inj_call∈{1,2} 无法处理 M2-04 时序；(g) D7 M2-03 缺非 sanitizer 参照点致 U246 不可判，且 san_options 与计数规则未冻结；(h) D8 缺失运行器与事实提取脚本致 r8m2a3 COMPLETENESS PASS 不成立；(i) D9-D11 结构与汇总互斥分类缺陷。

E8-102	P05-S4 R8 M2a4 更正（只追加）。原条目不改。
        有效预注册 v2 PREREG_M2_EFFECTIVE_R8_M2a4.tsv（sha256 d917b3e2...）取代 r8m2a3 预注册：150 个 point_id 与全部 exp_* 原值逐项不变（exp_* 改动为 0）。新增 13 个控制与规则列：class_rule（JUDGE_D003 vs BASELINE_ONLY_RULE）、output_assertion（I6_ONLY, RECORD_ONLY, NONE）、双失败 8 列（exp_hit1, exp_hit2, exp_inject2_invalid=0, exp_inject2_suppressed=0, k_before2=2, k_fail2=3, fail_layer1=1, fail_layer2=1/UNRESOLVED）、san_ref_point_id（12 个 REP 点映射至 M2-01 同 env 点，19 个 G5/G6 点记为 NO_REF 并判 UNJUDGED）、san_options（冻结 ASAN/UBSAN_OPTIONS 日志落盘于 EV/run/pass<n>/<point_id>/）、state_analyzer（指定本轮 state_judge_m2_r8m2a4.py 及其 sha256）。

E8-103	P05-S4 R8 M2a4 更正（只追加）。原条目不改。
        状态分析器 state_judge_m2_r8m2a4.py（sha256 becf0ab5...）解除 U13 硬编码，支持预注册动态时序索引与 M2-04 双失败及 I5/I6 断言。经历史 R6c 真实证据回放验证（checkpoints/p05/evidence/p05-s4r6c/），在 177 点 × 2 passes × 6 不变量（2124 项）全面比对中实现差异数为 0（REPLAY_R6c_R8_M2a4.tsv）。
"""

def main():
    if os.path.exists(EV_RUL_APP) or os.path.exists(EV_ERR_APP):
        sys.exit(f"REFUSED: append files already exist in EV (U17)")

    os.makedirs(EV, exist_ok=True)
    with open(EV_RUL_APP, "w", encoding="utf-8") as fh:
        fh.write(RULINGS_TEXT)
    with open(EV_ERR_APP, "w", encoding="utf-8") as fh:
        fh.write(ERRATA_TEXT.lstrip("\n"))

    # Append to living files
    with open(RUL_FILE, "a", encoding="utf-8") as fh:
        fh.write(RULINGS_TEXT)
    with open(ERR_FILE, "a", encoding="utf-8") as fh:
        fh.write(ERRATA_TEXT)

    print("Appended U248-U252 to RULINGS.tsv and E8-101-E8-103 to ERRATA_8.txt.")

if __name__ == "__main__":
    main()
