#!/usr/bin/env python3
# update_state_r9m3d.py -- update checkpoints/p05/STATE.md for round r9m3d (U358): baseline HEAD, current round,
# the key-number row, the open-question rows for U354 and U356, the RP-R6d-15 wording (U352), the closing note and
# the evidence-location entry. Every anchor must occur exactly once; the old bytes/sha are asserted first. New file
# (r9m3d). usage: update_state_r9m3d.py [STATE.md]
import os, sys, hashlib
REPO = os.getcwd()
STATE = os.path.join(REPO, "checkpoints/p05/STATE.md")
NL = chr(10)
EXPECTED_SHA = "95ea14b6caa33692bc22b7fa644c0583dfd3bd90eef4cab51f6b133b12474f67"
EXPECTED_BYTES = 5908
A1 = "| 本轮开工基线 HEAD（r9m3c） | " + chr(96) + "01fd3c0e4cf436aef5780486c8b8327c25849713" + chr(96) + " |"
B1 = "| 本轮开工基线 HEAD（r9m3d） | " + chr(96) + "c4f67071e80f8dd573f3653c04250708e7339b7f" + chr(96) + " |"
A2 = ("| 当前轮次 | **P05-S4 R9 M3c（r9m3c）**：U343–U350、E9-58–E9-66 落账 + M3b 独立只读复核（DIFFS=0）+ "
      "签收就绪审计（MET=14 GAP=0 TRANSFERRED_S5=5）+ 最终红点台账 + 签收范围声明草稿 |")
B2 = ("| 当前轮次 | **P05-S4 R9 M3d（r9m3d）**：U351–U358 落账 + §3 P-1…P-6 复核（6/6 属实）+ E9-67–E9-73 勘误 + "
      "修正版最终红点台账（唯一 id 26，TRANSFERRED_S5=6）+ 去重 S5 移交（唯一项 7）+ 签收范围声明草稿 v2 |")
A3 = ("| S4R9 M3c | U343–U350、E9-58–E9-66；M3b 独立复核 DIFFS=0；READINESS MET=14 GAP=0 TRANSFERRED_S5=5；"
      "红点范围内开放 0；S5 移交 10 项 | " + chr(96) + "P05_S4R9_M3c_REPORT.md" + chr(96) + " |")
B3 = A3 + NL + ("| S4R9 M3d | U351–U358、E9-67–E9-73；§3 P-1…P-6 复核 6/6 属实；红点唯一 id 26、TRANSFERRED_S5=6；"
                "去重 S5 移交 7 项；签收草稿 v2 | " + chr(96) + "P05_S4R9_M3d_REPORT.md" + chr(96) + " |")
A4 = "| RP-R8-M2c-1/1b | U350 确认按 U304 关闭（18 点全 MATCH） | 关闭 | " + chr(96) + "P05_S4R9_M2c_REPORT.md" + chr(96) + " |"
B4 = A4 + NL + ("| 其他层失败变体（RP-R6d-14） | U354 关闭（M2-05 8 点全 MATCH；范围 P0/P2/PP1/PP2、F4、"
                "driver_r8m2a2_layers） | 关闭（U354） | " + chr(96) + "VERDICT_R9.tsv" + chr(96) + " |") + NL + (
      "| S1/S2 移交：七处 info=NULL seam | U356 闭合（M1R3 G6 7/7 MATCH） | 关闭（U356） | " + chr(96) +
      "VERDICT_M1_F4_R9M1R3.tsv" + chr(96) + " |")
A5 = ("| Python/Lua 可见性（RP-R6d-15） | U345 独立复核一致（DIFFS=0），带范围声明关闭 | 关闭（待用户审核） | " +
      chr(96) + "REJUDGE_E2E_R9M3C.tsv" + chr(96) + " |")
B5 = ("| Python/Lua 可见性（RP-R6d-15） | U352 接受 S-B 复核（DIFFS=0），U345 关闭条件成立 | 关闭（U345/U352） | " +
      chr(96) + "REJUDGE_E2E_R9M3C.tsv" + chr(96) + " |")
A6 = "> 说明：本轮完成 R9 M3c（裁决/勘误 + M3b 独立只读复核 + 签收就绪审计 + 最终红点台账 + 签收范围声明草稿），不宣布阶段完成；等待用户审核。"
B6 = "> 说明：本轮完成 R9 M3d（U351–U358 落账 + §3 P 项复核 + 勘误 + 修正版红点台账/去重 S5 移交/就绪审计/签收草稿 v2），不宣布阶段完成；等待用户审核。"
A7 = ("- **S4 R9 M3c（r9m3c）**：证据 " + chr(96) + "checkpoints/p05/evidence/p05-s4r9/m3c/" + chr(96) + "（" + chr(96) +
      "SHA256SUMS.txt" + chr(96) + "）；小表 " + chr(96) + "checkpoints/p05/registries/s4r9/M3c/" + chr(96) + "（" + chr(96) +
      "SHA256SUMS.txt" + chr(96) + "）；报告 " + chr(96) + "P05_S4R9_M3c_REPORT.md" + chr(96) + "。")
B7 = ("- **S4 R9 M3d（r9m3d）**：证据 " + chr(96) + "checkpoints/p05/evidence/p05-s4r9/m3d/" + chr(96) + "（" + chr(96) +
      "SHA256SUMS.txt" + chr(96) + "）；小表 " + chr(96) + "checkpoints/p05/registries/s4r9/M3d/" + chr(96) + "（" + chr(96) +
      "SHA256SUMS.txt" + chr(96) + "）；报告 " + chr(96) + "P05_S4R9_M3d_REPORT.md" + chr(96) + "。") + NL + A7
PAIRS = [(A1, B1), (A2, B2), (A3, B3), (A4, B4), (A5, B5), (A6, B6), (A7, B7)]


def main():
    p = sys.argv[1] if len(sys.argv) > 1 else STATE
    old = open(p, "rb").read()
    a = hashlib.sha256(old).hexdigest()
    if a != EXPECTED_SHA:
        print("HARD_STOP state prefix sha %s != %s" % (a, EXPECTED_SHA))
        return 2
    if len(old) != EXPECTED_BYTES:
        print("HARD_STOP state prefix bytes %d != %d" % (len(old), EXPECTED_BYTES))
        return 2
    txt = old.decode("utf-8")
    for a_s, b_s in PAIRS:
        c = txt.count(a_s)
        if c != 1:
            print("HARD_STOP anchor count %d for: %s" % (c, a_s[:70]))
            return 2
    for a_s, b_s in PAIRS:
        txt = txt.replace(a_s, b_s)
    if "U354" not in txt or "U356" not in txt:
        print("HARD_STOP U354/U356 not reflected in STATE")
        return 2
    new = txt.encode("utf-8")
    if len(new) > 8192:
        print("HARD_STOP STATE too large: %d bytes" % len(new))
        return 2
    open(p, "wb").write(new)
    print("STATE bytes %d -> %d sha %s" % (len(old), len(new), hashlib.sha256(new).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
