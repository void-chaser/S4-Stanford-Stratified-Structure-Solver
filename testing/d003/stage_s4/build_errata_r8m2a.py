#!/usr/bin/env python3
# build_errata_r8m2a.py -- P05-S4 R8 M2a section 3.2: text of the ERRATA_8.txt append (E8-88..E8-90).
# Writes the append text to $EV/ERRATA_APPEND_R8_M2a.txt and appends it to checkpoints/p05/registries/s4r8/ERRATA_8.txt
# ONLY if the existing file is still at the start-gate state (prefix check: 66346 bytes, sha256 1930bc2b...).
# Append only (U17): no existing entry is changed.  Refuses if the append file exists.
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
ERRATA = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "ERRATA_8.txt")
APPEND = os.path.join(EV, "ERRATA_APPEND_R8_M2a.txt")
START_BYTES = 66346
START_SHA = "1930bc2b389c1859fd8c4a7b9c103dc7e01495f26ca8c199bda1b73ee6768ba4"

BLOCKS = [
    ("E8-88\tP05-S4 R8 M2a 更正（只追加；依据 AGENTS.md 第 2、5 节与 P05-S4 R8 M2a 任务书 §3.2）。原条目不改。\n"
     "        M1a6 预注册中 ADD22-A-10 的 env（closed1d NG=1）与映射表第 10 行和来源 A_CTRL 第 2–7 行不一致（U231）。"
     "r8m1c4 `FIX_COVERAGE_M1_R8_M1c4_R2.tsv` 中的 MAP_ENV_MISMATCH 2 行如实反映了这一点。原条目与原表不改。\n"),
    ("E8-89\tP05-S4 R8 M2a 更正（只追加）。原条目不改。\n"
     "        r8m1c4 任务书 §4.5「27 个文件」应为「29 个文件（27 个由清单覆盖 + 2 份清单）」（U230）。\n"),
    ("E8-90\tP05-S4 R8 M2a 更正（只追加）。原条目不改。\n"
     "        r8m1c4 的判定阳性对照在 m1c3 证据目录的 tmp 下生成了 `verdict_override.tsv`（U233）。\n"),
]


def main():
    if os.path.exists(APPEND):
        print("build_errata_r8m2a: REFUSED exists (U17): %s" % APPEND)
        return 2
    with open(ERRATA, "rb") as fh:
        cur = fh.read()
    if len(cur) != START_BYTES or hashlib.sha256(cur).hexdigest() != START_SHA:
        print("build_errata_r8m2a: REFUSED ERRATA_8.txt is not at the start-gate state (bytes=%d)" % len(cur))
        return 2
    body = "\n" + "\n".join(b.rstrip("\n") for b in BLOCKS) + "\n"
    os.makedirs(EV, exist_ok=True)
    with open(APPEND, "x", encoding="utf-8") as fh:
        fh.write(body)
    with open(ERRATA, "ab") as fh:
        fh.write(body.encode("utf-8"))
    print("build_errata_r8m2a: appended %d entries to ERRATA_8.txt; append file %s" % (len(BLOCKS), APPEND))
    return 0


if __name__ == "__main__":
    sys.exit(main())
