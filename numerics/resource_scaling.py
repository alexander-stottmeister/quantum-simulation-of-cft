#!/usr/bin/env python3
"""
Resource-scaling figure (supp: figure11.pdf).

Single log-log axis, resources RELATIVE to the near-term point (no dual axis):
  * sites  n(delta)/n_0        ~ (delta_0/delta)^{1/2}   (discretization, s=2)
  * gates  (T=1, relative)     ~ (delta_0/delta)^{3/2}   (Heisenberg 1/delta x per-run n T)
Calibration (the near-term point of the Letter): one-particle L^2 bound for the
D10 wavelet at observation scale M=3 reaches delta_0 ~ 0.4 at N=6, i.e. n_0 = 128
sites / 256 qubits (cf. the wavelet-RG convergence figure).  Then
  error = a/n^2 with a = delta_0 n_0^2  =>  n(delta) = n_0 (delta_0/delta)^{1/2}
                                          = 81 delta^{-1/2}.
Dyadic lattice sizes n = 2^{N+1} are marked on the sites line.
"""
import numpy as np
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

BLUE, VERM = "#0072B2", "#D55E00"   # Okabe-Ito, fixed assignment
d0, n0 = 0.4, 128                    # calibration: near-term point

delta = np.logspace(0, -3, 200)
sites_rel = (d0 / delta) ** 0.5      # n(delta)/n0
gates_rel = (d0 / delta) ** 1.5      # gate count at T=1, relative to near-term run

fig, ax = plt.subplots(figsize=(4.6, 3.05))
ax.loglog(delta, gates_rel, "--", color=VERM, lw=1.3, label=r"gates $\propto\delta^{-3/2}$ ($T=1$)")
ax.loglog(delta, sites_rel, "-", color=BLUE, lw=1.3, label=r"sites $n(\delta)\propto\delta^{-1/2}$")

# dyadic lattice sizes on the sites line
for N in (7, 8, 9, 10):
    dN = d0 * 4.0 ** (6 - N)
    ax.plot(dN, 2.0 ** (N - 6), "o", color=BLUE, ms=4, mfc="white", mew=1.0)
    ax.annotate(rf"$N={N}$", (dN, 2.0 ** (N - 6)), textcoords="offset points",
                xytext=(6, -9), fontsize=7.5, color=BLUE)

# near-term anchor
ax.plot(d0, 1.0, "*", color="black", ms=10, zorder=5)
ax.annotate(r"near-term point ($n{=}128$: 256 qubits, $N{=}6$)", (d0, 1.0),
            textcoords="offset points", xytext=(7, -14), fontsize=7.5, ha="left")

ax.set_xlabel(r"target accuracy $\delta$")
ax.set_ylabel(r"resources relative to the near-term point")
ax.set_xlim(1.3, 8e-4)   # accuracy improves to the right
ax.set_ylim(0.4, 3e4)
ax.grid(True, which="major", ls=":", lw=0.4, color="0.85")
ax.legend(frameon=False, fontsize=8, loc="upper left", handlelength=1.9)

fig.tight_layout(pad=0.4)
fig.savefig("figure11.pdf")
print("wrote figure11.pdf")
