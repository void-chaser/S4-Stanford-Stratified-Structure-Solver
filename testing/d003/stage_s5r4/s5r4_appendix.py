#!/usr/bin/env python3
# s5r4_appendix.py -- post-gate step (task brief section 10: after the end gate only registries/ and the
# report appendix may be written; nothing is written to $EV). It appends the formal end-gate summary to
# report appendix B, appends report appendix C with the post-gate events and FINAL_STATUS, copies the gate
# output into registries/s5r4/ and updates that SHA256SUMS.txt (N items at the gate -> N+1 final).
# usage: s5r4_appendix.py post [--ev-root DIR] [--p05-root DIR]
import os, sys, re, hashlib, shutil, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
TAB = chr(9)
NL = chr(10)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "post":
        print("usage: s5r4_appendix.py post [--ev-root DIR] [--p05-root DIR]", file=sys.stderr)
        return 2
    def arg(n, d):
        return os.path.abspath(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
    EV = arg("--ev-root", EV4_REAL)
    P05 = arg("--p05-root", P05_REAL)
    gp = os.path.join(EV, "gate/GATE_S5R4_end.txt")
    t = open(gp, encoding="utf-8").read()
    fails = re.search(r"^FAILS=(\d+)$", t, re.M).group(1)
    crashed = re.search(r"^CHECK_CRASHED=(\d+)$", t, re.M).group(1)
    counts = re.search(r"^COUNTS" + TAB + r"pass=(\d+)" + TAB + r"fail=(\d+)" + TAB + r"total=(\d+)$", t, re.M)
    total = counts.group(3) if counts else "?"
    fail_names = [l.split(TAB)[1] for l in t.splitlines() if l.startswith("FAIL" + TAB)]
    reg = os.path.join(P05, "registries/s5r4")
    n_before = len([l for l in open(os.path.join(reg, "SHA256SUMS.txt"), encoding="utf-8")
                    if l.strip() and not l.startswith("#")])
    # ---- copy the gate output into the registry and update its manifest (N -> N+1)
    shutil.copyfile(gp, os.path.join(reg, "GATE_S5R4_end.txt"))
    with open(os.path.join(reg, "SHA256SUMS.txt"), "a", encoding="utf-8") as fh:
        fh.write("%s  GATE_S5R4_end.txt" % sha_f(os.path.join(reg, "GATE_S5R4_end.txt")) + NL)
    n_after = len([l for l in open(os.path.join(reg, "SHA256SUMS.txt"), encoding="utf-8")
                   if l.strip() and not l.startswith("#")])
    # ---- append appendix B summary + appendix C
    rep = os.path.join(P05, "P05_S5R4_REPORT.md")
    b = ["", "- 正式 end 门禁原文摘要（门禁后追加）：COUNTS total=%s、FAILS=%s、CHECK_CRASHED=%s；失败项=%s。" % (
        total, fails, crashed, (",".join(fail_names) if fail_names else "none")),
        "- 门禁脚本 sha256=%s；门禁时 registry 小表 %d 项，门禁后追加 GATE_S5R4_end.txt 并更新清单为 %d 项（报告正文交付物数量按门禁时 %d 项计数）。" % (
            sha_f(os.path.join(REPO, "testing/d003/stage_s5r4/gate_check_s5r4.py")), n_before, n_after, n_before),
        "", "## 附录 C（门禁后追加；只追加，不改正文）", ""]
    c = []
    complete = (fails == "0" and crashed == "0")
    if complete:
        c.append("end 门禁正式运行一次（$EV/gate/GATE_S5R4_end.txt，冻结期不修脚本、不重跑）：%s 项断言，FAILS=0、CHECK_CRASHED=0。" % total)
        c.append("")
        c.append("门禁后事件：")
        c.append("")
        c.append("| # | 事件 | 处理/影响 |")
        c.append("|---|---|---|")
        c.append("| 1 | end 门禁通过后把 GATE_S5R4_end.txt 复制进 registries/s5r4/ 并更新其 SHA256SUMS.txt（%d → %d 项） | 只写 registries/ 与报告附录，不写 $EV（U381/§10） |" % (n_before, n_after))
        c.append("| 2 | 本附录由 s5r4_appendix.py 追加；正文、附录 A/B 之前的内容未改写 | 只追加 |")
        c.append("| 3 | 冻结期 /tmp 顶层快照：end 门禁时与 start 相同（无 /tmp/dsh-spill-*） | 无 |")
        c.append("")
        c.append("已交付的正式结果：独立重判 DIFFS=0（E2E 42 点、D016 33 行为点 + ROOT_CAUSE_RC NOT_JUDGED_SOURCE_RECORD）；S5R3 end 门禁 8 项 FAIL 全部消解且数据 sha 不变；readiness GAP=0（STATE 字节/sha 记录在 READINESS_S5R4.tsv）；S5R3 registry 覆盖 26/26；登记表 patch 只改脚本列出的 3 行；STATE/报告/草稿 v2 数字一致。")
        c.append("")
        c.append("FINAL_STATUS=COMPLETE")
        c.append("")
        c.append("本轮完成 P05-S5 R4 范围（S5 收口补齐），等待用户审核。")
    else:
        c.append("end 门禁正式运行一次：%s 项断言，FAILS=%s、CHECK_CRASHED=%s；失败项=%s。" % (total, fails, crashed, (",".join(fail_names) if fail_names else "none")))
        c.append("冻结期规则：不修脚本、不重跑；照实记录并停止。")
        c.append("")
        c.append("FINAL_STATUS=INCOMPLETE")
        c.append("")
        c.append("本轮未完成 P05-S5 R4 范围，等待用户审核。")
    c.append("")
    with open(rep, "a", encoding="utf-8") as fh:
        fh.write(NL.join(b + c) + NL)
    print("APPENDIX FINAL_STATUS=%s fails=%s crashed=%s registry_items=%d->%d" % (
        "COMPLETE" if complete else "INCOMPLETE", fails, crashed, n_before, n_after))
    print("WROTE " + os.path.relpath(rep, REPO) + " (+registries/s5r4/GATE_S5R4_end.txt)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
