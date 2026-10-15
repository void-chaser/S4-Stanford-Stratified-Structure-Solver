/* ------------------------------------------------------------------------
 * [P05-S4 R8 M2a2 R3, U244 rule set R3] Target 2 of the dual-target injector.  Replaces the R2 target 2 block.
 *   S4FMM_INJECT2 = s4malloc                  with S4FMM_NTH2 = canonical integer >= 1
 *   S4FMM_INJECT2 = plancall:K:M              K-th fft_plan_dft_2d call of the process, M-th wrapped malloc inside it
 *   S4FMM_INJECT2 = linearsolve_null2:ID:K    ID in {134,138,144,244,375,265,273}, K-th call of that ID
 * Rule 1: canonical decimal integers only (no sign, no leading zero, no blank, no trailing text, value >= 1).
 * Rule 2: same-kind comparison with target 1 (s4malloc: stream index; plancall: (K,M); linearsolve_null2: (ID,K));
 *         equal -> target 2 INVALID, never fires, stderr "S4FMM INJECT2 INVALID <reason>".
 * Rule 3: cross-kind requests never conflict.
 * Rule 4: runtime fallback only: if target 1 consumed the same event, target 2 is SUPPRESSED (printed, counted).
 * Rule 5: n_hits2, s4fmm_inject2_hits(), s4fmm_inject2_requested(), s4fmm_inject2_invalid(), s4fmm_inject2_suppressed().
 * ------------------------------------------------------------------------ */
static int t2_parsed = 0;
static int t2_kind = 0;              /* 0 none, 1 s4malloc, 2 plancall, 3 linearsolve_null2, -1 invalid request */
static long t2_nth = 0, t2_k = 0, t2_m = 0;
static int t2_id = 0;
static long n_hits2 = 0;
static long n_invalid2 = 0;          /* refused target 2 requests (rule 2 and parse failures) */
static long n_suppressed2 = 0;       /* rule 4 */
static long t2_malloc_seen = 0;      /* S4_malloc calls from FMM objects, target 2 stream index */
static int t2_arm = 0;
static long t2_plan_alloc = 0;
static const int t2_b2_ids[7] = {134, 138, 144, 244, 375, 265, 273};

/* Canonical decimal integer >= 1: first char 1..9, the rest 0..9, at most 9 digits, nothing else. */
static int t2_canon(const char *s, long *out){
	if(NULL == s || s[0] < '1' || s[0] > '9'){ return 0; }
	long v = 0;
	int len = 0;
	for(const char *p = s; '\0' != *p; ++p){
		if(*p < '0' || *p > '9'){ return 0; }
		if(++len > 9){ return 0; }
		v = v * 10 + (long)(*p - '0');
	}
	if(v < 1){ return 0; }
	*out = v;
	return 1;
}

/* Target 1 request as the same-kind comparison needs it (canonical values only).  It reads the
 * same environment variables as target 1 and does not change any target 1 state. */
static int t1c_kind = 0;             /* 0 other or unparsable, 1 s4malloc, 2 plancall, 3 linearsolve_null2 */
static long t1c_nth = 0, t1c_k = 0, t1c_m = 0;
static int t1c_id = 0;
static void t1c_parse(void){
	const char *m = mode();
	t1c_kind = 0;
	if(0 == strcmp(m, "s4malloc")){
		if(t2_canon(getenv("S4FMM_NTH"), &t1c_nth)){ t1c_kind = 1; }
		return;
	}
	if(0 == strncmp(m, "plancall:", 9)){
		const char *colon = strchr(m + 9, ':');
		char kb[12] = {0}, mb[12] = {0};
		if(NULL == colon || colon - (m + 9) <= 0 || colon - (m + 9) >= 11){ return; }
		memcpy(kb, m + 9, (size_t)(colon - (m + 9)));
		if(strlen(colon + 1) >= 11){ return; }
		strcpy(mb, colon + 1);
		if(t2_canon(kb, &t1c_k) && t2_canon(mb, &t1c_m)){ t1c_kind = 2; }
		return;
	}
	if(0 == strncmp(m, "linearsolve_null2:", 18)){
		const char *colon = strchr(m + 18, ':');
		char ib[12] = {0}, kb[12] = {0};
		if(NULL == colon || colon - (m + 18) <= 0 || colon - (m + 18) >= 11){ return; }
		memcpy(ib, m + 18, (size_t)(colon - (m + 18)));
		if(strlen(colon + 1) >= 11){ return; }
		strcpy(kb, colon + 1);
		long idv = 0;
		if(t2_canon(ib, &idv) && t2_canon(kb, &t1c_k)){ t1c_id = (int)idv; t1c_kind = 3; }
		return;
	}
}

static void t2_invalid(const char *why){
	n_invalid2++;
	t2_kind = -1;
	std::fprintf(stderr, "S4FMM INJECT2 INVALID %s\n", why);
}

static void t2_parse(void){
	if(t2_parsed){ return; }
	t2_parsed = 1;
	const char *m = mode2();
	if('\0' == m[0]){ return; }
	t1c_parse();
	if(0 == strcmp(m, "s4malloc")){
		long v = 0;
		if(!t2_canon(getenv("S4FMM_NTH2"), &v)){ t2_invalid("s4malloc needs S4FMM_NTH2 as a canonical integer >= 1"); return; }
		if(1 == t1c_kind && t1c_nth == v){ t2_invalid("same S4_malloc event as target 1 (same stream index)"); return; }
		t2_kind = 1; t2_nth = v;
		return;
	}
	if(0 == strncmp(m, "plancall:", 9)){
		const char *colon = strchr(m + 9, ':');
		char kb[12] = {0}, mb[12] = {0};
		if(NULL == colon || colon - (m + 9) <= 0 || colon - (m + 9) >= 11 || strlen(colon + 1) >= 11){
			t2_invalid("plancall needs K:M as canonical integers >= 1"); return;
		}
		memcpy(kb, m + 9, (size_t)(colon - (m + 9)));
		strcpy(mb, colon + 1);
		long k = 0, mm = 0;
		if(!t2_canon(kb, &k) || !t2_canon(mb, &mm)){ t2_invalid("plancall needs K:M as canonical integers >= 1"); return; }
		if(2 == t1c_kind && t1c_k == k && t1c_m == mm){ t2_invalid("same plan event as target 1 (same (K,M))"); return; }
		t2_kind = 2; t2_k = k; t2_m = mm;
		return;
	}
	if(0 == strncmp(m, "linearsolve_null2:", 18)){
		const char *colon = strchr(m + 18, ':');
		char ib[12] = {0}, kb[12] = {0};
		if(NULL == colon || colon - (m + 18) <= 0 || colon - (m + 18) >= 11 || strlen(colon + 1) >= 11){
			t2_invalid("linearsolve_null2 needs ID:K as canonical integers"); return;
		}
		memcpy(ib, m + 18, (size_t)(colon - (m + 18)));
		strcpy(kb, colon + 1);
		long idv = 0, k = 0;
		if(!t2_canon(ib, &idv) || !t2_canon(kb, &k)){ t2_invalid("linearsolve_null2 needs ID:K as canonical integers"); return; }
		int known = 0;
		for(int i = 0; i < 7; ++i){ if(t2_b2_ids[i] == (int)idv){ known = 1; } }
		if(!known){ t2_invalid("linearsolve_null2 ID is not one of the seven B2 sites"); return; }
		if(3 == t1c_kind && t1c_id == (int)idv && t1c_k == k){ t2_invalid("same LinearSolve event as target 1 (same (ID,K))"); return; }
		t2_kind = 3; t2_id = (int)idv; t2_k = k;
		return;
	}
	t2_invalid("unknown target 2 kind");
}
extern "C" long s4fmm_inject2_hits(void){ return n_hits2; }
extern "C" int s4fmm_inject2_requested(void){ return '\0' != mode2()[0]; }
extern "C" long s4fmm_inject2_invalid(void){ t2_parse(); return n_invalid2; }
extern "C" long s4fmm_inject2_suppressed(void){ return n_suppressed2; }

/* Rule 4 helper: target 2 is skipped when target 1 consumed the event in this hook call. */
static void t2_suppress(const char *where){
	n_suppressed2++;
	std::fprintf(stderr, "S4FMM INJECT2 SUPPRESSED %s (target 1 consumed the same event; target 2 skipped)\n", where);
}
