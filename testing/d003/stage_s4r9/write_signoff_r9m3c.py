#!/usr/bin/env python3
# write_signoff_r9m3c.py -- write the P05-S3/P05-S4 signoff-scope DRAFT from the readiness audit and the S5 handoff.
# The title and the first line say 草稿，非签收；签收只由用户在对话中给出. New file (r9m3c).
import os, sys
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
RDY = os.path.join(EV, "READINESS_P05_S3S4_R9M3C.tsv")
HAND = os.path.join(EV, "S5_HANDOFF_R9M3C.tsv")
OUT = os.path.join(REPO, "checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT.md")
TAB = chr(9)
NL = chr(10)


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
        rows.append(dict(zip(hdr, f)))
    return rows


def main():
    rows = read_table(RDY)
    hand = read_table(HAND)
    cnt = {}
    for r in rows:
        cnt[r.get("status", "?")] = cnt.get(r.get("status", "?"), 0) + 1
    gaps = [r for r in rows if r.get("status") == "GAP"]
    lines = []
    lines.append("# 草稿，非签收；签收只由用户在对话中给出 — P05-S3 / P05-S4 签收范围声明（草稿）")
    lines.append("")
    lines.append("> 本文件是规划/执行侧准备的签收范围声明草稿，不构成签收。签收只由用户在对话中明确给出。")
    lines.append("> 数据来源：checkpoints/p05/evidence/p05-s4r9/m3c/READINESS_P05_S3S4_R9M3C.tsv（只读复算）与 S5_HANDOFF_R9M3C.tsv。")
    lines.append("> 就绪计数：MET=%d GAP=%d TRANSFERRED_S5=%d CLOSED_BY_RULING=%d（共 %d 行）。" % (
        cnt.get("MET", 0), cnt.get("GAP", 0), cnt.get("TRANSFERRED_S5", 0), cnt.get("CLOSED_BY_RULING", 0), len(rows)))
    lines.append("")
    lines.append("## P05-S3（D003 修复范围 + S3 补充轮）")
    lines.append("")
    lines.append("### 已验证内容")
    lines.append("- 分配/调用点的失败清理与返回码：M1/M2 预注册矩阵与 seam 对照（证据：registries/s4r9/M1R3/VERDICT_M1_F4_R9M1R3.tsv、registries/s4r9/M2/VERDICT_R9.tsv、registries/s4r9/M1R3/POSCTRL_M1_R9M1R3.txt）。")
    lines.append("- 失败后模式/缓存不安装（S3-4b）：按 U29 带范围声明关闭（证据：P05_S3_4b_CLOSURE.md）。")
    lines.append("- I2 注释与 S4_internal.h:263 措辞：按 U8/U11/U31 关闭（证据：F2/F3/F4 树与 M1R3 判定）。")
    lines.append("")
    lines.append("### 证据入口")
    lines.append("- checkpoints/p05/P05_S3R3_CLOSEOUT.md、P05_S3R4_CLOSEOUT.md、P05_S3R5_CLOSEOUT.md、P05_S3_4b_CLOSURE.md")
    lines.append("- checkpoints/p05/registries/s4r9/M1R3/、registries/s4r9/M2/")
    lines.append("")
    lines.append("### 不包含内容")
    lines.append("- 不覆盖非 FMM 的 S4_malloc（OUT_OF_SCOPE_D003，转 S5）。")
    lines.append("- 不覆盖 B 树行为（B 列不是修复证据）。")
    lines.append("- S3 的历史自检不作为 S4 修复后验证；S4 的修后验证以 F4 上的 R9 结果为准。")
    lines.append("")
    lines.append("## P05-S4（D003 失败传播 + Python/Lua 可见性 E2E）")
    lines.append("")
    lines.append("### 已验证内容")
    lines.append("- M1/M2 未修复基线对照、修复后等价与返回码：M1R3 总表与 M2 正式两遍（证据见上）。")
    lines.append("- make test 相对基线无新增失败：registries/s4r9/M3b/MAKETEST_VERDICT_R9M3B.tsv（NO_NEW_FAILURE，8/8 reconcile 的 ok 列）。")
    lines.append("- Python/Lua 公共 API E2E（U343/U345）：E2E_OK=25、CONTROL_OK=17、其余类别 none；本轮独立只读重判差异 0（REJUDGE_E2E_R9M3C.tsv、REJUDGE_COMPARE_R9M3C.txt）。")
    lines.append("- 阳性对照：E2E 重判 16/16 PASS（POSCTRL_REJUDGE_R9M3C.txt）；make test 重解析 2/2 PASS。")
    lines.append("")
    lines.append("### 证据入口")
    lines.append("- checkpoints/p05/registries/s4r9/M3b/（E2E 正式两遍、make test 判定、预注册、校准）")
    lines.append("- checkpoints/p05/registries/s4r9/M3c/（本轮独立复核、复验、就绪审计、最终红点台账、冻结清单）")
    lines.append("- checkpoints/p05/P05_S4R9_M3b_REPORT.md、P05_S4R9_M3c_REPORT.md")
    lines.append("")
    lines.append("### 不包含内容")
    lines.append("- seam-only 族（LinearSolve A/B/B2/B2-buf、FMM 返回码族 E、分配 seam 家族 C、kottke_alloc:31）不出 E2E 点，由 M1/M2 覆盖行代替（U344）。")
    lines.append("- Lua REPL 仅覆盖 cf/fft/kt/vl 四族；jones/nv/exp 无 REPL 点（范围事实，E9-63）。")
    lines.append("- 不含 B 树行为。")
    lines.append("")
    lines.append("### 转入 S5 的项")
    for r in hand:
        lines.append("- %s → %s（来源：%s）" % (r.get("item", "?"), r.get("transfer_scope", "?"), r.get("source", "?")))
    lines.append("")
    lines.append("### GAP 明细（原样列出，不得隐去）")
    if gaps:
        for r in gaps:
            lines.append("- %s：%s（%s）" % (r.get("group"), r.get("item"), r.get("recomputed", "")))
    else:
        lines.append("- 无 GAP（READINESS 复算 GAP=0）。")
    lines.append("")
    lines.append("> 再次声明：本文件是草稿，非签收；签收只由用户在对话中给出。")
    lines.append("")
    open(OUT, "w", encoding="utf-8").write(NL.join(lines))
    print("WROTE " + OUT + " bytes=%d" % os.path.getsize(OUT))
    print("COUNTS " + str(sorted(cnt.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
