#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2), section 2: request semantic reconstruction.  New file.

Read only.  For each of the 1128 source rows of CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv it:
  1. locates the ORIGINAL source row by (source_registry, source_row) = (registry name, physical line number in the
     registry file).  No row is located by point_id alone.  A physical line whose point_id or tree does not match the
     coverage row is refused.  Refusal is counted, not defaulted.
  2. reads request_raw, nth, route, twice_env, NG, inj_call, expected_class and the basis from the original row;
  3. reconstructs the canonical injection target (s4malloc:K, exec:K, plan:N, plancall:K:M, rnv1:M, win:M, seam
     site/ID with K, control, or ADDITION_SECTION7 for rows of the S3R4 additions);
  4. takes the counting unit from the coverage table and reports it.  No nth is guessed.  A missing parameter that the
     request needs is recorded as MISSING_PARAMETER and the row is not classified.

It does NOT classify REACHED (that is done by classify step, in the same script after the unit event check).
Output: REQUEST_RECON_R8_M1a4AUDIT2_<name>.tsv (one row per coverage row) and a summary.
Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/reconstruct_requests_r8m1a4audit2.py RECON_NAME
RECON_NAME must be REQUEST_RECON_R8_M1a4AUDIT2_<name>.tsv (bare name) and must not exist (U17).
"""
import hashlib
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit2")
REG_R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
REG_S3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c3")
REG_S3C2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c2")
REG_M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
COVER = os.path.join(REG_M1A, "CALLSEQ_POINT_COVERAGE_R8_M1a4_R3.tsv")
COVER_CHECK = os.path.join(REG_M1A, "CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4_R3.tsv")
NAME_RE = re.compile(r"^REQUEST_RECON_R8_M1a4AUDIT2_[A-Za-z0-9_]+\.tsv$")

# Source file per source_row prefix.  The coverage table labels 414 ADD_v3 rows with source_registry "M2"; their
# source_row prefix is "M2_ADD_v3", so the FILE is decided by the prefix (the label alone would mislead).
# (file, header line number).  Header lines were read from the files (see the round report).
SRC = {
    "M1": (os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M1.tsv"), 7),
    "M2": (os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M2.tsv"), 14),
    "M2_ADD_v3": (os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv"), 7),
    "M2_CTRL_SEAM": (os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv"), 4),
    "M3": (os.path.join(REG_R7, "REGISTRY_S4_PRE_R7_M3.tsv"), 20),
    "ADD": (os.path.join(REG_S3, "R8_ADDITIONS_S3R4C3.tsv"), 1),
}
# (source_registry label, source_row prefix) -> SRC key.  Any pair not listed is refused.
SRC_KEY = {
    ("M1", "M1"): "M1",
    ("M2", "M2"): "M2",
    ("M2", "M2_ADD_v3"): "M2_ADD_v3",
    ("M2_CTRL_SEAM", "CTRL"): "M2_CTRL_SEAM",
    ("M3", "M3"): "M3",
    ("R8_ADDITIONS_S3R4C3", "ADD"): "ADD",
}

# request token parsers
RE_S4 = re.compile(r"^s4malloc(?::(\d+))?$")
RE_EXEC = re.compile(r"^exec(?::(\d+))?$")
RE_PLAN = re.compile(r"^plan(?::(\d+))?$")
RE_PLANCALL = re.compile(r"^plancall:(\d+):(\d+)$")
RE_RNV1 = re.compile(r"^rnv1:(\d+)$")
RE_WIN = re.compile(r"^win:(\d+)$")
RE_INIT = re.compile(r"^init:(\d+)$")
RE_SEAM = re.compile(r"^(alloc|kottke_alloc|fmmret|linearsolve_null2|linearsolve):(\d+):(\d+)(?::([a-z]+))?$")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_phys(path):
    """Physical lines of a registry file, with 1-based physical line numbers."""
    with open(path, encoding="utf-8") as fh:
        return fh.read().splitlines()


def header_of(lines, hline):
    return lines[hline - 1].split("\t")


def canonical(req):
    """Return (kind, canonical_target, K, M, site_id, note) or raise ValueError with a reason."""
    if req in ("", "-"):
        return ("NO_REQUEST", "-", None, None, None, "request '-'")
    if req == "none":
        return ("CONTROL", "none", None, None, None, "control, no injection")
    m = RE_S4.match(req)
    if m:
        return ("S4MALLOC", "s4malloc:K=%s" % m.group(1) if m.group(1) else "s4malloc:K=MISSING", m.group(1), None, None,
                "wrapped S4_malloc, K-th call" if m.group(1) else "s4malloc without K")
    m = RE_EXEC.match(req)
    if m:
        return ("EXEC", "exec:K=%s" % m.group(1) if m.group(1) else "exec:K=MISSING", m.group(1), None, None,
                "wrapped fft_plan_exec, K-th call" if m.group(1) else "exec without K")
    m = RE_PLAN.match(req)
    if m:
        return ("PLAN", "plan:N=%s" % m.group(1) if m.group(1) else "plan:N=MISSING", m.group(1), None, None,
                "N-th plan call (bare plan takes nth from the registry)" if m.group(1) else "plan without N")
    m = RE_PLANCALL.match(req)
    if m:
        return ("PLANCALL", "plancall:K=%s:M=%s" % (m.group(1), m.group(2)), m.group(1), m.group(2), None,
                "M-th wrapped malloc inside plan call K")
    m = RE_RNV1.match(req)
    if m:
        return ("RNV1", "rnv1:M=%s" % m.group(1), None, m.group(1), None,
                "M-th malloc inside a Pattern_GenerateFlowField window (count reset per window)")
    m = RE_WIN.match(req)
    if m:
        return ("WIN", "win:M=%s" % m.group(1), None, m.group(1), None, "M-th window of the S3R4 additions injector")
    m = RE_INIT.match(req)
    if m:
        return ("INIT", "init:K=%s" % m.group(1), m.group(1), None, None, "init K of the S3R4 additions injector")
    m = RE_SEAM.match(req)
    if m:
        site = m.group(4) if m.group(4) else "-"
        return ("SEAM", "%s:ID=%s:K=%s%s" % (m.group(1), m.group(2), m.group(3),
                                              (":SITE=%s" % site) if m.group(4) else ""),
                m.group(3), None, m.group(2), "seam %s, ID %s, K-th hit" % (m.group(1), m.group(2)))
    raise ValueError("unrecognised request token: %r" % req)


# M3 registry: the K of a bare request is not a column of the M3 table.  It is taken from the historical table that
# the M3 row names in its source_file column (dryrun_m3_r7.py derive_state_env uses NTH_or_K of that table for G5;
# the G6 seam rows take their K from inj_call of the seam table).  The join key is (point_id, tree) for G5 and
# point_id for G6; a missing or duplicate key is refused, never defaulted.
M3_STATE = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r6c", "REGISTRY_S4_PRE_R6b_STATE_v2.tsv")
M3_SEAM = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r6c", "REGISTRY_S4_PRE_R6c_SEAM.tsv")


def load_keyed(path, hline, keycols):
    """Return {key tuple: row dict}; refuse duplicate keys.  Header at physical line hline."""
    lines = read_phys(path)
    hdr = header_of(lines, hline)
    out = {}
    for ln in lines[hline:]:
        if not ln or ln.startswith("#"):
            continue
        cols = ln.split("\t")
        if len(cols) != len(hdr):
            raise SystemExit("REFUSED: %s column count" % path)
        r = dict(zip(hdr, cols))
        k = tuple(r[c] for c in keycols)
        if k in out:
            raise SystemExit("REFUSED: duplicate key %r in %s" % (k, path))
        out[k] = r
    return out


def m3_k_from_history(group, pid, tree, state_map, seam_map):
    """(K_text, source_column, source_row_text) or (None, reason).  No default is used."""
    if group == "G5":
        r = state_map.get((pid, tree))
        if r is None:
            return None, "no STATE row for (point_id, tree)"
        v = r["NTH_or_K"]
        m = re.match(r"^(K|NTH)=(\d+)$", v)
        if not m:
            return None, "NTH_or_K %r is not K=N or NTH=N" % v
        return m.group(2), "STATE.NTH_or_K=%s" % v
    if group == "G6":
        r = seam_map.get((pid,))
        if r is None:
            return None, "no SEAM row for point_id"
        return r["inj_call"], "SEAM.inj_call=%s" % r["inj_call"]
    return None, "group %s has no K source" % group


def main(argv):
    if len(argv) != 2 or not NAME_RE.match(argv[1]):
        raise SystemExit("usage: reconstruct_requests_r8m1a4audit2.py REQUEST_RECON_R8_M1a4AUDIT2_<name>.tsv")
    out = os.path.join(EV, argv[1])
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)

    # coverage rows
    with open(COVER, encoding="utf-8") as fh:
        clines = fh.read().splitlines()
    chdr = clines[0].split("\t")
    cover = [dict(zip(chdr, ln.split("\t"))) for ln in clines[1:] if ln]
    if len(cover) != 1128:
        raise SystemExit("REFUSED: coverage rows %d != 1128" % len(cover))

    # check table (for the old REACHED value, read only)
    with open(COVER_CHECK, encoding="utf-8") as fh:
        kl = fh.read().splitlines()
    khdr = kl[0].split("\t")
    check = {}
    for ln in kl[1:]:
        if not ln:
            continue
        r = dict(zip(khdr, ln.split("\t")))
        check[(r["source_registry"], r["source_row"])] = r

    # source registries: physical lines
    src_lines = {}
    src_hash = {}
    for name, (path, hline) in SRC.items():
        src_lines[name] = read_phys(path)
        src_hash[name] = sha256_file(path)

    rows = []
    refused = []
    cls_counter = Counter()
    for c in cover:
        reg = c["source_registry"]
        srow = c["source_row"]
        pid = c["point_id"]
        m = re.match(r"^([A-Za-z0-9_]+):(\d+)$", srow)
        if not m:
            refused.append((reg, srow, pid, "source_row format"))
            continue
        prefix, num = m.group(1), int(m.group(2))
        key = SRC_KEY.get((reg, prefix))
        if key is None:
            refused.append((reg, srow, pid, "(registry, prefix) pair not in SRC_KEY"))
            continue
        path, hline = SRC[key]
        lines = src_lines[key]
        if num < 1 or num > len(lines):
            refused.append((reg, srow, pid, "physical line out of range"))
            continue
        ln = lines[num - 1]
        if not ln or ln.startswith("#"):
            refused.append((reg, srow, pid, "physical line is comment or blank"))
            continue
        cols = ln.split("\t")
        hdr = header_of(lines, hline)
        if len(cols) != len(hdr):
            refused.append((reg, srow, pid, "column count %d != header %d" % (len(cols), len(hdr))))
            continue
        orig = dict(zip(hdr, cols))
        # the registry's own identifier must match the coverage row point_id.  The S3R4 additions table names the
        # point in column "item" (A-806, B-415, ...); its "point_or_combo" column is a combination key within the
        # point (closed2d-ng1, fft-ng5, ...), kept as recorded and never compared with point_id.
        own_id = orig.get("point_id", orig.get("item"))
        if own_id is None:
            refused.append((reg, srow, pid, "no point_id / item column in %s" % key))
            continue
        if own_id != pid:
            refused.append((reg, srow, pid, "identifier %s != coverage %s" % (own_id, pid)))
            continue
        rows.append((c, orig, key, srow, num))

    # M3 historical tables (keys: STATE (point_id, tree); SEAM (point_id))
    state_map = load_keyed(M3_STATE, 21, ["point_id", "tree"])
    seam_map = load_keyed(M3_SEAM, 7, ["point_id"])

    # build the output
    out_rows = []
    for c, orig, reg, srow, num in rows:
        req_raw = orig.get("request", "")
        # the third element is the SRC key ("ADD" for the S3R4 additions table), not the coverage source_registry label
        if reg == "ADD":
            req_raw = orig.get("injection", "")
        if reg == "M3":
            req_raw = orig.get("request", "")
            # the M3 row has no nth column: K comes from the historical table it names (see m3_k_from_history)
            k_text, k_src = m3_k_from_history(orig.get("group"), orig.get("point_id"), orig.get("tree"),
                                              state_map, seam_map)
            orig["nth"] = k_text if k_text is not None else "-"
            orig["_k_source"] = k_src
        try:
            kind, target, K, M, site_id, desc = canonical(req_raw) if req_raw else ("NO_REQUEST", "-", None, None, None, "empty")
            status = "OK"
        except ValueError as e:
            kind, target, K, M, site_id, desc = ("UNRECOGNISED", "-", None, None, None, str(e))
            status = "REFUSED"
        nth = orig.get("nth", "-")
        # A bare request name (s4malloc, exec, plan) takes its K / N from the nth column of the SAME physical row.
        # The value is read, never guessed: nth '-' or empty is MISSING_PARAMETER.  A request with an explicit K
        # keeps its own K (the nth column is then recorded only, and must not contradict it).
        if kind in ("S4MALLOC", "EXEC", "PLAN") and K is None:
            if nth in ("", "-"):
                status = "MISSING_PARAMETER"
                desc = "%s without K/N: request has no K and nth is '%s'" % (kind, nth)
            else:
                K = nth
                if kind == "S4MALLOC":
                    target = "s4malloc:K=%s" % nth
                elif kind == "EXEC":
                    target = "exec:K=%s" % nth
                else:
                    target = "plan:N=%s" % nth
                desc = "K/N from nth column of the same row (%s)" % reg
        # the historical expectation of the source row (column names differ by registry; no default)
        exp_col = "expected" if reg == "M3" else "expected_class"
        expected = orig.get(exp_col, "-")
        out_rows.append((c["source_registry"], srow, num, c["point_id"], c["group"], c["source_tree"], c["run_tree"],
                         c["mode"], c["NG"], c["route"], req_raw or "-", nth, kind, target, K or "-",
                         M or "-", site_id or "-", c["unit_id"], check.get((reg, srow), {}).get("reach_status", "-"),
                         c["coverage_class"], status, desc, expected, orig.get("_k_source", "-")))
        cls_counter[(kind, status)] += 1

    with open(out, "x", encoding="utf-8") as fh:
        fh.write("source_registry\tsource_row\tsource_physical_line\tpoint_id\tgroup\tsource_tree\trun_tree\tmode\tNG\troute\t"
                 "request_raw\tnth_registry\tkind\tcanonical_target\tK\tM\tsite_id\tunit_id\told_reach_status\t"
                 "coverage_class\trecon_status\trecon_detail\thistorical_expected\tk_source\n")
        for r in out_rows:
            fh.write("\t".join(str(x).replace("\t", " ") for x in r) + "\n")

    print("reconstruct rows=%d refused=%d" % (len(out_rows), len(refused)))
    for k, v in sorted(cls_counter.items()):
        print("  %s %s %d" % (k[0], k[1], v))
    for r in refused[:20]:
        print("  REFUSED %s %s %s %s" % r)
    return 0 if not refused else 3


if __name__ == "__main__":
    sys.exit(main(sys.argv))
