# callsite_audit_r8m2a2_r3.py -- P05-S4 R8 M2a2 R3 (brief 4.1 / 4.7 section 4): static call-site and relocation audit of the
# hooks and --wrap symbols used by the R3 dual injector and the R4 dual drivers.  Read-only tools only (nm, objdump -dr,
# readelf); nothing is executed.  Output: $EV/CALLSITE_AUDIT_R8_M2a2_R3.tsv.  Refuses to overwrite (U17).
# Conclusions are limited to "static link relation holds" (STATIC_LINK_HOLDS) or "does not hold"; dynamic reachability is
# left to M2b.
# Usage: sh testing/d003/safe_run.sh p05-s4r8/m2a2 -- python3 -I -B testing/d003/stage_s4/callsite_audit_r8m2a2_r3.py
import os
import re
import subprocess
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a2")
D4 = os.path.join(EV, "build_R4")
# The first version wrote CALLSITE_AUDIT_R8_M2a2_R3.tsv (unsuffixed); its objdump -dr parse missed the relocation records,
# so it is kept as a record and superseded by this _R2 table.
OUT = os.path.join(EV, "CALLSITE_AUDIT_R8_M2a2_R3_R2.tsv")

WRAP_SYMS = [
    ("malloc", "__wrap_malloc", "__real_malloc"),
    ("_Z9S4_mallocm", "__wrap__Z9S4_mallocm", "__real__Z9S4_mallocm"),
    ("_Z15fft_plan_dft_2dPiPSt7complexIdES2_i", "__wrap__Z15fft_plan_dft_2dPiPSt7complexIdES2_i", "__real__Z15fft_plan_dft_2dPiPSt7complexIdES2_i"),
    ("_Z13fft_plan_execP12tag_fft_plan", "__wrap__Z13fft_plan_execP12tag_fft_plan", "__real__Z13fft_plan_execP12tag_fft_plan"),
]
HOOKS = [
    "S4_TEST_LINEARSOLVE_NULLINFO2_AFTER",
    "S4_TEST_LINEARSOLVE_NULLINFO2BUF_AFTER",
    "S4_TEST_LINEARSOLVE_NULLINFO_AFTER",
    "S4_TEST_LINEARSOLVE_AFTER",
    "S4_TEST_FMMRET_AFTER",
    "S4_TEST_FMMBUF_AFTER",
    "S4_TEST_ALLOC_HOOK",
    "S4_TEST_KOTTKE_HOOK",
    "S4_TEST_ADDFIELD_AFTER",
]
DRIVERS = ["dual-F3-dbg-R4", "layers-dual-F3-dbg-R4"]
INJ_OBJ = os.path.join(D4, "inject_r8m2a2_dual_R3.o")


def run(args):
    r = subprocess.run(args, cwd=REPO, capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr


def main():
    if os.path.exists(OUT):
        print("callsite_audit_r8m2a2_r3: REFUSED exists (U17): %s" % OUT)
        return 2
    rows = []
    # (a) archive / object references: the injector object's undefined symbols (U)
    rc, out, err = run(["nm", "-u", INJ_OBJ])
    undef = set()
    for line in out.splitlines():
        parts = line.split()
        if parts:
            undef.add(parts[-1])
    # (b) relocation records in the injector object (objdump -r: "offset TYPE symbol-addend"; R_X86_64_PLT32 call sites)
    rc2, out2, err2 = run(["objdump", "-r", INJ_OBJ])
    rel = {}
    for line in out2.splitlines():
        m = re.match(r"^([0-9a-f]+)\s+R_X86_64_(PLT32|PC32|64)\s+(\S+?)(?:[-+]0x[0-9a-f]+)?$", line.strip())
        if m:
            rel.setdefault(m.group(3), []).append(m.group(1))
    # injector object: the wrap entry points are DEFINED (T) there; the real functions are UNDEFINED (U) references
    rc4, out4, err4 = run(["nm", INJ_OBJ])
    inj_defined = {}
    for line in out4.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[1] in ("T", "t", "W", "w"):
            inj_defined[parts[2]] = parts[1]
    for (sym, wrap, real) in WRAP_SYMS:
        st_w = inj_defined.get(wrap)
        rows.append((wrap, "defined_in_injector_object", st_w if st_w else "ABSENT", "-", "nm_T_or_W",
                     "STATIC_LINK_HOLDS" if st_w else "NOT_HOLDS"))
        ref_real = real in undef
        sites = rel.get(real, [])
        rows.append((real, "undefined_ref_in_injector_object", "U" if ref_real else "ABSENT",
                     ",".join(sites) if sites else "-", "objdump_-dr_relocation_offsets",
                     "STATIC_LINK_HOLDS" if (ref_real and sites) else "NOT_HOLDS"))
    # (c) final drivers: the --wrap symbols and the hook symbols are DEFINED (T) in the linked executable
    for drv in DRIVERS:
        exe = os.path.join(D4, drv)
        rc3, out3, err3 = run(["nm", exe])
        defined = {}
        for line in out3.splitlines():
            parts = line.split()
            if len(parts) == 3 and parts[1] in ("T", "t", "W", "w"):
                defined[parts[2]] = parts[1]
        for (sym, wrap, real) in WRAP_SYMS:
            st = defined.get(wrap)
            rows.append((wrap, "defined_in_final_driver:" + drv, st if st else "ABSENT", "-", "nm_T_or_W",
                         "STATIC_LINK_HOLDS" if st else "NOT_HOLDS"))
        for hook in HOOKS:
            st = defined.get(hook)
            # a hook is referenced by a driver's seam only when the seam is built in; the R4 dual drivers are built on F3-dbg,
            # which has no seam macros, so an absent hook is recorded as HOOK_NOT_IN_THIS_BUILD (not a failure)
            if st:
                res = "STATIC_LINK_HOLDS"
            else:
                res = "HOOK_NOT_IN_THIS_BUILD"
            rows.append((hook, "defined_in_final_driver:" + drv, st if st else "ABSENT", "-", "nm_T_or_W", res))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("# CALLSITE_AUDIT_R8_M2a2_R3 -- static link relations only; dynamic reachability is M2b (no driver run)\n")
        f.write("# columns: symbol	role	state	relocation_sites_in_object	source	conclusion\n")
        for r in rows:
            f.write("\t".join(str(x) for x in r) + "\n")
    print("callsite_audit_r8m2a2_r3: wrote %s rows=%d" % (OUT, len(rows)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
