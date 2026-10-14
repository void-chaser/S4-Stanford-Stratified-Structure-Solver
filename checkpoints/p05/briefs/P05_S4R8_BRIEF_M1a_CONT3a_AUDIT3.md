# P05-S4 R8 M1a 续3a 审核修正第三部分 任务书（原文存档）

> 存档说明：本文件为用户在对话中下发的"审核修正第三部分"任务书原文（r8m1a4audit3），按惯例另存为新的 brief。
> 它不替换、不覆盖原续3a任务书 `P05_S4R8_BRIEF_M1a_CONT3a.md`、恢复补充 `P05_S4R8_BRIEF_M1a_CONT3a_RESUME.md`、第一部分审核修正 `P05_S4R8_BRIEF_M1a_CONT3a_AUDIT.md` 与第二部分审核修正 `P05_S4R8_BRIEF_M1a_CONT3a_AUDIT2.md`。
> 仍属原续3a，不是新阶段、不是续3b。不注入、不补跑、不运行 M1b/M1c；不修改 S4/ 和任何已提交的 testing/d003 文件，新脚本一律带 r8m1a4audit3 编号；不得宣布完成或签收。工作量不是停止理由。任何停下都要做 end 门禁和记录提交。

## 〇、用户裁决（开工门禁通过后追加到 RULINGS.tsv，来源写"R8 M1a 续3a 审核修正第三部分任务书 §〇"）

- **U188**（44 行）：audit2 对裸 plan 请求的语义解析有误。注入器的 plan 模式是"第 nth 次 plan 调用内的第 nth 次 malloc"（inject_r4_plan.cpp:38、79–84、587，两个计数共用 nth()），不是"第 N 次 plan 调用"。按正确语义重新分类；历史 INVALID_NOT_REACHED 若与计数一致，记 EXPECTED_NOT_REACHED。这是更正分类，不是改期望。追加 E8-67 更正 audit2 报告 §4.3 和 STATE 待裁决项 (a)。
- **U189**（119 行）：F2 的 K 来源指定为 registries/s4r7/M3_F2_RESULTS_R6c_STATE.tsv 的 NTH_or_K（键为 point_id+pass），并与 M3_F2_STATE_R6c_pass1/pass2.tsv 的 env_as_run 中的 S4FMM_NTH 交叉核对。两遍一致才采用；不一致或缺失的记 EVIDENCE_INSUFFICIENT，不得猜测。
- **U190**（T1/补跑）：以"逐单元 PLAN_START 与 PLAN_END、WIN_OPEN 与 WIN_CLOSE 的 seq 集合完全相等，且 trace_error=NONE"作为 out_of_scope 未发生的直接证据（依据：callseq_r8m1a4_gdb.py 每个 START 只建一个 FinishBreakpoint，建失败写 trace_error；stop 与 out_of_scope 只会发生其一）。198 单元全部满足时，补跑预注册标为 WITHDRAWN（原文件保留，不删除）；任何一个单元不满足，则这个单元所在的配对保留在补跑范围内。T6：对 198 单元实际用到的每个不同驱动（按 sha256 去重）做只读符号查询。
- **U191**（K0）：接受 A 段 K0 为 EVIDENCE_INSUFFICIENT；A-U96 三行 NOT_VERIFIED_K0 转入 M1b，由注入结果直接验证，本轮不加观测运行。

## 一、开工：先新增门禁 gate11_r8m1a4audit3.sh（以 gate10_r8m1a4audit2_r2.sh 为蓝本，基线 HEAD=<阶段B提交哈希>，HEAD^=86ba3a2，status 必须为空），先运行 start 并确认 FAILS=0，然后再做任何追加。输出名用 GATE_R8_M1a4_AUDIT3_<名>.txt；派生的复核名须匹配 ^S4R7_RECHECK_GATE_R8_M1A4_[A-Z0-9_]+\.tsv$；end 模式从 START_FILE 读取开工值，不用位置参数传。

## 二、新增 classify_requests_r8m1a4audit3.py：plan 按 U188 判定（取第 N 次调用内的 PLAN_MALLOC 次数 ≥ N），G5-F2 按 U189 补 K，其余规则与 audit2 相同。输出 REQUEST_TARGETS_R8_M1a4AUDIT3.tsv、与 audit2 的逐行差异表、44 行结论表、119 行 K 来源表。

## 三、新增 tracer_pairing_r8m1a4audit3.py（按 U190 逐单元核对配对）和 symq_r8m1a4audit3.sh（覆盖所有不同驱动）；输出缺口表。缺口为空就撤回补跑预注册，否则只更新补跑范围。

## 四、22 行映射原样保留（19 VERIFIED_STRICT / 3 NOT_VERIFIED_K0）。

## 五、收尾：证据清单、registries 复制与 SHA256SUMS、更新 STATE（只有缺口为空、没有 UNEXPECTED_NOT_REACHED 时，才可写"可进入续3b（待用户审核）"）、写报告 P05_S4R8_REPORT_M1a_CONT3a_AUDIT3.md、运行 end、逐路径 git add、提交。提交脚本的清单必须包含提交脚本自己；提交后 status 必须为空。

## 六、停止条件：身份或完整性不符；start 门禁失败；出现 UNEXPECTED_NOT_REACHED，或 U189 下有点两遍不一致（登记后继续不依赖它的步骤）。

## 七、写入规则：同 audit2 §十。内联命令不得含任何 > 字符；ERRATA 正文不写 /tmp 字面量；所有输出只写 $EV=checkpoints/p05/evidence/p05-s4r8/m1a4audit3。最终回复为纯 Markdown，不超过 40 行，不得出现 HTML 标签。
