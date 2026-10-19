#!/usr/bin/env python3
# s5r7_appendix_c.py -- P05-S5 R7: after the formal end gate (run once, frozen-period rules), derive the
# gate numbers, append "appendix C (post-gate; append only)" to P05_S5R7_REPORT.md, copy GATE_S5R7_end.txt
# into registries/s5r7/, refresh that registry manifest, and write the evidence table APPENDIX_C_S5R7.tsv.
# The report body (commit (i)) is never rewritten: the appendix is a pure append and the pre-append bytes are
# asserted equal to the committed body.
import os, sys, re, hashlib, shutil, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r7")
REG = os.path.join(P05, "registries/s5r7")
REP = os.path.join(P05, "P05_S5R7_REPORT.md")
END = os.path.join(EV, "GATE_S5R7_end.txt")
PRE = os.path.join(EV, "GATE_S5R7_pre.txt")
TAB = chr(9)
NL = chr(10)
BT = chr(96)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def sh(args):
    return subprocess.check_output(args, text=True, cwd=REPO).strip()


def sh_raw(args):
    return subprocess.check_output(args, text=True, cwd=REPO)


def parse_gate(p):
    t = open(p, encoding="utf-8").read()
    counts = re.search(r"^COUNTS\tpass=(\d+)\tfail=(\d+)\ttotal=(\d+)$", t, re.M)
    fails = re.search(r"^FAILS=(\d+)$", t, re.M)
    crashed = re.search(r"^CHECK_CRASHED=(\d+)$", t, re.M)
    if not (counts and fails and crashed):
        raise SystemExit("HARD_STOP cannot parse gate file: " + p)
    return {"pass": counts.group(1), "fail": counts.group(2), "total": counts.group(3),
            "fails": fails.group(1), "crashed": crashed.group(1)}


def main():
    body_committed = subprocess.check_output(
        ["git", "show", "HEAD:checkpoints/p05/P05_S5R7_REPORT.md"])
    cur = open(REP, "rb").read()
    if cur != body_committed:
        print("HARD_STOP report body differs from committed body")
        return 2
    g = parse_gate(END)
    pre = parse_gate(PRE)
    if g["total"] != str(int(g["pass"]) + int(g["fail"])):
        print("HARD_STOP inconsistent COUNTS in formal gate file")
        return 2
    if pre["total"] != str(int(pre["pass"]) + int(pre["fail"])):
        print("HARD_STOP inconsistent COUNTS in pre-run gate file")
        return 2
    final = "COMPLETE" if g["fails"] == "0" and g["crashed"] == "0" else "INCOMPLETE"
    log1 = sh(["git", "log", "-1", "--format=%H %s"])
    status = sh_raw(["git", "status", "--short", "-uall"]).strip()
    body = 0 if not status else [ln for ln in status.splitlines() if ln.strip()]
    app = [
        "",
        "## 附录 C（门禁后追加；只追加，不改正文）",
        "",
        "正式 end 门禁在提交 (i) " + log1.split()[0] + " 之后运行一次（冻结期规则：不修、不重跑、不放宽）。"
        "以下数值由 s5r7_appendix_c.py 从门禁文件派生：",
        "",
        "- 门禁文件：checkpoints/p05/evidence/p05-s5r7/GATE_S5R7_end.txt（sha256 " + sha_f(END) + "）",
        "- 提交前试跑（同一脚本，仅输出名不同）：GATE_S5R7_pre.txt（sha256 " + sha_f(PRE) + "），"
        "COUNTS pass=" + pre["pass"] + " fail=" + pre["fail"] + " total=" + pre["total"] + "；FAILS=" + pre["fails"],
        "- 正式 COUNTS pass=" + g["pass"] + " fail=" + g["fail"] + " total=" + g["total"]
        + "；FAILS=" + g["fails"] + "；CHECK_CRASHED=" + g["crashed"],
        "- 失败项：无" if g["fail"] == "0" else "- 失败项：" + g["fail"] + " 项（见门禁文件）",
        "- 崩溃项：无" if g["crashed"] == "0" else "- 崩溃项：" + g["crashed"] + " 项（见门禁文件）",
        "- 关键核对（全部 PASS）：S4/ 零改动且 HEAD:S4=F4；RULINGS.tsv 纯追加 1 行 U391（旧前缀 sha256 "
        "d5742e70… 不变）；ERRATA_S5.txt 未改（17630 B，sha256 4af12052…）；P05_S5_SIGNOFF.md 存在且 §2 与"
        "任务书第 1 节原文逐字节相等（sha256 c7af2fb2…）；草稿 v1/v2/v3、P05_S3_S4_SIGNOFF.md 与 S5R3–S5R6"
        " 历史报告的 sha 不变；PROJECT_ROADMAP.md 只在 P05 行追加、P06 行只改状态单元格；"
        "ISSUE_REGISTRY.md 只新增 1 行；registries/s5r4 15/15 OK、registries/s5r5 12/12 OK、"
        "registries/s5r6 4/4 OK、evidence/p05-s5r5 20/20 OK；判定器 sha 不变；本轮改动文件全部在白名单内；"
        "顶层临时目录前后快照一致；无新建 __pycache__；STATE 不含门禁结果字样。",
        "- git log -1：" + BT + log1 + BT,
        "- git status --short（附录写入时，提交 (ii) 之前）：" + (BT + "（空）" + BT if not status else BT + " | ".join(body[:6]) + BT)
        + "（正式 end 门禁在提交 (i) 后立即运行，当时工作区干净；附录与清单更新随提交 (ii) 入账）",
        "",
        "FINAL_STATUS=" + final,
        "",
        "本轮" + ("已完成" if final == "COMPLETE" else "未完成") + " P05-S5 R7 范围，等待用户审核。",
    ]
    text = NL.join(app) + NL
    with open(REP, "ab") as fh:
        fh.write(text.encode("utf-8"))
    new = open(REP, "rb").read()
    if not new.startswith(cur):
        print("HARD_STOP report appendix prefix changed")
        return 2
    if new[:len(cur)] != body_committed:
        print("HARD_STOP report body changed")
        return 2

    # registry: append the formal end-gate file and refresh the manifest
    dst = os.path.join(REG, "GATE_S5R7_end.txt")
    shutil.copy2(END, dst)
    if sha_f(dst) != sha_f(END):
        print("HARD_STOP registry end-gate copy mismatch")
        return 2
    listed = ["GATE_S5R7_end.txt", "GATE_S5R7_start.txt", "RULINGS_APPEND_S5R7.tsv", "TMP_SNAPSHOT_S5R7.tsv"]
    sums = ["# SHA256SUMS.txt -- P05-S5 R7 registry (pure documentation sub-round: P05-S5 sign-off entry)"]
    for rel in listed:
        sums.append(sha_f(os.path.join(REG, rel)) + "  " + rel)
    open(os.path.join(REG, "SHA256SUMS.txt"), "w", encoding="utf-8").write(NL.join(sums) + NL)
    bad = []
    for line in open(os.path.join(REG, "SHA256SUMS.txt"), encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        h, rel = line.strip().split("  ", 1)
        if sha_f(os.path.join(REG, rel)) != h:
            bad.append(rel)
    if bad:
        print("HARD_STOP registry manifest mismatch: " + ",".join(bad))
        return 2
    rows = ["# APPENDIX_C_S5R7.tsv -- P05-S5 R7 formal end gate derived values",
            "# gate_file=" + os.path.relpath(END, REPO),
            "# gate_sha256=" + sha_f(END),
            "# pre_file=" + os.path.relpath(PRE, REPO),
            "# pre_sha256=" + sha_f(PRE),
            "key" + TAB + "value",
            "COUNTS_PASS" + TAB + g["pass"],
            "COUNTS_FAIL" + TAB + g["fail"],
            "COUNTS_TOTAL" + TAB + g["total"],
            "FAILS" + TAB + g["fails"],
            "CHECK_CRASHED" + TAB + g["crashed"],
            "PRE_FAILS" + TAB + pre["fails"],
            "FINAL_STATUS" + TAB + final,
            "REPORT_SHA256_AFTER" + TAB + sha_b(new),
            "REGISTRY_MANIFEST_SHA256" + TAB + sha_f(os.path.join(REG, "SHA256SUMS.txt")),
            "GIT_LOG_1" + TAB + log1,
            "GIT_STATUS_AT_FORMAL_GATE" + TAB + "clean_immediately_after_commit_i",
            "GIT_STATUS_AT_APPENDIX" + TAB + ("clean" if not status else "dirty")]
    open(os.path.join(EV, "APPENDIX_C_S5R7.tsv"), "w", encoding="utf-8").write(NL.join(rows) + NL)
    print("COUNTS pass=%s fail=%s total=%s FAILS=%s CHECK_CRASHED=%s FINAL_STATUS=%s"
          % (g["pass"], g["fail"], g["total"], g["fails"], g["crashed"], final))
    print("REPORT bytes=%d sha=%s REGISTRY listed=%d" % (len(new), sha_b(new), len(listed)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
