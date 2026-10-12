#!/usr/bin/env python3
"""P05-S4 R7 cont6 (with ADD1 U68): M2b orchestrator (new file, rewritten in cont6).

Groups, in order (U67): CTRL_SEAM, G2c, G1, G2a.  G2c-control is NOT run (U65a: NOT_RUN_REGISTRY_ERROR).
Two passes each, tree F and F2.  Output RESULTS_R7_<G>_pass<P>_run5.tsv (never overwritten, U17).

Usage (through safe_run; absolute paths under $EV; U17):
  python3 -I -B testing/d003/stage_s4r7/run_m2b_all_r7.py dry-run EVDIR OUT.txt
  python3 -I -B testing/d003/stage_s4r7/run_m2b_all_r7.py run     EVDIR RUNTAG     (RUNTAG = run5)

Contract:
  - Judge: judge_d003.classify (imported, not modified).  CLASSES imported from judge_d003 (not copied).
  - verdict_of() is the ONLY place a verdict is decided (U68):
      expected INVALID_NOT_REACHED: NOT_REACHED_AS_EXPECTED iff cls == INVALID and hit == 0 and rc is not None; else MISMATCH.
      expected in CLASSES:          MATCH iff cls == expected; else MISMATCH.
  - Stop rule (U67, U68): after a group's two passes are complete, the run stops if the group has any MISMATCH or FLAKY.
    MATCH and NOT_REACHED_AS_EXPECTED do not stop the run.
  - FLAKY (U66): pass 1 and pass 2 differ in class, verdict, rc, rc1, rc2 or hit for the same point.
  - F versus F2 (U66): base id from compare_trees_r7.base_id; the five fields rc, rc1, rc2, hit, class compared.
  - Points: v2 (REGISTRY_S4_PRE_R7_M2.tsv, sha e4dd2c87...) joined to ADD (REGISTRY_S4_PRE_R7_M2_ADD_v2.tsv) on
    (point_id, tree, group) (E7-21(a)).  Request, inj_call, ng, real come from run_m2_r7.py (imported): point_spec,
    join_points, real_of, category_of, clean_env, GRID, sha256_file, run, facts, drivers_recorded.
  - CTRL_SEAM: REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv (U65b), drivers from DRIVERS_R7_SEAM.tsv, control=True.
  - G2a: seam drivers from DRIVERS_R7_SEAM.tsv (U61): request fmmret:* -> fmmret-<tree>; else seamF-<tree>.
  - G1: R7 driver d003-<tree>-plain (DRIVERS_R7.tsv).  G2c: d003plan-<tree>-plain.
  - Every driver sha256 and every seam library sha256 is checked before any run.
  - Outputs under $EV only: RESULTS_R7_<G>_pass<P>_run5.tsv, REGRESS_R7_M2b.tsv, M2B_SUMMARY_R7.txt,
    NONMATCH_OVERFLOW_R7_M2b.tsv (if more than 50 non-MATCH rows).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import run_m2_r7 as M  # noqa: E402  imported, not copied
import judge_d003 as J  # noqa: E402  imported, not modified
import matrix_r2 as MR  # noqa: E402  imported, not modified: build_env (U71a; matrix_r2.py:98-109)
from compare_trees_r7 import base_id  # noqa: E402  imported (U66)

GROUP_ORDER = ("CTRL_SEAM", "G2c", "G1", "G2a")
NOT_RUN_GROUP = "G2c-control"                 # U65a
NONMATCH_LIST_MAX = 50
SEAM_DRIVERS = "DRIVERS_R7_SEAM.tsv"
CTRL_SEAM_REG = "REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv"
# expected labels allowed in v2/ADD: judge classes, plus the G1 label of E7-4 (U68)
EXPECTED_OK = set(J.CLASSES) | {"INVALID_NOT_REACHED"}
# the FMM modes the driver accepts (driver_d003.cpp:173-175); checked in dry-run, not hand-typed elsewhere
DRIVER_MODES = ("fft", "kottke", "jones", "nv", "vl", "experimental", "closed2d", "closed1d", "tensor",
                "fftjones", "fftnv", "fftvl")
COLS = ["point_id", "group", "tree", "mode", "request", "inj_call", "expected_class", "class", "verdict",
        "rc", "rc1", "rc2", "hit", "reason"]


def verdict_of(expected, cls, rc, hit):
    """The single verdict rule (U68; E7-4; E7-31).  Returns "MATCH", "NOT_REACHED_AS_EXPECTED" or "MISMATCH"."""
    if expected == "INVALID_NOT_REACHED":
        if cls == "INVALID" and hit == 0 and rc is not None:
            return "NOT_REACHED_AS_EXPECTED"
        return "MISMATCH"
    return "MATCH" if cls == expected else "MISMATCH"


def table_raw(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            rows.append(line.split("\t"))
    return rows


def table_dict(path):
    header, rows = None, []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            rows.append(dict(zip(header, f)))
    return rows


def under_ev(ev, path):
    """Refuses any output path that is not inside the evidence directory (AGENTS 3; cont5 0)."""
    ap = os.path.abspath(path)
    if not ap.startswith(os.path.abspath(ev) + os.sep):
        raise SystemExit("REFUSED: output path outside EVDIR: %s" % path)
    return ap


def load_seam_drivers(ev):
    """{(name, tree): (lib_sha, drv_sha, drv_path, lib_path)} from DRIVERS_R7_SEAM.tsv (link_seam_drivers_r7.sh)."""
    out = {}
    for r in table_raw(os.path.join(ev, SEAM_DRIVERS)):
        name, tree, lib_sha, drv_sha, lib_path = r[0], r[1], r[2], r[3], r[4]
        out[(name, tree)] = (lib_sha, drv_sha, os.path.join(ev, "drivers_r7", "seam-%s" % name, "driver"), lib_path)
    return out


def seam_driver_name(request, tree):
    """library_for (run_r4_matrix.py:55-70) for the F and F2 rows of G2a and CTRL_SEAM: fmmret -> fmmret-<tree>, else seamF-<tree>."""
    if request.startswith("fmmret:"):
        return "fmmret-%s" % tree
    return "seamF-%s" % tree


def check_driver(path, sha):
    if not os.path.isfile(path) or M.sha256_file(path) != sha:
        raise SystemExit("REFUSED: driver sha256 differs from the record: %s" % path)


def driver_for(group, request, tree, rec, seam):
    """(path, expected sha256) of the driver for one point."""
    if group in ("CTRL_SEAM", "G2a"):
        name = seam_driver_name(request, tree)
        if (name, tree) not in seam:
            raise SystemExit("REFUSED: no seam driver %s for tree %s" % (name, tree))
        _lib, drv_sha, drv_path, _lp = seam[(name, tree)]
        return drv_path, drv_sha
    fam = "d003" if group == "G1" else "d003plan"
    key = (fam, tree, "plain")
    if key not in rec:
        raise SystemExit("REFUSED: no recorded driver %s" % (key,))
    _lib, drv_sha, drv_path = rec[key]
    drv = drv_path if os.path.isabs(drv_path) else os.path.join(REPO, drv_path)
    return drv, drv_sha


def ctrl_seam_points(ev):
    """CTRL_SEAM rows from the U65(b) pre-registration.  Each row: point id, driver name, tree, mode, NG, request, expected."""
    out = []
    for r in table_dict(os.path.join(ev, CTRL_SEAM_REG)):
        if not r.get("point_id", "").startswith("CTRL-SEAM-"):
            continue
        out.append({"point_id": r["point_id"], "driver": r["driver"], "tree": r["tree"], "mode": r["mode"],
                    "ng": r["NG"], "request": r["request"], "inj_call": "-", "expected": r["expected_class"],
                    "twice": False, "control": True})
    return out


def history_case(group, point_id, twice):
    """The case name the historical runners gave a point (U71a; E7-32).
    G1 (run_r3_sweep.py:118) and G2c (run_r4_regress.py:79): "t4/" for the twice route, "r3/" for the once route.
    G2a (run_r4_matrix.py:101): the point id itself, no prefix."""
    if group == "G2a":
        return point_id
    return ("t4/" if twice else "r3/") + point_id


def build_row(group, point, nth):
    """The row that matrix_r2.build_env reads (U71a).  nth comes from the ADD table ("-" for G2a, run_r4_matrix.py:102)."""
    return {"case": history_case(group, point["point_id"], point["twice"]), "request": point["request"], "nth": nth,
            "mode": point["mode"], "ng": point["ng"]}


def g_points():
    """{group: [point dict]} for G1, G2c, G2a: v2 joined to ADD.  Each point carries the ADD nth and its build_env row."""
    out = {g: [] for g in ("G2c", "G1", "G2a", NOT_RUN_GROUP)}
    for r, a in M.join_points():
        g = r["group"]
        if g not in out:
            continue
        s = M.point_spec(r, a)
        nth = a["nth"] if a is not None else "-"
        p = {"point_id": r["point_id"], "group": g, "tree": r["tree"], "mode": s["mode"], "request": s["request"],
             "inj_call": s["inj_call"], "ng": s["ng"], "twice": s["twice"], "control": s["control"],
             "expected": r["expected_class"], "nth": nth}
        p["row"] = build_row(g, p, nth)
        out[g].append(p)
    return out


def point_env(point):
    """The environment of one point: matrix_r2.build_env(row) for G1, G2c, G2a (U71a).  CTRL_SEAM keeps its registered env
    (no NTH needed: control, no injection)."""
    return M.clean_env(MR.build_env(point["row"]))


def dry_run(ev):
    """Checks (cont6 2.6, ADD1 2): modes, driver and library sha256, output path, expected labels, parse counts."""
    rec = M.drivers_recorded()
    seam = load_seam_drivers(ev)
    checked = 0
    for key, (lib_sha, drv_sha, drv_path, lib_path) in seam.items():
        check_driver(drv_path, drv_sha)
        if M.sha256_file(lib_path) != lib_sha:
            raise SystemExit("REFUSED: seam library sha256 differs from DRIVERS_R7_SEAM for %s" % (key,))
        checked += 2
    for key, (_lib, drv_sha, drv_path) in rec.items():
        if key[0] in ("d003", "d003plan") and key[2] == "plain":
            drv = drv_path if os.path.isabs(drv_path) else os.path.join(REPO, drv_path)
            check_driver(drv, drv_sha)
            checked += 1
    pts = {"CTRL_SEAM": ctrl_seam_points(ev)}
    pts.update(g_points())
    lines = ["# DRYRUN_R7_M2b_run5b (cont6, ADD1).  No S4 run.  Driver sha256 and library sha256 checked; modes, expectations, outputs checked."]
    unparse = 0
    label_counts = {}
    nth_rows = {}
    examples = {}
    for g in GROUP_ORDER:
        rows = pts[g]
        ok = 0
        for p in rows:
            try:
                if p["mode"] not in DRIVER_MODES and not p["control"]:
                    raise ValueError("mode %r not accepted by the driver" % p["mode"])
                if p["control"] and p["mode"] not in DRIVER_MODES:
                    raise ValueError("control mode %r not accepted by the driver" % p["mode"])
                if p["expected"] not in EXPECTED_OK:
                    raise ValueError("expected label %r not in judge CLASSES nor INVALID_NOT_REACHED" % p["expected"])
                if g == "G1" and not p["control"]:
                    M.category_of(p["point_id"])
                if not p["control"] and p["request"] in ("", "-"):
                    raise ValueError("no request")
                if not p["control"] and p["inj_call"] not in ("1", "2"):
                    raise ValueError("inj_call %r" % p["inj_call"])
                if p["ng"] != "9":
                    raise ValueError("ng %r (expected 9)" % p["ng"])
                if g != "CTRL_SEAM":
                    # U71(a): the environment is matrix_r2.build_env(row) and must match the ADD nth and route
                    env = point_env(p)
                    nth = p["nth"]
                    if nth not in ("-", "") and int(nth) > 1:
                        nth_rows[g] = nth_rows.get(g, 0) + 1
                        if env.get("S4FMM_NTH") != nth:
                            raise ValueError("env S4FMM_NTH %r != ADD nth %r" % (env.get("S4FMM_NTH"), nth))
                    if p["twice"] and env.get("S4FMM_TWICE") != "slab":
                        raise ValueError("twice row lacks S4FMM_TWICE=slab")
                    if not p["twice"] and "S4FMM_TWICE" in env:
                        raise ValueError("once row carries S4FMM_TWICE")
                    if g in ("G1", "G2c") and env.get("S4FMM_NTH") is None and nth not in ("-", ""):
                        raise ValueError("G1/G2c row lacks S4FMM_NTH while ADD nth is %r" % nth)
                    examples.setdefault(g, "FMM_MODE=%s S4FMM_NG=%s S4FMM_INJECT=%s S4FMM_NTH=%s S4FMM_TWICE=%s case=%s" % (
                        env.get("FMM_MODE"), env.get("S4FMM_NG"), env.get("S4FMM_INJECT", "-"),
                        env.get("S4FMM_NTH", "-"), env.get("S4FMM_TWICE", "-"), p["row"]["case"]))
                label_counts[p["expected"]] = label_counts.get(p["expected"], 0) + 1
                ok += 1
            except Exception as exc:  # noqa: BLE001  (reported and counted)
                unparse += 1
                lines.append("UNPARSEABLE\t%s\t%s\t%s" % (g, p["point_id"], exc))
        lines.append("# group=%s rows=%d parseable=%d" % (g, len(rows), ok))
    lines.append("# group=%s rows=%d status=EXCLUDED_U65 (not counted as unparseable)"
                 % (NOT_RUN_GROUP, len([r for r, a in M.join_points() if r["group"] == NOT_RUN_GROUP])))
    lines.append("# expected label counts: %s" % ", ".join("%s=%d" % (k, label_counts[k]) for k in sorted(label_counts)))
    lines.append("# rows with nth > 1 (ADD nth): %s" % (", ".join("%s=%d" % (g, nth_rows[g]) for g in sorted(nth_rows)) or "none"))
    for g in GROUP_ORDER:
        if g in examples:
            lines.append("# example environment %s: %s" % (g, examples[g]))
    lines.append("# expected nth > 1 counts (cont7 brief, not yet verified before this run): G1 210, G2c 16")
    lines.append("# driver/library sha256 checked: %d" % checked)
    lines.append("# total unparseable: %d" % unparse)
    return "\n".join(lines) + "\n", unparse


def run_group(ev, group, tag, rec, seam, pts):
    """Run one group, two passes, both trees.  Returns {pass: [row lists]} with row = COLS order."""
    results = {}
    for pas in ("1", "2"):
        out = under_ev(ev, os.path.join(ev, "RESULTS_R7_%s_pass%s_%s.tsv" % (group, pas, tag)))
        if os.path.exists(out):
            raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out)
        res = []
        for p in pts:
            drv, drv_sha = driver_for(group, p["request"], p["tree"], rec, seam)
            check_driver(drv, drv_sha)
            if group == "CTRL_SEAM":
                # registered control environment (no injection, so no NTH): FMM_MODE and NG only
                env = M.clean_env({"FMM_MODE": p["mode"], "S4FMM_NG": p["ng"]})
            else:
                env = point_env(p)  # matrix_r2.build_env(row) (U71a)
            rc, txt = M.run([drv] + M.GRID, env)
            f = M.facts(txt)
            if p["control"]:
                cls, _label, reason = J.classify(rc, f["rc1"], f["rc2"], f["hit"], control=True, real=True, inj_call=1)
                inj = "-"
            else:
                real = M.real_of(group, p["point_id"])
                cls, _label, reason = J.classify(rc, f["rc1"], f["rc2"], f["hit"], control=False, real=real,
                                                 inj_call=int(p["inj_call"]))
                inj = p["inj_call"]
            verdict = verdict_of(p["expected"], cls, rc, f["hit"])
            res.append([p["point_id"], group, p["tree"], p["mode"], p["request"], inj, p["expected"], cls, verdict,
                        str(rc), str(f["rc1"]), str(f["rc2"]), str(f["hit"]), reason])
        with open(out, "w", encoding="utf-8") as fh:
            fh.write("# %s -- P05-S4 R7 M2b %s pass %s %s.  Judge: judge_d003.classify (imported); verdict: verdict_of (U68).\n"
                     % (os.path.basename(out), group, pas, tag))
            fh.write("\t".join(COLS) + "\n")
            for row in res:
                fh.write("\t".join(row) + "\n")
        results[pas] = res
    return results


def pass_and_tree_checks(per_pass):
    """Per-point checks for one group (U66): pass 1 against pass 2 (FLAKY), and F against F2 (five fields)."""
    flaky = []
    by_key = {"1": {}, "2": {}}
    for pas in ("1", "2"):
        for row in per_pass[pas]:
            by_key[pas][(row[0], row[2])] = row
    for key in by_key["1"]:
        a, b = by_key["1"][key], by_key["2"].get(key)
        if b is None:
            flaky.append((key, "ABSENT_PASS2"))
            continue
        if [a[7], a[8], a[9], a[10], a[11], a[12]] != [b[7], b[8], b[9], b[10], b[11], b[12]]:
            flaky.append((key, "FLAKY"))
    tree_unequal = []
    pass1 = per_pass["1"]
    pairs = {}
    for row in pass1:
        pairs.setdefault(base_id(row[0], row[2]), {})[row[2]] = row
    for base, d in pairs.items():
        if "F" in d and "F2" in d:
            f, f2 = d["F"], d["F2"]
            if [f[7], f[9], f[10], f[11], f[12]] != [f2[7], f2[9], f2[10], f2[11], f2[12]]:
                tree_unequal.append(base)
    return flaky, tree_unequal


def summarize(ev, tag, per_group, regress_out, summary_out, stopped):
    """Write REGRESS_R7_M2b.tsv and M2B_SUMMARY_R7.txt (counts; non-MATCH rows listed up to NONMATCH_LIST_MAX)."""
    lines = ["# REGRESS_R7_M2b.tsv -- P05-S4 R7 M2b summary (run %s).  Counts only.  verdict via verdict_of (U68)." % tag,
             "group\tpass\trows\tMATCH\tNOT_REACHED_AS_EXPECTED\tMISMATCH\tFLAKY_points\tF_vs_F2_unequal_points\tstatus"]
    nonmatch = []
    for g in GROUP_ORDER:
        if g not in per_group:
            lines.append("%s\t-\t-\t-\t-\t-\t-\t-\tNOT_RUN" % g)
            continue
        flaky, tree_uneq = per_group[g]["checks"]
        for pas in ("1", "2"):
            res = per_group[g]["passes"][pas]
            m = sum(1 for r in res if r[8] == "MATCH")
            nr = sum(1 for r in res if r[8] == "NOT_REACHED_AS_EXPECTED")
            mm = sum(1 for r in res if r[8] == "MISMATCH")
            for r in res:
                if r[8] == "MISMATCH":
                    nonmatch.append([g, pas] + r)
            status = "STOP" if g == stopped else ("OK" if mm == 0 and not flaky and not tree_uneq else "CHECK")
            lines.append("%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%s" % (g, pas, len(res), m, nr, mm, len(flaky), len(tree_uneq), status))
    lines.append("# verdicts: MATCH and NOT_REACHED_AS_EXPECTED are both not-stop; MISMATCH and FLAKY stop the run (U67, U68).")
    sum_lines = ["# M2B_SUMMARY_R7 -- run %s.  Counts; MISMATCH rows listed up to %d; overflow in NONMATCH_OVERFLOW_R7_M2b.tsv."
                 % (tag, NONMATCH_LIST_MAX),
                 "total MISMATCH rows: %d" % len(nonmatch),
                 "stopped after group: %s" % (stopped or "none")]
    for row in nonmatch[:NONMATCH_LIST_MAX]:
        sum_lines.append("MISMATCH\t" + "\t".join(row))
    if len(nonmatch) > NONMATCH_LIST_MAX:
        over = under_ev(ev, os.path.join(ev, "NONMATCH_OVERFLOW_R7_M2b_%s.tsv" % tag))
        if os.path.exists(over):
            raise SystemExit("REFUSED: exists (U17): %s" % over)
        with open(over, "w", encoding="utf-8") as fh:
            fh.write("\n".join("\t".join(r) for r in nonmatch[NONMATCH_LIST_MAX:]) + "\n")
    with open(regress_out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    with open(summary_out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(sum_lines) + "\n")
    print("summary -> %s" % summary_out)


def run_all(ev, tag):
    if not tag.startswith("run") or not tag[3:].isdigit():
        raise SystemExit("REFUSED: run label must be run<N>")
    # the summary files carry the run label (cont7): run5 files (void, HARNESS_INVALID) are kept and never overwritten (U17)
    regress_out = under_ev(ev, os.path.join(ev, "REGRESS_R7_M2b_%s.tsv" % tag))
    summary_out = under_ev(ev, os.path.join(ev, "M2B_SUMMARY_R7_%s.txt" % tag))
    for p in (regress_out, summary_out):
        if os.path.exists(p):
            raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % p)
    rec = M.drivers_recorded()
    seam = load_seam_drivers(ev)
    pts = {"CTRL_SEAM": ctrl_seam_points(ev)}
    pts.update(g_points())
    per_group = {}
    stopped = None
    for g in GROUP_ORDER:
        passes = run_group(ev, g, tag, rec, seam, pts[g])
        flaky, tree_uneq = pass_and_tree_checks(passes)
        per_group[g] = {"passes": passes, "checks": (flaky, tree_uneq)}
        mm = sum(1 for pas in passes for r in passes[pas] if r[8] == "MISMATCH")
        if mm or flaky:
            stopped = g
            break
    summarize(ev, tag, per_group, regress_out, summary_out, stopped)
    if stopped is not None:
        print("STOPPED after group %s (MISMATCH or FLAKY); later groups not run (U67, U68)" % stopped)
        return 1
    return 0


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    mode, ev = argv[1], argv[2]
    if not os.path.isabs(ev):
        ev = os.path.join(REPO, ev)
    if mode == "dry-run":
        if len(argv) != 4:
            raise SystemExit("usage: run_m2b_all_r7.py dry-run EVDIR OUT.txt")
        out = under_ev(ev, argv[3] if os.path.isabs(argv[3]) else os.path.join(ev, argv[3]))
        if os.path.exists(out):
            raise SystemExit("REFUSED: exists (U17): %s" % out)
        text, unparse = dry_run(ev)
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("dry-run unparseable=%d -> %s" % (unparse, out))
        return 0 if unparse == 0 else 1
    if mode == "run":
        if len(argv) != 4:
            raise SystemExit("usage: run_m2b_all_r7.py run EVDIR RUNTAG")
        return run_all(ev, argv[3])
    raise SystemExit(__doc__)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
