#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# audit_r9m1r2_r9m1r3_v2.py -- Audit of G-1..G-8, forensic script recovery, and bare write audit for r9m1r2 (Step S-B). New file per Rule 3.
import base64, csv, datetime, difflib, hashlib, os, re, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))
M1R2_EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2")
FORENSIC_DIR = os.path.join(EV, "forensic")
os.makedirs(FORENSIC_DIR, exist_ok=True)

# --------------------------------------------------------------------
# 1. Audit of G-1..G-8
# --------------------------------------------------------------------
audit_rows = []

audit_rows.append([
    "G-1",
    "冻结与实际调用不一致",
    "a413db0 (01:51:09Z); m1r2 safe_run.log L29, L30, L33, L34, L39, L40, L37, L44; FROZEN_SCRIPTS_R9M1R2.tsv",
    "属实",
    "记录提交 (i) a413db0 于 01:51:09Z 提交。随后 L29 写入 compare_f3_f4_r9m1r2_R2.py，L30 写入 posctrl_r9m1r2_R2.py，L33 写入 run_smoke_r9m1r2_R2.py，L34 写入 run_formal_r9m1r2_R2.py，L39 写入 run_formal_r9m1r2_R3.py，全部发生在 (i) 之后。最终正式事实来自 L40 的 formal_R3，冒烟来自 L37 的 smoke_R2，比对来自 L44 的 compare_R2。FROZEN_SCRIPTS_R9M1R2.tsv 中列出的 run_formal/run_smoke/compare/posctrl 原件均未产出最终结果。"
])

audit_rows.append([
    "G-2",
    "多次调用正式/冒烟/阳性对照脚本",
    "m1r2 safe_run.log L28, L31, L32, L35, L37, L38, L40; runs/formal/; P05_S4R9_M1R2_REPORT.md:175-179",
    "属实",
    "日志证实：posctrl 运行 2 次（L28, L31）；smoke 运行 3 次（L32, L35, L37）；formal 运行 2 次（L38, L40）。runs/formal 下仅有 m1c_F4、pass1、pass2 子目录，无 FORMAL_FACTS 输出文件，经源码核实系 run_formal_r9m1r2_R2.py:228 中使用 r['id'] 访问 RESULTS_R6c_STATE.tsv（实际列名为 point_id）导致 KeyError 抛出中断。报告 §8.1 声称正式运行脚本仅调用 1 次与实际日志严重不符。"
])

audit_rows.append([
    "G-3",
    "原地改写后重跑且阳性对照未覆盖",
    "m1r2 safe_run.log L36, L37, L43, L44, L31; F3_F4_EQUIV_R9M1R2.tsv",
    "属实",
    "日志证实：L36 原地改写 run_smoke_r9m1r2_R2.py 后 L37 重跑；L43 原地改写 compare_f3_f4_r9m1r2_R2.py 后 L44 重跑并覆盖 F3_F4_EQUIV_R9M1R2.tsv。L31 运行的 posctrl 使用的是 L29 版本的 compare，L43 原地改写后未重新执行阳性对照进行覆盖验证。"
])

audit_rows.append([
    "G-4",
    "m1r2 裸写候选（mtime 与日志无对应）",
    "checkpoints/p05/evidence/p05-s4r9/m1r2/tmp/; P05_S4R9_M1R2_REPORT.md:235",
    "属实",
    "文件 mtime 证实：tmp/test_plain_g, test_dbg_g, gdb_test.cmd, count.cmd, d003-F3-test-dbg, d003plan-F3-test-dbg, d003plan-F4-test-dbg 生成于 01:31-01:35Z，介于日志 L13 (01:28:30Z) 与 L14 (01:37:26Z) 之间，无对应日志；posctrl_tampered_pass1/pass2/verdict/agg.tsv 与 posctrl_case3_verdict/agg.tsv 生成于 01:49:05Z，早于 L24 (01:49:27Z)，亦无对应日志。报告 §11 记载越界写入 0 并声称全部写入经 safe_run.sh 运行，遗漏披露裸写。"
])

audit_rows.append([
    "G-5",
    "收尾顺序混乱与门禁多跑/改写",
    "m1r2 safe_run.log L52-L65; checkpoints/p05/evidence/p05-s4r9/m1r2/SHA256SUMS.txt",
    "属实",
    "日志证实：events_r9m1r2.py 于 L52 运行，而 safe_run.log 全长 65 条，L53-L65 共 13 条操作未进入事件表；end 门禁于 L53, L56, L60, L63 运行 4 次，中间插入 L54, L55, L57, L58, L59, L61, L62, L64, L65 等多次内联 exec 脚本改写报告 §13、小表与 SHA256SUMS；当前对 m1r2/SHA256SUMS.txt 做 sha256sum -c，safe_run.log 与 tmp/status_now_end.txt 两项 FAILED，且 GATE_R9M1R2_end_R4.txt 未包含在清单中。"
])

audit_rows.append([
    "G-6",
    "G2c_control 未运行行填值 0/CONTROL_OK",
    "run_formal_r9m1r2_R3.py:90-97; PREREG_M1_F4_R9M1R2.tsv; P05_S4R9_M1R2_REPORT.md:207",
    "属实",
    "源码证实：run_formal_r9m1r2_R3.py:90-97 对 f3_effective_verdict=NOT_RUN_AS_EXPECTED 的 3 行直接返回 rc='0', rc1='0', rc2='0', class='CONTROL_OK'，未真实调用驱动；预注册中这 3 行 exp_class=NOT_RUN_REGISTRY_ERROR、env=NOT_RUN；报告 §9.2 错误地将合成的 0/CONTROL_OK 称为'本轮事实'。"
])

audit_rows.append([
    "G-7",
    "M1c G6 不变量 I1..I6 未进入判定与比对",
    "verdict_r9m1r2.py:133; compare_f3_f4_r9m1r2_R2.py:91-132,183; F3_F4_EQUIV_R9M1R2.tsv; M1C_F3_RESULTS_R6c_SEAM.tsv",
    "属实",
    "源码与输出证实：verdict_r9m1r2.py:133 显式限制 if grp == 'G5':，G6 判定完全忽略 I1..I6；compare_f3_f4_r9m1r2_R2.py:91-132 中 F3 侧 G6 错误读取了 M1C_F3_STATE_SEAM_R6c_pass1.tsv，致使 F3 侧 I1..I6 全为 '-'，而在 compare 脚本中任一侧为 '-' 时跳过比对；最终 F3_F4_EQUIV 中 G6 25 行 f3_I* 全为 '-'，未能实现逐字段比对。历史真值在 registries/s4r8/M1c/r8m1c3/M1C_F3_RESULTS_R6c_SEAM.tsv。"
])

audit_rows.append([
    "G-8",
    "K 命中数核对范围不足与点数对应缺失",
    "build_kmap_r9m1r2.py:175-184; K_INHERIT_R9M1R2.tsv",
    "属实",
    "源码与表格证实：build_kmap_r9m1r2.py:175-184 仅在 8 个预设 FMM 模式（S4FMM_NG=9）下比较 plain 与 kmap 的 malloc 命中数，未按 26 个 d003/d003plan 组各自专有的 clean_env 与断点符号逐一比对命中数；K_INHERIT_R9M1R2.tsv 虽汇总 m1_points_count 为 416，但未给出与 M1 651 行运行点的逐行归属对应表。"
])

audit_tsv_path = os.path.join(EV, "AUDIT_R9M1R2_R9M1R3.tsv")
with open(audit_tsv_path, "w", encoding="utf-8") as f:
    f.write("# AUDIT_R9M1R2_R9M1R3.tsv -- Verification and audit of G-1..G-8 in r9m1r2 (Step S-B)" + chr(10))
    f.write(chr(9).join(["item", "fact_description", "log_line_or_file_line", "conclusion", "details"]) + chr(10))
    for r in audit_rows:
        f.write(chr(9).join(r) + chr(10))
print(f"Wrote AUDIT_R9M1R2_R9M1R3.tsv ({len(audit_rows)} rows).")

# --------------------------------------------------------------------
# 2. Forensic recovery of r9m1r2 script versions from safe_run.log
# --------------------------------------------------------------------
log_path = os.path.join(M1R2_EV, "safe_run.log")
with open(log_path, "r", encoding="utf-8") as f:
    log_lines = f.read().splitlines()

extracted_scripts = []
for idx, line in enumerate(log_lines, 1):
    parts = line.split(chr(9))
    utc_ts = parts[0]
    cmd = parts[3] if len(parts) > 3 else ""

    cursor = 0
    while True:
        pos_open = line.find("open('", cursor)
        if pos_open == -1:
            pos_open = line.find('open("', cursor)
            if pos_open == -1:
                break
            q = '"'
        else:
            q = "'"
        cursor = pos_open + 6
        end_fname = line.find(q, cursor)
        if end_fname == -1:
            break
        fpath = line[cursor:end_fname]
        cursor = end_fname + 1
        fname = os.path.basename(fpath)
        
        pos_b64 = line.find("base64.b64decode(", cursor)
        if pos_b64 == -1 or pos_b64 > cursor + 30:
            continue
        q_b64 = line[pos_b64 + 17]
        if q_b64 not in ("'", '"'):
            continue
        start_b64 = pos_b64 + 18
        end_b64 = line.find(q_b64, start_b64)
        if end_b64 == -1:
            continue
        b64_content = line[start_b64:end_b64]
        cursor = end_b64 + 1

        try:
            data = base64.b64decode(b64_content)
            sha = hashlib.sha256(data).hexdigest()
            extracted_scripts.append((fname, idx, utc_ts, len(data), sha, data))
        except Exception:
            pass

script_version_rows = []
by_script = {}
for fname, line_num, utc_ts, length, sha, data in extracted_scripts:
    base_name = os.path.splitext(fname)[0]
    out_fname = f"{base_name}_line{line_num}.py"
    out_fpath = os.path.join(FORENSIC_DIR, out_fname)
    with open(out_fpath, "wb") as f:
        f.write(data)

    text_lines = data.decode("utf-8", errors="replace").splitlines(keepends=True)
    prev = by_script.get(fname)
    if prev is None:
        diff_lines = 0
        diff_note = "initial_version"
    else:
        prev_lines = prev.decode("utf-8", errors="replace").splitlines(keepends=True)
        udiff = list(difflib.unified_diff(prev_lines, text_lines))
        diff_lines = len(udiff)
        diff_note = f"{diff_lines}_diff_lines_vs_previous"

    by_script[fname] = data
    script_version_rows.append([fname, str(line_num), utc_ts, sha, str(length), str(diff_lines), diff_note, out_fname])

script_versions_tsv = os.path.join(EV, "SCRIPT_VERSIONS_R9M1R3.tsv")
with open(script_versions_tsv, "w", encoding="utf-8") as f:
    f.write("# SCRIPT_VERSIONS_R9M1R3.tsv -- Forensic script versions extracted from r9m1r2 safe_run.log (Step S-B)" + chr(10))
    f.write(chr(9).join(["script_name", "safe_run_line", "utc_timestamp", "sha256", "bytes", "diff_lines", "diff_note", "recovered_file"]) + chr(10))
    for r in script_version_rows:
        f.write(chr(9).join(r) + chr(10))
print(f"Wrote SCRIPT_VERSIONS_R9M1R3.tsv ({len(script_version_rows)} versions).")

# --------------------------------------------------------------------
# 3. Bare write audit of m1r2 directory against safe_run.log
# --------------------------------------------------------------------
bare_rows = []
for root, dirs, files in os.walk(M1R2_EV):
    for fn in sorted(files):
        fp = os.path.join(root, fn)
        rel = os.path.relpath(fp, M1R2_EV)
        if rel.startswith("forensic/") or rel.startswith("shakedown/"):
            continue
        st = os.stat(fp)
        mtime_dt = datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc)
        mtime_str = mtime_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        fsize = st.st_size
        fsha = hashlib.sha256(open(fp, "rb").read()).hexdigest()

        matched_line = None
        for idx, line in enumerate(log_lines, 1):
            parts = line.split(chr(9))
            if len(parts) >= 4 and (fn in parts[3] or rel in parts[3]):
                matched_line = idx
                break

        classification = "LOGGED" if matched_line is not None else "UNLOGGED_BARE_WRITE_CANDIDATE"
        note = f"matched_safe_run_L{matched_line}" if matched_line is not None else "no_direct_cmd_match"
        bare_rows.append([rel, mtime_str, str(fsize), fsha, classification, note])

bare_audit_tsv = os.path.join(EV, "BARE_WRITE_AUDIT_R9M1R3.tsv")
with open(bare_audit_tsv, "w", encoding="utf-8") as f:
    f.write("# BARE_WRITE_AUDIT_R9M1R3.tsv -- Audit of all files in m1r2 evidence against safe_run.log (Step S-B)" + chr(10))
    f.write(chr(9).join(["relpath", "mtime_utc", "bytes", "sha256", "classification", "note"]) + chr(10))
    for r in bare_rows:
        f.write(chr(9).join(r) + chr(10))
print(f"Wrote BARE_WRITE_AUDIT_R9M1R3.tsv ({len(bare_rows)} files).")
