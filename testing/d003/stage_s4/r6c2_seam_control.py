#!/usr/bin/env python3
# r6c2_seam_control.py -- P05-S4 R6c2-2 step 2 (new file; U18 (a), ERRATA_6c E6c-7).
#
# Writes REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv BEFORE any seam state run.  One NO-INJECTION control per (library, mode)
# combination of the 25 seam points (18 combinations).  Each control runs the same driver as its seam points, with the
# same FMM_MODE and S4FMM_NG, and S4FMM_INJECT unset (the injector is then inert).  Status INFLUENCED.
#
# Inputs (read here, not edited):
#   REGISTRY_S4_PRE_R6c_SEAM.tsv   the 25 seam points (the (library, mode) set is taken from it)
#   SEAM driver sha256 records:    seam_dbg/DRIVERS_DBG_SEAM.tsv (seamF, fmmret-F) and the r6b-fmmret-F link record
#   R6c2 driver record             seam_dbg/drivers/r6b-fmmret-F/DRIVER_R6b_FMMRET_F.sha256 (written by r6c2_link_fmmret.sh)
# Driver mapping (E6c-3): the seamF points use driver-r6b-seamF; the fmmret-F points use driver-r6b-fmmret-F.
#
# The control of a (library, mode) combination serves every seam point of that combination (points_served column).
# The sum of points_served must equal 25.  The file records sha256 of the file and a UTC timestamp in a sidecar file.
#
# Usage: python3 -I -B testing/d003/stage_s4/r6c2_seam_control.py PREREG_SEAM DRIVERS_DBG_SEAM EVDIR
#   writes EVDIR/REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv (refuses to overwrite), .sha256 and _TIMESTAMP_UTC.txt
import datetime
import hashlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

LIB_DRIVER_SHA = {}  # filled from the sha256 records below


def read_prereg(path):
    header, rows = None, []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            f = line.split("\t")
            if header is None:
                header = f
                continue
            rows.append(dict(zip(header, f)))
    return rows


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def driver_records(drivers_tsv, ev):
    """(library -> (driver path, sha256)) for the STATE drivers (driver-r6b-seamF, driver-r6b-fmmret-F).

    DRIVERS_DBG_SEAM.tsv lists the plain driver-d003 of each library (not the state driver), so it is NOT used for the
    control drivers.  Its only role here is a check that the library build records exist (the file is read, not trusted).
    The sha256 of each state driver is computed from the file (read only)."""
    with open(drivers_tsv, encoding="utf-8") as fh:
        names = {raw.rstrip("\n").split("\t")[0] for raw in fh if raw.strip() and not raw.startswith("#")}
    if not {"seamF", "fmmret-F"} <= names:
        raise SystemExit("REFUSED: DRIVERS_DBG_SEAM.tsv lacks seamF or fmmret-F build records")
    out = {}
    for lib, p in (("seamF", os.path.join(ev, "seam_dbg", "drivers", "r6b-seamF", "driver-r6b-seamF")),
                   ("fmmret-F", os.path.join(ev, "seam_dbg", "drivers", "r6b-fmmret-F", "driver-r6b-fmmret-F"))):
        if not os.path.isfile(p):
            raise SystemExit("REFUSED: state driver missing: %s" % p)
        out[lib] = (p, sha256_file(p))
    return out


def main(argv):
    if len(argv) != 4:
        raise SystemExit("usage: r6c2_seam_control.py PREREG_SEAM DRIVERS_DBG_SEAM EVDIR")
    prereg, drivers_tsv, ev = argv[1:4]
    out = os.path.join(ev, "REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv")
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists, never overwritten (U17): %s" % out)
    pts = read_prereg(prereg)
    if len(pts) != 25:
        raise SystemExit("REFUSED: seam prereg rows %d != 25" % len(pts))
    drv = driver_records(drivers_tsv, ev)
    combos = {}
    for d in pts:
        key = (d["library"], d["mode"])
        combos.setdefault(key, []).append(d["point_id"])
    if len(combos) != 18:
        raise SystemExit("REFUSED: combinations %d != 18" % len(combos))
    served = sum(len(v) for v in combos.values())
    if served != 25:
        raise SystemExit("REFUSED: served points %d != 25" % served)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = []
    lines.append("# REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv -- P05-S4 R6c2 seam controls (U18 (a), ERRATA_6c E6c-7).")
    lines.append("# One no-injection control per (library, mode) combination of the 25 seam points (18 combinations).")
    lines.append("# Written BEFORE any seam state run.  Status INFLUENCED (the seam state run is what this control serves).")
    lines.append("# Control = same driver and same FMM_MODE/S4FMM_NG as its points; S4FMM_INJECT unset; route once.")
    lines.append("# UTC written: %s" % ts)
    cols = ["control_id", "library", "mode", "route", "driver", "driver_sha256", "env", "points_served", "status"]
    lines.append("\t".join(cols))
    for i, (key, pids) in enumerate(sorted(combos.items()), 1):
        lib, mode = key
        path, sha = drv[lib]
        cid = "SC%02d-%s-%s" % (i, lib, mode)
        env = "FMM_MODE=%s;S4FMM_NG=9" % mode
        lines.append("\t".join([cid, lib, mode, "once", os.path.relpath(path, REPO), sha, env, ";".join(sorted(pids)),
                                "INFLUENCED"]))
    lines.append("# summary: combinations %d ; points served %d (must be 25)" % (len(combos), served))
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    digest = sha256_file(out)
    with open(os.path.join(ev, "REGISTRY_S4_PRE_R6c_SEAM_CONTROL.sha256"), "w", encoding="utf-8") as fh:
        fh.write("%s  REGISTRY_S4_PRE_R6c_SEAM_CONTROL.tsv\n" % digest)
    with open(os.path.join(ev, "REGISTRY_S4_PRE_R6c_SEAM_CONTROL_TIMESTAMP_UTC.txt"), "w", encoding="utf-8") as fh:
        fh.write(ts + "\n")
    print("control: combinations=%d served=%d sha256=%s -> %s" % (len(combos), served, digest, out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
