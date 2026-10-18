#!/usr/bin/env python3
# s5r5_shakedown_verify.py -- verify the staging end-gate output OUTSIDE the gate (U388).
# Requires: FAILS=0, CHECK_CRASHED=0, every gate check name present exactly once with PASS, and the EV_ROOT /
# P05_ROOT records pointing into the staging tree. Writes SHAKEDOWN_REHEARSAL.txt and APPENDIX_A_S5R5.txt
# (the report appendix A is appended from it before commit (i)).
import os, sys, re, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r5")
STAGE = os.path.join(EV, "shakedown")
GATE = os.path.join(REPO, "testing/d003/stage_s5r5/gate_check_s5r5.py")
OUT = os.path.join(STAGE, "gate/GATE_S5R5_end.txt")
TAB = chr(9)
NL = chr(10)
SHAKEDOWN_PREFIX = "checkpoints/p05/evidence/p05-s5r5/shakedown/"


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def rd(p):
    return open(p, encoding="utf-8").read()


def main():
    if not os.path.isfile(OUT):
        print("HARD_STOP staging gate output missing: " + os.path.relpath(OUT, REPO))
        return 2
    t = rd(OUT)
    names = re.findall(r'add\("([A-Z0-9_]+)"', rd(GATE))
    res = {}
    for line in t.splitlines():
        f = line.split(TAB)
        if len(f) >= 2 and f[0] in ("PASS", "FAIL"):
            res.setdefault(f[1], []).append(f[0])
    missing = [n for n in names if len(res.get(n, [])) != 1]
    notpass = [n for n in names if res.get(n) == ["FAIL"]]
    fails = re.search(r"^FAILS=(\d+)$", t, re.M)
    crashed = re.search(r"^CHECK_CRASHED=(\d+)$", t, re.M)
    counts = re.search(r"^COUNTS\t(pass=\d+)\t(fail=\d+)\t(total=\d+)$", t, re.M)
    rec = {}
    for line in t.splitlines():
        f = line.split(TAB)
        if len(f) >= 3 and f[0] == "RECORD":
            rec[f[1]] = f[2].replace("value=", "")
    ev_root = rec.get("EV_ROOT", "")
    p05_root = rec.get("P05_ROOT", "")
    roots_ok = ev_root.startswith(SHAKEDOWN_PREFIX) and p05_root.startswith(SHAKEDOWN_PREFIX)
    ok = (fails and fails.group(1) == "0" and crashed and crashed.group(1) == "0"
          and not missing and not notpass and roots_ok and counts)
    lines = ["# SHAKEDOWN_REHEARSAL.txt -- P05-S5 R5 staging rehearsal (U388)",
             "SHAKEDOWN_GATE_OUTPUT=" + os.path.relpath(OUT, REPO),
             "SHAKEDOWN_GATE_SHA256=" + sha_f(OUT),
             "SHAKEDOWN_GATE_SCRIPT=" + os.path.relpath(GATE, REPO),
             "SHAKEDOWN_GATE_SCRIPT_SHA256=" + sha_f(GATE),
             "STAGING_EV_ROOT=" + ev_root,
             "STAGING_P05_ROOT=" + p05_root,
             "ROOTS_ARE_STAGING=" + ("yes" if roots_ok else "no"),
             "CHECKS_EXPECTED=" + str(len(names)),
             "CHECKS_PRESENT_ONCE=" + str(len([n for n in names if len(res.get(n, [])) == 1])),
             "CHECKS_PASS=" + str(len([n for n in names if res.get(n) == ["PASS"]])),
             "CHECKS_FAIL=" + str(len(notpass)),
             "MISSING=" + (",".join(missing[:5]) if missing else "none"),
             "COUNTS=" + (counts.group(0) if counts else "MISSING"),
             "FAILS=" + (fails.group(1) if fails else "MISSING"),
             "CHECK_CRASHED=" + (crashed.group(1) if crashed else "MISSING"),
             "SHAKEDOWN_VERDICT=" + ("PASS" if ok else "FAIL")]
    rec_out = os.path.join(STAGE, "SHAKEDOWN_REHEARSAL.txt")
    open(rec_out, "w", encoding="utf-8").write(NL.join(lines) + NL)
    appendix = [
        "",
        "- 试跑（staging rehearsal）在提交 (i) 之前完成，使用同一份 gate_check_s5r5.py，只换根路径参数（--ev-root / --p05-root / --out 指向 $EV/shakedown/ 下的 staging 根）。",
        "- 试跑门禁输出：evidence/p05-s5r5/shakedown/gate/GATE_S5R5_end.txt（sha256 " + sha_f(OUT) + "，" + str(len(names)) + " 项断言）。",
        "- 门禁之外的 s5r5_shakedown_verify.py 核验结果：COUNTS " + (counts.group(0) if counts else "MISSING") + "；失败数=" + (fails.group(1) if fails else "MISSING") + "；检查器崩溃数=" + (crashed.group(1) if crashed else "MISSING") + "；" + str(len(names)) + " 项检查全部出现且为通过；EV_ROOT/P05_ROOT 均为 shakedown 路径。",
        "- 试跑期间出现的任何失败按四类归因（缺正式产物 / 检查器缺陷 / 链顺序 / 数据缺陷），检查器缺陷在提交 (i) 之前修好并用同一脚本 sha 重跑（迭代记录见 evidence/p05-s5r5/shakedown/ 与报告事件表）。",
        "- 试跑不替代正式门禁：正式门禁在提交 (i) 之后只运行一次，结果见附录 C。",
        ""]
    open(os.path.join(EV, "APPENDIX_A_S5R5.txt"), "w", encoding="utf-8").write(NL.join(appendix) + NL)
    print(NL.join(lines))
    print("WROTE " + os.path.relpath(rec_out, REPO))
    print("WROTE " + os.path.relpath(os.path.join(EV, "APPENDIX_A_S5R5.txt"), REPO))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
