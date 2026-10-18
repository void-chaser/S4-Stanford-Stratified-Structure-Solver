#!/usr/bin/env python3
# judge_maketest_s5r3.py -- P05-S5 R3 make test judge. Copied from judge_maketest_r9m3b_v2.py
# (U374: same criteria, same "Ran N" reconciliation); s5r3 additions are the shakedown mode
# (single F4 run duplicated as four logs, marked SHAKEDOWN_DUP) and the four-case positive control.
# A unittest unit is the line "test_x (mod.Class.test_x)"; its status is the first status word on that
# line or on a following line, scanning until the next unit line.
# Reconciliation is mandatory: per log and per unittest block, the recognised unit count must equal
# "Ran N" and the skipped count must equal "OK (skipped=k)". Mismatch -> RECONCILE_FAIL.
# modes:
#   formal [LOGDIR UNITS VERDICT]
#   shakedown [LOGDIR]
#   posctrl [--seed-dir DIR] OUT.txt
import os, sys, re, shutil

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
SHK = os.path.join(EV, "shakedown")
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
    ran_line = None
    for i, l in enumerate(block):
        m = re.search(r"^Ran (\d+) tests?", l.strip())
        if m:
            ran, ran_line = int(m.group(1)), i
        if l.strip().startswith("OK (skipped=") or "OK (skipped=" in l:
            m2 = re.search(r"skipped=(\d+)", l)
            if m2:
                skipped = int(m2.group(1))
    if skipped is None and any(l.strip() == "OK" for l in block):
        skipped = 0
    return ran, skipped, ran_line


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
        ran, skipped, ran_line = block_facts(block)
        got_skipped = len([1 for uid, st in seen.items() if st == "skipped"])
        recon[name] = {
            "units": len(seen), "ran": ran, "skipped_expected": skipped, "skipped_got": got_skipped,
            "ran_line": ran_line, "ok": (ran is not None and len(seen) == ran and skipped is not None and got_skipped == skipped),
        }
    for name in STAGE_UNITS:
        block = blocks.get(name, [])
        failed = any(l.startswith("make: ***") and "Error" in l for l in block)
        units[name] = ("FAIL" if failed else ("ok" if block else "MISSING"), name)
        recon[name] = {"units": 1 if block else 0, "ran": None, "skipped_expected": None, "skipped_got": None,
                       "ran_line": None, "ok": bool(block) and not failed}
    return units, recon, blocks


def failing(units):
    return set(u for u, v in units.items() if v[0] in FAIL_STATUS)


def decide(run_units, run_recon, recon_ok):
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


def run_formal(logdir, units_path, verdict_path, verbose=True):
    run_units = {}
    run_recon = {}
    recon_ok = True
    recon_lines = []
    for key in LOGNAMES:
        u, r, b = parse_log(os.path.join(logdir, key + ".log"))
        run_units[key] = u
        run_recon[key] = r
        for stage in UNIT_STAGES + STAGE_UNITS:
            rr = r.get(stage, {})
            if stage in UNIT_STAGES:
                ok = rr.get("ok")
                recon_lines.append((key, stage, rr.get("units"), rr.get("ran"), rr.get("skipped_got"),
                                    rr.get("skipped_expected"), "OK" if ok else "FAIL"))
                if not ok:
                    recon_ok = False
    verdict, detail = decide(run_units, run_recon, recon_ok)
    rows = []
    unit_count = len(run_units["B_p1"])
    with open(units_path, "w", encoding="utf-8") as fh:
        fh.write("# MAKETEST_UNITS_S5R3.tsv -- per unit x 4 passes, parsed from the S5R3 formal logs (U374)" + NL)
        fh.write(TAB.join(["unit", "stage"] + LOGNAMES) + NL)
        for key, (st, stage) in sorted(run_units["B_p1"].items(), key=lambda kv: (kv[1][1], kv[0])):
            vals = [run_units[l].get(key, ("ABSENT", ""))[0] for l in LOGNAMES]
            rows.append((key, stage, vals))
            fh.write(TAB.join([key, stage] + vals) + NL)
    with open(verdict_path, "w", encoding="utf-8") as fh:
        fh.write("# MAKETEST_VERDICT_S5R3.tsv -- make test verdict for P05-S5 R3 (U374; same criteria as U333a)" + NL)
        fh.write(TAB.join(["item", "value"]) + NL)
        items = [("verdict", verdict), ("unit_count", str(unit_count)),
                 ("B_failing", ",".join(detail["B_fails"]) or "none"),
                 ("F4_failing", ",".join(detail["F4_fails"]) or "none"),
                 ("new_failures", ",".join(detail["new_fails"]) or "none"),
                 ("flaky", (";".join("%s:%s:%s->%s" % f for f in detail["flaky"])) or "none"),
                 ("suite_diff", (";".join("%s:%s" % f for f in detail["suite_diff"])) or "none"),
                 ("criteria", "F4 failing set subset of B failing set AND no F4 p1/p2 difference AND identical unit sets AND all four logs reconcile with Ran N / skipped=k")]
        for k, v in items:
            fh.write(TAB.join([k, v]) + NL)
        fh.write("# reconciliation rows: log/stage/units/Ran_N/skipped_got/skipped_expected/ok" + NL)
        for r in recon_lines:
            fh.write(TAB.join(["reconcile"] + [str(x) for x in r]) + NL)
    if verbose:
        for r in recon_lines:
            print("RECON %-6s %-20s units=%s ran=%s skipped=%s/%s %s" % r)
        print("VERDICT " + verdict)
        for k, v in items:
            print(k + "=" + v)
        print("WROTE " + units_path)
        print("WROTE " + verdict_path)
    return verdict, detail, recon_lines, unit_count


def mode_shakedown():
    logdir = os.path.join(SHK, "maketest")
    os.makedirs(logdir, exist_ok=True)
    src = os.path.join(EV, "maketest/F4_p1.log")
    if not os.path.isfile(src):
        print("HARD_STOP shakedown F4 run missing")
        return 2
    for k in LOGNAMES:
        shutil.copyfile(src, os.path.join(logdir, k + ".log"))
    open(os.path.join(logdir, "SHAKEDOWN_DUP"), "w").write(
        "all four logs are copies of the single F4 shakedown run (task brief section 6)" + NL)
    verdict, detail, recon, cnt = run_formal(logdir, os.path.join(logdir, "MAKETEST_UNITS_S5R3.tsv"),
                                             os.path.join(logdir, "MAKETEST_VERDICT_S5R3.tsv"))
    print("SHAKEDOWN verdict=%s unit_count=%d (SHAKEDOWN_DUP)" % (verdict, cnt))
    return 0 if verdict == "NO_NEW_FAILURE" else 1


def mode_posctrl(seeddir, out_txt):
    seed = {k: os.path.join(seeddir, k + ".log") for k in LOGNAMES}
    for k, p in seed.items():
        if not os.path.isfile(p):
            print("HARD_STOP posctrl seed missing " + p)
            return 2
    cases = []

    def fresh(case):
        d = os.path.join(EV, "posctrl/maketest", case)
        os.makedirs(d, exist_ok=True)
        for k in LOGNAMES:
            shutil.copyfile(seed[k], os.path.join(d, k + ".log"))
        return d

    def patch_status(path, uid, new_status):
        lines = read_lines(path)
        pat = re.compile(r"^(" + re.escape(uid) + r" \(.*?\)\.\.\.\s+)(ok|FAIL|ERROR|skipped)")
        hit = None
        for i, l in enumerate(lines):
            m = pat.match(l.strip())
            if m:
                hit = i
                break
        if hit is None:
            return False
        nl = lines[hit]
        pos = nl.rfind("ok")
        if pos < 0:
            return False
        lines[hit] = nl[:pos] + new_status + nl[pos + 2:]
        open(path, "w", encoding="utf-8").write(NL.join(lines) + NL)
        return True

    def flip_docstring_unit(d, logname):
        lines = read_lines(os.path.join(d, logname))
        blocks = split_blocks(lines)
        block = blocks["s4test_unittest"]
        ents = parse_unittest_block(block)
        for uid, st, idx in ents:
            if st == "ok":
                m = UNIT_RE.match(block[idx].strip())
                if not m.group(3).strip():
                    for j in range(idx + 1, min(idx + 8, len(block))):
                        if UNIT_RE.match(block[j].strip()):
                            break
                        if status_in(block[j]) == "ok":
                            start = lines.index([b for n, b in STAGES if n == "s4test_unittest"][0])
                            absj = start + j
                            nl = lines[absj]
                            pos = nl.rfind("ok")
                            lines[absj] = nl[:pos] + "FAIL" + nl[pos + 2:]
                            open(os.path.join(d, logname), "w", encoding="utf-8").write(NL.join(lines) + NL)
                            return uid, status_in(block[j])
        return None, None

    # A: one docstring-carried ok unit flipped to FAIL in F4_p1 -> NEW_FAILURE
    d = fresh("caseA_docstring_unit_ok_to_fail")
    uid, st = flip_docstring_unit(d, "F4_p1.log")
    if uid is None:
        print("HARD_STOP posctrl case A unit not found")
        return 2
    cases.append(("A_DOCSTRING_UNIT_OK_TO_FAIL", "NEW_FAILURE", d, "flipped %s (F4_p1) ok->FAIL" % uid))
    # B: one unit flipped ok->FAIL in B_p2 only -> FLAKY
    d = fresh("caseB_flaky")
    uid, st = flip_docstring_unit(d, "B_p2.log")
    if uid is None:
        print("HARD_STOP posctrl case B unit not patched")
        return 2
    cases.append(("B_FLAKY_P2_STATUS_DIFF", "FLAKY", d, "flipped %s in B_p2 only" % uid))
    # C: one unit renamed in F4_p2 only -> SUITE_DIFF (counts still reconcile with Ran N)
    d = fresh("caseC_suite_diff")
    lines = read_lines(os.path.join(d, "F4_p2.log"))
    hit = None
    for i, line in enumerate(lines):
        m = UNIT_RE.match(line.strip())
        if m and status_in(m.group(3)) is not None:
            hit = i
            break
    if hit is None:
        print("HARD_STOP posctrl case C unit not found")
        return 2
    m = UNIT_RE.match(lines[hit].strip())
    old_uid = m.group(2)
    new_uid = old_uid + "_RENAMED"
    lines[hit] = lines[hit].replace(old_uid, new_uid)
    open(os.path.join(d, "F4_p2.log"), "w", encoding="utf-8").write(NL.join(lines) + NL)
    cases.append(("C_SUITE_DIFF_UNIT_RENAMED", "SUITE_DIFF", d, "renamed %s -> %s in F4_p2" % (old_uid, new_uid)))
    # D: one unit line deleted from F4_p1 -> RECONCILE_FAIL (count no longer equals Ran N)
    d = fresh("caseD_reconcile_fail")
    lines = read_lines(os.path.join(d, "F4_p1.log"))
    blocks = split_blocks(lines)
    ents = parse_unittest_block(blocks["s4test_unittest"])
    drop_uid, drop_st, drop_idx = ents[5]
    start = lines.index([b for n, b in STAGES if n == "s4test_unittest"][0])
    del lines[start + drop_idx]
    open(os.path.join(d, "F4_p1.log"), "w", encoding="utf-8").write(NL.join(lines) + NL)
    cases.append(("D_DELETE_ONE_UNIT_LINE", "RECONCILE_FAIL", d, "deleted unit line " + drop_uid))
    results = []
    for name, want, d, note in cases:
        up = os.path.join(d, "UNITS.tsv")
        vp = os.path.join(d, "VERDICT.tsv")
        verdict, detail, recon, cnt = run_formal(d, up, vp, verbose=False)
        results.append((name, want, verdict, verdict == want, note))
    all_ok = all(r[3] for r in results)
    with open(out_txt, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_MAKETEST_S5R3.txt -- positive control of judge_maketest_s5r3.py on tampered on-disk log copies (U374)" + NL)
        fh.write("# seed logs: " + os.path.relpath(seeddir, REPO) + "/{B,F4}_p{1,2}.log; each case keeps all four copies on disk" + NL)
        fh.write("# verdict recomputed by the same formal code path (no constant self-proof)" + NL)
        for name, want, got, ok, note in results:
            fh.write("%s: %s (expected=%s actual=%s) -- %s" % (name, "PASS" if ok else "FAIL", want, got, note) + NL)
        fh.write("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % ("PASS" if all_ok else "FAIL",
                                                           sum(1 for r in results if r[3]), len(results)) + NL)
        fh.write("CATEGORIES_COVERED: " + ",".join(sorted(set(r[1] for r in results))) + NL)
    for name, want, got, ok, note in results:
        print("%-30s want=%-14s got=%-15s %s" % (name, want, got, "PASS" if ok else "FAIL"))
    print("OVERALL %s %d/%d" % ("PASS" if all_ok else "FAIL", sum(1 for r in results if r[3]), len(results)))
    return 0 if all_ok else 1


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "formal"
    if mode == "formal":
        logdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(EV, "maketest")
        units_path = sys.argv[3] if len(sys.argv) > 3 else os.path.join(EV, "MAKETEST_UNITS_S5R3.tsv")
        verdict_path = sys.argv[4] if len(sys.argv) > 4 else os.path.join(EV, "MAKETEST_VERDICT_S5R3.tsv")
        verdict, detail, recon, cnt = run_formal(logdir, units_path, verdict_path)
        return 0 if verdict == "NO_NEW_FAILURE" else 1
    if mode == "shakedown":
        return mode_shakedown()
    if mode == "posctrl":
        a = sys.argv
        seeddir = os.path.join(EV, "maketest")
        if "--seed-dir" in a:
            seeddir = a[a.index("--seed-dir") + 1]
        out_txt = a[a.index("--seed-dir") + 2] if "--seed-dir" in a else (a[2] if len(a) > 2 else os.path.join(EV, "POSCTRL_MAKETEST_S5R3.txt"))
        return mode_posctrl(seeddir, out_txt)
    print("unknown mode " + mode, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())