#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m2b; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# soln_supp_r9m2b.py -- SOLN independent supplementary judge for I6 and san (Step S-E).
import argparse, hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DEFAULT_EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m2b"))

EXPECTED_PREREG_SOLN_SHA = "6b41d1dc9472cfa95c1500e19c306b07a030b8c70a2977bf739d41d6679ac484"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        while True:
            chunk = fh.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def load_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.strip().split("\t") for l in fh if not l.startswith("#") and l.strip()]
    hdr = lines[0]
    return [dict(zip(hdr, r)) for r in lines[1:]]

def load_facts(path):
    rows = load_tsv(path)
    return {r["point_id"]: r for r in rows}

def judge_soln_row(prereg_row, facts1_map, facts2_map):
    pid = prereg_row["point_id"]
    ctrl_id = prereg_row["control_point_id"].replace("-F3", "-F4")
    r_call = prereg_row.get("retry_call", "2")
    c_call = prereg_row.get("control_output_call", "2")
    exp_i6 = prereg_row.get("exp_I6", "HOLD")
    exp_san = prereg_row.get("exp_san", "-")

    r1 = facts1_map.get(pid)
    r2 = facts2_map.get(pid)
    c1 = facts1_map.get(ctrl_id)
    c2 = facts2_map.get(ctrl_id)

    if not r1 or not r2:
        return "ERROR_MISSING_POINT_FACTS", "-", "-", "-", "-", "MISMATCH", "Facts missing for point"
    if not c1 or not c2:
        return "ERROR_MISSING_CTRL_FACTS", "-", "-", "-", "-", "MISMATCH", f"Facts missing for control point {ctrl_id}"

    # Evaluate I6 pass 1 & 2
    sha_pt_1 = r1.get(f"call{r_call}_sha256", "NONE_PT_1")
    sha_ctrl_1 = c1.get(f"call{c_call}_sha256", "NONE_CTRL_1")
    i6_p1 = "HOLD" if sha_pt_1 == sha_ctrl_1 else "VIOLATED"

    sha_pt_2 = r2.get(f"call{r_call}_sha256", "NONE_PT_2")
    sha_ctrl_2 = c2.get(f"call{c_call}_sha256", "NONE_CTRL_2")
    i6_p2 = "HOLD" if sha_pt_2 == sha_ctrl_2 else "VIOLATED"

    # Evaluate san pass 1 & 2
    san_p1 = "-"
    san_p2 = "-"
    san_ok = True
    if exp_san not in ("-", "", None):
        act_san_1 = str(r1.get("san_reports", "-"))
        crash_san_1 = str(r1.get("san_crash", "-"))
        if act_san_1 == str(exp_san) and crash_san_1 == "0":
            san_p1 = "PASS"
        else:
            san_p1 = "FAIL"
            san_ok = False

        act_san_2 = str(r2.get("san_reports", "-"))
        crash_san_2 = str(r2.get("san_crash", "-"))
        if act_san_2 == str(exp_san) and crash_san_2 == "0":
            san_p2 = "PASS"
        else:
            san_p2 = "FAIL"
            san_ok = False

    i6_ok = (i6_p1 == exp_i6 and i6_p2 == exp_i6)
    verdict = "MATCH" if (i6_ok and san_ok) else "MISMATCH"

    details = []
    if not i6_ok:
        details.append(f"I6({i6_p1},{i6_p2}!={exp_i6})")
    if not san_ok:
        details.append(f"san({san_p1},{san_p2})")
    detail_str = ";".join(details) if details else "ALL_EXPECTATIONS_MET"

    return i6_p1, i6_p2, san_p1, san_p2, verdict, detail_str

def main():
    parser = argparse.ArgumentParser(description="P05-S4 R9 M2b SOLN supplementary judge")
    parser.add_argument("--ev", default=DEFAULT_EV, help="Evidence directory")
    parser.add_argument("--out", default=None, help="Output TSV path")
    args = parser.parse_args()

    ev = os.path.realpath(args.ev)
    os.makedirs(ev, exist_ok=True)
    out_tsv = args.out or os.path.join(ev, "SOLN_SUPP_JUDGE_R9M2b.tsv")

    prereg_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M0", "PREREG_SOLN_F4_R9.tsv")
    if not os.path.isfile(prereg_path):
        sys.exit(f"PREREG_SOLN_F4_R9.tsv missing: {prereg_path}")

    # Check prereg sha256
    act_sha = sha256_file(prereg_path)
    if act_sha != EXPECTED_PREREG_SOLN_SHA:
        sys.exit(f"PREREG_SOLN_F4_R9.tsv sha mismatch: expected {EXPECTED_PREREG_SOLN_SHA}, got {act_sha}")
    print(f"Verified PREREG_SOLN_F4_R9.tsv sha256 OK: {act_sha}")

    facts1_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M2", "FACTS_pass1_R9.tsv")
    facts2_path = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r9", "M2", "FACTS_pass2_R9.tsv")

    facts1 = load_facts(facts1_path)
    facts2 = load_facts(facts2_path)
    prereg_rows = load_tsv(prereg_path)

    results = []
    match_count = 0
    mismatch_count = 0

    for r in prereg_rows:
        pid = r["point_id"]
        ctrl_id = r["control_point_id"].replace("-F3", "-F4")
        exp_i6 = r.get("exp_I6", "HOLD")
        exp_san = r.get("exp_san", "-")

        i6_p1, i6_p2, san_p1, san_p2, verdict, detail_str = judge_soln_row(r, facts1, facts2)
        if verdict == "MATCH":
            match_count += 1
        else:
            mismatch_count += 1

        results.append([
            pid, ctrl_id, exp_i6, i6_p1, i6_p2, exp_san, san_p1, san_p2, verdict, detail_str
        ])

    with open(out_tsv, "w", encoding="utf-8") as fh:
        fh.write("# SOLN_SUPP_JUDGE_R9M2b.tsv -- SOLN supplementary judgment for I6 and san (Rule U300/U301)\n")
        fh.write("point_id\tcontrol_point_id\texp_I6\tI6_p1\tI6_p2\texp_san\tsan_p1\tsan_p2\tverdict\tdetails\n")
        for row in results:
            fh.write("\t".join(row) + "\n")

    print(f"SOLN supplementary judge complete. Total points: {len(results)}")
    print(f"MATCH: {match_count}/18, MISMATCH: {mismatch_count}/18")
    print(f"Output written to {out_tsv}")

    if mismatch_count > 0:
        print("WARNING: SOLN supplementary judge found mismatches!")
        sys.exit(1)

if __name__ == "__main__":
    main()
