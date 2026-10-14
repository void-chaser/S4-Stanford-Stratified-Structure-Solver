#!/usr/bin/env python3
# summarize_r8m1b3.py -- P05-S4 R8 M1b3 summary tables. New file.
# Reads: PREREG_SUPP_R8_M1b3.tsv, RESULTS_SUPP_R8_M1b3.tsv (this round), ENV_AUDIT_M1B_R8_M1b2.tsv (selection),
#        VERDICT_M1B_R8_M1b1.tsv (round M1b1 verdicts, for the crosswalk and the effective table only).
# Writes into $EV only: VERDICT_SUPP_R8_M1b3.tsv, CROSSWALK_M1B1_SUPP_R8_M1b3.tsv, EFFECTIVE_M1B_R8_M1b3.tsv.
import csv, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1b3")
EV1 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1b1")
EV2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1b", "r8m1b2")
PREREG = os.path.join(EV, "PREREG_SUPP_R8_M1b3.tsv")
RES = os.path.join(EV, "RESULTS_SUPP_R8_M1b3.tsv")
AUDIT = os.path.join(EV2, "ENV_AUDIT_M1B_R8_M1b2.tsv")
VER1 = os.path.join(EV1, "VERDICT_M1B_R8_M1b1.tsv")


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    header = lines[0].split("\t")
    return [dict(zip(header, l.split("\t"))) for l in lines[1:]]


def write_tsv(path, cols, rows, comment):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write("# " + comment + "\n")
        w = csv.writer(fh, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE)
        w.writerow(cols)
        for r in rows:
            w.writerow([r.get(c, "") for c in cols])
    os.replace(tmp, path)


def main():
    prereg = read_tsv(PREREG)
    res = read_tsv(RES)
    audit = read_tsv(AUDIT)
    v1 = read_tsv(VER1)

    # Key = (group, point_id, tree). point_id alone is NOT unique: G1 and G2c share point ids.
    res_by = {(r["group"], r["point_id"], r["tree"]): r for r in res}
    v1_by = {(r["group"], r["point_id"], r["tree"]): r for r in v1}
    audit_by = {(r["group"], r["point_id"], r["tree"]): r for r in audit}

    # ----- VERDICT_SUPP -----
    # keys of the supplementary set (342)
    keys = [(r["group"], r["point_id"], r["tree"]) for r in prereg]
    if len(set(keys)) != 342 or len(res_by) != 342:
        sys.exit("key count mismatch")
    v_rows = []
    agg = {}
    for k in keys:
        r = res_by[k]
        grp, tree = r["group"], r["tree"]
        ov = r["verdict_overall"]
        assert k == (grp, r["point_id"], tree)
        agg.setdefault((grp, tree), {"MATCH": 0, "MISMATCH": 0, "NOT_REACHED_AS_EXPECTED": 0, "FLAKY": 0,
                                     "CRASH": 0, "SILENT_SWALLOW": 0, "NOT_RUN": 0})
        if r["pass_consistent"] != "YES":
            cat = "FLAKY"
        elif ov == "MATCH":
            cat = "MATCH"
        elif ov == "NOT_REACHED_AS_EXPECTED":
            cat = "NOT_REACHED_AS_EXPECTED"
        else:
            cat = "MISMATCH"
        agg[(grp, tree)][cat] += 1
        if r["p1_class"] == "CRASH":
            agg[(grp, tree)]["CRASH"] += 1
        if r["p1_class"] == "SILENT_SWALLOW":
            agg[(grp, tree)]["SILENT_SWALLOW"] += 1
        v_rows.append({"group": grp, "tree": tree, "point_id": k[1], "verdict_overall": ov,
                       "pass_consistent": r["pass_consistent"], "category_summary": cat})
    vcols = ["group", "tree", "point_id", "verdict_overall", "pass_consistent", "category_summary"]
    write_tsv(os.path.join(EV, "VERDICT_SUPP_R8_M1b3.tsv"), vcols, v_rows,
              "VERDICT_SUPP_R8_M1b3.tsv -- per-row verdicts of RESULTS_SUPP_R8_M1b3 (rows 342)")
    # group/tree aggregate appended as a second file
    arows = []
    for (grp, tree), d in sorted(agg.items()):
        arows.append({"group": grp, "tree": tree, **{k: str(v) for k, v in d.items()}})
    acols = ["group", "tree", "MATCH", "MISMATCH", "NOT_REACHED_AS_EXPECTED", "FLAKY", "CRASH", "SILENT_SWALLOW", "NOT_RUN"]
    write_tsv(os.path.join(EV, "VERDICT_SUPP_R8_M1b3_AGG.tsv"), acols, arows,
              "VERDICT_SUPP_R8_M1b3_AGG.tsv -- counts by group and tree (MATCH, MISMATCH, FLAKY, NOT_REACHED_AS_EXPECTED, CRASH, SILENT_SWALLOW)")

    # ----- CROSSWALK (342 rows: M1b1 category vs supplementary category) -----
    x_rows = []
    for k in keys:
        r = res_by[k]
        a = audit_by[k]
        m = v1_by.get(k)
        m1_ov = m["verdict_overall"] if m else "MISSING"
        m1_cls_p1 = m["actual_class_p1"] if m else "MISSING"
        m1_env = a["prereg_env"]
        x_rows.append({
            "group": r["group"], "tree": r["tree"], "point_id": k[1],
            "m1b1_env": m1_env, "m1b1_verdict": m1_ov, "m1b1_class_p1": m1_cls_p1,
            "m1b1_class_p2": m["actual_class_p2"] if m else "MISSING",
            "supp_env_as_run": r["env_as_run"], "supp_inj_call": r["inj_call"], "supp_real": r["real"],
            "supp_class_p1": r["p1_class"], "supp_class_p2": r["p2_class"],
            "supp_run_rc_p1": r["p1_run_rc"], "supp_rc1_p1": r["p1_rc1"], "supp_rc2_p1": r["p1_rc2"],
            "supp_hit_p1": r["p1_hit"], "supp_verdict_overall": r["verdict_overall"],
            "pass_consistent": r["pass_consistent"],
            "is_m1b1_silent_swallow": "YES" if m1_cls_p1 == "SILENT_SWALLOW" else "NO",
        })
    xcols = ["group", "tree", "point_id", "m1b1_env", "m1b1_verdict", "m1b1_class_p1", "m1b1_class_p2",
             "supp_env_as_run", "supp_inj_call", "supp_real", "supp_class_p1", "supp_class_p2",
             "supp_run_rc_p1", "supp_rc1_p1", "supp_rc2_p1", "supp_hit_p1", "supp_verdict_overall",
             "pass_consistent", "is_m1b1_silent_swallow"]
    write_tsv(os.path.join(EV, "CROSSWALK_M1B1_SUPP_R8_M1b3.tsv"), xcols, x_rows,
              "CROSSWALK_M1B1_SUPP_R8_M1b3.tsv -- 342 rows: M1b1 category vs supplementary category (facts from both)")

    # ----- EFFECTIVE (830 rows) -----
    eff = []
    supp_keys = set(keys)
    for r in v1:
        k = (r["group"], r["point_id"], r["tree"])
        grp = r["group"]
        if k in supp_keys:
            s = res_by[k]
            eff.append({"row_id": r["row_id"], "group": grp, "point_id": k[1], "tree": k[2],
                        "source": "SUPP_R8_M1b3", "effective_verdict": s["verdict_overall"],
                        "effective_class_p1": s["p1_class"], "effective_pass_consistent": s["pass_consistent"],
                        "effective_category": ("FLAKY" if s["pass_consistent"] != "YES" else s["verdict_overall"])})
        else:
            if r["verdict_overall"] == "NOT_RUN_AS_EXPECTED":
                src = "M1b1_NOT_RUN"
                cat = "NOT_RUN"
            else:
                src = "M1b1_ENV_AGREE"
                cat = r["verdict_overall"]
            eff.append({"row_id": r["row_id"], "group": grp, "point_id": k[1], "tree": k[2],
                        "source": src, "effective_verdict": r["verdict_overall"],
                        "effective_class_p1": r["actual_class_p1"], "effective_pass_consistent": "M1b1",
                        "effective_category": cat})
    ecols = ["row_id", "group", "point_id", "tree", "source", "effective_verdict", "effective_class_p1",
             "effective_pass_consistent", "effective_category"]
    write_tsv(os.path.join(EV, "EFFECTIVE_M1B_R8_M1b3.tsv"), ecols, eff,
              "EFFECTIVE_M1B_R8_M1b3.tsv -- 830 rows: which result is used (ENV_AGREE 488 from M1b1; 342 from supplementary run; 6 NOT_RUN)")

    # totals for the 830 rows
    tot = {}
    for e in eff:
        c = e["effective_category"]
        tot[c] = tot.get(c, 0) + 1
    print("EFFECTIVE_ROWS=%d" % len(eff))
    for k in sorted(tot):
        print("EFFECTIVE_%s=%d" % (k, tot[k]))
    src_cnt = {}
    for e in eff:
        src_cnt[e["source"]] = src_cnt.get(e["source"], 0) + 1
    print("SOURCES=%s" % src_cnt)
    print("AGG")
    for (grp, tree), d in sorted(agg.items()):
        print("%s %s %s" % (grp, tree, d))
    return 0


if __name__ == "__main__":
    sys.exit(main())
