#!/usr/bin/env python3
# s5r5_errata.py -- P05-S5 R5 errata: snapshot the R4-final ERRATA_S5.txt into registries/s5r5/r4_final/
# and append ES5-15 / ES5-16 (task brief section 2; pure append, prefix sha asserted unchanged).
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
ERR = os.path.join(P05, "registries/s5r2/ERRATA_S5.txt")
SNAPDIR = os.path.join(P05, "registries/s5r5/r4_final")
SNAP = os.path.join(SNAPDIR, "ERRATA_S5_R4FINAL.txt")
TAB = chr(9)
NL = chr(10)

EXP_BYTES = 13848
EXP_SHA = "8aec8fd5e21c9fd2d3e5f3189d921eebe2fdde23524c5ea41087137fd641ba4f"

BLOCKS = [
    ("ES5-15", [
        "ES5-15",
        "- 事实：gate_check_s5r4.py:997 把 \"STAGING_MODE\"+TAB+\"yes\" 与记录格式 RECORD\\tSTAGING_MODE\\tvalue=yes 比较。"
        "试跑走的是第 992–994 行的“自身输出”分支，覆盖不到第 995–997 行。",
        "- 影响：S5R4 正式门禁 FAILS=1、CHECK_CRASHED=0、FINAL_STATUS=INCOMPLETE（失败项 SHAKEDOWN_USED_STAGING_ROOTS）；"
        "被检数据（试跑门禁输出 RECORD\\tSTAGING_MODE\\tvalue=yes、FAILS=0）正确，138 项 PASS 不受影响。",
        "- 证据：checkpoints/p05/evidence/p05-s5r4/gate/GATE_S5R4_end.txt（sha 20bb6ad0…，1 FAIL）；"
        "checkpoints/p05/evidence/p05-s5r4/shakedown/gate/GATE_S5R4_end.txt 第 4 行 RECORD\\tSTAGING_MODE\\tvalue=yes；"
        "P05_S5R4_REPORT.md 附录 C。",
        "- 处理方式：U386、U388。R5 不改、不重跑 gate_check_s5r4.py；新脚本 s5r5_recheck_staging.py 在 R4 冻结数据上"
        "同时用修正逻辑与 R4 原有逻辑重判该行（只读）；R5 门禁不得出现“是否试跑/输出路径是否为自身”的分支，"
        "试跑由门禁之外的 s5r5_shakedown_verify.py 核验。",
    ]),
    ("ES5-16", [
        "ES5-16",
        "- 事实：S5R4 的 STATE 在门禁之前写入了门禁结果（“正式 end 门禁 FAILS=0”与开放问题表“收口范围完成（无可做）”）"
        "属于门禁前预投影；就绪审计只核对 STATE 字节和 sha，没有核对内容是否属实，导致 GAP=0 失真（STATE 内容与门禁实际结果不符）。",
        "- 影响：STATE 与门禁后附录 C 的 FINAL_STATUS=INCOMPLETE 不一致；签收范围判断不能依据该 STATE 行。",
        "- 证据：checkpoints/p05/STATE.md（R4 版本，sha 1a962c77…）第 2 节 S5R4 行与第 3 节“S5 签收”行；"
        "P05_S5R4_REPORT.md 附录 C 事件 C2。",
        "- 处理方式：U387、U389、U390。R5 起门禁前写的 STATE/草稿/报告正文不得写任何门禁结果，只能写“见附录 C”；"
        "就绪审计必须用正则断言三处不含门禁结果字样，并核对 STATE 的 S5R4 行与 S5R4 附录 C 的 FINAL_STATUS=INCOMPLETE 一致。",
    ]),
]


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def main():
    before = open(ERR, "rb").read()
    if len(before) != EXP_BYTES or sha_b(before) != EXP_SHA:
        print("HARD_STOP ERRATA start snapshot mismatch bytes=%d sha=%s" % (len(before), sha_b(before)))
        return 2
    last = [l for l in before.decode("utf-8").splitlines() if l.startswith("ES5-")]
    if not last or last[-1] != "ES5-14":
        print("HARD_STOP ERRATA last entry is not ES5-14: %s" % (last[-1] if last else "none"))
        return 2
    os.makedirs(SNAPDIR, exist_ok=True)
    with open(SNAP, "wb") as fh:
        fh.write(before)
    if open(SNAP, "rb").read() != before or sha_b(open(SNAP, "rb").read()) != EXP_SHA:
        print("HARD_STOP snapshot copy mismatch")
        return 2
    payload = []
    for (_uid, block) in BLOCKS:
        payload.extend(block)
    text = NL.join(payload) + NL
    with open(ERR, "ab") as fh:
        fh.write(text.encode("utf-8"))
    after = open(ERR, "rb").read()
    if after[:EXP_BYTES] != before or sha_b(after[:EXP_BYTES]) != EXP_SHA:
        print("HARD_STOP ERRATA prefix changed")
        return 2
    ids = [l for l in after.decode("utf-8").splitlines() if l.startswith("ES5-")]
    ok = ids[-1] == "ES5-16" and ids.count("ES5-15") == 1 and ids.count("ES5-16") == 1
    body = ["# ERRATA_APPEND_S5R5.tsv -- P05-S5 R5 pure append (ES5-15, ES5-16)",
            "# before_bytes=%d before_sha256=%s" % (EXP_BYTES, EXP_SHA),
            "# after_bytes=%d after_sha256=%s" % (len(after), sha_b(after)),
            "# r4_final_snapshot=%s snapshot_sha256=%s" % (os.path.relpath(SNAP, REPO), sha_b(open(SNAP, "rb").read())),
            "# last_entry=%s entries_appended=2" % ids[-1],
            "id" + TAB + "appended"]
    for (uid, _b) in BLOCKS:
        body.append(uid + TAB + "yes")
    out = os.path.join(EV, "ERRATA_APPEND_S5R5.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("ERRATA after_bytes=%d sha=%s last=%s ok=%s" % (len(after), sha_b(after), ids[-1], ok))
    print("SNAPSHOT " + os.path.relpath(SNAP, REPO) + " sha=" + sha_b(open(SNAP, "rb").read()))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
