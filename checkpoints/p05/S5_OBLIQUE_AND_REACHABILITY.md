# P05 / S5：C 的斜入射检验与 B 的可达性补全（证据收集最后一轮）

> 基线：`5b72793051eb705f0e9b2e5398e1a5f0484da0cb`（Master）
> 门禁起点：`4cb0793`（没有已跟踪改动，没有暂存改动，`checkpoints/p05/` 之外没有未跟踪文件）
> 来源标注：**实测** = 本轮运行或读取的原始输出；**代码阅读** = 只读源码（行号经 grep 核对）；**推断** = 由实测加代码阅读得出，未直接验证；**未确定** = 证据不足。
> 证据：`checkpoints/p05/evidence/s5/`（被 `.git/info/exclude` 忽略，**未提交**）；清单 `EVIDENCE.sha256`；归档见第 8 节。

---

## 0. 结论摘要

- **C（注入错误是否传播到输出）：保持开放，但问题已被精确化。** 在斜入射 θ=30°（φ=0 与 φ=45°），NB=1，FFT 路径，**Python-Option `PolarizationBasis='Default'` bei `PolarizationDecomposition=True`（VL-Zweig, belegt im Quellcode `S4.cpp:2387–2394` und zur Laufzeit gezählt: VL=1, NV=0, Jones=0; siehe Abschnitt 1.2）**下：手动把 `Epsilon_inv[0]` 改为 1，与真实 scratch1、scratch2 注入，**第一次调用的 144 个 E/H 与对照均无超出舍入的变化**。这属于 S5 所定义的结论 (c)。但同一配置下，**特征值层面确实敏感**：`Epsilon_inv` 的改变使本征值 `q[1]` 从 8.7159 变为 8.0226（φ=0），并使本征向量 `phi` 在 φ=45° 时发生变化（`phi[0]` 从 1 变为 0.7071）。因此 C 的开放问题应表述为：**特征值层面的变化为什么没有进入 E/H**，而不是笼统的"传播是否发生"。
- **B（执行期分配失败的危险等级）：条件可达；输出层面在所测配置下未观察到伤害。** 可达性在 S5 中被扩大：`kf_bfly_generic` 的命中不只出现在 square 晶格的 NB=1–4（S4 的结论），还出现在 hex 的 NB=1–4、rect 的 NB=1–4（有 72 次命中的 NB=3、4 也在其中）。但**"可达"不等于"有害"**：S5 没有对这些新增的可达配置测量输出是否改变。
- **T20 的 scratch2 解释被否定**：S5 工作过程中的初步推断（本报告内部，S4 报告中并无此假设）认为 scratch2 落在 `plans[0]`（第 212 行，`Epsilon2` 块），栈显示它实际落在 `fmm_FFT.cpp:183`（`plans[4]`，计算 `Epsilon_inv` 的那次）。因此 scratch1 与 scratch2 命中同一次 FFT 执行的两个窗口内分配，两者的中间量结果不同（scratch1：`solve_info=1`、`Epsilon_inv=1`；scratch2：`solve_info=0`、`Epsilon_inv=0.4591`）。**这一差异的机制未解释**，列入残余风险。
- **T21 的重要新事实：偏振基改变 `kf_bfly_generic` 的命中次数。** 在 `n_G` 相同（hex NB=1–4：n_G=1；rect NB=3、4：n_G=3）且两个偏振基都完整求解的 6 个组合上，VL 与 Normal 的命中次数不同：rect 72 对 40，hex 18 对 10。S4 与本轮早先的"求解中途失败造成计数差异"的解释**被推翻**（第 6 节第 2 条）。
- **T22 的重合：** Option `PolarizationBasis='Default'` 下 54 个组合中，命中次数 >0 的有 12 个；其中 6 个失败，6 个成功。命中**不是**失败的充分条件。Die Trefferzahl 18 erscheint sowohl bei erfolgreichem (hex NB=1) als auch bei fehlgeschlagenem Lauf (square NB=1), sie hängt also nicht vom Erfolg ab (V-E, geprüft).
- **Kottke 路径（`SubpixelSmoothing=True`）**: Bei NB=1–4 mit VL-Zweig (Option `Default`) erfolgreich (n_G=1), Trefferzahl 0. Die O-1-Messung in S4 fand auf der ClosedForm-Route statt; hier wurde nur die Kottke-Route mit der FFT-Route verglichen. Eine Aussage "O-1 tritt auf Kottke nicht auf" ist deshalb nicht belegt und wird nicht gemacht.

---

## 1. 门禁、回归与环境

- 门禁：HEAD 为 `4cb0793`，没有已跟踪改动，没有暂存改动，`checkpoints/p05/` 之外没有未跟踪文件（主脑追认的门禁定义）。
- 驱动副本的 kdir 参数化是唯一的新增改动（第 5 节第 1 条），以 diff 存证：`s5/drv/driver-s5-vs-history.diff`（4 个 hunk，其中 S5 的 kdir 替换是其中一个）。
- 注入器副本：计数输出只含 `n`、`arm`、`seq`（不读返回地址，S4 第 5 节第 1 条）。
- **回归（步骤 1，T19 的 22 个用例）：0 差异。** 未设置 `S4FMM_THETA`、`S4FMM_PHI`、`S4FMM_DUMP`、`S4FMM_DUMP1`、`S4FMM_MALLOC_LOG` 时，22 个用例在 `rc`、`RC first`、`RC retry`、`HIT`、`finite_FAILED` 上与 S1B 索引逐项一致。比对器经灵敏度检验（人为改一个 rc 即报告差异）。证据：`s5/t19/regression.txt`。
- 构建：O0（`-O0 -g -fno-inline -fno-omit-frame-pointer`，经 `CFLAGS/CXXFLAGS` 覆盖），每个作业内重建（`/tmp` 在工具调用之间被清空，本轮至少 6 次）。

### 1.1 kdir 参数化的几何（代码阅读 + 算术，已核对）

- 入射方向：`kdir = (sinθ·cosφ, sinθ·sinφ, cosθ)`；偏振参考：`udir = (−sinφ, cosφ, 0)`。
- 正交性：`kdir·udir = 0`（三组算术核对，精确为 0），所以库的正交化（`S4.cpp:4130–4131`）不改变 `udir`。
- 面内波矢：`S->k = (sinθ cosφ, sinθ sinφ)`（空气，`root_eps=1`），由 `S4.cpp:4146` 的 `k_new = root_eps·kn` 给出。
- 实测（`s5/t20/geometry-index.txt`，gdb 在 `S4.cpp:4302` 只读）：

| 配置 | `S->k` | `n_G` | `G` | `kx[0]`, `ky[0]` |
|---|---|---|---|---|
| θ=0 | 0, 0 | 1 | (0,0) | 0, 0 |
| θ=30°, φ=0 | 0.5, 0 | 1 | (0,0) | **3.13845, 0** |
| θ=30°, φ=45° | 0.35355, 0.35355 | 1 | (0,0) | **2.21922, 2.21922** |

斜入射时 `kx`、`ky` 非零，`Epsilon_inv` 可以进入 `kp`，前提成立。

---

### 1.2 Zweigzuordnung der Standardoption (Laufzeitnachweis vorhanden)

- **Quellcode** (Lesezugriff, `S4/S4.cpp:2375–2394` und `S4/main_python.c:1799–1816`): Bei `PolarizationDecomposition=True` setzt die Option `PolarizationBasis='Default'` beide Basisflags auf 0 und `use_polarization_basis=1`. Die Verzweigung in `S4.cpp:2387–2394` wählt dann den VL-Zweig (`FMMGetEpsilon_PolBasisVL`), weil weder Jones noch Normal gesetzt sind.
- **Laufzeitnachweis** (`s5/t21/branch-VL-count.gdb.txt`, `s5/gdb/t21-branch-count.gdb`): Für die Konfiguration quadratisch, NB=1, FFT, `PolarizationBasis='Default'`, `PolarizationDecomposition=True` zählen die Haltepunkte **VL = 1, NV = 0, Jones = 0**. Der Lauf endet regulär (gdb rc 0). Der Eintritt in `FMMGetEpsilon_PolBasisVL` ist damit zur Laufzeit belegt.
- **Abgleich mit der Matrix**: Dieselbe Zelle hat in der Matrix denselben Status `EXCEPTION` mit identischer Fehlermeldung (`eigensystem could not be solved`), siehe `s5/t21/matrix-index.txt`. Die Matrix-Transkripte enthalten nur Zählzeilen; der Zweig wurde deshalb für diese eine Zelle separat gezählt, nicht für alle 54.
- **Verfahrensnotiz**: Zwei frühere Versuche sind gescheitert und bleiben als Dateien erhalten. `s5/t21/branch-VL-check.gdb.txt` (Haltepunkte ohne Fortsetzung: der Lauf hielt am ersten Treffer, deshalb fehlte die Statuszeile) und der Gate-Abbruch von bash-411 (verfolgte Datei `S1_evidence_digest.txt` war geändert). Beide Fehler sind behoben; der belegte Stand ist die Zählung mit Fortsetzung.

## 2. T20：斜入射 + NB=1 的敏感性对照

### 2.1 配置

NB=1，`DiscretizedEpsilon=True`（FFT 路径），**VL 基**，θ=30°，φ∈{0°, 45°}，f=0.999（驱动固定频率）。四组：

- **A**：对照，无注入，无改值。
- **B**：手动写入，在 `S4.cpp:2375`（`FMMGetEpsilon_FFT` 返回之后）把 `pB->Epsilon_inv[0]` 设为 1（两段 `double` 布局写入，S4 T16 已验证）。
- **C**：真实注入 scratch1（`S4FMM_INJECT=scratch S4FMM_NTH=1`）。
- **D**：真实注入 scratch2（`S4FMM_INJECT=scratch S4FMM_NTH=2`）。

### 2.2 E/H 比较（第一次调用，144 个元素）

判定阈值在看到数据之前确定为 `max|diff| = 1e-12`：它远大于双精度舍入（约 2.2e-16），远小于任何有意义的物理量。

| 配置 | 比较 | 相同元素 | 不同元素 | 最大绝对差 | 类别 | 证据 |
|---|---|---|---|---|---|---|
| φ=0 | A vs B（手动写入） | 144 | 0 | 0 | **逐位相同** | `s5/t20/A-phi0.eh`、`B-phi0.eh` |
| φ=0 | A vs C（scratch1） | 144 | 0 | 0 | **逐位相同** | `s5/t20/C-phi0.eh` |
| φ=0 | A vs D（scratch2） | 144 | 0 | 0 | **逐位相同** | `s5/t20/D-phi0.eh` |
| φ=45° | A vs B（手动写入） | 0 | 144 | 4.44e-16 | 舍入级 | `s5/t20/B-phi45.eh` |
| φ=45° | A vs C（scratch1） | 0 | 144 | 4.44e-16 | 舍入级 | `s5/t20/C-phi45.eh` |
| φ=45° | A vs D（scratch2） | 144 | 0 | 0 | **逐位相同** | `s5/t20/D-phi45.eh` |

- 最大**相对**差（φ=45°）为 14.07，来自分母接近零的元素，没有物理意义，本报告只引用绝对差。
- 可重放性：A 组在两次独立运行（`s5/t20/A-phi*.eh` 与 `s5/t20q/A-phi*.eh`）中**字节级相同**，因此 φ=45° 的舍入级差异不是运行间的噪声。
- **舍入而非系统偏移（实测，符号与均值检验）**：φ=45° 下，B 与 A 的 144 个差值中，正 60 个、负 84 个（无单一方向）；中位数 `|diff|=1.11e-16`，范围 `2.8e-17` 至 `4.4e-16`（双精度最后一位附近）；均值 `−3.5e-17`，均值/标准差 `= −0.18`（远小于 1，无系统偏移）。C 与 A 的差值分布**与 B 完全相同**（同样的正负个数、同样的均值与标准差），与 B、C 在特征值层面等价（第 2.3 节）一致。
- 注入状态（`s5/t20/index.txt`、`s5/t20inj/`）：C 与 D 的 `RC first=0`、`RC retry=0`，`HIT=1`（注入命中，被静默吞掉）。

### 2.3 中间量（运行证据）

| 量 | φ=0：A | φ=0：B | φ=0：C（注入后） | φ=45°：A | φ=45°：B | φ=45°：C（注入后） |
|---|---|---|---|---|---|---|
| 求解输入 `Epsilon_inv[0]`（`rcwa.cpp:823`） | 0.4591 | **1** | — | 0.4591 | **1** | — |
| `solve_info`（`fmm_FFT.cpp:207`） | — | — | **1** | — | — | **1** |
| `Epsilon_inv[0]`（`fmm_FFT.cpp:207`） | — | — | **1** | — | — | **1** |
| `eigen_info` | 0 | 0 | 0 | 0 | 0 | 0 |
| `kp[0]`, `kp[3]`（求解后） | 39.40, 34.88 | 39.40, **29.55** | 39.40, 29.55 | 37.14, 37.14 | 34.47, 34.47 | 34.47, 34.47 |
| `kp[1]`, `kp[2]`（求解后） | 0, 0 | 0, 0 | 0, 0 | 2.26, 2.26 | **4.92, 4.92** | 4.92, 4.92 |
| `q[0]`, `q[1]`（求解后） | 8.7159, **8.7159** | 8.7159, **8.0226** | 8.7159, 8.0226 | 8.7159, 8.7159 | 8.7159, **8.0226** | 8.7159, 8.0226 |
| `phi[0]`, `phi[1]`（求解后） | 1, 0 | 1, 0 | 1, 0 | 1, 0 | **0.7071, 0.7071** | 0.7071, 0.7071 |

- 手动写入（B）与真实注入（C）的求解后量（`kp`、`q`、`phi`、`eigen_info`）**逐项相同**（两个几何）：真实注入造成的值与手动值在特征值层面等价，没有被后续覆盖。
- 证据：`s5/t20q/A-phi*.gdb.txt`、`s5/t20q/B-phi*.gdb.txt`、`s5/t20inj/C-eig-phi*.gdb.txt`、`s5/t20/C-state-phi*.gdb.txt`（注：C-state 读数由 T20 第一次运行写入 `s5/t20/`，不在 `t20inj/`）。

### 2.4 scratch2 的中间量与栈（运行证据）

- D 组（scratch2，`fmm_FFT.cpp:207`）：`solve_info=0`，`Epsilon_inv[0]=0.4591`（与对照相同）。证据：`s5/t20inj/D-state-phi*.gdb.txt`。
- **栈（实测，`s5/t20inj/scratch2-stack-phi*.gdb.txt`，两个几何一致）**：`__wrap_malloc` ← `kf_bfly_generic`（`kiss_fft.c:216`）← `kf_work` ← `kiss_fft_stride_checked` ← `kiss_fftnd_checked` ← `fft_plan_exec` ← `__wrap__fft_plan_exec` ← **`FMMGetEpsilon_FFT`（`fmm_FFT.cpp:183`）**。
- `fmm_FFT.cpp:183` 是 `fft_plan_exec(plans[4])`（计算 `Epsilon_inv`），不是循环中的 `plans[w]`（第 212 行）。**这否定了 S4/S5 初步推断的"scratch2 落在 `Epsilon2` 块"。**
- 因此 scratch1 与 scratch2 命中**同一次** `plans[4]` 的两个窗口内分配（它们分别是这次执行中 `kiss_fftnd` 的两次 `kf_bfly_generic`）。两者结果不同：scratch1 导致 `solve_info=1`、`Epsilon_inv=1`；scratch2 导致 `solve_info=0`、`Epsilon_inv` 不变。**这一差异的机制未解释**（第 7 节残余风险第 1 条）。

### 2.5 结论 (c)，适用配置

按 S5 的三类判定：

- (a) 手动改值后输出变，且真实注入后输出也变：**不满足**（两者都无超出舍入的变化）。
- (b) 手动改值后输出变，但真实注入后输出不变：**不满足**（手动改值后输出也不变）。
- (c) 手动改值后输出仍不变：**满足**。

**结论 (c) 的适用配置**：斜入射 θ=30°，φ∈{0°, 45°}，NB=1，**FFT 路径**（`DiscretizedEpsilon=True`，`SubpixelSmoothing=False`），**VL 基**，驱动频率 f=0.999，驱动固定几何（圆盘 r=0.25，ε=4，板厚 0.5）。**不适用于**：Normal 基、Jones 基、Kottke 路径、NB≥2、其它 θ/φ。

### 2.6 对 C 的精确表述

- **特征值层面敏感**（φ=0：`q[1]` 变化；φ=45°：`phi` 变化）。这已实测。
- **E/H 层面在所测配置下不敏感**。这已实测。
- **二者之间的环节未解释**：`GetFieldOnGrid` 如何使用 `q`、`phi`、`kp`、`Epsilon_inv` 以致 `q[1]` 的变化不进入 E/H，**是残余风险**（第 7 节第 2 条）。这是机制研究，不属于证据收集。

---

## 3. T21：B 的可达性补全（不用注入，不改源码）

### 3.1 方法（已验证）

- 对象：Python 公共 API（`S4.New`、`SetOptions`、`SetMaterial`、`AddLayer`、`SetRegionCircle`、`SetExcitationPlanewave`、`SetFrequency`、`GetAmplitudes`），O0 构建，在 gdb 下运行。
- 计数：`break kf_bfly_generic` + `commands … silent … continue`，**不停下、不改源码、不依赖注入器**。
- 前提（已验证，`s5/t21/probe-run.gdb.txt`）：`kf_bfly_generic` 是 `static`（`t` 符号），断点在 `run` 之前为 `<PENDING>`，在扩展加载后自动解析并在真实求解中命中（`Breakpoint 1, kf_bfly_generic … p=1`）。
- 固定几何：玻璃圆盘 r=0.25、ε=4，空气中板厚 0.5，正入射，f=0.427。只变晶格与 NB。
- 每个组合一次独立的 gdb 运行；结果 JSON 与计数来自同一 transcript（已核对）。

### 3.2 矩阵：晶格 × NB × 路径（VL 基，54 个组合，全部完成）

计数：`hits` = `kf_bfly_generic` 命中次数（`KFBFLY_HIT`）。`n_G` 与状态来自同一 transcript 的 JSON。

| 晶格 | NB | 路径 | VL：状态 | n_G | 命中 | Normal：命中 / 状态 / n_G |
|---|---|---|---|---|---|---|
| square | 1 | FFT | **EXCEPTION** | — | 18 | 10 / ok / 1 |
| square | 1 | Kottke | ok | 1 | 0 | — |
| square | 2 | FFT | **EXCEPTION** | — | 18 | 10 / ok / 1 |
| square | 2 | Kottke | ok | 1 | 0 | — |
| square | 3 | FFT | **EXCEPTION** | — | 18 | 10 / ok / 1 |
| square | 3 | Kottke | ok | 1 | 0 | — |
| square | 4 | FFT | **EXCEPTION** | — | 18 | 10 / ok / 1 |
| square | 4 | Kottke | ok | 1 | 0 | — |
| square | 5 | FFT | ok | 5 | 0 | — |
| square | 5 | Kottke | ok | 5 | 0 | — |
| square | 9 | FFT | ok | 9 | 0 | — |
| square | 9 | Kottke | ok | 9 | 0 | — |
| square | 12 | FFT | ok | 9 | 0 | — |
| square | 12 | Kottke | ok | 9 | 0 | — |
| square | 16 | FFT | ok | 13 | 0 | — |
| square | 16 | Kottke | ok | 13 | 0 | — |
| square | 25 | FFT | ok | 25 | 0 | — |
| square | 25 | Kottke | ok | 25 | 0 | — |
| rect | 1 | FFT | **EXCEPTION** | — | 18 | 10 / ok / 1 |
| rect | 1 | Kottke | ok | 1 | 0 | — |
| rect | 2 | FFT | **EXCEPTION** | — | 18 | 10 / ok / 1 |
| rect | 2 | Kottke | ok | 1 | 0 | — |
| rect | 3 | FFT | ok | 3 | **72** | 40 / ok / 3 |
| rect | 3 | Kottke | ok | 3 | 0 | — |
| rect | 4 | FFT | ok | 3 | **72** | 40 / ok / 3 |
| rect | 4 | Kottke | ok | 3 | 0 | — |
| rect | 5 | FFT | ok | 5 | 0 | — |
| rect | 5 | Kottke | ok | 5 | 0 | — |
| rect | 9 | FFT | ok | 9 | 0 | — |
| rect | 9 | Kottke | ok | 9 | 0 | — |
| rect | 12 | FFT | ok | 11 | 0 | — |
| rect | 12 | Kottke | ok | 11 | 0 | — |
| rect | 16 | FFT | ok | 15 | 0 | — |
| rect | 16 | Kottke | ok | 15 | 0 | — |
| rect | 25 | FFT | ok | 23 | 0 | — |
| rect | 25 | Kottke | ok | 23 | 0 | — |
| hex | 1 | FFT | ok | 1 | **18** | 10 / ok / 1 |
| hex | 1 | Kottke | ok | 1 | 0 | — |
| hex | 2 | FFT | ok | 1 | **18** | 10 / ok / 1 |
| hex | 2 | Kottke | ok | 1 | 0 | — |
| hex | 3 | FFT | ok | 1 | **18** | 10 / ok / 1 |
| hex | 3 | Kottke | ok | 1 | 0 | — |
| hex | 4 | FFT | ok | 1 | **18** | 10 / ok / 1 |
| hex | 4 | Kottke | ok | 1 | 0 | — |
| hex | 5 | FFT | ok | 5 | 0 | — |
| hex | 5 | Kottke | ok | 5 | 0 | — |
| hex | 9 | FFT | ok | 9 | 0 | — |
| hex | 9 | Kottke | ok | 9 | 0 | — |
| hex | 12 | FFT | ok | 9 | 0 | — |
| hex | 12 | Kottke | ok | 9 | 0 | — |
| hex | 16 | FFT | ok | 13 | 0 | — |
| hex | 16 | Kottke | ok | 13 | 0 | — |
| hex | 25 | FFT | ok | 23 | 0 | — |
| hex | 25 | Kottke | ok | 23 | 0 | — |

- 证据：`s5/t21/matrix-index.txt`（54 行，与 54 个 transcript 的 status 与 `n_G` 逐项一致，0 不一致），54 个 transcript 的命名规则为 `s5/t21/<晶格>-nb<NB>-<路径>-VL.gdb.txt`（晶格 ∈ {square, rect, hex}；路径 ∈ {fft, kottke}），例如 `s5/t21/hex-nb1-fft-VL.gdb.txt`（已展开核对存在）。
- **Kottke 路径的命中全部为 0**（27 个组合）。
- **命中的 `(p, m)` 全部为 `(1, 1)`**（所有 VL 与 Normal 的 transcript 核对，`s5/t21/*.gdb.txt` 中 `KFBFLY_HIT` 行的分布）。即命中全部来自退化的 `p=1` 调用。
- VL 失败的 6 个组合中，Normal 基全部成功（见 3.3）。

### 3.3 VL 失败的 Normal 重跑（规则：不留空缺）

按规则，VL 失败的组合改用 Normal 基重跑（列表从索引读取，不手工输入）：

| 组合 | Normal：状态 | n_G | 命中 | 证据 |
|---|---|---|---|---|
| square NB=1, FFT | ok | 1 | 10 | `s5/t21/square-nb1-fft-Normal.gdb.txt` |
| square NB=2, FFT | ok | 1 | 10 | `s5/t21/square-nb2-fft-Normal.gdb.txt` |
| square NB=3, FFT | ok | 1 | 10 | `s5/t21/square-nb3-fft-Normal.gdb.txt` |
| square NB=4, FFT | ok | 1 | 10 | `s5/t21/square-nb4-fft-Normal.gdb.txt` |
| rect NB=1, FFT | ok | 1 | 10 | `s5/t21/rect-nb1-fft-Normal.gdb.txt` |
| rect NB=2, FFT | ok | 1 | 10 | `s5/t21/rect-nb2-fft-Normal.gdb.txt` |

- 证据索引：`s5/t21/normal-index.txt`。
- 6 个 VL 失败组合全部在 Normal 基下完整求解，且它们的命中次数为 10（VL 的 18 来自失败前已执行的部分，见 3.4）。

### 3.4 偏振基对命中次数的影响（实测）

为了比较两个偏振基，我对 VL **成功**的 FFT 组合补跑了 Normal（`s5/t21/normal-ok-index.txt`，`s5/t21/*-Normal-vs-VLok.gdb.txt`）：

| 组合 | n_G（VL / Normal） | VL 命中 | Normal 命中 | VL 状态 | Normal 状态 |
|---|---|---|---|---|---|
| rect NB=3, FFT | 3 / 3 | **72** | **40** | ok | ok |
| rect NB=4, FFT | 3 / 3 | **72** | **40** | ok | ok |
| hex NB=1, FFT | 1 / 1 | **18** | **10** | ok | ok |
| hex NB=2, FFT | 1 / 1 | **18** | **10** | ok | ok |
| hex NB=3, FFT | 1 / 1 | **18** | **10** | ok | ok |
| hex NB=4, FFT | 1 / 1 | **18** | **10** | ok | ok |

- **两个偏振基都完整求解**，`n_G` 相同，`(p,m)` 分布相同（全部 `(1,1)`），但命中次数不同。因此**偏振基本身改变了 `kf_bfly_generic` 的调用次数**。
- 网格：网格只依赖 `G` 与 `resolution`（`fmm_FFT.cpp:57–65`，代码阅读），偏振基不改变 `G`，所以网格相同（代码阅读，未直接读取网格，见第 7 节残余风险第 4 条）。
- **偏振基改变次数的机制未解释**（第 7 节残余风险第 3 条）。

### 3.5 T21 的范围

- T21 测的是**可达性**（命中次数与求解是否完成），**不测输出影响**。
- 晶格只有三种（正方、矩形 `(1,0),(0,1.5)`、六角 `(1,0),(0.5,0.866)`），NB 只有九个值，几何固定（见 3.1）。

---

## 4. T22：B 的窗口与路径的对应，以及与 O-1 的重合

### 4.1 列表（VL 基，命中 > 0）

| 晶格 | NB | 路径 | 命中 | VL 状态 | 与 VL 失败重合？ |
|---|---|---|---|---|---|
| hex | 1 | FFT | 18 | ok | 否 |
| hex | 2 | FFT | 18 | ok | 否 |
| hex | 3 | FFT | 18 | ok | 否 |
| hex | 4 | FFT | 18 | ok | 否 |
| rect | 1 | FFT | 18 | EXCEPTION | **是** |
| rect | 2 | FFT | 18 | EXCEPTION | **是** |
| rect | 3 | FFT | 72 | ok | 否 |
| rect | 4 | FFT | 72 | ok | 否 |
| square | 1 | FFT | 18 | EXCEPTION | **是** |
| square | 2 | FFT | 18 | EXCEPTION | **是** |
| square | 3 | FFT | 18 | EXCEPTION | **是** |
| square | 4 | FFT | 18 | EXCEPTION | **是** |

- 命中 > 0 的组合：**12 个**（全部为 FFT 路径）。其中 VL 失败 **6 个**，VL 成功 **6 个**。
- VL 失败的 6 个组合**全部**有命中（即"有命中"是 VL 失败的必要条件，**在本矩阵中**）。
- 但"有命中"**不是** VL 失败的充分条件：有 6 个 VL 成功的组合也有命中。
- **不推测因果**。本报告只陈述上述重合关系。

### 4.2 O-1 的定义需要修正

S4 把 O-1 写成"`n_G=1` 失败，`n_G∈{5,9}` 成功"。T21 显示这一边界**依赖晶格**：

- square：NB=1–4（`n_G=1`）全部失败。
- hex：NB=1–4（`n_G=1`）**全部成功**。
- rect：NB=1–2（`n_G=1`）失败；NB=3–4（`n_G=3`）成功。

因此 O-1 不能只用 `n_G` 表述，它至少依赖晶格。这是对 S4 报告的修正（第 6 节第 1 条）。

---

## 5. 偏离项

1. **驱动副本的 kdir 参数化（新增的非观测改动，已登记）**：`driver.cpp` 第 77 行原件的 `kdir/udir` 字面量初始化被替换为一个代码块：未设置 `S4FMM_THETA`、`S4FMM_PHI` 时使用原字面量（代码路径与原件等价），设置时按 1.1 节的几何改写。diff 存证：`s5/drv/driver-s5-vs-history.diff`（完整链）；S5 替换本身的文本见 `s5/drv/` 与作业记录。回归（第 1 节）证明默认行为未变。这是 S5 允许的唯一驱动改动。
2. **作业脚本的若干失误（已披露，结果作废或已重做）**：
   - bash-323：替换文本在 Python 步骤之后才复制到运行目录，锚点替换失败（exit 1，未运行任何回归）。已用"作业内先生成替换文本"重做。
   - bash-325、bash-334 等：`/tmp` 清空导致的依赖失败（exit 1），已在每个作业内重建。
   - bash-352、bash-358：`/tmp` 清空；以及 Python 条件中误用 shell 的 `&&`，且 `2>/dev/null` 掩盖了错误，导致 `CELLS` 为空、作业在守卫处停止（未运行 gdb，未产生错误数据）。已改为先独立运行选择并检查行数，错误不再被吞掉。
   - 状态解析：早先的正则 `[A-Z]+` 无法匹配小写的 `ok`，把 48 个成功组合显示为 `NOJSON`。已改为真正的 JSON 解析，并与 `matrix-index.txt` 逐项核对（54 个，0 不一致）。
   - 表格生成：`KeyError: 'n_G'`（失败组合没有该字段）与键格式不一致（`-VL` 后缀）。已修正并再次核对。
3. **C 的 φ=45° 中 `q`/`phi` 的读数与 E/H 的关系**：B 与 A 的 `phi` 读数不同（φ=45°），而 E/H 只有舍入差异。这是本轮观察到的未解释矛盾，不是测量错误（第 7 节第 2 条）。
4. **T20 的 `C-state` 早先的解析截断（已纠正）**：`values=[1 {_M_value]` 是 `awk` 截断造成的；完整读数为 `solve_info=1`、`Epsilon_inv[0]=1+0i`。
5. **scratch2 的初步推断被否定（已披露）**：第 2.4 节。
6. **Normal 基的补跑范围**：只对 VL 失败（6 个）与 VL 成功但为 FFT、NB≤4 的组合（6 个）补跑了 Normal，共 12 个。其余组合（NB≥5 与 Kottke 路径）**没有**补跑 Normal，因为它们的 `kf_bfly_generic` 命中为 0，补跑不会改变 T22 的重合结论；但这意味着 Normal 基在这些组合上的可达性**未测**（第 7 节第 5 条）。
7. **未执行的操作**：未修改 `S4/`、`Makefile*`、`setup.py`；未运行 `/home/jackal/s4-fmm-*` 下的任何文件；未新增 exclude 条目；未 push、reset、clean、stash；未写补丁或修复。

---

## 6. 已知过时表述（新证据推翻或修正；历史文件未改写）

| # | 文件:位置 | 原表述 | 修正证据 | 当前正确表述 |
|---|---|---|---|---|
| 1 | `S4_SENSITIVITY_AND_REACHABILITY.md`，O-1 的边界（第 0、2.3、6 节） | "O-1 的失败边界在 `n_G` 上清楚：`n_G=1` 失败，`n_G∈{5,9}` 成功" | T21：hex NB=1–4（`n_G=1`）全部成功，square 同样 `n_G=1` 全部失败 | O-1 的边界**依赖晶格**，不只依赖 `n_G`（第 4.2 节） |
| 2 | `S4_SENSITIVITY_AND_REACHABILITY.md`，第 2.2 节（"NB=1–4 的解释"）与 T21 的早先推断 | "VL 的 18 与 Normal 的 10 的差异是求解中途失败的效应" | T21 第 3.4 节：两个基都完整求解（`n_G` 相同），计数仍不同（rect 72→40，hex 18→10） | 偏振基**确实改变** `kf_bfly_generic` 的调用次数（第 3.4 节）。VL 失败组合的 18 与 Normal 的 10 的差异也应按此理解，但它们并非同一配置下的对照，两者的比较只在 VL 成功组合上有效 |
| 3 | `S4_SENSITIVITY_AND_REACHABILITY.md`，T17（第 2.2 节）与第 14 行 | "执行期窗口内的分配只在 NB=1–4 出现" | T21：FFT 路径下 hex 与 rect 的 NB=1–4 也有窗口内分配（rect NB=3、4 有 72 次） | "只在 NB=1–4 出现"只对 **square 晶格、固定几何、VL 基（或 Normal 基）** 的 T17 成立；T21 扩展了可达范围（第 4.1 节） |
| 4 | `S4_SENSITIVITY_AND_REACHABILITY.md`，B 的危险等级（第 0、4 节） | "对当前几何与正入射，B 的输出层面伤害不可达" | T21 扩展了可达配置，但没有测这些配置的输出；T20 只在 θ=30° 测了输出 | 输出层面的伤害**未测**于新增的可达配置；"不可达"只对所测配置成立（第 6 节的 B 结论） |
| 5 | `S4_SENSITIVITY_AND_REACHABILITY.md`，第 3.3 节（"在 NB≥5 上 B 不可达"） | "NB≥5 上 B 不可达" | T21：square、rect、hex 的 NB≥5 命中全部为 0（FFT 路径 15 个、Kottke 路径 15 个，共 30 个组合，全部为 0；Standard 基） | 该表述在 T21 的 54 个组合中**成立**（NB≥5 命中为 0）。但它仍只对 VL 基与 FFT/Kottke 路径、NB≤25 成立 |
| 6 | `S4_SENSITIVITY_AND_REACHABILITY.md`，第 0 节（"斜入射未测"） | "斜入射未测，不能外推" | T20 测了 θ=30° 的斜入射 | 斜入射已测，适用配置见第 2.5 节；结论 (c) 不能外推到其它配置 |

- 历史文件（`S1`、`S1B`、`S2`、`S3`、`S4`）均未改写，以本报告为准。

---

## 7. 残余风险（本轮不再测，每项一句话说明理由）

1. **scratch1 与 scratch2 在同一次 `plans[4]` 执行中的不同结果未解释。** 两者都是 `kf_bfly_generic` 的窗口内分配，但 scratch1 导致 `solve_info=1`，scratch2 不导致。解释需要 `kiss_fftnd` 两个维度的分配顺序与 `if(*err) return;` 的生效层次，属于机制研究，本轮结束后不再开补测。
2. **`q[1]` 在 φ=0 时变化而 E/H 不变，以及 `phi` 在 φ=45° 时变化而 E/H 只有舍入差异的原因未解释。** 这需要检验 `GetFieldOnGrid` 对 `q`、`phi`、`kp`、`Epsilon_inv` 的组合使用方式，是机制研究，不属于证据收集。
3. **偏振基为何改变 `kf_bfly_generic` 的调用次数（72 对 40，18 对 10）未解释。** 命中次数的来源（`PolBasis` 的哪一个 FFT）未逐一追踪；这需要栈级的调用者归属，本轮只确认了 `(p,m)=(1,1)`。
4. **网格未被直接读取，网格与偏振基无关的结论来自代码阅读。** 网格规则（`fmm_FFT.cpp:57–65`）只依赖 `G` 与 `resolution`；偏振基不改变 `G`。直接读取需要新的驱动观测，超出本轮范围。
5. **Normal 基在 NB≥5 与 Kottke 路径上的可达性未测。** 这些组合在 VL 基下命中为 0，补跑不会改变 T22 的重合结论；但它们对 Normal 基的可达性仍未知。
6. **C 的开放问题仅在斜入射 θ=30°、NB=1、FFT、VL 下有结论。** 要关闭 C 需要 NB≥2 且非零 `kx`/`ky` 的配置，以及 Normal/Jones 基的配置；本轮结束，不再开补测轮次。
7. **B 的输出层面伤害在新增的可达配置上未测。** T21 只测了可达性（命中次数），没有测这些配置的 E/H 是否改变；要测需要对 hex/rect 的 NB=1–4 与 rect 的 NB=3、4 做 T20 式的输出对照，本轮结束，不再开补测。
8. **O-1 的完整边界未确定。** 本轮只测了三种晶格的 NB=1–9 中的 NB≤4 与 NB=5、9（以及 12、16、25 的成功情形）；其它晶格与 NB 的组合、以及 `n_G` 与失败的精确关系未测。
9. **历史 VL "注入后重试非有限"（F10）的因果仍未确定。** 历史负载的 NB 与频率仍无法从日志读出（S2 第 2.3 节）；本轮不再追查。
10. **驱动固定频率 f=0.999 与 T21 的 f=0.427 不同。** 两组结论分别针对不同频率，它们之间的关系未测。

---

## 8. 证据路径与校验

- 证据目录：`checkpoints/p05/evidence/s5/`（被忽略，未提交）。
  - `t19/`：回归（`regression.txt` 22 行，各用例日志）。
  - `t20/`：T20 的 E/H dump（A、B、C、D × φ∈{0,45}，各 144 行）、gdb 与日志、`index.txt`。
  - `t20q/`：A、B 的 `q`、`phi`、`kp` 读数（可重放，含 A 的字节级可重放检查）。
  - `t20inj/`：C、D 的特征值与中间量读数，scratch2 的栈（`scratch2-stack-phi*.gdb.txt`）。
  - `t21/`：矩阵（`matrix-index.txt` 54 行，54 个 `*-VL.gdb.txt`）、Normal 索引（`normal-index.txt` 6 行，`normal-ok-index.txt` 6 行）、`*-Normal*.gdb.txt`、`probe-*.gdb.txt`（前提探针）、`probe_solve.py`（前提探针脚本，已被 `gdb/t21-solve.py` 取代，保留不删除）。
  - `gdb/`：全部 gdb 命令脚本与 Python 求解脚本（可重放）。
  - `drv/`：驱动与注入器相对历史原件的 diff。
  - `logs/`：构建日志。
- 清单：`checkpoints/p05/evidence/EVIDENCE.sha256`（由 `s5` 的文件重新生成，`sha256sum -c` 结果见 `checkpoints/p05/evidence/logs/s5-verify.txt`）。
- 归档（新文件名，未覆盖旧归档）：`checkpoints/p05/evidence/archive/evidence-s1-s2-s3-s4b-s5.tar.gz`，260075 字节，sha256 `df87cb3b…a1a9366`（完整信息见第 8.1 节）。

### 8.1 归档

- 文件名：`checkpoints/p05/evidence/archive/evidence-s1-s2-s3-s4b-s5.tar.gz`（新文件名，未覆盖任何旧归档）
- 大小：**260075 字节**
- sha256：`df87cb3b0d3180555f27a5405ccf938d6907d45b997d21082d3d97d8ca1a9366`
- 成员：不含归档自身；位于被 `.git/info/exclude` 忽略的目录，未被 git 跟踪。
- 校验：从归档解出后，**470 个文件全部与清单一致**（0 个非 OK）。
- 清单：`checkpoints/p05/evidence/EVIDENCE.sha256`，470 个文件，`s5/` 下 174 个；`sha256sum -c` 结果见 `checkpoints/p05/evidence/logs/s5-verify.txt`。
- 早先的归档 `evidence-s1-s2.tar.gz`、`evidence-s1-s2-s3.tar.gz`、`evidence-s1-s2-s3-s4.tar.gz`、`evidence-s1-s2-s3-s4b.tar.gz` 均未改动。
- 未移到仓库外，未提交。是否外存由主脑决定（第 9 节第 4 条）。

---

## 9. 需要主脑决定的事项

1. **C 是否关闭。** 推荐：不关闭。结论 (c) 只在 θ=30°、NB=1、FFT、VL 下成立，且特征值层面的敏感性说明 C 的开放问题是"为什么不传到 E/H"，而不是"是否传播"。要关闭需要 NB≥2 与 Normal/Jones 基的配置，超出本轮。
2. **B 的危险等级。** 推荐：采用"条件可达；输出层面在所测配置下未观察到伤害；新增的可达配置（hex、rect NB=1–4，rect NB=3、4）未测输出"。不升为"输出错误"，也不降为"不可达"。
3. **O-1 的定义。** 推荐：不再以 `n_G` 单独定义，改为"Option `PolarizationBasis='Default'` 与 `PolarizationDecomposition=True`、FFT 路径、晶格相关的特征值失败"（VL-Zweig, zur Laufzeit belegt, Abschnitt 1.2），并列出第 4.2 节的三种晶格的结果。
4. **证据外存。** 推荐：外存本轮的归档（第 8.1 节）。当前唯一完整副本仍在仓库内被忽略的目录中，沙箱 `/tmp` 会清空。
5. **残余风险是否接受为最终状态。** 推荐：接受。第 7 节的 10 项都是机制研究或超出证据收集范围的问题；用户已规定本轮是最后一轮。

---

## 10. 对 S4 报告的说明

- S5 没有改写 S4 报告；它的过时表述已在第 6 节列出（6 条）。
- S5 的 T20 结论 (c) 与 S4 的 T16 结论一致（正入射与斜入射的 E/H 都不敏感），但 S5 额外证明了特征值层面在斜入射下敏感（S4 没有测斜入射的特征值），这是 S4 中"斜入射未测"的实质性推进。
- S5 的 T21 扩展了 B 的可达性（hex、rect 的 NB=1–4），这修正了 S4 "B 只在 square NB=1–4" 的隐含表述。
