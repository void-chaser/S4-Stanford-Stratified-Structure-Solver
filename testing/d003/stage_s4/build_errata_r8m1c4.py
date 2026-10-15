#!/usr/bin/env python3
# build_errata_r8m1c4.py -- P05-S4 R8 M1c4 ERRATA builder (brief section 3.2, E8-83 to E8-87). New file.
# Writes the text to append to checkpoints/p05/registries/s4r8/ERRATA_8.txt as $EV/ERRATA_APPEND_R8_M1c4.txt.
# Append-only. Called by append_errata_r8m1c4.sh. It does not modify ERRATA_8.txt itself.
# Usage: python3 -I -B build_errata_r8m1c4.py
import os

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)
OUT = os.path.join(EV, "ERRATA_APPEND_R8_M1c4.txt")
if os.path.exists(OUT):
    raise SystemExit("REFUSED exists (U17): %s" % OUT)

TEXT = """
E8-83	P05-S4 R8 M1c4 更正（只追加；依据 AGENTS.md 第 2、5 节与 P05-S4 R8 M1c4 任务书 §3.2）。原条目不改。
        r8m1c3 报告 §0、§6、§6.3，STATE 关键数字表，以及 M1_SUMMARY_R8_M1c3_R2.tsv 中"NOT_RUN 0"有误，应为 NOT_RUN_AS_EXPECTED 6（G2c_control，见 U224）。REPORT_COUNT_CHECK_R8_M1c3.txt 的 ALL_MATCH 只说明报告与总表一致，不说明总表正确。

E8-84	P05-S4 R8 M1c4 更正（只追加）。原条目不改。
        r8m1c3 报告 §7 与 FIX_COVERAGE_M1_R8_M1c3_R2.tsv 的结论"806、415、RP-S3R4-1 NOT_COVERED_IN_M1 → M2"有误。正确结论见 U225 与本轮 FIX_COVERAGE_M1_R8_M1c4_R2.tsv：806、1729/RP-S3R4-1、415 在 M1 中按返回码与类别口径已覆盖（F3 行 MATCH），I1–I6 未测，不转 M2。

E8-85	P05-S4 R8 M1c4 更正（只追加）。原条目不改。
        r8m1c3 报告 §6.1 称第一版 M1_SUMMARY_R8_M1c3.tsv 覆盖规则过宽而作废。实际上它与 _R2 的 sha256 相同（5b7cee33…），只有 FIX_COVERAGE 两版内容不同。

E8-86	P05-S4 R8 M1c4 更正（只追加）。原条目不改。
        r8m1c3 registries 的文件名与证据不一致（见 U226），且 STATE 中引用的 VERDICT_M1C_R8_M1c3_AGG_R3.tsv、M1_SUMMARY_R8_M1c3_R2.tsv 在 registries 中不存在。名称对照见 REGISTRY_NAME_MAP_R8_M1c3.tsv（本轮 registries/s4r8/M1c/r8m1c4/）。

E8-87	P05-S4 R8 M1c4 更正（只追加）。原条目不改。
        r8m1c3 比较阳性对照的实现与正式比较脚本不同，且正式脚本的 OUT_PREFIX 参数未被使用（见 U227）。本轮阳性对照调用 compare_m1c_f3_r8m1c4.py，结果见 POSCTRL_M1C_R8_M1c4.txt。
"""

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write(TEXT)
print("BUILT_ERRATA_BYTES=%d -> %s" % (os.path.getsize(OUT), OUT))
