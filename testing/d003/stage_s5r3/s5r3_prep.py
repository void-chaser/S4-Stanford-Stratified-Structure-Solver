#!/usr/bin/env python3
# s5r3_prep.py -- P05-S5 R3 M1: append rulings U372..U377 and errata ES5-6..ES5-8 (pure append with
# byte-prefix assertions), and copy the two missing S5R2 D016 files into registries/s5r3/s5r2_supplement/
# with sha256 checked against the p05-s5r2 evidence manifest. One call, one safe_run record.
import os, sys, subprocess, hashlib

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def sha_f(p):
    return sha_b(open(p, "rb").read())


def wr(p, t):
    rp = os.path.realpath(p)
    if not (rp.startswith(os.path.join(REPO, "checkpoints/p05") + os.sep)
            or rp.startswith(os.path.join(REPO, "testing/d003") + os.sep)):
        raise SystemExit("WRITE_OUTSIDE " + rp)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(t)


def append_assert(path, add):
    old = open(path, "rb").read()
    ns = NL.join(add) + NL
    new = old + ns.encode("utf-8")
    wr(path, new.decode("utf-8"))
    chk = open(path, "rb").read()
    if chk[:len(old)] != old:
        raise SystemExit("PREFIX_BROKEN " + path)
    return len(old), len(chk), sha_b(old), sha_b(chk)


def max_u(path):
    m = "U0"
    for line in open(path, encoding="utf-8"):
        f = line.split(TAB)
        if f and f[0].startswith("U") and f[0][1:].isdigit() and int(f[0][1:]) > int(m[1:]):
            m = f[0]
    return m


RULINGS = [
    ("U372", "S5R2 的 D016 比较器缺陷（d016_run_s5r2.py 的 proc_row 把预注册标签 ABSENT 与观测计数 0 比较，导致 PY_STDERR_INFO2/LUA_STDERR_INFO2 判 MISMATCH）登记为 ES5-6；S5R2 判定表与门禁 FAIL 保留为历史，不改。S5R3 用新脚本 d016_run_s5r3.py（同一 D016 点族与输入、同一期望含义）在新预注册 PREREG_D016_S5R3.tsv 下作为新运行正式跑两遍；这不是改期望。"),
    ("U373", "S5R3 全量 E2E 复用 M3b 的 42 点（25 注入 + 17 对照）与 M3b 的装置逻辑：把 testing/d003/stage_s4r9/ 下 M3b 的构建、运行、判定脚本复制为 stage_s5r3/ 的 *_s5r3 版本，只改路径、轮次标签与输出文件名，复制后写逐行 diff 证明没有其他改动；构建方式与 M3b 相同；无注入校准结果必须与 CALIB_E2E_R9M3B.tsv 的命中序号与 size 逐点一致，不一致就停下报告，不得自行调整 nth。"),
    ("U374", "make test 沿用 M3a 的方法：B 树（37a82e8）与 F4 树各两遍，判据 NO_NEW_FAILURE（F4 失败集合 ⊆ B 失败集合、F4 两遍无不一致、两树单元集合相同），单元数必须与日志 \"Ran N\" 对账。"),
    ("U375", "AC-4 由 U364 回答（历史证据可引用，S5R3 重跑）；AC-3 按 S5R3 E2E 与 D016 结果给出最终映射。"),
    ("U376", "批准 S5R3 修改 testing/s4test/ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md：只追加或替换由脚本列出的行，内容为 ES5-6/7 的更正说明与 S5R3 结果；这两个文件纳入本轮提交范围；不改 AGENTS.md。"),
    ("U377", "S5R3 编写 P05_S5_SIGNOFF_DRAFT.md（S5 范围声明草稿，标明\"未签收\"），不写签收文件。"),
]
ERRATA = [
    "ES5-6",
    "- 事实：S5R2 的 D016 正式两遍在行为上完全一致：28 个行为点行（8 个失败点 + 8 个同对象重试 + 8 个对照 + 2 个恢复 + 2 个参考，两前端）两遍观测相同、0 FLAKY、两个进程 rc=0、两条恢复行两遍 rel_err=0.000e+00；两个 stderr 计数均为 0。",
    "- 缺陷位置：d016_run_s5r2.py 第 218-219 行的 proc_row 把预注册标签 ABSENT 与观测计数 0 做字符串直比，导致 PY_STDERR_INFO2/LUA_STDERR_INFO2 判 MISMATCH。行为事实是 0 次出现，正是预注册期望。",
    "- 冻结前未被发现的原因：S5R2 试跑门禁把 D016_VERDICT 检查写成 deferred 就判 PASS（checkpoints/p05/evidence/p05-s5r2/shakedown/gate/GATE_S5R2_end.txt 第 83 行：PASS D016_VERDICT_TWO_PASSES_NO_MISMATCH expected=MATCH=33 MISMATCH=0 FLAKY=0 actual=deferred(shakedown, formal verdict comes from the frozen period)），缺陷因此在冻结前没有暴露。",
    "- 影响范围：S5R2 D016_VERDICT_S5R2.tsv 的 SUMMARY 为 MATCH=31 MISMATCH=2 FLAKY=0；MISMATCH 不是行为偏差，也不是期望变更。S5R2 判定表与门禁 FAIL 保留为历史，不改。",
    "- 处理方式：U372。S5R3 用新脚本 d016_run_s5r3.py（同一点族与输入、同一期望含义；比较器按预注册列名读取，stderr 类行规定为\"预注册 ABSENT ⇔ 计数 == 0\"，并在新预注册中显式写 expected_count=0；不对任何行做字符串直比的特例）在新预注册 PREREG_D016_S5R3.tsv 下作为新运行正式跑两遍；这不是改期望。",
    "ES5-7",
    "- 事实：S5R2 报告 §7 没有说明 MISMATCH=2 的原因，也没有指向 D016_VERDICT_S5R2_ERRATA.txt；§8 表二（工具与脚本事件）缺少\"冻结期比较器缺陷\"一条；ISSUE_REGISTRY.md 第 48 行与 PROJECT_ROADMAP.md 第 145 行的\"MISMATCH=2\"缺少原因说明。",
    "- 处理方式：不改 S5R2 报告（历史）。按 U376 用脚本把这两行原文替换为\"MISMATCH=2 为比较器格式缺陷（ES5-6），行为点全 MATCH；S5R3 重跑结果见 checkpoints/p05/registries/s5r3/D016_VERDICT_S5R3.tsv\"；替换只发生在脚本列出的行，unified diff 见 REGISTRY_APPLY_DIFF_S5R3.txt。",
    "- 影响范围：本勘误不改变 S5R2 报告、S5R2 registries 与 S5R2 门禁文件本身；S5R3 报告的事件表二列出本缺陷。",
    "ES5-8",
    "- 事实：D016_VERDICT_S5R2_ERRATA.txt 与 D016_BUILD_S5R2.tsv 留在证据目录 p05-s5r2/，未复制进 registries/s5r2/，因此 s5r2 小表清单不含这两件。",
    "- 处理方式：按任务书 §2 复制到 registries/s5r3/s5r2_supplement/，不改 registries/s5r2/ 及其 SHA256SUMS.txt；复制件 sha256 与 p05-s5r2/SHA256SUMS.txt 的记录逐项一致（脚本校验结果见 checkpoints/p05/evidence/p05-s5r3/S5R2_SUPPLEMENT_COPY_S5R3.tsv）。",
    "- 附带说明：本轮按 §2 向 registries/s5r2/ERRATA_S5.txt 纯追加 ES5-6..8，因此 registries/s5r2/SHA256SUMS.txt 中 ERRATA_S5.txt 的旧 sha256 与追加后的文件不再相等。该清单文件本身不改、不重写；S5R3 end 门禁对 s5r2 小表的复核把 ERRATA_S5.txt 记为\"按 §2 追加导致预期变化\"，其余 10 项仍逐项复核。",
]


def main():
    gate = os.path.join(EV, "GATE_S5R3_start.txt")
    if not os.path.isfile(gate):
        print("HARD_STOP start gate missing")
        return 2
    if "FAILS=0" not in open(gate, encoding="utf-8").read():
        print("HARD_STOP start gate has FAILs")
        return 2
    rows = ["# RULINGS_APPEND_S5R3.tsv -- pure append of U372..U377 (prefix asserted byte-for-byte)",
            TAB.join(["id", "given_in_round", "bytes_before", "bytes_after", "prefix_sha256", "after_sha256", "max_u_after"])]
    rul = os.path.join(P05, "registries/RULINGS.tsv")
    repair = "--repair-errata" in sys.argv
    for uid, txt in ([] if repair else RULINGS):
        b, a, sb, sa = append_assert(rul, [TAB.join([uid, "P05-S5 R3 任务书 §1", txt, "P05-S5 R3 任务书 §1", "生效"])])
        mu = max_u(rul)
        rows.append(TAB.join([uid, "P05-S5 R3 任务书 §1", str(b), str(a), sb, sa, mu]))
        print("RULING %s bytes %d -> %d max_u=%s" % (uid, b, a, mu))
    wr(os.path.join(EV, "RULINGS_APPEND_S5R3.tsv"), NL.join(rows) + NL)
    rows = ["# ERRATA_APPEND_S5R3.tsv -- pure append of ES5-6..ES5-8 (prefix asserted byte-for-byte)",
            TAB.join(["errata_id", "bytes_before", "bytes_after", "prefix_sha256", "after_sha256"])]
    err = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
    blocks = []
    for line in ERRATA:
        if line.startswith("ES5-"):
            blocks.append([line])
        else:
            blocks[-1].append(line)
    if "--repair-errata" in sys.argv:
        # repair mode: rebuild from the p05-s5r2 evidence copy, then pure-append the three blocks.
        ev_orig = os.path.join(P05, "evidence/p05-s5r2/ERRATA_S5.txt")
        want_sha = None
        for line in open(os.path.join(EV, "GATE_S5R3_start.txt"), encoding="utf-8"):
            if line.startswith("RECORD" + TAB + "ERRATA_S5_SHA256" + TAB):
                want_sha = line.rstrip(NL).split("=")[-1]
        ob = open(ev_orig, "rb").read()
        if sha_b(ob) != want_sha:
            print("HARD_STOP evidence ERRATA copy sha mismatch")
            return 2
        open(err, "wb").write(ob)
        print("ERRATA rebuilt from evidence copy sha=%s" % sha_b(ob))
    for blk in blocks:
        b, a, sb, sa = append_assert(err, [""] + blk)
        rows.append(TAB.join([blk[0], str(b), str(a), sb, sa]))
        print("ERRATA %s bytes %d -> %d" % (blk[0], b, a))
    wr(os.path.join(EV, "ERRATA_APPEND_S5R3.tsv"), NL.join(rows) + NL)
    # --- s5r2 supplement copy, sha checked against the p05-s5r2 evidence manifest
    src = os.path.join(P05, "evidence/p05-s5r2")
    want = {}
    for line in open(os.path.join(src, "SHA256SUMS.txt"), encoding="utf-8"):
        line = line.rstrip(NL)
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        want[parts[1]] = parts[0]
    dst = os.path.join(P05, "registries/s5r3/s5r2_supplement")
    os.makedirs(dst, exist_ok=True)
    rows = ["# S5R2_SUPPLEMENT_COPY_S5R3.tsv -- the two S5R2 D016 files copied into registries/s5r3/s5r2_supplement/ (ES5-8)",
            "# sha256_evidence = the value recorded in checkpoints/p05/evidence/p05-s5r2/SHA256SUMS.txt",
            TAB.join(["file", "sha256_source", "sha256_copy", "sha256_evidence", "match"])]
    ok = True
    for f in ("D016_VERDICT_S5R2_ERRATA.txt", "D016_BUILD_S5R2.tsv"):
        sp = os.path.join(src, f)
        dp = os.path.join(dst, f)
        hs = sha_f(sp)
        open(dp, "wb").write(open(sp, "rb").read())
        hd = sha_f(dp)
        ev = want.get(f, "NOT_IN_EVIDENCE_MANIFEST")
        m = "OK" if (hs == hd == ev) else "FAIL"
        if m != "OK":
            ok = False
        rows.append(TAB.join([f, hs, hd, ev, m]))
        print("SUPPLEMENT %s %s" % (f, m))
    wr(os.path.join(EV, "S5R2_SUPPLEMENT_COPY_S5R3.tsv"), NL.join(rows) + NL)
    # record current errata/rulings state for later gates
    st = ["# LEDGER_STATE_S5R3.txt -- rulings/errata byte+sha state after the M1 append",
          TAB.join(["file", "bytes", "sha256", "max_u_or_last_e"])]
    st.append(TAB.join(["registries/RULINGS.tsv", str(len(open(rul, "rb").read())), sha_f(rul), max_u(rul)]))
    eb = open(err, "rb").read()
    last = [l for l in eb.decode("utf-8").splitlines() if l.startswith("ES5-")]
    st.append(TAB.join(["registries/s5r2/ERRATA_S5.txt", str(len(eb)), sha_b(eb), last[-1] if last else "?"]))
    wr(os.path.join(EV, "LEDGER_STATE_S5R3.txt"), NL.join(st) + NL)
    print("ERRORS=%d" % (0 if ok else 1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
