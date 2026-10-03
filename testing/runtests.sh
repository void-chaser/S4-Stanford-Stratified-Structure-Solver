#!/bin/sh

S4_BIN="${S4_BIN:-../build/S4}"
TMPFILE='tmpfile'
EX_DIR="${TEST_EXAMPLES_DIR:-../examples}"
DIFF="${DIFF_TOOL:-./numdiff}"

MANIFEST="${TEST_MANIFEST:-testcases.txt}"

trap 'rm -f "$TMPFILE".*' EXIT INT TERM

if [ ! -x "$S4_BIN" ]; then
    echo "Error: Executable $S4_BIN not found or not executable."
    exit 1
fi
if [ ! -x "$DIFF" ]; then
    echo "Error: Diff tool $DIFF not found or not executable."
    exit 1
fi
if [ ! -f "$MANIFEST" ]; then
    echo "Error: Manifest $MANIFEST not found."
    exit 1
fi

WHICH=1
FAIL=0
CASES=0

while read -r luafile resultfile tol extra; do
    # Skip empty lines and comments
    [ -z "$luafile" ] && continue
    case "$luafile" in
        \#*) continue ;;
    esac

    if [ -z "$luafile" ] || [ -z "$resultfile" ] || [ -z "$tol" ] || [ -n "$extra" ]; then
        echo "Error: Invalid manifest line: '$luafile $resultfile $tol $extra' (must have exactly three non-empty fields)."
        FAIL=1
        continue
    fi
    CASES=$((CASES + 1))

    echo "Running $luafile"
    if [ ! -f "$EX_DIR/$luafile" ]; then
        echo "Error: Lua script $EX_DIR/$luafile not found."
        FAIL=1
        continue
    fi
    if [ ! -f "$EX_DIR/$resultfile" ]; then
        echo "Error: Baseline file $EX_DIR/$resultfile not found."
        FAIL=1
        continue
    fi

    "$S4_BIN" "$EX_DIR/$luafile" > "$TMPFILE.$WHICH" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "Error: Execution failed for $luafile"
        FAIL=1
        rm -f "$TMPFILE.$WHICH"
    else
        "$DIFF" "$EX_DIR/$resultfile" "$TMPFILE.$WHICH" "$tol"
        if [ $? -eq 0 ]; then
            rm -f "$TMPFILE.$WHICH"
        else
            echo "Error: Comparison failed for $luafile"
            FAIL=1
            rm -f "$TMPFILE.$WHICH"
        fi
    fi
    WHICH=$((WHICH + 1))
done < "$MANIFEST"

if [ "$CASES" -eq 0 ]; then
    echo "Error: No test cases found in $MANIFEST"
    exit 1
fi

if [ "$FAIL" -ne 0 ]; then
    echo "Lua regression tests FAILED."
    exit 1
fi
echo "Lua regression tests PASSED."
exit 0
