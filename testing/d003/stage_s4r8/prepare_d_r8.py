#!/usr/bin/env python3
"""P05-S4 R8 M0 step 4 (U113, U119, U124, U125): preparation of the D smoke test.  New file.

Run through safe_run (python3 -I -B).  Read only, except for three new output files in $EV:
  DRIVER_MAP_R8_D.tsv   (U124: point, registered tree, registered driver family, actual driver, actual path, driver sha256)
  EXPECT_R8_D.txt       (U125: the 8 expected rows, copied from REGISTRY_S3R4C3_D.tsv, with its sha256)
  D_PREPARE_CHECK_R8.tsv (one row per point: every assertion of section 4, PASS or FAIL)
Nothing here runs a driver.  If any assertion fails the script exits 1 and run_d_r8.py must not be started.
"""
import hashlib
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
R7_STAGE = os.path.join(REPO, "testing", "d003", "stage_s4r7")
D_REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c3", "REGISTRY_S3R4C3_D.tsv")
D_REG_SHA = "a251a3b856f7772a09ce587918125f3b91d525cacc16db238e6787312353a9d5"
CTRL_REG = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7", "REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv")
DRV_R7 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7", "DRIVERS_R7.tsv")
DRV_SEAM_R8 = os.path.join(EV, "DRIVERS_R8.tsv")
LIB_SEAM = os.path.join(EV, "build_r8", "seam_plain")
F3_PLAIN = os.path.join(EV, "build_r8", "F3-plain", "build", "libS4.a")
FMMRET_LIB = os.path.join(LIB_SEAM, "fmmret-F3-plain", "build", "libS4.a")
SEAMF_LIB = os.path.join(LIB_SEAM, "seamF-F3-plain", "build", "libS4.a")

sys.path.insert(0, R7_STAGE)
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import run_m2b_all_r7 as B  # noqa: E402  imported, not modified (g_points, point_env, ctrl_seam_points, verdict_of)
import run_m2_r7 as M  # noqa: E402  imported, not modified (run, facts, clean_env, GRID, real_of, sha256_file)
import expected_env_independent_r7 as EX  # noqa: E402  imported, not modified (history rule for the environment)

D_ORDER = [
    ("CTRL_SEAM", "CTRL-SEAM-fmmret-F"),
    ("CTRL_SEAM", "CTRL-SEAM-seamF-F2"),
    ("G2c", "M-once-fft-exec-1-F"),
    ("G2c", "M-twice-vl-plan-1-F2"),
    ("G1", "CTL-closed1d-F"),
    ("G1", "M-twice-vl-plan-1-F2"),
    ("G2a", "R4-ACF1-F-F"),
    ("G2a", "R4-SI02-F-F2"),
]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


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


def drivers_r8():
    """{(name, tree, mode): (lib_sha, drv_sha, lib_path, driver_path)} from DRIVERS_R8.tsv (link_drivers_r8.sh)."""
    out = {}
    with open(DRV_SEAM_R8, encoding="utf-8") as fh:
        next(fh)
        for raw in fh:
            f = raw.rstrip("\n").split("\t")
            if len(f) < 7:
                continue
            name, tree, mode, lib_sha, drv_sha, lib_path, drv_path = f[:7]
            out[name] = (lib_sha, drv_sha, lib_path, drv_path, tree, mode)
    return out


def family_of(group, point_id, request, ctrl_driver):
    """U124: the registered driver family of a point."""
    if group == "CTRL_SEAM":
        # family = the driver column of the CTRL_SEAM registration, reduced to its family name
        return "fmmret" if ctrl_driver.startswith("fmmret") else "seamF"
    if group == "G2a":
        return "fmmret" if request.startswith("fmmret:") else "seamF"
    if group == "G1":
        return "d003"
    if group == "G2c":
        return "d003plan"
    raise ValueError("no family rule for group %s" % group)


ACTUAL_DRIVER = {"fmmret": "seam-fmmret-F3", "seamF": "seam-seamF-F3", "d003": "d003-F3-plain",
                 "d003plan": "d003plan-F3-plain"}


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: prepare_d_r8.py  (no arguments; outputs are fixed names in EV)")
    for name in ("DRIVER_MAP_R8_D.tsv", "EXPECT_R8_D.txt", "D_PREPARE_CHECK_R8.tsv"):
        if os.path.exists(os.path.join(EV, name)):
            raise SystemExit("REFUSED: exists (U17): %s" % name)
    if sha(D_REG) != D_REG_SHA:
        raise SystemExit("REFUSED: REGISTRY_S3R4C3_D.tsv sha256 differs")
    for p in (F3_PLAIN, FMMRET_LIB, SEAMF_LIB, DRV_SEAM_R8, DRV_R7, CTRL_REG):
        if not os.path.isfile(p):
            raise SystemExit("REFUSED: input missing: %s" % p)

    reg = {}
    for r in table(D_REG):
        reg[(r["group"], r["point_id"])] = r
    ctrl = {r["point_id"]: r for r in table(CTRL_REG) if r["point_id"].startswith("CTRL-SEAM-")}
    drv = drivers_r8()

    # g_points(): v2 joined to ADD (G1, G2c, G2a); keyed by (point_id, group) for the eight D points
    pts = B.g_points()
    by_key = {}
    for g in ("G1", "G2c", "G2a"):
        for p in pts[g]:
            by_key[(g, p["point_id"])] = p

    checks = []   # (point, check, expected, actual, PASS/FAIL)
    map_rows = []
    expect_rows = []
    fails = 0

    def chk(point, what, want, got):
        nonlocal fails
        ok = (want == got)
        if not ok:
            fails += 1
        checks.append((point, what, str(want), str(got), "PASS" if ok else "FAIL"))
        return ok

    for group, pid in D_ORDER:
        point = "%s/%s" % (group, pid)
        r = reg.get((group, pid))
        if r is None:
            chk(point, "present in REGISTRY_S3R4C3_D.tsv", "present", "absent")
            continue
        exp_class, exp_rc1 = r["expected_class"], r["expected_rc1"]
        expect_rows.append((pid, group, exp_class, exp_rc1, r["tree"], r["mode"], r["request"], r["inj_call"]))
        if group == "CTRL_SEAM":
            c = ctrl.get(pid)
            chk(point, "present in CTRL_SEAM registration", "present", "present" if c else "absent")
            if c is None:
                continue
            # U124: the family comes from the driver column of the CTRL_SEAM registration (fmmret-F -> fmmret, seamF-F2 -> seamF)
            fam = family_of(group, pid, "none", c["driver"])
            chk(point, "registered driver column (CTRL_SEAM) is a family name", True, c["driver"] in ("fmmret-F", "fmmret-F2", "seamF-F", "seamF-F2"))
            chk(point, "registered tree of CTRL_SEAM row = D registration", r["tree"], c["tree"])
            chk(point, "registered expected class = D registration", c["expected_class"], exp_class)
            env = M.clean_env({"FMM_MODE": r["mode"], "S4FMM_NG": "9"})
            want_env = EX.expected_env_from_history("CTRL_SEAM", pid, r["tree"], mode=r["mode"])
            got_env = {k: env[k] for k in env if k.startswith("FMM_") or k.startswith("S4FMM_")}
            chk(point, "environment = history expectation (FMM_MODE, S4FMM_NG only)", want_env, got_env)
            chk(point, "control: no injection variables", False,
                any(k in got_env for k in ("S4FMM_INJECT", "S4FMM_NTH", "S4FMM_TWICE")))
        else:
            p = by_key.get((group, pid))
            chk(point, "present in v2 joined to ADD", "present", "present" if p else "absent")
            if p is None:
                continue
            chk(point, "expected class: v2 (joined) = REGISTRY_S3R4C3_D.tsv", exp_class, p["expected"])
            fam = family_of(group, pid, p["request"], "")
            chk(point, "request in D registration = joined request", r["request"], p["request"])
            chk(point, "inj_call in D registration = joined inj_call", r["inj_call"], p["inj_call"])
            chk(point, "tree in D registration = joined tree", r["tree"], p["tree"])
            env = B.point_env(p)
            want_env = EX.expected_env_from_history(group, pid, p["tree"], mode=p["mode"])
            got_env = {k: env[k] for k in env if k.startswith("FMM_") or k.startswith("S4FMM_")}
            chk(point, "environment = history expectation (independent rule)", want_env, got_env)
        # U124: the actual driver is the F3 plain driver of the registered family (ACTUAL_DRIVER, from the family)
        actual = ACTUAL_DRIVER[fam]
        if actual not in drv:
            chk(point, "actual driver recorded in DRIVERS_R8.tsv", "present", "absent")
            continue
        lib_sha, drv_sha, lib_path, drv_path, dtree, dmode = drv[actual]
        chk(point, "actual tree of the driver = F3 (DRIVERS_R8.tsv)", "F3", dtree)
        chk(point, "actual mode of the driver is a plain build", True, dmode.endswith("plain"))
        want_lib = {"d003": F3_PLAIN, "d003plan": F3_PLAIN, "fmmret": FMMRET_LIB, "seamF": SEAMF_LIB}[fam]
        chk(point, "driver library path = the F3 plain library of its family (DRIVERS_R8.tsv)", want_lib, lib_path)
        chk(point, "driver sha256 = recorded (DRIVERS_R8.tsv)", drv_sha, sha(drv_path) if os.path.isfile(drv_path) else "missing")
        map_rows.append((pid, group, r["tree"], fam, actual, drv_path, drv_sha))

    ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if fails:
        out = os.path.join(EV, "D_PREPARE_CHECK_R8.tsv")
        with open(out, "x", encoding="utf-8") as fh:
            fh.write("# D_PREPARE_CHECK_R8.tsv -- prepare_d_r8.py at %s; FAILS=%d; no driver run; run_d_r8.py must not start.\n" % (ts, fails))
            fh.write("point\tcheck\texpected\tactual\tresult\n")
            for row in checks:
                fh.write("\t".join(row) + "\n")
        print("prepare_d_r8: FAILS=%d -> D_PREPARE_CHECK_R8.tsv (no DRIVER_MAP or EXPECT written)" % fails)
        return 1

    dm = os.path.join(EV, "DRIVER_MAP_R8_D.tsv")
    with open(dm, "x", encoding="utf-8") as fh:
        fh.write("# DRIVER_MAP_R8_D.tsv -- U124 driver map for the D smoke test, written %s.  Actual tree F3 for every point.\n" % ts)
        fh.write("point_id\tgroup\tregistered_tree\tregistered_driver_family\tactual_driver\tactual_driver_path\tdriver_sha256\n")
        for row in map_rows:
            fh.write("\t".join((row[0], row[1], row[2], row[3], row[4], row[5], row[6])) + "\n")
    ex = os.path.join(EV, "EXPECT_R8_D.txt")
    with open(ex, "x", encoding="utf-8") as fh:
        fh.write("# EXPECT_R8_D.txt -- U125 expected classes, copied from REGISTRY_S3R4C3_D.tsv (sha256 %s), written %s. Status INFLUENCED.\n" % (D_REG_SHA, ts))
        fh.write("point_id\tgroup\texpected_class\texpected_rc1\ttree\tmode\trequest\tinj_call\n")
        for row in expect_rows:
            fh.write("\t".join(row) + "\n")
    with open(os.path.join(EV, "D_PREPARE_CHECK_R8.tsv"), "x", encoding="utf-8") as fh:
        fh.write("# D_PREPARE_CHECK_R8.tsv -- prepare_d_r8.py at %s; FAILS=0; no driver run.\n" % ts)
        fh.write("point\tcheck\texpected\tactual\tresult\n")
        for row in checks:
            fh.write("\t".join(row) + "\n")
    print("prepare_d_r8: FAILS=0 -> DRIVER_MAP_R8_D.tsv, EXPECT_R8_D.txt, D_PREPARE_CHECK_R8.tsv")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
