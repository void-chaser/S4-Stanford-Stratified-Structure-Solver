# P05 当前状态(每轮结束更新,保持一页以内)

> 规则见仓库根 `AGENTS.md`。本文件是摘要;细节以各轮报告为准。签收只由用户给出。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| HEAD(本文件起草时) | `86d01ed`(P05-S4 R4) |
| `HEAD:S4` | `4a6f64927a30537740dd0c8f11f9a5aae5e46ba4`(= 冻结树 F `1c11905`) |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收(带范围声明,见 `P05_S1_S2_SIGNOFF.md`);S3、S4、S5 未签收 |
| 当前阶段 | P05-S4(验证)。R1–R4 已提交,等待 R5 |

## 2. 各轮关键数字(P05-S4,冻结树 F)

| 轮 | 内容 | 关键数字 | 报告 |
|---|---|---|---|
| R1 | 门禁、预注册(62 个 R1 编号) | 无运行 | (无独立报告;见 R2 报告的 ERRATA_2) |
| R2 | 四树构建、首次三列运行 | 15 用例 × B/A/F = 45 行:34 MATCH、11 MISMATCH(其中 9 行未命中,均为预注册 NTH 映射错误) | `P05_S4R2_REPORT.md` |
| R3 | 调用序发现 + FMM 分配/plan/exec 穷举 | 范围内 141 点;B:123 MATCH、4 MISMATCH、22 INVALID;F:127 MATCH、22 INVALID、0 CRASH/SILENT_SWALLOW | `P05_S4R3_REPORT.md` |
| R4 | F 上 seam 库;SI/AL18/FE/info=NULL/CLM/ACF;plan NTH≥3 补测 | 主矩阵 75 行:59 MATCH、0 MISMATCH、10 INVALID(B 的 FE,结构性)、6 NO_EXPECTATION;F 列 25/25 REPORTED_FAILURE。plancall 44 对:34 MATCH、10 MISMATCH(B,twice NTH 12–16) | `P05_S4R4_REPORT.md` |

R1 覆盖表(62 个编号,R4 合并后):57 REACHED,5 UNMAPPED(AL02、K1A、K1B、D016、RNV1)。

## 3. 开放问题(未闭合前 S3、S4 都不能签收)

1. **plan twice NTH 12–16(fft、kottke 各 5 点)**:B 与 F 的 rc/rc1/rc2 相同(1/0/1),B 无检查却不崩溃。F 的这 10 行不能作为检查生效的证据。需 gdb 机理调查(用户已授权)。
2. **plan M≥2**:一次 plan 调用内第 2 次及以后的 malloc 未注入。
3. **UNMAPPED 5 项**:
   - AL02:与 EXP40 同一站点,R1 重复登记,待确认后注销;
   - K1A、K1B:R4 报告"路径未确认"有误。证据在 `registries/s3r2/R2-4bc_SUMMARY.txt`(R2-4c,eps=0 与 1e-300:start 139 → new rc 20),new = `ff6dd7c`,其 `S4/` 与 F 相同。待 R5 复核登记;
   - D016:证据在 `evidence/p05-s3r2/R2-4b_runs/` 与 `registries/s3r2/R2-4bc_SUMMARY.txt`(VL NG=1 返回 −10);
   - RNV1:S3R2 报告第 3.3 节写明 error 路径未被触发,仅 [源码] 结论,无运行证据。
4. **S3 移交给 S4 而未运行的验收项**(`evidence/p05-s3/D4_P05_S4_INPUTS.txt` 第四节;路线图 P05 行):失败后模式/缓存不安装;失败后不缓存部分 P;Python/Lua 可见失败;恢复后重试正确(V3);中间量错误是否改变输出(类别 C);NB=1–8 覆盖。
5. **V4 sanitizer**:ASan/UBSan 下的失败路径未跑。
6. B 侧未解释(只影响基线列,不阻塞):R3 的 jones/vl vfield NTH4 为 SILENT_SWALLOW、nv 为 CRASH。
7. 非 FMM `S4_malloc`:静态 35 个调用行(`S4.cpp`),不属 D003,留给 S5 登记表;不追"约 43"的估计差额。

## 4. 证据位置

| 轮 | 证据目录(不提交) | 已提交的小型结果表 | sha256 清单 |
|---|---|---|---|
| R1 | `evidence/p05-s4/` | 未复制(R5 第一步) | 无(R5 补) |
| R2 | `evidence/p05-s4r2/` | 未复制(R5 第一步) | 仅预注册 `REGISTRY_S4_PRE_R2_v2.sha256` |
| R3 | `evidence/p05-s4r3/` | 未复制(R5 第一步) | 仅预注册 `REGISTRY_S4_PRE_R3.sha256` |
| R4 | `evidence/p05-s4r4/` | 未复制(R5 第一步) | 仅预注册 `REGISTRY_S4_PRE_R4.sha256`、`REGISTRY_S4_PRE_R4_B.sha256` |

S3R2 的结果表已在 `registries/s3r2/`(提交 `1c11905`)。
