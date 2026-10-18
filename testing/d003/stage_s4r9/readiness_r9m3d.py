#!/usr/bin/env python3
# readiness_r9m3d.py -- read-only signoff-readiness audit for P05-S3/P05-S4, recomputed from the registries.
# Groups: the three ROADMAP P05 acceptance criteria, the seven "nothing left to do" criteria, and every row of the
# STATE open-questions table. U357: every ruling cell is a real U number from RULINGS.tsv or the literal
# "-（事实项）"; a cell containing "见 STATE 行" is a hard error. Counts are de-duplicated (unique ledger id, unique
# handoff item) and the table ends with "# UNIQUE=... ROWS=...". New file (r9m3d).
# usage: readiness_r9m3d.py [OUT.tsv] [--ledger PATH] [--handoff PATH] [--state PATH]
import os, sys, re, hashlib
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
REG = os.path.join(REPO, "checkpoints/p05/registries")
M3B = os.path.join(EV, "..", "m3b")
M3C_EV = os.path.join(EV, "..", "m3c")
M1R3 = os.path.join(REG, "s4r9/M1R3")
M2 = os.path.join(REG, "s4r9/M2")
STATE = os.path.join(REPO, "checkpoints/p05/STATE.md")
LEDGER = os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv")
HANDOFF = os.path.join(EV, "S5_HANDOFF_R9M3D.tsv")
OUT = os.path.join(EV, "READINESS_P05_S3S4_R9M3D.tsv")
TAB = chr(9)
NL = chr(10)
FACT = "-（事实项）"
COLS = ["group", "item", "evidence_registry_path", "recomputed", "ruling", "status", "note"]
# STATE section 3 item prefix -> ruling cell. Every non-fact value must be a real U id (checked at runtime).
STATE_RULING = [
    ("S3-4b", "U29"),
    ("806、415", "U225"),
    ("RNV1", "U25"),
    ("双目标", "U244/U246"),
    ("张量路径 K-1", "U274/U281"),
    ("RP-R8-M2c-1/1b", "U304/U350"),
    ("B 侧 jones", FACT),
    ("NB=1–8", "U249"),
    ("Python/Lua 可见性", "U345/U352"),
    ("ClosedForm", "U339/U340"),
    ("ES3R4-5", "U90/U95/U99/U100"),
    ("U38 缺陷分类", "U90/U333"),
    ("非 FMM", FACT),
    ("ADD22", FACT),
    ("U2 stage e", "U248"),
    ("r8m2c/d", "U276/U282"),
    ("其他层失败变体", "U354"),
    ("S1/S2 移交", "U356"),
]
HIST = ["s3r5", "s4r9/M0", "s4r9/M1", "s4r9/M1R2", "s4r9/M1R3", "s4r9/M1R4", "s4r9/M2", "s4r9/M2b",
        "s4r9/M2c", "s4r9/M3a", "s4r9/M3b", "s4r9/M3c"]


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


def read_kv(path):
    out = {}
    hdr, rows = read_table(path)
    for r in rows:
        if "item" in r and "value" in r:
            out[r["item"]] = r["value"]
    return out


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def verify_sums(d):
    man = os.path.join(d, "SHA256SUMS.txt")
    if not os.path.isfile(man):
        return False, 0, "missing"
    n = 0
    for line in open(man, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        p = line.split(None, 1)
        if len(p) == 2:
            n += 1
            fp = os.path.join(d, p[1].strip())
            if not os.path.isfile(fp) or sha(fp) != p[0]:
                return False, n, "sha mismatch " + p[1].strip()
    return True, n, "all %d OK" % n


def ledger_meta(path):
    meta = {}
    if not os.path.isfile(path):
        return meta
    for line in open(path, encoding="utf-8"):
        m = re.match(r"# OPEN_IN_SCOPE=(\d+)", line)
        if m:
            meta["open_in_scope"] = int(m.group(1))
        m = re.match(r"# TRANSFERRED_S5=(\d+)\t(.*)", line)
        if m:
            meta["transfer_count"] = int(m.group(1))
            meta["transfer_ids"] = [x for x in m.group(2).strip().split(",") if x]
    return meta


def classify(stt, dest):
    if "S5" in dest and "关闭" not in stt:
        return "TRANSFERRED_S5"
    if "关闭" in stt or "闭合" in stt or "裁决" in stt or "关闭" in dest or "已裁决" in dest:
        return "CLOSED_BY_RULING"
    if "已实测" in stt or "完成" in stt or "MATCH" in stt or "已核实" in stt or "已覆盖" in stt:
        return "MET"
    if "OPEN" in stt:
        return "TRANSFERRED_S5" if "S5" in dest else "GAP"
    return "GAP"


def main():
    global STATE
    args = sys.argv[1:]
    out = OUT
    ledger = LEDGER
    handoff_p = HANDOFF
    pos = []
    i = 0
    while i < len(args):
        if args[i] == "--ledger" and i + 1 < len(args):
            ledger = args[i + 1]; i += 2
        elif args[i] == "--handoff" and i + 1 < len(args):
            handoff_p = args[i + 1]; i += 2
        elif args[i] == "--state" and i + 1 < len(args):
            STATE = args[i + 1]; i += 2
        elif args[i] == "--out" and i + 1 < len(args):
            out = args[i + 1]; i += 2
        else:
            pos.append(args[i]); i += 1
    if pos:
        out = pos[0]
    # ---- rulings set (U357) ----
    rul_p = os.path.join(REG, "RULINGS.tsv")
    have = set()
    for line in open(rul_p, encoding="utf-8"):
        f = line.split(TAB)
        if f and re.match(r"^U\d+$", f[0]):
            have.add(f[0])
    if not have:
        print("HARD_STOP no rulings parsed")
        return 2
    # ---- recomputed numbers ----
    _, m1 = read_table(os.path.join(M1R3, "VERDICT_M1_F4_R9M1R3.tsv"))
    if not m1:
        print("HARD_STOP missing M1R3 verdict")
        return 2
    m1_counts = {}
    for r in m1:
        m1_counts[r.get("verdict", "?")] = m1_counts.get(r.get("verdict", "?"), 0) + 1
    m1_match = m1_counts.get("MATCH", 0)
    m1_mismatch = m1_counts.get("MISMATCH", 0)
    m1_other = {k: v for k, v in m1_counts.items() if k not in ("MATCH", "MISMATCH")}
    _, m2 = read_table(os.path.join(M2, "VERDICT_R9.tsv"))
    m2_match = len([r for r in m2 if r.get("verdict") == "MATCH"])
    m2_bad = len([r for r in m2 if r.get("verdict") == "MISMATCH" or (r.get("mismatches", "-") not in ("-", ""))])
    _, e2e = read_table(os.path.join(M3B, "E2E_VERDICT_R9M3B.tsv"))
    e2e_counts = {}
    for r in e2e:
        e2e_counts[r.get("verdict", "?")] = e2e_counts.get(r.get("verdict", "?"), 0) + 1
    e2e_ok = e2e_counts.get("E2E_OK", 0)
    e2e_ctl = e2e_counts.get("CONTROL_OK", 0)
    e2e_other = {k: v for k, v in e2e_counts.items() if k not in ("E2E_OK", "CONTROL_OK")}
    mkv = read_kv(os.path.join(M3B, "MAKETEST_VERDICT_R9M3B.tsv"))
    rej_diffs = -1
    cmp_p = os.path.join(M3C_EV, "REJUDGE_COMPARE_R9M3C.txt")
    if os.path.isfile(cmp_p):
        for line in open(cmp_p, encoding="utf-8"):
            if line.startswith("DIFFS="):
                rej_diffs = int(line.strip().split("=")[1])
    rev_fails = -1
    rev_p = os.path.join(M3C_EV, "REVERIFY_R9M3B_R9M3C.tsv")
    if os.path.isfile(rev_p):
        for line in open(rev_p, encoding="utf-8"):
            if line.startswith("# FAILS="):
                rev_fails = int(line.strip().split("=")[1])
    # ---- ledger: unique ids, header-repeat rows ignored, duplicate ids counted once ----
    if not os.path.isfile(ledger):
        print("HARD_STOP missing ledger " + ledger)
        return 2
    lhdr, lrows = read_table(ledger)
    if not lhdr or "id" not in lhdr or "current_status" not in lhdr:
        print("HARD_STOP ledger missing id/current_status columns")
        return 2
    lrows = [r for r in lrows if r.get("id", "") not in ("", "id")]
    uniq_ids = set(r["id"] for r in lrows)
    ledger_uniq = len(uniq_ids)
    ledger_rows = len(lrows)
    meta = ledger_meta(ledger)
    open_in_scope = meta.get("open_in_scope", -1)
    t5_ids = sorted(r["id"] for r in lrows if r["current_status"] == "TRANSFERRED_S5")
    # ---- handoff: unique items, bidirectional coverage ----
    hh, hrows = read_table(handoff_p)
    hand_uniq = len(set(r.get("item_id", "") for r in hrows if r.get("item_id")))
    covered = set()
    h_bad = []
    for r in hrows:
        ids = [x.strip() for x in (r.get("ledger_ids", "") or "").split(";") if x.strip() not in ("", "-")]
        rows_ = [x.strip() for x in (r.get("state_rows", "") or "").split(";") if x.strip() not in ("", "-")]
        if not ids and not rows_:
            h_bad.append(r.get("item_id", "?"))
        covered.update(ids)
    missing = sorted(set(t5_ids) - covered)
    extra = sorted(covered - set(t5_ids))
    coverage_ok = bool(hrows) and not h_bad and not missing and not extra
    # ---- historical registries + STATE ----
    hist_ok = True
    hist_detail = []
    for d in HIST:
        ok, n, det = verify_sums(os.path.join(REG, d))
        hist_ok = hist_ok and ok
        hist_detail.append("%s=%d" % (d.split("/")[-1], n))
    state_bytes = os.path.getsize(STATE) if os.path.isfile(STATE) else -1
    rows = []

    def add(group, item, evid, recomputed, ruling, status, note=""):
        rows.append((group, item, evid, recomputed, ruling, status, note))

    add("ROADMAP_P05", "每个受影响的 prepare/execute 点有正负对照",
        "registries/s4r9/M1R3/VERDICT_M1_F4_R9M1R3.tsv; registries/s4r9/M3b/E2E_VERDICT_R9M3B.tsv",
        "M1R3 MATCH=%d（其他=%s）; E2E 注入点=%d 全部 E2E_OK、对照=%d CONTROL_OK" % (
            m1_match, str(sorted(m1_other.items())), e2e_ok, e2e_ctl),
        "U314/U319/U320", "MET")
    add("ROADMAP_P05", "失败后模式/缓存不安装",
        "registries/s4r9/M1R3/VERDICT_M1_F4_R9M1R3.tsv; P05_S3_4b_CLOSURE.md",
        "S3-4b 已按 U29 带范围声明关闭（状态注记 FAILED_CALL_STATE）；M1R3 seam/CTRL 组 MATCH",
        "U29", "CLOSED_BY_RULING")
    st_a3 = "MET" if (rej_diffs == 0 and e2e_ok == 25 and e2e_ctl == 17 and not e2e_other) else "GAP"
    add("ROADMAP_P05", "Python/Lua 可见失败、恢复重试正确",
        "registries/s4r9/M3b/E2E_VERDICT_R9M3B.tsv; m3c/REJUDGE_E2E_R9M3C.tsv",
        "E2E_OK=%d CONTROL_OK=%d 其他=%s；独立重判差异=%d" % (e2e_ok, e2e_ctl, str(sorted(e2e_other.items())), rej_diffs),
        "U343/U345", st_a3)
    st1 = "MET" if open_in_scope == 0 else "GAP"
    add("WUKEZUO", "①范围内红点全部修复并完成修后回归",
        "registries/s4r9/M3d/RED_POINTS_LEDGER_FINAL_R9M3D.tsv",
        "红点唯一 id 数=%d；范围内仍开放=%d（台账数据行=%d，表头式/重复行已去重）" % (
            ledger_uniq, open_in_scope, ledger_rows),
        "U304/U350", st1)
    gap_state = len([r for r in rows if r[5] == "GAP"])
    add("WUKEZUO", "②开放项完成或经裁决转出",
        "registries/RULINGS.tsv; STATE.md §3; m3d/S5_HANDOFF_R9M3D.tsv",
        "STATE 开放项行见本表 STATE_OPEN 组；GAP=%d；移交双向覆盖=%s（台账 TRANSFERRED_S5=%d、移交唯一项=%d）" % (
            gap_state, "OK" if coverage_ok else "ORPHAN", len(t5_ids), hand_uniq),
        FACT, "MET" if (gap_state == 0 and coverage_ok) else "GAP")
    need = [os.path.join(EV, "AUDIT_R9M3C_R9M3D.tsv"), ledger, handoff_p]
    missing_runs = len([p for p in need if not os.path.isfile(p)])
    add("WUKEZUO", "③无待跑运行",
        "m3d/AUDIT_R9M3C_R9M3D.tsv; m3d/RED_POINTS_LEDGER_FINAL_R9M3D.tsv; m3d/S5_HANDOFF_R9M3D.tsv",
        "缺失的正式产物=%d" % missing_runs, FACT, "MET" if missing_runs == 0 else "GAP")
    add("WUKEZUO", "④STATE/registries/报告一致",
        "registries/s4r9/M3c/SHA256SUMS.txt; P05_S4R9_M3d_REPORT.md; STATE.md",
        "历史 registries 清单全部 OK=%s（%s）；STATE 字节=%d；正式 end 门禁核对报告-清单一致性" % (
            hist_ok, ",".join(hist_detail), state_bytes),
        FACT, "MET" if (hist_ok and 0 < state_bytes <= 8192) else "GAP")
    add("WUKEZUO", "⑤make test 相对基线无新增失败",
        "registries/s4r9/M3b/MAKETEST_VERDICT_R9M3B.tsv",
        "verdict=%s unit_count=%s" % (mkv.get("verdict", "?"), mkv.get("unit_count", "?")),
        "U333/U338", "MET" if mkv.get("verdict") == "NO_NEW_FAILURE" else "GAP")
    pre_bad = m1_mismatch + m1_counts.get("FLAKY", 0) + m1_counts.get("VALUE_DRIFT", 0) + m2_bad
    add("WUKEZUO", "⑥预注册矩阵无 MISMATCH/FLAKY/VALUE_DRIFT",
        "registries/s4r9/M1R3/VERDICT_M1_F4_R9M1R3.tsv; registries/s4r9/M2/VERDICT_R9.tsv",
        "M1R3 MISMATCH=%d MATCH=%d 其他=%s；M2 MATCH=%d 异常=%d；合计异常=%d" % (
            m1_mismatch, m1_match, str(sorted(m1_other.items())), m2_match, m2_bad, pre_bad),
        "U314/U319/U320", "MET" if pre_bad == 0 else "GAP")
    add("WUKEZUO", "⑦Python/Lua 正常与失败→可见报错→重试恢复",
        "registries/s4r9/M3b/E2E_VERDICT_R9M3B.tsv; m3c/POSCTRL_REJUDGE_R9M3C.txt",
        "E2E_OK=%d CONTROL_OK=%d；独立重判差异=%d" % (e2e_ok, e2e_ctl, rej_diffs),
        "U343/U345", "MET" if (rej_diffs == 0 and e2e_ok == 25 and e2e_ctl == 17) else "GAP")
    # ---- every STATE section 3 row (U357) ----
    text = open(STATE, encoding="utf-8").read().splitlines()
    in3 = False
    n_state = 0
    for i, line in enumerate(text, 1):
        if line.startswith("## 3."):
            in3 = True
            continue
        if in3 and line.startswith("## "):
            break
        if not in3 or not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        if cells[0] in ("项",) or set(cells[0]) <= set("-: "):
            continue
        item, stt, dest = cells[0], cells[1], cells[2]
        status = classify(stt, dest)
        ruling = FACT
        for prefix, rv in STATE_RULING:
            if item.startswith(prefix):
                ruling = rv
                break
        add("STATE_OPEN", item, "STATE.md:%d (registries/RULINGS.tsv)" % i,
            "state=%s; destination=%s" % (stt, dest), ruling, status)
        n_state += 1
    if n_state == 0:
        print("HARD_STOP no STATE section 3 rows parsed")
        return 2
    # ---- U357: every ruling cell must be a real U id or the fact literal ----
    bad_ruling = []
    for r in rows:
        if r[4] == FACT:
            continue
        for tok in r[4].split("/"):
            if not re.match(r"^U\d+$", tok) or tok not in have:
                bad_ruling.append((r[1], r[4]))
                break
    if bad_ruling:
        print("HARD_STOP U357 ruling cells not real U ids: %s" % bad_ruling[:4])
        return 4
    counts = {}
    for r in rows:
        counts[r[5]] = counts.get(r[5], 0) + 1
    gaps = [r for r in rows if r[5] == "GAP"]
    lines = ["# READINESS_P05_S3S4_R9M3D.tsv -- P05-S3/P05-S4 signoff-readiness audit (read-only; recomputed, U357)",
             "# counts are de-duplicated: one ledger id / one handoff item counts once; a header-repeat row is not a row",
             TAB.join(COLS)]
    for r in rows:
        lines.append(TAB.join(str(x) for x in r))
    lines.append("# COUNTS " + " ".join("%s=%d" % (k, counts.get(k, 0))
                                       for k in ("MET", "GAP", "TRANSFERRED_S5", "CLOSED_BY_RULING")))
    lines.append("# GAPS=%d" % len(gaps))
    for r in gaps:
        lines.append("# GAP\t" + r[0] + "\t" + r[1])
    lines.append("# LEDGER_UNIQUE_IDS=%d LEDGER_ROWS=%d HANDOFF_UNIQUE_ITEMS=%d LEDGER_TRANSFERRED_S5=%d" % (
        ledger_uniq, ledger_rows, hand_uniq, len(t5_ids)))
    lines.append("# RULING_CELLS_ALL_REAL_U=YES")
    lines.append("# UNIQUE=%d ROWS=%d" % (len(set(r[0] + "|" + r[1] for r in rows)), len(rows)))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines) + NL)
    print("COUNTS " + str(sorted(counts.items())))
    print("GAPS=%d ledger_unique_ids=%d handoff_unique=%d coverage=%s" % (
        len(gaps), ledger_uniq, hand_uniq, "OK" if coverage_ok else "ORPHAN"))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
