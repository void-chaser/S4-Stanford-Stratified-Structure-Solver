#!/usr/bin/env python3
"""Mirror of examples/2d/Fan_PRB_65_2002/fig12.lua in Python.

Geometry and parameters are copied verbatim from the Lua example so that the two
frontends can be compared on identical input:

    lattice          square, a = 1
    NumBasis         100
    materials        Silicon eps = 12, Vacuum eps = 1
    layers           AirAbove (semi-infinite), Slab (d = 0.5, patterned),
                     AirBelow (copy of AirAbove)
    pattern          circle of vacuum, radius 0.2, centred at the origin
    excitation       normal incidence, s-polarised, unit amplitude
    sweep            freq = 0.25 .. 0.27 step 0.003

Output columns are ``freq  T  R``, normalised by the incident power, which is
the unambiguous form both frontends can produce (the Lua example prints the raw
signed Poynting flux, whose sign convention differs between the frontends).
"""

import sys

import S4


def main():
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=100)
    sim.AddMaterial("Silicon", 12)
    sim.AddMaterial("Vacuum", 1)

    sim.AddLayer("AirAbove", 0, "Vacuum")
    sim.AddLayer("Slab", 0.5, "Silicon")
    sim.SetRegionCircle("Slab", "Vacuum", (0, 0), 0.2)
    sim.AddLayerCopy("AirBelow", 0, "AirAbove")

    sim.SetExcitationPlanewave((0, 0), 1, 0)

    # The Lua loop is `for freq=0.25,0.27,0.003`, which yields 7 values.
    freq = 0.25
    while freq <= 0.27 + 1e-12:
        sim.SetFrequency(freq)
        inc, refl = sim.GetPowerFlux("AirAbove", 0.0)
        trans, _ = sim.GetPowerFlux("AirBelow", 0.0)
        inc = inc.real
        print("%.12g\t%.12g\t%.12g" % (freq, trans.real / inc, -refl.real / inc))
        freq += 0.003
    sys.stdout.flush()


if __name__ == "__main__":
    main()
