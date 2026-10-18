#!/usr/bin/env python3
# append_rulings_r9m3c.py -- append U343..U350 to checkpoints/p05/registries/RULINGS.tsv (old file + new rows).
# The prefix sha256 is asserted before writing; the old bytes are never rewritten. New file (r9m3c).
import os, sys, hashlib
REPO = os.getcwd()
P = os.path.join(REPO, "checkpoints/p05/registries/RULINGS.tsv")
EXPECTED_SHA = "4bcebe609f7c280d1083f69fd117719ffa98fa8dc7793130e0168f0e36c9631a"
EXPECTED_BYTES = 139934
TAB = chr(9)
NL = chr(10)
ROWS = [
 ("U343", "P05-S4 R9 M3c 任务书 §2",
  "PREREG_E2E_R9M3B.tsv 的 42 点布点、nth（CF/FFT/KT/EXP=1，JONES/NV/VL=3）、容差 1e-12、Lua 批处理 exp_retry_same=NOT_APPLICABLE_PROCESS_EXIT 与 REPL 观测口径，认可。",
  "P05-S4 R9 M3c 任务书 §2", "生效"),
 ("U344", "P05-S4 R9 M3c 任务书 §2",
  "U340 的 SEAM_ONLY 处理（LinearSolve A/B/B2/B2-buf、FMM 返回码族 E、分配 seam 家族 C、kottke_alloc:31 不出 E2E 点，以 M1/M2 覆盖行代替），接受。",
  "P05-S4 R9 M3c 任务书 §2", "生效"),
 ("U345", "P05-S4 R9 M3c 任务书 §2",
  "M3b 正式两遍判定（E2E_OK 25、CONTROL_OK 17，其余类别 0，新红点 0）接受，条件是 §4 S-B 的独立复核结果一致。若一致，RP-R6d-15（Python/Lua 可见性）带范围声明关闭。范围声明：F4 上经 Python 与 Lua 公共 API 可达的 7 个点族（CF/FFT/KT/JONES/NV/VL，EXP 仅 Lua），注入 s4malloc/plan/exec 三种方式，检查失败可见、同对象重试（Python 全族；Lua 仅 REPL 的 cf/fft/kt/vl 四族）、新对象/新进程重试等于参考值；seam-only 族由 M1/M2 覆盖；不含 B 树行为。",
  "P05-S4 R9 M3c 任务书 §2", "生效"),
 ("U346", "P05-S4 R9 M3c 任务书 §2",
  "M3b 表二的两处顺序偏差（S-C 先于 start 门禁；start_recheck 先于冻结清单）接受，只登记勘误。理由：预注册早于任何注入运行这一不变量，已由 end 门禁检查成立。",
  "P05-S4 R9 M3c 任务书 §2", "生效"),
 ("U347", "P05-S4 R9 M3c 任务书 §2",
  "M3b end 门禁 EVIDENCE_SHA256SUMS_OK 的 FAIL 判为检查器缺陷（gate_check_r9m3b_v3.py 写死了 v1 脚本名），接受；由本轮 S-B 的只读复验代替（m3b 证据清单全部 OK）。M3b 门禁文件不修改。",
  "P05-S4 R9 M3c 任务书 §2", "生效"),
 ("U348", "P05-S4 R9 M3c 任务书 §2",
  "M3b 报告附录 A 中“4 遍 × 2 段对账 存在 FAIL”一句是 closeout 脚本的列下标错误（取了 skipped 期望列而不是 ok 列），与事实相反。事实以 MAKETEST_VERDICT_R9M3B.tsv 的 8/8 OK 为准；报告不改，只登记勘误。",
  "P05-S4 R9 M3c 任务书 §2", "生效"),
 ("U349", "P05-S4 R9 M3c 任务书 §2",
  "不另立 M3a 门禁更正件；U337 加 E9-57 已足够。",
  "P05-S4 R9 M3c 任务书 §2", "生效"),
 ("U350", "P05-S4 R9 M3c 任务书 §2",
  "RP-R8-M2c-1/1b 已由 U304 关闭。旧台账不改，在本轮最终红点台账中按 U304 记为已关闭。",
  "P05-S4 R9 M3c 任务书 §2", "生效"),
]


def main():
    old = open(P, "rb").read()
    a = hashlib.sha256(old).hexdigest()
    if a != EXPECTED_SHA:
        print("HARD_STOP prefix sha %s != %s" % (a, EXPECTED_SHA))
        return 2
    if len(old) != EXPECTED_BYTES:
        print("HARD_STOP prefix bytes %d != %d" % (len(old), EXPECTED_BYTES))
        return 2
    if not old.endswith(NL.encode("utf-8")):
        old += NL.encode("utf-8")
    add = "".join(TAB.join(r) + NL for r in ROWS)
    new = old + add.encode("utf-8")
    if new[:len(old)] != old:
        print("HARD_STOP prefix changed")
        return 2
    open(P, "wb").write(new)
    print("RULINGS bytes %d -> %d sha %s" % (len(old), len(new), hashlib.sha256(new).hexdigest()))
    print("APPENDED " + ",".join(r[0] for r in ROWS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
