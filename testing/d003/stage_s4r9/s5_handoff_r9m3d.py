#!/usr/bin/env python3
# s5_handoff_r9m3d.py -- de-duplicated P05-S5 handoff list (U355). One row per unique transferred item, with the
# ledger id(s) and STATE row(s) it maps to. The script checks both directions and exits non-zero on any orphan:
#   direction 1: every TRANSFERRED_S5 id in the corrected ledger appears in the table;
#   direction 2: every table item maps to at least one ledger id or STATE row.
# All tables are read by column name. New file (r9m3d).
# usage: s5_handoff_r9m3d.py [OUT.tsv] [--ledger PATH] [--ledger-m3c PATH] [--state PATH]
import os, sys, re
REPO = os.getcwd()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3d")
REG = os.path.join(REPO, "checkpoints/p05/registries")
LEDGER = os.path.join(EV, "RED_POINTS_LEDGER_FINAL_R9M3D.tsv")
LEDGER_M3C = os.path.join(REG, "s4r9/M3c/RED_POINTS_LEDGER_FINAL_R9M3C.tsv")
HANDOFF_M3C = os.path.join(REG, "s4r9/M3c/S5_HANDOFF_R9M3C.tsv")
STATE = os.path.join(REPO, "checkpoints/p05/STATE.md")
TAB = chr(9)
NL = chr(10)

# The seven unique S5 items after de-duplication. source_ruling is the ruling that caused the transfer; for facts
# without a U-number the cell says so explicitly (never a STATE-row back-reference in the ruling column).
ITEMS = [
    ("S5-M3D-01", "B 侧 jones/vl SILENT、nv CRASH", "S5（基线观察，不是修复证据）",
     "-（事实项：B 列不是修复证据）", "RP-R6d-6", "STATE §3「B 侧 jones/vl SILENT、nv CRASH」"),
    ("S5-M3D-02", "NB=1–8、类别 C", "S5（M2-07 81 点全 MATCH；M2-08 转 S5）",
     "U249", "RP-R6d-16;RP-R6d-17", "STATE §3「NB=1–8、类别 C」"),
    ("S5-M3D-03", "ES3R4-5/528/1164", "S5（OUT_OF_SCOPE_D003）",
     "U90/U95/U99/U100", "-", "STATE §3「ES3R4-5/528/1164」"),
    ("S5-M3D-04", "非 FMM S4_malloc（约 35–43 处）", "S5（范围决策）",
     "-（事实项：范围决策）", "RP-R6d-18", "STATE §3「非 FMM S4_malloc（约 35–43 处）」"),
    ("S5-M3D-05", "U2 stage e（I1 特殊规则）", "S5（NOT_FOUND_IN_SCOPE）",
     "U248", "-", "STATE §3「U2 stage e（I1 特殊规则）」"),
    ("S5-M3D-06", "RP-R6d-3 no-TWICE 路径（OUT_OF_SCOPE_D003）", "S5（OUT_OF_SCOPE_D003）",
     "OUT_OF_SCOPE_D003", "RP-R6d-3", "-"),
    ("S5-M3D-07", "RP-R6d-7 D016（B 侧 rc 来源未追踪）", "S5（B 侧基线观察；F 侧归 D016/D003）",
     "-（事实项：B 侧基线）", "RP-R6d-7", "-"),
]


def read_table(path):
    rows = []
    hdr = None
    if not os.path.isfile(path):
        return hdr, rows
    for line in open(path, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f and f[0] == hdr[0]:
            continue
        rows.append(dict(zip(hdr, f)))
    return hdr, rows


def norm(name):
    s = name.replace(chr(96), "")
    s = s.replace("（", "(").replace("）", ")")
    s = re.sub(r"\([^()]*\)", "", s)
    s = re.sub(r"[\s、，,。:：;；·]", "", s)
    s = s.lower().replace("silent_swallow", "silent")
    return s


def main():
    args = sys.argv[1:]
    out = os.path.join(EV, "S5_HANDOFF_R9M3D.tsv")
    ledger = LEDGER
    i = 0
    pos = []
    while i < len(args):
        if args[i] == "--ledger" and i + 1 < len(args):
            ledger = args[i + 1]; i += 2
        elif args[i] == "--state" and i + 1 < len(args):
            global STATE
            STATE = args[i + 1]; i += 2
        elif args[i] == "--out" and i + 1 < len(args):
            out = args[i + 1]; i += 2
        else:
            pos.append(args[i]); i += 1
    if pos:
        out = pos[0]
    if not os.path.isfile(ledger):
        print("HARD_STOP missing ledger " + ledger)
        return 2
    hdr, drows = read_table(ledger)
    if not hdr or "id" not in hdr or "current_status" not in hdr:
        print("HARD_STOP ledger missing columns")
        return 2
    t5 = set(r["id"] for r in drows if r["current_status"] == "TRANSFERRED_S5")
    # direction 1
    covered = set()
    for it in ITEMS:
        for rid in it[4].split(";"):
            rid = rid.strip()
            if rid and rid != "-":
                covered.add(rid)
    missing = sorted(t5 - covered)
    extra = sorted(covered - t5)
    if missing or extra:
        print("HARD_STOP handoff bidirectionality: missing_from_handoff=%s not_transferred_in_ledger=%s" % (
            missing, extra))
        return 3
    # direction 2: each item must map to a ledger id or a STATE row
    bad = [it[0] for it in ITEMS if (it[4].strip() in ("", "-")) and (it[5].strip() in ("", "-"))]
    if bad:
        print("HARD_STOP items without ledger id or STATE row: %s" % bad)
        return 3
    # provenance: the five canonical names that the M3c handoff held must all be present (no invented items)
    h_hdr, h_rows = read_table(HANDOFF_M3C)
    if not h_rows:
        print("HARD_STOP missing M3c handoff input")
        return 2
    m3c_names = []
    for r in h_rows:
        it = r.get("item", "")
        if it:
            m3c_names.append(norm(it))
    m3c_unique = sorted(set(m3c_names))
    if len(h_rows) != 10 or len(m3c_unique) != 5:
        print("HARD_STOP M3c handoff dedupe facts changed: rows=%d unique=%d" % (len(h_rows), len(m3c_unique)))
        return 3
    ours = set(norm(it[1]) for it in ITEMS)
    absent = [n for n in m3c_unique if n not in ours]
    if absent:
        print("HARD_STOP M3c handoff canonical items not covered: %s" % absent)
        return 3
    lines = ["# S5_HANDOFF_R9M3D.tsv -- de-duplicated P05-S5 handoff (U355): one row per unique item",
             "# columns: item_id, canonical_name, scope, source_ruling, ledger_ids, state_rows",
             "# ledger TRANSFERRED_S5 ids covered: %d (%s)" % (len(t5), ",".join(sorted(t5))),
             "# unique items=%d rows=%d (M3c handoff had %d data rows -> %d unique canonical names)" % (
                 len(ITEMS), len(ITEMS), len(h_rows), len(m3c_unique)),
             TAB.join(["item_id", "canonical_name", "scope", "source_ruling", "ledger_ids", "state_rows"])]
    for it in ITEMS:
        lines.append(TAB.join(it))
    lines.append("# UNIQUE=%d ROWS=%d" % (len(ITEMS), len(ITEMS)))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(NL.join(lines) + NL)
    print("ledger_transferred_s5=%d handoff_unique=%d bidirectional=OK" % (len(t5), len(ITEMS)))
    print("WROTE " + out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
