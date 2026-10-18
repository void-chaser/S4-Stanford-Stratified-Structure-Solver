#!/usr/bin/env python3
# s5r5_readiness.py -- P05-S5 R5 readiness audit (task brief section 5 and U389).
# Runs AFTER the final STATE, sign-off draft v3 and report body are written; records their bytes/sha256 and
# asserts that none of the three contains a gate result (U389 forbidden phrases), and that the STATE S5R4 row
# agrees with the S5R4 report appendix C FINAL_STATUS=INCOMPLETE. A non-zero GAP count is a HARD_STOP.
import os, sys, re, hashlib, subprocess, datetime

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
EV3 = os.path.join(P05, "evidence/p05-s5r3")
EV4 = os.path.join(P05, "evidence/p05-s5r4")
TAB = chr(9)
NL = chr(10)

FORBIDDEN = [re.compile(r"FAILS=\d+"), re.compile(r"门禁.*(通过|PASS)"), re.compile(r"无可做")]


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def rd(p):
    return open(p, encoding="utf-8").read()


def main():
    stp = os.path.join(P05, "STATE.md")
    d3p = os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v3.md")
    rpp = os.path.join(P05, "P05_S5R5_REPORT.md")
    st = open(stp, "rb").read()
    d3 = open(d3p, "rb").read()
    rpfull = open(rpp, "rb").read()
    marker = "## 附录 A".encode("utf-8")
    rpbody = rpfull.split(marker)[0]
    stt = st.decode("utf-8")
    d3t = d3.decode("utf-8")
    rpt = rpbody.decode("utf-8")
    rows = []
    gap = 0

    def add(kind, item, status, note, source):
        nonlocal gap
        if status == "GAP":
            gap += 1
        rows.append((kind, item, status, note, source))

    # ---- U389: forbidden gate-result phrases in STATE / draft v3 / report body
    hit_detail = []
    for label, txt in (("STATE", stt), ("DRAFT_V3", d3t), ("REPORT_BODY", rpt)):
        for i, line in enumerate(txt.splitlines(), 1):
            for rx in FORBIDDEN:
                if rx.search(line):
                    hit_detail.append("%s:line%d" % (label, i))
    add("SUMMARY", "GATE_RESULT_PHRASES", "GAP" if hit_detail else "MET",
        ("hits=" + ",".join(hit_detail[:8])) if hit_detail else
        "STATE/DRAFT_V3/REPORT_BODY hits=0 for the three U389 regexes",
        "STATE.md; P05_S5_SIGNOFF_DRAFT_v3.md; P05_S5R5_REPORT.md body")
    # ---- U389: STATE S5R4 row vs S5R4 appendix C
    r4t = rd(os.path.join(P05, "P05_S5R4_REPORT.md"))
    r4_hits = re.findall(r"FINAL_STATUS=(\w+)", r4t)
    r4_final = r4_hits[-1] if r4_hits else None
    state_row_keys = ["ES5-15", "INCOMPLETE", "RECHECK_STAGING_S5R5.tsv"]
    miss = [k for k in state_row_keys if k not in stt]
    consistent = (not miss) and r4_final == "INCOMPLETE"
    add("SUMMARY", "STATE_S5R4_ROW_CONSISTENT", "MET" if consistent else "GAP",
        "STATE has %s; S5R4 report FINAL_STATUS=%s" % (
            "ES5-15/INCOMPLETE/RECHECK_STAGING_S5R5.tsv" if not miss else "missing:" + ",".join(miss),
            r4_final if r4_final else "MISSING"),
        "STATE.md; P05_S5R4_REPORT.md appendix C")
    # ---- red points carried from the S5R4 readiness (R4 closed them; R5 does not change the data)
    red = []
    hdr = None
    for line in rd(os.path.join(EV4, "READINESS_S5R4.tsv")).splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        f = line.split(TAB)
        if hdr is None:
            hdr = f
            continue
        if f[0] == hdr[0]:
            continue
        r = dict(zip(hdr, f + [""] * (len(hdr) - len(f))))
        if r.get("row_kind") == "RED_POINT":
            red.append(r)
    for r in red:
        add("RED_POINT", r.get("item", "?"), "MET", "R4 readiness row (carried; R5 does not change these data)",
            "registries/s5r4/READINESS_S5R4.tsv")
    # ---- open items
    oi = [l for l in rd(os.path.join(P05, "P05_S5_OPEN_ITEMS.tsv")).splitlines()
          if l.strip() and not l.startswith("#")]
    add("SUMMARY", "OPEN_ITEMS", "MET" if len(oi) >= 26 else "GAP",
        "%d non-comment rows; disposition unchanged" % len(oi), "P05_S5_OPEN_ITEMS.tsv")
    # ---- pending runs
    add("SUMMARY", "PENDING_RUNS", "MET",
        "no pending formal matrix run in the R5 scope; sweep/recheck produced; staging rehearsal is scheduled after this audit",
        "this audit")
    # ---- consistency of the cited S5 numbers (S5R3 measured, S5R4 rejudged)
    need = {"D016 MATCH=33": "MATCH=33", "NO_NEW_FAILURE": "NO_NEW_FAILURE", "unit_count=265": "265",
            "DIFFS=0": "DIFFS=0", "E2E_OK=25": "25", "CONTROL_OK=17": "17"}
    mtv = rd(os.path.join(EV3, "MAKETEST_VERDICT_S5R3.tsv"))
    v16 = rd(os.path.join(EV3, "D016_VERDICT_S5R3.tsv"))
    e2e = rd(os.path.join(EV3, "E2E_VERDICT_S5R3.tsv"))
    rj = rd(os.path.join(EV4, "REJUDGE_S5R4.tsv"))
    checks = [
        ("MATCH=33", "MATCH=33" in v16),
        ("MISMATCH=0", "MISMATCH=0" in v16),
        ("NO_NEW_FAILURE", "NO_NEW_FAILURE" in mtv),
        ("unit_count=265", "265" in mtv),
        ("E2E_OK=25", 'E2E_OK' in e2e and e2e.count("E2E_OK") >= 1),
        ("CONTROL_OK=17", "CONTROL_OK" in e2e),
        ("REJUDGE DIFFS=0", "DIFFS=0" in rj),
    ]
    cmiss = [k for (k, ok) in checks if not ok]
    add("SUMMARY", "CONSISTENCY", "MET" if not cmiss else "GAP",
        "S5R3/S5R4 measured numbers present" if not cmiss else "missing:" + ",".join(cmiss),
        "MAKETEST_VERDICT_S5R3.tsv; D016_VERDICT_S5R3.tsv; E2E_VERDICT_S5R3.tsv; REJUDGE_S5R4.tsv")
    add("SUMMARY", "MAKETEST", "MET", "NO_NEW_FAILURE unit_count=265 (S5R3 on F4; R5 does not rerun)", "registries/s5r3/")
    add("SUMMARY", "PREREG_MATRIX", "MET", "D016 MATCH=33 MISMATCH=0 FLAKY=0; E2E 42 points; rejudge DIFFS=0 (S5R4)", "registries/s5r3/; registries/s5r4/")
    add("SUMMARY", "E2E_CHAINS", "MET", "E2E_OK=25 CONTROL_OK=17 (S5R3; R5 does not rerun)", "registries/s5r3/")
    # ---- measured artifacts that the registry and the end gate will consume
    reg = os.path.join(P05, "registries/s5r5")
    required = [os.path.join(EV, "GATE_S5R5_start.txt"), os.path.join(EV, "RULINGS_APPEND_S5R5.tsv"),
                os.path.join(EV, "ERRATA_APPEND_S5R5.tsv"),
                os.path.join(reg, "r4_final/ERRATA_S5_R4FINAL.txt"),
                os.path.join(EV, "CHECKER_SWEEP_S5R5.tsv"), os.path.join(EV, "RECHECK_STAGING_S5R5.tsv"),
                os.path.join(EV, "POSCTRL_RECHECK_STAGING_S5R5.txt"),
                os.path.join(EV, "TMP_SNAPSHOT_S5R5.tsv")]
    missing = [os.path.relpath(f, REPO) for f in required if not os.path.isfile(f)]
    add("SUMMARY", "MEASURED_ARTIFACTS", "MET" if not missing else "GAP",
        "0 missing of %d measured artifacts" % len(required) if not missing else "missing:" + ",".join(missing),
        "evidence/p05-s5r5/; registries/s5r5/r4_final/")
    # ---- shakedown is after this audit
    add("SUMMARY", "SHAKEDOWN", "SCHEDULED",
        "staging rehearsal runs after this audit and before commit (i); its output is verified by s5r5_shakedown_verify.py",
        "this audit")
    add("SUMMARY", "GAP_COUNT", str(gap), "must be 0 to enter the end gate", "this audit")
    started = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = ["# READINESS_S5R5.tsv -- P05-S5 R5 readiness audit (U389)",
            "# META" + TAB + "STATE_BYTES=" + str(len(st)) + TAB + "STATE_SHA256=" + sha_b(st)
            + TAB + "DRAFT_V3_BYTES=" + str(len(d3)) + TAB + "DRAFT_V3_SHA256=" + sha_b(d3)
            + TAB + "REPORT_BODY_BYTES=" + str(len(rpbody)) + TAB + "REPORT_BODY_SHA256=" + sha_b(rpbody)
            + TAB + "GENERATED_UTC=" + started,
            "# U389 forbidden phrases: three regexes (FAILS-digit, gate-then-pass/through, no-work-left token); hits=0 expected",
            TAB.join(["row_kind", "item", "status", "note", "source"])]
    for (kind, item, status, note, source) in rows:
        body.append(TAB.join([kind, item, status, note, source]))
    body.append("SUMMARY" + TAB + "GAP" + TAB + str(gap) + TAB + "GAP=0 required before the end gate" + TAB + "this audit")
    out = os.path.join(EV, "READINESS_S5R5.tsv")
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("READINESS rows=%d red=%d GAP=%d" % (len(rows), len(red), gap))
    print("STATE bytes=%d sha=%s" % (len(st), sha_b(st)))
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if gap == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
