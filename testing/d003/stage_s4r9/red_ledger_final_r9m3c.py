#!/usr/bin/env python3
# red_ledger_final_r9m3c.py -- consolidate every committed red-point ledger under checkpoints/p05/registries into one
# final table (one row per red point), with legacy-id de-duplication, latest-ruling status and conflicts at the tail.
# All tables are read by column name. New file (r9m3c).
# usage: red_ledger_final_r9m3c.py [OUT.tsv]
import os, sys, glob, re
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3c")
REG = os.path.join(REPO, "checkpoints/p05/registries")
TAB = chr(9)
NL = chr(10)
OUT = os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3C.tsv")
RANK = {"s4r6c": 10, "s4r6d": 20, "s4r8/M2/r8m2c": 30, "s4r8/M2/r8m2d": 31, "s4r8/M2/r8m2e": 32,
        "s4r9/M2": 40, "s4r9/M3b": 50}
TREE_COMMIT = {"F4": "05097a7", "F3": "8d8202a", "F2": "a07b5ac", "F": "1c11905", "B": "37a82e8", "A": "876181c", "H": "64eb0b5"}
# legacy R6c ids that the R6d ledger explicitly maps to RP-R6d-* (the R6d ledger rows say "mapping of R6c ...")
LEGACY = {
    "RP-R5-2": "RP-R6d-3", "RP-R5-3": "RP-R6d-4", "RP-R5-4": "RP-R6d-5", "E6-3": "RP-R6d-4",
    "E6-4": "RP-R6d-3", "E6-8": "RP-R6d-9", "E6-8-U11": "RP-R6d-10", "U14-OBS": "RP-R6d-11",
    "E6c-6": "RP-R6d-12", "RNV1": "RP-R6d-1", "B-SS-JV": "RP-R6d-6", "DUAL-I7": "RP-R6d-13",
    "OTHER-LAYER": "RP-R6d-14", "R7-PY-LUA": "RP-R6d-15", "R7-NB18": "RP-R6d-16", "R7-CAT-C": "RP-R6d-17",
    "R7-D016-B": "RP-R6d-7", "S5-MALLOC": "RP-R6d-18", "RS-177": "RP-R6d-19", "RS-SEAM": "RP-R6d-20",
}
RES = {
    "RP-R5-1": ("CLOSED", "U1", "已关闭（U1）"),
    "RP-R6d-1": ("CLOSED", "U25", "已关闭（RNV1：F2/F3/F4 全部 MATCH）"),
    "RP-R6d-2": ("CLOSED", "U1", "已关闭（U1）"),
    "RP-R6d-3": ("TRANSFERRED_S5", "OUT_OF_SCOPE_D003", "S5（OUT_OF_SCOPE_D003，已记录）"),
    "RP-R6d-4": ("CLOSED", "CLOSED_BY_RULING", "已关闭"),
    "RP-R6d-5": ("CLOSED", "CLOSED_BY_RULING", "已关闭"),
    "RP-R6d-6": ("TRANSFERRED_S5", "S5", "S5（B 侧基线观察，不是修复证据）"),
    "RP-R6d-7": ("TRANSFERRED_S5", "S5", "S5（B 侧基线观察；F 侧归 D016/D003）"),
    "RP-R6d-8": ("CLOSED", "U274/U281", "已关闭（张量路径 K-1，带范围声明）"),
    "RP-R6d-9": ("CLOSED", "U8/U11", "已关闭（I2 注释）"),
    "RP-R6d-10": ("CLOSED", "U31", "已关闭（S4_internal.h:263 注释）"),
    "RP-R6d-11": ("NO_RED_POINT", "-", "非红点（observation）"),
    "RP-R6d-12": ("CLOSED", "CLOSED_BY_RULING", "已关闭"),
    "RP-R6d-13": ("CLOSED", "U9/U25", "已关闭（R8 完成）"),
    "RP-R6d-14": ("TRANSFERRED_S5", "U20", "S5（other-layer 失败变体）"),
    "RP-R6d-15": ("CLOSED", "U345", "带范围声明关闭（U345；条件为 S-B 复核一致）"),
    "RP-R6d-16": ("TRANSFERRED_S5", "U249", "S5（M2-07 81 点 MATCH；M2-08 转 S5）"),
    "RP-R6d-17": ("TRANSFERRED_S5", "U249", "S5（类别 C：M2-08 转 S5）"),
    "RP-R6d-18": ("TRANSFERRED_S5", "范围决策", "S5（非 FMM S4_malloc 登记）"),
    "RP-R6d-19": ("NO_RED_POINT", "-", "非红点（observation 177）"),
    "RP-R6d-20": ("NO_RED_POINT", "-", "非红点（observation 25 seam）"),
    "RP-R8-M2c-1": ("CLOSED", "U304/U350", "已关闭（U304；U350 确认）"),
    "RP-R8-M2c-1b": ("CLOSED", "U304/U350", "已关闭（U304；U350 确认）"),
    "K-1": ("CLOSED", "U274/U281", "已关闭（U274/U281）"),
    "RP-R9M3B-NONE": ("NO_RED_POINT", "-", "无新红点"),
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
        rows.append(dict(zip(hdr, f)))
    return hdr, rows


def pick(row, names, default=""):
    for n in names:
        if n in row and row[n] != "":
            return row[n]
    return default


def rank_of(rel):
    for key, r in RANK.items():
        if rel.startswith("checkpoints/p05/registries/" + key + "/"):
            return r, key
    return 0, rel


def main():
    files = sorted(glob.glob(os.path.join(REG, "**", "RED_POINTS_LEDGER*.tsv"), recursive=True))
    file_rows = []
    occ = {}
    for f in files:
        rel = os.path.relpath(f, REPO)
        hdr, rows = read_table(f)
        rk, key = rank_of(rel)
        n_data = len([l for l in open(f, encoding="utf-8") if l.strip() and not l.startswith("#")])
        file_rows.append((rel, n_data, rk))
        for row in rows:
            rid = pick(row, ["id"], "")
            if not rid:
                continue
            canon = LEGACY.get(rid, rid)
            occ.setdefault(canon, []).append({
                "legacy_id": rid, "file": rel, "rank": rk,
                "round": pick(row, ["source_round", "r6c_id"], "") or key.upper(),
                "site": pick(row, ["site", "location"]),
                "tree": pick(row, ["tree"]),
                "evidence": pick(row, ["evidence"]),
                "status": pick(row, ["status", "aux_status"]),
                "destination": pick(row, ["destination", "repair_destination_proposal"]),
            })
    u345_ok = False
    cmp_p = os.path.join(EV, "REJUDGE_COMPARE_R9M3C.txt")
    if os.path.isfile(cmp_p):
        for line in open(cmp_p, encoding="utf-8"):
            if line.startswith("DIFFS="):
                u345_ok = (line.strip() == "DIFFS=0")
    out_rows = []
    conflicts = []
    open_in_scope = 0
    for canon in sorted(occ):
        o = sorted(occ[canon], key=lambda x: x["rank"])
        first, last = o[0], o[-1]
        tree = last["tree"]
        commit = ""
        for k, v in TREE_COMMIT.items():
            if tree.startswith(k):
                commit = v
                break
        if canon in RES:
            status, ruling, dest = RES[canon]
        else:
            status = "OPEN" if ("OPEN" in last["status"] or "DEFERRED" in last["status"]) else last["status"]
            ruling = ", ".join(sorted(set(re.findall(r"U\d+", " ".join([last["evidence"], last["destination"], last["status"]]))))) or "-"
            dest = last["destination"] or last["status"]
        if canon == "RP-R6d-15" and not u345_ok:
            status, ruling, dest = "OPEN", "U345（未生效）", "S-B 复核存在差异，U345 关闭未生效"
        if status in ("OPEN", "DEFERRED") and "S5" not in dest:
            open_in_scope += 1
        raw = [x["status"] for x in o]
        if len(set(raw)) > 1:
            conflicts.append((canon, "|".join(sorted(set(raw))), ruling, dest))
        evid = (last["evidence"][:300] + "...") if len(last["evidence"]) > 300 else last["evidence"]
        out_rows.append((canon, first["round"], last["site"], "tree=%s commit=%s" % (tree, commit or "-"), evid, ruling, status, dest))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("# RED_POINTS_LEDGER_FINAL_R9M3C.tsv -- consolidated red-point ledger (one row per id)" + NL)
        fh.write("# input ledgers (path, data lines, rank):" + NL)
        for rel, n, rk in file_rows:
            fh.write("#   %s\tlines=%d\trank=%d" % (rel, n, rk) + NL)
        fh.write("# dedup rule: same id across ledgers -> one row; legacy R6c ids mapped to the R6d ids that the R6d ledger" + NL)
        fh.write("#   explicitly records as its mapping; first_round from the earliest ledger by rank." + NL)
        fh.write("# status/destination: latest ledger plus canonical ruling resolution (U1, U8/U11, U25/U31, U249, U274/U281, U304/U350, U345)." + NL)
        fh.write(TAB.join(["id", "first_round", "location", "repair_commit_tree", "post_fix_evidence", "closing_ruling", "current_status", "destination"]) + NL)
        for r in out_rows:
            fh.write(TAB.join(str(x) for x in r) + NL)
        fh.write("# CONFLICTS: same id with different raw status across ledgers: %d" % len(conflicts) + NL)
        for canon, raw, ruling, dest in conflicts:
            fh.write("# CONFLICT\t%s\traw=%s\tresolved_by=%s\tdestination=%s" % (canon, raw, ruling, dest) + NL)
        fh.write("# OPEN_IN_SCOPE=%d" % open_in_scope + NL)
        fh.write("# NO_RED_POINT_ROWS=%d" % len([r for r in out_rows if r[6] == "NO_RED_POINT"]) + NL)
    print("input_ledgers=%d ids=%d conflicts=%d open_in_scope=%d" % (len(files), len(out_rows), len(conflicts), open_in_scope))
    print("WROTE " + OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
