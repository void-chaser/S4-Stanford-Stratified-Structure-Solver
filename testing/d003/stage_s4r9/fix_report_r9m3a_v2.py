#!/usr/bin/env python3
# fix_report_r9m3a_v2.py -- add the E9-45 disclosure (unlogged writes), the ERRATA count and the extra decision item.
import os, sys, hashlib
NL = chr(10)
P = "checkpoints/p05/P05_S4R9_M3a_REPORT.md"
A1 = "- 勘误追加：`append_errata_r9m3a.py`"
INS1 = "- 本轮自身勘误：E9-45 登记本轮多条含写入命令未经过 safe_run（详见 §9.2 第 9 行与 §10 第 4 项）。ERRATA_9 现 38912 字节，最后一条 E9-45，共 45 条（原 34 条 + 本轮 11 条）。" + NL + "- 勘误追加：`append_errata_r9m3a.py`
A2 = "| 8 | 框架落盘：无 `/tmp/dsh-spill-*` 记录 | — |"
INS2 = "| 8 | 框架落盘：无 `/tmp/dsh-spill-*` 记录 | — |" + NL + "| 9 | 多条含写入的命令用外层 `&&` 串联，只有第一条真正经过 `safe_run.sh`，其余 `python3 -c` 写入未被日志覆盖 | 登记 E9-45；不追改日志、不补写日志，end 门禁 `UNLOGGED_SELF` 按 FAIL 如实记录 |"
A3 = "3. **make test 判定**"
INS3 = "4. **本轮未记录写入的处置**：E9-45 所述情况（写入目标均在允许范围内、但部分命令未进入 `safe_run.log`）如何处置：接受登记，或要求后续轮次补做日志覆盖。逐文件清单见 end 门禁 `UNLOGGED_SELF` 行。" + NL + "3. **make test 判定**"


def main():
    rep = sys.argv[1] if len(sys.argv) > 1 else P
    b = open(rep, "rb").read()
    text = b.decode("utf-8")
    for a in (A1, A2, A3):
        if text.count(a) != 1:
            print("HARD_STOP: anchor count", text.count(a), repr(a[:50]))
            return 2
    text = text.replace(A1, INS1).replace(A2, INS2).replace(A3, INS3)
    nb = text.encode("utf-8")
    open(rep, "wb").write(nb)
    print("report %d -> %d bytes; sha %s" % (len(b), len(nb), hashlib.sha256(nb).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
