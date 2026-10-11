#!/bin/sh
# D003 unified entry point (P05-S2R6, R6-2).
#
#   sh testing/d003/run_all.sh --out DIR [--trees B,A,H] [--stage LIST]
#
#   --out DIR     output directory: a relative subdirectory of checkpoints/p05/evidence/
#                 (for example p05-s2r6/repro-1).  Every write goes through
#                 testing/d003/safe_run.sh, which refuses any path outside the repository.
#   --trees LIST  tree labels, default B,A,H.
#                   B = 37a82e8  historical BASE  (runner label BASE)
#                   A = 876181c  historical CUR   (runner label CUR)
#                   H = 64eb0b5  reference tree   (runner label H)
#                 H's testing/ is the committed testing/ of HEAD; its S4/ comes from 64eb0b5.
#   --stage LIST  default all, in this canonical order:
#                   export build seam drivers matrix judge report
#
# Idempotency: a stage with a DONE line for the same tree list in OUT/STAGES.txt is skipped
# and reported on stderr.  A failing stage stops the run with exit 1 and a reason, on stderr and
# in OUT/STAGES.txt.  Nothing is skipped silently.
#
# Exit status: 0 = every requested stage completed; 1 = a stage failed; 2 = usage, or a refusal
# by safe_run.sh.
#
# What this script does not do:
#   * it never edits judge_d003.py, matrix_r2.py, matrix_d003.py or any existing seam script; it
#     only calls them;
#   * it never writes into S4/ (each tree is a git-archive copy, and seams are applied to copies);
#   * it never writes /tmp (TMPDIR is set to OUT/tmp through safe_run.sh).
#
# Build options: the repository defaults of Makefile.Linux
# (-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC).  The CPU model and compiler
# are recorded in OUT/BUILD_OPTIONS.txt.
#
# Library families (macro sets verified against the frozen S2R2-S2R5 builds; see README.md):
#   plain    (none)                                         trees B, A, H
#   seamAB   ALLOC_SEAM KOTTKE_SEAM LINEARSOLVE_SEAM LINEARSOLVE_SEAM_NULLINFO   trees B, A (families A,B,C,D)
#   seamH    ALLOC_SEAM KOTTKE_SEAM LINEARSOLVE_SEAM LINEARSOLVE_SEAM_NULLINFO2  tree H (B2, then A,C,D)
#   fmmbuf   FMMBUF_SEAM                                    tree B (family E, observe only)
#   fmmpert  FMMPERT_SEAM                                   tree B (family E, identity perturbation)
#   fmmret   FMMRET_SEAM                                    trees A, H (family E, status)
#   addf     ADDFIELD_SEAM                                  tree H (family F)
#   b2buf    LINEARSOLVE_SEAM_NULLINFO2BUF                  tree H (output-only B2)
#
# Each library is built on its own copy, so a seam never leaks into another library.

set -u

REPO=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "run_all: not inside a git work tree" >&2; exit 2; }
H="$REPO/testing/d003"
SAFE="$H/safe_run.sh"
PY=${PYTHON:-python3}
JOBS=${JOBS:-$(nproc)}
CANON_STAGES="export build seam drivers matrix judge report"
COMMIT_B=37a82e8
COMMIT_A=876181c
COMMIT_H=64eb0b5
LIBFLAGS="-llapack -lblas -Wl,--wrap=malloc -Wl,--wrap=_Z13fft_plan_execP12tag_fft_plan -Wl,--wrap=_Z15fft_plan_dft_2dPiPSt7complexIdES2_i -Wl,--wrap=_Z9S4_mallocm"

usage() {
    echo "usage: sh testing/d003/run_all.sh --out DIR [--trees B,A,H] [--stage LIST]" >&2
    echo "  stages (default all, canonical order): $CANON_STAGES" >&2
}

OUT_ARG=""
TREES="B,A,H"
STAGES=""
while [ "$#" -gt 0 ]; do
    case "$1" in
        --out) [ "$#" -ge 2 ] || { usage; exit 2; }; OUT_ARG=$2; shift 2;;
        --trees) [ "$#" -ge 2 ] || { usage; exit 2; }; TREES=$2; shift 2;;
        --stage) [ "$#" -ge 2 ] || { usage; exit 2; }; STAGES=$2; shift 2;;
        -h|--help) usage; exit 0;;
        *) echo "run_all: unknown argument: $1" >&2; usage; exit 2;;
    esac
done
[ -n "$OUT_ARG" ] || { echo "run_all: --out is required" >&2; usage; exit 2; }
case "$OUT_ARG" in
    /*) echo "run_all: --out must be a relative subdirectory of checkpoints/p05/evidence" >&2; exit 2;;
esac
[ -n "$STAGES" ] || STAGES=$(echo "$CANON_STAGES" | tr ' ' ',')
for t in $(echo "$TREES" | tr ',' ' '); do
    case "$t" in B|A|H) ;; *) echo "run_all: unknown tree label: $t (allowed: B,A,H)" >&2; exit 2;; esac
done
for s in $(echo "$STAGES" | tr ',' ' '); do
    case " $CANON_STAGES " in *" $s "*) ;; *) echo "run_all: unknown stage: $s" >&2; exit 2;; esac
done

OUT="$REPO/checkpoints/p05/evidence/$OUT_ARG"

# Every command that writes goes through safe_run.sh.  safe_run.sh validates OUT_ARG and exits 2
# before running the command when OUT_ARG resolves outside the repository.
run_safe() {
    sh "$SAFE" "$OUT_ARG" -- "$@"
}

run_safe sh -c 'mkdir -p "$EV/tmp" && touch "$EV/STAGES.txt"' || { echo "run_all: cannot prepare $OUT (refused or failed)" >&2; exit 2; }
STAGEFILE="$OUT/STAGES.txt"

# record STAGE STATUS REASON: appends one line; never rewrites.
record() {
    run_safe sh -c 'printf "%s\t%s\t%s\t%s\n" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$1" "$2" "$3" >> "$EV/STAGES.txt"' sh "$1" "$2" "$3" \
        || echo "run_all: warning: could not record $1 $2" >&2
}

# stage_done NAME: a DONE line for NAME with this exact tree list exists.
stage_done() {
    awk -F'\t' -v s="$1" -v t="$TREES" '$2==s && $3=="DONE" && $4=="trees="t {found=1} END{exit !found}' "$STAGEFILE" 2>/dev/null
}

fail() {
    echo "run_all: STAGE $1 FAILED: $2" >&2
    record "$1" FAILED "$2"
    exit 1
}

tree_commit() {
    case "$1" in B) echo $COMMIT_B;; A) echo $COMMIT_A;; H) echo $COMMIT_H;; esac
}

# build_lib TREE SRC_DIR BUILD_NAME MACROS
# Builds $SRC_DIR/build/libS4.a from the exported tree with the repository default options.
# MACROS is a list of "-D..." flags (empty for the plain library).
build_lib() {
    _t=$1; _src=$2; _name=$3; _macros=$4
    run_safe sh -c 'cd "$1" && make objdir > "$2/build-$3.log" 2>&1 && make -j"$4" CPPFLAGS="$5 -IS4 -IS4/RNP -IS4/kiss_fft" build/libS4.a >> "$2/build-$3.log" 2>&1' \
        sh "$_src" "$OUT" "$_name" "$JOBS" "$_macros" \
        || return 1
    [ -f "$_src/build/libS4.a" ] || return 1
    run_safe sh -c 'sha256sum "$1/build/libS4.a" > "$2/libS4-$3.sha256"' sh "$_src" "$OUT" "$_name" || return 1
    return 0
}

# export_tree LABEL COMMIT: git archive of COMMIT into OUT/trees/LABEL.  H gets HEAD's testing/.
export_tree() {
    _lbl=$1; _c=$2; _d="$OUT/trees/$_lbl"
    run_safe sh -c 'rm -rf "$1" && mkdir -p "$1" && git -C "$2" archive "$3" | tar -x -C "$1"' sh "$_d" "$REPO" "$_c" || return 1
    if [ "$_lbl" = "H" ]; then
        run_safe sh -c 'rm -rf "$1/testing" && mkdir -p "$1/testing" && git -C "$2" archive HEAD testing | tar -x -C "$1"' sh "$_d" "$REPO" || return 1
    fi
    [ -d "$_d/S4" ] || return 1
    return 0
}

# ---------------------------------------------------------------------------
# stage export: git archive per tree (H = 64eb0b5 S4/ and build files, with HEAD's testing/).
# ---------------------------------------------------------------------------
stage_export() {
    for t in $(echo "$TREES" | tr ',' ' '); do
        export_tree "$t" "$(tree_commit "$t")" || fail export "export of tree $t ($(tree_commit "$t")) failed"
        n=$(find "$OUT/trees/$t" -type f | wc -l)
        [ "$n" -gt 0 ] || fail export "tree $t exported zero files"
    done
    record export DONE "trees=$TREES"
}

# ---------------------------------------------------------------------------
# stage build: plain library for each requested tree (default options).
# ---------------------------------------------------------------------------
stage_build() {
    for t in $(echo "$TREES" | tr ',' ' '); do
        build_lib "$t" "$OUT/trees/$t" "plain-$t" "" || fail build "plain library build failed for tree $t (see $OUT/build-plain-$t.log)"
    done
    flags="-O3 -Wall -march=native -fcx-limited-range -fno-exceptions -fPIC"
    cpu=$(grep -m1 'model name' /proc/cpuinfo 2>/dev/null | sed 's/^[^:]*: *//')
    run_safe sh -c 'printf "flags=%s\ncpu=%s\ncompiler=%s\n" "$1" "$2" "$(g++ --version | head -1)" > "$3/BUILD_OPTIONS.txt"' sh "$flags" "$cpu" "$OUT" \
        || fail build "could not write BUILD_OPTIONS.txt"
    record build DONE "trees=$TREES"
}

# ---------------------------------------------------------------------------
# stage seam: family libraries.  Each is built from a FRESH export of its commit (never reusing the
# plain tree), with the family seam applied by the existing apply scripts.  Check-only runs first.
# ---------------------------------------------------------------------------
stage_seam() {
    for t in $(echo "$TREES" | tr ',' ' '); do
        c=$(tree_commit "$t")
        case "$t" in
            B|A)
                # families A,B,C,D (apply_seam_r2.py), macros as in the frozen seam-AB builds
                sd="$OUT/seam/$t-AB"
                run_safe sh -c 'rm -rf "$1" && mkdir -p "$1" && git -C "$2" archive "$3" | tar -x -C "$1"' sh "$sd" "$REPO" "$c" \
                    || fail seam "export for seam $t-AB failed"
                run_safe sh -c '"$5" -I -B "$1/testing/d003/seam/apply_seam_r2.py" --root "$2" --repo "$1" --families A,B,C,D --check-only --report "$4/seam-check-$3.txt" >/dev/null' \
                    sh "$REPO" "$sd" "$t-AB" "$OUT" "$PY" || fail seam "check-only A,B,C,D failed for $t"
                run_safe sh -c '"$5" -I -B "$1/testing/d003/seam/apply_seam_r2.py" --root "$2" --repo "$1" --families A,B,C,D --report "$4/seam-apply-$3.txt" >/dev/null' \
                    sh "$REPO" "$sd" "$t-AB" "$OUT" "$PY" || fail seam "write A,B,C,D failed for $t"
                build_lib "$t" "$sd" "seamAB-$t" "-DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM" \
                    || fail seam "seamAB library build failed for $t"
                ;;
            H)
                sd="$OUT/seam/H-B2"
                run_safe sh -c 'rm -rf "$1" && mkdir -p "$1" && git -C "$2" archive "$3" | tar -x -C "$1"' sh "$sd" "$REPO" "$c" \
                    || fail seam "export for seam H failed"
                run_safe sh -c '"$5" -I -B "$1/testing/d003/seam/apply_seam_b2.py" --root "$2" --repo "$1" --check-only --report "$4/seam-check-B2-H.txt" >/dev/null' \
                    sh "$REPO" "$sd" "" "$OUT" "$PY" || fail seam "check-only B2 failed for H"
                run_safe sh -c '"$5" -I -B "$1/testing/d003/seam/apply_seam_b2.py" --root "$2" --repo "$1" --report "$4/seam-apply-B2-H.txt" >/dev/null' \
                    sh "$REPO" "$sd" "" "$OUT" "$PY" || fail seam "write B2 failed for H"
                run_safe sh -c '"$5" -I -B "$1/testing/d003/seam/apply_seam_r2.py" --root "$2" --repo "$1" --families A,C,D --check-only --report "$4/seam-check-ACD-H.txt" >/dev/null' \
                    sh "$REPO" "$sd" "" "$OUT" "$PY" || fail seam "check-only A,C,D failed for H"
                run_safe sh -c '"$5" -I -B "$1/testing/d003/seam/apply_seam_r2.py" --root "$2" --repo "$1" --families A,C,D --report "$4/seam-apply-ACD-H.txt" >/dev/null' \
                    sh "$REPO" "$sd" "" "$OUT" "$PY" || fail seam "write A,C,D failed for H"
                build_lib H "$sd" "seamH" "-DS4_TEST_LINEARSOLVE_SEAM -DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2 -DS4_TEST_ALLOC_SEAM -DS4_TEST_KOTTKE_SEAM" \
                    || fail seam "seamH library build failed"
                ;;
        esac
    done
    # family E / F / B2buf: single-macro libraries.  Each one is a fresh export of its commit with
    # one apply script (the existing script for that family).  Built only when requested.
    for t in $(echo "$TREES" | tr ',' ' '); do
        case "$t" in
            B)
                single_family fmmbuf B "$(tree_commit B)" "-DS4_TEST_FMMBUF_SEAM" \
                    "apply_seam_r5_fmmret.py" "--tree B" ;;
            A)
                single_family fmmret A "$(tree_commit A)" "-DS4_TEST_FMMRET_SEAM" \
                    "apply_seam_r5_fmmret.py" "--tree A" ;;
            H)
                single_family fmmret H "$(tree_commit H)" "-DS4_TEST_FMMRET_SEAM" \
                    "apply_seam_r5_fmmret.py" "--tree H" ;;
        esac
    done
    # the B-only perturbation (fmmpert) and the H-only F and output-only B2 libraries
    for t in $(echo "$TREES" | tr ',' ' '); do
        case "$t" in
            B)
                single_family fmmpert B "$(tree_commit B)" "-DS4_TEST_FMMPERT_SEAM" \
                    "apply_seam_r5_fmmret.py" "--tree BPERT" ;;
            H)
                single_family addf H "$(tree_commit H)" "-DS4_TEST_ADDFIELD_SEAM" \
                    "apply_seam_r5_addfield.py" ""
                single_family b2buf H "$(tree_commit H)" "-DS4_TEST_LINEARSOLVE_SEAM_NULLINFO2BUF" \
                    "apply_seam_r4_buf.py" "" ;;
        esac
    done
    record seam DONE "trees=$TREES"
}

# single_family FAMILY TREE COMMIT MACRO SCRIPT EXTRA_ARGS
# One fresh export of COMMIT, one existing apply script (EXTRA_ARGS may be empty), then the
# library with MACRO.  The apply script refuses any root inside S4/ (it is given the copy).
single_family() {
    _fam=$1; _t=$2; _c=$3; _macro=$4; _script=$5; _extra=$6
    _sd="$OUT/seam/$_t-$_fam"
    run_safe sh -c 'rm -rf "$1" && mkdir -p "$1" && git -C "$2" archive "$3" | tar -x -C "$1"' sh "$_sd" "$REPO" "$_c" \
        || fail seam "export for $_fam on $_t failed"
    if [ -n "$_extra" ]; then
        run_safe sh -c 'cd "$1" && "$2" -I -B "$3/testing/d003/seam/$4" $5 --root "$6" --repo "$3" --report "$7/seam-apply-$8.txt" >/dev/null' \
            sh "$_sd" "$PY" "$REPO" "$_script" "$_extra" "$_sd" "$OUT" "$_fam-$_t" \
            || fail seam "apply of $_fam on $_t failed"
    else
        run_safe sh -c 'cd "$1" && "$2" -I -B "$3/testing/d003/seam/$4" --root "$5" --repo "$3" --report "$6/seam-apply-$7.txt" >/dev/null' \
            sh "$_sd" "$PY" "$REPO" "$_script" "$_sd" "$OUT" "$_fam-$_t" \
            || fail seam "apply of $_fam on $_t failed"
    fi
    build_lib "$_t" "$_sd" "$_fam-$_t" "$_macro" || fail seam "$_fam library build failed for $_t"
}

# ---------------------------------------------------------------------------
# stage drivers: one driver per library, linked from the committed driver sources with the
# committed link flags.  The sha256 of each driver is written to OUT/drivers/DRIVERS.tsv and is
# the pin the matrix stage passes to matrix_r2.py (--driver-sha256).
# ---------------------------------------------------------------------------
# driver_for LIB_NAME LIB_DIR : link $H/src/driver_d003.cpp + inject against LIB_DIR/build/libS4.a
driver_for() {
    _name=$1; _ldir=$2
    _bin="$OUT/drivers/$_name/driver-d003"
    [ -f "$_ldir/build/libS4.a" ] || return 1
    run_safe sh -c 'mkdir -p "$1" && g++ -O1 -Wall -Wextra -Wno-unused-parameter -I "$2/S4" -I "$2/S4/fmm" "$3/src/driver_d003.cpp" "$3/src/inject_d003.cpp" -o "$4" -L "$2/build" -lS4 '"$LIBFLAGS" \
        sh "$OUT/drivers/$_name" "$_ldir" "$H" "$_bin" || return 1
    [ -x "$_bin" ] || return 1
    _sha=$(sha256sum "$_bin" | cut -d' ' -f1)
    run_safe sh -c 'printf "%s\t%s\t%s\n" "$1" "$2" "$3" >> "$4/drivers/DRIVERS.tsv"' sh "$_name" "$_sha" "$_bin" "$OUT" || return 1
    return 0
}

stage_drivers() {
    run_safe sh -c 'mkdir -p "$1/drivers" && : > "$1/drivers/DRIVERS.tsv"' sh "$OUT" || fail drivers "could not create drivers directory"
    for t in $(echo "$TREES" | tr ',' ' '); do
        case "$t" in
            B)
                driver_for plain-B "$OUT/trees/B" || fail drivers "plain-B driver failed"
                driver_for AB-B "$OUT/seam/B-AB" || fail drivers "AB-B driver failed"
                driver_for fmmbuf-B "$OUT/seam/B-fmmbuf" || fail drivers "fmmbuf-B driver failed"
                driver_for fmmpert-B "$OUT/seam/B-fmmpert" || fail drivers "fmmpert-B driver failed" ;;
            A)
                driver_for plain-A "$OUT/trees/A" || fail drivers "plain-A driver failed"
                driver_for AB-A "$OUT/seam/A-AB" || fail drivers "AB-A driver failed"
                driver_for fmmret-A "$OUT/seam/A-fmmret" || fail drivers "fmmret-A driver failed" ;;
            H)
                driver_for plain-H "$OUT/trees/H" || fail drivers "plain-H driver failed"
                driver_for H-B2 "$OUT/seam/H-B2" || fail drivers "H-B2 driver failed"
                driver_for fmmret-H "$OUT/seam/H-fmmret" || fail drivers "fmmret-H driver failed"
                driver_for addf-H "$OUT/seam/H-addf" || fail drivers "addf-H driver failed"
                driver_for b2buf-H "$OUT/seam/H-b2buf" || fail drivers "b2buf-H driver failed" ;;
        esac
    done
    record drivers DONE "trees=$TREES"
}

# ---------------------------------------------------------------------------
# stage matrix: run each frozen registry through matrix_r2.py, two passes per (registry, tree).
#
# matrix_r2.py filters rows by tree only, not by family.  A tree can therefore mix families that
# need different libraries (for example H linearsolve_null2 and H linearsolve_null2buf).  This stage
# writes one FAMILY-FILTERED COPY of each registry per (tree, build) into OUT/matrix/inputs/ and runs
# each copy against the driver of that build.  The frozen registries are never edited; every copy
# records its source sha256 and its own sha256 in OUT/matrix/inputs/INPUTS.tsv.
#
#   build selection (tree, family prefix) -> driver name in OUT/drivers/DRIVERS.tsv
#     B: alloc, linearsolve_null, s4malloc -> AB-B ;  fmmbuf -> fmmbuf-B ;  fmmpert -> fmmpert-B
#     A: alloc, linearsolve_null, s4malloc -> AB-A ;  fmmret -> fmmret-A
#     H: alloc, linearsolve_null2, s4malloc -> H-B2 ;  fmmret -> fmmret-H ;  addf -> addf-H ;
#        linearsolve_null2buf -> b2buf-H
#   A row whose (tree, family) is not in this table makes the stage fail (nothing is skipped).
# ---------------------------------------------------------------------------
REG_DIR="$REPO/checkpoints/p05/registries"

# the registries that are runner inputs (10-field format), with their frozen paths
MATRIX_REGS="s2r3/stage3/REG_3B_THREECOLUMN.tsv s2r3/stage3/REG_3C2_FFTCHAIN.tsv s2r3/stage3/REG_3C3_CLOSED.tsv s2r3/stage3/REG_3C1_EXPERIMENTAL.tsv s2r4/r4-1/REG_R4_1_POSTHOC.tsv s2r5/r5-1/REG_R5_1_FMMRET.tsv s2r5/r5-1/REG_R5_1_BPERT.tsv s2r5/r5-2/REG_R5_2_ADDFIELD.tsv s2r5/r5-2/REG_R5_2_ADDFIELD_FFT.tsv"

# build_for TREE FAMILY -> prints driver name, or nothing (unknown pair)
build_for() {
    case "$1:$2" in
        B:alloc|B:linearsolve_null|B:s4malloc) echo AB-B;;
        B:fmmbuf) echo fmmbuf-B;;
        B:fmmpert) echo fmmpert-B;;
        A:alloc|A:linearsolve_null|A:s4malloc) echo AB-A;;
        A:fmmret) echo fmmret-A;;
        H:alloc|H:linearsolve_null2|H:s4malloc) echo H-B2;;
        H:fmmret) echo fmmret-H;;
        H:addf) echo addf-H;;
        H:linearsolve_null2buf) echo b2buf-H;;
        *) echo "";;
    esac
}

# the runner tree label for a tree label
runner_tree() {
    case "$1" in B) echo BASE;; A) echo CUR;; H) echo H;; esac
}

# driver_sha NAME -> sha256 pinned in DRIVERS.tsv
driver_sha() {
    awk -F'\t' -v n="$1" '$1==n {print $2; exit}' "$OUT/drivers/DRIVERS.tsv"
}

driver_path() {
    awk -F'\t' -v n="$1" '$1==n {print $3; exit}' "$OUT/drivers/DRIVERS.tsv"
}

stage_matrix() {
    [ -s "$OUT/drivers/DRIVERS.tsv" ] || fail matrix "no drivers (run stage drivers first)"
    run_safe sh -c 'mkdir -p "$1/matrix/inputs" "$1/matrix/runs" && : > "$1/matrix/inputs/INPUTS.tsv" && : > "$1/matrix/RUNS.tsv"' sh "$OUT" \
        || fail matrix "could not create the matrix directories"
    for t in $(echo "$TREES" | tr ',' ' '); do
        rt=$(runner_tree "$t")
        for reg in $MATRIX_REGS; do
            src="$REG_DIR/$reg"
            base=$(basename "$reg" .tsv)
            # families present for this tree in this registry (rows with 10 fields and this tree)
            fams=$(awk -F'\t' -v t="$rt" 'NF==10 && $3==t { r=$4; if (r=="-"||r=="") next; split(r,a,":"); print a[1] }' "$src" | sort -u)
            [ -n "$fams" ] || continue
            for fam in $fams; do
                bn=$(build_for "$t" "$fam")
                [ -n "$bn" ] || fail matrix "no build for tree $t family $fam (registry $reg); refusing to guess"
                dsha=$(driver_sha "$bn")
                dpath=$(driver_path "$bn")
                [ -n "$dsha" ] && [ -x "$dpath" ] || fail matrix "driver $bn missing for tree $t family $fam"
                tag="$base--$t--$fam"
                copy="$OUT/matrix/inputs/$tag.tsv"
                # filtered copy: header lines kept, rows of this tree and this family only
                run_safe sh -c 'awk -F"\t" -v t="$2" -v f="$3" '"'"'/^#/{print; next} NF==10 && $3==t { r=$4; split(r,a,":"); if (a[1]==f || (f=="s4malloc" && r ~ /^s4malloc/)) print }'"'"' "$1" > "$4"' \
                    sh "$src" "$rt" "$fam" "$copy" || fail matrix "could not write filtered copy $tag"
                nrows=$(grep -v '^#' "$copy" | grep -c .)
                [ "$nrows" -gt 0 ] || fail matrix "no rows for tree $t family $fam in $reg"
                srcsha=$(sha256sum "$src" | cut -d' ' -f1)
                copysha=$(sha256sum "$copy" | cut -d' ' -f1)
                run_safe sh -c 'printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\n" "$1" "$2" "$3" "$4" "$5" "$6" "$7" >> "$8/matrix/inputs/INPUTS.tsv"' \
                    sh "$reg" "$t" "$fam" "$bn" "$srcsha" "$copysha" "$nrows" "$OUT" || fail matrix "could not record input $tag"
                # two passes per (registry, tree, family), each into its own run directory
                for pass in 1 2; do
                    rd="$OUT/matrix/runs/$tag/pass$pass"
                    run_safe sh -c '"$1" -I -B "$2/testing/d003/matrix_r2.py" run --registry "$3" --driver "$4" --driver-sha256 "$5" --tree "$6" --runs "$7/runs" --out "$7"' \
                        sh "$PY" "$REPO" "$copy" "$dpath" "$dsha" "$rt" "$rd" \
                        > "$OUT/matrix/runs/$tag.pass$pass.stdout" 2>&1
                    rc=$?
                    printf '%s\tpass%s\trc=%s\n' "$tag" "$pass" "$rc" >> "$OUT/matrix/RUNS.tsv"
                    [ "$rc" -eq 0 ] || fail matrix "matrix run failed for $tag pass $pass (rc $rc; see $OUT/matrix/runs/$tag.pass$pass.stdout)"
                done
            done
        done
    done
    record matrix DONE "trees=$TREES"
}

# ---------------------------------------------------------------------------
# stage judge: summarize_r6.py compares the fresh matrix with the registries (their expectation
# column) and replays the frozen historical indexes.  Every row gets a derived status:
#   MATCHED, STRUCTURAL_DECLARED (the NO set equals the declared S2 set exactly), or UNDECLARED.
# UNDECLARED rows make this stage fail (exit 1): an unexplained difference is never passed.
# ---------------------------------------------------------------------------
stage_judge() {
    run_safe sh -c '"$1" -I -B "$2/testing/d003/summarize_r6.py" --out "$3" --repo "$2" > "$3/judge.stdout" 2>&1' \
        sh "$PY" "$REPO" "$OUT"
    jrc=$?
    if [ "$jrc" -ne 0 ]; then
        fail judge "summary exited with status $jrc (see $OUT/judge.stdout; 3 = UNDECLARED rows present)"
    fi
    record judge DONE "trees=$TREES"
}

# ---------------------------------------------------------------------------
# stage report: writes the machine-readable TSV and the human summary (both written by the judge)
# and a manifest of the output files with their sha256.  It fails if they are missing.
# ---------------------------------------------------------------------------
stage_report() {
    [ -s "$OUT/report/summary.tsv" ] || fail report "summary.tsv missing (run stage judge first)"
    [ -s "$OUT/report/SUMMARY.txt" ] || fail report "SUMMARY.txt missing (run stage judge first)"
    run_safe sh -c 'cd "$1" && find report trees drivers matrix seam -type f 2>/dev/null | LC_ALL=C sort | xargs sha256sum > "$1/report/SHA256SUMS.txt"' \
        sh "$OUT" || fail report "could not write report/SHA256SUMS.txt"
    record report DONE "trees=$TREES"
}

for s in $(echo "$STAGES" | tr ',' ' '); do
    if stage_done "$s"; then
        echo "run_all: stage $s already DONE for trees=$TREES, skipped (idempotent)" >&2
        continue
    fi
    "stage_$s"
done
exit 0
