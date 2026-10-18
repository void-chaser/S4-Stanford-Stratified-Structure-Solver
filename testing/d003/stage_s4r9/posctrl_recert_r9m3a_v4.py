#!/usr/bin/env python3
# posctrl_recert_r9m3a_v4.py -- v4 (v1 crashed in diff_count_events: the timestamp comparison referenced an undefined name). Positive control on the recertification logic using tampered on-disk copies (J-1 / U329).
# Each case copies a committed table into $EV/posctrl/<case>/, keeps an untouched baseline copy, writes a
# tampered copy with exactly one edit, and runs the recomputation against both. Expected: baseline 0 diffs,
# tampered exactly 1 diff.
# usage: python3 -I -B testing/d003/stage_s4r9/posctrl_recert_r9m3a.py OUTDIR OUT.txt
import os, sys, re

REPO = os.getcwd()
EV_M1R3 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r3")
EV_M1R4 = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m1r4")
REG_M1R3 = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R3")
REG_M1R4 = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R4")
EXPECTED_P1_SHA = "090797d8d082fffdcc6193188947b049bcfc3ad5cbddb350cab63f0e14f6fef4"
EXPECTED_P2_SHA = "85b1f1583ead47c1606bc8bc50819648ae1772b588f7728b1d83db74599e22d9"
LOG_TS_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)\t")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            b = fh.read(65536)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


import hashlib


def read_rows(p):
    ls = [l.rstrip("\n").split("\t") for l in open(p, encoding="utf-8") if l.strip() and not l.startswith("#")]
    h = ls[0]
    return h, [dict(zip(h, r)) for r in ls[1:]]


def key_of(r, idcol):
    return (r["section"], r["group"], r[idcol])


def recompute_verdicts(p1, p2, prereg):
    _, pre = read_rows(prereg)
    _, f1 = read_rows(p1)
    _, f2 = read_rows(p2)
    prem = {key_of(r, "point_id"): r for r in pre}
    m1 = {key_of(r, "point_id"): r for r in f1}
    m2 = {key_of(r, "point_id"): r for r in f2}
    out = {}
    for k in prem:
        exp, r1, r2 = prem[k], m1[k], m2[k]
        sec, grp, pid = k
        consistent = all(r1.get(f) == r2.get(f) for f in ("rc1", "rc2", "rc3", "hit", "class"))
        if sec == "M1c" and grp in ("G5", "G6"):
            for iname in ("I1", "I2", "I3", "I4", "I5", "I6"):
                if r1.get(iname, "-") != r2.get(iname, "-"):
                    consistent = False
        if not consistent:
            v = "GDB_DIVERGENT" if r1.get("rc3") != r2.get("rc3") else "FLAKY"
        else:
            contract = exp.get("contract", "-")
            exp_eff = exp.get("f3_effective_verdict", "-")
            if contract == "NOT_RUN_REGISTRY_ERROR" or exp_eff == "NOT_RUN_AS_EXPECTED" or exp.get("env") == "NOT_RUN":
                v = "NOT_RUN_AS_EXPECTED" if (r1.get("class") == "NOT_RUN_REGISTRY_ERROR" and r1.get("rc1") == "-") else "MISMATCH"
            elif contract == "NOT_REACHED_AS_EXPECTED" or exp_eff == "NOT_REACHED_AS_EXPECTED":
                v = "NOT_REACHED_AS_EXPECTED" if (r1.get("hit") == "0" and r1.get("class") == "INVALID") else "MISMATCH"
            else:
                d = []
                if exp.get("exp_rc1", "-") != "-" and r1.get("rc1") != exp.get("exp_rc1"):
                    d.append("rc1")
                if sec == "M1b":
                    if exp.get("exp_rc2", "-") not in ("-", "", "0", None) and r1.get("rc2") != exp.get("exp_rc2"):
                        d.append("rc2")
                else:
                    if exp.get("exp_rc2", "-") != "-" and r1.get("rc2") != exp.get("exp_rc2"):
                        d.append("rc2")
                if exp.get("exp_rc3", "-") != "-" and r1.get("rc3") != exp.get("exp_rc3"):
                    d.append("rc3")
                if exp.get("exp_hit", "-") != "-" and r1.get("hit") != exp.get("exp_hit"):
                    d.append("hit")
                if sec == "M1c":
                    exp_pv = exp.get("exp_point_verdict", "-")
                    if exp_pv == "-" and grp in ("G6c", "CTRL_AUX"):
                        exp_pv = "CONTROL_OK"
                    if r1.get("class") != exp_pv and r1.get("class") != exp.get("exp_class"):
                        d.append("class")
                    if grp in ("G5", "G6"):
                        for iname in ("I1", "I2", "I3", "I4", "I5", "I6"):
                            if exp.get("exp_" + iname, "-") != "-" and r1.get(iname, "-") != exp.get("exp_" + iname):
                                d.append(iname)
                else:
                    if r1.get("class") != exp.get("exp_class"):
                        d.append("class")
                v = "MATCH" if not d else "MISMATCH"
        out[k] = v
    return out


def diff_count_verdict(recomputed, table_path):
    _, tab = read_rows(table_path)
    bad = 0
    for r in tab:
        k = key_of(r, "point_id")
        if k not in recomputed or recomputed[k] != r.get("verdict"):
            bad += 1
    return bad


def diff_count_equiv(table_path, facts_path):
    _, tab = read_rows(table_path)
    _, facts = read_rows(facts_path)
    fm = {key_of(r, "point_id"): r for r in facts}
    bad = 0
    for r in tab:
        if r.get("section") != "M1c" or r.get("group") not in ("G5", "G6"):
            continue
        k = key_of(r, "f4_point_id")
        if k not in fm:
            bad += 1
            continue
        for idx in ("I1", "I2", "I3", "I4", "I5", "I6"):
            if r.get("f4_" + idx, "-") != fm[k].get(idx, "-"):
                bad += 1
                break
    return bad


def parse_log(ev_dir):
    out = []
    for idx, line in enumerate(open(os.path.join(ev_dir, "safe_run.log"), encoding="utf-8", errors="replace").read().splitlines(), 1):
        m = LOG_TS_RE.match(line)
        if not m:
            continue
        out.append((idx, m.group(1)))
    return out


def events_anchor(ev_dir):
    best = 0
    for idx, line in enumerate(open(os.path.join(ev_dir, "safe_run.log"), encoding="utf-8", errors="replace").read().splitlines(), 1):
        if "events_r9m1r3.py" in line and line[:4] == "2026":
            ts = line.split("\t")[0]
            if ts >= "2026-10-18T04:28:39Z":
                best = idx
    return best


def diff_count_events(table_path, lines):
    # The frozen events logic numbers every NON-BLANK physical line; a continuation line of a
    # multi-line command carries no timestamp of its own and the table stores its text in the
    # second column. Recomputation therefore compares the line SET and the timestamps of the
    # lines that do start with a timestamp.
    rows = {}
    for line in open(table_path, encoding="utf-8"):
        if not line.strip() or line.startswith("#") or line.startswith("log_line\t"):
            continue
        f = line.rstrip("\n").split("\t")
        if f[0].isdigit():
            rows[int(f[0])] = f[1]
    hi = max(rows) if rows else 0
    anchor = max([i for i, l in enumerate(lines, 1) if "sha_sums_r9m1r3.py" in l] or [0])
    expect = set(i for i in range(1, min(anchor or hi, len(lines)) + 1) if lines[i - 1].strip())
    diffs = len(expect - set(rows)) + len(set(rows) - expect) + (0 if hi == anchor else 1)
    for i in sorted(expect & set(rows)):
        m = LOG_TS_RE.match(lines[i - 1])
        if m and rows[i] != m.group(1):
            diffs += 1
    return diffs


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a/posctrl")
    out_txt = sys.argv[2] if len(sys.argv) > 2 else os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r9/m3a/POSCTRL_R9M3A.txt")
    p1 = os.path.join(EV_M1R3, "runs/formal/FORMAL_FACTS_M1_F4_R9M1R3_pass1.tsv")
    p2 = os.path.join(EV_M1R3, "runs/formal/FORMAL_FACTS_M1_F4_R9M1R3_pass2.tsv")
    prereg = os.path.join(REG_M1R3, "PREREG_M1_F4_R9M1R3.tsv")
    verdict_f = os.path.join(REG_M1R3, "VERDICT_M1_F4_R9M1R3.tsv")
    equiv_f = os.path.join(REG_M1R3, "F3_F4_EQUIV_R9M1R3.tsv")
    events_f = os.path.join(EV_M1R4, "EVENTS_RECALC_R9M1R3.tsv")
    if not os.path.isfile(events_f):
        events_f = os.path.join(REG_M1R4, "EVENTS_RECALC_R9M1R3.tsv")
    log_lines = open(os.path.join(EV_M1R3, "safe_run.log"), encoding="utf-8", errors="replace").read().splitlines()

    results = []

    def case_dir(name):
        d = os.path.join(outdir, name)
        os.makedirs(d, exist_ok=True)
        return d

    def copy(src, dst):
        data = open(src, "rb").read()
        with open(dst, "wb") as fh:
            fh.write(data)
        return dst

    # ---- case 1: VERDICT, one row verdict flipped ----
    d = case_dir("case1_verdict")
    base = copy(verdict_f, os.path.join(d, "VERDICT_baseline.tsv"))
    comp = recompute_verdicts(p1, p2, prereg)
    d_base = diff_count_verdict(comp, base)
    h, rows = read_rows(base)
    tgt = None
    for r in rows:
        if r.get("verdict") == "MATCH":
            tgt = r
            break
    if tgt is None:
        tgt = rows[0]
    tampered = os.path.join(d, "VERDICT_tampered.tsv")
    with open(tampered, "w", encoding="utf-8") as fh:
        fh.write("\t".join(h) + "\n")
        flipped = False
        for r in rows:
            row = list(r[x] for x in h)
            if not flipped and r is tgt:
                row[h.index("verdict")] = "MISMATCH" if r["verdict"] == "MATCH" else "MATCH"
                flipped = True
            fh.write("\t".join(row) + "\n")
    d_tamp = diff_count_verdict(comp, tampered)
    results.append(("CASE_1_VERDICT_ONE_ROW_FLIPPED", d_base == 0, d_tamp == 1, "baseline_diffs=%d tampered_diffs=%d" % (d_base, d_tamp)))

    # ---- case 2: EQUIV, one M1c G6 I3 cell changed ----
    d = case_dir("case2_equiv")
    base = copy(equiv_f, os.path.join(d, "EQUIV_baseline.tsv"))
    d_base = diff_count_equiv(base, p1)
    h, rows = read_rows(base)
    tampered = os.path.join(d, "EQUIV_tampered.tsv")
    changed = False
    with open(tampered, "w", encoding="utf-8") as fh:
        fh.write("\t".join(h) + "\n")
        for r in rows:
            row = [r[x] for x in h]
            if not changed and r.get("section") == "M1c" and r.get("group") == "G6":
                cur = r.get("f4_I3", "-")
                row[h.index("f4_I3")] = "0" if cur != "0" else "1"
                changed = True
            fh.write("\t".join(row) + "\n")
    d_tamp = diff_count_equiv(tampered, p1)
    results.append(("CASE_2_EQUIV_G6_I3_CHANGED", d_base == 0, d_tamp == 1, "baseline_diffs=%d tampered_diffs=%d changed=%s" % (d_base, d_tamp, changed)))

    # ---- case 3: FORMAL_FACTS pass1, one rc1 cell changed (sha witness) ----
    d = case_dir("case3_formal_facts")
    base = copy(p1, os.path.join(d, "FORMAL_FACTS_pass1_baseline.tsv"))
    tampered = os.path.join(d, "FORMAL_FACTS_pass1_tampered.tsv")
    h, rows = read_rows(base)
    changed = False
    with open(tampered, "w", encoding="utf-8") as fh:
        fh.write("\t".join(h) + "\n")
        for r in rows:
            row = [r[x] for x in h]
            if not changed and r.get("rc1") not in (None, "-"):
                row[h.index("rc1")] = "77" if r.get("rc1") != "77" else "78"
                changed = True
            fh.write("\t".join(row) + "\n")
    d_base = 0 if sha256_file(base) == EXPECTED_P1_SHA else 1
    d_tamp = 0 if sha256_file(tampered) == EXPECTED_P1_SHA else 1
    results.append(("CASE_3_FORMAL_FACTS_RC1_CHANGED", d_base == 0, d_tamp == 1, "baseline_mismatch=%d tampered_mismatch=%d changed=%s" % (d_base, d_tamp, changed)))

    # ---- case 4: EVENTS_RECALC, one row deleted ----
    d = case_dir("case4_events_recalc")
    base = copy(events_f, os.path.join(d, "EVENTS_RECALC_baseline.tsv"))
    d_base = diff_count_events(base, log_lines)
    lines = open(base, encoding="utf-8").read().splitlines()
    body = [l for l in lines if l.strip() and not l.startswith("#") and not l.startswith("log_line\t")]
    keep = body[:len(body) // 2] + body[len(body) // 2 + 1:]
    tampered = os.path.join(d, "EVENTS_RECALC_tampered.tsv")
    with open(tampered, "w", encoding="utf-8") as fh:
        fh.write("# tampered copy: one data row deleted\n")
        fh.write("log_line\tutc_timestamp\tcategory\tcommand_summary\n")
        for l in keep:
            fh.write(l + "\n")
    d_tamp = diff_count_events(tampered, log_lines)
    results.append(("CASE_4_EVENTS_ONE_ROW_DELETED", d_base == 0, d_tamp == 1, "baseline_diffs=%d tampered_diffs=%d rows=%d" % (d_base, d_tamp, len(body))))

    all_pass = all(ok_base and ok_tamp for _, ok_base, ok_tamp, _ in results)
    with open(out_txt, "w", encoding="utf-8") as fh:
        fh.write("# POSCTRL_R9M3A.txt -- positive control for the recertification logic on tampered on-disk copies (J-1, U329)\n")
        fh.write("# every case has an untouched baseline copy (expect 0 differences) and a tampered copy (expect exactly 1)\n")
        for name, ok_base, ok_tamp, detail in results:
            st = "PASS" if (ok_base and ok_tamp) else "FAIL"
            fh.write("%s: %s (expected baseline=0 tampered=1, actual %s)\n" % (name, st, detail))
        fh.write("OVERALL_POSITIVE_CONTROL: %s (%d/%d cases)\n" % ("PASS" if all_pass else "FAIL", sum(1 for _, a, b, _ in results if a and b), len(results)))
    for name, ok_base, ok_tamp, detail in results:
        print("%s PASS=%s %s" % (name, ok_base and ok_tamp, detail))
    print("OVERALL %s" % ("PASS" if all_pass else "FAIL"))
    print("WROTE " + out_txt)
    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
