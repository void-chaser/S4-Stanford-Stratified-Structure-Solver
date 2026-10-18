#!/usr/bin/env python3
# append_errata_r9m3b.py -- append the E9-46.. entries for the K-1..K-8 claims (all verified true by
# audit_r9m3a_r9m3b_v3.py) and for the U334..U337 facts, asserting the opening prefix first. New file (r9m3b).
# usage: python3 -I -B testing/d003/stage_s4r9/append_errata_r9m3b.py ERRATA_9.txt AUDIT_R9M3A_R9M3B.tsv
import os, sys, hashlib

REPO = os.getcwd()
TAB = chr(9)
NL = chr(10)
PRE_BYTES = 38912
PRE_SHA = "d5d8d9a0f46086df6855cb4637b035a641b327dd2f95fff1773002b9fbdc49ee"
PRE_LAST = "E9-45"
PRE_COUNT = 45
IMPACT = {
    "K-1": ("M3a 的 Python E2E 参考步在注入环境下执行，预注册的命中点实际未在注入进程的第一次求解处被观测。", "登记 E9-46；本轮 e2e_python_r9m3b.py 与 run_e2e_r9m3b.py 改为参考值另起无注入进程，注入进程的第一次求解即 A 步。"),
    "K-2": ("M3a 的 Lua 装置不可运行：选项名不存在、参数传递方式错误、多余 argv 会被当作脚本文件。", "登记 E9-47；本轮 e2e_lua_r9m3b.lua 用 S4.arg + -a 传参、使用真实方法名并在缺失时 error 退出，不再 pcall 静默跳过。"),
    "K-3": ("M3a 预注册把 jones/nv/vl 的 s4malloc nth 记为 1，实际会落在 fmm_FFT 而不是 PolBasis。", "登记 E9-48；本轮以注入无关的 gdb 校准把三族的 nth 定为 3（前两次来自 FMMGetEpsilon_FFT），并记录校准 size。"),
    "K-4": ("M3a 的 E2E_API_SURVEY 把 ClosedForm、Kottke、Lua UseExperimentalFMM、Lua REPL 继续执行误判为不可达，导致点族与研究结论错误。", "登记 E9-49；本轮 E2E_API_SURVEY_R9M3B.md 逐条按源码改写，并把 CF、KT、EXP、REPL 纳入正式点族。"),
    "K-5": ("M3a 的 make test 解析漏掉 90 个带 docstring 的单元，且未与 Ran N 对账，M3a 的 NO_NEW_FAILURE 缺少单元级完备性。", "登记 E9-50；本轮 judge_maketest_r9m3b.py 按“直到下一个单元行为止”的状态词解析并与 Ran N / skipped=k 逐遍对账。"),
    "K-6": ("M3a 报告正文与表一对 /tmp 写入给出相反陈述。", "登记 E9-51；本轮表一按 U338 补登记为项目套件固有、临时目录、非执行者违规，正文与表一一致。"),
    "K-7": ("M3a 的 Lua visible 判据恒为真、阳性对照未覆盖 Lua，E2E 判定对 Lua 完全失效。", "登记 E9-52；本轮 visible 判据改为具体错误文本（GetPoyntingFlux: 开头），阳性对照在落盘篡改副本上覆盖三个前端与全部类别。"),
    "K-8": ("M3a 的预注册与装置选项不一致，报告编号与 STATE 数字错误，交付物可追溯性受损。", "登记 E9-53；本轮预注册的选项列与装置逐组一致，报告编号与 STATE 数字由 report_check 复算校验。"),
    "U334": ("M3a 冻结期的 run_maketest 调用计数与“每个脚本调用 1 次”的纪律不符。", "登记 E9-54；按 U334 接受第二次调用的四遍结果为正式结果，本轮不重跑，报告与 STATE 记录该事实。"),
    "U335": ("M3a 的收尾脚本在 (i) 之后写入 testing/d003，且有两个脚本内部生成的产物未出现在命令行里。", "登记 E9-55；按 U335 接受并登记，本轮收尾脚本全部在 (i) 之前冻结，门禁按“脚本声明的输出清单”归属内部生成物。"),
    "U336": ("M3a 的 report_check 数字核对与实际 STATE 字节数不符。", "登记 E9-56；按 U336 以 STATE 实际 5191 字节为准，只登记勘误，不改 M3a 报告。"),
    "U337": ("M3a 的 end 门禁 6 条缺陷与 start 复核 10 条 FAIL 使其核验效力受损。", "登记 E9-57；本轮 gate_check_r9m3b.py 按 U337 修好：调用计数从 FROZEN 清单读文件名、start 不变量只在 start 模式检查、end 模式只查前缀 sha、清单解析允许反引号。"),
}


def read_audit(path):
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


def main():
    if len(sys.argv) < 3:
        print("usage: append_errata_r9m3b.py ERRATA_9.txt AUDIT.tsv")
        return 2
    path, auditp = sys.argv[1], sys.argv[2]
    data = open(path, "rb").read()
    if len(data) != PRE_BYTES or hashlib.sha256(data).hexdigest() != PRE_SHA:
        print("HARD_STOP prefix mismatch bytes=%d sha=%s" % (len(data), hashlib.sha256(data).hexdigest()))
        return 2
    txt = data.decode("utf-8")
    ids = [line.split()[0] for line in txt.splitlines() if line.startswith("E9-")]
    if ids[-1] != PRE_LAST or len(ids) != PRE_COUNT:
        print("HARD_STOP last=%s count=%d" % (ids[-1], len(ids)))
        return 2
    audit = read_audit(auditp)
    bad = [r["item"] for r in audit if r.get("verdict") != "属实"]
    if bad:
        print("HARD_STOP audit items not true: " + ",".join(bad))
        return 2
    if not txt.endswith(NL):
        txt += NL
    blocks = []
    n = PRE_COUNT
    for r in audit:
        n += 1
        eid = "E9-%d" % n
        impact, action = IMPACT[r["item"]]
        blocks.append(NL.join([
            eid,
            "- 事实：规划者复核项 " + r["item"] + " 属实（claim: " + r["planner_claim"] + "）。本轮由脚本从原文件复算： " + r["computed_facts"],
            "- 证据文件与行号：" + r["evidence_file_lines"],
            "- 影响范围：" + impact,
            "- 处理方式：" + action,
        ]))
    new = txt + NL.join(blocks) + NL
    open(path, "wb").write(new.encode("utf-8"))
    nb = new.encode("utf-8")
    print("appended=%d bytes %d -> %d sha %s" % (len(blocks), len(data), len(nb), hashlib.sha256(nb).hexdigest()))
    print("new_last_id=E9-%d count=%d" % (n, n))
    return 0


if __name__ == "__main__":
    sys.exit(main())
