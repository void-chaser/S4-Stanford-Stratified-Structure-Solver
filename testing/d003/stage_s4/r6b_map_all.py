#!/usr/bin/env python3
# r6b_map_all.py -- P05-S4 R6b-2 (new file).  Builds the 202-point map for R6b (S3-4b state judgement).
# Sources (each row records its source file and 1-based line number):
#   R3       : registries/s4r6/MAP_R6_R3.tsv (119 F REPORTED_FAILURE points, R6-2a)            -> 119
#   R4PC     : registries/s4r4/RESULTS_R4_PLANCALL_pass1.tsv, tree F (22 plan points)          -> 22
#   R5M2     : registries/s4r5/RESULTS_R5_PLANM_pass1.tsv, tree F (36 M=2 plan points)        -> 36
#   R4SEAM   : registries/s4r4/RESULTS_R4.tsv, tree F (25 main-matrix points; seam library)   -> 25
# Each point's F observed class (from its own source) is written as "obs_F_source".  Twice points set S4FMM_TWICE=slab
# explicitly in the runner (not from the map).  The map is NOT a judgement; it is the input of R6b-2 registration.
#
# Usage: python3 -I -B testing/d003/stage_s4/r6b_map_all.py OUT_TSV
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
REG = os.path.join(REPO, "checkpoints", "p05", "registries")


def rows_with_lines(path):
    """Yield (lineno, fields) for non-comment, non-empty lines; the first such line is the header."""
    header = None
    with open(path, encoding="utf-8") as fh:
        for n, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            yield n, dict(zip(header, f))


def route_of_point(pid):
    # M-<route>-<mode>-<category>-<NTH>, M2-<route>-..., R4-...
    parts = pid.split("-")
    return parts[1] if parts[0].startswith("M") and len(parts) > 1 else ""


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: r6b_map_all.py OUT_TSV")
    out = argv[1]
    rows = []

    # --- R3: 119 points from the R6-2a map (already checked by its own script; re-counted here) ---
    r3_path = os.path.join(REG, "s4r6", "MAP_R6_R3.tsv")
    r3_rows = []
    with open(r3_path, encoding="utf-8") as fh:
        header = None
        for n, raw in enumerate(fh, 1):
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            d = dict(zip(header, f))
            r3_rows.append((n, d))
    for n, d in r3_rows:
        rows.append({
            "point_id": d["point_id"], "source": "R3", "source_file": "registries/s4r6/MAP_R6_R3.tsv",
            "source_line": str(n), "tree": "F", "route": d["route"], "mode": d["mode"],
            "category": d["category"], "nth": d["nth"], "request": d["request"], "inj_call": d["inj_call"],
            "twice": d["twice"], "obs_F_source": d["observed_r3"], "expect_F_source": d["expected_class"],
            "r1_id": "", "nth_K": "", "M": "",
        })

    # --- R4 plancall: 22 F points ---
    pc_path = os.path.join(REG, "s4r4", "RESULTS_R4_PLANCALL_pass1.tsv")
    for n, d in rows_with_lines(pc_path):
        if d["tree"] != "F":
            continue
        rows.append({
            "point_id": d["point_id"], "source": "R4PC", "source_file": "registries/s4r4/RESULTS_R4_PLANCALL_pass1.tsv",
            "source_line": str(n), "tree": "F", "route": d["route"], "mode": d["mode"], "category": "plan",
            "nth": "", "request": d["request"], "inj_call": d["inj_call"],
            "twice": "slab" if d["route"] == "twice" else "-", "obs_F_source": d["observed"],
            "expect_F_source": d["expected"], "r1_id": "", "nth_K": d["nth_K"], "M": d["M"],
        })

    # --- R5 M=2: 36 F points ---
    m2_path = os.path.join(REG, "s4r5", "RESULTS_R5_PLANM_pass1.tsv")
    for n, d in rows_with_lines(m2_path):
        if d["tree"] != "F":
            continue
        rows.append({
            "point_id": d["point_id"], "source": "R5M2", "source_file": "registries/s4r5/RESULTS_R5_PLANM_pass1.tsv",
            "source_line": str(n), "tree": "F", "route": d["route"], "mode": d["mode"], "category": "plan",
            "nth": "", "request": d["request"], "inj_call": d["inj_call"],
            "twice": "slab" if d["route"] == "twice" else "-", "obs_F_source": d["observed"],
            "expect_F_source": d["expected"], "r1_id": "", "nth_K": d["nth_K"], "M": d["M"],
        })

    # --- R4 main matrix seam: 25 F points ---
    seam_path = os.path.join(REG, "s4r4", "RESULTS_R4.tsv")
    for n, d in rows_with_lines(seam_path):
        if d["tree"] != "F":
            continue
        rows.append({
            "point_id": d["point_id"], "source": "R4SEAM", "source_file": "registries/s4r4/RESULTS_R4.tsv",
            "source_line": str(n), "tree": "F", "route": "seam", "mode": d["mode"], "category": d["family"],
            "nth": "", "request": d["request"], "inj_call": "NA", "twice": "-",
            "obs_F_source": d["obs_pass1"], "expect_F_source": d["expected"], "r1_id": d["r1_id"],
            "nth_K": "", "M": "",
        })

    counts = {}
    for r in rows:
        counts[r["source"]] = counts.get(r["source"], 0) + 1
    total = len(rows)
    if total != 202 or counts != {"R3": 119, "R4PC": 22, "R5M2": 36, "R4SEAM": 25}:
        raise SystemExit("REFUSED: map count mismatch: total=%d counts=%s (expected 202: R3 119, R4PC 22, R5M2 36, R4SEAM 25)"
                         % (total, counts))
    ids = [r["point_id"] for r in rows]
    if len(set(ids)) != len(ids):
        dup = sorted({x for x in ids if ids.count(x) > 1})
        raise SystemExit("REFUSED: duplicate point_id in map: %s" % dup[:10])

    cols = ["point_id", "source", "source_file", "source_line", "tree", "route", "mode", "category", "nth", "nth_K", "M",
            "request", "inj_call", "twice", "expect_F_source", "obs_F_source", "r1_id"]
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# MAP_R6b_ALL.tsv -- P05-S4 R6b-2 point map (202 points, tree F).  Sources and line numbers in columns.\n")
        fh.write("# obs_F_source / expect_F_source are the values of the SOURCE table (not a judgement of R6b).\n")
        fh.write("\t".join(cols) + "\n")
        for r in rows:
            fh.write("\t".join(r.get(c, "") for c in cols) + "\n")
    print("total=%d counts=%s" % (total, counts))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
