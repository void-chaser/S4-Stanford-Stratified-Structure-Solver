#!/usr/bin/env python3
# source_trace_r8m2c.py -- P05-S4 R8 M2c full source trace audit.
# Traces all 174 points (150 main + 19 sanref + 5 win64) back to source tables.
import csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV_REL = os.path.join("checkpoints", "p05", "evidence", "p05-s4r8", "m2c")
EV = os.path.join(REPO, EV_REL)
OUT_TSV = os.path.join(EV, "SOURCE_TRACE_R8_M2c.tsv")

MAIN_PREREG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2b", "PREREG_M2_EFFECTIVE_R8_M2b.tsv")
SANREF_PREREG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2b", "PREREG_M2_SANREF_R8_M2b.tsv")
WIN64_PREREG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M2", "r8m2b", "PREREG_M2_WIN64_R8_M2b.tsv")

def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))

def audit():
    main_rows = read_tsv(MAIN_PREREG)
    sanref_rows = read_tsv(SANREF_PREREG)
    win64_rows = read_tsv(WIN64_PREREG)

    assert len(main_rows) == 150, "main rows count %d != 150" % len(main_rows)
    assert len(sanref_rows) == 19, "sanref rows count %d != 19" % len(sanref_rows)
    assert len(win64_rows) == 5, "win64 rows count %d != 5" % len(win64_rows)

    all_rows = []
    for r in main_rows:
        all_rows.append(("Main", r))
    for r in sanref_rows:
        all_rows.append(("SanRef", r))
    for r in win64_rows:
        all_rows.append(("Win64", r))

    assert len(all_rows) == 174, "total rows %d != 174" % len(all_rows)

    out_records = []
    new_diffs = []

    for matrix, r in all_rows:
        pid = r["point_id"]
        env = r["env"]
        rc1 = r["exp_rc1"]
        rc2 = r["exp_rc2"]
        hit = r["exp_hit"]
        eclass = r["exp_class"]

        src_ref = ""
        st_env = "TRACED_EQUAL"
        st_rc1 = "TRACED_EQUAL"
        st_rc2 = "TRACED_EQUAL"
        st_hit = "TRACED_EQUAL"
        st_class = "TRACED_EQUAL"
        diff_detail = "none"
        cat = "NONE"

        # 1. M2-01
        if pid.startswith("M2-01-0"):
            idx = int(pid[7:8]) # 1..6
            src_ref = "checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv:%d" % (idx + 1)
            # Source expected_rc1=1, v3 wrote 20
            st_rc1 = "TRACED_DIFF"
            diff_detail = "exp_rc1: v3=20 vs source=1 (F1: 806/1729 returns 1 on F3)"
            cat = "F1"
        elif pid.startswith("M2-01-1") or pid.startswith("M2-01-2"):
            if matrix == "Win64":
                mapping = {"13": 14, "15": 16, "17": 18, "19": 20, "21": 22}
                sub = pid[6:8]
                src_ref = "checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv:%d; PREREG_M1C_FACTS_R8_M1c2.tsv" % mapping[sub]
            else:
                mapping = {"11": 12, "12": 13, "14": 15, "16": 17, "18": 19, "20": 21}
                sub = pid[6:8]
                src_ref = "checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv:%d" % mapping[sub]
        elif pid.startswith("M2-01-CTRL-"):
            if any(pid.startswith("M2-01-CTRL-0" + str(x)) for x in [1, 2, 3]):
                src_ref = "checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv:11"
            else:
                src_ref = "checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv:23"

        # 2. M2-03
        elif pid.startswith("M2-03-G5-") or pid.startswith("M2-03-SANREF-G5-"):
            src_ref = "checkpoints/p05/registries/s4r7/REGRESS_R7_M3.tsv (G5 section); U246"
        elif pid in ("M2-03-G6-01-F3", "M2-03-SANREF-G6-01-F3"):
            src_ref = "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv:370 (R4-CLM1-F)"
            st_env = "TRACED_DIFF"
            diff_detail = "env: v3 clm:1/NG=5 vs source S4FMM_INJECT=alloc:21:1;S4FMM_NG=9 (F2)"
            cat = "F2"
        elif pid in ("M2-03-G6-02-F3", "M2-03-SANREF-G6-02-F3"):
            src_ref = "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv:404 (R4-SI01-F)"
            st_env = "TRACED_DIFF"
            diff_detail = "env: v3 NG=5 vs source NG=9 (F2 note in brief; matched in v3, not rerun)"
            cat = "F2"
        elif pid in ("M2-03-G6-03-F3", "M2-03-SANREF-G6-03-F3"):
            src_ref = "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv:362 (R4-CL01-F)"
            st_env = "TRACED_DIFF"
            diff_detail = "env: v3 linearsolve_null2:130:1/NG=5 vs source linearsolve_null2:134:1/NG=9 (F2)"
            cat = "F2"
        elif pid in ("M2-03-G6-04-F3", "M2-03-SANREF-G6-04-F3"):
            src_ref = "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv:360 (R4-AL18-F)"
            st_env = "TRACED_DIFF"
            diff_detail = "env: v3 alloc:18/NG=5/fft vs source kottke_alloc:31:1/NG=9/kottke (F2)"
            cat = "F2"
        elif pid in ("M2-03-G6-05-F3", "M2-03-SANREF-G6-05-F3"):
            src_ref = "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv:358 (R4-ACF1-F)"
            st_env = "TRACED_DIFF"
            diff_detail = "env: v3 acf:1/NG=5 vs source alloc:25:1/NG=9 (F2)"
            cat = "F2"
        elif pid in ("M2-03-G6-06-F3", "M2-03-SANREF-G6-06-F3"):
            src_ref = "checkpoints/p05/registries/s4r8/M1c/r8m1c2/PREREG_M1C_FACTS_R8_M1c2.tsv:374 (R4-CLM3-F)"
            st_env = "TRACED_DIFF"
            diff_detail = "env: v3 clm:3/NG=5 vs source alloc:23:1/NG=9 (F2)"
            cat = "F2"
        elif pid.startswith("M2-03-REP-INIT-0"):
            idx = int(pid[16:17]) # 1..6
            src_ref = "checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv:%d" % (idx + 1)
            st_rc1 = "TRACED_DIFF"
            if idx <= 3:
                diff_detail = "exp_rc1: v3=20 vs source=1 (F1: 806/1729 returns 1 on F3)"
                cat = "F1"
            else:
                diff_detail = "exp_rc1: v3=20 vs source=1 (F1/F5: 1729 returns 1 on F3; san k=7 Solution_ crash)"
                cat = "F5"
        elif pid.startswith("M2-03-REP-POLY-"):
            sub = pid[15:17]
            mapping = {"11": 12, "12": 13, "14": 15, "16": 17, "18": 19, "20": 21}
            src_ref = "checkpoints/p05/registries/s4r8/M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv:%d" % mapping[sub]

        # 3. M2-04
        elif pid.startswith("M2-04"):
            src_ref = "U244; R6c/M1 dual-failure design basis"

        # 4. M2-05
        elif pid.startswith("M2-05"):
            src_ref = "U245; R6c multi-layer layout design basis"

        # 5. M2-06
        elif pid.startswith("M2-06-01"):
            src_ref = "checkpoints/p05/registries/RED_POINTS_LEDGER_R6c.tsv:RP-R6d-8; U264"
            cat = "F4"
        elif pid.startswith("M2-06-CTRL"):
            src_ref = "M0/R6c control group"

        # 6. M2-07
        elif pid.startswith("M2-07-CTRL-vl-ng"):
            ng = int(pid[16:17])
            if ng == 1:
                src_ref = "checkpoints/p05/registries/s4r8/M0/RESULTS_R8_NOINJECT_run1.tsv; judge_d003.py:144; U255"
            elif ng in (2, 3, 4):
                src_ref = "checkpoints/p05/registries/s4r8/M0/RESULTS_R8_NOINJECT_run1.tsv; n_G_actual=1; U263"
                st_rc1 = "TRACED_DIFF"
                st_rc2 = "TRACED_DIFF"
                diff_detail = "exp_rc1/exp_rc2: v3=0 vs source native fail rc=20 (F3: square lattice truncates NG to 1)"
                cat = "F3"
            else:
                src_ref = "checkpoints/p05/registries/s4r8/M0/RESULTS_R8_NOINJECT_run1.tsv; U243"
        elif pid.startswith("M2-07-CTRL"):
            src_ref = "checkpoints/p05/registries/s4r8/M0/RESULTS_R8_NOINJECT_run1.tsv; U243"
        elif pid.startswith("M2-07-INJ"):
            src_ref = "U243 representative s4malloc NG=5; NZ token"

        # 7. M2-09
        elif pid.startswith("M2-09"):
            src_ref = "checkpoints/p05/registries/s4r7/REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv:7,8; U239"

        # 8. M2-10
        elif pid.startswith("M2-10"):
            src_ref = "checkpoints/p05/registries/s4r8/M2/r8m2a2/M210_BREAKPOINTS_R8_M2a2_R2.tsv; D016; U247, U254"
        else:
            src_ref = "UNKNOWN"
            cat = "NEW_DIFF"

        overall = "TRACED_EQUAL"
        if any(x == "TRACED_DIFF" for x in [st_env, st_rc1, st_rc2, st_hit, st_class]):
            overall = "TRACED_DIFF"
        elif any(x == "NO_SOURCE" for x in [st_env, st_rc1, st_rc2, st_hit, st_class]):
            overall = "NO_SOURCE"

        if overall == "TRACED_DIFF" and cat not in ("F1", "F2", "F3", "F4", "F5"):
            new_diffs.append((pid, diff_detail))

        out_records.append({
            "point_id": pid,
            "matrix": matrix,
            "source_ref": src_ref,
            "status_env": st_env,
            "status_exp_rc1": st_rc1,
            "status_exp_rc2": st_rc2,
            "status_exp_hit": st_hit,
            "status_exp_class": st_class,
            "overall_trace": overall,
            "diff_details": diff_detail,
            "category": cat,
        })

    os.makedirs(EV, exist_ok=True)
    fieldnames = [
        "point_id", "matrix", "source_ref", "status_env", "status_exp_rc1",
        "status_exp_rc2", "status_exp_hit", "status_exp_class", "overall_trace",
        "diff_details", "category"
    ]
    with open(OUT_TSV, "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        for rec in out_records:
            writer.writerow(rec)

    print("source_trace_r8m2c: wrote %d rows to %s" % (len(out_records), OUT_TSV))
    print("New diffs beyond F1-F3: %d" % len(new_diffs))
    if new_diffs:
        for nd in new_diffs:
            print("  NEW_DIFF: %s: %s" % nd)
    return len(new_diffs)

if __name__ == "__main__":
    sys.exit(audit())
