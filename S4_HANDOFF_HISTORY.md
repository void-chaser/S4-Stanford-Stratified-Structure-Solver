# S4 技术交接文档

> 快照日期：2026-10-01（用户时区 Australia/Sydney）。供新的 Codex Agent 继任。
> 本文生成过程仅读取现有文件、Git 元数据、软件版本和历史日志；**没有启动测试、构建、安装、修改现有代码或中断任何任务**。唯一新增文件是本文件。
> 下述测试命令是历史实际命令或未来验收入口，不代表本次已执行，也不授权立即执行。

## 1. 先读摘要

- 项目是 Stanford Stratified Structure Solver（S4），面向分层周期结构的 RCWA 电磁仿真；核心 C/C++，Python 与 Lua 前端。
- 当前目标：让现代 Python（当前为 3.14.4）在 Linux 上可靠构建和使用；验证数值、对象生命周期、错误传播、文件输出和回归装置。最终可支持论文复现，但目前**未独立定量复现论文结果**。
- 当前真实树：`/srv/nvme/projects/S4-Stanford-Stratified-Structure-Solver`，分支 `feature/python314-binding`，HEAD `b97f63989c4d8192faee119e4dbcb70ef4a27219`。
- D15 已集成真实工作树并完成有范围限制的验收；这些修复以及较早阶段成果仍未提交。不要认为 HEAD 包含所有成果。
- 生成本文前：19 个已跟踪文件修改，41 个未跟踪文件（Git 简略显示为 4 组），暂存区为空。完整清单见附录。
- 主套件最近有效记录是 **总计 257，256 通过，1 跳过，预期失败 0**；不是“257 项通过”。
- 优先后续任务：FMM FFT 错误传播与残缺层模式缓存。真实树仍有 **10 个**忽略 `fft_plan_exec` 返回值的静态调用点；“9 个”是旧报告的错误计数。
- 已存在 FMM 工作副本，见第 11 节；可能有其他 Agent 正在推进，**先协调、不得覆盖或中断**。
- 精确衍射截止点：安全报错已加固；普适、可信的精确点物理解尚未完成。不要通过强制 `-O3`、小扰动、过滤 NaN 或简单整体伪逆宣称修复。

## 2. 证据等级与使用规则

| 标记 | 意义 | 允许得出的结论 |
|---|---|---|
| R：当前只读核实 | 本次实际读取的源码、哈希、Git、版本、日志文件 | 确认文件/代码/记录存在；读取成功日志不等于本次运行成功 |
| I：此前独立复核 | 本对话中 Codex 在较早轮次亲自运行，有工具输出记录 | 在当时源码、构建、输入及覆盖范围内有效；不外推全库安全 |
| L：现存运行日志 | 例如 DeepSeek 留存的完整输出、命令、退出码 | 可核验“日志记录了什么”；执行者、范围、二进制关联须分别说明 |
| H：历史报告 | 附件、检查点、DEFECTS.md 中的文字结论 | 作为线索，不直接升级为独立证实事实 |
| U：未知/未验证 | 无完整证据、推测、候选实验、未运行平台 | 必须保持未知，不包装为通过 |

源码中的修复可由 R 确认存在，但其所有失败路径正确性不能仅靠代码存在来证明。成功回归快照不是独立物理基准。`OK (skipped=1)` 不能把跳过计为通过。

## 3. 执行环境、依赖与访问约束

### 3.1 本次只读获取的环境（R）

| 项目 | 版本/状态 |
|---|---|
| 主机 | `38X-Ubuntu` |
| 当前 Agent | 直接位于 Linux 主机，cwd 为真实仓库；shell bash |
| OS | Ubuntu 26.04.1 LTS，Resolute Raccoon |
| 架构/内核 | x86_64；`7.0.0-31-generic` |
| `python3 --version` | Python 3.14.4 |
| GCC / G++ | 15.2.0 |
| GNU Make | 4.4.1 |
| Python 3.14 / 开发包（dpkg） | `3.14.4-1ubuntu0.2` |
| `python3` 元包（dpkg） | `3.14.3-0ubuntu2`；元包号不等于当前解释器运行版本 |
| Lua / Lua 开发包 | `5.2.4-4` |
| BLAS / LAPACK 开发包 | `3.12.1-7ubuntu1` |
| setuptools / pip（当前 Python metadata） | 78.1.1 / 25.1.1 |
| NumPy / SciPy（当前 Python metadata） | 2.3.5 / 1.16.3；不是核心解析参考的必需依赖 |
| OpenSSH client（dpkg） | `1:10.2p1-2ubuntu3.6` |

核心构建需要 C/C++ 编译器、make、Python 开发头与 setuptools、BLAS/LAPACK；Lua 前端另需 Lua 5.2 开发包。测试使用标准库 unittest；NumPy 曾用于独立 SVD 研究，不应成为标准解析参考的循环依赖。工具装置用到 rsync、patch、timeout、sha256sum 等。Valgrind 历史报告为未安装；本次未重新查询，不视作当前事实。

根目录与 `/`、`/srv`、`/srv/nvme`、`/srv/nvme/projects` 的适用 `AGENTS.md` 本次未发现；继任时仍应重新检查。未做全文件系统搜索。

### 3.2 SSH 与 SMB

- 从 Windows 客户端接入时，构建和执行必须通过 SSH 到 `38X-Ubuntu`；SMB 只是服务器文件的映射，写入它可能直接修改真实树，不能当作隔离副本。
- 历史 Windows 沙箱中 Git 自带 ssh 曾报 `couldn't create signal pipe, Win32 error 5`；曾改用 `C:\Windows\System32\OpenSSH\ssh.exe`。这是客户端历史情况，不是当前 Linux 需要套用的命令。
- 本 Agent 已直接在服务器，不必为了“远程流程”再绕行 SSH。环境变化时先确认 hostname、uname 和路径。
- 历史 WSL 曾有 `Wsl/E_ACCESSDENIED`；与 Linux 核心正确性无直接关系。
- 当前会话此前检查未发现 `dsh-crew` / `dsh_run_worker` 可调用工具。只能说明未暴露给当时会话，不能证明服务器未安装或未运行该 MCP。新 Agent 需自行检查工具列表，不要擅自安装或改配置。
- Git 远端认证、当前远端分支状态、本次是否可推送均**未核查**；不要把早期授权或登录叙述当作当前推送授权。

## 4. Git 基线与历史任务

### 4.1 已提交基线（R）

HEAD 提交标题：`Fix Python 3.14 binding on Linux`。
提交记录日期：2026-09-29 15:35:25 +1000；作者 Ziyang Li。
提交说明：替换陈旧内部 API 调用和 distutils 生成方式、修复并行构建依赖、增加基础 RCWA 绑定测试；明确未复现论文。

HEAD 修改 10 文件，包含 `setup.py`、`gensetup.py.sh`、`main_python.c`、`Makefile.common`、4 项原始冒烟测试等。前一个提交 `182480d` 为 Python 3 兼容 WIP。

### 4.2 历史阶段梳理（H/L，部分 I）

1. 原始仓库同步、Python 版本及 Linux 环境检查、Python 3.14 绑定构建修复，形成 HEAD。
2. 逐步建立解析参考、子进程崩溃隔离、API、Clone、扫频、Lua 对照、收敛与回归测试。
3. 修复 Clone 所有权、SetFrequency 缓存失效、两层界面路由、绑定解析及插值器问题。
4. 通过 sanitizer 定位并修复 `zlahqr_` 空区间下溢、恢复合法单元素输出；修复 `ztrevc_` 的 NULL 指针偏移。
5. 研究截止点故障：从优化相关 NaN 追到奇异界面求解和 `omega*q` 除零；收敛为明确报错、失败不缓存的安全契约，未完成精确点数值算法。
6. 修复 Python 两个错误路径泄漏、Python/Lua 网格文件输出、公开 C 网格输入契约。
7. D15 修复网格准备期及 FFT 执行期分配失败，经历 fault harness 加固、路径保护、正式十文件集成。
8. 最近建议推进 FMM FFT 错误传播；现场已发现独立工作副本，但没有在本次获得正式完成报告。

测试数量从 41/79/122/142/148 等增长至 257；早期数量只代表当轮，不是当前验收基准。各历史阶段的完整 diff、首个提交方案和执行日志不都齐全；不凭历史报告补造缺失证据。

## 5. 已完成修改与技术决策

以下“完成”是当前真实树已存在实现，并有现存测试/日志或此前复核支撑；不等于所有平台和全部 OOM 路径已证明。

| 范围 | 当前实现/决策 | 证据与边界 |
|---|---|---|
| D1/D2 Clone | 清除 memcpy 后共享所有权、初始化计数/数组、深拷贝材料/图案/多边形/激励、正确区分 union 类型、统一失败清理；不释放借用的 exc.layer | R：当前源码与 clone 测试；L：主套件通过。完整故障注入当前有 planewave/exterior/polygon 三夹具及命中计数；本次没有运行其 sweep |
| 材料/构造清理 | Material_Destroy 释放名称；New 的关键 NULL 检查等 | R/H；仍非全库分配审计 |
| D3 两层 | 两层结构选择已有 SolveInterior，而非继续使用退化 SolveAll | R；两层解析及三层对照测试已存在；精确截止单独处理 |
| D4 插值器 | 正确拼写、自然三次样条、Hermite/输入验证及资源修复 | R：Interpolator.c 和测试；L：最终套件通过；深层 OOM 唯一跳过项仍未自动实测 |
| D5/D6/D7 绑定 | SpectrumSampler 格式串、polygon 转换异常/输入，以及 Exterior 签名记录 | R/H；不能将 Exterior 的全部 Lua 资源归属判为已解决 |
| D8 Lua 回归 | manifest 新路径、3 份 txt 基线、runner/numdiff 严格错误识别 | R/L；基线是当前求解器回归快照，不是论文正确性证明 |
| D9 扫频 | Python SetFrequency 复用 C API 失效层模式、解和场缓存，保留告警 | R；正逆序/新对象/材料变化等测试，L 主套件 |
| 特征求解器 | zlahqr_ 先处理空区间，合法单元素仍写 W；ztrevc_ 对可选 NULL 参数不做伪 1 基偏移 | R：Eigensystems.cpp；6 项直接 W 哨兵测试及 sanitizer 历史证据 |
| 对齐分配器 | sanitizer 分支使用 posix_memalign/free；保持非 sanitizer 分支 | R；realloc 的跨平台/偏移稳定性仍有边界，见第 10 节 |
| D10 截止安全 | 检查 SolveAll/GetSMatrix/SolveInterior 等失败状态，错误 3；非有限输出错误 18；失败不标记 solved，走既有清理 | R/L；是安全处理，不是精确截止点物理解 |
| D11 | Python GetAmplitudes/GetPowerFluxByOrder 错误路径释放 scratch | R/H/L；Lua Integrate/Exterior 等仍待审计 |
| D12 Python 网格 | 参数、非有限结果、文件 fopen/write/close 错误处理、释放与对象恢复 | R/I/L；文件输出不承诺两文件事务/回滚 |
| D13 Lua 网格 | GetFieldPlane 输入、输出文件错误、资源清理、可捕获错误与恢复 | R/L；不等于 ext_lua 全入口审计完成 |
| D14 公开 C 网格 | NULL/尺寸/乘积容量/无层/TRACE 检查，E/H 独立可选 | R/L；接口无容量参数，不能验证调用者实际缓冲长度 |
| D15/D15b | eh/from/to/计划/包装对象检查与唯一清理；checked KISS FFT、递归/多维错误传播，内部网格改 int 返回，上层 C/Python/Lua 传播 | R/I/L；网格链已验收，FMM 10 调用点仍不处理执行返回值 |

### 5.1 D15 关键契约

- `kf_bfly_generic` scratch 失败设置调用局部 err，不使用 NULL；递归不再重组失败子变换。
- 新增 checked KISS 入口，原 void 入口保留并委托，保证旧签名；旧入口不能给调用者提供状态，不能据此宣称所有第三方使用安全。
- `fft_plan_exec` 内部接口返回 int；KISS 错误进入 GetFieldOnGrid，停止在输出发布之前，清理计划和缓冲，返回 1。
- 网格链实测故障时 E/H 及两侧哨兵不变，同对象重试成功；不能外推其他求解错误的所有输出均不变。
- Python 对核心分配错误的既有语义为 RuntimeError（含 memory allocation error occurred）；不要未经契约评估改成全局 MemoryError。
- Lua 可 pcall 捕获；不能用 exit/abort 替代错误传播。
- 网格 from/to/tmpbuf 为不同对象；在该二维网格入口下 in-place 分支不可达的论证和 8 网格见证已记录。直接 fin==fout 的第三方调用未动态覆盖。
- Python/Lua 文件输出：.E 成功而 .H 失败时 .E 可能保留；写失败可留下部分文件。抛异常并释放资源，不承诺回滚或两文件原子提交。

## 6. 数值验证与不可外推的范围

### 6.1 独立参考（R/L）

`testing/s4test/analytic.py` 不 import S4，使用 math/cmath 的 Fresnel、TMM、Airy。
最终日志 `/home/jackal/s4-d15-acceptance5/final-accept.log` 的 C_selftest 记录：

- worst |TMM-Fresnel| = 5.551e-16；无损 worst |R+T-1| = 4.441e-16。
- 无损 worst |Airy-TMM| = 6.661e-16。
- n=1→2 法向界面 R=1/9、T=8/9。
- Brewster p 反射约 2.435e-32；全反射 R=1、T=0；四分之一波匹配层反射约 2.109e-33。
- 日志内的有损 TMM 结果可出现 R+T>1；这些夹具选择 Airy 参考。不能概括成“任何有损 TMM 都数学上无效”，可能涉及实现和符号约定；一般性结论未证明。

实际约定：GetPowerFlux 返回沿 +z 的有符号 forward/backward；无损入射介质下常用 R=-backward.real/incident.real，T=exit_forward.real/incident.real。复杂入射介质的定义不能照搬无损参考，需按具体测试约定审计。
GetAmplitudes 长度 2*n_G；分量符号/偏振约定以具体测试为准，不把单个法向 s 夹具的索引推广到所有配置。倒格矢单位 1/a，未乘 2π。

### 6.2 截止点（H/L；安全覆盖有 I）

平坦方晶格、eps 1→4、法向 s、NumBasis=9，f=1.0 可精确 q=0。
历史纯 -O1 可 NaN 或错误 r≈+0.9974，而 -O3 -march=native 可偶然得到 r=-1/3；邻点 0.999/1.001 给出 Fresnel。当前检测到奇异/非有限的路径明确报错。
其他截止族包括 f=0.5（玻璃级次）、sqrt(2)、2.0；并非只一个频点。默认优化在部分输入仍可给正确有限值，不能要求每个精确点/每种编译都报同一错误。
历史转储报告 MakeQ 的 18×18 矩阵 rank=14、4 维零空间；部分物理入射列相容、截止列不相容；Q 的邻点极限发散而物理解收敛。因此整体残差不能证明物理入射无解，整体最小范数 Q 也未被证明等于物理极限。本次没有重算矩阵/SVD，这些为研究证据，不是普适不可能性证明。

### 6.3 正常工程回归（I）

此前 Codex 独立对平坦/图案各 7×3、11×3、3×11、7×7、49×3、1×7 网格进行修复前后比较：3480 个复数分量差值为 0。证明这些具体输入的正常行为不变，不证明全部物理模型正确。
论文例 `examples/2d/Fan_PRB_65_2002/fig12.lua` 可运行及能量守恒属于运行/工程验证；没有取得论文原始曲线并独立定量比较。

## 7. 实际执行过的测试命令与结果（本次未执行）

### 7.1 最终集成日志：L，本次只读核实

日志：`/home/jackal/s4-d15-acceptance5/final-accept.log`，记录 24 个 EXIT 均为 0、FINAL_ACCEPT_DONE。

| 模式/范围 | 日志结果 |
|---|---|
| A 真实树干净 -O1 make test | 4 smoke；主套件 257 总计/256通过/1跳过；自检、Lua 正/负向通过；另 C API 16 |
| B 真实树默认优化，最后运行 | 同上主套件；C API 16；当时留下默认优化二进制 |
| C 独立 ASan+UBSan 副本 | C API 16、smoke 4、主套件257/1跳过、自检、Lua三套；日志功能诊断0 |
| D 真实源码派生测试插桩副本 | scratch14/14；解释器7案例两侧通过；泄漏12/12含4096 B正向对照 |
| E 独立 TRACE 副本 | C API16通过 |

主套件已含 C API 模块时，另跑 C API16属于针对性重复，不可简单相加宣传为不同测试数。三个模式各有一次同一 OOM 跳过，不代表三个不同缺陷。

原始实际命令（执行目录及 env 必须对应各树；下列只记录，不运行）：

```bash
# A / B，真实树
make test PYTHON=python3 CFLAGS="-O1 -fPIC" CXXFLAGS="-O1 -fPIC"
make test PYTHON=python3
python3 -W error::ResourceWarning -m unittest testing.s4test.test_capi_field_plane -v
(cd testing && ./runtests.sh)

# C，独立副本；先在对应副本清理陈旧产物，不能碰并行任务目录
S="-O1 -g -fPIC -fsanitize=address,undefined -fno-omit-frame-pointer"
make S4_pyext PYTHON=python3 CFLAGS="$S" CXXFLAGS="$S" LDFLAGS="-fsanitize=address,undefined"
make build/S4 CFLAGS="$S" CXXFLAGS="$S"
# 实际功能环境包含 detect_leaks=0:abort_on_error=1:halt_on_error=1，Python 仅进程级预加载 libasan
python3 -m unittest discover -s testing -p 'test_python_binding.py' -v
python3 -m unittest discover -s testing/s4test -p 'test_*.py'
python3 testing/s4test/selftest_analytic.py
(cd testing/s4test && ./test_lua_regression_negative.sh)
(cd testing/s4test && python3 test_lua_api_negative.py)

# E，独立副本
make S4_pyext PYTHON=python3 CFLAGS="-O1 -fPIC -DENABLE_S4_TRACE" CXXFLAGS="-O1 -fPIC -DENABLE_S4_TRACE"
make build/S4 CFLAGS="-O1 -fPIC -DENABLE_S4_TRACE" CXXFLAGS="-O1 -fPIC -DENABLE_S4_TRACE"
```

日志中的 env 初始化并非全部展开在 CMD 行；不要把上面的裸 Python 命令当作完整 sanitizer 启动脚本，需阅读日志/装置。Python 运行要固定 PYTHONPATH 与 S4_TEST_REPO_ROOT，记录实际 S4.__file__ 和哈希。

### 7.2 Codex 之前亲自执行（I，对话工具记录）

- D15 候选及真实树严格矩阵 `run-matrix.sh <tree>`：24/24。
- 真实树：`PYTHONPATH="$PWD:$PWD/testing/s4test" python3 -W error::ResourceWarning -m unittest discover -s testing/s4test -p 'test_*.py'`：257 总计，1跳过，0失败，约17.45秒。
- scratch14/14、解释器7/7、泄漏12/12和负向12/12在候选阶段独立重跑。相关明细 `/tmp/s4-d15-review-r3/`。
- 49×3 112字节分配第1/4/8次失败：返回1、输出不变、恢复成功。
- 构建目录保护8/8，含一次新目录构建；不是本次生成本文时执行。

### 7.3 测试装置调用（历史实际入口；未来须先获执行范围）

装置 `/home/jackal/s4-d15-harness/`，当前 README 使用唯一不存在的目标，不再删既有目录。

```bash
H=/home/jackal/s4-d15-harness
TARGET="/tmp/d15-instr-$(date -u +%Y%m%dT%H%M%SZ)-$$"
"$H/build-instrumented.sh" /path/to/frozen/tree "$TARGET"
S4_CXX_EXTRA="-fsanitize=address,undefined" "$H/run-scratch-c.sh" "$TARGET"
S4_HARNESS_LOGS=/tmp/d15-logs "$H/run-interpreters.sh" "$TARGET"
S4_HARNESS_LOGS=/tmp/d15-logs "$H/run-leaks.sh" "$TARGET"
S4_HARNESS_LOGS=/tmp/d15-logs "$H/run-negative.sh" "$TARGET"
env -u S4_CXX_EXTRA "$H/run-matrix.sh" /path/to/non-sanitized/tree
```

- 真 scratch 故障在 kf_bfly_generic 的分配处，S4_GRIDFAULT_SCRATCH_AT 指定命中；radix7→112 B、radix11→176 B。
- S4_GRIDFAULT_AT 26..31 是执行调用前模拟，不能冒充真实 scratch。准备期1..25另列。
- 不全局 export LD_PRELOAD 或 sanitizer flags；ASan 拦截器可能遮蔽 LD_PRELOAD 注入器。hit=0必须失败。
- 功能 detect_leaks=0 不证明无泄漏。泄漏 runner 独立 detect_leaks=1，4096 B正向对照预期exit23。
- LSan 历史在 ptrace沙箱中会 fatal；环境限制要记录，不当作产品缺陷或检查通过。若需不同权限执行，按平台授权流程，不擅自绕过。

## 8. 必须保留的错误与纠正记录

| 原症状/误判 | 当前解决方案或纠正 |
|---|---|
| Clone free(): invalid pointer / 材料type直传 / union清零毁半径 | 所有权隔离、按源类型复制、只对 polygon 顶点深拷贝、完整故障scope；首次补丁不是最终版本 |
| SetFrequency 扫频一直返回首频结果 | 调用 C API，失效模式/解/场缓存；单频冒烟发现不了，保留正逆序/新建对照 |
| 两层返回 R=T=0 | 路由 SolveInterior；三层零厚度对照及 Fresnel，不将错误零输出固化为基线 |
| zlahqr_ 写工作区前64 B | 空区间 ilo>ihi 与 size_t 下溢；保留 ilo==ihi 写 W。扩大工作区的假设未修复问题 |
| ztrevc_ NULL 指针伪1基偏移 | 对可选 select/vl 做 NULL 守卫；不能称 UB“无害”而忽略 |
| 修复多轮看似无效 | .so / build temp 陈旧，必须强制重链接、核实实际加载路径和哈希；时间戳不足 |
| -O1 NaN、-O3“正确” | 截止 q=0、界面LU失败状态和最终除零；不能用优化级别掩盖。FMA解释是历史假设，未经跨配置证明 |
| whole Frobenius residual ⇒ 无物理解 | 结论撤回；需逐物理列分析，局部矩阵解也不证明整个递归极限 |
| 把0/0设0后得到错误有限反射 | 方案未集成；保留明确失败，不能伪造数值 |
| 7×3 FFT scratch112 B失败 SIGSEGV | checked KISS及递归/多维状态传播；4×3只走小radix发现不了，加入7/11/49网格 |
| 注入把成功malloc的指针置NULL | 测试自身泄漏112 B；改成分配本身失败，使用LSan正向控制 |
| runner只匹配成功文本 | 保存退出码、完成/断言计数、san诊断；成功文本后exit77必须拒绝 |
| abs(v)==abs(v)“有限” | Inf仍会通过；遍历全E/H形状与实虚部math.isfinite，Lua同样验证 |
| 3000次RSS不增长⇒无泄漏 | 仅经验观察，不能证明；用分配栈、字节/次数、规模对照和检测器正向控制 |
| CFLAGS环境赋值“纯-O1” | Makefile +=仍追加-O3；使用make命令行变量覆盖，并检查实际编译命令 |
| Windows文本管道传输 | CRLF重复注入或整文件LF化；按字节传输、SHA256验证、保留原行尾 |
| SMB文件被当独立副本 | 实际写真实树；唯一Linux副本隔离，同步前备份和范围哈希核对 |
| build-instrumented rm -rf用户目录 | 已改：先验证源，拒绝任何已有目标含悬空链接，mkdir/mktemp唯一目录，失败留日志 |
| README占位目标/探针忽略退出码 | 已改：先赋真实TARGET；探针必须rc0、最终PASS、无失败或san诊断 |

## 9. 未解决问题、失败案例及优先级

### P1：FMM FFT 失败传播（下一阶段主线）

R：真实源码有10个不检查返回值的静态点：FFT2、Kottke2、Jones4、NV1、VL1。
R：`S4/fmm/fmm.h` 的函数与函数指针已有 int 返回值；`Simulation_ComputeLayerModes` 忽略 FMM 返回值，其他层模式调用点也需审计。
风险：FFT失败后使用部分结果，继续本征求解并安装残缺缓存。**这是源码确认的风险；本次没有运行一个具体FMM故障复现，也没有认定所有分支都可触发generic scratch。**

### P2：其他资源归属/分配安全

- Lua Integrate、SetExcitationExterior：现有缺陷文档记录为待办，失败点和所有权需要逐路径确认。
- Python模块初始化1760 B/2处：日志归因PyInit_S4的静态类型与异常对象；未修生命周期。不能宣称Python全部LSan结果空。
- 插值器深层OOM：唯一明确skip；RLIMIT_AS会先误伤Python分配，尚无准确逐C分配失败注入。
- GetFieldAtPoint、GetZStressTensorIntegral、Simulation_InitSolution 等局部申请未完全审计。此前16 B全进程注入崩溃栈在Simulation_InitSolution，不可冒称为网格generic scratch的新缺陷。
- 内部网格入口实际缓冲容量、ext_lua的返回码传播及其他公开入口不是全部覆盖。
- 普通realloc_aligned的偏移稳定性仅历史1024试验，无平台无关证明；sanitizer分支malloc_usable_size语义依赖实现，不做跨平台保证。此前怀疑它导致截止NaN未被证实，特定复现根本无realloc，不应按猜测重改。

### P3：数值/平台扩展

- D10精确截止点可信求解：开放研究；目前安全报错，不要求任意小量或整体伪逆作为补丁。
- MPI实际构建、FFTW、OpenMP、32位size_t、Windows构建、直接KISS in-place第三方入口未动态验收。
- 场积分/应力物理解读、图案结构独立物理基准、论文定量复现需另立任务。
- Python旧版本支持范围未系统建立：当前重点是3.14/Linux，不能把“老绑定适配”表述成已测所有Python版本。

## 10. 下一阶段执行顺序与验收标准（计划，不是已完成）

1. **先协调现场**：询问/读取FMM工作副本负责Agent的状态；不要清理或覆盖它，不启动并行真实树构建。
2. 从当前工作树完整复制到新唯一目录，含未跟踪测试；冻结源码哈希，不用HEAD导出代替。
3. 为10静态点逐个建立入口选项、网格/radix、分配/释放、缓存安装及上层返回值链。
4. 建立真实失败复现，证明命中FMM建模而非输出网格FFT。若自动选平滑FFT网格使generic scratch不可达，明确列原因，选可达计划/缓冲故障；边界模拟另列。
5. 最小修复：FFT非零立即停止消费输出；FMM统一清理并返回；层模式/解层检查状态，不缓存部分对象；C/Python/Lua可捕获报错，解除故障同对象恢复。
6. 核实既有成功层缓存不被破坏，失败对象可销毁；不只在FMM return1而让外层继续。
7. 每个可达分支至少真实失败案例，含后续阶段/部分工作已完成；完整形状与有限性、返回码、命中、恢复、资源检查。
8. 正常同标志前后数值回归；纯-O1、默认优化、相关C/Python/Lua、ASan+UBSan、独立LSan正向控制；回归D15网格矩阵和主套件，CRLF与diff --check。
9. runner必须拒绝成功文本后exit77、超时、san错误、未命中、空遍历假通过。
10. 完成独立候选补丁与证据后停止，**新的同步/提交/推送不能沿用D15旧授权**。

不会以“所有测试通过”承诺Linux永不失败。不得通过过滤NaN、放宽容差、expectedFailure、进程exit/abort掩盖目标缺陷。文档修正与未来提交拆分可另行规划，本次未执行。

## 11. 路径、交付物与并行工作注意

| 用途 | 路径/状态 |
|---|---|
| 真实工作树 | `/srv/nvme/projects/S4-Stanford-Stratified-Structure-Solver` |
| D15冻结候选 | `/home/jackal/sandbox/s4-gridalloc-20260930T113900Z` |
| D15补丁 | `/tmp/s4-d15-patches/`，01..05 |
| D15初期/执行期/收尾检查点 | `/tmp/s4-gridalloc-CHECKPOINT.md`、`/tmp/s4-d15-CHECKPOINT.md`、`/tmp/s4-d15-accept-CHECKPOINT.md` |
| 十文件集成副本 | `/home/jackal/s4-d15-integration-20260930T131205Z` |
| 十文件原始备份 | `/home/jackal/s4-d15-real-backup-20260930T131245Z`：files/、SHA256SUMS.before、attrs.txt、git-state.txt、ten-files.tar.gz、RESTORE.md |
| 最终集成验收 | `/home/jackal/s4-d15-acceptance5/final-accept.log`；san-final/、d-logs/等 |
| 最终插桩树 | `/tmp/d15-instr-final-20260930T131617Z-3043850` |
| 独立复核 | `/tmp/s4-d15-review-r3/`；较早临时复核目录可能清理或过期 |
| 独立装置 | `/home/jackal/s4-d15-harness/`；清单 `/home/jackal/s4-d15-harness.sha256`，33文件 |
| FMM工作指针 | `/tmp/s4-fmm-dir.txt` 指向 `/home/jackal/s4-fmm-20260930T132345Z` |
| FMM临时记录 | `/tmp/fmm-build.log`、`/tmp/fmm-smoke.py`、`/tmp/fmm-smoke2.py`、`/tmp/fmm-smoke3.py` |

FMM目录本次确认存在；S4.cpp及五个FMM文件与真实树不同；顶层未找到正式md/log/txt交付说明。构建日志有编译/链接输出，但没有完整冻结源码关联、退出状态和验收矩阵，**不能认定候选完成**。草稿smoke脚本含与当前API不匹配的调用或分量索引；不要盲目执行或以文件存在当作有效测试。
是否当前仍有任务执行、该副本最新负责人、候选正确性均缺信息。本次不查询或终止进程，不修改该副本。所有/tmp路径是易失研究产物，不是永久交付存储。

## 12. 文档已知问题与缺失信息

- DEFECTS.md 仍有历史段落矛盾：D4标题fixed但正文叙述旧的未实现状态；D12摘要仍说Lua open而D13已记录fixed；D15部分旧段落计数9或curdim>=3需结合round3读。
- testing/s4test/README.md仍留122项旧状态；不要作为当前数量。
- Clone测试docstring提solution copy，但历史曾撤回解状态深拷贝；按当前源码核实，不用docstring推断实现。
- 所有修复的逐提交归属尚未建立：多数是同一未提交工作树；本文件不伪造提交链。
- 外部论文原始数据、预期误差预算、特定复现目标缺失。
- 当前远端是否含HEAD、SSH/Git认证、推送状态、跨Python版本/平台矩阵未核实。
- 当前全进程/所有调用路径泄漏安全、allocator理论保证、FMM候选完整验收缺失。
- 全文快照不是文件系统原子事务；若其他Agent同时写文件，继任需重新核对相关哈希。

## 13. 新 Agent 首次读取后应做什么

本节是后续建议，不授权立即启动测试。

1. 读本文、Git差异和当前任务约束；确认没有并行Agent在改同一文件。
2. 重新只读核对分支/HEAD/暂存区及FMM现场；理解19修改+41未跟踪都是有价值成果。
3. 不执行全仓库clean/reset/stash；不把真实树当实验副本；不把HEAD当集成后源码。
4. 先问清任务范围：继续FMM候选、整理提交，或论文复现是不同任务。
5. 需要构建时使用独立唯一目录，清理只限确认所属的构建产物；禁止 rm -rf 用户传入既有目标。
6. 当运行获授权后，再采用第10节验收计划，准确记录源码与二进制哈希、通过/跳过、实际覆盖。

---

## 附录 A：生成本文前的 Git 快照（R）

```text
 M Makefile.common
 M S4/Interpolator.c
 M S4/RNP/Eigensystems.cpp
 M S4/S4.cpp
 M S4/S4.h
 M S4/fmm/fft_iface.cpp
 M S4/fmm/fft_iface.h
 M S4/kiss_fft/kiss_fft.c
 M S4/kiss_fft/kiss_fft.h
 M S4/kiss_fft/tools/kiss_fftnd.c
 M S4/kiss_fft/tools/kiss_fftnd.h
 M S4/main_lua.c
 M S4/main_python.c
 M S4/numalloc.c
 M S4/rcwa.cpp
 M S4/rcwa.h
 M testing/numdiff
 M testing/runtests.sh
 M testing/testcases.txt
?? examples/0d/fabry_perot/fresnel.txt
?? examples/2d/Fan_PRB_65_2002/fig12.txt
?? examples/simple/simple.txt
?? testing/s4test/
```

暂存区为空（`git diff --cached --stat` 无输出）。添加本文后预计新增 `?? S4_HANDOFF.md`，未提交成果仍保持不变。

### A.1 已跟踪差异统计（不含未跟踪测试）

```text
 Makefile.common                |  61 ++++
 S4/Interpolator.c              | 182 ++++++++---
 S4/RNP/Eigensystems.cpp        |  58 +++-
 S4/S4.cpp                      | 688 +++++++++++++++++++++++++++++++++++++----
 S4/S4.h                        |  28 ++
 S4/fmm/fft_iface.cpp           |  26 +-
 S4/fmm/fft_iface.h             |   5 +-
 S4/kiss_fft/kiss_fft.c         |  53 +++-
 S4/kiss_fft/kiss_fft.h         |   8 +
 S4/kiss_fft/tools/kiss_fftnd.c |  19 +-
 S4/kiss_fft/tools/kiss_fftnd.h |   3 +
 S4/main_lua.c                  | 567 +++++++++++++++++++++++----------
 S4/main_python.c               | 372 ++++++++++++++--------
 S4/numalloc.c                  |  49 +++
 S4/rcwa.cpp                    | 156 +++++++---
 S4/rcwa.h                      |   7 +-
 testing/numdiff                | 126 +++++---
 testing/runtests.sh            | 104 +++++--
 testing/testcases.txt          |  13 +-
 19 files changed, 1973 insertions(+), 552 deletions(-)
```

### A.2 已跟踪修改文件快照哈希

| 文件 | SHA256 |
|---|---|
| `Makefile.common` | `6cd117a2d9868c1d5c25ab30cd71ce0036e2163e88531a251862602ba79af531` |
| `S4/Interpolator.c` | `79d0e389ac3104bb4eea4feacffd266745fb8e7fc5bd7c8d893249d266cf7d27` |
| `S4/RNP/Eigensystems.cpp` | `76db4bb77ea4febe03b3aae892936a0bda889d97ece6b3157a3005c201cc99de` |
| `S4/S4.cpp` | `1e9ff5359921d8074325dbfe07684d12d0e982bbd464f531e765ce7b4ed0c782` |
| `S4/S4.h` | `402ac739dcdf9c6c859e121b1cc6eee9c9771cc49cba3d145beac4d92965bfce` |
| `S4/fmm/fft_iface.cpp` | `5372eb8474d0439d2f084e96f2692c527e20bb13f9071daa3aaf54784c9c1a27` |
| `S4/fmm/fft_iface.h` | `dc4092571a11aaf34467f145bc3c5723ff8b58cfcadfe0656ded71a1e7c1da0c` |
| `S4/kiss_fft/kiss_fft.c` | `abab7f3c332f5be37b749f3532867060a9541047bb3dac964219f5eca12f12ab` |
| `S4/kiss_fft/kiss_fft.h` | `d0af626278fa69afd09e31ae91478f8a00924b6fd0041e8c29c945633e85eed7` |
| `S4/kiss_fft/tools/kiss_fftnd.c` | `10c587f111977d6fc80ce62097d8a06505fd72d4759bc4d54db21268f34d85fa` |
| `S4/kiss_fft/tools/kiss_fftnd.h` | `1b4ecb062aa0bd26afe09087b5c58c61680af8e2b48424bd5901984dd4cbbd27` |
| `S4/main_lua.c` | `39ae3cf1d969fac85bac4065b7ab5a2d5df7ce76bc3f68768640babcde3e5c70` |
| `S4/main_python.c` | `cf564682da822e8cbf3122adc8afe9859659f8113407284e7702ab6de69827cd` |
| `S4/numalloc.c` | `d70db3ee2286535c7782530c0ca5d748928ff0a7ef5df10810e76c2b31a3e83e` |
| `S4/rcwa.cpp` | `44bbf15ae1f931834f87f1d4450e227099145296fe238e8010c4a8bfb3f190dd` |
| `S4/rcwa.h` | `fd30fafff1fe01ee0aaeb295c158b2c64c343772ba1eae6b48bb376fa82a9ad6` |
| `testing/numdiff` | `62af9676291d45e3e3b73d845e0cc559a9cd6acb585af1b639a0c186064e540e` |
| `testing/runtests.sh` | `d871c428c97c9770969bd270bc704f81e53f3adb505eee6f2544d823c0c79aa4` |
| `testing/testcases.txt` | `4fdf9f309eb4d9b1a9f034f0ac63aaa2ecd3ef1e3f3e3ab55817c812550ec207` |

### A.3 未跟踪成果完整清单（生成前）

```text
examples/0d/fabry_perot/fresnel.txt
examples/2d/Fan_PRB_65_2002/fig12.txt
examples/simple/simple.txt
testing/s4test/DEFECTS.md
testing/s4test/README.md
testing/s4test/analytic.py
testing/s4test/capi_field_plane_driver.cpp
testing/s4test/clone_fault_probe.py
testing/s4test/clone_isolation.py
testing/s4test/exterior_excitation_isolation.py
testing/s4test/gen_regression_data.py
testing/s4test/isolation_cases.py
testing/s4test/lua_frontend.py
testing/s4test/mirror_fig12.lua
testing/s4test/mirror_fig12.py
testing/s4test/probe_two_layer.lua
testing/s4test/regression_data.json
testing/s4test/s4test_common.py
testing/s4test/selftest_analytic.py
testing/s4test/selftest_suite.py
testing/s4test/test_analytic_reference.py
testing/s4test/test_capi_field_plane.py
testing/s4test/test_clone_equivalence.py
testing/s4test/test_clone_fault_injection.py
testing/s4test/test_cutoff_safety.py
testing/s4test/test_eigensolver_workspace.py
testing/s4test/test_exterior_excitation.py
testing/s4test/test_grid_output_safety.py
testing/s4test/test_interpolator.lua
testing/s4test/test_interpolator.py
testing/s4test/test_lua_api_negative.py
testing/s4test/test_lua_field_plane.py
testing/s4test/test_lua_python_cross.py
testing/s4test/test_lua_regression_negative.sh
testing/s4test/test_python_api.py
testing/s4test/test_regression_baseline.py
testing/s4test/test_structures.py
testing/s4test/test_sweep_frequency.py
testing/s4test/test_two_layer_acceptance.py
testing/s4test/test_two_layer_interface.py
testing/s4test/test_zlahqr_direct.py
```

## 附录 B：当前二进制与 D15 冻结校验（R）

只读取文件字节，不加载扩展。历史最终默认优化产物供对照；哈希相同支持产物一致，不证明未来改源码后仍有效。

| 路径 | SHA256 |
|---|---|
| `build/libS4.a` | `879a46069a1b792feaa2730e9e04c7e408c2664f58f365bc4388749dbc3f2c0e` |
| `build/S4` | `19daaa776dc740d4f26540f5faef1bebf636c79b3045bd8bd2ca902132d44432` |
| `S4.cpython-314-x86_64-linux-gnu.so` | `00c960a9b8fd21cf6b35c6b175ad069cc0d2a680cb8dead05ff0f50730c780af` |
| `/tmp/s4-d15-patches/01-getfieldongrid-allocation-safety.patch` | `91e8e298e19a7751550b651c479b7ebeebca6ce5b7d6308599c14f93425dec09` |
| `/tmp/s4-d15-patches/02-fft-plan-ownership-and-exec-status.patch` | `c068dd69d6f26e9fcec1fb957bb36806f237cffd637adfe268f8c4292648d450` |
| `/tmp/s4-d15-patches/03-grid-callers-propagate.patch` | `f84645a058467ec62018edb5d593986d15999dffec6e42d61a252e7e4dcee499` |
| `/tmp/s4-d15-patches/04-kiss-fft-execution-failure.patch` | `08b97ef8090072a5710b10f2829ea4f71dc291392b2c161e0aba0a13f1f7ad43` |
| `/tmp/s4-d15-patches/05-docs-d15.patch` | `e6617f72cb51b999472f064827909465bdeed73f57456ceba36b94f1678b1e2b` |
| `/home/jackal/s4-d15-harness.sha256` | `21196e5800a4966bfa9e76eb285699dc132b9920241faf427da9088bf3d020c2` |

### B.1 D15十文件与冻结候选逐字节比较

| 文件 | 当前SHA256 | 与候选比较 |
|---|---|---|
| `S4/rcwa.cpp` | `44bbf15ae1f931834f87f1d4450e227099145296fe238e8010c4a8bfb3f190dd` | MATCH |
| `S4/rcwa.h` | `fd30fafff1fe01ee0aaeb295c158b2c64c343772ba1eae6b48bb376fa82a9ad6` | MATCH |
| `S4/S4.cpp` | `1e9ff5359921d8074325dbfe07684d12d0e982bbd464f531e765ce7b4ed0c782` | MATCH |
| `S4/fmm/fft_iface.cpp` | `5372eb8474d0439d2f084e96f2692c527e20bb13f9071daa3aaf54784c9c1a27` | MATCH |
| `S4/fmm/fft_iface.h` | `dc4092571a11aaf34467f145bc3c5723ff8b58cfcadfe0656ded71a1e7c1da0c` | MATCH |
| `S4/kiss_fft/kiss_fft.c` | `abab7f3c332f5be37b749f3532867060a9541047bb3dac964219f5eca12f12ab` | MATCH |
| `S4/kiss_fft/kiss_fft.h` | `d0af626278fa69afd09e31ae91478f8a00924b6fd0041e8c29c945633e85eed7` | MATCH |
| `S4/kiss_fft/tools/kiss_fftnd.c` | `10c587f111977d6fc80ce62097d8a06505fd72d4759bc4d54db21268f34d85fa` | MATCH |
| `S4/kiss_fft/tools/kiss_fftnd.h` | `1b4ecb062aa0bd26afe09087b5c58c61680af8e2b48424bd5901984dd4cbbd27` | MATCH |
| `testing/s4test/DEFECTS.md` | `8d0d3f3ea5af9c3e6687fe191118329c9e63a8533a57144ca3ad849cb91fb3a4` | MATCH |
