#!/usr/bin/env python3
# relr2_rulings.py -- P05 delivery round REL-R2 task brief section 2: append exactly one ruling row U392
# to checkpoints/p05/registries/RULINGS.tsv.  No existing row is rewritten: the baseline is the blob at
# HEAD (c88bf30) and the script asserts the old prefix stays byte-identical after the append.
import os, sys, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-rel-r2")
RUL = os.path.join(P05, "registries/RULINGS.tsv")
BASE_HEAD = "c88bf30954a356e1cbdd49cf7a53218778c0ae3e"
TAB = chr(9)
NL = chr(10)


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def build_row():
    fields = [
        "U392",
        "用户对话授权（P05 交付轮 REL-R2 任务书 §2）",
        "授权本轮在主仓库执行以下 .git 引用写入且仅限这些：(a) git tag -a p05-signed-20261019 3de6d8b "
        "-m \"P05 S1-S5 signed off (U391)\"；(b) git tag -a p05-rel-r1-20261019 c88bf30 "
        "-m \"P05 REL-R1 non-regression PASS\"；(c) 用 git fetch <本地克隆路径> "
        "p05/d003-fft-error-propagation:p05/d003-fft-error-propagation 在主仓库创建产品分支引用；"
        "(d) 正常 git commit（仅当前工作分支）。主仓库仍禁止 checkout/switch/reset/stash/clean/gc/prune/fsck/worktree；"
        "产品分支只能在 $EV 下的独立本地克隆中构建（克隆内的 checkout -b、commit 允许）。若标签或分支名已存在则停下报告，"
        "不得覆盖、不得 -f。",
        "P05 交付轮 REL-R2 任务书 §2（用户授权）",
        "生效",
    ]
    return (TAB.join(fields) + NL).encode("utf-8")


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
    if "U392" in base.decode("utf-8"):
        print("HARD_STOP RULINGS already contains U392")
        return 2
    row = build_row()
    with open(RUL, "ab") as fh:
        fh.write(row)
    cur = open(RUL, "rb").read()
    if cur[:len(base)] != base or sha_b(cur[:len(base)]) != sha_b(base):
        print("HARD_STOP RULINGS prefix changed")
        return 2
    appended = cur[len(base):]
    lines = [l for l in appended.decode("utf-8").split(NL) if l.strip()]
    if len(lines) != 1:
        print("HARD_STOP expected exactly one appended row, got %d" % len(lines))
        return 2
    fields = lines[0].split(TAB)
    if len(fields) != 5 or fields[0] != "U392" or fields[4] != "生效":
        print("HARD_STOP appended row shape is wrong")
        return 2
    body = ["# RULINGS_APPEND_RELR2.tsv -- P05 delivery round REL-R2 RULINGS.tsv append (U392, user authorisation)",
            "# baseline = blob at HEAD " + BASE_HEAD,
            "# before_bytes=%d before_sha256=%s" % (len(base), sha_b(base)),
            "# after_bytes=%d after_sha256=%s" % (len(cur), sha_b(cur)),
            "# prefix_bytes=%d prefix_sha256=%s prefix_unchanged=yes" % (len(base), sha_b(cur[:len(base)])),
            "# rows_appended=1 new_row_id=U392 row_bytes=%d row_sha256=%s" % (len(row), sha_b(row)),
            "id" + TAB + "given_in_round" + TAB + "fields" + TAB + "status",
            fields[0] + TAB + fields[1] + TAB + "5" + TAB + fields[4],
            "ROW_SHA256" + TAB + sha_b(row)]
    open(os.path.join(EV, "RULINGS_APPEND_RELR2.tsv"), "w", encoding="utf-8").write(NL.join(body) + NL)
    print("RULINGS before=%d/%s after=%d/%s row_sha=%s" % (len(base), sha_b(base), len(cur), sha_b(cur), sha_b(row)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
