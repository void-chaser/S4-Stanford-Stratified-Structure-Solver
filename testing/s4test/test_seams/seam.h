/* TEST-ONLY seam policy for the D002 Part3 closeout.
 *
 * This header exists only to exercise the rcwa -> S4 -> front-end propagation
 * of a non-zero RNP solver info.  It is a header-only, internal-linkage
 * utility: the production sources never include it, and rcwa.cpp includes it
 * only under -DS4_TEST_EIGEN_INFO.
 *
 * Policy (frozen):
 *   1. The injection request from S4_TEST_EIGEN_INFO is parsed STRICTLY:
 *      optional single sign, then decimal digits only, no surrounding or
 *      trailing characters, magnitude representable as a non-zero int.
 *      "0", "", " ", "abc", "1x", " 1", "0x1", "+", "-", "1.0" and
 *      out-of-range values are all INVALID and must not inject anything.
 *   2. A REAL non-zero solver info always wins.  The seam may only turn a
 *      successful (info == 0) solve into a failure; it can never rewrite a
 *      real non-zero info, and it can never turn a failure into success.
 *   3. Every real solver invocation that reaches the seam emits one EVENT line
 *      carrying the solver's own value, the environment classification, the
 *      requested value and the final effective value.  A HIT line is emitted
 *      additionally whenever the final value is non-zero, preserving the
 *      previous machine-readable form.
 */
#ifndef S4C_SEAM_H_INCLUDED
#define S4C_SEAM_H_INCLUDED

#include <stdio.h>
#include <stdlib.h>

#define S4C_SEAM_ENV "S4_TEST_EIGEN_INFO"
#define S4C_SEAM_MAX 2147483647L

/* Classification of an environment string.
 *   0 -> invalid (empty, malformed, or out of range)
 *   1 -> valid non-zero integer
 *   2 -> valid integer equal to zero
 * On 1 or 2 the parsed value is stored in *out (0 for class 2). */
static int s4c_seam_classify(const char *s, int *out) {
	const char *p = s;
	int sign = 1;
	long v = 0;
	if (NULL == s || '\0' == *s) { return 0; }
	if ('+' == *p || '-' == *p) { sign = ('-' == *p) ? -1 : 1; ++p; }
	if ('\0' == *p) { return 0; }
	for (; '\0' != *p; ++p) {
		if (*p < '0' || *p > '9') { return 0; }
		v = v * 10 + (long)(*p - '0');
		if (v > S4C_SEAM_MAX) { return 0; }
	}
	v *= sign;
	if (0 == v) { if (NULL != out) { *out = 0; } return 2; }
	if (NULL != out) { *out = (int)v; }
	return 1;
}

/* 1 when the string is a strictly valid non-zero injection request. */
static int s4c_seam_parse(const char *s, int *out) {
	return (1 == s4c_seam_classify(s, out)) ? 1 : 0;
}

/* Pure decision: real failures win; only a successful solve may be injected. */
static int s4c_seam_decide(int solver_info, int env_valid, int requested, int *final_out) {
	int final_info = solver_info;
	if (0 != solver_info) {
		final_info = solver_info;
	} else if (env_valid) {
		final_info = requested;
	}
	if (NULL != final_out) { *final_out = final_info; }
	return final_info;
}

/* Test-only entry point used by rcwa.cpp after the real RNP call. */
static int s4c_seam_resolve(int solver_info, const char *branch) {
	const char *env = getenv(S4C_SEAM_ENV);
	const char *env_state = "unset";
	int requested = 0;
	int env_valid = 0;
	int cls = 0;
	int final_info = solver_info;
	if (NULL != env) {
		if ('\0' == *env) {
			env_state = "empty";
		} else {
			cls = s4c_seam_classify(env, &requested);
			if (1 == cls) { env_valid = 1; env_state = "valid"; }
			else if (2 == cls) { env_state = "zero"; }
			else { env_state = "invalid"; }
		}
	}
	s4c_seam_decide(solver_info, env_valid, requested, &final_info);
	fprintf(stderr,
	        "S4_TEST_EIGEN_SEAM_EVENT branch=%s solver_info=%d env_state=%s requested=%d final=%d\n",
	        branch, solver_info, env_state, requested, final_info);
	if (0 != final_info) {
		fprintf(stderr, "S4_TEST_EIGEN_SEAM_HIT branch=%s injected_info=%d\n",
		        branch, final_info);
	}
	return final_info;
}

#endif /* S4C_SEAM_H_INCLUDED */
