#!/usr/bin/env python3
# append_rulings_r9m3a.py -- append user rulings U328..U333 to RULINGS.tsv. New file (r9m3a).
# usage: python3 -I -B testing/d003/stage_s4r9/append_rulings_r9m3a.py checkpoints/p05/registries/RULINGS.tsv
# Guards (hard stop on mismatch): the current file must equal the start-gate byte length and sha256,
# the highest U id must be U327, and none of U328..U333 may already exist.
import os, sys, hashlib

EXPECT_BYTES = 134794
EXPECT_SHA = "8b3d0e31fff12ddd84827e2f508f458f73c8574681feb2100aa684f9a3428ae2"
EXPECT_MAX_U = 327
NEW_FIRST_U = 328
SRC = "P05-S4 R9 M3a 任务书 §3"
STATUS = "生效"

ROWS = [
    ("U328", "r9m1r4 的独立复算（RECERT_R9M1R3.tsv 中 VERDICT/EQUIV/SUMMARY/FORMAL_FACTS 各项）连同规划者复核（J-7），作为 M1 有效结果（r9m1r3 的 VERDICT、F3_F4_EQUIV、M1_SUMMARY）的核证。M1 不再开修正轮。J-1..J-6 按事实登记勘误。"),
    ("U329", "r9m1r4 的阳性对照（POSCTRL_RECERT_R9M1R4.txt）不作为有效对照。本轮 S-B 用落盘篡改副本对 recert 的复算逻辑重做阳性对照（POSCTRL_R9M3A.txt），作为替代。"),
    ("U330", "r9m1r3 门禁补做断言以本轮 S-B 产出的 BACKFILL_FULL_R9M1R3.tsv 为准（覆盖 FROZEN_SCRIPTS_R9M1R3 的全部 14 个脚本）。events=2、report_check=3 按事实记为 FAIL，与 E9-32 对应，不另作处理。"),
    ("U331", "J-4 中 UNLOGGED_WRITES_R9M1R3.tsv 不再改写。本轮输出更正表 UNLOGGED_CORR_R9M3A.tsv，逐行说明两份版本的差异，并按 m1r3/m1r4 日志重新判定那两行的归属。"),
    ("U332", "r9m1r4 附录 A.3 的 4 项：项一接受（报告中没有询问用户确认的语句，属检查器误匹配）；项二接受（门禁设计缺陷，finalize 在门禁后单次执行）；项三不按原文接受，以 J-5 的事实为准（EVENTS 覆盖到第 56 行）；项四由本轮把 STATE 压缩到 <= 8192 字节。"),
    ("U333", "M3 范围：a) make test，在导出树上 B 与 F4 各两遍，判据为 F4 的失败测试集合包含于 B 的失败测试集合且 F4 两遍一致；b) Python/Lua 公共 API E2E（正常 -> 注入失败 -> 可见报错 -> 同一对象重试恢复 / 全新对象重试恢复），M3a 只做设计、构建与预注册，M3b 运行；c) U38 已由 U90 裁决，M3 只核对台账，不重新分类；d) E2E 中 API 层没有报错（SILENT_SWALLOW）或重试后结果不一致，登记为新红点按 U4 处理，本阶段不改 S4/。"),
]


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/p05/registries/RULINGS.tsv"
    old = open(path, "rb").read()
    if len(old) != EXPECT_BYTES:
        print("HARD_STOP: byte length %d != expected %d" % (len(old), EXPECT_BYTES))
        return 2
    if sha256_bytes(old) != EXPECT_SHA:
        print("HARD_STOP: sha256 %s != expected %s" % (sha256_bytes(old), EXPECT_SHA))
        return 2
    text = old.decode("utf-8")
    nums = []
    for line in text.splitlines():
        f = line.split("\t")[0]
        if f.startswith("U") and f[1:].isdigit():
            nums.append(int(f[1:]))
    if not nums or max(nums) != EXPECT_MAX_U:
        print("HARD_STOP: max U id %s != expected U%d" % (nums and ("U%d" % max(nums)) or "none", EXPECT_MAX_U))
        return 2
    existing = set("U%d" % n for n in nums)
    for uid, _ in ROWS:
        if uid in existing:
            print("HARD_STOP: %s already exists" % uid)
            return 2
    if not text.endswith("\n"):
        text += "\n"
    add = []
    for uid, body in ROWS:
        assert "\t" not in uid and "\t" not in body and "\n" not in body
        add.append("%s\t%s\t%s\t%s\t%s\n" % (uid, SRC, body, SRC, STATUS))
    new_text = text + "".join(add)
    new_b = new_text.encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(new_b)
    print("APPENDED %d rulings (%s..%s)" % (len(ROWS), ROWS[0][0], ROWS[-1][0]))
    print("BEFORE bytes=%d sha=%s" % (len(old), sha256_bytes(old)))
    print("AFTER  bytes=%d sha=%s" % (len(new_b), sha256_bytes(new_b)))
    print("PREFIX_PRESERVED=%s" % (new_b.startswith(old),))
    return 0


if __name__ == "__main__":
    sys.exit(main())
