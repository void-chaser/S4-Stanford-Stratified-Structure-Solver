"""Smoke tests for the compiled S4 extension and its basic RCWA workflow."""

import math
import unittest

import S4


class PythonBindingTests(unittest.TestCase):
    def make_slab(self, patterned=False):
        sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=25 if patterned else 1)
        sim.AddMaterial("Air", 1)
        sim.AddMaterial("Slab", 12)
        sim.AddLayer("Top", 0, "Air")
        sim.AddLayer("Middle", 0.5, "Slab")
        if patterned:
            sim.SetRegionCircle("Middle", "Air", (0, 0), 0.2)
        sim.AddLayerCopy("Bottom", 0, "Top")
        sim.SetFrequency(0.4)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        return sim

    def test_uniform_slab_conserves_power(self):
        sim = self.make_slab()
        incident, reflected = sim.GetPowerFlux("Top")
        transmitted, backwards = sim.GetPowerFlux("Bottom")
        self.assertAlmostEqual(incident.real, 1, places=10)
        self.assertAlmostEqual(backwards.real, 0, places=10)
        self.assertAlmostEqual(incident.real + reflected.real, transmitted.real, places=10)
        self.assertTrue(math.isfinite(transmitted.real))

    def test_patterned_slab_and_options(self):
        sim = self.make_slab(patterned=True)
        sim.SetVerbosity(0)
        sim.SetOptions(LanczosSmoothing={"Width": 1.0, "Power": 2})
        incident, reflected = sim.GetPowerFlux("Top")
        transmitted, _ = sim.GetPowerFlux("Bottom")
        self.assertAlmostEqual(incident.real + reflected.real, transmitted.real, places=8)
        self.assertTrue(math.isfinite(transmitted.real))

    def test_material_update_recomputes_solution(self):
        sim = S4.New(((1, 0), (0, 1)), 1)
        sim.AddMaterial("Air", 1)
        sim.AddMaterial("Slab", 12)
        sim.SetLayer("Top", 0, "Air")
        sim.SetLayer("Middle", 0.5, "Slab")
        sim.AddLayerCopy("Bottom", 0, "Top")
        sim.SetFrequency(0.4)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        before = sim.GetPowerFlux("Bottom")[0].real
        sim.SetMaterial("Slab", 4)
        after = sim.GetPowerFlux("Bottom")[0].real
        self.assertGreater(abs(after - before), 0.1)

    def test_invalid_input_raises_instead_of_crashing(self):
        with self.assertRaises(ValueError):
            S4.New(((1, 0), (0, 1)), 0)
        sim = S4.New(((1, 0), (0, 1)), 1)
        with self.assertRaises(ValueError):
            sim.AddLayer("Unknown", 0, "Missing")
        sim.AddMaterial("Air", 1)
        sim.AddLayer("Only", 0, "Air")
        sim.SetFrequency(0.4)
        sim.SetExcitationPlanewave((0, 0), 1, 0)
        with self.assertRaisesRegex(RuntimeError, "At least two layers"):
            sim.GetPowerFlux("Only")


if __name__ == "__main__":
    unittest.main()
