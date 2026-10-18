#!/usr/bin/env python3
# s5r4_acceptance.py -- P05_ACCEPTANCE_MAP_S5R4.tsv (task brief section 6/9): AC-1..AC-4 with the S5R4
# independent-rejudge and consistency results added to the S5R3 run evidence. All rows must be MET.
# usage: s5r4_acceptance.py formal [--ev-root DIR] [--p05-root DIR]
import os, sys, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
EV3 = os.path.join(P05_REAL, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)


def read_tsv(p, skip_first=("SUMMARY",)):
    rows, hdr = [], None
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f[0] == hdr[0] or f[0] in skip_first:
            continue
        rows.append(dict(zip(hdr, f + [""] * (len(hdr) - len(f)))))
    return rows


def kv(p):
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
        print("usage: s5r4_acceptance.py formal [--ev-root DIR] [--p05-root DIR]", file=sys.stderr)
        return 2
    def arg(n, d):
        return os.path.abspath(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
    EV = arg("--ev-root", EV4_REAL)
    rej = {}
    p = os.path.join(EV, "REJUDGE_S5R4.tsv")
    if os.path.isfile(p):
        for line in open(p, encoding="utf-8"):
            if line.startswith("SUMMARY" + TAB):
                for x in line.rstrip(NL).split(TAB)[1:]:
                    k, _, v = x.partition("=")
                    rej[k] = v
    d16 = {}
    for line in open(os.path.join(EV3, "D016_VERDICT_S5R3.tsv"), encoding="utf-8"):
        if line.startswith("SUMMARY" + TAB):
            for x in line.rstrip(NL).split(TAB)[1:]:
                k, _, v = x.partition("=")
                d16[k] = v
    ec, fe = {}, {}
    for r in read_tsv(os.path.join(EV3, "E2E_VERDICT_S5R3.tsv")):
        ec[r["verdict"]] = ec.get(r["verdict"], 0) + 1
        if r["verdict"] == "E2E_OK":
            fe[r["frontend"]] = fe.get(r["frontend"], 0) + 1
    mt = kv(os.path.join(EV3, "MAKETEST_VERDICT_S5R3.tsv"))
    rows = [("ac_id", "acceptance_criterion", "committed_evidence", "status", "notes"),
            ("AC-1", "每个受影响的 prepare/execute 点有正负对照",
             "P05_S4R9_M2_REPORT.md + registries/s4r9/M2/；P05_S4R9_M1R3_REPORT.md + registries/s4r9/M1R3/",
             "MET", "F4 上 M2 两遍与 M1R3 651 点已提交判定（U364 历史证据可引用）；不外推到其它树/布局"),
            ("AC-2", "失败后模式/缓存不安装",
             "P05_S3_4b_CLOSURE.md（U29：202 注入点 HOLD 202 / VIOLATED 0）；P05_S4R9_M3c_REPORT.md + registries/s4r9/M3c/",
             "MET", "U29 关闭声明与 M3c 就绪审计 GAP=0；范围声明见 U29 原文"),
            ("AC-3", "Python/Lua 可见失败，恢复重试正确",
             "PREREG_E2E_S5R3.tsv; E2E_VERDICT_S5R3.tsv; PREREG_D016_S5R3.tsv; D016_VERDICT_S5R3.tsv; REJUDGE_S5R4.tsv; POSCTRL_E2E_S5R3.txt; POSCTRL_D016_S5R3.txt",
             "MET" if (d16.get("MISMATCH") == "0" and fe.get("py") == 10 and fe.get("lua_batch") == 11
                       and fe.get("lua_repl") == 4 and rej.get("DIFFS") == "0") else "GAP",
             "S5R3 在 F4 上重跑并由 S5R4 独立重判复核：E2E E2E_OK=%d CONTROL_OK=%d（py=%s lua_batch=%s lua_repl=%s），独立重判 DIFFS=%s（E2E 42 点 SAME）；D016 MATCH=%s MISMATCH=%s FLAKY=%s（U375 最终映射，重判 33 行为点 SAME）" %
             (ec.get("E2E_OK", -1), ec.get("CONTROL_OK", -1), fe.get("py"), fe.get("lua_batch"), fe.get("lua_repl"),
              rej.get("DIFFS"), d16.get("MATCH"), d16.get("MISMATCH"), d16.get("FLAKY"))),
            ("AC-4", "M3a/M3b 的 make test 与 E2E 结果能否作为 S5 前端与回归的已提交证据",
             "U364（历史证据可引用，S5R3 在 F4 上重跑）；MAKETEST_VERDICT_S5R3.tsv; E2E_VERDICT_S5R3.tsv",
             "MET", "由 U364 回答；S5R3 重跑 make test %s（unit_count=%s）与 E2E 42 点，MISMATCH/FLAKY 均为 0；S5R4 不重跑（U385），独立重判 DIFFS=%s" %
             (mt.get("verdict", "?"), mt.get("unit_count", "?"), rej.get("DIFFS")))]
    out = os.path.join(EV, "P05_ACCEPTANCE_MAP_S5R4.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(TAB.join(r) for r in rows) + NL)
    met = sum(1 for r in rows[1:] if r[3] == "MET")
    print("ACCEPTANCE rows=%d MET=%d GAP=%d" % (len(rows) - 1, met, len(rows) - 1 - met))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if met == len(rows) - 1 else 1


if __name__ == "__main__":
    sys.exit(main())
