#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r3; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# prereg_r9m1r3_v2.py -- Pre-registration freeze for F4 regression (651 rows) and cited F2 (651 rows) (Rules U318, U319, U320, Step S-E). New file.
import csv, datetime, hashlib, os, subprocess, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r3"))
os.makedirs(EV, exist_ok=True)

OUT_F4 = os.path.join(EV, "PREREG_M1_F4_R9M1R3.tsv")
OUT_F4_SHA = os.path.join(EV, "PREREG_M1_F4_R9M1R3.tsv.sha256")
OUT_F4_TIME = os.path.join(EV, "PREREG_M1_F4_R9M1R3_TIMESTAMP_UTC.txt")

OUT_F2 = os.path.join(EV, "PREREG_M1_CITED_F2_R9M1R3.tsv")
OUT_F2_SHA = os.path.join(EV, "PREREG_M1_CITED_F2_R9M1R3.tsv.sha256")
OUT_F2_TIME = os.path.join(EV, "PREREG_M1_CITED_F2_R9M1R3_TIMESTAMP_UTC.txt")

OUT_DIFF = os.path.join(EV, "PREREG_VS_R9M1R2_DIFF_R9M1R3.tsv")
OUT_ENG = os.path.join(EV, "ENGINE_COLUMNS_R9M1R3.txt")

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        while True:
            c = fh.read(65536)
            if not c: break
            h.update(c)
    return h.hexdigest()

def utc_str():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# 1. Source verification: PREREG_M1_F4_R9M1R2.tsv
src_f4_path = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R2/PREREG_M1_F4_R9M1R2.tsv")
exp_src_sha = "35333fd452b9e20d0e7ec5adf46db19c57504ea8fee0a3af6ad908b21f465ec1"
act_src_sha = sha256_file(src_f4_path)
assert act_src_sha == exp_src_sha, f"Source PREREG_M1_F4_R9M1R2.tsv sha mismatch: {act_src_sha} != {exp_src_sha}"
print(f"Verified source PREREG_M1_F4_R9M1R2.tsv sha256 = {act_src_sha[:12]}...")

with open(src_f4_path, encoding="utf-8") as f:
    lines_r2 = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
header_f4 = lines_r2[0]
rows_r2 = [dict(zip(header_f4, l)) for l in lines_r2[1:]]
assert len(rows_r2) == 651, f"Expected 651 rows in source, got {len(rows_r2)}"

# 2. Build PREREG_M1_F4_R9M1R3.tsv
# Under U319/U320:
# - G2c_control maintains NOT_RUN expectation: exp_class=NOT_RUN_REGISTRY_ERROR, exp_rc1="-", exp_rc2="-", exp_rc3="-", exp_hit="-", exp_point_verdict="NOT_RUN_REGISTRY_ERROR", f3_effective_verdict="NOT_RUN_AS_EXPECTED"
# - G5/G6 exp_I1..I6 original values retained.
rows_r3 = []
for r in rows_r2:
    new_r = dict(r)
    sec = r["section"]
    grp = r["group"]
    pid = r["point_id"]

    if grp == "G2c_control":
        assert new_r["exp_class"] == "NOT_RUN_REGISTRY_ERROR"
        assert new_r["exp_rc1"] == "-"
        assert new_r["exp_rc2"] == "-"
        assert new_r["exp_rc3"] == "-"
        assert new_r["exp_hit"] == "-"
        assert new_r["f3_effective_verdict"] == "NOT_RUN_AS_EXPECTED"

    rows_r3.append(new_r)

# Write PREREG_M1_F4_R9M1R3.tsv
with open(OUT_F4, "w", encoding="utf-8") as f:
    f.write("# PREREG_M1_F4_R9M1R3.tsv -- Pre-registration fact expectation table for F4 (651 rows; Rule U318, U319, U320)" + chr(10))
    f.write(chr(9).join(header_f4) + chr(10))
    for r in rows_r3:
        f.write(chr(9).join([r[k] for k in header_f4]) + chr(10))

f4_sha = sha256_file(OUT_F4)
f4_time = utc_str()
with open(OUT_F4_SHA, "w", encoding="utf-8") as f: f.write(f4_sha + "\n")
with open(OUT_F4_TIME, "w", encoding="utf-8") as f: f.write(f4_time + "\n")
print(f"Wrote PREREG_M1_F4_R9M1R3.tsv ({len(rows_r3)} rows), sha256={f4_sha}.")

# 3. Diff against PREREG_M1_F4_R9M1R2.tsv
diff_rows = []
exp_cols = ["exp_class", "exp_rc1", "exp_rc2", "exp_rc3", "exp_hit", "exp_point_verdict",
            "exp_I1", "exp_I2", "exp_I3", "exp_I4", "exp_I5", "exp_I6", "inj_call", "contract", "f3_effective_verdict"]

exp_diff_count = 0
for idx, (r2, r3) in enumerate(zip(rows_r2, rows_r3), 1):
    diff_fields = []
    for col in header_f4:
        v2 = r2[col]
        v3 = r3[col]
        if v2 != v3:
            diff_fields.append(f"{col}(R2={v2}!=R3={v3})")
            if col in exp_cols:
                exp_diff_count += 1
    diff_rows.append([
        r3["section"], r3["group"], r3["point_id"],
        "DIFF" if diff_fields else "SAME",
        ";".join(diff_fields) if diff_fields else "NONE"
    ])

with open(OUT_DIFF, "w", encoding="utf-8") as f:
    f.write("# PREREG_VS_R9M1R2_DIFF_R9M1R3.tsv -- Diff between r9m1r2 and r9m1r3 F4 pre-registration (Step S-E)" + chr(10))
    f.write(chr(9).join(["section", "group", "point_id", "status", "differences"]) + chr(10))
    for r in diff_rows:
        f.write(chr(9).join(r) + chr(10))

print(f"Wrote PREREG_VS_R9M1R2_DIFF_R9M1R3.tsv. Expectation columns diff count: {exp_diff_count} (must equal 0).")
assert exp_diff_count == 0, f"Expectation diff count was {exp_diff_count}, expected 0!"

# 4. Generate PREREG_M1_CITED_F2_R9M1R3.tsv
src_f2_path = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R2/PREREG_M1_CITED_F2_R9M1R2.tsv")
exp_f2_sha = "8ffdb6a5775837baa6e36bcfc9abe94ee49d05019b08dec4a46a7aa2b3da2626"
act_f2_sha = sha256_file(src_f2_path)
assert act_f2_sha == exp_f2_sha, f"Source F2 sha mismatch: {act_f2_sha} != {exp_f2_sha}"

with open(src_f2_path, encoding="utf-8") as f:
    lines_f2 = [l.strip().split("\t") for l in f if l.strip() and not l.startswith("#")]
header_f2 = lines_f2[0]
rows_f2 = [dict(zip(header_f2, l)) for l in lines_f2[1:]]
assert len(rows_f2) == 651, f"Expected 651 rows in cited F2, got {len(rows_f2)}"

# Write PREREG_M1_CITED_F2_R9M1R3.tsv
with open(OUT_F2, "w", encoding="utf-8") as f:
    f.write("# PREREG_M1_CITED_F2_R9M1R3.tsv -- Cited F2 fact expectations (651 rows; Rule U317, U318)" + chr(10))
    f.write(chr(9).join(header_f2) + chr(10))
    for r in rows_f2:
        f.write(chr(9).join([r[k] for k in header_f2]) + chr(10))

f2_sha = sha256_file(OUT_F2)
f2_time = utc_str()
with open(OUT_F2_SHA, "w", encoding="utf-8") as f: f.write(f2_sha + "\n")
with open(OUT_F2_TIME, "w", encoding="utf-8") as f: f.write(f2_time + "\n")
print(f"Wrote PREREG_M1_CITED_F2_R9M1R3.tsv ({len(rows_f2)} rows), sha256={f2_sha}.")

# 5. Generate ENGINE_COLUMNS_R9M1R3.txt
eng_r2_path = os.path.join(REPO, "checkpoints/p05/registries/s4r9/M1R2/ENGINE_COLUMNS_R9M1R2.txt")
eng_r2_text = open(eng_r2_path, encoding="utf-8").read()

eng_additions = """
4. U319 Un-run Control Rows Handling Criteria:
- Absolute Rule for Un-run Rows:
  * Any point where execution was intentionally not run (including the 3 rows in M1b G2c_control where f3_effective_verdict == NOT_RUN_AS_EXPECTED) must strictly record facts as: rc="-", rc1="-", rc2="-", rc3="-", hit="-", class="NOT_RUN_REGISTRY_ERROR", verdict="NOT_RUN_AS_EXPECTED".
  * It is strictly prohibited to fabricate or synthesize numerical return codes (such as rc=0, rc1=0, rc2=0) or class="CONTROL_OK" for rows where the driver was never invoked.
  * In the equivalence comparison table (F3_F4_EQUIV), these un-run rows are categorized as NOT_RUN in the hit classification and are excluded from EQUIVALENT.
- Historical Citations:
  * testing/d003/stage_s4/run_supp_r8m1b3.py:73-82 / plan_and_run_m1b_r8m1b1.py:60-70:
    "if src == 'M1b1_NOT_RUN': rc1, rc2, rc3, hit, cls = '-', '-', '-', '-', 'NOT_RUN_REGISTRY_ERROR'; env = 'NOT_RUN'"
  * testing/d003/stage_s4r9/verdict_r9m1r2.py:73-77:
    "if exp_eff == 'NOT_RUN_AS_EXPECTED': v = 'NOT_RUN_AS_EXPECTED'"

5. U320 M1c G6 Invariants I1..I6 Criteria and Seam Results Integration:
- Invariants I1..I6 for G6:
  * For M1c G6 (seam failure injection points), invariants I1 through I6 and point_verdict MUST enter formal verdict and F3 vs F4 equivalence comparison.
  * In formal verdict (VERDICT_M1_F4), F4 side values for I1..I6 and point_verdict are obtained from both pass 1 and pass 2 runs of RESULTS_R6c_SEAM.tsv and verified for consistency (FLAKY/GDB_DIV = 0) and matched against exp_I1..I6.
  * In equivalence comparison (F3_F4_EQUIV), F4 side takes RESULTS_R6c_SEAM facts; F3 side strictly takes r8m1c3 committed table checkpoints/p05/registries/s4r8/M1c/r8m1c3/M1C_F3_RESULTS_R6c_SEAM.tsv (where all 25 rows have verified HOLD/NA invariant strings); expectation takes PREREG_M1_F4_R9M1R3.tsv exp_I1..I6.
  * Strict three-way field-by-field string equality is required; compare scripts must not read M1C_F3_STATE_SEAM_R6c_pass1.tsv (which has unjudged '-' entries) and must not skip when either side is non-empty.
- Historical Citations:
  * testing/d003/stage_s4/verdict_m1c_r8m1c3.py:80:
    "inv_m = inv_map(read_rows(os.path.join(F3DIR, 'RESULTS_R6c_SEAM.tsv')))"
  * testing/d003/stage_s4/verdict_m1c_r8m1c3.py:87-93:
    "def run_row(grp, base_id, pas): ... rec = (m1 if pas == '1' else m2).get(base_id); return rec, SEAM_FACT, (inv_m.get((base_id, pas)) if rec else None)"
  * testing/d003/stage_s4/verdict_m1c_r8m1c3.py:136-143:
    "for k in INV: exp = fr.get('exp_' + k, '-'); if exp in ('', '-'): continue; if inv.get(k, '') != exp: ok = False; diffs.append('pass%s:%s exp=%s got=%s' % (pas, k, exp, inv.get(k, '')))"
"""

eng_r3_text = eng_r2_text.replace("R9M1R2", "R9M1R3").replace("Rule U314", "Rules U314, U319, U320") + eng_additions
with open(OUT_ENG, "w", encoding="utf-8") as f:
    f.write(eng_r3_text)

print(f"Wrote ENGINE_COLUMNS_R9M1R3.txt ({len(eng_r3_text)} bytes).")
