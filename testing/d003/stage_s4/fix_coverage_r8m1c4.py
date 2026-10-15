#!/usr/bin/env python3
# fix_coverage_r8m1c4.py -- P05-S4 R8 M1c4 fix coverage of the 22 ADDITIONS rows (U225). New file.
# Join rule (U225): ADD22-<A|B>-<n>-<tree>: n equals the 'row' of ADDITIONS_MAPPING_22_R8_M1a6.tsv.
# Check (U225): the env of the ADD22 row must equal, key by key (FMM_MODE, S4FMM_NG, S4FMM_INJECT),
# the env derived from the mapping row (point_or_combo = <mode>-ng<NG>, injection = S4FMM_INJECT;
# injection 'none' means no S4FMM_INJECT key). A mismatch marks the row MAP_ENV_MISMATCH (not counted).
# Output: $EV/FIX_COVERAGE_M1_R8_M1c4.tsv
# Run: sh testing/d003/safe_run.sh p05-s4r8/m1c4 -- python3 -I -B testing/d003/stage_s4/fix_coverage_r8m1c4.py
import os
import re
import sys
from collections import Counter, defaultdict

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c4")
REG = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8")
MAP = os.path.join(REG, "M1a", "ADDITIONS_MAPPING_22_R8_M1a6.tsv")
PRE = os.path.join(REG, "M1a", "REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv")
EFF = os.path.join(REG, "M1b", "r8m1b3", "EFFECTIVE_M1B_R8_M1b3.tsv")
RES = os.path.join(REG, "M1b", "r8m1b1", "RESULTS_M1B_R8_M1b1.tsv")
OUT = os.path.join(EV, "FIX_COVERAGE_M1_R8_M1c4_R2.tsv")  # _R2: the first version (FIX_COVERAGE_M1_R8_M1c4.tsv) is void (U17)

ADD_RE = re.compile(r"^ADD22-([AB])-(\d+)-(F[23])$")
ADD_CTRL = re.compile(r"^ADD22-([AB])-(control|control)-(F[23])$")  # not used by the data; kept for clarity


def read_tsv(path, header_first):
    rows = []
    header = None
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if header is None:
                if parts[0] != header_first:
                    raise SystemExit("unexpected header in %s: %s" % (path, parts[0]))
                header = parts
                continue
            rows.append(parts)
    return header, rows


def env_dict(s):
    d = {}
    for item in s.split(";"):
        if not item or "=" not in item:
            continue
        k, v = item.split("=", 1)
        d[k] = v
    return d


def mapping_env_list(point_or_combo, injection):
    """Expected env dicts for a mapping row. A single combo '<mode>-ng<N>' gives one dict. A control row
    lists several combos ('a|b|c' or 'fft/kottke x NG1,5,9'); each member is checked against the
    ADD22 row of the same control (see main). Returns None when the form is not understood."""
    if point_or_combo in ("-", ""):
        return None
    m = re.match(r"^([a-z0-9]+)-ng(\d+)$", point_or_combo)
    if m:
        d = {"FMM_MODE": m.group(1), "S4FMM_NG": m.group(2)}
        if injection != "none":
            d["S4FMM_INJECT"] = injection
        return [d]
    if "|" in point_or_combo:
        out = []
        for part in point_or_combo.split("|"):
            mm = re.match(r"^([a-z0-9]+)-ng(\d+)$", part)
            if not mm:
                return None
            d = {"FMM_MODE": mm.group(1), "S4FMM_NG": mm.group(2)}
            if injection != "none":
                d["S4FMM_INJECT"] = injection
            out.append(d)
        return out
    return None


def main():
    map_header, map_rows = read_tsv(MAP, "row")
    mh = {h: i for i, h in enumerate(map_header)}
    mapping = {}
    for r in map_rows:
        mapping[int(r[mh["row"]])] = {
            "item": r[mh["item"]],
            "tree": r[mh["tree"]],
            "point_or_combo": r[mh["point_or_combo"]],
            "injection": r[mh["injection"]],
            "expected_class": r[mh["expected_class"]],
            "expected_rc1": r[mh["expected_rc1"]],
        }

    pre_header, pre_rows = read_tsv(PRE, "group")
    ph = {h: i for i, h in enumerate(pre_header)}
    pre = {}
    for r in pre_rows:
        if r[ph["group"]] != "ADDITIONS_22":
            continue
        pre[r[ph["point_id"]]] = {
            "env": r[ph["env"]],
            "exp_rc1": r[ph["expected_rc1"]],
        }

    eff_header, eff_rows = read_tsv(EFF, "row_id")
    eh = {h: i for i, h in enumerate(eff_header)}
    eff = {}
    for r in eff_rows:
        if r[eh["group"]] != "ADDITIONS_22":
            continue
        eff[(r[eh["point_id"]], r[eh["tree"]])] = {
            "verdict": r[eh["effective_verdict"]],
            "class_p1": r[eh["effective_class_p1"]],
        }

    res_header, res_rows = read_tsv(RES, "row_id")
    rh = {h: i for i, h in enumerate(res_header)}
    res = {}
    for r in res_rows:
        if r[rh["group"]] != "ADDITIONS_22":
            continue
        res[r[rh["point_id"]]] = {
            "env": r[rh["env"]],
            "p1_rc1": r[rh["p1_rc1"]],
        }

    lines = []
    summary = defaultdict(list)  # item -> list of (tree, verdict, class_p1, map_ok)
    checks = Counter()

    point_ids = sorted(pre.keys())
    for pid in point_ids:
        m = ADD_RE.match(pid)
        if not m:
            raise SystemExit("unexpected ADD22 point_id: %s" % pid)
        sub, n, tree = m.group(1), int(m.group(2)), m.group(3)
        mrow = mapping.get(n)
        if mrow is None:
            raise SystemExit("no mapping row for n=%d" % n)
        env_pre = env_dict(pre[pid]["env"])
        env_as = env_dict(res[pid]["env"]) if pid in res else {}
        item = mrow["item"]
        keys = ("FMM_MODE", "S4FMM_NG", "S4FMM_INJECT")
        # env check (U225): the ADD22 env must equal, key by key, one expected env of the mapping row.
        # Single-combo rows: exactly that env. Control rows listing several combos ('a|b|c'): equal to one member.
        members = mapping_env_list(mrow["point_or_combo"], mrow["injection"])
        if members is None:
            map_ok = "MAP_UNCHECKABLE_COMBO"
        else:
            got = {k: env_pre.get(k) for k in keys if k in env_pre}
            ok = any({k: v for k, v in m.items()} == got for m in members)
            map_ok = "MAP_OK" if ok else "MAP_ENV_MISMATCH"
        # the injection 'none' control rows must carry no S4FMM_INJECT key
        if mrow["injection"] == "none" and "S4FMM_INJECT" in env_pre:
            map_ok = "MAP_ENV_MISMATCH"
        # B-control ('fft/kottke x NG1,5,9'): mode in {fft, kottke} and NG in {1,5,9}, no injection
        if mrow["point_or_combo"].startswith("fft/kottke x NG"):
            ok = env_pre.get("FMM_MODE") in ("fft", "kottke") and env_pre.get("S4FMM_NG") in ("1", "5", "9") and "S4FMM_INJECT" not in env_pre
            map_ok = "MAP_OK" if ok else "MAP_ENV_MISMATCH"
        checks[map_ok] += 1
        eff_row = eff.get((pid, tree), {"verdict": "NA", "class_p1": "NA"})
        lines.append((n, item, pid, tree, env_pre, map_ok, eff_row["verdict"], eff_row["class_p1"],
                      res.get(pid, {}).get("p1_rc1", "NA"), mrow["expected_class"], mrow["expected_rc1"]))
        summary[item].append((tree, eff_row["verdict"], eff_row["class_p1"], map_ok))

    if os.path.exists(OUT):
        raise SystemExit("REFUSED exists (U17): %s" % OUT)
    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# FIX_COVERAGE_M1_R8_M1c4 -- fix coverage of ADD22 (U225). Join: ADD22 n = mapping row. "
                 "F3 rows are the coverage; F2 rows are the pre-fix regression baseline (not repair evidence).\n")
        fh.write("# part 1: per-row table\n")
        fh.write("n\titem\tpoint_id\ttree\tenv\tmap_check\teffective_verdict\teffective_class_p1\tp1_rc1\tmapping_expected_class\tmapping_expected_rc1\n")
        for ln in lines:
            n, item, pid, tree, env_pre, map_ok, verdict, cls, rc1, mexp, mrc1 = ln
            env_s = ";".join("%s=%s" % (k, env_pre[k]) for k in sorted(env_pre))
            fh.write("%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (n, item, pid, tree, env_s, map_ok, verdict, cls, rc1, mexp, mrc1))
        fh.write("# part 2: per-item summary (F3 coverage; F2 baseline distribution)\n")
        fh.write("item\tF3_rows\tF3_MATCH\tF3_classes\tF2_rows\tF2_class_distribution\tmap_check_all_ok\tinvariants_I1_I6\tstatus\n")
        by_item = defaultdict(list)
        for ln in lines:
            by_item[ln[1]].append(ln)
        for item in sorted(by_item):
            rows = by_item[item]
            f3 = [r for r in rows if r[3] == "F3"]
            f2 = [r for r in rows if r[3] == "F2"]
            f3_match = sum(1 for r in f3 if r[6] == "MATCH")
            f3_cls = Counter(r[7] for r in f3)
            f2_cls = Counter(r[7] for r in f2)
            map_all = all(r[5] == "MAP_OK" for r in rows)
            covered = (len(f3) > 0 and f3_match == len(f3) and map_all)
            if item == "A-U96":
                # U96 belongs to U100 (transferred to P05-S5, U225); it is not an M1 fix coverage item
                status = "NOT_IN_M1_FIX_SCOPE_U96_TO_S5"
            elif item.endswith("control"):
                # control rows are controls, not fix items; the map check is reported as is
                status = "CONTROL_ROW_NOT_A_FIX"
            elif covered:
                status = "COVERED_IN_M1_RC_CLASS"
            else:
                status = "NOT_COVERED_IN_M1"
            fh.write("%s\t%d\t%d\t%s\t%d\t%s\t%s\tNOT_MEASURED_IN_M1\t%s\n" % (
                item, len(f3), f3_match,
                ",".join("%s:%d" % (k, f3_cls[k]) for k in sorted(f3_cls)),
                len(f2),
                ",".join("%s:%d" % (k, f2_cls[k]) for k in sorted(f2_cls)),
                "YES" if map_all else "NO",
                status))
        fh.write("# map check counts\n")
        for k in sorted(checks):
            fh.write("MAPCHECK\t%s\t%d\n" % (k, checks[k]))
        fh.write("# note: F2 rows are the pre-fix baseline; a F2 row is not repair evidence.\n")
    for item in sorted(summary):
        rs = summary[item]
        f3 = [r for r in rs if r[0] == "F3"]
        print("%s F3=%d MATCH=%d" % (item, len(f3), sum(1 for r in f3 if r[1] == "MATCH")))
    print("MAPCHECK %s" % dict(checks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
