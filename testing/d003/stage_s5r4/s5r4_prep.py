#!/usr/bin/env python3
# s5r4_prep.py -- P05-S5 R4 task brief section 1: snapshot the R3-final ERRATA_S5.txt (8228 B, last
# entry ES5-8) and RULINGS.tsv before any append, then append U378-U385 (5 tab fields each) and
# ES5-9..ES5-14, asserting after every append that the pre-round prefix is byte-identical and that no
# original line changed.  This is the only copy of the R3-final ERRATA (used by s5r3_completion).
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r4")
TAB = chr(9)
NL = chr(10)
RUL = os.path.join(P05, "registries/RULINGS.tsv")
ERR = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def sha_f(p):
    return sha_b(open(p, "rb").read())


def rd(p):
    return open(p, encoding="utf-8").read()


def wr(p, t):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(t)


def start_records():
    d = {}
    for line in rd(os.path.join(EV, "GATE_S5R4_start.txt")).splitlines():
        if line.startswith("RECORD" + TAB):
            f = line.split(TAB)
            d[f[1]] = f[2].replace("value=", "")
    return d


RULINGS_ROWS = [
    ("U378", "P05-S5 R4 任务书 §1（用户本轮批准）",
     "S5R3 end 门禁的 5 项 FAIL（RULINGS_LINES_5_FIELDS、FROZEN_POST_I_CALL_COUNTS_MATCH、MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST、D016_VERDICT_ROWS_34、CALIB_DIFF_ZERO）认定为检查器/冻结标注缺陷，不是被检数据缺陷：分别由注释行未排除、FROZEN mode 标注与实际命令不符、git status 输出被整体 strip、表头行未排除、SUMMARY 行未排除造成。S5R3 的判定表、门禁原文与脚本一律不改；S5R4 用新脚本 gate_check_s5r4.py 修正检查逻辑，用同一数据（sha 不变）重判，并对每一项修正给出落盘变异阳性对照（篡改数据必须使该检查 FAIL）。",
     "P05-S5 R4 任务书 §1", "生效"),
    ("U379", "P05-S5 R4 任务书 §1（用户本轮批准）",
     "S5R3 独立重判 rejudge_s5r3.py 正式调用崩溃（read_tsv 把 D016_VERDICT_S5R3.tsv 的 SUMMARY 行当作数据行，KeyError），未产出 REJUDGE_S5R3.tsv，登记为 ES5-9。S5R4 新写 rejudge_s5r4.py：不 import judge_e2e_s5r3.py / d016_run_s5r3.py；读 S5R3 已有预注册与逐点 JSON（只读，不重跑注入）；跳过注释行、表头行与 SUMMARY 行，按列名读取；输出到 S5R4 证据。S5R4 对 checkpoints/p05/evidence/p05-s5r3/ 不做任何写入。",
     "P05-S5 R4 任务书 §1；ERRATA ES5-9", "生效"),
    ("U380", "P05-S5 R4 任务书 §1（用户本轮批准）",
     "registries/s5r3/ 小表清单不完整（10/26）是 chain copy 在缺 REJUDGE_S5R3.tsv 时 HARD_STOP 的级联结果。registries/s5r3/ 与其 SHA256SUMS.txt 保持历史、不重写；S5R4 在 registries/s5r4/s5r3_completion/ 补齐 S5R3 应交付但未入清单的 7 项（REJUDGE 为 S5R4 产出，其余 6 项从证据复制），并写 SHA256SUMS.txt 与 README；S5R4 报告给出 S5R3 26/26 覆盖对照（19 项已在 registries/s5r3/ 中，逐项 sha 与 p05-s5r3/SHA256SUMS.txt 一致）。ERRATA_S5.txt 的 S5R3 终版快照（8228 B，最后条目 ES5-8）必须在 S5R4 追加新条目之前复制并记录 sha。",
     "P05-S5 R4 任务书 §1；ERRATA ES5-12", "生效"),
    ("U381", "P05-S5 R4 任务书 §1（用户本轮批准）",
     "S5R4 起，试跑（shakedown）的 end 门禁必须达到 FAILS=0 且 CHECK_CRASHED=0（通过证据根/checkpoints 根/首个 POST_I 行覆盖在 staging 中完整演练，不碰正式路径）；不得再以'FAILS 均为试跑期必然'或仅 CHECK_CRASHED=0 作为通过条件。试跑中任何 FAIL 必须逐项归因（缺正式产物/检查器缺陷/链顺序/数据缺陷）；检查器缺陷必须在记录提交 (i) 之前修好，并用同一脚本 sha 重跑试跑至 FAILS=0。",
     "P05-S5 R4 任务书 §1；ERRATA ES5-14", "生效"),
    ("U382", "P05-S5 R4 任务书 §1（用户本轮批准）",
     "S5R4 的就绪审计必须在最终 STATE 写入之后运行；READINESS_S5R4.tsv 必须记录其读取的 STATE 字节数与 sha256；end 门禁逐项核对与最终 STATE 一致。READINESS GAP 必须为 0；否则 HARD_STOP，不得进入 end 门禁，也不得写'本轮完成'。",
     "P05-S5 R4 任务书 §1", "生效"),
    ("U383", "P05-S5 R4 任务书 §1（用户本轮批准）",
     "S5R4 不改 P05_S5_SIGNOFF_DRAFT.md（S5R3 版本保留为历史），新写 P05_S5_SIGNOFF_DRAFT_v2.md，仍标'未签收'。v2 不得包含任何未实测结论：'独立重判 DIFFS=0'只能在 S5R4 正式重判产出并实测为 0 之后写入，并注明行覆盖；若正式重判非零，v2 写实测值并说明本轮未完成。v2 须列 S5R4 的修正项（独立重判、门禁 5 项、就绪审计、registry 补齐）与已知限制。",
     "P05-S5 R4 任务书 §1；ERRATA ES5-13", "生效"),
    ("U384", "P05-S5 R4 任务书 §1（用户本轮批准）",
     "批准 S5R4 修改 testing/s4test/ISSUE_REGISTRY.md 与 PROJECT_ROADMAP.md 中由脚本列出的行（D016 行、P05 行及 D016 分条），内容为 ES5-9 与 S5R4 收口结果；只允许脚本列出的行变化（unified diff 断言）；这两个文件纳入本轮提交范围；不改 AGENTS.md。",
     "P05-S5 R4 任务书 §1", "生效"),
    ("U385", "P05-S5 R4 任务书 §1（用户本轮批准）",
     "S5R4 不重跑 D016/E2E/make test 的正式矩阵：S4/ 树=F4、判定器 sha 与构建配方未变，S5R3 的正式结果与证据 sha 保持有效；S5R4 只做独立重判与一致性收口。若独立重判发现记录判定本身有误，HARD_STOP 报告并等待用户裁决，不得自行重跑或修改判定。",
     "P05-S5 R4 任务书 §1", "生效"),
]

ERRATA_BLOCKS = [
    ("ES5-9", [
        "- 事实：rejudge_s5r3.py 正式调用崩溃：read_tsv() 把 D016_VERDICT_S5R3.tsv 的 SUMMARY 行当作数据行，按 point_id/verdict 取值时 KeyError 'point_id'，未产出 REJUDGE_S5R3.tsv。",
        "- 证据：checkpoints/p05/evidence/p05-s5r3/gate/GATE_S5R3_end.txt 的 FAIL REJUDGE_DIFFS_ZERO（actual=MISSING）；testing/d003/stage_s5r3/rejudge_s5r3.py 第 269-275 行的 read_tsv/verdict 读取路径；S5R3 报告附录 C #6。",
        "- 影响：S5R3 独立重判缺失；end 门禁 #6 FAIL，并级联 READINESS GAP=2 与 registries/s5r3 清单只剩 10 条（见 ES5-12）。S5R3 判定表本身未受影响。",
        "- 处理方式：U379。S5R4 新写 testing/d003/stage_s5r4/rejudge_s5r4.py：不 import 判定/比较器脚本；跳过以 # 开头的注释行、表头行与首字段为 SUMMARY 的行，按列名读取；读 S5R3 预注册与逐点 JSON（只读，不重跑注入）；输出到 S5R4 证据。S5R4 对 checkpoints/p05/evidence/p05-s5r3/ 零写入。",
    ]),
    ("ES5-10", [
        "- 事实：S5R3 end 门禁 5 项 FAIL 均为检查器/冻结标注缺陷，被检数据 sha 不变：",
        "  (1) RULINGS_LINES_5_FIELDS：检查器把以 # 开头的注释头行也当作 5 字段数据行统计（gate_check_s5r3.py:194-202 未跳过 # 行）；修正=跳过 # 行后每非空行正好 5 个 tab 字段。",
        "  (2) FROZEN_POST_I_CALL_COUNTS_MATCH：rejudge_s5r3.py 在 FROZEN_SCRIPTS_S5R3.tsv 中写 mode=formal（exp=1），正式调用命令不含 formal 词，门禁按 mode 子串计数得 0；修正=FROZEN mode 按列名读取、mode='-' 表示任意调用、正式命令必须含 formal 词；R4 清单写 mode=formal。",
        "  (3) MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST：gate_check_s5r3.py:267-277 把 git status 输出整体 strip() 后首行丢失前导状态空格，路径切片错位（actual=M PROJECT_ROADMAP.md）；修正=用 --porcelain=v1 原始输出、按 ln[:2] 状态 + ln[3:] 路径解析。",
        "  (4) D016_VERDICT_ROWS_34：gate_check_s5r3.py:307 未排除表头行（actual=35）；修正=排除 # 行、首字段 point_id 的表头行与 SUMMARY 行后计数 34，并断言 MATCH=33/RECORD=1。",
        "  (5) CALIB_DIFF_ZERO：gate_check_s5r3.py:341 把首列为 SUMMARY 的行也按 diff 列比较（actual=DIFFS=0=）；修正=排除 SUMMARY 行、其余每行 diff==SAME、SUMMARY 的 DIFFS=0 一致。",
        "- 证据：checkpoints/p05/evidence/p05-s5r3/gate/GATE_S5R3_end.txt 上述 5 条 FAIL；S5R3 报告附录 C #1-#5；数据 sha 以 p05-s5r3/SHA256SUMS.txt（sha ab40c174…）为准。",
        "- 处理方式：U378。S5R3 判定表、门禁原文与脚本不改；S5R4 用 gate_check_s5r4.py 修正检查逻辑，同一数据重新判定，并逐项配落盘变异阳性对照（POSCTRL_GATE_S5R4.txt）。",
    ]),
    ("ES5-11", [
        "- 事实：S5R3 报告正文笔误与占位：§4 写'判定行 35'（实际 D016_VERDICT 数据行=34：33 MATCH + 1 RECORD）；§5 写'DIFFS=?'占位（CALIB 实测 DIFFS=0；独立重判 R3 未产出）；§11 写'26 项与 26 条记录一致'但 registries/s5r3/SHA256SUMS.txt 实际只有 10 条。",
        "- 证据：checkpoints/p05/P05_S5R3_REPORT.md 第 28、36、95 行；S5R3 报告附录 C 已用最终状态声明更正清单不完整一项。",
        "- 影响：仅报告文字；不改判定/证据。",
        "- 处理方式：R3 报告不改（历史），S5R4 报告与本勘误记录；S5R4 报告的自检（REPORT_CHECK_S5R4）必须核对派生文字与源表一致。",
    ]),
    ("ES5-12", [
        "- 事实：S5R3 链顺序与输出路径缺陷：(a) chain copy 在缺 REJUDGE_S5R3.tsv 时 HARD_STOP，导致 registries/s5r3 只复制了 POSCTRL 三件（另加 start gate/FROZEN 等共 10 条），7 件正式交付未复制；(b) signoff 草稿被写到证据目录 $EV/ 而非 checkpoints/p05/，门禁后以 cp 补救；(c) 就绪审计在最终 STATE 之前运行，记录 STATE 的检查因此 GAP。",
        "- 证据：S5R3 报告附录 C #7/#8 与事件 11/12；registries/s5r3/SHA256SUMS.txt（sha c982514f…，10 条）。",
        "- 影响：登记清单不完整（10/26）；READINESS GAP=2。",
        "- 处理方式：U380 与 S5R4 链顺序修正：先产出重判再复制 registry；signoff 直接写 checkpoints/p05/；就绪审计在最终 STATE 之后运行并记录 STATE 字节/sha；S5R4 在 registries/s5r4/s5r3_completion/ 补齐 7 件并给出 26/26 覆盖对照。",
    ]),
    ("ES5-13", [
        "- 事实：S5R3 签收范围声明草稿 P05_S5_SIGNOFF_DRAFT.md §2 写'阳性对照：D016 5/5、E2E 19/19、make test 4/4；独立重判 DIFFS=0'，其中'独立重判 DIFFS=0'在草稿写就时并无实测产出（R3 正式重判崩溃，见 ES5-9）。",
        "- 证据：checkpoints/p05/P05_S5_SIGNOFF_DRAFT.md 第 339 行（由 S5R3 链生成）；S5R3 报告附录 C #6。",
        "- 影响：草稿含未实测结论；不得作为签收依据。",
        "- 处理方式：U383。S5R3 草稿保留为历史不改；S5R4 新写 P05_S5_SIGNOFF_DRAFT_v2.md，其中 DIFFS=0 只在 S5R4 正式重判实测之后写入并注明行覆盖。",
    ]),
    ("ES5-14", [
        "- 事实：S5R3 任务书把试跑（shakedown）end 门禁的通过条件定为'CHECK_CRASHED=0'，接受 40 项 FAIL 为'试跑期必然'；5 项检查器缺陷因此在冻结前未被发现，直到正式门禁才暴露。",
        "- 证据：S5R3 报告附录 A（COUNTS pass=38 fail=40 total=78、FAILS=40、以 CHECK_CRASHED=0 为通过条件）；S5R3 报告附录 C。",
        "- 影响：冻结后发现可修的检查器缺陷，冻结期不能修，只能照实登记为下一轮收口。",
        "- 处理方式：U381。S5R4 试跑必须 FAILS=0 且 CHECK_CRASHED=0，使用 staging 证据根/checkpoints 根/POST_I 起点行完整演练；任何 FAIL 逐项归因，检查器缺陷在提交 (i) 之前修好并用同一脚本 sha 重跑。",
    ]),
]


def main():
    sr = start_records()
    fails = []

    def chk(name, exp, act):
        ok = str(exp) == str(act)
        print(("PASS" if ok else "FAIL") + TAB + name + TAB + "expected=%s" % exp + TAB + "actual=%s" % act)
        if not ok:
            fails.append(name)

    # ---- snapshot R3-final ERRATA and RULINGS (the only copy; U380)
    rul_before = open(RUL, "rb").read()
    err_before = open(ERR, "rb").read()
    chk("RULINGS_PREFIX_BEFORE_BYTES", sr["RULINGS_BYTES"], len(rul_before))
    chk("RULINGS_PREFIX_BEFORE_SHA", sr["RULINGS_SHA256"], sha_b(rul_before))
    chk("ERRATA_PREFIX_BEFORE_BYTES", sr["ERRATA_S5_BYTES"], len(err_before))
    chk("ERRATA_PREFIX_BEFORE_SHA", sr["ERRATA_S5_SHA256"], sha_b(err_before))
    snapdir = os.path.join(EV, "r3_final")
    os.makedirs(snapdir, exist_ok=True)
    rul_snap = os.path.join(snapdir, "RULINGS_S5R3_FINAL.tsv")
    err_snap = os.path.join(snapdir, "ERRATA_S5_R3FINAL.txt")
    open(rul_snap, "wb").write(rul_before)
    open(err_snap, "wb").write(err_before)
    chk("RULINGS_SNAPSHOT_SHA", sha_b(rul_before), sha_f(rul_snap))
    chk("ERRATA_SNAPSHOT_SHA", sha_b(err_before), sha_f(err_snap))
    chk("ERRATA_SNAPSHOT_BYTES_8228", 8228, os.path.getsize(err_snap))
    snap_rows = ["row_kind" + TAB + "path" + TAB + "bytes" + TAB + "sha256" + TAB + "note",
                 TAB.join(["SNAPSHOT", "checkpoints/p05/evidence/p05-s5r4/r3_final/RULINGS_S5R3_FINAL.tsv",
                           str(len(rul_before)), sha_b(rul_before), "R3-final RULINGS before U378-U385 append"]),
                 TAB.join(["SNAPSHOT", "checkpoints/p05/evidence/p05-s5r4/r3_final/ERRATA_S5_R3FINAL.txt",
                           str(len(err_before)), sha_b(err_before), "R3-final ERRATA_S5 (last entry ES5-8) before ES5-9..14"])]
    wr(os.path.join(EV, "R3_FINAL_SNAPSHOT_S5R4.tsv"), NL.join(snap_rows) + NL)
    # ---- append rulings
    lines = []
    for (uid, given, summary, rec, status) in RULINGS_ROWS:
        row = TAB.join([uid, given, summary, rec, status])
        assert row.count(TAB) == 4, uid
        lines.append(row)
    add_rul = NL.join(lines) + NL
    if not rul_before.endswith(NL.encode("utf-8")):
        add_rul = NL + add_rul
    open(RUL, "ab").write(add_rul.encode("utf-8"))
    rul_after = open(RUL, "rb").read()
    chk("RULINGS_PREFIX_BYTE_IDENTICAL", sha_b(rul_before), sha_b(rul_after[:len(rul_before)]))
    chk("RULINGS_ADDED_BYTES", len(add_rul.encode("utf-8")), len(rul_after) - len(rul_before))
    # every appended line has exactly 5 fields and each new U id appears exactly once
    add_lines = add_rul.encode("utf-8").decode("utf-8").splitlines()
    chk("RULINGS_APPENDED_5_FIELDS", [5] * len(lines), [len(l.split(TAB)) for l in add_lines])
    ids = [l.split(TAB)[0] for l in rul_after.decode("utf-8").splitlines() if l.startswith("U")]
    chk("RULINGS_NEW_IDS_ONCE", 8, sum(1 for u in ("U378", "U379", "U380", "U381", "U382", "U383", "U384", "U385") if ids.count(u) == 1))
    mu = max(int(x[1:]) for x in ids if x[1:].isdigit())
    chk("RULINGS_MAX_U_385", "U385", "U%d" % mu)
    wr(os.path.join(EV, "RULINGS_APPEND_S5R4.tsv"),
       NL.join(["row_kind" + TAB + "id" + TAB + "given_in_round" + TAB + "bytes_before" + TAB + "bytes_after" + TAB + "sha_before" + TAB + "sha_after" + TAB + "prefix_ok"] +
               [TAB.join(["RULING", uid, given, str(len(rul_before)), str(len(rul_after)), sha_b(rul_before), sha_b(rul_after), "YES"]) for (uid, given, _s, _r, _t) in RULINGS_ROWS]) + NL)
    # ---- append errata
    blocks = []
    for bid, bl in ERRATA_BLOCKS:
        blocks.append(bid + NL + NL.join(bl))
    # the existing file separates ES5-n blocks with one blank line; match that convention
    add_err = NL + NL.join(blocks) + NL
    if not err_before.endswith(NL.encode("utf-8")):
        add_err = NL + add_err
    open(ERR, "ab").write(add_err.encode("utf-8"))
    err_after = open(ERR, "rb").read()
    chk("ERRATA_PREFIX_BYTE_IDENTICAL", sha_b(err_before), sha_b(err_after[:len(err_before)]))
    chk("ERRATA_ADDED_BYTES", len(add_err.encode("utf-8")), len(err_after) - len(err_before))
    last = [l for l in err_after.decode("utf-8").splitlines() if l.startswith("ES5-")]
    chk("ERRATA_LAST_ES5_14", "ES5-14", last[-1] if last else "none")
    want = ["ES5-%d" % i for i in range(9, 15)]
    chk("ERRATA_ES5_9_TO_14_PRESENT", want, [x for x in last if x in want])
    wr(os.path.join(EV, "ERRATA_APPEND_S5R4.tsv"),
       NL.join(["row_kind" + TAB + "entry" + TAB + "bytes_before" + TAB + "bytes_after" + TAB + "sha_before" + TAB + "sha_after" + TAB + "prefix_ok"] +
               [TAB.join(["ERRATA", bid, str(len(err_before)), str(len(err_after)), sha_b(err_before), sha_b(err_after), "YES"]) for (bid, _b) in ERRATA_BLOCKS]) + NL)
    print("COUNTS" + TAB + "fail=%d" % len(fails) + TAB + "total=23")
    print("PREP_FAILS=%d" % len(fails))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
