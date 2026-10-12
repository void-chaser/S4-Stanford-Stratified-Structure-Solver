#!/usr/bin/env python3
"""P05-S4 R7 M1a (U44): POSTHOC re-judgement of the 18 M1 control rows.  New file.  READ ONLY: no driver is run.

Inputs (read only):
  - REGISTRY_S4_PRE_R7_M1.tsv: the registered control rows (the rc string is read from column first_expected_class,
    which is where the generator wrote it; expected_win1_rc holds "-" for controls, see ERRATA_CTRL item 1).
  - m1_selfcheck/M1-CTRL-*/pass{1,2}_run2/nogdb.out: the stored stdout of each control run.
Rules (ERRATA_CTRL item 3):
  a. MATCH_TO_REGISTRY: observed RC first, RC retry and the process rc equal the registered string, and hit = 0.
  b. CONTROL_OK: (a) and rc_first = rc_retry = run_rc = 0.
  c. BASELINE_RC_EQUAL: (a) and rc_first = 20 (vl, fftvl NG1; the D016 -10 path).
  d. NOT_EQUAL otherwise.
The process rc is not stored in nogdb.out; it is read from the registry string only where the runner recorded it in
RESULTS_R7_M1_pass{N}_run2.tsv column rc.  So the rc value used here is taken from that results table (the stored run rc),
and the nogdb.out text supplies RC first, RC retry and the hit count.
Output (new file, U17): argv[1].  Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r7/rejudge_ctrl_m1_r7.py EVDIR/RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv
"""
import os
import re
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7")
REG = os.path.join(EV, "REGISTRY_S4_PRE_R7_M1.tsv")
RES = {"1": os.path.join(EV, "RESULTS_R7_M1_pass1_run2.tsv"), "2": os.path.join(EV, "RESULTS_R7_M1_pass2_run2.tsv")}
RE_RC1 = re.compile(r"^RC first (-?\d+)\s*$", re.M)
RE_RC2 = re.compile(r"^RC retry (-?\d+)\s*$", re.M)
RE_HITC = re.compile(r"^S4FMM HITCOUNT (-?\d+)\s*$", re.M)
RE_HIT = re.compile(r"^S4FMM HIT ", re.M)


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


def parse_reg_string(s):
    """'rc_first=20,rc_retry=20,run_rc=0' -> (20, 20, 0) as strings."""
    d = dict(p.split("=", 1) for p in s.split(","))
    return d["rc_first"], d["rc_retry"], d["run_rc"]


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: rejudge_ctrl_m1_r7.py OUT.tsv")
    out = argv[1]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    reg = {r["point_id"]: r for r in table(REG) if r["group"] == "control"}
    if len(reg) != 18:
        raise SystemExit("control rows in registry %d != 18" % len(reg))
    lines = ["# RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv -- P05-S4 R7 M1a (U44): POSTHOC re-judgement of the 18 control rows.",
             "# Read only: stored nogdb.out and the stored process rc of RESULTS_R7_M1_pass{N}_run2.tsv.  No driver run.",
             "# Rule: ERRATA CTRL item 3.  Original RESULTS and REGRESS rows stay MISMATCH (U44).  Status POSTHOC.",
             "point_id\tmode\tNG\tregistered_string\tpass\tobs_rc_first\tobs_rc_retry\tobs_run_rc\thit\tlabel\tmatch_to_registry"]
    counts = {}
    for pas, rpath in RES.items():
        by = {r["point_id"]: r for r in table(rpath)}
        for pid, r in sorted(reg.items()):
            # the rc string is in column expected_class (index 8); first_expected_class holds CONTROL_OK (see ERRATA CTRL item 1)
            want = parse_reg_string(r["expected_class"])
            base = os.path.join(EV, "m1_selfcheck", pid, "pass%s_run2" % pas, "nogdb.out")
            with open(base, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            m1, m2 = RE_RC1.search(text), RE_RC2.search(text)
            hc = RE_HITC.search(text)
            hit = int(hc.group(1)) if hc else len(RE_HIT.findall(text))
            obs_rc1 = m1.group(1) if m1 else "NA"
            obs_rc2 = m2.group(1) if m2 else "NA"
            obs_run = by[pid]["rc"]
            equal = (obs_rc1, obs_rc2, obs_run) == want and hit == 0
            if not equal:
                label = "NOT_EQUAL"
            elif want == ("0", "0", "0"):
                label = "CONTROL_OK"
            elif want[0] == "20":
                label = "BASELINE_RC_EQUAL"
            else:
                label = "NOT_EQUAL"
            counts[(pas, label)] = counts.get((pas, label), 0) + 1
            lines.append("\t".join([pid, r["mode"], r["NG"], r["expected_class"], pas, obs_rc1, obs_rc2, obs_run,
                                    str(hit), label, "YES" if equal else "NO"]))
    lines.append("# counts: %s" % ", ".join("pass%s %s=%d" % (k[0], k[1], v) for k, v in sorted(counts.items())))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines[-2:]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
