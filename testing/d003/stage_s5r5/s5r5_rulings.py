#!/usr/bin/env python3
# s5r5_rulings.py -- P05-S5 R5 ruling register append (task brief section 1; pure append).
# Appends U386..U390 as exactly 5 tab fields per row, asserts the prefix is byte-identical to the R5 start
# snapshot (no rewriting), and records the appended rows and the before/after shas in the round evidence.
import os, sys, re, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
RUL = os.path.join(P05, "registries/RULINGS.tsv")
TAB = chr(9)
NL = chr(10)

EXP_BYTES = 154825
EXP_SHA = "24e65c3223c94deafbfd58d74e613aec2e5749159b39dfe93014ee32dc86a2d3"
EXP_MAX = 385

ROUND = "P05-S5 R5 任务书 §1（用户已批准）"
REF = "P05-S5 R5 任务书 §1"
STATUS = "生效"
ROWS = [
    ("U386",
     "S5R4 正式 end 门禁的唯一 FAIL（SHAKEDOWN_USED_STAGING_ROOTS）认定为检查器字符串缺陷。R5 不改、不重跑 "
     "gate_check_s5r4.py，也不重跑 S5R4 的 139 项正式门禁；改用新脚本 testing/d003/stage_s5r5/s5r5_recheck_staging.py，"
     "在 R4 冻结数据上同时用修正后的逻辑和 R4 原有逻辑重判该项（只读）。另外 138 项以 S5R4 正式门禁原文 PASS 为准"
     "（记录门禁文件 sha）。"),
    ("U387",
     "S5R4 的 STATE 行“正式 end 门禁 FAILS=0”和开放问题表中的“收口范围完成（无可做）”属于门禁前预投影，R5 予以更正。"
     "R5 起，门禁前写的 STATE、草稿、报告正文只能写“见 P05_S5R5_REPORT.md 附录 C”，不得写任何门禁结果。"),
    ("U388",
     "R5 门禁 gate_check_s5r5.py 中不得出现任何依据“是否试跑”或“输出路径是否为自身”的分支。试跑和正式运行只差根路径参数，"
     "检查逻辑逐字相同；门禁不读取任何门禁输出文件（包括试跑门禁输出）。试跑门禁输出由门禁之外的 "
     "s5r5_shakedown_verify.py 核验，并且必须在提交 (i) 之前完成。"),
    ("U389",
     "就绪审计 s5r5_readiness.py 除了记录 STATE 字节与 sha，还必须断言 STATE、草稿 v3、报告正文中不含门禁结果字样"
     "（正则 FAILS=\\d+|门禁.*(通过|PASS)|无可做 出现即 GAP），并核对 STATE 中 S5R4 行与 S5R4 附录 C 的 "
     "FINAL_STATUS=INCOMPLETE 一致。"),
    ("U390",
     "新写 P05_S5_SIGNOFF_DRAFT_v3.md（v1、v2 保留为历史，不改），仍标“未签收”。门禁结果只写"
     "“见 P05_S5R5_REPORT.md 附录 C；若附录 C 中 FINAL_STATUS≠COMPLETE，本草稿无效”。"),
]


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def main():
    before = open(RUL, "rb").read()
    if len(before) != EXP_BYTES or sha_b(before) != EXP_SHA:
        print("HARD_STOP RULINGS start snapshot mismatch bytes=%d sha=%s" % (len(before), sha_b(before)))
        return 2
    txt = before.decode("utf-8")
    maxu = 0
    for line in txt.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        f = line.split(TAB)
        if f and re.match(r"^U(\d+)$", f[0]):
            maxu = max(maxu, int(f[0][1:]))
    if maxu != EXP_MAX:
        print("HARD_STOP RULINGS max U is %d, expected %d" % (maxu, EXP_MAX))
        return 2
    if not txt.endswith(NL):
        print("HARD_STOP RULINGS does not end with a newline")
        return 2
    lines = []
    for (uid, summary) in ROWS:
        fields = [uid, ROUND, summary, REF, STATUS]
        if len(fields) != 5 or any(TAB in x or NL in x for x in fields):
            print("HARD_STOP row %s is not a clean 5-field row" % uid)
            return 2
        lines.append(TAB.join(fields))
    payload = (NL.join(lines) + NL).encode("utf-8")
    with open(RUL, "ab") as fh:
        fh.write(payload)
    after = open(RUL, "rb").read()
    if after[:EXP_BYTES] != before:
        print("HARD_STOP prefix changed")
        return 2
    if sha_b(after[:EXP_BYTES]) != EXP_SHA:
        print("HARD_STOP prefix sha changed")
        return 2
    atxt = after.decode("utf-8")
    bad = []
    for line in atxt.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        if len(line.split(TAB)) != 5:
            bad.append(line[:40])
    ids = [l.split(TAB)[0] for l in atxt.splitlines() if not l.startswith("#") and l.strip()]
    once = [u for (u, _) in ROWS if ids.count(u) != 1]
    maxu2 = max(int(i[1:]) for i in ids if re.match(r"^U\d+$", i))
    ok = (not bad) and (not once) and maxu2 == 390
    body = ["# RULINGS_APPEND_S5R5.tsv -- P05-S5 R5 pure append (U386..U390)",
            "# before_bytes=%d before_sha256=%s" % (EXP_BYTES, EXP_SHA),
            "# after_bytes=%d after_sha256=%s" % (len(after), sha_b(after)),
            "# rows_appended=%d max_u=U%d five_fields_ok=%s once_each=%s" % (
                len(ROWS), maxu2, "yes" if not bad else "no", "yes" if not once else "no"),
            "id" + TAB + "given_in_round" + TAB + "record_file_and_entry" + TAB + "status"]
    for (uid, summary) in ROWS:
        body.append(TAB.join([uid, ROUND, REF, STATUS]))
    out = os.path.join(EV, "RULINGS_APPEND_S5R5.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("RULINGS after_bytes=%d sha=%s max=U%d rows_ok=%s" % (len(after), sha_b(after), maxu2, ok))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
