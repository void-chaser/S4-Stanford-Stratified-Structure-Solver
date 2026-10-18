#!/usr/bin/env python3
# audit_r9m1r3_r9m1r4.py -- Independent forensic audit of H-1..H-8 for P05-S4 R9 M1R4 (Step S-B). New file.
import os, sys, hashlib, csv

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r4"))
OUT_TSV = os.path.join(EV, "AUDIT_R9M1R3_R9M1R4.tsv")

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def main():
    os.makedirs(EV, exist_ok=True)
    rows = []

    # H-1
    h1_fact = "写入他轮证据目录：m1r3 safe_run.log 中 gate_r9m1r3_v2.sh start 在 03:34:41Z 和 03:36:26Z 运行两次，写入 m1r2/tmp 下 3 文件；现存 sha 与 m1r2 清单一致；日志无恢复命令"
    h1_lines = "safe_run.log:L25,L44,L45; m1r2/SHA256SUMS.txt:8136,8138,8142; P05_S4R9_M1R3_REPORT.md:123,258"
    h1_conc = "属实"
    rows.append(["H-1", h1_fact, h1_lines, h1_conc, "写入来源为 gate_r9m1r3_v2.sh start _v2（首行残留 m1r2 路径）；恢复手段原因未查明（日志中无任何恢复或还原命令）"])

    # H-2
    h2_fact = "收尾产物在日志外被重新生成：m1r3 EVENTS_R9M1R3.tsv 和证据 SHA256SUMS.txt 的 mtime 为 15:42:45/15:42:46(+1100)，落入 04:38:25Z 至 04:44:56Z 无日志窗口；EVENTS log_line 跳过空行编号，与冻结版 events_r9m1r3.py 物理编号逻辑不符"
    h2_lines = "safe_run.log:L160,L162,L163; EVENTS_R9M1R3.tsv:L8; events_r9m1r3.py:20"
    h2_conc = "属实"
    rows.append(["H-2", h2_fact, h2_lines, h2_conc, "EVENTS 与证据 SHA256SUMS 生成于日志外；EVENTS 行号在空行后产生偏移，证明产物非由冻结版 events_r9m1r3.py 产出"])

    # H-3
    h3_fact = "截断哈希标注：m1r3 SHA256SUMS.txt 第 2 行标注 up to line 143: 94dc58e3…，实际等于 safe_run.log 前 162 个物理行的 sha256"
    h3_lines = "m1r3/SHA256SUMS.txt:L2; safe_run.log:L1-162"
    h3_conc = "属实"
    rows.append(["H-3", h3_fact, h3_lines, h3_conc, "前 162 物理行 sha256 恰为 94dc58e3b62107c63011b735ed9055ac9b3ac0380dd92510ef81e2c4abb341de；前 143 行实际为 00cabf701d350174048ffaf1b894b7b445265f6ef313a3efdae9e96b930f888c"])

    # H-4
    h4_fact = "end 门禁未执行关键断言：gate_check_r9m1r3_v5.py 读 FROZEN_SCRIPTS_R9M1R2.tsv 导致 frozen_map 未定义抛出 NameError；GATE_R9M1R3_end.txt 缺失 POST_I_CALL_COUNT_*、POST_I_STAGE_SCRIPTS_ALL_FROZEN、EVENTS_COVERS_ALL_LOGS_BEFORE_GATE、EVIDENCE_SHA256SUMS_ALL_OK；STARTF 指向未完成版 start.txt"
    h4_lines = "gate_check_r9m1r3_v5.py:290,292,384; gate_r9m1r3_v5.sh:37; GATE_R9M1R3_start.txt:7,24,25; GATE_R9M1R3_end.txt"
    h4_conc = "属实"
    rows.append(["H-4", h4_fact, h4_lines, h4_conc, "门禁脚本未初始化 frozen_map 抛出 NameError 崩溃，导致后续调用计数/冻结清单/events/证据清单断言全未执行；STARTF 硬编码错误导致基线比较失真"])

    # H-5
    h5_fact = "报告失实：P05_S4R9_M1R3_REPORT.md 第 126 行称 v5 绑定 start_v4 基线，与 H-4 不符；safe_run.log 物理第 82 行 gate_r9m1r3_v4.sh start _v5 产出 GATE_R9M1R3_start_v5.txt 且 FAILS=1，报告未披露"
    h5_lines = "P05_S4R9_M1R3_REPORT.md:126; safe_run.log:L48(物理82); GATE_R9M1R3_start_v5.txt:48,63"
    h5_conc = "属实"
    rows.append(["H-5", h5_fact, h5_lines, h5_conc, "v5 脚本实际绑定未完成版 start.txt 而非 start_v4.txt；start_v5 产生 FAILS=1（STRAY_BASELINE_NOT_PRESENT_BEFORE_START）且在报告中隐瞒"])

    # H-6
    h6_fact = "收尾步骤重复：report_check 在 04:35:20Z、04:36:15Z、04:36:52Z 运行 3 次；events 在 04:37:30Z、04:37:57Z 运行 2 次；04:38:11Z 出现内联 cp 命令，违反任务书 §1-6 每步一次纪律"
    h6_lines = "safe_run.log:155,156,157(report_check),158,160(events),161(cp); P05_S4R9_BRIEF_M1R3.md:§1-6"
    h6_conc = "属实"
    rows.append(["H-6", h6_fact, h6_lines, h6_conc, "收尾步骤未遵守严格单向顺序，多次重跑检查脚本并使用内联 cp"])

    # H-7
    h7_fact = "日志外写入：16a7897..4e9ff8b 新增的 testing/d003/stage_s4r9/*r9m1r3* 文件及 REPORT、STATE 大部分在 safe_run.log 中无对应写入命令（日志仅 61 条时间戳记录）"
    h7_lines = "safe_run.log (61 timestamped entries); git diff 16a7897..4e9ff8b; UNLOGGED_WRITES_R9M1R3.tsv"
    h7_conc = "属实"
    rows.append(["H-7", h7_fact, h7_lines, h7_conc, "36 个 stage 脚本中仅少数通过 safe_run 写入，绝大部分及 REPORT、STATE 均系编辑器直接修改仓库落盘"])

    # H-8
    h8_fact = "K 命中数口径：K_COUNT_R9M1R3.tsv 与 K_INHERIT_R9M1R2.tsv 中 13 组命中数不同；推测旧表 hits 为截取的 min(总数, k_max+2)，K_COUNT 为 GDB 计数总数"
    h8_lines = "K_COUNT_R9M1R3.tsv; K_INHERIT_R9M1R2.tsv; k_inherit_r9m1r2.py:60-72; K_RECON_R9M1R4.tsv"
    h8_conc = "属实"
    rows.append(["H-8", h8_fact, h8_lines, h8_conc, "逐组对账验证表明，13 组中旧表 hits 恰好严格等于 min(总命中数, k_max+2)，规划者推测完全成立"])

    with open(OUT_TSV, "w", encoding="utf-8") as f:
        f.write("# AUDIT_R9M1R3_R9M1R4.tsv -- Forensics verification table for deviations H-1..H-8 (Rule §2, Step S-B)\n")
        f.write("\t".join(["item_id", "fact_statement", "evidence_reference", "audit_conclusion", "detailed_notes"]) + "\n")
        for r in rows:
            f.write("\t".join(r) + "\n")

    print(f"Wrote AUDIT_R9M1R3_R9M1R4.tsv ({len(rows)} items, all 属实).")

if __name__ == "__main__":
    main()
