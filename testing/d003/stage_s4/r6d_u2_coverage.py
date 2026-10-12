#!/usr/bin/env python3
"""P05-S4 R6d-3: stage classification and coverage tables for the 202-point U2 set.

New script of round R6d (ERRATA_6d E6d-3).  It reads committed registries, evidence
gdb logs and tree F source lines (git show, read-only).  It writes only into the R6d
evidence directory given as argument 1 (default p05-s4r6d).

Stages (ERRATA_6d E6d-3, item 1):
  a = inside Simulation_ComputeLayerModes, before the FMM epsilon call
  b = inside FMMGetEpsilon_* (including the fmm_ret status rewrite of fmmret:*)
  c = AddFieldToCache (PolBasis modes only)
  d = after the FMM return, before ComputeLayerModes returns
  e = no stage (boundary; must be outside every ENTER/RETURN pair)

Outputs (EV):
  SEAM_SITE_STAGE_R6d.tsv     25 rows, source line text of each anchor
  U2_STAGE_R6d.tsv            202 rows
  U2_STAGE_COUNT_R6d.tsv      stage x inj_kind x mode
  U2_CACHEHIT_R6d.tsv         cache-hit check (stage c)
  U2_COVERAGE_R6d.tsv         U2 coverage table (brief R6d section 3)

Exit codes: 2 = assertion failed (nothing else written); 3 = STAGE_CONFLICT present
(tables not written, work stops for the user).
"""
import collections
import os
import re
import subprocess
import sys

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV_NAME = sys.argv[1] if len(sys.argv) > 1 else "p05-s4r6d"
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", EV_NAME)

TREE_F = "4a6f64927a30537740dd0c8f11f9a5aae5e46ba4"

MAP = os.path.join(REPO, "checkpoints/p05/registries/s4r6b/MAP_R6b_ALL.tsv")
SITEMAP = os.path.join(REPO, "checkpoints/p05/registries/s4r3/SITEMAP.tsv")
RES_STATE = os.path.join(REPO, "checkpoints/p05/registries/s4r6c/RESULTS_R6c_STATE.tsv")
RES_SEAM = os.path.join(REPO, "checkpoints/p05/registries/s4r6c/RESULTS_R6c_SEAM.tsv")
LOG_STATE = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r6c/state/pass1")
LOG_SEAM = os.path.join(REPO, "checkpoints/p05/evidence/p05-s4r6c/state/seam_pass1")


def die(code, msg):
    sys.stderr.write("r6d_u2_coverage: " + msg + "\n")
    sys.exit(code)


def read_tsv(path):
    hdr, rows = None, []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#") or not line.strip():
                continue
            f = line.rstrip("\n").split("\t")
            if hdr is None:
                hdr = f
                continue
            rows.append(dict(zip(hdr, f)))
    return rows


def read_log(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read().splitlines()


def tree_line(path, lineno):
    """Source line text of tree F at lineno (1-based), CR stripped."""
    txt = subprocess.check_output(["git", "show", "HEAD:S4/" + path], text=True)
    lines = txt.split("\n")
    return lines[lineno - 1].rstrip("\r")


# ---------------------------------------------------------------------------
# 0. Tree F identity
# ---------------------------------------------------------------------------
if subprocess.check_output(["git", "rev-parse", "HEAD:S4"], text=True).strip() != TREE_F:
    die(2, "HEAD:S4 differs from tree F")

# ---------------------------------------------------------------------------
# 1. The 202-point map and its R3/R4PC/R5M2 correspondence to SITEMAP.
#    Rule (planner R6d-1 item 2): drop the 'M2-' prefix and the '-F' suffix, then
#    match SITEMAP point_id.  Assert 177 matched, 0 NOMATCH, all callers FMMGetEpsilon_*.
# ---------------------------------------------------------------------------
MAP_ROWS = read_tsv(MAP)
if len(MAP_ROWS) != 202:
    die(2, "MAP has %d rows, expected 202" % len(MAP_ROWS))

SM = {}
for r in read_tsv(SITEMAP):
    SM[r["point_id"]] = r

def sitemap_key(pid):
    """Map a MAP point_id (R3/R4PC/R5M2 form) to its SITEMAP point_id."""
    k = pid
    if k.startswith("M2-"):
        k = "M-" + k[len("M2-"):]
    if k.endswith("-F"):
        k = k[:-2]
    return k

FMM_POINT_SOURCES = ("R3", "R4PC", "R5M2")
fmm_rows = [r for r in MAP_ROWS if r["source"] in FMM_POINT_SOURCES]
if len(fmm_rows) != 177:
    die(2, "R3+R4PC+R5M2 rows = %d, expected 177" % len(fmm_rows))

sm_hit, sm_nomatch = {}, []
for r in fmm_rows:
    k = sitemap_key(r["point_id"])
    if k not in SM:
        sm_nomatch.append(r["point_id"])
    else:
        sm_hit[r["point_id"]] = SM[k]
if len(sm_hit) != 177 or sm_nomatch:
    die(2, "SITEMAP correspondence: matched=%d NOMATCH=%d %s" % (len(sm_hit), len(sm_nomatch), sm_nomatch[:5]))
callers = collections.Counter(v["caller_function"] for v in sm_hit.values())
if any(not c.startswith("FMMGetEpsilon_") for c in callers):
    die(2, "non-FMM caller among the 177 points: %s" % callers)

# ---------------------------------------------------------------------------
# 2. Seam anchors (25 points).  Stage and kind are fixed here by the source reading in
#    the basis column.  Each anchor's line text is read from tree F and must contain
#    the fragment (asserted).  request = MAP request string.
# ---------------------------------------------------------------------------
SEAM_ANCHORS = {
    # request: (file, line, fragment, stage, inj_kind, basis)
    "linearsolve:1:1:info": ("fmm/fmm_FFT.cpp", 209, "RNP::LinearSolve<'N'>(n,n, Epsilon2", "b", "SEAM_INFO_FORCED_A",
        "[源码] fmm_FFT.cpp:209 LinearSolve inside FMMGetEpsilon_FFT; hook after the call sets solve_info (apply_seam.py:12-30, linearsolve_seam.patch); the FMM return check is fmm_FFT.cpp:210"),
    "linearsolve:2:1:info": ("fmm/fmm_kottke.cpp", 284, "RNP::LinearSolve<'N'>(n,n, Epsilon2", "b", "SEAM_INFO_FORCED_A",
        "[源码] fmm_kottke.cpp:284 LinearSolve inside FMMGetEpsilon_Kottke; hook after the call sets solve_info (apply_seam.py); the FMM return check follows"),
    "linearsolve_null2:134:1": ("fmm/fmm_closed.cpp", 134, "RNP::LinearSolve<'N'>(n,n, Epsilon_inv", "b", "SEAM_INFO_FORCED_B2",
        "[源码] fmm_closed.cpp:134 LinearSolve inside FMMGetEpsilon_ClosedForm (1D); hook sets the real &solve_info non-zero after the solve, before its check (apply_seam_b2.py:7-12)"),
    "linearsolve_null2:138:1": ("fmm/fmm_closed.cpp", 138, "RNP::LinearSolve<'N'>(n,n, &Epsilon2[n+0*n2]", "b", "SEAM_INFO_FORCED_B2",
        "[源码] fmm_closed.cpp:138 second 1D solve inside FMMGetEpsilon_ClosedForm (apply_seam_b2.py:7-12)"),
    "linearsolve_null2:144:1": ("fmm/fmm_closed.cpp", 144, "RNP::LinearSolve<'N'>(n,n, &Epsilon2[0+0*n2]", "b", "SEAM_INFO_FORCED_B2",
        "[源码] fmm_closed.cpp:144 2D solve inside FMMGetEpsilon_ClosedForm (apply_seam_b2.py:7-12)"),
    "linearsolve_null2:244:1": ("fmm/fmm_closed.cpp", 244, "RNP::LinearSolve<'N'>(n,n, &Epsilon2[0+0*n2]", "b", "SEAM_INFO_FORCED_B2",
        "[源码] fmm_closed.cpp:244 tensor-branch solve inside FMMGetEpsilon_ClosedForm (apply_seam_b2.py:7-12)"),
    "linearsolve_null2:265:1": ("fmm/fmm_PolBasisNV.cpp", 267, "RNP::LinearSolve<'N'>(n,n, Eta,n, mDelta", "b", "SEAM_INFO_FORCED_B2",
        "[源码] fmm_PolBasisNV.cpp:267 solve inside FMMGetEpsilon_PolBasisNV (tree F line; the H-tree anchor was 265, apply_seam_b2.py); hook sets solve_info non-zero (apply_seam_b2.py:7-12)"),
    "linearsolve_null2:273:1": ("fmm/fmm_PolBasisVL.cpp", 273, "RNP::LinearSolve<'N'>(n,n, Eta,n, mDelta", "b", "SEAM_INFO_FORCED_B2",
        "[源码] fmm_PolBasisVL.cpp:273 solve inside FMMGetEpsilon_PolBasisVL (apply_seam_b2.py:7-12)"),
    "linearsolve_null2:375:1": ("fmm/fmm_PolBasisJones.cpp", 375, "RNP::LinearSolve<'N'>(n,n, Eta,n, &Epsilon2[n+n*n2]", "b", "SEAM_INFO_FORCED_B2",
        "[源码] fmm_PolBasisJones.cpp:375 solve inside FMMGetEpsilon_PolBasisJones (apply_seam_b2.py:7-12)"),
    "fmmret:150:1": ("S4.cpp", 2382, "fmm_ret = FMMGetEpsilon_Experimental(", "b", "SEAM_RET",
        "[源码] S4.cpp:2382 real FMM call; the status is rewritten after the call (apply_seam_r5_fmmret.py:7-9); the return check is S4.cpp:2413"),
    "fmmret:151:1": ("S4.cpp", 2386, "fmm_ret = FMMGetEpsilon_Kottke(", "b", "SEAM_RET",
        "[源码] S4.cpp:2386 real FMM call (Kottke dispatch); status rewritten after the call (apply_seam_r5_fmmret.py:7-9)"),
    "fmmret:152:1": ("S4.cpp", 2388, "fmm_ret = FMMGetEpsilon_FFT(", "b", "SEAM_RET",
        "[源码] S4.cpp:2388 real FMM call (FFT dispatch); status rewritten after the call"),
    "fmmret:153:1": ("S4.cpp", 2391, "fmm_ret = FMMGetEpsilon_PolBasisJones(", "b", "SEAM_RET",
        "[源码] S4.cpp:2391 real FMM call (FFT+Jones dispatch); status rewritten after the call"),
    "fmmret:154:1": ("S4.cpp", 2393, "fmm_ret = FMMGetEpsilon_PolBasisNV(", "b", "SEAM_RET",
        "[源码] S4.cpp:2393 real FMM call (FFT+NV dispatch); status rewritten after the call"),
    "fmmret:155:1": ("S4.cpp", 2395, "fmm_ret = FMMGetEpsilon_PolBasisVL(", "b", "SEAM_RET",
        "[源码] S4.cpp:2395 real FMM call (FFT+VL dispatch); status rewritten after the call"),
    "fmmret:156:1": ("S4.cpp", 2403, "fmm_ret = FMMGetEpsilon_PolBasisJones(", "b", "SEAM_RET",
        "[源码] S4.cpp:2403 real FMM call (ClosedForm+Jones); status rewritten after the call"),
    "fmmret:157:1": ("S4.cpp", 2405, "fmm_ret = FMMGetEpsilon_PolBasisNV(", "b", "SEAM_RET",
        "[源码] S4.cpp:2405 real FMM call (ClosedForm+NV); status rewritten after the call"),
    "fmmret:158:1": ("S4.cpp", 2407, "fmm_ret = FMMGetEpsilon_PolBasisVL(", "b", "SEAM_RET",
        "[源码] S4.cpp:2407 real FMM call (ClosedForm+VL); status rewritten after the call"),
    "fmmret:159:1": ("S4.cpp", 2400, "fmm_ret = FMMGetEpsilon_ClosedForm(", "b", "SEAM_RET",
        "[源码] S4.cpp:2400 real FMM call (ClosedForm); status rewritten after the call"),
    "kottke_alloc:31:1": ("fmm/fmm_kottke.cpp", 78, "std::complex<double> *work = fft_alloc_complex(6*ng2);", "b", "SEAM_RET",
        "[源码] fmm_kottke.cpp:78 allocation inside FMMGetEpsilon_Kottke, before its NULL check at 79"),
    "alloc:21:1": ("S4.cpp", 2267, "*layer_modes = (LayerModes*)malloc(sizeof(LayerModes));", "a", "SEAM_RET",
        "[源码] S4.cpp:2267 LayerModes malloc at the start of Simulation_ComputeLayerModes, before any FMM call; NULL check 2269-2272 returns 20"),
    "alloc:22:1": ("S4.cpp", 2301, "pB->q = (std::complex<double>*)S4_malloc(", "a", "SEAM_RET",
        "[源码] S4.cpp:2301 pB->q malloc, before the FMM calls (2382-2407) and the return check (2413); NULL check 2307"),
    "alloc:23:1": ("S4.cpp", 2421, "double *rwork = (double*)S4_malloc(sizeof(double) * 4*n);", "d", "SEAM_RET",
        "[源码] S4.cpp:2421 rwork malloc after the FMM return check (2413-2417) and the eigensystem stage start (2418)"),
    "alloc:24:1": ("S4.cpp", 2446, "work = (std::complex<double>*)S4_malloc(sizeof(std::complex<double>) * lwork);", "d", "SEAM_RET",
        "[源码] S4.cpp:2446 work malloc after the FMM return check (2413-2417) and the workspace query (2432-2445)"),
    "alloc:25:1": ("S4.cpp", 4007, "FieldCache *f = (FieldCache*)S4_malloc(", "c", "SEAM_RET",
        "[源码] S4.cpp:4007 FieldCache malloc inside Simulation_AddFieldToCache (S4.cpp:4005); the caller checks are fmm_PolBasis{Jones,NV,VL}.cpp:340/230/237; PolBasis modes only"),
}

SEAM_ROWS = [r for r in MAP_ROWS if r["source"] == "R4SEAM"]
if len(SEAM_ROWS) != 25:
    die(2, "seam rows = %d, expected 25" % len(SEAM_ROWS))

seam_site = []
for r in SEAM_ROWS:
    req = r["request"]
    if req not in SEAM_ANCHORS:
        die(2, "no anchor for seam request %s" % req)
    rel, line, frag, stage, kind, basis = SEAM_ANCHORS[req]
    src = tree_line(rel, line)
    if frag not in src:
        die(2, "anchor text mismatch %s %s:%d: %r" % (req, rel, line, src))
    seam_site.append((r["point_id"], req, rel, line, src, stage, kind, basis))

# ---------------------------------------------------------------------------
# 3. Log check.  For each point: the failing layer's ENTER/RETURN pair must contain the
#    HIT for stages a-d; a HIT for stage e must be outside all ENTER/RETURN pairs.
#    c only in PolBasis modes.
# ---------------------------------------------------------------------------
ENTER_RE = re.compile(r"^R6BCLM ENTER idx (\d+) name (\S+)")
RETURN_RE = re.compile(r"^R6BCLM RETURN idx (\d+) name (\S+) rc (\d+)")
HIT_RE = re.compile(r"^S4FMM HIT (.*)$")


def layer_windows(lines):
    """Return list of (idx, enter_line, return_line) for each ENTER/RETURN pair."""
    wins, open_enter = [], {}
    for i, l in enumerate(lines):
        m = ENTER_RE.match(l)
        if m:
            open_enter[int(m.group(1))] = i
            continue
        m = RETURN_RE.match(l)
        if m:
            idx = int(m.group(1))
            if idx in open_enter:
                wins.append((idx, open_enter.pop(idx), i, int(m.group(3))))
    return wins


def hits(lines):
    return [(i, m.group(1)) for i, l in enumerate(lines) for m in [HIT_RE.match(l)] if m]


def call_segment(lines, inj_call):
    """Line index range [start, end) of the R6CREQ <inj_call> segment (the injected call)."""
    starts = [i for i, l in enumerate(lines) if re.match(r"^R6CREQ (\d+) ", l)]
    seg = {}
    for k, s in enumerate(starts):
        n = int(re.match(r"^R6CREQ (\d+) ", lines[s]).group(1))
        end = starts[k + 1] if k + 1 < len(starts) else len(lines)
        seg[n] = (s, end)
    return seg.get(int(inj_call))


def check_point(log_path, failing_layer, inj_call, stage, mode):
    """Return (verdict, text).  verdict in CONSISTENT / STAGE_CONFLICT / STAGE_UNRESOLVED.

    The check is made inside the injected call (R6CREQ <inj_call> segment): for stages a-d the
    HIT must lie between ENTER and RETURN of the failing layer (rc != 0); for stage e the HIT
    must lie outside every ENTER/RETURN pair.  twice-route points fail again in a later call
    (k_fail may differ from inj_call); that is not a conflict, so only the injected call is used.
    """
    if not os.path.exists(log_path):
        return "STAGE_UNRESOLVED", "no gdb log %s" % log_path
    lines = read_log(log_path)
    seg = call_segment(lines, inj_call)
    if seg is None:
        return "STAGE_UNRESOLVED", "no R6CREQ %s segment" % inj_call
    s0, s1 = seg
    wins = [w for w in layer_windows(lines) if s0 <= w[1] < s1]
    real_hits = [(i, t) for (i, t) in hits(lines) if s0 <= i < s1]
    if not real_hits:
        return "STAGE_UNRESOLVED", "no HIT line in injected call %s" % inj_call
    fw = [w for w in wins if str(w[0]) == str(failing_layer)]
    if stage in ("a", "b", "c", "d"):
        if not fw:
            return "STAGE_CONFLICT", "stage %s but no ENTER/RETURN of failing layer %s in injected call %s" % (stage, failing_layer, inj_call)
        idx, enter, ret, rc = fw[0]
        inside = [t for (i, t) in real_hits if enter < i < ret]
        if not inside:
            return "STAGE_CONFLICT", "stage %s but no HIT inside failing-layer window (idx %s)" % (stage, idx)
        if stage == "c" and mode not in ("nv", "jones", "vl"):
            # AddFieldToCache is called from the PolBasis modes only
            return "STAGE_CONFLICT", "stage c outside PolBasis mode %s" % mode
        return "CONSISTENT", "HIT inside ENTER/RETURN of failing layer %s rc %d (injected call %s)" % (idx, rc, inj_call)
    if stage == "e":
        for w in fw:
            if any(w[1] < i < w[2] for (i, _) in real_hits):
                return "STAGE_CONFLICT", "stage e but HIT inside failing-layer window"
        return "CONSISTENT", "HIT outside all ENTER/RETURN windows"
    return "STAGE_UNRESOLVED", "unknown stage %s" % stage


# ---------------------------------------------------------------------------
# 4. Assemble U2 rows.  177 FMM points: stage from the SITEMAP caller (planner item 1),
#    mode / route / inj_call / failing layer from RESULTS_R6c.  Seam points: from the
#    anchor table (source) and RESULTS_R6c_SEAM (log facts).
# ---------------------------------------------------------------------------
state_by_pid = {}
for r in read_tsv(RES_STATE):
    if r["pass"] == "1":
        state_by_pid[r["point_id"]] = r
seam_by_pid = {}
for r in read_tsv(RES_SEAM):
    if r["pass"] == "1":
        seam_by_pid[r["point_id"]] = r

# Stage of a FMM point: caller is FMMGetEpsilon_* (asserted), so stage b.
# inj_kind by request:
#   exec      -> BOUNDARY_SIM   (inject_r4_plan.cpp:607-612, not a new finding)
#   s4malloc  -> REAL_ALLOC     (real S4_malloc failure in an FMM TU, inject_r4_plan.cpp:496-501)
#   plan*     -> REAL_ALLOC     (real malloc failure in fft_plan_dft_2d, inject_r4_plan.cpp:79-92)

def inj_kind_fmm(req):
    if req.startswith("exec"):
        return "BOUNDARY_SIM"
    if req.startswith("s4malloc") or req.startswith("plan"):
        return "REAL_ALLOC"
    die(2, "unknown FMM request %s" % req)

u2 = []
conflicts = []
for r in MAP_ROWS:
    pid = r["point_id"]
    if r["source"] in FMM_POINT_SOURCES:
        sm = sm_hit[pid]
        st = state_by_pid.get(pid)
        if st is None:
            die(2, "no RESULTS_R6c_STATE pass-1 row for %s" % pid)
        stage = "b"
        kind = inj_kind_fmm(r["request"])
        basis = "[源码] SITEMAP caller %s (%s, YES) -> FMMGetEpsilon_* => stage b; request %s" % (
            sm["caller_function"], sm["point_id"], r["request"])
        log = os.path.join(LOG_STATE, pid, "gdb.log")
        verdict, text = check_point(log, st["failing_layer"], st["inj_call"], stage, r["mode"])
        u2.append({
            "point_id": pid, "source": r["source"], "mode": r["mode"], "route": r["route"],
            "inj_call": st["inj_call"], "inj_kind": kind, "stage": stage,
            "basis": basis, "log_check": text, "result": verdict,
            "failing_layer": st["failing_layer"], "k_fail": st["k_fail"], "hit": st["hit"],
        })
    elif r["source"] == "R4SEAM":
        sd = seam_by_pid.get(pid)
        if sd is None:
            die(2, "no RESULTS_R6c_SEAM pass-1 row for %s" % pid)
        site = [s for s in seam_site if s[0] == pid][0]
        _, req, rel, line, src, stage, kind, basis = site
        log = os.path.join(LOG_SEAM, pid, "gdb.log")
        verdict, text = check_point(log, sd["failing_layer"], sd["inj_call"], stage, r["mode"])
        u2.append({
            "point_id": pid, "source": r["source"], "mode": r["mode"], "route": r["route"],
            "inj_call": sd["inj_call"], "inj_kind": kind, "stage": stage,
            "basis": "%s | source text: %s" % (basis, src.strip()),
            "log_check": text, "result": verdict,
            "failing_layer": sd["failing_layer"], "k_fail": sd["k_fail"], "hit": sd["hit"],
        })
    else:
        die(2, "unknown source %s" % r["source"])

if len(u2) != 202:
    die(2, "U2 rows = %d" % len(u2))
if len(set(x["point_id"] for x in u2)) != 202:
    die(2, "duplicate point_id in U2")
conflicts = [x for x in u2 if x["result"] == "STAGE_CONFLICT"]
unresolved = [x for x in u2 if x["result"] == "STAGE_UNRESOLVED"]

# Planner stop rules: STAGE_CONFLICT -> stop and report; > 20 UNRESOLVED -> stop.
if conflicts:
    sys.stderr.write("STAGE_CONFLICT %d points:\n" % len(conflicts))
    for c in conflicts:
        sys.stderr.write("  %s  %s\n" % (c["point_id"], c["log_check"]))
    sys.exit(3)
if len(unresolved) > 20:
    die(3, "STAGE_UNRESOLVED %d > 20: stop" % len(unresolved))

# ---------------------------------------------------------------------------
# 5. Write tables (EV only).  No existing file is overwritten.
# ---------------------------------------------------------------------------
os.makedirs(EV, exist_ok=True)


def out_path(name):
    p = os.path.join(EV, name)
    if os.path.exists(p):
        die(2, "refusing to overwrite %s" % p)
    return p


def write_rows(name, header, rows, comment):
    with open(out_path(name), "w", encoding="utf-8", newline="") as fh:
        fh.write("# %s\n" % comment)
        fh.write("\t".join(header) + "\n")
        for row in rows:
            fh.write("\t".join(str(row.get(h, "")) for h in header) + "\n")


# 5.1 SEAM_SITE_STAGE_R6d.tsv
write_rows(
    "SEAM_SITE_STAGE_R6d.tsv",
    ["point_id", "request", "file", "line", "source_line_text", "stage", "inj_kind", "basis"],
    [{"point_id": s[0], "request": s[1], "file": "S4/" + s[2], "line": s[3],
      "source_line_text": s[4].strip(), "stage": s[5], "inj_kind": s[6], "basis": s[7]} for s in seam_site],
    "SEAM_SITE_STAGE_R6d.tsv -- P05-S4 R6d seam anchor stage table (25 points, tree F).  Source text read from HEAD:S4 (git show).",
)

# 5.2 U2_STAGE_R6d.tsv
U2_HDR = ["point_id", "source", "mode", "route", "inj_call", "inj_kind", "stage", "basis",
          "log_check", "result", "failing_layer", "k_fail", "hit"]
write_rows(
    "U2_STAGE_R6d.tsv", U2_HDR, u2,
    "U2_STAGE_R6d.tsv -- P05-S4 R6d-3 stage of the 202 U2 points.  Rule: ERRATA_6d E6d-3.  Log check against RESULTS_R6c_* and gdb logs.",
)

# 5.3 Count table: stage x inj_kind x mode
cnt = collections.Counter((x["stage"], x["inj_kind"], x["mode"]) for x in u2)
count_rows = []
for (stg, kind, mode), n in sorted(cnt.items()):
    count_rows.append({"stage": stg, "inj_kind": kind, "mode": mode, "n": n})
write_rows("U2_STAGE_COUNT_R6d.tsv", ["stage", "inj_kind", "mode", "n"], count_rows,
           "U2_STAGE_COUNT_R6d.tsv -- stage x inj_kind x mode (202 points).  Stage e = 0 is written as 0 (not covered; destination R8).")

# 5.4 Cache-hit table (stage c, PolBasis)
cache_rows = [x for x in u2 if x["stage"] == "c"]
write_rows("U2_CACHEHIT_R6d.tsv", U2_HDR, cache_rows,
           "U2_CACHEHIT_R6d.tsv -- stage c points (AddFieldToCache cache-install failure).  Count %d." % len(cache_rows))

# 5.5 Coverage table
stage_counts = collections.Counter(x["stage"] for x in u2)
cov = []
for stg in ("a", "b", "c", "d", "e"):
    n = stage_counts.get(stg, 0)
    if n == 0:
        status, dest = "NOT_COVERED", "R8 (stage e special rule of I1 is not tested in R6d)"
    else:
        status, dest = "COVERED", "-"
    cov.append({"stage": stg, "n_points": n, "status": status, "destination": dest})
write_rows("U2_COVERAGE_R6d_by_stage.tsv", ["stage", "n_points", "status", "destination"], cov,
           "U2_COVERAGE_R6d_by_stage.tsv -- coverage by stage (U2 point count per stage).  Stage e: 0 -> not covered, destination R8.")

print("ok: 202 rows; stages", dict(stage_counts))
print("results", dict(collections.Counter(x["result"] for x in u2)))
print("kinds", dict(collections.Counter(x["inj_kind"] for x in u2)))


# ---------------------------------------------------------------------------
# 6. U28 item-by-item coverage (ERRATA_6d U28; brief R6d section 3 item 3).
#    Each row: item of the U2 original text (split into testable items), status
#    (covered / changed by ruling / not covered), evidence, and destination.
#    Counts are taken from the result tables above, not typed in.
# ---------------------------------------------------------------------------
def tally(rows, key):
    return collections.Counter(r[key] for r in rows)

st_rows = [r for r in read_tsv(RES_STATE) if r["pass"] == "1"]
se_rows = [r for r in read_tsv(RES_SEAM) if r["pass"] == "1"]
i3_st = tally(st_rows, "I3")
i2_se = tally(se_rows, "I2")
i3_se = tally(se_rows, "I3")
stage_n = collections.Counter(x["stage"] for x in u2)
kind_n = collections.Counter(x["inj_kind"] for x in u2)

U28 = [
    ("U2-1", "U2 original: failed-state modes NOT installed (failing layer modes==NULL)",
     "covered",
     "I1 HOLD %d/%d (177 state points, passes 1-2; seam 25 points)" % (
         tally(st_rows, "I1")["HOLD"], len(st_rows)),
     "RESULTS_R6c_STATE.tsv; RESULTS_R6c_SEAM.tsv (registries/s4r6c)", "-"),
    ("U2-2", "U2 original: cache NOT installed (cache entry of the failed call absent; PolBasis)",
     "covered (partly)",
     "I3 HOLD %d, N/A %d for 177 points; seam I3 HOLD %d, N/A %d; stage c points in table = %d (alloc:25, jones)" % (
         i3_st["HOLD"], i3_st["N/A"], i3_se["HOLD"], i3_se["N/A"], stage_n.get("c", 0)),
     "RESULTS_R6c_STATE.tsv I3; RESULTS_R6c_SEAM.tsv I3; U2_CACHEHIT_R6d.tsv; ERRATA_6d U26 (I3 N/A accepted)",
     "stage c covers only 1 point (jones); nv/vl cache install failure not covered: R8"),
    ("U2-3", "U2 original: solution state NOT installed (request layer solved==0, I4)",
     "covered",
     "I4 HOLD 177/177 (state) and 25/25 (seam), passes 1-2",
     "RESULTS_R6c_STATE.tsv I4; RESULTS_R6c_SEAM.tsv I4 (I4 = I4', U14)",
     "-"),
    ("U2-4", "U2 original: other layers keep their modes and are not re-entered on retry (I2, I5)",
     "covered",
     "I2 HOLD 177/177 (state), seam HOLD %d, N/A %d; I5 HOLD 177/177 and 25/25" % (
         i2_se["HOLD"], i2_se["N/A"]),
     "RESULTS_R6c_STATE.tsv I2, I5; RESULTS_R6c_SEAM.tsv I2, I5; ERRATA_6 E6-8",
     "-"),
    ("U2-5", "U2 original: stage a (inside ComputeLayerModes before FMM)",
     "covered (2 points)",
     "stage a n=%d (alloc:21, alloc:22; both HIT in layer 0 window, rc 20)" % stage_n.get("a", 0),
     "U2_STAGE_R6d.tsv; SEAM_SITE_STAGE_R6d.tsv", "2 points only"),
    ("U2-6", "U2 original: stage b (inside FMMGetEpsilon_*, incl. fmmret)",
     "covered",
     "stage b n=%d (REAL_ALLOC %d, BOUNDARY_SIM %d, SEAM_INFO_FORCED %d, SEAM_RET %d)" % (
         stage_n.get("b", 0),
         sum(1 for x in u2 if x["stage"] == "b" and x["inj_kind"] == "REAL_ALLOC"),
         sum(1 for x in u2 if x["stage"] == "b" and x["inj_kind"] == "BOUNDARY_SIM"),
         sum(1 for x in u2 if x["stage"] == "b" and x["inj_kind"].startswith("SEAM_INFO")),
         sum(1 for x in u2 if x["stage"] == "b" and x["inj_kind"] == "SEAM_RET")),
     "U2_STAGE_R6d.tsv; U2_STAGE_COUNT_R6d.tsv",
     "stage-b basis is [源码] SITEMAP caller; log check = HIT inside failing layer, not an FMM-function boundary (see ERRATA_6d E6d-5)"),
    ("U2-7", "U2 original: stage c (AddFieldToCache, PolBasis only)",
     "covered (1 point)",
     "stage c n=%d" % stage_n.get("c", 0),
     "U2_CACHEHIT_R6d.tsv", "see U2-2"),
    ("U2-8", "U2 original: stage d (after FMM return, before ComputeLayerModes returns)",
     "covered (2 points)",
     "stage d n=%d (alloc:23, alloc:24)" % stage_n.get("d", 0),
     "U2_STAGE_R6d.tsv", "2 points only"),
    ("U2-9", "U2 original: stage e (outside every ENTER/RETURN; special rule of I1)",
     "not covered",
     "stage e n=0 (no point of U2 is in stage e)",
     "U2_STAGE_COUNT_R6d.tsv; U2_COVERAGE_R6d.tsv",
     "R8: the stage-e special rule of I1 is therefore not tested in R6d"),
    ("U2-10", "U2 original: I7 (sanitizer) judgement",
     "changed by ruling (DEFERRED, U9)",
     "I7 DEFERRED for all 177 + 25 points (no sanitizer run)",
     "RULINGS.tsv U9", "R8 (U9)"),
    ("U2-11", "U2 original: dual-target injection",
     "changed by ruling (DEFERRED, U9)",
     "not run in R6c/R6d",
     "RULINGS.tsv U9", "R8 (U9)"),
    ("U2-12", "U2 original: other-layer failure variants (failure in a layer other than layer 1)",
     "changed by ruling (DEFERRED, U20)",
     "not run (the state-judgement windows only cover the failing layer, layer 1 for the 177 points)",
     "RULINGS.tsv U20", "R8 (U20)"),
    ("U2-13", "U2 original: seam controls (I2/I3/I6 need a no-injection control)",
     "covered",
     "control table U18: 18 controls (R6c2); seam state 25 points pass 1-2",
     "REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv; RESULTS_R6c_SEAM.tsv",
     "-"),
    ("U2-14", "U2 original: judge self-test (corrupted examples VIOLATED on the named invariant)",
     "covered",
     "R6c2 self-test 11/11 corrupted VIOLATED, 3/3 originals HOLD",
     "SELFTEST_R6c2_v2.tsv (registries/s4r6c)",
     "-"),
    ("U2-15", "U2 original: RNV1 (pattern malloc without NULL check; section 4 of brief R6d)",
     "covered (R6d-2)",
     "RNV1 CRASH (rc 139) MATCH in RESULTS_R6d_RNV1_pass1_run2 and pass2_run2 (see RED_POINTS_LEDGER_R6d.tsv)",
     "RESULTS_R6d_RNV1_pass{1,2}_run2.tsv; RNV1_SOURCE_R6d.md; ERRATA_6d U24",
     "vl NG=1 baseline rc 20 is an OBSERVATION of normal input, not counted in RNV1"),
]

u28_rows = [dict(zip(["item", "u2_item", "status", "evidence_and_count", "evidence_path", "destination"], r)) for r in U28]
write_rows("U2_COVERAGE_R6d.tsv", ["item", "u2_item", "status", "evidence_and_count", "evidence_path", "destination"],
           u28_rows,
           "U2_COVERAGE_R6d.tsv -- U28 item-by-item coverage of the U2 original text (ERRATA_6d U28).  Replaces the stage-only table (kept as _stage_only.tsv.bak).")
print("U28 rows", len(u28_rows))
