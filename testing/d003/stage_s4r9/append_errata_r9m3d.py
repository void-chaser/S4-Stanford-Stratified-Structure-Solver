#!/usr/bin/env python3
# append_errata_r9m3d.py -- append E9-67.. to checkpoints/p05/registries/s4r9/ERRATA_9.txt (old file + new entries):
# one entry per section-3 P item whose audit verdict is "属实", then one entry for U353. The prefix sha256/bytes are
# asserted before writing; the U-354/U-356 statuses in RULINGS are cross-checked against the audit. New file (r9m3d).
import os, sys, re, hashlib
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
REG = os.path.join(REPO, "checkpoints/p05/registries")
AUDIT = os.path.join(EV, "AUDIT_R9M3C_R9M3D.tsv")
P = os.path.join(REG, "s4r9/ERRATA_9.txt")
M3C_EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
EXPECTED_SHA = "9bd2933d41d9ada8eba9928cd187f92a274b28e36d35d3c43c5de5a562390432"
EXPECTED_BYTES = 56754
FIRST_ID = 67
TAB = chr(9)
NL = chr(10)
IMPACT = {
    "P-1": "M3c 最终台账把已由 M2-05 实测覆盖的其他层失败变体记为转 S5，与 M2 判定表不一致。",
    "P-2": "M3c 的 S5 移交表含重复项，且缺 RP-R6d-3、RP-R6d-7；台账与移交两个方向的对应不成立。",
    "P-3": "M3c 就绪审计第①条的红点行数把台账表头算成数据行（27 vs 唯一 id 26）。",
    "P-4": "M3c 签收草稿 v1 的转入 S5 项重复且缺项，与台账不一致。",
    "P-5": "M3c 签收草稿 v1 未说明 S1/S2 范围声明第 (2) 条的七处 info=NULL seam 移交已闭合。",
    "P-6": "M3c 就绪审计的 RP-R6d-15 行沿用“待用户审核”旧措辞，且裁决列写“见 STATE 行”（U357 不允许）。",
}
ACTION = {
    "P-1": "登记 E9-67；M3d 台账按 U354 将 RP-R6d-14 记为已关闭（8 点全 MATCH，范围 P0/P2/PP1/PP2、F4、driver_r8m2a2_layers）。",
    "P-2": "登记 E9-68；M3d 的 S5 移交表去重为 7 个唯一项，并按 U355 双向核对（补入 RP-R6d-3、RP-R6d-7）。",
    "P-3": "登记 E9-69；M3d 就绪审计按列名解析、跳过表头式行并按唯一 id 去重，① 的红点数等于台账唯一 id 数。",
    "P-4": "登记 E9-70；M3d 签收草稿 v2 的转入 S5 只列去重后的唯一项，每项注明来源裁决。",
    "P-5": "登记 E9-71；M3d 签收草稿 v2 单列“S1/S2 签收移交项的闭合”一节（U356），并注明 F4 上族 B 的 info=NULL 锚点已不存在。",
    "P-6": "登记 E9-72；M3d 就绪审计每行裁决号为真实 U 编号或“-（事实项）”，RP-R6d-15 行改用 U345/U352。",
}


def read_table(path):
    rows = []
    hdr = None
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


def ruling_status(uid):
    for line in open(os.path.join(REG, "RULINGS.tsv"), encoding="utf-8"):
        f = line.split(TAB)
        if f and f[0] == uid and len(f) >= 5:
            return f[4].strip()
    return "MISSING"


def u353_lines():
    log = os.path.join(M3C_EV, "safe_run.log")
    lines = open(log, encoding="utf-8", errors="replace").read().splitlines()
    sha_line = prog_line = 0
    for i, line in enumerate(lines, 1):
        if "sha_sums_r9m3c.py checkpoints/p05/evidence/p05-s4r9/m3c/SHA256SUMS.txt" in line:
            sha_line = i
        if "progress_r9m3c.py freeze analysis done" in line:
            prog_line = i
    return sha_line, prog_line


def main():
    _, aud = read_table(AUDIT)
    if not aud:
        print("HARD_STOP missing audit table")
        return 2
    by_item = {}
    for r in aud:
        by_item[r.get("item", "")] = r
    # cross-check U354/U356 status against the audit verdicts
    for uid, item in (("U354", "P-1"), ("U356", "P-5")):
        st = ruling_status(uid)
        ok = by_item.get(item, {}).get("verdict") == "属实"
        if ok and "生效" not in st:
            print("HARD_STOP RULINGS %s status %s but audit %s is true" % (uid, st, item))
            return 2
        if (not ok) and "未生效" not in st:
            print("HARD_STOP RULINGS %s status %s but audit %s is false" % (uid, st, item))
            return 2
    entries = []
    for item in ("P-1", "P-2", "P-3", "P-4", "P-5", "P-6"):
        r = by_item.get(item)
        if not r:
            print("HARD_STOP audit missing " + item)
            return 2
        if r.get("verdict") != "属实":
            continue
        entries.append((r.get("claim", "") + "；实际值：" + r.get("actual_value", ""), r.get("evidence", ""),
                        IMPACT[item], ACTION[item]))
    sha_line, prog_line = u353_lines()
    if not (sha_line and prog_line and prog_line > sha_line):
        print("HARD_STOP cannot locate the M3c sha_sums/progress order evidence")
        return 2
    entries.append((
        "M3c end 门禁 EVIDENCE_SHA256SUMS_OK 的 FAIL 判为执行顺序错误：正式收尾链中 sha_sums（safe_run.log 第 %d 行）"
        "之后又写了一行 progress（第 %d 行），使证据清单的日志前缀与实际写入顺序不一致；结果表未受影响，删除误加行后"
        "逐项校验 16/16 一致。M3c 表二的三条顺序偏差（第 1、2、3 条：脚本先于 start 门禁、FROZEN 先于收尾试跑链、"
        "readiness 先于红点台账）同样接受。" % (sha_line, prog_line),
        "P05_S4R9_M3c_REPORT.md 附录 B; m3c/GATE_R9M3C_end.txt; m3c/safe_run.log:%d,%d; 表二 §7.2 第 1–3 条" % (
            sha_line, prog_line),
        "M3c end 门禁产生一处执行顺序型 FAIL，核验效力受损；M3c 的收尾链顺序与任务书不一致。",
        "按 U353 只登记勘误，不重跑 M3c；M3d 把“progress 最后一行”放在 sha_sums 之前，并把 sha_sums 作为 $EV 的最后一次写入。"))
    old = open(P, "rb").read()
    a = hashlib.sha256(old).hexdigest()
    if a != EXPECTED_SHA:
        print("HARD_STOP errata prefix sha %s != %s" % (a, EXPECTED_SHA))
        return 2
    if len(old) != EXPECTED_BYTES:
        print("HARD_STOP errata prefix bytes %d != %d" % (len(old), EXPECTED_BYTES))
        return 2
    if not old.endswith(NL.encode("utf-8")):
        old += NL.encode("utf-8")
    body = ""
    nid = FIRST_ID
    for fact, ref, impact, action in entries:
        eid = "E9-%d" % nid
        nid += 1
        body += eid + NL
        body += "- 事实：" + fact + NL
        body += "- 证据文件与行号：" + ref + NL
        body += "- 影响范围：" + impact + NL
        body += "- 处理方式：" + action + NL
    new = old + body.encode("utf-8")
    if new[:len(old)] != old:
        print("HARD_STOP prefix changed")
        return 2
    open(P, "wb").write(new)
    ids = re.findall(r"^(E9-\d+)", new.decode("utf-8"), re.M)
    print("entries=%d ids=%s..%s count=%d" % (len(entries), ids[FIRST_ID - 1], ids[-1], len(ids)))
    print("ERRATA bytes %d -> %d sha %s" % (len(old), len(new), hashlib.sha256(new).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
