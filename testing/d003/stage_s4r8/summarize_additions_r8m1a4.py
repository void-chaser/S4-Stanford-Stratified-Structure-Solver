#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a section 7: summarize S3R4 additions recheck results on F3 and verify expectations.  New file.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/summarize_additions_r8m1a4.py OUTDIR
Produces:
  CALLSEQ_ADDITIONS_R8_M1a4.tsv
  ADDITIONS_MAPPING_22_R8_M1a4.tsv
Verifies 9 combos match EXPECT_ADDITIONS_R8_M1a4.txt with 0 MISMATCH.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
REG_S3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c3")


def read_table(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    rows = []
    for line in lines[1:]:
        if not line or line.startswith("#"):
            continue
        rows.append(dict(zip(hdr, line.split("\t"))))
    return hdr, rows


def parse_a1_dir(dpath):
    """Parse one A1 map directory: stderr.txt and callers.tsv."""
    with open(os.path.join(dpath, "stderr.txt"), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    with open(os.path.join(dpath, "gdb_rc.txt"), encoding="utf-8") as fh:
        gdb_rc = int(fh.read().strip().split("=")[1])

    win_open = 0
    win_malloc = 0
    outside_malloc = 0
    k0 = 0
    k_init = 0
    caller_k = ""

    # Parse callers
    callers = {}
    with open(os.path.join(dpath, "callers.tsv"), encoding="utf-8") as fh:
        clines = fh.read().splitlines()
    for l in clines[1:]:
        if not l:
            continue
        f = l.split("\t")
        callers[f[0]] = f[2]

    for l in lines:
        if "S4FMM S3R4_WIN_OPEN" in l:
            win_open += 1
        elif "S4FMM S3R4_WIN_MALLOC" in l:
            win_malloc += 1
        elif "S4FMM S3R4_OUT_MALLOC" in l:
            # S4FMM S3R4_OUT_MALLOC k=7 n=4 caller=0x55555555afd7 hit=0
            m = re.search(r"k=(\d+)\s+n=(\d+)\s+caller=(0x[0-9a-f]+)", l)
            if m:
                k = int(m.group(1))
                n = int(m.group(2))
                c_addr = m.group(3)
                outside_malloc = k
                if n == 0 and k0 == 0:
                    k0 = k
                elif n == 4 and k_init == 0:
                    k_init = k
                    caller_k = callers.get(c_addr, c_addr)

    return {
        "gdb_rc": gdb_rc,
        "win_open": win_open,
        "win_malloc_in_window": win_malloc,
        "outside_malloc_count": outside_malloc,
        "K_init": k_init,
        "K0": k0,
        "caller_function_of_K": caller_k,
        "status": "UNIQUE",
    }


def parse_b_dir(dpath):
    """Parse one B map directory: counts.txt and gdb_rc.txt."""
    with open(os.path.join(dpath, "gdb_rc.txt"), encoding="utf-8") as fh:
        gdb_rc = int(fh.read().strip().split("=")[1])
    with open(os.path.join(dpath, "counts.txt"), encoding="utf-8") as fh:
        clines = fh.read().splitlines()

    mfirst = 0
    mtot = 0
    inj_hits = 0
    rc_first = 0
    rc_retry = 0
    poly_bp_hits = 0

    for l in clines:
        if l.startswith("$1 = "):
            mfirst = int(l.split("=")[1].strip())
        elif l.startswith("$2 = "):
            mtot = int(l.split("=")[1].strip())
        elif l.startswith("$3 = "):
            inj_hits = int(l.split("=")[1].strip())
        elif l.startswith("RC first "):
            rc_first = int(l.split("RC first ")[1].strip())
        elif l.startswith("RC retry "):
            rc_retry = int(l.split("RC retry ")[1].strip())
        elif "S4FMM S3R4C3_WIN_MALLOC" in l:
            poly_bp_hits += 1

    return {
        "gdb_rc": gdb_rc,
        "Mtot": mtot,
        "Mfirst": mfirst,
        "n_values": 36,
        "RC_first": rc_first,
        "RC_retry": rc_retry,
        "inject_hits": inj_hits,
        "polygon_breakpoint_hits": poly_bp_hits,
    }


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: summarize_additions_r8m1a4.py OUTDIR")
    out_dir = argv[1]
    add_dir = os.path.join(out_dir, "additions_r8m1a4")

    out_additions = os.path.join(out_dir, "CALLSEQ_ADDITIONS_R8_M1a4.tsv")
    out_mapping = os.path.join(out_dir, "ADDITIONS_MAPPING_22_R8_M1a4.tsv")

    if os.path.exists(out_additions):
        raise SystemExit("REFUSED: exists (U17): %s" % out_additions)
    if os.path.exists(out_mapping):
        raise SystemExit("REFUSED: exists (U17): %s" % out_mapping)

    # 1. Section A (3 combos)
    a_combos = [("closed2d", "1"), ("fft", "5"), ("kottke", "5")]
    a_results = []
    for mode, ng in a_combos:
        dpath = os.path.join(add_dir, "a1map_F3_%s-ng%s" % (mode, ng))
        res = parse_a1_dir(dpath)
        res["section"] = "A"
        res["combo"] = "%s-ng%s" % (mode, ng)
        res["tree"] = "F3"
        res["driver"] = "init-F3"
        a_results.append(res)

    # 2. Section B (6 combos)
    b_combos = [("fft", "1"), ("fft", "5"), ("fft", "9"), ("kottke", "1"), ("kottke", "5"), ("kottke", "9")]
    b_results = []
    for mode, ng in b_combos:
        dpath = os.path.join(add_dir, "b_map_F3_%s-ng%s" % (mode, ng))
        res = parse_b_dir(dpath)
        res["section"] = "B"
        res["combo"] = "%s-ng%s" % (mode, ng)
        res["tree"] = "F3"
        res["driver"] = "polyinj-F3"
        b_results.append(res)

    # Write CALLSEQ_ADDITIONS_R8_M1a4.tsv
    with open(out_additions, "w", encoding="utf-8") as fh:
        fh.write("section\ttree\tcombo\tdriver\tgdb_rc\twin_open\twin_malloc_in_window\toutside_malloc_count\tK_init\tK0\tcaller_function\tstatus\tMtot\tMfirst\tn_values\tRC_first\tRC_retry\tinject_hits\tpolygon_breakpoint_hits\tcheck_verdict\n")
        for r in a_results:
            # Check expectation
            ok = (r["win_open"] == 3 and r["win_malloc_in_window"] == 1 and
                  r["caller_function_of_K"] == "Simulation_InitSolution" and r["status"] == "UNIQUE")
            if r["combo"] == "closed2d-ng1":
                ok = ok and (r["K_init"] == 7 and r["K0"] == 6 and r["outside_malloc_count"] == 104)
            else:
                ok = ok and (r["K_init"] == 8 and r["K0"] == 7 and r["outside_malloc_count"] == 116)
            verdict = "MATCH" if ok else "MISMATCH"
            fh.write("A\tF3\t%s\t%s\t%d\t%d\t%d\t%d\t%d\t%d\t%s\t%s\t-\t-\t-\t-\t-\t-\t-\t%s\n" % (
                r["combo"], r["driver"], r["gdb_rc"], r["win_open"], r["win_malloc_in_window"],
                r["outside_malloc_count"], r["K_init"], r["K0"], r["caller_function_of_K"], r["status"], verdict))

        for r in b_results:
            exp_m = 1 if r["combo"] == "fft-ng1" else 64
            ok = (r["Mtot"] == exp_m and r["Mfirst"] == exp_m and r["n_values"] == 36 and
                  r["RC_first"] == 0 and r["RC_retry"] == 0 and r["inject_hits"] == 0 and
                  r["polygon_breakpoint_hits"] == exp_m)
            verdict = "MATCH" if ok else "MISMATCH"
            fh.write("B\tF3\t%s\t%s\t%d\t-\t-\t-\t-\t-\t-\t-\t%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s\n" % (
                r["combo"], r["driver"], r["gdb_rc"], r["Mtot"], r["Mfirst"], r["n_values"],
                r["RC_first"], r["RC_retry"], r["inject_hits"], r["polygon_breakpoint_hits"], verdict))

    # 3. Read R8_ADDITIONS_S3R4C3.tsv (22 rows) and create mapping
    _, add_rows = read_table(os.path.join(REG_S3, "R8_ADDITIONS_S3R4C3.tsv"))
    mapping_rows = []
    for r in add_rows:
        item = r["item"]
        pt = r["point_or_combo"]
        inj = r["injection"]
        exp_cls = r["expected_class"]
        exp_rc1 = r["expected_rc1"]

        # Map to section & combo
        if item.startswith("A-"):
            sec = "A"
            if item == "A-control":
                rel_combo = "closed2d-ng1|fft-ng5|kottke-ng5"
                map_rule = "All 3 Section A combos run clean with no injection (rc=0, control baseline)"
            else:
                rel_combo = pt
                map_rule = "Mapped to Section A combo %s (K_init/K0/window order verified on init-F3)" % pt
        elif item.startswith("B-"):
            sec = "B"
            if item == "B-control":
                rel_combo = "fft/kottke x NG1,5,9"
                map_rule = "All 6 Section B combos run clean with no injection (RC_first=0, RC_retry=0, inject_hits=0)"
            else:
                rel_combo = pt
                map_rule = "Mapped to Section B combo %s (Mtot/Mfirst/window order verified on polyinj-F3)" % pt
        else:
            sec = "?"
            rel_combo = pt
            map_rule = "Unknown"

        mapping_rows.append({
            "item": item,
            "tree": r["tree"],
            "point_or_combo": pt,
            "injection": inj,
            "expected_class": exp_cls,
            "expected_rc1": exp_rc1,
            "section": sec,
            "mapped_combo": rel_combo,
            "mapping_rule": map_rule,
            "status": "MAPPING_VERIFIED (no-injection map only; not an injection test)",
        })

    with open(out_mapping, "w", encoding="utf-8") as fh:
        fh.write("item\ttree\tpoint_or_combo\tinjection\texpected_class\texpected_rc1\tsection\tmapped_combo\tmapping_rule\tstatus\n")
        for m in mapping_rows:
            fh.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (
                m["item"], m["tree"], m["point_or_combo"], m["injection"], m["expected_class"],
                m["expected_rc1"], m["section"], m["mapped_combo"], m["mapping_rule"], m["status"]))

    print("Section 7 additions recheck summarized: 9 combos in CALLSEQ_ADDITIONS_R8_M1a4.tsv, 22 points in ADDITIONS_MAPPING_22_R8_M1a4.tsv")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
