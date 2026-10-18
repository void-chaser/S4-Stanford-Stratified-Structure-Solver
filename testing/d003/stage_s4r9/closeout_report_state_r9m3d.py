#!/usr/bin/env python3
# closeout_report_state_r9m3d.py -- closeout step 1: append appendix A (every number recomputed from the result
# tables by column name) to the report and verify the final STATE markers. STATE itself was finalised in S-B
# (update_state_r9m3d.py) so that the readiness audit can read the U354/U356 rows; this script therefore checks the
# STATE anchors instead of rewriting them. Script/table names used in the appendix come from FROZEN_SCRIPTS_R9M3D.tsv
# when it exists (it does in the formal freeze run). New file (r9m3d).
# usage: closeout_report_state_r9m3d.py REPORT STATE [START_GATE] [RECHECK_GATE] [FROZEN]
import os, sys, re, hashlib
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
REG = os.path.join(REPO, "checkpoints/p05/registries")
TAB = chr(9)
NL = chr(10)
PH_A = "（APPENDIX_A_PLACEHOLDER）"
PH_B = "（APPENDIX_B_PLACEHOLDER）"


def read_table(path):
    rows = []
    hdr = None
    if not os.path.isfile(path):
        return hdr, rows
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f and f[0] == hdr[0]:
            continue
        rows.append(dict(zip(hdr, f)))
    return hdr, rows


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def gate_counts(path):
    p = f = tot = -1
    if os.path.isfile(path):
        for line in open(path, encoding="utf-8"):
            m = re.match(r"COUNTS\tpass=(\d+)\tfail=(\d+)\tskip=(\d+)\ttotal=(\d+)", line)
            if m:
                p, f, tot = int(m.group(1)), int(m.group(2)), int(m.group(4))
            m2 = re.match(r"FAILS=(\d+)", line)
            if m2:
                f = int(m2.group(1))
    return p, f, tot


def posctrl(path):
    if not os.path.isfile(path):
        return "missing"
    txt = open(path, encoding="utf-8").read()
    return "PASS" if "RESULT: PASS" in txt else "FAIL"


def main():
    rep_p = sys.argv[1]
    st_p = sys.argv[2]
    start_g = sys.argv[3] if len(sys.argv) > 3 else os.path.join(EV, "GATE_R9M3D_start.txt")
    recheck_g = sys.argv[4] if len(sys.argv) > 4 else os.path.join(EV, "GATE_R9M3D_start_RECHECK.txt")
    frozen_p = sys.argv[5] if len(sys.argv) > 5 else os.path.join(EV, "FROZEN_SCRIPTS_R9M3D.tsv")
    env = {}
    env["sp"], env["sf"], env["st"] = gate_counts(start_g)
    env["rp"], env["rf"], env["rt"] = gate_counts(recheck_g)
    if env["sp"] < 0 or env["rp"] < 0:
        print("HARD_STOP missing gate counts")
        return 2
    _, aud = read_table(os.path.join(EV, "AUDIT_R9M3C_R9M3D.tsv"))
    if not aud:
        print("HARD_STOP missing audit table")
        return 2
    env["at"] = len([r for r in aud if r.get("verdict") == "属实"])
    env["an"] = len(aud)
    mis = [r.get("item") for r in aud if r.get("verdict") != "属实"]
    env["amis"] = ",".join(mis) if mis else "none"
    rul_p = os.path.join(REG, "RULINGS.tsv")
    rul_b = open(rul_p, "rb").read()
    nums = [int(l.split(TAB)[0][1:]) for l in rul_b.decode("utf-8", "replace").splitlines()
            if l.startswith("U") and l.split(TAB)[0][1:].isdigit()]
    env["umax"] = "U%d" % max(nums)
    env["ub"] = len(rul_b)
    env["us"] = hashlib.sha256(rul_b).hexdigest()[:8]
    st354 = st356 = "MISSING"
    for line in rul_b.decode("utf-8", "replace").splitlines():
        f = line.split(TAB)
        if len(f) >= 5 and f[0] == "U354":
            st354 = f[4].strip()
        if len(f) >= 5 and f[0] == "U356":
            st356 = f[4].strip()
    env["s354"], env["s356"] = st354, st356
    err_p = os.path.join(REG, "s4r9/ERRATA_9.txt")
    err_b = open(err_p, "rb").read()
    ids = re.findall(r"^(E9-\d+)", err_b.decode("utf-8", "replace"), re.M)
    env["elast"], env["ecnt"] = ids[-1], len(ids)
    env["eb"] = len(err_b)
    env["es"] = hashlib.sha256(err_b).hexdigest()[:8]
    led_p = os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv")
    _, led = read_table(led_p)
    env["lu"] = len(set(r.get("id", "") for r in led))
    env["lr"] = len(led)
    env["lt5"] = len([r for r in led if r.get("current_status") == "TRANSFERRED_S5"])
    env["lopen"] = 0
    env["lconf"] = 0
    for line in open(led_p, encoding="utf-8"):
        m = re.match(r"# OPEN_IN_SCOPE=(\d+)", line)
        if m:
            env["lopen"] = int(m.group(1))
        m = re.match(r"# CONFLICTS: same id with different raw status across the original ledgers: (\d+)", line)
        if m:
            env["lconf"] = int(m.group(1))
    _, hand = read_table(os.path.join(EV, "S5_HANDOFF_R9M3D.tsv"))
    env["hu"] = len(set(r.get("item_id", "") for r in hand))
    covered = set()
    for r in hand:
        for x in (r.get("ledger_ids", "") or "").split(";"):
            x = x.strip()
            if x and x != "-":
                covered.add(x)
    t5 = set(r["id"] for r in led if r.get("current_status") == "TRANSFERRED_S5")
    if covered != t5 or not hand:
        print("HARD_STOP handoff coverage mismatch")
        return 2
    _, rdy = read_table(os.path.join(EV, "READINESS_P05_S3S4_R9M3D.tsv"))
    if not rdy:
        print("HARD_STOP missing readiness table")
        return 2
    rc = {}
    for r in rdy:
        rc[r.get("status", "?")] = rc.get(r.get("status", "?"), 0) + 1
    gaps = [r.get("item", "") for r in rdy if r.get("status") == "GAP"]
    env["rn"] = len(rdy)
    env["rm"] = rc.get("MET", 0)
    env["rg"] = rc.get("GAP", 0)
    env["rt5"] = rc.get("TRANSFERRED_S5", 0)
    env["rc"] = rc.get("CLOSED_BY_RULING", 0)
    env["rgaps"] = ",".join(gaps) if gaps else "none"
    env["ph"] = posctrl(os.path.join(EV, "POSCTRL_HANDOFF_R9M3D.txt"))
    env["pr"] = posctrl(os.path.join(EV, "POSCTRL_READINESS_R9M3D.txt"))
    env["pc"] = posctrl(os.path.join(EV, "POSCTRL_REPORT_CHECK_R9M3D.txt"))
    if not os.path.isfile(frozen_p):
        frozen_line = ("- 冻结清单：尚未写定（试跑期按 §5 顺序，收尾链试跑先于冻结清单；end 门禁的冻结相关检查在试跑期标 SKIP）")
    else:
        fr = read_table(frozen_p)[1]
        frozen_line = "- 冻结清单：FROZEN_SCRIPTS_R9M3D.tsv 共 %d 项（脚本名由 end 门禁从该清单读取）" % len(fr)
    st_b = open(st_p, "rb").read()
    if len(st_b) > 8192:
        print("HARD_STOP STATE too large: %d" % len(st_b))
        return 2
    st_txt = st_b.decode("utf-8")
    for marker in ("r9m3d", "U354", "U356"):
        if marker not in st_txt:
            print("HARD_STOP STATE missing marker " + marker)
            return 2
    env["sb"] = len(st_b)
    env["ss"] = hashlib.sha256(st_b).hexdigest()[:8]
    ap = [
        "记录提交 (i) 之后由冻结脚本执行；本附录的数字全部由 closeout 从结果表复算，未手写。",
        "",
        "- 门禁：start PASS=%(sp)d FAILS=%(sf)d（total=%(st)d）；start 前缀复核 PASS=%(rp)d FAILS=%(rf)d（total=%(rt)d）" % env,
        "- §3 P 项复核：AUDIT_R9M3C_R9M3D.tsv %(at)d/%(an)d 属实；规划者事实有误：%(amis)s" % env,
        "- 裁决：RULINGS 最大 %(umax)s（%(ub)d 字节，sha %(us)s）；U354/U356 状态=%(s354)s/%(s356)s" % env,
        "- 勘误：ERRATA_9.txt 最后 %(elast)s，共 %(ecnt)d 条（%(eb)d 字节，sha %(es)s）" % env,
        "- 修正版台账：唯一 id=%(lu)d，数据行=%(lr)d，TRANSFERRED_S5=%(lt5)d，范围内仍开放=%(lopen)d，冲突=%(lconf)d" % env,
        "- S5 移交：唯一项=%(hu)d（台账 TRANSFERRED_S5 全部覆盖，双向核对 OK）" % env,
        "- 就绪审计：READINESS 共 %(rn)d 行：MET=%(rm)d GAP=%(rg)d TRANSFERRED_S5=%(rt5)d CLOSED_BY_RULING=%(rc)d；GAP 明细：%(rgaps)s" % env,
        "- 阳性对照：handoff=%(ph)s；readiness=%(pr)s；report_check=%(pc)s" % env,
        frozen_line,
        "- STATE 最终字节数：%(sb)d（<=8192），sha %(ss)s" % env,
        "- 数据来源：m3d/RED_POINTS_LEDGER_FINAL_R9M3D.tsv、m3d/S5_HANDOFF_R9M3D.tsv、m3d/READINESS_P05_S3S4_R9M3D.tsv、m3d/AUDIT_R9M3C_R9M3D.tsv",
    ]
    rep_txt = open(rep_p, encoding="utf-8").read()
    if rep_txt.count(PH_A) != 1:
        print("HARD_STOP report appendix-A placeholder count %d" % rep_txt.count(PH_A))
        return 2
    if rep_txt.count(PH_B) != 1:
        print("HARD_STOP report appendix-B placeholder count %d" % rep_txt.count(PH_B))
        return 2
    new = rep_txt.replace(PH_A, NL.join(ap))
    open(rep_p, "wb").write(new.encode("utf-8"))
    print("report bytes %d -> %d sha %s" % (
        len(rep_txt.encode("utf-8")), len(new.encode("utf-8")),
        hashlib.sha256(new.encode("utf-8")).hexdigest()))
    print("appendix A lines=%d" % len(ap))
    return 0


if __name__ == "__main__":
    sys.exit(main())
