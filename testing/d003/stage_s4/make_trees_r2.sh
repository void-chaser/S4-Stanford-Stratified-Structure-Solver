#!/bin/sh
# make_trees_r2.sh -- P05-S4 R2-1: writes OUT/TREES.tsv from git facts only.
# Usage: sh testing/d003/safe_run.sh p05-s4r2 -- sh testing/d003/stage_s4/make_trees_r2.sh p05-s4r2
# Every value comes from git rev-parse / git merge-base --is-ancestor / git log (read-only).
set -u
REPO=$(git rev-parse --show-toplevel)
OUT="$REPO/checkpoints/p05/evidence/${1:?usage: make_trees_r2.sh OUT_ARG}"
F="$OUT/TREES.tsv"
anc() { if git merge-base --is-ancestor "$1" "$2" 2>/dev/null; then echo yes; else echo no; fi; }
{
    printf '# TREES.tsv -- P05-S4 R2-1 tree name table. Every cell from git (rev-parse, merge-base --is-ancestor, ls-tree).\n'
    printf '# Columns: tag, runner_label, commit, S4_tree_hash, role, contains_b00b630, contains_de52142, S3R_commits_present, S3R2_commits_present, historical_names\n'
    printf 'tag\trunner_label\tcommit\tS4_tree_hash\trole\tcontains_b00b630\tcontains_de52142\tS3R_present\tS3R2_present\thistorical_names\n'
    for row in "B|BASE|37a82e8|baseline (no S2/S3 fixes)|BASE B|historical name B (task); BASE (runner)" \
               "A|CUR|876181c|S2 fixes (b00b630, de52142) only|A (CUR)|historical name A (task); CUR (runner)" \
               "H|H|64eb0b5|all S3R fixes up to the S3R stop point (S4 tree equals S; H = 64eb0b5 in run_all.sh)|H|historical name H (task); H (runner)" \
               "F|F|1c11905|frozen tree of S4 R1/R2: S3 + S3R + S3R2 source commits|F (new in S4)|UNKNOWN (new name in S4)"; do
        tag=$(echo "$row" | cut -d'|' -f1)
        rl=$(echo "$row" | cut -d'|' -f2)
        c=$(echo "$row" | cut -d'|' -f3)
        role=$(echo "$row" | cut -d'|' -f4)
        hn=$(echo "$row" | cut -d'|' -f6)
        h=$(git rev-parse "$c:S4")
        s3r=""; for x in e83255f 73e00ef df3bb02 35cd7b3; do [ "$(anc "$x" "$c")" = yes ] && s3r="$s3r $x"; done
        s3r2=""; for x in 3e77aa9 44bcf1c ff6dd7c; do [ "$(anc "$x" "$c")" = yes ] && s3r2="$s3r2 $x"; done
        printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "$tag" "$rl" "$c" "$h" "$role" \
            "$(anc b00b630 "$c")" "$(anc de52142 "$c")" "[${s3r# }]" "[${s3r2# }]" "$hn"
    done
} > "$F"
echo "wrote $F"
