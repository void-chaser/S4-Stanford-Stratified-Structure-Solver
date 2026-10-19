#!/usr/bin/env python3
# relr3_rulings.py -- P05 delivery round REL-R3: append exactly six ruling rows U393-U398 to
# checkpoints/p05/registries/RULINGS.tsv (task brief section 1).  No existing row is rewritten: the
# baseline is the blob at HEAD (4607e96, whose last clause is U392) and the script asserts the old
# prefix stays byte-identical after the append.
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-rel-r3")
RUL = os.path.join(P05, "registries/RULINGS.tsv")
BASE_HEAD = "4607e969ba138f8bcaffa4fba6340dd3b2e1f25b"
TAB = chr(9)
NL = chr(10)


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


ROWS = [
    ("U393",
     "用户对话授权（P05 交付轮 REL-R3 任务书 §1）",
     "只授权以下远端写入，目标远端 origin = https://github.com/void-chaser/S4-Stanford-Stratified-Structure-Solver.git："
     "(a) git push origin refs/heads/p05/d003-fft-error-propagation:refs/heads/p05/d003-fft-error-propagation；"
     "(b) git push origin refs/heads/archive/p05-d003-full-20261019:refs/heads/archive/p05-d003-full-20261019；"
     "(c) git push origin refs/tags/p05-signed-20261019；"
     "(d) git push origin refs/tags/p05-rel-r1-20261019。"
     "一律不加 -f、--force-with-lease、--mirror、--all、--tags、--delete。"
     "不推 codex/*、master 或其它任何 ref。不向上游 victorliu/S4 写任何东西。",
     "P05 交付轮 REL-R3 任务书 §1（用户授权）",
     "生效"),
    ("U394",
     "用户对话授权（P05 交付轮 REL-R3 任务书 §1）",
     "本地引用：主仓库只允许追加执行 git branch archive/p05-d003-full-20261019 4607e96"
     "（若已存在则停下报告，不得 -f），以及 push 时 git 自动更新 refs/remotes/origin/*。"
     "其余禁令照旧：不得 checkout、switch、reset、stash、clean、gc、prune、fsck、worktree。",
     "P05 交付轮 REL-R3 任务书 §1（用户授权）",
     "生效"),
    ("U395",
     "用户对话授权（P05 交付轮 REL-R3 任务书 §1）",
     "PR：用 gh 在 fork 内开一个 Draft PR：--repo void-chaser/S4-Stanford-Stratified-Structure-Solver "
     "--base master --head p05/d003-fft-error-propagation --draft，正文来自 $EV/PR_BODY_RELR3.md"
     "（用 --body-file）。不得 merge、不得 ready-for-review、不得加 reviewer，不向上游开 PR。",
     "P05 交付轮 REL-R3 任务书 §1（用户授权）",
     "生效"),
    ("U396",
     "用户裁决（P05 交付轮 REL-R3 任务书 §1）",
     "ROADMAP 和 ISSUE_REGISTRY 不带入产品分支，它们的全文随归档分支推送。",
     "P05 交付轮 REL-R3 任务书 §1（用户裁决）",
     "生效"),
    ("U397",
     "用户裁决（P05 交付轮 REL-R3 任务书 §1）",
     "敏感信息命中（绝对路径、用户名、上游作者邮箱）接受现状，不改写历史。"
     "前提是 §3 的补扫中 token/密钥类仍为 0；不为 0 就停下，不推送。",
     "P05 交付轮 REL-R3 任务书 §1（用户裁决）",
     "生效"),
    ("U398",
     "用户裁决（P05 交付轮 REL-R3 任务书 §1）",
     "证据离线备份由用户手工执行。本轮只产出备份命令清单和只读校验脚本，不执行备份，不写仓库外路径。",
     "P05 交付轮 REL-R3 任务书 §1（用户裁决）",
     "生效"),
]


def main():
    base = subprocess.run(["git", "show", BASE_HEAD + ":checkpoints/p05/registries/RULINGS.tsv"],
                          cwd=REPO, capture_output=True).stdout
    if not base.endswith(NL.encode("utf-8")):
        print("HARD_STOP RULINGS baseline does not end with a newline")
        return 2
    cur_disk = open(RUL, "rb").read()
    if cur_disk != base:
        print("HARD_STOP RULINGS.tsv differs from the committed baseline (bytes=%d/%d)" % (len(cur_disk), len(base)))
        return 2
    text = base.decode("utf-8")
    if "U393" in text:
        print("HARD_STOP RULINGS already contains U393")
        return 2
    payload = "".join(TAB.join(f) + NL for f in ROWS).encode("utf-8")
    with open(RUL, "ab") as fh:
        fh.write(payload)
    cur = open(RUL, "rb").read()
    if cur[:len(base)] != base or sha_b(cur[:len(base)]) != sha_b(base):
        print("HARD_STOP RULINGS prefix changed")
        return 2
    appended = cur[len(base):]
    lines = [l for l in appended.decode("utf-8").split(NL) if l.strip()]
    if len(lines) != 6:
        print("HARD_STOP expected exactly six appended rows, got %d" % len(lines))
        return 2
    ids = [l.split(TAB)[0] for l in lines]
    if ids != ["U393", "U394", "U395", "U396", "U397", "U398"]:
        print("HARD_STOP appended row ids are wrong: " + ",".join(ids))
        return 2
    if not all(len(l.split(TAB)) == 5 and l.split(TAB)[4] == "生效" for l in lines):
        print("HARD_STOP appended row shape is wrong")
        return 2
    row_shas = [sha_b((l + NL).encode("utf-8")) for l in lines]
    body = ["# RULINGS_APPEND_RELR3.tsv -- P05 delivery round REL-R3 RULINGS.tsv append (U393-U398, user rulings)",
            "# baseline = blob at HEAD " + BASE_HEAD + " (last clause U392)",
            "# before_bytes=%d before_sha256=%s" % (len(base), sha_b(base)),
            "# after_bytes=%d after_sha256=%s" % (len(cur), sha_b(cur)),
            "# prefix_bytes=%d prefix_sha256=%s prefix_unchanged=yes" % (len(base), sha_b(cur[:len(base)])),
            "# rows_appended=%d payload_bytes=%d payload_sha256=%s" % (len(lines), len(payload), sha_b(payload)),
            TAB.join(["row_index", "id", "fields", "status", "row_sha256", "source"]),
            "# Columns: row_index, id, fields, status, row_sha256, source"]
    # put the column header before the record rows (the comment line is skipped by readers)
    body = body[:-1] + [TAB.join(["row_index", "id", "fields", "status", "row_sha256"])]
    for i, l in enumerate(lines, 1):
        f = l.split(TAB)
        body.append(TAB.join([str(i), f[0], "5", f[4], row_shas[i - 1]]))
    open(os.path.join(EV, "RULINGS_APPEND_RELR3.tsv"), "w", encoding="utf-8").write(NL.join(body) + NL)
    print("RULINGS before=%d/%s after=%d/%s rows=6" % (len(base), sha_b(base), len(cur), sha_b(cur)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
