#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2), section 2 classification.  New file.

Read only.  Input: the reconstruction table REQUEST_RECON_R8_M1a4AUDIT2_<name>.tsv (one row per source row, 1128),
the post-hoc validated unit event logs (events.tsv under callseq_r8m1a4_r3/<unit>/), and the old coverage check (read
only, for the comparison column).

For each source row the canonical target is checked against the unit's event counts, with the counting rule of the
injector (see the round report, section 2):
  S4MALLOC K  : max seq of S4MALLOC events >= K                      (global count)
  EXEC K      : max seq of EXEC events >= K                          (global count)
  PLAN N      : max seq of PLAN_START events >= N                    (N-th plan call)
  PLANCALL K:M: max sub_seq of PLAN_MALLOC events with seq == K >= M (M-th malloc in plan call K)
  RNV1 M      : some window has max sub_seq of WIN_MALLOC >= M       (per-window count; first window reaching M)
  WIN M       : max seq of WIN_OPEN events >= M                     (S3R4 additions window count)
  SEAM ID K   : max seq of SEAM events with sub_seq == ID and func == hook >= K  (per-ID count)
  CONTROL / NO_REQUEST : CONTROL_NA (no injection, nothing to reach)
A row whose K/M is MISSING_PARAMETER in the reconstruction is EVIDENCE_INSUFFICIENT (no default, no guess).
A row whose unit is not in the post-hoc validated set is EVIDENCE_INSUFFICIENT.

Status vocabulary: REACHED / EXPECTED_NOT_REACHED / UNEXPECTED_NOT_REACHED / NOW_REACHED_WAS_NOT_REACHED /
CONTROL_NA / ADDITION_SECTION7 / EVIDENCE_INSUFFICIENT.
  EXPECTED_NOT_REACHED is never assigned by this script: no source states that a row is expected not to be reached.
  NOW_REACHED_WAS_NOT_REACHED is assigned when the old coverage check says NOT reached and this check says REACHED.
  UNEXPECTED_NOT_REACHED is assigned when the old check says REACHED and this check says NOT reached.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/classify_requests_r8m1a4audit2.py RECON_NAME CLASS_NAME
RECON_NAME: REQUEST_RECON_R8_M1a4AUDIT2_<name>.tsv (existing).  CLASS_NAME: REQUEST_TARGETS_R8_M1a4AUDIT2_<name>.tsv (new).
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
COVER_CHECK = os.path.join(REG_M1A, "CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4_R3.tsv")
RECON_RE = re.compile(r"^REQUEST_RECON_R8_M1a4AUDIT2_[A-Za-z0-9_]+\.tsv$")
CLASS_RE = re.compile(r"^REQUEST_TARGETS_R8_M1a4AUDIT2_[A-Za-z0-9_]+\.tsv$")
HOOKS = {"S4_TEST_ALLOC_HOOK", "S4_TEST_KOTTKE_HOOK", "S4_TEST_FMMRET_AFTER", "S4_TEST_LINEARSOLVE_AFTER",
         "S4_TEST_LINEARSOLVE_NULLINFO2_AFTER", "S4_TEST_ADDFIELD_AFTER"}


def read_rows(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        if not ln:
            continue
        cols = ln.split("\t")
        if len(cols) != len(hdr):
            raise SystemExit("REFUSED: reconstruction row column count")
        rows.append(dict(zip(hdr, cols)))
    return hdr, rows


def read_events(uid, cache):
    if uid in cache:
        return cache[uid]
    path = os.path.join(RAW, uid, "events.tsv")
    if not os.path.isfile(path):
        cache[uid] = None
        return None
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    ev = [dict(zip(hdr, ln.split("\t"))) for ln in lines[1:] if ln]
    cache[uid] = ev
    return ev


def check_target(kind, K, M, site, ev, family=None):
    """(reached: bool, evidence_text)."""
    if kind == "S4MALLOC":
        mx = max([int(e["seq"]) for e in ev if e["event_type"] == "S4MALLOC"] or [0])
        return mx >= int(K), "s4malloc_max=%d" % mx
    if kind == "EXEC":
        mx = max([int(e["seq"]) for e in ev if e["event_type"] == "EXEC"] or [0])
        return mx >= int(K), "exec_max=%d" % mx
    if kind == "PLAN":
        mx = max([int(e["seq"]) for e in ev if e["event_type"] == "PLAN_START"] or [0])
        return mx >= int(K), "plan_max=%d" % mx
    if kind == "PLANCALL":
        ks = int(K)
        mx = max([int(e["sub_seq"]) for e in ev if e["event_type"] == "PLAN_MALLOC" and int(e["seq"]) == ks] or [0])
        return mx >= int(M), "plan_%d_malloc_max=%d" % (ks, mx)
    if kind == "RNV1":
        mx = max([int(e["sub_seq"]) for e in ev if e["event_type"] == "WIN_MALLOC"] or [0])
        return mx >= int(M), "win_malloc_max=%d" % mx
    if kind == "WIN":
        mx = max([int(e["seq"]) for e in ev if e["event_type"] == "WIN_OPEN"] or [0])
        return mx >= int(M), "win_open_max=%d" % mx
    if kind == "SEAM":
        # site is the ID (integer text) of the seam hook; family selects the hook name (HOOK_OF_FAMILY)
        if family is None or family not in HOOK_OF_FAMILY:
            raise ValueError("no hook for seam family %r" % family)
        hook = HOOK_OF_FAMILY[family]
        if site in ("", "-", None):
            raise ValueError("seam row without ID")
        mx = max([int(e["seq"]) for e in ev if e["event_type"] == "SEAM" and e["func"] == hook
                  and int(e["sub_seq"]) == int(site)] or [0])
        return mx >= int(K), "seam_max=%d hook=%s" % (mx, hook)
    raise ValueError("no check for kind %s" % kind)


# seam request family -> the hook name in callseq_r8m1a4_gdb.py (setup_breakpoints) that counts it
HOOK_OF_FAMILY = {
    "alloc": "S4_TEST_ALLOC_HOOK",
    "kottke_alloc": "S4_TEST_KOTTKE_HOOK",
    "fmmret": "S4_TEST_FMMRET_AFTER",
    "linearsolve": "S4_TEST_LINEARSOLVE_AFTER",
    "linearsolve_null2": "S4_TEST_LINEARSOLVE_NULLINFO2_AFTER",
}


def site_hook(site):
    """site is the text 'FAMILY:ID=<n>:K=<k>[:SITE=<s>]' built by reconstruct_requests (site_id holds 'ID')."""
    return None


def hook_of_row(family, _site):
    return HOOK_OF_FAMILY.get(family)


def main(argv):
    if len(argv) != 3 or not RECON_RE.match(argv[1]) or not CLASS_RE.match(argv[2]):
        raise SystemExit("usage: classify_requests_r8m1a4audit2.py REQUEST_RECON_R8_M1a4AUDIT2_<name>.tsv REQUEST_TARGETS_R8_M1a4AUDIT2_<name>.tsv")
    recon_path = os.path.join(EV, argv[1])
    out = os.path.join(EV, argv[2])
    if not os.path.isfile(recon_path):
        raise SystemExit("REFUSED: reconstruction table missing: %s" % recon_path)
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    hdr, rows = read_rows(recon_path)
    if len(rows) != 1128:
        raise SystemExit("REFUSED: reconstruction rows %d != 1128" % len(rows))

    # old coverage check (for the comparison column; read only)
    with open(COVER_CHECK, encoding="utf-8") as fh:
        kl = fh.read().splitlines()
    khdr = kl[0].split("\t")
    old = {}
    for ln in kl[1:]:
        if not ln:
            continue
        r = dict(zip(khdr, ln.split("\t")))
        old[(r["source_registry"], r["source_row"])] = r["reach_status"]

    cache = {}
    cnt = Counter()
    out_rows = []
    for r in rows:
        key = (r["source_registry"], r["source_row"])
        old_status = old.get(key, "-")
        kind = r["kind"]
        recon = r["recon_status"]
        uid = r["unit_id"]
        target = r["canonical_target"]
        K = r["K"]
        M = r["M"]
        site = r["site_id"]
        detail = ""
        if kind in ("CONTROL", "NO_REQUEST"):
            status = "CONTROL_NA"
            detail = "no injection"
        elif r["source_registry"] == "R8_ADDITIONS_S3R4C3":
            status = "ADDITION_SECTION7"
            detail = "S3R4 additions: reviewed in section 5, not by this check"
        elif recon != "OK":
            status = "EVIDENCE_INSUFFICIENT"
            detail = "reconstruction: %s" % recon
        else:
            ev = read_events(uid, cache)
            family = r["request_raw"].split(":", 1)[0] if r["request_raw"] else None
            if ev is None:
                status = "EVIDENCE_INSUFFICIENT"
                detail = "no events for unit %s" % uid
            else:
                try:
                    reached, ev_text = check_target(kind, K if K != "-" else None, M if M != "-" else None,
                                                    site, ev, family)
                except (TypeError, ValueError) as e:
                    status = "EVIDENCE_INSUFFICIENT"
                    detail = "check error: %s" % e
                else:
                    detail = ev_text
                    expected = r.get("historical_expected", "-")
                    if reached and expected == "INVALID_NOT_REACHED":
                        # the historical class says the injection is not reached; this count reaches it.  It is listed
                        # separately (task 2) and is never merged into REACHED.
                        status = "NOW_REACHED_WAS_NOT_REACHED"
                        detail = ev_text + "; historical INVALID_NOT_REACHED (R3 class, not run)"
                    elif reached and old_status == "REACHED":
                        status = "REACHED"
                    elif reached:
                        # the old check did not record REACHED; this check does: reported separately (task 2)
                        status = "NOW_REACHED_WAS_NOT_REACHED"
                    elif old_status == "REACHED":
                        status = "UNEXPECTED_NOT_REACHED"
                    else:
                        # neither check reaches it; no source states that the point is expected not to be reached,
                        # so it is a coverage gap, not an expected result
                        status = "UNEXPECTED_NOT_REACHED"
        cnt[status] += 1
        out_rows.append((r["source_registry"], r["source_row"], r["point_id"], r["group"], r["run_tree"], r["mode"],
                         r["NG"], r["route"], r["request_raw"], kind, target, K, M, site, uid, old_status,
                         status, detail))

    with open(out, "x", encoding="utf-8") as fh:
        fh.write("source_registry\tsource_row\tpoint_id\tgroup\trun_tree\tmode\tNG\troute\trequest_raw\tkind\t"
                 "canonical_target\tK\tM\tsite_id\tunit_id\told_reach_status\tstatus\tdetail\n")
        for o in out_rows:
            fh.write("\t".join(str(x).replace("\t", " ") for x in o) + "\n")
    print("classify rows=%d" % len(out_rows))
    for k, v in sorted(cnt.items()):
        print("  %s %d" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
