#!/usr/bin/env python3
# relr1_verdict.py -- M3 of REL-R1: judge every pre-registered unit from the on-disk observation tables
# BY COLUMN NAME.  It reads rc, signals, file sha256 and numdiff results only (plus the unittest status
# tokens for T1); it never reads a driver's PASS/FAIL summary line.  Categories:
#   SAME, DIFF_WITHIN_TOL, DIFF, NEW_FAIL, FIXED, BOTH_FAIL, TIMEOUT, SKIP_DECLARED, FLAKY.
# Modes: formal | posctrl
import os, sys, json, hashlib, subprocess, shutil

REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1")
TREES = os.path.join(EV, "trees")
UNITS = os.path.join(EV, "units")
TAB = chr(9)
NL = chr(10)
CATEGORIES = ["SAME", "DIFF_WITHIN_TOL", "DIFF", "NEW_FAIL", "FIXED", "BOTH_FAIL", "TIMEOUT", "SKIP_DECLARED", "FLAKY"]
FAIL_STATUS = ("FAIL", "ERROR", "unexpected success")
EXPECTED_UNIT_COUNT = 265


def relmax(p1, p2):
    try:
        a = open(p1, encoding="utf-8", errors="replace").read().split()
        b = open(p2, encoding="utf-8", errors="replace").read().split()
    except OSError:
        return "NONE"
    if len(a) != len(b):
        return "LEN_DIFF"
    m = 0.0
    for x, y in zip(a, b):
        try:
            fx, fy = float(x), float(y)
        except ValueError:
            if x != y:
                return "NONNUMERIC_DIFF"
            continue
        m = max(m, abs(fx - fy) / max(abs(fx), abs(fy), 1e-300))
    return "%.3e" % m


def numdiff_rc(f1, f2, tol="1e-12"):
    tool = os.path.join(REPO, "testing", "numdiff")
    if not (os.path.isfile(f1) and os.path.isfile(f2)):
        return "MISSING_FILE"
    p = subprocess.run(["perl", tool, f1, f2, tol], cwd=EV, capture_output=True, text=True)
    return p.returncode


def read_kv(path):
    d = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        k, _, v = line.rstrip(NL).partition(TAB)
        d[k] = v
    return d


def read_prereg():
    rows, hdr = [], None
    for line in open(os.path.join(EV, "PREREG_RELR1.tsv"), encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def load_units(units_dir=None):
    d = {}
    src = units_dir or UNITS
    if not os.path.isdir(src):
        return d
    for n in sorted(os.listdir(src)):
        if n.endswith(".tsv"):
            u = read_kv(os.path.join(src, n))
            if u.get("unit_id"):
                d[u["unit_id"]] = u
    return d


def read_tsv_rows(path):
    rows, hdr = [], None
    if not os.path.isfile(path):
        return rows
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if hdr is None:
            hdr = f
            continue
        rows.append(dict(zip(hdr, f)))
    return rows


def read_maketest():
    verdict = {}
    for r in read_tsv_rows(os.path.join(EV, "MAKETEST_VERDICT_RELR1.tsv")):
        verdict[r["item"]] = r["value"]
    units = read_tsv_rows(os.path.join(EV, "MAKETEST_UNITS_RELR1.tsv"))
    recon = read_tsv_rows(os.path.join(EV, "MAKETEST_RECON_RELR1.tsv"))
    return verdict, units, recon


def cross_tree_cat(b, f):
    """category from two per-tree normalised statuses (ok/fail/timeout)."""
    if b == "timeout" or f == "timeout":
        return "TIMEOUT"
    if b == "ok" and f == "ok":
        return "SAME"
    if b == "ok" and f == "fail":
        return "NEW_FAIL"
    if b == "fail" and f == "ok":
        return "FIXED"
    return "BOTH_FAIL"


def norm_status(st, rc):
    if st == "TIMEOUT" or rc == "TIMEOUT":
        return "timeout"
    if st in ("PASS", "RAN_OK", "ok", "skipped", "expected failure"):
        return "ok"
    return "fail"


def judge_t1(prereg):
    verdict, units, recon = read_maketest()
    out = []
    done = {}
    md = os.path.join(EV, "maketest")
    for seg in ("B_p1", "B_p2", "F4_p1", "F4_p2"):
        p = os.path.join(md, seg + ".done")
        if os.path.isfile(p):
            kv = {}
            for tok in open(p, encoding="utf-8").read().split():
                k, _, v = tok.partition("=")
                kv[k] = v
            done[seg] = kv
    for seg in ("B_p1", "B_p2", "F4_p1", "F4_p2"):
        tree, pas = seg.split("_")
        rc = done.get(seg, {}).get("rc", "MISSING")
        tree_ok = all(done.get(tree + "_p" + p, {}).get("rc") == "0" for p in ("1", "2"))
        cat = "SAME" if rc == "0" else "DIFF"
        out.append({"unit_id": "T1_%s" % seg, "suite": "T1_make_test", "category": cat,
                    "B_status": "ok" if tree == "B" and rc == "0" else ("fail" if tree == "B" else "na"),
                    "F4_status": "ok" if tree == "F4" and rc == "0" else ("fail" if tree == "F4" else "na"),
                    "detail": "segment rc=%s tree_both_passes_ok=%s" % (rc, tree_ok),
                    "prereg_units": "T1_%s" % seg, "source_table": "maketest/%s.done" % seg})
    n_unit = 0
    stage_seen = set()
    for r in units:
        u = r["unit"]
        vals = [r.get(k, "ABSENT") for k in ("B_p1", "F4_p1", "B_p2", "F4_p2")]
        b1, f1, b2, f2 = vals
        flaky = (b1 != b2) or (f1 != f2)
        if flaky:
            cat = "FLAKY"
        else:
            nb, nf = norm_status(b1, "0" if b1 != "UNRECOGNISED" else "1"), norm_status(f1, "0" if f1 != "UNRECOGNISED" else "1")
            if b1 in FAIL_STATUS and f1 in FAIL_STATUS:
                cat = "BOTH_FAIL"
            elif b1 in FAIL_STATUS and f1 not in FAIL_STATUS:
                cat = "FIXED"
            elif f1 in FAIL_STATUS and b1 not in FAIL_STATUS:
                cat = "NEW_FAIL"
            elif b1 == "UNRECOGNISED" or f1 == "UNRECOGNISED":
                cat = "DIFF"
            else:
                cat = "SAME"
        if r.get("stage") in ("selftest_analytic", "lua_regression", "lua_regression_negative", "lua_api_negative"):
            uid = "T1_STAGE_" + r["stage"]
            stage_seen.add(r["stage"])
        else:
            uid = "T1_UNIT_" + u
            n_unit += 1
        out.append({"unit_id": uid, "suite": "T1_make_test", "category": cat,
                    "B_status": norm_status(b1, "0"), "F4_status": norm_status(f1, "0"),
                    "detail": "B_p1=%s F4_p1=%s B_p2=%s F4_p2=%s" % (b1, f1, b2, f2),
                    "prereg_units": "", "source_table": "MAKETEST_UNITS_RELR1.tsv"})
    for stage in ("selftest_analytic", "lua_regression", "lua_regression_negative", "lua_api_negative"):
        if stage not in stage_seen:
            out.append({"unit_id": "T1_STAGE_" + stage, "suite": "T1_make_test", "category": "DIFF",
                        "B_status": "missing", "F4_status": "missing", "detail": "stage block missing from the logs",
                        "prereg_units": "", "source_table": "MAKETEST_UNITS_RELR1.tsv"})
    verdict_units = verdict.get("unit_count", "MISSING")
    out.append({"unit_id": "T1_UNIT_COUNT", "suite": "T1_make_test",
                "category": "SAME" if str(verdict_units) == str(EXPECTED_UNIT_COUNT) else "DIFF",
                "B_status": "na", "F4_status": "na",
                "detail": "unit_count=%s expected=%d" % (verdict_units, EXPECTED_UNIT_COUNT),
                "prereg_units": "", "source_table": "MAKETEST_VERDICT_RELR1.tsv"})
    for r in recon:
        if r.get("ok") != "OK":
            out.append({"unit_id": "T1_RECONCILE_%s_%s" % (r.get("log"), r.get("stage")), "suite": "T1_make_test",
                        "category": "DIFF", "B_status": "na", "F4_status": "na",
                        "detail": "units=%s ran_n=%s skipped=%s/%s" % (r.get("units"), r.get("ran_n"),
                                                                       r.get("skipped_got"), r.get("skipped_expected")),
                        "prereg_units": "", "source_table": "MAKETEST_RECON_RELR1.tsv"})
    out.append({"unit_id": "T1_MAKETEST_VERDICT", "suite": "T1_make_test",
                "category": "SAME" if verdict.get("verdict") == "NO_NEW_FAILURE" else "DIFF",
                "B_status": "na", "F4_status": "na",
                "detail": "verdict=%s new_failures=%s flaky=%s suite_diff=%s" % (
                    verdict.get("verdict"), verdict.get("new_failures"), verdict.get("flaky"), verdict.get("suite_diff")),
                "prereg_units": "", "source_table": "MAKETEST_VERDICT_RELR1.tsv"})
    return out


def judge_t3(prereg, units):
    out = []
    t3 = [r for r in prereg if r["suite"] == "T3_examples" and r["expect_B"] != "SKIP_DECLARED"]
    by_ex = {}
    for r in t3:
        eid = r["unit_id"][len("T3_"):].rsplit("_", 2)[0]
        by_ex.setdefault(eid, []).append(r["unit_id"])
    for eid in sorted(by_ex):
        ids = by_ex[eid]
        obs = {}
        for uid in ids:
            pass_ = uid.rsplit("_p", 1)[1]
            tree = uid.rsplit("_", 2)[1]
            obs[(tree, pass_)] = units.get(uid, {})
        def rco(key):
            o = obs.get(key, {})
            return o.get("status"), o.get("rc"), o.get("timed_out"), o.get("stdout_sha256"), o.get("stderr_sha256")
        flaky = []
        for tree in ("B", "F4"):
            a, b = rco((tree, "1")), rco((tree, "2"))
            if a[0] != b[0] or a[1] != b[1] or a[2] != b[2] or a[3] != b[3] or a[4] != b[4]:
                flaky.append(tree)
        if flaky:
            cat = "FLAKY"
            detail = "two-pass difference in " + ",".join(flaky)
        else:
            def rcnorm(x):
                s = str(x)
                return int(s) if s.lstrip("-").isdigit() else x
            st_b, rc_b, to_b, so_b, se_b = rco(("B", "1"))
            st_f, rc_f, to_f, so_f, se_f = rco(("F4", "1"))
            rc_b, rc_f = rcnorm(rc_b), rcnorm(rc_f)
            if st_b is None or st_f is None:
                cat, detail = "DIFF", "missing observation"
            elif to_b == "YES" or to_f == "YES":
                cat = "TIMEOUT"
                detail = "B_timeout=%s F4_timeout=%s" % (to_b, to_f)
            elif rc_b == 0 and rc_f == 0:
                if so_b == so_f and se_b == se_f:
                    cat = "SAME"
                    detail = "stdout/stderr sha256 equal"
                else:
                    pb, pf = obs[("B", "1")].get("stdout_path", ""), obs[("F4", "1")].get("stdout_path", "")
                    nd = numdiff_rc(pb, pf, "1e-12")
                    rl = relmax(pb, pf)
                    if nd == 0 and se_b == se_f:
                        cat = "DIFF_WITHIN_TOL"
                        detail = "numdiff rc=0 max_rel=%s" % rl
                    else:
                        cat = "DIFF"
                        detail = "numdiff rc=%s max_rel=%s stderr_same=%s" % (nd, rl, se_b == se_f)
            elif rc_b == 0 and rc_f != 0:
                cat = "NEW_FAIL"
                detail = "B rc=%s F4 rc=%s" % (rc_b, rc_f)
            elif rc_b != 0 and rc_f == 0:
                cat = "FIXED"
                detail = "B rc=%s F4 rc=%s" % (rc_b, rc_f)
            else:
                cat = "BOTH_FAIL"
                detail = "B rc=%s F4 rc=%s" % (rc_b, rc_f)
                if se_b != se_f:
                    # both fail: decide whether the stderr difference is only the displayed .lua path
                    # (Lua truncates long absolute paths, so the two tree paths render differently)
                    try:
                        import re as _re
                        eb = open(os.path.join(REPO, obs[("B", "1")].get("stderr_path", "")), encoding="utf-8", errors="replace").read()
                        ef = open(os.path.join(REPO, obs[("F4", "1")].get("stderr_path", "")), encoding="utf-8", errors="replace").read()
                        def norm_err(t):
                            return NL.join(_re.sub(r"\S*\.lua:\d+:", lambda m: "<PATH>" + m.group(0).split("/")[-1], ln) for ln in t.splitlines())
                        norm = norm_err(eb) == norm_err(ef)
                        detail += "; stderr equivalent after normalising the displayed .lua path" if norm else "; stderr differs beyond the displayed path"
                    except OSError:
                        detail += "; stderr unreadable"
        out.append({"unit_id": "T3_" + eid, "suite": "T3_examples", "category": cat,
                    "B_status": obs.get(("B", "1"), {}).get("status", "missing"),
                    "F4_status": obs.get(("F4", "1"), {}).get("status", "missing"),
                    "detail": detail, "prereg_units": ";".join(ids), "source_table": "units/T3_*.tsv"})
    return out


def judge_suite(prereg, units, suite, pairs, unit_prefix):
    """pairs: list of (comparison_unit_id, [(tree, unit_id), ...])"""
    out = []
    for cuid, members in pairs:
        trees = {}
        for tree, uid in members:
            trees[tree] = units.get(uid, {})
        b = trees.get("B", {})
        f = trees.get("F4", {})
        bs = norm_status(b.get("status", "MISSING"), b.get("rc", ""))
        fs = norm_status(f.get("status", "MISSING"), f.get("rc", ""))
        cat = cross_tree_cat(bs, fs)
        detail = "B status=%s rc=%s; F4 status=%s rc=%s" % (b.get("status"), b.get("rc"), f.get("status"), f.get("rc"))
        if suite == "T6_c_api":
            detail += "; numdiff_vs_reference B=%s F4=%s" % (b.get("numdiff_rc"), f.get("numdiff_rc"))
        out.append({"unit_id": cuid, "suite": suite, "category": cat, "B_status": bs, "F4_status": fs,
                    "detail": detail, "prereg_units": ";".join(uid for _, uid in members),
                    "source_table": "units/%s*.tsv" % unit_prefix})
    return out


def judge_t4(units):
    u = units.get("T4_F4_p04_pipeline", {})
    cat = "SAME" if u.get("status") == "PASS" else "DIFF"
    return [{"unit_id": "T4_F4_p04_pipeline", "suite": "T4_p04_pipeline", "category": cat,
             "B_status": "na", "F4_status": norm_status(u.get("status", "MISSING"), u.get("rc", "MISSING")),
             "detail": u.get("extra", ""), "prereg_units": "T4_F4_p04_pipeline", "source_table": "units/T4_*.tsv"}]


def judge_t7(prereg, units):
    u = units.get("T7_clone_maketest", {})
    verdict, _, _ = read_maketest()
    t7 = verdict.get("T7_clone_vs_F4", "ABSENT")
    ok = u.get("status") == "PASS" and t7 == "EQUAL_UNIT_SET"
    if ok:
        cat = "SAME"
    elif u.get("status") == "PASS" and t7 != "EQUAL_UNIT_SET":
        cat = "DIFF"
    else:
        cat = "NEW_FAIL"
    return [{"unit_id": "T7_clone_maketest", "suite": "T7_fresh_clone", "category": cat,
             "B_status": "na", "F4_status": norm_status(u.get("status", "MISSING"), u.get("rc", "")),
             "detail": "make test rc=%s clone_vs_F4=%s" % (u.get("rc"), t7),
             "prereg_units": "T7_clone_maketest", "source_table": "units/T7_*.tsv + MAKETEST_VERDICT_RELR1.tsv"}]


def judge_all(prereg, units):
    rows = []
    rows += judge_t1(prereg)
    # T2
    pairs = []
    for case in ("simple", "fresnel", "fanfig12"):
        pairs.append(("T2_%s" % case, [("B", "T2_B_%s" % case), ("F4", "T2_F4_%s" % case)]))
    pairs.append(("T2_runtests_sh", [("B", "T2_B_runtests_sh"), ("F4", "T2_F4_runtests_sh")]))
    rows += judge_suite(prereg, units, "T2_runtests_reference", pairs, "T2_")
    rows += judge_t3(prereg, units)
    rows += judge_t4(units)
    # T5
    pairs = [("T5_p04_aggregate", [("B", "T5_B_p04_aggregate"), ("F4", "T5_F4_p04_aggregate")]),
             ("T5_d002", [("B", "T5_B_d002"), ("F4", "T5_F4_d002")])]
    rows += judge_suite(prereg, units, "T5_p04_unit_tests", pairs, "T5_")
    # T6
    rows += judge_suite(prereg, units, "T6_c_api",
                        [("T6_capi", [("B", "T6_B_capi"), ("F4", "T6_F4_capi")])], "T6_")
    rows += judge_t7(prereg, units)
    # declared skips and record-only units straight from the pre-registration (anything not judged above)
    covered = set()
    for r in rows:
        for uid in (r.get("prereg_units") or "").split(";"):
            if uid:
                covered.add(uid)
    for r in prereg:
        if r["unit_id"] in covered:
            continue
        rule = r.get("compare_rule", "")
        if rule == "RECORD_ONLY":
            detail = "RECORD_ONLY (not judged): " + r["note"][:280]
        elif rule == "SKIP_DECLARED" or r.get("expect_B") == "SKIP_DECLARED" or r.get("expect_F4") == "SKIP_DECLARED":
            detail = r["note"][:300]
        else:
            detail = "NOT_OBSERVED: pre-registered unit has no observation"
        rows.append({"unit_id": r["unit_id"], "suite": r["suite"], "category": "SKIP_DECLARED",
                     "B_status": "na", "F4_status": "na", "detail": detail,
                     "prereg_units": r["unit_id"], "source_table": "PREREG_RELR1.tsv"})
    return rows


def write_tables(rows, verdict_path, summary_path, prereg):
    cols = ["unit_id", "suite", "category", "B_status", "F4_status", "detail", "prereg_units", "source_table"]
    lines = ["# VERDICT_RELR1.tsv -- REL-R1 judgement, one row per comparison unit",
             "# Categories: " + ", ".join(CATEGORIES),
             "# Rows whose prereg_units column is empty are detail rows (per-unittest-unit T1 rows, reconciliation and",
             "# unit-count checks); every pre-registered unit id appears in exactly one prereg_units column.",
             TAB.join(cols)]
    for r in rows:
        lines.append(TAB.join([r.get(c, "") for c in cols]))
    open(verdict_path, "w", encoding="utf-8").write(NL.join(lines) + NL)
    counts = {c: 0 for c in CATEGORIES}
    for r in rows:
        counts[r["category"]] = counts.get(r["category"], 0) + 1
    prereg_ids = set(r["unit_id"] for r in prereg)
    covered = set()
    for r in rows:
        for uid in (r["prereg_units"] or "").split(";"):
            if uid:
                covered.add(uid)
    missing = sorted(prereg_ids - covered)
    extra = sorted(covered - prereg_ids)
    timeouts = [r for r in rows if r["category"] == "TIMEOUT"]
    timeout_pairs_same = all(r["B_status"] == "timeout" and r["F4_status"] == "timeout" for r in timeouts)
    bad = [r for r in rows if r["category"] in ("NEW_FAIL", "DIFF", "FLAKY")]
    ok = not bad and timeout_pairs_same and not missing and not extra
    s = ["# SUMMARY_RELR1.txt -- P05 delivery round REL-R1 summary",
         "# counts are read from VERDICT_RELR1.tsv by column name; one category per line",
         "REGISTRY_ROWS=%d" % len(rows),
         "PREREG_UNITS=%d" % len(prereg_ids),
         "PREREG_UNITS_COVERED=%d" % len(covered)]
    for c in CATEGORIES:
        s.append("%s=%d" % (c, counts.get(c, 0)))
    s += ["TIMEOUT_BOTH_TREES_SAME=%s" % ("YES" if timeout_pairs_same else "NO"),
          "PREREG_UNITS_MISSING=%d" % len(missing),
          "PREREG_UNITS_EXTRA=%d" % len(extra),
          "NEW_FAIL_CONDITION=%s" % ("0" if counts["NEW_FAIL"] == 0 else str(counts["NEW_FAIL"])),
          "NON_REGRESSION=%s" % ("PASS" if ok else "FAIL")]
    if missing:
        s.append("MISSING_UNIT_IDS=" + ",".join(missing[:10]))
    if extra:
        s.append("EXTRA_UNIT_IDS=" + ",".join(extra[:10]))
    for r in bad:
        s.append("FAILING_UNIT" + TAB + r["unit_id"] + TAB + r["category"] + TAB + r["detail"][:200])
    open(summary_path, "w", encoding="utf-8").write(NL.join(s) + NL)
    return counts, ok, s


def posctrl(units):
    """3 tampered copies of the real T3 observations; same judging code path as the formal run."""
    base = os.path.join(EV, "posctrl", "verdict")
    seed_ids = ["T3_simple__simple_B_p1", "T3_simple__simple_B_p2", "T3_simple__simple_F4_p1", "T3_simple__simple_F4_p2"]
    SEED_EX = "T3_simple__simple"
    missing = [u for u in seed_ids if u not in units]
    if missing:
        print("HARD_STOP posctrl seed missing: " + ",".join(missing))
        return 2
    cases = []
    # A: one number changed in the F4 pass-1 stdout -> DIFF
    d = os.path.join(base, "caseA_stdout_digit_changed")
    os.makedirs(os.path.join(d, "units"), exist_ok=True)
    for uid in seed_ids:
        shutil.copyfile(os.path.join(UNITS, uid + ".tsv"), os.path.join(d, "units", uid + ".tsv"))
    # both F4 passes are changed identically, so determinism holds and the B-vs-F4 comparison is DIFF
    import re as _re
    for pas in ("p1", "p2"):
        o = units[SEED_EX + "_F4_" + pas]
        dst = os.path.join(d, "F4_%s.stdout" % pas)
        shutil.copyfile(o["stdout_path"], dst)
        txt = open(dst, encoding="utf-8", errors="replace").read()
        m = _re.search(r"[-+]?[0-9]+\.[0-9]+([eE][-+]?[0-9]+)?", txt)
        if not m:
            print("HARD_STOP posctrl A: no number in stdout")
            return 2
        txt2 = txt[:m.start()] + "123456789.5" + txt[m.end():]
        open(dst, "w", encoding="utf-8").write(txt2)
        tsv = read_kv(os.path.join(d, "units", SEED_EX + "_F4_" + pas + ".tsv"))
        tsv["stdout_path"] = os.path.relpath(dst, REPO)
        tsv["stdout_sha256"] = hashlib.sha256(txt2.encode()).hexdigest()
        write_kv(os.path.join(d, "units", SEED_EX + "_F4_" + pas + ".tsv"), tsv)
    cases.append(("A_ONE_STDOUT_NUMBER_CHANGED", "DIFF", d))
    # B: F4 rc made non-zero (both passes) -> NEW_FAIL
    d = os.path.join(base, "caseB_f4_rc_nonzero")
    os.makedirs(os.path.join(d, "units"), exist_ok=True)
    for uid in seed_ids:
        shutil.copyfile(os.path.join(UNITS, uid + ".tsv"), os.path.join(d, "units", uid + ".tsv"))
    for uid in (SEED_EX + "_F4_p1", SEED_EX + "_F4_p2"):
        t = read_kv(os.path.join(d, "units", uid + ".tsv"))
        t["rc"] = "1"
        t["status"] = "RAN_FAIL"
        write_kv(os.path.join(d, "units", uid + ".tsv"), t)
    cases.append(("B_F4_RETURN_CODE_NONZERO", "NEW_FAIL", d))
    # C: F4 pass-2 differs from F4 pass-1 -> FLAKY
    d = os.path.join(base, "caseC_f4_p2_differs")
    os.makedirs(os.path.join(d, "units"), exist_ok=True)
    for uid in seed_ids:
        shutil.copyfile(os.path.join(UNITS, uid + ".tsv"), os.path.join(d, "units", uid + ".tsv"))
    o = units[SEED_EX + "_F4_p2"]
    dst = os.path.join(d, "F4_p2.stdout")
    shutil.copyfile(o["stdout_path"], dst)
    txt = open(dst, encoding="utf-8", errors="replace").read() + "extra\n"
    open(dst, "w", encoding="utf-8").write(txt)
    t = read_kv(os.path.join(d, "units", SEED_EX + "_F4_p2.tsv"))
    t["stdout_path"] = os.path.relpath(dst, REPO)
    t["stdout_sha256"] = hashlib.sha256(txt.encode()).hexdigest()
    write_kv(os.path.join(d, "units", SEED_EX + "_F4_p2.tsv"), t)
    cases.append(("C_F4_PASS2_DIFFERS", "FLAKY", d))
    prereg = read_prereg()
    outrows = ["# POSCTRL_RELR1.txt -- positive control of relr1_verdict.py on tampered COPIES of the formal",
               "# T3 observations of examples/simple (copies under $EV/posctrl/verdict/; the formal units/ are untouched).",
               "# The same judging code path (judge_t3) is used for every case."]
    allok = True
    npass = 0
    for name, want, d in cases:
        tampered = load_units(os.path.join(d, "units"))
        rows = judge_t3(prereg, tampered)
        got = [r["category"] for r in rows if r["unit_id"] == SEED_EX]
        actual = got[0] if got else "NO_ROW"
        ok = actual == want
        allok = allok and ok
        npass += 1 if ok else 0
        outrows.append("%s: %s (expected=%s actual=%s) -- %s" % (name, "PASS" if ok else "FAIL", want, actual, d))
        write_tables(rows, os.path.join(d, "VERDICT.tsv"), os.path.join(d, "SUMMARY.txt"), prereg)
    outrows.append("OVERALL_POSITIVE_CONTROL: %s (%d/%d)" % ("PASS" if allok else "FAIL", npass, len(cases)))
    outrows.append("CATEGORIES_COVERED: DIFF,NEW_FAIL,FLAKY")
    outp = os.path.join(EV, "POSCTRL_RELR1.txt")
    open(outp, "w", encoding="utf-8").write(NL.join(outrows) + NL)
    print(NL.join(outrows))
    print("WROTE " + os.path.relpath(outp, REPO))
    return 0 if allok else 1


def write_kv(path, d):
    keys = ["unit_id", "suite", "tree", "pass", "status", "rc", "signal", "timed_out",
            "stdout_sha256", "stderr_sha256", "stdout_path", "stderr_path", "reference_path",
            "numdiff_rc", "numdiff_relmax", "dur_s", "extra"]
    lines = ["# tampered copy for the positive control; same schema as units/*.tsv"]
    for k in keys:
        lines.append(k + TAB + str(d.get(k, "")))
    open(path, "w", encoding="utf-8").write(NL.join(lines) + NL)


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "formal"
    prereg = read_prereg()
    units = load_units()
    if mode == "formal":
        rows = judge_all(prereg, units)
        vp = os.path.join(EV, "VERDICT_RELR1.tsv")
        sp = os.path.join(EV, "SUMMARY_RELR1.txt")
        counts, ok, lines = write_tables(rows, vp, sp, prereg)
        print("ROWS=%d" % len(rows))
        for c in CATEGORIES:
            print("%s=%d" % (c, counts.get(c, 0)))
        print("NON_REGRESSION=%s" % ("PASS" if ok else "FAIL"))
        print("WROTE " + os.path.relpath(vp, REPO))
        print("WROTE " + os.path.relpath(sp, REPO))
        return 0 if ok else 1
    if mode == "posctrl":
        return posctrl(units)
    print("unknown mode " + mode)
    return 2


if __name__ == "__main__":
    sys.exit(main())
