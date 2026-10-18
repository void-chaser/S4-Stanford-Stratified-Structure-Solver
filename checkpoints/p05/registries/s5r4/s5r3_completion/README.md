# registries/s5r4/s5r3_completion/ -- S5R3 deliverables completed in S5R4 (U380, ES5-12)

S5R3 was supposed to register 26 deliverables; the S5R3 chain copy stopped at the missing
REJUDGE_S5R3.tsv (HARD_STOP), so registries/s5r3/ only holds a 10-item SHA256SUMS.txt. The
S5R3 directory and its SHA256SUMS.txt are historical and are NOT rewritten. This directory
completes the 7 missing items:

| # | item | source | note |
|---|---|---|---|
| 20 | REJUDGE_S5R3.tsv | this round: REJUDGE_S5R4.tsv (byte copy) | R3 rejudge crashed (ES5-9); the S5R4 formal independent re-judge output is the S5R3 re-judge deliverable |
| 21 | READINESS_S5R3.tsv | evidence/p05-s5r3/ | recovered R3 readiness audit (GAP=2 recorded there) |
| 22 | P05_ACCEPTANCE_MAP_S5R3.tsv | evidence/p05-s5r3/ | recovered R3 acceptance map |
| 23 | REGISTRY_APPLY_DIFF_S5R3.txt | evidence/p05-s5r3/ | recovered R3 registry patch diff |
| 24 | REPORT_CHECK_S5R3.txt | evidence/p05-s5r3/ | recovered R3 report self-check |
| 25 | COPY_DIFF_S5R3.txt | evidence/p05-s5r3/ | recovered R3 harness copy diff |
| 26 | ERRATA_S5_R3FINAL.txt | evidence/p05-s5r4/r3_final/ | byte copy of the S5R3-final ERRATA_S5.txt (8228 B, last entry ES5-8) taken before the S5R4 append |

S5R3 26/26 coverage: the 19 items already in registries/s5r3/ (each sha256 verified against
evidence/p05-s5r3/SHA256SUMS.txt) plus these 7 items. p05-s5r3/ and registries/s5r3/ are unchanged
(sha256 of their SHA256SUMS.txt files are recorded by the S5R4 start gate).

## 26/26 mapping

| S5R3 # | item | where |
|---|---|---|
| 1 | GATE_S5R3_start.txt | registries/s5r3/GATE_S5R3_start.txt |
| 2 | PREREG_D016_S5R3.tsv | registries/s5r3/PREREG_D016_S5R3.tsv |
| 3 | PREREG_D016_S5R3.tsv.sha256.txt | registries/s5r3/PREREG_D016_S5R3.tsv.sha256.txt |
| 4 | PREREG_MAKETEST_S5R3.tsv | registries/s5r3/PREREG_MAKETEST_S5R3.tsv |
| 5 | PREREG_E2E_S5R3.tsv | registries/s5r3/PREREG_E2E_S5R3.tsv |
| 6 | PREREG_E2E_S5R3.tsv.sha256.txt | registries/s5r3/PREREG_E2E_S5R3.tsv.sha256.txt |
| 7 | D016_VERDICT_S5R3.tsv | registries/s5r3/D016_VERDICT_S5R3.tsv |
| 8 | D016_BUILD_S5R3.tsv | registries/s5r3/D016_BUILD_S5R3.tsv |
| 9 | E2E_VERDICT_S5R3.tsv | registries/s5r3/E2E_VERDICT_S5R3.tsv |
| 10 | E2E_BUILD_S5R3.tsv | registries/s5r3/E2E_BUILD_S5R3.tsv |
| 11 | CALIB_DIFF_S5R3.tsv | registries/s5r3/CALIB_DIFF_S5R3.tsv |
| 12 | MAKETEST_UNITS_S5R3.tsv | registries/s5r3/MAKETEST_UNITS_S5R3.tsv |
| 13 | MAKETEST_VERDICT_S5R3.tsv | registries/s5r3/MAKETEST_VERDICT_S5R3.tsv |
| 14 | POSCTRL_D016_S5R3.txt | registries/s5r3/POSCTRL_D016_S5R3.txt |
| 15 | POSCTRL_E2E_S5R3.txt | registries/s5r3/POSCTRL_E2E_S5R3.txt |
| 16 | POSCTRL_MAKETEST_S5R3.txt | registries/s5r3/POSCTRL_MAKETEST_S5R3.txt |
| 17 | FROZEN_SCRIPTS_S5R3.tsv | registries/s5r3/FROZEN_SCRIPTS_S5R3.tsv |
| 18 | s5r2_supplement/D016_VERDICT_S5R2_ERRATA.txt | registries/s5r3/s5r2_supplement/D016_VERDICT_S5R2_ERRATA.txt |
| 19 | s5r2_supplement/D016_BUILD_S5R2.tsv | registries/s5r3/s5r2_supplement/D016_BUILD_S5R2.tsv |
| 20 | REJUDGE_S5R3.tsv | s5r3_completion/REJUDGE_S5R3.tsv |
| 21 | READINESS_S5R3.tsv | s5r3_completion/READINESS_S5R3.tsv |
| 22 | P05_ACCEPTANCE_MAP_S5R3.tsv | s5r3_completion/P05_ACCEPTANCE_MAP_S5R3.tsv |
| 23 | REGISTRY_APPLY_DIFF_S5R3.txt | s5r3_completion/REGISTRY_APPLY_DIFF_S5R3.txt |
| 24 | REPORT_CHECK_S5R3.txt | s5r3_completion/REPORT_CHECK_S5R3.txt |
| 25 | COPY_DIFF_S5R3.txt | s5r3_completion/COPY_DIFF_S5R3.txt |
| 26 | ERRATA_S5_R3FINAL.txt | s5r3_completion/ERRATA_S5_R3FINAL.txt |

Coverage=26/26 (19 already registered + 7 completed here).

