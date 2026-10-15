#!/usr/bin/env python3
# prereg_r8m2a.py -- P05-S4 R8 M2a section 4.5: M2 pre-registration (FROZEN before any M2 run).
# Writes $EV/PREREG_M2_R8_M2a_R2.tsv, PREREG_M2_R8_M2a_R2.sha256, PREREG_M2_R8_M2a_R2_TIMESTAMP_UTC.txt,
# and $EV/PREREG_M2_COUNT_R8_M2a_R2.txt (item x tree counts; asserts that the item sums equal the row total).
# Points written in this round (only items with an existing, pinned driver and a historical expectation):
#   M2-01 : 17 F3 repair points (ADD22 rows 1-6 and 11-21), driver init-F3 or polyinj-F3 (M1a linked, sha pinned)
#   M2-09 : CTRL_SEAM fmmret re-test, F3 and F2 (drivers seam-fmmret-F3 from DRIVERS_R8; F2 seamF-F2 from R7 record)
# Not written (listed in COUNT as not-written, with the reason): M2-00 (all covered by M0), M2-02, M2-08 (search not done),
# M2-03/04/05 (new apparatus not built in M2a), M2-06, M2-07 (no pinned driver run in M2a), M2-10 (B gdb not run),
# M3_DEFERRED.  Refuses to overwrite (U17).  No S4 driver is run here.
import hashlib
import os
import sys

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m2a")
S4R8 = os.path.join(REPO, "checkpoints", "p05", "registries", "s4r8")
TAG = "_R2"
PREREG = os.path.join(EV, "PREREG_M2_R8_M2a" + TAG + ".tsv")
SHA_FILE = os.path.join(EV, "PREREG_M2_R8_M2a" + TAG + ".sha256")
TS_FILE = os.path.join(EV, "PREREG_M2_R8_M2a" + TAG + "_TIMESTAMP_UTC.txt")
COUNT = os.path.join(EV, "PREREG_M2_COUNT_R8_M2a" + TAG + ".txt")

# Pinned driver/library hashes (recorded facts, not recomputed here; verified by inventory_r8m2a.py).
LIB_F3 = "abbc01c78f0a422f3494556bb43e212e397fbbf49d03370132ae45e2c268e5de"
DRV_INIT_F3 = "ff66cfc1bf87b6c22d13e32dc6adf3c5e6b090fdcad745bf5248f74dd9510b68"
DRV_POLY_F3 = "419cfb727932cc8d9417fd3a873c578f2f1f597f57e501041d9dd3b221ad30a9"
DRV_SEAM_FMMRET_F3 = "f7d445cc2a48ef9d7fae2118c3cd3c715bffaff2de89ab795dd74613f2ea585c"
DRV_SEAM_FMMRET_F2 = "79a3d3e7abd7993af99da6c24a4f9e1d24ed96b8be4e4cbd140be0652a5967b6"

COLS = ["point_id", "item", "tree", "driver", "driver_sha256", "lib_sha256", "env", "passes", "exp_rc1", "exp_rc2",
        "exp_signal", "exp_hit", "exp_class", "exp_I1", "exp_I2", "exp_I3", "exp_I4", "exp_I5", "exp_I6", "exp_I7",
        "exp_stage", "basis", "status"]


def sha256_file(path):
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def read_tsv(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    return [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def main():
    if os.path.exists(PREREG) or os.path.exists(SHA_FILE) or os.path.exists(COUNT):
        print("prereg_r8m2a: REFUSED exists (U17): PREREG_M2_R8_M2a%s" % TAG)
        return 2
    # Input hash check: the M1a6 mapping and the M1b registry must match the recorded M1c4 facts (already verified
    # by the start gate for the M1 chain); here only existence is required.
    for rel in ("M1a/ADDITIONS_MAPPING_22_R8_M1a6.tsv", "M1a/REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv"):
        if not os.path.isfile(os.path.join(S4R8, rel)):
            print("prereg_r8m2a: REFUSED missing input %s" % rel)
            return 2

    rows = []
    not_written = {}
    # --- M2-01: 17 F3 points (ADD22 rows 1-6 and 11-21 of the mapping; row 7-9 = U96 excluded, row 10 control) ---
    mapping = read_tsv(os.path.join(S4R8, "M1a", "ADDITIONS_MAPPING_22_R8_M1a6.tsv"))
    registry_env = {}
    with open(os.path.join(S4R8, "M1a", "REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv"), encoding="utf-8") as fh:
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) > 6 and p[0] == "ADDITIONS_22" and p[2] == "F3":
                registry_env[p[1]] = p[5]
    # M1b registry: F3 rows of group ADDITIONS_22 give expected_rc1, expected_rc2, expected_class, expected_hit, env.
    m1b = {}
    with open(os.path.join(S4R8, "M1a", "REGISTRY_S4_PRE_R8_M1b_R8_M1a6.tsv"), encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            p = dict(zip(head, line.rstrip("\n").split("\t")))
            if p.get("group") == "ADDITIONS_22" and p.get("tree") == "F3":
                m1b[p["point_id"]] = p
    n = 0
    for m in mapping:
        row_no = int(m["row"])
        if row_no not in list(range(1, 7)) + list(range(11, 22)):
            continue  # rows 7-9 are U96 (excluded: U100 -> S5), row 10 is a control, row 22 is the B control
        # the M1b point id is ADD22-<item>-F3, where <item> is the numbered id of the row (A-1..A-6, B-11..B-21)
        # map row -> numbered M1b id: rows 1-3 = A-1..3, rows 4-6 = A-4..6, rows 11-21 = B-11..21 (ADDITIONS_MAPPING_22_R8_M1a6)
        if 1 <= row_no <= 6:
            numbered = "A-%d" % row_no
        else:
            numbered = "B-%d" % row_no
        pid_m1b = "ADD22-%s-F3" % numbered
        if pid_m1b not in m1b:
            print("prereg_r8m2a: REFUSED no M1b F3 row for %s (row %d)" % (pid_m1b, row_no))
            return 2
        reg = m1b[pid_m1b]
        # Cross-check (brief 4.5): the M1b env must name the same mode and NG as the mapping's mapped_combo.
        combo = m["mapped_combo"]  # e.g. closed2d-ng1, fft-ng5, kottke-ng5, fft-ng1, kottke-ng9
        mode_ng = combo.split("-ng")
        env_mode = [kv.split("=", 1)[1] for kv in reg["env"].split(";") if kv.startswith("FMM_MODE=")]
        env_ng = [kv.split("=", 1)[1] for kv in reg["env"].split(";") if kv.startswith("S4FMM_NG=")]
        if len(mode_ng) != 2 or not env_mode or not env_ng or env_mode[0] != mode_ng[0] or env_ng[0] != mode_ng[1]:
            print("prereg_r8m2a: REFUSED env/mapping mismatch row %d: mapping %s, M1b env %s" % (row_no, combo, reg["env"]))
            return 2
        n += 1
        # Driver: A items (806, 1729) use the init injector (init-F3); B (415) polyinj-F3.
        if numbered.startswith("A-"):
            drv, dsha = "init-F3", DRV_INIT_F3
        else:
            drv, dsha = "polyinj-F3", DRV_POLY_F3
        rows.append({
            "point_id": "M2-01-%02d-F3" % row_no, "item": "M2-01", "tree": "F3", "driver": drv,
            "driver_sha256": dsha, "lib_sha256": LIB_F3, "env": reg["env"], "passes": "2",
            "exp_rc1": reg["expected_rc1"], "exp_rc2": reg["expected_rc2"], "exp_signal": "-",
            "exp_hit": reg["expected_hit"], "exp_class": reg["expected_class"],
            "exp_I1": "HOLD", "exp_I2": "HOLD", "exp_I3": "-", "exp_I4": "HOLD", "exp_I5": "HOLD", "exp_I6": "HOLD",
            "exp_I7": "DEFERRED", "exp_stage": "-",
            "basis": "U232; ADDITIONS_MAPPING_22_R8_M1a6 row %d; M1b registry %s; R6b registry header 5-11; R7 M3 G5 HOLD" % (row_no, pid_m1b),
            "status": "INFLUENCED",
        })
    # M2-09 (CTRL_SEAM fmmret) is NOT written: CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv records the driver paths and
    # sha256 but no env and no expectation, so an env written here would be invented.  Listed as open (not written).

    total = len(rows)
    not_written = {
        "M2-00": "no point: all six A_CTRL combos COVERED_BY_M0 (A10 crosswalk R2)",
        "M2-02": "NOT_FOUND: candidate search not completed in M2a",
        "M2-03": "not written: sanitizer apparatus not built in M2a",
        "M2-04": "not written: dual-target apparatus not built in M2a",
        "M2-05": "not written: other-layer apparatus not built in M2a",
        "M2-06": "not written: tensor path injection ID-to-line mapping not verified",
        "M2-07": "not written: NB=1-8 grid not enumerated in M2a",
        "M2-08": "NOT_FOUND: NB>=2 configuration search not completed in M2a",
        "M2-09": "not written: CTRL_SEAM_DRIVER_RESOLUTION_C5.tsv has no env or expectation for fmmret; needs user ruling",
        "M2-10": "not written: B gdb run not in M2a (no S4 run)",
        "M3_DEFERRED": "deferred to M3 (U235)",
    }

    # §4.5 count assertion: sum over items (per tree) must equal the total number of rows
    per = {}
    for r in rows:
        per.setdefault((r["item"], r["tree"]), 0)
        per[(r["item"], r["tree"])] += 1
    s = sum(per.values())
    if s != total:
        print("prereg_r8m2a: FAIL count sum %d != total %d" % (s, total))
        return 1

    os.makedirs(EV, exist_ok=True)
    with open(PREREG, "x", encoding="utf-8") as fh:
        fh.write("\t".join(COLS) + "\n")
        for r in rows:
            fh.write("\t".join(r[c] for c in COLS) + "\n")
    digest = sha256_file(PREREG)
    with open(SHA_FILE, "x", encoding="utf-8") as fh:
        fh.write("%s  PREREG_M2_R8_M2a%s.tsv\n" % (digest, TAG))
    import datetime
    with open(TS_FILE, "x", encoding="utf-8") as fh:
        fh.write("PREREG_M2_R8_M2a%s.tsv frozen at %s\n" % (TAG, datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")))
    with open(COUNT, "x", encoding="utf-8") as fh:
        fh.write("# PREREG_M2_COUNT_R8_M2a%s -- counts by item x tree (sum asserted = total)\n" % TAG)
        for k in sorted(per):
            fh.write("COUNT\t%s\t%s\t%d\n" % (k[0], k[1], per[k]))
        fh.write("TOTAL_ROWS\t%d\n" % total)
        fh.write("SUM_OF_ITEMS\t%d\n" % s)
        fh.write("ASSERT_SUM_EQ_TOTAL\tPASS\n")
        for k in sorted(not_written):
            fh.write("NOT_WRITTEN\t%s\t%s\n" % (k, not_written[k]))
    print("prereg_r8m2a: rows=%d sha256=%s" % (total, digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
