#!/usr/bin/env python3
"""
Correlator-level convergence of the Koo-Saleur dynamics (supp Fig.: figure10.pdf).

Setting (momentum-cutoff RG, chiral complex fermion, c=1; the same setting as the
momentum-RG one-particle figures of the Supplemental Material):

  * modes l in Z+1/2 (NS sector), |l| < Lambda; lattice scale N has Lambda_N = 2^N,
    i.e. 2^{N+1} = n modes -- the mode count of the n-site lattice.
  * one-particle Koo-Saleur symbol in the conformal normalization nu_N = 2/eps_N,
    eps_N = 2^{-N}:  the L_k block is
        B_N[l+k, l] = (nu_N/2) * sin(eps_N (l + k/2)) = (1/eps_N) sin(eps_N (l + k/2))
    (phase-free: the e^{+i eps k/4} entry phase of the Letter's Nambu matrix cancels
    against the e^{-i eps k/4} prefactor on the diagonal channel).  Continuum:
        B_inf[l+k, l] = (l + k/2).
    The simulated generator is the self-adjoint H_k = L_k + L_{-k}; its one-particle
    symbol is  s = B + B^T  (real symmetric band matrix).  As N -> infinity at fixed l,
        (1/eps) sin(eps x) = x - eps^2 x^3/6 + ... ,
    so the symbol error is O(4^{-N}) -- the s=2 rate.
  * vacuum: Dirac sea P_< = projection onto l < 0 (the ground state of s_0, since
    sign(sin(eps l)) = sign(l) for |eps l| < pi).
  * observable: bounded smeared fields a(f), a(g) with fixed coefficient vectors
    supported on |l| < 8  (observation scale M = 3), identical at every scale
    (the momentum-cutoff scaling map acts as the identity on retained modes).
  * correlator:  C^{(N)}(t) = <Omega_N | a^dag(f) a_t(g) | Omega_N>,
    a_t(g) = e^{itH} a(g) e^{-itH}.  For the number-conserving bilinear
    H = sum h_{l'l} a^dag_{l'} a_l one has  [H, a_l] = -sum_q h_{lq} a_q, hence
    a_t(g) = a(e^{it h} g)  and, in the quasi-free sea state,
        C^{(N)}(t) = < e^{it s} g , P_< f > .
    The reference is the truncated continuum (Lambda_c = 2048 >> momentum reach of
    e^{its}g for the t,k used here).

Self-checks (printed): hermiticity, unitarity of the flow, exact t=0 agreement
(the error is purely dynamical), closed-form k=0 comparison, and the fitted decay
ratio per step of N (expect ~4 = 2^{2}, i.e. s=2).
"""
import numpy as np

# ---------- model builders ----------------------------------------------------


def modes(Lam):
    """Half-integer momenta l with |l| < Lam."""
    return np.arange(-Lam + 0.5, Lam, 1.0)


def symbol(Lam, k, N=None):
    """One-particle symbol s = B + B^T of H_k = L_k + L_{-k} on modes(Lam).
    N=None -> continuum entries (l+k/2); else lattice entries (1/eps) sin(eps (l+k/2))."""
    ll = modes(Lam)
    m = len(ll)
    B = np.zeros((m, m))
    if k == 0:
        vals = ll if N is None else (2.0**N) * np.sin(2.0**(-N) * ll)
        np.fill_diagonal(B, vals)
    else:
        # entry B[i+k, i]  connects l -> l+k  (k integer, half-integer grid shifts by k)
        x = ll[:-k] + k / 2.0
        vals = x if N is None else (2.0**N) * np.sin(2.0**(-N) * x)
        B[np.arange(k, m), np.arange(0, m - k)] = vals
    return B + B.T


def testvectors(Lam):
    """Scale-M=3 smeared-field coefficient vectors (support |l|<8), unit norm.
    Identical physical vectors at every scale/cutoff."""
    ll = modes(Lam)
    supp = np.abs(ll) < 8
    f = np.where(supp, np.exp(-(ll / 4.0) ** 2), 0.0)
    g = np.where(supp, ll * np.exp(-(ll / 4.0) ** 2), 0.0)
    return f / np.linalg.norm(f), g / np.linalg.norm(g), ll


def correlator(Lam, k, ts, N=None):
    """C(t) = <e^{its} g, P_< f> for t in ts."""
    s = symbol(Lam, k, N)
    assert np.allclose(s, s.T), "symbol not symmetric"
    f, g, ll = testvectors(Lam)
    w, V = np.linalg.eigh(s)
    gV = V.T @ g
    sea = ll < 0
    out = []
    for t in ts:
        gt = V @ (np.exp(1j * t * w) * gV)
        # unitarity check
        assert abs(np.linalg.norm(gt) - 1.0) < 1e-10, "flow not unitary"
        out.append(np.sum(np.conj(gt[sea]) * f[sea]))
    return np.array(out)


# ---------- self-checks --------------------------------------------------------

print("== self-checks ==")
# (i) t=0 agreement: error must be exactly static-free (identical vectors & sea)
c_lat0 = correlator(2**4, 2, [0.0], N=4)[0]
c_con0 = correlator(2**11, 2, [0.0], N=None)[0]
print(f"t=0 lattice-vs-continuum difference: {abs(c_lat0 - c_con0):.2e}  (expect ~1e-16)")

# (ii) closed-form k=0 check on the lattice
N0, Lam0, t0 = 6, 2**6, 0.7
f0, g0, ll0 = testvectors(Lam0)
sea0 = ll0 < 0
phase = np.exp(-1j * t0 * (2.0**N0) * 2.0 * np.sin(2.0**(-N0) * ll0))  # e^{-it s_0(l)}, s_0 = 2*(1/eps) sin(eps l)... see below
# careful: symbol() for k=0 returns B+B^T = 2*diag((1/eps) sin(eps l))
c_closed = np.sum(np.conj(g0[sea0]) * phase[sea0] * f0[sea0])
c_matrix = correlator(Lam0, 0, [t0], N=N0)[0]
print(f"k=0 closed form vs matrix flow:      {abs(c_closed - c_matrix):.2e}  (expect ~1e-14)")

# ---------- main computation ---------------------------------------------------

LamC = 2**11          # continuum reference cutoff (leakage negligible for t<=2, k<=2)
Ns = np.arange(4, 11)  # lattice scales N = 4..10
ks = [0, 1, 2]
tA = 0.5              # panel (a) time

print("\n== panel (a): |C^(N)(t) - C^inf(t)| at t = %.2f ==" % tA)
ref = {k: correlator(LamC, k, [tA])[0] for k in ks}
errA = {}
for k in ks:
    errA[k] = np.array([abs(correlator(2**N, k, [tA], N=N)[0] - ref[k]) for N in Ns])
    ratios = errA[k][:-1] / errA[k][1:]
    print(f"  k={k}: err(N)={np.array2string(errA[k], precision=2)}")
    print(f"        per-step decay ratios: {np.array2string(ratios, precision=2)}  (expect -> 4)")

# panel (b): error vs t at fixed N
Nb = 8
tsB = np.linspace(0.0, 2.0, 81)[1:]  # skip t=0 (error identically ~0)
print(f"\n== panel (b): error vs t at N={Nb} ==")
errB = {}
for k in ks:
    refB = correlator(LamC, k, tsB)
    latB = correlator(2**Nb, k, tsB, N=Nb)
    errB[k] = np.abs(latB - refB)
    print(f"  k={k}: err(t=0.5)={errB[k][19]:.2e}  err(t=1)={errB[k][39]:.2e}  err(t=2)={errB[k][-1]:.2e}")

# ---------- figure -------------------------------------------------------------

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["CMU Serif", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "cm",
    "font.size": 8.5,
    "axes.labelsize": 9,
    "axes.linewidth": 0.6,
    "xtick.direction": "in", "ytick.direction": "in",
    "xtick.top": True, "ytick.right": True,
})

# Okabe-Ito (colorblind-safe), fixed assignment k=0,1,2; markers as secondary encoding
COL = {0: "#0072B2", 1: "#D55E00", 2: "#009E73"}
MRK = {0: "o", 1: "s", 2: "^"}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(6.7, 2.75))

# --- panel (a) ---
for k in ks:
    ax1.semilogy(Ns, errA[k], MRK[k] + "-", color=COL[k], lw=1.1, ms=4.2,
                 mfc="white", mew=1.0, label=rf"$k={k}$")
# 4^{-N} guide through the k=0 point at N=7
gN = np.array([6.0, 10.0])
g0 = errA[0][Ns.tolist().index(7)]
ax1.semilogy(gN, g0 * 4.0 ** (7 - gN), "--", color="0.45", lw=0.9)
ax1.text(8.62, g0 * 4.0 ** (7 - 8.45) * 1.9, r"$\propto 4^{-N}$", color="0.30", fontsize=8)
ax1.set_xlabel(r"$N$")
ax1.set_ylabel(r"$|C^{(N)}(t)-C(t)|$")
ax1.set_title(r"(a)  $t=0.5$,  $M=3$", fontsize=9)
ax1.grid(True, which="major", ls=":", lw=0.4, color="0.85")
ax1.legend(frameon=False, fontsize=8, loc="lower left", handlelength=1.6)

# --- panel (b) ---
for k in ks:
    ax2.semilogy(tsB, errB[k], "-", color=COL[k], lw=1.2, label=rf"$k={k}$")
    ax2.semilogy(tsB[7::16], errB[k][7::16], MRK[k], color=COL[k], ms=3.8,
                 mfc="white", mew=0.9)
ax2.set_xlabel(r"$t$")
ax2.set_ylabel(r"$|C^{(N)}(t)-C(t)|$")
ax2.set_title(rf"(b)  $N={Nb}$,  $M=3$", fontsize=9)
ax2.grid(True, which="major", ls=":", lw=0.4, color="0.85")
ax2.legend(frameon=False, fontsize=8, loc="upper left", handlelength=1.6)

fig.tight_layout(pad=0.4)
fig.savefig("figure10.pdf")
print("\nwrote figure10.pdf")
