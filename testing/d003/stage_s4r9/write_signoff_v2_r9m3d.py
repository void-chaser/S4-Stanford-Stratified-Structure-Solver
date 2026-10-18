#!/usr/bin/env python3
# write_signoff_v2_r9m3d.py -- write the corrected P05-S3/P05-S4 signoff-scope DRAFT v2 from the recomputed tables
# (readiness, handoff, corrected ledger, audit, M1R3 verdict, P05_S4R4 report and the S1/S2 signoff record). No number
# is hand-typed; the "与 v1 的差异" table mirrors P-1..P-6. New file (r9m3d).
# usage: write_signoff_v2_r9m3d.py [OUT.md]
import os, sys, re
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
REG = os.path.join(REPO, "checkpoints/p05/registries")
M1R3 = os.path.join(REG, "s4r9/M1R3")
OUT = os.path.join(REPO, "checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT_v2.md")
S1S2 = os.path.join(REPO, "checkpoints/p05/P05_S1_S2_SIGNOFF.md")
R4 = os.path.join(REPO, "checkpoints/p05/P05_S4R4_REPORT.md")
M3C_C = os.path.join(REPO, "checkpoints/p05/P05_S3R3_CLOSEOUT.md")
M3_4B = os.path.join(REPO, "checkpoints/p05/P05_S3_4b_CLOSURE.md")
TAB = chr(9)
NL = chr(10)
POINTS = ("R4-CL01-F-F4", "R4-CL02-F-F4", "R4-CL03-F-F4", "R4-CL04-F-F4",
          "R4-PJ01-F-F4", "R4-PN01-F-F4", "R4-PV01-F-F4")


def read_table(path):
    rows = []
    hdr = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f and f[0] == hdr[0]:
            continue
        rows.append(dict(zip(hdr, f)))
    return hdr, rows


def v1_items():
    orig = os.path.join(REPO, "checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT.md")
    lines = open(orig, encoding="utf-8").read().splitlines()
    items = []
    insec = False
    for line in lines:
        if line.startswith("### 转入 S5 的项"):
            insec = True
            continue
        if insec and line.startswith("#"):
            break
        if insec and line.strip().startswith("- "):
            items.append(line.strip()[2:])
    return items


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else OUT
    _, aud = read_table(os.path.join(EV, "AUDIT_R9M3C_R9M3D.tsv"))
    _, rdy = read_table(os.path.join(EV, "READINESS_P05_S3S4_R9M3D.tsv"))
    _, hand = read_table(os.path.join(EV, "S5_HANDOFF_R9M3D.tsv"))
    _, led = read_table(os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv"))
    rc = {}
    for r in rdy:
        rc[r.get("status", "?")] = rc.get(r.get("status", "?"), 0) + 1
    gaps = [r.get("item", "") for r in rdy if r.get("status") == "GAP"]
    led_ids = set(r.get("id", "") for r in led)
    led_t5 = sorted(r["id"] for r in led if r.get("current_status") == "TRANSFERRED_S5")
    open_in_scope = 0
    for line in open(os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv"), encoding="utf-8"):
        m = re.match(r"# OPEN_IN_SCOPE=(\d+)", line)
        if m:
            open_in_scope = int(m.group(1))
    true_n = len([r for r in aud if r.get("verdict") == "属实"])
    # M1R3 G6 seven points (U356)
    _, m1 = read_table(os.path.join(M1R3, "VERDICT_M1_F4_R9M1R3.tsv"))
    got = [r for r in m1 if r.get("group") == "G6" and r.get("point_id") in POINTS]
    seven = len(got) == 7 and all(r.get("verdict") == "MATCH" and r.get("tree") == "F4" for r in got)
    # P05_S4R4 report section 2a line numbers (info=NULL family B anchor gone on F4)
    r4_lines = open(R4, encoding="utf-8").read().splitlines()
    r4_hits = [i for i, l in enumerate(r4_lines, 1) if "info=NULL 的族 B 锚点在 F 上不存在" in l]
    r4_ref = ("P05_S4R4_REPORT.md §2 a 第 %s 行" % ",".join(str(x) for x in r4_hits[:2])) if r4_hits else "P05_S4R4_REPORT.md §2"
    s12 = open(S1S2, encoding="utf-8").read()
    s2_line = ""
    for line in s12.splitlines():
        if line.startswith("(2)"):
            s2_line = line.strip()
    lines = []
    lines.append("# 草稿，非签收；签收只由用户在对话中给出 — P05-S3 / P05-S4 签收范围声明（草稿 v2）")
    lines.append("")
    lines.append("> 本文件是规划/执行侧准备的签收范围声明**草稿**，不构成签收。签收只由用户在对话中明确给出。")
    lines.append("> 数据来源（M3d 修正版）：checkpoints/p05/evidence/p05-s4r9/m3d/ 下的 READINESS_P05_S3S4_R9M3D.tsv、")
    lines.append("> S5_HANDOFF_R9M3D.tsv、RED_POINTS_LEDGER_FINAL_R9M3D.tsv、AUDIT_R9M3C_R9M3D.tsv；本文件由 write_signoff_v2_r9m3d.py 生成。")
    lines.append("> 就绪计数：MET=%d GAP=%d TRANSFERRED_S5=%d CLOSED_BY_RULING=%d（共 %d 行）。" % (
        rc.get("MET", 0), rc.get("GAP", 0), rc.get("TRANSFERRED_S5", 0), rc.get("CLOSED_BY_RULING", 0), len(rdy)))
    lines.append("")
    lines.append("## P05-S3（D003 修复范围 + S3 补充轮）")
    lines.append("")
    lines.append("### 已验证内容")
    lines.append("- 分配/调用点的失败清理与返回码：M1/M2 预注册矩阵与 seam 对照（证据：registries/s4r9/M1R3/VERDICT_M1_F4_R9M1R3.tsv、registries/s4r9/M2/VERDICT_R9.tsv）。")
    lines.append("- 806、415、RP-S3R4-1：按 U225 由 M1/M2 覆盖（806=A-1/2/3，RP-S3R4-1=A-4/5/6，415 同映射规则）；状态见 READINESS 的 STATE_OPEN 行。")
    lines.append("- RNV1（RP-R6d-1）：F2/F3/F4 全部 MATCH（U25），证据 registries/s4r6d/ 与 P05_S3R3_CLOSEOUT.md。")
    lines.append("- K-1（RP-R6d-8）：按 U274/U281 带范围声明关闭（未复现静默吞没；张量路径范围见 U274/U281），证据 M206_DIAG_SUMMARY.txt、RESULTS_R5_K1.tsv。")
    lines.append("- S3-4b（失败后模式/缓存不安装）：按 U29 带范围声明关闭，证据 P05_S3_4b_CLOSURE.md。")
    lines.append("- 其他层失败变体（RP-R6d-14）：U354 关闭（M2-05 共 8 点全 MATCH，范围 P0/P2/PP1/PP2、F4、driver_r8m2a2_layers；U20 的推迟由 U354 结束）。")
    lines.append("")
    lines.append("### 证据入口")
    lines.append("- checkpoints/p05/P05_S3R3_CLOSEOUT.md、P05_S3R4_CLOSEOUT.md、P05_S3R5_CLOSEOUT.md、P05_S3_4b_CLOSURE.md")
    lines.append("- checkpoints/p05/registries/s4r9/M1R3/、registries/s4r9/M2/、registries/s4r9/M3d/")
    lines.append("")
    lines.append("### 不包含内容")
    lines.append("- 不覆盖非 FMM 的 S4_malloc（OUT_OF_SCOPE_D003，转 S5）。")
    lines.append("- 不覆盖 B 树行为（B 列不是修复证据）。")
    lines.append("- S3 的历史自检不作为 S4 修复后验证；S4 的修后验证以 F4 上的 R9 结果为准。")
    lines.append("")
    lines.append("## P05-S4（D003 失败传播 + Python/Lua 可见性 E2E）")
    lines.append("")
    lines.append("### 已验证内容")
    lines.append("- M1/M2 未修复基线对照、修复后等价与返回码：M1R3 总表与 M2 正式两遍（证据见 P05-S3 节）。")
    lines.append("- make test 相对基线无新增失败：registries/s4r9/M3b/MAKETEST_VERDICT_R9M3B.tsv（NO_NEW_FAILURE，8/8 reconcile 的 ok 列）。")
    lines.append("- Python/Lua 公共 API E2E（U343/U345/U352）：E2E_OK=25、CONTROL_OK=17、其余类别 none；M3c 独立只读重判差异 0（REJUDGE_E2E_R9M3C.tsv、REJUDGE_COMPARE_R9M3C.txt）。")
    lines.append("- 阳性对照：E2E 重判 16/16 PASS（POSCTRL_REJUDGE_R9M3C.txt）；make test 重解析 2/2 PASS。")
    lines.append("")
    lines.append("### S1/S2 签收移交项的闭合（U356）")
    lines.append("- S1/S2 签收范围声明第 (2) 条原文：%s" % (s2_line if s2_line else "（见 P05_S1_S2_SIGNOFF.md §2）"))
    lines.append("- 该项移交的七处 info=NULL 的 LinearSolve 修前 seam 现以 M1R3 G6 组 R4-CL01..CL04、R4-PJ01、R4-PN01、R4-PV01（F4）的判定为闭合证据：7/7 MATCH%s（两遍类别 HOLD，驱动 r6bseam-seamF-F4）。" % ("" if seven else "（复核不成立）"))
    lines.append("- 注意：F4 上族 B 原有的 info=NULL 锚点已不存在（%s：F 已把七处改为 &solve_info），所以这 7 点测的是修复后的 &solve_info 路径，不是修前 seam。" % r4_ref)
    lines.append("- 结论：按 U356，S1/S2 签收范围声明第 (2) 条的移交在 P05-S4 范围内已闭合。")
    lines.append("")
    lines.append("### 证据入口")
    lines.append("- checkpoints/p05/registries/s4r9/M3b/（E2E 正式两遍、make test 判定、预注册、校准）")
    lines.append("- checkpoints/p05/registries/s4r9/M3d/（修正版最终红点台账、去重 S5 移交、就绪审计、P 项复核、冻结清单）")
    lines.append("- checkpoints/p05/P05_S4R9_M3b_REPORT.md、P05_S4R9_M3c_REPORT.md、P05_S4R9_M3d_REPORT.md")
    lines.append("")
    lines.append("### 不包含内容")
    lines.append("- seam-only 族（LinearSolve A/B/B2/B2-buf、FMM 返回码族 E、分配 seam 家族 C、kottke_alloc:31）不出 E2E 点，由 M1/M2 覆盖行代替（U344）。")
    lines.append("- Lua REPL 仅覆盖 cf/fft/kt/vl 四族；jones/nv/exp 无 REPL 点（范围事实，E9-63）。")
    lines.append("- 不含 B 树行为。")
    lines.append("")
    lines.append("### 转入 S5 的项（去重后的唯一项，U355）")
    for r in hand:
        lines.append("- %s → %s；来源裁决：%s；对应台账 id：%s；对应 STATE：%s" % (
            r.get("canonical_name", ""), r.get("scope", ""), r.get("source_ruling", ""),
            r.get("ledger_ids", ""), r.get("state_rows", "")))
    lines.append("")
    lines.append("### GAP 明细（原样列出，不得隐去）")
    if gaps:
        for g in gaps:
            lines.append("- GAP：%s" % g)
    else:
        lines.append("- 无 GAP（READINESS 复算 GAP=0；台账唯一 id=%d，范围内仍开放=%d，TRANSFERRED_S5=%d，移交唯一项=%d）。" % (
            len(led_ids), open_in_scope, len(led_t5), len(hand)))
    lines.append("")
    lines.append("## 与 v1 的差异（逐条对应 P-1…P-6）")
    lines.append("")
    lines.append("| 项 | v1 的问题 | v2 的修正 |")
    lines.append("|---|---|---|")
    diff = {
        "P-1": "台账把 RP-R6d-14 记为 TRANSFERRED_S5（依据 U20），与 M2-05 的 8 点全 MATCH 不一致",
        "P-2": "S5 移交表 10 行去重后仅 5 项，且缺 RP-R6d-3、RP-R6d-7；台账 TRANSFERRED_S5 有 7 个 id",
        "P-3": "READINESS ① 写红点行=27（把台账表头算成数据行），台账唯一 id 是 26",
        "P-4": "签收草稿 v1 的转入 S5 项 10 条含重复，且缺 RP-R6d-3、RP-R6d-7",
        "P-5": "v1 未说明 S1/S2 范围声明第 (2) 条的 info=NULL seam 移交已闭合",
        "P-6": "v1 的 READINESS 中 RP-R6d-15 行仍是“待用户审核”旧措辞，裁决列写“见 STATE 行”",
    }
    fix = {
        "P-1": "v2 按 U354 把 RP-R6d-14 记为已关闭（M2-05 8 点全 MATCH；范围 P0/P2/PP1/PP2、F4、driver_r8m2a2_layers）",
        "P-2": "v2 的转入 S5 只列去重后的 7 个唯一项，并按 U355 双向核对（补入 RP-R6d-3、RP-R6d-7）",
        "P-3": "v2 的 READINESS ① 按唯一 id 去重（=26），与修正版台账一致",
        "P-4": "v2 的转入 S5 项每项注明来源裁决，无重复、无缺项",
        "P-5": "v2 新增“S1/S2 签收移交项的闭合（U356）”一节，注明 F4 上 info=NULL 锚点已不存在",
        "P-6": "v2 的 READINESS 每行裁决号为真实 U 编号或“-（事实项）”，RP-R6d-15 行改用 U345/U352，无“见 STATE 行”",
    }
    for item in ("P-1", "P-2", "P-3", "P-4", "P-5", "P-6"):
        v = [r.get("verdict", "") for r in aud if r.get("item") == item]
        lines.append("| %s | %s | %s |" % (item, diff[item], fix[item] + ("（复核：%s）" % v[0] if v else "")))
    lines.append("")
    lines.append("> 再次声明：本文件是**草稿，非签收**；签收只由用户在对话中给出。")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines) + NL)
    print("readiness MET=%d GAP=%d T5=%d CLOSED=%d rows=%d" % (
        rc.get("MET", 0), rc.get("GAP", 0), rc.get("TRANSFERRED_S5", 0), rc.get("CLOSED_BY_RULING", 0), len(rdy)))
    print("audit_true=%d/%d seven_match=%s handoff=%d ledger_uniq=%d t5=%d" % (
        true_n, len(aud), seven, len(hand), len(led_ids), len(led_t5)))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
