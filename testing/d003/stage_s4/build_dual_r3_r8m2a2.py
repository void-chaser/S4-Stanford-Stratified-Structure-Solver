# build_dual_r3_r8m2a2.py -- P05-S4 R8 M2a2 (R3 dual-target injector, U244 rule set R3).
# Builds testing/d003/stage_s4/inject_r8m2a2_dual_R3.cpp from inject_r8m2a2_dual_R2.cpp by LINE-RANGE SPLICING.
# Target 1 code (every line outside the replaced ranges) is carried over unchanged; the checker below
# proves that every removed R2 line lies inside an allowed range.  The R2 file is only read.
# Writes SRC_DIFF_R8_M2a2_inject_dual_R3.txt (R2 -> R3) and SRC_DIFF_R8_M2a2_inject_dual_R3_base.txt (base -> R3).
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2a2 -- python3 -I -B testing/d003/stage_s4/build_dual_r3_r8m2a2.py p05-s4r8/m2a2
import difflib
import os
import sys

EVREL = sys.argv[1] if len(sys.argv) > 1 else "p05-s4r8/m2a2"
REPO = os.path.realpath(os.getcwd())
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", EVREL)
STAGE = os.path.join(REPO, "testing", "d003", "stage_s4")
SRC_R2 = os.path.join(STAGE, "inject_r8m2a2_dual_R2.cpp")
SRC_BASE = os.path.join(STAGE, "inject_r4_plan.cpp")
OUT = os.path.join(STAGE, "inject_r8m2a2_dual_R3.cpp")

BLOCK_A = r"""/* ------------------------------------------------------------------------
 * [P05-S4 R8 M2a2 R3, U244 rule set R3] Target 2 of the dual-target injector.
 *   S4FMM_INJECT2 = s4malloc                  with S4FMM_NTH2 = canonical integer >= 1
 *   S4FMM_INJECT2 = plancall:K:M              K-th fft_plan_dft_2d call of the process, M-th wrapped malloc inside it
 *   S4FMM_INJECT2 = linearsolve_null2:ID:K    ID in {134,138,144,244,375,265,273}, K-th call of that ID (K >= 1)
 * Rule 1: canonical numbers only (plain decimal, value >= 1, no sign, no leading zero, no blank, no trailing text).
 * Rule 2: same-kind comparison with the parsed event of target 1 (as target 1 itself reads it):
 *           s4malloc  : stream index  (target 1 nth())
 *           plancall  : (K, M)        (target 1 plancall:K:M, or plan with NTH = N, which is (N, N))
 *           B2        : (ID, K)       (target 1 linearsolve_null2 or linearsolve_null2buf)
 *         Equal events: target 2 INVALID, never fires; stderr "S4FMM INJECT2 INVALID <reason>", printed once at start.
 * Rule 3: cross-kind requests never conflict (each kind counts its own event stream).
 * Rule 4: runtime fallback only: target 1 consumed the same event in the same call, so target 2 is SUPPRESSED
 *         (stderr "S4FMM INJECT2 SUPPRESSED <where>", counted in n_suppressed2).  Not a rejection.
 * Rule 5: n_hits2 and read-only query functions (s4fmm_inject2_*).
 * ------------------------------------------------------------------------ */
static const char *mode2(void){ const char *m = getenv("S4FMM_INJECT2"); return m ? m : ""; }
static int t2_parsed = 0;
static int t2_kind = 0;              /* 0 none, 1 s4malloc, 2 plancall, 3 linearsolve_null2, -1 invalid request */
static long t2_nth = 0, t2_k = 0, t2_m = 0;
static int t2_id = 0;
static long n_hits2 = 0;
static long n_invalid2 = 0;          /* target 2 requests refused (rule 1, rule 2, unknown kind) */
static long n_suppressed2 = 0;       /* rule 4 */
static long t2_malloc_seen = 0;      /* target 2 index of S4_malloc calls from FMM objects (FMM stream) */
static int t2_arm = 0;               /* 1 while plan call K runs (target 2) */
static long t2_plan_alloc = 0;       /* wrapped mallocs inside the armed plan call (target 2) */
static const int t2_b2_ids[7] = {134, 138, 144, 244, 375, 265, 273};

/* canonical decimal integer >= 1: first digit 1..9, then 0..9 only, at most 9 digits */
static int t2_canon(const char *s, long *out){
	if(NULL == s || s[0] < '1' || s[0] > '9'){ return 0; }
	long v = 0;
	int len = 0;
	for(const char *p = s; '\0' != *p; ++p){
		if(*p < '0' || *p > '9' || ++len > 9){ return 0; }
		v = v * 10 + (long)(*p - '0');
	}
	*out = v;
	return 1;
}
/* "A:B" with both parts canonical */
static int t2_split2(const char *s, long *a, long *b){
	const char *colon = strchr(s, ':');
	if(NULL == colon){ return 0; }
	char ab[16] = {0}, bb[16] = {0};
	const size_t la = (size_t)(colon - s);
	if(la == 0 || la >= sizeof(ab) || strlen(colon + 1) >= sizeof(bb)){ return 0; }
	memcpy(ab, s, la);
	strcpy(bb, colon + 1);
	return t2_canon(ab, a) && t2_canon(bb, b);
}
static int t2_b2_known(int id){
	for(int i = 0; i < 7; ++i){ if(t2_b2_ids[i] == id){ return 1; } }
	return 0;
}

/* Target 1 event as target 1 reads it, for the same-kind comparison only.  It reads the environment with the same
 * scanf forms that target 1's own hooks use (so the comparison is between the events target 1 actually fires on),
 * but it does not decide canonical form: rule 1 is applied to target 2's text alone.  Target 1 is not changed. */
static int t1e_kind = 0;             /* 0 none, 1 s4malloc, 2 plancall, 3 B2 (linearsolve_null2 or null2buf) */
static long t1e_a = 0, t1e_b = 0;    /* kind 1: a = stream index; kind 2: (a, b) = (K, M); kind 3: (a, b) = (ID, K) */
static void t1e_parse(void){
	const char *m = mode();
	t1e_kind = 0;
	if(0 == strcmp(m, "s4malloc")){ t1e_kind = 1; t1e_a = nth(); return; }
	/* mode "plan" (target 1, global plan-malloc count NTH) is NOT a (K, M) event: it is not compared with plancall. */
	if(0 == strncmp(m, "plancall:", 9)){
		long k = 0, mm = 0;
		int used = 0;
		if(2 == sscanf(m + 9, "%ld:%ld%n", &k, &mm, &used) && '\0' == m[9 + used] && k >= 1 && mm >= 1){
			t1e_kind = 2; t1e_a = k; t1e_b = mm;
		}
		return;
	}
	if(0 == strncmp(m, "linearsolve_null2:", 18) || 0 == strncmp(m, "linearsolve_null2buf:", 21)){
		const char *p = (0 == strncmp(m, "linearsolve_null2buf:", 21)) ? m + 21 : m + 18;
		int id = 0, k = 0, used = 0;
		if(2 == sscanf(p, "%d:%d%n", &id, &k, &used) && '\0' == p[used] && k >= 1 && t2_b2_known(id)){
			t1e_kind = 3; t1e_a = id; t1e_b = k;
		}
	}
}

static void t2_invalid(const char *why){
	n_invalid2++;
	t2_kind = -1;
	std::fprintf(stderr, "S4FMM INJECT2 INVALID %s\n", why);
}
static void t2_suppressed(const char *where){
	n_suppressed2++;
	std::fprintf(stderr, "S4FMM INJECT2 SUPPRESSED %s (target 1 consumed the same event; target 2 skipped)\n", where);
}
static void t2_parse(void){
	if(t2_parsed){ return; }
	t2_parsed = 1;
	const char *m = mode2();
	if('\0' == m[0]){ return; }
	t1e_parse();
	long a = 0, b = 0;
	if(0 == strcmp(m, "s4malloc")){
		if(!t2_canon(getenv("S4FMM_NTH2"), &a)){ t2_invalid("s4malloc needs S4FMM_NTH2 as a canonical integer >= 1"); return; }
		if(1 == t1e_kind && t1e_a == a){ t2_invalid("same S4_malloc event as target 1 (same stream index)"); return; }
		t2_kind = 1; t2_nth = a;
		return;
	}
	if(0 == strncmp(m, "plancall:", 9)){
		if(!t2_split2(m + 9, &a, &b)){ t2_invalid("plancall needs K:M as canonical integers >= 1"); return; }
		if(2 == t1e_kind && t1e_a == a && t1e_b == b){ t2_invalid("same plan event as target 1 (same (K,M))"); return; }
		t2_kind = 2; t2_k = a; t2_m = b;
		return;
	}
	if(0 == strncmp(m, "linearsolve_null2:", 18)){
		if(!t2_split2(m + 18, &a, &b)){ t2_invalid("linearsolve_null2 needs ID:K as canonical integers"); return; }
		if(!t2_b2_known((int)a)){ t2_invalid("linearsolve_null2 ID is not one of the seven B2 sites"); return; }
		if(3 == t1e_kind && t1e_a == a && t1e_b == b){ t2_invalid("same LinearSolve event as target 1 (same (ID,K))"); return; }
		t2_kind = 3; t2_id = (int)a; t2_k = b;
		return;
	}
	t2_invalid("unknown target 2 kind");
}
/* Process start: parse once, so an invalid request is reported even if no hook is reached. */
static void t2_at_start(void) __attribute__((constructor));
static void t2_at_start(void){ t2_parse(); }

extern "C" long s4fmm_inject2_hits(void){ return n_hits2; }
extern "C" int s4fmm_inject2_requested(void){ return '\0' != mode2()[0]; }
extern "C" long s4fmm_inject2_invalid(void){ return n_invalid2; }
extern "C" long s4fmm_inject2_suppressed(void){ return n_suppressed2; }

/* Arms target 2 for plan call K (rule 2: the same K with another M is allowed).  Disarms on every return path. */
struct t2_plan_scope {
	int on;
	explicit t2_plan_scope(int want) : on(want) { if(on){ t2_plan_alloc = 0; t2_arm = 1; } }
	~t2_plan_scope(){ if(on){ t2_arm = 0; } }
};

#ifdef S4FMM_DUAL_HARNESS
/* Test-only, compiled only into the synthetic harness (never into a production object): sets the target 2 state
 * directly, bypassing the parse, so that the runtime SUPPRESSED path (rule 4) can be driven.
 *   kind 1: a = stream index;  kind 2: a = K, b = M;  kind 3: a = ID, b = K. */
extern "C" void s4fmm_dual_harness_force_t2(int kind, long a, long b){
	t2_parsed = 1; t2_kind = kind;
	if(1 == kind){ t2_nth = a; }
	else if(2 == kind){ t2_k = a; t2_m = b; }
	else if(3 == kind){ t2_id = (int)a; t2_k = b; }
	t1e_parse();
}
#endif
"""

# Target 2 plan-call bookkeeping must count every malloc of its armed plan call, including one that target 1 consumes.
# Insert BEFORE the unchanged target 1 branches (R2 line 152).  Target 1 is not changed: its branches still decide
# its own hit.  To detect a shared event (rule 4) BEFORE target 1 returns, the same condition target 1 uses is
# evaluated read-only here (n_plan_alloc + 1 == nth() for mode plan; pc_alloc + 1 == pc_m for plancall).  The read-only
# prediction is checked by the harness (case SHARED_PLAN_PREDICTION) against the actual target 1 result.
BLOCK_M1 = r"""	/* [P05-S4 R8 M2a2 R3, U244] target 2 counts its armed plan call's mallocs before target 1 can return NULL, so a
	 * malloc that target 1 consumes still advances target 2's count.  Read-only prediction of target 1's own hit on this
	 * malloc (same condition as its branches below), used only for rule 4. */
	t2_parse();
	if(1 == t2_arm && 2 == t2_kind){ t2_plan_alloc++; }
	const int t2_plan_hit = (1 == t2_arm && 2 == t2_kind && t2_plan_alloc == t2_m);
	const int t1_plan_pred = (1 == arm && 0 == strcmp(mode(), "plan") && n_plan_alloc + 1 == nth());
	const int t1_pc_pred = (1 == arm && pc_ok && pc_alloc + 1 == pc_m);
	if(t2_plan_hit && (t1_plan_pred || t1_pc_pred)){
		t2_suppressed("plan malloc");
	}
"""

# Target 2 fires after the unchanged target 1 branches (R2 lines 152-168) and only when target 1 did not return on
# this malloc.  The SUPPRESSED decision was taken in BLOCK_M1, so target 2 does not fire on a shared malloc.
BLOCK_M2 = r"""	/* [P05-S4 R8 M2a2 R3, U244] target 2 plancall fire, reached only when target 1 did not return on this malloc
	 * and the malloc was not a shared event (rule 4 handled above). */
	if(t2_plan_hit && !(t1_plan_pred || t1_pc_pred)){
		n_hits2++;
		n_hits++;
		std::fprintf(stderr, "S4FMM HIT dual target2 real malloc failure: plan call %ld malloc %ld, %zu B (hit2=%ld total=%ld)\n", t2_k, t2_plan_alloc, n, n_hits2, n_hits);
		return NULL;
	}
"""

BLOCK_B2 = r"""/* [P05-S4 R8 M2a2 R3, U244] Target 2 for family B2.  The target 1 hook runs first (body unchanged).  Target 2 then acts
 * only when target 1 did not consume this call; if target 1 did consume it, target 2 is SUPPRESSED (rule 4). */
extern "C" void S4_TEST_LINEARSOLVE_NULLINFO2_AFTER(int id, int *info, std::complex<double> *b, int n, int ld, int model){
	const long hits_before = n_hits;
	b2_target1_hook(id, info, b, n, ld, model);
	t2_parse();
	if(3 != t2_kind || id != t2_id){ return; }
	const int ix = b2_index(id);
	if(ix < 0 || b2_calls[ix] != t2_k){ return; }
	if(n_hits != hits_before){ t2_suppressed("linearsolve_null2"); return; }
	if(NULL == info){ return; }
	*info = 1;
	if(1 == model){
		for(int j = 0; j < n; ++j){
			for(int i = 0; i < n; ++i){
				b[i + j*ld] = std::complex<double>(i == j ? 1.0 : 0.0, 0.0);
			}
		}
	}
	n_hits2++;
	n_hits++;
	std::fprintf(stderr, "S4FMM HIT dual target2 linearsolve_null2 id=%d call=%ld model=%d (hit2=%ld total=%ld)\n", id, b2_calls[ix], model, n_hits2, n_hits);
}
"""

# S4_malloc wrapper: target 2 index is counted first (R2 counted it the same way), then the unchanged target 1
# branch runs; target 2 fires only if target 1 did not return NULL on this call.
BLOCK_S4 = r"""extern "C" void *__wrap__Z9S4_mallocm(size_t size){
	/* [P05-S4 R8 M2a2 R3, U244] target 2 index: counted before target 1 can return NULL, so a call that target 1 fails
	 * still advances target 2's index (both index the same process-wide stream of FMM S4_malloc calls). */
	t2_parse();
	const long t2_idx = (1 == t2_kind) ? ++t2_malloc_seen : 0;
	const int t2_hit = (1 == t2_kind && t2_idx == t2_nth);
	/* read-only prediction of target 1's own hit on this call (same condition as its branch below), used only for rule 4 */
	const int t1_pred = (0 == strcmp(mode(), "s4malloc") && n_s4malloc + 1 == nth());
	if(t2_hit && t1_pred){
		t2_suppressed("s4malloc");
	}
	if(0 == strcmp(mode(), "s4malloc")){
		n_s4malloc++;
		if(n_s4malloc == nth()){
			n_hits++;
			std::fprintf(stderr, "S4FMM HIT real S4_malloc failure: FMM call %zu B (hit=%ld)\n", size, n_s4malloc);
			return NULL;
		}
	}
	if(t2_hit && !t1_pred){
		n_hits2++;
		n_hits++;
		std::fprintf(stderr, "S4FMM HIT dual target2 real S4_malloc failure: FMM call %zu B (stream index %ld, hit2=%ld total=%ld)\n", size, t2_idx, n_hits2, n_hits);
		return NULL;
	}
	return __real__Z9S4_mallocm(size);
}
"""

BLOCK_P1 = r"""	/* [P05-S4 R8 M2a2 R3, U244] target 2 plan-call scope: armed for plan call K, disarmed on every return below. */
	t2_parse();
	const t2_plan_scope t2_scope(2 == t2_kind && n_plan_calls == t2_k);
"""

# (first R2 line, last R2 line, replacement text) -- inclusive 1-based R2 ranges; "insert" uses first = last + 1 with last given.
REPLACE = [
    (66, 137, BLOCK_A),
    (169, 179, BLOCK_M2),
    (366, 388, BLOCK_B2),
    (604, 624, BLOCK_S4),
    (720, 728, ""),
]
INSERT_AFTER = [
    (151, BLOCK_M1),
    (704, BLOCK_P1),
]
# Allowed R2 ranges whose lines may be removed or changed (the union of REPLACE ranges).
ALLOWED_REMOVED = [(a, b) for (a, b, _) in REPLACE]

# Anchors that must match the R2 text at the splice boundaries (sanity check against a changed R2).
ANCHORS = {
    66: "/* ------------------------------------------------------------------------",
    137: "extern \"C\" int s4fmm_inject2_requested(void)",
    151: "#endif",
    152: "if(1 == arm && 0 == strcmp(mode(), \"plan\")){",
    169: "/* [P05-S4 R8 M2a2 R2, U244] target 2 plancall: its own armed flag",
    179: "\t}",
    366: "/* [P05-S4 R8 M2a2 R2, U244] Target 2 for family B2.",
    388: "}",
    604: "extern \"C\" void *__wrap__Z9S4_mallocm(size_t size){",
    624: "}",
    704: "std::fprintf(stderr, \"S4FMM WITNESS plan call=",
    705: "if(0 == strcmp(mode(), \"plan\") && n_plan_calls == nth()){",
    720: "/* [P05-S4 R8 M2a2 R2, U244] target 2 plancall: arm only for its own plan call K",
    728: "\t}",
}


def read_lines(path):
    with open(path, "r", encoding="utf-8", newline="") as f:
        return f.read().split("\n")


def main():
    if os.path.exists(OUT):
        print("build_dual_r3_r8m2a2: REFUSED exists (U17): %s" % OUT)
        return 2
    r2 = read_lines(SRC_R2)
    # R2 ends with a newline, so the last split element is "".
    n = len(r2)
    bad = []
    for ln, want in ANCHORS.items():
        got = r2[ln - 1] if ln - 1 < n else ""
        if want not in got and got.strip() != want.strip():
            bad.append((ln, want, got))
    if bad:
        for ln, want, got in bad:
            print("ANCHOR_MISMATCH line=%d want=%r got=%r" % (ln, want, got))
        print("build_dual_r3_r8m2a2: FAIL anchors")
        return 1

    # Build the output by walking the R2 lines once.  Every R2 line is either kept (its number is recorded in
    # kept_lines) or lies inside a REPLACE range (recorded in removed_lines).  The check below uses these explicit
    # line numbers, not a sequence alignment, so repeated lines (for example "}" or "arm = 0;") cannot mislead it.
    rep_map = {a: (b, t) for (a, b, t) in REPLACE}
    ins_map = {ln: t for (ln, t) in INSERT_AFTER}
    out = []
    kept_lines = []
    removed_lines = []
    i = 1
    while i <= n:
        if i in rep_map:
            b, t = rep_map[i]
            removed_lines.extend(range(i, b + 1))
            if t:
                out.extend(t.split("\n")[:-1])
            i = b + 1
            continue
        out.append(r2[i - 1])
        kept_lines.append(i)
        if i in ins_map:
            out.extend(ins_map[i].split("\n")[:-1])
        i += 1
    text = "\n".join(out)
    if not text.endswith("\n"):
        text += "\n"

    # Checker 1: every removed R2 line lies inside an allowed range, and every R2 line is accounted for once.
    removed_outside = [ln for ln in removed_lines if not any(a <= ln <= b for (a, b) in ALLOWED_REMOVED)]
    accounted = sorted(kept_lines + removed_lines)
    if removed_outside:
        print("build_dual_r3_r8m2a2: FAIL removed R2 lines outside allowed ranges: %s" % removed_outside[:20])
        return 1
    if accounted != list(range(1, n + 1)):
        print("build_dual_r3_r8m2a2: FAIL R2 line accounting (kept+removed != 1..%d)" % n)
        return 1
    print("build_dual_r3_r8m2a2: checker1 removed=%d kept=%d removed_outside=0" % (len(removed_lines), len(kept_lines)))

    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write(text)

    diff_r2 = difflib.unified_diff(r2, text.split("\n"), "a/testing/d003/stage_s4/inject_r8m2a2_dual_R2.cpp",
                                   "b/testing/d003/stage_s4/inject_r8m2a2_dual_R3.cpp", lineterm="")
    diff_base = difflib.unified_diff(read_lines(SRC_BASE), text.split("\n"),
                                     "a/testing/d003/stage_s4/inject_r4_plan.cpp",
                                     "b/testing/d003/stage_s4/inject_r8m2a2_dual_R3.cpp", lineterm="")
    os.makedirs(EV, exist_ok=True)
    with open(os.path.join(EV, "SRC_DIFF_R8_M2a2_inject_dual_R3.txt"), "w", encoding="utf-8") as f:
        f.write("# SRC_DIFF R2 -> R3 (inject_r8m2a2_dual_R2.cpp -> inject_r8m2a2_dual_R3.cpp); generated by build_dual_r3_r8m2a2.py\n")
        f.write("\n".join(diff_r2) + "\n")
    with open(os.path.join(EV, "SRC_DIFF_R8_M2a2_inject_dual_R3_base.txt"), "w", encoding="utf-8") as f:
        f.write("# SRC_DIFF base -> R3 (inject_r4_plan.cpp -> inject_r8m2a2_dual_R3.cpp); generated by build_dual_r3_r8m2a2.py\n")
        f.write("\n".join(diff_base) + "\n")
    print("build_dual_r3_r8m2a2: OK lines_r2=%d lines_r3=%d removed_outside=0" % (n, len(text.split("\n"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
