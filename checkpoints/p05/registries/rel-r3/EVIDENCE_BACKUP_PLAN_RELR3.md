# 证据离线备份计划（REL-R3，用户手工执行）

> 任务书 §1 U398：证据离线备份由用户手工执行。**本轮不执行备份、不写仓库外路径**；本文件只给出
> 命令清单和只读校验步骤。备份介质与是否包含克隆目录由用户决定。

## 1 备份范围与体积

- 主目标：`checkpoints/p05/evidence/`（各轮证据目录与各轮 `SHA256SUMS.txt`）。
- 次目标：`checkpoints/p05/registries/`（小型结果表，已在 git 中；随仓库备份即可）。
- 当前 `checkpoints/p05/evidence` 约 11.5 GiB（以本轮 end 审计的实测值为准）。
- **可以排除**（可由产品分支/远端重建，不进入离线备份）：
  - `checkpoints/p05/evidence/p05-rel-r2/prod`（产品分支独立本地克隆）
  - `checkpoints/p05/evidence/p05-rel-r2/verifyclone`（REL-R2 验证克隆）
  - `checkpoints/p05/evidence/p05-rel-r3/remoteclone`（REL-R3 远端新克隆）
  - 任何轮的 `tmp/` 目录

## 2 备份命令（在仓库根执行，目标介质路径由用户填写）

建议至少两份离线介质。先确认介质已挂载且路径存在，再执行：

```sh
# 变量：目标介质挂载点
MEDIA=/media/<user>/P05_BACKUP_1

# 方式 A：增量 rsync（保留证据目录结构；排除可重建的克隆与 tmp）
rsync -aH --info=progress2 \
  --exclude 'p05-rel-r2/prod/' \
  --exclude 'p05-rel-r2/verifyclone/' \
  --exclude 'p05-rel-r3/remoteclone/' \
  --exclude 'tmp/' \
  checkpoints/p05/evidence/ "$MEDIA/evidence/"

# 小表与清单（体积小，建议一并备份）
rsync -aH checkpoints/p05/registries/ "$MEDIA/registries/"
```

```sh
# 方式 B：单文件归档（便于异地保存；同样排除可重建目录）
tar -C checkpoints/p05 \
  --exclude='evidence/p05-rel-r2/prod' \
  --exclude='evidence/p05-rel-r2/verifyclone' \
  --exclude='evidence/p05-rel-r3/remoteclone' \
  --exclude='evidence/*/tmp' \
  -czf "$MEDIA/p05-evidence-relr3.tar.gz" evidence registries
```

## 3 只读校验步骤（备份完成后执行）

1. **逐轮清单校验**：对每个证据目录执行 `sha256sum -c`（只读）：

   ```sh
   for f in "$MEDIA"/evidence/*/SHA256SUMS.txt; do
       ( cd "$(dirname "$f")" && sha256sum -c SHA256SUMS.txt )
   done
   ```

   每个 `SHA256SUMS.txt` 的说明行会注明被排除的文件（如 `safe_run.log`、门禁输出、`SHA256SUMS.txt` 自身）；
   这些排除项不应报缺失。

2. **统一校验脚本（只读）**：本轮新增的 `testing/d003/stage_relr3/relr3_backup_verify.py` 遍历介质路径下
   所有 `SHA256SUMS.txt`，逐项重算 sha256（对介质只读），并把报告写到本轮证据目录：

   ```sh
   python3 testing/d003/stage_relr3/relr3_backup_verify.py \
       --media "$MEDIA" \
       --out checkpoints/p05/evidence/p05-rel-r3/BACKUP_VERIFY_RELR3.tsv
   ```

   期望输出行：`VERDICT PASS`（missing=0、bad=0）。该脚本**只读介质**，写入仅限 `$EV/`。
   本轮不运行该脚本去访问仓库外路径（U398）。

3. **归档方式校验**：若用方式 B，先 `tar -tzf` 列表核对，再解包到**新的空目录**后重复第 1 步。

## 4 本轮不做什么

- 不执行任何备份/压缩命令；不创建 `/media/` 或其它仓库外路径。
- 不修改、不删除现有证据目录。
- 备份是否完成、介质选择、是否包含上述克隆目录，留给用户（见报告 §9）。
