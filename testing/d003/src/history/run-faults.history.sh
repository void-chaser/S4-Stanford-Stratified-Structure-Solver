#!/bin/bash
# Strict fault matrix for the FMM epsilon path.
#
#   run-faults.sh <tree> <label> <mode:strict|baseline> [driver-binary]
#
# Every "expected fault" case passes only when all of these hold:
#   process exit 0; the declared fault hit exactly the declared number of times;
#   first call returns the memory code 1; retry returns 0; outputs and both
#   sentinels untouched on the failure; retry output entirely finite; the driver
#   reported no FAILED check and a PASS; the completed marker is present exactly
#   once; and there is no sanitizer/timeout/signal diagnostic.
# "baseline" judges the pre-fix tree instead: an expected fault must show the
# defect (exit 0 with the fault having fired, or a crash), so its rules differ.
set -u
H="$(cd "$(dirname "$0")" && pwd)"
TREE="${1:?usage: run-faults.sh <tree> <label> <strict|baseline> [driver]}"
LABEL="${2:?label}"; MODE="${3:-strict}"; DRIVER="${4:-}"
BIN="${DRIVER:-$H/bin/driver-$LABEL}"
if [ -z "$DRIVER" ]; then
  mkdir -p "$H/bin" "$H/logs"
  g++ -O1 -I "$TREE/S4" -I "$TREE/S4/fmm" "$H/src/driver.cpp" "$H/src/inject.cpp" \
      -o "$BIN" -L "$TREE/build" -lS4 -llapack -lblas \
      -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan \
      -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i > "$H/logs/build-$LABEL.log" 2>&1 \
    || { echo "BUILD FAILED for $LABEL"; tail -5 "$H/logs/build-$LABEL.log"; exit 2; }
fi
pass=0; fail=0; na=0; n=0
# spec: branch stage plan_call alloc exec hits type ng outs
run_one() {
  local br="$1" stage="$2" pc="$3" al="$4" ex="$5" hits="$6" type="$7" ng="$8" outs="$9"
  n=$((n+1))
  local log="$H/logs/$LABEL-$br-$stage-$pc-$al-$ex-$type.log"
  local rc=0
  timeout 300 env FMM_MODE="$br" S4FMM_NG="$ng" S4FMM_STAGE="$stage" S4FMM_PLAN_CALL="$pc" \
      S4FMM_ALLOC="$al" S4FMM_EXEC="$ex" "$BIN" pattern "$outs" 4 3 > "$log" 2>&1 || rc=$?
  local rc1 rc2 hit bad done san res why=""
  rc1=$(grep -oE '^RC first -?[0-9]+' "$log" | awk '{print $3}')
  rc2=$(grep -oE '^RC retry -?[0-9]+' "$log" | awk '{print $3}')
  hit=$(grep -c '^S4FMM HIT' "$log")
  bad=$(grep -c 'FAILED' "$log")
  done=$(grep -c '^S4FMM DRIVER DONE' "$log")
  res=$(grep -c '^RESULT pattern both PASS' "$log")
  san=$(grep -cE 'ERROR: AddressSanitizer|ERROR: LeakSanitizer|SUMMARY: (Address|UndefinedBehavior)Sanitizer|runtime error:|AddressSanitizer:DEADLYSIGNAL|ABORTING' "$log")
  case "$type" in
    fault)
      [ "$rc" = 0 ] || why="$why; exit=$rc${rc:+$([ "$rc" = 124 ] && echo '(timeout)')$([ "$rc" -ge 128 ] 2>/dev/null && echo '(signal)')}"
      [ "$hit" = "$hits" ] || why="$why; hits=$hit want=$hits"
      [ "$rc1" = 1 ] || why="$why; rc1=${rc1:-none} want=1"
      [ "$rc2" = 0 ] || why="$why; rc2=${rc2:-none} want=0"
      [ "$bad" = 0 ] || why="$why; failed_checks=$bad"
      [ "$res" = 1 ] || why="$why; driver not PASS"
      [ "$done" = 1 ] || why="$why; completed marker=$done"
      [ "$san" = 0 ] || why="$why; sanitizer_lines=$san"
      ;;
    control)
      [ "$rc" = 0 ] || why="$why; exit=$rc"
      [ "$hit" = 0 ] || why="$why; unexpected hits=$hit"
      [ "$rc1" = 0 ] || why="$why; rc1=${rc1:-none} want=0 (no injection)"
      [ "$rc2" = 0 ] || why="$why; rc2=${rc2:-none}"
      [ "$bad" = 0 ] || why="$why; failed_checks=$bad"
      [ "$res" = 1 ] || why="$why; driver not PASS"
      [ "$done" = 1 ] || why="$why; completed marker=$done"
      [ "$san" = 0 ] || why="$why; sanitizer_lines=$san"
      ;;
    probe)   # reachability probe: ok either way, but a hit must behave like a fault
      if [ "$hit" != 0 ]; then
        [ "$rc" = 0 ] || why="$why; exit=$rc"
        [ "$rc1" = 1 ] || why="$why; rc1=${rc1:-none} want=1 after a hit"
        [ "$rc2" = 0 ] || why="$why; rc2=${rc2:-none}"
        [ "$bad" = 0 ] || why="$why; failed_checks=$bad"
        [ "$san" = 0 ] || why="$why; sanitizer_lines=$san"
      fi
      ;;
    baseline) # pre-fix tree: the defect is that the failure is ignored (or crashes)
      if [ "$hit" != 0 ]; then
        if [ "$rc" = 0 ] && [ "$rc1" = 0 ]; then why=""
        elif [ "$rc" -ge 128 ] 2>/dev/null || [ "$rc" = 134 ] || [ "$rc" = 139 ]; then why=""
        else why="$why; unexpected: exit=$rc rc1=${rc1:-none}"; fi
      else
        why=""
      fi
      ;;
  esac
  local verdict
  if [ -z "$why" ]; then verdict=PASS; pass=$((pass+1))
  else verdict=FAIL; fail=$((fail+1)); fi
  printf "  %-8s %-7s pc=%s al=%s ex=%s %-8s ng=%-2s %-4s rc=%-3s rc1=%-4s rc2=%-4s hit=%s checks=%s marker=%s res=%s san=%s %s\n" \
    "$br" "$stage" "$pc" "$al" "$ex" "$type" "$ng" "$verdict" "$rc" "${rc1:-none}" "${rc2:-none}" "$hit" "$bad" "$done" "$res" "$san" "$why"
}
echo "== FMM fault matrix ($MODE) =="
if [ "$MODE" = baseline ]; then
  for br in fft kottke jones nv vl; do
    run_one "$br" plan  1 1 0 1 fault 9 both
    run_one "$br" exec  0 0 1 1 fault 9 both
  done
  run_one fft scratch 0 1 1 1 fault 1 both
else
  # normal controls (no injection)
  for br in fft kottke jones nv vl; do run_one "$br" none 0 0 0 0 control 9 both; done
  run_one fft none 0 0 0 0 control 1 both
  # real execution-stage allocation failure: FFT with NumBasis=1 -> 1x1 grid -> 16 B scratch
  run_one fft scratch 0 1 1 1 fault 1 both
  run_one fft scratch 0 1 2 1 fault 1 both
  # real preparation-stage allocation failures
  for br in fft kottke jones nv vl; do run_one "$br" plan 1 1 0 1 fault 9 both; done
  run_one fft    plan 2 1 0 1 fault 9 both      # a later plan
  run_one kottke plan 2 1 0 1 fault 9 both
  # execution-entry boundary simulation (no real execution allocation exists there)
  for br in fft kottke jones nv vl; do run_one "$br" exec 0 0 1 1 fault 9 both; done
  run_one jones exec 0 0 4 1 fault 9 both       # a later local transform: LU/cache must be skipped
  # reachability probes: is a 16-byte scratch allocation reached on an 8x8 FMM grid?
  for br in kottke jones nv vl; do run_one "$br" scratch 0 1 1 0 probe 9 both; done
fi
echo "TOTAL cases=$n pass=$pass fail=$fail inapplicable=$na"
[ "$fail" = 0 ]
