#!/usr/bin/env python3
# s5r5_events.py -- write the two event tables of the round (task brief section 5) into EVENTS_S5R5.tsv.
# Table 1 = out-of-repository write attempts (command named a target outside $REPO); table 2 = tool/script
# events (framework spills, heredoc residue, script defects found and fixed before the freeze).
import os, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r5")
TAB = chr(9)
NL = chr(10)

# table 1 rows: round, command, target, persisted
TABLE1 = [
    ("s5r5", "awk -F'\\t' ... | tee /dev/stderr | wc -l",
     "tee 的目标 /dev/stderr（仓库外设备路径，非 $REPO 下）", "未落盘（tee 报 No such device or address；同一管道的 wc 仍输出 139）"),
]
# table 2 rows: event, handling/effect
TABLE2 = [
    ("s5r5_checker_sweep.py 首跑 HARD_STOP：AST 只收集到 131/139 个断言（循环生成的 8 个检查名未展开）",
     "按 for 元组展开 % 格式的检查名，收集 139；复查无重复名"),
    ("s5r5_checker_sweep.py 二跑 HARD_STOP KeyError EVIDENCE_SUMS_COVERS_ALL：其 not in 出现在 os.walk 目录剪枝，被归为否定匹配但无重算器",
     "补该断言在 R4 冻结数据上的重算（941 个文件逐一对照清单，结果 PASS_941_FILES），证明非空洞"),
    ("s5r5_checker_sweep.py 重跑时 VACUOUS=2：工作区 STATE 已是 R5 版本，否定匹配重算读不到 R4 冻结 STATE",
     "改为从冻结提交 1600ca1 用只读 git show 读 R4 STATE（sha 与 READINESS_S5R4 记录一致）；VACUOUS=0"),
    ("s5r5_recheck_staging.py formal 首跑 rc=1：输入文件不在 S5R4 SHA256SUMS.txt 中（清单声明 shakedown/ 被排除）",
     "改为两条诚实的清单对照：排除声明命中 + 清单覆盖的 SHAKEDOWN_ITERATIONS_S5R4.txt 条目 sha 匹配；rc=0"),
    ("s5r5_readiness.py 首跑 GAP=1：读 S5R4 报告的 FINAL_STATUS 时取到附录 B 的 PENDING_GATE（附录 C 的 INCOMPLETE 在其后）",
     "改为取最后一次出现（=附录 C 的 INCOMPLETE），GAP=0"),
    ("s5r5_gate_posctrl.py 首跑 32/36：4 个 clean 失败（MODIFIED 期望写成固定行数；NO_PYCACHE 把 2026-10-11 的历史 __pycache__ 计入；REGISTRY_EXPECTED 表头被当数据行；POSCTRL 自指 clean 的 --ev-root 覆盖被默认值优先）",
     "逐项修正：期望改为与行数无关；NO_PYCACHE 只计本轮开始后新建的 __pycache__（U388 口径）；解析跳过 rel_path 表头；clean 侧改用独立 ev 根"),
    ("s5r5_gate_posctrl.py 二跑 34/36：REGISTRY_EXPECTED 篡改误改表头；FROZEN 列表在 gate 脚本修改后未重建（stale）",
     "篡改只改数据行；重建 FROZEN 后 36/36"),
    ("gate_check_s5r5.py HEAD_R5_I_COMMITS_ONLY 期望原写为 ok_0_commits；提交 (i) 后会变成 ok_1_commits 而误 FAIL（若只在试跑验证就发现不了，属 ES5-15 同类覆盖缺陷）",
     "期望改为与提交数无关的 ok（只要求基线之后的提交主题都含 P05-S5 R5 (i)）；并在逐检查阳性对照里用 clean 夹具模拟提交 (i) 之后的分支"),
    ("s5r5_shakedown.py 首跑即 36/36，无 FAIL 需要归因",
     "试跑门禁输出与 SHAKEDOWN_REHEARSAL.txt 落盘，由门禁之外的 s5r5_shakedown_verify.py 核验：36/36 项检查均出现且成立，失败数=0，检查器崩溃数=0"),
]
# appended by later regenerations (kept data-driven so the report body can embed the latest tables)
EXTRA1 = []
EXTRA2 = []


def main():
    for (rnd, cmd, tgt, pers) in TABLE1 + EXTRA1:
        for x in (rnd, cmd, tgt, pers):
            assert TAB not in x and NL not in x
    for (evt, hnd) in TABLE2 + EXTRA2:
        for x in (evt, hnd):
            assert TAB not in x and NL not in x
    rows = ["# EVENTS_S5R5.tsv -- two event tables of P05-S5 R5",
            TAB.join(["table", "idx", "col1", "col2", "col3", "col4"])]
    for i, (rnd, cmd, tgt, pers) in enumerate(TABLE1, 1):
        rows.append(TAB.join(["1", str(i), rnd, cmd, tgt, pers]))
    for i, (evt, hnd) in enumerate(TABLE2, 1):
        rows.append(TAB.join(["2", str(i), evt, hnd, "", ""]))
    out = os.path.join(EV, "EVENTS_S5R5.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("EVENTS table1=%d table2=%d" % (len(TABLE1), len(TABLE2)))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
