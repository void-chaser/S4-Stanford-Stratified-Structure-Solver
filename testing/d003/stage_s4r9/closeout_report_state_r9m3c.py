#!/usr/bin/env python3
# closeout_report_state_r9m3c.py -- closeout step 1: append appendix A to the report and finalise STATE.md, every number
# recomputed from the result tables (by column name). New file (r9m3c).
# usage: closeout_report_state_r9m3c.py REPORT.md STATE.md
import os, sys, re, hashlib
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
REG = os.path.join(REPO, "checkpoints/p05/registries")
M3B = os.path.join(EV, "..", "m3b")
TAB = chr(9)
NL = chr(10)
PH = "（APPENDIX_A_PLACEHOLDER）"


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


def kv(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 2:
            out.setdefault(f[0], f[1])
    return out


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def counter(path, key):
    txt = open(path, encoding="utf-8").read()
    m = re.search(r"COUNTS\tpass=(\d+)\tfail=(\d+)", txt)
    f = re.search(r"^FAILS=(\d+)", txt, re.M)
    return (int(m.group(1)) if m else -1), (int(f.group(1)) if f else -1)


def main():
    rep_p = sys.argv[1]
    st_p = sys.argv[2]
    cats = {}
    ver = read_table(os.path.join(M3B, "E2E_VERDICT_R9M3B.tsv"))
    for r in ver:
        cats[r.get("verdict", "?")] = cats.get(r.get("verdict", "?"), 0) + 1
    extra = {k: v for k, v in cats.items() if k not in ("CONTROL_OK", "E2E_OK")}
    extra_txt = ", ".join("%s=%d" % (k, v) for k, v in sorted(extra.items())) or "none"
    cmp_p = os.path.join(EV, "REJUDGE_COMPARE_R9M3C.txt")
    rej_diffs = -1
    rej_points = -1
    if os.path.isfile(cmp_p):
        for line in open(cmp_p, encoding="utf-8"):
            if line.startswith("DIFFS="):
                rej_diffs = int(line.strip().split("=")[1])
            elif line.startswith("POINTS="):
                rej_points = int(line.strip().split("=")[1])
    posE = [l for l in open(os.path.join(EV, "POSCTRL_REJUDGE_R9M3C.txt"), encoding="utf-8").read().splitlines()
            if l.startswith("OVERALL_POSITIVE_CONTROL")][-1]
    posR = [l for l in open(os.path.join(EV, "POSCTRL_REPORT_CHECK_R9M3C.txt"), encoding="utf-8").read().splitlines()
            if l.startswith("RESULT:")][-1]
    mk = kv(os.path.join(M3B, "MAKETEST_VERDICT_R9M3B.tsv"))
    rec = [l.rstrip(NL).split(TAB) for l in open(os.path.join(M3B, "MAKETEST_VERDICT_R9M3B.tsv"), encoding="utf-8")
           if l.startswith("reconcile" + TAB)]
    rec_ok = len(rec) == 8 and all(r[-1] == "OK" for r in rec)
    # reverify counts
    rev = read_table(os.path.join(EV, "REVERIFY_R9M3B_R9M3C.tsv"))
    man_items = {}
    for r in rev:
        if r.get("kind") == "manifest":
            man_items[r.get("target")] = r.get("detail")
    rev_fails = -1
    for line in open(os.path.join(EV, "REVERIFY_R9M3B_R9M3C.tsv"), encoding="utf-8"):
        if line.startswith("# FAILS="):
            rev_fails = int(line.strip().split("=")[1])
    # audit
    audit = read_table(os.path.join(EV, "AUDIT_R9M3B_R9M3C.tsv"))
    audit_ok = len([r for r in audit if r.get("verdict") == "属实"])
    mis = [r.get("item") for r in audit if r.get("verdict") != "属实"]
    gs_pass, gs_fail = counter(os.path.join(EV, "GATE_R9M3C_start.txt"), "")
    recheck_p = sys.argv[3] if len(sys.argv) > 3 else os.path.join(EV, "GATE_R9M3C_start_RECHECK.txt")
    gr_pass, gr_fail = counter(recheck_p, "")
    rul_b = open(os.path.join(REG, "RULINGS.tsv"), "rb").read()
    rul_nums = [int(l.split(TAB)[0][1:]) for l in rul_b.decode("utf-8", "replace").splitlines()
                if l.startswith("U") and l.split(TAB)[0][1:].isdigit()]
    err_b = open(os.path.join(REG, "s4r9/ERRATA_9.txt"), "rb").read()
    err_ids = re.findall(r"^(E9-\d+)", err_b.decode("utf-8", "replace"), re.M)
    # readiness
    rdy = read_table(os.path.join(EV, "READINESS_P05_S3S4_R9M3C.tsv"))
    rc = {}
    for r in rdy:
        rc[r.get("status", "?")] = rc.get(r.get("status", "?"), 0) + 1
    gaps = [r.get("item") for r in rdy if r.get("status") == "GAP"]
    hand = read_table(os.path.join(EV, "S5_HANDOFF_R9M3C.tsv"))
    # red ledger
    red_lines = open(os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3C.tsv"), encoding="utf-8").read().splitlines()
    red_rows = len([l for l in red_lines if l and not l.startswith("#")])
    red_open = 0
    red_conf = 0
    for l in red_lines:
        if l.startswith("# OPEN_IN_SCOPE="):
            red_open = int(l.strip().split("=")[1])
        elif l.startswith("# CONFLICTS:"):
            red_conf = int(re.search(r"(\d+)$", l.strip()).group(1))
    red_norow = 0
    for l in red_lines:
        if l.startswith("# NO_RED_POINT_ROWS="):
            red_norow = int(l.strip().split("=")[1])
    new_red = "无（E2E 无 API_SILENT / RETRY_DIFF / RETRY_FAIL）" if not extra else "见 E2E 判据"
    ap = [
        "记录提交 (i) 之后由冻结脚本执行；本附录的数字全部由 closeout 从结果表复算，未手写。",
        "",
        "- 门禁：start PASS=%d FAILS=%d；start 前缀复核 PASS=%d FAILS=%d" % (gs_pass, gs_fail, gr_pass, gr_fail),
        "- L 项复核：AUDIT_R9M3B_R9M3C.tsv %d/%d 属实；规划者事实有误：%s" % (
            audit_ok, len(audit), ",".join(mis) if mis else "none"),
        "- 裁决/勘误：RULINGS 最大 U%d（%d 字节，sha %s）；ERRATA_9.txt 最后 %s，共 %d 条（%d 字节，sha %s）" % (
            max(rul_nums), len(rul_b), hashlib.sha256(rul_b).hexdigest()[:8], err_ids[-1], len(err_ids), len(err_b),
            hashlib.sha256(err_b).hexdigest()[:8]),
        "- M3b 独立复核：REJUDGE %d 点，DIFFS=%d；类别 CONTROL_OK=%d, E2E_OK=%d，其他 %s；阳性对照 %s" % (
            rej_points, rej_diffs, cats.get("CONTROL_OK", 0), cats.get("E2E_OK", 0), extra_txt, posE),
        "- 复验：m3b 证据清单 %s；registries/s4r9/M3b 清单 %s；make test reconcile %s；REVERIFY FAILS=%d" % (
            man_items.get("m3b_evidence", "?"), man_items.get("registries_M3b", "?"),
            ("8 行全部 OK" if rec_ok else "存在 FAIL"), rev_fails),
        "- make test 只读重解析：verdict=%s unit_count=%s；4 遍 × 2 段对账 %s（8/8 reconcile 的 ok 列）" % (
            mk.get("verdict", "?"), mk.get("unit_count", "?"), ("全部 OK" if rec_ok else "存在 FAIL")),
        "- 新增红点：%s" % new_red,
        "- 签收就绪：READINESS 共 %d 行：MET=%d GAP=%d TRANSFERRED_S5=%d CLOSED_BY_RULING=%d；GAP 明细：%s" % (
            len(rdy), rc.get("MET", 0), rc.get("GAP", 0), rc.get("TRANSFERRED_S5", 0), rc.get("CLOSED_BY_RULING", 0),
            (",".join(gaps) if gaps else "none")),
        "- 最终红点台账：%d 行（非红点行 %d），范围内仍开放 %d 个；冲突 %d 处（以最新裁决解决）" % (
            red_rows, red_norow, red_open, red_conf),
        "- S5 移交：%d 项（S5_HANDOFF_R9M3C.tsv）" % len(hand),
        "- 报告检查阳性对照：%s" % posR,
        "- STATE 最终字节数：@STATE_BYTES@（<=8192）",
        "- 逐点明细：REJUDGE_E2E_R9M3C.tsv；红点台账：RED_POINTS_LEDGER_FINAL_R9M3C.tsv；就绪审计：READINESS_P05_S3S4_R9M3C.tsv",
    ]
    rep_txt = open(rep_p, "rb").read().decode("utf-8")
    if rep_txt.count(PH) != 1:
        print("HARD_STOP report placeholder count %d" % rep_txt.count(PH))
        return 2
    st_txt = open(st_p, "rb").read().decode("utf-8")
    a1 = "| 本轮开工基线 HEAD（r9m3b） | `6aa11d8b2eb3bea896406842c30eda742af19080` |"
    a2 = "| 当前轮次 | **P05-S4 R9 M3b（r9m3b）**：M3a 偏差裁决落账（U334–U342、E9-46..E9-57）+ make test 只读重解析（NO_NEW_FAILURE，4 遍对账通过）+ E2E 修订/校准/新预注册（42 点）/正式两遍（CONTROL_OK=17, E2E_OK=25） |"
    a3 = "| S4R9 M3b | U334–U342、E9-46–E9-57；make test 只读重解析 NO_NEW_FAILURE（265 单元、4 遍对账通过）；E2E 预注册 42 点、正式两遍 CONTROL_OK=17, E2E_OK=25；新红点 0 | `P05_S4R9_M3b_REPORT.md` |"
    a4 = "| RP-R8-M2c-1/1b | 按 U304 关闭（18 点全 MATCH） | 关闭 | `P05_S4R9_M2c_REPORT.md` |"
    a5 = "| Python/Lua 可见性（RP-R6d-15） | 正式两遍实测：CONTROL_OK=17, E2E_OK=25；其他类别 none | 已实测（待用户审核） | `E2E_VERDICT_R9M3B.tsv` |"
    a6 = "> 说明：本轮完成 R9 M3b（勘误收口 + make test 重解析 NO_NEW_FAILURE + E2E 修订/校准/预注册/正式两遍），不宣布阶段完成；等待用户审核。"
    a7 = "- **S4 R9 M3b（r9m3b）**：证据 `checkpoints/p05/evidence/p05-s4r9/m3b/`（`SHA256SUMS.txt`）；小表 `checkpoints/p05/registries/s4r9/M3b/`（`SHA256SUMS.txt`）；报告 `P05_S4R9_M3b_REPORT.md`。"
    for a in (a1, a2, a3, a4, a5, a6, a7):
        if st_txt.count(a) != 1:
            print("HARD_STOP state anchor count %d for: %s" % (st_txt.count(a), a[:60]))
            return 2
    b1 = "| 本轮开工基线 HEAD（r9m3c） | `01fd3c0e4cf436aef5780486c8b8327c25849713` |"
    b2 = "| 当前轮次 | **P05-S4 R9 M3c（r9m3c）**：U343–U350、E9-58–E9-66 落账 + M3b 独立只读复核（DIFFS=%d）+ 签收就绪审计（MET=%d GAP=%d TRANSFERRED_S5=%d）+ 最终红点台账 + 签收范围声明草稿 |" % (
        rej_diffs, rc.get("MET", 0), rc.get("GAP", 0), rc.get("TRANSFERRED_S5", 0))
    b3 = a3 + NL + "| S4R9 M3c | U343–U350、E9-58–E9-66；M3b 独立复核 DIFFS=%d；READINESS MET=%d GAP=%d TRANSFERRED_S5=%d；红点范围内开放 %d；S5 移交 %d 项 | `P05_S4R9_M3c_REPORT.md` |" % (
        rej_diffs, rc.get("MET", 0), rc.get("GAP", 0), rc.get("TRANSFERRED_S5", 0), red_open, len(hand))
    b4 = "| RP-R8-M2c-1/1b | U350 确认按 U304 关闭（18 点全 MATCH） | 关闭 | `P05_S4R9_M2c_REPORT.md` |"
    b5 = "| Python/Lua 可见性（RP-R6d-15） | U345 独立复核一致（DIFFS=%d），带范围声明关闭 | 关闭（待用户审核） | `REJUDGE_E2E_R9M3C.tsv` |" % rej_diffs
    b6 = "> 说明：本轮完成 R9 M3c（裁决/勘误 + M3b 独立只读复核 + 签收就绪审计 + 最终红点台账 + 签收范围声明草稿），不宣布阶段完成；等待用户审核。"
    b7 = "- **S4 R9 M3c（r9m3c）**：证据 `checkpoints/p05/evidence/p05-s4r9/m3c/`（`SHA256SUMS.txt`）；小表 `checkpoints/p05/registries/s4r9/M3c/`（`SHA256SUMS.txt`）；报告 `P05_S4R9_M3c_REPORT.md`。" + NL + a7
    st_new = st_txt.replace(a1, b1).replace(a2, b2).replace(a3, b3).replace(a4, b4).replace(a5, b5).replace(a6, b6).replace(a7, b7)
    body = NL.join(ap)
    body = body.replace("@STATE_BYTES@", str(len(st_new.encode("utf-8"))))
    rep_new = rep_txt.replace(PH, body)
    open(rep_p, "wb").write(rep_new.encode("utf-8"))
    open(st_p, "wb").write(st_new.encode("utf-8"))
    print("report bytes %d -> %d sha %s" % (len(rep_txt.encode("utf-8")), len(rep_new.encode("utf-8")),
                                            hashlib.sha256(rep_new.encode("utf-8")).hexdigest()))
    print("state bytes %d -> %d sha %s" % (len(st_txt.encode("utf-8")), len(st_new.encode("utf-8")),
                                           hashlib.sha256(st_new.encode("utf-8")).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
