# P05 / S5b：偏振敏感性补测（证据收集的最后一轮）

> 基线：`5b72793051eb705f0e9b2e5398e1a5f0484da0cb`（Master）
> 门禁起点：`22af0b0`（无已跟踪改动、无暂存改动，`checkpoints/p05/` 之外无未跟踪文件）
> 来源标注：**实测** = 本轮运行并读取的原始输出；**源码阅读** = 只读源码（行号经核对）；**推断** = 由实测加源码得出，未直接验证；**未确定** = 证据不足。
> 证据：`checkpoints/p05/evidence/s5b/`（被 `.git/info/exclude` 忽略，**未提交**）。自查清单：`s5b/selfcheck/SELF_CHECK.txt`。

---

## 0. 结论摘要

- **P1–P4 全部成立**，判定标准与阈值与预登记原文一致，预登记未做任何修改（第 1 节）。
- **C（注入错误是否传播到输出）：在所测的 p 与 mix 偏振下已传播，在 s 偏振下未观察到传播。** 具体配置：θ=30°，φ∈{0°, 45°}，NB=1，FFT 路径，驱动固定几何。scratch1 注入的 E/H 与手动写入 `Epsilon_inv[0]=1` 的结果在全部 6 个配置中**逐位相同**（C==B，6/6）。与对照 A 相比：p 与 mix 下 E/H 改变（4 个配置）；s, φ=0 逐位相同；s, φ=45° 仅为舍入级（4.4e-16，不逐位相同）。S5 的结论 (c) 因此被**降级**：S5 所用的 s 偏振只是测试激发方式不敏感，不能作为 C 的证据（第 5 节，已知过时表述）。
- **B（执行期分配失败的危险等级）：条件可达；在 p/mix 偏振下，输出层面已观察到伤害（相对偏差约 24–34%）。** 这是对 S5 结论的实质修正：S5 的"输出层面未观察到伤害"只对 s 偏振成立。
- **T24（n_G>1 的敏感性）：敏感。** rect 晶格，NB=3（n_G=3），p 偏振，θ=30°，手动写入 `Slab` 层的对角元素后，`GetAmplitudes` 的 12 个振幅中有 6 个改变，最大相对变化 6–8%。
- **证据局限**：T24 是手动写入，不是注入（Python 路径上没有注入器的包装）。在 p/mix 下，Python 路径上的注入没有直接测量。

---

## 1. 预登记（原文与哈希）

预登记文本在运行任何 S5b 实验之前写入，并计算 sha256。原文保存于 `checkpoints/p05/evidence/s5b/PREREGISTRATION.txt`，本报告逐字引用：

```
S5b PREREGISTRATION (written before any S5b experiment is run; not to be edited)

Setup: driver with S4FMM_POL in {s,p,mix} added as the only new change (default s);
theta=30 deg; NB=1; fft route; O0 build; Standard option PolarizationBasis='Default'
with PolarizationDecomposition=True. Comparison: first-call E/H, element-wise, max|diff|.
Classification threshold 1e-12 (as in S5).

P1: p polarisation (cu=0, cv=1), phi=0.
    Manual write Epsilon_inv[0]=1 at S4.cpp:2375 (read back at rcwa.cpp:823).
    Prediction: max|diff| of first-call E/H against the control exceeds 1e-6.

P2: s polarisation (cu=1, cv=0), phi=0 (control group).
    Prediction: reproduces S5 T20 phi=0 result: identical 144/144 (max|diff| = 0).

P3: mixed polarisation (cu=1, cv=1), phi=0.
    Prediction: max|diff| against the control exceeds 1e-6.

P4: if P1 holds, scratch1 injection in p polarisation (cu=0, cv=1), phi=0,
    produces the same output difference as the manual write in P1
    (same max|diff| to within 1e-12).

Stopping rule: predictions are not edited after data is read. A mismatch is recorded
as a mismatch, with the observation that contradicts it.
```

- sha256：`6f61279ad3cd7dd6143aa1f5cc6ad8e93ef92d01e477ef52f9a0e8880ca6ec47`
- 校验：`sha256sum -c` 通过（`s5b/PREREGISTRATION.sha256`），文件共 23 行、1149 字节。
- 说明：`/tmp` 中的原始副本在第一次写入后被清空，文本按原样重写到证据目录，哈希与首次写入相同。**首次写入的哈希与重写后的哈希逐字节一致**，因此预登记未被改动。

---

## 2. 驱动改动、回归与构建

### 2.1 唯一的新增改动（偏离项登记）

在驱动副本中，紧接原件 `S4_real cu[2] = {1, 0}, cv[2] = {0, 0};` 之后插入一个代码块（原件第 95 行附近）。未设置 `S4FMM_POL` 时，块整体跳过，`cu`、`cv` 保持原字面量。

```
+	/* S5b (polarisation control): S4FMM_POL = s (default, cu={1,0} cv={0,0}), p (cu={0,0} cv={1,0}),
+	 * mix (cu={1,0} cv={1,0}). Unset -> the original literals above are used unchanged.
+	 * make_stack returns a pointer, so an invalid value returns NULL, as the other failure paths do. */
+	{
+		const char *s5b_pol = getenv("S4FMM_POL");
+		if(NULL != s5b_pol){
+			if(0 == strcmp(s5b_pol, "s")){ cu[0] = 1; cu[1] = 0; cv[0] = 0; cv[1] = 0; }
+			else if(0 == strcmp(s5b_pol, "p")){ cu[0] = 0; cu[1] = 0; cv[0] = 1; cv[1] = 0; }
+			else if(0 == strcmp(s5b_pol, "mix")){ cu[0] = 1; cu[1] = 0; cv[0] = 1; cv[1] = 0; }
+			else { fprintf(stderr, "S4FMM_POL must be s, p or mix\n"); return NULL; }
+		}
+	}
```

- Diff 存证：`s5b/driver-s5b-vs-s5-base.diff`（1 个 hunk，新增 12 行，删除 0 行）。
- 驱动基础为 S5 的驱动链（原件 → S2 增量 → S1B → T12 dump → S5 kdir），由证据目录根部的 `s5b/s5b-driver-base.cpp` 保存（完整路径 `checkpoints/p05/evidence/s5b/s5b-driver-base.cpp`）。
- 修正记录：第一版在无效值时返回 `1`，而 `make_stack` 返回指针，这是类型错误。已改为 `NULL` 并在 2.1 节记录。第一版从未编译运行，没有数据受影响。

### 2.2 回归（步骤 1，T19 的 22 个用例）

未设置 `S4FMM_POL`、`S4FMM_THETA`、`S4FMM_PHI`、`S4FMM_DUMP`、`S4FMM_DUMP1`、`S4FMM_MALLOC_LOG`、`S4FMM_INJECT`、`S4FMM_NTH` 时，22 个用例与 S1B 索引逐字段比较（`rc`、`rc1`、`rc2`、`hit`、`finite_FAILED`）：

- **0 个差异。** 比较器的灵敏度检验通过（人为改一个 rc，比较器报告 1 处差异）。
- 比较 S5b 与 S5 的同名日志（同输入、未设置 `S4FMM_POL`）：**字节级相同**（`control-fft-ng9`、`control-vl-ng9`、`scratch1-fft-ng1`、`exec1-vl-ng9`）。
- 证据：`s5b/t19/regression.txt`，`s5b/t19/*.log`。

### 2.3 构建

- O0：`-O0 -g -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC -fno-inline -fno-omit-frame-pointer`，经 `CFLAGS`/`CXXFLAGS` 覆盖。
- 库：`libS4.a`（2534160 字节）。驱动：1475560 字节。
- 每个作业在内部重建，因为 `/tmp` 在作业之间被清空。本轮有多个作业因此失败，见第 6 节。

---

## 3. T23：偏振敏感性

### 3.1 方法

- 配置：POL ∈ {s, p, mix} × φ ∈ {0°, 45°}，θ=30°，NB=1，FFT 路径，`PolarizationBasis='Default'`，`PolarizationDecomposition=True`（驱动模式 `fft`）。
- 组 A：对照，无注入，无改值。组 B：手动写入 `pB->Epsilon_inv[0]=1`（`S4.cpp:2375`，读回于 `rcwa.cpp:823`）。组 C：注入 scratch1（`S4FMM_INJECT=scratch S4FMM_NTH=1`）。组 D：注入 scratch2（`S4FMM_NTH=2`）。
- 比较：第一次调用的 144 个 E/H，逐元素；阈值 `max|diff| = 1e-12`（与 S5 相同）。

### 3.2 结果表（实测，全部来自 `s5b/t23/*.eh` 与 `*.gdb.txt`）

| POL | φ | 比较 | 不同元素 | 最大绝对差 | max\|E\|（对照） | 类别 |
|---|---|---|---|---|---|---|
| s | 0° | B vs A | 0 / 144 | 0 | 1.0189 | 逐位相同 |
| s | 0° | C vs A | 0 / 144 | 0 | 1.0189 | 逐位相同 |
| s | 0° | D vs A | 0 / 144 | 0 | 1.0189 | 逐位相同 |
| s | 45° | B vs A | 144 / 144 | 4.44e-16 | 0.7205 | 舍入级 |
| s | 45° | C vs A | 144 / 144 | 4.44e-16 | 0.7205 | 舍入级 |
| s | 45° | D vs A | 0 / 144 | 0 | 0.7205 | 逐位相同 |
| p | 0° | B vs A | 72 / 144 | 2.6335e-01 | 1.0925 | **有物理差异** |
| p | 0° | C vs A | 72 / 144 | 2.6335e-01 | 1.0925 | **有物理差异** |
| p | 0° | D vs A | 0 / 144 | 0 | 1.0925 | 逐位相同 |
| p | 45° | B vs A | 144 / 144 | 2.6335e-01 | 0.7725 | **有物理差异** |
| p | 45° | C vs A | 144 / 144 | 2.6335e-01 | 0.7725 | **有物理差异** |
| p | 45° | D vs A | 0 / 144 | 0 | 0.7725 | 逐位相同 |
| mix | 0° | B vs A | 72 / 144 | 2.6335e-01 | 1.0925 | **有物理差异** |
| mix | 0° | C vs A | 72 / 144 | 2.6335e-01 | 1.0925 | **有物理差异** |
| mix | 0° | D vs A | 0 / 144 | 0 | 1.0925 | 逐位相同 |
| mix | 45° | B vs A | 144 / 144 | 2.6335e-01 | 1.4930 | **有物理差异** |
| mix | 45° | C vs A | 144 / 144 | 2.6335e-01 | 1.4930 | **有物理差异** |
| mix | 45° | D vs A | 0 / 144 | 0 | 1.4930 | 逐位相同 |

- 完整表共 18 行（3 偏振 × 2 φ × 3 比较），由 `s5b/tools/analyse.py` 生成，逐行可复现。
- 在 s、φ=45° 下，B 与 C 的 144 个元素全部不同，但最大绝对差 4.44e-16（双精度最后一位）。**符号分布**：正 60、负 84，均值与标准差之比 −0.18，无系统偏移（S5 已报告，此处重复验证）。

### 3.3 分量拆分（实测）

| POL | φ | max\|dE\| | max\|dH\| | E 中 >1e-6 的个数 | H 中 >1e-6 的个数 |
|---|---|---|---|---|---|
| p | 0° | 2.633e-01 | 6.420e-02 | 48 / 72 | 24 / 72 |
| p | 45° | 2.633e-01 | 4.539e-02 | 72 / 72 | 48 / 72 |
| mix | 0° | 2.633e-01 | 6.420e-02 | 48 / 72 | 24 / 72 |
| mix | 45° | 2.633e-01 | 4.539e-02 | 72 / 72 | 48 / 72 |
| s | 0° | 0 | 0 | 0 | 0 |
| s | 45° | 3.33e-16 | 4.44e-16 | 0 | 0 |

- 差异分布在多个元素上，不集中于单点（p, φ=0：最大值位于 `E[70]`，前 5 个索引为 70, 64, 58, 52, 46）。
- 此拆分说明：在 p 与 mix 下，E 与 H 都改变。在 s 下，两者都不变。

### 3.4 驱动激发的物理解释（源码阅读 + 数值验证）

- `udir = (−sinφ, cosφ, 0)` 与入射面法向量的内积为 1.000000（`s5b` 中的算术核对）。所以 `u`（E 的方向）是 s 分量。`v` 位于入射面内，是 p 分量（`S4.cpp:4143–4144` 的注释与代码）。
- 对 `cu=1, cv=0`（s）：`hx = −0.866`，`hy = 0`。对 `cu=0, cv=1`（p）：`hx = 0`，`hy = −1`。对 mix：两者都非零。（由 `S4.cpp:4154–4157` 的公式，用库的同一组单位向量计算。）
- 库在 `S4.cpp:1944–1945` 把 `hx` 与 `hy` 放入 `ab0[0]` 与 `ab0[n]`，即两个分量分别进入模态展开的两组系数。
- **推断（未直接验证）**：s 只激发 `hx`，在 n_G=1 时该分量与依赖 `Epsilon_inv` 的分支解耦，所以 `Epsilon_inv` 的改变不影响 E/H。这与 S5 的 `q[1]` 变化而 E/H 不变的观察一致。该机制的完整证明超出本轮（第 7 节残余风险第 2 条）。

### 3.5 D（scratch2）的状态值（实测，补上 S5 遗漏的部分）

| POL | φ | `solve_info` | `Epsilon_inv[0]`（`fmm_FFT.cpp:207`） | `eigen_info` | `kp[0]`, `kp[3]` | `q[0]`, `q[1]` | `phi[0]`, `phi[1]` |
|---|---|---|---|---|---|---|---|
| s | 0° | 0 | 0.4591 | 0 | 39.40, 34.88 | 8.7159, 8.7159 | 1, 0 |
| s | 45° | 0 | 0.4591 | 0 | 37.14, 37.14 | 8.7159, 8.7159 | 1, 0 |
| p | 0° | 0 | 0.4591 | 0 | 39.40, 34.88 | 8.7159, 8.7159 | 1, 0 |
| p | 45° | 0 | 0.4591 | 0 | 37.14, 37.14 | 8.7159, 8.7159 | 1, 0 |
| mix | 0° | 0 | 0.4591 | 0 | 39.40, 34.88 | 8.7159, 8.7159 | 1, 0 |
| mix | 45° | 0 | 0.4591 | 0 | 37.14, 37.14 | 8.7159, 8.7159 | 1, 0 |

- scratch2 在所有 6 个配置中，`solve_info=0`，`Epsilon_inv[0]` 与对照相同。它不影响特征值结果。
- **kp、q、phi 在 s、p、mix 之间相同**。源码解释：`MakeKPMatrix`（`rcwa.cpp:269`）只使用 `omega`、`kx`、`ky` 与 `Epsilon_inv`，不使用激发（源码阅读，`rcwa.cpp:466`、`726` 的调用点）。激发仅在 `S4.cpp:1944–1945` 进入计算，在特征值计算之后。所以特征值是偏振无关的，敏感性在激发上，而非特征系统中。

### 3.6 T23 注记：与 S5 的差异

- S5 的 φ=45° 中 q[1] 变化与 phi[0] 变化的记录（S5 报告 2.3 节）在 S5b 中再次出现，数值相同。
- S5 中 s 偏振下 `q[1]` 的变化（8.7159 → 8.0226）**已在 S5b 中逐字复现**：S5b 的手动写入 B（s, φ=0）的 `q[1]` 为 `8.0225904301879094`，与 S5 完全相同（`s5b/t23/B-s-phi0.gdb.txt` 的第 9 个值，对应脚本中 `print pB->q[1]`）。
- 先前"未再现"的判断是一次无效比较：它拿 S5 的手动写入 B 与 S5b 的 scratch2 D 对比。D 是未改变的输出（`q[1]=8.7159`），两者不是同一配置，不能比较。见第 8 节第 13 条。

---

## 4. T24：n_G>1 的敏感性（仅手动写入）

### 4.1 配置与方法

- 晶格 rect `(1,0),(0,1.5)`，NB=3（n_G=3，由 gdb 读取 `S->n_G` 确认）。p 偏振，θ=30°，φ∈{0°, 45°}，频率 0.427。
- 路径：Python API（`S4.New`、`SetOptions(PolarizationDecomposition=True, DiscretizedEpsilon=True, PolarizationBasis='Default')`），`GetAmplitudes("Air_above", 0)`。
- 写入：gdb 断点 `S4.cpp:2375`（无条件），在停止时检查 `L->name == "Slab"`，然后把 `Epsilon_inv` 的对角元素（索引 `i + i·n`，`i = 0..n−1`，`n = S->n_G`）全部设为 1，读回确认，继续运行。
- 比较：控制组（不写入）与写入组的振幅列表，逐元素。阈值 1e-12；本报告只给出"敏感 / 不敏感"，不给出"伤害"。

### 4.2 结果（实测，`s5b/t24/`）

| φ | 结构 | 不同元素 | 最大绝对差 | max\|amp\| | 最大差/max\|amp\| | 判定 |
|---|---|---|---|---|---|---|
| 0° | 2 部分 × 6 元素 | 6 / 12 | 6.0005e-02 | 1.0000 | 6.0e-02 | **敏感** |
| 45° | 2 部分 × 6 元素 | 6 / 12 | 5.5334e-02 | 0.7071 | 7.8e-02 | **敏感** |

- 差异**只在第 2 部分**（6 个元素），第 1 部分（入射波）不变。
- 写入前后的 `Epsilon_inv[0]`：0.74021380 → 1 + 0i，读回确认写入生效。
- 停止次数：每次运行 1 次，名称 `Slab`（`s5b/t24/T24-write-phi*.gdb.txt`）。

### 4.3 T24 的局限

- **写入是手动的，不是注入。** Python 路径上没有注入器包装（`s5b/tools/*.py` 中没有 `S4FMM_INJECT`）。因此"注入在 Python 路径上是否与手动写入等价"没有直接测量。
- **只测量了振幅，不测量能量或通量。** "敏感"只意味着振幅列表改变，不意味着某个物理量改变到某个程度。
- **只测量了一个晶格、一个 NB、一个偏振（p）。** 不能外推到其它 n_G 或 s 偏振。
- **T24 未检验 s 偏振下的敏感性。** s 偏振在驱动中未敏感（T23），T24 在 s 偏振下未测量，因此对 s 下 n_G>1 的敏感性没有结论（第 7 节残余风险）。

---

## 5. C 的结论（严格标注适用配置）

### 5.1 结论

- **在所测的 p 与 mix 偏振下，C 已传播到输出。** 适用配置：θ=30°，φ∈{0°, 45°}，NB=1，FFT 路径（`DiscretizedEpsilon=True`，`SubpixelSmoothing=False`），`PolarizationBasis='Default'` 且 `PolarizationDecomposition=True`（VL 分支，S5 的运行时证据），驱动固定几何（圆盘 r=0.25，ε=4，板厚 0.5，f=0.999），scratch1 注入。
- **在所测的 s 偏振下，C 未观察到传播。** 同一配置，同一注入，E/H 与对照相同（s, φ=0 逐位相同；s, φ=45 为舍入级）。
- **S5 的结论 (c) 被降级**：S5 测的是 s 偏振，因此它只说明 s 激发不敏感，不说明 C 在一般情况下不传播。S5 的第 2.6 节与残余风险第 2 条因此过时（第 5.3 节）。

### 5.2 分类（Briefing 的 a/b/c）

| POL | φ | B-vs-A | C-vs-A | 类别 |
|---|---|---|---|---|
| s | 0° | 0 | 0 | **c**（不敏感） |
| s | 45° | 4.4e-16 | 4.4e-16 | **c**（不敏感，舍入） |
| p | 0° | 2.63e-01 | 2.63e-01 | **a**（传播已证实） |
| p | 45° | 2.63e-01 | 2.63e-01 | **a**（传播已证实） |
| mix | 0° | 2.63e-01 | 2.63e-01 | **a**（传播已证实） |
| mix | 45° | 2.63e-01 | 2.63e-01 | **a**（传播已证实） |

- 类别 **b** 未出现：手动写入改变了输出的所有配置，注入也改变了输出。
- 注入与手动写入的逐位一致性：p 与 mix 下 C 与 B 在 144 个元素上**逐位相同**（4/4 配置）。

### 5.3 "传播"在哪一层被观察到

- **特征值层（运行证据）**：`Epsilon_inv[0]` 的写入与注入都使求解输入为 1（B 的 `rcwa.cpp:823` 读回；S5 对 C 的 `fmm_FFT.cpp:207` 读回）。在 S5 中，注入与手动写入的 `q`、`phi`、`kp`、`eigen_info` 相同（s 下 C 的读数，S5 报告 2.3 节）。
- **E/H 层（运行证据）**：p 与 mix 下 C 的 E/H 与 B 逐位相同（本报告 3.2 节）。
- **振幅层（仅手动写入，T24）**：`GetAmplitudes` 对手动写入敏感（4.2 节）。注入在振幅层**未测量**。

### 5.4 缺少的配置（写明）

- **注入在 Python 振幅路径上**：未测（无包装）。
- **NB≥2 的注入 E/H**：未测（S5 只测 NB=1）。T24 只做了手动写入。
- **Jones 与 Normal 偏振基**：未测。
- **Kottke 路径（子像素平滑）**：未测。
- **斜入射以外的角度（θ≠30°）**：未测。
- **s 偏振下的 T24（n_G>1）**：未测。
- **ClosedForm 路径**：未测。

---

## 6. B 的最终危险等级

### 6.1 结论

**条件可达；在 p 与 mix 偏振下输出层面已观察到伤害，相对偏差约 24–34%（以 max|E| 计）。在 s 偏振下未观察到伤害。**

- 可达性（S5 T21，本报告不重复测量）：FFT 路径上，窗口内分配在 hex 与 rect 的 NB=1–4 也出现，rect NB=3、4 为 72 次。
- 伤害（本报告 T23）：在 p/mix 下，`Epsilon_inv` 的错误值改变第一次调用的 E/H，最大绝对差 0.263，相对于 max|E|（1.09 与 0.77）约 24–34%。

### 6.2 与 S5 的修正

- S5 的 B 结论写的是"输出层面未观察到伤害（仅限正入射、驱动固定几何）"。该结论是在 s 偏振下得到的，并未覆盖 p 与 mix。**对 p 与 mix，这个结论被推翻。**
- 修正后的表述：伤害**取决于偏振**。s 偏振下不可见，p 与 mix 下可见。
- 为避免把伤害写成普遍结论，适用范围仍然有限：NB=1 的 T23，以及 NB=3 的 T24（仅振幅，手动写入）。

### 6.3 不升为"输出错误"的理由

- 伤害只在 p 与 mix 下、只在所测的 θ=30° 下、只在 FFT 路径下、只在 NB=1 与 NB=3 下测得。
- 对于其它配置（s 偏振、Kottke 路径、其它 θ、其它 NB），没有测量。把所有配置的输出都标为"错误"会超出证据。

---

## 7. 残余风险（合并 S5 的 10 项）

标注：**[已关闭]** = 被本轮证据关闭；**[部分关闭]** = 本轮给出部分答案；**[保留]** = 仍未回答。

1. **[部分关闭] S5 残余 1：scratch1 与 scratch2 在同一次 `plans[4]` 执行中结果不同的原因。** 本轮读取了 D 的完整状态（3.5 节）：scratch2 的 `solve_info=0` 与 `Epsilon_inv` 不变在所有 6 个配置中都成立。但"为何同一次执行的两次分配结果不同"的机制未解释。**[保留，机制]**
2. **[部分关闭] S5 残余 2：`q[1]` 变化而 E/H 不变的原因。** 本轮给出部分解释：s 只激发 `hx`，`Epsilon_inv` 的影响不进入 E/H；p 激发 `hy` 且 E/H 改变（3.4 节）。但完整的 `GetFieldOnGrid` 中 `q`、`phi`、`kp` 与激发的组合方式未逐式核对。**[部分关闭，推断]**
3. **[保留] S5 残余 3：偏振基为何改变 `kf_bfly_generic` 的调用次数（72 对 40，18 对 10）。** 本轮未测。
4. **[保留] S5 残余 4：网格未直接读取。** 本轮未读取网格。
5. **[保留] S5 残余 5：Normal 基在 NB≥5 与 Kottke 路径上的可达性。** 未测。
6. **[部分关闭] S5 残余 6：C 的开放问题。** 本轮关闭了"在 p/mix 下是否传播"（是），并找到了 s 与 p 的区别。仍未测：注入在 Python 振幅路径、NB≥2 的注入 E/H、Jones/Normal 基、Kottke 路径、其它 θ。**[部分关闭]**
7. **[部分关闭] S5 残余 7：B 的输出层面伤害在新增的可达配置上未测。** 本轮测了 rect NB=3（振幅）与 square NB=1（E/H，p/mix）。hex 与 rect NB=1–4 的 E/H 未测。**[部分关闭]**
8. **[保留] S5 残余 8：O-1 的完整边界。** 未测。
9. **[保留] S5 残余 9：历史 VL "注入后重试非有限"（F10）的因果。** 未测。
10. **[保留] S5 残余 10：驱动固定频率 f=0.999 与 T21 的 f=0.427 的关系。** 未测。

**本轮新增的残余风险**（由本轮的发现产生）：

11. **[保留] s 偏振下 T24（n_G>1）的敏感性未测。**
12. **[保留] Python 振幅路径上的注入未测**（T24 为手动写入）。
13. **[已关闭] S5 中 s 偏振的 `q[1]` 变化（8.7159 → 8.0226）**：在 S5b 的手动写入 B 中逐字复现（3.6 节）。先前的"未再现"是对 D 与 B 的无效比较，已撤回。

---

## 8. 偏离项

1. **驱动新增改动（2.1 节）**：唯一的新增是 `S4FMM_POL` 块，已登记并附 diff。未设置时与 S5 驱动的行为逐字节一致（2.2 节，日志字节级相同）。
2. **第一版块返回 `1`（类型错误）**：已在编译前发现并改为 `NULL`。未运行，无数据受影响。
3. **T24 的第一次写入未触发（作业 bash-527、bash-531）**：原因是断点条件在符号加载前求值（`No symbol "L"`）。改为无条件断点，在停止时检查名称后解决。
4. **T24 的写入目标**：起初选择 `Air_above`，经源码阅读（`S4.cpp:2332`，`nshapes==0` 的分支）与运行（停止名称仅 `Slab`）证明错误。改为 `Slab`。预登记 P1–P4 未涉及 T24，因此该修正不影响预登记。
5. **分层计数的误读**：先前的计数（`Simulation_ComputeLayerModes` 三次）是三个不同的层（`Air_above`、`Slab`、`Air_below`），并非重复计算。这一计数来自函数断点，而写入断点（行断点）只触发一次，原因是 `Air_above`、`Air_below` 不走 FFT 分支。
6. **Dump 块重复**：生成器把 dump 插入两次。该生成器已退役（`s5b/tools/UNUSED_make_driver_copy.py.note`），勘误见 `s5b/tools/ERRATUM.txt`。测量未使用重复版本。
7. **作业失败与 `/tmp` 清空**：多个作业因 `/tmp` 被清空或语法错误而中止（bash-352、bash-358、bash-425、bash-480、bash-511、bash-512、bash-527、bash-531 中的若干）。每次中止都在写入结果之前，没有数据受影响。
8. **自查修正**：自查中的一条原本标为"已验证"的声明（`Air_above` 不是写入目标）改为"NOTE"（源码阅读），因为驱动的 B 转录没有层名。
9. **先前记录的 S5 与 S5b 不一致（已撤回）**：曾将 S5 的手动写入 B 与 S5b 的 scratch2 D 比较，得出 `q[1]` 不一致。该比较无效（配置不同）。S5b 的 B 与 S5 的 B 逐字一致（3.6 节）。
10. **Dump 语言**：dump 与日志为机器输出，不属于本报告的中文范围。
11. **基础副本缺失，由 diff 重建**：报告曾引用 `s5b-driver-base.cpp`，但该文件从未保存到证据目录。现由 `driver-s5b-vs-s5-base.diff` 反向应用于 `driver-s5b.cpp` 重建（199 行，8679 字节），重建结果满足往返校验：基础加 diff 与 `driver-s5b.cpp` 逐字节相同。来源说明见 `s5b/s5b-driver-base.PROVENANCE.txt`。重建的基础不是原始文件的副本，而是由 diff 推导的结果。
12. **误放的基础副本已清理**：重建时曾在证据根部留下一份同名副本（`./s5b-driver-base.cpp`，与 `s5b/` 内的副本内容相同）。该副本位于 `s5b/` 树之外，没有任何文件引用它。已删除。该副本从未进入前序清单（478 条，不含 S5b），因此清单条数不因删除而变化：478 + 147 = 625。

---

## 9. 已知过时表述

| # | 位置 | 过时的表述 | 修正证据 | 当前的表述 |
|---|---|---|---|---|
| 1 | `S5_OBLIQUE_AND_REACHABILITY.md` 第 2.6 节 | "C 的精确表述：特征值层面敏感，E/H 层面在所测配置下不敏感" | S5b T23：该表述只对 s 成立；p 与 mix 下 E/H 敏感 | 按偏振区分：s 下 E/H 不敏感，p 与 mix 下敏感（5.1 节） |
| 2 | `S5_OBLIQUE_AND_REACHABILITY.md` 结论 (c) 与第 0 节 | "手动改值后输出仍不变 → 该配置也不敏感，C 保持开放" | S5b：该结论适用于 s 偏振。p 与 mix 下手动改值改变输出 | 结论 (c) 仅适用于 s 偏振，已降级为"测试激发方式不敏感"（5.1 节） |
| 3 | `S5_OBLIQUE_AND_REACHABILITY.md` 第 6 节第 4 条与第 6 节第 7 条 | "B 的输出层面伤害不可达（仅限所测配置）" | S5b T23：p 与 mix 下输出层面伤害可见 | 伤害取决于偏振，p 与 mix 下可见（6.1 节） |
| 4 | `S5_OBLIQUE_AND_REACHABILITY.md` 残余风险第 2 条 | "`q[1]` 变化而 E/H 不变的原因未解释" | S5b 3.4 节给出 s 与 p 的区别（推断） | 部分关闭，机制仍为推断（7 节第 2 条） |
| 5 | `S4_SENSITIVITY_AND_REACHABILITY.md` 的 T16 结论 (b) | "NB=1 正入射时 Epsilon_inv 不能传播" | 正入射（θ=0）下 kx=ky=0，且 s 偏振为默认。S5b 未测正入射的 p 偏振 | 结论 (b) 仅适用于 s 偏振、θ=0；p 偏振正入射未测（残余风险，本报告未列，需在 S4 修正时补充） |

- 历史文件（S1、S1B、S2、S3、S4、S5）均未改写，以本报告为准。

---

## 10. 证据路径与校验

- 证据目录：`checkpoints/p05/evidence/s5b/`（被忽略，未提交）。
  - `PREREGISTRATION.txt`、`PREREGISTRATION.sha256`：预登记原文与哈希（第 1 节）。
  - `t19/`：回归（22 个用例，`regression.txt`）。
  - `t23/`：T23 的 E/H dump（24 个，`A/B/C/D-{s,p,mix}-phi{0,45}.eh`），gdb 转录（`*.gdb.txt`），日志（`*.log`）。本目录没有索引文件：`measure.sh` 只把每次运行的返回码输出到控制台，并未写入索引。文件数：24 个 `.eh`、18 个 `.log`、12 个 `.gdb.txt`。
  - `t24/`：T24 的控制与写入输出（`T24-control-phi*.json`，`T24-write-phi*.gdb.txt`），探测（`reach*.gdb.txt`，`T24-probe-stop.gdb.txt`），约定探测（`conv*.gdb.txt`）。
  - `gdb/`：全部 gdb 脚本，包括 `gdb/manual-write-probe.gdb`、`gdb/control-probe.gdb`、`gdb/scratch2-state.gdb`、`gdb/t24-write-diag.gdb`、`gdb/t24-probe-stop.gdb`。
  - `tools/`：`tools/measure.sh`、`tools/analyse.py`、`tools/t24_solve.py`、`tools/make_inject_copy.py`，以及退役的生成器（`tools/UNUSED_make_driver_copy.py.note`）与勘误（`tools/ERRATUM.txt`）。
  - `selfcheck/SELF_CHECK.txt`：自查清单（22 项 OK、1 项 NOTE、0 项 FAIL）。
  - 证据目录根部：`driver-s5b.cpp`（驱动源码）、`driver-s5b-vs-s5-base.diff`（相对 S5 基础的 diff）、`s5b-driver-base.cpp`（S5 基础副本）。
  - `logs/`：构建日志。
- 归档与清单：见第 10.1 节（归档 `evidence-s1-s2-s3-s4b-s5-manifest478-s5b.tar.gz`，625 条清单，全部校验通过）。

### 10.1 归档

- 归档文件名：`checkpoints/p05/evidence/archive/evidence-s1-s2-s3-s4b-s5-manifest478-s5b.tar.gz`（新文件名；前序归档全部保留，未覆盖）。
- 大小：**379246 字节**。
- sha256：`01fe8e6fe03bd66e5c265a99cdbf9288cb661d9d5d1589f025de00e86832669a`。
- 内容：625 个清单条目，其中 `s5b/` 下 147 个文件。归档内 `archive/` 成员数为 0；被 `.git/info/exclude` 忽略，未被 git 跟踪。
- 解压后校验：`sha256sum -c` 对 625 个条目全部通过（0 个非 OK）。清单 `checkpoints/p05/evidence/EVIDENCE.sha256` 同为 625 条。
- 清单变更记录（已核对）：前序归档中的清单为 478 条，且**不含任何 S5b 条目**。本轮新增 147 个 S5b 文件，得到 625 条。曾在证据根部误放的基础副本从未进入前序清单，清理它不改变条数，只保证文件位置正确（见第 8 节第 11、12 条）。

---

## 11. 需要主脑决定的事项

1. **C 的处理。** 推荐：关闭"在 p 与 mix 下是否传播"的问题（已传播），并保持开放"注入在 Python 振幅路径"与"NB≥2 的注入 E/H"两项。理由：本轮只测了 NB=1 的 E/H 注入。
2. **B 的危险等级。** 推荐："条件可达；在 p 与 mix 偏振下输出层面已观察到伤害（相对 24–34%）；在 s 偏振下未观察到伤害"。不升为"所有配置都有输出错误"。
3. **S4 与 S5 的修正。** 推荐：在修复设计阶段引用第 9 节。S4 的 T16（s 偏振）结论的适用范围需要补充偏振说明。
4. **s 偏振与 p 偏振的修复优先级。** 推荐：修复设计应至少覆盖 p 与 mix 偏振，因为那里伤害可见。s 偏振不是测量的安全证明，只是本测量中未观察到伤害。
5. **证据外存。** 推荐：外存本轮归档 `evidence-s1-s2-s3-s4b-s5-manifest478-s5b.tar.gz`（379246 字节，sha256 `01fe8e6f…832669a`）。当前唯一完整副本位于被忽略的目录中，沙箱的 `/tmp` 会被清空。
6. **残余风险 13（S5 的 q[1] 读数）。** 推荐：在下一次修复前核对 S5 的读取点，否则 S5 的一条数据可能有误。

---

## 12. 摘要语言说明

- 本报告为中文。代码标识符、文件名、变量名、公式与命令保留原文。
- S5 报告与 S1 摘要中的德语句子的翻译单独提交（`docs(p05): S5 language normalization`），不混入本报告的提交。
