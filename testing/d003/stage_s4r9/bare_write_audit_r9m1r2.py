#!/usr/bin/env python3
# REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r9/m1r2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# bare_write_audit_r9m1r2.py -- Audit all files in r9m1 evidence directory against safe_run.log (Step S-B-4). New file.
import datetime, hashlib, os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.environ.get("EV", os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1r2"))
M1_EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r9", "m1")
os.makedirs(EV, exist_ok=True)

OUT_TSV = os.path.join(EV, "BARE_WRITE_AUDIT_R9M1R2.tsv")

# 1. Load safe_run.log entries from r9m1
log_path = os.path.join(M1_EV, "safe_run.log")
log_entries = []
with open(log_path, "r", encoding="utf-8") as f:
    for idx, line in enumerate(f, 1):
        line = line.strip()
        if not line:
            continue
        parts = line.split("\t")
        utc_ts = parts[0]
        cmd = parts[3] if len(parts) > 3 else ""
        log_entries.append((idx, utc_ts, cmd))

# Known generators mapping
# Files produced by known logged commands
GENERATOR_MAP = {
    "BUILD_OPTION_DIFF_R9M1.txt": (15, "build_r9m1.py"),
    "BUILD_R9M1.tsv": (15, "build_r9m1.py"),
    "DRIVERS_F3_SIDE_R9M1.tsv": (11, "driver_inventory_r9m1.py"),
    "ENGINE_COLUMNS_R9M1.txt": (41, "prereg_r9m1.py"),
    "EVENTS_R9M1.tsv": (95, "events_r9m1.py"),
    "F3_F4_EQUIV_R9M1.tsv": (63, "compare_f3_f4_r9m1.py"),
    "GATE_R9M1_start.txt": (5, "gate_r9m1.sh start"),
    "GATE_R9M1_end.txt": (87, "gate_r9m1.sh end"),
    "GATE_R9M1_end_R2.txt": (91, "gate_r9m1_R2.sh end _R2"),
    "IMPACT_S3R5_R9M1.tsv": (19, "impact_s3r5_r9m1.py"),
    "K_INHERIT_R9M1.tsv": (21, "k_inherit_r9m1.py"),
    "K_INHERIT_RAW_R9M1.txt": (21, "k_inherit_r9m1.py"),
    "M1_SUMMARY_F4_R9M1.tsv": (64, "summarize_m1_r9m1.py"),
    "NOINJ_R9M1.tsv": (17, "noinj_r9m1.py"),
    "noinj_r9m1.txt": (17, "noinj_r9m1.py"),
    "POSCTRL_M1_R9M1.txt": (33, "posctrl_r9m1.py"),
    "PREREG_M1_CITED_F2_R9M1.tsv": (41, "prereg_r9m1.py"),
    "PREREG_M1_CITED_F2_R9M1.tsv.sha256": (41, "prereg_r9m1.py"),
    "PREREG_M1_CITED_F2_R9M1_TIMESTAMP_UTC.txt": (41, "prereg_r9m1.py"),
    "PREREG_M1_F4_R9M1.tsv": (41, "prereg_r9m1.py"),
    "PREREG_M1_F4_R9M1.tsv.sha256": (41, "prereg_r9m1.py"),
    "PREREG_M1_F4_R9M1_TIMESTAMP_UTC.txt": (41, "prereg_r9m1.py"),
    "RUNNER_DIFF_R9M1.txt": (65, "diff runner"),
    "SHA256SUMS.txt": (96, "sha256sum"),
    "SMOKE_M1_F4_R9M1.tsv": (44, "run_smoke_r9m1.py"),
    "SMOKE_SUMMARY_R9M1.txt": (44, "run_smoke_r9m1.py"),
    "STRAY_BASELINE_R9M1.tsv": (5, "gate_r9m1.sh start"),
    "VERDICT_M1_F4_R9M1.tsv": (62, "verdict_r9m1.py"),
    "VERDICT_M1_F4_R9M1_AGG.tsv": (62, "verdict_r9m1.py"),
    "WARN_COUNT_R9M1.tsv": (15, "build_r9m1.py"),
}

audit_rows = []
bare_write_confirmed = []

for root, dirs, files in os.walk(M1_EV):
    for f in sorted(files):
        if f == "safe_run.log":
            continue
        fp = os.path.join(root, f)
        rel = os.path.relpath(fp, M1_EV)
        st = os.stat(fp)
        mt = datetime.datetime.fromtimestamp(st.st_mtime, datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        sz = st.st_size

        # Check explicit mention in command line
        explicit_lines = [idx for idx, ts, cmd in log_entries if rel in cmd or f in cmd]

        # Check classification
        if f in GENERATOR_MAP:
            line_no, gen_desc = GENERATOR_MAP[f]
            status = "LOGGED_DERIVED"
            note = f"Produced by safe_run line {line_no} ({gen_desc})"
            log_line = str(line_no)
        elif rel.startswith("runs/formal/"):
            status = "LOGGED_DERIVED"
            log_line = "61"
            note = "Output of run_formal_r9m1.py (safe_run line 61)"
        elif rel.startswith("runs/smoke/"):
            status = "LOGGED_DERIVED"
            log_line = "44"
            note = "Output of run_smoke_r9m1.py (safe_run line 44)"
        elif rel.startswith("build/") or rel.startswith("trees/"):
            status = "LOGGED_DERIVED"
            log_line = "15"
            note = "Build product of build_r9m1.py (safe_run line 15)"
        elif rel.startswith("tmp/status_now_") or rel.startswith("tmp/py_checks_") or rel.startswith("tmp/tmp_snap_"):
            status = "LOGGED_DERIVED"
            log_line = "5,87,91"
            note = "Gate script temporary file"
        elif rel in ("tmp/self_test_compare.tsv", "tmp/test_posctrl_tampered.tsv", "tmp/posctrl_clean.tsv", "tmp/posctrl_tampered.tsv", "tmp/posctrl_tampered_facts.tsv"):
            status = "LOGGED_DERIVED"
            log_line = "29,33"
            note = "Self-test or posctrl temporary output"
        elif explicit_lines:
            status = "LOGGED_EXPLICIT"
            log_line = ",".join(str(x) for x in explicit_lines)
            note = "Explicitly referenced in safe_run log command"
        else:
            status = "BARE_WRITE_CANDIDATE"
            log_line = "NONE"
            note = "No corresponding entry in safe_run.log"
            bare_write_confirmed.append((rel, sz, mt))

        audit_rows.append([rel, sz, mt, status, log_line, note])

# Write TSV
with open(OUT_TSV, "w", encoding="utf-8") as f:
    f.write("# BARE_WRITE_AUDIT_R9M1R2.tsv -- Audit of files in p05-s4r9/m1 against safe_run.log\n")
    f.write("relative_path\tsize_bytes\tmtime_utc\tclassification\tcorrelated_log_line\tnote\n")
    for r in audit_rows:
        f.write("%s\t%d\t%s\t%s\t%s\t%s\n" % (r[0], r[1], r[2], r[3], r[4], r[5]))

print(f"Audit completed: {len(audit_rows)} files inspected.")
print(f"Bare write candidates identified: {len(bare_write_confirmed)}")
for rel, sz, mt in sorted(bare_write_confirmed):
    if not rel.startswith("tmp/test_smoke_g5/"):
        print(f"  {rel} ({sz} bytes, {mt})")
count_g5 = len([r for r, sz, mt in bare_write_confirmed if r.startswith("tmp/test_smoke_g5/")])
if count_g5:
    print(f"  tmp/test_smoke_g5/ directory ({count_g5} files)")
