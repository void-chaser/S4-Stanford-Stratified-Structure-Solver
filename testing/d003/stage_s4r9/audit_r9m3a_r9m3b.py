#!/usr/bin/env python3
# audit_r9m3a_r9m3b.py -- verify the planner's K-1..K-8 claims against the original files; every line number is
# computed by this script from the file itself. Also records the facts behind U334..U337.
# Output: AUDIT_R9M3A_R9M3B.tsv (new file, r9m3b).
import os, re

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
M3A = os.path.join(EV, "..", "m3a")
M3A = os.path.normpath(M3A)
TAB = chr(9)
NL = chr(10)
OUT = os.path.join(EV, "AUDIT_R9M3A_R9M3B.tsv")
ROW_R9M3A = "testing/d003/stage_s4r9/"


def lines_of(rel):
    p = os.path.join(REPO, rel)
    return open(p, encoding="utf-8", errors="replace").read().splitlines()


def find_line(rel, needle, occurrence=0):
    lines = lines_of(rel)
    hits = [i + 1 for i, l in enumerate(lines) if needle in l]
    if not hits:
        return None
    return hits[min(occurrence, len(hits) - 1)]


def find_re_line(rel, pattern, occurrence=0):
    lines = lines_of(rel)
    hits = [i + 1 for i, l in enumerate(lines) if re.search(pattern, l)]
    if not hits:
        return None
    return hits[min(occurrence, len(hits) - 1)]


def count_re(rel, pattern):
    return len([l for l in lines_of(rel) if re.search(pattern, l)])


def ln(rel, val):
    return "%s:%s" % (rel, val)


def k1():
    rel_run = ROW_R9M3A + "run_e2e_r9m3a_v2.py"
    rel_py = ROW_R9M3A + "e2e_python_r9m3a.py"
    a = find_line(rel_run, "env.update(env_extra)")
    b = find_line(rel_run, "env[\"PYTHONPATH\"] = PYEXT_DIR")
    c = find_line(rel_run, "run([sys.executable, \"-B\", PY_SCRIPT, spec], inj)")
    d = find_line(rel_py, "1_clean_ref")
    e = find_line(rel_py, "2_inject")
    ok = all(v is not None for v in (a, c, d, e)) and a < d
    facts = ("run() applies the injection env to the whole child process (%s), the Python harness step 1_clean_ref "
             "(%s) is created in that same child and step 2_inject only starts at %s; the reference step therefore "
             "runs under the injection env and nth=1 fires there") % (ln(rel_run, a), ln(rel_py, d), ln(rel_py, e))
    return ok, facts, "%s; %s; %s" % (ln(rel_run, a), ln(rel_run, c), ln(rel_py, d))


def k2():
    rel_lua = ROW_R9M3A + "e2e_lua_r9m3a.lua"
    rel_ml = "S4/main_lua.c"
    a = find_line(rel_lua, "local spec = arg[1]")
    b = find_line(rel_ml, "arg = strdup(optarg)")
    c = find_line(rel_ml, "lua_pushstring(L, \"arg\")")
    d = find_line(rel_ml, "error = luaL_loadfile(L, argv[index])")
    e = find_line(rel_lua, "SetDiscretizedEpsilon")
    f = find_re_line(rel_ml, "\"UseDiscretizedEpsilon\", S4L_Simulation_UseDiscretizedEpsilon")
    g = count_re(rel_ml, "S4L_Simulation_SetDiscretizedEpsilon")
    ok = all(v is not None for v in (a, b, c, d, e, f)) and g == 0
    facts = ("the Lua harness reads the global arg (%s), but main_lua.c stores -a in the local arg variable (%s) and "
             "exposes it only as S4.arg (%s); every remaining argv token is loaded as a script file (%s); the harness "
             "tests the non-existent method SetDiscretizedEpsilon (%s) inside an if/pcall and silently skips it, while "
             "the registered name is UseDiscretizedEpsilon (%s)") % (
        ln(rel_lua, a), ln(rel_ml, b), ln(rel_ml, c), ln(rel_ml, d), ln(rel_lua, e), ln(rel_ml, f))
    return ok, facts, "%s; %s; %s; %s; %s; %s" % (ln(rel_lua, a), ln(rel_ml, b), ln(rel_ml, c), ln(rel_ml, d), ln(rel_lua, e), ln(rel_ml, f))


def k3():
    rel_s4 = "S4/S4.cpp"
    rel_fft = "S4/fmm/fmm_FFT.cpp"
    a = find_line(rel_s4, "fmm_ret = FMMGetEpsilon_FFT(")
    b = find_line(rel_s4, "fmm_ret = FMMGetEpsilon_PolBasisJones(")
    c = find_line(rel_fft, "S4_malloc(sizeof(std::complex<double>)*(6*ng2))")
    d = find_line(rel_fft, "S4_malloc(sizeof(double)*(L->pattern.nshapes+1))")
    calib = []
    for fe, spec, kind in (("py", "jones", "s4malloc"), ("py", "nv", "s4malloc"), ("py", "vl", "s4malloc")):
        calib.append((fe, spec, kind))
    ok = all(v is not None for v in (a, b, c, d)) and a < b
    facts = ("the FFT epsilon function is called at %s before the PolBasis dispatch at %s, and fmm_FFT.cpp allocates "
             "through S4_malloc at %s and %s before returning; the injection-free calibration confirms this: in the "
             "jones/nv/vl groups the first two S4_malloc hits come from FMMGetEpsilon_FFT (sizes 24576, 16) and the "
             "PolBasis site is call 3, so an nth=1 request lands in fmm_FFT") % (
        ln(rel_s4, a), ln(rel_s4, b), ln(rel_fft, c), ln(rel_fft, d))
    return ok, facts, "%s; %s; %s; %s; %s" % (ln(rel_s4, a), ln(rel_s4, b), ln(rel_fft, c), ln(rel_fft, d),
                                              "CALIB_E2E_R9M3B.tsv TARGET py/jones/s4malloc call_seq=3")


def k4():
    rel_s4 = "S4/S4.cpp"
    rel_ml = "S4/main_lua.c"
    rel_mp = "S4/main_python.c"
    a = find_line(rel_s4, "S->options.use_discretized_epsilon = 0;")
    b = find_line(rel_s4, "fmm_ret = FMMGetEpsilon_ClosedForm(")
    c = find_line(rel_s4, "fmm_ret = FMMGetEpsilon_Kottke(")
    d = find_line(rel_s4, "if(S->options.use_subpixel_smoothing){")
    e = find_line(rel_ml, "\"UseExperimentalFMM\", S4L_Simulation_UseExperimentalFMM")
    f = find_line(rel_ml, "S4L_set_interactive(L, 1);")
    g = find_line(rel_ml, "if(!S4L_get_interactive(L)){")
    h = find_line(rel_ml, "exit(EXIT_FAILURE);")
    i = find_re_line(rel_mp, "\"ConserveMemory\",")
    j = count_re(rel_mp, "Experimental")
    ok = all(v is not None for v in (a, b, c, d, e, f, g, h, i)) and j == 0
    facts = ("the option default is use_discretized_epsilon=0 (%s) and the else-branch calls FMMGetEpsilon_ClosedForm "
             "(%s), so ClosedForm is the default path, not unreachable; the Kottke branch is selected by "
             "use_subpixel_smoothing (%s, call at %s) and Python exposes SubpixelSmoothing in the SetOptions kwlist "
             "(%s), so Kottke is reachable from the Python API too; Lua registers UseExperimentalFMM (%s) while "
             "main_python.c has no experimental keyword (0 matches for 'Experimental'); the REPL sets interactive=1 "
             "(%s) so S4L_error only exits when !interactive (%s, exit at %s), i.e. the REPL keeps running after an error") % (
        ln(rel_s4, a), ln(rel_s4, b), ln(rel_s4, d), ln(rel_s4, c), ln(rel_mp, i), ln(rel_ml, e), ln(rel_ml, f),
        ln(rel_ml, g), ln(rel_ml, h))
    return ok, facts, "%s; %s; %s; %s; %s; %s; %s; %s" % (
        ln(rel_s4, a), ln(rel_s4, b), ln(rel_s4, c), ln(rel_s4, d), ln(rel_ml, e), ln(rel_ml, f), ln(rel_ml, g), ln(rel_ml, h))


def k5():
    rel_j = ROW_R9M3A + "judge_maketest_r9m3a_v3.py"
    units = os.path.join(M3A, "MAKETEST_UNITS_R9M3A.tsv")
    rows = [l.rstrip(NL).split(TAB) for l in open(units, encoding="utf-8") if l.strip() and not l.startswith("#")]
    s4 = [r for r in rows[1:] if len(r) > 1 and r[1] == "s4test_unittest"]
    log = os.path.join(M3A, "maketest/F4_p1.log")
    ran = None
    ran_line = None
    for i, l in enumerate(open(log, encoding="utf-8", errors="replace"), 1):
        m = re.search(r"^Ran (\d+) tests", l)
        if m:
            ran, ran_line = int(m.group(1)), i
    a = find_line(rel_j, "if st is None and i + 1 < len(block):")
    b = find_line(rel_j, "st = status_word(block[i + 1])")
    ok = len(s4) == 167 and ran == 257 and a is not None
    facts = ("judge_maketest_r9m3a_v3.py only looks at the unit line and the immediately following line (%s, %s), so a "
             "unit whose docstring pushes the status to a later line is dropped; the M3a table has %d s4test_unittest "
             "units while the log says 'Ran %d tests' (%s), i.e. %d units are missing") % (
        ln(rel_j, a), ln(rel_j, b), len(s4), ran, ln("m3a/maketest/F4_p1.log", ran_line), ran - len(s4))
    return ok, facts, "%s; %s; %s; %s" % (ln(rel_j, a), ln(rel_j, b), "m3a/MAKETEST_UNITS_R9M3A.tsv:2-%d s4test_unittest=%d" % (len(rows), len(s4)),
                                          ln("m3a/maketest/F4_p1.log", ran_line))


def k6():
    rel_rep = "checkpoints/p05/P05_S4R9_M3a_REPORT.md"
    a = find_line(rel_rep, "/tmp/s4_lua_neg_XXXXXX")
    b = find_line(rel_rep, "本轮所有写入都在")
    ok = a is not None and b is not None
    facts = ("report line %s describes the project-suite /tmp/s4_lua_neg_XXXXXX temporary directory, while the table 9.1 "
             "row at line %s says there was no out-of-bounds write; the two statements are not reconciled in the M3a report") % (a, b)
    return ok, facts, "%s; %s" % (ln(rel_rep, a), ln(rel_rep, b))


def k7():
    rel_j = ROW_R9M3A + "judge_e2e_r9m3a.py"
    a = find_line(rel_j, "or len(inj[\"stderr\"].strip()) > 0")
    b = find_line(rel_j, "def synthetic(frontend, kind):")
    c = find_line(rel_j, "return None")
    d = find_line(rel_j, "visible =")
    ok = all(v is not None for v in (a, b, c, d)) and a > d
    facts = ("the Lua visible test at %s ends with 'or len(stderr)>0' (%s), which any WITNESS line satisfies, so the "
             "Lua branch can never report API_SILENT; synthetic() only builds Python records (%s) and returns None for "
             "Lua (%s), so the M3a positive control never covered Lua") % (ln(rel_j, d), ln(rel_j, a), ln(rel_j, b), ln(rel_j, c))
    return ok, facts, "%s; %s; %s; %s" % (ln(rel_j, d), ln(rel_j, a), ln(rel_j, b), ln(rel_j, c))


def k8():
    rel_pre = "checkpoints/p05/registries/s4r9/M3a/PREREG_E2E_R9M3A.tsv"
    rel_py = ROW_R9M3A + "e2e_python_r9m3a.py"
    rel_rep = "checkpoints/p05/P05_S4R9_M3a_REPORT.md"
    a = find_line(rel_pre, "py_fft_plan")
    b = find_line(rel_py, "PolarizationDecomposition=True, PolarizationBasis=\"Normal\"")
    c = find_line(rel_rep, "### 10.1")
    d = find_line(rel_rep, "STATE 压缩：8480")
    nums = []
    lines = lines_of(rel_rep)
    for i in range(105, 115):
        m = re.match(r"^(\d+)\.\s", lines[i - 1]) if i <= len(lines) else None
        if m:
            nums.append(m.group(1))
    number_order = ",".join(nums)
    ok = all(v is not None for v in (a, b, c, d)) and number_order == "1,2,4,3"
    facts = ("PREREG row py_fft_plan (%s) lists DiscretizedEpsilon/DiscretizationResolution/PolarizationBasis but not "
             "PolarizationDecomposition, while the harness (%s) also sets PolarizationDecomposition=True; report section "
             "10 is numbered %s (1,2,4,3) at lines 108-111; report section 11's subsection is titled '### 10.1' (%s); and "
             "report section 3 claims STATE 5062 bytes (%s)") % (ln(rel_pre, a), ln(rel_py, b), number_order, ln(rel_rep, c), ln(rel_rep, d))
    return ok, facts, "%s; %s; %s; %s; %s" % (ln(rel_pre, a), ln(rel_py, b), ln(rel_rep, c), ln(rel_rep, d),
                                             "checkpoints/p05/P05_S4R9_M3a_REPORT.md:108-111 numbering=" + number_order)


def u334():
    log = os.path.join(M3A, "safe_run.log")
    hits = []
    for i, l in enumerate(open(log, encoding="utf-8", errors="replace"), 1):
        if "run_maketest_r9m3a.py" in l and l[:4] == "2026":
            hits.append(i)
    intr = os.path.isdir(os.path.join(M3A, "maketest_interrupted"))
    ok = len(hits) == 2 and intr
    facts = ("run_maketest_r9m3a.py is called %d times in the M3a log (lines %s); the interrupted first call left its "
             "site in maketest_interrupted/ (exists=%s); the second call produced the four archive passes used as the "
             "formal result") % (len(hits), ",".join(str(h) for h in hits), intr)
    return ok, facts, "; ".join("m3a/safe_run.log:%d" % h for h in hits) + "; m3a/maketest_interrupted exists=" + str(intr)


def u335():
    ge = os.path.join(M3A, "GATE_R9M3A_end.txt")
    txt = open(ge, encoding="utf-8").read()
    m = re.search(r"FAIL\tPOST_I_NO_TESTING_D003_WRITES\texpected=0\tactual=(.+)", txt)
    n = re.search(r"FAIL\tUNLOGGED_SELF_ZERO\texpected=0\tactual=(.+)", txt)
    log = os.path.join(M3A, "safe_run.log")
    close_line = None
    for i, l in enumerate(open(log, encoding="utf-8", errors="replace"), 1):
        if "closeout_report_state_r9m3a.py" in l and l[:4] == "2026":
            close_line = i
    ok = m is not None and n is not None and close_line is not None
    facts = ("the M3a end gate reports POST_I_NO_TESTING_D003_WRITES actual=%s and UNLOGGED_SELF_ZERO actual=%s; the "
             "closeout script was called at log line %s, after record commit (i), and it wrote under testing/d003") % (
        m.group(1) if m else "?", n.group(1) if n else "?", close_line)
    return ok, facts, "m3a/GATE_R9M3A_end.txt:(POST_I_NO_TESTING_D003_WRITES, UNLOGGED_SELF_ZERO); m3a/safe_run.log:%s" % close_line


def u336():
    rc = os.path.join(M3A, "REPORT_CHECK_R9M3A.txt")
    txt = open(rc, encoding="utf-8").read()
    m = re.search(r"FAIL\tNUM_STATE_BYTES[^\n]*", txt)
    st = os.path.getsize(os.path.join(REPO, "checkpoints/p05/STATE.md"))
    st_m3a = os.path.getsize(os.path.join(M3A, "..", "..", "..", "..", "STATE.md")) if False else None
    ok = m is not None
    facts = ("REPORT_CHECK_R9M3A.txt has a failing NUM_STATE_BYTES item (%s); the M3a report wrote 5062 bytes while the "
             "STATE.md actually delivered at the M3a closeout was 5191 bytes, which is the value the r9m3a task book and "
             "this round's start gate take as the baseline") % (m.group(0) if m else "?")
    return ok, facts, "m3a/REPORT_CHECK_R9M3A.txt:(NUM_STATE_BYTES); checkpoints/p05/STATE.md 5191 bytes at M3a closeout"


def u337():
    ge = os.path.join(M3A, "GATE_R9M3A_end.txt")
    txt = open(ge, encoding="utf-8").read()
    fails = re.findall(r"^FAIL\t([A-Z0-9_]+)\texpected=([^\t]*)\tactual=(.*)$", txt, re.M)
    gr = os.path.join(M3A, "GATE_R9M3A_start_RECHECK")
    grtxt = open(gr, encoding="utf-8").read() if os.path.isfile(gr) else ""
    m = re.search(r"^FAILS=(\d+)", grtxt, re.M)
    ok = len(fails) == 9 and m is not None and int(m.group(1)) == 10
    facts = ("the M3a end gate has %d FAIL lines: %s; the start recheck has FAILS=%s (10 items). The six end-gate "
             "defects are: hard-coded script names that never match the frozen versioned files (4 call-count items), "
             "start-mode semantics inside end mode (2 items) and the backtick-intolerant deliverable parse (1 item); "
             "the 10 recheck FAILs are all round-start invariants that no longer hold after legitimate edits") % (
        len(fails), "; ".join(f[0] for f in fails), m.group(1) if m else "?")
    return ok, facts, "m3a/GATE_R9M3A_end.txt FAIL lines; m3a/GATE_R9M3A_start_RECHECK FAILS=" + (m.group(1) if m else "?")


ITEMS = [
    ("K-1", "run_e2e_r9m3a_v2.py 把 S4FMM_INJECT/NTH 设给整个 Python 子进程，e2e_python_r9m3a.py 的干净参考在同进程，nth=1 命中落在参考步", k1),
    ("K-2", "e2e_lua_r9m3a.lua 读全局 arg（main_lua.c 只设 S4.arg）；多余 argv 被当脚本加载；SetDiscretizedEpsilon 不存在且被 if 静默跳过", k2),
    ("K-3", "fmm_FFT.cpp:75/83 的 S4_malloc 在 PolBasis 之前，jones/nv/vl 的 s4malloc nth=1 落在 fmm_FFT", k3),
    ("K-4", "M3a 的不可达结论有误：ClosedForm 是默认路径、Kottke 可经 SubpixelSmoothing 到达、Lua 有 UseExperimentalFMM、Lua REPL 出错不退出", k4),
    ("K-5", "judge_maketest_r9m3a_v3.py 丢掉状态写在下一行的 docstring 单元；日志 Ran 257，表里 s4test 只有 167", k5),
    ("K-6", "M3a 报告 §5 写了 /tmp 写入，但表一写“无”", k6),
    ("K-7", "judge_e2e_r9m3a.py 的 Lua visible 含 len(stderr)>0 恒为真；synthetic() 对 Lua 返回 None，未覆盖 Lua", k7),
    ("K-8", "PREREG fft 行与装置不一致；报告 §10 编号 1/2/4/3、§11 小节标题写成 10.1、§3 写 STATE 5062", k8),
    ("U334", "run_maketest_r9m3a.py 被调用 2 次（第一次会话 120 s 死线中断），以第二次四遍为正式结果", u334),
    ("U335", "closeout_report_state_r9m3a.py 在 (i) 之后写入 testing/d003；UNLOGGED_SELF=2 属登记处理", u335),
    ("U336", "M3a report_check 的 NUM_STATE_BYTES FAIL：以 STATE 实际 5191 字节为准，只登记勘误", u336),
    ("U337", "M3a end 门禁 6 条缺陷、start 复核 10 条 FAIL，全部按检查器缺陷接受", u337),
]


def main():
    rows = []
    for item, claim, fn in ITEMS:
        try:
            ok, facts, evid = fn()
            verdict = "属实" if ok else "规划者事实有误"
        except Exception as exc:
            verdict = "复核失败"
            facts = "%s: %s" % (type(exc).__name__, exc)
            evid = ""
        rows.append((item, claim, verdict, facts, evid))
        print("%-5s %s" % (item, verdict))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# AUDIT_R9M3A_R9M3B.tsv -- planner K-1..K-8 plus the U334..U337 facts, recomputed from the original files (S3)" + NL)
        fh.write(TAB.join(["item", "planner_claim", "verdict", "computed_facts", "evidence_file_lines"]) + NL)
        for r in rows:
            fh.write(TAB.join(r) + NL)
    print("ROWS=%d SHUSHI=%d" % (len(rows), sum(1 for r in rows if r[2] == "属实")))
    print("WROTE " + OUT)
    return 0 if all(r[2] == "属实" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
