#!/usr/bin/env python3
# s5r5_checker_sweep.py -- P05-S5 R5 static sweep of the S5R4 end-gate checker (task brief section 3, read only).
# Enumerates every safe() check of testing/d003/stage_s5r4/gate_check_s5r4.py by AST, classifies its mechanism
# (reads_record_line / self_branch / negative_in / other), records the R4 formal result, and re-evaluates every
# reads_record_line / negative_in check on the R4 frozen data with the CORRECT record format. A R4 PASS that
# cannot be reproduced this way would be VACUOUS and would be a HARD_STOP; the expected count is zero.
import os, sys, ast, re, hashlib, subprocess

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
P05 = os.path.join(REPO, "checkpoints/p05")
EV = os.path.join(P05, "evidence/p05-s5r5")
EV3 = os.path.join(P05, "evidence/p05-s5r3")
EV4 = os.path.join(P05, "evidence/p05-s5r4")
GATE4 = os.path.join(REPO, "testing/d003/stage_s5r4/gate_check_s5r4.py")
TAB = chr(9)
NL = chr(10)

EXP_GATE4_SHA = "829f2708601ae55678d00ec8ef46754781ffe12538fd2cd98a126313692fd2c7"
EXP_BASE_HEAD = "1600ca1ba333e68988dc6d22211487b27e676191"
EXP_STATE_R4_SHA = "1a962c77e13f8c3f1189b7227855bf8826f48b7af84a43badd6cc21de509807c"
EXP_R4_TOTAL = 139
EXP_R4_PASS = 138
EXP_R4_FAIL_NAME = "SHAKEDOWN_USED_STAGING_ROOTS"


def sha_f(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def rd(p):
    return open(p, encoding="utf-8").read()


def safe_name(node):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "safe"


def main():
    src = rd(GATE4)
    sha4 = sha_f(GATE4)
    if sha4 != EXP_GATE4_SHA:
        print("HARD_STOP gate_check_s5r4.py sha mismatch: %s" % sha4)
        return 2
    tree = ast.parse(src)
    lines = src.splitlines()
    # every function definition (module level and nested) -> source segment
    fdefs = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            seg = ast.get_source_segment(src, node) or ""
            fdefs[node.name] = (node.lineno, seg)
    # record() keys written by the R4 gate (a check that string-concatenates one of these with TAB is a
    # reads_record_line check: it matches the writer's RECORD line format instead of parsing it)
    rec_keys = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "record":
            if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                rec_keys.add(node.args[0].value)
    parent = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parent[child] = node

    def loop_names(node):
        """Expand safe("<fmt>" % v, ...) inside 'for v in (<const>, ...)' to the generated check names."""
        fmtnode = node.args[0]
        if not (isinstance(fmtnode, ast.BinOp) and isinstance(fmtnode.op, ast.Mod)
                and isinstance(fmtnode.left, ast.Constant) and isinstance(fmtnode.left.value, str)
                and isinstance(fmtnode.right, ast.Name)):
            return []
        var = fmtnode.right.id
        cur = node
        while cur in parent:
            cur = parent[cur]
            if isinstance(cur, ast.For) and isinstance(cur.target, ast.Name) and cur.target.id == var:
                out = []
                if isinstance(cur.iter, (ast.Tuple, ast.List)):
                    for e in cur.iter.elts:
                        if isinstance(e, ast.Constant) and isinstance(e.value, str):
                            out.append(fmtnode.left.value % e.value)
                if isinstance(cur.iter, ast.Call) and isinstance(cur.iter.func, ast.Name) and cur.iter.func.id == "range":
                    for e in cur.iter.args:
                        if isinstance(e, ast.Constant) and isinstance(e.value, int):
                            out.append(fmtnode.left.value % e.value)
                return out
        return []

    calls = []
    for node in ast.walk(tree):
        if not safe_name(node) or not node.args:
            continue
        nm = node.args[0]
        if isinstance(nm, ast.Constant) and isinstance(nm.value, str):
            calls.append((node, nm.value))
        else:
            for g in loop_names(node):
                calls.append((node, g))
    calls.sort(key=lambda t: (t[0].lineno, t[0].col_offset, t[1]))

    def resolve(node):
        if isinstance(node, ast.Name) and node.id in fdefs:
            return fdefs[node.id][1]
        return ast.get_source_segment(src, node) or ""

    # ---- R4 formal result per check
    g4 = os.path.join(EV4, "gate/GATE_S5R4_end.txt")
    formal = {}
    for line in rd(g4).splitlines():
        f = line.split(TAB)
        if len(f) >= 2 and f[0] in ("PASS", "FAIL"):
            formal[f[1]] = f[0]
    if len(formal) != EXP_R4_TOTAL or list(formal.values()).count("FAIL") != 1:
        print("HARD_STOP R4 formal gate file does not hold 139 checks with 1 FAIL")
        return 2

    rows = []
    for (node, name) in calls:
        kind = "other"
        body = resolve(node.args[1]) if len(node.args) > 1 else ""
        has_record = any(k in body for k in rec_keys) and ("TAB" in body) and ("+" in body) and (" in " in body)
        has_self = bool(re.search(r"realpath\s*\(\s*outp|realpath\s*\(\s*out_path|if\s+staging|staging\s+else", body))
        has_neg = ("not in" in body) or bool(re.search(r"0\s+if\s+any\s*\(", body))
        if has_record:
            kind = "reads_record_line"
        elif has_self:
            kind = "self_branch"
        elif has_neg:
            kind = "negative_in"
        # shakedown coverage of the formal branch (R4 shakedown ran the gate on the staging roots, so a
        # self-branch check took its self branch and the formal branch was NOT exercised there)
        if has_self:
            shak_cov = "no"
        else:
            shak_cov = "n/a"
        record_fmt = "no" if kind == "reads_record_line" else "n/a"
        rows.append({
            "check_name": name, "line": node.lineno, "kind": kind, "record_format_ok": record_fmt,
            "has_self_branch": "yes" if has_self else "no",
            "formal_branch_exercised_in_shakedown": shak_cov,
            "r4_formal_result": formal.get(name, "MISSING"), "verdict": "", "body": body,
        })
    if len(rows) != EXP_R4_TOTAL:
        print("HARD_STOP AST collected %d checks, expected %d" % (len(rows), EXP_R4_TOTAL))
        return 2
    names = [r["check_name"] for r in rows]
    dup = sorted(set(n for n in names if names.count(n) > 1))
    if dup:
        print("HARD_STOP duplicate check names: %s" % dup)
        return 2

    # ---- re-evaluation helpers (read only, R4 frozen data)
    # the R4 STATE is read from the frozen commit 1600ca1 (read only): the working tree STATE is rewritten by
    # R5 later in the chain, so the R4 snapshot must come from git, not from the work tree.
    try:
        state4_bytes = subprocess.check_output(
            ["git", "show", EXP_BASE_HEAD + ":checkpoints/p05/STATE.md"], cwd=REPO)
    except subprocess.CalledProcessError:
        state4_bytes = b""
    state4_ok = hashlib.sha256(state4_bytes).hexdigest() == EXP_STATE_R4_SHA

    def reeval_state_markers():
        if not state4_ok:
            return "STATE_NOT_R4_FINAL"
        t = state4_bytes.decode("utf-8")
        return "PASS" if ("P05-S5 R4" in t and "未签收" in t) else "FAIL"

    def reeval_state_numbers():
        if not state4_ok:
            return "STATE_NOT_R4_FINAL"
        t = state4_bytes.decode("utf-8")
        miss = [k for k in ("DIFFS=0", "GAP=0", "26/26", "33", "265", "NO_NEW_FAILURE") if k not in t]
        return "PASS" if not miss else "FAIL:" + ",".join(miss)

    def reeval_calib():
        p = os.path.join(EV3, "CALIB_DIFF_S5R3.tsv")
        data = []
        summ = []
        hdr = None
        for line in rd(p).splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            f = line.split(TAB)
            if hdr is None:
                hdr = f
                continue
            if f[0] == hdr[0]:
                continue
            if f[0] == "SUMMARY":
                summ.append(f)
                continue
            data.append(dict(zip(hdr, f)))
        bad = [r for r in data if r.get("diff") != "SAME"]
        if bad or len(summ) != 1:
            return "FAIL:rows_diff=%d summary=%d" % (len(bad), len(summ))
        idx = summ[0].index("DIFFS=0") if "DIFFS=0" in summ[0] else -1
        if idx < 0:
            return "FAIL:summary_no_DIFFS0"
        return "PASS"

    def reeval_readiness_consistency():
        p = os.path.join(EV4, "READINESS_S5R4.tsv")
        hdr = None
        for line in rd(p).splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            f = line.split(TAB)
            if hdr is None:
                hdr = f
                continue
            if f[0] == hdr[0]:
                continue
            r = dict(zip(hdr, f + [""] * (len(hdr) - len(f))))
            if r.get("item") == "CONSISTENCY":
                need = ["33", "265", "NO_NEW_FAILURE", "DIFFS=0", "GAP=0", "26/26"]
                miss = [k for k in need if k not in r.get("note", "")]
                return "PASS" if not miss else "FAIL:" + ",".join(miss)
        return "FAIL:row_missing"

    def reeval_signoff_v2():
        p = os.path.join(P05, "P05_S5_SIGNOFF_DRAFT_v2.md")
        if not os.path.isfile(p):
            return "FAIL:absent"
        t = rd(p)
        if len(t.strip()) < 200:
            return "FAIL:empty_file_vacuous"
        if any(k in t for k in ("已签收", "P05 完成", "P05-S5 完成")):
            return "FAIL:completion_claim_present"
        return "PASS"

    def reeval_evidence_covers():
        p = os.path.join(EV4, "SHA256SUMS.txt")
        sums = {}
        for line in rd(p).splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split()
            sums[" ".join(parts[1:])] = parts[0]
        actual = set()
        for root, dirs, files in os.walk(EV4):
            dirs[:] = sorted(d for d in dirs if d not in ("tmp", "gate", "trees", "shakedown"))
            for f in files:
                rel = os.path.relpath(os.path.join(root, f), EV4)
                if rel in ("safe_run.log", "SHA256SUMS.txt"):
                    continue
                actual.add(rel)
        miss = sorted(actual - set(sums))
        extra = sorted(set(sums) - actual)
        if miss or extra:
            return "FAIL:missing=%s extra=%s" % (miss[:3], extra[:3])
        return "PASS_%d_FILES" % len(actual)

    def reeval_staging_mode():
        p = os.path.join(EV4, "shakedown/gate/GATE_S5R4_end.txt")
        t = rd(p)
        corrected = "FAIL"
        orig = "PASS"
        for line in t.splitlines():
            f = line.split(TAB)
            if len(f) >= 3 and f[0] == "RECORD" and f[1] == "STAGING_MODE":
                corrected = "PASS" if f[2] == "value=yes" else "FAIL:" + f[2]
        if "STAGING_MODE" + TAB + "yes" in t:
            orig = "PASS"
        else:
            orig = "not_staging"
        return corrected, orig

    reeval = {
        "STATE_MARKERS_R4": reeval_state_markers,
        "STATE_CRITICAL_NUMBERS": reeval_state_numbers,
        "CALIB_DIFF_ZERO": reeval_calib,
        "READINESS_CONSISTENCY_ROW": reeval_readiness_consistency,
        "SIGNOFF_V2_NO_COMPLETION_CLAIM": reeval_signoff_v2,
        "EVIDENCE_SUMS_COVERS_ALL": reeval_evidence_covers,
    }
    details = []
    vacuous = 0
    for r in rows:
        n = r["check_name"]
        if r["kind"] == "reads_record_line":
            corrected, orig = reeval_staging_mode()
            r["verdict"] = "CK_DEFECT_R4_FALSE_FAIL" if (r["r4_formal_result"] == "FAIL" and corrected == "PASS" and orig != "PASS") else "UNEXPECTED"
            details.append("RE_EVAL" + TAB + n + TAB + "corrected=" + corrected + TAB + "r4_original=" + orig
                           + TAB + "r4_formal_result=" + r["r4_formal_result"])
        elif r["kind"] == "negative_in":
            got = reeval[n]()
            r["verdict"] = "OK_NON_VACUOUS" if got.startswith("PASS") else "VACUOUS"
            if not got.startswith("PASS"):
                vacuous += 1
            details.append("RE_EVAL" + TAB + n + TAB + "correct_format_result=" + got)
        elif r["kind"] == "self_branch":
            r["verdict"] = "OK_COVERAGE_GAP" if r["r4_formal_result"] == "PASS" else "R4_FAIL_NOT_VACUOUS"
            details.append("SELF_BRANCH" + TAB + n + TAB + "r4_formal_result=" + r["r4_formal_result"]
                           + TAB + "shakedown_formal_branch_exercised=" + r["formal_branch_exercised_in_shakedown"])
        else:
            r["verdict"] = "OK" if r["r4_formal_result"] == "PASS" else "R4_FAIL"
    sweep_rows = len(rows)
    self_rows = len([r for r in rows if r["has_self_branch"] == "yes"])
    record_rows = len([r for r in rows if r["kind"] == "reads_record_line"])
    neg_rows = len([r for r in rows if r["kind"] == "negative_in"])
    out = os.path.join(EV, "CHECKER_SWEEP_S5R5.tsv")
    body = ["# CHECKER_SWEEP_S5R5.tsv -- static sweep of testing/d003/stage_s5r4/gate_check_s5r4.py (read only)",
            "# gate4_sha256=" + sha4,
            "# r4_formal_gate=" + os.path.relpath(g4, REPO) + " sha256=" + sha_f(g4),
            "# kind: reads_record_line = string-matches a RECORD line; self_branch = branches on the output path or the",
            "#       staging flag; negative_in = 'not in' / negated match that can pass vacuously; other = plain read.",
            "# every reads_record_line / negative_in check was re-evaluated on the R4 frozen data with the correct format."]
    body += details
    body.append(TAB.join(["check_name", "line", "kind", "record_format_ok", "has_self_branch",
                          "formal_branch_exercised_in_shakedown", "r4_formal_result", "verdict"]))
    for r in rows:
        body.append(TAB.join([r["check_name"], str(r["line"]), r["kind"], r["record_format_ok"],
                              r["has_self_branch"], r["formal_branch_exercised_in_shakedown"],
                              r["r4_formal_result"], r["verdict"]]))
    body.append("SUMMARY" + TAB + "SWEEP_ROWS" + TAB + str(sweep_rows))
    body.append("SUMMARY" + TAB + "SELF_BRANCH_ROWS" + TAB + str(self_rows))
    body.append("SUMMARY" + TAB + "RECORD_LINE_ROWS" + TAB + str(record_rows))
    body.append("SUMMARY" + TAB + "NEGATIVE_IN_ROWS" + TAB + str(neg_rows))
    body.append("SUMMARY" + TAB + "VACUOUS" + TAB + str(vacuous))
    body.append("SUMMARY" + TAB + "RE_EVAL_CORRECTED_PASS" + TAB
                + str(len([d for d in details if d.startswith("RE_EVAL") and "corrected=PASS" in d])))
    body.append("SUMMARY" + TAB + "RE_EVAL_R4_ORIGINAL_NOT_STAGING" + TAB
                + str(len([d for d in details if d.startswith("RE_EVAL") and "r4_original=not_staging" in d])))
    body.append("SUMMARY" + TAB + "R4_FORMAL_PASSES" + TAB
                + str(len([r for r in rows if r["r4_formal_result"] == "PASS"])))
    body.append("SUMMARY" + TAB + "R4_FORMAL_FAILS" + TAB
                + str(len([r for r in rows if r["r4_formal_result"] == "FAIL"])))
    body.append("SUMMARY" + TAB + "R4_GATE_SHA256" + TAB + sha_f(g4))
    open(out, "w", encoding="utf-8").write(NL.join(body) + NL)
    print("SWEEP_ROWS=%d SELF_BRANCH_ROWS=%d RECORD_LINE_ROWS=%d NEGATIVE_IN_ROWS=%d VACUOUS=%d"
          % (sweep_rows, self_rows, record_rows, neg_rows, vacuous))
    for d in details:
        print(d)
    print("WROTE " + os.path.relpath(out, REPO))
    return 0 if vacuous == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
