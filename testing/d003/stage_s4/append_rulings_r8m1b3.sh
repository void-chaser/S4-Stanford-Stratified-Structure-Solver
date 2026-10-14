#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1b3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_rulings_r8m1b3.sh -- append U205..U208 to RULINGS.tsv (append only). New file.
set -u
RUL="$REPO/checkpoints/p05/registries/RULINGS.tsv"
grep -q '^U205	' "$RUL" && { echo "U205 exists; refuse" >&2; exit 2; }
grep -q '^U206	' "$RUL" && { echo "U206 exists; refuse" >&2; exit 2; }
grep -q '^U207	' "$RUL" && { echo "U207 exists; refuse" >&2; exit 2; }
grep -q '^U208	' "$RUL" && { echo "U208 exists; refuse" >&2; exit 2; }
cat >> "$RUL" <<'EOF'
U205	P05-S4 R8 M1b3 任务书 §0	采纳 M1b2 报告方案 A。补充预注册 PREREG_SUPP_R8_M1b3.tsv 覆盖 ENV_AUDIT_M1B_R8_M1b2.tsv 中 audit_verdict ≠ ENV_AGREE 的全部 342 行（G1 282 + G2c 60；F2/F3 各半），沿用 U203 的全部约束（来源只能是 R7 原始调用参数，状态 INFLUENCED，结果单独成表，不覆盖 M1b1）。	P05-S4 R8 M1b3 任务书 §0	生效
U206	P05-S4 R8 M1b3 任务书 §0	M1b1 中 G1 的 50 行 SILENT_SWALLOW（F2 25 + F3 25，均为 R7 inj_call=2 的 twice 点，事实 rc1=20/rc2=0/hit=1）判定为缺 S4FMM_NTH 造成的环境假象：不进红点台账，不作为任何产品结论的依据。	P05-S4 R8 M1b3 任务书 §0	生效
U207	P05-S4 R8 M1b3 任务书 §0	补跑的 inj_call 只能取 R7 的 REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv 的 inj_call 列；real 只能按 run_m2_r7.real_of 的规则；env 必须等于 expected_env_independent_r7.expected_env_from_history(...) 的返回值，逐键比较。三项都不得从期望 rc 反推。每次调用把实际传给驱动的 FMM_* 与 S4FMM_* 变量写入结果表的 env_as_run 列。	P05-S4 R8 M1b3 任务书 §0	生效
U208	P05-S4 R8 M1b3 任务书 §0	M1c 的环境以 R7 调用日志的 env_as_run 为准，本轮补交核对表。若 440/440 一致，M1c 在下一轮（r8m1c1）单独执行，本轮不跑 M1c。	P05-S4 R8 M1b3 任务书 §0	生效
EOF
echo "appended U205-U208 to RULINGS.tsv"
