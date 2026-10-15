#!/usr/bin/env python3
# verdict_m2_r8m2a2.py -- P05-S4 R8 M2a2 section 4.7: verdict of M2 results against the prereg.
# Copied from verdict_m2_r8m2a.py (P05-S4 R8 M2a) and changed as follows (see SRC_DIFF_R8_M2a2_verdict.txt):
#   1. EV is m2a2 (the evidence directory of this round); the output prefix must start with VERDICT_M2_R8_M2a2.
#   2. exp_rc1 / exp_rc2 accept the token NZ ("non-zero"): MATCH when the observed rc is non-zero, MISMATCH when it is 0.
#   3. exp_signal and exp_hit are compared (the R8 M2a version did not compare them).
#   4. exp_san (sanitizer report count, M2-03 only): the observed san_reports column must equal the prereg value.
#   5. Controls (exp_class CONTROL_OK) are judged with control=True by judge_d003.classify, as before.
# Usage: python3 -I -B verdict_m2_r8m2a2.py <RESULTS_DIR_rel_to_repo> <PREREG_rel_to_repo> <OUT_PREFIX>
#   RESULTS_DIR: a directory with RESULTS_pass1.tsv and RESULTS_pass2.tsv
#                (columns: point_id, tree, rc1, rc2, rc, signal, hit, I1..I7, san_reports, class)
#   OUT_PREFIX : outputs <OUT_PREFIX>_VERDICT.tsv and <OUT_PREFIX>_SUMMARY.txt under EV; refuses to overwrite (U17)
# The judge (testing/d003/judge_d003.py) is checked by sha256 and loaded read-only; it is not modified.
import hashlib
import importlib.util
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
JUDGE = os.path.join(REPO, "testing", "d003", "judge_d003.py")
JUDGE_SHA = "d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
FIELDS = ["exp_rc1", "exp_rc2", "exp_signal", "exp_hit", "exp_class"] + ["exp_I%d" % i for i in range(1, 8)] + ["exp_san"]


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def load_judge():
    if sha256_file(JUDGE) != JUDGE_SHA:
        raise SystemExit("verdict_m2_r8m2a2: REFUSED judge sha256 mismatch")
    spec = importlib.util.spec_from_file_location("judge_d003", JUDGE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def judged_class(judge, row, control):
    rc = None if row["rc"] in ("", "-") else int(row["rc"])
    rc1 = None if row["rc1"] in ("", "-") else int(row["rc1"])
    rc2 = None if row["rc2"] in ("", "-") else int(row["rc2"])
    hit = int(row["hit"]) if row["hit"] not in ("", "-") else 0
    cls, _label, _reason = judge.classify(rc, rc1, rc2, hit, control=control)
    return cls


def rc_matches(expected, observed):
    """NZ = any non-zero observed rc.  Otherwise exact integer comparison."""
    if expected == "NZ":
        return observed not in ("", "-") and int(observed) != 0
    return observed == expected


def main(argv):
    if len(argv) != 4:
        print("usage: verdict_m2_r8m2a2.py RESULTS_DIR PREREG OUT_PREFIX")
        return 2
    results_dir = os.path.join(REPO, argv[1])
    prereg = os.path.join(REPO, argv[2])
    out_prefix = argv[3]
    if "/" in out_prefix or ".." in out_prefix or not out_prefix.startswith("VERDICT_M2_R8_M2a2"):
        print("verdict_m2_r8m2a2: REFUSED OUT_PREFIX must be a plain name starting VERDICT_M2_R8_M2a2")
        return 2
    out_v = os.path.join(EV, out_prefix + "_VERDICT.tsv")
    out_s = os.path.join(EV, out_prefix + "_SUMMARY.txt")
    if os.path.exists(out_v) or os.path.exists(out_s):
        print("verdict_m2_r8m2a2: REFUSED exists (U17): %s" % out_prefix)
        return 2

    judge = load_judge()
    pre = {r["point_id"]: r for r in read_tsv(prereg)}
    p1 = {r["point_id"]: r for r in read_tsv(os.path.join(results_dir, "RESULTS_pass1.tsv"))}
    p2 = {r["point_id"]: r for r in read_tsv(os.path.join(results_dir, "RESULTS_pass2.tsv"))}

    rows = []
    mismatch = flaky = missing = 0
    for pid, e in pre.items():
        control = e["exp_class"] == "CONTROL_OK"
        r1 = p1.get(pid)
        r2 = p2.get(pid)
        if r1 is None or r2 is None:
            missing += 1
            rows.append([pid, "MISSING_RESULT", "-", "-"])
            continue
        c1 = judged_class(judge, r1, control)
        c2 = judged_class(judge, r2, control)
        obs1 = {"exp_rc1": r1["rc1"], "exp_rc2": r1["rc2"], "exp_signal": r1.get("signal", "-"),
                "exp_hit": r1.get("hit", "-"), "exp_class": c1, "exp_san": r1.get("san_reports", "-")}
        obs2 = {"exp_rc1": r2["rc1"], "exp_rc2": r2["rc2"], "exp_signal": r2.get("signal", "-"),
                "exp_hit": r2.get("hit", "-"), "exp_class": c2, "exp_san": r2.get("san_reports", "-")}
        for i in range(1, 8):
            obs1["exp_I%d" % i] = r1.get("I%d" % i, "-")
            obs2["exp_I%d" % i] = r2.get("I%d" % i, "-")
        diffs = []
        for f in FIELDS:
            exp = e.get(f, "-")
            if exp == "-":
                continue
            if f in ("exp_rc1", "exp_rc2"):
                ok = rc_matches(exp, obs1[f])
            else:
                ok = obs1.get(f) == exp
            if not ok:
                diffs.append(f)
        flk = [f for f in FIELDS if obs1.get(f) != obs2.get(f)]
        if diffs:
            mismatch += 1
        if flk:
            flaky += 1
        verdict = "FLAKY" if flk else ("MISMATCH" if diffs else "MATCH")
        rows.append([pid, verdict, ",".join(diffs) or "-", ",".join(flk) or "-"])

    os.makedirs(EV, exist_ok=True)
    with open(out_v, "x", encoding="utf-8") as fh:
        fh.write("point_id\tverdict\tmismatch_fields\tflaky_fields\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    summary = ["VERDICT_M2 points=%d MISMATCH=%d FLAKY=%d MISSING=%d" % (len(pre), mismatch, flaky, missing),
               "judge_sha256=%s" % JUDGE_SHA, "prereg=%s" % argv[2], "results=%s" % argv[1]]
    with open(out_s, "x", encoding="utf-8") as fh:
        fh.write("\n".join(summary) + "\n")
    print(summary[0])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
