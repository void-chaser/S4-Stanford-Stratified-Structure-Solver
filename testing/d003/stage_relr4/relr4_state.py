#!/usr/bin/env python3
# relr4_state.py -- P05 delivery round REL-R4: entry-document sync of checkpoints/p05/STATE.md only.
# Edits, in this order and nothing else:
#   section 1: the '当前轮次' row becomes REL-R4; the 'P05 交付轮' row gains REL-R4;
#   section 2: one REL-R4 row is appended after the REL-R3 row;
#   section 4: one REL-R4 evidence-location bullet is appended;
#   footer: one provenance line is appended.
# It never pre-writes a gate result (the only gate reference is 'appendix C'), and a second invocation
# refuses to duplicate anything.  S1-S5, REL-R1, REL-R2 and REL-R3 historical numbers are not changed.
import os, sys, hashlib, datetime

REPO = os.getcwd()
P05 = os.path.join(REPO, "checkpoints/p05")
STATE = os.path.join(P05, "STATE.md")
SUM = os.path.join(REPO, "checkpoints/p05/registries/rel-r4/SUMMARY_RELR4.txt")
NL = chr(10)
MARK = "P05_RELR4_REPORT.md"
KEYS = ["REGRESSION_TOTAL", "IMPROVED" if False else "T1_U_VS_F4_IMPROVED", "T1_U_VS_F4_BOTH_FAIL",
        "T1_B_VS_F4_SAME", "T1_B_VS_F4_BOTH_FAIL", "T1_U_VS_F4_DIFF_WITHIN_TOL",
        "T1_U_VS_F4_DIFF_ATTRIBUTED", "T1_U_VS_F4_REGRESSION", "T1_U_VS_F4_FLAKY",
        "T3_WITH_MPI_BANNER", "T3_MPI_COMPARE_OK", "T3_MPI_COMPARE_TOTAL", "UNIT_COUNT",
        "T4_SPEC_REF_PASS", "T4_POSITIVE_CONTROL_PASS", "T2_REF_PASS", "T2_REF_TOTAL"]


def summary_numbers():
    d = {}
    for line in open(SUM, encoding="utf-8"):
        if "=" in line and not line.startswith("#"):
            k, v = line.strip().split("=", 1)
            d[k] = v
    missing = [k for k in KEYS if k not in d]
    if missing:
        raise SystemExit("HARD_STOP missing keys in SUMMARY_RELR4.txt: " + ",".join(missing))
    return d


def main():
    src = open(STATE, encoding="utf-8").read()
    if MARK in src:
        print("HARD_STOP STATE.md already mentions REL-R4; refusing to duplicate")
        return 2
    d = summary_numbers()
    row = ("| REL-R4 | P05 交付轮（rel-r4）：原版 S4 U（上游 7fd00a2）/ 当前 F4 / 未修复基线 B 三方对照 + MPI + "
           "C API 对照；U/B/F4 各为独立克隆（U 网络克隆，B/F4 本地 --revision 克隆）；C API 程序 "
           "capi_fig12_relr4.c；关键计数 T1 SAME=%s IMPROVED=%s BOTH_FAIL=%s REGRESSION=%s FLAKY=%s "
           "DIFF_WITHIN_TOL=%s DIFF_ATTRIBUTED=%s；B-vs-F4 复现 SAME=%s BOTH_FAIL=%s；T2 参考 %s/%s；"
           "MPI 三树均 With MPI support=%s、MPI 一致性 %s/%s；T4 spec 参考 PASS=%s、阳性对照 PASS=%s；"
           "unit_count=%s；门禁结果见报告附录 C | P05_RELR4_REPORT.md；registries/rel-r4/ |" % (
               d["T1_U_VS_F4_SAME"] if "T1_U_VS_F4_SAME" in d else "?", d["T1_U_VS_F4_IMPROVED"],
               d["T1_U_VS_F4_BOTH_FAIL"], d["T1_U_VS_F4_REGRESSION"], d["T1_U_VS_F4_FLAKY"],
               d["T1_U_VS_F4_DIFF_WITHIN_TOL"], d["T1_U_VS_F4_DIFF_ATTRIBUTED"],
               d["T1_B_VS_F4_SAME"], d["T1_B_VS_F4_BOTH_FAIL"], d["T2_REF_PASS"], d["T2_REF_TOTAL"],
               d["T3_WITH_MPI_BANNER"], d["T3_MPI_COMPARE_OK"], d["T3_MPI_COMPARE_TOTAL"],
               d["T4_SPEC_REF_PASS"], d["T4_POSITIVE_CONTROL_PASS"], d["UNIT_COUNT"]))
    lines = src.split(NL)
    out = []
    done = {"cur": False, "delivery": False, "row": False}
    sec = 0
    for line in lines:
        if line.startswith("## "):
            sec = 1 if line.startswith("## 1") else (2 if line.startswith("## 2") else
                                                    (4 if line.startswith("## 4") else 3))
        if sec == 1 and line.startswith("| 当前轮次 |") and not done["cur"]:
            out.append("| 当前轮次 | P05 交付轮 REL-R4（rel-r4：原版 S4 / 当前三方对照 + MPI + C API 对照；"
                       "不是 P05 新阶段，S1–S5、REL-R1、REL-R2、REL-R3 历史不改；门禁结果见 "
                       "P05_RELR4_REPORT.md 附录 C） |")
            done["cur"] = True
            continue
        if sec == 1 and line.startswith("| P05 交付轮 |") and not done["delivery"]:
            out.append(line.rstrip(" |").rstrip() + "；REL-R4（rel-r4；原版 S4 / 当前三方对照 + MPI + C API "
                       "对照；门禁结果见 P05_RELR4_REPORT.md 附录 C） |")
            done["delivery"] = True
            continue
        out.append(line)
        if sec == 2 and line.startswith("| REL-R3 |") and not done["row"]:
            out.append(row)
            done["row"] = True
    if not all(done.values()):
        print("HARD_STOP anchors not found: " + repr(done))
        return 2
    # evidence bullet at the end of section 4
    bullet = ("- **P05 交付轮 REL-R4（rel-r4）**：证据 checkpoints/p05/evidence/p05-rel-r4/"
              "（SHA256SUMS.txt；含上游 U 克隆 upstream/S4 与 B/F4 独立克隆 trees/，均不入 git）；"
              "小表 checkpoints/p05/registries/rel-r4/；报告 P05_RELR4_REPORT.md（门禁结果见附录 C）。")
    marker = None
    for i, line in enumerate(out):
        if line.startswith("（REL-R3 行由 relr3_state.py"):
            marker = i + 1
            break
    if marker is None:
        out.append(bullet)
    else:
        out.insert(marker, bullet)
    utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out.append("")
    out.append("（REL-R4 行由 relr4_state.py 于 %s 追加；S1–S5、REL-R1、REL-R2、REL-R3 的历史数字未改）" % utc)
    data = NL.join(out)
    if "P05-" + "S6" in data:
        raise SystemExit("HARD_STOP STATE.md would contain a P05-S6 mention")
    open(STATE, "w", encoding="utf-8").write(data)
    print("STATE.md updated; bytes=%d" % len(data.encode("utf-8")))
    print("SHA256=" + hashlib.sha256(open(STATE, "rb").read()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
