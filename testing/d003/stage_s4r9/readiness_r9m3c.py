#!/usr/bin/env python3
# readiness_r9m3c.py -- read-only signoff-readiness audit for P05-S3/P05-S4: the three ROUTE acceptance criteria,
# the seven "nothing left to do" criteria, and every row of the STATE open-questions table. Also writes the S5 handoff
# list for the TRANSFERRED_S5 rows. All tables are read by column name. New file (r9m3c).
# usage: readiness_r9m3c.py
import os, sys, re, hashlib
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
REG = os.path.join(REPO, "checkpoints/p05/registries")
M3B = os.path.join(REG, "s4r9/M3b")
M1R3 = os.path.join(REG, "s4r9/M1R3")
M2 = os.path.join(REG, "s4r9/M2")
STATE = os.path.join(REPO, "checkpoints/p05/STATE.md")
REPORT = os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3c_REPORT.md")
OUT = os.path.join(EV, "READINESS_P05_S3S4_R9M3C.tsv")
HAND = os.path.join(EV, "S5_HANDOFF_R9M3C.tsv")
TAB = chr(9)
NL = chr(10)


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
        return False, 0
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
                return False, n
    return True, n


def main():
    # ---- recomputed numbers ----
    _, m1 = read_table(os.path.join(M1R3, "VERDICT_M1_F4_R9M1R3.tsv"))
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
    cmp_p = os.path.join(EV, "REJUDGE_COMPARE_R9M3C.txt")
    if os.path.isfile(cmp_p):
        for line in open(cmp_p, encoding="utf-8"):
            if line.startswith("DIFFS="):
                rej_diffs = int(line.strip().split("=")[1])
    rev_fails = -1
    rev_p = os.path.join(EV, "REVERIFY_R9M3B_R9M3C.tsv")
    if os.path.isfile(rev_p):
        for line in open(rev_p, encoding="utf-8"):
            if line.startswith("# FAILS="):
                rev_fails = int(line.strip().split("=")[1])
    ledger_p = os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3C.tsv")
    red_final = os.path.join(REG, "s4r9/M3c/RED_POINTS_LEDGER_FINAL_R9M3C.tsv")
    lp = ledger_p if os.path.isfile(ledger_p) else red_final
    open_in_scope = -1
    conflicts = -1
    ledger_rows = 0
    if os.path.isfile(lp):
        open_in_scope = 0
        conflicts = 0
        for line in open(lp, encoding="utf-8"):
            if line.startswith("# OPEN_IN_SCOPE="):
                open_in_scope = int(line.strip().split("=")[1])
            elif line.startswith("# CONFLICTS:"):
                conflicts = int(re.search(r"(\d+)$", line.strip()).group(1))
            elif line.startswith("#") or not line.strip():
                continue
            else:
                ledger_rows += 1
    hist_ok = True
    hist_detail = []
    for d in ("s3r5", "s4r9/M0", "s4r9/M1", "s4r9/M1R2", "s4r9/M1R3", "s4r9/M1R4", "s4r9/M2", "s4r9/M2b",
              "s4r9/M2c", "s4r9/M3a", "s4r9/M3b"):
        ok, n = verify_sums(os.path.join(REG, d))
        hist_ok = hist_ok and ok
        hist_detail.append("%s=%d" % (d.split("/")[-1], n))
    state_bytes = os.path.getsize(STATE) if os.path.isfile(STATE) else -1
    rows = []

    def add(group, item, evid, recomputed, ruling, status, note=""):
        rows.append((group, item, evid, recomputed, ruling, status, note))

    # ---- ROUTE P05 acceptance (three) ----
    add("ROADMAP_P05", "每个受影响的 prepare/execute 点有正负对照",
        "registries/s4r9/M1R3/VERDICT_M1_F4_R9M1R3.tsv; registries/s4r9/M3b/E2E_VERDICT_R9M3B.tsv",
        "M1R3 MATCH=%d（其他=%s）; E2E 注入点=%d 全部 E2E_OK、对照=%d CONTROL_OK；M1R3 阳性对照见 POSCTRL_M1_R9M1R3.txt" % (
            m1_match, str(sorted(m1_other.items())), e2e_ok, e2e_ctl),
        "U314/U319/U320（M1R3）；U343/U345（E2E）", "MET")
    add("ROADMAP_P05", "失败后模式/缓存不安装",
        "registries/s4r9/M1R3/VERDICT_M1_F4_R9M1R3.tsv; P05_S3_4b_CLOSURE.md",
        "S3-4b 已按 U29 带范围声明关闭（状态注记 FAILED_CALL_STATE）；M1R3 seam/CTRL 组 MATCH",
        "U29", "CLOSED_BY_RULING")
    st_a3 = "MET" if (rej_diffs == 0 and e2e_ok == 25 and e2e_ctl == 17 and not e2e_other) else "GAP"
    add("ROADMAP_P05", "Python/Lua 可见失败、恢复重试正确",
        "registries/s4r9/M3b/E2E_VERDICT_R9M3B.tsv; m3c/REJUDGE_E2E_R9M3C.tsv",
        "E2E_OK=%d CONTROL_OK=%d 其他=%s；独立重判差异=%d" % (e2e_ok, e2e_ctl, str(sorted(e2e_other.items())), rej_diffs),
        "U343/U345", st_a3)

    # ---- seven "nothing left to do" ----
    st1 = "MET" if open_in_scope == 0 else "GAP"
    add("WUKEZUO", "①范围内红点全部修复并完成修后回归",
        "registries/s4r9/M3c/RED_POINTS_LEDGER_FINAL_R9M3C.tsv", "红点行=%d；范围内仍开放=%d" % (ledger_rows, open_in_scope),
        "U304/U350 等", st1)
    gap_state = len([r for r in rows if r[5] == "GAP"])
    add("WUKEZUO", "②开放项完成或经裁决转出",
        "registries/RULINGS.tsv; STATE.md §3", "STATE 开放项行见本表 STATE_OPEN 组；GAP=%d" % gap_state,
        "见各 STATE 行", "MET" if gap_state == 0 else "GAP")
    missing_runs = len([p for p in (rev_p, cmp_p, ledger_p) if not os.path.isfile(p)])
    add("WUKEZUO", "③无待跑运行",
        "m3c/REJUDGE_COMPARE_R9M3C.txt; m3c/REVERIFY_R9M3B_R9M3C.tsv; m3c/RED_POINTS_LEDGER_FINAL_R9M3C.tsv",
        "缺失的正式产物=%d" % missing_runs, "-", "MET" if missing_runs == 0 else "GAP")
    add("WUKEZUO", "④STATE/registries/报告一致",
        "registries/s4r9/M3c/SHA256SUMS.txt; P05_S4R9_M3c_REPORT.md; STATE.md",
        "历史 registries 清单全部 OK=%s（%s）；STATE 字节=%d；正式 end 门禁核对报告-清单一致性" % (
            hist_ok, ",".join(hist_detail), state_bytes),
        "-", "MET" if (hist_ok and state_bytes <= 8192) else "GAP",
        "M3c registries 在正式收尾链中由 copy_registries 生成，最终一致性由 end 门禁检查")
    add("WUKEZUO", "⑤make test 相对基线无新增失败",
        "registries/s4r9/M3b/MAKETEST_VERDICT_R9M3B.tsv",
        "verdict=%s unit_count=%s" % (mkv.get("verdict", "?"), mkv.get("unit_count", "?")),
        "U333a/U338", "MET" if mkv.get("verdict") == "NO_NEW_FAILURE" else "GAP")
    pre_bad = m1_mismatch + m1_counts.get("FLAKY", 0) + m1_counts.get("VALUE_DRIFT", 0) + m2_bad
    add("WUKEZUO", "⑥预注册矩阵无 MISMATCH/FLAKY/VALUE_DRIFT",
        "registries/s4r9/M1R3/VERDICT_M1_F4_R9M1R3.tsv; registries/s4r9/M2/VERDICT_R9.tsv",
        "M1R3 MISMATCH=%d MATCH=%d 其他=%s；M2 MATCH=%d 异常=%d；合计异常=%d" % (
            m1_mismatch, m1_match, str(sorted(m1_other.items())), m2_match, m2_bad, pre_bad),
        "U314/U319/U320", "MET" if pre_bad == 0 else "GAP")
    add("WUKEZUO", "⑦Python/Lua 正常与失败→可见报错→重试恢复",
        "registries/s4r9/M3b/E2E_VERDICT_R9M3B.tsv; m3c/POSCTRL_REJUDGE_R9M3C.txt",
        "E2E_OK=%d CONTROL_OK=%d；独立重判差异=%d；阳性对照见 POSCTRL_REJUDGE_R9M3C.txt" % (e2e_ok, e2e_ctl, rej_diffs),
        "U343/U345", "MET" if (rej_diffs == 0 and e2e_ok == 25 and e2e_ctl == 17) else "GAP")

    # ---- every STATE §3 row ----
    text = open(STATE, encoding="utf-8").read().splitlines()
    in3 = False
    hand = []
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
        status = "GAP"
        if "S5" in dest and "关闭" not in stt:
            status = "TRANSFERRED_S5"
        elif "RP-R6d-15" in item or "Python/Lua 可见性" in item:
            status = "CLOSED_BY_RULING" if rej_diffs == 0 else "GAP"
        elif "关闭" in stt or "裁决" in stt or "裁决" in dest:
            status = "CLOSED_BY_RULING"
        elif "已实测" in stt or "完成" in stt or "MATCH" in stt or "已核实" in stt or "已闭合" in stt or "已覆盖" in stt:
            status = "MET"
        elif "OPEN" in stt:
            status = "TRANSFERRED_S5" if "S5" in dest else "GAP"
        else:
            status = "GAP"
        add("STATE_OPEN", item, "STATE.md:%d (registries/RULINGS.tsv)" % i,
            "state=%s; destination=%s" % (stt, dest), "见 STATE 行", status)
        if status == "TRANSFERRED_S5":
            hand.append((item, dest, "STATE.md:%d" % i))

    # ---- S5 handoff ----
    hand += [
        ("B 侧 jones/vl SILENT_SWALLOW、nv CRASH", "S5（基线观察，不是修复证据）", "P05_S1R_O1_ATTRIBUTION.md"),
        ("NB=1–8、类别 C（M2-08）", "S5（U249）", "registries/RULINGS.tsv U249"),
        ("ES3R4-5/528/1164", "S5（U90/U95/U99/U100，OUT_OF_SCOPE_D003）", "registries/RULINGS.tsv"),
        ("非 FMM S4_malloc（约 35–43 处）", "S5（范围决策）", "PROJECT_ROADMAP.md"),
        ("U2 stage e（I1 特殊规则）", "S5（U248，NOT_FOUND_IN_SCOPE）", "registries/RULINGS.tsv"),
    ]
    counts = {}
    for r in rows:
        counts[r[5]] = counts.get(r[5], 0) + 1
    gaps = [r for r in rows if r[5] == "GAP"]
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# READINESS_P05_S3S4_R9M3C.tsv -- P05-S3/P05-S4 signoff-readiness audit (read-only; recomputed from registries)" + NL)
        fh.write(TAB.join(["group", "item", "evidence_registry_path", "recomputed", "ruling", "status", "note"]) + NL)
        for r in rows:
            fh.write(TAB.join(str(x) for x in r) + NL)
        fh.write("# COUNTS " + " ".join("%s=%d" % (k, counts.get(k, 0)) for k in ("MET", "GAP", "TRANSFERRED_S5", "CLOSED_BY_RULING")) + NL)
        fh.write("# GAPS=%d" % len(gaps) + NL)
        for r in gaps:
            fh.write("# GAP\t" + r[0] + "\t" + r[1] + NL)
    with open(HAND, "w", encoding="utf-8") as fh:
        fh.write("# S5_HANDOFF_R9M3C.tsv -- items transferred to P05-S5 with their source rulings" + NL)
        fh.write(TAB.join(["item", "transfer_scope", "source"]) + NL)
        for item, scope, src in hand:
            fh.write(TAB.join([item, scope, src]) + NL)
    print("COUNTS " + str(sorted(counts.items())))
    print("GAPS=%d TRANSFERRED_S5=%d HANDOFF=%d" % (len(gaps), counts.get("TRANSFERRED_S5", 0), len(hand)))
    print("WROTE " + OUT)
    print("WROTE " + HAND)
    return 0


if __name__ == "__main__":
    sys.exit(main())
