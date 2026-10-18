#!/usr/bin/env python3
# append_rulings_r9m3d.py -- append U351..U358 to checkpoints/p05/registries/RULINGS.tsv (old file + new rows).
# The prefix sha256/bytes are asserted first; the old bytes are never rewritten. The status of U354 / U356 is
# computed from the section-3 P-1 / P-5 checks (they must not be hardcoded active): if the premise fails the row is
# written as "未生效（前提不成立）". New file (r9m3d).
import os, sys, re, hashlib
REPO = os.getcwd()
REG = os.path.join(REPO, "checkpoints/p05/registries")
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
M3C = os.path.join(REG, "s4r9/M3c")
M2 = os.path.join(REG, "s4r9/M2")
M1R3 = os.path.join(REG, "s4r9/M1R3")
P = os.path.join(REG, "RULINGS.tsv")
EXPECTED_SHA = "443d8a380f85975ebd1d023bf0667696ec24cb53078e78bae16462470fe26116"
EXPECTED_BYTES = 142281
TAB = chr(9)
NL = chr(10)
SQ = chr(34)


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


def check_p1():
    hdr, m2 = read_table(os.path.join(M2, "VERDICT_R9.tsv"))
    points = [r["point_id"] for r in m2 if r.get("point_id", "").startswith("M2-05")]
    all_match = bool(points) and all(r.get("verdict") == "MATCH" for r in m2 if r.get("point_id", "").startswith("M2-05"))
    verdicts = sorted(set(r.get("verdict", "?") for r in m2 if r.get("point_id", "").startswith("M2-05")))
    u245 = ""
    for line in open(os.path.join(REG, "RULINGS.tsv"), encoding="utf-8"):
        if line.startswith("U245" + TAB):
            u245 = line
    layouts_ok = all(k in u245 for k in ("P0", "P2", "PP1", "PP2")) and "driver_r8m2a2_layers" in u245
    hdr3, led = read_table(os.path.join(M3C, "RED_POINTS_LEDGER_FINAL_R9M3C.tsv"))
    r14 = [r for r in led if r.get("id") == "RP-R6d-14"]
    loc = r14[0].get("location", "") if r14 else ""
    desc_ok = ("two layers" in loc) and ("not at position 1" in loc)
    ok = all_match and len(points) == 8 and layouts_ok and desc_ok
    return ok, "M2-05 ids=%d all_MATCH=%s verdicts=%s; U245 P0/P2/PP1/PP2+driver=%s; RP-R6d-14 location=%s" % (
        len(points), all_match, verdicts, layouts_ok, loc[:120])


def check_p5():
    points = ("R4-CL01-F-F4", "R4-CL02-F-F4", "R4-CL03-F-F4", "R4-CL04-F-F4",
              "R4-PJ01-F-F4", "R4-PN01-F-F4", "R4-PV01-F-F4")
    hdr, m1 = read_table(os.path.join(M1R3, "VERDICT_M1_F4_R9M1R3.tsv"))
    got = {}
    for r in m1:
        if r.get("point_id") in points and r.get("group") == "G6":
            got[r["point_id"]] = r
    ok = len(got) == 7 and all(got[p].get("verdict") == "MATCH" and got[p].get("tree") == "F4" for p in points)
    detail = ";".join("%s=%s/%s/%s" % (p, got[p].get("driver_name", "?"), got[p].get("pass1_class", "?"),
                                        got[p].get("pass2_class", "?")) for p in points if p in got)
    return ok, "rows=%d detail=%s" % (len(got), detail)


def main():
    p1_ok, p1_detail = check_p1()
    p5_ok, p5_detail = check_p5()
    st354 = "生效" if p1_ok else "未生效（前提不成立）"
    st356 = "生效" if p5_ok else "未生效（前提不成立）"
    ROWS = [
        ("U351", "P05-S4 R9 M3d 任务书 §2",
         "M3c 的 U343–U350 与 E9-58–E9-66 落账生效。",
         "P05-S4 R9 M3d 任务书 §2", "生效"),
        ("U352", "P05-S4 R9 M3d 任务书 §2",
         "M3c 的 S-B 独立复核结果（DIFFS=0、E2E_OK=25、CONTROL_OK=17、阳性对照 16/16、REVERIFY FAILS=0）接受。"
         "U345 的关闭条件成立，RP-R6d-15 按 U345 的范围声明关闭。",
         "P05-S4 R9 M3d 任务书 §2", "生效"),
        ("U353", "P05-S4 R9 M3d 任务书 §2",
         "M3c end 门禁 EVIDENCE_SHA256SUMS_OK 的 FAIL 判为执行顺序错误：sha_sums 之后又写了一行 progress。"
         "结果表未受影响。接受“删除误加行、逐项校验 16/16 一致”的处理，只登记勘误，不重跑。"
         "M3c 表二的三条顺序偏差同样接受，只登记勘误。",
         "P05-S4 R9 M3d 任务书 §2", "生效"),
        ("U354", "P05-S4 R9 M3d 任务书 §2",
         "RP-R6d-14（其他层失败变体）不再转 S5。依据：U245 定义了 P0/P2/PP1/PP2 四种布局，R9 M2 在 F4 上正式两遍测了"
         " M2-05 共 8 点（4 个注入点、4 个对照），全部 MATCH；另有补测点 M2-05-P0-F4-C，也是 MATCH。范围声明：仅限这四种布局、"
         "F4、驱动 driver_r8m2a2_layers。U20 的“推迟”由本裁决结束。前提：§3 P-1 复核属实；不属实时，本裁决不生效，"
         "并写入“需用户裁决”。复核：P-1 属实（" + ("%d 点全 MATCH" % 8 if p1_ok else "不成立") + "）。",
         "P05-S4 R9 M3d 任务书 §2", st354),
        ("U355", "P05-S4 R9 M3d 任务书 §2",
         "S5 移交清单以去重后的唯一项为准。最终红点台账里每个 TRANSFERRED_S5 的 id 都必须出现在移交清单中，反过来移交清单的每一项"
         "也必须能对应到台账 id 或 STATE 行，不能有只出现在一边的项。RP-R6d-3（no-TWICE 路径，OUT_OF_SCOPE_D003）和"
         " RP-R6d-7（D016，B 侧 rc 来源未追踪）按台账现状转 S5，补进移交清单。",
         "P05-S4 R9 M3d 任务书 §2", "生效"),
        ("U356", "P05-S4 R9 M3d 任务书 §2",
         "S1/S2 签收范围声明第 (2) 条（七处 info=NULL 的 LinearSolve 修前 seam 移交 P05-S4）以 M1R3 中 G6 组"
         " R4-CL01..CL04、R4-PJ01、R4-PN01、R4-PV01（F4）的判定作为闭合证据。前提：§3 P-5 复核为 7/7 MATCH。"
         "签收草稿 v2 要单列一节写明这项移交已闭合，并注明 F4 上族 B 原有的 info=NULL 锚点已不存在"
         "（P05_S4R4_REPORT.md §2a），所以这 7 点测的是修复后的 &solve_info 路径。复核：P-5 " + ("7/7 MATCH" if p5_ok else "不成立") + "。",
         "P05-S4 R9 M3d 任务书 §2", st356),
        ("U357", "P05-S4 R9 M3d 任务书 §2",
         "就绪审计重算时，每一行的“裁决号”必须是 RULINGS.tsv 中真实存在的 U 编号，或者写 “-（事实项）”，"
         "不得写“见 STATE 行”。RP-R6d-15 那行改用 U345/U352。",
         "P05-S4 R9 M3d 任务书 §2", "生效"),
        ("U358", "P05-S4 R9 M3d 任务书 §2",
         "M3c 已提交的产物不改；M3d 的修正版作为签收前的唯一现行版本。STATE 的开放问题表要同步反映 U354 与 U356。",
         "P05-S4 R9 M3d 任务书 §2", "生效"),
    ]
    old = open(P, "rb").read()
    a = hashlib.sha256(old).hexdigest()
    if a != EXPECTED_SHA:
        print("HARD_STOP rulings prefix sha %s != %s" % (a, EXPECTED_SHA))
        return 2
    if len(old) != EXPECTED_BYTES:
        print("HARD_STOP rulings prefix bytes %d != %d" % (len(old), EXPECTED_BYTES))
        return 2
    if not old.endswith(NL.encode("utf-8")):
        old += NL.encode("utf-8")
    add = "".join(TAB.join(r) + NL for r in ROWS)
    new = old + add.encode("utf-8")
    if new[:len(old)] != old:
        print("HARD_STOP prefix changed")
        return 2
    open(P, "wb").write(new)
    print("RULINGS bytes %d -> %d sha %s" % (len(old), len(new), hashlib.sha256(new).hexdigest()))
    print("P1 ok=%s -> U354 status=%s" % (p1_ok, st354))
    print("P5 ok=%s -> U356 status=%s" % (p5_ok, st356))
    print("P1 detail: " + p1_detail[:200])
    print("P5 detail: " + p5_detail[:300])
    print("APPENDED " + ",".join(r[0] for r in ROWS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
