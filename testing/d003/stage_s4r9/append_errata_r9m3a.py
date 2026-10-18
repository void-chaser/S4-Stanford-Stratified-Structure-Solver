#!/usr/bin/env python3
# append_errata_r9m3a.py -- append E9-35..E9-44 to ERRATA_9.txt (J-1..J-6 of r9m1r4, plus the J-6 sub-items).
# usage: python3 -I -B testing/d003/stage_s4r9/append_errata_r9m3a.py ERRATA_9.txt AUDIT.tsv [BACKFILL.tsv]
# Guard: the current file must equal the start-gate byte length and sha256, and the last id must be E9-34.
import os, sys, hashlib

EXPECT_BYTES = 30931
EXPECT_SHA = "49add16f2343c92893fc500d25f3d37b6b1c4c76be5e7cb3eb891308037f5748"
EXPECT_LAST = "E9-34"


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def audit_refs(p):
    refs = {}
    if not os.path.isfile(p):
        return refs
    for line in open(p, encoding="utf-8"):
        f = line.rstrip("\n").split("\t")
        if len(f) >= 3 and f[0].startswith("J-"):
            refs[f[0]] = f[2]
    return refs


def main():
    errata_path = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/p05/registries/s4r9/ERRATA_9.txt"
    audit_path = sys.argv[2] if len(sys.argv) > 2 else ""
    backfill_path = sys.argv[3] if len(sys.argv) > 3 else ""
    refs = audit_refs(audit_path)
    old = open(errata_path, "rb").read()
    if len(old) != EXPECT_BYTES:
        print("HARD_STOP: bytes %d != %d" % (len(old), EXPECT_BYTES))
        return 2
    if sha256_bytes(old) != EXPECT_SHA:
        print("HARD_STOP: sha256 %s != %s" % (sha256_bytes(old), EXPECT_SHA))
        return 2
    import re
    ids = [m.group(1) for m in re.finditer(r"^(E9-\d+)", old.decode("utf-8"), re.M)]
    if not ids or ids[-1] != EXPECT_LAST:
        print("HARD_STOP: last id %s != %s" % (ids[-1] if ids else "none", EXPECT_LAST))
        return 2
    existing = set(ids)

    entries = [
        ("E9-35", "J-1",
         "r9m1r4 的阳性对照 POSCTRL_RECERT_R9M1R4.txt 无效：case3 把常量 sha256(b\"tampered_fact\") 与 EXPECTED_P1_SHA 相比、case4 把 158-1 与 158 相比，两者恒为真；case1/case2 只在内存里改字典，不读落盘的篡改副本；任务书 S-D 要求的篡改副本目录 m1r4/shakedown/posctrl 从未建立。",
         "阴阳性对照失效，r9m1r4 的复算逻辑实际未经任何篡改检验。",
         "按 U329 作废该对照；本轮以 posctrl_recert_r9m3a_v4.py 在 $EV/posctrl/<case>/ 写落盘篡改副本重做，结果见 POSCTRL_R9M3A.txt（4/4 PASS）。"),
        ("E9-36", "J-2",
         "r9m1r4 的“补做 r9m1r3 门禁断言”不完整：recert 的 target_scripts 只覆盖 5 个脚本，而 FROZEN_SCRIPTS_R9M1R3 按脚本计有 14 个；漏掉的 9 个中，events_r9m1r3.py 实际被调用 2 次、report_check_r9m1r3.py 实际被调用 3 次。",
         "r9m1r3 的收尾纪律违规（重复调用）未被补做断言检出，E9-32 的结论缺少门禁层面的证据。",
         "按 U330 由 backfill_full_r9m3a.py 对 14 个脚本逐一计数，结果见 BACKFILL_FULL_R9M1R3.tsv（events=2、report_check=3 记 FAIL）。"),
        ("E9-37", "J-3",
         "r9m1r4 的 AUDIT_R9M1R3_R9M1R4.tsv 对 H-5 记为“属实（物理82）”，而 m1r3 safe_run.log 中 gate_r9m1r3_v4.sh start _v5 的实际物理行号是 94；第 82 行是 heredoc 内容，不是该命令。",
         "审计表沿用了任务书给出的错误行号，未按原始文件复算，削弱了审计的可核证性。",
         "本轮由 audit_r9m1r4_r9m3a_v3.py 从原文件复算行号，写入 AUDIT_R9M1R4_R9M3A_v3.tsv 的 J-3 行；r9m1r4 已提交文件不改。"),
        ("E9-38", "J-4",
         "r9m1r4 在记录提交 (i) 之后改写了已提交文件 registries/s4r9/M1R4/UNLOGGED_WRITES_R9M1R3.tsv（786b150 提交、2f86aa1 再改），把 RULINGS.tsv 与 ERRATA_9.txt 两行的 mtime 从 03:44:43Z 改成 r9m1r4 自己 append 产生的 05:23:53Z，于是这两行被误记为 r9m1r3 的“未记录写入”。gate_check_r9m1r4_v3.py 的 COMMITTED_I 检查范围只含 testing/d003 与 briefs，不覆盖 registries，因而没有拦住。",
         "冻结期纪律被破坏（(i) 已提交文件被改写），且掩盖了真实的写入归属。",
         "按 U331 不再改写该文件；本轮由 unlogged_corr_r9m3a.py 输出 UNLOGGED_CORR_R9M3A.tsv，逐行给出两版本差异与按日志重新判定的归属（两行均归 r9m1r4）。本轮的 gate_check_r9m3a_v2.py 已在 COMMITTED_I 检查中加入 registries 范围。"),
        ("E9-39", "J-5",
         "r9m1r4 的 end 门禁设计缺陷：POST_I_CALL_COUNT_FINALIZE 期望 1，而 finalize 在门禁之后执行、门禁时刻应为 0；EVENTS 锚点取“首个 end 匹配”，命中的是试跑行而不是正式门禁行；shakedown 的两次 end 试跑都是 COMMIT_I_PRESENT=missing，POST_I 块从未执行；EVENTS_R9M1R4.tsv 的 54 行覆盖到第 56 行，第 57 行（sha_sums）未覆盖，报告附录 A.2 的“覆盖门禁前全部日志”与事实不符。",
         "end 门禁未能对收尾顺序与事件覆盖提供有效核验，试跑期的 POST_I 断言空转。",
         "本轮 gate_check_r9m3a_v2.py 重写为：冻结脚本各 1 次（gate 自身按门禁时刻计入）、EVENTS 锚点取 (i) 之后最后一次 events 调用行、events 行集合由冻结逻辑重算比对、截断哈希行号等于 sha_sums 调用行；并允许 --commit-i 在试跑期模拟 (i) 使 POST_I 块真正执行。"),
        ("E9-40", "J-6",
         "r9m1r4 的 report_check 在禁用词检查处命中报告正文里的“不询问是否签收”而提前退出，第 3 步数字核对没有执行，报告因此未被完整检查。",
         "收尾质量检查空转，报告与台账的一致性缺少机器核验。",
         "本轮 report_check_r9m3a.py 的禁用词检查改为逐行判别否定式（不把“不询问…”当作违规），并要求第 3 步数字核对必须执行且在输出中留痕。"),
        ("E9-41", "J-6",
         "r9m1r4 的 STATE.md 为 8480 字节，超过任务书规定的 8192 字节。",
         "STATE 超出预算，历史行未按要求压缩。",
         "按 U332 项四由本轮把 STATE 压到 <= 8192 字节，并由 end 门禁断言 STATE_BYTES_LE_8192。"),
        ("E9-42", "J-6",
         "r9m1r4 的报告正文 §9 写“需用户裁决：无”，与同一文件附录 A.3 列出的 4 项矛盾。",
         "正文与附录对同一事实给出相反结论。",
         "本轮报告把“需用户裁决”集中写在正文一节，附录只做补充，且不再出现与正文相反的空结论。"),
        ("E9-43", "J-6",
         "r9m1r4 的报告 §10.1 列出 13 项小表，registries/s4r9/M1R4/SHA256SUMS.txt 只有 11 项：EVENTS_R9M1R4.tsv 与失败的初版 GATE_R9M1R4_start.txt 未进入 registries。",
         "报告交付物清单与实际上交清单不一致，交付物不可完整复核。",
         "本轮 copy_registries_r9m3a.py 先复制再逐项比对 sha256，并写 registries/s4r9/M3a/SHA256SUMS.txt；end 门禁第 11 项由脚本解析报告“交付物”一节与清单项数比对。"),
        ("E9-44", "J-6",
         "r9m1r4 的报告 §1 写开工门禁“41 项全数 PASS”，未在同一节说明初版 start 门禁 FAILS=1（M1R2_SUMS_34）。",
         "报告只披露成功的一版门禁，省略了失败的一版，读者无法还原真实过程。",
         "本轮报告的门禁一节同时列出试跑版与正式版结果（含本轮的崩溃版 gate_check_r9m3a.py 与其 v2 修正），事件表登记全部重跑。"),
    ]

    out = old
    if not out.endswith(b"\n"):
        out += b"\n"
    added = []
    for eid, jitem, fact, impact, action in entries:
        if eid in existing:
            print("HARD_STOP: %s already present" % eid)
            return 2
        ref = refs.get(jitem, "")
        lines = ["", eid, "- 事实：" + fact]
        if jitem == "J-2" and backfill_path:
            lines.append("- 证据文件与行号：%s；%s；%s" % (ref, backfill_path, errata_evidence_extra(jitem)))
        else:
            lines.append("- 证据文件与行号：" + ref if ref else "- 证据文件与行号：见本报告与 AUDIT_R9M1R4_R9M3A_v3.tsv")
        lines.append("- 影响范围：" + impact)
        lines.append("- 处理方式：" + action)
        block = "\n".join(lines) + "\n"
        out += block.encode("utf-8")
        added.append(eid)

    with open(errata_path, "wb") as fh:
        fh.write(out)
    print("APPENDED %d errata: %s" % (len(added), ",".join(added)))
    print("BEFORE bytes=%d sha=%s" % (len(old), sha256_bytes(old)))
    print("AFTER  bytes=%d sha=%s" % (len(out), sha256_bytes(out)))
    print("PREFIX_PRESERVED=%s" % (out.startswith(old),))
    return 0


def errata_evidence_extra(jitem):
    if jitem == "J-2":
        return "checkpoints/p05/evidence/p05-s4r9/m1r3/safe_run.log:L155,L156,L157,L158,L160,L169"
    return ""


if __name__ == "__main__":
    sys.exit(main())
