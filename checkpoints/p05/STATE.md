# P05 当前状态(每轮结束更新,保持一页以内)

> 规则见仓库根 `AGENTS.md`。本文件是摘要;细节以各轮报告为准。签收只由用户给出。

## 1. 当前位置

| 项 | 值 |
|---|---|
| 分支 | `codex/p05-d003-fft-error-propagation` |
| HEAD(R5 收尾时) | 见 `git log -1`(R5 的收尾提交;R5 之前为 `2551a5e`) |
| `HEAD:S4` | `4a6f64927a30537740dd0c8f11f9a5aae5e46ba4`(= 冻结树 F `1c11905`) |
| 判定器 sha256 | `d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb` |
| 阶段签收 | S1、S2 已签收(带范围声明,见 `P05_S1_S2_SIGNOFF.md`);S3、S4、S5 未签收 |
| 当前阶段 | P05-S4(验证)子轮次 R5 已完成范围内工作,等待用户审核(见 `P05_S4R5_REPORT.md`) |

## 2. 各轮关键数字(P05-S4,冻结树 F)

| 轮 | 内容 | 关键数字 | 报告 |
|---|---|---|---|
| R1 | 门禁、预注册(62 个 R1 编号) | 无运行 | (无独立报告;见 R2 报告的 ERRATA_2) |
| R2 | 四树构建、首次三列运行 | 15 用例 × B/A/F = 45 行:34 MATCH、11 MISMATCH(其中 9 行未命中,均为预注册 NTH 映射错误) | `P05_S4R2_REPORT.md` |
| R3 | 调用序发现 + FMM 分配/plan/exec 穷举 | 范围内 141 点;B:123 MATCH、4 MISMATCH、22 INVALID;F:127 MATCH、22 INVALID、0 CRASH/SILENT_SWALLOW | `P05_S4R3_REPORT.md` |
| R4 | F 上 seam 库;SI/AL18/FE/info=NULL/CLM/ACF;plan NTH≥3 补测 | 主矩阵 75 行:59 MATCH、0 MISMATCH、10 INVALID(B 的 FE,结构性)、6 NO_EXPECTATION;F 列 25/25 REPORTED_FAILURE。plancall 44 对:34 MATCH、10 MISMATCH(B,twice NTH 12–16) | `P05_S4R4_REPORT.md` |

| R5 | 子轮次:回填 R1–R4(44 文件);gdb 调查 plan twice NTH 12–16;M≥2;UNMAPPED 清账;V4 sanitizer;V3 重试 | 等价性 24/24 SAME;gdb:TWICE=slab 路线 F 检查执行(i),无 TWICE 路线未定;M=2 36 点 F 全 MATCH;K1 F 4/4 MATCH;D016 MATCH;V4 224 点类别 224 SAME、sanitizer 发现 0;V3 132 点 IDENTICAL(单列 70) | `P05_S4R5_REPORT.md` |

R1 覆盖表(62 个编号,R4 合并后):57 REACHED,5 UNMAPPED。R5 之后:AL02 注销为 EXP40 重复;K1A、K1B、D016 已测;RNV1 部分(见第 3 节)。

## 3. 开放问题(未闭合前 S3、S4 都不能签收)

R5 之后的状态。"关闭"指有运行证据;"部分"指只关闭了其中一部分;闭合与否由用户决定。

1. **plan twice NTH 12–16(fft、kottke 各 5 点)** — **部分关闭,仍开放**。TWICE=slab 路线已机理化:F 的 `fmm_FFT:90` 检查执行,返回 20(R5-2 Q2/Q5 = i);B 无检查,`fft_plan_exec(NULL)` 段错误。无 TWICE 路线的 F 结论**未定**(断点矛盾,E5-13)。**新发现**:R4 plancall 的 twice 行实际无 TWICE(E5-10),任务书前提"TWICE=slab 时 1/0/1"不成立(实测 F 1/0/20、B SIGSEGV)。待用户裁决。
2. **plan M≥2** — **关闭**(R5-3):m(K)=2 在 156 个 (模式、路由、K) 观察中两遍一致(无 m≥3);M=2 的 36 个范围内点 F 全部 REPORTED_FAILURE(MATCH);B 全部 CRASH(基线)。
3. **UNMAPPED 5 项**:
   - AL02 — **关闭**:与 EXP40 同一站点(experimental.cpp:40),注销为重复登记(E5-5);
   - K1A、K1B — **关闭**(R5-4):F 在 eps 0、1e-300 得 rc 20,在 1e-100、4 得 0,与预注册一致;F 场与 S3R2 new 逐字节一致;B 在 eps 0、1e-300 段错误。**张量路径 K-1 仍开放**(R5 未做,S3R2 报告第 6 节第 4 条);
   - D016 — **关闭**(R5-4):F 的 `pattern_generate_flow_field` 返回 −10(两次),驱动 rc 20;B 返回 0,与 S3R2 一致;
   - RNV1 — **部分,仍开放**:pattern 内 malloc 确认存在(每次 nv 运行 3 次,F 与 B 相同);注入未做(需新注入器,不改 S4/);pattern 的 work malloc 无 NULL 检查(源码),注入预计先段错误,不会到达 −10 路径。列入 R6。
4. **S3 移交清单(D4 第四节)** — 逐条见 `evidence/p05-s4r5/S3_HANDOFF_COVERAGE_R5.tsv`:
   - 失败后模式/缓存不安装 — **仍开放**(驱动 witness partial_modes=1,语义未定,E5-15);
   - 失败后不缓存部分 P — **仍开放**(无直接缓存探针);
   - Python/Lua 可见失败 — **仍开放**(R6,R5 未跑);
   - 恢复后重试正确(V3) — **部分关闭**:132 点重试场与同模式同路由基准逐字节相同;单列 70 点(rc2-only 45、R4 seam 25)未比较;
   - 中间量错误(类别 C) — **仍开放**(R6);
   - NB=1–8 覆盖 — **仍开放**(R6);
   - 失败码传播链(四节 a) — **关闭(TWICE=slab 路线)**:FFT 1 → CLM 20 → GFP 20(R5-2)。
5. **V4 sanitizer** — **关闭**(R5-5):224 个注入点 + 5 个控制库,类别 224 SAME,sanitizer 发现 0;阳性对照确认工具能报告。
6. **B 侧未解释**(只影响基线列,不阻塞):R3 的 jones/vl SILENT_SWALLOW、nv CRASH — **仍开放**(未在 R5 查)。
7. **非 FMM `S4_malloc`**:静态 35 个调用行,不属 D003,留给 S5 — **仍开放**(S5 登记)。
8. **新开**:
   - E5-10:R4 plancall twice 行无 TWICE(前提偏差,需用户裁决是否以 TWICE=slab 重跑 R4 twice 行);
   - E5-15:驱动 witness `partial_modes=1` 与 "failed layer kept no partial modes FAILED"(132/132),语义未定;
   - E5-3:`registries/s4r3/ERRATA_3.txt` 与 `REGISTRY_S4_PRE_R3.sha256` 不一致(文件在清单后 8 分钟被改),需用户裁决;
   - E5-17:R4 GATE 的 `/tmp_none` 越界写入尝试(历史,见报告违规表)。

## 4. 证据位置

| 轮 | 证据目录(不提交) | 已提交的小型结果表 | sha256 清单 |
|---|---|---|---|
| R1 | `evidence/p05-s4/` | `registries/s4r1/`(GATE、REGISTRY_S4_PRE、PRE_REGISTRY_ERRATA_1、write_guard.log) | `registries/s4r1/SHA256SUMS.txt`(R5 已生成) |
| R2 | `evidence/p05-s4r2/` | `registries/s4r2/`(R2 结果与预注册 v2) | `registries/s4r2/SHA256SUMS.txt`(R5 已生成);证据目录 `evidence/p05-s4r2/SHA256SUMS.txt` |
| R3 | `evidence/p05-s4r3/` | `registries/s4r3/`(R3 结果、覆盖、红点、预注册 v3) | `registries/s4r3/SHA256SUMS.txt`(R5 已生成);证据目录 `evidence/p05-s4r3/SHA256SUMS.txt` |
| R4 | `evidence/p05-s4r4/` | `registries/s4r4/`(R4 结果、预注册 v4 与 B 版、plancall、regress、seam、drivers) | `registries/s4r4/SHA256SUMS.txt`(R5 已生成);证据目录 `evidence/p05-s4r4/SHA256SUMS.txt` |

S3R2 的结果表已在 `registries/s3r2/`(提交 `1c11905`)。
