#!/usr/bin/env python3
# kmatch_r9m1r4_v2.py -- K hit count reconciliation and coverage audit (Step S-E, v2). New file.
# Baseline HEAD: 4e9ff8be523bbf52a6b11757a6e04405a4a114e9
import os, sys, csv

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r4"))

M1R3_REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R3")
M1R2_REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M1R2")

def main():
    out_dir = EV
    args = sys.argv[1:]
    if "--out-dir" in args:
        idx = args.index("--out-dir")
        if idx + 1 < len(args):
            out_dir = args[idx + 1]
    os.makedirs(out_dir, exist_ok=True)
    out_tsv = os.path.join(out_dir, "K_RECON_R9M1R4.tsv")

    # 1. Load K_COUNT_R9M1R3.tsv
    kcount = {}
    with open(os.path.join(M1R3_REG, "K_COUNT_R9M1R3.tsv"), encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        r = dict(zip(h, l))
        kcount[r["group_id"]] = r

    # 2. Load K_INHERIT_R9M1R2.tsv
    kinherit = {}
    with open(os.path.join(M1R2_REG, "K_INHERIT_R9M1R2.tsv"), encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    h = lines[0]
    for l in lines[1:]:
        r = dict(zip(h, l))
        kinherit[r["group_id"]] = r

    # 3. Load K_COVERAGE_R9M1R3.tsv
    cov_rows = []
    with open(os.path.join(M1R3_REG, "K_COVERAGE_R9M1R3.tsv"), encoding="utf-8") as f:
        lines = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
    cov_h = lines[0]
    for l in lines[1:]:
        cov_rows.append(dict(zip(cov_h, l)))

    k_points = [r for r in cov_rows if r.get("needs_k") == "YES"]
    non_k_points = [r for r in cov_rows if r.get("needs_k") == "NO"]

    assert len(cov_rows) == 651, f"Expected 651 coverage rows, got {len(cov_rows)}"
    assert len(k_points) == 416, f"Expected 416 K points, got {len(k_points)}"
    assert len(non_k_points) == 235, f"Expected 235 non-K points, got {len(non_k_points)}"

    rows = []
    mismatched_groups = 0
    diff_count = 0

    for gid in sorted(kcount.keys()):
        kc = kcount[gid]
        ki = kinherit[gid]

        k_max = int(kc["k_max"])
        c_plain = int(kc["f4_plain_hits"])
        c_kmap = int(kc["f4_kmap_hits"])
        assert c_plain == c_kmap, f"GDB count plain != kmap for {gid}"

        i_hits = int(ki["hits_f4"])
        k_max_plus_2 = k_max + 2
        exp_old_hits = min(c_plain, k_max_plus_2)

        matched = (i_hits == exp_old_hits)
        if not matched:
            mismatched_groups += 1

        is_different = (c_plain != i_hits)
        if is_different:
            diff_count += 1
            reason = f"Truncated in old table: total {c_plain} hits capped at k_max+2={k_max_plus_2}"
        else:
            reason = f"Full total {c_plain} fits within k_max+2={k_max_plus_2}"

        m1_pts = ki.get("m1_points_count", "-")
        rows.append([
            gid, kc["driver_family"], str(k_max), str(c_plain), str(i_hits),
            str(k_max_plus_2), str(exp_old_hits), "YES" if matched else "NO",
            "DIFFERENT" if is_different else "IDENTICAL", str(m1_pts), reason
        ])

    assert mismatched_groups == 0, f"Hypothesis failed for {mismatched_groups} groups!"
    assert diff_count == 13, f"Expected exactly 13 groups with count differences, got {diff_count}"

    with open(out_tsv, "w", encoding="utf-8") as f:
        f.write("# K_RECON_R9M1R4.tsv -- K hit count reconciliation across 26 groups and coverage audit (Step S-E)\n")
        f.write("# Summary: 26 groups audited; 13 groups have truncated hits in old table; all 26 match min(total, k_max+2) hypothesis; coverage 416 + 235 = 651闭环\n")
        f.write("\t".join([
            "group_id", "driver_family", "k_max", "kcount_total_hits", "kinherit_old_hits",
            "k_max_plus_2", "expected_old_hits", "hypothesis_matched",
            "count_comparison", "m1_points_count", "reconciliation_notes"
        ]) + "\n")
        for r in rows:
            f.write("\t".join(r) + "\n")

    print(f"K reconciliation completed: 26 groups, 13 diff groups reconciled, hypothesis 100% PASS -> {out_tsv}")
    return True

if __name__ == "__main__":
    main()
