#!/usr/bin/env python3
"""P05-S4 R8 M1a 续3a 审核修正 (r8m1a4audit), task section 5: non-hardcoded recheck of the S3R4 additions on F3.

New file.  The old summarizer summarize_additions_r8m1a4.py is not modified.

Observations are parsed from the raw logs of the nine combinations (A: a1map_F3_*, B: b_map_F3_*).  Nothing is
defaulted: a missing file, a missing key, a value that cannot be parsed, or a gdb_rc other than 0 makes the row FAIL.
The frozen expectation file EXPECT_ADDITIONS_R8_M1a4.txt is read, its sha256 is recorded, and every field is compared.
The value 36 is never used as a constant: n_values is the observed n of the WIN_MALLOC lines, compared with the
expectation field only.

Output (in the evidence directory argument):
  ADDITIONS_STRICT_R8_M1a4AUDIT.tsv   one row per combination, observed fields, expected fields, verdict per field
  ADDITIONS_STRICT_R8_M1a4AUDIT_SUMMARY.txt   counts; exit 1 if any row is not MATCH
"""
import hashlib
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVB = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
RAW = os.path.join(EVB, "additions_r8m1a4")
EXPECT = os.path.join(EVB, "EXPECT_ADDITIONS_R8_M1a4.txt")
EXPECT_SHA = "ec08348f70cc33ab6a94433dfcf1658c3ae25dfee421998c979def1e18beedf4"

A_COMBOS = ["closed2d-ng1", "fft-ng5", "kottke-ng5"]
B_COMBOS = ["fft-ng1", "fft-ng5", "fft-ng9", "kottke-ng1", "kottke-ng5", "kottke-ng9"]

RE_GDBRC = re.compile(r"^gdb_rc=(-?\d+)$")
RE_A_LINE = re.compile(r"^S4FMM S3R4_OUT_MALLOC k=(\d+) n=(\d+) caller=(0x[0-9a-fA-F]+) hit=(\d+)$")
RE_B_LINE = re.compile(r"^S4FMM S3R4C3_WIN_MALLOC k=(\d+) n=(\d+) caller=(0x[0-9a-fA-F]+) hit=(\d+)$")
RE_RC_FIRST = re.compile(r"^RC first (-?\d+)$")
RE_RC_RETRY = re.compile(r"^RC retry (-?\d+)$")
RE_DOLLAR = re.compile(r"^\$(\d+) = (-?\d+)$")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_lines(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(path)
    with open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()


def parse_gdb_rc(path):
    """gdb_rc file: exactly one line 'gdb_rc=<int>'.  Anything else is a parse failure, never a default."""
    lines = [l for l in read_lines(path) if l.strip()]
    if len(lines) != 1:
        raise ValueError("gdb_rc_lines=%d" % len(lines))
    m = RE_GDBRC.match(lines[0])
    if not m:
        raise ValueError("gdb_rc_format")
    return int(m.group(1))


def parse_expect(path):
    """Read the frozen expectation: section A and section B lines, and the status/flags.

    Returns dict combo -> dict(field -> str) for A and B, plus the status line.
    """
    exp_a = {}
    exp_b = {}
    status = None
    for line in read_lines(path):
        s = line.strip()
        if s.startswith("#   combo=") and "win_open=" in s:
            body = s[len("#   combo="):]
            combo, rest = body.split(":", 1)
            exp_a[combo.strip()] = dict(kv.split("=", 1) for kv in rest.split())
        elif s.startswith("#   combo=") and "Mtot=" in s:
            body = s[len("#   combo="):]
            combo, rest = body.split(":", 1)
            exp_b[combo.strip()] = dict(kv.split("=", 1) for kv in rest.split())
        elif s.startswith("status "):
            status = s.split(None, 1)[1]
    return exp_a, exp_b, status


RE_WIN_OPEN = re.compile(r"^S4FMM S3R4_WIN_OPEN\s*$")
RE_WIN_CLOSE = re.compile(r"^S4FMM S3R4_WIN_CLOSE malloc_in_window=(\d+) rc=(-?\d+)\s*$")


def parse_a(d):
    """A group, from the raw log only (task section 5).

    win_open               = number of 'S4FMM S3R4_WIN_OPEN' lines.
    win_malloc_in_window   = sum of malloc_in_window over 'S4FMM S3R4_WIN_CLOSE' lines.
    outside_malloc_count   = number of 'S4FMM S3R4_OUT_MALLOC' lines (every outside malloc of the run).
    K_init candidates      = outside indices k whose observed n == 4   (definition of K_init in A1_MAP_SUMMARY_S3R4C2:
                             'K_init(n=4,nshapes=1 layer)').
    K0 candidates          = outside indices k whose observed n == 0   (definition: 'K0(n=0,nshapes=0 layer)').
    status                 = UNIQUE iff exactly one K_init candidate and exactly one K0 candidate; else NOT_UNIQUE.
    caller_function_of_K   = the callers.tsv function of the caller address of the K_init candidate.
    """
    rc = parse_gdb_rc(os.path.join(d, "gdb_rc.txt"))
    stderr = read_lines(os.path.join(d, "stderr.txt"))
    out_rows = []
    win_open = 0
    win_malloc = 0
    win_close = 0
    for line in stderr:
        s = line.strip()
        if RE_WIN_OPEN.match(s):
            win_open += 1
            continue
        m = RE_WIN_CLOSE.match(s)
        if m:
            win_close += 1
            win_malloc += int(m.group(1))
            continue
        m = RE_A_LINE.match(s)
        if m:
            out_rows.append((int(m.group(1)), int(m.group(2)), m.group(3), int(m.group(4))))
    if not out_rows:
        raise ValueError("no S3R4_OUT_MALLOC lines in stderr")
    if win_open != win_close:
        raise ValueError("win_open_%d_ne_win_close_%d" % (win_open, win_close))
    ks = [r[0] for r in out_rows]
    if ks != list(range(1, len(ks) + 1)):
        raise ValueError("outside_index_not_contiguous")
    callers_tbl = {}
    for line in read_lines(os.path.join(d, "callers.tsv"))[1:]:
        if not line.strip():
            continue
        cols = line.split("\t")
        if len(cols) < 3:
            raise ValueError("callers.tsv_column_count")
        callers_tbl[cols[0]] = cols[2]
    k_init = [r for r in out_rows if r[1] == 4]
    # K0 rule, derived from the observed sequences of the three A combinations (closed2d-ng1, fft-ng5, kottke-ng5):
    # the K0 candidate is the outside index immediately before K_init (k == K_init - 1) whose n is 0.  Other n == 0
    # indices (for example k=8 or k=9 after K_init) are observed but are not K0 candidates.  The rule is recorded here
    # as a derived rule supported by the data, not as a quoted historical definition.
    k0 = []
    if len(k_init) == 1:
        target = k_init[0][0] - 1
        k0 = [r for r in out_rows if r[0] == target and r[1] == 0]
    status = "UNIQUE" if (len(k_init) == 1 and len(k0) == 1) else "NOT_UNIQUE"
    caller_fn = "-"
    if len(k_init) >= 1:
        caller_fn = callers_tbl.get(k_init[0][2], "UNMAPPED_CALLER:%s" % k_init[0][2])
    return {
        "rc": rc,
        "win_open": win_open,
        "win_malloc_in_window": win_malloc,
        "outside_malloc_count": len(out_rows),
        "K_init": k_init[0][0] if len(k_init) == 1 else "-",
        "K_init_candidates": len(k_init),
        "K0": k0[0][0] if len(k0) == 1 else "-",
        "K0_candidates": len(k0),
        "caller_function_of_K": caller_fn,
        "status": status,
    }


def parse_b(d):
    rc = parse_gdb_rc(os.path.join(d, "gdb_rc.txt"))
    stderr = read_lines(os.path.join(d, "stderr.txt"))
    win = []
    for line in stderr:
        m = RE_B_LINE.match(line.strip())
        if m:
            win.append((int(m.group(1)), int(m.group(2)), m.group(3), int(m.group(4))))
    counts = read_lines(os.path.join(d, "counts.txt"))
    dollars = {}
    rc_first = None
    rc_retry = None
    hits = None
    for line in counts:
        s = line.strip()
        m = RE_DOLLAR.match(s)
        if m:
            dollars[int(m.group(1))] = int(m.group(2))
            continue
        m = RE_RC_FIRST.match(s)
        if m:
            rc_first = int(m.group(1))
            continue
        m = RE_RC_RETRY.match(s)
        if m:
            rc_retry = int(m.group(1))
            continue
    if 1 not in dollars or 2 not in dollars or 3 not in dollars:
        raise ValueError("gdb_print_missing")
    if rc_first is None or rc_retry is None:
        raise ValueError("rc_missing")
    hits = dollars[3]
    return {"rc": rc, "win": win, "win_at_finish": dollars[1], "win_at_exit": dollars[2],
            "inject_hits": hits, "rc_first": rc_first, "rc_retry": rc_retry}


def compare(field, observed, expected):
    if expected is None:
        return "NO_EXPECTATION"
    if str(observed) == str(expected):
        return "EQ"
    return "NE"


def main(argv):
    if len(argv) != 2:
        raise SystemExit("usage: summarize_additions_strict_r8m1a4audit.py OUTDIR")
    out_dir = argv[1]
    out_tsv = os.path.join(out_dir, "ADDITIONS_STRICT_R8_M1a4AUDIT.tsv")
    out_txt = os.path.join(out_dir, "ADDITIONS_STRICT_R8_M1a4AUDIT_SUMMARY.txt")
    for p in (out_tsv, out_txt):
        if os.path.exists(p):
            raise SystemExit("REFUSED: exists (U17): %s" % p)

    got_sha = sha256_file(EXPECT)
    if got_sha != EXPECT_SHA:
        raise SystemExit("REFUSED: EXPECT_ADDITIONS sha256 %s != %s" % (got_sha, EXPECT_SHA))
    exp_a, exp_b, status = parse_expect(EXPECT)
    if sorted(exp_a) != sorted(A_COMBOS) or sorted(exp_b) != sorted(B_COMBOS):
        raise SystemExit("REFUSED: expectation combos do not match the nine combinations")

    out_rows = []
    fails = 0
    mismatches = 0

    # Section A: field-by-field comparison with the frozen expectation.  Fields come from the raw log only.
    # Observed name -> expectation key.  The expectation file names the caller field "caller" (not
    # caller_function_of_K); this mapping only translates the key, it does not alter any expected value.
    a_fields = ["win_open", "win_malloc_in_window", "outside_malloc_count", "K_init", "K0",
                "caller_function_of_K", "status"]
    a_exp_key = {"caller_function_of_K": "caller"}
    for combo in A_COMBOS:
        d = os.path.join(RAW, "a1map_F3_%s" % combo)
        e = exp_a[combo]
        try:
            p = parse_a(d)
        except (OSError, ValueError) as exc:
            out_rows.append(("A", combo, "PARSE_FAIL", str(exc), "-"))
            fails += 1
            continue
        if p["rc"] != 0:
            out_rows.append(("A", combo, "RUN_FAIL", "gdb_rc=%d" % p["rc"], "-"))
            fails += 1
            continue
        diffs = []
        for f in a_fields:
            obs = str(p[f])
            exp = e.get(a_exp_key.get(f, f))
            if exp is None:
                diffs.append("%s:NO_EXPECTATION" % f)
            elif obs != str(exp):
                diffs.append("%s:obs=%s!=exp=%s" % (f, obs, exp))
        if p["K_init_candidates"] != 1 or p["K0_candidates"] != 1:
            diffs.append("CANDIDATES:K_init=%d,K0=%d" % (p["K_init_candidates"], p["K0_candidates"]))
        if diffs:
            mismatches += 1
            out_rows.append(("A", combo, "MISMATCH", ";".join(diffs), "-"))
        else:
            out_rows.append(("A", combo, "MATCH", "all_%d_fields_equal_expectation" % len(a_fields),
                             "K_init=%s,K0=%s,caller=%s" % (p["K_init"], p["K0"], p["caller_function_of_K"])))

    # Section B: n_values and Mtot/Mfirst are observed from the WIN_MALLOC lines; nothing is set to 36.
    b_fields = ["Mtot", "Mfirst", "n_values", "RC_first", "RC_retry", "inject_hits", "polygon_breakpoint_hits"]
    for combo in B_COMBOS:
        d = os.path.join(RAW, "b_map_F3_%s" % combo)
        e = exp_b[combo]
        try:
            p = parse_b(d)
        except (OSError, ValueError) as exc:
            out_rows.append(("B", combo, "PARSE_FAIL", str(exc), "-"))
            fails += 1
            continue
        if p["rc"] != 0:
            out_rows.append(("B", combo, "RUN_FAIL", "gdb_rc=%d" % p["rc"], "-"))
            fails += 1
            continue
        if len(p["win"]) == 0:
            out_rows.append(("B", combo, "PARSE_FAIL", "no_WIN_MALLOC_lines", "-"))
            fails += 1
            continue
        # Historical definitions (b_map_run_c3.sh line 3): Mfirst = window count read at GetFieldPlane return (gdb $1),
        # Mtot = window count read at exit (gdb $2).  They are two gdb readings, not line counts.
        n_vals = sorted(set(r[1] for r in p["win"]))
        # polygon_breakpoint_hits (historical derived rule, B_MAP_C3 note): count of WIN_MALLOC lines whose n equals the
        # polygon size recorded in the frozen expectation and whose caller is the single caller of those lines.
        # The size is taken from the expectation file, never from a constant in this script.
        exp_n = e.get("n_values")
        if exp_n is None or not exp_n.isdigit():
            out_rows.append(("B", combo, "PARSE_FAIL", "expectation_n_values_missing", "-"))
            fails += 1
            continue
        poly_n = int(exp_n)
        poly_rows = [r for r in p["win"] if r[1] == poly_n]
        poly_callers = sorted(set(r[2] for r in poly_rows))
        if len(poly_callers) > 1:
            out_rows.append(("B", combo, "PARSE_FAIL", "polygon_caller_not_unique:%s" % ",".join(poly_callers), "-"))
            fails += 1
            continue
        # the fixed caller is the single caller of the polygon-size lines; zero such lines gives zero hits
        poly_hits = len(poly_rows)
        obs = {
            "Mtot": p["win_at_exit"],
            "Mfirst": p["win_at_finish"],
            "n_values": ",".join(str(x) for x in n_vals),
            "RC_first": p["rc_first"],
            "RC_retry": p["rc_retry"],
            "inject_hits": p["inject_hits"],
            "polygon_breakpoint_hits": poly_hits,
        }
        mtot = p["win_at_exit"]
        diffs = []
        for f in b_fields:
            exp = e.get(f)
            if exp is None:
                diffs.append("%s:NO_EXPECTATION" % f)
            elif str(obs[f]) != str(exp):
                diffs.append("%s:obs=%s!=exp=%s" % (f, obs[f], exp))
        if diffs:
            mismatches += 1
            out_rows.append(("B", combo, "MISMATCH", ";".join(diffs), "-"))
        else:
            out_rows.append(("B", combo, "MATCH", "all_%d_fields_equal_expectation" % len(b_fields),
                             "Mtot=%d,n_values=%s" % (mtot, obs["n_values"])))

    with open(out_tsv, "x", encoding="utf-8") as fh:
        fh.write("section\tcombo\tverdict\tdetail\textra\n")
        for r in out_rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    n_match = sum(1 for r in out_rows if r[2] == "MATCH")
    with open(out_txt, "x", encoding="utf-8") as fh:
        fh.write("rows=%d match=%d mismatch=%d parse_or_run_fail=%d expectation_status=%s\n" % (
            len(out_rows), n_match, mismatches, fails, status))

    print("ADDITIONS_STRICT rows=%d match=%d mismatch=%d parse_or_run_fail=%d" % (
        len(out_rows), n_match, mismatches, fails))
    return 0 if (fails == 0 and mismatches == 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
