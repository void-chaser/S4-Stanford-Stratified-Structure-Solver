#!/bin/bash
# Fake S4-FMM driver, one variant per invocation.
#   $1 = variant   $2 = declared branch (used for witness/hit lines)
# Unknown variants are a hard ARGERROR (exit 2); there is no default success
# output and no fallthrough that silently produces empty output.
#
# Variant behaviours are preserved from the archived inputs; each variant now
# also carries a valid final "RESULT pattern both PASS" and a valid
# declared-branch WITNESS unless the variant exists specifically to break that
# element.  That way every negative case is rejected by its own intended rule
# instead of incidentally by "no final PASS".
set -u
ulimit -c 0
V="$1"; BR="${2:-fft}"

hit_line() { printf 'S4FMM HIT real malloc failure: stage=%s branch=%s plan_call=1 alloc=1 exec=1 bytes=16 (hit=%s)\n' "$1" "$BR" "$2"; }
witness()  { printf 'S4FMM WITNESS branch=%s enter\n' "$1"; }
checks()   { printf 'CHECK failed layer kept no partial modes before retry ok\nCHECK retry output is finite                   ok\n'; }
done_()    { echo "S4FMM DRIVER DONE"; }
pass_()    { echo "RESULT pattern both PASS"; }
diag_()    { echo "RESULT injected failure observed"; }
rc_pair()  { if [ "$1" = 0 ]; then echo "RC first 0"; else echo "RC first 1"; fi; echo "RC retry 0"; }

case "$V" in
  # ------------------------------------------------- fault, one valid HIT
  # Valid positives: correct HIT once, declared WITNESS, first 1 / retry 0,
  # final PASS and completion marker exactly once.
  clean-hit|fault-ok)
    hit_line plan 1
    rc_pair 1
    witness "$BR"
    checks
    diag_
    pass_
    done_
    exit 0 ;;

  # Fault-side negatives.  Each keeps a valid final PASS and a valid
  # declared-branch WITNESS so only the named rule can reject it.
  exit77|nohit|rc1zero|nomarker|san|hang|signal|probe-hit-ok|probe-hit-extra)
    case "$V" in
      nohit) : ;;                                   # deliberately no HIT line
      *)     hit_line plan 1 ;;
    esac
    case "$V" in probe-hit-extra) hit_line plan 2 ;; esac
    case "$V" in rc1zero) rc_pair 0 ;; *) rc_pair 1 ;; esac
    witness "$BR"
    checks
    diag_
    pass_
    case "$V" in nomarker) : ;; *) done_ ;; esac
    case "$V" in san) echo "==1==ERROR: AddressSanitizer: heap-use-after-free on address 0x1" ;; esac
    case "$V" in
      hang)   sleep 600 ;;
      signal) kill -SEGV $$ ;;
      exit77) exit 77 ;;
      *)      exit 0 ;;
    esac ;;

  # Defect A: every fault-success hallmark except the complete final PASS.
  no-final-pass)
    hit_line plan 1
    rc_pair 1
    witness "$BR"
    checks
    diag_
    done_
    exit 0 ;;

  # Defect B: declared WITNESS is correct, the HIT carries a different branch.
  wrong-branch)
    BR=vl hit_line plan 1
    rc_pair 1
    witness fft
    checks
    diag_
    pass_
    done_
    exit 0 ;;

  # ------------------------------------------------------ clean no-hit runs
  nohit-first-error|nohit-exit77|nohit-timeout|nohit-signal|baseline-nohit|witness-none-probe)
    if [ "$V" = nohit-first-error ]; then echo "RC first 1"; else echo "RC first 0"; fi
    echo "RC retry 0"
    case "$V" in witness-none-probe) witness none ;; *) witness "$BR" ;; esac
    echo "CHECK retry output is finite                   ok"
    pass_
    case "$V" in
      nohit-exit77)  done_; exit 77 ;;
      nohit-timeout) done_; sleep 600 ;;
      nohit-signal)  done_; kill -SEGV $$ ;;
      *)             done_; exit 0 ;;
    esac ;;

  # R8: no HIT, only a branch=none witness --> missing declared-branch witness.
  witness-none-only)
    echo "RC first 0"
    echo "RC retry 0"
    witness none
    pass_
    done_
    exit 0 ;;

  # ------------------------------------------------- control-style clean run
  clean-nohit)
    echo "RC first 0"
    echo "RC retry 0"
    witness "$BR"
    echo "CHECK retry output is finite                   ok"
    pass_
    done_
    exit 0 ;;

  # R9: declared-branch witness present, plus an ADDITIONAL branch=none witness.
  witness-extra-none)
    echo "RC first 0"
    echo "RC retry 0"
    witness "$BR"
    witness none
    pass_
    done_
    exit 0 ;;

  # --------------------------------------------------------------- baseline
  # Hit ignored, no crash: allowed by the independent baseline rule.
  baseline-hit-ignored)
    hit_line plan 1
    echo "RC first 0"
    echo "RC retry 0"
    witness "$BR"
    witness none
    done_
    pass_
    exit 0 ;;

  # Target crash after a hit: allowed by the independent baseline rule.
  baseline-hit-target-crash)
    hit_line plan 1
    witness "$BR"
    done_
    kill -SEGV $$ ;;

  # ==================== correction-round regression variants ==============
  # R1 / audit pass-suffix: only "RESULT pattern both PASS-extra", no complete
  # final PASS line.
  pass-suffix)
    echo "RC first 0"
    echo "RC retry 0"
    witness "$BR"
    echo "RESULT pattern both PASS-extra"
    done_
    exit 0 ;;

  # R2: the complete final PASS line appears twice.
  pass-twice)
    echo "RC first 0"
    echo "RC retry 0"
    witness "$BR"
    pass_
    pass_
    done_
    exit 0 ;;

  # R3 / audit witness-prefix: branch=vl with a separate xbranch=fft field.
  # xbranch is not a branch field, so the declared branch is not witnessed.
  witness-prefix)
    echo "RC first 0"
    echo "RC retry 0"
    echo "S4FMM WITNESS branch=vl xbranch=fft enter"
    pass_
    done_
    exit 0 ;;

  # R4 / audit witness-double: two branch fields on one WITNESS record.
  witness-double)
    echo "RC first 0"
    echo "RC retry 0"
    echo "S4FMM WITNESS branch=vl branch=fft enter"
    pass_
    done_
    exit 0 ;;

  # R6: HIT branch value is an extension of the declared branch.
  hit-extra)
    echo "S4FMM HIT real malloc failure: stage=plan branch=fft-extra plan_call=1 alloc=1 exec=1 bytes=16 (hit=1)"
    rc_pair 1
    witness "$BR"
    diag_
    pass_
    done_
    exit 0 ;;

  # R7: HIT is valid but the only WITNESS records branch=none.
  witness-only-none)
    hit_line plan 1
    rc_pair 1
    witness none
    diag_
    pass_
    done_
    exit 0 ;;

  # R5 / audit hit-unbalanced: two HIT lines, one with a duplicated branch
  # field and one with no branch field at all.
  hit-unbalanced)
    echo "S4FMM HIT real malloc failure: stage=plan branch=fft branch=fft plan_call=1 alloc=1 exec=1 bytes=16 (hit=1)"
    echo "S4FMM HIT real malloc failure: stage=plan plan_call=1 alloc=1 exec=1 bytes=16 (hit=2)"
    rc_pair 1
    witness "$BR"
    diag_
    pass_
    done_
    exit 0 ;;

  # N1: control with no HIT, but the FIRST attempt reports a failure.
  # Everything else is a normal clean run, so only the original per-attempt
  # check can reject it.
  control-first-error)
    echo "RC first 1"
    echo "RC retry 0"
    witness "$BR"
    pass_
    done_
    exit 0 ;;

  # N2: control with no HIT, but the RETRY attempt reports a failure.
  control-retry-error)
    echo "RC first 0"
    echo "RC retry 1"
    witness "$BR"
    pass_
    done_
    exit 0 ;;

  # N3: control whose WITNESS carries a glob metacharacter as the branch
  # value.  The branch field must be read from the log text alone, so a file
  # named branch=fft in the cwd must not turn "*" into "fft".
  branch-glob)
    echo "RC first 0"
    echo "RC retry 0"
    echo "S4FMM WITNESS branch=* enter"
    pass_
    done_
    exit 0 ;;

  *) echo "S4FMM ARGERROR unknown fake variant: $V" >&2; exit 2 ;;
esac
