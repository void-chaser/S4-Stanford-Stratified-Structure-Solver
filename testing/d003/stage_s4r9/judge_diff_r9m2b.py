#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# judge_diff_r9m2b.py -- Unified diff and analysis of R9 judge and runner tools vs R8 M2e (Step S-F).
import argparse, difflib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DEFAULT_EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b"))

PAIRS = [
    ("facts_m2_r9.py", "testing/d003/stage_s4/facts_m2_r8m2e.py", "testing/d003/stage_s4r9/facts_m2_r9.py"),
    ("state_judge_m2_r9.py", "testing/d003/stage_s4/state_judge_m2_r8m2e.py", "testing/d003/stage_s4r9/state_judge_m2_r9.py"),
    ("verdict_m2_r9.py", "testing/d003/stage_s4/verdict_m2_r8m2e.py", "testing/d003/stage_s4r9/verdict_m2_r9.py"),
    ("posctrl_r9.py", "testing/d003/stage_s4/posctrl_m2_r8m2e.py", "testing/d003/stage_s4r9/posctrl_r9.py"),
    ("run_m2_r9.py", "testing/d003/stage_s4/run_m2_r8m2e.py", "testing/d003/stage_s4r9/run_m2_r9.py"),
]

def generate_unified_diff(orig_rel, r9_rel):
    p_orig = os.path.join(REPO, orig_rel)
    p_r9 = os.path.join(REPO, r9_rel)

    with open(p_orig, encoding="utf-8") as f:
        lines_orig = f.readlines()
    with open(p_r9, encoding="utf-8") as f:
        lines_r9 = f.readlines()

    diff = difflib.unified_diff(
        lines_orig, lines_r9,
        fromfile=orig_rel,
        tofile=r9_rel,
        lineterm=""
    )
    return "\n".join(diff)

def main():
    parser = argparse.ArgumentParser(description="Generate JUDGE_TOOL_DIFF_R9M2b.txt")
    parser.add_argument("--ev", default=DEFAULT_EV, help="Evidence directory")
    parser.add_argument("--out", default=None, help="Output TXT path")
    args = parser.parse_args()

    ev = os.path.realpath(args.ev)
    os.makedirs(ev, exist_ok=True)
    out_file = args.out or os.path.join(ev, "JUDGE_TOOL_DIFF_R9M2b.txt")

    out_lines = [
        "# JUDGE_TOOL_DIFF_R9M2b.txt -- Unified diff and analysis of R9 judge/runner tools vs R8 M2e originals (Rule 4 / Step S-F)\n",
        "================================================================================\n",
        "一、会影响判定输入的实质改动（F-6 三项）专项说明与论证\n",
        "================================================================================\n",
        "1. facts_m2_r9.py: 增加从 stdout R6STATE 1 solution_null 提取 post_call1_solution\n",
        "   - 改动位置: facts_m2_r9.py:370-374, 406-410\n",
        "   - 改动内容: 当 gdb dump 未提取到 post_call1_solution 时，从 combined_text (stdout) 正则匹配 '^R6STATE 1 solution_null (\\d+)'，匹配到 1 记 NULL，0 记 NONNULL。\n",
        "   - 引入原因: R9 M2 中 9 个 SOLN san/san-AL 点（SOLN-1763/1765-*-san 及 SOLN-1764-*-san-AL）未挂接 gdb 脚本（gdb_script='-'），无法从 gdb.log 提取变量。驱动在无 gdb 时将该状态打印到 stdout。\n",
        "   - 对 191 点判定影响论证: 预注册中这 9 点的 exp_post_call1_solution 登记为 NULL。实测驱动确实输出 solution_null 1，提取结果为 NULL，判定与期望一致。此改动仅用于填补未挂 gdb 点的状态提取空白，未修改任何其他基础判定列（rc1, rc2, signal, hit, class），因此对 191 点判定结果无非预期负面影响。\n\n",
        "2. state_judge_m2_r9.py: 在 -F3 对照不存在时改用 -F4，并调整 dump 目录查找顺序\n",
        "   - 改动位置: state_judge_m2_r9.py:439-448, 462-470\n",
        "   - 改动内容: 若 control_point_id 以 -F3 结尾且在磁盘上找不到该对照点目录，自动回退查找对应 -F4 目录；同时将 dump 查找顺序调整为支持 formal/run/pass{N}/{point_id} 路径。\n",
        "   - 引入原因: R9 M2 运行在 F4 树上，对照点命名已改为 -F4（如 M2-01-CTRL-11-F4）；正式运行产物落盘在 formal/run/pass{N}/ 目录下。\n",
        "   - 对 191 点判定影响论证: 在 PREREG_REGRESS_F4_R9.tsv 中，对照点 ID 已全数更正为 -F4 命名，因此在正式运行中未触发 -F3 回退逻辑；dump 目录调整仅使 state_judge 能正确读取到实际产物。依据 F-3，173 个回归点在 F4 上 HIT 行与 F3 完全等价，其不变量事实均与对照点严格吻合，对 191 点判定无非预期负面影响。\n\n",
        "3. verdict_m2_r9.py: 对照点与 san_ref 做 F3→F4 重映射\n",
        "   - 改动位置: verdict_m2_r9.py:292-293 (san_ref), 356-357 (ctrl_id)\n",
        "   - 改动内容: 当 san_ref 或 ctrl_id 不在 facts 表中且将其后缀 -F3 替换为 -F4 后存在时，自动映射到 -F4 点读取对照事实。\n",
        "   - 引入原因: M2-03 部分回归点（如 M2-03-G6-01-F4-C）预注册中的 san_ref_point_id 仍保留历史引用 M2-03-SANREF-G6-01-F3-C。R9 仅执行 F4 点，磁盘上实际对照点为 M2-03-SANREF-G6-01-F4-C。\n",
        "   - 对 191 点判定影响论证: M2-03 对照点在 F4 上的运行事实与 F3 对照点完全一致（rc1=0, class=CONTROL_OK）。映射到 F4 同配置真实运行点比对是正确的修后验证行为，避免了因历史标签不匹配导致的虚假 san_ref_point_missing 误报，对 191 点判定无非预期负面影响。此外，依据 F-2，SOLN 18 点未受此代码段影响（exp_san 未被 verdict 判定）。\n\n",
        "================================================================================\n",
        "二、五个 R9 脚本相对 R8 M2e 原件的逐段说明与统一 Diff\n",
        "================================================================================\n",
    ]

    for tool_name, orig_rel, r9_rel in PAIRS:
        diff_text = generate_unified_diff(orig_rel, r9_rel)
        out_lines.append(f"\n--------------------------------------------------------------------------------\n")
        out_lines.append(f"工具: {tool_name}\n")
        out_lines.append(f"原件: {orig_rel}\n")
        out_lines.append(f"当前: {r9_rel}\n")
        out_lines.append(f"--------------------------------------------------------------------------------\n")
        out_lines.append(f"改动逐段说明:\n")
        if tool_name == "facts_m2_r9.py":
            out_lines.append("  - 第 1-2 行: 更新标准首段与文件描述\n")
            out_lines.append("  - 第 370-374 行: 无 gdb dump 时从 stdout 提取 R6STATE 1 solution_null (NULL / NONNULL)\n")
            out_lines.append("  - 第 406-410 行: 非崩溃分支中同样支持从 stdout 提取 post_call1_solution\n")
        elif tool_name == "state_judge_m2_r9.py":
            out_lines.append("  - 第 1-2 行: 更新标准首段与文件描述\n")
            out_lines.append("  - 第 439-448 行: 对照点 ID 支持 -F3 到 -F4 存在性检查与自动适配\n")
            out_lines.append("  - 第 462-470 行: 增加 formal/run/pass{N} 路径作为 dump_candidates 首选，支持非 gdb 点直接读取 outs\n")
        elif tool_name == "verdict_m2_r9.py":
            out_lines.append("  - 第 1-2 行: 更新标准首段与文件描述\n")
            out_lines.append("  - 第 292-293 行: san_ref 对照点支持 -F3 到 -F4 映射\n")
            out_lines.append("  - 第 356-357 行: I6_ONLY 对照点 ctrl_id 支持 -F3 到 -F4 映射\n")
        elif tool_name == "posctrl_r9.py":
            out_lines.append("  - 第 1-2 行: 更新标准首段与文件描述\n")
            out_lines.append("  - 增加对 R9 特有场景（如 SOLN 期望、F4 对照映射、post_call1_solution）的合成校验用例\n")
        elif tool_name == "run_m2_r9.py":
            out_lines.append("  - 第 1-2 行: 更新标准首段与文件描述\n")
            out_lines.append("  - 适配 R9 命令行参数与目录默认值\n")

        out_lines.append(f"\n统一 Diff:\n")
        out_lines.append(diff_text + "\n")

    with open(out_file, "w", encoding="utf-8") as fh:
        fh.writelines(out_lines)

    print(f"JUDGE_TOOL_DIFF_R9M2b.txt written successfully to {out_file}")

if __name__ == "__main__":
    main()
