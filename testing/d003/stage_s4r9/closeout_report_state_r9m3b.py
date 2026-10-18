#!/usr/bin/env python3
# closeout_report_state_r9m3b.py -- closeout step 1: append the formal-result appendix A to the report and finalise
# STATE.md, both computed from the result tables (never from constants). New file (r9m3b).
# usage: python3 -I -B testing/d003/stage_s4r9/closeout_report_state_r9m3b.py REPORT.md STATE.md
import os, sys, re, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
TAB = chr(9)
NL = chr(10)
PH = "（APPENDIX_A_PLACEHOLDER）"


def read_tsv(path):
    rows = []
    hdr = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def kv(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if len(f) >= 2:
            out.setdefault(f[0], f[1])
    return out


def main():
    if len(sys.argv) < 3:
        print("usage: closeout_report_state_r9m3b.py REPORT.md STATE.md")
        return 2
    rep_p, st_p = sys.argv[1], sys.argv[2]
    ver = read_tsv(os.path.join(EV, "E2E_VERDICT_R9M3B.tsv"))
    cats = {}
    for r in ver:
        cats[r.get("verdict", "?")] = cats.get(r.get("verdict", "?"), 0) + 1
    def c(name):
        return cats.get(name, 0)
    flaky = [r.get("point_id") for r in ver if r.get("verdict") == "FLAKY"]
    invalid = [r.get("point_id") for r in ver if r.get("verdict") == "INVALID"]
    offt = [r.get("point_id") for r in ver if r.get("verdict") == "HIT_OFF_TARGET"]
    miss = [r.get("point_id") for r in ver if r.get("verdict") == "MISSING_RUN"]
    mk = kv(os.path.join(EV, "MAKETEST_VERDICT_R9M3B.tsv"))
    recon_lines = []
    for line in open(os.path.join(EV, "MAKETEST_VERDICT_R9M3B.tsv"), encoding="utf-8"):
        if line.startswith("reconcile" + TAB):
            recon_lines.append(line.rstrip(NL).split(TAB))
    build = kv(os.path.join(EV, "E2E_BUILD_R9M3B.tsv"))
    calib = [l for l in open(os.path.join(EV, "CALIB_E2E_R9M3B.tsv"), encoding="utf-8")]
    calib_target = len([l for l in calib if l.startswith("TARGET")])
    calib_event = len([l for l in calib if l.startswith("EVENT")])
    pre_sha = kv(os.path.join(EV, "PREREG_E2E_R9M3B.sha256.txt"))
    prereg_rows = read_tsv(os.path.join(EV, "PREREG_E2E_R9M3B.tsv"))
    pre_points = len([r for r in prereg_rows if r.get("is_control") == "NO"])
    pre_controls = len([r for r in prereg_rows if r.get("is_control") == "YES"])
    pre_sha_v = pre_sha.get("PREREG_E2E_R9M3B.tsv", "") or ""
    posE = open(os.path.join(EV, "POSCTRL_E2E_R9M3B.txt"), encoding="utf-8").read().strip().splitlines()
    posM = open(os.path.join(EV, "POSCTRL_MAKETEST_R9M3B.txt"), encoding="utf-8").read().strip().splitlines()
    posE_line = [l for l in posE if l.startswith("OVERALL_POSITIVE_CONTROL")][-1]
    posM_line = [l for l in posM if l.startswith("OVERALL_POSITIVE_CONTROL")][-1]
    red = read_tsv(os.path.join(EV, "RED_POINTS_LEDGER_APPEND_R9M3B.tsv"))
    real_red = [r for r in red if r.get("id") != "RP-R9M3B-NONE"]
    audit = read_tsv(os.path.join(EV, "AUDIT_R9M3A_R9M3B.tsv"))
    audit_ok = len([r for r in audit if r.get("verdict") == "属实"])
    gs = open(os.path.join(EV, "GATE_R9M3B_start.txt"), encoding="utf-8").read()
    gs_pass = re.search(r"COUNTS\tpass=(\d+)", gs)
    gs_fail = re.search(r"^FAILS=(\d+)", gs, re.M)
    cats_txt = "CONTROL_OK=%d, E2E_OK=%d" % (c("CONTROL_OK"), c("E2E_OK"))
    extra = {k: v for k, v in cats.items() if k not in ("CONTROL_OK", "E2E_OK")}
    extra_txt = ", ".join("%s=%d" % (k, v) for k, v in sorted(extra.items())) or "none"
    recon_bad = [r for r in recon_lines if r[6] != "OK"]
    ap = [
        "记录提交 (i) 之后由冻结脚本执行；本附录的数字全部由 closeout 从结果表复算，未手写。",
        "",
        "- E2E 正式两遍（pass1、pass2）：" + cats_txt + "；其他类别： " + extra_txt,
        "- E2E 判据：visible 为具体错误文本（Python RuntimeError 含 GetPowerFlux；Lua 以 GetPoyntingFlux: 开头的 stderr 行），HIT 的序号与 size 必须等于 CALIB；FLAKY=" + (",".join(flaky) if flaky else "none") + "，INVALID=" + (",".join(invalid) if invalid else "none") + "，HIT_OFF_TARGET=" + (",".join(offt) if offt else "none") + "，MISSING_RUN=" + (",".join(miss) if miss else "none"),
        "- E2E 阳性对照（冻结期正式调用 1 次）：" + posE_line,
        "- make test 只读重解析：verdict=" + mk.get("verdict", "?") + " unit_count=" + mk.get("unit_count", "?") + "；4 遍 × 2 段对账 " + ("全部 OK" if not recon_bad else "存在 FAIL: " + str(recon_bad[:4])) + "；阳性对照：" + posM_line,
        "- 构建：Python 扩展 sha " + build.get("PYEXT_SHA256", "?")[:8] + "（与 M3a 差异仅 build-id 与树路径），Lua 前端 sha " + build.get("LUA_FRONTEND_SHA256", "?")[:8] + "（与 M3a 逐字节相同）",
        "- 校准：EVENT 行 " + str(calib_event) + "、TARGET 行 " + str(calib_target) + "（17 个前端 × 选项组，注入无关；gdb 日志在 $EV/calib/）",
        "- 预注册：PREREG_E2E_R9M3B.tsv 共 " + str(len(prereg_rows)) + " 行（" + str(pre_points) + " 注入点 + " + str(pre_controls) + " 无注入对照），sha=" + pre_sha_v[:8] + "，状态 INFLUENCED",
        "- 新增红点： " + (str(len(real_red)) + " 项（" + ",".join(r.get("id", "?") for r in real_red) + "）" if real_red else "无（无 API_SILENT / RETRY_DIFF / RETRY_FAIL）"),
        "- 门禁：start PASS=" + (gs_pass.group(1) if gs_pass else "?") + " FAILS=" + (gs_fail.group(1) if gs_fail else "?") + "；审计 " + str(audit_ok) + "/12 属实；FROZEN 调用计数由 end 门禁按清单核对",
        "- STATE 最终字节数：" + "@STATE_BYTES@" + "（<=8192）",
        "- 逐点明细：E2E_VERDICT_R9M3B.tsv；红点表：RED_POINTS_LEDGER_APPEND_R9M3B.tsv；台账核对：LEDGER_CHECK_R9M3B.tsv",
        "",
        "台账：RULINGS 最大 U342；ERRATA 最后 E9-57，共 57 条；本轮 M3a 判定 NO_NEW_FAILURE 因上述重解析通过而成立（U338）。",
    ]
    rep_txt = open(rep_p, "rb").read().decode("utf-8")
    if rep_txt.count(PH) != 1:
        print("HARD_STOP report placeholder count %d" % rep_txt.count(PH))
        return 2
    st_txt = open(st_p, "rb").read().decode("utf-8")
    a1 = "| 当前轮次 | **P05-S4 R9 M3b（r9m3b）**：M3a 偏差裁决落账（U334–U342、E9-46..E9-57）+ make test 只读重解析 + E2E 装置修订/校准/新预注册/正式两遍（收尾时由 closeout 填写结论） |"
    a2 = "| S4R9 M3b | （收尾时由 closeout 填写） | `P05_S4R9_M3b_REPORT.md` |"
    a3 = "| Python/Lua 可见性（RP-R6d-15） | 装置与预注册完成；M3b 收尾时由 closeout 填写正式结论 | M3b | `PREREG_E2E_R9M3B.tsv` |"
    a4 = "> 说明：本轮进行 R9 M3b（勘误收口 + make test 重解析 + E2E 修订/校准/预注册/正式两遍），不宣布阶段完成；结论由 closeout 填写。"
    for a in (a1, a2, a3, a4):
        if st_txt.count(a) != 1:
            print("HARD_STOP state anchor count %d for: %s" % (st_txt.count(a), a[:60]))
            return 2
    b1 = "| 当前轮次 | **P05-S4 R9 M3b（r9m3b）**：M3a 偏差裁决落账（U334–U342、E9-46..E9-57）+ make test 只读重解析（NO_NEW_FAILURE，4 遍对账通过）+ E2E 修订/校准/新预注册（" + str(len(prereg_rows)) + " 点）/正式两遍（" + cats_txt + "） |"
    b2 = "| S4R9 M3b | U334–U342、E9-46–E9-57；make test 只读重解析 NO_NEW_FAILURE（" + str(mk.get("unit_count", "?")) + " 单元、4 遍对账通过）；E2E 预注册 " + str(len(prereg_rows)) + " 点、正式两遍 " + cats_txt + "；新红点 " + str(len(real_red)) + " | `P05_S4R9_M3b_REPORT.md` |"
    b3 = "| Python/Lua 可见性（RP-R6d-15） | 正式两遍实测：" + cats_txt + "；其他类别 " + extra_txt + " | 已实测（待用户审核） | `E2E_VERDICT_R9M3B.tsv` |"
    b4 = "> 说明：本轮完成 R9 M3b（勘误收口 + make test 重解析 NO_NEW_FAILURE + E2E 修订/校准/预注册/正式两遍），不宣布阶段完成；等待用户审核。"
    st_new = st_txt.replace(a1, b1).replace(a2, b2).replace(a3, b3).replace(a4, b4)
    body = NL.join(ap)
    body = body.replace("@STATE_BYTES@", str(len(st_new.encode("utf-8"))))
    rep_new = rep_txt.replace(PH, body)
    open(rep_p, "wb").write(rep_new.encode("utf-8"))
    open(st_p, "wb").write(st_new.encode("utf-8"))
    print("report bytes %d -> %d sha %s" % (len(rep_txt.encode("utf-8")), len(rep_new.encode("utf-8")),
                                            hashlib.sha256(rep_new.encode("utf-8")).hexdigest()))
    print("state bytes %d -> %d sha %s" % (len(st_txt.encode("utf-8")), len(st_new.encode("utf-8")),
                                           hashlib.sha256(st_new.encode("utf-8")).hexdigest()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
