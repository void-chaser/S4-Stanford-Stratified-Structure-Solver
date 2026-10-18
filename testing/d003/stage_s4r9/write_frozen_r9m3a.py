#!/usr/bin/env python3
# write_frozen_r9m3a.py -- write FROZEN_SCRIPTS_R9M3A.tsv from the current file hashes (run before commit (i)).
import hashlib, os
PATHS = [
 "testing/d003/stage_s4r9/run_maketest_r9m3a.py",
 "testing/d003/stage_s4r9/judge_maketest_r9m3a_v3.py",
 "testing/d003/stage_s4r9/report_check_r9m3a.py",
 "testing/d003/stage_s4r9/copy_registries_r9m3a.py",
 "testing/d003/stage_s4r9/events_r9m3a.py",
 "testing/d003/stage_s4r9/sha_sums_r9m3a.py",
 "testing/d003/stage_s4r9/gate_r9m3a_v2.sh",
 "testing/d003/stage_s4r9/gate_check_r9m3a_v2.py",
 "checkpoints/p05/evidence/p05-s4r9/m3a/PREREG_MAKETEST_R9M3A.tsv",
 "checkpoints/p05/evidence/p05-s4r9/m3a/PREREG_E2E_R9M3A.tsv",
]
OUT = "checkpoints/p05/evidence/p05-s4r9/m3a/FROZEN_SCRIPTS_R9M3A.tsv"
lines = ["# FROZEN_SCRIPTS_R9M3A.tsv -- frozen scripts and pre-registration tables recorded before record commit (i)"]
lines.append("path" + chr(9) + "sha256")
for p in PATHS:
    h = hashlib.sha256(open(p, "rb").read()).hexdigest()
    lines.append(p + chr(9) + h)
open(OUT, "w", encoding="utf-8").write(chr(10).join(lines) + chr(10))
print("frozen items:", len(PATHS), "->", OUT)
