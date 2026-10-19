#!/usr/bin/env python3
# relr1_judge_maketest.py -- make test judge for REL-R1.  Same criteria and 'Ran N' reconciliation as
# judge_maketest_s5r3.py (U374), re-pointed at $EV of this round, plus the optional T7 fresh-clone log
# as an extra column.  A unittest unit is the line "test_x (mod.Class.test_x)"; its status is the first
# status word on that line or on a following line, scanning until the next unit line.
# The judge reads only the raw logs; it never reads a driver's PASS/FAIL summary line.
# modes: formal [LOGDIR] | posctrl  (positive control of the FLAKY/NEW_FAILURE/SUITE_DIFF judgements)
import os, sys, re, shutil, hashlib

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1")
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
STATUS_WORDS = ("expected failure", "unexpected success", "skipped", "ERROR", "FAIL", "ok")
UNIT_RE = re.compile(r"^(test_[A-Za-z0-9_]+) \(([A-Za-z0-9_.]+)\)(.*)$")
STATUS_RE = re.compile(r"\.\.\.\s+(ok|FAIL|ERROR|skipped|expected failure|unexpected success)\b")
LOGNAMES = ["B_p1", "F4_p1", "B_p2", "F4_p2"]
CLONE_LOG = "T7_clone.log"


def status_in(text):
    m = STATUS_RE.search(text)
    return m.group(1) if m else None


def read_lines(path):
    if not os.path.isfile(path):
        raise SystemExit("missing log: " + path)
    return open(path, encoding="utf-8", errors="replace").read().splitlines()


def split_blocks(lines):
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
    return blocks


def parse_unittest_block(block):
    units = []
    i = 0
    n = len(block)
    while i < n:
        line = block[i].strip()
        m = UNIT_RE.match(line)
        if not m:
            i += 1
            continue
        uid = m.group(2)
        status = status_in(m.group(3))
        j = i + 1
        while status is None and j < n:
            nxt = block[j].strip()
            if UNIT_RE.match(nxt):
                break
            status = status_in(nxt)
            j += 1
        units.append((uid, status if status else "UNRECOGNISED", i))
        i = j if j > i else i + 1
    return units


def block_facts(block):
    ran = None
    skipped = None
    for i, l in enumerate(block):
        m = re.search(r"^Ran (\d+) tests?", l.strip())
        if m:
            ran = int(m.group(1))
        if "OK (skipped=" in l:
            m2 = re.search(r"skipped=(\d+)", l)
            if m2:
                skipped = int(m2.group(1))
    if skipped is None and any(l.strip() == "OK" for l in block):
        skipped = 0
    return ran, skipped


def parse_log(path):
    lines = read_lines(path)
    blocks = split_blocks(lines)
    units = {}
    recon = {}
    for name in UNIT_STAGES:
        block = blocks.get(name, [])
        ents = parse_unittest_block(block)
        seen = {}
        for uid, st, idx in ents:
            if uid in seen:
                seen[uid] = "DUPLICATE"
            else:
                seen[uid] = st
        for uid, st in seen.items():
            units[uid] = (st, name)
        ran, skipped = block_facts(block)
        got_skipped = len([1 for uid, st in seen.items() if st == "skipped"])
        recon[name] = {"units": len(seen), "ran": ran, "skipped_expected": skipped, "skipped_got": got_skipped,
                       "ok": (ran is not None and len(seen) == ran and skipped is not None and got_skipped == skipped)}
    for name in STAGE_UNITS:
        block = blocks.get(name, [])
        failed = any(l.startswith("make: ***") and "Error" in l for l in block)
        units[name] = ("FAIL" if failed else ("ok" if block else "MISSING"), name)
        recon[name] = {"units": 1 if block else 0, "ran": None, "skipped_expected": None, "skipped_got": None,
                       "ok": bool(block) and not failed}
    return units, recon, blocks


def failing(units):
    return set(u for u, v in units.items() if v[0] in FAIL_STATUS)


def decide(run_units, recon_ok):
    b_fail = failing(run_units["B_p1"]) | failing(run_units["B_p2"])
    f_fail = failing(run_units["F4_p1"]) | failing(run_units["F4_p2"])
    new_fail = sorted(f_fail - b_fail)
    flaky = []
    for run in ("B", "F4"):
        a = run_units[run + "_p1"]
        b = run_units[run + "_p2"]
        for u in sorted(set(a) & set(b)):
            if a[u][0] != b[u][0]:
                flaky.append((run, u, a[u][0], b[u][0]))
    all_sets = [set(v) for v in run_units.values()]
    union = set()
    for s in all_sets:
        union |= s
    suite_diff = []
    for k, s in zip(LOGNAMES, all_sets):
        for u in sorted(union - s):
            suite_diff.append((u, "absent_in_" + k))
    if not recon_ok:
        verdict = "RECONCILE_FAIL"
    elif suite_diff:
        verdict = "SUITE_DIFF"
    elif new_fail:
        verdict = "NEW_FAILURE"
    elif flaky:
        verdict = "FLAKY"
    else:
        verdict = "NO_NEW_FAILURE"
    return verdict, {"B_fails": sorted(b_fail), "F4_fails": sorted(f_fail), "new_fails": new_fail,
                     "flaky": sorted(flaky), "suite_diff": suite_diff}


def run_formal(logdir, units_path=None, recon_path=None, verdict_path=None, verbose=True):
    run_units = {}
    recon_ok = True
    recon_rows = []
    for key in LOGNAMES:
        u, r, b = parse_log(os.path.join(logdir, key + ".log"))
        run_units[key] = u
        for stage in UNIT_STAGES:
            rr = r.get(stage, {})
            ok = rr.get("ok")
            recon_rows.append((key, stage, rr.get("units"), rr.get("ran"), rr.get("skipped_got"),
                               rr.get("skipped_expected"), "OK" if ok else "FAIL"))
            if not ok:
                recon_ok = False
        for stage in STAGE_UNITS:
            rr = r.get(stage, {})
            recon_rows.append((key, stage, rr.get("units"), "-", "-", "-", "OK" if rr.get("ok") else "FAIL"))
            if not rr.get("ok"):
                recon_ok = False
    clone_units = None
    clonep = os.path.join(logdir, CLONE_LOG)
    if os.path.isfile(clonep):
        clone_units, crecon, _ = parse_log(clonep)
    verdict, detail = decide(run_units, recon_ok)
    unit_count = len(run_units["B_p1"])
    cols = ["unit", "stage"] + LOGNAMES + ([CLONE_LOG[:-4]] if clone_units is not None else [])
    if units_path:
        with open(units_path, "w", encoding="utf-8") as fh:
            fh.write("# MAKETEST_UNITS_RELR1.tsv -- per unittest unit x the four make test passes (+ T7 clone log when present)." + NL)
            fh.write("# One row per unit; status words are the unittest status tokens read from the raw logs." + NL)
            fh.write(TAB.join(cols) + NL)
            for key, (st, stage) in sorted(run_units["B_p1"].items(), key=lambda kv: (kv[1][1], kv[0])):
                vals = [run_units[l].get(key, ("ABSENT", ""))[0] for l in LOGNAMES]
                if clone_units is not None:
                    vals.append(clone_units.get(key, ("ABSENT", ""))[0])
                fh.write(TAB.join([key, stage] + vals) + NL)
    if recon_path:
        with open(recon_path, "w", encoding="utf-8") as fh:
            fh.write("# MAKETEST_RECON_RELR1.tsv -- per log and unittest block: recognised units vs 'Ran N' vs skipped" + NL)
            fh.write(TAB.join(["log", "stage", "units", "ran_n", "skipped_got", "skipped_expected", "ok"]) + NL)
            for r in recon_rows:
                fh.write(TAB.join([str(x) for x in r]) + NL)
    if verdict_path:
        with open(verdict_path, "w", encoding="utf-8") as fh:
            fh.write("# MAKETEST_VERDICT_RELR1.tsv -- make test verdict for REL-R1 (same criteria as U374)" + NL)
            fh.write(TAB.join(["item", "value"]) + NL)
            t7 = "ABSENT"
            if clone_units is not None:
                same = set(clone_units) == set(run_units["F4_p1"])
                diff = sorted((set(clone_units) | set(run_units["F4_p1"])) - (set(clone_units) & set(run_units["F4_p1"])))
                t7 = "EQUAL_UNIT_SET" if same else "UNIT_SET_DIFF:" + ",".join(diff[:5])
            items = [("verdict", verdict), ("unit_count", str(unit_count)),
                     ("B_failing", ",".join(detail["B_fails"]) or "none"),
                     ("F4_failing", ",".join(detail["F4_fails"]) or "none"),
                     ("new_failures", ",".join(detail["new_fails"]) or "none"),
                     ("flaky", (";".join("%s:%s:%s->%s" % (a, b, c, d) for a, b, c, d in detail["flaky"])) or "none"),
                     ("suite_diff", (";".join("%s:%s" % f for f in detail["suite_diff"])) or "none"),
                     ("T7_clone_vs_F4", t7),
                     ("criteria", "F4 failing set subset of B failing set AND no F4 p1/p2 difference AND identical unit sets AND all four logs reconcile with Ran N / skipped=k")]
            for k, v in items:
                fh.write(TAB.join([k, v]) + NL)
    if verbose:
        for r in recon_rows:
            print("RECON %-6s %-22s units=%s ran=%s skipped=%s/%s %s" % r)
        print("VERDICT " + verdict)
        if clone_units is not None:
            print("T7 checkout units=%d" % len(clone_units))
    return verdict, detail, recon_rows, unit_count


def mode_posctrl():
    seeded = os.path.join(EV, "maketest")
    cases = []
    names = ["caseA_new_failure", "caseB_flaky", "caseC_suite_diff"]
    for cname in names:
        d = os.path.join(EV, "posctrl/maketest", cname)
        os.makedirs(d, exist_ok=True)
        for k in LOGNAMES:
            shutil.copyfile(os.path.join(seeded, k + ".log"), os.path.join(d, k + ".log"))
        cases.append((cname, d))
    results = []

    def flip_unit(path, want_status):
        lines = read_lines(path)
        blocks = split_blocks(lines)
        block = blocks["s4test_unittest"]
        ents = parse_unittest_block(block)
        start = lines.index([b for n, b in STAGES if n == "s4test_unittest"][0])
        for uid, st, idx in ents:
            if st != want_status:
                continue
            m = UNIT_RE.match(block[idx].strip())
            target_abs = None
            if m.group(3).strip() and status_in(m.group(3)) is not None:
                target_abs = start + idx
            else:
                for j in range(idx + 1, min(idx + 8, len(block))):
                    if UNIT_RE.match(block[j].strip()):
                        break
                    if status_in(block[j]) == want_status:
                        target_abs = start + j
                        break
            if target_abs is None:
                continue
            nl = lines[target_abs]
            pos = nl.rfind(want_status)
            repl = "FAIL" if want_status == "ok" else "ok"
            lines[target_abs] = nl[:pos] + repl + nl[pos + len(want_status):]
            open(path, "w", encoding="utf-8").write(NL.join(lines) + NL)
            return uid
        return None

    def rename_unit(path):
        lines = read_lines(path)
        for i, line in enumerate(lines):
            m = UNIT_RE.match(line.strip())
            if m and status_in(m.group(3)) is not None:
                lines[i] = line.replace(m.group(2), m.group(2) + "_RENAMED", 1)
                open(path, "w", encoding="utf-8").write(NL.join(lines) + NL)
                return m.group(2)
        return None

    d = cases[0][1]
    uid = flip_unit(os.path.join(d, "F4_p1.log"), "ok")
    results.append(("A_ONE_UNIT_FAIL_IN_F4", "NEW_FAILURE", d, "flipped %s ok->FAIL in F4_p1" % uid))
    d = cases[1][1]
    uid = flip_unit(os.path.join(d, "B_p2.log"), "ok")
    results.append(("B_UNIT_STATUS_DIFF_ACROSS_PASSES", "FLAKY", d, "flipped %s ok->FAIL in B_p2 only" % uid))
    d = cases[2][1]
    uid = rename_unit(os.path.join(d, "F4_p2.log"))
    results.append(("C_UNIT_RENAMED_IN_F4_P2", "SUITE_DIFF", d, "renamed %s in F4_p2" % uid))
    outrows = ["# POSCTRL_MAKETEST_RELR1.txt -- positive control of relr1_judge_maketest.py on tampered copies of the" + NL,
               "# formal logs (copies under $EV/posctrl/maketest/; the formal logs are never touched)." + NL]
    allok = True
    for name, want, d, note in results:
        verdict, detail, recon, cnt = run_formal(d, verbose=False)
        ok = verdict == want
        allok = allok and ok
        outrows.append("%s: %s (expected=%s actual=%s) -- %s" % (name, "PASS" if ok else "FAIL", want, verdict, note) + NL)
    outrows.append("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % ("PASS" if allok else "FAIL", sum(1 for r in results), len(results)) + NL)
    outp = os.path.join(EV, "POSCTRL_MAKETEST_RELR1.txt")
    open(outp, "w", encoding="utf-8").write("".join(outrows))
    print("".join(outrows).strip())
    print("WROTE " + os.path.relpath(outp, REPO))
    return 0 if allok else 1


def tmp_quick():
    # tiny self-check: the FLAKY branch of decide() is reached by the same code path as formal
    return 0


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "formal"
    if mode == "formal":
        logdir = os.path.join(EV, "maketest")
        return 0 if run_formal(logdir,
                               units_path=os.path.join(EV, "MAKETEST_UNITS_RELR1.tsv"),
                               recon_path=os.path.join(EV, "MAKETEST_RECON_RELR1.tsv"),
                               verdict_path=os.path.join(EV, "MAKETEST_VERDICT_RELR1.tsv"))[0] == "NO_NEW_FAILURE" else 1
    if mode == "posctrl":
        return mode_posctrl()
    print("unknown mode " + mode, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
