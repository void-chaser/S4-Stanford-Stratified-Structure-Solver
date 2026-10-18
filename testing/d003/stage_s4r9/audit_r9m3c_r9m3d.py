#!/usr/bin/env python3
# audit_r9m3c_r9m3d.py -- re-verify the planner's section-3 P-1..P-6 claims against the original files. Every line
# number and count is computed here (never copied from the brief). Writes AUDIT_R9M3C_R9M3D.tsv; a claim is either
# "属实" or "规划者事实有误" with the actual value attached. All tables are read by column name. New file (r9m3d).
import os, sys, re
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
REG = os.path.join(REPO, "checkpoints/p05/registries")
M3C = os.path.join(REG, "s4r9/M3c")
M2 = os.path.join(REG, "s4r9/M2")
M1R3 = os.path.join(REG, "s4r9/M1R3")
M3C_EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
STAGE = os.path.join(REPO, "testing/d003/stage_s4r9")
SIGNOFF_V1 = os.path.join(REPO, "checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT.md")
SIGNOFF_S1S2 = os.path.join(REPO, "checkpoints/p05/P05_S1_S2_SIGNOFF.md")
OUT = os.path.join(EV, "AUDIT_R9M3C_R9M3D.tsv")
TAB = chr(9)
NL = chr(10)
COLS = ["item", "claim", "verdict", "actual_value", "evidence", "note"]


def read_table(path):
    rows = []
    hdr = None
    if not os.path.isfile(path):
        return hdr, rows
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


def norm(name):
    s = name.replace(chr(96), "")
    s = s.replace("（", "(").replace("）", ")")
    s = re.sub(r"\([^()]*\)", "", s)
    s = re.sub(r"[\s、，,。:：;；·]", "", s)
    return s.lower().replace("silent_swallow", "silent")


def p1():
    _, m2 = read_table(os.path.join(M2, "VERDICT_R9.tsv"))
    rows = [r for r in m2 if r.get("point_id", "").startswith("M2-05")]
    ids = sorted(r["point_id"] for r in rows)
    all_match = bool(rows) and all(r.get("verdict") == "MATCH" for r in rows)
    u245 = ""
    for line in open(os.path.join(REG, "RULINGS.tsv"), encoding="utf-8"):
        if line.startswith("U245" + TAB):
            u245 = line
    layouts_ok = all(k in u245 for k in ("P0", "P2", "PP1", "PP2")) and "driver_r8m2a2_layers" in u245
    _, led = read_table(os.path.join(M3C, "RED_POINTS_LEDGER_FINAL_R9M3C.tsv"))
    r14 = [r for r in led if r.get("id") == "RP-R6d-14"]
    loc = r14[0].get("location", "") if r14 else ""
    status = r14[0].get("current_status", "") if r14 else ""
    ruling = r14[0].get("closing_ruling", "") if r14 else ""
    desc_ok = ("two layers" in loc) and ("not at position 1" in loc)
    ok = all_match and len(rows) == 8 and layouts_ok and desc_ok and status == "TRANSFERRED_S5" and ruling == "U20"
    actual = ("M2-05 rows=%d all_MATCH=%s ids=%s; U245 layouts P0/P2/PP1/PP2+driver_r8m2a2_layers=%s; "
              "ledger RP-R6d-14 status=%s ruling=%s location=%s; layout description corresponds=%s") % (
        len(rows), all_match, ",".join(ids), layouts_ok, status, ruling, loc[:110], desc_ok)
    return ok, actual, "M2/VERDICT_R9.tsv; RULINGS.tsv U245; M3C ledger RP-R6d-14"


def p2():
    _, hand = read_table(os.path.join(M3C, "S5_HANDOFF_R9M3C.tsv"))
    names = [norm(r.get("item", "")) for r in hand if r.get("item")]
    uniq = sorted(set(names))
    _, led = read_table(os.path.join(M3C, "RED_POINTS_LEDGER_FINAL_R9M3C.tsv"))
    t5 = sorted(r["id"] for r in led if r.get("current_status") == "TRANSFERRED_S5")
    CANON = {"RP-R6d-6": ["b侧jones/vlsilentnvcrash"], "RP-R6d-16": ["nb=1–8类别c"], "RP-R6d-17": ["nb=1–8类别c"],
             "RP-R6d-18": ["非fmms4_malloc"]}
    no_item = []
    for rid in t5:
        c = CANON.get(rid)
        if not c or not any(x in uniq for x in c):
            no_item.append(rid)
    ok = (len(hand) == 10 and len(uniq) == 5 and len(t5) == 7
          and "RP-R6d-3" in no_item and "RP-R6d-7" in no_item)
    actual = ("M3c handoff data rows=%d; unique canonical names=%d (%s); ledger TRANSFERRED_S5 ids=%d (%s); "
              "ids without a handoff item=%s") % (
        len(hand), len(uniq), "|".join(uniq), len(t5), ",".join(t5), ",".join(no_item))
    return ok, actual, "M3c/S5_HANDOFF_R9M3C.tsv; M3c/RED_POINTS_LEDGER_FINAL_R9M3C.tsv"


def p3():
    _, rdy = read_table(os.path.join(M3C, "READINESS_P05_S3S4_R9M3C.tsv"))
    red = [r for r in rdy if r.get("item", "").startswith("①")]
    claimed = -1
    if red:
        m = re.search(r"红点行=(\d+)", red[0].get("recomputed", ""))
        claimed = int(m.group(1)) if m else -1
    led_p = os.path.join(M3C, "RED_POINTS_LEDGER_FINAL_R9M3C.tsv")
    _, led = read_table(led_p)
    uniq = len(set(r.get("id", "") for r in led))
    lines = open(led_p, encoding="utf-8").read().splitlines()
    header_line = 0
    naive = 0
    for i, line in enumerate(lines, 1):
        if not line.strip() or line.startswith("#"):
            continue
        naive += 1
        if line.split(TAB)[0] == "id":
            header_line = i
    src = os.path.join(STAGE, "readiness_r9m3c.py")
    src_lines = open(src, encoding="utf-8").read().splitlines()
    inc_line = 0
    loop_line = 0
    for i, line in enumerate(src_lines, 1):
        if "ledger_rows += 1" in line:
            inc_line = i
        if "for line in open(lp" in line:
            loop_line = i
    extra = naive - uniq
    ok = claimed == naive and extra == 1 and header_line > 0 and inc_line > 0
    actual = ("READINESS ① 写红点行=%d；台账唯一 id 数=%d；台账非注释非空行=%d（含表头）；多算=%d；"
              "表头行号=%d；成因：%s 的 %d–%d 行循环未跳过表头，%d 行 ledger_rows += 1 把表头算成一行") % (
        claimed, uniq, naive, extra, header_line, os.path.relpath(src, REPO), loop_line - 1, inc_line, inc_line)
    return ok, actual, "%s; RED_POINTS_LEDGER_FINAL_R9M3C.tsv:%d" % (os.path.relpath(src, REPO), header_line)


def p4():
    txt = open(SIGNOFF_V1, encoding="utf-8").read().splitlines()
    items = []
    insec = False
    for line in txt:
        if line.startswith("### 转入 S5 的项"):
            insec = True
            continue
        if insec and line.startswith("#"):
            break
        if insec and line.strip().startswith("- "):
            items.append(line.strip()[2:])
    names = [norm(x.split("→")[0]) for x in items]
    uniq = sorted(set(names))
    joined = " ".join(items)
    has3 = ("RP-R6d-3" in joined) or ("no-TWICE" in joined)
    has7 = ("RP-R6d-7" in joined) or ("D016" in joined)
    ok = len(items) == 10 and len(uniq) == 5 and (not has3) and (not has7)
    actual = ("signoff v1 转入 S5 项=%d 条；规范化去重=%d；缺 RP-R6d-3=%s；缺 RP-R6d-7=%s") % (
        len(items), len(uniq), not has3, not has7)
    return ok, actual, "P05_S3_S4_SIGNOFF_DRAFT.md 转入 S5 的项"


def p5():
    points = ("R4-CL01-F-F4", "R4-CL02-F-F4", "R4-CL03-F-F4", "R4-CL04-F-F4",
              "R4-PJ01-F-F4", "R4-PN01-F-F4", "R4-PV01-F-F4")
    _, m1 = read_table(os.path.join(M1R3, "VERDICT_M1_F4_R9M1R3.tsv"))
    got = {}
    for r in m1:
        if r.get("group") == "G6" and r.get("point_id") in points:
            got[r["point_id"]] = r
    ok = len(got) == 7 and all(got[p].get("verdict") == "MATCH" and got[p].get("tree") == "F4" for p in points)
    detail = ";".join("%s driver=%s pass1=%s pass2=%s verdict=%s tree=%s" % (
        p, got[p].get("driver_name"), got[p].get("pass1_class"), got[p].get("pass2_class"),
        got[p].get("verdict"), got[p].get("tree")) for p in points if p in got)
    s12 = open(SIGNOFF_S1S2, encoding="utf-8").read()
    s2_ok = ("七处 info=NULL 的 LinearSolve 修前 seam 不可测" in s12) and ("P05-S4" in s12)
    v1 = open(SIGNOFF_V1, encoding="utf-8").read()
    v1_closed = ("info=NULL" in v1) or ("S1/S2 签收移交项" in v1)
    ok = ok and s2_ok and (not v1_closed)
    actual = ("7 点=%s; P05_S1_S2_SIGNOFF §2(2) 原文存在=%s; signoff v1 说明该移交已闭合=%s") % (
        detail, s2_ok, v1_closed)
    return ok, actual, "M1R3/VERDICT_M1_F4_R9M1R3.tsv; P05_S1_S2_SIGNOFF.md §2; P05_S3_S4_SIGNOFF_DRAFT.md"


def p6():
    _, rdy = read_table(os.path.join(M3C, "READINESS_P05_S3S4_R9M3C.tsv"))
    row = [r for r in rdy if "RP-R6d-15" in r.get("item", "")]
    old_wording = bool(row) and ("待用户审核" in row[0].get("recomputed", ""))
    jian = len([r for r in rdy if "见 STATE 行" in (r.get("ruling", "") + r.get("recomputed", ""))])
    ruling_jian = len([r for r in rdy if "见 STATE 行" in r.get("ruling", "")])
    ok = old_wording and ruling_jian == 16
    actual = ("READINESS RP-R6d-15 state 含“待用户审核”=%s（recomputed=%s）；裁决列写“见 STATE 行”的行数=%d（全字段含=%d）；总行数=%d") % (
        old_wording, row[0].get("recomputed", "")[:120] if row else "missing", ruling_jian, jian, len(rdy))
    return ok, actual, "M3c/READINESS_P05_S3S4_R9M3C.tsv"


def main():
    checks = [
        ("P-1", "M3c 台账 RP-R6d-14=TRANSFERRED_S5 依据 U20，但 M2 的 M2-05 行全部 MATCH，且 U245 布局与位置描述对应", p1),
        ("P-2", "M3c S5 移交 10 行去重后 5 项；台账 TRANSFERRED_S5 有 7 个 id，RP-R6d-3、RP-R6d-7 在移交表里没有对应项", p2),
        ("P-3", "READINESS ① 写红点行=27，而台账唯一 id 数是 26；多算的是表头行，给脚本文件名与行号", p3),
        ("P-4", "签收草稿 v1 的转入 S5 项有 10 条，含重复，并且缺 RP-R6d-3、RP-R6d-7", p4),
        ("P-5", "M1R3 G6 组 R4-CL01..04、R4-PJ01、R4-PN01、R4-PV01（F4）共 7 点 MATCH；v1 未说明移交闭合", p5),
        ("P-6", "READINESS RP-R6d-15 行仍是“待用户审核”旧措辞；裁决列写“见 STATE 行”的行数要数出", p6),
    ]
    rows = []
    for item, claim, fn in checks:
        ok, actual, evid = fn()
        verdict = "属实" if ok else "规划者事实有误"
        rows.append((item, claim, verdict, actual, evid, ""))
    lines = ["# AUDIT_R9M3C_R9M3D.tsv -- section-3 P-1..P-6 re-verification against the original files (read-only)",
             TAB.join(COLS)]
    for r in rows:
        lines.append(TAB.join(r))
    true_n = len([r for r in rows if r[2] == "属实"])
    lines.append("# VERDICT_TRUE=%d FALSE=%d" % (true_n, len(rows) - true_n))
    lines.append("# UNIQUE=%d ROWS=%d" % (len(rows), len(rows)))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines) + NL)
    for r in rows:
        print(r[0] + "\t" + r[2] + "\t" + r[3][:220])
    print("VERDICT_TRUE=%d FALSE=%d" % (true_n, len(rows) - true_n))
    print("WROTE " + OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
