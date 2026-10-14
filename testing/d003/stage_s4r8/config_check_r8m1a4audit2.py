#!/usr/bin/env python3
"""P05-S4 R8 M1a CONT3a audit part 2 (r8m1a4audit2), section 3 step 2: independent per-unit configuration check.  New file.

Read only.  Reads the 198-unit table, the 198-run table, the 198 raw unit directories, the driver registries and the
seam driver tables, and checks for every unit (unit = one gdb run of one driver with one configuration):
  C1  the unit exists in the run table once, with the same pair_id, run_tree, driver_tag, driver_sha256, cmd_env;
  C2  the unit's driver_sha256 equals the registry record of its driver tag (DRIVERS_R8_M1a or the F2 reuse table);
  C3  the unit's driver_path equals the registry path and the file's sha256 equals driver_sha256 (file read now);
  C4  argv equals the historical runner GRID argv (pattern both 4 3) from counted_families_r8m1a4.py and run_m2_r7 usage;
  C5  cmd_env, after parsing, contains FMM_MODE and S4FMM_NG equal to the unit's mode and NG, and S4FMM_TWICE=slab only
      when twice_env == slab (the runner builds its environment from these fields, so the record must agree);
  C6  the dedup key (driver identity, run_tree, mode, NG, twice_env, environment, argv) is unique over the 198 units;
  C7  for each F2/F3 pair the two units differ only in run_tree and driver identity (same mode, NG, twice_env, env, argv);
  C8  DRIVER_TAG_AUDIT NO_DRIVER_PATH_COLUMN rows (8, DRIVERS_R7_SEAM and DRIVER_R6B_SEAM_R7 families): the driver is
      resolved from the library directory's sibling driver under drivers_r7/ (printf column order read from the
      generators; no header), the registry hash is taken from the printf column for the driver, and the file's sha256
      is computed.  Rows that cannot be resolved are EVIDENCE_INSUFFICIENT.
  C9  the per-unit raw directory exists and holds events.tsv, summary.json, gdb.stdout.txt, gdb.stderr.txt.

Usage (through safe_run):
  python3 -I -B testing/d003/stage_s4r8/config_check_r8m1a4audit2.py OUTFILE_NAME
OUTFILE_NAME must be CONFIG_CHECK_R8_M1a4AUDIT2_<name>.tsv (a bare name) and must not exist (U17).  Writes only into the
round evidence directory.  The last line of stdout is "config_check fails=<n> evidence_insufficient=<m>".
"""
import hashlib
import os
import re
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1a4audit2")
RAW = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "callseq_r8m1a4_r3")
REG_M1A = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8", "M1a")
REG_R7 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r7")
EV_R7 = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r7")
OUT_RE = re.compile(r"^CONFIG_CHECK_R8_M1a4AUDIT2_[A-Za-z0-9_]+\.tsv$")
GRID_ARGV = "pattern both 4 3"

UNITS_FILE = os.path.join(REG_M1A, "CALLSEQ_UNITS_R8_M1a4_R3.tsv")
RUNS_FILE = os.path.join(REG_M1A, "CALLSEQ_RUNS_R8_M1a4_R3.tsv")
DRV_M1A = os.path.join(REG_M1A, "DRIVERS_R8_M1a.tsv")
DRV_F2 = os.path.join(REG_M1A, "DRIVERS_R8_M1a_F2_REUSED.tsv")
AUDIT = os.path.join(REG_M1A, "DRIVER_TAG_AUDIT_R8_M1a4.tsv")
SEAM7 = os.path.join(REG_R7, "DRIVERS_R7_SEAM.tsv")
R6BSEAM7 = os.path.join(REG_R7, "DRIVER_R6B_SEAM_R7.tsv")
R6BSEAM7F2 = os.path.join(REG_R7, "DRIVER_R6B_SEAM_R7_F2.tsv")
DRIVERS_R7_DIR = os.path.join(EV_R7, "drivers_r7")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_tsv_with_header(path, header_prefix=None):
    """Return (header, rows) for a TSV whose header is the first non-comment line.  Comment lines start with '#'.
    Rows must have as many columns as the header; anything else raises SystemExit (no silent default)."""
    with open(path, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    hdr = None
    rows = []
    for n, line in enumerate(lines, 1):
        if not line or line.startswith("#"):
            continue
        cols = line.split("\t")
        if hdr is None:
            hdr = cols
            continue
        if len(cols) != len(hdr):
            raise SystemExit("REFUSED: %s line %d has %d columns, header has %d" % (path, n, len(cols), len(hdr)))
        rows.append((n, dict(zip(hdr, cols))))
    if hdr is None:
        raise SystemExit("REFUSED: no header in %s" % path)
    return hdr, rows


def read_tsv_no_header(path, columns):
    """Read a table with no header.  The column order is the printf order of its generator (named in the caller)."""
    rows = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            line = line.rstrip("\n")
            if not line:
                continue
            cols = line.split("\t")
            if len(cols) != len(columns):
                raise SystemExit("REFUSED: %s line %d has %d columns, expected %d" % (path, n, len(cols), len(columns)))
            rows.append((n, dict(zip(columns, cols))))
    return rows


def main(argv):
    if len(argv) != 2 or not OUT_RE.match(argv[1]):
        raise SystemExit("usage: config_check_r8m1a4audit2.py CONFIG_CHECK_R8_M1a4AUDIT2_<name>.tsv")
    out = os.path.join(EV, argv[1])
    if os.path.exists(out):
        raise SystemExit("REFUSED: exists (U17): %s" % out)

    fails = []
    insuff = []
    results = []  # (check, unit_id, status, detail)

    def rec(check, unit, status, detail):
        results.append((check, unit, status, detail))
        if status == "FAIL":
            fails.append((check, unit, detail))
        elif status == "EVIDENCE_INSUFFICIENT":
            insuff.append((check, unit, detail))

    # ---- load tables ----
    _, units_rows = read_tsv_with_header(UNITS_FILE)
    units = [r for _, r in units_rows]
    _, runs_rows = read_tsv_with_header(RUNS_FILE)
    runs = {r["unit_id"]: r for _, r in runs_rows}
    _, drv_m1a_rows = read_tsv_with_header(DRV_M1A)
    drv_m1a = {r["driver"]: r for _, r in drv_m1a_rows}
    _, drv_f2_rows = read_tsv_with_header(DRV_F2)
    drv_f2 = {r["driver"]: r for _, r in drv_f2_rows}
    seam7 = read_tsv_no_header(SEAM7, ["name", "tree", "lib_sha256", "driver_sha256", "library_path"])
    r6b7 = read_tsv_no_header(R6BSEAM7, ["driver", "lib_sha256", "driver_sha256", "library_path"])
    r6b7f2 = read_tsv_no_header(R6BSEAM7F2, ["driver", "lib_sha256", "driver_sha256", "library_path"])

    # ---- C0: counts ----
    rec("C0_UNIT_COUNT", "-", "PASS" if len(units) == 198 else "FAIL", "units=%d" % len(units))
    rec("C0_RUN_COUNT", "-", "PASS" if len(runs) == 198 else "FAIL", "runs=%d" % len(runs))
    unit_ids = [u["unit_id"] for u in units]
    rec("C0_UNIT_ID_UNIQUE", "-", "PASS" if len(set(unit_ids)) == len(unit_ids) else "FAIL", "unique=%d" % len(set(unit_ids)))

    # ---- C1 / C2 / C3 / C4 / C5 / C9 per unit ----
    key_counter = Counter()
    key_members = defaultdict(list)
    for u in units:
        uid = u["unit_id"]
        r = runs.get(uid)
        if r is None:
            rec("C1_RUN_PRESENT", uid, "FAIL", "no run row")
            continue
        same = all(r[k] == u[k] for k in ("pair_id", "run_tree", "driver_sha256"))
        rec("C1_RUN_FIELDS_EQ_UNIT", uid, "PASS" if same else "FAIL",
            "pair=%s/%s tree=%s/%s sha=%s" % (u["pair_id"], r["pair_id"], u["run_tree"], r["run_tree"],
                                              "eq" if u["driver_sha256"] == r["driver_sha256"] else "ne"))
        rec("C1_CMD_ENV_EQ_UNIT_ENV", uid, "PASS" if r["cmd_env"] == u["env"] else "FAIL",
            "run=%s unit=%s" % (r["cmd_env"], u["env"]))
        rec("C1_RUN_TAG_EQ_UNIT_TAG", uid, "PASS" if r["driver_tag"] == u["driver_tag"] else "FAIL",
            "run=%s unit=%s" % (r["driver_tag"], u["driver_tag"]))

        # C2: registry record of the driver tag
        tag = u["driver_tag"]
        if tag in drv_m1a:
            reg = drv_m1a[tag]
            reg_sha = reg["driver_sha256"]
            reg_path = reg["driver_path"]
            src = "DRIVERS_R8_M1a"
        elif tag in drv_f2:
            reg = drv_f2[tag]
            reg_sha = reg["sha256_record"]
            reg_path = reg["path"]
            src = "DRIVERS_R8_M1a_F2_REUSED"
        else:
            reg = None
            reg_sha = None
            reg_path = None
            src = None
        if reg is None:
            rec("C2_DRIVER_TAG_IN_REGISTRY", uid, "FAIL", "tag %s not in registries" % tag)
        else:
            rec("C2_UNIT_SHA_EQ_REGISTRY", uid, "PASS" if u["driver_sha256"] == reg_sha else "FAIL",
                "%s unit=%s registry=%s" % (src, u["driver_sha256"][:12], (reg_sha or "")[:12]))
            rec("C3_UNIT_PATH_EQ_REGISTRY", uid, "PASS" if u["driver_path"] == reg_path else "FAIL", src)
            if os.path.isfile(u["driver_path"]):
                now = sha256_file(u["driver_path"])
                rec("C3_FILE_SHA_EQ_UNIT", uid, "PASS" if now == u["driver_sha256"] else "FAIL", now[:12])
            else:
                rec("C3_FILE_SHA_EQ_UNIT", uid, "FAIL", "driver file missing: %s" % u["driver_path"])

        # C4: argv
        rec("C4_ARGV_EQ_GRID", uid, "PASS" if u["argv"] == GRID_ARGV else "FAIL", u["argv"])

        # C5: environment expansion consistent with fields
        env_map = {}
        for part in u["env"].split(" "):
            if "=" in part:
                k, v = part.split("=", 1)
                env_map[k] = v
        ok_mode = env_map.get("FMM_MODE") == u["mode"]
        ok_ng = env_map.get("S4FMM_NG") == u["NG"]
        twice_expected = u["twice_env"] == "slab"
        ok_twice = (env_map.get("S4FMM_TWICE") == "slab") == twice_expected
        rec("C5_ENV_MODE_NG_TWICE", uid, "PASS" if (ok_mode and ok_ng and ok_twice) else "FAIL",
            "mode=%s ng=%s twice=%s env=%s" % (u["mode"], u["NG"], u["twice_env"], u["env"]))

        # C6 key
        key = (u["driver_sha256"], u["run_tree"], u["mode"], u["NG"], u["twice_env"], u["env"], u["argv"])
        key_counter[key] += 1
        key_members[key].append(uid)

        # C9 raw directory
        ud = os.path.join(RAW, uid)
        present = all(os.path.isfile(os.path.join(ud, f)) for f in ("events.tsv", "summary.json", "gdb.stdout.txt", "gdb.stderr.txt"))
        rec("C9_RAW_FILES_PRESENT", uid, "PASS" if present else "FAIL", ud)

    dup_keys = [k for k, c in key_counter.items() if c > 1]
    rec("C6_DEDUP_KEY_UNIQUE", "-", "PASS" if not dup_keys else "FAIL",
        "keys=%d duplicates=%d" % (len(key_counter), len(dup_keys)))

    # ---- C7: F2/F3 pair differs only in tree and driver identity ----
    pairs = defaultdict(list)
    for u in units:
        pairs[u["pair_id"]].append(u)
    for pid in sorted(pairs):
        members = pairs[pid]
        trees = sorted(m["run_tree"] for m in members)
        if len(members) != 2 or trees != ["F2", "F3"]:
            rec("C7_PAIR_HAS_F2_AND_F3", pid, "FAIL", "trees=%s" % trees)
            continue
        a = [m for m in members if m["run_tree"] == "F2"][0]
        b = [m for m in members if m["run_tree"] == "F3"][0]
        # C7a: configuration fields must be identical on both sides of the pair.
        cfg_diff = [k for k in ("mode", "NG", "route", "twice_env", "argv", "env") if a[k] != b[k]]
        rec("C7_PAIR_SAME_CONFIG", pid, "PASS" if not cfg_diff else "FAIL",
            "differ=%s" % (",".join(cfg_diff) if cfg_diff else "none"))
        # C7b: coverage attribution (families, sites) must be identical; points_n is the number of registry points
        # attributed to the unit and is reported, not required to be equal (a point is attributed to one side only).
        att_diff = [k for k in ("families", "sites") if a[k] != b[k]]
        rec("C7_PAIR_SAME_FAMILIES_SITES", pid, "PASS" if not att_diff else "FAIL",
            "differ=%s" % (",".join(att_diff) if att_diff else "none"))
        if a["points_n"] == b["points_n"]:
            pts = "EQUAL"
        else:
            pts = "ASYMMETRIC_F2=%s_F3=%s" % (a["points_n"], b["points_n"])
        rec("C7_POINT_ATTRIBUTION", pid, "INFO", pts)
        rec("C7_PAIR_DRIVER_IDENTITY_DIFFERS", pid,
            "PASS" if (a["driver_sha256"] != b["driver_sha256"] and a["driver_tag"] != b["driver_tag"]) else "FAIL",
            "F2=%s F3=%s" % (a["driver_tag"], b["driver_tag"]))

    # ---- C8: NO_DRIVER_PATH_COLUMN rows ----
    _, audit_rows = read_tsv_with_header(AUDIT)
    no_path = [r for _, r in audit_rows if r["status"] == "NO_DRIVER_PATH_COLUMN"]
    rec("C8_NO_DRIVER_PATH_ROWS", "-", "PASS" if len(no_path) == 8 else "FAIL", "rows=%d" % len(no_path))
    seam_by_name = {r["name"]: r for _, r in seam7}
    r6b_by_name = {r["driver"]: r for _, r in r6b7}
    r6bf2_by_name = {r["driver"]: r for _, r in r6b7f2}
    for r in no_path:
        tag = r["driver_tag"]
        table = r["table"]
        recorded = r["recorded_driver_sha256"]
        found = None
        if table == "DRIVERS_R7_SEAM":
            rec_row = seam_by_name.get(tag)
            if rec_row is not None:
                found = (rec_row["driver_sha256"], rec_row["tree"])
                if rec_row["driver_sha256"] != recorded:
                    rec("C8_SEAM_REGISTRY_SHA_EQ_AUDIT", tag, "FAIL", "table=%s audit=%s" % (rec_row["driver_sha256"][:12], recorded[:12]))
        elif table == "DRIVER_R6B_SEAM_R7":
            rec_row = r6b_by_name.get(tag)
            if rec_row is not None:
                found = (rec_row["driver_sha256"], "-")
        elif table == "DRIVER_R6B_SEAM_R7_F2":
            rec_row = r6bf2_by_name.get(tag)
            if rec_row is not None:
                found = (rec_row["driver_sha256"], "-")
        if found is None:
            rec("C8_NO_DRIVER_PATH_RESOLVED", tag, "EVIDENCE_INSUFFICIENT", "table=%s: no printf-order row" % table)
            continue
        # The driver file is in drivers_r7 under the driver name (seam-<name> for DRIVERS_R7_SEAM; r6bseam-<name> for the R6B tables).
        name = tag
        cand = []
        if table == "DRIVERS_R7_SEAM":
            cand.append(os.path.join(DRIVERS_R7_DIR, "seam-%s" % name, "driver"))
        else:
            cand.append(os.path.join(DRIVERS_R7_DIR, name, "driver"))
        path = None
        for c in cand:
            if os.path.isfile(c):
                path = c
                break
        if path is None:
            rec("C8_NO_DRIVER_PATH_RESOLVED", tag, "EVIDENCE_INSUFFICIENT",
                "table=%s: driver file not found under drivers_r7 (%s)" % (table, ";".join(cand)))
            continue
        now = sha256_file(path)
        rec("C8_NO_DRIVER_FILE_SHA_EQ_RECORD", tag, "PASS" if now == found[0] else "FAIL",
            "table=%s file=%s now=%s record=%s" % (table, os.path.relpath(path, REPO), now[:12], found[0][:12]))

    # ---- write ----
    with open(out, "x", encoding="utf-8") as fh:
        fh.write("check\tunit\tstatus\tdetail\n")
        for check, unit, status, detail in results:
            fh.write("%s\t%s\t%s\t%s\n" % (check, unit, status, detail.replace("\t", " ")))
    counts = Counter(s for _, _, s, _ in results)
    print("config_check results: %s" % dict(sorted(counts.items())))
    print("config_check fails=%d evidence_insufficient=%d" % (len(fails), len(insuff)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
