#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2), section 5: strict additions recheck (A and B), with the frozen K0 rule.
New file.  Does NOT modify summarize_additions_r8m1a4.py or summarize_additions_strict_r8m1a4audit.py.

Read only.  Parses the original raw logs of the nine F3 combinations and compares every expectation field with
EXPECT_ADDITIONS_R8_M1a4.txt (frozen, sha256 ec08348f...).  No value is hard-coded as an observation: each observed value is
parsed from the log, and a missing line is recorded as MISSING (never 0, never the expected value).

Section A (a1map_F3_<combo>/stderr.txt, callers.tsv), per combination:
  win_open                 = number of S3R4_WIN_OPEN lines
  win_malloc_in_window     = sum of malloc_in_window over S3R4_WIN_CLOSE lines
  outside_malloc_count     = number of S3R4_OUT_MALLOC lines
  K_init                   = the OUT_MALLOC line with n == 4 that occurs before the SECOND WIN_OPEN (UNIQUE required)
  K0                       = per K0_RULE_R8_M1a4AUDIT2.txt: EVIDENCE_INSUFFICIENT unless the log records the layer of an
                             n == 0 allocation; the stderr fields (k, n, caller, hit) do not carry the layer
  caller                   = caller of the K_init line, mapped through callers.tsv (function name column)
  status                   = UNIQUE if K_init has exactly one candidate, else NOT_UNIQUE
Section B (b_map_F3_<combo>/stderr.txt, counts.txt, gdb_rc.txt), per combination:
  Mtot, Mfirst             = gdb $2 and $1 from counts.txt (definitions in b_map_run_c3.sh line 3)
  n_values                 = the set of n values of S3R4C3_WIN_MALLOC lines; reported as a single value only if the set has one
                             member, else as the sorted set
  RC_first, RC_retry       = "RC first N" / "RC retry N" from counts.txt; a missing value is MISSING
  inject_hits              = the hit field of WIN_MALLOC lines (count of hit=1)
  polygon_breakpoint_hits  = count of WIN_MALLOC lines whose n equals the polygon size of the expectation (historical
                             derivation, as in B_MAP_C3; NOT a source breakpoint hit)
  gdb_rc                   = gdb_rc.txt value

Comparison: field by field against the frozen expectation file.  Status per field: MATCH / MISMATCH / NOT_UNIQUE /
EVIDENCE_INSUFFICIENT / MISSING.  Any MISMATCH, NOT_UNIQUE, EVIDENCE_INSUFFICIENT or MISSING in a combination makes the
combination not MATCH.  Exit status: 0 only if all nine combinations are MATCH; 3 otherwise.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/summarize_additions_strict_r8m1a4audit2.py SUMMARY_NAME
SUMMARY_NAME: ADDITIONS_STRICT_R8_M1a4AUDIT2_<name>.tsv (bare name, must not exist, U17).
"""
import hashlib
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVR = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
EV = os.path.join(EVR, "m1a4audit2")
ADD = os.path.join(EVR, "additions_r8m1a4")
REG_M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
EXPECT = os.path.join(REG_M1A, "EXPECT_ADDITIONS_R8_M1a4.txt")
EXPECT_SHA = "ec08348f70cc33ab6a94433dfcf1658c3ae25dfee421998c979def1e18beedf4"
RULE = os.path.join(EV, "K0_RULE_R8_M1a4AUDIT2.txt")
NAME_RE = re.compile(r"^ADDITIONS_STRICT_R8_M1a4AUDIT2_[A-Za-z0-9_]+\.tsv$")

A_COMBOS = ["closed2d-ng1", "fft-ng5", "kottke-ng5"]
B_COMBOS = ["fft-ng1", "fft-ng5", "fft-ng9", "kottke-ng1", "kottke-ng5", "kottke-ng9"]

RE_WIN_OPEN = re.compile(r"^S4FMM S3R4_WIN_OPEN\s*$")
RE_WIN_CLOSE = re.compile(r"^S4FMM S3R4_WIN_CLOSE malloc_in_window=(\d+) rc=(-?\d+)\s*$")
RE_OUT = re.compile(r"^S4FMM S3R4_OUT_MALLOC k=(\d+) n=(\d+) caller=(0x[0-9a-fA-F]+) hit=(\d+)\s*$")
RE_B_WIN = re.compile(r"^S4FMM S3R4C3_WIN_MALLOC k=(\d+) n=(\d+) caller=(0x[0-9a-fA-F]+) hit=(\d+)\s*$")
RE_RC_FIRST = re.compile(r"^RC first (-?\d+)\s*$", re.M)
RE_RC_RETRY = re.compile(r"^RC retry (-?\d+)\s*$", re.M)
RE_GDB_RC = re.compile(r"^gdb_rc=(-?\d+)\s*$")
RE_GDB_MTOT = re.compile(r"\$2\s*=\s*(-?\d+)")
RE_GDB_MFIRST = re.compile(r"\$1\s*=\s*(-?\d+)")
POLY_N = 36  # the polygon size of the expectation (see the expectation header, ES3R4-25: sizeof(int)*3*(n_vertices-2), n_vertices 5)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def parse_expect(path):
    """Expected values: {section: {combo: {field: value}}}.  Read from the frozen file; nothing is typed here."""
    out = {"A": {}, "B": {}}
    sec = None
    for ln in read_text(path).splitlines():
        if ln.startswith("# Section A"):
            sec = "A"
            continue
        if ln.startswith("# Section B"):
            sec = "B"
            continue
        m = re.match(r"^#\s+combo=([A-Za-z0-9_-]+):\s*(.*)$", ln)
        if m and sec:
            combo = m.group(1)
            fields = {}
            for tok in m.group(2).split():
                if "=" in tok:
                    k, v = tok.split("=", 1)
                    fields[k] = v
            out[sec][combo] = fields
    return out


def callers_map(path):
    """caller address -> function name (column 3) from callers.tsv (header row skipped)."""
    m = {}
    for ln in read_text(path).splitlines():
        cols = ln.split("\t")
        if len(cols) >= 3 and cols[0].startswith("0x"):
            m[cols[0].lower()] = cols[2]
    return m


def sec_a(combo, cmap):
    d = os.path.join(ADD, "a1map_F3_%s" % combo)
    st = os.path.join(d, "stderr.txt")
    cl = os.path.join(d, "callers.tsv")
    if not (os.path.isfile(st) and os.path.isfile(cl)):
        return None, "missing input in %s" % d
    lines = read_text(st).splitlines()
    wins = 0
    in_win_total = 0
    outs = []  # (line_index, k, n, caller, hit)
    second_win_idx = None
    for i, ln in enumerate(lines):
        if RE_WIN_OPEN.match(ln):
            wins += 1
            if wins == 2:
                second_win_idx = i
            continue
        m = RE_WIN_CLOSE.match(ln)
        if m:
            in_win_total += int(m.group(1))
            continue
        m = RE_OUT.match(ln)
        if m:
            outs.append((i, int(m.group(1)), int(m.group(2)), m.group(3).lower(), int(m.group(4))))
    obs = {
        "win_open": str(wins),
        "win_malloc_in_window": str(in_win_total),
        "outside_malloc_count": str(len(outs)),
    }
    if second_win_idx is None:
        obs["K_init"] = "MISSING_SECOND_WIN_OPEN"
        obs["caller"] = "-"
        obs["status"] = "MISSING"
        obs["K0"] = "EVIDENCE_INSUFFICIENT"
        return obs, "no second WIN_OPEN"
    cands = [o for o in outs if o[0] < second_win_idx and o[2] == 4]
    if len(cands) == 1:
        obs["K_init"] = str(cands[0][1])
        obs["status"] = "UNIQUE"
        obs["caller"] = cmap.get(cands[0][3], "UNMAPPED:%s" % cands[0][3])
    elif len(cands) == 0:
        obs["K_init"] = "NO_CANDIDATE"
        obs["status"] = "NO_CANDIDATE"
        obs["caller"] = "-"
    else:
        obs["K_init"] = "NOT_UNIQUE:" + ",".join(str(c[1]) for c in cands)
        obs["status"] = "NOT_UNIQUE"
        obs["caller"] = "-"
    # K0 per K0_RULE: the stderr line has no layer field; K0 is not determined by this log.
    obs["K0"] = "EVIDENCE_INSUFFICIENT"
    return obs, "ok"


def sec_b(combo):
    d = os.path.join(ADD, "b_map_F3_%s" % combo)
    st = os.path.join(d, "stderr.txt")
    ct = os.path.join(d, "counts.txt")
    gr = os.path.join(d, "gdb_rc.txt")
    for p in (st, ct, gr):
        if not os.path.isfile(p):
            return None, "missing input %s" % p
    stderr_txt = read_text(st)
    counts = read_text(ct)
    gdbrc = None
    for ln in read_text(gr).splitlines():
        m = RE_GDB_RC.match(ln)
        if m:
            gdbrc = m.group(1)
    obs = {"gdb_rc": gdbrc if gdbrc is not None else "MISSING"}
    m2 = RE_GDB_MTOT.search(counts)
    m1 = RE_GDB_MFIRST.search(counts)
    obs["Mtot"] = m2.group(1) if m2 else "MISSING"
    obs["Mfirst"] = m1.group(1) if m1 else "MISSING"
    wins = []
    for ln in stderr_txt.splitlines():
        m = RE_B_WIN.match(ln)
        if m:
            wins.append((int(m.group(1)), int(m.group(2)), m.group(3), int(m.group(4))))
    ns = sorted(set(w[1] for w in wins))
    if not ns:
        obs["n_values"] = "MISSING"
    elif len(ns) == 1:
        obs["n_values"] = str(ns[0])
    else:
        obs["n_values"] = "SET:" + ",".join(str(x) for x in ns)
    f = RE_RC_FIRST.search(counts)
    r = RE_RC_RETRY.search(counts)
    obs["RC_first"] = f.group(1) if f else "MISSING"
    obs["RC_retry"] = r.group(1) if r else "MISSING"
    obs["inject_hits"] = str(sum(1 for w in wins if w[3] == 1))
    obs["polygon_breakpoint_hits"] = str(sum(1 for w in wins if w[1] == POLY_N))
    return obs, "ok"


def main(argv):
    if len(argv) != 2 or not NAME_RE.match(argv[1]):
        raise SystemExit("usage: summarize_additions_strict_r8m1a4audit2.py ADDITIONS_STRICT_R8_M1a4AUDIT2_<name>.tsv")
    out = os.path.join(EV, argv[1])
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    if sha256_file(EXPECT) != EXPECT_SHA:
        raise SystemExit("REFUSED: expectation file sha256 differs from the frozen value")
    if not os.path.isfile(RULE):
        raise SystemExit("REFUSED: K0 rule file missing")
    exp = parse_expect(EXPECT)
    cmap = callers_map(os.path.join(ADD, "a1map_F3_closed2d-ng1", "callers.tsv"))

    rows = []
    combo_status = {}
    status_count = Counter()

    def compare(section, combo, obs, notes):
        exp_fields = exp[section].get(combo)
        if exp_fields is None:
            rows.append((section, combo, "-", "-", "-", "NO_EXPECTATION", notes))
            combo_status[(section, combo)] = "NO_EXPECTATION"
            return
        all_ok = True
        for field, ev in exp_fields.items():
            ov = obs.get(field, "MISSING") if obs is not None else "MISSING"
            if ov == "MISSING" or ov == "-":
                st = "MISSING"
            elif ov.startswith("NOT_UNIQUE") or ov in ("NOT_UNIQUE", "NO_CANDIDATE"):
                st = "NOT_UNIQUE"
            elif ov == "EVIDENCE_INSUFFICIENT":
                st = "EVIDENCE_INSUFFICIENT"
            elif ov == ev:
                st = "MATCH"
            else:
                st = "MISMATCH"
            if st != "MATCH":
                all_ok = False
            rows.append((section, combo, field, ev, ov, st, notes))
            status_count[st] += 1
        combo_status[(section, combo)] = "MATCH" if all_ok else "NOT_MATCH"

    for combo in A_COMBOS:
        obs, note = sec_a(combo, cmap)
        compare("A", combo, obs, note)
        # the same task section 5 rule for the A combinations: the gdb return code of the run, read from gdb_rc.txt
        gfile = os.path.join(ADD, "a1map_F3_%s" % combo, "gdb_rc.txt")
        gv = "MISSING"
        if os.path.isfile(gfile):
            for ln in read_text(gfile).splitlines():
                m = RE_GDB_RC.match(ln)
                if m:
                    gv = m.group(1)
        gst = "MISSING" if gv == "MISSING" else ("MATCH" if gv == "0" else "MISMATCH")
        rows.append(("A", combo, "gdb_rc(task_s5_rule)", "0", gv, gst, "task section 5 rule; not in EXPECT file"))
        status_count[gst] += 1
        if gst != "MATCH":
            combo_status[("A", combo)] = "NOT_MATCH"
    for combo in B_COMBOS:
        obs, note = sec_b(combo)
        compare("B", combo, obs, note)
        # task section 5: a non-zero gdb_rc must not be MATCH.  The frozen expectation file does not list this field,
        # so it is checked here against the task rule (expected 0), and is recorded as such in the note column.
        if obs is not None:
            gv = obs.get("gdb_rc", "MISSING")
            if gv == "MISSING":
                gst = "MISSING"
            elif gv == "0":
                gst = "MATCH"
            else:
                gst = "MISMATCH"
            rows.append(("B", combo, "gdb_rc(task_s5_rule)", "0", gv, gst, "task section 5 rule; not in EXPECT file"))
            status_count[gst] += 1
            if gst != "MATCH":
                combo_status[("B", combo)] = "NOT_MATCH"

    with open(out, "x", encoding="utf-8") as fh:
        fh.write("section\tcombo\tfield\texpected\tobserved\tstatus\tnote\n")
        for r in rows:
            fh.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")

    n_match = sum(1 for v in combo_status.values() if v == "MATCH")
    n_total = len(A_COMBOS) + len(B_COMBOS)
    print("additions strict: combinations MATCH %d of %d; field statuses %s" % (n_match, n_total, dict(sorted(status_count.items()))))
    return 0 if n_match == n_total else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
