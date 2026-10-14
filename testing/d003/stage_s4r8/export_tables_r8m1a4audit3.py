#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 3 (r8m1a4audit3), section 2 result tables.  New file.  Read only (writes tables).

Reads REQUEST_TARGETS_R8_M1a4AUDIT3.tsv (the audit3 classification) and writes:
  DIFF_AUDIT2_AUDIT3_R8_M1a4AUDIT3.tsv      row-by-row difference from audit2 (every row; status changed or not)
  CONCLUSION44_R8_M1a4AUDIT3.tsv            the 44 plan rows: historical class, audit2 status, audit3 status (U188)
  K_SOURCE_119_R8_M1a4AUDIT3.tsv            the 119 G5-F2 rows: K value, source and agreement (U189)
Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/export_tables_r8m1a4audit3.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit3")
EV2 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit2")
TGT = os.path.join(EV, "REQUEST_TARGETS_R8_M1a4AUDIT3.tsv")
A2 = os.path.join(EV2, "REQUEST_TARGETS_R8_M1a4AUDIT2_RUN3.tsv")
OUTS = ["DIFF_AUDIT2_AUDIT3_R8_M1a4AUDIT3.tsv", "CONCLUSION44_R8_M1a4AUDIT3.tsv", "K_SOURCE_119_R8_M1a4AUDIT3.tsv"]


def read_rows(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        if ln:
            cols = ln.split("\t")
            if len(cols) != len(hdr):
                raise SystemExit("REFUSED: column count in %s" % path)
            rows.append(dict(zip(hdr, cols)))
    return rows


def write_table(name, hdr, rows):
    out = os.path.join(EV, name)
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % name)
    with open(out, "x", encoding="utf-8") as fh:
        fh.write("\t".join(hdr) + "\n")
        for r in rows:
            fh.write("\t".join(str(r[h]).replace("\t", " ") for h in hdr) + "\n")
    return len(rows)


def main(argv):
    if len(argv) != 1:
        raise SystemExit("usage: export_tables_r8m1a4audit3.py")
    tgt = read_rows(TGT)
    a2 = read_rows(A2)
    if len(tgt) != 1128 or len(a2) != 1128:
        raise SystemExit("REFUSED: row count")
    a2map = {(r["source_registry"], r["source_row"]): r for r in a2}

    diff = []
    for r in tgt:
        key = (r["source_registry"], r["source_row"])
        o = a2map[key]
        diff.append({
            "source_registry": r["source_registry"], "source_row": r["source_row"], "point_id": r["point_id"],
            "group": r["group"], "source_tree": r["source_tree"], "kind": r["kind"],
            "canonical_target": r["canonical_target"], "unit_id": r["unit_id"],
            "audit2_status": o["status"], "audit3_status": r["status"],
            "changed": "yes" if o["status"] != r["status"] else "no",
            "k_source": r["k_source"],
        })
    dh = ["source_registry", "source_row", "point_id", "group", "source_tree", "kind", "canonical_target", "unit_id",
          "audit2_status", "audit3_status", "changed", "k_source"]
    n_diff = write_table(OUTS[0], dh, diff)

    plan44 = []
    for r in tgt:
        if r["kind"] == "PLAN" and r["status"] == "EXPECTED_NOT_REACHED":
            plan44.append({
                "source_registry": r["source_registry"], "source_row": r["source_row"], "point_id": r["point_id"],
                "source_tree": r["source_tree"], "canonical_target": r["canonical_target"], "unit_id": r["unit_id"],
                "historical_class": "INVALID_NOT_REACHED",
                "audit2_status": r["audit2_status"], "audit3_status": r["status"], "detail": r["detail"],
            })
    ph = ["source_registry", "source_row", "point_id", "source_tree", "canonical_target", "unit_id",
          "historical_class", "audit2_status", "audit3_status", "detail"]
    n44 = write_table(OUTS[1], ph, plan44)

    k119 = []
    for r in tgt:
        if r["k_source"].startswith("K_SOURCE_G5F2"):
            k119.append({
                "source_registry": r["source_registry"], "source_row": r["source_row"], "point_id": r["point_id"],
                "source_tree": r["source_tree"], "kind": r["kind"], "K": r["K"], "unit_id": r["unit_id"],
                "k_source": r["k_source"], "audit3_status": r["status"], "detail": r["detail"],
            })
    kh = ["source_registry", "source_row", "point_id", "source_tree", "kind", "K", "unit_id", "k_source",
          "audit3_status", "detail"]
    n119 = write_table(OUTS[2], kh, k119)

    print("diff rows=%d changed=%d" % (n_diff, sum(1 for d in diff if d["changed"] == "yes")))
    print("conclusion44 rows=%d" % n44)
    print("k_source119 rows=%d" % n119)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
