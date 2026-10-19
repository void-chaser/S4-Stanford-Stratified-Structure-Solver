#!/usr/bin/env python3
# relr4_rulings.py -- P05 delivery round REL-R4 task brief section 1: append exactly five ruling rows
# U399-U403 to checkpoints/p05/registries/RULINGS.tsv.  No existing row is rewritten: the baseline is the
# file recorded by the start gate (bytes + sha256) and the script asserts the old prefix stays
# byte-identical and that exactly five well-formed rows were appended.
import os, sys, hashlib, subprocess

REPO = os.getcwd()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-rel-r4")
RUL = os.path.join(P05, "registries/RULINGS.tsv")
START = os.path.join(EV, "GATE_RELR4_start.txt")
TAB = chr(9)
NL = chr(10)


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def start_records():
    d = {}
    for line in open(START, encoding="utf-8"):
        if line.startswith("RECORD" + TAB):
            f = line.rstrip(NL).split(TAB)
            if len(f) >= 3:
                k, _, v = f[2].partition("=")
                d[f[1]] = v
    return d


ROWS = [
    ("U399", "P05 交付轮 REL-R4 任务书 §1（用户裁决）",
     "对照基准从“P05 修复前（B）”扩大到“原版 S4（U，上游 victorliu/S4 master 7fd00a2）”。"
     "目标是确认原版能跑通的，当前 F4 也能跑通；原版跑不通、当前能跑通的，记为改进。",
     "P05 交付轮 REL-R4 任务书 §1（用户裁决）"),
    ("U400", "P05 交付轮 REL-R4 任务书 §1（用户裁决）",
     "原版克隆必须放在本轮证据目录内，不放 /tmp 或其他仓库外路径。克隆保留为证据，不提交。",
     "P05 交付轮 REL-R4 任务书 §1（用户裁决）"),
    ("U401", "P05 交付轮 REL-R4 任务书 §1（用户裁决）",
     "原版只因 gcc 15 把 int-conversion 当错误而不能编译。允许在构建命令的环境变量里加 "
     "CFLAGS=-Wno-error=int-conversion，不改原版任何源文件和 Makefile。这一处是原版 Lua GetAmplitudes "
     "自身的 bug（fork 里已由 93b1c90 修复）；必须核实没有任何 example 调用 GetAmplitudes。",
     "P05 交付轮 REL-R4 任务书 §1（用户裁决）"),
    ("U402", "P05 交付轮 REL-R4 任务书 §1（用户裁决）",
     "用户已在本机安装 OpenMPI。MPI 示例这轮必须实际运行，不再声明跳过。",
     "P05 交付轮 REL-R4 任务书 §1（用户裁决）"),
    ("U403", "P05 交付轮 REL-R4 任务书 §1（用户裁决）",
     "C API 按原 examples/C_api/main.c 的逻辑，用当前公开 C API 新写测试程序，放在 "
     "testing/d003/stage_relr4/；原示例不动。它只是 P13 的提前检查，不算完成或修复 P13。",
     "P05 交付轮 REL-R4 任务书 §1（用户裁决）"),
]


def build_rows():
    out = b""
    for rid, src, body, basis in ROWS:
        out += (TAB.join([rid, src, body, basis, "生效"]) + NL).encode("utf-8")
    return out


def main():
    rec = start_records()
    if "RULINGS_SHA256" not in rec or "RULINGS_BYTES" not in rec:
        print("HARD_STOP start gate lacks the RULINGS baseline records")
        return 2
    base_sha = rec["RULINGS_SHA256"]
    base_bytes = int(rec["RULINGS_BYTES"])
    cur = open(RUL, "rb").read()
    if sha_b(cur) != base_sha or len(cur) != base_bytes:
        print("HARD_STOP RULINGS.tsv no longer matches the start-gate baseline")
        return 2
    if "U399" in cur.decode("utf-8") or "U403" in cur.decode("utf-8"):
        print("HARD_STOP RULINGS already contains U399/U403")
        return 2
    add = build_rows()
    with open(RUL, "ab") as fh:
        fh.write(add)
    new = open(RUL, "rb").read()
    if new[:len(cur)] != cur or sha_b(new[:len(cur)]) != base_sha:
        print("HARD_STOP RULINGS prefix changed")
        return 2
    appended = new[len(cur):]
    lines = [l for l in appended.decode("utf-8").split(NL) if l.strip()]
    if len(lines) != 5:
        print("HARD_STOP expected 5 appended rows, got %d" % len(lines))
        return 2
    ids = [l.split(TAB)[0] for l in lines]
    if ids != ["U399", "U400", "U401", "U402", "U403"]:
        print("HARD_STOP appended ids are %r" % ids)
        return 2
    for l in lines:
        if len(l.split(TAB)) != 5 or l.split(TAB)[4] != "生效":
            print("HARD_STOP malformed appended row")
            return 2
    body = ["# RULINGS_APPEND_RELR4.tsv -- P05 delivery round REL-R4 RULINGS.tsv append (U399-U403)",
            "# baseline = whole file before the append (recorded by the start gate)",
            "# before_bytes=%d before_sha256=%s" % (len(cur), base_sha),
            "# after_bytes=%d after_sha256=%s" % (len(new), sha_b(new)),
            "# prefix_bytes=%d prefix_sha256=%s prefix_unchanged=yes" % (len(cur), sha_b(new[:len(cur)])),
            "# rows_appended=%d" % len(lines),
            "id" + TAB + "source" + TAB + "given_in_round" + TAB + "status"]
    for l in lines:
        f = l.split(TAB)
        body.append(TAB.join([f[0], f[1], f[3], f[4]]))
    body.append("APPENDED_BYTES_SHA256=" + TAB + sha_b(appended))
    open(os.path.join(EV, "RULINGS_APPEND_RELR4.tsv"), "w", encoding="utf-8").write(NL.join(body) + NL)
    print("RULINGS before=%d/%s after=%d/%s rows_appended=%d" % (len(cur), base_sha[:16], len(new), sha_b(new)[:16], len(lines)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
