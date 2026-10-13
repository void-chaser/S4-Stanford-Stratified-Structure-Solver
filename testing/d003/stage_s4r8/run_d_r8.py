#!/usr/bin/env python3
"""P05-S4 R8 M0 step 4 (U113, U119, U124, U125): D smoke test, eight points, two passes.  New file.

Run through safe_run (python3 -I -B), after prepare_d_r8.py has written DRIVER_MAP_R8_D.tsv and EXPECT_R8_D.txt with
FAILS=0 (D_PREPARE_CHECK_R8.tsv).  Usage:
  python3 -I -B testing/d003/stage_s4r8/run_d_r8.py PASS        (PASS = 1 or 2)

Imported, not modified: run_m2b_all_r7 (g_points, point_env, verdict_of), run_m2_r7 (run, facts, clean_env, GRID,
real_of, sha256_file), judge_d003 (classify), expected_env_independent_r7 (expected_env_from_history).
Not called: run_group, driver_for, dry_run, seam_driver_name, and the DRIVERS path of run_m2_r7.
The driver of every point comes only from DRIVER_MAP_R8_D.tsv.  The judge reads facts only (rc, rc1, rc2, signal, hit);
the driver's own PASS/FAIL line is not read.
Output (new, refused if it exists, U17): $EV/RESULTS_R8_D_pass<PASS>.tsv; $EV/D_SUMMARY_R8.txt is written after pass 2.
"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
R7_STAGE = os.path.join(REPO, "testing", "d003", "stage_s4r7")
sys.path.insert(0, R7_STAGE)
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import run_m2b_all_r7 as B  # noqa: E402  imported, not modified
import run_m2_r7 as M  # noqa: E402  imported, not modified
import judge_d003 as J  # noqa: E402  imported, not modified
import expected_env_independent_r7 as EX  # noqa: E402  imported, not modified

COLS = ["point_id", "group", "registered_tree", "actual_tree", "driver", "driver_sha256", "expected_class", "class",
        "verdict", "rc", "rc1", "rc2", "hit", "reason", "registered_driver_family", "actual_driver_path", "lib_sha256"]
RUN_PASS = ("1", "2")


def table(path):
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


def load_map():
    return table(os.path.join(EV, "DRIVER_MAP_R8_D.tsv"))


def load_expect():
    return table(os.path.join(EV, "EXPECT_R8_D.txt"))


def main(argv):
    if len(argv) != 2 or argv[1] not in RUN_PASS:
        raise SystemExit("usage: run_d_r8.py 1|2")
    pas = argv[1]
    out = os.path.join(EV, "RESULTS_R8_D_pass%s.tsv" % pas)
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out)
    dmap = {r["point_id"] + "|" + r["group"]: r for r in load_map()}
    expect = {r["point_id"] + "|" + r["group"]: r for r in load_expect()}
    if len(dmap) != 8 or set(dmap) != set(expect):
        raise SystemExit("REFUSED: DRIVER_MAP and EXPECT do not hold the same eight points")
    # U124: the driver file is checked against the recorded sha256 before every run; the driver must lie in this
    # round's evidence; its library and tree are those recorded in DRIVERS_R8.tsv (tree F3)
    drivers = {}
    for r in table(os.path.join(EV, "DRIVERS_R8.tsv")):
        drivers[r["driver"]] = r
    for key, r in dmap.items():
        path = r["actual_driver_path"]
        if "checkpoints/p05/evidence/p05-s4r8/" not in path:
            raise SystemExit("REFUSED: driver outside the round evidence: %s" % key)
        if not os.path.isfile(path) or M.sha256_file(path) != r["driver_sha256"]:
            raise SystemExit("REFUSED: driver sha256 differs from DRIVER_MAP: %s" % key)
        d = drivers.get(r["actual_driver"])
        if d is None or d["tree"] != "F3":
            raise SystemExit("REFUSED: driver %s is not recorded as tree F3 in DRIVERS_R8.tsv" % r["actual_driver"])
        r["lib_sha256"] = d["lib_sha256"]

    ctrl_ids = {p["point_id"] for p in B.ctrl_seam_points(os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7"))}
    pts = B.g_points()
    by_key = {}
    for g in ("G1", "G2c", "G2a"):
        for p in pts[g]:
            by_key[(g, p["point_id"])] = p

    rows = []
    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for key in sorted(dmap):
        r = dmap[key]
        pid, group = r["point_id"], r["group"]
        ex = expect[key]
        exp_class, exp_rc1 = ex["expected_class"], ex["expected_rc1"]
        if group == "CTRL_SEAM":
            if pid not in ctrl_ids:
                raise SystemExit("REFUSED: %s is not a CTRL_SEAM point" % pid)
            env = M.clean_env({"FMM_MODE": ex["mode"], "S4FMM_NG": "9"})
            control = True
        else:
            p = by_key.get((group, pid))
            if p is None:
                raise SystemExit("REFUSED: %s not in g_points()" % key)
            env = B.point_env(p)
            control = p["control"]
        # environment check (U75b): the history expectation must equal the environment that will be passed
        want = EX.expected_env_from_history(group, pid, ex["tree"], mode=ex["mode"])
        got = {k: env[k] for k in env if k.startswith("FMM_") or k.startswith("S4FMM_")}
        if got != want:
            raise SystemExit("REFUSED: environment of %s differs from the history expectation: %r != %r" % (key, got, want))
        rc, txt = M.run([r["actual_driver_path"]] + M.GRID, env)
        f = M.facts(txt)
        if control:
            cls, _label, reason = J.classify(rc, f["rc1"], f["rc2"], f["hit"], control=True, real=True, inj_call=1)
        else:
            real = M.real_of(group, pid)
            cls, _label, reason = J.classify(rc, f["rc1"], f["rc2"], f["hit"], control=False, real=real,
                                             inj_call=int(ex["inj_call"]))
        verdict = B.verdict_of(exp_class, cls, rc, f["hit"])
        actual_tree = drivers[r["actual_driver"]]["tree"]
        rows.append([pid, group, ex["tree"], actual_tree, r["actual_driver"], r["driver_sha256"], exp_class, cls, verdict,
                     str(rc), str(f["rc1"]), str(f["rc2"]), str(f["hit"]), reason, r["registered_driver_family"],
                     r["actual_driver_path"], r["lib_sha256"]])
    with open(out, "x", encoding="utf-8") as fh:
        fh.write("# RESULTS_R8_D_pass%s.tsv -- P05-S4 R8 M0 D smoke, pass %s, utc %s.  Judge: judge_d003.classify (imported); verdict: verdict_of (U68).\n"
                 % (pas, pas, ts))
        fh.write("\t".join(COLS) + "\n")
        for row in rows:
            fh.write("\t".join(row) + "\n")
    m = sum(1 for x in rows if x[8] == "MATCH")
    mm = sum(1 for x in rows if x[8] == "MISMATCH")
    print("run_d_r8 pass %s: MATCH=%d MISMATCH=%d -> %s" % (pas, m, mm, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
