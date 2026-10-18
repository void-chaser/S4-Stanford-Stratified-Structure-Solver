#!/usr/bin/env python3
# append_rulings_r9m1r4.py -- Append rulings U323..U327 to RULINGS.tsv (Step S-C). New file.
import os, sys, subprocess

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
RUL_PATH = os.path.join(REPO, "checkpoints", "p05", "registries", "RULINGS.tsv")

def main():
    if not os.path.isfile(RUL_PATH):
        print(f"RULINGS.tsv missing at {RUL_PATH}", file=sys.stderr)
        sys.exit(1)

    old_content = open(RUL_PATH, "r", encoding="utf-8").read()
    
    # Assert git prefix
    head_content = subprocess.check_output(["git", "show", "HEAD:checkpoints/p05/registries/RULINGS.tsv"], cwd=REPO, text=True)
    if not old_content.startswith(head_content):
        print("Prefix assertion failed: RULINGS.tsv diverged from HEAD", file=sys.stderr)
        sys.exit(1)

    # Assert last U number is U322
    lines = [l.strip() for l in old_content.splitlines() if l.strip() and not l.startswith("#")]
    last_u = lines[-1].split("\t")[0]
    if last_u != "U322":
        print(f"Assertion failed: last U number is {last_u}, expected U322", file=sys.stderr)
        sys.exit(1)

    new_rulings = [
        ("U323", "P05-S4 R9 M1 第三修正轮任务书 §3", "r9m1r3 的物理事实（m1r3/runs/formal 下两遍 FORMAL_FACTS，sha 090797d8… 和 85b1f158…）不重跑。r9m1r3 的 VERDICT、F3_F4_EQUIV、M1_SUMMARY 在本轮复核（S-D）通过后成为 M1 的有效结果，本轮报告和 STATE 作为它们的核证。复核不一致时，以本轮独立复算的结果为准，并列入'需用户裁决'。", "P05-S4 R9 M1 第三修正轮任务书 §3", "生效"),
        ("U324", "P05-S4 R9 M1 第三修正轮任务书 §3", "H-1 写入 m1r2 证据目录属于硬停止违规，按已披露接受，不追认为合规。现存 3 个文件的内容经本轮核对等于 m1r2 清单记录值，不再处理。", "P05-S4 R9 M1 第三修正轮任务书 §3", "生效"),
        ("U325", "P05-S4 R9 M1 第三修正轮任务书 §3", "H-2、H-3、H-6、H-7 按事实登记为勘误。r9m1r3 已提交的 EVENTS、SHA256SUMS 不改，由本轮按冻结逻辑重算的 EVENTS_RECALC_R9M1R3.tsv 和 SHA_RECHECK_R9M1R3.tsv 作为更正件。", "P05-S4 R9 M1 第三修正轮任务书 §3", "生效"),
        ("U326", "P05-S4 R9 M1 第三修正轮任务书 §3", "r9m1r3 的 end 门禁没有执行的那几项断言，由本轮 recert 脚本以只读方式补做，结果写进 RECERT_R9M1R3.tsv。GATE_R9M1R3_end.txt 保持原样。", "P05-S4 R9 M1 第三修正轮任务书 §3", "生效"),
        ("U327", "P05-S4 R9 M1 第三修正轮任务书 §3", "K 的命中数以 K_COUNT_R9M1R3（总数）为准。K_INHERIT_R9M1R2 中 hits 列的含义按 H-8 的复核结果，在 K_RECON_R9M1R4.tsv 里说明。", "P05-S4 R9 M1 第三修正轮任务书 §3", "生效"),
    ]

    new_lines = []
    for r in new_rulings:
        if len(r) != 5:
            print("Ruling fields != 5", file=sys.stderr)
            sys.exit(1)
        new_lines.append("\t".join(r))

    to_append = "\n".join(new_lines) + "\n"
    new_content = old_content + to_append

    # Assert new file = old file + new lines
    assert new_content == old_content + to_append
    assert new_content.startswith(old_content)

    with open(RUL_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Appended {len(new_rulings)} rulings (U323..U327). New bytes: {len(new_content.encode('utf-8'))}.")

if __name__ == "__main__":
    main()
