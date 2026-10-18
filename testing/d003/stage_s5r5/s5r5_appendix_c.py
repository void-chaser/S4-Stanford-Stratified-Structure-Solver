#!/usr/bin/env python3
# s5r5_appendix_c.py -- AFTER the one formal end-gate run: derive appendix C (COUNTS / FAILS / CHECK_CRASHED /
# FINAL_STATUS) from the gate file, append it to the report, copy the gate file into registries/s5r5/ and update
# the registry manifest. Nothing else is written (task brief section 7 freeze rule).
import os, sys, re, hashlib, shutil, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
REG = os.path.join(P05, "registries/s5r5")
REPORT = os.path.join(P05, "P05_S5R5_REPORT.md")
GATE_OUT = os.path.join(EV, "gate/GATE_S5R5_end.txt")
NL = chr(10)
TAB = chr(9)


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    if not os.path.isfile(GATE_OUT):
        print("HARD_STOP formal gate output missing: " + os.path.relpath(GATE_OUT, REPO))
        return 2
    t = open(GATE_OUT, encoding="utf-8").read()
    mf = re.search(r"^FAILS=(\d+)$", t, re.M)
    mc = re.search(r"^CHECK_CRASHED=(\d+)$", t, re.M)
    mcounts = re.search(r"^COUNTS\t(pass=\d+)\t(fail=\d+)\t(total=\d+)$", t, re.M)
    if not (mf and mc and mcounts):
        print("HARD_STOP cannot derive COUNTS/FAILS/CHECK_CRASHED from the gate file")
        return 2
    fails = int(mf.group(1))
    crashed = int(mc.group(1))
    final = "COMPLETE" if (fails == 0 and crashed == 0) else "INCOMPLETE"
    fails_lines = [l for l in t.splitlines() if l.startswith("FAIL" + TAB)]
    crashed_lines = [l for l in t.splitlines() if l.startswith("CRASHED" + TAB)]
    body = ["", "## 附录 C（门禁后追加；只追加，不改正文）", "",
            "正式 end 门禁运行一次（冻结期规则：不修、不重跑、不放宽）。以下 COUNTS/FAILS/CHECK_CRASHED/FINAL_STATUS 全部由 s5r5_appendix_c.py 从门禁文件派生：", "",
            "- 门禁文件：checkpoints/p05/evidence/p05-s5r5/gate/GATE_S5R5_end.txt（sha256 " + sha_f(GATE_OUT) + "）",
            "- " + mcounts.group(0).replace(TAB, " ") + "；失败数=" + str(fails) + "；检查器崩溃数=" + str(crashed),
            "- 失败项：" + ("无" if not fails_lines else "；".join(l.replace(TAB, " ") for l in fails_lines)),
            "- 崩溃项：" + ("无" if not crashed_lines else "；".join(l.replace(TAB, " ") for l in crashed_lines)),
            "",
            "FINAL_STATUS=" + final,
            "",
            ("本轮已完成 P05-S5 R5 范围，等待用户审核。" if final == "COMPLETE"
             else "本轮未完成 P05-S5 R5 范围，等待用户审核。"),
            ""]
    with open(REPORT, "a", encoding="utf-8") as fh:
        fh.write(NL.join(body) + NL)
    # registry: copy the formal gate file and update the manifest
    os.makedirs(REG, exist_ok=True)
    dst = os.path.join(REG, "GATE_S5R5_end.txt")
    shutil.copy2(GATE_OUT, dst)
    files = []
    for root, dirs, fs in os.walk(REG):
        for f in fs:
            rel = os.path.relpath(os.path.join(root, f), REG)
            if rel == "SHA256SUMS.txt":
                continue
            files.append(rel)
    files.sort()
    sums = ["# SHA256SUMS.txt -- P05-S5 R5 registry (r4_final/ is the frozen R4 errata snapshot; GATE_S5R5_end.txt appended after the gate)"]
    for rel in files:
        sums.append(sha_f(os.path.join(REG, rel)) + "  " + rel)
    open(os.path.join(REG, "SHA256SUMS.txt"), "w", encoding="utf-8").write(NL.join(sums) + NL)
    print("APPENDIX_C appended counts=%s fails=%d crashed=%d FINAL_STATUS=%s" % (mcounts.group(0), fails, crashed, final))
    print("REGISTRY gate file copied; manifest items=%d" % len(files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
