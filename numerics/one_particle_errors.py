#!/usr/bin/env python3
"""One-particle convergence data for supplement figures 3-7.

Regenerates, from scratch, the numerical data behind

    Fig. 3  (fig:waveleterrorM)   wavelet RG,          c = 0,      k = 0, M in {3,4,5}, K in {8,10}
    Fig. 4  (fig:waveleterrork)   wavelet RG,          c = 0,      k = 0, M = 3, factorised bounds
    Fig. 5  (fig:momrgerrorM)     momentum-cutoff RG,  c = 1/2, 1, k = 0, M in {3,4,5}
    Fig. 6  (fig:momrgerrork)     momentum-cutoff RG,  c = 1/2, 1, M = 3, k in {0,+-1,+-2}
    Fig. 7  (fig:momrgerrorHS)    momentum-cutoff RG,  off-diagonal HS error, k in {+-2,+-3,+-4}

The 2021/22 originals were opaque PDFs with no generating code.  Everything here is
derived from the revised companion manuscript (referred to below as [v5]):

    lattice_cft/free_fermion_cft_v5.tex

Conventions, all fixed by [v5]:

    L        = pi                      (so pi/L = 1)
    eps_N    = 2^{-N} L = pi 2^{-N},   L_N eps_N = L,  L_N = 2^N
    Gamma_{inf,+} = Z                  Ramond sector          ([v5], eq. (37))
    Gamma_{inf,-} = Z + 1/2            Neveu-Schwarz sector
    Gamma_{N,+}   = {-2^N, ..., 2^N-1},  Gamma_{N,-} = {-2^N+1/2, ..., 2^N-1/2}
    chi_{Gamma_N} = indicator of Gamma_{N,.}, symmetrised in the Ramond sector to
                    (-pi/eps_N, pi/eps_N) cap Gamma_N, i.e. |n| < 2^N     ([v5], fn. to eq. (232))
    m0(xi)   = 2^{-1/2} sum_n h_n e^{-i n xi},  shat(xi) = prod_{j>=1} m0(2^{-j} xi)
    _K s     = Daubechies scaling function with K vanishing moments, 2K taps, supp [0, 2K-1]

Wavelet route ([v5], proof of Lemma 4.7 = lem:KSconv):

    f^{(N)}_k(M,m) = shat(eps_N m) cos(eps_N k/4)^2 sin(eps_N (m+k/2))/eps_N
                                        * prod_{j=1..N-M} m0(eps_{M+j}(m+k))
    f_k(M,m)       = shat(eps_M (m+k)) (m + k/2)

and the plotted quantity is   ( sum_m |f^{(N)}_k(M,m) - f_k(M,m)|^2 )^{1/2},
the summation index m running over Gamma_{inf,.}.  For k = 0 the finite product
telescopes against shat by the infinite-product identity and the difference collapses to
shat(eps_M m) m (sinc(eps_N m) - 1), i.e. [v5], eq. (262) = eq:errordecay.

Momentum-cutoff route ([v5], eq. (235) = eq:momrgestimates).  Diagonal bound, upper
("+") chirality, summation index n = the *incoming* momentum:

    D_k(M,N)^2 = sum_n chi_{Gamma_M}(n) theta(n-k) theta(n)
                    | cos(eps_N k/4)^2 sin(eps_N (n-k/2))/eps_N chi_{Gamma_N}(n-k) - (n-k/2) |^2

Off-diagonal Hilbert-Schmidt bound (no chi_{Gamma_M}, both chi_{Gamma_N} present):

    H_k(N)^2   = sum_n theta(n-k) theta(-n)
                    | cos(eps_N k/4)^2 sin(eps_N (n-k/2))/eps_N chi_{Gamma_N}(n-k) chi_{Gamma_N}(n) - (n-k/2) |^2

The plotted quantities are D_k(M,N) and H_k(N).  The index set of the HS sum is the finite
strip between 0 and k, so H_k vanishes for k = 0, +-1 in the Neveu-Schwarz sector (for
k = +-1 the single admissible half-integer momentum has n -+ k/2 = 0), which is the
statement of the caption of Fig. 7 and of [v5], Remark 4.22 = rem:moeberror.

Stdlib + numpy only; no matplotlib.  Plots are produced separately by the pgfplots
sources in figures_src/, which read the .dat files written here.

Usage
    python3 one_particle_errors.py --selftest     checks + fitted decay exponents
    python3 one_particle_errors.py --write        writes figures_src/figure{3..7}.dat
"""

import argparse
import math
import os
import sys

import numpy as np
from numpy.polynomial import polynomial as P

# --------------------------------------------------------------------------------------
# conventions
# --------------------------------------------------------------------------------------

L = math.pi                       # circumference parameter of S^1_L, as in every figure


def eps(N):
    """eps_N = 2^{-N} L."""
    return 2.0 ** (-N) * L


def gamma_inf(sector, mmax):
    """Gamma_{inf,+} = Z (Ramond) or Gamma_{inf,-} = Z + 1/2 (Neveu-Schwarz), |m| <= mmax."""
    if sector == "R":
        return np.arange(-mmax, mmax + 1, 1.0)
    if sector == "NS":
        return np.arange(-mmax + 0.5, mmax + 0.5, 1.0)
    raise ValueError("sector must be 'R' or 'NS'")


def chi_gamma(x, N):
    """chi_{Gamma_N}: indicator of |x| < pi/eps_N = 2^N (symmetrised, cf. [v5] fn. to eq. (232))."""
    return (np.abs(np.asarray(x, float)) < 2.0 ** N - 1e-9).astype(float)


# --------------------------------------------------------------------------------------
# Daubechies filters and the scaling function
# --------------------------------------------------------------------------------------

def daubechies(K):
    """Orthonormal Daubechies filter, K vanishing moments, 2K taps, sum_n h_n = sqrt(2).

    Spectral factorisation of the Daubechies polynomial: the minimum-phase root selection
    gives the extremal-phase ("db") filter, supp(_K s) = [0, 2K-1].
    """
    coef = np.array([float(math.comb(K - 1 + n, n)) for n in range(K)])
    ys = np.roots(coef[::-1]) if K > 1 else np.array([])
    zs = []
    for y in ys:
        b = 2 - 4 * y
        disc = np.sqrt(b * b - 4 + 0j)
        for z in ((b + disc) / 2, (b - disc) / 2):
            if abs(z) < 1.0 - 1e-12:
                zs.append(z)
                break
    poly = np.array([1.0 + 0j])
    for _ in range(K):
        poly = P.polymul(poly, [1.0, 1.0])
    for z in zs:
        poly = P.polymul(poly, [-z, 1.0])
    h = np.real_if_close(poly, tol=1e6).real
    return h / np.sum(h) * math.sqrt(2.0)


def m0(xi, h):
    """m0(xi) = 2^{-1/2} sum_n h_n e^{-i n xi}, evaluated by Horner in w = e^{-i xi}."""
    w = np.exp(-1j * np.asarray(xi, float))
    out = np.zeros(w.shape, dtype=complex)
    for c in h[::-1]:
        out = out * w + c
    return out / math.sqrt(2.0)


def prod_m0(xi, h, jmin, jmax):
    """prod_{j=jmin..jmax} m0(2^{-j} xi).  Never formed as a quotient of shat's ([v5],
    proof of Lemma 4.7: shat vanishes on 2 pi Z \\ {0}, so the quotient has poles)."""
    xi = np.asarray(xi, float)
    out = np.ones(xi.shape, dtype=complex)
    for j in range(jmin, jmax + 1):
        out = out * m0(xi * 2.0 ** (-j), h)
    return out


def shat(xi, h, extra=54):
    """shat(xi) = prod_{j>=1} m0(2^{-j} xi), truncated adaptively.

    The tail of the product is 1 + O(2^{-J}|xi|), so J = log2|xi| + extra with extra = 54
    is at the double-precision floor; see selftest().
    """
    xi = np.asarray(xi, float)
    mx = max(float(np.max(np.abs(xi))) if xi.size else 1.0, 1.0)
    J = int(np.ceil(np.log2(mx))) + extra
    return prod_m0(xi, h, 1, J)


def orthonormality_error(h):
    """max_k | sum_n h_n h_{n+2k} - delta_{k0} |."""
    n = len(h)
    return max(abs(sum(h[i] * h[i + 2 * k] for i in range(n - 2 * k)) - (1.0 if k == 0 else 0.0))
               for k in range(n // 2))


def centre_of_mass(h):
    """mu(s) = int x s(x) dx = 2^{-1/2} sum_n n h_n ([v5], Remark 3.5)."""
    return float(sum(n * h[n] for n in range(len(h))) / math.sqrt(2.0))


def sobolev_exponent(h, jmin=6, jmax=14, npts=8001):
    """sigma_K from the dyadic-block L^2 decay of shat ([v5], eq. (114) = eq:sobolevindex).

    On the block [2^j, 2^{j+1}] the integral of |shat|^2 behaves as a^{1-2p} with p the
    pointwise L^2 decay exponent and sigma = p - 1/2, hence sigma = -slope/2.
    """
    a, e = [], []
    for j in range(jmin, jmax):
        xi = np.linspace(2.0 ** j, 2.0 ** (j + 1), npts)
        a.append(2.0 ** j)
        e.append(float(np.trapezoid(np.abs(shat(xi, h)) ** 2, xi)))
    slope = np.polyfit(np.log(np.array(a)), np.log(np.array(e)), 1)[0]
    return float(-slope / 2.0)


_FILTER_CACHE = {}


def filt(K):
    if K not in _FILTER_CACHE:
        _FILTER_CACHE[K] = daubechies(K)
    return _FILTER_CACHE[K]


# --------------------------------------------------------------------------------------
# wavelet route:  sum_m | f^{(N)}_k(M,m) - f_k(M,m) |^2          (figures 3 and 4)
# --------------------------------------------------------------------------------------

def wavelet_terms(K, M, N, k=0, sector="R", mexp=15):
    """The two symbols of [v5], proof of Lemma 4.7, on |m| <= 2^mexp.

    Returns (m, f_N, f).  mexp = 15 is converged to 10 significant digits (selftest).

    [v5] states the comparison for N > M; N = M is the natural limiting case (the finite
    product is empty, R^M_N = 1) and is the leftmost point of every curve of figure 3.
    """
    if N < M:
        raise ValueError("the comparison of Lemma 4.7 needs N >= M")
    h = filt(K)
    eM, eN = eps(M), eps(N)
    m = gamma_inf(sector, 2 ** mexp)
    f_N = (shat(eN * m, h) * math.cos(0.25 * eN * k) ** 2
           * np.sin(eN * (m + k / 2.0)) / eN
           * prod_m0(eM * (m + k), h, 1, N - M))
    f = shat(eM * (m + k), h) * (m + k / 2.0)
    return m, f_N, f


def wavelet_error(K, M, N, k=0, sector="R", mexp=15):
    """( sum_m |f^{(N)}_k - f_k|^2 )^{1/2}  -- the quantity plotted in Figs. 3 and 4."""
    m, f_N, f = wavelet_terms(K, M, N, k, sector, mexp)
    return math.sqrt(float(np.sum(np.abs(f_N - f) ** 2)))


def wavelet_error_split(K, M, N, k=0, sector="R", mexp=15):
    """The two regions of [v5], eqs. (267)/(268) = eq:errorBZ / eq:errortail.

    Returns (Brillouin-zone part, tail part) of the *squared* sum, split at |m+k| = pi/eps_N.
    """
    m, f_N, f = wavelet_terms(K, M, N, k, sector, mexp)
    d = np.abs(f_N - f) ** 2
    inside = np.abs(m + k) <= 2.0 ** N
    return float(np.sum(d[inside])), float(np.sum(d[~inside]))


# --------------------------------------------------------------------------------------
# the factorised Sobolev bound of figure 4
# --------------------------------------------------------------------------------------

def _sup_sinc(delta, xmax=60.0, npts=4000001):
    """sup_{x in R} |sinc(x) - 1|^2 / |x|^{2 delta}; equals 1/36 at delta = 2."""
    x = np.linspace(1e-6, xmax, npts)
    return float(np.max(np.abs(np.sin(x) / x - 1.0) ** 2 / np.abs(x) ** (2 * delta)))


_SUP_CACHE = {}


def error_factor_sq(delta, N):
    """Error^2(delta, L, 0, N) of [v5], eq. (263) = eq:errordecayexp0, *second* line:

        2 L (pi/L)^{2(1+delta)} eps_N^{2 delta} sup_x |sinc(x)-1|^2 |x|^{-2 delta}.

    This closed form -- not the sharper lattice supremum on the first line -- is what the
    2022 figure 4 plots; it is exactly proportional to eps_N^{2 delta}, which is why those
    curves are perfect straight lines of slope delta.  See FIGURES.md.
    """
    if delta not in _SUP_CACHE:
        _SUP_CACHE[delta] = _sup_sinc(delta)
    return 2 * L * (math.pi / L) ** (2 * (1 + delta)) * eps(N) ** (2 * delta) * _SUP_CACHE[delta]


def error_factor_sq_lattice(delta, N, sector="R", mexp=16):
    """Error^2(delta, L, 0, N), *first* (sharp) line of [v5], eq. (263):

        2 L sup_{m in Gamma_inf} (1 + (L/pi)|m|)^{-2(1+delta)} m^2 |sinc(eps_N m) - 1|^2.
    """
    m = gamma_inf(sector, 2 ** mexp)
    m = m[np.abs(m) > 1e-9]
    x = eps(N) * m
    w = (1.0 + (L / math.pi) * np.abs(m)) ** (-2 * (1 + delta))
    return 2 * L * float(np.max(w * m ** 2 * np.abs(np.sin(x) / x - 1.0) ** 2))


def sobolev_norm_sq(K, M, delta, sector="R", mexp=12):
    """|| shat(eps_M .) ||^2_{h^{1+delta}} = (1/2L) sum_m (1 + (L/pi)|m|)^{2(1+delta)} |shat(eps_M m)|^2.

    Finite exactly when 1 + delta < sigma_K ([v5], Remark 3.13).  For (K, delta) = (8, 2)
    it is *divergent* (sigma_8 = 2.917 < 3) and the value returned depends on mexp; the
    default mexp = 12 is the truncation that reproduces the 2022 curve.  See FIGURES.md.
    """
    h = filt(K)
    m = gamma_inf(sector, 2 ** mexp)
    w = (1.0 + (L / math.pi) * np.abs(m)) ** (2 * (1 + delta))
    return float(np.sum(w * np.abs(shat(eps(M) * m, h)) ** 2)) / (2 * L)


def factorised_bound(K, M, delta, N, sector="R", mexp=12):
    """Error(delta,L,0,N) * || shat(eps_M .) ||_{h^{1+delta}}, the right side of [v5] (262)."""
    return math.sqrt(error_factor_sq(delta, N) * sobolev_norm_sq(K, M, delta, sector, mexp))


# --------------------------------------------------------------------------------------
# momentum-cutoff route                                           (figures 5, 6 and 7)
# --------------------------------------------------------------------------------------

def momrg_diag(M, N, k, sector="NS", chirality=+1, legacy_k_sign=False):
    """Diagonal bound of [v5], eq. (235) = eq:momrgestimates, first estimate; square root.

    Summation index n = incoming momentum, chi_{Gamma_M}(n) cutting the one-particle
    vector R^M_inf(eta).  The two chiralities give identical values (reflection n -> -n),
    so `chirality` only exists for documentation.

    legacy_k_sign=True puts chi_{Gamma_M} on the outgoing momentum instead, which is the
    same as replacing k by -k; that is what the 2022 figure 6 does.  See FIGURES.md.
    """
    s = chirality
    eN = eps(N)
    n = gamma_inf(sector, 2 ** (M + 4))
    arg = n - s * k / 2.0
    out = n - s * k                                   # outgoing momentum
    keep = (s * out > 0) & (s * n > 0)
    cut = chi_gamma(out if legacy_k_sign else n, M)
    approx = math.cos(0.25 * eN * k) ** 2 * np.sin(eN * arg) / eN * chi_gamma(out, N)
    return math.sqrt(float(np.sum(keep * cut * np.abs(approx - arg) ** 2)))


def momrg_hs(N, k, sector="NS", chirality=+1):
    """Off-diagonal Hilbert-Schmidt bound of [v5], eq. (235), second estimate; square root.

    [v5] displays the (+-) block, theta(+-(n-+k)) theta(-+n); eq. (234) = eq:noquantconv
    needs both off-diagonal blocks, and the (-+) one is obtained by exchanging the two
    theta's.  Each is supported on the finite strip between 0 and k, and exactly one of
    them is non-empty for a given sign of k, so their sum is even in k -- which is why
    Fig. 7 labels its three curves k = +-2, +-3, +-4.
    """
    s = chirality
    eN = eps(N)
    n = gamma_inf(sector, 2 ** (N + 2))
    arg = n - s * k / 2.0
    out = n - s * k                                   # outgoing momentum
    keep = ((s * out > 0) & (-s * n > 0)) | ((-s * out > 0) & (s * n > 0))
    approx = (math.cos(0.25 * eN * k) ** 2 * np.sin(eN * arg) / eN
              * chi_gamma(out, N) * chi_gamma(n, N))
    return math.sqrt(float(np.sum(keep * np.abs(approx - arg) ** 2)))


# --------------------------------------------------------------------------------------
# fitted decay exponents
# --------------------------------------------------------------------------------------

def fit_exponent(Ns, vals):
    """Least-squares slope of -log2(value) against N: value ~ 2^{-rate N}."""
    Ns = np.asarray(Ns, float)
    v = np.asarray(vals, float)
    good = v > 0
    if good.sum() < 2:
        return float("nan")
    return float(-np.polyfit(Ns[good], np.log2(v[good]), 1)[0])


# --------------------------------------------------------------------------------------
# figure data
# --------------------------------------------------------------------------------------

FIG3_N = [5, 6, 7, 8]
FIG4_N = [4, 5, 6, 7, 8]
FIG5_N = [5, 6, 7, 8, 9, 10]
FIG6_N = [5, 6, 7, 8, 9, 10]
FIG7_N = [5, 6, 7, 8, 9, 10]

FIG3_SERIES = [("M5K8", 5, 8), ("M5K10", 5, 10), ("M4K8", 4, 8),
               ("M4K10", 4, 10), ("M3K8", 3, 8), ("M3K10", 3, 10)]
FIG4_BOUNDS = [("sobhK4", 0.5, 4), ("sobhK8", 0.5, 8), ("sobhK10", 0.5, 10),
               ("sob1K8", 1.0, 8), ("sob1K10", 1.0, 10),
               ("sob3hK8", 1.5, 8), ("sob3hK10", 1.5, 10),
               ("sob2K8", 2.0, 8), ("sob2K10", 2.0, 10)]
FIG4_TRUE = [("trueK8", 8), ("trueK10", 10)]
FIG5_SERIES = [("M3", 3), ("M4", 4), ("M5", 5)]
FIG6_SERIES = [("kp2", 2), ("kp1", 1), ("k0", 0), ("km1", -1), ("km2", -2)]
FIG7_SERIES = [("k2", 2), ("k3", 3), ("k4", 4)]


def figure3_data(sector="R"):
    cols = {"N": FIG3_N}
    for name, M, K in FIG3_SERIES:
        cols[name] = [wavelet_error(K, M, N, 0, sector) for N in FIG3_N]
    return cols


def figure4_data(sector="R", mexp=12):
    cols = {"N": FIG4_N}
    for name, d, K in FIG4_BOUNDS:
        cols[name] = [factorised_bound(K, 3, d, N, sector, mexp) for N in FIG4_N]
    for name, K in FIG4_TRUE:
        cols[name] = [wavelet_error(K, 3, N, 0, sector) for N in FIG4_N]
    return cols


def figure5_data(sector="NS", legacy=False):
    cols = {"N": FIG5_N}
    for name, M in FIG5_SERIES:
        cols[name] = [momrg_diag(M, N, 0, sector, legacy_k_sign=legacy) for N in FIG5_N]
    return cols


def figure6_data(sector="NS", legacy=False):
    cols = {"N": FIG6_N}
    for name, k in FIG6_SERIES:
        cols[name] = [momrg_diag(3, N, k, sector, legacy_k_sign=legacy) for N in FIG6_N]
    return cols


def figure7_data(sector="NS"):
    cols = {"N": FIG7_N}
    for name, k in FIG7_SERIES:
        cols[name] = [momrg_hs(N, k, sector) for N in FIG7_N]
    return cols


def write_dat(path, cols, order, comment):
    """pgfplots-readable table: one comment line, one header row of column names."""
    n = len(cols["N"])
    with open(path, "w") as fh:
        fh.write("# %s\n" % comment)
        fh.write(" ".join("%-14s" % c for c in order).rstrip() + "\n")
        for i in range(n):
            row = []
            for c in order:
                v = cols[c][i]
                row.append("%-14d" % v if c == "N" else "%-14.8e" % v)
            fh.write(" ".join(row).rstrip() + "\n")


def write_all(outdir, legacy=False):
    specs = [
        ("figure3.dat", figure3_data(),
         ["N"] + [n for n, _, _ in FIG3_SERIES],
         "Fig. 3 (fig:waveleterrorM): wavelet RG, c=0, k=0. "
         "( sum_m |f^(N)_0(M,m)-f_0(M,m)|^2 )^{1/2}, [v5] Lemma 4.7 / eq. (262)."),
        ("figure4.dat", figure4_data(),
         ["N"] + [n for n, _, _ in FIG4_BOUNDS] + [n for n, _ in FIG4_TRUE],
         "Fig. 4 (fig:waveleterrork): wavelet RG, c=0, k=0, M=3. "
         "sob<s>K<K> = Error(s,L,0,N)*||shat(eps_M .)||_{h^{1+s}}, [v5] eqs. (262)-(263); "
         "true<K> = the exact error, same quantity as figure3.dat at M=3."),
        ("figure5.dat", figure5_data(legacy=legacy),
         ["N"] + [n for n, _ in FIG5_SERIES],
         "Fig. 5 (fig:momrgerrorM): momentum-cutoff RG, c=1/2,1, k=0, NS sector. "
         "Diagonal bound of [v5] eq. (235), square root."),
        ("figure6.dat", figure6_data(legacy=legacy),
         ["N"] + [n for n, _ in FIG6_SERIES],
         "Fig. 6 (fig:momrgerrork): momentum-cutoff RG, M=3, NS sector, k=0,+-1,+-2. "
         "Diagonal bound of [v5] eq. (235), square root."),
        ("figure7.dat", figure7_data(),
         ["N"] + [n for n, _ in FIG7_SERIES],
         "Fig. 7 (fig:momrgerrorHS): momentum-cutoff RG, off-diagonal HS bound of "
         "[v5] eq. (235), square root; even in k, zero for k=0,+-1 in the NS sector."),
    ]
    for fname, cols, order, comment in specs:
        path = os.path.join(outdir, fname)
        write_dat(path, cols, order, comment)
        print("wrote %s" % path)
    return specs


# --------------------------------------------------------------------------------------
# selftest
# --------------------------------------------------------------------------------------

# Published Daubechies taps (Daubechies, "Ten Lectures on Wavelets", Table 6.1; the same
# numbers as PyWavelets' db2/db3/db4).  They are the MIRROR of what daubechies() builds:
# reversing a real filter replaces m0(xi) by e^{-i(2K-1)xi} conj(m0(xi)), leaving |shat|
# unchanged but reflecting s about the midpoint of its support.  The unreversed filter is
# the manuscript's convention, pinned below by mu(s).
_PUBLISHED_TAPS = {
    2: [0.48296291314469025, 0.83651630373746899, 0.22414386804185735, -0.12940952255092145],
    3: [0.33267055295095688, 0.80689150931333875, 0.45987750211933132, -0.13501102001039084,
        -0.085441273882241486, 0.035226291882100656],
    4: [0.23037781330885523, 0.71484657055254153, 0.63088076792959036, -0.027983769416983849,
        -0.18703481171888114, 0.030841381835986965, 0.032883011666982945, -0.010597401784997278],
}
# [v5], Remark 3.13 = rem:regularityvalues
_SIGMA_TABLE = {2: 1.000, 3: 1.415, 4: 1.776, 5: 2.098, 6: 2.390,
                7: 2.661, 8: 2.917, 9: 3.165, 10: 3.406, 11: 3.641}
# [v5], Remark 3.5 = rem:recentring
_MU_TABLE = {4: 5.99, 10: 16.87}
# [v5], Remark 4.32 = rem:errorrates: the tail decays at 2 sigma_K - 2
_TAIL_TABLE = {4: 1.55, 8: 3.83, 10: 4.81}


def selftest():
    ok = True

    def check(label, value, tol, target=0.0):
        nonlocal ok
        good = abs(value - target) < tol
        ok = ok and good
        print("  %-58s %12.3e   %s" % (label, value, "ok" if good else "FAIL"))

    print("Daubechies filters")
    worst = max(float(np.max(np.abs(daubechies(K)[::-1] - np.array(ref))))
                for K, ref in _PUBLISHED_TAPS.items())
    check("taps vs Ten Lectures Table 6.1 (up to reflection)", worst, 1e-11)
    check("double-shift orthonormality, K = 2..12",
          max(orthonormality_error(daubechies(K)) for K in range(2, 13)), 1e-14)
    check("sum_n h_n - sqrt(2), K = 2..12",
          max(abs(float(np.sum(daubechies(K))) - math.sqrt(2.0)) for K in range(2, 13)), 1e-14)
    check("shat(0) - 1, K = 4, 8, 10",
          max(abs(float(np.abs(shat(np.array([0.0]), filt(K))[0])) - 1.0) for K in (4, 8, 10)), 1e-13)
    check("|shat| invariant under filter reversal (K = 4)",
          float(np.max(np.abs(np.abs(shat(np.linspace(0.3, 40.0, 97), filt(4)))
                              - np.abs(shat(np.linspace(0.3, 40.0, 97), filt(4)[::-1]))))), 1e-13)
    check("shat product truncation: extra = 54 vs 74 (K = 8, xi <= 2^15)",
          float(np.max(np.abs(shat(np.linspace(1.0, 2.0 ** 15, 2001), filt(8), 54)
                              - shat(np.linspace(1.0, 2.0 ** 15, 2001), filt(8), 74)))), 1e-12)
    check("mu(s) vs [v5] Rmk 3.5 (5.99, 16.87)",
          max(abs(centre_of_mass(filt(K)) - v) for K, v in _MU_TABLE.items()), 5e-3)
    check("sigma_K vs [v5] Rmk 3.13 table, K = 2..11",
          max(abs(sobolev_exponent(daubechies(K)) - v) for K, v in _SIGMA_TABLE.items()), 6e-3)

    print("\nWavelet route")
    check("sum_m convergence: mexp 15 vs 17 (K=8, M=5, N=8), rel.",
          abs(wavelet_error(8, 5, 8, 0, "R", 15) / wavelet_error(8, 5, 8, 0, "R", 17) - 1.0), 1e-9)
    check("Ramond vs Neveu-Schwarz lattice (K=8, M=5, N=8), rel.",
          abs(wavelet_error(8, 5, 8, 0, "R") / wavelet_error(8, 5, 8, 0, "NS") - 1.0), 1e-6)
    # for k = 0 the finite product telescopes: f^(N) - f = shat(eps_M m) m (sinc(eps_N m) - 1)
    m, f_N, f = wavelet_terms(8, 3, 6, 0, "R")
    x = eps(6) * m
    closed = shat(eps(3) * m, filt(8)) * m * (np.where(np.abs(x) < 1e-14, 1.0,
                                                       np.sin(x) / np.where(x == 0, 1, x)) - 1.0)
    check("k=0 collapse to [v5] eq. (262), max abs",
          float(np.max(np.abs((f_N - f) - closed))), 1e-9)
    print("  tail decay rate vs [v5] Rmk 4.32 (2 sigma_K - 2):")
    for K, target in _TAIL_TABLE.items():
        tails = [wavelet_error_split(K, 3, N, 0)[1] for N in range(5, 12)]
        r = fit_exponent(range(5, 12), tails)
        good = abs(r - target) < 0.05
        ok = ok and good
        print("    K = %-3d tail rate %6.3f   expected %5.2f   %s"
              % (K, r, target, "ok" if good else "FAIL"))

    print("\nMomentum-cutoff route")
    check("HS bound vanishes for k = 0, +-1 (NS sector)",
          max(momrg_hs(N, k) for N in (5, 8, 10) for k in (0, 1, -1)), 1e-14)
    check("HS bound even in k (|k| = 2, 3, 4)",
          max(abs(momrg_hs(N, k) - momrg_hs(N, -k)) for N in (5, 8, 10) for k in (2, 3, 4)), 1e-12)
    check("diagonal bound independent of chirality (M=3, k=2)",
          max(abs(momrg_diag(3, N, 2, "NS", +1) - momrg_diag(3, N, 2, "NS", -1))
              for N in (5, 8, 10)), 1e-12)
    f5, f6 = figure5_data(), figure6_data()
    check("Fig. 5 at M=3 equals Fig. 6 at k=0",
          max(abs(a - b) for a, b in zip(f5["M3"], f6["k0"])), 1e-15)

    print("\nFitted decay exponents (value ~ 2^{-rate N})")
    expected = {}
    for K in (8, 10):
        expected[K] = min(4.0, 2 * _SIGMA_TABLE[K] - 2) / 2.0

    print("  figure 3  wavelet, k=0   [expected min(4, 2 sigma_K - 2)/2]")
    d3 = figure3_data()
    for name, M, K in FIG3_SERIES:
        print("    %-8s rate %6.3f   expected %5.3f" % (name, fit_exponent(d3["N"], d3[name]),
                                                        expected[K]))
    print("  figure 4  factorised bounds [expected s] and true error")
    d4 = figure4_data()
    for name, d, K in FIG4_BOUNDS:
        print("    %-8s rate %6.3f   expected %5.3f" % (name, fit_exponent(d4["N"], d4[name]), d))
    for name, K in FIG4_TRUE:
        print("    %-8s rate %6.3f   expected %5.3f" % (name, fit_exponent(d4["N"], d4[name]),
                                                        expected[K]))
    print("  figure 5  momentum cutoff, k=0   [expected 2]")
    d5 = figure5_data()
    for name, M in FIG5_SERIES:
        print("    %-8s rate %6.3f   expected 2.000" % (name, fit_exponent(d5["N"], d5[name])))
    print("  figure 6  momentum cutoff, M=3   [expected 2]")
    d6 = figure6_data()
    for name, k in FIG6_SERIES:
        print("    %-8s rate %6.3f   expected 2.000" % (name, fit_exponent(d6["N"], d6[name])))
    print("  figure 7  off-diagonal HS        [expected 2]")
    d7 = figure7_data()
    for name, k in FIG7_SERIES:
        print("    %-8s rate %6.3f   expected 2.000" % (name, fit_exponent(d7["N"], d7[name])))

    print("\n-> %s" % ("ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED"))
    return ok


# --------------------------------------------------------------------------------------

def main(argv=None):
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--selftest", action="store_true",
                    help="run the checks and print the fitted decay exponent of every curve")
    ap.add_argument("--write", action="store_true",
                    help="write figure{3..7}.dat")
    ap.add_argument("--outdir", default=os.path.join(here, "figures_src"),
                    help="where the .dat files go (default: figures_src/ beside this script)")
    ap.add_argument("--legacy-k-sign", action="store_true",
                    help="put chi_{Gamma_M} on the outgoing momentum in the diagonal "
                         "momentum-cutoff bound, i.e. reproduce the 2022 figure 6 labelling")
    args = ap.parse_args(argv)
    if not (args.selftest or args.write):
        args.selftest = args.write = True
    rc = 0
    if args.selftest:
        rc = 0 if selftest() else 1
        print()
    if args.write:
        os.makedirs(args.outdir, exist_ok=True)
        write_all(args.outdir, legacy=args.legacy_k_sign)
    return rc


if __name__ == "__main__":
    sys.exit(main())
