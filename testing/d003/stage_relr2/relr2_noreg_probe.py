#!/usr/bin/env python3
# relr2_noreg_probe.py -- REL-R2 no-injection research (task brief section 3.5): try candidate public-API
# inputs against the REL-R1 B and F4 exported trees, one child process per (case, tree), so a crash is
# observed as a process return code.  Read-only for the trees; writes only $EV/NOREG_PROBE_RELR2.tsv.
import os, sys, json, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r2")
TREES = os.path.join(REPO, "checkpoints/p05/evidence/p05-rel-r1/trees")
CASE = os.path.join(REPO, "testing/d003/stage_relr2/relr2_noreg_case.py")
OUT = os.path.join(EV, "NOREG_PROBE_RELR2.tsv")
TAB = chr(9)
NL = chr(10)
CASES = ["vl_nb1", "nv_nb1", "jones_nb1", "cf_eps0", "cf_epsbig",
         "kt_eps0", "kt_epsbig", "cf_eps_singular_tensor", "kt_eps_singular_tensor"]
TREEDIRS = {"B": os.path.join(TREES, "B"), "F4": os.path.join(TREES, "F4")}
TIMEOUT = 300


def main():
    rows = []
    for case in CASES:
        for label, tdir in TREEDIRS.items():
            if not os.path.isdir(tdir):
                rows.append({"case": case, "tree": label, "proc_rc": "NO_TREE", "status": "NO_TREE",
                             "detail": "", "all_finite": "", "same_as_other_tree": ""})
                continue
            try:
                p = subprocess.run([sys.executable, CASE, "--tree", tdir, "--case", case],
                                   capture_output=True, text=True, timeout=TIMEOUT, cwd=REPO)
                rc = p.returncode
                line = [l for l in p.stdout.splitlines() if l.strip().startswith("{")]
                rec = json.loads(line[-1]) if line else {"status": "NO_JSON"}
                detail = rec.get("message", "") or rec.get("value", "")
                rows.append({"case": case, "tree": label, "proc_rc": str(rc), "status": rec.get("status", "?"),
                             "detail": detail.replace(TAB, " ")[:240],
                             "all_finite": str(rec.get("all_finite", "")),
                             "same_as_other_tree": ""})
            except subprocess.TimeoutExpired:
                rows.append({"case": case, "tree": label, "proc_rc": "TIMEOUT", "status": "TIMEOUT",
                             "detail": "", "all_finite": "", "same_as_other_tree": ""})
    # mark whether B and F4 agree per case
    by_case = {}
    for r in rows:
        by_case.setdefault(r["case"], {})[r["tree"]] = r
    for case, d in by_case.items():
        b, f = d.get("B"), d.get("F4")
        if b and f:
            same = "YES" if (b["proc_rc"], b["status"], b["detail"]) == (f["proc_rc"], f["status"], f["detail"]) else "NO"
            b["same_as_other_tree"] = same
            f["same_as_other_tree"] = same
    cols = ["case", "tree", "proc_rc", "status", "all_finite", "same_as_other_tree", "detail"]
    lines = ["# NOREG_PROBE_RELR2.tsv -- REL-R2 no-injection reachability probe (task brief section 3.5)",
             "# Candidate public-API inputs run against the REL-R1 exported B and F4 trees (S4 source identical to",
             "# the product branch); one child process per (case, tree), so a signal shows up in proc_rc.",
             "# Written " + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
             TAB.join(cols)]
    for r in rows:
        lines.append(TAB.join(r[c] for c in cols))
    os.makedirs(EV, exist_ok=True)
    open(OUT, "w", encoding="utf-8").write(NL.join(lines) + NL)
    print("WROTE", os.path.relpath(OUT, REPO), "rows=%d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
