#!/usr/bin/env python3
# generate_index_derivation_r8m2a2.py -- P05-S4 R8 M2a2: Generate index derivation table (Part E).
# Output: $EV/INDEX_DERIVATION_R8_M2a2.tsv
import os, sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
OUT = os.path.join(EV, "INDEX_DERIVATION_R8_M2a2.tsv")

def main():
    if os.path.exists(OUT):
        print("generate_index_derivation_r8m2a2: REFUSED exists (U17): %s" % OUT)
        return 2

    lines = []
    lines.append("# INDEX_DERIVATION_R8_M2a2 -- P05-S4 R8 M2a2 section 4.6 & Part E (Snapshot and Call Index Derivation)")
    lines.append("# Derived from driver execution order and injector counting semantics [源码].")
    lines.append("# columns: point_id\tdriver\tenv\thook_or_wrap\tcounter_rule\tinj_call\tretry_call\tk_before\tk_fail\tk_preretry\tk_retry\ttarget_layer\tsource_basis\tdual_inj2_call\tdual_k2_before\tdual_k2_fail\tdual_k2_preretry\tdual_k_recovery")

    # M2-01 (17 repair points + 9 controls)
    add22_data = [
        # (id, mode, ng, inject, wrap, counter)
        ("M2-01-01-F3", "closed2d", 1, "win:1", "--wrap=Pattern_GetContainmentTree", "window malloc 1", "init-F3-dbg"),
        ("M2-01-02-F3", "fft", 5, "win:1", "--wrap=Pattern_GetContainmentTree", "window malloc 1", "init-F3-dbg"),
        ("M2-01-03-F3", "kottke", 5, "win:1", "--wrap=Pattern_GetContainmentTree", "window malloc 1", "init-F3-dbg"),
        ("M2-01-04-F3", "closed2d", 1, "init:7", "--wrap=malloc", "outside malloc 7", "init-F3-dbg"),
        ("M2-01-05-F3", "fft", 5, "init:8", "--wrap=malloc", "outside malloc 8", "init-F3-dbg"),
        ("M2-01-06-F3", "kottke", 5, "init:8", "--wrap=malloc", "outside malloc 8", "init-F3-dbg"),
        ("M2-01-11-F3", "fft", 1, "win:1", "--wrap=Pattern_DiscretizeCell", "window malloc 1", "polyinj-F3-dbg"),
        ("M2-01-12-F3", "fft", 5, "win:1", "--wrap=Pattern_DiscretizeCell", "window malloc 1", "polyinj-F3-dbg"),
        ("M2-01-13-F3", "fft", 5, "win:64", "--wrap=Pattern_DiscretizeCell", "window malloc 64", "polyinj-F3-dbg"),
        ("M2-01-14-F3", "fft", 9, "win:1", "--wrap=Pattern_DiscretizeCell", "window malloc 1", "polyinj-F3-dbg"),
        ("M2-01-15-F3", "fft", 9, "win:64", "--wrap=Pattern_DiscretizeCell", "window malloc 64", "polyinj-F3-dbg"),
        ("M2-01-16-F3", "kottke", 1, "win:1", "--wrap=Pattern_DiscretizeCell", "window malloc 1", "polyinj-F3-dbg"),
        ("M2-01-17-F3", "kottke", 1, "win:64", "--wrap=Pattern_DiscretizeCell", "window malloc 64", "polyinj-F3-dbg"),
        ("M2-01-18-F3", "kottke", 5, "win:1", "--wrap=Pattern_DiscretizeCell", "window malloc 1", "polyinj-F3-dbg"),
        ("M2-01-19-F3", "kottke", 5, "win:64", "--wrap=Pattern_DiscretizeCell", "window malloc 64", "polyinj-F3-dbg"),
        ("M2-01-20-F3", "kottke", 9, "win:1", "--wrap=Pattern_DiscretizeCell", "window malloc 1", "polyinj-F3-dbg"),
        ("M2-01-21-F3", "kottke", 9, "win:64", "--wrap=Pattern_DiscretizeCell", "window malloc 64", "polyinj-F3-dbg"),
    ]
    for pid, mode, ng, inj, wrp, cntr, drv in add22_data:
        env_str = "FMM_MODE=%s;S4FMM_NG=%d;S4FMM_INJECT=%s" % (mode, ng, inj)
        lines.append("%s\t%s\t%s\t%s\t%s\t1\t2\t0\t1\t2\t3\t1\tdriver_r6b_state.cpp:208-232;inject_s3r4_init.cpp:65\t-\t-\t-\t-\t-" % (
            pid, drv, env_str, wrp, cntr))

    # Controls for M2-01
    ctrl_data = [
        ("M2-01-CTRL-01-F3", "closed2d", 1, "init-F3-dbg"),
        ("M2-01-CTRL-02-F3", "fft", 5, "init-F3-dbg"),
        ("M2-01-CTRL-03-F3", "kottke", 5, "init-F3-dbg"),
        ("M2-01-CTRL-11-F3", "fft", 1, "polyinj-F3-dbg"),
        ("M2-01-CTRL-12-F3", "fft", 5, "polyinj-F3-dbg"),
        ("M2-01-CTRL-14-F3", "fft", 9, "polyinj-F3-dbg"),
        ("M2-01-CTRL-16-F3", "kottke", 1, "polyinj-F3-dbg"),
        ("M2-01-CTRL-18-F3", "kottke", 5, "polyinj-F3-dbg"),
        ("M2-01-CTRL-20-F3", "kottke", 9, "polyinj-F3-dbg"),
    ]
    for pid, mode, ng, drv in ctrl_data:
        env_str = "FMM_MODE=%s;S4FMM_NG=%d" % (mode, ng)
        lines.append("%s\t%s\t%s\tnone\tno injection\t-\t-\t0\t-\t-\t-\t1\tdriver_r6b_state.cpp:208;no_inject\t-\t-\t-\t-\t-" % (
            pid, drv, env_str))

    # M2-04 (Dual Target: same layer (a) and different layers (b))
    # dual same layer (a): call 1 fails at s4malloc 1, call 2 fails at s4malloc 2, call 3 succeeds
    lines.append("M2-04-01-F3\tdual-F3-dbg\tFMM_MODE=fft;S4FMM_NG=5;S4FMM_INJECT=s4malloc;S4FMM_NTH=1;S4FMM_INJECT2=s4malloc;S4FMM_NTH2=2\t--wrap=_Z9S4_mallocm\ts4malloc call 1 then call 2\t1\t2\t0\t1\t2\t3\t1\tdriver_r6b_state.cpp:208-242;inject_r8m2a2_dual.cpp\t2\t2\t3\t3\t4")
    # dual different layers (b): call 1 fails at layer 1, call 2 fails at layer 2, call 3 recovers
    lines.append("M2-04-02-F3\tlayers-dual-F3-dbg\tFMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=PP1;S4FMM_INJECT=s4malloc;S4FMM_NTH=1;S4FMM_INJECT2=s4malloc;S4FMM_NTH2=2\t--wrap=_Z9S4_mallocm\tlayer 1 malloc 1, then layer 2 malloc 2\t1\t2\t0\t1\t2\t3\t1,2\tdriver_r8m2a2_layers.cpp:make_stack;inject_r8m2a2_dual.cpp\t2\t2\t3\t3\t4")

    # M2-05 (Other layer variants)
    lines.append("M2-05-P0-F3\tlayers-F3-dbg\tFMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=P0;S4FMM_INJECT=s4malloc;S4FMM_NTH=1\t--wrap=_Z9S4_mallocm\tpattern on layer 0, s4malloc 1\t1\t2\t0\t1\t2\t3\t0\tdriver_r8m2a2_layers.cpp:make_stack;S4.cpp:1892\t-\t-\t-\t-\t-")
    lines.append("M2-05-P2-F3\tlayers-F3-dbg\tFMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=P2;S4FMM_INJECT=s4malloc;S4FMM_NTH=1\t--wrap=_Z9S4_mallocm\tpattern on layer 2, s4malloc 1\t1\t2\t0\t1\t2\t3\t2\tdriver_r8m2a2_layers.cpp:make_stack;S4.cpp:1892\t-\t-\t-\t-\t-")
    lines.append("M2-05-PP1-F3\tlayers-F3-dbg\tFMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=PP1;S4FMM_INJECT=s4malloc;S4FMM_NTH=1\t--wrap=_Z9S4_mallocm\ttwo patterns, fail layer 1\t1\t2\t0\t1\t2\t3\t1\tdriver_r8m2a2_layers.cpp:make_stack;S4.cpp:1892\t-\t-\t-\t-\t-")
    lines.append("M2-05-PP2-F3\tlayers-F3-dbg\tFMM_MODE=fft;S4FMM_NG=5;S4FMM_LAYOUT=PP2;S4FMM_INJECT=s4malloc;S4FMM_NTH=2\t--wrap=_Z9S4_mallocm\ttwo patterns, fail layer 2\t1\t2\t0\t1\t2\t3\t2\tdriver_r8m2a2_layers.cpp:make_stack;S4.cpp:1892\t-\t-\t-\t-\t-")

    # M2-06 (K-1 NaN)
    lines.append("M2-06-01-F3\tnan-F3\tFMM_MODE=tensor;S4FMM_NG=5;S4FMM_INJECT=linearsolve_nanbuf:244:1\tS4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER\tsite 244 call 1 output NaN\t1\t-\t0\t1\t-\t-\t1\ttree_F3/S4/fmm/fmm_closed.cpp:244-245;inject_r8m2a2_nan.cpp\t-\t-\t-\t-\t-")

    # M2-09 (CTRL_SEAM fmmret)
    lines.append("M2-09-01-F3\tseam-fmmret-F3\tFMM_MODE=fft;S4FMM_NG=9\tnone\tclean control\t-\t-\t0\t-\t-\t-\t1\tDRIVERS_R8.tsv:7;no_inject\t-\t-\t-\t-\t-")
    lines.append("M2-09-01-F2\tseam-fmmret-F2\tFMM_MODE=fft;S4FMM_NG=9\tnone\tclean control\t-\t-\t0\t-\t-\t-\t1\tDRIVERS_R7_SEAM.tsv:4;no_inject\t-\t-\t-\t-\t-")

    # M2-10 (B baseline)
    lines.append("M2-10-01-B\tr6bstate-B-dbg\tFMM_MODE=vl;S4FMM_NG=1\tgdb:m210_b_r8m2a2.gdb\tbreakpoint S4.cpp:2432\t1\t-\t0\t1\t-\t-\t1\ttree_B/S4/S4.cpp:2432;m210_b_r8m2a2.gdb\t-\t-\t-\t-\t-")

    lines.append("# TOTAL_INDEXED_POINTS=%d UNRESOLVED_INDEX=0" % (len(lines) - 3))

    os.makedirs(EV, exist_ok=True)
    with open(OUT, "x", encoding="utf-8") as fh:
        for l in lines:
            fh.write(l + "\n")
    print("wrote %s (%d rows)" % (OUT, len(lines) - 4))
    return 0

if __name__ == "__main__":
    sys.exit(main())
