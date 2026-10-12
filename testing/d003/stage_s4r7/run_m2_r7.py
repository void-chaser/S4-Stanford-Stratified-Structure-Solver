#!/usr/bin/env python3
"""P05-S4 R7 M2 runner (cont3, new file).  Runs the M2 registered points on the R7 build of F and F2.

Usage (through safe_run; every output file must not exist):
  python3 -I -B testing/d003/stage_s4r7/run_m2_r7.py dry-parse EVDIR           (no S4 run; writes nothing but the printed report)
  python3 -I -B testing/d003/stage_s4r7/run_m2_r7.py run EVDIR GROUP PASS RUN  (GROUP in G2b,G3,G4,G1,G2a,G2c,G2c-control)

Contract (cont3 section 2.3 and 3):
  - Points come from v2 (REGISTRY_S4_PRE_R7_M2.tsv, sha e4dd2c87...) joined to ADD (REGISTRY_S4_PRE_R7_M2_ADD.tsv) on
    (point_id, tree).  A point that does not join is a refusal (exit non-zero, nothing run).
  - Drivers: DRIVERS_R7.tsv (driver sha256 + library sha256 recorded).  Seam points use the plain seam library and
    the d003plan driver (inject_r4_plan.cpp handles alloc:, fmmret:, linearsolve:, linearsolve_null2:, kottke_alloc:;
    verified in cont3 by grep).  The driver sha256 is compared with the recorded value before every run.
  - Judgement: judge_d003.classify(rc, rc1, rc2, hit, control, real, inj_call) imported, not modified.
    real = (category != exec) as in run_r3_sweep.py / run_r4_regress.py.  Controls use control=True.
  - facts read from stdout AND stderr (the HIT line is on stderr; DRIVER_REPRO_CHECK_M2.txt).
  - rc is the process exit status (judge input rc).  The driver's own PASS/FAIL is NOT used.
Output: EVDIR/RESULTS_R7_<GROUP>_pass<P>_run4.tsv (never overwritten).
"""
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003 as J  # noqa: E402  (imported, not modified)

EV_REL = "checkpoints/p05/evidence/p05-s4r7"
V2 = os.path.join(REPO, EV_REL, "REGISTRY_S4_PRE_R7_M2.tsv")
ADD = os.path.join(REPO, EV_REL, "REGISTRY_S4_PRE_R7_M2_ADD_v2.tsv")  # inj_call 1 for G2a (matrix_r2.inj_call_of); the earlier ADD file (G2a inj_call "-") is superseded before any run
V2_SHA = "e4dd2c8779887f57044253a7e1674923a0fb34a0c6fcd437459572ae8d92ba2c"
DRIVERS = os.path.join(REPO, EV_REL, "DRIVERS_R7.tsv")
SEAM_RES = os.path.join(REPO, EV_REL, "build_r7", "seam_plain", "BUILD_SEAM_PLAIN_R7_RESULT.tsv")
GRID = ["pattern", "both", "4", "3"]
TIMEOUT_S = 600
GROUPS = ("G2b", "G3", "G4", "G1", "G2a", "G2c", "G2c-control")
RE_RC1 = re.compile(r"^RC first (-?\d+)\s*$", re.M)
RE_RC2 = re.compile(r"^RC retry (-?\d+)\s*$", re.M)
RE_HITC = re.compile(r"^S4FMM HITCOUNT (-?\d+)\s*$", re.M)
RE_HIT = re.compile(r"^S4FMM HIT ", re.M)


def sha256_file(path):
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


def join_points():
    """Join v2 and ADD on (point_id, tree, group).  The group is part of the key because the same point id appears
    in more than one group (e.g. M-once-fft-plan-3-F is in G1 as INVALID_NOT_REACHED and in G2b as REPORTED_FAILURE;
    104 point-id/tree pairs occur in two groups, 0 occur twice within a group).  Refuse on any unmatched point."""
    v2 = table(V2)
    add = {(r["point_id"], r["tree"], r["group"]): r for r in table(ADD)}
    out, missing = [], []
    for r in v2:
        a = add.get((r["point_id"], r["tree"], r["group"]))
        if a is None:
            # the v2 controls of G2c-control and the plancall groups carry no ADD row: they are run with request
            # from v2 itself (see point_request below)
            if r["group"] in ("G2b", "G3", "G4"):
                out.append((r, None))
                continue
            missing.append(r["point_id"] + "/" + r["tree"])
            continue
        if a["expected_class"] != r["expected_class"]:
            raise SystemExit("REFUSED: expected_class differs between v2 and ADD for %s" % r["point_id"])
        out.append((r, a))
    if missing:
        raise SystemExit("REFUSED: %d v2 points have no ADD row, e.g. %s" % (len(missing), missing[:5]))
    return out


def drivers_recorded():
    """Return {(driver, tree, mode): (lib_sha, drv_sha, path)} from DRIVERS_R7.tsv (plain and dbg)."""
    rec = {}
    for r in table_raw(DRIVERS):
        rec[(r[0], r[1], r[2])] = (r[3], r[4], r[5])
    return rec


def table_raw(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if f[0] == "driver":
                continue
            rows.append(f)
    return rows


def clean_env(extra):
    env = {k: v for k, v in os.environ.items() if not (k.startswith("FMM_") or k.startswith("S4FMM_"))}
    env.update(extra)
    return env


def run(cmd, env):
    try:
        p = subprocess.run(cmd, env=env, cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=TIMEOUT_S)
        rc, out = p.returncode, p.stdout
    except subprocess.TimeoutExpired as exc:
        rc, out = 124, (exc.stdout or b"")
    if rc is not None and rc < 0:
        rc = 128 - rc
    return rc, out.decode("utf-8", errors="replace")


def facts(text):
    m1, m2 = RE_RC1.search(text), RE_RC2.search(text)
    hc = RE_HITC.search(text)
    hit = int(hc.group(1)) if hc else len(RE_HIT.findall(text))
    return {"rc1": int(m1.group(1)) if m1 else None, "rc2": int(m2.group(1)) if m2 else None, "hit": hit}


CATS = ("malloc", "plan", "exec", "control")


def real_of(group, pid):
    """The judge's 'real' flag, as the historical runner of each group used it (cont3 section 2.3; judge_d003.py:66).

    real only changes the label string ("(boundary simulation)" when False), never the class.
      G1, G2c: real = (category != exec)   (run_r3_sweep.py:87; run_r4_regress.py)  -- category from the point id
      G2a, G2b: real = True                (run_r4_matrix.py:140)
      G3: real = True                      (run_r5_planm.py; all G3 points are plan-class)
      G4: real = True                      (run_r6_twice_slab.py:117)
    Seam (G2a) and control ids carry no category token, so they are not parsed for one (G2a uses real=True).
    """
    if group in ("G2a", "G2b", "G3", "G4"):
        return True
    if group in ("G1", "G2c"):
        return "-exec-" not in pid
    if group == "G2c-control":
        # control rows are judged with control=True, and judge_d003.classify's control branch does not read real
        # (judge_d003.py: the control branch checks hit, rc, rc1 only).  real is set True as a placeholder value.
        return True
    raise ValueError("no real rule for group %s" % group)


def category_of(pid):
    """The category token of a point id (-malloc-, -plan-, -exec-); exactly one must be present (G1/G2b/G3/G4 only)."""
    hits = [c for c in CATS if ("-%s-" % c) in pid]
    if len(hits) != 1:
        raise ValueError("category token not unique in %r: %s" % (pid, hits))
    return hits[0]


def point_spec(r, a):
    """The request, inj_call, twice flag, NG and mode for a point.

    NG: v2 carries "-" for every group, so NG comes from the historical setting, not from v2 (cont3 section 2.3):
    R4 plancall, R5 M=2 and R4 seam/regress rows all ran with NG 9 (run_r4_plancall.py:84, run_r5_san_inject.py:177).
    ADD carries NG for G1 and G2c; a v2-only point (G2b, G3, G4) takes NG 9.
    """
    if a is not None:
        ng = a["ng"] if a["ng"] not in ("", "-") else "9"
        return {"request": a["request"], "inj_call": a["inj_call"], "twice": a["twice_env"] == "slab",
                "ng": ng, "mode": r["mode"], "control": a["request"] == "none"}
    # plancall points (G2b, G3, G4): request and inj_call are carried by v2 itself
    return {"request": r["request"], "inj_call": r["inj_call"], "twice": r["route"] == "twice",
            "ng": "9", "mode": r["mode"], "control": r["request"] == "none"}


def dry_parse(ev):
    rows = join_points()
    rec = drivers_recorded()
    by = {}
    unparse = 0
    lines = ["# dry-parse of the M2 registration (no S4 run).  Joins v2 and ADD on (point_id, tree, group); checks request, inj_call, ng and the real rule per group."]
    for r, a in rows:
        g = r["group"]
        by[g] = by.get(g, 0) + 1
        try:
            s = point_spec(r, a)
            real_of(g, r["point_id"])           # every group must have a real rule, else ValueError
            if g in ("G1", "G2b", "G3", "G4") and not s["control"]:
                category_of(r["point_id"])      # these ids carry exactly one category token
            if not s["control"] and s["request"] in ("", "-"):
                raise ValueError("no request")
            if not s["control"] and s["inj_call"] not in ("1", "2"):
                raise ValueError("inj_call %r" % s["inj_call"])
            if s["ng"] not in ("9",):
                raise ValueError("ng %r (expected 9 for M2 groups)" % s["ng"])
        except Exception as exc:  # noqa: BLE001  (reported, counted)
            unparse += 1
            lines.append("UNPARSEABLE\t%s\t%s" % (r["point_id"], exc))
    lines.append("# joined points by group: %s" % ", ".join("%s=%d" % (k, v) for k, v in sorted(by.items())))
    lines.append("# total joined: %d; unparseable: %d" % (len(rows), unparse))
    print("\n".join(lines))
    return 0 if unparse == 0 else 1


def main(argv):
    if len(argv) < 3:
        raise SystemExit(__doc__)
    if argv[1] == "dry-parse":
        return dry_parse(argv[2])
    if argv[1] != "run" or len(argv) != 6:
        raise SystemExit(__doc__)
    ev, group, pas, tag = argv[2], argv[3], argv[4], argv[5]
    if group not in GROUPS:
        raise SystemExit("REFUSED: unknown group %s" % group)
    if pas not in ("1", "2"):
        raise SystemExit("PASS must be 1 or 2")
    if not re.match(r"^run[0-9]+$", tag):
        raise SystemExit("REFUSED: run label must be run<N>")
    out = os.path.join(ev, "RESULTS_R7_%s_pass%s_%s.tsv" % (group, pas, tag))
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out)
    if sha256_file(V2) != V2_SHA:
        raise SystemExit("REFUSED: v2 sha256 differs")
    rec = drivers_recorded()
    rows = [(r, a) for r, a in join_points() if r["group"] == group]
    if not rows:
        raise SystemExit("REFUSED: no points in group %s" % group)

    res = []
    for r, a in rows:
        s = point_spec(r, a)
        tree = r["tree"]
        # driver: plancall/seam groups use the d003plan family (inject_r4_plan.cpp); G1 uses d003 (inject_d003.cpp)
        fam = "d003" if group == "G1" else "d003plan"
        key = (fam, tree, "plain")
        if key not in rec:
            raise SystemExit("REFUSED: no recorded driver %s" % (key,))
        lib_sha, drv_sha, drv_path = rec[key]
        drv = os.path.join(REPO, drv_path) if not os.path.isabs(drv_path) else drv_path
        if not os.path.isfile(drv) or sha256_file(drv) != drv_sha:
            raise SystemExit("REFUSED: driver sha256 differs from DRIVERS_R7: %s" % drv)
        env = {"FMM_MODE": s["mode"], "S4FMM_NG": s["ng"]}
        if s["request"] != "none":
            env["S4FMM_INJECT"] = s["request"]
        if s["twice"]:
            env["S4FMM_TWICE"] = "slab"
        pdir = os.path.join(ev, "m2", group, r["point_id"], "pass%s_%s" % (pas, tag))
        rc, txt = run([drv] + GRID, clean_env(env))
        os.makedirs(pdir, exist_ok=True)
        with open(os.path.join(pdir, "run.out"), "w", encoding="utf-8") as fh:
            fh.write(txt)
        f = facts(txt)
        if s["control"]:
            # judged by judge_d003.classify with control=True (its control branch checks hit, rc, rc1).  The runner does
            # NOT re-implement the rule: a copy would miss the hit != 0 check (found in cont3).  inj_call is a placeholder
            # 1 here: classify requires 1 or 2 on every call (judge_d003.py:64); the control branch does not use it.
            cls, _label, reason = J.classify(rc, f["rc1"], f["rc2"], f["hit"], control=True, real=True, inj_call=1)
            verdict = "MATCH" if cls == r["expected_class"] else "MISMATCH"
        else:
            # real = not an exec point (run_r3_sweep.py / run_r4_regress.py: real=(cat != "exec")); the category is
            # read from the point id, not from the group name (the group name is never "exec")
            real = real_of(group, r["point_id"])
            cls, _label, reason = J.classify(rc, f["rc1"], f["rc2"], f["hit"], control=False, real=real,
                                             inj_call=int(s["inj_call"]))
            verdict = "MATCH" if cls == r["expected_class"] else "MISMATCH"
        res.append([r["point_id"], group, tree, s["mode"], s["request"], s["inj_call"], r["expected_class"], cls, verdict,
                    str(rc), str(f["rc1"]), str(f["rc2"]), str(f["hit"]), reason])

    cols = ["point_id", "group", "tree", "mode", "request", "inj_call", "expected_class", "class", "verdict",
            "rc", "rc1", "rc2", "hit", "reason"]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# %s -- P05-S4 R7 M2 %s pass %s run %s.  Judge: judge_d003.classify (imported).\n"
                 % (os.path.basename(out), group, pas, tag))
        fh.write("\t".join(cols) + "\n")
        for row in res:
            fh.write("\t".join(row) + "\n")
    mism = sum(1 for x in res if x[8] != "MATCH")
    print("group=%s pass=%s run=%s rows=%d non_match=%d -> %s" % (group, pas, tag, len(res), mism, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
