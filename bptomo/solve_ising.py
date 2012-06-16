import numpy as np
from scipy import ndimage, stats
import math
from math import exp, log1p
from scipy import stats
from _ising import _build_logZp, log_exp_plus_exp, solve_microcanonical_chain_pyx, solve_microcanonical_chain
from tan_tan import fast_mag_chain, fast_mag_chain_nu

#-------------------------- Canonical formulation ----------------

def mag_chain(h, J, hext, full_output=False):
    """
    Compute the total magnetization for an Ising chain.
    Use the cython function fast_mag_chain_nu

    Parameters
    ----------

    h: 1-d ndarray of floats
        local field

    J: 1-d ndarray
        couplings between spins

    hext: float
        global field
    """
    magtot, hloc = fast_mag_chain_nu(h, J, hext)
    if full_output:
        return magtot, hloc
    else:
        return magtot

#@profile
def solve_canonical_h(h, J, y):
    """
    Solve Ising chain in the canonical formulation.

    Parameters
    ----------

    h: 1-d ndarray of floats
        local field

    y: total magnetization

    J: 1-d ndarray of floats
        coupling between spins

    Returns
    -------

    hloc: 1-d ndarray of floats
        local magnetization
    """
    epsilon= .02
    hext = 0
    N = len(h) 
    y = min(y, N)
    y = max(y, -N)
    mag_tot = mag_chain(h, J, hext)
    if mag_tot < y:
        hmin = 0
        hext = 8
        while y - mag_chain(h, J, hext) > epsilon:
            hmin = hext
            hext *= 2
        hmax = hext
    else:
        hmax = 0
        hext = -8
        while mag_chain(h, J, hext) - y > epsilon:
            hmax = hext
            hext *= 2
        hmin = hext
    mag_tot = 2 * N
    iter_nb = 0
    # dichotomy
    while abs(mag_tot - y) / N > epsilon and iter_nb < 200:
        iter_nb += 1
        hext = 0.5 * (hmin + hmax)
        mag_tot, hloc = mag_chain(h, J, hext, full_output=True)
        if mag_tot < y:
            hmin = hext
        else:
            hmax = hext
    return hloc


# ---------------------------------------------------------------

min_inf = -10000
max_inf = 500

#----------------Microconical Ising chain -----------------------------



def log_gaussian_weight(s, s0, beta=4.):
    """
    probability of s if the measure if s_0
    With the hypothesis of Gaussian white noise, it is a Gaussian.

    Parameters
    ----------

    s: float
        sum of spins

    s0: float
        measure

    beta: float
        width of the Gaussian. The more noise on the projections, the
        larger beta should be.
    """
    return np.maximum(-40, - beta * (s - s0)**2)


def gaussian_weight(s, s0, beta=4.):
    """
    probability of s if the measure if s_0
    With the hypothesis of Gaussian white noise, it is a Gaussian.

    Parameters
    ----------

    s: float
        sum of spins

    s0: float
        measure

    beta: float
        width of the Gaussian. The more noise on the projections, the
        larger beta should be.
    """
    return np.exp(np.maximum(-40, - beta * (s - s0)**2))

def solve_microcanonical_h(h, J, s0, error=1):
    """
    Compute local magnetization for microcanonical Ising chain
    """
    h = np.asarray(h).astype(np.float)
    J = np.asarray(J).astype(np.float)
    s0 = float(s0)
    try:
        proba = solve_microcanonical_chain(h, J, s0)
    except FloatingPointError:
        print 'other'
        proba = solve_microcanonical_chain_pyx(h, J, s0)
    res = 0.5 * (proba[1] - proba[0])
    big_field = 10
    res[res > big_field] = big_field
    res[res < -big_field] = -big_field
    return res


# ------------------ Solving Ising model for one projection -----------

def solve_line(field, Js, y, onsager=1, big_field=400, use_micro=False):
    """
    Solve Ising chain

    Parameters
    ----------

    field: 1-d ndarray
        Local field on the spins

    Js: float
        Coupling between spins

    y: float
        Sum of the spins (value of the projection)

    onsager: float

    big_field: float

    use_micro: bool, default False

    Returns
    -------

    hloc: 1-d ndarray, same shape as field
        local magnetization
    """
    mask_blocked = np.abs(field) > big_field
    field[mask_blocked] = big_field * np.sign(field[mask_blocked])
    if np.all(mask_blocked) and np.abs(np.sign(field).sum() - y) < 0.1:
        return (1.5 - onsager) * field
    elif use_micro is False or np.sum(~mask_blocked) > 25:
        hloc = solve_canonical_h(field, Js, y)
        mask_blocked = np.abs(hloc) > big_field
        hloc[mask_blocked] = big_field * np.sign(hloc[mask_blocked])
        hloc -= onsager * field
        return hloc
    else:
        hloc = solve_microcanonical_h(field, Js, y)
        mask_blocked = np.abs(hloc) > big_field
        hloc[mask_blocked] = big_field * np.sign(hloc[mask_blocked])
        hloc -= onsager * field
        return hloc

