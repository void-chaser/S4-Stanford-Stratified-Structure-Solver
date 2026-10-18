#!/usr/bin/env python3
# append_errata_r9m3a_v2.py -- append E9-45 (this round wrote several files outside the safe_run wrapper).
import sys, hashlib
EXPECT_SHA = "8d54e8af1a3b8724ac926b5fd7e2085e3c3f3eab0faa807c3539346ee84165ea"
EXPECT_BYTES = 38065
ENTRY = [
 "",
 "E9-45",
 "- 事实：r9m3a 本轮多条含写入的命令用外层 shell 的 && 串联，只有第一条命令真正经过 testing/d003/safe_run.sh，其余 python3 -c 写入落在日志之外；end 门禁的 UNLOGGED_SELF 检查因此检出未记录写入（写入目标都在允许范围内，没有越界写入）。",
 "- 证据文件与行号：checkpoints/p05/evidence/p05-s4r9/m3a/safe_run.log；checkpoints/p05/evidence/p05-s4r9/m3a/GATE_R9M3A_end.txt 的 UNLOGGED_SELF 行；本轮报告事件表二。",
 "- 影响范围：本轮部分文件的写入缺少 safe_run 日志覆盖，削弱了写入可审计性（与 E9-33 同类，但未涉及越界路径，也不是编辑器工具直写）。",
 "- 处理方式：照实登记，不追改历史日志、不补写日志；报告表二与需用户裁决逐条列出，end 门禁该项按 FAIL 记录。",
]
NL = chr(10)


def main():
    p = sys.argv[1] if len(sys.argv) > 1 else "checkpoints/p05/registries/s4r9/ERRATA_9.txt"
    b = open(p, "rb").read()
    if len(b) != EXPECT_BYTES or hashlib.sha256(b).hexdigest() != EXPECT_SHA:
        print("HARD_STOP: unexpected current file", len(b), hashlib.sha256(b).hexdigest())
        return 2
    text = b.decode("utf-8")
    if "E9-45" in text:
        print("HARD_STOP: E9-45 already present")
        return 2
    nb = (text + NL.join(ENTRY) + NL).encode("utf-8")
    open(p, "wb").write(nb)
    print("APPENDED E9-45; bytes %d -> %d; sha %s" % (len(b), len(nb), hashlib.sha256(nb).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
