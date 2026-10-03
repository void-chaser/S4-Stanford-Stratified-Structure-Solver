"""Structure builders shared by the tests that need several pattern shapes.

Kept in one module so that the Clone test and the API test describe the same
geometries, and so the shape parameters can be asserted to be *distinct* in one
place.  That assertion matters: with equal parameters a circle, an ellipse, a
rectangle and a polygon can be optically equivalent at a given frequency, which
would make a Clone test pass without ever distinguishing the shape types.
"""

import math

import S4

__all__ = [
    "N_SLAB",
    "SHAPES",
    "DISTINCT_SHAPES",
    "build_patterned_slab",
    "build_scalar_stack",
    "build_tensor_stack",
    "read_rt",
]

N_SLAB = math.sqrt(12.0)

#: Every shape applied to the same slab, as keyword arguments for
#: ``S4_Simulation.SetRegion*``.  The parameters differ deliberately, including
#: a non-zero rotation where the method accepts one, so that a mis-copied shape
#: cannot coincidentally produce the same answer as the original.
SHAPES = {
    "circle": {
        "method": "SetRegionCircle",
        "args": ("Slab", "Air", (0.0, 0.0), 0.25),
    },
    "ellipse": {
        "method": "SetRegionEllipse",
        "args": ("Slab", "Air", (0.05, -0.05), 20.0, (0.30, 0.12)),
    },
    "rectangle": {
        "method": "SetRegionRectangle",
        "args": ("Slab", "Air", (-0.1, 0.1), 35.0, (0.22, 0.35)),
    },
    "polygon": {
        "method": "SetRegionPolygon",
        "args": ("Slab", "Air", (0.0, 0.0), 15.0,
                 ((0.0, 0.0), (0.35, 0.05), (0.30, 0.30), (0.05, 0.20))),
    },
}

#: Two shapes whose parameters are clearly different; used to prove that the
#: test can tell shapes apart at all.
DISTINCT_SHAPES = ("circle", "polygon")


def build_patterned_slab(shape=None, num_basis=81, freq=0.5):
    """Silicon slab with an air pattern, between two semi-infinite air layers.

    Parameters
    ----------
    shape : str or None
        Key into ``SHAPES``; None leaves the slab unpatterned.
    """
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    sim.AddMaterial("Air", 1)
    sim.AddMaterial("Slab", N_SLAB ** 2)
    sim.AddLayer("Above", 0, "Air")
    sim.AddLayer("Slab", 0.5, "Slab")
    if shape is not None:
        spec = SHAPES[shape]
        getattr(sim, spec["method"])(*spec["args"])
    sim.AddLayerCopy("Below", 0, "Above")
    sim.SetFrequency(freq)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    return sim


def build_scalar_stack(num_basis=1, freq=0.4):
    """Scalar materials only, with a pattern and a layer copy."""
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    sim.AddMaterial("Air", 1)
    sim.AddMaterial("Si", 12)
    sim.AddMaterial("Lossy", 12 + 0.5j)
    sim.AddLayer("Top", 0, "Air")
    sim.AddLayer("Slab", 0.5, "Si")
    sim.SetRegionCircle("Slab", "Lossy", (0, 0), 0.2)
    sim.AddLayerCopy("Bot", 0, "Top")
    sim.SetFrequency(freq)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    return sim


def build_tensor_stack(num_basis=25, freq=0.4):
    """Includes an anisotropic 3x3 tensor material.

    The tensor is spelled as three rows of complex entries; the binding rejects
    the flat "real, imaginary" pair form.
    """
    sim = S4.New(Lattice=((1, 0), (0, 1)), NumBasis=num_basis)
    sim.AddMaterial("Air", 1)
    sim.AddMaterial("Si", 12)
    sim.AddMaterial("Aniso", ((12 + 0j, 0.5 + 0j, 0j),
                              (0.5 + 0j, 12 + 0j, 0j),
                              (0j, 0j, 4 + 0j)))
    sim.AddLayer("Top", 0, "Air")
    sim.AddLayer("Mid", 0.5, "Aniso")
    sim.SetRegionCircle("Mid", "Si", (0, 0), 0.2)
    sim.AddLayerCopy("Bot", 0, "Top")
    sim.SetFrequency(freq)
    sim.SetExcitationPlanewave((0, 0), 1, 0)
    return sim


def read_rt(sim, top, bottom, z_offset=0.0):
    """Power reflectance and transmittance.

    Sign convention measured on this binding: the incident flux is
    ``cos(theta)/n_above`` and the backward flux in the incidence layer is
    negative, so ``R = -backward/incident``.
    """
    inc, refl = sim.GetPowerFlux(top, z_offset)
    trans, _ = sim.GetPowerFlux(bottom, z_offset)
    if inc.real == 0.0:
        raise AssertionError("incident power is zero")
    return -refl.real / inc.real, trans.real / inc.real
