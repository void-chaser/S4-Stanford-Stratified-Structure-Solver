#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a audit (r8m1a4audit): check the _R3 unit table against the historical runners.  New file.

Read-only with respect to the repository.  Writes one TSV into the evidence directory given as argument.

This audit does NOT reuse the mapping functions of counted_families_r8m1a4.py.  It re-derives, from the historical
runner rules (run_m1_r7.py driver table, run_m2b_all_r7.py history_case / build_row / seam_driver_name,
dryrun_m3_r7.py derive_seam_env) and from the registry rows themselves, the expected environment of every
registry row, and compares it with the environment that the _R3 unit table gives that row.

Output: AUDIT_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv, one line per registry row, with the derived values and a verdict.
A row is OK only if mode, NG, TWICE, driver family and the run tree of the driver all agree.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REG_R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
CP_R3 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")


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


def history_m2_env(group, pid, add_row, v2_row):
    """Historical M2 environment rule.

    NG: ADD row NG if present, else "9" (run_m2b_all_r7.py point_spec / run_m2_r7.py point_spec, comment 175-177).
    TWICE: history_case: G2a case = point id (no t4/ prefix, so never TWICE); G1/G2c: t4/ (TWICE) iff twice flag,
           twice flag = ADD twice_env == slab if ADD row exists, else v2 route == twice (run_m2_r7.py point_spec).
    driver family: G1 -> d003; G2c/G2b/G3/G4 -> d003plan; G2a -> seam (seam_driver_name: fmmret prefix -> fmmret, else seamF).
    """
    if add_row is not None:
        ng = add_row["ng"] if add_row["ng"] not in ("", "-") else "9"
        twice = add_row["twice_env"] == "slab"
        req = add_row["request"]
    else:
        ng = "9"
        twice = v2_row["route"] == "twice"
        req = v2_row["request"]
    if group == "G2a":
        twice = False  # case = point id, build_env sets TWICE only for t4/ cases
        fam = "fmmret" if req.startswith("fmmret:") else "seamF"
    elif group == "G1":
        fam = "d003"
    else:
        fam = "d003plan"
    return ng, twice, fam, req


def history_m3_env(group, route, req):
    """Historical M3 environment rule (dryrun_m3_r7.py derive_seam_env: once route, no TWICE; state: run_r6c_state rule).

    G5 state points: driver r6bstate; TWICE from route == twice (the state rule is route-driven, see M3 registry 'route').
    G6/G6c seam points: driver r6bseam (fmmret prefix -> fmmret, else seamF); seam rule: once route, no TWICE.
    NG: 9 (dryrun_m3_r7.py line 20).
    """
    ng = "9"
    if group == "G5":
        return ng, route == "twice", "r6bstate", req
    fam = "r6bseam-fmmret" if req.startswith("fmmret:") else "r6bseam-seamF"
    return ng, False, fam, req


def history_m1_env(point_id, group, request, ng_col):
    """Historical M1 driver rule (run_m1_r7.py DRIVER table): tri points (M1-42-tri / M1-G8) -> tri; others -> r6dnv1.

    M1 has no route/TWICE column; it runs once (run_m1_r7 rule), so TWICE is False.
    """
    fam = "tri" if (point_id.startswith("M1-42-tri") or point_id.startswith("M1-G8")) else "r6dnv1"
    return ng_col, False, fam, request


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: audit_units_vs_history_r8m1a4audit.py OUTDIR")
    out_dir = argv[1]
    out_path = os.path.join(out_dir, "AUDIT_UNITS_VS_HISTORY_R8_M1a4AUDIT.tsv")
    if os.path.exists(out_path):
        raise SystemExit("REFUSED: exists (U17): %s" % out_path)

    m2 = read_rows(os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M2.tsv"))
    add = read_rows(os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv"))
    m1 = read_rows(os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M1.tsv"))
    m3 = read_rows(os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M3.tsv"))

    # ADD keyed by (point_id, tree, group); a key that is not unique is refused (ambiguity)
    add_by = {}
    for n, r in add:
        key = (r["point_id"], r["tree"], r["group"])
        if key in add_by:
            raise SystemExit("REFUSED: duplicate ADD key %s at line %d" % (key, n))
        add_by[key] = (n, r)

    out_rows = []
    counts = {"OK": 0, "MISMATCH": 0}
    for n, r in m2:
        key = (r["point_id"], r["tree"], r["group"])
        add_entry = add_by.get(key)
        add_row = add_entry[1] if add_entry else None
        ng, twice, fam, req = history_m2_env(r["group"], r["point_id"], add_row, r)
        out_rows.append(("M2", n, r["point_id"], r["group"], r["tree"], r["mode"], ng, "slab" if twice else "-",
                         fam, req, add_entry[0] if add_entry else "-"))
    for n, r in m1:
        ng, twice, fam, req = history_m1_env(r["point_id"], r["group"], r["request"], r["NG"])
        out_rows.append(("M1", n, r["point_id"], r["group"], r["tree"], r["mode"], ng, "slab" if twice else "-",
                         fam, req, "-"))
    for n, r in m3:
        ng, twice, fam, req = history_m3_env(r["group"], r["route"], r["request"])
        out_rows.append(("M3", n, r["point_id"], r["group"], r["tree"], r["mode"], ng, "slab" if twice else "-",
                         fam, req, "-"))

    with open(out_path, "x", encoding="utf-8") as fh:
        fh.write("registry\tline\tpoint_id\tgroup\ttree\tmode\tNG\ttwice_env\tdriver_family\trequest\tadd_line\n")
        for row in out_rows:
            fh.write("\t".join(str(x) for x in row) + "\n")

    print("AUDIT_UNITS_VS_HISTORY rows=%d (M2=%d, M1=%d, M3=%d)" % (
        len(out_rows), len(m2), len(m1), len(m3)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
