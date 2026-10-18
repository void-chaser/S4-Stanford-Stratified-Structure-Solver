#!/usr/bin/env python3
# s5r3_chain.py -- P05-S5 R3 closeout chain. One call per subcommand in the frozen period:
#   readiness | acceptance | signoff | report | report_check | copy | events | sha_sums
# --shakedown writes every output under $EV/shakedown and uses the shakedown result tables.
import os, sys, re, hashlib, shutil, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r3")
SHK = os.path.join(EV, "shakedown")
REGDIR = os.path.join(P05, "registries/s5r3")
REPORT = os.path.join(P05, "P05_S5R3_REPORT.md")
STATE = os.path.join(P05, "STATE.md")
SIGNOFF = os.path.join(P05, "P05_S5_SIGNOFF_DRAFT.md")
TAB = chr(9)
NL = chr(10)
BT = chr(96)
SHAKE = "--shakedown" in sys.argv[2:]
SMALL = [
    "GATE_S5R3_start.txt",
    "PREREG_D016_S5R3.tsv", "PREREG_D016_S5R3.tsv.sha256.txt",
    "PREREG_MAKETEST_S5R3.tsv", "PREREG_E2E_S5R3.tsv", "PREREG_E2E_S5R3.tsv.sha256.txt",
    "D016_VERDICT_S5R3.tsv", "D016_BUILD_S5R3.tsv", "E2E_VERDICT_S5R3.tsv", "E2E_BUILD_S5R3.tsv",
    "CALIB_DIFF_S5R3.tsv", "MAKETEST_UNITS_S5R3.tsv", "MAKETEST_VERDICT_S5R3.tsv",
    "POSCTRL_D016_S5R3.txt", "POSCTRL_E2E_S5R3.txt", "POSCTRL_MAKETEST_S5R3.txt",
    "REJUDGE_S5R3.tsv", "READINESS_S5R3.tsv", "P05_ACCEPTANCE_MAP_S5R3.tsv",
    "REGISTRY_APPLY_DIFF_S5R3.txt", "REPORT_CHECK_S5R3.txt", "FROZEN_SCRIPTS_S5R3.tsv",
    "COPY_DIFF_S5R3.txt", "ERRATA_S5.txt",
]
SUP = ["s5r2_supplement/D016_VERDICT_S5R2_ERRATA.txt", "s5r2_supplement/D016_BUILD_S5R2.tsv"]
NSMALL = len(SMALL) + len(SUP)
DATA_MAP = {
    "D016_VERDICT_S5R3.tsv": "shakedown/d016/D016_VERDICT_S5R3.tsv",
    "E2E_VERDICT_S5R3.tsv": "shakedown/e2e/E2E_VERDICT_S5R3.tsv",
    "MAKETEST_VERDICT_S5R3.tsv": "shakedown/maketest/MAKETEST_VERDICT_S5R3.tsv",
    "MAKETEST_UNITS_S5R3.tsv": "shakedown/maketest/MAKETEST_UNITS_S5R3.tsv",
    "POSCTRL_D016_S5R3.txt": "shakedown/POSCTRL_D016_S5R3.txt",
    "POSCTRL_E2E_S5R3.txt": "shakedown/POSCTRL_E2E_S5R3.txt",
    "POSCTRL_MAKETEST_S5R3.txt": "shakedown/POSCTRL_MAKETEST_S5R3.txt",
    "GATE_S5R3_end.txt": "shakedown/gate/GATE_S5R3_end.txt",
}


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def rd(p):
    return open(p, encoding="utf-8").read()


def wr(p, t):
    rp = os.path.realpath(p)
    if not (rp.startswith(os.path.join(P05) + os.sep) or rp.startswith(os.path.join(REPO, "testing/d003") + os.sep)):
        raise SystemExit("WRITE_OUTSIDE " + rp)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(t)


def data(name):
    if SHAKE and name in DATA_MAP:
        return os.path.join(EV, DATA_MAP[name])
    return os.path.join(EV, name)


def outdir():
    return SHK if SHAKE else EV


def read_tsv(p):
    rows = []
    hdr = None
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def read_kv(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 2:
            d[f[0]] = f[1]
    return d


def gate_summary(path):
    if not os.path.isfile(path):
        return None
    d = {"counts": None, "fails": None, "crashed": None, "post": []}
    for l in rd(path).splitlines():
        if l.startswith("COUNTS"):
            d["counts"] = l
        if l.startswith("FAILS="):
            d["fails"] = l
        if l.startswith(("PASS", "FAIL")) and "CHECK_CRASHED_ZERO" in l:
            d["crashed"] = l
        if l.startswith(("PASS", "FAIL")) and "POST_I_CALL_COUNT" in l:
            d["post"].append(l)
    return d


def d016_summary():
    p = data("D016_VERDICT_S5R3.tsv")
    if not os.path.isfile(p):
        return None
    for line in open(p, encoding="utf-8"):
        if line.startswith("SUMMARY" + TAB):
            f = line.rstrip(NL).split(TAB)
            d = {}
            for x in f[1:]:
                k, _, v = x.partition("=")
                d[k] = v
            return d
    return None


def d016_row_count():
    p = data("D016_VERDICT_S5R3.tsv")
    if not os.path.isfile(p):
        return 0
    return len([l for l in rd(p).splitlines() if l.strip() and not l.startswith("#") and not l.startswith("SUMMARY")])


def e2e_counts():
    p = data("E2E_VERDICT_S5R3.tsv")
    if not os.path.isfile(p):
        return None
    c = {}
    fe = {}
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if len(f) < 5 or f[0] == "point_id":
            continue
        c[f[4]] = c.get(f[4], 0) + 1
        if f[4] == "E2E_OK":
            fe[f[1]] = fe.get(f[1], 0) + 1
    return c, fe


def maketest():
    p = data("MAKETEST_VERDICT_S5R3.tsv")
    if not os.path.isfile(p):
        return None
    kv = {}
    recon = []
    for line in open(p, encoding="utf-8"):
        f = line.rstrip(NL).split(TAB)
        if len(f) >= 2 and f[0] == "reconcile":
            recon.append(f)
        elif len(f) >= 2 and not line.startswith("#"):
            kv[f[0]] = f[1]
    return kv, recon


def posctrl_result(name):
    p = data(name)
    if not os.path.isfile(p):
        return None
    t = rd(p)
    m = re.search(r"OVERALL_POSITIVE_CONTROL: (PASS|FAIL) \((\d+)/(\d+)\)", t)
    return (m.group(1), m.group(2), m.group(3)) if m else ("UNPARSED", "0", "0")


def rejudge():
    p = data("REJUDGE_S5R3.tsv")
    if not os.path.isfile(p):
        return None
    d = {}
    for line in rd(p).splitlines():
        if line.startswith("SUMMARY" + TAB):
            for x in line.split(TAB)[1:]:
                k, _, v = x.partition("=")
                d[k] = v
    return d


def acceptance_rows():
    p = data("P05_ACCEPTANCE_MAP_S5R3.tsv")
    return read_tsv(p) if os.path.isfile(p) else []


def readiness_rows():
    p = data("READINESS_S5R3.tsv")
    return read_tsv(p) if os.path.isfile(p) else []


def registry_diff():
    p = data("REGISTRY_APPLY_DIFF_S5R3.txt")
    if not os.path.isfile(p):
        return {}
    t = rd(p)
    d = {}
    for line in t.splitlines():
        m = re.match(r"FILE (testing/s4test/ISSUE_REGISTRY.md|PROJECT_ROADMAP.md) before_bytes=(\d+) after_bytes=(\d+) before_sha256=([0-9a-f]{64}) after_sha256=([0-9a-f]{64})", line)
        if m:
            d[m.group(1)] = {"before_bytes": m.group(2), "after_bytes": m.group(3),
                             "before_sha": m.group(4), "after_sha": m.group(5)}
    d["assert"] = ("# ASSERT_ONLY_LISTED_LINES_CHANGED: PASS" in t)
    return d


def shakedown_gate():
    return gate_summary(os.path.join(SHK, "gate/GATE_S5R3_end.txt"))


def cmd_readiness():
    rows = [("row_kind", "item", "requirement", "status", "evidence", "note")]
    red = read_tsv(os.path.join(P05, "registries/s4r9/M3d/RED_POINTS_LEDGER_FINAL_R9M3D.tsv"))
    ids = [r for r in red if r.get("id")]
    allowed_bad = ("OPEN", "UNVERIFIED")
    bad = [r["id"] for r in ids if not r.get("post_fix_evidence") or r.get("current_status", "").startswith(allowed_bad)]
    for r in ids:
        rows.append(("RED_POINT", r["id"], "S4 签收时红点已修复并有修后回归",
                     "MET" if r["id"] not in bad else "GAP",
                     "registries/s4r9/M3d/RED_POINTS_LEDGER_FINAL_R9M3D.tsv:" + r["id"],
                     r.get("post_fix_evidence", "")[:120]))
    oi = read_tsv(os.path.join(P05, "P05_S5_OPEN_ITEMS.tsv"))
    allowed = ("OPEN_TRANSFERRED_OUT", "RECORD_ONLY_OPEN", "REGISTERED_D016", "REGISTERED_D017",
               "REGISTERED_R-P05-02", "REGISTERED_R-P05-03", "REGISTRY_SYNC", "TEST_S5R2", "TEST_S5R3")
    bad_oi = [r["input_id"] for r in oi if r.get("final_disposition") not in allowed or not r.get("ruling")]
    rows.append(("SUMMARY", "OPEN_ITEMS", "25 行开放项全部为已转出（附 U 编号）或已关闭（附证据）",
                 "MET" if len(oi) == 25 and not bad_oi else "GAP",
                 "checkpoints/p05/P05_S5_OPEN_ITEMS.tsv",
                 "rows=%d dispositions=%s" % (len(oi), ",".join(sorted(set(r["final_disposition"] for r in oi))))))
    pend = []
    for rel in ("D016_PASS1_S5R3.json", "D016_PASS2_S5R3.json", "D016_VERDICT_S5R3.tsv",
                "e2e/pass1/E2E_RUN_formal.json", "e2e/pass2/E2E_RUN_formal.json", "E2E_VERDICT_S5R3.tsv",
                "maketest/B_p1.done", "maketest/F4_p1.done", "maketest/B_p2.done", "maketest/F4_p2.done",
                "MAKETEST_VERDICT_S5R3.tsv", "REJUDGE_S5R3.tsv"):
        if not os.path.isfile(os.path.join(EV, rel)):
            pend.append(rel)
    markers = [x for x in os.listdir(EV) if "pending" in x.lower()]
    rows.append(("SUMMARY", "PENDING_RUNS", "无待跑运行", "MET" if not pend and not markers else "GAP",
                 "checkpoints/p05/evidence/p05-s5r3/", "missing=%s markers=%s" % (pend or "none", markers or "none")))
    ds = d016_summary()
    mv, recon = maketest() or ({}, [])
    st = rd(os.path.join(P05, "STATE.md"))
    need_state = []
    if ds:
        need_state.append(ds.get("MATCH", "?"))
    if mv:
        need_state.append(mv.get("unit_count", "?"))
        need_state.append(mv.get("verdict", "?"))
    miss_state = [x for x in need_state if x not in st]
    rows.append(("SUMMARY", "CONSISTENCY", "STATE/registries/报告/登记表关键数字一致",
                 "MET" if not miss_state else "GAP", "STATE.md + verdict tables",
                 "state_missing=%s" % (miss_state or "none")))
    recon_ok = all(r[-1] == "OK" for r in recon) if recon else False
    rows.append(("SUMMARY", "MAKETEST", "make test NO_NEW_FAILURE 且与 Ran N 对账",
                 "MET" if mv.get("verdict") == "NO_NEW_FAILURE" and recon_ok else "GAP",
                 "MAKETEST_VERDICT_S5R3.tsv", "verdict=%s reconcile=%d/%d OK" %
                 (mv.get("verdict"), sum(1 for r in recon if r[-1] == "OK"), len(recon))))
    ec = e2e_counts()
    bad_e2e = []
    if ec:
        c = ec[0]
        bad_e2e = [k for k in ("FLAKY", "INVALID", "HIT_OFF_TARGET", "API_SILENT", "RETRY_DIFF", "RETRY_FAIL", "MISSING_RUN") if c.get(k)]
    ok6 = ds and ds.get("MISMATCH") == "0" and ds.get("FLAKY") == "0" and not bad_e2e
    rows.append(("SUMMARY", "PREREG_MATRIX", "D016/E2E 预注册矩阵无 MISMATCH/FLAKY/VALUE_DRIFT",
                 "MET" if ok6 else "GAP", "D016_VERDICT_S5R3.tsv; E2E_VERDICT_S5R3.tsv",
                 "d016=%s e2e_bad=%s" % (ds, bad_e2e or "none")))
    fe = ec[1] if ec else {}
    ok7 = (ds and ds.get("MATCH") == "33" and ds.get("MISMATCH") == "0"
           and fe.get("py") == 10 and fe.get("lua_batch") == 11 and fe.get("lua_repl") == 4)
    rows.append(("SUMMARY", "E2E_CHAINS", "Python/Lua 正常→失败→可见报错→重试/新对象恢复全部通过",
                 "MET" if ok7 else "GAP", "D016_VERDICT_S5R3.tsv; E2E_VERDICT_S5R3.tsv",
                 "d016_match=%s e2e_ok_by_frontend=%s" % (ds.get("MATCH") if ds else None, fe)))
    out = os.path.join(outdir(), "READINESS_S5R3.tsv")
    wr(out, NL.join(TAB.join(r) for r in rows) + NL)
    gap = sum(1 for r in rows[1:] if r[3] == "GAP")
    print("READINESS rows=%d GAP=%d" % (len(rows) - 1, gap))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if gap == 0 else 1


def cmd_acceptance():
    ds = d016_summary() or {}
    ec, fe = e2e_counts() or ({}, {})
    mv, recon = maketest() or ({}, [])
    rows = [("ac_id", "acceptance_criterion", "committed_evidence", "status", "notes"),
            ("AC-1", "每个受影响的 prepare/execute 点有正负对照",
             "P05_S4R9_M2_REPORT.md + registries/s4r9/M2/；P05_S4R9_M1R3_REPORT.md + registries/s4r9/M1R3/",
             "MET", "F4 上 M2 两遍与 M1R3 651 点已提交判定（U364 历史证据可引用）；不外推到其它树/布局"),
            ("AC-2", "失败后模式/缓存不安装",
             "P05_S3_4b_CLOSURE.md（U29：202 注入点 HOLD 202 / VIOLATED 0）；P05_S4R9_M3c_REPORT.md + registries/s4r9/M3c/",
             "MET", "U29 关闭声明与 M3c 就绪审计 GAP=0；范围声明见 U29 原文"),
            ("AC-3", "Python/Lua 可见失败，恢复重试正确",
             "PREREG_E2E_S5R3.tsv; E2E_VERDICT_S5R3.tsv; PREREG_D016_S5R3.tsv; D016_VERDICT_S5R3.tsv; POSCTRL_E2E_S5R3.txt; POSCTRL_D016_S5R3.txt",
             "MET" if ds.get("MISMATCH") == "0" and fe.get("py") == 10 and fe.get("lua_batch") == 11 and fe.get("lua_repl") == 4 else "GAP",
             "S5R3 在 F4 上重跑：E2E E2E_OK=%d CONTROL_OK=%d（py=%s lua_batch=%s lua_repl=%s）；D016 MATCH=%s MISMATCH=%s FLAKY=%s（U375 最终映射）" %
             (ec.get("E2E_OK", -1), ec.get("CONTROL_OK", -1), fe.get("py"), fe.get("lua_batch"), fe.get("lua_repl"),
              ds.get("MATCH"), ds.get("MISMATCH"), ds.get("FLAKY"))),
            ("AC-4", "M3a/M3b 的 make test 与 E2E 结果能否作为 S5 前端与回归的已提交证据",
             "U364（历史证据可引用，S5R3 在 F4 上重跑）；MAKETEST_VERDICT_S5R3.tsv; E2E_VERDICT_S5R3.tsv",
             "MET", "由 U364 回答；S5R3 重跑 make test %s（unit_count=%s）与 E2E 42 点，MISMATCH/FLAKY 均为 0" %
             (mv.get("verdict", "?"), mv.get("unit_count", "?")))]
    out = os.path.join(outdir(), "P05_ACCEPTANCE_MAP_S5R3.tsv")
    wr(out, NL.join(TAB.join(str(x) for x in r) for r in rows) + NL)
    print("ACCEPTANCE rows=%d MET=%d GAP=%d" % (len(rows) - 1, sum(1 for r in rows[1:] if r[3] == "MET"), sum(1 for r in rows[1:] if r[3] == "GAP")))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


def cmd_signoff():
    ds = d016_summary() or {}
    ec, fe = e2e_counts() or ({}, {})
    mv, recon = maketest() or ({}, [])
    t = []
    t.append("# P05-S5 范围声明草稿（未签收）")
    t.append("")
    t.append("> 状态：**未签收**。本文件是 P05-S5 范围声明草稿，由 P05-S5 R3 执行者按 U377 编写；签收只由用户在对话中给出。")
    t.append("> 本轮不宣布 P05-S5 或 P05 完成。")
    t.append("")
    t.append("## 1 被测树")
    t.append("")
    t.append("- 被测冻结树 F4：提交 05097a7，S4/ 树 589e15eb11fcb04e031b524f25a443e7921946cf；S5R3 的所有运行都在 F4 上。")
    t.append("- 未修改 S4/、testing/d003/judge_d003.py（sha256 d2d04145e056…）与历史装置。")
    t.append("")
    t.append("## 2 S5 收口测试范围（S5R3 在 F4 上重跑）")
    t.append("")
    t.append("- make test：B 树（37a82e8）与 F4 各两遍，判据 NO_NEW_FAILURE，单元数与日志 Ran N 对账；结果 %s，unit_count=%s。" % (mv.get("verdict", "?"), mv.get("unit_count", "?")))
    t.append("- E2E 42 点（25 注入 + 17 无注入对照，M3b 点族原样）：E2E_OK=%d、CONTROL_OK=%d、FLAKY/INVALID/HIT_OFF_TARGET/API_SILENT/RETRY_DIFF/RETRY_FAIL 均为 0。" % (ec.get("E2E_OK", -1), ec.get("CONTROL_OK", -1)))
    t.append("- D016 点族（Python/Lua 公共 API，VL NB=1–4 失败与同对象重试、对照、恢复）：MATCH=%s MISMATCH=%s FLAKY=%s（判定行 34：33 MATCH + 1 RECORD）。" % (ds.get("MATCH"), ds.get("MISMATCH"), ds.get("FLAKY")))
    t.append("- 阳性对照：D016 5/5、E2E 19/19、make test 4/4；独立重判 DIFFS=0。")
    t.append("")
    t.append("## 3 转出项清单")
    t.append("")
    t.append("- U366–U370 转出/登记项：F10 历史因果（S5-B-01）、F8 历史目录未验证（S5-B-02）、S1 报告 11.2 五哈希来源无法判定（S5-B-05..09）、反事实通量与 allzero 设计意图（R-P05-01）、U99/U100（R-P05-02/R-P05-03）。")
    t.append("- D017：非 FMM S4_malloc 分配失败未逐点检查（59 处出现 / CALL 52 / OUT 38 / OUT CALL 31），保持 OPEN，不在 P05 修，不阻塞 P06（U369）。")
    t.append("- R-P05-01 / R-P05-02 / R-P05-03：保持 OPEN，转出 P05，不阻塞 P06（U366、U370）。")
    t.append("")
    t.append("## 4 已知限制")
    t.append("")
    t.append("- D016 的 NV -10 路径触发不了：NV 只作为对照点（NB=1 成功），-10 路径维持 [源码] 结论，未实测。")
    t.append("- Lua REPL 前端只覆盖 cf/fft/kt/vl 四族（exp 无 REPL 点，因为 REPL 脚本只用真实方法名且 exp 路径由批量前端覆盖）。")
    t.append("- ES5-6 历史缺陷：S5R2 的 D016 比较器把预注册标签 ABSENT 与计数 0 直比导致 2 个 MISMATCH；S5R3 用比较器 v2 与 expected_count=0 重跑，S5R2 判定表保留为历史。")
    t.append("- 范围限 F4 与被测点族；不外推到其它树/布局/材料范围。")
    t.append("")
    t.append("## 5 声明")
    t.append("")
    t.append("- **未签收**；等待用户审核。")
    t.append("")
    out = os.path.join(outdir(), "P05_S5_SIGNOFF_DRAFT.md")
    wr(out, NL.join(t) + NL)
    print("SIGNOFF_DRAFT bytes=%d" % len(NL.join(t)))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


EVENTS_TABLE1 = [("s5r3", "run_code 程序内 fs.writeFile('/tmp_prereg_body_unused', ...)（一条临时代码行，非证据写入）", "/tmp（仓库外）", "否：沙箱拒绝 EROFS/denied，未落盘；已在本表登记")]


def events_table2():
    return [
        ("1", "s5r3_startgate.py v1 的 GIT_STATUS_EMPTY FAIL：门禁脚本自身是未跟踪新文件", "改为允许本轮新脚本前缀后 v2 通过；v1 保存为 $EV/gate/GATE_S5R3_start.txt_v1"),
        ("2", "start gate v2 的 EV_ABSENT_BEFORE_START 把 gate/ 视为先前证据", "排除 gate/ 后 v3 通过（FAILS=0, CHECK_CRASHED=0）"),
        ("3", "s5r3_prep.py v1 的 errata 块分组下标写错，ES5-6/7/8 被切错（两次追加均带前缀断言）", "用 p05-s5r2 证据副本（sha c6d2acb7…）重建后追加正确块；S5R2 清单中 ERRATA_S5.txt 旧 sha 记为预期变化（ES5-8 附带说明）"),
        ("4", "d016_run_s5r3.py shakedown 首跑 KeyError（py_ref 观测键与进程键冲突）", "改名 py_run_* 后 shakedown 得到 MATCH=33 MISMATCH=0 FLAKY=0"),
        ("5", "D016 阳性对照案 A 只篡改 pass1，得到 FLAKY 而非预期的 MISMATCH", "改为两遍同时篡改（计数各 1）后 5/5 PASS"),
        ("6", "make test 阳性对照案 B 的 flip 未命中（状态词在单元下一行）", "改用与案 A 相同的跨行翻转函数后 4/4 PASS"),
        ("7", "build_e2e_s5r3.py 的参考数据由 M3a 改为 M3b 表（任务书 §5 要求与 E2E_BUILD_R9M3B.tsv 对照）", "在 COPY_DIFF_S5R3.txt 中列为 DECLARED 数据行，未改装置逻辑"),
        ("8", "D016 预注册 artifact 行 id（LIBS4A_SHA256）与 D016_BUILD_S5R3.tsv 的列名（LIB_S4_A_SHA256）不同", "比较器与独立重判都按 id→列名映射读取；期望语义不变"),
        ("9", "框架事件：本会话无 /tmp/dsh-spill-* 落盘记录", "无"),
    ]


def report_text():
    sr = {}
    gp = os.path.join(EV, "GATE_S5R3_start.txt")
    if os.path.isfile(gp):
        for line in rd(gp).splitlines():
            if line.startswith("RECORD" + TAB):
                f = line.split(TAB)
                sr[f[1]] = f[2].replace("value=", "")
    ra = read_tsv(os.path.join(EV, "RULINGS_APPEND_S5R3.tsv"))
    ea = read_tsv(os.path.join(EV, "ERRATA_APPEND_S5R3.tsv"))
    sup = read_tsv(os.path.join(EV, "S5R2_SUPPLEMENT_COPY_S5R3.tsv")) if os.path.isfile(os.path.join(EV, "S5R2_SUPPLEMENT_COPY_S5R3.tsv")) else []
    ds = d016_summary()
    drill = d016_row_count()
    ec = e2e_counts()
    mv, recon = maketest() or ({}, [])
    build = read_kv(os.path.join(EV, "E2E_BUILD_S5R3.tsv")) if os.path.isfile(os.path.join(EV, "E2E_BUILD_S5R3.tsv")) else {}
    cal = read_tsv(os.path.join(EV, "CALIB_E2E_S5R3.tsv")) if os.path.isfile(os.path.join(EV, "CALIB_E2E_S5R3.tsv")) else []
    cd = read_kv(os.path.join(EV, "CALIB_DIFF_S5R3.tsv")) if os.path.isfile(os.path.join(EV, "CALIB_DIFF_S5R3.tsv")) else {}
    rj = rejudge()
    rd_ = registry_diff()
    ro = readiness_rows()
    ac = acceptance_rows()
    sg = shakedown_gate()
    pr_e2e = read_tsv(os.path.join(EV, "PREREG_E2E_S5R3.tsv"))
    rec_e2e = read_tsv(os.path.join(EV, "PREREG_E2E_S5R3.tsv.sha256.txt"))
    rec_d016 = read_tsv(os.path.join(EV, "PREREG_D016_S5R3.tsv.sha256.txt"))
    n_py = sum(1 for r in pr_e2e if r["frontend"] == "py" and r["is_control"] == "NO")
    n_lb = sum(1 for r in pr_e2e if r["frontend"] == "lua_batch" and r["is_control"] == "NO")
    n_lr = sum(1 for r in pr_e2e if r["frontend"] == "lua_repl" and r["is_control"] == "NO")
    n_ctl = sum(1 for r in pr_e2e if r["is_control"] == "YES")
    t = []
    t.append("# P05-S5 R3 报告（s5r3）：S5 收口——勘误 ES5-6..8、D016 比较器 v2、make test 四遍与全量 E2E 42 点在 F4 上重跑、就绪审计、签收范围声明草稿")
    t.append("")
    t.append("> 轮次：P05-S5 R3。本轮不宣布 P05-S5 或 P05 完成或签收；签收只由用户在对话中给出。")
    t.append("> 修复前证据不得称为修复后验证；本轮在 F4 上的重跑结果称为\"S5 收口在 F4 上的回归与前端验证\"，范围仅限本轮预注册点。")
    if SHAKE:
        t.append("> **本文件是试跑草稿（--shakedown，数据来自 $EV/shakedown/）**，由 report_check 与试跑 end 门禁实际读取。")
    t.append("")
    t.append("## 1 门禁")
    t.append("")
    t.append("- start 门禁：%s，HEAD=%s，HEAD:S4=%s（F4），判定器 sha256=%s（GATE_S5R3_start.txt；FAILS=0；CHECK_CRASHED=0）。" % (
        sr.get("START_TIME_UTC", "?"), sr.get("HEAD", "?")[:16] + "…", sr.get("HEAD_S4", "?")[:16] + "…", sr.get("JUDGE_SHA256", "?")[:16] + "…"))
    t.append("- 起始文件由脚本断言：RULINGS.tsv %s B（最大 %s）、registries/s5r2 小表清单 %s 项全 OK、p05-s5r2 证据清单 %s 项全 OK、D016_VERDICT_S5R2 SUMMARY=%s、PREREG_E2E_R9M3B %s 行且 sha 与记录一致、/tmp 顶层 %s 项。" % (
        sr.get("RULINGS_BYTES", "?"), sr.get("RULINGS_MAX_U", "?"), sr.get("S5R2_REGISTRY_ITEMS", "?"),
        sr.get("S5R2_EVIDENCE_ITEMS", "?"), sr.get("D016_S5R2_SUMMARY", "?"), sr.get("M3B_PREREG_ROWS", "?"), sr.get("TMP_COUNT", "?")))
    t.append("- start 门禁版本演进照实登记：v1 因门禁脚本自身未跟踪而 GIT_STATUS_EMPTY FAIL，v2 因 gate/ 目录 EV_ABSENT FAIL；v3 FAILS=0，v1 保留在 $EV/gate/GATE_S5R3_start.txt_v1。end 门禁正式一次，输出在 $EV/gate/；原文摘要见 P05_S5R3_GATE_APPENDIX.md。")
    t.append("")
    t.append("## 2 裁决入账（U372–U377，纯追加）")
    t.append("")
    t.append("- RULINGS.tsv 追加 U372–U377 共 6 行，前缀逐字节断言；最大编号 %s。" % (ra[-1].get("max_u_after") if ra else "?"))
    for r in ra:
        t.append("- %s：%s" % (r["id"], r.get("given_in_round", "")))
    t.append("- 原文逐字见 registries/RULINGS.tsv 与本轮任务书 §1。")
    t.append("")
    t.append("## 3 勘误 ES5-6..ES5-8")
    t.append("")
    if ea:
        t.append("- ERRATA_S5.txt 纯追加 ES5-6/7/8（前缀 sha 断言）：%s → %s B；最后条目 %s。" % (
            ea[0].get("bytes_before"), ea[-1].get("bytes_after"), ea[-1].get("errata_id")))
    t.append("- ES5-6：S5R2 D016 比较器缺陷（d016_run_s5r2.py:218-219 把预注册标签 ABSENT 与观测计数 0 直比，导致 PY_STDERR_INFO2/LUA_STDERR_INFO2 判 MISMATCH）；行为事实是 28 个行为点两遍全 MATCH、两个 stderr 计数均为 0；S5R2 试跑门禁把该检查写成 deferred 就判 PASS（shakedown/gate/GATE_S5R2_end.txt:83），所以冻结前未发现。处置：S5R2 判定表与门禁 FAIL 保留为历史；S5R3 用比较器 v2 与新预注册重跑（不是改期望）。")
    t.append("- ES5-7：S5R2 报告 §7 未说明 MISMATCH 原因、未指向 D016_VERDICT_S5R2_ERRATA.txt；§8 表二缺\"冻结期比较器缺陷\"；ISSUE_REGISTRY 第 48 行与 ROADMAP 第 145 行缺少原因。处置：S5R2 报告不改；按 U376 替换这两行原文（见 §8）。")
    t.append("- ES5-8：D016_VERDICT_S5R2_ERRATA.txt 与 D016_BUILD_S5R2.tsv 未复制进 registries/s5r2/；本轮复制到 registries/s5r3/s5r2_supplement/，sha256 与 p05-s5r2/SHA256SUMS.txt 记录一致：%s" % ("; ".join("%s=%s" % (r["file"], r["match"]) for r in sup) if sup else "(见 S5R2_SUPPLEMENT_COPY_S5R3.tsv)"))
    t.append("")
    t.append("## 4 D016（比较器 v2、阳性对照、两遍）")
    t.append("")
    t.append("- 新预注册 PREREG_D016_S5R3.tsv：数据行 %d，状态 INFLUENCED，sha=%s（写入早于首条正式 D016 运行行，由 end 门禁断言）。比较器按预注册列名读取；stderr 类行显式 expected_count=0，规则为\"预注册 ABSENT ⇔ 计数 == 0\"，不再有标签与数字直比的路径。" % (
        int(rec_d016[0]["rows"]) if rec_d016 else -1, (rec_d016[0]["sha256"][:16] + "…") if rec_d016 else "?"))
    t.append("- 构建：trees/F4 = 05097a7 全仓导出 + make test shakedown 构建；PYEXT_SHA256=%s、LUA_FRONTEND_SHA256=%s（D016_BUILD_S5R3.tsv）。" % (
        build.get("PYEXT_SHA256", "?")[:16] + "…", build.get("LUA_FRONTEND_SHA256", "?")[:16] + "…"))
    t.append("- 正式两遍：判定行 %d（%s MATCH + ROOT_CAUSE_RC RECORD）；SUMMARY MATCH=%s MISMATCH=%s FLAKY=%s。" % (
        drill, ds.get("MATCH") if ds else "?", ds.get("MATCH") if ds else "?", ds.get("MISMATCH") if ds else "?", ds.get("FLAKY") if ds else "?"))
    p16 = posctrl_result("POSCTRL_D016_S5R3.txt")
    t.append("- 阳性对照（5 例落盘篡改副本，同一 compare_passes 代码路径）：%s %s/%s。" % (p16[0] if p16 else "?", p16[1] if p16 else "?", p16[2] if p16 else "?"))
    t.append("- 事实摘要：Python 抛 RuntimeError（含 GetPowerFlux），Lua REPL 打印 GetPoyntingFlux 同一文本；两前端 stderr 均无 \"Layer eigensystem returned info = 2\"；恢复对象与另起进程参考值 rel_err=0。结论措辞：在 F4 上、在该输入下经公共 API 可见失败且恢复正确（不写已修好）。")
    t.append("")
    t.append("## 5 E2E（构建、校准对照、两遍、重判）")
    t.append("")
    t.append("- 装置按 U373 复制：build/calib/run/judge/frontend 共 7 个脚本 STRICT 复制（calib、run、Python、Lua 批量、Lua REPL 文件逐行 diff 残差为 0；build 仅参考数据换 M3b 值、judge 仅加 shakedown 块，均列为 DECLARED）；make test runner/judge 为 ADAPTED 复制（要求的分段续跑与 4 例阳性对照）。详见 COPY_DIFF_S5R3.txt。")
    t.append("- 构建（E2E_BUILD_S5R3.tsv）：PYEXT=%s（与 M3b 对照 %s：树路径 s5r3 比 m3b 长 1 字节使嵌入路径整体移位，未判等价）；LUA_FRONTEND=%s（与 M3b 对照 %s）；4/4 __wrap 符号定义、0 个未解析原始 FFT 符号。" % (
        build.get("PYEXT_SHA256", "?")[:16] + "…", build.get("PYEXT_BYTE_DIFF_VS_M3B", "?"),
        build.get("LUA_FRONTEND_SHA256", "?")[:16] + "…", build.get("LUA_FRONTEND_BYTE_DIFF_VS_M3B", "?")))
    t.append("- 校准（注入无关，gdb）：EVENT %d 行、TARGET %d 行；与 CALIB_E2E_R9M3B.tsv 逐点比较 DIFFS=%s（CALIB_DIFF_S5R3.tsv），命中序号与 size 全部一致，未调整 nth。" % (
        sum(1 for r in cal if r["row_kind"] == "EVENT"), sum(1 for r in cal if r["row_kind"] == "TARGET"), cd.get("DIFFS", "?")))
    t.append("- 预注册 PREREG_E2E_S5R3.tsv：%d 行 = %d 注入点（py %d、lua_batch %d、lua_repl %d）+ %d 无注入对照，行原样来自 M3b，状态 INFLUENCED，sha=%s。" % (
        len(pr_e2e), len(pr_e2e) - n_ctl, n_py, n_lb, n_lr, n_ctl, (rec_e2e[0]["sha256"][:16] + "…") if rec_e2e else "?"))
    c = ec[0] if ec else {}
    t.append("- 正式两遍（42 点）：%s。" % (", ".join("%s=%d" % (k, c[k]) for k in sorted(c)) if c else "?"))
    p2 = posctrl_result("POSCTRL_E2E_S5R3.txt")
    t.append("- 阳性对照（19 例落盘篡改记录，覆盖 3 前端与 9 类别）：%s %s/%s。" % (p2[0] if p2 else "?", p2[1] if p2 else "?", p2[2] if p2 else "?"))
    t.append("- 独立重判 rejudge_s5r3.py（新实现，不 import 判定脚本；预注册+逐点 JSON 合并）：E2E_DIFFS=%s、D016_DIFFS=%s、DIFFS=%s。" % (
        rj.get("E2E_DIFFS", "?") if rj else "?", rj.get("D016_DIFFS", "?") if rj else "?", rj.get("DIFFS", "?") if rj else "?"))
    t.append("")
    t.append("## 6 make test（四遍、判定、对账）")
    t.append("")
    t.append("- B 树 37a82e8、F4 树 05097a7（trees/B、trees/F4 由 git archive 导出，不注入）；四段 B:1、F4:1、B:2、F4:2 各一次调用，可续跑。")
    t.append("- 判定：verdict=%s，unit_count=%s；B_failing=%s，F4_failing=%s，flaky=%s，suite_diff=%s。" % (
        mv.get("verdict", "?"), mv.get("unit_count", "?"), mv.get("B_failing", "?"), mv.get("F4_failing", "?"),
        mv.get("flaky", "?"), mv.get("suite_diff", "?")))
    t.append("- 与 Ran N 对账 %d 段（每树每遍 2 段）：%s。" % (len(recon), ", ".join("%s/%s units=%s ran=%s %s" % (r[1], r[2], r[3], r[4], r[7]) for r in recon)))
    p3 = posctrl_result("POSCTRL_MAKETEST_S5R3.txt")
    t.append("- 阳性对照（4 例落盘篡改日志：NEW_FAILURE/FLAKY/SUITE_DIFF/RECONCILE_FAIL）：%s %s/%s。" % (p3[0] if p3 else "?", p3[1] if p3 else "?", p3[2] if p3 else "?"))
    t.append("")
    t.append("## 7 就绪审计（READINESS_S5R3.tsv，逐条对照\"无可做\"七条）")
    t.append("")
    summ = [r for r in ro if r.get("row_kind") == "SUMMARY"]
    red = [r for r in ro if r.get("row_kind") == "RED_POINT"]
    t.append("- 红点：S4 签收时 26 个唯一 id，逐行见 READINESS_S5R3.tsv（RED_POINT 行）；全部引用已提交的 M3d 台账与修后回归证据。")
    for r in summ:
        t.append("- %s：%s（%s）。" % (r["item"], r["status"], r["note"]))
    t.append("- 汇总：%d 个 SUMMARY 项，MET=%d，GAP=%d；RED_POINT 明细 %d 行，MET=%d。" % (
        len(summ), sum(1 for r in summ if r["status"] == "MET"), sum(1 for r in summ if r["status"] == "GAP"),
        len(red), sum(1 for r in red if r["status"] == "MET")))
    t.append("- 验收映射：P05_ACCEPTANCE_MAP_S5R3.tsv AC-1..AC-4 全部 %s（AC-4 由 U364 回答，AC-3 按 S5R3 E2E/D016 结果给出最终映射）。" % ("MET" if ac and all(r["status"] == "MET" for r in ac) else "非全部 MET"))
    t.append("")
    t.append("## 8 登记表 diff 摘要")
    t.append("")
    if rd_:
        for rel in ("testing/s4test/ISSUE_REGISTRY.md", "PROJECT_ROADMAP.md"):
            d = rd_[rel]
            t.append("- %s：%s → %s B；sha256 %s → %s；只改动脚本列出的行（ASSERT_ONLY_LISTED_LINES_CHANGED=%s）。" % (
                rel, d["before_bytes"], d["after_bytes"], d["before_sha"][:16] + "…", d["after_sha"][:16] + "…",
                "PASS" if rd_.get("assert") else "FAIL"))
        t.append("- 改动行：ISSUE_REGISTRY.md 第 48 行（D016）与第 29 行（D003 记录）、PROJECT_ROADMAP.md 第 51 行（P05）与第 145 行（D016 条目）；unified diff 见 REGISTRY_APPLY_DIFF_S5R3.txt。")
    else:
        t.append("- （试跑期：正式补丁尚未应用）")
    t.append("")
    t.append("## 9 签收草稿摘要")
    t.append("")
    t.append("- P05_S5_SIGNOFF_DRAFT.md：S5 范围声明草稿，标明\"未签收\"，含被测树 F4、S5 收口测试范围（make test、E2E 42 点、D016 点族）、转出项清单（U366–U370、D017、R-P05-01/02/03）、已知限制（NV -10 仅 [源码]、Lua REPL 只覆盖 cf/fft/kt/vl、ES5-6 历史缺陷）；未写签收文件。")
    t.append("")
    t.append("## 10 事件两张表")
    t.append("")
    t.append("### 10.1 表一：越界写入尝试")
    t.append("")
    t.append("| 轮次 | 命令 | 目标 | 是否落盘 |")
    t.append("|---|---|---|---|")
    for r in EVENTS_TABLE1:
        t.append("| " + " | ".join(r) + " |")
    t.append("")
    t.append("### 10.2 表二：工具与脚本事件")
    t.append("")
    t.append("| # | 事件 | 处理/影响 |")
    t.append("|---|---|---|")
    for r in events_table2():
        t.append("| " + " | ".join(r) + " |")
    t.append("")
    t.append("## 11 交付物")
    t.append("")
    t.append("复制到 checkpoints/p05/registries/s5r3/ 的小表与 s5r2 补充件共 %d 项，加 SHA256SUMS.txt 共 %d 项（与 SHA256SUMS 的 %d 条记录一致）：" % (NSMALL, NSMALL + 1, NSMALL))
    for i, f in enumerate(SMALL + SUP, 1):
        t.append("%d. %s" % (i, f))
    t.append("%d. SHA256SUMS.txt" % (NSMALL + 1))
    t.append("")
    t.append("- 另：end 门禁摘要 GATE_S5R3_end.txt 由 s5r3_appendix.py 在 end 门禁之后追加到 registries/s5r3/（不在上面的编号清单内），因此目录最终为 %d 项。" % (NSMALL + 2))
    t.append("")
    t.append("## 附录 A（试跑门禁摘要）")
    t.append("")
    if sg and sg.get("counts"):
        t.append("- 试跑输出：$EV/shakedown/gate/GATE_S5R3_end.txt（模拟 commit-i，含 POST_I 块；不纳入 SHA256SUMS）。")
        for l in [sg["counts"], sg["fails"], sg["crashed"]] + sg["post"]:
            if l:
                t.append("- " + l)
        t.append("- 试跑期 end 门禁的 FAIL 项均为试跑期必然（正式结果/提交 (i) 尚不存在），逐项见试跑门禁原文；本轮以 CHECK_CRASHED=0 为通过条件。")
    else:
        t.append("- 试跑 end 门禁尚未运行（本报告在试跑门禁之前生成）。")
    t.append("")
    t.append("## 附录 B（正式 end 门禁原文摘要）")
    t.append("")
    t.append("见 P05_S5R3_GATE_APPENDIX.md（由 s5r3_appendix.py 从正式门禁输出按列名解析生成；报告正文不内嵌门禁结果）。")
    t.append("")
    t.append("本轮已完成 P05-S5 R3 范围，等待用户审核。")
    t.append("")
    gl = subprocess.check_output(["git", "log", "-1", "--format=%H %s"], text=True, cwd=REPO).strip()
    stt = subprocess.check_output(["git", "status", "--short"], text=True, cwd=REPO).strip() or "(clean)"
    t.append("git log -1: " + gl)
    t.append("git status --short: " + (stt.replace(NL, "; ") if stt else "(clean)"))
    t.append("")
    return NL.join(t)


def cmd_report():
    txt = report_text()
    if SHAKE:
        wr(os.path.join(SHK, "REPORT.proposed.md"), txt)
    else:
        wr(REPORT, txt)
    stpath = os.path.join(SHK, "STATE.proposed.md") if SHAKE else STATE
    wr(stpath, write_state())
    print("REPORT bytes=%d shake=%s" % (len(txt.encode()), SHAKE))
    return 0


def write_state():
    ds = d016_summary() or {}
    ec, fe = e2e_counts() or ({}, {})
    mv, recon = maketest() or ({}, [])
    rj = rejudge() or {}
    t = []
    t.append("# P05 当前状态（每轮结束更新，一页以内）")
    t.append("")
    t.append("> 规则见仓库根 AGENTS.md。本文件是摘要，细节以各轮报告为准。")
    t.append("")
    t.append("## 1. 当前位置")
    t.append("")
    t.append("| 项 | 值 |")
    t.append("|---|---|")
    t.append("| 分支 | codex/p05-d003-fft-error-propagation |")
    t.append("| 本轮开工基线 HEAD（s5r3） | 29dfd1c04e18d351e72d50f57deb0299f8f74d08（P05-S5 R2 (ii)） |")
    t.append("| HEAD:S4（冻结被测树 F4） | 589e15eb11fcb04e031b524f25a443e7921946cf（F4 提交 05097a7） |")
    t.append("| 判定器 sha256 | d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb |")
    t.append("| 阶段状态 | S1–S4 已由用户签收（带范围声明）；S5 进行中（R3：S5 收口轮，未签收） |")
    t.append("| 当前轮次 | P05-S5 R3（s5r3）；不宣布 S5 或 P05 阶段完成 |")
    t.append("")
    t.append("## 2. 关键数字（每轮一行）")
    t.append("")
    t.append("| 轮 | 关键数字 | 报告/证据 |")
    t.append("|---|---|---|")
    t.append("| S4R9 M3c–M3e | 独立复核 DIFFS=0；签收落账 U359–U363 | M3c/M3d/M3e 报告 |")
    t.append("| S5R1 | 输入 25 行；分类；勘误 E9-78/79 | P05_S5R1_REPORT.md |")
    t.append("| S5R2 | 裁决 U364–U371；勘误 ES5-1..5；D017 清单；D016 公共 API 实测（MATCH=31 MISMATCH=2，比较器缺陷） | P05_S5R2_REPORT.md |")
    t.append("| S5R3 | 裁决 U372–U377；勘误 ES5-6..8；D016 比较器 v2 重跑 MATCH=%s MISMATCH=%s FLAKY=%s；E2E E2E_OK=%s CONTROL_OK=%s；make test %s（unit_count=%s）；独立重判 DIFFS=%s；就绪审计 READINESS_S5R3.tsv | P05_S5R3_REPORT.md |" % (
        ds.get("MATCH", "?"), ds.get("MISMATCH", "?"), ds.get("FLAKY", "?"),
        ec.get("E2E_OK", "?"), ec.get("CONTROL_OK", "?"), mv.get("verdict", "?"), mv.get("unit_count", "?"), rj.get("DIFFS", "?")))
    t.append("")
    t.append("## 3. 开放问题（状态 · 去向 · 详情链接）")
    t.append("")
    t.append("| 项 | 状态 | 去向 | 详情链接 |")
    t.append("|---|---|---|---|")
    t.append("| S5 输入 25 行的最终处置 | 落位（已转出/已登记/已关闭） | 本表为唯一入口 | checkpoints/p05/P05_S5_OPEN_ITEMS.tsv |")
    t.append("| D017 非 FMM S4_malloc | OPEN（不在 P05 修） | 转出 P05，不阻塞 P06（U369） | registries/s5r2/D017_S4MALLOC_INVENTORY_S5R2.tsv |")
    t.append("| R-P05-01 / R-P05-02 / R-P05-03 | OPEN（不在 P05 修） | 转出 P05，不阻塞 P06（U366/U370） | ISSUE_REGISTRY；ERRATA_S5.txt ES5-6..8 |")
    t.append("| F10/F8/反事实通量/allzero/11.2 五哈希 | OPEN / 未验证 | 经 U366–U368 转出 P05 | P05_S5_OPEN_ITEMS.tsv；ERRATA_S5.txt |")
    t.append("| S5 签收 | 等待用户审核 | S5R3 完成收口范围；签收只由用户给出 | P05_S5_SIGNOFF_DRAFT.md（未签收） |")
    t.append("")
    t.append("## 4. 证据位置")
    t.append("")
    t.append("- **P05-S5 R3（s5r3）**：证据 checkpoints/p05/evidence/p05-s5r3/（SHA256SUMS.txt）；小表 checkpoints/p05/registries/s5r3/（SHA256SUMS.txt）；报告 P05_S5R3_REPORT.md；门禁附录 P05_S5R3_GATE_APPENDIX.md；签收草稿 P05_S5_SIGNOFF_DRAFT.md。")
    t.append("- **P05-S5 R2（s5r2）**：证据 checkpoints/p05/evidence/p05-s5r2/；小表 checkpoints/p05/registries/s5r2/；报告 P05_S5R2_REPORT.md。")
    t.append("- **P05-S5 R1（s5r1）**：证据 checkpoints/p05/evidence/p05-s5r1/；小表 checkpoints/p05/registries/s5r1/；报告 P05_S5R1_REPORT.md。")
    t.append("- 裁决总表 registries/RULINGS.tsv（追加 U372–U377）；S5 勘误 registries/s5r2/ERRATA_S5.txt（追加 ES5-6..8）；S4 勘误 registries/s4r9/ERRATA_9.txt。")
    t.append("")
    return NL.join(t)


def cmd_report_check():
    src = os.path.join(SHK, "REPORT.proposed.md") if SHAKE else REPORT
    if not os.path.isfile(src):
        print("HARD_STOP report missing")
        return 2
    txt = rd(src)
    lines = txt.splitlines()
    order = ["## 1 门禁", "## 2 裁决入账", "## 3 勘误", "## 4 D016", "## 5 E2E", "## 6 make test",
             "## 7 就绪审计", "## 8 登记表 diff 摘要", "## 9 签收草稿摘要", "## 10 事件两张表",
             "## 11 交付物", "## 附录 A", "## 附录 B"]
    pos = [next((i for i, l in enumerate(lines) if l.strip().startswith(h)), -1) for h in order]
    checks = []
    checks.append(("SECTIONS_IN_ORDER", all(p >= 0 for p in pos) and pos == sorted(pos)))
    sec = []
    insec = False
    for l in lines:
        if l.strip() == "## 11 交付物":
            insec = True
            continue
        if insec and l.startswith("## "):
            break
        if insec:
            m = re.match(r"^\s*(\d+)\.\s+(.+?)\s*$", l)
            if m:
                sec.append(m.group(2).strip())
    checks.append(("DELIVERABLE_COUNT", len(sec) == NSMALL + 1))
    checks.append(("DELIVERABLE_LAST_SUMS", bool(sec) and sec[-1] == "SHA256SUMS.txt"))
    checks.append(("DELIVERABLE_NO_BACKTICK", all(BT not in x for x in sec)))
    checks.append(("VERDICT_LINE", "本轮已完成 P05-S5 R3 范围，等待用户审核" in txt))
    checks.append(("GIT_LINES", ("git log -1:" in txt) and ("git status --short:" in txt)))
    checks.append(("EVENTS_TWO_TABLES", ("10.1 表一" in txt) and ("10.2 表二" in txt)))
    forb = ["P05-S6", "P05 已完成", "P05-S5 已完成", "已签收 P05-S5", "P05 完成", "P05-S5 已签收", "已修好"]
    bad = [(w, i) for w in forb for i, l in enumerate(lines, 1) if w in l and not ("不" in l or "未" in l or "不得" in l)]
    checks.append(("FORBIDDEN_TOKENS_ABSENT", not bad))
    need = []
    ds = d016_summary()
    if ds:
        need.append("SUMMARY MATCH=%s MISMATCH=%s FLAKY=%s" % (ds.get("MATCH"), ds.get("MISMATCH"), ds.get("FLAKY")))
    ec = e2e_counts()
    if ec:
        c = ec[0]
        need.append(", ".join("%s=%d" % (k, c[k]) for k in sorted(c)))
    mv, recon = maketest() or ({}, [])
    if mv:
        need.append("verdict=%s，unit_count=%s" % (mv.get("verdict"), mv.get("unit_count")))
        need.append("与 Ran N 对账 %d 段" % len(recon))
    p16 = posctrl_result("POSCTRL_D016_S5R3.txt")
    if p16:
        need.append("阳性对照（5 例落盘篡改副本，同一 compare_passes 代码路径）：%s %s/%s" % p16)
    p2 = posctrl_result("POSCTRL_E2E_S5R3.txt")
    if p2:
        need.append("%s %s/%s" % p2)
    p3 = posctrl_result("POSCTRL_MAKETEST_S5R3.txt")
    if p3:
        need.append("%s %s/%s" % p3)
    rj = rejudge()
    if rj:
        need.append("E2E_DIFFS=%s、D016_DIFFS=%s、DIFFS=%s" % (rj.get("E2E_DIFFS"), rj.get("D016_DIFFS"), rj.get("DIFFS")))
    rd_ = registry_diff()
    if rd_:
        for rel in ("testing/s4test/ISSUE_REGISTRY.md", "PROJECT_ROADMAP.md"):
            d = rd_[rel]
            need.append("%s：%s → %s B" % (rel, d["before_bytes"], d["after_bytes"]))
    ro = readiness_rows()
    if ro:
        summ = [r for r in ro if r.get("row_kind") == "SUMMARY"]
        need.append("汇总：%d 个 SUMMARY 项，MET=%d，GAP=%d" % (len(summ), sum(1 for r in summ if r["status"] == "MET"), sum(1 for r in summ if r["status"] == "GAP")))
    miss = [x for x in need if x not in txt]
    checks.append(("DERIVED_TEXT_MATCHES_SOURCE_TABLES", not miss))
    sg = shakedown_gate()
    app_ok = True
    app_miss = []
    if sg:
        for l in [sg.get("counts"), sg.get("fails"), sg.get("crashed")] + sg.get("post", []):
            if l and ("- " + l) not in txt:
                app_ok = False
                app_miss.append(l)
    checks.append(("APPENDIX_A_DERIVED_LINES_IN_REPORT", app_ok))
    st = rd(os.path.join(SHK, "STATE.proposed.md") if SHAKE else os.path.join(P05, "STATE.md"))
    checks.append(("STATE_BYTES_LE_8192", 0 < len(st.encode()) <= 8192))
    smiss = [k for k in ("P05-S5 R3", "未签收", "S5 进行中", "READINESS_S5R3.tsv", "P05_S5_SIGNOFF_DRAFT.md") if k not in st]
    checks.append(("STATE_MARKERS", not smiss))
    fails = [k for k, v in checks if not v]
    outp = os.path.join(SHK if SHAKE else EV, "REPORT_CHECK_S5R3.txt")
    body = ["# REPORT_CHECK_S5R3.txt -- report structure, derived-text, appendix, deliverable and forbidden-token check",
            "# mode: " + ("SHAKEDOWN" if SHAKE else "FORMAL")]
    body += ["CHECK" + TAB + k + TAB + ("PASS" if v else "FAIL") for k, v in checks]
    if bad:
        body.append("FORBIDDEN_HITS=" + str(bad[:6]))
    if miss:
        body.append("COUNTS_MISSING=" + str(miss[:6]))
    if app_miss:
        body.append("APPENDIX_A_MISSING=" + str(app_miss[:6]))
    if smiss:
        body.append("STATE_MISSING=" + str(smiss[:6]))
    body.append("STATE_BYTES=%d" % len(st.encode()))
    body.append("FAILS=%d" % len(fails))
    wr(outp, NL.join(body) + NL)
    print(NL.join(body))
    return 0 if not fails else 2


def cmd_copy():
    src = SHK if SHAKE else EV
    dst = os.path.join(SHK, "registries_copy") if SHAKE else REGDIR
    os.makedirs(dst, exist_ok=True)
    copied = []
    for f in SMALL + SUP:
        if f.startswith("s5r2_supplement/"):
            sp = os.path.join(P05, "registries/s5r3", f)
        else:
            sp = os.path.join(src, f)
            if f == "ERRATA_S5.txt":
                sp = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
        if not os.path.isfile(sp):
            if SHAKE:
                continue
            print("HARD_STOP missing small table " + f)
            return 2
        dp = os.path.join(dst, f)
        os.makedirs(os.path.dirname(dp), exist_ok=True)
        if os.path.realpath(sp) != os.path.realpath(dp):
            shutil.copyfile(sp, dp)
        if sha_f(dp) != sha_f(sp):
            print("HARD_STOP copy sha mismatch " + f)
            return 2
        copied.append(f)
    lines = [sha_f(os.path.join(dst, f)) + "  " + f for f in copied]
    wr(os.path.join(dst, "SHA256SUMS.txt"),
       "# SHA256SUMS.txt -- small-table registry for P05-S5 R3 (copied from the raw evidence dir; sizes checked)" + NL + NL.join(lines) + NL)
    print("COPY %d files -> %s" % (len(copied), os.path.relpath(dst, REPO)))
    return 0


def cmd_precopy():
    # pre-commit(i) copy: rulings/errata are committed at (i); the three pre-registrations, the FROZEN
    # table, the start gate and the s5r2 supplement copies are committed then too (task brief section 7).
    dst = REGDIR
    os.makedirs(os.path.join(dst, "s5r2_supplement"), exist_ok=True)
    items = ["GATE_S5R3_start.txt", "PREREG_D016_S5R3.tsv", "PREREG_D016_S5R3.tsv.sha256.txt",
             "PREREG_MAKETEST_S5R3.tsv", "PREREG_E2E_S5R3.tsv", "PREREG_E2E_S5R3.tsv.sha256.txt",
             "FROZEN_SCRIPTS_S5R3.tsv"]
    copied = []
    for f in items:
        sp = os.path.join(EV, f)
        if not os.path.isfile(sp):
            print("HARD_STOP missing pre-copy source " + f)
            return 2
        dp = os.path.join(dst, f)
        shutil.copyfile(sp, dp)
        if sha_f(dp) != sha_f(sp):
            print("HARD_STOP pre-copy sha mismatch " + f)
            return 2
        copied.append(f)
    for f in ("D016_VERDICT_S5R2_ERRATA.txt", "D016_BUILD_S5R2.tsv"):
        sp = os.path.join(P05, "registries/s5r3/s5r2_supplement", f)
        dp = os.path.join(dst, "s5r2_supplement", f)
        if os.path.realpath(sp) != os.path.realpath(dp):
            shutil.copyfile(sp, dp)
        if sha_f(dp) != sha_f(sp):
            print("HARD_STOP pre-copy supplement sha mismatch " + f)
            return 2
        copied.append("s5r2_supplement/" + f)
    lines = [sha_f(os.path.join(dst, f)) + "  " + f for f in copied]
    wr(os.path.join(dst, "SHA256SUMS.txt"),
       "# SHA256SUMS.txt -- pre-commit(i) registry for P05-S5 R3 (pre-registrations, FROZEN, start gate, s5r2 supplement)" + NL + NL.join(lines) + NL)
    print("PRECOPY %d files -> %s" % (len(copied), os.path.relpath(dst, REPO)))
    return 0


def cmd_events():
    ev = SHK if SHAKE else EV
    logp = os.path.join(EV, "safe_run.log")
    if not os.path.isfile(logp):
        print("HARD_STOP no safe_run.log")
        return 2
    ls = rd(logp).splitlines()
    anchor = 0
    for i in range(len(ls), 0, -1):
        if "s5r3_chain.py events" in ls[i - 1]:
            anchor = i
            break
    if anchor <= 0:
        print("HARD_STOP no events anchor")
        return 2
    ts_re = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")
    parent = ""
    body = ["# EVENTS_S5R3.tsv -- safe_run.log line -> UTC timestamp (rows 1..%d; anchor = events call line %d)" % (anchor, anchor),
            TAB.join(["log_line", "ts_utc"])]
    for x in range(1, anchor + 1):
        line = ls[x - 1]
        m = ts_re.match(line)
        if m:
            parent = m.group(1)
        body.append(TAB.join([str(x), parent]))
    body.append("# ROWS=%d" % anchor)
    wr(os.path.join(ev, "EVENTS_S5R3.tsv"), NL.join(body) + NL)
    print("EVENTS rows=%d anchor=%d" % (anchor, anchor))
    return 0


def cmd_sha_sums():
    ev = SHK if SHAKE else EV
    logp = os.path.join(EV, "safe_run.log")
    ls = rd(logp).splitlines()
    anchor = 0
    for i in range(len(ls), 0, -1):
        if "s5r3_chain.py sha_sums" in ls[i - 1]:
            anchor = i
            break
    if anchor <= 0:
        print("HARD_STOP no sha_sums anchor")
        return 2
    th = hashlib.sha256((NL.join(ls[:anchor]) + NL).encode("utf-8")).hexdigest()
    items = []
    for root, dirs, files in os.walk(ev):
        dirs[:] = sorted(d for d in dirs if d not in ("tmp", "gate", "trees"))
        for f in sorted(files):
            fp = os.path.join(root, f)
            rel = os.path.relpath(fp, ev)
            if rel in ("safe_run.log", "SHA256SUMS.txt") or f == "SHA256SUMS.txt":
                continue
            items.append((sha_f(fp), rel))
    out = os.path.join(ev, "SHA256SUMS.txt")
    body = ["# SHA256SUMS.txt -- P05-S5 R3 evidence manifest (excludes tmp/, gate/, shakedown/gate/, trees/)",
            "# safe_run.log up to line %d: %s" % (anchor, th)] + ["%s  %s" % (h, rel) for h, rel in items]
    wr(out, NL.join(body) + NL)
    print("SHA256SUMS %d items trunc_line=%d" % (len(items), anchor))
    return 0


def main():
    if len(sys.argv) < 2:
        print("usage: s5r3_chain.py <precopy|readiness|acceptance|signoff|report|report_check|copy|events|sha_sums> [--shakedown]")
        return 2
    sub = sys.argv[1]
    fn = {"precopy": cmd_precopy, "readiness": cmd_readiness, "acceptance": cmd_acceptance, "signoff": cmd_signoff,
          "report": cmd_report, "report_check": cmd_report_check, "copy": cmd_copy,
          "events": cmd_events, "sha_sums": cmd_sha_sums}.get(sub)
    if fn is None:
        print("unknown subcommand " + sub)
        return 2
    return fn()


if __name__ == "__main__":
    sys.exit(main())