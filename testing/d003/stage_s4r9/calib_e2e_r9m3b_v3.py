#!/usr/bin/env python3
# calib_e2e_r9m3b_v2.py -- injection-free gdb calibration of the E2E option groups. New file (r9m3b).
# v2 fixes two v1 defects found in shakedown: (a) the site regex rejected the demangled symbol
# argument list, (b) the lua_repl run line must pass "-a SPEC" itself because gdb's "run < FILE"
# does not keep the --args list. No injection environment variable is set anywhere in this script.
# usage: python3 -I -B testing/d003/stage_s4r9/calib_e2e_r9m3b_v2.py [--only py:cf,lua_batch:exp]
import os, sys, subprocess, re

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3b")
TREE = os.path.join(EV, "trees/E2E_F4")
PY_SCRIPT = os.path.join(REPO, "testing/d003/stage_s4r9/e2e_python_r9m3b.py")
LUA_SCRIPT = os.path.join(REPO, "testing/d003/stage_s4r9/e2e_lua_r9m3b.lua")
REPL_SCRIPT = os.path.join(REPO, "testing/d003/stage_s4r9/e2e_lua_repl_r9m3b.txt")
LUA_BIN = os.path.join(TREE, "build/S4_e2e")
CALDIR = os.path.join(EV, "calib")
GDBDIR = os.path.join(EV, "tmp")
TAB = chr(9)
NL = chr(10)
GROUPS = ([("py", s) for s in ("cf", "fft", "kt", "jones", "nv", "vl")] +
          [("lua_batch", s) for s in ("cf", "fft", "kt", "jones", "nv", "vl", "exp")] +
          [("lua_repl", s) for s in ("cf", "fft", "kt", "vl")])
TARGET_FN = {"cf": "FMMGetEpsilon_ClosedForm", "fft": "FMMGetEpsilon_FFT", "kt": "FMMGetEpsilon_Kottke",
             "jones": "FMMGetEpsilon_PolBasisJones", "nv": "FMMGetEpsilon_PolBasisNV",
             "vl": "FMMGetEpsilon_PolBasisVL", "exp": "FMMGetEpsilon_Experimental"}


def gdb_cmd_file(fe, spec, tag):
    path = os.path.join(GDBDIR, "calib_%s_%s_%s.gdb" % (fe, spec, tag))
    lines = ["set pagination off", "set confirm off", "set breakpoint pending on",
             "set environment PYTHONPATH " + TREE,
             "set environment PYTHONDONTWRITEBYTECODE 1",
             "unset environment S4FMM_INJECT", "unset environment S4FMM_NTH",
             "set $s4n = 0", "set $pn = 0", "set $en = 0",
             "break __wrap__Z9S4_mallocm",
             "commands", "silent",
             "set $s4n = $s4n + 1",
             "printf \"EV_S4M seq=%d size=%lu\\n\", $s4n, (unsigned long)$rdi",
             "info symbol *(void **)$rsp",
             "continue", "end",
             "break __wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i",
             "commands", "silent",
             "set $pn = $pn + 1",
             "printf \"EV_PLAN seq=%d\\n\", $pn",
             "continue", "end",
             "break __wrap__Z13fft_plan_execP12tag_fft_plan",
             "commands", "silent",
             "set $en = $en + 1",
             "printf \"EV_EXEC seq=%d\\n\", $en",
             "continue", "end",
             "break __wrap_malloc",
             "commands", "silent",
             "printf \"EV_MALLOC size=%lu\\n\", (unsigned long)$rdi",
             "continue", "end"]
    if fe == "lua_repl":
        lines.append("run -a " + spec + " < " + REPL_SCRIPT)
    else:
        lines.append("run")
    lines += ["printf \"EV_END s4m=%d plan=%d exec=%d\\n\", $s4n, $pn, $en"]
    open(path, "w", encoding="utf-8").write(NL.join(lines) + NL)
    return path


def run_group(fe, spec):
    tag = "r9m3bv2"
    cmdf = gdb_cmd_file(fe, spec, tag)
    logp = os.path.join(CALDIR, "%s_%s.log" % (fe, spec))
    if fe == "py":
        argv = ["gdb", "-nx", "-batch", "-x", cmdf, "--args", "python3", "-B", PY_SCRIPT, "calib", spec]
    elif fe == "lua_batch":
        argv = ["gdb", "-nx", "-batch", "-x", cmdf, "--args", LUA_BIN, "-a", spec, LUA_SCRIPT]
    else:
        argv = ["gdb", "-nx", "-batch", "-x", cmdf, "--args", LUA_BIN, "-a", spec]
    env = dict(os.environ)
    env["PYTHONPATH"] = TREE
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("S4FMM_INJECT", None)
    env.pop("S4FMM_NTH", None)
    p = subprocess.run(argv, cwd=TREE, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=300)
    open(logp, "w", encoding="utf-8").write("### gdb calib %s %s%s%s" % (fe, spec, NL, p.stdout) + NL + "### rc=" + str(p.returncode) + NL)
    return p.returncode, p.stdout


def parse_events(text):
    events = []
    lines = text.splitlines()
    for i, line in enumerate(lines):
        m = re.match(r"^EV_S4M seq=(\d+) size=(\d+)$", line.strip())
        if m:
            site = "UNRESOLVED"
            j = i + 1
            while j < len(lines) and j <= i + 4:
                ln = lines[j].strip()
                if ln.startswith("EV_") or ln.startswith("### "):
                    break
                mm = re.match(r"^(.+?) \+ \d+ in section ", ln)
                if mm:
                    site = mm.group(1).strip()
                    site = re.sub(r"\(.*$", "", site)
                    break
                if ln.startswith("No symbol matches"):
                    break
                j += 1
            events.append({"kind": "s4malloc", "seq": int(m.group(1)), "size": int(m.group(2)), "site": site})
            continue
        m = re.match(r"^EV_PLAN seq=(\d+)$", line.strip())
        if m:
            events.append({"kind": "plan", "seq": int(m.group(1)), "size": None, "site": "fft_plan_dft_2d"})
            continue
        m = re.match(r"^EV_EXEC seq=(\d+)$", line.strip())
        if m:
            events.append({"kind": "exec", "seq": int(m.group(1)), "size": None, "site": "fft_plan_exec"})
            continue
        m = re.match(r"^EV_MALLOC size=(\d+)$", line.strip())
        if m:
            events.append({"kind": "malloc", "seq": None, "size": int(m.group(1)), "site": "malloc"})
    first_plan_malloc = None
    seen_plan1 = False
    for e in events:
        if e["kind"] == "plan" and e["seq"] == 1:
            seen_plan1 = True
            continue
        if seen_plan1 and e["kind"] == "plan" and e["seq"] == 2:
            break
        if seen_plan1 and e["kind"] == "malloc":
            first_plan_malloc = e["size"]
            break
    for e in events:
        if e["kind"] == "plan" and e["seq"] == 1:
            e["size"] = first_plan_malloc
    return events, first_plan_malloc


def main():
    os.makedirs(CALDIR, exist_ok=True)
    os.makedirs(GDBDIR, exist_ok=True)
    only = None
    if "--only" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",")
    rows = []
    targets = []
    fails = []
    for fe, spec in GROUPS:
        key = fe + ":" + spec
        if only and key not in only:
            continue
        rc, text = run_group(fe, spec)
        events, plan_malloc = parse_events(text)
        n_s4m = len([e for e in events if e["kind"] == "s4malloc"])
        n_plan = len([e for e in events if e["kind"] == "plan"])
        n_exec = len([e for e in events if e["kind"] == "exec"])
        print("CALIB %-9s %-5s rc=%d s4m=%d plan=%d exec=%d plan_malloc=%s" % (fe, spec, rc, n_s4m, n_plan, n_exec, plan_malloc))
        for e in events:
            rows.append(("EVENT", fe, spec, e["kind"], "" if e["seq"] is None else str(e["seq"]),
                         "" if e["size"] is None else str(e["size"]), e["site"], ""))
        tfn = TARGET_FN[spec]
        s4_first = [e for e in events if e["kind"] == "s4malloc" and tfn in e["site"]]
        if s4_first:
            targets.append(("TARGET", fe, spec, "s4malloc", str(s4_first[0]["seq"]), str(s4_first[0]["size"]),
                            s4_first[0]["site"], "first S4_malloc whose frame-1 symbol is " + tfn))
        else:
            fails.append(("NO_TARGET_S4MALLOC", fe, spec))
        if spec in ("fft", "kt") or (fe == "lua_repl" and spec == "fft"):
            if n_plan >= 1:
                targets.append(("TARGET", fe, spec, "plan", "1", "" if plan_malloc is None else str(plan_malloc),
                                "fft_plan_dft_2d", "first plan call; size = first malloc inside it"))
            else:
                fails.append(("NO_PLAN_CALL", fe, spec))
        if spec in ("fft", "kt") and fe != "lua_repl":
            if n_exec >= 1:
                targets.append(("TARGET", fe, spec, "exec", "1", "NA", "fft_plan_exec",
                                "first exec call; the HIT line carries no size"))
            else:
                fails.append(("NO_EXEC_CALL", fe, spec))
    out = os.path.join(EV, "CALIB_E2E_R9M3B.tsv")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# CALIB_E2E_R9M3B.tsv -- injection-free gdb calibration of the E2E option groups (S-C3), produced by calib_e2e_r9m3b_v2.py" + NL)
        fh.write("# Each frontend x option group was run under gdb -nx -batch with breakpoints on __wrap__Z9S4_mallocm," + NL)
        fh.write("# __wrap__Z15fft_plan_dft_2d..., __wrap__Z13fft_plan_exec... and __wrap_malloc. No injection variable was set." + NL)
        fh.write("# EVENT rows are the observed calls in hit order; TARGET rows give each point's nth and calibrated size." + NL)
        fh.write(TAB.join(["row_kind", "frontend", "spec", "kind", "call_seq", "size", "site", "note"]) + NL)
        for r in rows + targets:
            fh.write(TAB.join(r) + NL)
    print("WROTE " + out)
    print("EVENT_ROWS=%d TARGET_ROWS=%d FAILS=%d" % (len(rows), len(targets), len(fails)))
    for f in fails:
        print("FAIL " + TAB.join(f))
    return 0 if not fails else 1


if __name__ == "__main__":
    sys.exit(main())
