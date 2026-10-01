#!/bin/bash
# Single-case runner.  run-one.sh <type> <branch> <ng> <stage> <plan_call> <alloc> <exec> <hits>
# Types: control | fault | probe | baseline
# S4FMM_BIN  : driver binary (real runs)
# S4FMM_FAKE : fake variant (negative/classification controls)
#
# Correction round: fixes the two runner defects
#   A. the final success marker is the complete line "RESULT pattern both PASS"
#      and it must occur exactly once;
#   B. the declared-branch witness must come from a WITNESS record, and every
#      HIT must carry its own matching branch field.
set -u
D="$(cd "$(dirname "$0")" && pwd)"
TYPES="control fault probe baseline"
[ "$#" = 8 ] || { echo "ARGERROR: expected 8 arguments, got $#"; exit 2; }
TYPE="$1"; BR="$2"; NG="$3"; STAGE="$4"; PC="$5"; AL="$6"; EX="$7"; HITS="$8"
case " $TYPES " in *" $TYPE "*) : ;; *) echo "ARGERROR: unknown type '$TYPE'"; exit 2 ;; esac
case "$BR" in fft|kottke|jones|nv|vl) : ;; *) echo "ARGERROR: unknown branch '$BR'"; exit 2 ;; esac
for v in "$NG" "$PC" "$AL" "$EX" "$HITS"; do case "$v" in ''|*[!0-9]*) echo "ARGERROR: non-numeric argument '$v'"; exit 2 ;; esac; done
LOG="$D/logs/one-$TYPE-$BR-$NG-$STAGE-$PC-$AL-$EX-${S4FMM_FAKE:-real}.log"
rc=0
if [ -n "${S4FMM_FAKE:-}" ]; then
  timeout "${S4FMM_TIMEOUT:-300}" "$D/fake.sh" "$S4FMM_FAKE" "$BR" > "$LOG" 2>&1 || rc=$?
else
  timeout "${S4FMM_TIMEOUT:-300}" env FMM_MODE="$BR" S4FMM_NG="$NG" S4FMM_STAGE="$STAGE" \
    S4FMM_PLAN_CALL="$PC" S4FMM_ALLOC="$AL" S4FMM_EXEC="$EX" \
    "${S4FMM_BIN:-$D/driver}" pattern both 4 3 > "$LOG" 2>&1 || rc=$?
fi

# ---------------------------------------------------------------- raw counts
rc1=$(grep -oE '^RC first -?[0-9]+' "$LOG" | awk '{print $3}')
rc2=$(grep -oE '^RC retry -?[0-9]+' "$LOG" | awk '{print $3}')
hit=$(grep -c '^S4FMM HIT' "$LOG")
bad=$(grep -c 'FAILED' "$LOG")
mk=$(grep -c '^S4FMM DRIVER DONE' "$LOG")
san=$(grep -cE 'ERROR: AddressSanitizer|ERROR: LeakSanitizer|SUMMARY: (Address|UndefinedBehavior)Sanitizer|runtime error:|AddressSanitizer:DEADLYSIGNAL|ABORTING' "$LOG")
argerr=$(grep -c 'ARGERROR' "$LOG")

# ---- defect A: count COMPLETE lines only, never a prefix or a suffix match.
# grep -x makes the whole line the pattern, so
#   "RESULT pattern both PASS-extra"  does not match
#   "RESULT pattern both PASS x"      does not match
# and trim/normalisation is never used to turn an illegal line into a legal one.
final_pass=$(grep -cxF 'RESULT pattern both PASS' "$LOG")
# Diagnostic line: may coexist with success, never substitutes for it.
diag_observed=$(grep -cxF 'RESULT injected failure observed' "$LOG")

# --------------------------------------------- defect B: strict field parsing
# These helpers must read the log text only.  If pathname expansion were
# active, an unquoted "$line" containing a value such as branch=* would be
# glob-expanded against the current directory, so a field named branch=fft
# sitting in the cwd could turn branch=* into branch=fft and flip the verdict.
# Expansion is therefore explicitly disabled around field splitting.
#
# field_count <name> <line> -> how many whitespace-separated fields are of the
# form NAME=value.  A field is an independent token, so xbranch=fft does not
# count as branch, and branch=fft-extra does not count as branch=fft.
field_count() {
  local want="$1" line="$2" f n=0
  case $- in *f*) ;; *) set -f ;; esac
  # shellcheck disable=SC2086
  for f in $line; do [ "${f%%=*}" = "$want" ] && n=$((n + 1)); done
  echo "$n"
}

# line_value <name> <line> -> value of the first NAME=value field
line_value() {
  local want="$1" line="$2" f
  case $- in *f*) ;; *) set -f ;; esac
  # shellcheck disable=SC2086
  for f in $line; do
    if [ "${f%%=*}" = "$want" ]; then echo "${f#*=}"; return 0; fi
  done
  echo ""
}

# line_parser <prefix> <line> <declared> <none-ok> <varname>
#   Validates ONE record line: the record name must have a field boundary, and
#   there must be exactly one branch= field whose value equals <declared>, or
#   equals none when <none-ok> is yes (WITNESS records only).  Any other
#   branch value, a missing field, an empty value, or a duplicate field is
#   rejected -- a correct field elsewhere on the line does not mask a wrong
#   one.  Sets <varname> to ok|notrecord|absentfield|badvalue|dupfield.
line_parser() {
  local prefix="$1" line="$2" declared="$3" none_ok="$4" __out="$5"
  local bc val
  # record name must be followed by whitespace (or end): WITNESS-extra and
  # AUDIT are therefore not witnesses.
  case "$line" in
    "$prefix"|"$prefix"[[:space:]]*) : ;;
    *) printf -v "$__out" '%s' 'notrecord'; return 0 ;;
  esac
  bc=$(field_count 'branch' "$line")
  if [ "$bc" = 0 ]; then printf -v "$__out" '%s' 'absentfield'; return 0; fi
  if [ "$bc" != 1 ]; then printf -v "$__out" '%s' 'dupfield'; return 0; fi
  val=$(line_value 'branch' "$line")
  if [ -z "$val" ]; then printf -v "$__out" '%s' 'badvalue'; return 0; fi
  if [ "$val" = "$declared" ]; then printf -v "$__out" '%s' 'ok'; return 0; fi
  if [ "$none_ok" = yes ] && [ "$val" = none ]; then printf -v "$__out" '%s' 'ok'; return 0; fi
  printf -v "$__out" '%s' 'badvalue'
  return 0
}

# ---- WITNESS: at least one declared-branch witness is required for
# control/fault/probe.  branch=none is allowed as an ADDITIONAL witness but
# never substitutes for the declared branch and never proves target entry.
wit_total=0; wit_declared=0; wit_none=0; wit_bad=0
wit_summary=""
while IFS= read -r line; do
  [ -n "$line" ] || continue
  wit_total=$((wit_total + 1))
  line_parser 'S4FMM WITNESS' "$line" "$BR" yes st
  case "$st" in
    ok)
      bval=$(line_value 'branch' "$line")
      if [ "$bval" = none ]; then wit_none=$((wit_none + 1)); else wit_declared=$((wit_declared + 1)); fi
      wit_summary="${wit_summary}${bval}," ;;
    *) wit_bad=$((wit_bad + 1)); wit_summary="${wit_summary}${st}," ;;
  esac
done < <(grep '^S4FMM WITNESS' "$LOG")
[ -n "$wit_summary" ] || wit_summary="none"

# ---- HIT: every HIT line must independently carry exactly one branch field
# equal to the declared branch.  Lines are judged one by one (never by pooling
# branch fields across lines), and only for fault and hit probe cases.
hit_valid=0; hit_bad=0; hit_summary=""
while IFS= read -r line; do
  [ -n "$line" ] || continue
  line_parser 'S4FMM HIT' "$line" "$BR" no st
  if [ "$st" = ok ]; then
    hit_valid=$((hit_valid + 1))
    hit_summary="${hit_summary}${BR},"
  else
    hit_bad=$((hit_bad + 1))
    hit_summary="${hit_summary}${st},"
  fi
done < <(grep '^S4FMM HIT' "$LOG")
[ -n "$hit_summary" ] || hit_summary="none"

# ------------------------------------------------------------ final verdict
why=""; verdict=PASS
case "$TYPE" in
  control|fault|probe)
    # checks shared by the three types that must exit normally
    [ "$argerr" = 0 ] || why="$why; ARGERROR in output"
    [ "$rc" = 0 ] || why="$why; exit=$rc"
    [ "$rc" = 124 ] && why="$why(timeout)"
    [ "$rc" -ge 128 ] 2>/dev/null && why="$why(signal)"
    [ "$san" = 0 ] || why="$why; sanitizer=$san"
    [ "$bad" = 0 ] || why="$why; FAILED=$bad"
    [ "$mk" = 1 ] || why="$why; marker=$mk"
    # defect A: exactly one complete final PASS line
    [ "$final_pass" = 1 ] || why="$why; final PASS count=$final_pass want=1"
    # defect B: the declared-branch witness must exist and no witness may be
    # malformed or carry an undeclared branch
    [ "$wit_bad" = 0 ] || why="$why; malformed witness=$wit_bad"
    [ "$wit_declared" -ge 1 ] || why="$why; no declared-branch WITNESS (declared=$BR)" ;;
esac
case "$TYPE" in
  control)
    [ "$hit" = 0 ] || why="$why; hits=$hit want=0"
    # original per-attempt checks: the control must not fail on either attempt
    [ "$rc1" = 0 ] || why="$why; rc1=${rc1:-none} want=0"
    [ "$rc2" = 0 ] || why="$why; rc2=${rc2:-none} want=0" ;;
  fault)
    [ "$hit" = "$HITS" ] || why="$why; hits=$hit want=$HITS"
    [ "$rc1" = 1 ] || why="$why; rc1=${rc1:-none} want=1"
    [ "$rc2" = 0 ] || why="$why; rc2=${rc2:-none} want=0"
    # every HIT must carry the declared branch
    [ "$hit_bad" = 0 ] || why="$why; HIT branch field invalid count=$hit_bad (declared=$BR)"
    [ "$hit_valid" = "$hit" ] || why="$why; valid HIT branch=$hit_valid want=$hit (declared=$BR)" ;;
  probe)
    if [ "$hit" = 0 ]; then
      # legitimately inapplicable only when everything succeeded normally
      [ "$rc1" = 0 ] || why="$why; no-hit but rc1=${rc1:-none}"
      [ "$rc2" = 0 ] || why="$why; rc2=${rc2:-none}"
      [ -z "$why" ] && verdict=INAPPLICABLE
    else
      [ "$hit" = "$HITS" ] || why="$why; hits=$hit want=$HITS"
      [ "$rc1" = 1 ] || why="$why; rc1=${rc1:-none} want=1 after a hit"
      [ "$rc2" = 0 ] || why="$why; rc2=${rc2:-none} want=0"
      [ "$hit_bad" = 0 ] || why="$why; HIT branch field invalid count=$hit_bad (declared=$BR)"
      [ "$hit_valid" = "$hit" ] || why="$why; valid HIT branch=$hit_valid want=$hit (declared=$BR)"
    fi ;;
  baseline)
    # the pre-fix tree is judged separately: no "must exit 0" rule, no final
    # PASS requirement after a crash, and branch=none is tolerated.
    [ "$argerr" = 0 ] || why="$why; ARGERROR in output"
    [ "$hit" -ge 1 ] || why="$why; no hit: proves nothing about the old tree"
    [ "$rc" = 124 ] && why="$why(timeout is not a target crash)"
    if [ -z "$why" ]; then
      if [ "$rc" = 0 ] && [ "$rc1" = 0 ]; then :
      elif [ "$rc" = 134 ] || [ "$rc" = 139 ]; then :
      else why="$why; unexpected exit=$rc rc1=${rc1:-none}"; fi
    fi ;;
esac
[ -n "$why" ] && verdict=FAIL

# One complete, parseable judgement record per run: one key=value per line, so
# no field can ever wrap and no partial continuation line can appear.
{
  printf 'record=verdict\n'
  printf 'case=%s branch=%s ng=%s stage=%s plan_call=%s alloc=%s exec=%s requested_hits=%s\n' \
    "$TYPE" "$BR" "$NG" "$STAGE" "$PC" "$AL" "$EX" "$HITS"
  printf 'proc_exit=%s rc1=%s rc2=%s hit=%s failed=%s marker=%s sanitizer=%s argerror=%s\n' \
    "$rc" "${rc1:-none}" "${rc2:-none}" "$hit" "$bad" "$mk" "$san" "$argerr"
  printf 'final_pass_count=%s diagnostic_count=%s\n' "$final_pass" "$diag_observed"
  printf 'witness_total=%s witness_declared=%s witness_none=%s witness_invalid=%s\n' \
    "$wit_total" "$wit_declared" "$wit_none" "$wit_bad"
  printf 'witness_branches=%s\n' "${wit_summary%,}"
  printf 'hit_branch_valid=%s hit_branch_invalid=%s\n' "$hit_valid" "$hit_bad"
  printf 'hit_branches=%s\n' "${hit_summary%,}"
  printf 'verdict=%s\n' "$verdict"
  printf 'reason=%s\n' "${why#; }"
}

[ "$verdict" = FAIL ] && exit 1
[ "$verdict" = INAPPLICABLE ] && exit 3
exit 0
