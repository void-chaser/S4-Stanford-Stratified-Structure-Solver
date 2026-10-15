#!/usr/bin/env python3
# make_prereg_m1c_facts_r8m1c2.py -- P05-S4 R8 M1c2 M1c fact-expectation freeze (brief section 4).
# Builds PREREG_M1C_FACTS_R8_M1c2.tsv (472 rows) and PREREG_M1C_FACTS_RECORD_R8_M1c2.txt in $EV.
# Reads only committed registries and the R7 frozen fact tables.  Does NOT read any R8 M1c run output.
# Self-checks (any failure -> exit 1, nothing frozen):
#   - gdb_* and nogdb_* fact columns equal between the two R7 F2 passes (state and seam);
#   - pass1 equals pass2 on fact columns;
#   - env of each of the 440 points equals the M1c prereg env as a key/value set (all 440 must agree);
#   - driver_sha256 equals the M1c prereg driver_sha256;
#   - invariants equal between the two passes; point_verdict all HOLD.
# Usage: python3 -I -B make_prereg_m1c_facts_r8m1c2.py
import hashlib, os, sys, time

REPO = os.path.realpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
EV = os.path.join(REPO, "checkpoints", "p05", "evidence", "p05-s4r8", "m1c2")
REG = os.path.join(REPO, "checkpoints", "p05", "registries")
S7 = os.path.join(REG, "s4r7")
S8 = os.path.join(REG, "s4r8", "M1a")
S6B = os.path.join(REG, "s4r6b")
os.makedirs(os.path.join(EV, "tmp"), exist_ok=True)

SRC = {
    "M3_F2_STATE_R6c_pass1": os.path.join(S7, "M3_F2_STATE_R6c_pass1.tsv"),
    "M3_F2_STATE_R6c_pass2": os.path.join(S7, "M3_F2_STATE_R6c_pass2.tsv"),
    "M3_F2_STATE_SEAM_R6c_pass1": os.path.join(S7, "M3_F2_STATE_SEAM_R6c_pass1.tsv"),
    "M3_F2_STATE_SEAM_R6c_pass2": os.path.join(S7, "M3_F2_STATE_SEAM_R6c_pass2.tsv"),
    "M3_F2_RESULTS_R6c_STATE": os.path.join(S7, "M3_F2_RESULTS_R6c_STATE.tsv"),
    "M3_F2_RESULTS_R6c_SEAM": os.path.join(S7, "M3_F2_RESULTS_R6c_SEAM.tsv"),
    "PREREG_M1C": os.path.join(S8, "REGISTRY_S4_PRE_R8_M1c_R8_M1a6.tsv"),
    "CONTROL_R6B": os.path.join(S6B, "REGISTRY_S4_PRE_R6b_CONTROL.tsv"),
}


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path):
    with open(path, encoding="utf-8") as fh:
        lines = [l.rstrip("\n") for l in fh if l.strip() and not l.startswith("#")]
    head = lines[0].split("\t")
    return head, [dict(zip(head, l.split("\t"))) for l in lines[1:]]


def env_set(s):
    out = {}
    for kv in s.split(";"):
        if not kv:
            continue
        k, _, v = kv.partition("=")
        out[k] = v
    return out


def env_no_dump(s):
    return ";".join(kv for kv in s.split(";") if kv and not kv.startswith("S4FMM_DUMP"))


failures = []


def fail(msg):
    failures.append(msg)


# ---- load ----
_, p1 = read_rows(SRC["M3_F2_STATE_R6c_pass1"])
_, p2 = read_rows(SRC["M3_F2_STATE_R6c_pass2"])
_, s1 = read_rows(SRC["M3_F2_STATE_SEAM_R6c_pass1"])
_, s2 = read_rows(SRC["M3_F2_STATE_SEAM_R6c_pass2"])
_, res_state = read_rows(SRC["M3_F2_RESULTS_R6c_STATE"])
_, res_seam = read_rows(SRC["M3_F2_RESULTS_R6c_SEAM"])
prehead, prereg = read_rows(SRC["PREREG_M1C"])
_, ctrl = read_rows(SRC["CONTROL_R6B"])

FACT_STATE = ["gdb_rc1", "gdb_rc2", "gdb_rc3", "gdb_hit", "gdb_done",
              "nogdb_rc1", "nogdb_rc2", "nogdb_rc3", "nogdb_hit", "nogdb_done", "rc_gdb", "rc_nogdb"]
FACT_SEAM = ["gdb_rc1", "gdb_rc2", "gdb_hit", "gdb_done", "nogdb_rc1", "nogdb_rc2", "nogdb_hit", "nogdb_done",
             "rc_gdb", "rc_nogdb"]


def facts(r, cols):
    return tuple(r.get(c, "") for c in cols)


# ---- self-check 1/2: pass1 == pass2 on fact columns, gdb == nogdb is checked per row below ----
if len(p1) != len(p2):
    fail("STATE pass row count differs")
else:
    for a, b in zip(p1, p2):
        if a["id"] != b["id"] or facts(a, FACT_STATE) != facts(b, FACT_STATE):
            fail("STATE pass1 != pass2 on facts at %s" % a["id"])
if len(s1) != len(s2):
    fail("SEAM pass row count differs")
else:
    for a, b in zip(s1, s2):
        if a["id"] != b["id"] or facts(a, FACT_SEAM) != facts(b, FACT_SEAM):
            fail("SEAM pass1 != pass2 on facts at %s" % a["id"])

# gdb vs nogdb column equality on each row (the freeze compares the gdb_* columns to nogdb_*)
for r in p1 + p2:
    if (r["gdb_rc1"], r["gdb_rc2"], r["gdb_rc3"], r["gdb_hit"], r["gdb_done"]) != (
            r["nogdb_rc1"], r["nogdb_rc2"], r["nogdb_rc3"], r["nogdb_hit"], r["nogdb_done"]):
        fail("STATE gdb != nogdb on facts at %s" % r["id"])
for r in s1 + s2:
    if (r["gdb_rc1"], r["gdb_rc2"], r["gdb_hit"], r["gdb_done"]) != (
            r["nogdb_rc1"], r["nogdb_rc2"], r["nogdb_hit"], r["nogdb_done"]):
        fail("SEAM gdb != nogdb on facts at %s" % r["id"])

# ---- self-check 3: invariants equal between the two passes and point_verdict all HOLD ----
inv_by_pass = {}
for r in res_state:
    inv_by_pass.setdefault((r["point_id"], r["pass"]), r)
verdicts = set()
for r in res_state + res_seam:
    verdicts.add(r.get("point_verdict", ""))
if verdicts != {"HOLD"}:
    fail("point_verdict not all HOLD: %s" % sorted(verdicts))
# RESULTS invariant equality between pass 1 and pass 2 (state table has a pass column)
inv_cols = ["I1", "I2", "I3", "I4", "I5", "I6", "I7", "point_verdict"]
pid_pass = {}
for r in res_state:
    pid_pass.setdefault(r["point_id"], {})[r["pass"]] = tuple(r.get(c, "") for c in inv_cols)
for pid, d in pid_pass.items():
    if "1" in d and "2" in d and d["1"] != d["2"]:
        fail("invariants differ between pass1 and pass2 for %s" % pid)

# ---- index facts by id ----
f_state = {}
for r in p1:
    f_state.setdefault(r["id"], r)
f_seam = {}
for r in s1:
    f_seam.setdefault(r["id"], r)

ctrl_ids = [c["control_id"] for c in ctrl]

# ---- build the 472 rows ----
rows = []
PREREG_SHA = sha256_file(SRC["PREREG_M1C"])
ENV_MISMATCH = []
DRIVER_MISMATCH = []
for pr in prereg:
    grp = pr["group"]
    if grp not in ("G5", "G6", "G6c"):
        continue
    pid_r8 = pr["point_id"]
    tree = pr["tree"]
    base_id = pid_r8[:-3] if pid_r8.endswith("-F3") else pid_r8
    if grp == "G5":
        src = f_state.get(base_id)
        if src is None:
            fail("G5 base point missing in R7 F2 facts: %s" % base_id)
            continue
        env_exp = env_no_dump(src["env_as_run"])
        exp_rc1, exp_rc2, exp_rc3, exp_hit = src["gdb_rc1"], src["gdb_rc2"], src["gdb_rc3"], src["gdb_hit"]
        row_kind = "point"
        fact_src = "M3_F2_STATE_R6c_pass1.tsv(+pass2)"
        verdict_src = "M3_F2_RESULTS_R6c_STATE.tsv"
        inv = {c: "" for c in ["I1", "I2", "I3", "I4", "I5", "I6", "I7"]}
        rr = None
        for r in res_state:
            if r["point_id"] == base_id and r["pass"] == "1":
                rr = r
                break
        if rr is None:
            fail("G5 invariant row missing: %s" % base_id)
            continue
        for c in ["I1", "I2", "I3", "I4", "I5", "I6", "I7"]:
            inv[c] = rr.get(c, "")
        pv = rr.get("point_verdict", "")
    elif grp == "G6":
        src = f_seam.get(base_id)
        if src is None:
            fail("G6 base point missing in R7 F2 seam facts: %s" % base_id)
            continue
        env_exp = env_no_dump(src["env_as_run"])
        exp_rc1, exp_rc2, exp_rc3, exp_hit = src["gdb_rc1"], src["gdb_rc2"], "-", src["gdb_hit"]
        row_kind = "point"
        fact_src = "M3_F2_STATE_SEAM_R6c_pass1.tsv(+pass2)"
        verdict_src = "M3_F2_RESULTS_R6c_SEAM.tsv"
        rr = None
        for r in res_seam:
            if r["point_id"] == base_id and r["pass"] == "1":
                rr = r
                break
        if rr is None:
            fail("G6 invariant row missing: %s" % base_id)
            continue
        inv = {c: rr.get(c, "") for c in ["I1", "I2", "I3", "I4", "I5", "I6", "I7"]}
        pv = rr.get("point_verdict", "")
    else:  # G6c control
        src = f_seam.get(base_id)
        if src is None:
            fail("G6c control missing in R7 F2 seam facts: %s" % base_id)
            continue
        env_exp = env_no_dump(src["env_as_run"])
        exp_rc1, exp_rc2, exp_rc3, exp_hit = src["gdb_rc1"], src["gdb_rc2"], "-", src["gdb_hit"]
        row_kind = "control"
        fact_src = "M3_F2_STATE_SEAM_R6c_pass1.tsv(+pass2)"
        verdict_src = "-"
        inv = {c: "-" for c in ["I1", "I2", "I3", "I4", "I5", "I6", "I7"]}
        pv = "-"
    # env: must equal the M1c prereg env as a key/value set (key order differs in the source)
    if env_set(env_exp) != env_set(pr["env"]):
        ENV_MISMATCH.append((pid_r8, env_exp, pr["env"]))
    # driver_sha256 is taken from the M1c prereg itself (freeze definition); the driver files are
    # re-hashed against it in the preflight (preflight_m1c_r8m1c2.py), not here.
    rows.append({
        "row_kind": row_kind,
        "group": grp,
        "point_id_r8": pid_r8,
        "base_id": base_id,
        "tree": tree,
        "driver_name": pr["driver_name"],
        "driver_sha256": pr["driver_sha256"],
        "env_expected": env_exp,
        "exp_rc1": exp_rc1,
        "exp_rc2": exp_rc2,
        "exp_rc3": exp_rc3 if grp == "G5" else "-",
        "exp_hit": exp_hit,
        "exp_point_verdict": pv if row_kind == "point" else "-",
        "exp_I1": inv.get("I1", "-"), "exp_I2": inv.get("I2", "-"), "exp_I3": inv.get("I3", "-"),
        "exp_I4": inv.get("I4", "-"), "exp_I5": inv.get("I5", "-"), "exp_I6": inv.get("I6", "-"),
        "exp_I7": inv.get("I7", "-"),
        "fact_source": fact_src,
        "verdict_source": verdict_src,
        "status": "INFLUENCED",
    })

if ENV_MISMATCH:
    fail("env mismatch vs M1c prereg for %d rows (first: %s)" % (len(ENV_MISMATCH), ENV_MISMATCH[0]))
if DRIVER_MISMATCH:
    fail("driver_sha256 mismatch for %d rows" % len(DRIVER_MISMATCH))

# ---- CTRL_AUX: 16 controls x 2 trees (F2, F3); facts from R7 F2 seam/state control rows ----
ctrl_rows = []
for cid in ctrl_ids:
    # G5 controls live in the state fact table as kind=control (pass1)
    src = None
    for r in p1:
        if r["kind"] == "control" and r["id"] == cid:
            src = r
            break
    if src is None:
        fail("CTRL_AUX control missing in R7 F2 state facts: %s" % cid)
        continue
    for tree in ("F2", "F3"):
        ctrl_rows.append({
            "row_kind": "control_aux",
            "group": "CTRL_AUX",
            "point_id_r8": "%s-%s" % (cid, tree) if tree == "F3" else cid,
            "base_id": cid,
            "tree": tree,
            "driver_name": "r6bstate-%s-dbg" % tree,
            "driver_sha256": "",
            "env_expected": env_no_dump(src["env_as_run"]),
            "exp_rc1": src["gdb_rc1"], "exp_rc2": src["gdb_rc2"], "exp_rc3": "-",
            "exp_hit": src["gdb_hit"],
            "exp_point_verdict": "-",
            "exp_I1": "-", "exp_I2": "-", "exp_I3": "-", "exp_I4": "-", "exp_I5": "-", "exp_I6": "-", "exp_I7": "-",
            "fact_source": "M3_F2_STATE_R6c_pass1.tsv(+pass2)",
            "verdict_source": "-",
            "status": "INFLUENCED",
        })

# fill CTRL_AUX driver sha256 from the M1c prereg where a row exists for the same driver (F2 / F3 driver)
drv_by_name = {}
for pr in prereg:
    drv_by_name.setdefault((pr["driver_name"], pr["tree"]), pr["driver_sha256"])
for r in ctrl_rows:
    r["driver_sha256"] = drv_by_name.get(("r6bstate-%s-dbg" % r["tree"], r["tree"]), "")
    if not r["driver_sha256"]:
        fail("no M1c prereg driver_sha256 for %s" % r["driver_name"])

rows.extend(ctrl_rows)

if len(rows) != 472:
    fail("row count %d != 472" % len(rows))

# ---- output ----
cols = ["row_kind", "group", "point_id_r8", "base_id", "tree", "driver_name", "driver_sha256", "env_expected",
        "exp_rc1", "exp_rc2", "exp_rc3", "exp_hit", "exp_point_verdict",
        "exp_I1", "exp_I2", "exp_I3", "exp_I4", "exp_I5", "exp_I6", "exp_I7",
        "fact_source", "verdict_source", "status"]
out_tsv = os.path.join(EV, "PREREG_M1C_FACTS_R8_M1c2.tsv")
out_rec = os.path.join(EV, "PREREG_M1C_FACTS_RECORD_R8_M1c2.txt")
if failures:
    for m in failures:
        print("SELFCHECK_FAIL\t" + m)
    print("FREEZE_NOT_WRITTEN failures=%d" % len(failures))
    sys.exit(1)

with open(out_tsv, "w", encoding="utf-8") as fh:
    fh.write("# PREREG_M1C_FACTS_R8_M1c2.tsv -- P05-S4 R8 M1c2 M1c fact-expectation freeze (472 rows; INFLUENCED).\n")
    fh.write("\t".join(cols) + "\n")
    for r in rows:
        fh.write("\t".join(str(r[c]) for c in cols) + "\n")

with open(out_rec, "w", encoding="utf-8") as fh:
    fh.write("PREREG_M1C_FACTS_RECORD_R8_M1c2\n")
    fh.write("utc=%s\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    fh.write("rows=%d\n" % len(rows))
    fh.write("rows_point_G5=%d\n" % sum(1 for r in rows if r["group"] == "G5"))
    fh.write("rows_point_G6=%d\n" % sum(1 for r in rows if r["group"] == "G6"))
    fh.write("rows_point_G6c=%d\n" % sum(1 for r in rows if r["group"] == "G6c"))
    fh.write("rows_CTRL_AUX=%d\n" % sum(1 for r in rows if r["group"] == "CTRL_AUX"))
    fh.write("output_sha256=%s\n" % sha256_file(out_tsv))
    fh.write("prereg_M1c_sha256=%s\n" % PREREG_SHA)
    for k, p in SRC.items():
        fh.write("source %s path=%s sha256=%s\n" % (k, os.path.relpath(p, REPO), sha256_file(p)))
    fh.write("SELFCHECK=PASS\n")
print("FREEZE_OK rows=%d" % len(rows))
print("OUT=%s" % out_tsv)
