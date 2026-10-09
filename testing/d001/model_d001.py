#!/usr/bin/env python3
"""P01 portable model for the first D001 matrix (f = 0.427, normal incidence, s-pol).

Import-side-effect free: importing this module must NOT import S4, construct a
simulation or trigger a solve.  Every function that needs S4 receives the module
as an explicit argument (`build_simulation(s4, case)`), so a caller can load a
specific isolated subject first and then hand it in.

Provenance of the model parameters: the frozen Task010 model settings, recovered
from `audit-workspace/010/010-20261002T104530Z-602b34dc/scripts/run_one_case_010.py`
and `.../CASE_MATRIX.json` (physics_common).  The parameters were read from the
historical runner; no historical result value is used here.

The 12 entries in ``cases/d001_first_matrix.json`` are variant-neutral
(N in {1,9} x {A,B,C} x repeat in {1,2}).  P02 is expected to run these against
two variants, i.e. 24 physical cases; P01 executes zero physical cases.
"""

import json
import math
import os

# --- frozen model constants (Task010 physics_common) ------------------------

FREQUENCY = 0.427
LATTICE = ((1, 0), (0, 1))
AMBIENT_EPSILON = 1.0
FILM_EPSILON_SCALAR = 4.0
FILM_EPSILON_TENSOR = ((4.0, 0.0, 0.0), (0.0, 4.0, 0.0), (0.0, 0.0, 4.0))
AIRTOP_THICKNESS = 0.0
FILM_THICKNESS = 0.25
AIRBOTTOM_THICKNESS = 0.0
CIRCLE_CENTER = (0.0, 0.0)
CIRCLE_RADIUS = 0.2
INCIDENCE_ANGLES = (0.0, 0.0)
ORDER = 0
S_AMPLITUDE = complex(1.0, 0.0)
P_AMPLITUDE = complex(0.0, 0.0)
SET_OPTIONS_CALLED = False

REPRESENTATIONS = ("A_SCALAR", "B_SAME_MATERIAL_CIRCLE", "C_ISOTROPIC_TENSOR")
BASIS_SET = (1, 9)
REPEATS = (1, 2)

DEFAULT_CASES = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "cases", "d001_first_matrix.json")


def case_key(num_basis, representation, repeat):
    """Variant-neutral case key, e.g. 'N9|B_SAME_MATERIAL_CIRCLE|r2'."""
    return "N%d|%s|r%d" % (num_basis, representation, repeat)


def load_cases(path=None):
    """Return the list of 12 variant-neutral model entries."""
    with open(path or DEFAULT_CASES, encoding="utf-8") as fh:
        doc = json.load(fh)
    return doc["cases"]


def load_case_document(path=None):
    with open(path or DEFAULT_CASES, encoding="utf-8") as fh:
        return json.load(fh)


def check_cases(cases):
    """Structural self-check: 12 complete, unique entries, exact Cartesian set."""
    problems = []
    if len(cases) != 12:
        problems.append("expected 12 cases, found %d" % len(cases))
    expected = set()
    for n in BASIS_SET:
        for rep in REPRESENTATIONS:
            for r in REPEATS:
                expected.add((n, rep, r))
    seen = set()
    required = ("case_key", "requested_num_basis", "representation", "repeat",
                "frequency", "polarization")
    for c in cases:
        for field in required:
            if field not in c:
                problems.append("case missing field %r: %r" % (field, c))
        triple = (c.get("requested_num_basis"), c.get("representation"), c.get("repeat"))
        if triple in seen:
            problems.append("duplicate case triple %r" % (triple,))
        seen.add(triple)
        if c.get("frequency") != FREQUENCY:
            problems.append("case %r has unexpected frequency %r" % (c.get("case_key"), c.get("frequency")))
        if c.get("polarization") != "s":
            problems.append("case %r has unexpected polarization %r" % (c.get("case_key"), c.get("polarization")))
        if "variant" in c:
            problems.append("case %r must stay variant-neutral" % (c.get("case_key"),))
    if seen != expected:
        problems.append("case set != N{1,9} x A/B/C x repeat{1,2}; missing=%r extra=%r"
                        % (sorted(expected - seen), sorted(seen - expected)))
    return problems


def build_simulation(s4, case):
    """Build (but do not solve) the D001 simulation for one case.

    `s4` is the already-imported S4 module for the subject under test.  Call
    order is copied from the historical runner; SetOptions is deliberately never
    called (Task010 recorded setOptions_called=false).
    """
    rep = case["representation"]
    if rep not in REPRESENTATIONS:
        raise ValueError("unknown representation %r" % (rep,))
    sim = s4.New(Lattice=LATTICE, NumBasis=case["requested_num_basis"])
    sim.SetMaterial(Name="Air", Epsilon=AMBIENT_EPSILON)
    if rep == "C_ISOTROPIC_TENSOR":
        sim.SetMaterial(Name="Film", Epsilon=FILM_EPSILON_TENSOR)
    else:
        sim.SetMaterial(Name="Film", Epsilon=FILM_EPSILON_SCALAR)
    sim.AddLayer(Name="AirTop", Thickness=AIRTOP_THICKNESS, S4_Material="Air")
    sim.AddLayer(Name="Film", Thickness=FILM_THICKNESS, S4_Material="Film")
    sim.AddLayer(Name="AirBottom", Thickness=AIRBOTTOM_THICKNESS, S4_Material="Air")
    if rep == "B_SAME_MATERIAL_CIRCLE":
        sim.SetRegionCircle(S4_Layer="Film", S4_Material="Film",
                            Center=CIRCLE_CENTER, Radius=CIRCLE_RADIUS)
    sim.SetExcitationPlanewave(IncidenceAngles=INCIDENCE_ANGLES,
                               sAmplitude=S_AMPLITUDE, pAmplitude=P_AMPLITUDE,
                               Order=ORDER)
    sim.SetFrequency(case["frequency"])
    return sim


def read_fluxes(sim):
    """P02 helper: one solve serves both reads; four complex fluxes are kept."""
    top_f, top_b = sim.GetPowerFlux(S4_Layer="AirTop", zOffset=0.0)
    bot_f, bot_b = sim.GetPowerFlux(S4_Layer="AirBottom", zOffset=0.0)
    return {
        "AirTop_forward": complex(top_f),
        "AirTop_backward": complex(top_b),
        "AirBottom_forward": complex(bot_f),
        "AirBottom_backward": complex(bot_b),
    }


def compute_RT(fluxes):
    """R = -Re(top backward)/incident, T = Re(bottom forward)/incident.

    incident = Re(AirTop.forward).  All four complex flux components are kept by
    the caller; this helper only performs the recorded sign/normalisation.
    """
    inc = fluxes["AirTop_forward"].real
    if not math.isfinite(inc) or inc <= 0.0:
        raise ValueError("non-finite or non-positive incident flux: %r" % (inc,))
    r = -fluxes["AirTop_backward"].real / inc
    t = fluxes["AirBottom_forward"].real / inc
    return {"incident": inc, "R": r, "T": t, "RplusT": r + t}


def main():
    import argparse
    ap = argparse.ArgumentParser(description="P01 D001 model case self-check")
    ap.add_argument("--cases", default=None)
    ap.add_argument("--json", default=None)
    args = ap.parse_args()
    cases = load_cases(args.cases)
    problems = check_cases(cases)
    out = {
        "module": "model_d001.py",
        "imports_S4": "S4" in __import__("sys").modules,
        "case_count": len(cases),
        "case_keys": [c["case_key"] for c in cases],
        "problems": problems,
        "self_check_pass": not problems,
        "physical_calls_executed": 0,
    }
    text = json.dumps(out, indent=2)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)
    return 0 if not problems else 2


if __name__ == "__main__":
    raise SystemExit(main())
