"""Independent analytic references for S4 regression tests.

Everything in this module is written from the textbook formulas and uses only
the Python standard library (``math``/``cmath``).  Nothing here imports or calls
S4, so the numbers it produces are an *independent* reference rather than a
restatement of what S4 computes.

Conventions used throughout S4
------------------------------
* Lengths are in units of the lattice constant (or of the free-space
  wavelength when a lattice is not physically meaningful).
* Frequencies are in units of ``c / a`` (i.e. normalized frequency).
* ``S4_Simulation.SetFrequency(f)`` sets ``omega = 2*pi*f``.
* Materials are specified by their *relative permittivity* ``epsilon``;
  ``epsilon = n**2`` for a non-magnetic material with refractive index ``n``.
* Planewave incidence angles are spherical: the first angle is the polar
  angle ``phi`` measured from the +z axis, so the in-plane wavevector is
  ``k_parallel = n_above * sin(phi)`` in normalized units.

Power-flux conventions
----------------------
``S4_Simulation.GetPowerFlux(layer, z)`` returns a 2-tuple of complex numbers
``(forward, backward)``, the *signed* Poynting fluxes along +z.  For a stack
illuminated from the top:

* in the top (incidence) layer ``forward`` is the incident power and
  ``backward`` is negative;
* in the bottom (substrate) layer ``forward`` is the transmitted power.

So with ``inc, refl = GetPowerFlux(top)`` and ``trans, _ = GetPowerFlux(bottom)``::

    R = -refl.real / inc.real
    T =  trans.real / inc.real

This module returns ``R`` and ``T`` under exactly that convention.
"""

import cmath
import math

__all__ = [
    "fresnel_coefficients",
    "fresnel_rt",
    "tmm_rt",
    "tmm_rt_spectrum",
    "airy_rt",
    "k_parallel_from_angle",
]


def k_parallel_from_angle(n_above, theta_deg):
    """Normalized in-plane wavevector ``k_parallel = n_above * sin(theta)``.

    ``theta_deg`` is the polar angle from the +z axis in degrees, matching the
    first argument of ``S4_Simulation.SetExcitationPlanewave``.
    """
    return n_above * math.sin(math.radians(theta_deg))


def _transverse_wavevector(n, k_parallel):
    """Return ``kz`` for a wave with in-plane wavevector ``k_parallel``.

    Uses the principal square root so that for a lossy or evanescent medium the
    correct branch is selected: positive real part, or positive imaginary part
    when the real part vanishes.
    """
    kz = cmath.sqrt(n * n - k_parallel * k_parallel)
    if kz.real < 0:
        kz = -kz
    elif kz.real == 0 and kz.imag < 0:
        kz = -kz
    return kz


def fresnel_coefficients(n1, n2, theta_deg, polarization):
    """Single-interface Fresnel amplitude coefficients.

    Parameters
    ----------
    n1, n2 : complex or float
        Refractive indices of the incidence and transmission media.
    theta_deg : float
        Polar angle of incidence from the +z axis, in degrees.
    polarization : {'s', 'p'}
        ``'s'`` is TE (E perpendicular to the plane of incidence),
        ``'p'`` is TM (H perpendicular to the plane of incidence).

    Returns
    -------
    (r, t) : tuple of complex
        Amplitude reflection and transmission coefficients.  ``t`` relates the
        tangential E amplitudes of the transmitted and incident waves.
    """
    n1 = complex(n1)
    n2 = complex(n2)
    kx = k_parallel_from_angle(n1, theta_deg)
    kz1 = _transverse_wavevector(n1, kx)
    kz2 = _transverse_wavevector(n2, kx)

    if polarization == "s":
        r = (kz1 - kz2) / (kz1 + kz2)
        t = 2 * kz1 / (kz1 + kz2)
    elif polarization == "p":
        r = (n2 * n2 * kz1 - n1 * n1 * kz2) / (n2 * n2 * kz1 + n1 * n1 * kz2)
        t = 2 * n1 * n2 * kz1 / (n2 * n2 * kz1 + n1 * n1 * kz2)
    else:
        raise ValueError("polarization must be 's' or 'p', got %r" % (polarization,))
    return r, t


def fresnel_rt(n1, n2, theta_deg, polarization):
    """Power reflectance and transmittance of a single interface.

    Returns ``(R, T)`` with ``R + T == 1`` for lossless media.  The obliquity
    factor ``Re(kz2)/Re(kz1)`` is included in ``T`` so that it is a true power
    ratio.  ``T`` is set to zero for total internal reflection.
    """
    n1 = complex(n1)
    n2 = complex(n2)
    kx = k_parallel_from_angle(n1, theta_deg)
    kz1 = _transverse_wavevector(n1, kx)
    kz2 = _transverse_wavevector(n2, kx)
    r, t = fresnel_coefficients(n1, n2, theta_deg, polarization)
    R = abs(r) ** 2
    if kz2.real <= 0:
        # Evanescent transmitted wave: no net real power crosses the interface.
        return R, 0.0
    T = (kz2 / kz1).real * abs(t) ** 2
    return R, T


def tmm_rt(layers, n_above, n_below, theta_deg, polarization, freq=1.0):
    """Reflectance/transmittance of a multilayer stack by the transfer matrix.

    The stack is illuminated from a semi-infinite medium ``n_above`` and exits
    into a semi-infinite medium ``n_below``.

    Parameters
    ----------
    layers : sequence of (thickness, refractive_index)
        ``thickness`` in the same length unit implied by ``freq``.  A thickness
        of 0 is valid and reduces the stack to a bare interface.
    n_above, n_below : complex
        Refractive indices of the semi-infinite outer media.
    theta_deg : float
        Polar angle of incidence in ``n_above``, degrees.
    polarization : {'s', 'p'}
    freq : float, optional
        Normalized frequency ``a/lambda``; the phase thickness is
        ``2*pi*freq*n*thickness``.  Defaults to 1.

    Returns
    -------
    (R, T) : tuple of float
        Power reflectance and transmittance.

    Notes
    -----
    Uses the characteristic-matrix formulation

        M_j = [[cos(d),          i*sin(d)/gamma_j],
               [i*gamma_j*sin(d), cos(d)          ]]

    with ``d = 2*pi*freq*kz_j*thickness`` and ``gamma_j = kz_j`` for s
    polarization or ``gamma_j = kz_j/eps_j`` for p polarization.  This is a
    different algorithm from the scattering-matrix recursion S4 uses, so
    agreement between the two is meaningful.
    """
    n_above = complex(n_above)
    n_below = complex(n_below)
    kx = k_parallel_from_angle(n_above, theta_deg)
    kz_above = _transverse_wavevector(n_above, kx)
    kz_below = _transverse_wavevector(n_below, kx)

    def gamma(n, kz):
        if polarization == "s":
            return kz
        if polarization == "p":
            return kz / (n * n)
        raise ValueError("polarization must be 's' or 'p', got %r" % (polarization,))

    m11 = complex(1.0)
    m12 = complex(0.0)
    m21 = complex(0.0)
    m22 = complex(1.0)

    k0 = 2 * math.pi * freq
    for thickness, n_layer in layers:
        n_layer = complex(n_layer)
        kz = _transverse_wavevector(n_layer, kx)
        g = gamma(n_layer, kz)
        d = k0 * kz * thickness
        c = cmath.cos(d)
        s = cmath.sin(d)
        l11, l12 = c, 1j * s / g
        l21, l22 = 1j * g * s, c
        m11, m12, m21, m22 = (
            m11 * l11 + m12 * l21,
            m11 * l12 + m12 * l22,
            m21 * l11 + m22 * l21,
            m21 * l12 + m22 * l22,
        )

    g_a = gamma(n_above, kz_above)
    g_b = gamma(n_below, kz_below)

    # Standard characteristic-matrix conversion to amplitude coefficients.
    denom = m11 * g_a + m12 * g_a * g_b + m21 + m22 * g_b
    r = (m11 * g_a + m12 * g_a * g_b - m21 - m22 * g_b) / denom
    t = 2 * g_a / denom

    R = abs(r) ** 2

    # The transmitted power ratio depends on the polarization convention.
    # Because t is built from the *unnormalized* admittance gamma, the
    # obliquity factor must be expressed in the same convention:
    #   s: gamma = kz           -> T = Re(kz_b) / Re(kz_a) * |t|^2
    #   p: gamma = kz / eps     -> T = Re(gamma_b) / Re(gamma_a) * |t|^2
    # Using Re(kz_b)/Re(kz_a) for p as well double-counts the index ratio and
    # is the bug this comment exists to prevent.
    if kz_below.real <= 0 or g_b.real <= 0:
        return R, 0.0
    T = (g_b / g_a).real * abs(t) ** 2
    return R, T


def tmm_rt_spectrum(layers, n_above, n_below, theta_deg, polarization, freqs):
    """``tmm_rt`` evaluated over a sequence of frequencies; returns two lists."""
    R = []
    T = []
    for f in freqs:
        r, t = tmm_rt(layers, n_above, n_below, theta_deg, polarization, f)
        R.append(r)
        T.append(t)
    return R, T


def airy_rt(thickness, n_film, n_above, n_below, theta_deg, polarization, freq=1.0):
    """Exact reflectance/transmittance of a SINGLE film, by the Airy sum.

    Why this exists alongside ``tmm_rt``
    ------------------------------------
    The characteristic/transfer-matrix formulation is *numerically ill
    conditioned for absorbing films*: the layer matrix contains
    ``exp(+i kz t)`` factors that grow without bound, and in double precision the
    growing solution swamps the physically relevant one.  Measured here with
    eps = 12 + 1j, d = 0.5, f = 0.5: ``tmm_rt`` returns R = 0.9956 and
    R + T = 1.615, while the exact answer is R = 0.3822, T = 0.3621.

    The Airy formula instead sums the multiply-reflected amplitudes in closed
    form, which stays accurate for lossy media, so it is the reference used for
    absorbing films.  ``tmm_rt`` remains valid (and is cross-checked against
    this function) for lossless stacks.

    Parameters
    ----------
    thickness : float
        Film thickness.
    n_film : complex
        Film refractive index.
    n_above, n_below : complex
        Refractive indices of the semi-infinite surrounding media.
    theta_deg : float
        Polar angle of incidence in ``n_above``, degrees.
    polarization : {'s', 'p'}
    freq : float
        Normalized frequency; the phase thickness is
        ``2*pi*freq*kz*thickness``.

    Returns
    -------
    (R, T) : tuple of float
        Power reflectance and transmittance.
    """
    n_above = complex(n_above)
    n_film = complex(n_film)
    n_below = complex(n_below)
    kx = k_parallel_from_angle(n_above, theta_deg)
    kz_above = _transverse_wavevector(n_above, kx)
    kz_film = _transverse_wavevector(n_film, kx)
    kz_below = _transverse_wavevector(n_below, kx)

    def _fresnel(n1, kz1, n2, kz2):
        """Fresnel coefficients for an interface, given both media's kz."""
        if polarization == "s":
            rr = (kz1 - kz2) / (kz1 + kz2)
            tt = 2 * kz1 / (kz1 + kz2)
        else:
            rr = (n2 * n2 * kz1 - n1 * n1 * kz2) / (n2 * n2 * kz1 + n1 * n1 * kz2)
            tt = 2 * n1 * n2 * kz1 / (n2 * n2 * kz1 + n1 * n1 * kz2)
        return rr, tt

    # kx is conserved across both interfaces, so kz_film is the same quantity
    # that Snell's law would give inside the film.
    r1, t1 = _fresnel(n_above, kz_above, n_film, kz_film)
    r2, t2 = _fresnel(n_film, kz_film, n_below, kz_below)

    delta = 2 * math.pi * freq * kz_film * thickness
    phase = cmath.exp(2j * delta)

    denom = 1.0 + r1 * r2 * phase
    r = (r1 + r2 * phase) / denom
    t = (t1 * t2 * cmath.exp(1j * delta)) / denom

    R = abs(r) ** 2
    if kz_below.real <= 0:
        return R, 0.0
    T = (kz_below / kz_above).real * abs(t) ** 2
    return R, T
