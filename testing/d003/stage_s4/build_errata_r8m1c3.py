#!/usr/bin/env python3
# build_errata_r8m1c3.py -- P05-S4 R8 M1c3 ERRATA builder (brief section 3.2). New file.
# Writes the text to append to checkpoints/p05/registries/s4r8/ERRATA_8.txt as $EV/ERRATA_APPEND_R8_M1c3.txt.
# Append-only: E8-81 corrects E8-79(e); E8-82 records the NO_OUTDIR case mismatch of r8m1c2 preflight.
# Called by append_errata_r8m1c3.sh.  Does not touch ERRATA_8.txt itself.
# Usage: python3 -I -B build_errata_r8m1c3.py
import os

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c3")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)
OUT = os.path.join(EV, "ERRATA_APPEND_R8_M1c3.txt")
if os.path.exists(OUT):
    raise SystemExit("REFUSED exists (U17): %s" % OUT)

TEXT = """
E8-81	P05-S4 R8 M1c3 更正（只追加；依据 AGENTS.md 第 2、5 节与 P05-S4 R8 M1c3 任务书 §3.2）。原条目不改。
        E8-79(e) 中写的脚本与表为 count_r7_f2_facts_r8m1c2.py / R7_F2_FACT_DIST_R8_M1c2.tsv；有效的是 count_r7_f2_facts_r8m1c2_R2.py / R7_F2_FACT_DIST_R8_M1c2_R2.tsv。旧版按整行比较两遍，因 gdb_log_sha256 列天然不同而报 False，属口径错误，不是数据不一致；数字 132/45/25/16/18 不变。

E8-82	P05-S4 R8 M1c3 记录（只追加；依据 AGENTS.md 第 5 节与 P05-S4 R8 M1c3 任务书 §3.2、U219）。
        r8m1c2 预检的 NO_OUTDIR 检查使用小写名 m1c_f2、m1c_f3，与运行脚本实际生成的 m1c_F2、m1c_F3 不对应。运行前 m1c_F2 确实不存在（依据：safe_run.log 的时间顺序与运行脚本的 U17 拒绝逻辑），结果不受影响。自 r8m1c3 起，预检检查实际名（见 U219）。
"""

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(TEXT)
print("BUILT_ERRATA_BYTES=%d -> %s" % (os.path.getsize(OUT), OUT))
