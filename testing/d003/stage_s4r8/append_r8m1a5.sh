#!/bin/sh
REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m1a5; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# append_r8m1a5.sh -- appends U192-U197 to RULINGS.tsv and E8-68, E8-69 to ERRATA_8.txt (brief CONT3b1 sections 3).  New file.
# Both files are append-only.  Before appending, the first bytes of each file are checked against the start-gate record.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m1a5 -- sh testing/d003/stage_s4r8/append_r8m1a5.sh
set -u
RUL="$REPO/checkpoints/p05/registries/RULINGS.tsv"
ERR="$REPO/checkpoints/p05/registries/s4r8/ERRATA_8.txt"
START="$EV/GATE_R8_M1a5_START.txt"
test -f "$START" || { echo "append_r8m1a5: start gate missing" >&2; exit 2; }
[ "$(tail -n 1 "$START")" = "FAILS=0" ] || { echo "append_r8m1a5: start gate not FAILS=0" >&2; exit 2; }
RB=$(awk -F'\t' '$1=="RECORD" && $2=="RULINGS_BYTES" {sub(/^value=/, "", $3); print $3}' "$START")
RH=$(awk -F'\t' '$1=="RECORD" && $2=="RULINGS_SHA256" {sub(/^value=/, "", $3); print $3}' "$START")
EB=$(awk -F'\t' '$1=="RECORD" && $2=="ERRATA_8_BYTES" {sub(/^value=/, "", $3); print $3}' "$START")
EH=$(awk -F'\t' '$1=="RECORD" && $2=="ERRATA_8_SHA256" {sub(/^value=/, "", $3); print $3}' "$START")
[ "$(head -c "$RB" "$RUL" | sha256sum | cut -d' ' -f1)" = "$RH" ] || { echo "append_r8m1a5: RULINGS prefix mismatch" >&2; exit 2; }
[ "$(head -c "$EB" "$ERR" | sha256sum | cut -d' ' -f1)" = "$EH" ] || { echo "append_r8m1a5: ERRATA_8 prefix mismatch" >&2; exit 2; }
SRC="生效"
printf '%s\t%s\t%s\t%s\t%s\n' \
'U192' 'R8 M1a 续3b1 任务书 §3' '接受 audit3（abf3e42）与阶段 B 存量提交 2a08aa5 的结果及全部披露；续3a 审核修正到此关闭；准许进入续3b。这只是续3b 的进入许可，不是 M1a 或 P05-S4 的签收。表一中的越界占位写入（根目录临时区占位路径）按执行偏离接受，不追认为合规。' 'checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1.md §3' "$SRC" >> "$RUL"
printf '%s\t%s\t%s\t%s\t%s\n' \
'U193' 'R8 M1a 续3b1 任务书 §3' '对 58 个 PLANCALL 点（U189 中的 EVIDENCE_INSUFFICIENT），K 与 M 取请求文本 plancall:K:M，并与 M3_F2_STATE_R6c_pass1/pass2.tsv 的 env_as_run 中 S4FMM_INJECT 的值交叉核对；两遍都相等才记 K_FROM_REQUEST_AGREED，否则记 EVIDENCE_INSUFFICIENT，并按停止条件处理。' 'checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1.md §3' "$SRC" >> "$RUL"
printf '%s\t%s\t%s\t%s\t%s\n' \
'U194' 'R8 M1a 续3b1 任务书 §3' 'audit3 的记录瑕疵按任务书 §4 修正：E8-68 缺失；end 规则在 start 后放宽；报告未附提交后 git 记录；STATE 超过一页、开放问题第 58 行去向已过时。' 'checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1.md §3' "$SRC" >> "$RUL"
printf '%s\t%s\t%s\t%s\t%s\n' \
'U195' 'R8 M1a 续3b1 任务书 §3' '续3b 分两轮。续3b1 = 本轮（瑕疵修正与正式预注册）；续3b2 = M1b/M1c 运行器（只用 --dry）、dry-run（不执行驱动）、M1a 总报告与收尾。' 'checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1.md §3' "$SRC" >> "$RUL"
printf '%s\t%s\t%s\t%s\t%s\n' \
'U196' 'R8 M1a 续3b1 任务书 §3' '预注册中 callseq_status 的规则：(a) 行映射到 REQUEST_TARGETS_R8_M1a4AUDIT3.tsv 的 unit_id，再映射到 CALLSEQ_F2_F3_R8_M1a4_R2.tsv 中的配对；配对为 IDENTICAL 时记 IDENTICAL；(b) CONTROL_NA 行记 N/A_CONTROL；(c) EXPECTED_NOT_REACHED 行记 IDENTICAL_NOT_REACHED，期望仍为 NOT_REACHED_AS_EXPECTED（U139(d)）；(d) S3R4 新增行按 ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN2.tsv 记 MAPPING_VERIFIED_STRICT，其中 A-U96 三行记 NOT_VERIFIED_K0_VERIFY_BY_INJECTION（U191）；(e) 其他情况（找不到 unit 或配对、配对不是 IDENTICAL）一律停止，不得自行重映射（U140）。' 'checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1.md §3' "$SRC" >> "$RUL"
printf '%s\t%s\t%s\t%s\t%s\n' \
'U197' 'R8 M1a 续3b1 任务书 §3' 'R7 中 source_tree = F 的行，在 R8 中对应 F3 行。F3 行的期望按 U139(b) 取 R7 中 F2 两遍一致的 class 与 rc1；不使用 R7 的 F 结果作期望。F 树本身不再运行。' 'checkpoints/p05/briefs/P05_S4R8_BRIEF_M1a_CONT3b1.md §3' "$SRC" >> "$RUL"
printf '\n%s\n%s\n' \
'E8-68  续3b1（r8m1a5）补写：STATE 引用的 E8-68 正文（只追加）。' \
'        内容：audit2 阶段 B 记录提交脚本 commit_rec_r8m1a4audit2_B.sh 的清单缺少脚本自身，且该脚本在 audit2 中未执行。audit3（r8m1a4audit3）在开工时把该脚本加入清单后执行，得到提交 2a08aa5（HEAD^ = 86ba3a2）。这是存量记录提交，不是 audit3 的新工作。依据：audit3 报告 §8.1。' >> "$ERR"
printf '\n%s\n%s\n%s\n%s\n%s\n' \
'E8-69  续3b1（r8m1a5）：audit3 的 gate11 end 规则在 start 后放宽，已披露（只追加；依据 U194）。' \
'        (1) audit3 的 gate11_r8m1a4audit3.sh 在 start 之后放宽了 end 规则：允许 start 中已有的行、三个活文件（前缀校验）以及名字含 AUDIT3/audit3/m1a4audit3 的未跟踪本轮文件。该放宽在 start 之后、end 之前作出，已记入 audit3 报告 §1.3。' \
'        (2) 本轮起，允许列表改为开工前冻结的数据文件（testing/d003/stage_s4r8/gate_allow_r8m1a5_start.txt 与 gate_allow_r8m1a5_end.txt），二者的 sha256 记入 start 门禁并在 end 中校验；门禁脚本只读这两个文件（gate12_r8m1a5.sh）。' \
'        (3) audit3 报告 §12 所说的"提交后 git 记录"并不存在。本轮用脚本把 git log -3 --oneline 与 git status --short 写入 FINAL_GIT_R8_M1a4AUDIT3_POST.txt 补齐（见 registries/s4r8/M1a/）。' \
'        (4) 旧报告不改；本条为其补充披露。' >> "$ERR"
printf 'append_r8m1a5: appended U192-U197 (6 rows) and E8-68, E8-69\n'
echo "RULINGS_BYTES_AFTER $(wc -c < "$RUL" | tr -d ' ')"
echo "ERRATA_8_BYTES_AFTER $(wc -c < "$ERR" | tr -d ' ')"
exit 0
