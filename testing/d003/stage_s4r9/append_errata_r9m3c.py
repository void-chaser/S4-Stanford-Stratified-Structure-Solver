#!/usr/bin/env python3
# append_errata_r9m3c.py -- append E9-58..E9-66 to checkpoints/p05/registries/s4r9/ERRATA_9.txt (old file + new
# entries). The prefix sha256 is asserted; the L audit rows must all be 属实 before writing. New file (r9m3c).
import os, sys, re, hashlib
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
AUDIT = os.path.join(EV, "AUDIT_R9M3B_R9M3C.tsv")
P = os.path.join(REPO, "checkpoints/p05/registries/s4r9/ERRATA_9.txt")
M3B_EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
MKV = os.path.join(M3B_EV, "MAKETEST_VERDICT_R9M3B.tsv")
REPORT = os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3b_REPORT.md")
GATE = os.path.join(REPO, "testing/d003/stage_s4r9/gate_check_r9m3b_v3.py")
EXPECTED_SHA = "2d32e4f1d8e584e65c7122aa6e5efd710b32991ddd5cadac4ea5cec979412716"
EXPECTED_BYTES = 51809
TAB = chr(9)
NL = chr(10)
Q = chr(34)


def read_audit():
    rows = {}
    hdr = None
    for line in open(AUDIT, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows[f[0]] = dict(zip(hdr, f))
    return rows


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    audit = read_audit()
    for k in ("L-1", "L-2", "L-3", "L-4", "L-5", "L-6"):
        if k not in audit:
            print("HARD_STOP audit missing " + k)
            return 2
        if audit[k].get("verdict") != "属实":
            print("HARD_STOP audit %s verdict %s" % (k, audit[k].get("verdict")))
            return 2
    rep = open(REPORT, encoding="utf-8").read()
    u346 = ("S-C 的构建/校准/预注册/注入试跑先于正式 start 门禁执行" in rep
            and "在冻结清单写定之前执行" in rep)
    g = open(GATE, encoding="utf-8").read()
    okn = 0
    tot = 0
    for line in open(os.path.join(M3B_EV, "SHA256SUMS.txt"), encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 1)
        if len(parts) == 2:
            tot += 1
            fp = os.path.join(M3B_EV, parts[1].strip())
            if os.path.isfile(fp) and sha(fp) == parts[0]:
                okn += 1
    u347 = ("sha_sums_r9m3b.py" in g) and (okn == tot and tot > 0)
    rec = [l.rstrip(NL).split(TAB) for l in open(MKV, encoding="utf-8") if l.startswith("reconcile" + TAB)]
    rec_ok = len(rec) == 8 and all(r[-1] == "OK" for r in rec)
    u348 = rec_ok and ("4 遍 × 2 段对账 存在 FAIL" in rep)
    for name, ok in (("U346", u346), ("U347", u347), ("U348", u348)):
        if not ok:
            print("HARD_STOP %s facts not found" % name)
            return 2
    refs = {k: audit[k]["file_line_refs"] for k in ("L-1", "L-2", "L-3", "L-4", "L-5", "L-6")}
    facts = {
        "L-1": "M3b 报告的附录 A 在写 make test 重解析时写“4 遍 × 2 段对账 存在 FAIL”，而列出的 4 行最后一列都是 OK。成因是 closeout_report_state_r9m3b.py 的 recon_bad 用 r[6] != " + Q + "OK" + Q + " 判定，r[6] 是 skipped 期望值列，ok 在 r[7]；report_check_r9m3b.py 未检出该句（REPORT_CHECK_R9M3B.txt 为 FAILS=0）。",
        "L-2": "gate_check_r9m3b_v3.py 的 EVIDENCE_SHA256SUMS 检查写死 testing/d003/stage_s4r9/sha_sums_r9m3b.py，而 FROZEN_SCRIPTS_R9M3B.tsv 与冻结期实际使用的是 sha_sums_r9m3b_v2.py，违背 U337 的“从 FROZEN 清单读实际文件名”。",
        "L-3": "M3b 报告 §9 表格在第 5 行之前、§12.2 表格在第 8 行之前各有一个空行，Markdown 表格被截断。",
        "L-4": "执行者对话摘要中“需用户裁决”的第 5 项（end 门禁检查器缺陷）与报告 §13 的第 5 项（是否另立 M3a 门禁更正件）不一致；end 门禁缺陷只出现在附录 B。报告侧结构由脚本复核；对话摘要不在仓库内。",
        "L-5": "LEDGER_CHECK_R9M3B.tsv 把 RP-R8-M2c-1/1b 的去向写成“待用户裁决是否关闭”，与 U304 的关闭裁决不一致；并把 RP-R8-M2c-1b 判为“STATE 中无对应行”，而 STATE 使用合并行“RP-R8-M2c-1/1b”。",
        "L-6": "范围事实：PREREG_E2E_R9M3B.tsv 中 lua_repl 只有 cf/fft/kt/vl 四个注入点与四个对照，jones/nv/exp 没有 REPL 点；这三族在 py 与 lua_batch 各有点、exp 仅 lua_batch。",
    }
    impacts = {
        "L-1": "M3b 报告附录 A 的 make test 结论与源表相反，派生文字不可信；report_check 未覆盖附录 A 的派生句。",
        "L-2": "M3b end 门禁的 EVIDENCE_SHA256SUMS 检查恒不匹配冻结脚本名，产生假 FAIL（U347）。",
        "L-3": "M3b 报告两张表被空行截断，Markdown 呈现不完整。",
        "L-4": "M3b 对话摘要与报告 §13 的第 5 项不一致。",
        "L-5": "M3b 台账核对把已由 U304 关闭的项写成待裁决，并误判合并行。",
        "L-6": "预注册的 REPL 覆盖范围只在 cf/fft/kt/vl 四族；jones/nv/exp 无 REPL 点，属范围事实。",
    }
    actions = {
        "L-1": "登记 E9-58；本轮 closeout 按列名读取 reconcile 的 ok 列，report_check 逐句核对附录 A 的派生文字，并在试跑期对故意写错的报告副本判出 FAIL。",
        "L-2": "登记 E9-59；本轮 gate_check 的 EVIDENCE_SHA256SUMS 与 EVENTS 锚点脚本名一律从 FROZEN_SCRIPTS_R9M3C.tsv 读取。",
        "L-3": "登记 E9-60；本轮报告表格内不得有空行，report_check 检查章节表格连续性。",
        "L-4": "登记 E9-61；本轮报告“需用户裁决”与对话摘要逐条一致。",
        "L-5": "登记 E9-62；本轮最终红点台账按最新裁决（U304、U350）记录关闭状态，并按合并行核对。",
        "L-6": "登记 E9-63；本轮 READINESS/S5 移交明确 REPL 覆盖仅 cf/fft/kt/vl 四族。",
    }
    entries = []
    for i, k in enumerate(("L-1", "L-2", "L-3", "L-4", "L-5", "L-6"), 58):
        entries.append(("E9-%d" % i, facts[k], refs[k], impacts[k], actions[k]))
    entries.append(("E9-64",
                    "M3b 表二的两处顺序偏差（S-C 先于 start 门禁；start_recheck 先于冻结清单）存在；预注册早于任何注入运行这一不变量已由 end 门禁检查成立（PREREG_WRITTEN_BEFORE_FIRST_E2E_RUN PASS）。",
                    "P05_S4R9_M3b_REPORT.md §12.2 rows 1 and 10",
                    "M3b 的执行顺序与任务书 §5 不一致。",
                    "按 U346 接受，只登记勘误；本轮严格按 §5 顺序执行，顺序偏差只在表二登记。"))
    entries.append(("E9-65",
                    "M3b end 门禁 EVIDENCE_SHA256SUMS_OK 报 FAIL，实际是 gate_check_r9m3b_v3.py 硬编码 v1 脚本名；m3b 证据清单经本轮只读复验全部 OK（%d/%d 项）。" % (okn, tot),
                    "gate_check_r9m3b_v3.py hard-coded name; m3b/SHA256SUMS.txt",
                    "M3b end 门禁产生一处假 FAIL，核验效力受损。",
                    "按 U347 接受为检查器缺陷；不修改 M3b 门禁文件，由本轮 S-B 只读复验代替。"))
    entries.append(("E9-66",
                    "M3b 报告附录 A 的“4 遍 × 2 段对账 存在 FAIL”与事实相反：8 行 reconcile 的 ok 列全为 OK（closeout 取错列下标）。",
                    "MAKETEST_VERDICT_R9M3B.tsv reconcile rows; P05_S4R9_M3b_REPORT.md 附录 A",
                    "M3b 报告附录 A 的 make test 结论文字错误。",
                    "按 U348 以 MAKETEST_VERDICT_R9M3B.tsv 的 8/8 OK 为准，报告不改，只登记勘误。"))
    old = open(P, "rb").read()
    a = hashlib.sha256(old).hexdigest()
    if a != EXPECTED_SHA:
        print("HARD_STOP errata prefix sha %s != %s" % (a, EXPECTED_SHA))
        return 2
    if len(old) != EXPECTED_BYTES:
        print("HARD_STOP errata prefix bytes %d != %d" % (len(old), EXPECTED_BYTES))
        return 2
    if not old.endswith(NL.encode("utf-8")):
        old += NL.encode("utf-8")
    body = ""
    for eid, fact, ref, impact, action in entries:
        body += eid + NL
        body += "- 事实：" + fact + NL
        body += "- 证据文件与行号：" + ref + NL
        body += "- 影响范围：" + impact + NL
        body += "- 处理方式：" + action + NL
    new = old + body.encode("utf-8")
    if new[:len(old)] != old:
        print("HARD_STOP prefix changed")
        return 2
    open(P, "wb").write(new)
    ids = re.findall(r"^(E9-\d+)", new.decode("utf-8"), re.M)
    print("ERRATA bytes %d -> %d sha %s count=%d last=%s" % (len(old), len(new), hashlib.sha256(new).hexdigest(), len(ids), ids[-1]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
