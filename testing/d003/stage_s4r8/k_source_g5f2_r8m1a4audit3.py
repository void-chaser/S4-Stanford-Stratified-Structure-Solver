#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 3 (r8m1a4audit3): U189 K source for G5-F2 requests.  New file.  Read only.

For each G5 point of tree F2 (177 points), the K is taken from registries/s4r7/M3_F2_RESULTS_R6c_STATE.tsv column NTH_or_K
(key point_id + pass), and cross-checked against the env_as_run field S4FMM_NTH of M3_F2_STATE_R6c_pass1.tsv and
M3_F2_STATE_R6c_pass2.tsv (key: point id in column 2 of each row with kind == point).
  - A K from RESULTS is used only when pass 1 and pass 2 give the same value in all three sources (RESULTS pass 1,
    RESULTS pass 2, env pass 1 S4FMM_NTH and env pass 2 S4FMM_NTH all equal).  Otherwise the point is EVIDENCE_INSUFFICIENT.
  - A missing key, a non-numeric value, or an unreadable file is EVIDENCE_INSUFFICIENT.  No value is guessed.
Writes one table: K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv (one row per point, 177 rows).

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/k_source_g5f2_r8m1a4audit3.py K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EVR = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8")
EV = os.path.join(EVR, "m1a4audit3")
R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
RESULTS = os.path.join(R7, "M3_F2_RESULTS_R6c_STATE.tsv")
PASS1 = os.path.join(R7, "M3_F2_STATE_R6c_pass1.tsv")
PASS2 = os.path.join(R7, "M3_F2_STATE_R6c_pass2.tsv")
OUT_RE = re.compile(r"^K_SOURCE_G5F2_R8_M1a4AUDIT3[A-Za-z0-9_]*\.tsv$")


def table(path, marker):
    """Return (header list, rows list of dict) for the table whose header line starts with marker."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    idx = None
    for i, ln in enumerate(lines):
        if ln.startswith(marker):
            idx = i
            break
    if idx is None:
        raise SystemExit("REFUSED: header not found in %s" % path)
    hdr = lines[idx].split("\t")
    rows = []
    for ln in lines[idx + 1:]:
        if not ln or ln.startswith("#"):
            continue
        cols = ln.split("\t")
        if len(cols) != len(hdr):
            raise SystemExit("REFUSED: column count in %s: %r" % (path, ln[:80]))
        rows.append(dict(zip(hdr, cols)))
    return hdr, rows


def num_of(text):
    m = re.match(r"^(K|NTH)=(\d+)$", text or "")
    return int(m.group(2)) if m else None


def env_nth(env_text):
    m = re.search(r"(?:^|;)S4FMM_NTH=(\d+)(?:;|$)", env_text or "")
    return int(m.group(1)) if m else None


def main(argv):
    if len(argv) != 2 or not OUT_RE.match(argv[1]):
        raise SystemExit("usage: k_source_g5f2_r8m1a4audit3.py K_SOURCE_G5F2_R8_M1a4AUDIT3<name>.tsv")
    out = os.path.join(EV, argv[1])
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)

    _, res_rows = table(RESULTS, "point_id\t")
    res = {}
    for r in res_rows:
        res[(r["point_id"], int(r["pass"]))] = r
    _, p1_rows = table(PASS1, "kind\t")
    _, p2_rows = table(PASS2, "kind\t")
    env1 = {r["id"]: env_nth(r["env_as_run"]) for r in p1_rows if r["kind"] == "point"}
    env2 = {r["id"]: env_nth(r["env_as_run"]) for r in p2_rows if r["kind"] == "point"}

    pids = sorted({k[0] for k in res})
    out_rows = []
    for pid in pids:
        r1 = res.get((pid, 1))
        r2 = res.get((pid, 2))
        k1 = num_of(r1["NTH_or_K"]) if r1 else None
        k2 = num_of(r2["NTH_or_K"]) if r2 else None
        e1 = env1.get(pid)
        e2 = env2.get(pid)
        vals = (k1, k2, e1, e2)
        if None in vals:
            status = "EVIDENCE_INSUFFICIENT"
            k_used = "-"
            why = "missing or non-numeric: res1=%s res2=%s env1=%s env2=%s" % (r1 and r1["NTH_or_K"], r2 and r2["NTH_or_K"], e1, e2)
        elif len(set(vals)) == 1:
            status = "K_FROM_HISTORY_AGREED"
            k_used = str(k1)
            why = "res1=%d res2=%d env1=%d env2=%d" % vals
        else:
            status = "EVIDENCE_INSUFFICIENT"
            k_used = "-"
            why = "disagree: res1=%d res2=%d env1=%d env2=%d" % vals
        out_rows.append((pid, status, k_used, why))

    with open(out, "x", encoding="utf-8") as fh:
        fh.write("point_id\tstatus\tK\tdetail\n")
        for o in out_rows:
            fh.write("\t".join(str(x) for x in o) + "\n")
    cnt = {}
    for o in out_rows:
        cnt[o[1]] = cnt.get(o[1], 0) + 1
    print("points=%d" % len(out_rows))
    for k in sorted(cnt):
        print("  %s %d" % (k, cnt[k]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
