#!/bin/sh
# P05-S4 R5-1: backfill the small result tables of R1-R4 into checkpoints/p05/registries/s4r1..s4r4.
# Run only through: sh testing/d003/safe_run.sh p05-s4r5 -- sh testing/d003/stage_s4/r5_backfill_registries.sh
# Originals are read only. Copies are verified by sha256 against originals; any mismatch aborts.
set -eu

REPO=$(git rev-parse --show-toplevel)
EV=$REPO/checkpoints/p05/evidence/p05-s4r5
mkdir -p "$EV/tmp"
export TMPDIR="$EV/tmp"

ER=$REPO/checkpoints/p05/evidence
RG=$REPO/checkpoints/p05/registries
MISS=$EV/R5_1_COPY_LOG.txt
MAXB=1048576

: > "$MISS"

# copy_one SRC_REL DEST_DIR DEST_NAME
copy_one() {
    src="$ER/$1"
    dd="$RG/$2"
    dn="$3"
    if ! ls -d "$src" >> "$MISS" 2>&1; then
        echo "MISSING	$2	$1	(original not found)" >> "$MISS"
        return 0
    fi
    sz=$(stat -c %s "$src")
    if [ "$sz" -gt "$MAXB" ]; then
        echo "SKIPPED_TOO_LARGE	$2	$1	size=$sz" >> "$MISS"
        return 0
    fi
    cp "$src" "$dd/$dn"
    a=$(sha256sum "$src" | cut -c1-64)
    b=$(sha256sum "$dd/$dn" | cut -c1-64)
    if [ "$a" != "$b" ]; then
        echo "SHA_MISMATCH	$2	$1	$a	$b" >> "$MISS"
        echo "sha mismatch: $1" >&2
        exit 1
    fi
    echo "COPIED	$2	$1	->	$dn	size=$sz	sha256=$a" >> "$MISS"
}

mkdir -p "$RG/s4r1" "$RG/s4r2" "$RG/s4r3" "$RG/s4r4"

# --- s4r1 (from evidence/p05-s4) ---
copy_one p05-s4/GATE.txt s4r1 GATE.txt
copy_one p05-s4/REGISTRY_S4_PRE.tsv s4r1 REGISTRY_S4_PRE.tsv
copy_one p05-s4/PRE_REGISTRY_ERRATA_1.txt s4r1 PRE_REGISTRY_ERRATA_1.txt
copy_one p05-s4/write_guard.log s4r1 write_guard.log

# --- s4r2 (from evidence/p05-s4r2) ---
copy_one p05-s4r2/ERRATA_2.txt s4r2 ERRATA_2.txt
copy_one p05-s4r2/TREES.tsv s4r2 TREES.tsv
copy_one p05-s4r2/REGISTRY_S4_PRE_R2_v2.tsv s4r2 REGISTRY_S4_PRE_R2_v2.tsv
copy_one p05-s4r2/REGISTRY_S4_PRE_R2_v2.sha256 s4r2 REGISTRY_S4_PRE_R2_v2.sha256
copy_one p05-s4r2/REGISTRY_S4_PRE_R2_DRAFT_INVALID.tsv s4r2 REGISTRY_S4_PRE_R2_DRAFT_INVALID.tsv
copy_one p05-s4r2/RESULTS_R2.tsv s4r2 RESULTS_R2.tsv
copy_one p05-s4r2/run3/raw_R2.tsv s4r2 raw_R2.tsv

# --- s4r3 (from evidence/p05-s4r3) ---
copy_one p05-s4r3/GATE_R3.txt s4r3 GATE_R3.txt
copy_one p05-s4r3/ERRATA_3.txt s4r3 ERRATA_3.txt
copy_one p05-s4r3/CALLSEQ.tsv s4r3 CALLSEQ.tsv
copy_one p05-s4r3/SITEMAP.tsv s4r3 SITEMAP.tsv
copy_one p05-s4r3/FIELDCALL_MAP.tsv s4r3 FIELDCALL_MAP.tsv
copy_one p05-s4r3/REGISTRY_S4_PRE_R3.tsv s4r3 REGISTRY_S4_PRE_R3.tsv
copy_one p05-s4r3/REGISTRY_S4_PRE_R3.sha256 s4r3 REGISTRY_S4_PRE_R3.sha256
copy_one p05-s4r3/RESULTS_R3.tsv s4r3 RESULTS_R3.tsv
copy_one p05-s4r3/COVERAGE_R3.tsv s4r3 COVERAGE_R3.tsv
copy_one p05-s4r3/RED_POINTS_R3.tsv s4r3 RED_POINTS_R3.tsv
copy_one p05-s4r3/OUTSCOPE_COUNT_R3.tsv s4r3 OUTSCOPE_COUNT_R3.tsv

# --- s4r4 (from evidence/p05-s4r4) ---
copy_one p05-s4r4/GATE_R4_pregate.txt s4r4 GATE_R4_pregate.txt
copy_one p05-s4r4/GATE_R4.txt s4r4 GATE_R4.txt
copy_one p05-s4r4/ERRATA_4.txt s4r4 ERRATA_4.txt
copy_one p05-s4r4/SEAMDIFF_R4.txt s4r4 SEAMDIFF_R4.txt
copy_one p05-s4r4/SEAMDIFF_R4.tsv s4r4 SEAMDIFF_R4.tsv
copy_one p05-s4r4/REGISTRY_S4_PRE_R4.tsv s4r4 REGISTRY_S4_PRE_R4.tsv
copy_one p05-s4r4/REGISTRY_S4_PRE_R4.sha256 s4r4 REGISTRY_S4_PRE_R4.sha256
copy_one p05-s4r4/REGISTRY_S4_PRE_R4_TIMESTAMP_UTC.txt s4r4 REGISTRY_S4_PRE_R4_TIMESTAMP_UTC.txt
copy_one p05-s4r4/REGISTRY_S4_PRE_R4_B.tsv s4r4 REGISTRY_S4_PRE_R4_B.tsv
copy_one p05-s4r4/REGISTRY_S4_PRE_R4_B.sha256 s4r4 REGISTRY_S4_PRE_R4_B.sha256
copy_one p05-s4r4/REGISTRY_S4_PRE_R4_B_TIMESTAMP_UTC.txt s4r4 REGISTRY_S4_PRE_R4_B_TIMESTAMP_UTC.txt
copy_one p05-s4r4/RESULTS_R4.tsv s4r4 RESULTS_R4.tsv
copy_one p05-s4r4/matrix_r4/CONTROL_R4.tsv s4r4 CONTROL_R4.tsv
copy_one p05-s4r4/plancall/RESULTS_R4_PLANCALL_pass1.tsv s4r4 RESULTS_R4_PLANCALL_pass1.tsv
copy_one p05-s4r4/plancall/RESULTS_R4_PLANCALL_pass2.tsv s4r4 RESULTS_R4_PLANCALL_pass2.tsv
copy_one p05-s4r4/regress/REGRESS_R4.tsv s4r4 REGRESS_R4.tsv
copy_one p05-s4r4/COVERAGE_R4_MERGED.tsv s4r4 COVERAGE_R4_MERGED.tsv
copy_one p05-s4r4/RED_POINTS_R4_MERGED.tsv s4r4 RED_POINTS_R4_MERGED.tsv
copy_one p05-s4r4/S4_MALLOC_STATIC_R4.txt s4r4 S4_MALLOC_STATIC_R4.txt
copy_one p05-s4r4/PLANINJ_DIFF_R4.txt s4r4 PLANINJ_DIFF_R4.txt
copy_one p05-s4r4/seam/LIBS_R4.tsv s4r4 LIBS_R4.tsv
copy_one p05-s4r4/drivers/DRIVERS.tsv s4r4 DRIVERS.tsv

# --- per-directory SHA256SUMS.txt over the copies (relative names) and original-vs-copy check ---
for r in s4r1 s4r2 s4r3 s4r4; do
    (
        cd "$RG/$r"
        : > SHA256SUMS.txt
        for f in $(ls | sort); do
            [ "$f" = "SHA256SUMS.txt" ] && continue
            sha256sum "$f" >> SHA256SUMS.txt
        done
    )
done

echo "R5-1 backfill done; log: $MISS"
