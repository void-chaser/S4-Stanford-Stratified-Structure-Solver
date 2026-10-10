# P04 必要 leak 行 1–4：负责人 B 接受记录

日期：2026-10-10（Australia/Sydney，AEDT）
候选：5cf534ce5ec223a6388d29bbb2c58f981f070241（父 963ccf153855734de968e6cf71477f324e33329c）
依据：第十一轮 `P04_CLOSEOUT_RECORD.md` §2 闭环表；第十二轮 `CLOSEOUT_DELTA.md` §6–8 修正。

## 负责人原文（批准依据）

> 我作为负责人，接受第十一轮闭环表中行 1–4 的已有保存证据及相应独立保存核验，采用 B 完成这四行的有限泄漏验收。接受记录中已披露的覆盖限制；此决定不构成独立动态 LSan 认证，也不扩大 P04 的冻结范围。

## 验收结果

| 行 | 目标 | 方式 | 保存证据位置（相对主检出） | 核验结果 |
|---|---|---|---|---|
| 1 | RNP n=2 dense 已有工作区：失败与重复调用 | B（保存证据验收，非独立动态 LSan 认证） | `.p04-review/remediation/repo/checkpoints/p04-remediation/evidence/round3/rnp-seam-workspace/` | SUMMARY compile_rc=0，18 个进程 run_rc=0 且 state=finished；18 个 `.stderr` 均为 0 字节；`round3/MANIFEST.sha256` 118/118 OK |
| 2 | rcwa n=2 dense 成功路径 | B（保存证据验收，非独立动态 LSan 认证） | `.p04-review/remediation/repo/checkpoints/p04-remediation/evidence/rcwa/candidate/` | SUMMARY compile_rc=0，null/short/exact/query 各 run_rc=0；`.stderr` 均为 0 字节；四个源码 blob 与候选一致 |
| 3 | rcwa n=2 非零 info：NULL / 短 / sufficient lwork=24 | B（保存证据验收，非独立动态 LSan 认证） | `.p04-review/remediation/repo/checkpoints/p04-remediation/evidence/round6/rcwa-failure-workspace/` | `VERDICT.json` pass=true；control_lost rc=23 且有报告，control_freed / control_reachable rc=0 无报告；`round6/MANIFEST.sha256` 78/78 OK |
| 4 | S4 Simulation_ComputeLayerModes 失败释放 q | B（保存证据验收，非独立动态 LSan 认证） | `.p04-review/remediation/round10/decision-20261010-5cf534c/asan-probe/`（32/32 OK）与 `.p04-review/remediation/round11/closeout-20261010-5cf534c/selfrun-20261010-c/`（MANIFEST 60/60、BINARIES 7/7） | ctl_lost rc=23（1 处直接泄漏）；ctl_freed、ctl_reachable rc=0 无报告；mut_inject rc=23（4 处直接泄漏，栈顶 Simulation_ComputeLayerModes）；tgt_unset、tgt_inject rc=0 无 LSan 报告；tgt_inject 的 4 条 RESULT 均为 rc=20 |

## 限制（负责人接受的范围，并如实记录）

- 以上四行均为**保存证据验收**，不是独立动态 LSan 认证，不能据此声称运行过独立 LSan。
- 行 1–3 只覆盖 n=2 dense；行 4 只覆盖 S4 层非均匀失败路径，均匀张量分支未动态运行。
- Python/Lua 前端未在 sanitizer 下运行；Lua GetAmplitudes 新分支未覆盖。
- 本决定不扩大 P04 冻结范围；HAVE_LAPACK、query、新 pthread、n>2、A-10r、D012、历史 provenance 仍在范围外。

## 本次新发现的核验缺口（未在闭环表中披露）

行 3 的 `round6/rcwa-failure-workspace/hashes.txt` 共 17 条：

- 5 个目录内文件（`VERDICT.json`、`RUN_STDOUT.txt` 等）核验通过。
- 4 个源码条目（`S4/rcwa.cpp`、`S4/rcwa.h`、`S4/RNP/Eigensystems.cpp`、`testing/s4test/test_seams/seam.h`）与候选 5cf534c 的 blob 一致（以源码树相对路径记录，不在本目录内）。
- `owned_failure_rcwa.cpp` 与 `repro/rcwa_failure_workspace/` 当前副本一致。
- `run.sh`、`check_results.py` 与当前 repro 副本不一致。这是历史 checker 与当前脚本的已披露差异（第八轮 REVIEW 明确：历史 checker 不冒称与当前一致）。本行接受的是 round6 保存运行所用的历史脚本，而非当前副本。
- `build-seam-asan/libS4.a`、`build-seam-asan/S4k/rcwa.o`、`../lsan_controls/lost.c` 不在保存目录内，本次无法核验；其它流程副本中存在同名文件，但不能证明与此 hashes.txt 对应。

该缺口不影响 VERDICT、控制 rc 与 round6 总清单结论，但它是**接受范围之外的新事实**：本行 B 接受的是已保存的 verdict、控制结果与总清单，不包含上述 hashes.txt 中无法在保存目录内核验的 build 对象与 lsan 控制源。若负责人要求，行 3 可撤回 B 或补充说明。

## 未覆盖（本记录不处理）

- 最终生产签收（D001、D002、P04）：未完成，需实际审核者签署。
- 最终采纳到主分支与正式状态落地：未授权，未执行。
- P05：未启动。

## 本次未执行的操作

未 fetch、switch、apply、commit、push、tag 或 PR；未修改任何历史证据目录或用户现场文件（`.gitignore`、`DEFECTS.md` 与其他未跟踪文件）。
