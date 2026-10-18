#!/usr/bin/env python3
# audit_r9m1r4_r9m3a_v3.py -- v3 of the J-1..J-6 re-verification. Fixes three defects of v1: the EVENTS table was read from the registries directory although r9m1r4 never copied it there; the sha_sums/end-gate anchors matched the bare basename (empty) instead of the full command token and took the first instead of the last match; the J-6 sub-check required the report to contain no occurrence of the checker word although the report carries only negated forms.
import os, sys, re, hashlib, subprocess, glob

REPO = os.getcwd()
EV_M3A = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a")
EV_M1R3 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r3")
EV_M1R4 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r4")
REG_M1R3 = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R3")
REG_M1R4 = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R4")
STAGE = os.path.join(REPO, "testing/d003/stage_s4r9")
RECERT = os.path.join(STAGE, "recert_r9m1r4_v2.py")
GATE_CHECK_M1R4 = os.path.join(STAGE, "gate_check_r9m1r4_v3.py")
REPORT_M1R4 = os.path.join(REPO, "checkpoints/p05/P05_S4R9_M1R4_REPORT.md")
LOG_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")


def lines_of(p):
    if not os.path.isfile(p):
        return []
    return open(p, encoding="utf-8", errors="replace").read().splitlines()


def find_lines(lines, needle):
    return [i + 1 for i, l in enumerate(lines) if needle in l]


def parse_log(ev_dir):
    out = []
    for idx, line in enumerate(lines_of(os.path.join(ev_dir, "safe_run.log")), 1):
        m = LOG_TS_RE.match(line)
        if not m:
            continue
        parts = line.split("\t")
        cmd = ""
        for x in parts[1:]:
            if x.startswith("cmd="):
                cmd = x[4:]
                break
        out.append((idx, m.group(1), cmd))
    return out


def script_calls(log, relpath, min_ts="", mode_word=""):
    hits = []
    for idx, ts, cmd in log:
        if min_ts and ts < min_ts:
            continue
        head = cmd.strip()
        if not re.match(r"^(?:python3|sh)\b", head):
            continue
        toks = head.split()
        if relpath not in toks:
            continue
        if mode_word and mode_word not in toks:
            continue
        hits.append(idx)
    return hits


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV_M3A, "AUDIT_R9M1R4_R9M3A_v3.tsv")
    rows = []

    def add(item, fact, evid, concl, notes):
        rows.append((item, fact, evid, concl, notes))

    recert_lines = lines_of(RECERT)
    log_m1r3 = parse_log(EV_M1R3)
    log_m1r4 = parse_log(EV_M1R4)

    # J-1
    tamper_line = find_lines(recert_lines, 'sha256(b"tampered_fact")')
    ev158_line = find_lines(recert_lines, "tampered_events_count")
    c1 = find_lines(recert_lines, 'comm_v[tampered_k]["verdict"] =')
    posdir_exists = os.path.isdir(os.path.join(EV_M1R4, "shakedown", "posctrl"))
    disk_writes = []
    if tamper_line:
        lo = max(0, min(tamper_line) - 40)
        hi = min(len(recert_lines), max(tamper_line) + 40)
        for i in range(lo, hi):
            if "open(" in recert_lines[i] and "posctrl" in recert_lines[i].lower():
                disk_writes.append(i + 1)
    all_ln = tamper_line + ev158_line + c1
    block_lo = min(all_ln) if all_ln else 0
    block_hi = max(all_ln) if all_ln else 0
    j1_ok = bool(tamper_line) and bool(ev158_line) and (not posdir_exists)
    add("J-1",
        "阳性对照无效：case3 以常量 sha256(b'tampered_fact') 与 EXPECTED_P1_SHA 比较、case4 以 158-1 与 158 比较（两项恒为真）；case1/2 只改内存字典不读落盘副本；m1r4/shakedown/posctrl 不存在",
        "recert_r9m1r4_v2.py:%d-%d; m1r4/shakedown/posctrl exists=%s" % (block_lo, block_hi, posdir_exists),
        "属实" if j1_ok else "规划者事实有误",
        "tampered_fact 行=%s; tampered_events_count 行=%s; case1 内存改字典行=%s; posctrl 落盘目录存在=%s; 篡改副本写盘语句行=%s" % (
            tamper_line, ev158_line, c1, posdir_exists, disk_writes if disk_writes else "none"))

    # J-2
    frozen_p = os.path.join(REG_M1R3, "FROZEN_SCRIPTS_R9M1R3.tsv")
    scripts = []
    for line in lines_of(frozen_p):
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("path\t"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0].startswith("testing/d003/") and (parts[0].endswith(".py") or parts[0].endswith(".sh")):
            scripts.append(parts[0])
    ts = find_lines(recert_lines, "target_scripts")
    target_n = 0
    if ts:
        for i in range(ts[0], min(len(recert_lines), ts[0] + 20)):
            target_n += len(re.findall(r'"[a-z_]+":', recert_lines[i]))
            if recert_lines[i].strip() == "}":
                break
    counts = {}
    for s in scripts:
        counts[os.path.basename(s)] = script_calls(log_m1r3, s, "2026-10-18T04:28:39Z")
    ev_hits = counts.get("events_r9m1r3.py", [])
    rc_hits = counts.get("report_check_r9m1r3.py", [])
    j2_ok = (len(scripts) == 14 and target_n == 5 and ev_hits == [158, 160] and rc_hits == [155, 156, 157])
    add("J-2",
        "补做断言不完整：recert 的 target_scripts 只有 5 项，FROZEN_SCRIPTS_R9M1R3 按脚本计 14 项；m1r3 日志中 events=2 次(158,160)、report_check=3 次(155-157)、其余各 1 次",
        "recert_r9m1r4_v2.py:%s; FROZEN_SCRIPTS_R9M1R3.tsv; m1r3/safe_run.log" % (ts or "-"),
        "属实" if j2_ok else "规划者事实有误",
        "frozen 脚本数=%d; recert target_scripts 项数=%d; events 物理行=%s; report_check 物理行=%s; 非1次脚本=%s" % (
            len(scripts), target_n, ev_hits, rc_hits, {k: v for k, v in sorted(counts.items()) if len(v) != 1}))

    # J-3
    l82 = lines_of(os.path.join(EV_M1R3, "safe_run.log"))
    ln94 = find_lines(l82, "gate_r9m1r3_v4.sh start _v5")
    line82_text = l82[81][:120] if len(l82) > 81 else ""
    audit_tsv = lines_of(os.path.join(REG_M1R4, "AUDIT_R9M1R3_R9M1R4.tsv"))
    h5_row = [l for l in audit_tsv if l.startswith("H-5\t")]
    says82 = any("物理82" in l for l in h5_row)
    j3_ok = (ln94 == [94]) and says82
    add("J-3",
        "H-5 行号：m1r3 safe_run.log 中 gate_r9m1r3_v4.sh start _v5 的物理行号是 94（任务书写的 82 是 heredoc 内容）；AUDIT_R9M1R3_R9M1R4.tsv 却记为属实（物理82）",
        "m1r3/safe_run.log 物理行=%s; 第82行=%r; AUDIT_R9M1R3_R9M1R4.tsv H-5 行" % (ln94, line82_text[:60]),
        "属实" if j3_ok else "规划者事实有误",
        "物理行94 核对=%s; 第82行是否该命令=%s; 审计表是否写82=%s" % (ln94 == [94], "gate_r9m1r3_v4.sh start _v5" in line82_text, says82))

    # J-4
    def git_show(rev, path):
        try:
            return subprocess.check_output(["git", "show", rev + ":" + path], cwd=REPO).decode("utf-8", "replace").splitlines()
        except subprocess.CalledProcessError:
            return []
    upath = "checkpoints/p05/registries/s4r9/M1R4/UNLOGGED_WRITES_R9M1R3.tsv"
    v_old = git_show("786b150", upath)
    v_new = git_show("2f86aa11c7ee1bb16f663abf03ddbf04674a6912", upath)
    diff_lines = [(i + 1, v_old[i], v_new[i]) for i in range(min(len(v_old), len(v_new))) if v_old[i] != v_new[i]]
    m1r4_1415 = [(idx, ts, cmd[:30]) for (idx, ts, cmd) in log_m1r4 if idx in (14, 15)]
    gc_lines = lines_of(GATE_CHECK_M1R4)
    committed_fn = find_lines(gc_lines, "def check_committed_i")
    scope_line = 0
    if committed_fn:
        for i in range(committed_fn[0], min(len(gc_lines), committed_fn[0] + 14)):
            if "git" in gc_lines[i] and "diff" in gc_lines[i]:
                scope_line = i + 1
                break
    scope_text = gc_lines[scope_line - 1] if scope_line else ""
    j4_ok = len(diff_lines) == 2 and not ("registries" in scope_text)
    add("J-4",
        "(i) 已提交文件被改写：UNLOGGED_WRITES_R9M1R3.tsv 在 786b150 提交、在 2f86aa1 被改（RULINGS.tsv 与 ERRATA_9.txt 两行 mtime 变为 05:23:53Z，即 m1r4 日志第 14、15 行）；gate_check_r9m1r4_v3.py 的 COMMITTED_I 检查不覆盖 registries",
        "git show 786b150 vs 2f86aa1 %s; m1r4/safe_run.log:%s; gate_check_r9m1r4_v3.py:%d" % (upath, [x[0] for x in m1r4_1415], scope_line),
        "属实" if j4_ok else "规划者事实有误",
        "差异行号(1-based,含注释)=%s; m1r4 日志第14/15行时间=%s; COMMITTED_I diff 行=%d 含 registries=%s" % (
            [d[0] for d in diff_lines], [x[1] for x in m1r4_1415], scope_line, "registries" in scope_text))

    # J-5
    end_gate = lines_of(os.path.join(EV_M1R4, "GATE_R9M1R4_end.txt"))
    fails = [l for l in end_gate if l.startswith("FAIL\t")]
    fin = [l for l in end_gate if "POST_I_CALL_COUNT_FINALIZE" in l]
    l4 = lines_of(os.path.join(EV_M1R4, "safe_run.log"))
    gate_end_lines = sorted(set(find_lines(l4, "gate_r9m1r4_v3.sh end") + find_lines(l4, "gate_r9m1r4_v2.sh end")))
    first_anchor = gate_end_lines[0] if gate_end_lines else 0
    ev_p = os.path.join(EV_M1R4, "EVENTS_R9M1R4.tsv")
    if not os.path.isfile(ev_p):
        ev_p = os.path.join(REG_M1R4, "EVENTS_R9M1R4.tsv")
    ev_lines = lines_of(ev_p)
    ev_rows = [l for l in ev_lines if l.strip() and not l.startswith("#") and not l.startswith("log_line\t")]
    max_ev_line = max([int(r.split("\t")[0]) for r in ev_rows if r.split("\t")[0].isdigit()] or [0])
    shak_files = sorted(glob.glob(os.path.join(EV_M1R4, "shakedown", "*", "GATE_*end*.txt")))
    shak_fail = [os.path.basename(f) for f in shak_files if re.search(r"FAIL\tCOMMIT_I_PRESENT", open(f, encoding="utf-8", errors="replace").read())]
    sha_sums_line = script_calls(log_m1r4, "testing/d003/stage_s4r9/sha_sums_r9m1r4.py")
    official_gate = [g for g in gate_end_lines if sha_sums_line and g > sha_sums_line[-1]]
    parts = {
        "finalize_expected_1_actual_0": bool(fin) and "expected=1\tactual=0" in fin[0],
        "first_end_anchor_is_shakedown": bool(official_gate) and first_anchor < official_gate[-1],
        "shakedown_end_post_i_not_executed": len(shak_fail) >= 1,
        "events_54_rows_max_56_and_57_uncovered": len(ev_rows) == 54 and max_ev_line == 56 and bool(sha_sums_line) and sha_sums_line[-1] == 57 and bool(official_gate) and official_gate[-1] == 58,
    }
    add("J-5",
        "end 门禁设计缺陷：finalize 期望 1 而门禁时刻为 0；EVENTS 锚点取首个 end 匹配（试跑行）；shakedown 的 end 试跑 POST_I 块未执行；EVENTS 54 行覆盖到第 56 行，第 57 行(sha_sums)未覆盖",
        "GATE_R9M1R4_end.txt; m1r4/safe_run.log:%s; EVENTS_R9M1R4.tsv" % gate_end_lines,
        "属实" if all(parts.values()) else "规划者事实有误",
        "end FAIL 行数=%d; finalize 断言=%r; 首个 end 锚点=%d; 正式 end 行=%s; sha_sums 行=%s; EVENTS 行=%d 最大 log_line=%d; 试跑缺 POST_I=%s; 分辨率=%s" % (
            len(fails), (fin[0][:55] if fin else "-"), first_anchor, official_gate, sha_sums_line, len(ev_rows), max_ev_line, shak_fail, parts))

    # J-6
    rc_lines = lines_of(os.path.join(STAGE, "report_check_r9m1r4.py"))
    forbidden = [i + 1 for i, l in enumerate(rc_lines) if "是否签收" in l]
    rep_lines = lines_of(REPORT_M1R4)
    rep_forbidden = find_lines(rep_lines, "是否签收")
    state_bytes = os.path.getsize(os.path.join(REPO, "checkpoints/p05/STATE.md"))
    sec9 = [i for i, l in enumerate(rep_lines) if re.match(r"^##\s*9\.", l.strip())]
    sec9_text = ""
    if sec9:
        j = sec9[0] + 1
        while j < len(rep_lines) and not re.match(r"^##\s", rep_lines[j].strip()):
            sec9_text += rep_lines[j] + "\n"
            j += 1
    a3_items = [i + 1 for i, l in enumerate(rep_lines) if re.match(r"^\d+\.\s+\*\*项", l.strip())]
    d101 = []
    start = None
    for i, l in enumerate(rep_lines):
        if re.match(r"^###\s*10\.1", l.strip()):
            start = i + 1
            break
    if start is not None:
        j = start
        while j < len(rep_lines) and not re.match(r"^###\s*10\.2", rep_lines[j].strip()):
            if re.match(r"^\d+\.\s+", rep_lines[j].strip()):
                d101.append(rep_lines[j].strip()[:50])
            j += 1
    reg_items = [l for l in lines_of(os.path.join(REG_M1R4, "SHA256SUMS.txt")) if l.strip() and not l.startswith("#")]
    sec1 = ""
    s1 = [i for i, l in enumerate(rep_lines) if re.match(r"^##\s*1\.", l.strip())]
    if s1:
        j = s1[0] + 1
        while j < len(rep_lines) and not re.match(r"^##\s", rep_lines[j].strip()):
            sec1 += rep_lines[j] + "\n"
            j += 1
    start_v1 = lines_of(os.path.join(EV_M1R4, "GATE_R9M1R4_start.txt"))
    v1_fails = [l for l in start_v1 if l.startswith("FAIL\t")]
    parts = {
        "report_check_word_list_hits_negated_report_text": bool(forbidden) and bool(rep_forbidden) and any("不询问是否签收" in l for l in rep_lines) and not any(re.search(r"是否签收\s*[?？]", l) for l in rep_lines),
        "state_over_8192": state_bytes > 8192,
        "sec9_says_none_but_a3_has_4": ("无" in sec9_text) and len(a3_items) == 4,
        "deliverables_13_vs_registry_11": len(d101) == 13 and len(reg_items) == 11,
        "sec1_claims_41_pass_without_initial_fail": ("41" in sec1 and "FAILS=1" not in sec1 and bool(v1_fails)),
    }
    add("J-6",
        "收尾质量：report_check 误中禁用词提前退出且第 3 步数字核对未执行；STATE 8480 字节 > 8192；报告 §9 写无与附录 A.3 四项矛盾；§10.1 列 13 项而 registries 只有 11 项；§1 称 41 项全 PASS 未披露初版 start 门禁 FAILS=1",
        "report_check_r9m1r4.py:%s; STATE.md(%dB); REPORT §9/A.3=%s; §10.1; GATE_R9M1R4_start.txt(%d FAIL)" % (forbidden, state_bytes, a3_items, len(v1_fails)),
        "属实" if all(parts.values()) else "规划者事实有误",
        "禁用词行=%s 报告内出现=%s; STATE 字节=%d; §9 含'无'=%s A.3 项数=%d; §10.1 项数=%d registries 项数=%d; §1 含41=%s 含FAILS=1=%s 初版 start FAIL=%d; 分项=%s" % (
            forbidden, rep_forbidden, state_bytes, "无" in sec9_text, len(a3_items), len(d101), len(reg_items),
            "41" in sec1, "FAILS=1" in sec1, len(v1_fails), parts))

    # J-7
    p1 = os.path.join(EV_M1R3, "runs/formal/FORMAL_FACTS_M1_F4_R9M1R3_pass1.tsv")
    p2 = os.path.join(EV_M1R3, "runs/formal/FORMAL_FACTS_M1_F4_R9M1R3_pass2.tsv")

    def load(p):
        ls = [l.split("\t") for l in lines_of(p) if l.strip() and not l.startswith("#")]
        h = ls[0]
        return {tuple([r[h.index("section")], r[h.index("group")], r[h.index("point_id")]]): dict(zip(h, r)) for r in ls[1:]}

    d1, d2 = load(p1), load(p2)
    fields = ["rc", "rc1", "rc2", "rc3", "hit", "class", "I1", "I2", "I3", "I4", "I5", "I6"]
    key_ok = (len(d1) == len(d2) == 651)
    ndiff = 0
    for k in d1:
        for f in fields:
            if d1[k].get(f) != d2[k].get(f):
                ndiff += 1
    vt = load(os.path.join(REG_M1R3, "VERDICT_M1_F4_R9M1R3.tsv"))
    vcount = {}
    for k, r in vt.items():
        vcount[r["verdict"]] = vcount.get(r["verdict"], 0) + 1
    j7_ok = key_ok and ndiff == 0 and vcount.get("MATCH") == 626 and vcount.get("NOT_REACHED_AS_EXPECTED") == 22 and vcount.get("NOT_RUN_AS_EXPECTED") == 3
    add("J-7",
        "规划者独立复核（仅参考）：两遍 FORMAL_FACTS 各 651 行、键唯一、12 个事实字段 0 处不同；已提交 VERDICT 为 626/22/3",
        "FORMAL_FACTS pass1/pass2; VERDICT_M1_F4_R9M1R3.tsv",
        "属实" if j7_ok else "规划者事实有误",
        "行数=%d/%d 键唯一=%s 字段差异=%d VERDICT 计数=%s" % (len(d1), len(d2), key_ok, ndiff, vcount))

    hdr = ["item_id", "fact_statement", "evidence_reference", "audit_conclusion", "detailed_notes"]
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write("# AUDIT_R9M1R4_R9M3A.tsv -- independent re-verification of the M1R4 process defects J-1..J-6 (J-7 reference only)\n")
        fh.write("\t".join(hdr) + "\n")
        for r in rows:
            fh.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")
    for r in rows:
        print("%s\t%s" % (r[0], r[3]))
    print("WROTE " + out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
