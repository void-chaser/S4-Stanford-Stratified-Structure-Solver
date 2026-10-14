#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 3 (r8m1a4audit3), section 2 classification.  New file.  Read only (writes one table).

Input:
  - REQUEST_RECON_R8_M1a4AUDIT2_RUN6.tsv (audit2 final reconstruction, 1128 rows; not modified)
  - the unit event logs under callseq_r8m1a4_r3/<unit>/events.tsv (post-hoc validated units; unchanged)
  - the old coverage check CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4_R3.tsv (comparison column only)
  - K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv (U189: K of the G5-F2 bare requests; agreed points only)
  - REQUEST_TARGETS_R8_M1a4AUDIT2_RUN3.tsv (audit2 classification; comparison only)

Rules (same as audit2 except as stated):
  S4MALLOC K  : max seq of S4MALLOC events >= K
  EXEC K      : max seq of EXEC events >= K
  PLAN N      : (U188) the N-th plan call contains >= N PLAN_MALLOC events, i.e. max sub_seq of PLAN_MALLOC with seq == N >= N.
                Injector: nth() is used for both the plan-call count and the malloc-in-call count (inject_r4_plan.cpp:38, 79-84, 587).
  PLANCALL K:M: max sub_seq of PLAN_MALLOC with seq == K >= M
  RNV1 M      : max sub_seq of WIN_MALLOC >= M
  WIN M       : max seq of WIN_OPEN >= M
  SEAM ID K   : max seq of SEAM events with func == hook and sub_seq == ID >= K
  CONTROL / NO_REQUEST : CONTROL_NA
A row whose K or N is missing (reconstruction MISSING_PARAMETER) is EVIDENCE_INSUFFICIENT, unless K comes from
K_SOURCE_G5F2 with status K_FROM_HISTORY_AGREED (U189); a G5-F2 point not agreed is EVIDENCE_INSUFFICIENT.

Status vocabulary:
  REACHED / EXPECTED_NOT_REACHED / UNEXPECTED_NOT_REACHED / NOW_REACHED_WAS_NOT_REACHED / CONTROL_NA / ADDITION_SECTION7 /
  EVIDENCE_INSUFFICIENT.
  EXPECTED_NOT_REACHED: the historical class is INVALID_NOT_REACHED and this count also does not reach (U188: same count).
  NOW_REACHED_WAS_NOT_REACHED: historical INVALID_NOT_REACHED but this count reaches (conflict; listed, not merged).
  UNEXPECTED_NOT_REACHED: the old check says REACHED and this count does not reach (the stop condition of part 3).

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/classify_requests_r8m1a4audit3.py REQUEST_TARGETS_R8_M1a4AUDIT3.tsv
"""
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVR = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
EV = os.path.join(EVR, "m1a4audit3")
EV2 = os.path.join(EVR, "m1a4audit2")
RAW = os.path.join(EVR, "callseq_r8m1a4_r3")
REG_M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
COVER_CHECK = os.path.join(REG_M1A, "CALLSEQ_POINT_COVERAGE_CHECK_R8_M1a4_R3.tsv")
RECON = os.path.join(EV2, "REQUEST_RECON_R8_M1a4AUDIT2_RUN6.tsv")
AUDIT2_TGT = os.path.join(EV2, "REQUEST_TARGETS_R8_M1a4AUDIT2_RUN3.tsv")
KSRC = os.path.join(EV, "K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv")
OUT_RE = re.compile(r"^REQUEST_TARGETS_R8_M1a4AUDIT3(_[A-Za-z0-9_]+)?\.tsv$")
HOOK_OF_FAMILY = {
    "alloc": "S4_TEST_ALLOC_HOOK",
    "kottke_alloc": "S4_TEST_KOTTKE_HOOK",
    "fmmret": "S4_TEST_FMMRET_AFTER",
    "linearsolve": "S4_TEST_LINEARSOLVE_AFTER",
    "linearsolve_null2": "S4_TEST_LINEARSOLVE_NULLINFO2_AFTER",
    "addfield": "S4_TEST_ADDFIELD_AFTER",
}


def read_table(path):
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = lines[0].split("\t")
    rows = []
    for ln in lines[1:]:
        if not ln:
            continue
        cols = ln.split("\t")
        if len(cols) != len(hdr):
            raise SystemExit("REFUSED: column count in %s" % path)
        rows.append(dict(zip(hdr, cols)))
    return rows


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


def check_target(kind, K, M, site, ev, family):
    if kind == "S4MALLOC":
        mx = max([int(e["seq"]) for e in ev if e["event_type"] == "S4MALLOC"] or [0])
        return mx >= int(K), "s4malloc_max=%d" % mx
    if kind == "EXEC":
        mx = max([int(e["seq"]) for e in ev if e["event_type"] == "EXEC"] or [0])
        return mx >= int(K), "exec_max=%d" % mx
    if kind == "PLAN":
        # U188: the N-th plan call must contain at least N PLAN_MALLOC events (malloc count inside call N)
        n = int(K)
        mx = max([int(e["sub_seq"]) for e in ev if e["event_type"] == "PLAN_MALLOC" and int(e["seq"]) == n] or [0])
        return mx >= n, "plan_%d_malloc_max=%d" % (n, mx)
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
        if family not in HOOK_OF_FAMILY:
            raise ValueError("no hook for seam family %r" % family)
        hook = HOOK_OF_FAMILY[family]
        mx = max([int(e["seq"]) for e in ev if e["event_type"] == "SEAM" and e["func"] == hook
                  and int(e["sub_seq"]) == int(site)] or [0])
        return mx >= int(K), "seam_max=%d hook=%s" % (mx, hook)
    raise ValueError("no check for kind %s" % kind)


def load_ksource():
    rows = read_table(KSRC)
    out = {}
    for r in rows:
        out[r["point_id"]] = r
    return out


def main(argv):
    if len(argv) != 2 or not OUT_RE.match(argv[1]):
        raise SystemExit("usage: classify_requests_r8m1a4audit3.py REQUEST_TARGETS_R8_M1a4AUDIT3[_name].tsv")
    out = os.path.join(EV, argv[1])
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)
    recon = read_table(RECON)
    if len(recon) != 1128:
        raise SystemExit("REFUSED: reconstruction rows %d != 1128" % len(recon))
    kmap = load_ksource()

    with open(COVER_CHECK, encoding="utf-8") as fh:
        kl = fh.read().splitlines()
    khdr = kl[0].split("\t")
    old = {}
    for ln in kl[1:]:
        if not ln:
            continue
        r = dict(zip(khdr, ln.split("\t")))
        old[(r["source_registry"], r["source_row"])] = r["reach_status"]
    a2 = {}
    for r in read_table(AUDIT2_TGT):
        a2[(r["source_registry"], r["source_row"])] = r["status"]

    cache = {}
    cnt = Counter()
    rows_out = []
    for r in recon:
        key = (r["source_registry"], r["source_row"])
        old_status = old.get(key, "-")
        kind = r["kind"]
        recon_status = r["recon_status"]
        uid = r["unit_id"]
        K = r["K"]
        M = r["M"]
        site = r["site_id"]
        detail = ""
        family = r["request_raw"].split(":", 1)[0] if r["request_raw"] else None
        k_src = "-"
        if kind in ("CONTROL", "NO_REQUEST"):
            status = "CONTROL_NA"
            detail = "no injection"
        elif r["source_registry"] == "R8_ADDITIONS_S3R4C3":
            status = "ADDITION_SECTION7"
            detail = "S3R4 additions: reviewed in section 5, not by this check"
        else:
            # U189: G5-F2 bare requests take K from the agreed history value
            if r["group"] == "G5" and r["source_tree"] == "F2" and kind in ("S4MALLOC", "EXEC", "PLAN") and K in ("-", "", "MISSING"):
                ks = kmap.get(r["point_id"])
                if ks is not None and ks["status"] == "K_FROM_HISTORY_AGREED":
                    K = ks["K"]
                    k_src = "K_SOURCE_G5F2:%s" % ks["detail"]
                else:
                    detail = "G5-F2 K not agreed: %s" % (ks["detail"] if ks else "point not in K_SOURCE table")
                    k_src = "K_SOURCE_G5F2:EVIDENCE_INSUFFICIENT"
            if recon_status != "OK" and k_src == "-":
                status = "EVIDENCE_INSUFFICIENT"
                detail = detail or ("reconstruction: %s" % recon_status)
            elif k_src.endswith("EVIDENCE_INSUFFICIENT"):
                status = "EVIDENCE_INSUFFICIENT"
            else:
                ev = read_events(uid, cache)
                if ev is None:
                    status = "EVIDENCE_INSUFFICIENT"
                    detail = "no events for unit %s" % uid
                else:
                    try:
                        reached, ev_text = check_target(kind, K if K not in ("-", "") else None,
                                                        M if M not in ("-", "") else None, site, ev, family)
                    except (TypeError, ValueError) as e:
                        status = "EVIDENCE_INSUFFICIENT"
                        detail = "check error: %s" % e
                    else:
                        detail = ev_text
                        hist = r.get("historical_expected", "-")
                        if kind == "PLAN" and not reached and hist == "INVALID_NOT_REACHED":
                            status = "EXPECTED_NOT_REACHED"
                            detail += "; U188: same count as historical INVALID_NOT_REACHED"
                        elif reached and hist == "INVALID_NOT_REACHED":
                            status = "NOW_REACHED_WAS_NOT_REACHED"
                            detail += "; historical INVALID_NOT_REACHED but this count reaches (listed, not merged)"
                        elif reached and old_status == "REACHED":
                            status = "REACHED"
                        elif reached:
                            status = "NOW_REACHED_WAS_NOT_REACHED"
                        elif old_status == "REACHED":
                            status = "UNEXPECTED_NOT_REACHED"
                        else:
                            status = "UNEXPECTED_NOT_REACHED"
        cnt[status] += 1
        rows_out.append((r["source_registry"], r["source_row"], r["point_id"], r["group"], r["source_tree"],
                         r["mode"], r["NG"], r["route"], r["request_raw"], kind, r["canonical_target"], K, M, site,
                         uid, old_status, a2.get(key, "-"), status, k_src, detail))

    with open(out, "x", encoding="utf-8") as fh:
        fh.write("source_registry\tsource_row\tpoint_id\tgroup\tsource_tree\tmode\tNG\troute\trequest_raw\tkind\t"
                 "canonical_target\tK\tM\tsite_id\tunit_id\told_reach_status\taudit2_status\tstatus\tk_source\tdetail\n")
        for o in rows_out:
            fh.write("\t".join(str(x).replace("\t", " ") for x in o) + "\n")
    print("classify rows=%d" % len(rows_out))
    for k, v in sorted(cnt.items()):
        print("  %s %d" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
