#!/usr/bin/env python3
# judge_maketest_r9m3a.py -- parse the make test logs into units and decide the F4-vs-B verdict (S-C step 3/4).
# modes:
#   formal  -- read <EV>/maketest/{B_p1,F4_p1,B_p2,F4_p2}.log and write MAKETEST_UNITS / MAKETEST_VERDICT
#   posctrl -- build synthetic logs from a seed log and verify the parser reports NEW_FAILURE and FLAKY
import os, sys

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a")
TAB = chr(9)
NL = chr(10)
STAGES = [
    ("test_python_binding", "=== original smoke tests (testing/test_python_binding.py) ==="),
    ("s4test_unittest", "=== S4 test suite (testing/s4test) ==="),
    ("selftest_analytic", "=== analytic reference self-check ==="),
    ("lua_regression", "=== S4 Lua test suite ==="),
    ("lua_regression_negative", "=== S4 Lua test suite negative ==="),
    ("lua_api_negative", "=== S4 Lua API negative ==="),
]
UNIT_STAGES = ("test_python_binding", "s4test_unittest")
STAGE_UNITS = ("selftest_analytic", "lua_regression", "lua_regression_negative", "lua_api_negative")
FAIL_STATUS = ("FAIL", "ERROR", "unexpected success")
STATUS_WORDS = ("ok", "FAIL", "ERROR", "expected failure", "unexpected success", "skipped", "FAILED")


def read_lines(path):
    if not os.path.isfile(path):
        raise SystemExit("missing log: " + path)
    return open(path, encoding="utf-8", errors="replace").read().splitlines()


def status_word(text):
    t = text.strip()
    for w in STATUS_WORDS:
        if t == w or t.startswith(w + " ") or t.startswith(w + ":") or t.startswith(w + " ("):
            return w
    return None


def parse_log(path):
    lines = read_lines(path)
    marks = []
    for name, banner in STAGES:
        for i, l in enumerate(lines):
            if l.strip() == banner:
                marks.append((i, name))
                break
    marks.sort()
    blocks = {}
    for k, (start, name) in enumerate(marks):
        end = marks[k + 1][0] if k + 1 < len(marks) else len(lines)
        blocks[name] = lines[start:end]
    units = {}
    for name in UNIT_STAGES:
        block = blocks.get(name, [])
        for i, raw in enumerate(block):
            line = raw.strip()
            if not line.startswith("test_") or "(" not in line:
                continue
            j = line.find("(")
            k = line.rfind(")")
            if k < j:
                continue
            uid = line[j + 1:k]
            if not uid or " " in uid:
                continue
            st = status_word(line[k + 1:])
            if st is None and i + 1 < len(block):
                st = status_word(block[i + 1])
            if st is None:
                continue
            units[uid] = (st, name)
    for name in STAGE_UNITS:
        block = blocks.get(name, [])
        failed = False
        for l in block:
            if l.startswith("make: ***") and "Error" in l:
                failed = True
        units[name] = ("FAIL" if failed else ("ok" if block else "MISSING"), name)
    return units, blocks


def failing(units):
    return set(u for u, v in units.items() if v[0] in FAIL_STATUS)


def decide(run_units):
    b_fail = failing(run_units["B_p1"]) | failing(run_units["B_p2"])
    f_fail = failing(run_units["F4_p1"]) | failing(run_units["F4_p2"])
    new_fail = sorted(f_fail - b_fail)
    flaky = []
    for run in ("B", "F4"):
        a = run_units[run + "_p1"]
        b = run_units[run + "_p2"]
        for u in set(a) & set(b):
            if a[u][0] != b[u][0]:
                flaky.append((run, u, a[u][0], b[u][0]))
    all_sets = [set(v) for v in run_units.values()]
    union = set()
    for s in all_sets:
        union |= s
    suite_diff = []
    for s in all_sets:
        for u in sorted(union - s):
            suite_diff.append((u, "absent"))
    detail = {"B_fails": sorted(b_fail), "F4_fails": sorted(f_fail), "new_fails": new_fail,
              "flaky": sorted(flaky), "suite_diff": suite_diff}
    if suite_diff:
        return "SUITE_DIFF", detail
    if new_fail:
        return "NEW_FAILURE", detail
    if flaky:
        return "FLAKY", detail
    return "NO_NEW_FAILURE", detail


def mode_formal(units_path, verdict_path):
    logdir = os.path.join(EV, "maketest")
    run_units = {}
    for run in ("B_p1", "F4_p1", "B_p2", "F4_p2"):
        u, _b = parse_log(os.path.join(logdir, run + ".log"))
        run_units[run] = u
    all_units = sorted(set().union(*[set(v) for v in run_units.values()]))
    with open(units_path, "w", encoding="utf-8") as fh:
        fh.write("# MAKETEST_UNITS_R9M3A.tsv -- per unit x 4 passes (S-C step 3)" + NL)
        fh.write(TAB.join(["unit", "stage", "B_p1", "F4_p1", "B_p2", "F4_p2"]) + NL)
        for u in all_units:
            row = [u]
            first = None
            for x in ("B_p1", "F4_p1", "B_p2", "F4_p2"):
                v = run_units[x].get(u, ("ABSENT", ""))
                row.append(v[0])
                if first is None and v[1]:
                    first = v[1]
            row.insert(1, first or "")
            fh.write(TAB.join(row) + NL)
    verdict, detail = decide(run_units)
    with open(verdict_path, "w", encoding="utf-8") as fh:
        fh.write("# MAKETEST_VERDICT_R9M3A.tsv -- make test verdict for R9 M3a (S-C step 3)" + NL)
        fh.write(TAB.join(["item", "value"]) + NL)
        fh.write(TAB.join(["verdict", verdict]) + NL)
        fh.write(TAB.join(["unit_count", str(len(all_units))]) + NL)
        fh.write(TAB.join(["B_failing", ",".join(detail["B_fails"]) or "none"]) + NL)
        fh.write(TAB.join(["F4_failing", ",".join(detail["F4_fails"]) or "none"]) + NL)
        fh.write(TAB.join(["new_failures", ",".join(detail["new_fails"]) or "none"]) + NL)
        fh.write(TAB.join(["flaky", str(detail["flaky"]) if detail["flaky"] else "none"]) + NL)
        fh.write(TAB.join(["suite_diff", str(detail["suite_diff"]) if detail["suite_diff"] else "none"]) + NL)
        fh.write(TAB.join(["criteria", "F4 failing set subset of B failing set AND no F4 p1/p2 difference AND identical unit sets"]) + NL)
    print("VERDICT %s units=%d new=%d flaky=%d suite_diff=%d" % (verdict, len(all_units), len(detail["new_fails"]), len(detail["flaky"]), len(detail["suite_diff"])))
    return 0


def write_log(d, name, lines):
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, name + ".log"), "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines) + NL)


def mode_posctrl(outdir, out_txt, seed):
    os.makedirs(outdir, exist_ok=True)
    base = read_lines(seed)
    caseA = os.path.join(outdir, "caseA_F4_one_extra_FAIL")
    fa = list(base)
    for i, l in enumerate(fa):
        if l.rstrip().endswith("... ok") and "(" in l:
            fa[i] = l.replace("... ok", "... FAIL")
            break
    for nm in ("B_p1", "B_p2", "F4_p2"):
        write_log(caseA, nm, base)
    write_log(caseA, "F4_p1", fa)
    caseB = os.path.join(outdir, "caseB_F4_p1_p2_differ")
    fb = list(base)
    for i, l in enumerate(fb):
        if l.rstrip().endswith("... ok") and "(" in l:
            fb[i] = l.replace("... ok", "... FAIL")
            break
    for nm in ("B_p1", "B_p2", "F4_p1"):
        write_log(caseB, nm, base)
    write_log(caseB, "F4_p2", fb)
    results = []
    for label, d, expect in (("CASE_A_F4_ONE_EXTRA_FAIL", caseA, "NEW_FAILURE"), ("CASE_B_F4_P1_P2_DIFFER", caseB, "FLAKY")):
        run_units = {}
        for run in ("B_p1", "F4_p1", "B_p2", "F4_p2"):
            u, _b = parse_log(os.path.join(d, run + ".log"))
            run_units[run] = u
        verdict, detail = decide(run_units)
        results.append((label, expect, verdict, verdict == expect, detail))
    all_ok = all(r[3] for r in results)
    with open(out_txt, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_MAKETEST_R9M3A.txt -- positive control of the make test parser/judge (S-C step 4)" + NL)
        fh.write("# seed log: " + seed + " (the shakedown F4 run; used only as a syntactically valid log body)" + NL)
        for label, expect, got, ok, detail in results:
            fh.write("%s: %s (expected=%s actual=%s new_failures=%s flaky=%s)" % (label, "PASS" if ok else "FAIL", expect, got, detail["new_fails"][:3], detail["flaky"][:3]) + NL)
        fh.write("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % ("PASS" if all_ok else "FAIL", sum(1 for r in results if r[3]), len(results)) + NL)
    for label, expect, got, ok, detail in results:
        print("%s expected=%s actual=%s PASS=%s" % (label, expect, got, ok))
    print("OVERALL %s" % ("PASS" if all_ok else "FAIL"))
    print("WROTE " + out_txt)
    return 0 if all_ok else 1


def main():
    if len(sys.argv) < 2:
        print("usage: judge_maketest_r9m3a.py formal UNITS VERDICT | posctrl OUTDIR OUT.txt SEED.log", file=sys.stderr)
        return 2
    mode = sys.argv[1]
    if mode == "formal":
        return mode_formal(sys.argv[2], sys.argv[3])
    if mode == "posctrl":
        return mode_posctrl(sys.argv[2], sys.argv[3], sys.argv[4])
    print("unknown mode", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
