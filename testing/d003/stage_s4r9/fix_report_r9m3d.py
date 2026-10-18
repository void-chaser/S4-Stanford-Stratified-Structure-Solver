#!/usr/bin/env python3
# fix_report_r9m3d.py -- post-end-gate step: replace the appendix-B placeholder in the report with the formal end-gate
# table, the git log -1 / git status --short footer and the registry count. It does not change appendix A and runs
# after the end gate (outside the frozen chain). New file (r9m3d).
# usage: fix_report_r9m3d.py REPORT [GATE_END]
import os, sys, re, subprocess
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
REG_DEST = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M3d")
TAB = chr(9)
NL = chr(10)
PH_B = "（APPENDIX_B_PLACEHOLDER）"


def sh(cmd):
    return subprocess.check_output(cmd, cwd=REPO, text=True, stderr=subprocess.STDOUT).strip()


def main():
    rep = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "checkpoints/p05/P05_S4R9_M3d_REPORT.md")
    gate = sys.argv[2] if len(sys.argv) > 2 else os.path.join(EV, "gate/GATE_R9M3D_end.txt")
    if not os.path.isfile(gate):
        print("HARD_STOP missing end gate file " + gate)
        return 2
    txt = open(rep, encoding="utf-8").read()
    if txt.count(PH_B) != 1:
        print("HARD_STOP appendix-B placeholder count %d" % txt.count(PH_B))
        return 2
    rc = os.path.join(EV, "REPORT_CHECK_R9M3D.txt")
    if not os.path.isfile(rc):
        print("HARD_STOP missing report check output")
        return 2
    fails = -1
    for line in open(rc, encoding="utf-8"):
        if line.startswith("FAILS="):
            fails = int(line.strip().split("=")[1])
    if fails != 0:
        print("HARD_STOP report check FAILS=%d" % fails)
        return 2
    rows = []
    counts = ""
    fails_line = ""
    for line in open(gate, encoding="utf-8"):
        line = line.rstrip("\r\n")
        if not line.strip():
            continue
        if line.startswith("COUNTS"):
            counts = line
            continue
        if line.startswith("FAILS="):
            fails_line = line
            continue
        f = line.split(TAB)
        if f[0] in ("PASS", "FAIL", "SKIP") and len(f) >= 4:
            exp = f[2].replace("expected=", "")
            act = f[3].replace("actual=", "")
            rows.append((f[0], f[1], exp[:90], act[:90]))
    reg_files = sorted(os.listdir(REG_DEST)) if os.path.isdir(REG_DEST) else []
    ap = ["### 附录 B（end 门禁）", "",
          "| 状态 | 检查 | 期望 | 实际 |", "|---|---|---|---|"]
    for st, name, exp, act in rows:
        ap.append("| %s | %s | %s | %s |" % (st, name, exp.replace("|", "/"), act.replace("|", "/")))
    ap.append("")
    ap.append("- " + counts.replace(TAB, "；"))
    ap.append("- " + fails_line)
    ap.append("- 该门禁在冻结期为唯一一次运行；输出位于 m3d/gate/GATE_R9M3D_end.txt，不纳入 $EV/SHA256SUMS.txt。")
    ap.append("")
    ap.append("git log -1（记录提交 (i)）：" + sh(["git", "log", "-1", "--format=%h %s"]))
    ap.append("")
    ap.append("git status --short（附录 B 落盘前、收尾提交 (ii) 前）：")
    ap.append("")
    for line in sh(["git", "status", "--short", "-uall"]).splitlines():
        ap.append(line)
    ap.append("")
    ap.append("（registries/s4r9/M3d/ 下 %d 个文件 = %d 项小表 + SHA256SUMS.txt，将在收尾提交 (ii) 一并提交。）" % (
        len(reg_files), max(0, len(reg_files) - 1)))
    new = txt.replace(PH_B, NL.join(ap))
    open(rep, "wb").write(new.encode("utf-8"))
    print("appendix B rows=%d reg_files=%d" % (len(rows), len(reg_files)))
    print("report bytes %d -> %d" % (len(txt.encode("utf-8")), len(new.encode("utf-8"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
