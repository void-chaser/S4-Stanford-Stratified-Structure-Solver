// P03 / D002 targeted native driver.
//
// This translation unit #includes the REAL Eigensystems.cpp from the variant
// tree given by -DD002_SRC="...".  Nothing of the eigensolver algorithm is
// copied or re-implemented here: the file-local statics zgebal_ / zgebak_ /
// zhseqr_ become visible in this TU precisely because the actual source file is
// compiled into it.
//
// Test-only seam: only when D002_TEST_SEAM is defined (and only in the seam
// variant tree, which renames zhseqr_'s definition to d002_inner_zhseqr_ under
// that same macro) this TU defines zhseqr_ as a thin wrapper that runs the real
// body and may override ONLY the returned status at the real return boundary.
// The wrapper never touches RNP::Eigensystem's own return statement, never
// prints an expected value, and never returns early from Eigensystem.
//
// The driver only PRODUCES raw observations (return status, eigenvalues,
// vector buffers, observed ilo/ihi/scale, observed permutation).  All judging
// is done by an independent Python comparator from the fixed input matrix.

#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <complex>
#include <limits>
#include <string>
#include <map>
#include <vector>
#include <fstream>
#include <sstream>
#include <iostream>
#include <chrono>
#include <unistd.h>

#ifdef D002_TEST_SEAM
// Forward declaration of the seam wrapper: the included TU calls zhseqr_ at its
// three call sites, so the wrapper must be visible before the include.
static int zhseqr_(char job, char compz, size_t n, size_t ilo, size_t ihi,
                   std::complex<double> *h, size_t ldh, std::complex<double> *w,
                   std::complex<double> *z, size_t ldz, std::complex<double> *_work);
#endif
#define D002_SRC_FILE D002_SRC
#include D002_SRC_FILE

// ---------------------------------------------------------------- seam state
#ifdef D002_TEST_SEAM
static int g_seam_mode = 0;          // 0 = pass the real value through
static int g_seam_forced_info = 0;   // value returned when mode != 0
static long g_seam_calls = 0;
static long g_seam_onlyvalues_calls = 0;
static long g_seam_schur_calls = 0;
static int  g_seam_onlyvalues_real = -12345;
static int  g_seam_last_real = -12345;
#endif

// ------------------------------------------------------------------ helpers
typedef std::complex<double> cplx;

static std::map<std::string, std::string> g_spec;
static std::ofstream g_out;

static std::string sp(const std::string &k, const std::string &d = "")
{
	std::map<std::string, std::string>::const_iterator it = g_spec.find(k);
	return (it == g_spec.end()) ? d : it->second;
}

static long long spi(const std::string &k, long long d = 0)
{
	std::string v = sp(k);
	return v.empty() ? d : atoll(v.c_str());
}

static void em(const std::string &k, const std::string &v) { g_out << k << " " << v << "\n"; }

static void emd(const std::string &k, double v)
{
	char buf[64]; snprintf(buf, sizeof(buf), "%.17g", v);
	g_out << k << " " << buf << "\n";
}

static void emz(const std::string &k, size_t idx, const cplx &z)
{
	char buf[192];
	snprintf(buf, sizeof(buf), "%s %zu %.17g %.17g", k.c_str(), idx, z.real(), z.imag());
	g_out << buf << "\n";
}

// fixture memory: allocated with new[] of EXACTLY the documented capacity so
// that ASan redzones sit immediately next to the valid region.
struct Buf {
	cplx *p; size_t n;
	Buf() : p(NULL), n(0) {}
	void alloc(size_t cnt) { n = cnt ? cnt : 1; p = new cplx[n]; for (size_t i = 0; i < n; ++i) p[i] = cplx(0., 0.); }
	~Buf() { delete[] p; }
	Buf(const Buf &);            // no copy
	Buf &operator=(const Buf &); // no assign
};

struct BufD {
	double *p; size_t n;
	BufD() : p(NULL), n(0) {}
	void alloc(size_t cnt) { n = cnt ? cnt : 1; p = new double[n]; for (size_t i = 0; i < n; ++i) p[i] = 0.; }
	~BufD() { delete[] p; }
	BufD(const BufD &);
	BufD &operator=(const BufD &);
};

int main(int argc, char **argv)
{
	if (argc < 3) { fprintf(stderr, "usage: %s <spec> <out>\n", argv[0]); return 2; }
	{
		std::ifstream f(argv[1]);
		if (!f) { fprintf(stderr, "cannot open spec %s\n", argv[1]); return 2; }
		std::string line;
		while (std::getline(f, line)) {
			if (line.empty() || line[0] == '#') continue;
			std::istringstream is(line);
			std::string k, v;
			is >> k;
			std::getline(is, v);
			size_t a = v.find_first_not_of(" \t");
			if (a != std::string::npos) v = v.substr(a);
			g_spec[k] = v;
		}
	}
	g_out.open(argv[2]);
	if (!g_out) { fprintf(stderr, "cannot open out %s\n", argv[2]); return 2; }

#ifdef D002_TEST_SEAM
	g_seam_mode = (int)spi("seam_mode", 0);
	g_seam_forced_info = (int)spi("seam_info", 0);
#endif

	const std::string case_id = sp("case_id");
	const std::string entry = sp("entry");
	const std::string matrix = sp("matrix");
	const std::string variant = sp("variant");
	em("case_id", case_id);
	em("entry", entry);
	em("matrix", matrix);
	em("variant", variant);
	em("pid", std::to_string((long)getpid()));

	// ---- load matrix (column-major, n x n stored with lda rows) ----
	std::ifstream mf(sp("matrix_file").c_str());
	if (!mf) { em("error", "cannot_open_matrix_file"); return 3; }
	std::string tok;
	mf >> tok >> tok;                       // "matrix" <id>
	if (tok != matrix) { em("error", "matrix_id_mismatch"); return 3; }
	size_t n = 0, lda = 0;
	mf >> n >> lda;
	std::vector<cplx> A(n * lda + 1, cplx(0., 0.));
	for (size_t j = 0; j < n; ++j)
		for (size_t i = 0; i < lda; ++i) {
			double re = 0., im = 0.;
			mf >> re >> im;
			A[i + j * lda] = cplx(re, im);
		}
	em("n", std::to_string((long)n));
	em("lda", std::to_string((long)lda));

	// ---- replicated Eigensystem pre-steps on an identical copy -----------
	// Recorded only to know which structural branch the real producer takes
	// (anrm / scalea / ilo / ihi / scale[]).  Real RNP routines are used.
	double anrm = 0.;
	if (n > 0) RNP::TLASupport::CheapMatrixNorm<'M'>(n, n, &A[0], lda, &anrm);
	const double eps = 2 * std::numeric_limits<double>::epsilon();
	const double smlnum = sqrt(std::numeric_limits<double>::min()) / eps;
	const double bignum = 1. / smlnum;
	bool scalea = false;
	double cscale = 1.;
	if (anrm > 0. && anrm < smlnum) { scalea = true; cscale = smlnum; }
	else if (anrm > bignum) { scalea = true; cscale = bignum; }
	emd("anrm", anrm);
	em("scalea", scalea ? "1" : "0");
	emd("cscale", cscale);
	emd("smlnum", smlnum);
	emd("bignum", bignum);

	std::vector<cplx> Abal = A;
	if (scalea) RNP::TLASupport::RescaleMatrix<'G'>(0, 0, anrm, cscale, n, n, &Abal[0], lda);
	std::vector<double> scale_ref(n + 1, 1.);
	size_t ilo_ref = 1, ihi_ref = n;
	if (n > 0) zgebal_('B', n, &Abal[0], lda, &ilo_ref, &ihi_ref, &scale_ref[0]);
	em("ilo_1based", std::to_string((long)ilo_ref));
	em("ihi_1based", std::to_string((long)ihi_ref));
	{
		std::ostringstream os;
		for (size_t i = 0; i < n; ++i) { if (i) os << " "; os << scale_ref[i]; }
		em("scale", os.str());
	}

	int rc = 0;

	if (entry == "API" || entry == "PROBE") {
		if (entry == "PROBE") { em("driver_rc", "0"); g_out.close(); return 0; }

		const std::string want = sp("want", "none");
		const std::string wmode = sp("work_mode", "internal");
		const std::string rmode = sp("rwork_mode", "internal");
		size_t ldvl = (size_t)spi("ldvl", (long long)n);
		size_t ldvr = (size_t)spi("ldvr", (long long)n);
		long long lwork_spec = spi("lwork", 0);
		size_t lwork = (lwork_spec < 0) ? (size_t)-1 : (size_t)lwork_spec;

		if (ldvl < n) ldvl = n;
		if (ldvr < n) ldvr = n;

		Buf a, w, vl, vr, work;
		BufD rwork;
		a.alloc(n * lda);
		for (size_t i = 0; i < n * lda; ++i) a.p[i] = A[i];
		w.alloc(n);

		cplx *pvl = NULL, *pvr = NULL;
		size_t vlcap = 0, vrcap = 0;
		if (want == "vl" || want == "both") { vl.alloc(n * ldvl); vlcap = n * ldvl; pvl = vl.p; }
		if (want == "vr" || want == "both") { vr.alloc(n * ldvr); vrcap = n * ldvr; pvr = vr.p; }

		cplx *pwork = NULL; double *prwork = NULL;
		size_t workcap = 0, rworkcap = 0;
		if (wmode == "exact") { work.alloc(2 * n); workcap = 2 * n; pwork = work.p; lwork = 2 * n; }
		else if (wmode == "short") { work.alloc(2 * n - 1); workcap = 2 * n - 1; pwork = work.p; lwork = 2 * n - 1; }
		else if (wmode == "query") { work.alloc(8); workcap = 8; pwork = work.p; lwork = (size_t)-1; }
		else if (wmode == "null_lwork") { pwork = NULL; lwork = 2 * n; }
		else { pwork = NULL; lwork = 0; }

		if (rmode == "exact") { rwork.alloc(2 * n); rworkcap = 2 * n; prwork = rwork.p; }
		else if (rmode == "short") { rwork.alloc(n); rworkcap = n; prwork = rwork.p; }
		else { prwork = NULL; }

		em("ldvl", std::to_string((long)ldvl));
		em("ldvr", std::to_string((long)ldvr));
		em("lwork_passed", (lwork == (size_t)-1) ? "SIZE_MAX" : std::to_string((long)lwork));
		em("work_mode", wmode);
		em("rwork_mode", rmode);
		em("want", want);
		em("a_capacity_elems", std::to_string((long)(n * lda)));
		em("vl_capacity_elems", std::to_string((long)vlcap));
		em("vr_capacity_elems", std::to_string((long)vrcap));
		em("work_capacity_elems", std::to_string((long)workcap));
		em("rwork_capacity_elems", std::to_string((long)rworkcap));

		std::chrono::steady_clock::time_point t0 = std::chrono::steady_clock::now();
		int info = RNP::Eigensystem(n, n ? &a.p[0] : NULL, lda, n ? &w.p[0] : NULL,
		                            pvl, ldvl, pvr, ldvr, pwork, prwork, lwork);
		std::chrono::steady_clock::time_point t1 = std::chrono::steady_clock::now();
		emd("elapsed_s", std::chrono::duration<double>(t1 - t0).count());
		em("info", std::to_string(info));

		if (wmode == "query" && pwork) emz("work0", 0, pwork[0]);
		for (size_t i = 0; i < n; ++i) emz("w", i, w.p[i]);
		for (size_t i = 0; i < vlcap; ++i) emz("vl_flat", i, vl.p[i]);
		for (size_t i = 0; i < vrcap; ++i) emz("vr_flat", i, vr.p[i]);
	} else if (entry == "HELPER_GEBAK") {
		// Real producer (the zgebal_ call above, same TU) feeding the real
		// consumer (zgebak_, same TU).  The permutation is observed by
		// decoding a marker matrix, never by instrumenting the algorithm.
		const std::string side = sp("side", "R");
		const std::string job = sp("job", "P");
		size_t m = (size_t)spi("m", (long long)n);
		size_t ldv = (size_t)spi("ldv", (long long)n);
		if (ldv < n) ldv = n;
		const size_t alloc = (n ? n : 1) * ldv;
		Buf v;
		v.alloc(alloc);
		for (size_t i = 0; i < alloc; ++i) v.p[i] = cplx(-777.0, 0.);
		for (size_t j = 0; j < m; ++j)
			for (size_t i = 0; i < n; ++i) v.p[i + j * ldv] = cplx(1000.0 + (double)i, 0.);
		em("side", side);
		em("job", job);
		em("m", std::to_string((long)m));
		em("ldv", std::to_string((long)ldv));
		em("v_capacity_elems", std::to_string((long)alloc));
		zgebak_(job.empty() ? 'P' : job[0], side.empty() ? 'R' : side[0], n, ilo_ref - 1, ihi_ref - 1,
		        &scale_ref[0], m, n ? &v.p[0] : NULL, ldv);
		for (size_t i = 0; i < alloc; ++i) emz("v_flat", i, v.p[i]);
	} else {
		em("error", "unknown_entry");
		rc = 4;
	}

#ifdef D002_TEST_SEAM
	em("seam_enabled", "1");
	em("seam_mode_used", std::to_string(g_seam_mode));
	em("seam_forced_info", std::to_string(g_seam_forced_info));
	em("seam_calls_total", std::to_string(g_seam_calls));
	em("seam_calls_onlyvalues", std::to_string(g_seam_onlyvalues_calls));
	em("seam_calls_schur", std::to_string(g_seam_schur_calls));
	em("seam_last_real_info", std::to_string(g_seam_last_real));
	em("seam_onlyvalues_real_info", std::to_string(g_seam_onlyvalues_real));
#else
	em("seam_enabled", "0");
#endif
	em("driver_rc", std::to_string(rc));
	g_out.close();
	return rc;
}

#ifdef D002_TEST_SEAM
// Test-only seam.  Runs the REAL zhseqr_ body, then may override only the
// returned status, at the real return boundary.  Compiled only into the seam
// variant; absent from the ordinary candidate build.
//   g_seam_mode == 0 : never override (pass the real status through)
//   g_seam_mode == 1 : override the only-values call (job='E', compz='N')
//   g_seam_mode == 2 : override every call (used to show the Schur/vector
//                      branches propagate a status on their own)
static int zhseqr_(char job, char compz, size_t n, size_t ilo, size_t ihi,
                   cplx *h, size_t ldh, cplx *w, cplx *z, size_t ldz, cplx *_work)
{
	int real_info = d002_inner_zhseqr_(job, compz, n, ilo, ihi, h, ldh, w, z, ldz, _work);
	++g_seam_calls;
	g_seam_last_real = real_info;
	if (job == 'E' && compz == 'N') { ++g_seam_onlyvalues_calls; g_seam_onlyvalues_real = real_info; }
	else { ++g_seam_schur_calls; }
	if (g_seam_mode == 2) return g_seam_forced_info;
	if (g_seam_mode == 1 && job == 'E' && compz == 'N') return g_seam_forced_info;
	return real_info;
}
#endif
