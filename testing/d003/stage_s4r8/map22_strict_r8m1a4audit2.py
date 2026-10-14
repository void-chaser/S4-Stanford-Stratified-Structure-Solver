#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2), section 5 step 4: strict re-mapping of the 22 additions rows.  New file.

Read only.  Input: the 22-row table ADDITIONS_MAPPING_22_R8_M1a4.tsv (earlier round, not modified) and the v3 strict
recheck ADDITIONS_STRICT_R8_M1a4AUDIT2_<name>.tsv.  Each row is linked to its mapped combination(s); the verdict is taken
from the per-field status of the combination(s) in the v3 table, never typed:
  MAPPING_VERIFIED_STRICT   : every field of every mapped combination the row depends on is MATCH
  NOT_VERIFIED_K0           : the row depends on K0 (item A-U96, injection init:K0) and K0 is EVIDENCE_INSUFFICIENT
  NOT_VERIFIED_OTHER        : any other non-MATCH field, missing combination, NOT_UNIQUE, MISMATCH or MISSING
The row's dependency is declared by its injection request: init:K0 (A-U96) depends on K0; win:M and init:K_init depend on
the K_init, win_open and caller fields; B rows depend on the B fields.  A combination with no row in the v3 table is
NOT_VERIFIED_OTHER (never MATCH by omission).

Scope: the verdict is a no-injection mapping check only.  It is not a 22-injection verification.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/map22_strict_r8m1a4audit2.py V3_NAME MAP_NAME
V3_NAME: ADDITIONS_STRICT_R8_M1a4AUDIT2_<name>.tsv (existing).  MAP_NAME: ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_<name>.tsv (new).
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit2")
REG_M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
MAP22 = os.path.join(REG_M1A, "ADDITIONS_MAPPING_22_R8_M1a4.tsv")
V3_RE = re.compile(r"^ADDITIONS_STRICT_R8_M1a4AUDIT2_[A-Za-z0-9_]+\.tsv$")
MAP_RE = re.compile(r"^ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_[A-Za-z0-9_]+\.tsv$")


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    return hdr, [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln]


def combo_verdict(v3rows, section, combo, fields):
    """Status of one mapped combination over the given fields: MATCH only if every listed field is MATCH."""
    seen = {}
    for r in v3rows:
        if r["section"] == section and r["combo"] == combo:
            seen[r["field"]] = r["status"]
    if not seen:
        return "NO_ROW"
    for f in fields:
        st = seen.get(f)
        if st is None:
            return "FIELD_MISSING:%s" % f
        if st != "MATCH":
            return "%s:%s" % (st, f)
    return "MATCH"


def main(argv):
    if len(argv) != 3 or not V3_RE.match(argv[1]) or not MAP_RE.match(argv[2]):
        raise SystemExit("usage: map22_strict_r8m1a4audit2.py ADDITIONS_STRICT_R8_M1a4AUDIT2_<name>.tsv ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_<name>.tsv")
    v3_path = os.path.join(EV, argv[1])
    out = os.path.join(EV, argv[2])
    if not os.path.isfile(v3_path):
        raise SystemExit("REFUSED: v3 table missing")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    _, v3rows = read_tsv(v3_path)
    _, rows22 = read_tsv(MAP22)
    if len(rows22) != 22:
        raise SystemExit("REFUSED: 22-row table has %d rows" % len(rows22))

    # which fields each section's dependency needs
    # the fields of each section as written by summarize_additions_strict_r8m1a4audit2.py (K0 is not a field here:
    # it is handled separately for A-U96 below); gdb_rc(task_s5_rule) is the task section 5 check of the gdb return code
    A_FIELDS = ["win_open", "win_malloc_in_window", "outside_malloc_count", "K_init", "caller", "status",
                "gdb_rc(task_s5_rule)"]
    B_FIELDS = ["Mtot", "Mfirst", "n_values", "RC_first", "RC_retry", "inject_hits", "polygon_breakpoint_hits",
                "gdb_rc(task_s5_rule)"]

    out_rows = []
    cnt = Counter()
    for i, r in enumerate(rows22, 1):
        item = r["item"]
        inj = r["injection"]
        section = r["section"]
        # mapped_combo is one combination, or several separated by '|'.  The B control row names six combinations in
        # its mapping_rule text ("All 6 Section B combos"); they are listed here explicitly, not parsed from free text.
        combos = r["mapped_combo"].split("|")
        if section == "B" and r["point_or_combo"].startswith("fft/kottke"):
            combos = ["fft-ng1", "fft-ng5", "fft-ng9", "kottke-ng1", "kottke-ng5", "kottke-ng9"]
        # (1) every mapped combination must be MATCH on the fields of its section
        verdicts = []
        for c in combos:
            if section == "A":
                v = combo_verdict(v3rows, "A", c, A_FIELDS)
            else:
                v = combo_verdict(v3rows, "B", c, B_FIELDS)
            verdicts.append((c, v))
        combos_ok = all(v == "MATCH" for _, v in verdicts)
        # (2) init:K0 (A-U96) additionally depends on the K0 field of its combination; K0 must be MATCH
        k0_ok = True
        k0_detail = "-"
        if item == "A-U96" and inj.startswith("init:"):
            k0_status = None
            for rr in v3rows:
                if rr["section"] == "A" and rr["combo"] == combos[0] and rr["field"] == "K0":
                    k0_status = rr["status"]
            k0_detail = "K0_STATUS:%s" % k0_status
            k0_ok = (k0_status == "MATCH")
            verdicts.append((combos[0], k0_detail))
        # (3) the status of the row
        if item == "A-U96" and inj.startswith("init:") and not k0_ok:
            status = "NOT_VERIFIED_K0"
        elif combos_ok and k0_ok:
            status = "MAPPING_VERIFIED_STRICT"
        else:
            status = "NOT_VERIFIED_OTHER"
        cnt[status] += 1
        detail = "; ".join("%s=%s" % (c, v) for c, v in verdicts)
        out_rows.append((i, item, r["tree"], r["point_or_combo"], inj, r["expected_class"], r["expected_rc1"], section,
                         r["mapped_combo"], status, detail))

    with open(out, "x", encoding="utf-8") as fh:
        fh.write("row\titem\ttree\tpoint_or_combo\tinjection\texpected_class\texpected_rc1\tsection\tmapped_combo\tstatus\tdetail\n")
        for o in out_rows:
            fh.write("\t".join(str(x).replace("\t", " ") for x in o) + "\n")
    print("map22 strict rows=%d %s" % (len(out_rows), dict(sorted(cnt.items()))))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
