#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2), section 3 step 3: F2 <-> F3 event-by-event sequence comparison.  New file.

Read only (does not modify compare_callseq_r8m1a4.py).  Only units whose strict recheck status is PASS
(STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT.tsv) are compared.  For each pair:
  - the F2 and F3 events.tsv are read in event_idx order;
  - the comparison fields are: event_type, func, caller, seq, sub_seq, and details (plan/window context, seam site/k,
    and the internal malloc detail of each plan/window: plan_call/alloc and win_call/alloc);
  - the only permitted name normalisation is quad -> quad_st (shape_get_intersection_area_quad -> ..._quad_st); it is
    applied to func and caller and recorded as IDENTICAL_AFTER_RENAME only if the normalised sequences are equal and the
    raw sequences were not;
  - rc_first and rc_retry are read from gdb.stdout ("RC first N" / "RC retry N").  A missing value is RC_UNAVAILABLE,
    never the process exit status;
  - the pair status is IDENTICAL, IDENTICAL_AFTER_RENAME, DIFFERENT or EVIDENCE_INSUFFICIENT.
Output: one row per pair, and a difference table (one row per differing event index) for DIFFERENT pairs.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/seqcompare_r8m1a4audit2.py SEQ_NAME
SEQ_NAME must be SEQCOMPARE_R8_M1a4AUDIT2_<name>.tsv (bare name) and must not exist (U17).
Writes SEQCOMPARE_R8_M1a4AUDIT2_<name>.tsv and SEQCOMPARE_DIFF_R8_M1a4AUDIT2_<name>.tsv into the round evidence directory.
Last stdout line: "seqcompare pairs=<n> identical=<a> after_rename=<b> different=<c> insufficient=<d>".
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVR = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
EV = os.path.join(EVR, "m1a4audit2")
RAW = os.path.join(EVR, "callseq_r8m1a4_r3")
REG_M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
STRICT = os.path.join(REG_M1A, "STRICT_RECHECK_CALLSEQ_R8_M1a4AUDIT.tsv")
UNITS = os.path.join(REG_M1A, "CALLSEQ_UNITS_R8_M1a4_R3.tsv")
NAME_RE = re.compile(r"^SEQCOMPARE_R8_M1a4AUDIT2_[A-Za-z0-9_]+\.tsv$")
EXPECT_COLS = ["event_idx", "event_type", "func", "caller", "seq", "sub_seq", "details"]
RENAME_FROM = "shape_get_intersection_area_quad"
RENAME_TO = "shape_get_intersection_area_quad_st"


def read_strict_pass():
    with open(STRICT, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    st = {}
    for line in lines[1:]:
        if not line:
            continue
        cols = line.split("\t")
        if len(cols) != len(hdr):
            raise SystemExit("REFUSED: strict table column count")
        r = dict(zip(hdr, cols))
        st[r["unit_id"]] = r
    return st


def read_units():
    with open(UNITS, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    out = {}
    for line in lines[1:]:
        if not line:
            continue
        r = dict(zip(hdr, line.split("\t")))
        out[r["unit_id"]] = r
    return out


def read_events(uid):
    path = os.path.join(RAW, uid, "events.tsv")
    if not os.path.isfile(path):
        return None, "events.tsv missing"
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    if not lines:
        return None, "events.tsv empty"
    hdr = lines[0].split("\t")
    if hdr != EXPECT_COLS:
        return None, "events header differs: %s" % hdr
    rows = []
    for n, line in enumerate(lines[1:], 2):
        cols = line.split("\t")
        if len(cols) != len(EXPECT_COLS):
            return None, "events line %d has %d columns" % (n, len(cols))
        rows.append(dict(zip(EXPECT_COLS, cols)))
    return rows, None


def read_rc(uid):
    path = os.path.join(RAW, uid, "gdb.stdout.txt")
    if not os.path.isfile(path):
        return None, None
    first = retry = None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = re.match(r"^RC first (-?\d+)\s*$", line)
            if m:
                first = m.group(1)
            m = re.match(r"^RC retry (-?\d+)\s*$", line)
            if m:
                retry = m.group(1)
    return first, retry


def sig(rows, normalise):
    """Comparison signature of an event list: (event_type, func, caller, seq, sub_seq, details) per row."""
    out = []
    for r in rows:
        func = r["func"]
        caller = r["caller"]
        if normalise:
            func = func.replace(RENAME_FROM, RENAME_TO)
            caller = caller.replace(RENAME_FROM, RENAME_TO)
        out.append((r["event_type"], func, caller, r["seq"], r["sub_seq"], r["details"]))
    return out


def main(argv):
    if len(argv) != 2 or not NAME_RE.match(argv[1]):
        raise SystemExit("usage: seqcompare_r8m1a4audit2.py SEQCOMPARE_R8_M1a4AUDIT2_<name>.tsv")
    out = os.path.join(EV, argv[1])
    diff_name = argv[1].replace("SEQCOMPARE_R8_", "SEQCOMPARE_DIFF_R8_")
    out_diff = os.path.join(EV, diff_name)
    for p in (out, out_diff):
        if os.path.exists(p):
            raise SystemExit("REFUSED: exists (U17): %s" % p)

    strict = read_strict_pass()
    units = read_units()
    pairs = {}
    for uid, u in units.items():
        pairs.setdefault(u["pair_id"], {})[u["run_tree"]] = uid

    rows_out = []
    diff_rows = []
    status_count = Counter()
    for pid in sorted(pairs):
        d = pairs[pid]
        if set(d) != {"F2", "F3"}:
            rows_out.append((pid, "-", "-", "EVIDENCE_INSUFFICIENT", "pair incomplete: %s" % sorted(d), "-", "-", "-", "-"))
            status_count["EVIDENCE_INSUFFICIENT"] += 1
            continue
        u2, u3 = d["F2"], d["F3"]
        s2 = strict.get(u2, {}).get("status")
        s3 = strict.get(u3, {}).get("status")
        if s2 != "PASS" or s3 != "PASS":
            rows_out.append((pid, u2, u3, "EVIDENCE_INSUFFICIENT", "strict status F2=%s F3=%s" % (s2, s3), "-", "-", "-", "-"))
            status_count["EVIDENCE_INSUFFICIENT"] += 1
            continue
        e2, err2 = read_events(u2)
        e3, err3 = read_events(u3)
        if err2 or err3:
            rows_out.append((pid, u2, u3, "EVIDENCE_INSUFFICIENT", "events F2=%s F3=%s" % (err2, err3), "-", "-", "-", "-"))
            status_count["EVIDENCE_INSUFFICIENT"] += 1
            continue
        raw2 = sig(e2, False)
        raw3 = sig(e3, False)
        n2 = sig(e2, True)
        n3 = sig(e3, True)
        rc2 = read_rc(u2)
        rc3 = read_rc(u3)
        rc_txt = "F2_first=%s_retry=%s;F3_first=%s_retry=%s" % (
            rc2[0] or "RC_UNAVAILABLE", rc2[1] or "RC_UNAVAILABLE", rc3[0] or "RC_UNAVAILABLE", rc3[1] or "RC_UNAVAILABLE")
        if raw2 == raw3:
            status = "IDENTICAL"
        elif n2 == n3:
            status = "IDENTICAL_AFTER_RENAME"
        else:
            status = "DIFFERENT"
        if status == "DIFFERENT":
            first = None
            for i in range(max(len(raw2), len(raw3))):
                a = raw2[i] if i < len(raw2) else None
                b = raw3[i] if i < len(raw3) else None
                if a != b:
                    first = i
                    diff_rows.append((pid, u2, u3, str(i + 1), repr(a), repr(b)))
            status_detail = "first_diff_index=%s len_F2=%d len_F3=%d" % (
                (first + 1) if first is not None else "-", len(raw2), len(raw3))
        else:
            status_detail = "events=%d" % len(raw2)
        status_count[status] += 1
        rows_out.append((pid, u2, u3, status, status_detail, rc_txt, str(len(raw2)), str(len(raw3)), "-"))

    with open(out, "x", encoding="utf-8") as fh:
        fh.write("pair_id\tF2_unit\tF3_unit\tstatus\tdetail\trc\tn_events_F2\tn_events_F3\tnote\n")
        for r in rows_out:
            fh.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")
    with open(out_diff, "x", encoding="utf-8") as fh:
        fh.write("pair_id\tF2_unit\tF3_unit\tevent_index\tF2_signature\tF3_signature\n")
        for r in diff_rows:
            fh.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")

    total = len(rows_out)
    print("seqcompare pairs=%d identical=%d after_rename=%d different=%d insufficient=%d" % (
        total, status_count["IDENTICAL"], status_count["IDENTICAL_AFTER_RENAME"], status_count["DIFFERENT"],
        status_count["EVIDENCE_INSUFFICIENT"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
