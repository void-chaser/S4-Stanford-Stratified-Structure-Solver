#!/usr/bin/env python3
# index_derivation_r8m2a2_R2.py -- P05-S4 R8 M2a2 CONT1 section 6: index derivation, version R2.
# Replaces (does not overwrite) INDEX_DERIVATION_R8_M2a2.tsv (R1, kept, SUPERSEDED).
# Every row is derived from files: source line numbers are located by search at run time, and the M1 hit
# evidence is read from the M1 run.out files.  Nothing is copied from the R1 table.
# Output: $EV/INDEX_DERIVATION_R8_M2a2_R2B.tsv  (R2B: the first R2 run wrote INDEX_DERIVATION_R8_M2a2_R2.tsv and was
#         found to assert FIRST_WINDOW_MALLOC_IN_CALL1 without a call-level source; that file is kept, SUPERSEDED by R2B)
# Columns: point_id, item, driver, env, inj_call, retry_call, k_before, k_fail, k_preretry, k_retry, target_layer,
#          nth_or_k, nth2_or_k2, layer_of_failure, source_basis, win_evidence, m2b_hit_check, status
import os
import re
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
OUT = os.path.join(EV, "INDEX_DERIVATION_R8_M2a2_R2B.tsv")
M1 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1b1", "runs", "ADDITIONS_22")
T_F3 = os.path.join(EV, "tree_F3", "S4")
ST4 = os.path.join(REPO, "testing", "d003", "stage_s4")
ST3C2 = os.path.join(REPO, "testing", "d003", "stage_s3r4c2")
ST3C3 = os.path.join(REPO, "testing", "d003", "stage_s3r4c3")
ST3R4 = os.path.join(REPO, "testing", "d003", "stage_s3r4")


def read_lines(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read().split("\n")


def find_line(path, pattern):
    """1-based line number of the first line matching regex, or 0."""
    rx = re.compile(pattern)
    for i, l in enumerate(read_lines(path), 1):
        if rx.search(l):
            return i
    return 0


def find_all(path, pattern):
    rx = re.compile(pattern)
    return [i for i, l in enumerate(read_lines(path), 1) if rx.search(l)]


def rel(p):
    return os.path.relpath(p, REPO)


def win_evidence(k_target, pname, mode_label):
    """Return (status, text) for the M1 window-malloc evidence of a poly win:k point.
    pname is the M1 point name (ADD22-B-<row>-F3).  The line of 'WIN_MALLOC k=<k>' and the matching 'HIT' line are
    read from the M1 run.out (pass1), with the positions of the 'RC first' and 'RC retry' markers."""
    if not os.path.isdir(M1):
        return "UNRESOLVED_INDEX", "M1 run directory missing"
    run = os.path.join(M1, pname, "pass1", "run.out")
    if not os.path.exists(run):
        return "UNRESOLVED_INDEX", "run.out missing for " + pname
    k_line = find_line(run, r"S3R4C3_WIN_MALLOC k=%d n=" % k_target)
    hit_line = find_line(run, r"S4FMM HIT real malloc failure: S3R4C3 poly window malloc %d," % k_target)
    rc_first = find_line(run, r"^RC first ")
    rc_retry = find_line(run, r"^RC retry ")
    if k_line == 0 or hit_line == 0:
        return "UNRESOLVED_INDEX", "no window malloc %d hit line in %s" % (k_target, pname)
    # Order inside run.out: stdout is written first (RC lines), stderr window lines are appended after the
    # driver stdout.  run.out is a concatenation, so the line order does NOT give call order.  Therefore the
    # call number of the hit cannot be read from run.out alone.
    return "UNRESOLVED_INDEX", ("%s: hit line %d (window k=%d), RC first at %d, RC retry at %d; run.out is a "
                                "concatenation (stdout then stderr), no per-call window count; call of the hit not "
                                "fixed by M1 evidence" % (pname, hit_line, k_target, rc_first, rc_retry))


def main():
    if os.path.exists(OUT):
        print("index_derivation_r8m2a2_R2: REFUSED exists (U17)")
        return 2
    rows = []
    # ---- source locations (all searched at run time) ----
    dr6b = os.path.join(ST4, "driver_r6b_state.cpp")
    r6b_k1 = find_line(dr6b, r"k_fail|call1 \(the injection")
    poly_drv = os.path.join(ST3C2, "driver_s3r4c2_poly.cpp")
    poly_call1 = find_line(poly_drv, r"S4_Simulation_GetFieldPlane")
    poly_snap = find_all(poly_drv, r"r6_snap\(S, [0-9]")
    poly_inj = os.path.join(ST3C3, "inject_s3r4c3_poly.cpp")
    cnt_line = find_line(poly_inj, r"count_window\+\+")
    no_reset = find_line(poly_inj, r"NOT reset on entry|cumulative")
    init_inj = os.path.join(ST3R4, "inject_s3r4_init.cpp")
    init_win = find_line(init_inj, r"win|window")
    init_out = find_line(init_inj, r"init")
    r6b_snap = find_all(dr6b, r"r6_snap\(S, [0-9]")
    dual_inj = os.path.join(ST4, "inject_r8m2a2_dual_R2.cpp")
    layers_drv = os.path.join(ST4, "driver_r8m2a2_layers_R2.cpp")
    layout_pp2 = find_line(layers_drv, r'"PP2"')
    fft_src = os.path.join(T_F3, "fmm", "fmm_FFT.cpp")
    fft_work = find_line(fft_src, r"S4_malloc\(sizeof\(std::complex<double>\)\*\(6\*ng2\)\)")
    fft_disc = find_line(fft_src, r"discval = \(double\*\)S4_malloc|S4_malloc\(sizeof\(double\)\*\(L->pattern\.nshapes\+1\)\)")
    s4cpp = os.path.join(T_F3, "S4.cpp")
    clm_nshapes = find_line(s4cpp, r"if\(0 == L->pattern\.nshapes\)")
    cls_loop = find_line(s4cpp, r"if\(NULL == SL->modes && SL->copy < 0\)")
    cls_ret = find_line(s4cpp, r"return modes_error;")

    # ---- init rows (inj_call 1; win is inside the window, init is outside) ----
    for name, env, win in [
        ("M2-01-01-F3", "FMM_MODE=closed2d;S4FMM_NG=1;S4FMM_INJECT=win:1", 1),
        ("M2-01-02-F3", "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=win:1", 1),
        ("M2-01-03-F3", "FMM_MODE=kottke;S4FMM_NG=5;S4FMM_INJECT=win:1", 1),
    ]:
        rows.append([name, "init-win", "init-F3-dbg", env, "1", "2", "0", "1", "2", "3", "1", "-", "-", "1",
                     "%s:%d (snapshot k=1 after call1, k_fail index); %s:%d (window count inside window); %s:%d (RC first marker)" %
                     (rel(dr6b), r6b_snap[1] if len(r6b_snap) > 1 else 0, rel(init_inj), init_win, rel(dr6b), find_line(dr6b, r"RC first")),
                     "win:%d: inside call1 only if the first window malloc of the process is in call1; the M1 run.out (concatenation) cannot fix the call; flagged UNRESOLVED_INDEX below" % win,
                     "HIT line of 'S3R4C3 poly window' k=1 in init-F3 run; I1 layer 1", "PENDING_PREREG"])
    for name, env in [
        ("M2-01-04-F3", "FMM_MODE=closed2d;S4FMM_NG=1;S4FMM_INJECT=init:7"),
        ("M2-01-05-F3", "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=init:8"),
        ("M2-01-06-F3", "FMM_MODE=kottke;S4FMM_NG=5;S4FMM_INJECT=init:8"),
    ]:
        rows.append([name, "init-malloc", "init-F3-dbg", env, "1", "2", "0", "1", "2", "3", "1", "-", "-", "1",
                     "%s:%d (k_fail/k_preretry/k_retry; inj_call 1) ; %s:%d (init counted outside the window)" %
                     (rel(dr6b), r6b_k1, rel(init_inj), init_out),
                     "init counts malloc outside the window (not reset per call); inj_call 1 fails in call1",
                     "init counter hit line; I1 layer 1", "PENDING_PREREG"])

    # ---- poly rows (driver call1/2/3 and cumulative window counter) ----
    poly_rows = [
        ("M2-01-11-F3", "FMM_MODE=fft;S4FMM_NG=1;S4FMM_INJECT=win:1", "fft", 1, 1, "ADD22-B-13-F3"),
        ("M2-01-12-F3", "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=win:1", "fft", 5, 1, "ADD22-B-13-F3"),
        ("M2-01-13-F3", "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=win:64", "fft", 5, 64, "ADD22-B-13-F3"),
        ("M2-01-14-F3", "FMM_MODE=fft;S4FMM_NG=9;S4FMM_INJECT=win:1", "fft", 9, 1, "ADD22-B-15-F3"),
        ("M2-01-15-F3", "FMM_MODE=fft;S4FMM_NG=9;S4FMM_INJECT=win:64", "fft", 9, 64, "ADD22-B-15-F3"),
        ("M2-01-16-F3", "FMM_MODE=kottke;S4FMM_NG=1;S4FMM_INJECT=win:1", "kottke", 1, 1, "ADD22-B-17-F3"),
        ("M2-01-17-F3", "FMM_MODE=kottke;S4FMM_NG=1;S4FMM_INJECT=win:64", "kottke", 1, 64, "ADD22-B-17-F3"),
        ("M2-01-18-F3", "FMM_MODE=kottke;S4FMM_NG=5;S4FMM_INJECT=win:1", "kottke", 5, 1, "ADD22-B-19-F3"),
        ("M2-01-19-F3", "FMM_MODE=kottke;S4FMM_NG=5;S4FMM_INJECT=win:64", "kottke", 5, 64, "ADD22-B-19-F3"),
        ("M2-01-20-F3", "FMM_MODE=kottke;S4FMM_NG=9;S4FMM_INJECT=win:1", "kottke", 9, 1, "ADD22-B-21-F3"),
        ("M2-01-21-F3", "FMM_MODE=kottke;S4FMM_NG=9;S4FMM_INJECT=win:64", "kottke", 9, 64, "ADD22-B-21-F3"),
    ]
    for name, env, mode, ng, k, addr in poly_rows:
        # The call that holds the M-th window malloc of the process is NOT fixed by the M1 evidence for any M,
        # including M=1: run.out is a concatenation of stdout and stderr, so its line order is not call order.
        # Therefore every poly win:M row is UNRESOLVED_INDEX unless win_evidence can fix the call (it cannot).
        status_w, text_w = win_evidence(k, addr, mode)
        kb, kf, kp, kr, rc = 0, 1, 2, 3, 2
        rows.append([name, "poly-win", "polyinj-F3-dbg", env, "1", str(rc), str(kb), str(kf), str(kp), str(kr), "1", "-", "-",
                     "1", "%s:%d (poly driver call1 GetFieldPlane); %s:%d (cumulative window counter, not reset); %s:%d (window wrap)" %
                     (rel(poly_drv), poly_call1, rel(poly_inj), no_reset, rel(poly_inj), cnt_line),
                     "%s; %s" % (status_w, text_w),
                     "HIT line 'S4FMM HIT real malloc failure: S3R4C3 poly window malloc %d' and RC first" % k,
                     status_w])

    # ---- CTRL rows ----
    for name, env, drv in [
        ("M2-01-CTRL-01-F3", "FMM_MODE=closed2d;S4FMM_NG=1", "init-F3-dbg"),
        ("M2-01-CTRL-02-F3", "FMM_MODE=fft;S4FMM_NG=5", "init-F3-dbg"),
        ("M2-01-CTRL-03-F3", "FMM_MODE=kottke;S4FMM_NG=5", "init-F3-dbg"),
        ("M2-01-CTRL-11-F3", "FMM_MODE=fft;S4FMM_NG=1", "polyinj-F3-dbg"),
        ("M2-01-CTRL-12-F3", "FMM_MODE=fft;S4FMM_NG=5", "polyinj-F3-dbg"),
        ("M2-01-CTRL-14-F3", "FMM_MODE=fft;S4FMM_NG=9", "polyinj-F3-dbg"),
        ("M2-01-CTRL-16-F3", "FMM_MODE=kottke;S4FMM_NG=1", "polyinj-F3-dbg"),
        ("M2-01-CTRL-18-F3", "FMM_MODE=kottke;S4FMM_NG=5", "polyinj-F3-dbg"),
        ("M2-01-CTRL-20-F3", "FMM_MODE=kottke;S4FMM_NG=9", "polyinj-F3-dbg"),
    ]:
        rows.append([name, "control", drv, env, "-", "-", "0", "-", "-", "-", "1", "-", "-", "-",
                     "no injection; control group", "-", "CONTROL_OK expected", "CONTROL"])

    # ---- M2-04 dual ----
    # (a) same layer: call1 fails at NTH=1 (layer 1, first malloc of the plan of layer 1);
    #     call2 fails at NTH2=2 in the same layer (layer 1, second malloc); call3 recovers.
    rows.append(["M2-04-01-F3", "dual-same-layer", "dual-F3-dbg",
                 "FMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=s4malloc;S4FMM_NTH=1;S4FMM_INJECT2=s4malloc;S4FMM_NTH2=2",
                 "1", "2", "0", "1", "2", "3", "1", "1", "2", "1",
                 "%s:%d (t2_malloc_seen counts the process-wide S4_malloc stream; target 2 index advances even when target 1 fails); call1 fails at stream 1 (work of layer 1), call2 recomputes layer 1 and fails at stream 2 (discval of layer 1); NTH2=2 is the stream index, not a layer index" %
                 (rel(dual_inj), find_line(dual_inj, r"t2_malloc_seen") or 0),
                 "two failures in one layer (a)", "HIT dual target2 real S4_malloc failure line; layer 1", "PENDING_PREREG"])
    # (b) two layers: call1 fails on layer 1 (NTH=1); call2 recomputes layer 1 (#2, #3 succeed), then layer 2 (#4) fails;
    #     call3 computes layer 2 only (#5, #6) and recovers.  NTH2 = 4.
    rows.append(["M2-04-02-F3", "dual-two-layer-PP1", "layers-dual-F3-dbg",
                 "FMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=PP1;S4FMM_INJECT=s4malloc;S4FMM_NTH=1;S4FMM_INJECT2=s4malloc;S4FMM_NTH2=4",
                 "1", "2", "0", "1", "2", "3", "1", "1", "4", "2",
                 "%s; %s:%d (ComputeLayerSolution walks layers in order and returns at the first failure)" %
                 (rel(dual_inj), rel(os.path.join(T_F3, "S4.cpp")), cls_loop),
                 "call2 recomputes layer 1 (#2,#3), then fails at layer 2 (#4): NTH2=4 (correction of R1 NTH2=2)",
                 "HIT dual target2 layer 2; call2 rc non-zero", "CORRECTED_FROM_R1"])

    # ---- M2-05 layers (CLM stream of the FMM epsilon/discval mallocs per pattern layer) ----
    # Each pattern layer enters FMM and performs 2 S4_malloc calls (work at fmm_FFT.cpp, discval).  A uniform layer
    # does not enter FMM (nshapes == 0 branch at S4.cpp).
    for name, layout, nth, target, note in [
        ("M2-05-P0-F3", "P0", 1, 0, "pattern on layer 0; first pattern malloc is at layer 0"),
        ("M2-05-P2-F3", "P2", 1, 2, "pattern on layer 2; first pattern malloc is at layer 2"),
        ("M2-05-PP1-F3", "PP1", 1, 1, "two patterns; first pattern layer is layer 1 (fails at NTH=1)"),
        ("M2-05-PP2-F3", "PP2", 3, 2, "two patterns; NTH=3 is the discval of layer 1 (work, discval, then layer 2 work); fails at layer 2"),
    ]:
        rows.append([name, "layers", "layers-F3-dbg",
                     "FMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=%s;S4FMM_INJECT=s4malloc;S4FMM_NTH=%d" % (layout, nth),
                     "1", "2", "0", "1", "2", "3", str(target), str(nth), "-", str(target),
                     "%s:%d (work), %s:%d (discval) per pattern layer; %s:%d (ComputeLayerSolution order)" %
                     (rel(fft_src), fft_work, rel(fft_src), fft_disc, rel(s4cpp), cls_loop) + "; " + note,
                     "layer order and per-layer malloc count (2 per pattern layer)",
                     "HIT s4malloc layer %d (NTH=%d)" % (target, nth),
                     "CORRECTED_FROM_R1" if name == "M2-05-PP2-F3" else "INFLUENCED"])

    # ---- M2-06 ----
    rows.append(["M2-06-01-F3", "nan", "nan-F3",
                 "FMM_MODE=tensor;S4FMM_NG=5;S4FMM_INJECT=linearsolve_nanbuf:244:1", "1", "-", "0", "1", "-", "-", "1",
                 "-", "-", "1", "%s:244-245 [源码]" % rel(os.path.join(T_F3, "fmm", "fmm_closed.cpp")),
                 "NaN written to the output buffer after a zero solve_info (K-1 path)", "HIT linearsolve_nanbuf line", "PENDING_PREREG"])

    # ---- M2-09 ----
    rows.append(["M2-09-01-F3", "ctrl-seam", "seam-fmmret-F3", "FMM_MODE=fft;S4FMM_NG=9", "-", "-", "0", "-", "-", "-", "1",
                 "-", "-", "-", "DRIVERS_R8.tsv (seam-fmmret-F3); no injection", "-", "CONTROL_OK", "CONTROL"])
    rows.append(["M2-09-01-F2", "ctrl-seam", "seam-fmmret-F2", "FMM_MODE=fft;S4FMM_NG=9", "-", "-", "0", "-", "-", "-", "1",
                 "-", "-", "-", "DRIVERS_R7_SEAM.tsv (seam-fmmret-F2); no injection", "-", "CONTROL_OK", "CONTROL"])

    # ---- M2-10 ----
    rows.append(["M2-10-01-B", "gdb-baseline", "r6bstate-B-dbg", "FMM_MODE=vl;S4FMM_NG=1", "1", "-", "0", "1", "-", "-", "1",
                 "-", "-", "-", "returns at tree_B/S4/S4.cpp:2362, 2416, 2432 (every 'return 20;' in CLM)", "-", "BASELINE_ONLY",
                 "PENDING_PREREG"])

    with open(OUT, "x", encoding="utf-8") as fh:
        fh.write("# INDEX_DERIVATION_R8_M2a2_R2 -- P05-S4 R8 M2a2 CONT1 section 6 (SUPERSEDES INDEX_DERIVATION_R8_M2a2.tsv; that file is kept)\n")
        fh.write("\t".join(["point_id", "item", "driver", "env", "inj_call", "retry_call", "k_before", "k_fail", "k_preretry",
                            "k_retry", "target_layer", "nth_or_k", "nth2_or_k2", "layer_of_failure", "source_basis",
                            "win_evidence", "m2b_hit_check", "status"]) + "\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
        unresolved = sum(1 for r in rows if r[-1] == "UNRESOLVED_INDEX" or "UNRESOLVED_INDEX" in r[15])
        fh.write("# TOTAL_ROWS=%d UNRESOLVED_INDEX=%d\n" % (len(rows), unresolved))
    print("index_derivation_r8m2a2_R2: rows=%d" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
