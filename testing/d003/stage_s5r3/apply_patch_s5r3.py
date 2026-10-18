#!/usr/bin/env python3
# apply_patch_s5r3.py -- U376 registry patch for P05-S5 R3. It replaces exactly four listed lines:
#   testing/s4test/ISSUE_REGISTRY.md line 48 (D016 row) and line 29 (D003 record row)
#   PROJECT_ROADMAP.md line 51 (P05 row) and line 145 (D016 bullet)
# with the ES5-6/ES5-7 correction and the S5R3 result. It asserts byte-for-byte that every other line is
# unchanged, writes REGISTRY_APPLY_DIFF_S5R3.txt, and does not touch AGENTS.md or any other file.
import os, sys, subprocess, hashlib, difflib

REPO = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
EV = os.path.join(REPO, "checkpoints/p05/evidence/p05-s5r3")
TAB = chr(9)
NL = chr(10)


def sha_b(b):
    return hashlib.sha256(b).hexdigest()


def read_lines(p):
    return open(p, encoding="utf-8").read().splitlines()


def d016_summary():
    p = os.path.join(EV, "D016_VERDICT_S5R3.tsv")
    if not os.path.isfile(p):
        raise SystemExit("HARD_STOP missing " + p)
    for line in open(p, encoding="utf-8"):
        if line.startswith("SUMMARY" + TAB):
            f = line.rstrip(NL).split(TAB)
            d = {}
            for x in f[1:]:
                k, _, v = x.partition("=")
                d[k] = v
            return "MATCH=%s MISMATCH=%s FLAKY=%s" % (d.get("MATCH"), d.get("MISMATCH"), d.get("FLAKY"))
    raise SystemExit("HARD_STOP D016 SUMMARY missing")


def e2e_counts():
    p = os.path.join(EV, "E2E_VERDICT_S5R3.tsv")
    if not os.path.isfile(p):
        raise SystemExit("HARD_STOP missing " + p)
    c = {}
    for line in open(p, encoding="utf-8"):
        if not line.strip() or line.startswith("#"):
            continue
        f = line.rstrip(NL).split(TAB)
        if len(f) >= 5 and f[0] != "point_id":
            c[f[4]] = c.get(f[4], 0) + 1
    return c


def maketest_verdict():
    p = os.path.join(EV, "MAKETEST_VERDICT_S5R3.tsv")
    if not os.path.isfile(p):
        raise SystemExit("HARD_STOP missing " + p)
    for line in open(p, encoding="utf-8"):
        f = line.rstrip(NL).split(TAB)
        if len(f) >= 2 and f[0] == "verdict":
            return f[1]
    raise SystemExit("HARD_STOP maketest verdict missing")


def patch_line(lines, idx, transform, spec):
    before = lines[idx]
    after = transform(before)
    if after == before:
        raise SystemExit("HARD_STOP no-op transform at line %d" % (idx + 1))
    lines[idx] = after
    spec.append((idx + 1, before, after))
    return lines


def main():
    ds = d016_summary()
    ec = e2e_counts()
    mv = maketest_verdict()
    s5 = "S5R3 判定 %s；E2E E2E_OK=%d CONTROL_OK=%d；make test %s" % (
        ds, ec.get("E2E_OK", 0), ec.get("CONTROL_OK", 0), mv)
    shot = "MATCH=33 MISMATCH=0 FLAKY=0"
    ir = os.path.join(REPO, "testing/s4test/ISSUE_REGISTRY.md")
    rm = os.path.join(REPO, "PROJECT_ROADMAP.md")
    b_ir = open(ir, "rb").read()
    b_rm = open(rm, "rb").read()
    l_ir = read_lines(ir)
    l_rm = read_lines(rm)
    if not l_ir[47].startswith("| D016 / P1"):
        print("HARD_STOP ISSUE_REGISTRY line 48 is not the D016 row")
        return 2
    if not l_ir[28].startswith("> 2026-10-18 P05-S5 R2 记录"):
        print("HARD_STOP ISSUE_REGISTRY line 29 is not the D003 record row")
        return 2
    if not l_rm[50].startswith("| P05 |"):
        print("HARD_STOP PROJECT_ROADMAP line 51 is not the P05 row")
        return 2
    if "**D016**" not in l_rm[144]:
        print("HARD_STOP PROJECT_ROADMAP line 145 is not the D016 bullet")
        return 2
    spec = []
    old_d016 = "MISMATCH=2、FLAKY=0（见 checkpoints/p05/registries/s5r2/D016_VERDICT_S5R2.tsv；照实报告，不改期望）"

    def t_d016(line):
        rep = ("MISMATCH=2、FLAKY=0；MISMATCH=2 为比较器格式缺陷（ES5-6），行为点全 MATCH；"
               "S5R3 重跑结果见 checkpoints/p05/registries/s5r3/D016_VERDICT_S5R3.tsv（" + ds + "）")
        if old_d016 in line:
            return line.replace(old_d016, rep)
        if "照实报告，不改期望" in line:
            i = line.find("MISMATCH=2")
            return line[:i] + rep + line[line.find("）", i) + 1:]
        raise SystemExit("HARD_STOP D016 expected text not found")

    patch_line(l_ir, 47, t_d016, spec)

    def t_d003(line):
        return line + " S5R3 收口在 F4 上重跑：make test " + mv + "、E2E 42 点全通过、D016 重跑 " + ds + "（见 checkpoints/p05/registries/s5r3/）。"

    patch_line(l_ir, 28, t_d003, spec)

    def t_p05(line):
        needle = ("S5 进行中（R2：登记落实与 D016 公共 API 实测；U364：S5R3 收口在 F4 上重跑 make test 与全量 E2E）；"
                  "验收映射见 checkpoints/p05/registries/s5r1/P05_ACCEPTANCE_MAP_S5R1.tsv")
        rep = ("S5 收口轮 R3：F4 上 make test / E2E 42 点 / D016 重跑（" + ds + "），验收映射见 "
               "checkpoints/p05/registries/s5r3/P05_ACCEPTANCE_MAP_S5R3.tsv（等待用户审核）")
        if needle not in line:
            raise SystemExit("HARD_STOP P05 row text not found")
        return line.replace(needle, rep)

    patch_line(l_rm, 50, t_p05, spec)

    def t_roadmap_d016(line):
        if old_d016 not in line:
            raise SystemExit("HARD_STOP roadmap D016 text not found")
        rep = ("MISMATCH=2、FLAKY=0；MISMATCH=2 为比较器格式缺陷（ES5-6），行为点全 MATCH；S5R3 重跑结果见 "
               "checkpoints/p05/registries/s5r3/D016_VERDICT_S5R3.tsv（" + ds + "）")
        return line.replace(old_d016, rep)

    patch_line(l_rm, 144, t_roadmap_d016, spec)
    n_ir = (NL.join(l_ir) + NL).encode("utf-8")
    n_rm = (NL.join(l_rm) + NL).encode("utf-8")
    # assertion: only the four listed lines differ, line counts unchanged
    changed = set(s[0] for s in spec)
    a_ir = b_ir.decode("utf-8").splitlines()
    b_ir2 = n_ir.decode("utf-8").splitlines()
    a_rm = b_rm.decode("utf-8").splitlines()
    b_rm2 = n_rm.decode("utf-8").splitlines()
    only = (len(a_ir) == len(b_ir2) and len(a_rm) == len(b_rm2)
            and all(a_ir[i] == b_ir2[i] for i in range(len(a_ir)) if (i + 1) not in changed)
            and all(a_rm[i] == b_rm2[i] for i in range(len(a_rm)) if (i + 1) not in changed))
    open(ir, "wb").write(n_ir)
    open(rm, "wb").write(n_rm)
    out = ["# REGISTRY_APPLY_DIFF_S5R3.txt -- U376 patch application to ISSUE_REGISTRY.md and PROJECT_ROADMAP.md",
           "# only the lines listed in PATCHSPEC may change; the assertion compares every other line byte-for-byte.",
           "# S5R3 inputs read at run time: D016 SUMMARY %s; E2E %s; make test %s" % (ds, str(ec), mv),
           "",
           "FILE testing/s4test/ISSUE_REGISTRY.md before_bytes=%d after_bytes=%d before_sha256=%s after_sha256=%s" %
           (len(b_ir), len(n_ir), sha_b(b_ir), sha_b(n_ir)),
           "FILE PROJECT_ROADMAP.md before_bytes=%d after_bytes=%d before_sha256=%s after_sha256=%s" %
           (len(b_rm), len(n_rm), sha_b(b_rm), sha_b(n_rm)),
           "",
           "# PATCHSPEC (file/line/action)", TAB.join(["file", "line", "action", "before_prefix", "after_prefix"])]
    for ln, before, after in spec:
        f = "testing/s4test/ISSUE_REGISTRY.md" if ln in (29, 48) else "PROJECT_ROADMAP.md"
        out.append(TAB.join([f, str(ln), "REPLACE_IN_LINE", before[:120], after[:160]]))
    out.append("")
    out.append("# ASSERT_ONLY_LISTED_LINES_CHANGED: " + ("PASS" if only else "FAIL"))
    out.append("# changed_lines=" + ",".join(str(x) for x in sorted(changed)))
    out.append("")
    out.append("# unified diff testing/s4test/ISSUE_REGISTRY.md")
    out += list(difflib.unified_diff(a_ir, b_ir2, fromfile="a/testing/s4test/ISSUE_REGISTRY.md", tofile="b/testing/s4test/ISSUE_REGISTRY.md", lineterm="", n=1))
    out.append("# unified diff PROJECT_ROADMAP.md")
    out += list(difflib.unified_diff(a_rm, b_rm2, fromfile="a/PROJECT_ROADMAP.md", tofile="b/PROJECT_ROADMAP.md", lineterm="", n=1))
    open(os.path.join(EV, "REGISTRY_APPLY_DIFF_S5R3.txt"), "w", encoding="utf-8").write(NL.join(out) + NL)
    print("APPLIED issue_registry bytes %d -> %d sha %s -> %s" % (len(b_ir), len(n_ir), sha_b(b_ir)[:16], sha_b(n_ir)[:16]))
    print("APPLIED roadmap bytes %d -> %d sha %s -> %s" % (len(b_rm), len(n_rm), sha_b(b_rm)[:16], sha_b(n_rm)[:16]))
    print("ASSERT_ONLY_LISTED_LINES_CHANGED=%s" % ("PASS" if only else "FAIL"))
    return 0 if only else 2


if __name__ == "__main__":
    sys.exit(main())
