#!/bin/bash
# manifest-generate.sh <output-file> <path>...
#
# Writes "sha256  path" lines for regular files, sorted, and returns non-zero
# if ANY step fails: a missing input, an enumeration or hashing failure, the
# final sort, or writing the output.  A later successful command can never mask
# an earlier failure, and a failure never leaves a stale output file behind
# that a caller could mistake for a freshly generated manifest.
#
# The OUTPUT MANIFEST ITSELF is always excluded, by its real path rather than
# by filename: whether it is called SHA256SUMS or m.sha256, whether it does not
# exist yet (first generation) or already exists (regeneration), whether it is
# named with an absolute or relative path, and whether it is discovered by a
# directory scan or passed as an explicit input.  A manifest that listed itself
# would record its own stale hash and fail its own verification on the next
# generation.
set -u

OUT="$1"; shift
[ -n "$OUT" ] || { echo "usage: manifest-generate.sh <out> <path>..." >&2; exit 2; }

rc=0

# --- reject an output path that cannot be written as a regular file ---------
if [ -d "$OUT" ]; then
  echo "manifest-generate: output path is a directory: $OUT" >&2
  exit 1
fi

# --- canonical identity of the output --------------------------------------
# Compare the candidate and the output as files (-ef, which resolves symlinks
# and relative forms) and as canonical path strings (which also covers an
# output that does not exist yet).
canonical() {  # canonical <path>
  local p="$1"
  local d b
  if [ -e "$p" ]; then
    readlink -f -- "$p" 2>/dev/null && return 0
  fi
  d=$(dirname -- "$p")
  b=$(basename -- "$p")
  if [ -d "$d" ]; then
    ( cd "$d" 2>/dev/null && printf '%s/%s\n' "$(pwd -P)" "$b" ) && return 0
  fi
  printf '%s\n' "$p"
}

OUT_CANON=$(canonical "$OUT")

excluded() {  # excluded <path> -> 0 when this path IS the output manifest
  local p="$1"
  [ "$p" = "$OUT" ] && return 0
  if [ -e "$OUT" ] && [ -e "$p" ] && [ "$p" -ef "$OUT" ]; then
    return 0
  fi
  [ "$(canonical "$p")" = "$OUT_CANON" ] && return 0
  return 1
}

# --- temporary files --------------------------------------------------------
tmp=$(mktemp) || { echo "manifest-generate: cannot create temp file" >&2; exit 1; }
final=$(mktemp) || { echo "manifest-generate: cannot create temp file" >&2; rm -f "$tmp"; exit 1; }
list=$(mktemp) || { echo "manifest-generate: cannot create temp file" >&2; rm -f "$tmp" "$final"; exit 1; }
cleanup() { rm -f "$tmp" "$final" "$list"; }
trap cleanup EXIT

# --- collect entries --------------------------------------------------------
# A file reached by more than one route (for example named explicitly and also
# found by a directory scan) is recorded once, keyed by its canonical path.
declare -A SEEN=()

collect_hash() {  # collect_hash <file>
  local c
  c=$(canonical "$1")
  [ -n "${SEEN[$c]:-}" ] && return 0
  SEEN[$c]=1
  # `--` guards a name that begins with a dash
  if ! sha256sum -- "$1" >> "$tmp"; then
    echo "manifest-generate: failing to hash: $1" >&2
    rc=1
  fi
}

for p in "$@"; do
  # The output manifest is never an input, even when it is passed explicitly.
  # This is checked before the existence test, so naming the output explicitly
  # before it exists is skipped rather than reported as a missing path.
  excluded "$p" && continue
  if [ -d "$p" ]; then
    # Enumerate first, then hash from this shell (not a subshell), so a hashing
    # failure actually reaches the accumulated rc.  pipefail still makes a
    # failure anywhere in the find pipeline observable.
    if ! ( set -o pipefail; find "$p" -type f -print0 > "$list" ); then
      echo "manifest-generate: failing to enumerate directory contents: $p" >&2
      rc=1
    fi
    while IFS= read -r -d '' found; do
      excluded "$found" && continue
      # The fixed SHA256SUMS basename is additionally skipped, so an unrelated
      # stale manifest of that name is never silently folded in.
      case "$found" in */SHA256SUMS) continue ;; esac
      [ -f "$found" ] || continue
      collect_hash "$found"
    done < "$list"
  elif [ -f "$p" ]; then
    collect_hash "$p"
  else
    echo "manifest-generate: MISSING PATH: $p" >&2
    rc=1
  fi
done
[ -s "$tmp" ] || { echo "manifest-generate: no entries collected" >&2; rc=1; }

# --- sort and write ---------------------------------------------------------
if ! sort -k2 "$tmp" > "$final"; then
  echo "manifest-generate: failing to sort manifest" >&2
  rc=1
fi

if [ "$rc" != 0 ]; then
  rm -f "$OUT"
  echo "manifest-generate: FAILED, no manifest written: $OUT" >&2
  exit 1
fi

if ! cp "$final" "$OUT"; then
  echo "manifest-generate: failing to write manifest: $OUT" >&2
  rm -f "$OUT"
  exit 1
fi
[ -s "$OUT" ] || { echo "manifest-generate: empty manifest written: $OUT" >&2; rm -f "$OUT"; exit 1; }

exit 0
