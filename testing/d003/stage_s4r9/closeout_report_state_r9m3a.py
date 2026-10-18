#!/usr/bin/env python3
# closeout_report_state_r9m3a.py -- fill appendix A of the report and finalise STATE.md (closeout step 1).
import os, sys, hashlib
NL = chr(10)
REP = "checkpoints/p05/P05_S4R9_M3a_REPORT.md"
ST = "checkpoints/p05/STATE.md"
PH = "（正式四遍在记录提交 (i) 之后由冻结脚本执行；结果在本附录给出。）"
APP = [
 "正式四遍（记录提交 (i) 之后，冻结脚本 `run_maketest_r9m3a.py`）：",
 "",
 "| 遍 | 树 | make rc | 单元数 |",
 "|---|---|---|---|",
 "| p1 | B | 0 | 175 |",
 "| p1 | F4 | 0 | 175 |",
 "| p2 | B | 0 | 175 |",
 "| p2 | F4 | 0 | 175 |",
 "",
 "- 判定（`MAKETEST_VERDICT_R9M3A.tsv`）：**NO_NEW_FAILURE**；B 与 F4 的失败集合都为空（none），F4 两遍之间 0 处不一致（flaky=none），两树单元集合相同（suite_diff=none）；逐单元 ×4 遍见 `MAKETEST_UNITS_R9M3A.tsv`（175 单元）。",
 "- 阳性对照（冻结期正式调用 1 次）：`POSCTRL_MAKETEST_R9M3A.txt`，NEW_FAILURE 与 FLAKY 两个合成用例都命中（OVERALL PASS）。",
 "- registries 交付物：`registries/s4r9/M3a/SHA256SUMS.txt` 共 17 项（加 `SHA256SUMS.txt` 自身，对应 §10.1 的 18 项）。",
 "- 冻结期异常（照实记录，不修不重跑）：`run_maketest_r9m3a.py` 第一次调用在第四遍 F4 p2 写盘过程被会话执行时限中断（会话侧 120 s 死线），中断现场已原样复制到 `maketest_interrupted/`；随后对同一冻结脚本作了**第二次**（也是最后一次）调用，四遍全部 rc=0。因此 end 门禁的 `POST_I_CALL_COUNT_RUN_MAKETEST_EQ_1` 按事实计得 2 并判 FAIL，列入需用户裁决。",
 "- start 门禁复核（记录提交 (i) 之前，`GATE_R9M3A_start_RECHECK`）：33 PASS / 10 FAIL。10 条 FAIL 全部是本轮合法改动造成的“轮次起点不变量”不再成立（STATE 字节数与 sha、RULINGS 字节数/sha/最大 U 号、ERRATA_9 字节数/sha/最后一条 E 号、M1R4 清单 sha 等），不是新缺陷；该项设计缺陷（复核无法在改动后通过）登记在需用户裁决。",
]
NOTE_OLD = "> 说明：本轮完成 R9 M3a（勘误收口 + make test 回归 + E2E 装置与预注册），不宣布阶段完成；预注册与不可达点族的处理等待用户审核后进入 M3b。"
NOTE_NEW = "> 说明：本轮完成 R9 M3a（勘误收口 + make test 回归 NO_NEW_FAILURE/175 单元 + E2E 装置与预注册 18 点，未运行 E2E 点），不宣布阶段完成；预注册、不可达点族与 end 门禁 FAIL 项的处置等待用户审核后进入 M3b。"
ROW_OLD = "| S4R9 M3a | J-1..J-6 属实（E9-35..E9-44，U328–U333）；make test 导出树回归；E2E 装置+预注册 18 点（不运行） | `P05_S4R9_M3a_REPORT.md` |"
ROW_NEW = "| S4R9 M3a | J-1..J-6 属实（E9-35..E9-44、E9-45，U328–U333）；make test 四遍 rc=0、175 单元、**NO_NEW_FAILURE**；E2E 装置+预注册 18 点（不运行、冒烟 1 次） | `P05_S4R9_M3a_REPORT.md` |"


def main():
    bad = 0
    r = open(REP, "rb").read()
    rt = r.decode("utf-8")
    if rt.count(PH) != 1:
        print("HARD_STOP report placeholder count", rt.count(PH))
        return 2
    rt = rt.replace(PH, NL.join(APP))
    open(REP, "wb").write(rt.encode("utf-8"))
    print("report bytes %d -> %d sha %s" % (len(r), len(rt.encode("utf-8")), hashlib.sha256(rt.encode("utf-8")).hexdigest()))
    s = open(ST, "rb").read()
    st = s.decode("utf-8")
    for a, b in ((NOTE_OLD, NOTE_NEW), (ROW_OLD, ROW_NEW)):
        n = st.count(a)
        print("state anchor count", n)
        if n != 1:
            return 2
        st = st.replace(a, b)
    open(ST, "wb").write(st.encode("utf-8"))
    print("state bytes %d -> %d sha %s" % (len(s), len(st.encode("utf-8")), hashlib.sha256(st.encode("utf-8")).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
