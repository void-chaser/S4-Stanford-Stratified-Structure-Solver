#!/usr/bin/env python3
# red_ledger_final_r9m3d.py -- M3d corrected final red-point ledger. Input is the committed M3c ledger; the script
# applies U352 (RP-R6d-15 condition met) and U354 (RP-R6d-14 closed, M2-05 all MATCH), keeps U355 (handoff covers
# every TRANSFERRED_S5 id) as a header invariant, and lists every changed id at the tail. All tables are read by
# column name. New file (r9m3d). usage: red_ledger_final_r9m3d.py [OUT.tsv]
import os, sys
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
REG = os.path.join(REPO, "checkpoints/p05/registries")
SRC = os.path.join(REG, "s4r9/M3c/RED_POINTS_LEDGER_FINAL_R9M3C.tsv")
TAB = chr(9)
NL = chr(10)
COLS = ["id", "first_round", "location", "repair_commit_tree", "post_fix_evidence", "closing_ruling",
        "current_status", "destination"]
CHANGES = {
    "RP-R6d-14": {
        "current_status": "CLOSED",
        "closing_ruling": "U354",
        "destination": "已关闭（U354：M2-05 8 点全 MATCH；范围 P0/P2/PP1/PP2、F4、driver_r8m2a2_layers）",
        "post_fix_evidence": "registries/s4r9/M2/VERDICT_R9.tsv M2-05 rows: 8 rows (4 injection P0/P2/PP1/PP2 + 4 controls,"
                             " incl M2-05-P0-F4-C) all MATCH; layouts per U245; closed by U354 (plan/code item P-1 verified)."
                             " (M3c row cited only U20/ERRATA_6c, no test evidence.)",
    },
    "RP-R6d-15": {
        "current_status": "CLOSED",
        "closing_ruling": "U345/U352",
        "destination": "带范围声明关闭（U345/U352；S-B 独立复核 DIFFS=0）",
        "post_fix_evidence": "registries/s4r5/S3_HANDOFF_COVERAGE_R5.tsv; M3c independent re-judge REJUDGE_E2E_R9M3C.tsv"
                             " (DIFFS=0, E2E_OK=25, CONTROL_OK=17); U345 close condition met per U352.",
    },
}


def read_table(path):
    rows = []
    hdr = None
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f and f[0] == hdr[0]:
            continue
        rows.append(dict(zip(hdr, f)))
    return hdr, rows


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv")
    if not os.path.isfile(SRC):
        print("HARD_STOP missing input " + SRC)
        return 2
    hdr, rows = read_table(SRC)
    missing_cols = [c for c in COLS if c not in hdr]
    if missing_cols:
        print("HARD_STOP %s missing columns %s" % (os.path.basename(SRC), missing_cols))
        return 2
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        print("HARD_STOP duplicate ids in input ledger")
        return 2
    changes = []
    for r in rows:
        rid = r["id"]
        if rid in CHANGES:
            old_status = r["current_status"]
            old_ruling = r["closing_ruling"]
            for k, v in CHANGES[rid].items():
                r[k] = v
            changes.append((rid, old_status, old_ruling, r["current_status"], r["closing_ruling"]))
    t5 = [r["id"] for r in rows if r["current_status"] == "TRANSFERRED_S5"]
    open_in_scope = len([r for r in rows if r["current_status"] in ("OPEN", "DEFERRED") and "S5" not in r["destination"]])
    no_red = len([r for r in rows if r["current_status"] == "NO_RED_POINT"])
    # header invariants copied from the M3c ledger
    src_txt = open(SRC, encoding="utf-8").read().splitlines()
    conflicts = 0
    for l in src_txt:
        if l.startswith("# CONFLICTS:"):
            conflicts = int(l.strip().split(":")[-1].strip())
    norow_src = 0
    for l in src_txt:
        if l.startswith("# NO_RED_POINT_ROWS="):
            norow_src = int(l.strip().split("=")[1])
    if norow_src != no_red:
        print("HARD_STOP NO_RED_POINT_ROWS mismatch %d != %d" % (norow_src, no_red))
        return 2
    lines = []
    lines.append("# RED_POINTS_LEDGER_FINAL_R9M3D.tsv -- M3d corrected consolidated red-point ledger (one row per id)")
    lines.append("# input: checkpoints/p05/registries/s4r9/M3c/RED_POINTS_LEDGER_FINAL_R9M3C.tsv (committed in M3c; unchanged)")
    lines.append("# corrections: U352 (RP-R6d-15 close condition met: S-B re-judge DIFFS=0), U354 (RP-R6d-14 CLOSED:")
    lines.append("#   M2-05 8 points all MATCH; scope = layouts P0/P2/PP1/PP2, tree F4, driver driver_r8m2a2_layers).")
    lines.append("# U355 invariant: the S5 handoff list must contain every TRANSFERRED_S5 id in this ledger and every")
    lines.append("#   handoff item must map to a ledger id or a STATE row (checked by s5_handoff_r9m3d.py).")
    lines.append("# dedup rule: one row per id (input already consolidated: legacy R6c ids mapped to RP-R6d-*).")
    lines.append("# CONFLICTS: same id with different raw status across the original ledgers: %d (carried from M3c)" % conflicts)
    lines.append(TAB.join(COLS))
    for r in rows:
        lines.append(TAB.join(r[c] for c in COLS))
    lines.append("# CHANGES=%d" % len(changes))
    for rid, old_s, old_rul, new_s, new_rul in changes:
        lines.append("# CHANGE\t%s\t%s → %s | 依据裁决 %s→%s" % (rid, old_s, new_s, old_rul, new_rul))
    lines.append("# OPEN_IN_SCOPE=%d" % open_in_scope)
    lines.append("# NO_RED_POINT_ROWS=%d" % no_red)
    lines.append("# TRANSFERRED_S5=%d\t%s" % (len(t5), ",".join(sorted(t5))))
    lines.append("# UNIQUE=%d ROWS=%d" % (len(set(ids)), len(rows)))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines) + NL)
    print("input_rows=%d unique=%d changes=%d transferred_s5=%d open_in_scope=%d" % (
        len(rows), len(set(ids)), len(changes), len(t5), open_in_scope))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
