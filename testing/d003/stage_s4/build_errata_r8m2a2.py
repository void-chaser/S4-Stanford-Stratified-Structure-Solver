#!/usr/bin/env python3
# build_errata_r8m2a2.py -- P05-S4 R8 M2a2 section 3.2: text of the ERRATA_8.txt append (E8-91..E8-95).
# New file. Writes the append text to $EV/ERRATA_APPEND_R8_M2a2.txt and appends it to
# checkpoints/p05/registries/s4r8/ERRATA_8.txt ONLY if the existing file is still at the start-gate state
# (67104 bytes, sha256 e559b011...).  Append only (U17): no existing entry is changed.  Refuses if the append file exists.
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
ERRATA = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "ERRATA_8.txt")
APPEND = os.path.join(EV, "ERRATA_APPEND_R8_M2a2.txt")
START_BYTES = 67104
START_SHA = "e559b0110a26f3f039b27a39c1a08924eee4b43e394ddf799cee347706cf7520"

BLOCKS = [
    ("E8-91\tP05-S4 R8 M2a2 更正（只追加；依据 AGENTS.md 第 2、5 节与 P05-S4 R8 M2a2 任务书 §3.2）。原条目不改。\n"
     "        r8m2a 报告 §14 与最终回复称 `testing/d003/__pycache__` 是「本轮产生（推断）」，这一说法不成立（mtime 证据见 U237）。\n"),
    ("E8-92\tP05-S4 R8 M2a2 更正（只追加）。原条目不改。\n"
     "        `PREREG_M2_R8_M2a_R2.tsv` 的 I 列不可判定（U238），由 r8m2a2 预注册的 M2-01 行取代。原表不改。\n"),
    ("E8-93\tP05-S4 R8 M2a2 更正（只追加）。原条目不改。\n"
     "        r8m2a 有四处不一致：(a) 设计表 `M2_DESIGN_R8_M2a_R2.tsv` 中 M2-01 的可行性为 `FEASIBLE_NEW_APPARATUS`，报告 §5 写作 `FEASIBLE_EXISTING`；"
     "(b) STATE §4 写有 `SHA256SUMS_END.txt`，但该文件不存在；(c) 报告写 STATE 为 7854 字节，提交后实际为 7857 字节；"
     "(d) end 门禁文件没有复制进 registries。前三处由本轮 STATE 与报告更正；第 (d) 处由 r8m2a2 §4.0 补登（4 个文件与 `SHA256SUMS_END.txt`）。已提交的原文件不改。\n"),
    ("E8-94\tP05-S4 R8 M2a2 更正（只追加）。原条目不改。\n"
     "        r8m2a 把 M2-09 的 env 与 M2-06 的 ID 映射列为「需用户裁决」，但两者都可以从已提交的登记表查到（U239、U240）。\n"),
    ("E8-95\tP05-S4 R8 M2a2 更正（只追加）。原条目不改。\n"
     "        `6a4f003` 是在 end 门禁 FAILS=1 时做的提交（U236）。\n"),
]


def main():
    if os.path.exists(APPEND):
        print("build_errata_r8m2a2: REFUSED exists (U17): %s" % APPEND)
        return 2
    with open(ERRATA, "rb") as fh:
        cur = fh.read()
    if len(cur) != START_BYTES or hashlib.sha256(cur).hexdigest() != START_SHA:
        print("build_errata_r8m2a2: REFUSED ERRATA_8.txt is not at the start-gate state (bytes=%d)" % len(cur))
        return 2
    body = "\n" + "\n".join(b.rstrip("\n") for b in BLOCKS) + "\n"
    os.makedirs(EV, exist_ok=True)
    with open(APPEND, "x", encoding="utf-8") as fh:
        fh.write(body)
    with open(ERRATA, "ab") as fh:
        fh.write(body.encode("utf-8"))
    print("build_errata_r8m2a2: appended %d entries to ERRATA_8.txt; append file %s" % (len(BLOCKS), APPEND))
    return 0


if __name__ == "__main__":
    sys.exit(main())
