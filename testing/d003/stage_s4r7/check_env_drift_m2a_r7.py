#!/usr/bin/env python3
"""P05-S4 R7 M2a: ENV_DRIFT check, F(R7) against the historical F class, point by point (new file; read only).

ENV_DRIFT (cont2 section 5) = the R7 build of F does not reproduce the historical F class of the source table.
For each G2b, G3, G4 point, this compares the class observed in RESULTS_R7_<G>_pass<P>_run4.tsv (tree F) with the
historical F class in the source table (expected of the F row, same point).  The R7 point id is the source id with the
tree suffix "-F" added, so the source id = R7 id minus its final "-F".  Writes one new file.  Read only; no driver is run.

Usage (through safe_run):  python3 -I -B testing/d003/stage_s4r7/check_env_drift_m2a_r7.py EVDIR OUT.tsv
"""
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REG = os.path.join(REPO, "checkpoints", "p05", "registries")
SOURCES = {
    "G2b": os.path.join(REG, "s4r4", "RESULTS_R4_PLANCALL_pass1.tsv"),
    "G3": os.path.join(REG, "s4r5", "RESULTS_R5_PLANM_pass1.tsv"),
    "G4": os.path.join(REG, "s4r6", "RESULTS_R6_TWICE_pass1.tsv"),
}


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


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: check_env_drift_m2a_r7.py EVDIR OUT.tsv")
    ev, out = argv[1], argv[2]
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    lines = ["# ENV_DRIFT check, M2a (G2b, G3, G4): F(R7) class vs historical F class in the source table, point by point.",
             "# historical = expected of the F row of the source table (pass1); R7 = class of RESULTS_R7 tree F, pass 1 and pass 2.",
             "group\tsource_id\thistorical_F\tR7_F_pass1\tR7_F_pass2\tenv_drift"]
    drift = total = absent = 0
    for g, src in SOURCES.items():
        hist = {d["point_id"]: d["expected"] for d in table(src) if d["tree"] == "F"}
        per_pass = {}
        for p in ("1", "2"):
            store = {}
            for d in table(os.path.join(ev, "RESULTS_R7_%s_pass%s_run4.tsv" % (g, p))):
                if d["tree"] != "F":
                    continue
                pid = d["point_id"]
                sid = pid[:-len("-F")] if pid.endswith("-F") else pid
                store[sid] = d["class"]
            per_pass[p] = store
        for sid in sorted(hist):
            total += 1
            c1 = per_pass["1"].get(sid, "ABSENT")
            c2 = per_pass["2"].get(sid, "ABSENT")
            if "ABSENT" in (c1, c2):
                absent += 1
            flag = "DRIFT" if (c1 != hist[sid] or c2 != hist[sid]) else "-"
            if flag == "DRIFT":
                drift += 1
            lines.append("\t".join([g, sid, hist[sid], c1, c2, flag]))
    lines.append("# points=%d env_drift=%d absent=%d" % (total, drift, absent))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("points=%d env_drift=%d absent=%d -> %s" % (total, drift, absent, out))
    return 0 if (drift == 0 and absent == 0 and total > 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
