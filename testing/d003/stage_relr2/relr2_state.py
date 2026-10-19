#!/usr/bin/env python3
# relr2_state.py -- P05 delivery round REL-R2: entry-document sync of checkpoints/p05/STATE.md only
# (task brief section 6).  Edits, in this order and nothing else:
#   section 1: the '当前轮次' row becomes REL-R2;
#   section 2: the REL-R1 row gains the SUMMARY_RELR1.txt key numbers; one REL-R2 row is appended;
#   section 4: one REL-R2 evidence-location bullet is appended;
#   footer: one provenance line is appended.
# It never pre-writes a gate result (the only gate reference is 'appendix C'), and a second invocation
# refuses to duplicate anything.  AGENTS.md / PROJECT_ROADMAP.md / ISSUE_REGISTRY.md are NOT touched.
import os, sys, hashlib, datetime

REPO = os.getcwd()
P05 = os.path.join(REPO, "checkpoints/p05")
STATE = os.path.join(P05, "STATE.md")
SUM = os.path.join(REPO, "checkpoints/p05/registries/rel-r1/SUMMARY_RELR1.txt")
MAKETEST_VERDICT = os.path.join(REPO, "checkpoints/p05/registries/rel-r1/MAKETEST_VERDICT_RELR1.tsv")
TAB = chr(9)
NL = chr(10)
MARK = "P05_RELR2_REPORT.md"
REL1_NUMBERS = ["SAME", "BOTH_FAIL", "SKIP_DECLARED", "NEW_FAIL", "DIFF", "FLAKY"]


def summary_numbers():
    d = {}
    for line in open(SUM, encoding="utf-8"):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            d[k] = v
    missing = [k for k in REL1_NUMBERS if k not in d]
    if missing:
        raise SystemExit("HARD_STOP missing keys in SUMMARY_RELR1.txt: " + ",".join(missing))
    # unit_count is not in SUMMARY_RELR1.txt; take it from the REL-R1 make-test verdict table by key name.
    mt = {}
    for line in open(MAKETEST_VERDICT, encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.rstrip(NL).split(TAB)
        if len(f) >= 2:
            mt[f[0]] = f[1]
    if "unit_count" not in mt:
        raise SystemExit("HARD_STOP missing unit_count in MAKETEST_VERDICT_RELR1.tsv")
    d["UNIT_COUNT"] = mt["unit_count"]
    return d


def main():
    src = open(STATE, encoding="utf-8").read()
    if MARK in src:
        print("HARD_STOP STATE.md already mentions REL-R2; refusing to duplicate")
        return 2
    d = summary_numbers()
    rel1_nums = ("SAME=%s；BOTH_FAIL=%s（均为既有失败）；SKIP_DECLARED=%s；NEW_FAIL=%s；DIFF=%s；"
                 "FLAKY=%s；unit_count=%s" % (d["SAME"], d["BOTH_FAIL"], d["SKIP_DECLARED"], d["NEW_FAIL"],
                                              d["DIFF"], d["FLAKY"], d["UNIT_COUNT"]))
    lines = src.split(NL)
    out = []
    done = {"cur": False, "rel1": False, "rel2": False, "ev": False}
    sec = 0
    for line in lines:
        if line.startswith("## "):
            sec = 1 if line.startswith("## 1") else (2 if line.startswith("## 2") else
                                                    (4 if line.startswith("## 4") else 3))
        if sec == 1 and line.startswith("| 当前轮次 |") and not done["cur"]:
            out.append("| 当前轮次 | P05 交付轮 REL-R2（rel-r2：本地分支整理与上传前审查；不是 P05 新阶段，"
                       "S1–S5 与 REL-R1 历史不改；门禁结果见 P05_RELR2_REPORT.md 附录 C） |")
            done["cur"] = True
            continue
        if sec == 1 and line.startswith("| P05 交付轮 |") and "REL-R1" in line:
            out.append("| P05 交付轮 | REL-R1（rel-r1；修复后完整原有功能非破坏性验证；门禁结果见 "
                       "P05_RELR1_REPORT.md 附录 C）与 REL-R2（rel-r2；产品分支构建与上传前审查；"
                       "门禁结果见 P05_RELR2_REPORT.md 附录 C） |")
            continue
        if sec == 2 and line.startswith("| REL-R1 |") and not done["rel1"]:
            cells = line.split(" | ")
            # cells: ['| REL-R1', '<numbers>', '<reports> |']
            if len(cells) != 3:
                raise SystemExit("HARD_STOP unexpected REL-R1 row shape")
            out.append("| REL-R1 | P05 交付轮（rel-r1）：修复后完整原有功能非破坏性验证（与 B 对照）；"
                       "关键计数 %s；各类别计数与 11 个既有失败例外清单见报告正文，门禁结果见报告附录 C | "
                       "P05_RELR1_REPORT.md；registries/rel-r1/ |" % rel1_nums)
            done["rel1"] = True
            out.append("| REL-R2 | P05 交付轮（rel-r2）：产品分支 p05/d003-fft-error-propagation 于独立克隆构建"
                       "（2 个提交，HEAD 8e4c014，S4 树 589e15eb；仅新增 doc/P05_D003_SUMMARY.md）；"
                       "V1–V6 全部与预注册一致（V5 只记录：build/S4 与 libS4.a 与 REL-R1 F4 逐字节 SAME）；"
                       "免注入可达路径未找到，产品分支不含 D003 专用测试；两个附注标签与分支引用已建（待 REL-R3 推送）；"
                       "上传前体积审查 A 新增 blob 3065 个共 46.1 MiB、无 ≥50 MB/≥100 MB blob，P 11 个共 0.3 MiB；"
                       "敏感信息命中（只记录不改写）A：/srv/nvme/ 5789 次/155 文件、/home/ 24 次/11 文件、用户名 26 次、"
                       "邮箱 12 次，P：仅上游作者邮箱 10 次；证据目录 11.38 GiB；门禁结果见报告附录 C | "
                       "P05_RELR2_REPORT.md；registries/rel-r2/ |")
            done["rel2"] = True
            continue
        out.append(line)
        if sec == 2 and line.startswith("| REL-R1 |") and not done["rel2"]:
            out.append("| REL-R2 | P05 交付轮（rel-r2）：产品分支 p05/d003-fft-error-propagation 于独立克隆构建"
                       "（2 个提交，HEAD 8e4c014，S4 树 589e15eb；仅新增 doc/P05_D003_SUMMARY.md）；"
                       "V1–V6 全部与预注册一致（V5 只记录：build/S4 与 libS4.a 与 REL-R1 F4 逐字节 SAME）；"
                       "免注入可达路径未找到，产品分支不含 D003 专用测试；两个附注标签与分支引用已建（待 REL-R3 推送）；"
                       "上传前体积审查 A 新增 blob 3065 个共 46.1 MiB、无 ≥50 MB/≥100 MB blob，P 11 个共 0.3 MiB；"
                       "敏感信息命中（只记录不改写）A：/srv/nvme/ 5789 次/155 文件、/home/ 24 次/11 文件、用户名 26 次、"
                       "邮箱 12 次，P：仅上游作者邮箱 10 次；证据目录 11.38 GiB；门禁结果见报告附录 C | "
                       "P05_RELR2_REPORT.md；registries/rel-r2/ |")
            done["rel2"] = True
    if done["ev"] is False:
        # append the evidence bullet at the end of section 4 (before the generator footer)
        marker = None
        for i, line in enumerate(out):
            if line.startswith("（本文件由 s5r7_state.py"):
                marker = i
                break
        bullet = ("- **P05 交付轮 REL-R2（rel-r2）**：证据 checkpoints/p05/evidence/p05-rel-r2/"
                  "（SHA256SUMS.txt；含产品分支独立克隆 prod/ 与验证克隆 verifyclone/，均不入 git）；"
                  "小表 checkpoints/p05/registries/rel-r2/；报告 P05_RELR2_REPORT.md（门禁结果见附录 C）；"
                  "产品分支引用 p05/d003-fft-error-propagation；标签 p05-signed-20261019、p05-rel-r1-20261019。")
        if marker is None:
            out.append(bullet)
        else:
            out.insert(marker, bullet)
        done["ev"] = True
    if not all(done.values()):
        print("HARD_STOP anchors not found: " + repr(done))
        return 2
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out.append("")
    out.append("（REL-R2 行由 relr2_state.py 于 %s 追加；S1–S5 与 REL-R1 的历史数字未改，只补 REL-R1 行计数）" % utc)
    data = NL.join(out)
    if "P05-" + "S6" in data:
        raise SystemExit("HARD_STOP STATE.md would contain a P05-S6 mention")
    open(STATE, "w", encoding="utf-8").write(data)
    print("STATE.md updated; bytes=%d" % len(data.encode("utf-8")))
    print("SHA256=" + hashlib.sha256(open(STATE, "rb").read()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
