#!/bin/sh
# D003 safe wrapper (P05-S2R6, R6-1).
#
#   sh testing/d003/safe_run.sh [--allow-system-read] OUT_DIR -- COMMAND [ARG...]
#
# Purpose: every harness command that writes files runs through this wrapper, so that
# writes stay inside the repository.  The wrapper:
#   a) computes REPO (git toplevel of the current directory) and sets
#      EV = $REPO/checkpoints/p05/evidence/<OUT_DIR>, creates $EV/tmp, exports TMPDIR;
#   b) requires OUT_DIR to resolve (realpath: symlinks and '..' resolved) to a path INSIDE
#      $REPO, otherwise exits 2 with the reason, BEFORE any subcommand is started;
#   c) inspects the subcommand arguments: an absolute path outside $REPO is refused unless it
#      is a read-only system path (/usr, /bin, /lib, /lib64, /etc, /opt, /proc, /sys, /dev/null)
#      and --allow-system-read was given.  A refused argument exits 2 before any subcommand runs;
#   d) appends one record per call to $EV/safe_run.log (UTC time, cwd, OUT_DIR, command).
#
# Reading is not restricted.  The guard applies to arguments that name absolute paths; it
# does not parse shell redirections inside a quoted command string.  Callers must still
# follow the write-path rules in the task (see testing/d003/README.md).
#
# Exit status: 2 = refused by this wrapper (nothing executed); otherwise the subcommand's
# own exit status is returned unchanged.

set -u

usage() {
    echo "usage: sh testing/d003/safe_run.sh [--allow-system-read] OUT_DIR -- COMMAND [ARG...]" >&2
}

# refuse MESSAGE...  : print the reason, append it to the refusal log, exit 2.
# The refusal log lives in the round's evidence directory (repository only).  Before REPO is
# known (not inside a git work tree) only stderr is used.  Refusal happens before any
# subcommand runs, so a refused call leaves a log line and nothing else.
refuse() {
    echo "safe_run: REFUSED: $*" >&2
    if [ -n "${REPO:-}" ] && [ -d "$REPO" ]; then
        _rl="$REPO/checkpoints/p05/evidence/p05-s2r6"
        if mkdir -p "$_rl" 2>/dev/null; then
            printf '%s\tcwd=%s\tREFUSED\t%s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(pwd -P)" "$*" >> "$_rl/safe_run_refusals.log"
        fi
    fi
    exit 2
}

ALLOW_SYS=0
if [ "${1:-}" = "--allow-system-read" ]; then
    ALLOW_SYS=1
    shift
fi
if [ "$#" -lt 3 ]; then
    usage
    exit 2
fi
OUT_ARG=$1
shift
if [ "$1" != "--" ]; then
    usage
    exit 2
fi
shift
if [ "$#" -lt 1 ]; then
    echo "safe_run: no COMMAND given" >&2
    exit 2
fi

# a) repository root from the current directory (must be inside a git work tree)
if ! REPO=$(git rev-parse --show-toplevel 2>/dev/null) || [ -z "$REPO" ]; then
    echo "safe_run: REFUSED: not inside a git work tree" >&2
    exit 2
fi
REPO=$(realpath -m -- "$REPO")

# b) OUT_DIR is taken relative to the evidence directory; it must not contain '..' or
#    leading '/' so that it cannot name a location outside EV.  Its resolved path must be
#    inside $REPO.  The subdirectory name is the evidence subdirectory (e.g. p05-s2r6/run1).
case "$OUT_ARG" in
    /*) refuse "OUT_DIR must be a relative subdirectory name, got absolute path: $OUT_ARG";;
esac
case "/$OUT_ARG/" in
    */../*) refuse "OUT_DIR contains '..': $OUT_ARG";;
esac
EV_BASE="$REPO/checkpoints/p05/evidence"
EV=$(realpath -m -- "$EV_BASE/$OUT_ARG")
case "$EV" in
    "$REPO"/*) ;;
    *) refuse "resolved OUT_DIR is outside the repository: $EV";;
esac
# A symbolic link inside the evidence tree could point out of $REPO; refuse if any
# existing component of the path is a symlink.  Check each existing ancestor (read only).
_p="$EV_BASE"
for _c in $(printf '%s' "$OUT_ARG" | tr '/' ' '); do
    _p="$_p/$_c"
    if [ -L "$_p" ]; then
        refuse "OUT_DIR component is a symbolic link: $_p"
    fi
done
if [ -L "$EV_BASE" ]; then
    refuse "evidence base is a symbolic link: $EV_BASE"
fi

# c) absolute arguments of the subcommand
READONLY_SYS_RE='^/(usr|bin|lib|lib64|etc|opt|proc|sys)(/|$)'
for a in "$@"; do
    case "$a" in
        /dev/null) continue;;
        /*) ;;
        *) continue;;
    esac
    # an argument that is a path under REPO is fine
    ra=$(realpath -m -- "$a")
    case "$ra" in
        "$REPO"|"$REPO"/*) continue;;
    esac
    if [ "$ALLOW_SYS" -eq 1 ] && printf '%s\n' "$ra" | grep -Eq "$READONLY_SYS_RE"; then
        echo "safe_run: note: read-only system path allowed by --allow-system-read: $a" >&2
        continue
    fi
    refuse "absolute path outside the repository in the command: $a (resolved: $ra; use --allow-system-read only for read-only system paths)"
done

# d) prepare the evidence directory and the log.  Creation happens only after the checks.
mkdir -p "$EV/tmp" || { echo "safe_run: cannot create $EV/tmp" >&2; exit 2; }
TMPDIR="$EV/tmp"
export TMPDIR
export REPO EV
LOG="$EV/safe_run.log"
{
    printf '%s\tcwd=%s\tout=%s\tcmd=' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$(pwd -P)" "$EV"
    for w in "$@"; do printf '%s ' "$w"; done
    printf '\n'
} >> "$LOG"

# run the subcommand from the repository root; its exit status is returned unchanged
cd "$REPO" || exit 2
"$@"
exit $?
