#!/bin/sh
# gate_v0.sh -- P05-S4 V0 gate record.  Writes $EV/GATE.txt only.  Read-only checks otherwise.
set -u
REPO=$(git rev-parse --show-toplevel)
EV="$REPO/checkpoints/p05/evidence/p05-s4"
TMPDIR="$EV/tmp"
export TMPDIR
{
    echo "P05-S4 V0 gate record"
    echo "generated_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo "repo=$REPO"
    echo "branch=$(git branch --show-current)"
    echo "head_at_start=$(git rev-parse HEAD)"
    echo "head_short=$(git rev-parse --short HEAD)"
    echo "expected_head=1c11905"
    echo "S4_tree_at_HEAD=$(git rev-parse HEAD:S4)"
    echo "S4_tree_expected_at_baseline=1d738e64f9864a475fdb3de34cd3601605df2c64"
    echo "S4_tree_37a82e8=$(git rev-parse 37a82e8:S4)"
    echo "S4_tree_5b72793=$(git rev-parse 5b72793:S4)"
    echo "judge_d003_sha256=$(sha256sum "$REPO/testing/d003/judge_d003.py" | cut -d' ' -f1)"
    echo "judge_expected_sha256=d2d04145e056163895ee917f13f90b68ffac226d3c620913407b0c51756209eb"
    echo "tmp_top_level_sha256_at_start=$(ls -A /tmp | sha256sum | cut -d' ' -f1)"
    echo "tmp_top_level_entries_at_start=$(ls -A /tmp | wc -l)"
    echo "--- git status --short (must be empty at start) ---"
    git status --short
    echo "--- git status --short line count ---"
    git status --short | wc -l
    echo "--- stash list ---"
    git stash list | wc -l
    echo "--- toolchain ---"
    g++ --version | head -1
    gcc --version | head -1
    echo "gdb: $(gdb --version | head -1)"
    echo "python3: $(python3 --version 2>&1)"
    echo "nproc=$(nproc)"
} > "$EV/GATE.txt"
echo "wrote $EV/GATE.txt"
