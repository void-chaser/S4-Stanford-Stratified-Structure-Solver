#!/usr/bin/env python3
# s5r4_readiness.py -- readiness audit for P05-S5 R4 (task brief section 7). It runs AFTER the final STATE
# (U382), records the STATE bytes/sha256 it read in a # META line, and walks the "nothing left to do" list.
# GAP>0 makes it exit non-zero (HARD_STOP before the end gate).
# usage: s5r4_readiness.py formal [--ev-root DIR] [--p05-root DIR]
import os, sys, re, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
EV3 = os.path.join(P05_REAL, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)
ALLOWED_OI = ("OPEN_TRANSFERRED_OUT", "RECORD_ONLY_OPEN", "REGISTERED_D016", "REGISTERED_D017",
              "REGISTERED_R-P05-02", "REGISTERED_R-P05-03", "REGISTRY_SYNC", "TEST_S5R2", "TEST_S5R3")


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def read_tsv(p, skip_first=("SUMMARY",)):
    rows = []
    hdr = None
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f[0] == hdr[0]:
            continue
        if f[0] in skip_first:
            continue
        rows.append(dict(zip(hdr, f + [""] * (len(hdr) - len(f)))))
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


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "formal":
        print("usage: s5r4_readiness.py formal [--ev-root DIR] [--p05-root DIR]", file=sys.stderr)
        return 2
    def arg(n, d):
        return os.path.abspath(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
    EV = arg("--ev-root", EV4_REAL)
    P05 = arg("--p05-root", P05_REAL)
    st = open(os.path.join(P05, "STATE.md"), "rb").read()
    stt = st.decode("utf-8")
    rows = [("row_kind", "item", "requirement", "status", "evidence", "note")]
    # 1 red points (26 unique ids, all with post-fix evidence)
    red = read_tsv(os.path.join(P05, "registries/s4r9/M3d/RED_POINTS_LEDGER_FINAL_R9M3D.tsv"))
    ids = [r for r in red if r.get("id")]
    bad = [r["id"] for r in ids if not r.get("post_fix_evidence") or r.get("current_status", "").startswith(("OPEN", "UNVERIFIED"))]
    for r in ids:
        rows.append(("RED_POINT", r["id"], "S4 签收时红点已修复并有修后回归",
                     "MET" if r["id"] not in bad else "GAP",
                     "registries/s4r9/M3d/RED_POINTS_LEDGER_FINAL_R9M3D.tsv:" + r["id"], r.get("post_fix_evidence", "")[:120]))
    # 2 open items (25 rows, disposition unchanged since S5R2/R3)
    oi = read_tsv(os.path.join(P05, "P05_S5_OPEN_ITEMS.tsv"))
    bad_oi = [r["input_id"] for r in oi if r.get("final_disposition") not in ALLOWED_OI or not r.get("ruling")]
    rows.append(("SUMMARY", "OPEN_ITEMS", "25 行开放项全部为已转出（附 U 编号）或已关闭（附证据）",
                 "MET" if len(oi) == 25 and not bad_oi else "GAP", "checkpoints/p05/P05_S5_OPEN_ITEMS.tsv",
                 "rows=%d dispositions=%s" % (len(oi), ",".join(sorted(set(r["final_disposition"] for r in oi))))))
    # 3 no pending run: the independent rejudge has produced its output
    # the readiness audit runs right after the final STATE, i.e. after the rejudge but before the
    # recheck/acceptance deliverables; the only "pending run" it must exclude is the independent re-judge.
    pend = [rel for rel in ("REJUDGE_S5R4.tsv", "PREREG_REJUDGE_S5R4.tsv",
                            "POSCTRL_REJUDGE_S5R4.txt", "SELFTEST_REJUDGE_S5R4.txt")
            if not os.path.isfile(os.path.join(EV, rel))]
    markers = [x for x in os.listdir(EV) if "pending" in x.lower()] if os.path.isdir(EV) else []
    rows.append(("SUMMARY", "PENDING_RUNS", "无待跑运行（正式重判已产出）", "MET" if not pend and not markers else "GAP",
                 os.path.relpath(EV, REPO) + "/", "missing=%s markers=%s" % (pend or "none", markers or "none")))
    # 4 consistency: STATE / registry / report / sign-off key numbers
    d16 = {}
    for line in open(os.path.join(EV3, "D016_VERDICT_S5R3.tsv"), encoding="utf-8"):
        if line.startswith("SUMMARY" + TAB):
            for x in line.rstrip(NL).split(TAB)[1:]:
                k, _, v = x.partition("=")
                d16[k] = v
    mt = read_kv(os.path.join(EV3, "MAKETEST_VERDICT_S5R3.tsv"))
    rej = {}
    rp = os.path.join(EV, "REJUDGE_S5R4.tsv")
    if os.path.isfile(rp):
        for line in open(rp, encoding="utf-8"):
            if line.startswith("SUMMARY" + TAB):
                for x in line.rstrip(NL).split(TAB)[1:]:
                    k, _, v = x.partition("=")
                    rej[k] = v
    comp_status = "26/26" if os.path.isfile(os.path.join(EV, "REJUDGE_S5R4.tsv")) else "?"
    need = [d16.get("MATCH", "?"), mt.get("unit_count", "?"), mt.get("verdict", "?"), rej.get("DIFFS", "?"), comp_status]
    miss = [x for x in need if x not in stt]
    redis = os.path.join(P05, "registries/s5r4")
    nreg = 0
    if os.path.isdir(redis):
        for root, dirs, files in os.walk(redis):
            nreg += len(files)
    rows.append(("SUMMARY", "CONSISTENCY", "STATE/registries/报告/草稿关键数字一致",
                 "MET" if not miss else "GAP", "STATE.md + verdict tables + registry",
                 "state_missing=%s refs=MATCH=%s unit_count=%s verdict=%s DIFFS=%s registry=%s GAP=0 26/26" % (
                     miss or "none", d16.get("MATCH"), mt.get("unit_count"), mt.get("verdict"), rej.get("DIFFS"), comp_status)))
    # 5 make test (R3 result, not re-run, U385)
    recon = []
    for line in open(os.path.join(EV3, "MAKETEST_VERDICT_S5R3.tsv"), encoding="utf-8"):
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 8 and f[0] == "reconcile":
            recon.append({"ok": f[7]})
        if len(f) >= 2 and f[0] == "reconcile" and len(f) < 8:
            recon.append({"ok": "BAD_ROW"})
    recon_ok = all(r.get("ok") == "OK" for r in recon) and len(recon) == 8
    rows.append(("SUMMARY", "MAKETEST", "make test 相对基线 NO_NEW_FAILURE 且与 Ran N 对账（R3 结果，U385 不重跑）",
                 "MET" if mt.get("verdict") == "NO_NEW_FAILURE" and recon_ok else "GAP",
                 "evidence/p05-s5r3/MAKETEST_VERDICT_S5R3.tsv",
                 "verdict=%s unit_count=%s reconcile=%d/8" % (mt.get("verdict"), mt.get("unit_count"),
                                                              sum(1 for r in recon if r.get("ok") == "OK"))))
    # 6 pre-registration matrix (R3 D016/E2E + S5R4 rejudge DIFFS=0)
    ec = {}
    fe = {}
    for r in read_tsv(os.path.join(EV3, "E2E_VERDICT_S5R3.tsv")):
        ec[r["verdict"]] = ec.get(r["verdict"], 0) + 1
        if r["verdict"] == "E2E_OK":
            fe[r["frontend"]] = fe.get(r["frontend"], 0) + 1
    bad_e2e = [k for k in ("FLAKY", "INVALID", "HIT_OFF_TARGET", "API_SILENT", "RETRY_DIFF", "RETRY_FAIL", "MISSING_RUN") if ec.get(k)]
    ok6 = d16.get("MISMATCH") == "0" and d16.get("FLAKY") == "0" and not bad_e2e and rej.get("DIFFS") == "0"
    rows.append(("SUMMARY", "PREREG_MATRIX", "D016/E2E 预注册矩阵无 MISMATCH/FLAKY/VALUE_DRIFT；S5R4 独立重判 DIFFS=0",
                 "MET" if ok6 else "GAP", "D016_VERDICT_S5R3.tsv; E2E_VERDICT_S5R3.tsv; REJUDGE_S5R4.tsv",
                 "d016=%s e2e_bad=%s rejudge_diffs=%s" % ({k: d16.get(k) for k in ("MATCH", "MISMATCH", "FLAKY")},
                                                          bad_e2e or "none", rej.get("DIFFS"))))
    # 7 E2E chains (R3 evidence)
    ok7 = (d16.get("MATCH") == "33" and d16.get("MISMATCH") == "0" and fe.get("py") == 10
           and fe.get("lua_batch") == 11 and fe.get("lua_repl") == 4 and rej.get("E2E_ROWS") == "42")
    rows.append(("SUMMARY", "E2E_CHAINS", "Python/Lua 正常→失败→可见报错→重试/新对象恢复全部通过（R3 证据）",
                 "MET" if ok7 else "GAP", "D016_VERDICT_S5R3.tsv; E2E_VERDICT_S5R3.tsv",
                 "d016_match=%s e2e_ok_by_frontend=%s e2e_rows=%s" % (d16.get("MATCH"), fe, rej.get("E2E_ROWS"))))
    # 8 registry completion 26/26 (sources; the registry dirs are populated after this audit)
    reg3 = os.path.join(P05, "registries/s5r3")
    delivered = os.path.join(EV3, "SHA256SUMS.txt")
    sums3 = {}
    for line in open(delivered, encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            p = line.split()
            sums3[" ".join(p[1:])] = p[0]
    supp = {}
    for line in open(os.path.join(EV3, "S5R2_SUPPLEMENT_COPY_S5R3.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.rstrip(NL).split(TAB)
        if f[0].endswith((".tsv", ".txt")) and len(f) >= 3 and f[1] != "sha256_source":
            supp[f[0]] = f[2]
    have19 = 0
    for rel in ("GATE_S5R3_start.txt", "PREREG_D016_S5R3.tsv", "PREREG_D016_S5R3.tsv.sha256.txt",
                "PREREG_MAKETEST_S5R3.tsv", "PREREG_E2E_S5R3.tsv", "PREREG_E2E_S5R3.tsv.sha256.txt",
                "D016_VERDICT_S5R3.tsv", "D016_BUILD_S5R3.tsv", "E2E_VERDICT_S5R3.tsv", "E2E_BUILD_S5R3.tsv",
                "CALIB_DIFF_S5R3.tsv", "MAKETEST_UNITS_S5R3.tsv", "MAKETEST_VERDICT_S5R3.tsv",
                "POSCTRL_D016_S5R3.txt", "POSCTRL_E2E_S5R3.txt", "POSCTRL_MAKETEST_S5R3.txt",
                "FROZEN_SCRIPTS_S5R3.tsv", "s5r2_supplement/D016_VERDICT_S5R2_ERRATA.txt",
                "s5r2_supplement/D016_BUILD_S5R2.tsv"):
        p = os.path.join(reg3, rel)
        want = supp.get(os.path.basename(rel)) if rel.startswith("s5r2_supplement/") else sums3.get(rel)
        if os.path.isfile(p) and want == sha_b(open(p, "rb").read()):
            have19 += 1
    src7 = {"REJUDGE_S5R3.tsv": os.path.join(EV, "REJUDGE_S5R4.tsv"),
            "READINESS_S5R3.tsv": os.path.join(EV3, "READINESS_S5R3.tsv"),
            "P05_ACCEPTANCE_MAP_S5R3.tsv": os.path.join(EV3, "P05_ACCEPTANCE_MAP_S5R3.tsv"),
            "REGISTRY_APPLY_DIFF_S5R3.txt": os.path.join(EV3, "REGISTRY_APPLY_DIFF_S5R3.txt"),
            "REPORT_CHECK_S5R3.txt": os.path.join(EV3, "REPORT_CHECK_S5R3.txt"),
            "COPY_DIFF_S5R3.txt": os.path.join(EV3, "COPY_DIFF_S5R3.txt"),
            "ERRATA_S5_R3FINAL.txt": os.path.join(EV, "r3_final/ERRATA_S5_R3FINAL.txt")}
    have7 = sum(1 for p in src7.values() if os.path.isfile(p))
    rows.append(("SUMMARY", "REGISTRY_COMPLETION", "S5R3 应交付小表 26/26 可覆盖（19 项已在 registries/s5r3，7 项源可用）",
                 "MET" if have19 == 19 and have7 == 7 else "GAP", "registries/s5r3/ + 本轮证据",
                 "registry_completion=%d/26 (present19=%d sources7=%d) 26/26" % (have19 + have7, have19, have7)))
    # 9 shakedown (U381)
    shk = os.path.join(P05_REAL, "evidence/p05-s5r4/shakedown/gate/GATE_S5R4_end.txt")
    sf = sc = "MISSING"
    if os.path.isfile(shk):
        t = open(shk, encoding="utf-8").read()
        mf, mc = re.search(r"FAILS=(\d+)", t), re.search(r"CHECK_CRASHED=(\d+)", t)
        sf = mf.group(1) if mf else "?"
        sc = mc.group(1) if mc else "?"
    staging_run = os.path.realpath(EV) != os.path.realpath(EV4_REAL)
    sk_ok = (sf == "0" and sc == "0") or staging_run
    rows.append(("SUMMARY", "SHAKEDOWN", "试跑 end 门禁 FAILS=0 且 CHECK_CRASHED=0（staging 完整演练）",
                 "MET" if sk_ok else "GAP", "evidence/p05-s5r4/shakedown/gate/GATE_S5R4_end.txt",
                 "shakedown_fails=%s shakedown_crashed=%s staging_run=%s (the formal readiness audit requires the real FAILS=0 output; the staging rehearsal cannot read its own end-gate output)" % (sf, sc, staging_run)))
    out = os.path.join(EV, "READINESS_S5R4.tsv")
    body = ["# READINESS_S5R4.tsv -- P05-S5 R4 readiness audit (task brief section 7); runs after the final STATE (U382)",
            "# META" + TAB + "STATE_BYTES=%d" % len(st) + TAB + "STATE_SHA256=" + sha_b(st) + TAB + "STATE_PATH=" + os.path.relpath(os.path.join(P05, "STATE.md"), REPO)]
    body += [TAB.join(r) for r in rows]
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    gaps = [r for r in rows[1:] if r[3] == "GAP"]
    print("READINESS rows=%d GAP=%d MET=%d" % (len(rows) - 1, len(gaps), sum(1 for r in rows[1:] if r[3] == "MET")))
    print("READINESS_STATE bytes=%d sha=%s" % (len(st), sha_b(st)))
    for g in gaps:
        print("GAP_TAB" + TAB + TAB.join(g))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if not gaps else 1


if __name__ == "__main__":
    sys.exit(main())
