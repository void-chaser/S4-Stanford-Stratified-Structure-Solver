#!/usr/bin/env python3
# append_rulings_r9m3b.py -- append U334..U342 to RULINGS.tsv in the "old file + new lines" form (5 columns),
# asserting the opening prefix hash first. New file (r9m3b).
# usage: python3 -I -B testing/d003/stage_s4r9/append_rulings_r9m3b.py checkpoints/p05/registries/RULINGS.tsv
import os, sys, hashlib

REPO = os.getcwd()
TAB = chr(9)
NL = chr(10)
PRE_BYTES = 136951
PRE_SHA = "579b73c9d8952c3465d7402231b167d09d5eb087dd5519d6b0cefbffbf089951"
PRE_MAX_U = 333
SOURCE = "P05-S4 R9 M3b 任务书 §2"
ROWS = [
    ("U334", "M3a 中 run_maketest_r9m3a.py 被调用 2 次（第 1 次因会话 120 s 死线中断，现场在 maketest_interrupted/）。接受，以第 2 次调用的四遍结果为正式结果，不重跑。"),
    ("U335", "closeout_report_state_r9m3a.py 在 (i) 之后写入 testing/d003；UNLOGGED_SELF=2（registries SHA256SUMS 由脚本内部生成；e2e_lua 的裸写入见 E9-45）。二者都接受，作为登记处理。今后收尾脚本必须在 (i) 之前冻结；脚本内部生成、但不出现在命令行里的产物，由门禁按“脚本声明的输出清单”归属。"),
    ("U336", "M3a 的 report_check 有一项 NUM_STATE_BYTES FAIL：以 STATE 实际的 5191 字节为准，只登记勘误，不改报告。"),
    ("U337", "M3a 的 end 门禁有 6 条缺陷（脚本名没有随版本号更新、start 语义检查放进了 end 模式、反引号解析失败），start 复核有 10 条 FAIL（轮次起点不变量在合法改动后不再成立）。全部按检查器缺陷接受。本轮门禁必须修好这些问题：调用计数从 FROZEN 清单读取实际文件名；start 不变量只在 start 模式检查，end 模式改为“只追加文件的前缀 sha 等于开工值”；清单解析允许反引号。"),
    ("U338", "make test 不再运行。M3a 判定 NO_NEW_FAILURE 的成立，以本轮 S-B 只读重解析通过为条件。项目套件 test_lua_regression_negative.sh 写 /tmp/s4_lua_neg_XXXXXX（退出时删除）属于项目固有行为：补登记到本轮表一（标注轮次 r9m3a、项目套件固有、临时目录、开工与结束时 /tmp 快照均为 0），不算执行者违规。"),
    ("U339", "PREREG_E2E_R9M3A.tsv 不批准（理由见 §3 的 K-1/K-2/K-3/K-7）。原文件保持不动，由本轮的 PREREG_E2E_R9M3B.tsv 取代。"),
    ("U340", "E2E 点族按 §4 S-C1 执行。LinearSolve A/B/B2/B2-buf、FMM 返回码族 E、分配 seam 家族 C、kottke_alloc:31 这些只能通过 seam 补丁到达的族，不出 E2E 点。在 COVERAGE_E2E_R9M3B.tsv 中标为 SEAM_ONLY，并给出 M1/M2 中已有的覆盖行。"),
    ("U341", "Lua 的批处理模式出错即退出进程，exp_retry_same 记为 NOT_APPLICABLE_PROCESS_EXIT；同对象重试改用 Lua 交互（REPL）模式观测。容差为逐元素相对误差 ≤1e-12，批准。"),
    ("U342", "新预注册在任何注入运行之前写好并记录 sha 与 UTC 时间。之后可以先试跑、再冻结、再正式运行，不需要为预注册另停一轮等用户审核。"),
]


def main():
    if len(sys.argv) < 2:
        print("usage: append_rulings_r9m3b.py RULINGS.tsv")
        return 2
    path = sys.argv[1]
    data = open(path, "rb").read()
    if len(data) != PRE_BYTES or hashlib.sha256(data).hexdigest() != PRE_SHA:
        print("HARD_STOP prefix mismatch bytes=%d sha=%s" % (len(data), hashlib.sha256(data).hexdigest()))
        return 2
    txt = data.decode("utf-8")
    nums = []
    for line in txt.splitlines():
        f = line.split(TAB)[0]
        if f.startswith("U") and f[1:].isdigit():
            nums.append(int(f[1:]))
    if max(nums) != PRE_MAX_U:
        print("HARD_STOP max U %d != %d" % (max(nums), PRE_MAX_U))
        return 2
    if not txt.endswith(NL):
        txt += NL
    add = []
    for uid, text in ROWS:
        add.append(TAB.join([uid, SOURCE, text, SOURCE, "生效"]))
    new = txt + NL.join(add) + NL
    open(path, "wb").write(new.encode("utf-8"))
    nb = new.encode("utf-8")
    print("appended=%d bytes %d -> %d sha %s" % (len(ROWS), len(data), len(nb), hashlib.sha256(nb).hexdigest()))
    print("new_last_id=" + ROWS[-1][0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
