#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1b3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_errata_r8m1b3.sh -- append E8-78 to ERRATA_8.txt (append only). New file.
set -u
ERR="$REPO/checkpoints/p05/registries/s4r8/ERRATA_8.txt"
grep -q '^E8-78' "$ERR" && { echo "E8-78 exists; refuse" >&2; exit 2; }
cat >> "$ERR" <<'EOF'
E8-78	P05-S4 R8 M1b3 更正（只追加；依据 AGENTS.md 第 2、5 节与任务书 §3 第 2 条）。
        (a) M1b1 的 94 行 MISMATCH 分两部分：44 行期望 INVALID、实测 REPORTED_FAILURE；50 行期望 REPORTED_FAILURE、实测 SILENT_SWALLOW。后者是 inj_call=2 时判定器取 rc2=0 造成的环境假象（U206）。
        (b) M1b1 运行器从期望 rc 反推 inj_call（plan_and_run_m1b_r8m1b1.py:226），本轮改为读 R7 的值（U207）。
        (c) M1b2 的 M1c 审计和生成器使用同一推导公式，不构成独立核对，由本轮核对表补足（ENV_LOGCHECK_M1C_R8_M1b3）。
        (d) M1b2 报告"缺 NTH/TWICE"的提法更正为：只缺 S4FMM_NTH，TWICE 正确。
        (e) M1b2 报告"M1c 可以执行"更正为"待用户审核"（U204/U208）。

EOF
echo "appended E8-78 to ERRATA_8.txt"
