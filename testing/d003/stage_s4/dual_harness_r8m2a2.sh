REPO=$(git rev-parse --show-toplevel); EV=$REPO/checkpoints/p05/evidence/p05-s4r8/m2a2; mkdir -p "$EV/tmp"; export TMPDIR="$EV/tmp"
# dual_harness_r8m2a2.sh -- P05-S4 R8 M2a2 R3: synthetic test of the dual-target injector rules (NOT an S4 driver).
# Each case sets the environment, runs the synthetic harness (no libS4 linked), and records one TSV row.
# Expectations are written here BEFORE the run (from the rules in the brief, section 1), not read from the output.
# Output: $EV/DUAL_HARNESS_R8_M2a2.tsv ; last line HARNESS=PASS or HARNESS=FAIL.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2a2 -- sh testing/d003/stage_s4/dual_harness_r8m2a2.sh harness_try3
# Refused if the output file exists (U17).
set -u
SUB=${1:-harness_try3}
H=$EV/build/$SUB
OUT=$EV/DUAL_HARNESS_R8_M2a2.tsv
if [ -e "$OUT" ]; then
    echo "dual_harness_r8m2a2: REFUSED exists (U17): $OUT" >&2
    exit 2
fi
for x in "$H/dual_harness_r8m2a2" "$H/dual_harness_r8m2a2_suppress"; do
    if [ ! -x "$x" ]; then echo "dual_harness_r8m2a2: missing executable $x" >&2; exit 2; fi
done

# case table: name | exe | env assignments | expect: s4_null b2_info hits hits2 invalid2 suppressed2 | rule
# The expectation for hits counts ALL injections (target 1 and target 2); hits2 counts target 2 only.
CASES='
C1_same_event_same_spelling|dual_harness_r8m2a2|S4FMM_INJECT=s4malloc S4FMM_NTH=2 S4FMM_INJECT2=s4malloc S4FMM_NTH2=2|1 0 1 0 1 0|rule2 same stream index -> INVALID, target 2 never fires
C2_same_event_leading_zero|dual_harness_r8m2a2|S4FMM_INJECT=s4malloc S4FMM_NTH=2 S4FMM_INJECT2=s4malloc S4FMM_NTH2=02|1 0 1 0 1 0|rule1 leading zero -> INVALID
C3_distinct_index|dual_harness_r8m2a2|S4FMM_INJECT=s4malloc S4FMM_NTH=2 S4FMM_INJECT2=s4malloc S4FMM_NTH2=4|2 0 2 1 0 0|different stream index -> both targets hit once
C4_cross_kind_s4malloc_plancall|dual_harness_r8m2a2|S4FMM_INJECT=s4malloc S4FMM_NTH=2 S4FMM_INJECT2=plancall:2:1|1 0 2 1 0 0|rule3 cross kind -> no conflict, both hit once
C5_noncanonical_plus_sign|dual_harness_r8m2a2|S4FMM_INJECT=s4malloc S4FMM_NTH=2 S4FMM_INJECT2=s4malloc S4FMM_NTH2=+3|1 0 1 0 1 0|rule1 sign -> INVALID
C6_noncanonical_blank|dual_harness_r8m2a2|S4FMM_INJECT=s4malloc S4FMM_NTH=2 S4FMM_INJECT2=s4malloc S4FMM_NTH2=3x|1 0 1 0 1 0|rule1 trailing text -> INVALID
C7_plancall_same_K_distinct_M|dual_harness_r8m2a2|S4FMM_INJECT=plancall:1:1 S4FMM_INJECT2=plancall:1:3|0 0 2 1 0 0|rule2 same K different M -> not a conflict, both hit once
C8_plancall_same_KM|dual_harness_r8m2a2|S4FMM_INJECT=plancall:1:2 S4FMM_INJECT2=plancall:1:2|0 0 1 0 1 0|rule2 same (K,M) -> INVALID
C9_b2_distinct_K|dual_harness_r8m2a2|S4FMM_INJECT=linearsolve_null2:244:1 S4FMM_INJECT2=linearsolve_null2:244:2|0 2 2 1 0 0|rule2 same ID different K -> both hit once
C10_b2_same_IDK|dual_harness_r8m2a2|S4FMM_INJECT=linearsolve_null2:244:2 S4FMM_INJECT2=linearsolve_null2:244:2|0 1 1 0 1 0|rule2 same (ID,K) -> INVALID
C11_suppressed_runtime|dual_harness_r8m2a2_suppress|S4FMM_INJECT=s4malloc S4FMM_NTH=2 HARNESS_FORCE_T2=1:2:0|1 0 1 0 0 1|rule4 target 1 consumes the same event -> SUPPRESSED (defence; parse-time rule 2 bypassed by the harness-only force path)
'
ROWS=0; FAILS=0
{
    printf 'case\texe\tenv\texpect_s4_null\texpect_b2_info\texpect_hits\texpect_hits2\texpect_invalid2\texpect_suppressed2\tobs_s4_null\tobs_b2_info\tobs_hits\tobs_hits2\tobs_invalid2\tobs_suppressed2\trc\tverdict\trule\n'
} > "$OUT"
printf '%s\n' "$CASES" | while IFS='|' read -r name exe envs expect rule; do
    [ -n "$name" ] || continue
    # expectation fields are the six numbers, in the order of the header
    set -- $expect
    e1=$1; e2=$2; e3=$3; e4=$4; e5=$5; e6=$6
    # run the case: environment only from $envs (no other S4FMM_* variables are inherited).  The harness's own exit
    # status is recorded (not the status of grep), stdout and stderr go to files under $EV/tmp.
    env -i PATH="$PATH" TMPDIR="$EV/tmp" $envs "$H/$exe" > "$EV/tmp/dual_${name}_stdout.txt" 2> "$EV/tmp/dual_${name}_stderr.txt"
    rc=$?
    line=$(grep '^HARNESS_RESULT' "$EV/tmp/dual_${name}_stdout.txt")
    o1=$(printf '%s\n' "$line" | sed -n 's/.*s4_null=\([0-9-]*\).*/\1/p')
    o2=$(printf '%s\n' "$line" | sed -n 's/.*b2_info=\([0-9-]*\).*/\1/p')
    o3=$(printf '%s\n' "$line" | sed -n 's/.*hits=\([0-9-]*\).*/\1/p')
    o4=$(printf '%s\n' "$line" | sed -n 's/.*hits2=\([0-9-]*\).*/\1/p')
    o5=$(printf '%s\n' "$line" | sed -n 's/.*invalid2=\([0-9-]*\).*/\1/p')
    o6=$(printf '%s\n' "$line" | sed -n 's/.*suppressed2=\([0-9-]*\).*/\1/p')
    v=PASS
    [ -n "$line" ] || v=FAIL
    [ "$o1" = "$e1" ] && [ "$o2" = "$e2" ] && [ "$o3" = "$e3" ] && [ "$o4" = "$e4" ] && [ "$o5" = "$e5" ] && [ "$o6" = "$e6" ] || v=FAIL
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$name" "$exe" "$envs" "$e1" "$e2" "$e3" "$e4" "$e5" "$e6" "$o1" "$o2" "$o3" "$o4" "$o5" "$o6" "$rc" "$v" "$rule" >> "$OUT"
done
# verdict over the table: a failed case, or a missing row, fails the harness
FAILS=$(awk -F'\t' 'NR>1 && $17!="PASS"{n++} END{print n+0}' "$OUT")
ROWS=$(awk -F'\t' 'NR>1{n++} END{print n+0}' "$OUT")
echo "CASES_ROWS=$ROWS FAILS=$FAILS" >> "$OUT"
if [ "$FAILS" -eq 0 ] && [ "$ROWS" -eq 11 ]; then
    echo "HARNESS=PASS" >> "$OUT"
else
    echo "HARNESS=FAIL" >> "$OUT"
fi
tail -n 3 "$OUT"
