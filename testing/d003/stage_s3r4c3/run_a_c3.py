#!/usr/bin/env python3
"""run_a_c3.py -- P05-S3R4 CONT3 self-check (A): 806 and 1729 injection runs (new file).

Reads the pre-registration REGISTRY_S3R4C2_A.tsv (unchanged, U109) and runs every row twice with the
init driver linked in CONT2 (sha256 checked; the binary is NOT relinked, U109).  Facts come from the
driver return code (signal -> 128+n) and from judge_d003.facts_from_log over stdout+stderr.  The class
comes from judge_d003.classify (imported, not modified).

Invoked only through:  sh testing/d003/safe_run.sh p05-s3r4c3 -- sh testing/d003/stage_s3r4c3/run_a_c3.sh PHASE
PHASE = inj (36 injection runs) or ctrl (6 no-injection controls).
"""
import csv
import hashlib
import os
import subprocess
import sys
import time

REPO = os.environ["REPO"]
EV = os.environ["EV"]
PHASE = sys.argv[1]
sys.path.insert(0, os.path.join(REPO, "testing", "d003"))
import judge_d003 as J  # noqa: E402

C2 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s3r4c2")
PREREG = os.path.join(C2, "REGISTRY_S3R4C2_A.tsv")
PREREG_SHA = "3f08fd8b86d2a5164b272cf3881729b3fbda04dca52e7b8d96dd64c586e5845d"
DRIVER = {
    "F2": os.path.join(C2, "drivers", "init-F2", "driver"),
    "F3": os.path.join(C2, "drivers", "init-F3", "driver"),
}
EXPECTED_SHA = {
    "F2": "29bb377c4eb5e1d393d2916d2ad9a05d9ecf781fc4cc709dd87332f8904d1158",
    "F3": "ff66cfc1bf87b6c22d13e32dc6adf3c5e6b090fdcad745bf5248f74dd9510b68",
}
PASSES = (1, 2)
CTRL_COMBOS = [("closed2d-ng1", "closed2d", 1), ("fft-ng5", "fft", 5), ("kottke-ng5", "kottke", 5)]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def run_one(tree, mode, ng, inj, outdir):
    """Run the driver once. Returns (rc, stdout_text, stderr_text)."""
    os.makedirs(outdir, exist_ok=True)
    env = {"PATH": os.environ.get("PATH", "")}
    env["FMM_MODE"] = mode
    env["S4FMM_NG"] = str(ng)
    env["S4FMM_DUMP_DIR"] = outdir
    if inj:
        env["S4FMM_INJECT"] = inj
    out_path = os.path.join(outdir, "stdout.txt")
    err_path = os.path.join(outdir, "stderr.txt")
    with open(out_path, "w") as fo, open(err_path, "w") as fe:
        p = subprocess.run([DRIVER[tree], "pattern", "both", "4", "3"],
                           env=env, stdout=fo, stderr=fe, cwd=REPO)
    rc = p.returncode
    if rc < 0:
        rc = 128 - rc  # killed by signal n -> 128+n
    with open(out_path) as f:
        so = f.read()
    with open(err_path) as f:
        se = f.read()
    return rc, so, se


def facts(rc, so, se):
    f = J.facts_from_log(so + se)
    return rc, f["rc1"], f["rc2"], f["hit"]


def main():
    t0 = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    for tree in ("F2", "F3"):
        got = sha256(DRIVER[tree])
        if got != EXPECTED_SHA[tree]:
            print("DRIVER SHA MISMATCH %s %s" % (tree, got))
            return 3
    print("driver sha ok %s" % t0)
    if sha256(PREREG) != PREREG_SHA:
        print("PREREG SHA MISMATCH")
        return 3
    print("prereg sha ok")

    if PHASE == "inj":
        results_path = os.path.join(EV, "RESULTS_S3R4C3_A.tsv")
        if os.path.exists(results_path):
            print("REFUSED: exists %s" % results_path)
            return 2
        with open(PREREG) as f:
            rows = list(csv.DictReader(f, delimiter="\t"))
        out_rows = []
        for r in rows:
            combo, mode, ng, tree = r["combo"], r["mode"], int(r["NG"]), r["tree"]
            pid, inj = r["point_id"], r["inj_spec"]
            exp_rc1, exp_class, exp_side = r["expected_rc1"], r["expected_class"], r["expected_side_rc2"]
            for pas in PASSES:
                d = os.path.join(EV, "a_c3", tree, combo, pid, "pass%d" % pas)
                rc, so, se = run_one(tree, mode, ng, inj, d)
                rc_, rc1, rc2, hit = facts(rc, so, se)
                cls, label, reason = J.classify(rc_, rc1, rc2, hit, control=False, real=True, inj_call=1)
                rc1_ok = (exp_rc1 == "-") or (rc1 is not None and str(rc1) == exp_rc1)
                verdict = "MATCH" if (cls == exp_class and rc1_ok) else "MISMATCH"
                side = "-"
                if exp_side != "-":
                    side = "MATCH" if (rc2 is not None and str(rc2) == exp_side) else "MISMATCH"
                out_rows.append([combo, mode, ng, tree, pid, inj, pas, rc_,
                                 "" if rc1 is None else rc1, "" if rc2 is None else rc2, hit,
                                 cls, reason, exp_rc1, exp_class, verdict, side])
        # FLAKY: the two passes of one point disagree on class or rc1
        by = {}
        for row in out_rows:
            by.setdefault((row[0], row[3], row[4]), []).append(row)
        for key, grp in by.items():
            if len(grp) == 2 and (grp[0][11] != grp[1][11] or grp[0][8] != grp[1][8]):
                for row in grp:
                    row[15] = "FLAKY"
        with open(results_path, "w") as f:
            f.write("\t".join(["combo", "mode", "NG", "tree", "point_id", "inj_spec", "pass", "rc",
                               "rc1", "rc2", "hit", "class", "reason", "expected_rc1",
                               "expected_class", "verdict", "side_rc2_match"]) + "\n")
            for row in out_rows:
                f.write("\t".join(str(x) for x in row) + "\n")
        n_match = sum(1 for r in out_rows if r[15] == "MATCH")
        n_mis = sum(1 for r in out_rows if r[15] == "MISMATCH")
        n_flaky = sum(1 for r in out_rows if r[15] == "FLAKY")
        print("A injection: rows=%d MATCH=%d MISMATCH=%d FLAKY=%d" % (len(out_rows), n_match, n_mis, n_flaky))
        return 0

    if PHASE == "ctrl":
        ctrl_path = os.path.join(EV, "RESULTS_S3R4C3_A_CTRL.tsv")
        if os.path.exists(ctrl_path):
            print("REFUSED: exists %s" % ctrl_path)
            return 2
        lines = ["combo\tmode\tNG\ttree\tpass\trc\trc1\trc2\thit\tclass\treason\tverdict"]
        for combo, mode, ng in CTRL_COMBOS:
            for tree in ("F2", "F3"):
                d = os.path.join(EV, "a_c3_ctrl", tree, combo, "pass1")
                rc, so, se = run_one(tree, mode, ng, None, d)
                rc_, rc1, rc2, hit = facts(rc, so, se)
                cls, label, reason = J.classify(rc_, rc1, rc2, hit, control=True, real=True, inj_call=1)
                verdict = "CONTROL_OK" if cls == "CONTROL_OK" else "NOT_CONTROL_OK"
                lines.append("\t".join(str(x) for x in [
                    combo, mode, ng, tree, 1, rc_,
                    "" if rc1 is None else rc1, "" if rc2 is None else rc2, hit,
                    cls, reason, verdict]))
        with open(ctrl_path, "w") as f:
            f.write("\n".join(lines) + "\n")
        print("A control written: %s" % ctrl_path)
        return 0

    print("unknown phase %s" % PHASE)
    return 2


if __name__ == "__main__":
    sys.exit(main())
