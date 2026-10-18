# P05-S5 R3 正式 end 门禁附录（P05_S5R3_GATE_APPENDIX.md）

> 由 s5r3_appendix.py 在 end 门禁之后从 $EV/gate/GATE_S5R3_end.txt 按列名解析生成；本文件不手写数字。
> end 门禁正式运行一次；本附录文件与 GATE_S5R3_end.txt 均在 sha_sums 之后追加到 registries/s5r3/（证据目录不再写入）。

## 1 总览

- END_TIME_UTC = 2026-10-18T10:13:43Z
- START_TIME_UTC = 2026-10-18T09:58:28Z
- COMMIT_I_SHA = 44ddcd1495b6f6a3cee7de6afd68571c8c2252d3
- COMMIT_I_SUBJECT = P05-S5 R3 (i): rulings U372..U377, errata ES5-6..ES5-8, D016 comparator-v2 prereg, make-test and E2E harness copies, frozen s5r3 scripts, s5r2 supplement; awaiting user review
- POST_I_LOG_RECORDS = 25
- STATE_BYTES = 2946
- REGISTRY_ITEMS = 9
- COUNTS	pass=70	fail=8	total=78
- FAILS=8
- CHECK_CRASHED=0

## 2 分组断言（原文行）

### D016 与预注册

- status=PASS	check=PREREG_D016_PRESENT	expected=present	actual=present
- status=PASS	check=PREREG_D016_SHA_MATCHES_RECORD	expected=2f59f40fded874c2897061da0ab8085b975ecd9a52203528d0876cbb8d2024bc	actual=2f59f40fded874c2897061da0ab8085b975ecd9a52203528d0876cbb8d2024bc
- status=PASS	check=PREREG_D016_STATUS_INFLUENCED	expected=INFLUENCED	actual=INFLUENCED
- status=PASS	check=PREREG_D016_ROWS	expected=36	actual=36
- status=PASS	check=PREREG_D016_HAS_EXPECTED_COUNT_COL	expected=expected_count	actual=expected_count
- status=PASS	check=PREREG_D016_STDERR_COUNT_ZERO	expected=PY_STDERR_INFO2=0;LUA_STDERR_INFO2=0	actual=PY_STDERR_INFO2=0;LUA_STDERR_INFO2=0
- status=PASS	check=PREREG_D016_BEFORE_FIRST_FORMAL_RUN	expected=1	actual=1
- status=PASS	check=D016_PASS1_PRESENT	expected=present	actual=present
- status=PASS	check=D016_PASS2_PRESENT	expected=present	actual=present
- status=PASS	check=D016_VERDICT_SUMMARY	expected=SUMMARY MATCH=33 MISMATCH=0 FLAKY=0	actual=SUMMARY MATCH=33 MISMATCH=0 FLAKY=0
- status=FAIL	check=D016_VERDICT_ROWS_34	expected=34	actual=35
- status=PASS	check=D016_POSCTRL_5_OF_5	expected=('PASS', '5', '5')	actual=('PASS', '5', '5')

### E2E 与校准

- status=PASS	check=PREREG_E2E_42_ROWS	expected=42	actual=42
- status=PASS	check=PREREG_E2E_SHA_MATCHES_RECORD	expected=2332927e01687e35c8e43a20ca6a281f27c2ceabcf602a0e1e4976ee5ccc2fb2	actual=2332927e01687e35c8e43a20ca6a281f27c2ceabcf602a0e1e4976ee5ccc2fb2
- status=PASS	check=PREREG_E2E_BEFORE_FIRST_INJECTION_RUN	expected=1	actual=1
- status=PASS	check=E2E_PASS1_42_POINTS	expected=42	actual=42
- status=PASS	check=E2E_PASS2_42_POINTS	expected=42	actual=42
- status=PASS	check=E2E_VERDICT_COUNTS	expected=CONTROL_OK=17;E2E_OK=25	actual=CONTROL_OK=17;E2E_OK=25
- status=PASS	check=E2E_POSCTRL_19_OF_19	expected=('PASS', '19', '19')	actual=('PASS', '19', '19')
- status=PASS	check=CALIB_TARGET_27	expected=27	actual=27
- status=FAIL	check=CALIB_DIFF_ZERO	expected=	actual=DIFFS=0=
- status=PASS	check=E2E_BUILD_WRAP_PY	expected=4/4	actual=4/4
- status=PASS	check=E2E_BUILD_WRAP_LUA	expected=4/4	actual=4/4
- status=PASS	check=E2E_BUILD_UNRESOLVED_FFT_ZERO	expected=0/0	actual=0/0

### make test / FROZEN

- status=PASS	check=FROZEN_SCRIPTS_SHA_UNCHANGED_END	expected=1	actual=1
- status=FAIL	check=FROZEN_POST_I_CALL_COUNTS_MATCH	expected=1	actual=0
- status=PASS	check=MAKETEST_B_p1_LOG_AND_DONE	expected=ok	actual=ok
- status=PASS	check=MAKETEST_F4_p1_LOG_AND_DONE	expected=ok	actual=ok
- status=PASS	check=MAKETEST_B_p2_LOG_AND_DONE	expected=ok	actual=ok
- status=PASS	check=MAKETEST_F4_p2_LOG_AND_DONE	expected=ok	actual=ok
- status=PASS	check=MAKETEST_VERDICT_NO_NEW_FAILURE	expected=NO_NEW_FAILURE	actual=NO_NEW_FAILURE
- status=PASS	check=MAKETEST_UNIT_COUNT_265	expected=265	actual=265
- status=PASS	check=MAKETEST_RECONCILE_ALL_OK	expected=0	actual=0
- status=PASS	check=MAKETEST_POSCTRL_4_OF_4	expected=('PASS', '4', '4')	actual=('PASS', '4', '4')

### 其它

- status=PASS	check=BRANCH_IS_EXPECTED	expected=codex/p05-d003-fft-error-propagation	actual=codex/p05-d003-fft-error-propagation
- status=PASS	check=HEAD_S4_TREE_EQ_F4	expected=589e15eb11fcb04e031b524f25a443e7921946cf	actual=589e15eb11fcb04e031b524f25a443e7921946cf
- status=PASS	check=JUDGE_SHA256	expected=d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb	actual=d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb
- status=PASS	check=F2_S4_TREE	expected=e124925f5b242486a913b813fa181664f665b048	actual=e124925f5b242486a913b813fa181664f665b048
- status=PASS	check=B_S4_TREE	expected=1d738e64f9864a475fdb3de34cd3601605df2c64	actual=1d738e64f9864a475fdb3de34cd3601605df2c64
- status=PASS	check=S4_DIR_ZERO_MODIFICATION	expected=unmodified	actual=unmodified
- status=PASS	check=START_GATE_PRESENT	expected=present	actual=present
- status=PASS	check=START_GATE_FAILS_ZERO	expected=0	actual=0
- status=PASS	check=START_GATE_CRASHED_ZERO	expected=0	actual=0
- status=PASS	check=START_RECORDS_PRESENT	expected=present	actual=present
- status=PASS	check=RULINGS_NOT_TRUNCATED	expected=1	actual=1
- status=PASS	check=RULINGS_PREFIX_OF_START_UNCHANGED	expected=a8a650c145b9f53a843ef3087968056ec97d770d878977043d557da6f615e95c	actual=a8a650c145b9f53a843ef3087968056ec97d770d878977043d557da6f615e95c
- status=PASS	check=RULINGS_MAX_U_377	expected=U377	actual=U377
- status=FAIL	check=RULINGS_LINES_5_FIELDS	expected=1	actual=0
- status=PASS	check=ERRATA_S5_PREFIX_OF_START_UNCHANGED	expected=c6d2acb7148f89659db418bc071b245b08c49a0f3a6e718a5b27bb3761aadfad	actual=c6d2acb7148f89659db418bc071b245b08c49a0f3a6e718a5b27bb3761aadfad
- status=PASS	check=ERRATA_S5_LAST_IS_ES5_8	expected=ES5-8	actual=ES5-8
- status=PASS	check=STATE_BYTES_LE_8192	expected=1	actual=1
- status=PASS	check=STATE_MARKERS	expected=1	actual=1
- status=PASS	check=COMMIT_I_PRESENT	expected=1	actual=1
- status=PASS	check=FROZEN_LIST_PRESENT	expected=present	actual=present
- status=PASS	check=POST_I_NO_TESTING_D003_WRITES	expected=0	actual=0
- status=PASS	check=COMMITTED_I_FILES_UNCHANGED_AT_END	expected=unmodified	actual=unmodified
- status=FAIL	check=MODIFIED_TRACKED_FILES_WITHIN_END_ALLOW_LIST	expected=ok	actual=M PROJECT_ROADMAP.md
- status=PASS	check=COPY_DIFF_STRICT_UNEXPECTED_ZERO	expected=0	actual=0
- status=FAIL	check=REJUDGE_DIFFS_ZERO	expected=0	actual=MISSING
- status=FAIL	check=READINESS_GAP_ZERO	expected=0	actual=2
- status=PASS	check=ACCEPTANCE_ALL_MET	expected=0	actual=0
- status=PASS	check=REGISTRY_APPLY_ASSERT_ONLY_LISTED	expected=PASS	actual=PASS
- status=PASS	check=REGISTRY_ISSUE_SHA_MATCHES_AFTER	expected=a2d113b50554c16350e92703954b511c10432437cebedbdbdca6bbf414f873d9	actual=a2d113b50554c16350e92703954b511c10432437cebedbdbdca6bbf414f873d9
- status=PASS	check=REGISTRY_ROADMAP_SHA_MATCHES_AFTER	expected=5a22f21ea6788f932a5d8a14c3d35c4b2e705b45266bd1ccd2b15ba8ea60ff06	actual=5a22f21ea6788f932a5d8a14c3d35c4b2e705b45266bd1ccd2b15ba8ea60ff06
- status=PASS	check=REGISTRY_ISSUE_HAS_ES5_6	expected=1	actual=1
- status=PASS	check=REGISTRY_ROADMAP_HAS_ES5_6	expected=1	actual=1
- status=PASS	check=REPORT_PRESENT	expected=present	actual=present
- status=PASS	check=REPORT_CHECK_FAILS_ZERO	expected=0	actual=0
- status=PASS	check=REPORT_VERDICT_LINE	expected=1	actual=1
- status=PASS	check=REPORT_SIGNOFF_DRAFT_REF	expected=1	actual=1
- status=FAIL	check=REGISTRIES_SUMS_ALL_OK	expected=26/OK	actual=9/OK
- status=PASS	check=EVIDENCE_SHA256SUMS_OK	expected=OK	actual=OK
- status=PASS	check=EVIDENCE_SUMS_COVERS_ALL	expected=missing=none extra=none	actual=missing=none extra=none
- status=PASS	check=EVIDENCE_SUMS_TRUNC_LINE_IS_SHA_SUMS_CALL	expected=OK	actual=OK
- status=PASS	check=EVENTS_ROW_SET_EQ_RECOMPUTATION	expected=OK	actual=OK
- status=PASS	check=TMP_SNAPSHOT_UNCHANGED	expected=0/01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b	actual=0/01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b
- status=PASS	check=OTHER_ROUND_EVIDENCE_UNTOUCHED	expected=none	actual=none
- status=PASS	check=REPORT_CHECK_STATE_BYTES_LE_8192	expected=2946	actual=2946
