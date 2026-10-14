#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a audit (r8m1a4audit): compare the _R3 coverage table with the history-rule audit.  New file.

Read-only.  Inputs:
  CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv   (the _R3 coverage rows, produced by counted_families_r8m1a4.py)
  m1a4audit/AUDIT_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv   (history-rule expectations, produced by the audit script)
Output: COMPARE_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv in the evidence directory argument.

Rule of comparison (no tolerance):
  key = (registry, point_id, group, tree)  -- must be unique on both sides; ambiguity is refused.
  compared fields: mode, NG, TWICE (slab or -), driver family.
  run_tree is reported but not compared: the source tree F (historical frozen tree) is mapped to the run tree F3
  by the scope rule of this round (task section 4; U179); that is a declared scope decision, not an agreement.
Verdict per row: OK or MISMATCH.  Any MISMATCH stops the dependent step; nothing is re-derived to remove it.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVB = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")

# coverage family -> history family name used by the audit
FAM_MAP = {
    "d003-plain": "d003",
    "d003plan-plain": "d003plan",
    "seam-seamF-plain": "seamF",
    "seam-fmmret-plain": "fmmret",
    "r6dnv1-plain": "r6dnv1",
    "tri-dbg": "tri",
    "r6bstate-dbg": "r6bstate",
    "r6bseam-seamF-dbg": "r6bseam-seamF",
    "r6bseam-fmmret-dbg": "r6bseam-fmmret",
}


def read_rows(path):
    hdr = None
    out = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            cols = line.split("\t")
            if hdr is None:
                hdr = cols
                continue
            if len(cols) != len(hdr):
                raise SystemExit("REFUSED: column count %d != %d at %s:%d" % (len(cols), len(hdr), path, n))
            out.append((n, dict(zip(hdr, cols))))
    return out


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: compare_units_vs_history_r8m1a4audit.py OUTDIR")
    out_dir = argv[1]
    out_path = os.path.join(out_dir, "COMPARE_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv")
    if os.path.exists(out_path):
        raise SystemExit("REFUSED: exists (U17): %s" % out_path)

    cov = read_rows(os.path.join(EVB, "CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv"))
    hist = read_rows(os.path.join(out_dir, "AUDIT_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv"))
    units = read_rows(os.path.join(EVB, "CALLSEQ_UNITS_R8_M1a4_R3.tsv"))

    # unit_id -> twice_env ("slab" or "-") from the _R3 unit table; a duplicate unit_id is refused
    unit_twice = {}
    for n, u in units:
        if u["unit_id"] in unit_twice:
            raise SystemExit("REFUSED: duplicate unit_id %s at unit line %d" % (u["unit_id"], n))
        unit_twice[u["unit_id"]] = u["twice_env"]

    # history side keyed by (registry, point_id, group, tree); must be unique
    hk = {}
    for n, r in hist:
        key = (r["registry"], r["point_id"], r["group"], r["tree"])
        if key in hk:
            raise SystemExit("REFUSED: ambiguous history key %s at line %d" % (key, n))
        hk[key] = (n, r)

    rows_out = []
    counts = {"OK": 0, "MISMATCH": 0, "NO_HISTORY_ROW": 0, "NOT_MAPPED": 0}
    seen = set()
    for n, c in cov:
        if c["coverage_class"] != "MAPPED":
            continue  # N/A control, and the 22 additions handled separately
        reg = c["source_registry"]
        key = (reg, c["point_id"], c["group"], c["source_tree"])
        if key in seen:
            # the same registry row can only appear once in coverage; a repeat is an error
            raise SystemExit("REFUSED: duplicate coverage key %s" % (key,))
        seen.add(key)
        hit = hk.get(key)
        if hit is None:
            rows_out.append((reg, n, c["point_id"], c["group"], c["source_tree"], "NO_HISTORY_ROW", "-", "-", "-", "NO_HISTORY_ROW"))
            counts["NO_HISTORY_ROW"] += 1
            continue
        hn, h = hit
        cov_fam = FAM_MAP.get(c["driver_family"])
        fields = []
        ok = True
        if c["mode"] != h["mode"]:
            fields.append("mode:%s!=%s" % (c["mode"], h["mode"]))
            ok = False
        if c["NG"] != h["NG"]:
            fields.append("NG:%s!=%s" % (c["NG"], h["NG"]))
            ok = False
        # The coverage table has no twice_env column.  Its unit table (_R3) carries TWICE in twice_env.  The coverage
        # row is joined to its unit by unit_id; TWICE is read from that unit, never from the route label, because
        # route labels of G2a (E/B2/C/A/D) and of seam rows are not TWICE flags (history_case, dryrun_m3 derive_seam_env).
        cov_twice = unit_twice.get(c["unit_id"])
        if cov_twice is None:
            raise SystemExit("REFUSED: coverage row with unit_id %s has no unit row" % c["unit_id"])
        if cov_twice != h["twice_env"]:
            fields.append("TWICE:%s!=%s" % (cov_twice, h["twice_env"]))
            ok = False
        if cov_fam is None:
            fields.append("UNMAPPED_FAMILY:%s" % c["driver_family"])
            ok = False
        elif cov_fam != h["driver_family"]:
            fields.append("DRIVER:%s!=%s" % (cov_fam, h["driver_family"]))
            ok = False
        verdict = "OK" if ok else "MISMATCH"
        counts[verdict] += 1
        rows_out.append((reg, n, c["point_id"], c["group"], c["source_tree"], verdict,
                         "run_tree=%s" % c["run_tree"], ";".join(fields) if fields else "-",
                         "history_line=%d" % hn, c["unit_id"]))

    with open(out_path, "x", encoding="utf-8") as fh:
        fh.write("registry\tcoverage_line\tpoint_id\tgroup\tsource_tree\tverdict\trun_tree_note\tfield_differences\thistory_ref\tunit_id\n")
        for row in rows_out:
            fh.write("\t".join(str(x) for x in row) + "\n")

    print("COMPARE_UNITS_VS_HISTORY mapped_rows=%d OK=%d MISMATCH=%d NO_HISTORY_ROW=%d" % (
        len(rows_out), counts["OK"], counts["MISMATCH"], counts["NO_HISTORY_ROW"]))
    if counts["MISMATCH"] or counts["NO_HISTORY_ROW"]:
        print("COMPARE_UNITS_VS_HISTORY: STOP (mismatch or unmatched row); not re-derived to remove it")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
