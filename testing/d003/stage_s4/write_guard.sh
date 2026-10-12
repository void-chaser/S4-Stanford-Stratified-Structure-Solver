#!/bin/sh
# write_guard.sh -- P05-S4 (round R1, V0) write-path guard.
#
# Usage (every writing command of this round):
#   sh testing/d003/safe_run.sh p05-s4 -- sh testing/d003/stage_s4/write_guard.sh 'COMMAND TEXT'
#   sh testing/d003/safe_run.sh p05-s4 -- sh testing/d003/stage_s4/write_guard.sh --file SCRIPT
# SCRIPT must lie under $EV/ or under $REPO/testing/d003/stage_s4/.
#
# Scan (textual, before anything runs):
#   1. every redirection target written as  > TARGET,  >> TARGET,  N> TARGET  or  >|TARGET.
#      TARGET is taken as the text up to the next unquoted space, ';', '|', '&' or ')'.
#      A redirection whose target is a file descriptor (&1, &2) is not a file write.
#   2. the destination word of tee, cp, install, ln, mv, mkdir, touch, rm, chmod (after the mode),
#      dd of=, tar -C, make -C, sed -i (refused), git add/rm/mv/update-index/read-tree paths,
#      and the value of -o, -F, --report, --out, --outdir, --root, --log, --dst, --dest, --output,
#      --dir, --save (also in = form).
#   3. cd: the target must lie in an allowed prefix.
#
# Accepted target: after expansion of $EV, ${EV}, ${EV:?}, $REPO, ${REPO}, ${REPO:?}, the target
# starts with the literal prefix $REPO/checkpoints/p05/  or  $REPO/testing/d003/stage_s4/  (or
# equals one of those directories without a slash).  Shell expansions AFTER the prefix are allowed
# ("$EV/x/$name").  A variable BEFORE the prefix is refused, because the scan cannot resolve it.
#
# Refused (exit 3, nothing executed).  Each refusal and each acceptance is one line in
# $EV/write_guard.log.  Refused also: any absolute target outside the prefixes, any relative write
# target, ".." segments, command substitution, backquotes, heredocs (<<), sed -i, a line ending in a
# backslash in a scanned script, text-mode arguments of more than one line.
#
# Limits (stated): the scan is textual.  It cannot see writes made by programs (compilers, make,
# python, the driver, git internals) or by commands built with eval or with variables that are not
# resolvable.  Those are covered by the repository status audit, the /tmp snapshots, and the review of
# each script under testing/d003/stage_s4/.
#
# Exit status: 2 = usage or setup error; 3 = refused (nothing executed); otherwise the status of the
# executed command.

set -u
set -f

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "write_guard: not inside a git work tree" >&2; exit 2; }
if [ -z "$REPO" ]; then
    echo "write_guard: empty repository root" >&2
    exit 2
fi
EV="$REPO/checkpoints/p05/evidence/p05-s4"
TMPDIR="$EV/tmp"
LOG="$EV/write_guard.log"
export REPO EV TMPDIR
mkdir -p "$TMPDIR" || { echo "write_guard: cannot create $TMPDIR" >&2; exit 2; }

MODE=text
if [ "${1:-}" = "--file" ]; then
    MODE=file
    shift
fi
if [ "$#" -ne 1 ]; then
    echo "write_guard: usage: write_guard.sh [--file] ARG" >&2
    exit 2
fi
ARG=$1

log_line() {
    printf '%s\t%s\tmode=%s\tcwd=%s\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$MODE" "$(pwd -P)" "$2" >> "$LOG"
}

bad() {
    log_line REFUSED "$1"
    echo "write_guard: REFUSED: $1" >&2
    exit 3
}

# expand_vars TEXT: textual expansion of the variables the guard knows.
expand_vars() {
    printf '%s\n' "$1" | sed -e "s|\${EV:?}|$EV|g" -e "s|\${EV}|$EV|g" -e "s|\$EV|$EV|g" \
        -e "s|\${REPO:?}|$REPO|g" -e "s|\${REPO}|$REPO|g" -e "s|\$REPO|$REPO|g"
}

# check_target RAW ROLE : RAW is the target text as written (quotes still present).
check_target() {
    _q=$(printf '%s' "$1" | tr -d '"'"'"'')
    _e=$(expand_vars "$_q")
    if [ -z "$_e" ]; then
        bad "empty target (role $2)"
    fi
    case "$_e" in
        *'`'*|*'$('*|*'<'*|*'>'*|*'&'*|*';'*|*'|'*|*'*'*|*'?'*|*'['*|*']'*|*'{'*|*'}'*|*'~'*|*'\'*)
            bad "unsafe characters in target (role $2): $_q" ;;
    esac
    case "$_e" in
        */../*|*/..|../*|..)
            bad "target contains '..' (role $2): $_e" ;;
    esac
    case "$_e" in
        "$REPO/checkpoints/p05/"*|"$REPO/testing/d003/stage_s4/"*|"$REPO/checkpoints/p05"|"$REPO/testing/d003/stage_s4") ;;
        *)
            bad "target outside the allowed prefixes (role $2): $_e" ;;
    esac
}

# first_word TEXT : the leading shell word of TEXT, quotes kept (up to unquoted space or ;|&).
first_word() {
    printf '%s' "$1" | sed -e 's/^[[:space:]]*//' -e 's/^\("[^"]*"\|'"'"'[^'"'"']*'"'"'\|[^[:space:];|&)]*\).*/\1/'
}

# scan_redirections LINE : every > or >> target in LINE.  Each '>' is taken once, from the
# text that follows it; the remainder of the line is scanned for the next '>'.
scan_redirections() {
    _rest=$1
    while :; do
        case "$_rest" in
            *'>'*) ;;
            *) break ;;
        esac
        _after=${_rest#*>}
        # '>>' : drop the second '>'
        case "$_after" in
            '>'*) _after=${_after#>} ;;
        esac
        # '>|' : drop the '|'
        case "$_after" in
            '|'*) _after=${_after#|} ;;
        esac
        _rest=$_after
        # '>&N' names a file descriptor (2>&1, >&2): not a file write
        case "$_after" in
            '&'*) continue ;;
        esac
        _t=$(printf '%s' "$_after" | sed -e 's/^[[:space:]]*//')
        if [ -z "$_t" ]; then
            bad "redirection without a target"
        fi
        # the target must be written as a quoted or bare word that starts with an allowed
        # prefix: "$EV/...", "$REPO/checkpoints/p05/...", "$REPO/testing/d003/stage_s4/...",
        # or the same with ${EV}, ${REPO}, ${EV:?}, ${REPO:?}.  Anything else is refused.
        case "$_t" in
            '"$EV/'*|'"${EV}/'*|'"${EV:?}/'*|'"$EV"'*|'"${EV}"'*|'"${EV:?}"'*) ;;
            '"$REPO/checkpoints/p05/'*|'"${REPO}/checkpoints/p05/'*|'"${REPO:?}/checkpoints/p05/'*) ;;
            '"$REPO/testing/d003/stage_s4/'*|'"${REPO}/testing/d003/stage_s4/'*|'"${REPO:?}/testing/d003/stage_s4/'*) ;;
            "\"$REPO/checkpoints/p05\""*|"\"$REPO/testing/d003/stage_s4\""*) ;;
            "\"\$EV\""*|"\"\${EV:?}\""*|"\"\${EV}\""*) ;;
            '$EV/'*|'${EV}/'*|'${EV:?}/'*|'$REPO/checkpoints/p05/'*|'${REPO}/checkpoints/p05/'*|'${REPO:?}/checkpoints/p05/'*) ;;
            '$REPO/testing/d003/stage_s4/'*|'${REPO}/testing/d003/stage_s4/'*|'${REPO:?}/testing/d003/stage_s4/'*) ;;
            *) bad "redirection target is not written with an allowed prefix: $_t" ;;
        esac
        # the textual check above is on the form as written; the expansion must also land inside
        _w=$(first_word "$_t")
        check_target "$_w" redirect
    done
}

# scan_write_commands LINE : destination words of write commands and option values.
scan_write_commands() {
    _norm=$(printf '%s\n' "$1" | sed -e 's/&&/ ; /g' -e 's/||/ ; /g' -e 's/;/ ; /g' -e 's/|/ ; /g')
    _seg=$_norm
    _IFS_SAVE=$IFS
    # split segments on ';' and examine words of each simple command
    _cmdline=$(printf '%s\n' "$_seg" | tr ';' '\n')
    printf '%s\n' "$_cmdline" | while IFS= read -r _cl; do
        _c1=$(printf '%s' "$_cl" | sed -e 's/^[[:space:]]*//' -e 's/^[^[:space:]]*\/\([^[:space:]]*\)$/\1/')
        # first real command word after optional leading assignments and 'sh -c' wrappers
        set -- $_cl
        _cmd=""
        for _w in "$@"; do
            case "$_w" in
                *=*) continue ;;
            esac
            _cmd=$_w
            break
        done
        _cmd=$(printf '%s' "$_cmd" | tr -d "\"'")
        case "$_cmd" in
            tee|cp|install|ln|mv|mkdir|touch|rm|chmod|dd|tar|make|sed|git|python3|gcc|g++|cc|c++|ar|sort|cd)
                ;;
            *) continue ;;
        esac
        _last=""
        _pend=""
        _chm=0
        _gsub=""
        _gdash=0
        _seen=0
        for _w in "$@"; do
            if [ "$_seen" -eq 0 ]; then
                _x=$(printf '%s' "$_w" | tr -d "\"'")
                if [ "$_x" = "$_cmd" ]; then
                    _seen=1
                fi
                continue
            fi
            _x=$(printf '%s' "$_w" | tr -d "\"'")
            if [ -n "$_pend" ]; then
                _role=$_pend
                _pend=""
                case "$_role" in
                    cd) check_target "$_x" cd ;;
                    git) check_target "$_x" git ;;
                    *) check_target "$_x" "$_role" ;;
                esac
                continue
            fi
            case "$_x" in
                -o) _pend=o; continue ;;
                -F) _pend=git; continue ;;
                -C) _pend=dir-C; continue ;;
                --report|--out|--outdir|--out-dir|--root|--log|--dst|--dest|--output|--dir|--save)
                    _pend=optpath; continue ;;
                --report=*|--out=*|--outdir=*|--out-dir=*|--root=*|--log=*|--dst=*|--dest=*|--output=*|--dir=*|--save=*)
                    check_target "${_x#*=}" optpath; continue ;;
                of=*) check_target "${_x#of=}" dd-of; continue ;;
            esac
            case "$_cmd" in
                tee)
                    case "$_x" in -*) ;; *) check_target "$_x" tee ;; esac ;;
                cp|install|ln)
                    case "$_x" in -*) ;; *) _last=$_x ;; esac ;;
                mv|mkdir|touch|rm)
                    case "$_x" in -*) ;; *) check_target "$_x" "$_cmd" ;; esac ;;
                chmod)
                    case "$_x" in
                        -*) ;;
                        *)
                            if [ "$_chm" -eq 0 ]; then
                                _chm=1
                            else
                                check_target "$_x" chmod
                            fi ;;
                    esac ;;
                sed)
                    case "$_x" in
                        -i|-i*|--in-place*) bad "sed in-place write is not allowed" ;;
                    esac ;;
                tar)
                    case "$_x" in
                        -C) _pend=dir-C ;;
                    esac ;;
                cd)
                    check_target "$_x" cd ;;
                git)
                    if [ -z "$_gsub" ]; then
                        case "$_x" in
                            -*) ;;
                            *) _gsub=$_x ;;
                        esac
                        continue
                    fi
                    case "$_gsub" in
                        add|rm|mv|update-index|read-tree)
                            case "$_x" in -*) ;; *) check_target "$_x" git ;; esac ;;
                        clean|worktree|init|apply|am|cherry-pick|update-ref)
                            bad "git $_gsub is not allowed in this round" ;;
                    esac ;;
            esac
        done
        if [ -n "$_last" ]; then
            check_target "$_last" "$_cmd-dst"
        fi
        if [ -n "$_pend" ]; then
            bad "option without a value (role $_pend)"
        fi
    done
    IFS=$_IFS_SAVE
}

# strip_single_quoted LINE : replace the contents of single-quoted strings by nothing, so that a
# '>' or '<' inside 'quotes' (for example a C source text) is not read as a redirection.
strip_single_quoted() {
    printf '%s\n' "$1" | sed -e "s/'[^']*'/''/g"
}

scan_line() {
    _bare=$(strip_single_quoted "$1")
    case "$_bare" in
        *'<<'*) bad "heredoc is not allowed (use the write tool, then --file)" ;;
    esac
    scan_redirections "$_bare"
    scan_write_commands "$_bare"
}

if [ "$MODE" = file ]; then
    case "$ARG" in
        "$EV"/*|"$REPO/testing/d003/stage_s4/"*) ;;
        *) bad "script file must lie under EV or testing/d003/stage_s4: $ARG" ;;
    esac
    case "$ARG" in
        */../*|*/..) bad "script path contains '..': $ARG" ;;
    esac
    if [ ! -f "$ARG" ]; then
        bad "script file does not exist: $ARG"
    fi
    while IFS= read -r _line || [ -n "$_line" ]; do
        _t=$(printf '%s' "$_line" | sed -e 's/^[[:space:]]*//')
        case "$_t" in
            ''|'#'*) continue ;;
        esac
        case "$_line" in
            *\\) bad "line continuation backslash is not allowed in a scanned script" ;;
        esac
        scan_line "$_line"
    done < "$ARG"
    log_line ALLOW "scan passed: file $ARG"
    exec sh "$ARG"
else
    _nl=$(printf '%s' "$ARG" | wc -l | tr -d ' ')
    if [ "$_nl" -ne 0 ]; then
        bad "text mode takes one line; put a multi-line script in a file and use --file"
    fi
    scan_line "$ARG"
    log_line ALLOW "scan passed: text $ARG"
    exec sh -c "$ARG"
fi
