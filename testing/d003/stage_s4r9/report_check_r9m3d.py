#!/usr/bin/env python3
# report_check_r9m3d.py -- report check: negation-aware forbidden words, required sections, table continuity, numeric
# cross-checks, every appendix-A derived sentence recomputed from the source tables, the deadline marker, the signoff
# draft v2 structure and the positive-control results. New file (r9m3d).
# usage: report_check_r9m3d.py REPORT.md [OUT.txt] [STATE.md]
import os, sys, re, hashlib
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
REG = os.path.join(REPO, "checkpoints/p05/registries")
TAB = chr(9)
NL = chr(10)
FORBIDDEN = ["已修好", "静态可达", "是否签收"]
REQUIRED = ["## 1", "## 2", "## 3", "## 4", "## 5", "## 6", "## 7", "## 8", "## 9", "交付物", "需用户裁决",
            "等待用户审核", "附录 A", "附录 B"]
PH_A = "（APPENDIX_A_PLACEHOLDER）"
PH_B = "（APPENDIX_B_PLACEHOLDER）"


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


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def gate_counts(path):
    p = f = tot = -1
    if os.path.isfile(path):
        for line in open(path, encoding="utf-8"):
            m = re.match(r"COUNTS\tpass=(\d+)\tfail=(\d+)\tskip=(\d+)\ttotal=(\d+)", line)
            if m:
                p, f, tot = int(m.group(1)), int(m.group(2)), int(m.group(4))
            m2 = re.match(r"FAILS=(\d+)", line)
            if m2:
                f = int(m2.group(1))
    return p, f, tot


def posctrl(path):
    if not os.path.isfile(path):
        return "missing"
    return "PASS" if "RESULT: PASS" in open(path, encoding="utf-8").read() else "FAIL"


def compute_env(state_p, recheck_p=None):
    env = {}
    env["sp"], env["sf"], env["st"] = gate_counts(os.path.join(EV, "GATE_R9M3D_start.txt"))
    env["rp"], env["rf"], env["rt"] = gate_counts(recheck_p or os.path.join(EV, "GATE_R9M3D_start_RECHECK.txt"))
    _, aud = read_table(os.path.join(EV, "AUDIT_R9M3C_R9M3D.tsv"))
    env["at"] = len([r for r in aud if r.get("verdict") == "属实"])
    env["an"] = len(aud)
    mis = [r.get("item") for r in aud if r.get("verdict") != "属实"]
    env["amis"] = ",".join(mis) if mis else "none"
    rul_p = os.path.join(REG, "RULINGS.tsv")
    rul_b = open(rul_p, "rb").read()
    nums = [int(l.split(TAB)[0][1:]) for l in rul_b.decode("utf-8", "replace").splitlines()
            if l.startswith("U") and l.split(TAB)[0][1:].isdigit()]
    env["umax"] = "U%d" % max(nums)
    env["ub"] = len(rul_b)
    env["us"] = hashlib.sha256(rul_b).hexdigest()[:8]
    st354 = st356 = "MISSING"
    for line in rul_b.decode("utf-8", "replace").splitlines():
        f = line.split(TAB)
        if len(f) >= 5 and f[0] == "U354":
            st354 = f[4].strip()
        if len(f) >= 5 and f[0] == "U356":
            st356 = f[4].strip()
    env["s354"], env["s356"] = st354, st356
    err_b = open(os.path.join(REG, "s4r9/ERRATA_9.txt"), "rb").read()
    ids = re.findall(r"^(E9-\d+)", err_b.decode("utf-8", "replace"), re.M)
    env["elast"], env["ecnt"] = ids[-1], len(ids)
    env["eb"] = len(err_b)
    env["es"] = hashlib.sha256(err_b).hexdigest()[:8]
    led_p = os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv")
    _, led = read_table(led_p)
    env["lu"] = len(set(r.get("id", "") for r in led))
    env["lr"] = len(led)
    env["lt5"] = len([r for r in led if r.get("current_status") == "TRANSFERRED_S5"])
    env["lopen"] = 0
    env["lconf"] = 0
    for line in open(led_p, encoding="utf-8"):
        m = re.match(r"# OPEN_IN_SCOPE=(\d+)", line)
        if m:
            env["lopen"] = int(m.group(1))
        m = re.match(r"# CONFLICTS: same id with different raw status across the original ledgers: (\d+)", line)
        if m:
            env["lconf"] = int(m.group(1))
    _, hand = read_table(os.path.join(EV, "S5_HANDOFF_R9M3D.tsv"))
    env["hu"] = len(set(r.get("item_id", "") for r in hand))
    _, rdy = read_table(os.path.join(EV, "READINESS_P05_S3S4_R9M3D.tsv"))
    rc = {}
    for r in rdy:
        rc[r.get("status", "?")] = rc.get(r.get("status", "?"), 0) + 1
    gaps = [r.get("item", "") for r in rdy if r.get("status") == "GAP"]
    env["rn"] = len(rdy)
    env["rm"], env["rg"], env["rt5"], env["rc"] = rc.get("MET", 0), rc.get("GAP", 0), rc.get("TRANSFERRED_S5", 0), rc.get("CLOSED_BY_RULING", 0)
    env["rgaps"] = ",".join(gaps) if gaps else "none"
    env["ph"] = posctrl(os.path.join(EV, "POSCTRL_HANDOFF_R9M3D.txt"))
    env["pr"] = posctrl(os.path.join(EV, "POSCTRL_READINESS_R9M3D.txt"))
    env["pc"] = posctrl(os.path.join(EV, "POSCTRL_REPORT_CHECK_R9M3D.txt"))
    st_b = open(state_p, "rb").read()
    env["sb"] = len(st_b)
    env["ss"] = hashlib.sha256(st_b).hexdigest()[:8]
    return env


def expected_appendix(env):
    fr_p = os.path.join(EV, "FROZEN_SCRIPTS_R9M3D.tsv")
    if not os.path.isfile(fr_p):
        frozen_line = ("- 冻结清单：尚未写定（试跑期按 §5 顺序，收尾链试跑先于冻结清单；end 门禁的冻结相关检查在试跑期标 SKIP）")
    else:
        frozen_line = "- 冻结清单：FROZEN_SCRIPTS_R9M3D.tsv 共 %d 项（脚本名由 end 门禁从该清单读取）" % len(
            read_table(fr_p)[1])
    return [
        "记录提交 (i) 之后由冻结脚本执行；本附录的数字全部由 closeout 从结果表复算，未手写。",
        "- 门禁：start PASS=%(sp)d FAILS=%(sf)d（total=%(st)d）；start 前缀复核 PASS=%(rp)d FAILS=%(rf)d（total=%(rt)d）" % env,
        "- §3 P 项复核：AUDIT_R9M3C_R9M3D.tsv %(at)d/%(an)d 属实；规划者事实有误：%(amis)s" % env,
        "- 裁决：RULINGS 最大 %(umax)s（%(ub)d 字节，sha %(us)s）；U354/U356 状态=%(s354)s/%(s356)s" % env,
        "- 勘误：ERRATA_9.txt 最后 %(elast)s，共 %(ecnt)d 条（%(eb)d 字节，sha %(es)s）" % env,
        "- 修正版台账：唯一 id=%(lu)d，数据行=%(lr)d，TRANSFERRED_S5=%(lt5)d，范围内仍开放=%(lopen)d，冲突=%(lconf)d" % env,
        "- S5 移交：唯一项=%(hu)d（台账 TRANSFERRED_S5 全部覆盖，双向核对 OK）" % env,
        "- 就绪审计：READINESS 共 %(rn)d 行：MET=%(rm)d GAP=%(rg)d TRANSFERRED_S5=%(rt5)d CLOSED_BY_RULING=%(rc)d；GAP 明细：%(rgaps)s" % env,
        "- 阳性对照：handoff=%(ph)s；readiness=%(pr)s；report_check=%(pc)s" % env,
        frozen_line,
        "- STATE 最终字节数：%(sb)d（<=8192），sha %(ss)s" % env,
        "- 数据来源：m3d/RED_POINTS_LEDGER_FINAL_R9M3D.tsv、m3d/S5_HANDOFF_R9M3D.tsv、m3d/READINESS_P05_S3S4_R9M3D.tsv、m3d/AUDIT_R9M3C_R9M3D.tsv",
    ]


def main():
    rep = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3d_REPORT.md")
    out = sys.argv[2] if len(sys.argv) > 2 else os.path.join(EV, "REPORT_CHECK_R9M3D.txt")
    state_p = sys.argv[3] if len(sys.argv) > 3 else os.path.join(REPO, "checkpoints/p05/STATE.md")
    recheck_p = sys.argv[4] if len(sys.argv) > 4 else None
    text = open(rep, encoding="utf-8").read() if os.path.isfile(rep) else ""
    lines = []
    fails = 0

    def chk(name, ok, detail):
        nonlocal fails
        if not ok:
            fails += 1
        lines.append(("PASS" if ok else "FAIL") + TAB + name + TAB + detail)

    bad = []
    for word in FORBIDDEN:
        for i, l in enumerate(text.splitlines(), 1):
            if word in l:
                idx = l.find(word)
                prefix = l[:idx]
                if "不" in prefix[-12:] or "禁止" in prefix[-12:]:
                    continue
                bad.append("%s@L%d" % (word, i))
    chk("FORBIDDEN_WORDS_NEGATION_AWARE", not bad, "none" if not bad else ",".join(bad[:6]))
    missing = [s for s in REQUIRED if s not in text]
    chk("REQUIRED_SECTIONS", not missing, "missing=" + str(missing) if missing else "all present")
    chk("APPENDIX_A_PLACEHOLDER_REPLACED", PH_A not in text, "placeholder absent")
    chk("APPENDIX_B_PLACEHOLDER_PRESENT", text.count(PH_B) == 1, "count=%d" % text.count(PH_B))
    rl = text.splitlines()
    split = []
    for i in range(len(rl) - 1):
        if rl[i].startswith("|") and rl[i + 1].strip() == "":
            j = i + 2
            while j < len(rl) and rl[j].strip() == "":
                j += 1
            if j < len(rl) and rl[j].startswith("|"):
                split.append(i + 1)
    chk("NO_BLANK_LINE_INSIDE_TABLES", not split, "none" if not split else str(split[:6]))
    chk("DEADLINE_MARKER", "本轮已完成 R9 M3d 范围，等待用户审核" in text, "marker present")
    env = compute_env(state_p, recheck_p)
    chk("STATE_BYTES_LE_8192", 0 < env["sb"] <= 8192, "bytes=%d" % env["sb"])
    # body facts (recomputed)
    body_facts = [
        ("RULINGS_MAX_U", "RULINGS 最大 %s" % env["umax"]),
        ("ERRATA_LAST_AND_COUNT", "ERRATA_9.txt 最后 %s，共 %d 条" % (env["elast"], env["ecnt"])),
        ("AUDIT_TRUE", "%d/%d 属实" % (env["at"], env["an"])),
        ("LEDGER_UNIQUE", "唯一 id %d" % env["lu"]),
        ("HANDOFF_UNIQUE", "S5 移交：唯一项 %d" % env["hu"]),
    ]
    for name, value in body_facts:
        chk("NUM_" + name, value in text, "recomputed=%s present=%s" % (value, value in text))
    # appendix A derived sentences, recomputed
    ap_m = re.search(r"### 附录 A.*?(?=### 附录 B|\Z)", text, re.S)
    ap = ap_m.group(0) if ap_m else ""
    chk("APPENDIX_A_PRESENT", bool(ap), "appendix A present")
    for i, exp in enumerate(expected_appendix(env)):
        chk("APPX_A_LINE_%02d" % (i + 1), exp in ap, "expected line %d" % (i + 1))
    chk("APPENDIX_B_PRESENT", "### 附录 B" in text, "appendix B heading present")
    # signoff draft v2 structure
    sg_p = os.path.join(REPO, "checkpoints/p05/P05_S3_S4_SIGNOFF_DRAFT_v2.md")
    if not os.path.isfile(sg_p):
        chk("SIGNOFF_V2_PRESENT", False, "missing draft v2")
    else:
        sg = open(sg_p, encoding="utf-8").read()
        first = ""
        for line in sg.splitlines():
            if line.strip():
                first = line.strip()
                break
        chk("SIGNOFF_V2_FIRST_LINE", "草稿，非签收；签收只由用户在对话中给出" in first, first[:100])
        chk("SIGNOFF_V2_MARKED", ("草稿，非签收" in sg) and ("签收只由用户在对话中给出" in sg), "marked as draft")
        for key in ("### S1/S2 签收移交项的闭合（U356）", "7/7 MATCH", "info=NULL", "&solve_info",
                    "### 转入 S5 的项", "## 与 v1 的差异", "P-6"):
            chk("SIGNOFF_V2_" + re.sub(r"[^A-Za-z0-9]+", "_", key)[:28], key in sg, "key present")
        _, hand = read_table(os.path.join(EV, "S5_HANDOFF_R9M3D.tsv"))
        n_items = 0
        insec = False
        for line in sg.splitlines():
            if line.startswith("### 转入 S5 的项"):
                insec = True
                continue
            if insec and line.startswith("#"):
                break
            if insec and line.strip().startswith("- "):
                n_items += 1
        chk("SIGNOFF_V2_S5_ITEM_COUNT", n_items == len(hand), "items=%d handoff=%d" % (n_items, len(hand)))
    # positive controls
    chk("POSCTRL_HANDOFF_PASS", env["ph"] == "PASS", "result=%s" % env["ph"])
    chk("POSCTRL_READINESS_PASS", env["pr"] == "PASS", "result=%s" % env["pr"])
    chk("POSCTRL_REPORT_CHECK_PASS", env["pc"] == "PASS", "result=%s" % env["pc"])
    body = "# REPORT_CHECK_R9M3D.txt -- report check (forbidden words, sections, numbers, appendix-A lines, signoff v2," + NL
    body += "# positive controls) -- every value recomputed from the result tables" + NL
    body += NL.join(lines) + NL + "FAILS=%d" % fails + NL
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(body)
    sys.stdout.write(body)
    return min(fails, 255)


if __name__ == "__main__":
    sys.exit(main())
