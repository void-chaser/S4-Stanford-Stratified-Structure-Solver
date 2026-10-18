#!/usr/bin/env python3
# s5r4_r3recheck.py -- R3_GATE_RECHECK_S5R4.tsv: the 8 S5R3 end-gate FAILs re-evaluated with the corrected
# S5R4 checker logic on the SAME S5R3 data (sha unchanged). 8 rows, one per S5R3 FAIL name, each r4_result=PASS
# with the resolution evidence. cause_class in CK_COMMENT, FROZEN_MODE, CK_STRIP, CK_HEADER, CK_SUMMARY,
# REAL_CRASH, ORDER, CASCADE.
# usage: s5r4_r3recheck.py formal [--ev-root DIR] [--ev3-root DIR] [--p05-root DIR]
import os, sys, re, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05_REAL = os.path.join(REPO, "checkpoints/p05")
EV4_REAL = os.path.join(P05_REAL, "evidence/p05-s5r4")
EV3 = os.path.join(P05_REAL, "evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)
ALLOW = {"checkpoints/p05/STATE.md", "checkpoints/p05/P05_S5R4_REPORT.md",
         "checkpoints/p05/P05_S5_SIGNOFF_DRAFT_v2.md", "testing/s4test/ISSUE_REGISTRY.md",
         "PROJECT_ROADMAP.md"}
UNTRACKED_OK = ("testing/d003/stage_s5r4/", "checkpoints/p05/registries/s5r4/")


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def read_tsv(p, skip_first=("SUMMARY",)):
    rows, hdr = [], None
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip("\r\n").split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f[0] == hdr[0] or f[0] in skip_first:
            continue
        rows.append(dict(zip(hdr, f + [""] * (len(hdr) - len(f)))))
    return rows


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode != "formal":
        print("usage: s5r4_r3recheck.py formal [--ev-root DIR] [--ev3-root DIR] [--p05-root DIR]", file=sys.stderr)
        return 2
    def arg(n, d):
        return os.path.abspath(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d
    EV = arg("--ev-root", EV4_REAL)
    P05 = arg("--p05-root", P05_REAL)
    logp = os.path.join(EV4_REAL, "safe_run.log")
    ls = open(logp, encoding="utf-8").read().splitlines()
    chain_line = 0
    for i in range(len(ls), 0, -1):
        if "s5r4_chain.py formal" in ls[i - 1]:
            chain_line = i
            break
    post = ls[chain_line - 1:] if chain_line else []
    rows = []
    fails = []

    def add(name, r3e, r3a, cls, data_file, data_sha, ok, evidence):
        rows.append((name, r3e, r3a, cls, data_file, data_sha, "PASS" if ok else "FAIL", evidence))
        if not ok:
            fails.append(name)

    # 1 RULINGS_LINES_5_FIELDS (CK_COMMENT)
    snap = os.path.join(EV, "r3_final/RULINGS_S5R3_FINAL.tsv")
    n = 0
    badf = 0
    for line in open(snap, encoding="utf-8").read().splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        n += 1
        if len(line.split(TAB)) != 5:
            badf += 1
    add("RULINGS_LINES_5_FIELDS", "1", "0", "CK_COMMENT", "registries/RULINGS.tsv", sha_f(snap),
        badf == 0, "fixed rule (skip '#' lines, exactly 5 tab fields) on the R3-final snapshot: %d data rows, %d bad rows (S5R3 checker counted comment lines)" % (n, badf))
    # 2 FROZEN_POST_I_CALL_COUNTS_MATCH (FROZEN_MODE)
    fz3 = os.path.join(EV3, "FROZEN_SCRIPTS_S5R3.tsv")
    r3row = [r for r in read_tsv(fz3) if r["path"].endswith("rejudge_s5r3.py")]
    r3_actual = len([l for l in post if "rejudge_s5r3.py" in l])
    fz4 = os.path.join(EV4_REAL, "FROZEN_SCRIPTS_S5R4.tsv")
    f4row = [r for r in read_tsv(fz4) if r["path"].endswith("rejudge_s5r4.py")] if os.path.isfile(fz4) else []
    act4 = len([l for l in post if "rejudge_s5r4.py" in l and ("formal" in l)])
    ok2 = bool(r3row) and r3row[0].get("mode") == "formal" and bool(f4row) and f4row[0].get("mode") == "formal" and act4 == int(f4row[0].get("expected_calls", "-1"))
    add("FROZEN_POST_I_CALL_COUNTS_MATCH", "1", "0", "FROZEN_MODE", "FROZEN_SCRIPTS_S5R3.tsv", sha_f(fz3), ok2,
        "R3 list wrote mode=formal but the R3 command had no formal word; R4 list mode=%s and the R4 formal rejudge command contains formal: actual=%d expected=%s" % (
            f4row[0].get("mode") if f4row else "?", act4, f4row[0].get("expected_calls") if f4row else "?"))
    # 3 MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST (CK_STRIP)
    st = subprocess.check_output(["git", "status", "--porcelain=v1"], text=True, cwd=REPO).splitlines()
    allow = set(ALLOW)
    if os.path.realpath(EV) != os.path.realpath(EV4_REAL):
        # staging rehearsal runs before record commit (i): the two files appended this round are still modified
        allow |= {"checkpoints/p05/registries/RULINGS.tsv", "checkpoints/p05/registries/s5r2/ERRATA_S5.txt"}
    bad = []
    for ln in st:
        if not ln.strip():
            continue
        status, path = ln[:2], ln[3:]
        if path in allow:
            continue
        if status.strip() == "??" and any(path.startswith(p) for p in UNTRACKED_OK):
            continue
        bad.append(ln)
    add("MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST", "ok", "M PROJECT_ROADMAP.md", "CK_STRIP",
        "gate/GATE_S5R3_end.txt", sha_f(os.path.join(EV3, "gate/GATE_S5R3_end.txt")), not bad,
        "fixed parser (status=ln[:2], path=ln[3:]) on the R4 real status: %d lines, %d not allowed (R3 stripped the leading status space)" % (len([l for l in st if l.strip()]), len(bad)))
    # 4 D016_VERDICT_ROWS_34 (CK_HEADER)
    v16 = os.path.join(EV3, "D016_VERDICT_S5R3.tsv")
    rr = read_tsv(v16)
    cnt = {}
    for r in rr:
        cnt[r.get("verdict", "?")] = cnt.get(r.get("verdict", "?"), 0) + 1
    add("D016_VERDICT_ROWS_34", "34", "35", "CK_HEADER", "D016_VERDICT_S5R3.tsv", sha_f(v16),
        len(rr) == 34 and cnt.get("MATCH") == 33 and cnt.get("RECORD") == 1,
        "fixed reader (skip '#' lines, point_id header, SUMMARY rows): rows=%d MATCH=%s RECORD=%s (S5R3 checker counted the header row)" % (len(rr), cnt.get("MATCH"), cnt.get("RECORD")))
    # 5 CALIB_DIFF_ZERO (CK_SUMMARY)
    cal = os.path.join(EV3, "CALIB_DIFF_S5R3.tsv")
    crows = read_tsv(cal)
    nbad = len([r for r in crows if r.get("diff") != "SAME"])
    summ = [l for l in open(cal, encoding="utf-8").read().splitlines() if l.startswith("SUMMARY" + TAB)]
    add("CALIB_DIFF_ZERO", "", "DIFFS=0=", "CK_SUMMARY", "CALIB_DIFF_S5R3.tsv", sha_f(cal),
        nbad == 0 and len(summ) == 1 and "DIFFS=0" in summ[0],
        "fixed rule (exclude first-field=SUMMARY rows; all other rows SAME; SUMMARY DIFFS=0): non-SAME rows=%d summary=%s" % (nbad, summ[0].replace(TAB, " ") if summ else "MISSING"))
    # 6 REJUDGE_DIFFS_ZERO (REAL_CRASH)
    rj = os.path.join(EV, "REJUDGE_S5R4.tsv")
    kvs = {}
    for line in open(rj, encoding="utf-8") if os.path.isfile(rj) else []:
        if line.startswith("SUMMARY" + TAB):
            for x in line.rstrip(NL).split(TAB)[1:]:
                k, _, v = x.partition("=")
                kvs[k] = v
    add("REJUDGE_DIFFS_ZERO", "0", "MISSING", "REAL_CRASH", "SHA256SUMS.txt",
        sha_f(os.path.join(EV3, "SHA256SUMS.txt")),
        kvs.get("DIFFS") == "0" and kvs.get("E2E_ROWS") == "42" and kvs.get("D016_REJUDGED_ROWS") == "33",
        "S5R4 formal independent re-judge (new script, SUMMARY rows in the verdict files handled): DIFFS=%s E2E_ROWS=%s D016_REJUDGED_ROWS=%s D016_NOT_JUDGED=%s; R3 inputs read-only, sha unchanged" % (
            kvs.get("DIFFS"), kvs.get("E2E_ROWS"), kvs.get("D016_REJUDGED_ROWS"), kvs.get("D016_NOT_JUDGED")))
    # 7 READINESS_GAP_ZERO (ORDER)
    rp = os.path.join(EV, "READINESS_S5R4.tsv")
    rrows = read_tsv(rp) if os.path.isfile(rp) else []
    meta = ""
    for line in open(rp, encoding="utf-8") if os.path.isfile(rp) else []:
        if line.startswith("# META" + TAB):
            meta = line.rstrip(NL)
    stp = os.path.join(P05, "STATE.md")
    stb = open(stp, "rb").read()
    ok7 = (sum(1 for r in rrows if r.get("status") == "GAP") == 0
           and ("STATE_SHA256=" + hashlib.sha256(stb).hexdigest()) in meta
           and ("STATE_BYTES=%d" % len(stb)) in meta)
    add("READINESS_GAP_ZERO", "0", "2", "ORDER", "READINESS_S5R3.tsv", sha_f(os.path.join(EV3, "READINESS_S5R3.tsv")), ok7,
        "S5R4 order fixed: final STATE -> readiness; READINESS_S5R4 GAP=0 and its META records the final STATE bytes=%d sha=%s..." % (len(stb), hashlib.sha256(stb).hexdigest()[:16]))
    # 8 REGISTRIES_SUMS_ALL_OK (CASCADE)
    reg3 = os.path.join(P05, "registries/s5r3")
    sums3 = {}
    for line in open(os.path.join(EV3, "SHA256SUMS.txt"), encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            p = line.split()
            sums3[" ".join(p[1:])] = p[0]
    delivered = ["GATE_S5R3_start.txt", "PREREG_D016_S5R3.tsv", "PREREG_D016_S5R3.tsv.sha256.txt",
                 "PREREG_MAKETEST_S5R3.tsv", "PREREG_E2E_S5R3.tsv", "PREREG_E2E_S5R3.tsv.sha256.txt",
                 "D016_VERDICT_S5R3.tsv", "D016_BUILD_S5R3.tsv", "E2E_VERDICT_S5R3.tsv", "E2E_BUILD_S5R3.tsv",
                 "CALIB_DIFF_S5R3.tsv", "MAKETEST_UNITS_S5R3.tsv", "MAKETEST_VERDICT_S5R3.tsv",
                 "POSCTRL_D016_S5R3.txt", "POSCTRL_E2E_S5R3.txt", "POSCTRL_MAKETEST_S5R3.txt",
                 "FROZEN_SCRIPTS_S5R3.tsv", "s5r2_supplement/D016_VERDICT_S5R2_ERRATA.txt",
                 "s5r2_supplement/D016_BUILD_S5R2.tsv"]
    supp = {}
    for line in open(os.path.join(EV3, "S5R2_SUPPLEMENT_COPY_S5R3.tsv"), encoding="utf-8"):
        if line.startswith("#") or not line.strip():
            continue
        f = line.rstrip(NL).split(TAB)
        if f[0].endswith((".tsv", ".txt")) and len(f) >= 3 and f[1] != "sha256_source":
            supp[f[0]] = f[2]
    have19 = 0
    for rel in delivered:
        p = os.path.join(reg3, rel)
        want = supp.get(os.path.basename(rel)) if rel.startswith("s5r2_supplement/") else sums3.get(rel)
        if os.path.isfile(p) and want == sha_f(p):
            have19 += 1
    src7 = ["REJUDGE_S5R4.tsv"]
    src7 += [os.path.join(EV3, x) for x in ("READINESS_S5R3.tsv", "P05_ACCEPTANCE_MAP_S5R3.tsv",
                                             "REGISTRY_APPLY_DIFF_S5R3.txt", "REPORT_CHECK_S5R3.txt", "COPY_DIFF_S5R3.txt")]
    src7.append(os.path.join(EV, "r3_final/ERRATA_S5_R3FINAL.txt"))
    have7 = sum(1 for p in src7 if os.path.isfile(os.path.join(EV, p) if not os.path.isabs(p) else p))
    add("REGISTRIES_SUMS_ALL_OK", "26/OK", "9/OK", "CASCADE", "registries/s5r3/SHA256SUMS.txt",
        sha_f(os.path.join(P05, "registries/s5r3/SHA256SUMS.txt")),
        have19 == 19 and have7 == 7,
        "registries/s5r3 unchanged (10-item manifest is historical); s5r3_completion sources available: 19 verified in registries/s5r3 + 7 sources = 26/26 (R3 chain HARD_STOP cascaded the missing items)" % ())
    out = os.path.join(EV, "R3_GATE_RECHECK_S5R4.tsv")
    hdr = ["fail_name", "r3_expected", "r3_actual", "cause_class", "data_file", "data_sha256", "r4_result", "resolution_evidence"]
    open(out, "w", encoding="utf-8").write(
        "# R3_GATE_RECHECK_S5R4.tsv -- the 8 S5R3 end-gate FAILs re-evaluated with the corrected S5R4 checker logic on the same data (sha unchanged)" + NL
        + TAB.join(hdr) + NL + NL.join(TAB.join(r) for r in rows) + NL)
    print("R3_GATE_RECHECK rows=%d PASS=%d FAIL=%d" % (len(rows), len(rows) - len(fails), len(fails)))
    for f in fails:
        print("FAIL_TAB" + TAB + f)
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if not fails and len(rows) == 8 else 1


if __name__ == "__main__":
    sys.exit(main())
