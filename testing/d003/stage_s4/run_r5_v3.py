#!/usr/bin/env python3
# run_r5_v3.py -- P05-S4 R5-6 (V3): retry equivalence on the PLAIN F driver.
# New file.  judge_d003.py is IMPORTED.  Driver: the R4 plain F driver (plain-r4-F, inject_r4_plan.cpp), the same
# binary that produced the M2 and R4 plancall results.  Baselines: $EV/v3/base/<mode>-<route>-p<pass>.txt (S4FMM_DUMP1,
# no injection, written by the shell loop in R5-6).
#
#   python3 -I -B testing/d003/stage_s4/run_r5_v3.py EV_DIR DRIVER_F OUT_TSV
#
# Points: the 132 F points with rc1 != 0 and a non-sanitizer REPORTED_FAILURE, from san/SAN_R5.tsv (sets R3, R4PC, M2).
# The R4 main-matrix (set R4M, seam libraries) is NOT compared against the plain baseline: its library is a seam build,
# not the plain tree.  The rc2-only points (rc1 = 0) are listed separately, not compared.
# Output columns: set, point_id, mode, route, rc1, rc2, hit, partial_modes(witness), retry_vs_base_cmp, max_rel_diff, note
import math
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
D003 = os.path.join(REPO, "testing", "d003")
sys.path.insert(0, D003)
sys.path.insert(0, HERE)

import judge_d003 as J  # noqa: E402

GRID = ["pattern", "both", "4", "3"]
TIMEOUT_S = 300
EVR = os.path.join(REPO, "checkpoints", "p05", "evidence")


def read_tsv(path):
    rows, header = [], None
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


def parse_field(path):
    """Read an S4FMM_DUMP / S4FMM_DUMP1 file: lines 'E idx value' and 'H idx value'."""
    e, h = [], []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            p = line.split()
            if len(p) == 3 and p[0] in ("E", "H"):
                (e if p[0] == "E" else h).append(float(p[2]))
    return e, h


def max_rel(a, b):
    """Largest relative difference over E and H (|a-b| / max(|a|,|b|,tiny)), and the count of non-finite values."""
    worst = 0.0
    nonfinite = 0
    for x, y in zip(a, b):
        if not (math.isfinite(x) and math.isfinite(y)):
            nonfinite += 1
            continue
        d = abs(x - y)
        s = max(abs(x), abs(y), 1e-300)
        worst = max(worst, d / s)
    return worst, nonfinite


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: run_r5_v3.py EV_DIR DRIVER_F OUT_TSV")
    ev, drv, out_tsv = argv[1], argv[2], argv[3]
    if not (os.path.isfile(drv) and os.access(drv, os.X_OK)):
        raise SystemExit("REFUSED: driver missing: %s" % drv)
    runs = os.path.join(ev, "v3", "retry_runs")
    os.makedirs(runs, exist_ok=True)
    base_dir = os.path.join(ev, "v3", "base")

    san = read_tsv(os.path.join(ev, "san", "SAN_R5.tsv"))
    # request, nth, mode, route for each point of the three sets (R4M excluded)
    pc = {r["point_id"]: r for r in read_tsv(os.path.join(EVR, "p05-s4r4", "plancall", "RESULTS_R4_PLANCALL_pass1.tsv")) if r["tree"] == "F"}
    m2 = {r["point_id"]: r for r in read_tsv(os.path.join(ev, "planm", "RESULTS_R5_PLANM_pass1.tsv")) if r["tree"] == "F"}
    inject_map = {"malloc": "s4malloc", "plan": "plan", "exec": "exec"}
    pre3 = {r["point_id"]: r for r in read_tsv(os.path.join(EVR, "p05-s4r3", "REGISTRY_S4_PRE_R3.tsv")) if r["tree"] == "F"}

    lines = ["# V3_RETRY_R5.tsv -- P05-S4 R5-6 (V3): retry equivalence on plain F (plain-r4-F driver).",
             "# retry_vs_base_cmp: cmp of the retry field (S4FMM_DUMP) with the baseline of the same mode and route (S4FMM_DUMP1,",
             "# no injection, two passes both byte-identical).  max_rel_diff computed only when cmp differs.",
             "# partial_modes / sentinel / untouched lines are the driver's own checks, recorded as FACTS, not as the verdict.",
             "set\tpoint_id\tmode\troute\trc1\trc2\thit\tretry_vs_base_cmp\tmax_rel_diff\tnonfinite\tdriver_checks\tnote"]
    n = 0
    for s in san:
        if s["set"] not in ("R3", "R4PC", "M2"):
            continue
        if s["class_san"] != "REPORTED_FAILURE" or s["rc1"] == "0":
            continue
        pid = s["point_id"]
        if s["set"] == "R3":
            p3 = pre3[pid]
            route = "twice" if pid.startswith("M-twice") else "once"
            mode = p3["mode"]
            # R3 request form: "<INJECT[cat]>" with NTH in S4FMM_NTH (see run_r3_sweep.py); use the same env
            env_req = inject_map[p3["category"]]
            env_nth = p3["NTH"]
            env = {"S4FMM_INJECT": env_req, "S4FMM_NTH": env_nth}
        elif s["set"] == "R4PC":
            row = pc[pid]
            route, mode = row["route"], row["mode"]
            env = {"S4FMM_INJECT": row["request"]}
        else:  # M2
            row = m2[pid]
            route, mode = row["route"], row["mode"]
            env = {"S4FMM_INJECT": row["request"]}

        base_name = "%s-%s-p1.txt" % (mode, route)
        base_path = os.path.join(base_dir, base_name)
        if not os.path.isfile(base_path):
            raise SystemExit("REFUSED: no baseline for %s %s" % (mode, route))

        dump = os.path.join(runs, "%s.txt" % pid)
        full = dict(os.environ)
        full.pop("S4FMM_TWICE", None)
        full["FMM_MODE"] = mode
        full["S4FMM_NG"] = "9"
        full.update(env)
        if route == "twice":
            full["S4FMM_TWICE"] = "slab"
        full["S4FMM_DUMP"] = dump
        log = os.path.join(runs, "%s.log" % pid)
        try:
            proc = subprocess.run([drv] + GRID, env=full, cwd=runs, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, timeout=TIMEOUT_S)
            rc = proc.returncode
            out = proc.stdout
        except subprocess.TimeoutExpired as exc:
            rc = 124
            out = exc.stdout or b""
        with open(log, "wb") as fh:
            fh.write(out)
        text = out.decode("utf-8", errors="replace")
        facts = J.facts_from_log(text)
        pm = re.search(r"partial_modes[=: ]+(\S+)", text)
        pmw = pm.group(1) if pm else "none"
        checks = [l.strip() for l in text.splitlines() if l.startswith("CHECK ")]
        ok_checks = sum(1 for c in checks if c.endswith(" ok"))
        fail_checks = sum(1 for c in checks if c.endswith("FAILED"))
        driver_checks = "ok=%d failed=%d" % (ok_checks, fail_checks)

        if os.path.isfile(dump) and os.path.getsize(dump) > 0:
            cmp_rc = subprocess.run(["cmp", "-s", dump, base_path]).returncode
            cmp_res = "IDENTICAL" if cmp_rc == 0 else "DIFFER"
            if cmp_rc != 0:
                ea, ha = parse_field(base_path)
                eb, hb = parse_field(dump)
                worst_e, nf_e = max_rel(ea, eb)
                worst_h, nf_h = max_rel(ha, hb)
                mrd = "%.6g" % max(worst_e, worst_h)
                nf = str(nf_e + nf_h)
            else:
                mrd, nf = "0", "0"
        else:
            cmp_res, mrd, nf = "NO_DUMP", "-", "-"
        note = "retry rc=%d" % rc
        lines.append("\t".join([s["set"], pid, mode, route, s["rc1"], str(facts["rc2"]), str(facts["hit"]),
                                cmp_res, mrd, nf, driver_checks + " partial_modes=" + pmw, note]))
        n += 1

    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("compared=%d -> %s" % (n, out_tsv))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
