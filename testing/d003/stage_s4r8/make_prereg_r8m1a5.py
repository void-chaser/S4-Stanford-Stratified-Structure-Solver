#!/usr/bin/env python3
# make_prereg_r8m1a5.py -- P05-S4 R8 M1b/M1c pre-registration (CONT3b1, brief section 5).  New file.
#
# This version does the checks that the brief makes mandatory before any expectation is written:
#   - every input file is read (committed tables only, plus the one evidence table named in the report, deviation D1)
#     and its path and sha256 are recorded in PREREG_INPUTS_R8_M1a5.tsv;
#   - per R7 group: the number of R7 points and the number of F2 rows in each of the two passes (PREREG_COUNTS);
#   - F2 two-pass agreement of class and rc1 for every point (brief 7: a disagreement is a stop, no expectation);
#   - U193: the 58 EVIDENCE_INSUFFICIENT PLANCALL points are cross-checked against both STATE passes (S4FMM_INJECT);
#   - U196(a): every CALLSEQ pair is IDENTICAL, and every unit of the R8 F2 request rows maps to a pair.
# It then writes PREREG_COUNTS_R8_M1a5.tsv, PREREG_STOP_R8_M1a5.tsv and PREREG_INPUTS_R8_M1a5.tsv.
#
# It does NOT write REGISTRY_S4_PRE_R8_M1b.tsv or REGISTRY_S4_PRE_R8_M1c.tsv.  Reason (recorded as stop STOP-EXP-1 in the
# stop table): the expectation of the two POSTHOC control points M1-CTRL-F2-fftvl-ng1 and M1-CTRL-F2-vl-ng1 is
# BASELINE_RC_EQUAL, which U139(c) does not map to an expected class.  Writing those two expectations would be a choice
# that the rulings do not make.  See the report, section 'stop items'.
#
# Run:  sh testing/d003/safe_run.sh p05-s4r8/m1a5 -- python3 -I -B testing/d003/stage_s4r8/make_prereg_r8m1a5.py
import hashlib, os, re, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a5")
EV4 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit2")
R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
R3C2 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c2")
R3C3 = os.path.join(REPO, "checkpoints", "p05", "registries", "s3r4c3")
M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")

INPUTS = []   # (label, relpath, sha256)
STOPS = []    # (stage, item, reason)


def stop(stage, item, reason):
    STOPS.append((stage, item, reason))


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def load(label, path):
    if not os.path.isfile(path):
        stop("INPUT", label, "missing: " + os.path.relpath(path, REPO))
        return None
    INPUTS.append((label, os.path.relpath(path, REPO), sha(path)))
    with open(path, encoding="utf-8", newline="") as fh:
        lines = [l.rstrip("\n") for l in fh if not l.startswith("#") and l.strip() != ""]
    if not lines:
        stop("INPUT", label, "empty")
        return None
    header = lines[0].split("\t")
    rows = []
    for n, l in enumerate(lines[1:], start=2):
        cells = l.split("\t")
        if len(cells) != len(header):
            stop("INPUT", label, "column count mismatch at data row %d" % n)
            continue
        d = dict(zip(header, cells))
        d["_row"] = n
        rows.append(d)
    return rows


def load_state(label, path):
    """STATE pass rows: raw lines starting with 'point'; column 1 = point id, column 7 = env (S4FMM_INJECT inside)."""
    if not os.path.isfile(path):
        stop("INPUT", label, "missing: " + os.path.relpath(path, REPO))
        return None
    INPUTS.append((label, os.path.relpath(path, REPO), sha(path)))
    out = {}
    with open(path, encoding="utf-8") as fh:
        for l in fh:
            if not l.startswith("point\t"):
                continue
            c = l.rstrip("\n").split("\t")
            m = re.search(r"S4FMM_INJECT=([^;]*)", c[7]) if len(c) > 7 else None
            out[c[1]] = m.group(1) if m else None
    return out


# ---------- load inputs ----------
REG_M1 = load("REG_M1", os.path.join(R7, "REGISTRY_S4_PRE_R7_M1.tsv"))
REG_M2 = load("REG_M2", os.path.join(R7, "REGISTRY_S4_PRE_R7_M2.tsv"))
REG_M2_ADD = load("REG_M2_ADD_v3", os.path.join(R7, "REGISTRY_S4_PRE_R7_M2_ADD_v3.tsv"))
REG_M2_CTRL = load("REG_M2_CTRL_SEAM", os.path.join(R7, "REGISTRY_S4_PRE_R7_M2_CTRL_SEAM.tsv"))
REG_M3 = load("REG_M3", os.path.join(R7, "REGISTRY_S4_PRE_R7_M3.tsv"))
RES = {}
for key, fn in [
    ("M1", "RESULTS_R7_M1_pass1_run2.tsv"), ("M1_2", "RESULTS_R7_M1_pass2_run2.tsv"),
    ("G1", "RESULTS_R7_G1_pass1_run7.tsv"), ("G1_2", "RESULTS_R7_G1_pass2_run7.tsv"),
    ("G2a", "RESULTS_R7_G2a_pass1_run7.tsv"), ("G2a_2", "RESULTS_R7_G2a_pass2_run7.tsv"),
    ("G2b", "RESULTS_R7_G2b_pass1_run4.tsv"), ("G2b_2", "RESULTS_R7_G2b_pass2_run4.tsv"),
    ("G2c", "RESULTS_R7_G2c_pass1_run7.tsv"), ("G2c_2", "RESULTS_R7_G2c_pass2_run7.tsv"),
    ("G3", "RESULTS_R7_G3_pass1_run4.tsv"), ("G3_2", "RESULTS_R7_G3_pass2_run4.tsv"),
    ("G4", "RESULTS_R7_G4_pass1_run4.tsv"), ("G4_2", "RESULTS_R7_G4_pass2_run4.tsv"),
    ("CTRL_SEAM", "RESULTS_R7_CTRL_SEAM_pass1_run7.tsv"), ("CTRL_SEAM_2", "RESULTS_R7_CTRL_SEAM_pass2_run7.tsv"),
]:
    RES[key] = load("RESULTS_" + key, os.path.join(R7, fn))
POSTHOC = load("RESULTS_M1_CTRL_REJUDGE_POSTHOC", os.path.join(R7, "RESULTS_R7_M1_CTRL_REJUDGE_POSTHOC.tsv"))
M3_P1 = load_state("M3_F2_STATE_R6c_pass1", os.path.join(R7, "M3_F2_STATE_R6c_pass1.tsv"))
M3_P2 = load_state("M3_F2_STATE_R6c_pass2", os.path.join(R7, "M3_F2_STATE_R6c_pass2.tsv"))
S3_A = load("REG_S3R4C2_A", os.path.join(R3C2, "REGISTRY_S3R4C2_A.tsv"))
S3_POLY = load("REG_S3R4C2_C_POLY", os.path.join(R3C2, "REGISTRY_S3R4C2_C_POLY.tsv"))
S3_CTRL = load("REG_S3R4C3_A_CTRL", os.path.join(R3C3, "REGISTRY_S3R4C3_A_CTRL.tsv"))
S3_B = load("REG_S3R4C3_B", os.path.join(R3C3, "REGISTRY_S3R4C3_B.tsv"))
REQ = load("REQUEST_TARGETS_AUDIT3", os.path.join(M1A, "REQUEST_TARGETS_R8_M1a4AUDIT3.tsv"))
CALLSEQ = load("CALLSEQ_F2_F3_R2", os.path.join(M1A, "CALLSEQ_F2_F3_R8_M1a4_R2.tsv"))
ADD22 = load("ADDITIONS_MAPPING_22_RUN2", os.path.join(EV4, "ADDITIONS_MAPPING_22_STRICT_R8_M1a4AUDIT2_RUN2.tsv"))
DRV = load("DRIVERS_R8_M1a", os.path.join(M1A, "DRIVERS_R8_M1a.tsv"))
DRV_F2 = load("DRIVERS_R8_M1a_F2_REUSED", os.path.join(M1A, "DRIVERS_R8_M1a_F2_REUSED.tsv"))
KSRC = load("K_SOURCE_G5F2", os.path.join(M1A, "K_SOURCE_G5F2_R8_M1a4AUDIT3.tsv"))


def index_by(rows, key):
    d = {}
    for r in rows or []:
        d.setdefault(r[key], []).append(r)
    return d


def f2_agreed(pass1, pass2, point_id):
    """(class, rc1) of the F2 row when both passes agree, None otherwise."""
    a = [r for r in index_by(pass1, "point_id").get(point_id, []) if r.get("tree") == "F2"]
    b = [r for r in index_by(pass2, "point_id").get(point_id, []) if r.get("tree") == "F2"]
    if len(a) != 1 or len(b) != 1:
        return None
    if a[0]["class"] != b[0]["class"] or a[0]["rc1"] != b[0]["rc1"]:
        return None
    return (a[0]["class"], a[0]["rc1"])


def main():
    needed = [REG_M1, REG_M2, REG_M2_ADD, REG_M2_CTRL, REG_M3, POSTHOC, M3_P1, M3_P2, S3_A, S3_POLY, S3_CTRL,
              S3_B, REQ, CALLSEQ, ADD22, DRV, DRV_F2, KSRC]
    if any(x is None for x in needed):
        stop("INPUT", "REQUIRED", "a required input is missing or unreadable; counts not computed")
        return None
    for k in RES:
        if RES[k] is None:
            stop("INPUT", k, "result table missing")
            return None

    counts = []
    GROUPS = [("M1", "M1", "M1_2"), ("G1", "G1", "G1_2"), ("G2a", "G2a", "G2a_2"), ("G2b", "G2b", "G2b_2"),
              ("G2c", "G2c", "G2c_2"), ("G3", "G3", "G3_2"), ("G4", "G4", "G4_2"),
              ("CTRL_SEAM", "CTRL_SEAM", "CTRL_SEAM_2")]
    for g, p1, p2 in GROUPS:
        f2_points = sorted({r["point_id"] for r in RES[p1] if r.get("tree") == "F2"})
        agreed = 0
        for pid in f2_points:
            if f2_agreed(RES[p1], RES[p2], pid) is None:
                stop("F2_TWO_PASS", pid, "F2 class or rc1 differs between passes (group %s); no expectation (brief 7)" % g)
            else:
                agreed += 1
        f2_rows_p2 = sum(1 for r in RES[p2] if r.get("tree") == "F2")
        counts.append((g, len(f2_points), f2_rows_p2, agreed))

    # ---- U193: the 58 EVIDENCE_INSUFFICIENT points, request text vs both STATE passes ----
    ev_ins = [r for r in KSRC if r["status"] == "EVIDENCE_INSUFFICIENT"]
    req_f2 = index_by([r for r in REQ if r["source_tree"] == "F2"], "point_id")
    k_rows = []
    for r in ev_ins:
        pid = r["point_id"]
        cands = req_f2.get(pid, [])
        if len(cands) != 1:
            stop("U193", pid, "request row not unique (%d)" % len(cands))
            continue
        m = re.match(r"plancall:(\d+):(\d+)$", cands[0]["request_raw"])
        if not m:
            stop("U193", pid, "request is not plancall: " + cands[0]["request_raw"])
            continue
        want = "plancall:%s:%s" % (m.group(1), m.group(2))
        a = M3_P1.get(pid)
        b = M3_P2.get(pid)
        if a == want and b == want:
            k_rows.append((pid, "K_FROM_REQUEST_AGREED", m.group(1), m.group(2), want, a, b))
        else:
            stop("U193", pid, "STATE INJECT %s|%s differs from request %s" % (a, b, want))
    if len(k_rows) != 58:
        stop("U193", "COUNT", "K_FROM_REQUEST_AGREED %d, expected 58" % len(k_rows))

    # ---- STOP-EXP-1: the expectation of the two POSTHOC BASELINE_RC_EQUAL control points is not defined by U139(c) ----
    bl = sorted({r["point_id"] for r in POSTHOC if r.get("label") == "BASELINE_RC_EQUAL"})
    stop("EXP", "STOP-EXP-1", "U139(c) defines expectations only for CONTROL_OK; BASELINE_RC_EQUAL points %s have no "
         "expected class under the rulings; not written, awaiting ruling (brief 7, 'expectation cannot be determined')"
         % ",".join(bl))
    # STOP-EXP-2: the expectations of REGISTRY_S4_PRE_R8_M1b/M1c are not generated in this version (see module header).
    stop("EXP", "STOP-EXP-2", "REGISTRY_S4_PRE_R8_M1b.tsv and REGISTRY_S4_PRE_R8_M1c.tsv are not written: this version "
         "computes the counts and the mandatory checks only; the expectation generator (U139a-e, U197) is not implemented "
         "here, so no formal pre-registration exists in this round (brief 5, 7)")

    # ---- U196(a): every CALLSEQ pair is IDENTICAL; every R8 F2 request unit that is not "-" maps to a pair ----
    cs_status = {}
    for r in CALLSEQ:
        cs_status[r["status"]] = cs_status.get(r["status"], 0) + 1
    if set(cs_status) != {"IDENTICAL"}:
        stop("U196", "CALLSEQ", "non-IDENTICAL pair status %s" % cs_status)
    pair_f2 = {r["unit_f2"] for r in CALLSEQ}
    pair_f3 = {r["unit_f3"] for r in CALLSEQ}
    unmapped = sorted({r["unit_id"] for r in REQ if r["source_tree"] == "F2" and r["unit_id"] not in ("-", "")
                       and r["unit_id"] not in pair_f2})
    if unmapped:
        stop("U196", "F2_UNITS", "%d F2 request units without a CALLSEQ pair (rule e)" % len(unmapped))

    if STOPS:
        return counts, k_rows
    return counts, k_rows


def write_all(counts, k_rows):
    os.makedirs(EV, exist_ok=True)
    names = ["PREREG_COUNTS_R8_M1a5.tsv", "PREREG_STOP_R8_M1a5.tsv", "PREREG_INPUTS_R8_M1a5.tsv",
             "K_SOURCE_PLANCALL58_R8_M1a5.tsv"]
    paths = {n: os.path.join(EV, n) for n in names}
    for p in paths.values():
        if os.path.exists(p):
            sys.exit("make_prereg_r8m1a5: exists (U17): " + p)
    with open(paths["PREREG_INPUTS_R8_M1a5.tsv"], "w", encoding="utf-8") as fh:
        fh.write("label\tpath\tsha256\n")
        for lab, rel, s in INPUTS:
            fh.write("%s\t%s\t%s\n" % (lab, rel, s))
    with open(paths["PREREG_STOP_R8_M1a5.tsv"], "w", encoding="utf-8") as fh:
        fh.write("stage\titem\treason\n")
        for st, it, rs in STOPS:
            fh.write("%s\t%s\t%s\n" % (st, it, rs))
    if counts is not None:
        with open(paths["PREREG_COUNTS_R8_M1a5.tsv"], "w", encoding="utf-8") as fh:
            fh.write("group\tr7_f2_points_pass1\tr7_f2_rows_pass2\tf2_two_pass_agreed\n")
            for g, n1, n2, ag in counts:
                fh.write("%s\t%d\t%d\t%d\n" % (g, n1, n2, ag))
    if k_rows is not None:
        with open(paths["K_SOURCE_PLANCALL58_R8_M1a5.tsv"], "w", encoding="utf-8") as fh:
            fh.write("point_id\tk_status\tK\tM\trequest\tstate_pass1\tstate_pass2\n")
            for pid, st, k, m, want, a, b in k_rows:
                fh.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\n" % (pid, st, k, m, want, a, b))
    return paths


if __name__ == "__main__":
    res = main()
    if res is None:
        counts, k_rows = None, None
    else:
        counts, k_rows = res
    paths = write_all(counts, k_rows)
    print("make_prereg_r8m1a5: stop_rows=%d; counts=%s; k_rows=%s" % (
        len(STOPS), "written" if counts is not None else "not written", "written" if k_rows is not None else "not written"))
