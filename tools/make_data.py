#!/usr/bin/env python3
"""Generate the JSON that the site's widgets check themselves against.

    python3 tools/make_data.py            # writes docs/data/*.json
    python3 tools/make_data.py --check    # recompute and diff against what is on disk

Everything here is *computed* from the formulas of the Supplemental Material, except the
values in ``anchors.json``, which are quoted from the manuscript and carry their locator.
The browser reimplements the same formulas in ``docs/assets/cft.js``; each widget page
compares its own numbers against this file at load and shows a pass/fail badge.  If the
two ever disagree, one of them is wrong and the badge says so.

Requires numpy and the standard library.  matplotlib is deliberately not used.

Conventions (docs/notation.html): two spacings, eps = 2^{-N} for the symbol and the
correlator (L = 1, as numerics_correlator.py) and eps_N = pi 2^{-N} for Theorem S1(i)
(L = pi, the value Theta_M is quoted at); the retained momentum set at scale N is
Gamma_N = { l in Z + 1/2 : |l| < 2^N } (Neveu-Schwarz half-integers), so |Gamma_N| =
2^{N+1} = n and eps_N^2 = 4^{-N}.  This is the convention of
``resubmission/numerics_correlator.py``, which is the reference implementation for the
correlator data and whose values this script reproduces.
"""
import argparse
import json
import os
import sys
import time

import numpy as np

PI = np.pi
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "docs", "data")

# ----------------------------------------------------------------- correlator (widget H)
# A reimplementation of resubmission/numerics_correlator.py that needs no matplotlib and
# exploits the band structure: for k != 0 the one-particle symbol s = B + B^T connects
# l <-> l +- k only, so it splits into k independent symmetric tridiagonal chains with
# zero diagonal.  docs/assets/cft.js does exactly this, with its own QL sweep.

LAM_C = 2 ** 11        # continuum reference cutoff, as in numerics_correlator.py
NS_PANEL_A = list(range(4, 11))
T_PANEL_A = 0.5
N_PANEL_B = 8
KS = [0, 1, 2]


def modes(Lam):
    return np.arange(-Lam + 0.5, Lam, 1.0)


def testvectors(Lam):
    ll = modes(Lam)
    supp = np.abs(ll) < 8                      # observation scale M = 3
    f = np.where(supp, np.exp(-((ll / 4.0) ** 2)), 0.0)
    g = np.where(supp, ll * np.exp(-((ll / 4.0) ** 2)), 0.0)
    return f / np.linalg.norm(f), g / np.linalg.norm(g), ll


def spectral(Lam, k, N=None):
    """(w, ab) with C(t) = sum_j exp(-i t w_j) ab_j."""
    f, g, ll = testvectors(Lam)
    pf = np.where(ll < 0, f, 0.0)
    sym = (lambda x: x) if N is None else (lambda x: (2.0 ** N) * np.sin(2.0 ** (-N) * x))
    if k == 0:
        return 2.0 * sym(ll), g * pf
    ws, abs_ = [], []
    m = len(ll)
    for res in range(k):
        idx = np.arange(res, m, k)
        nn = len(idx)
        off = sym(ll[idx[:-1]] + k / 2.0)
        T = np.zeros((nn, nn))
        T[np.arange(nn - 1), np.arange(1, nn)] = off
        T[np.arange(1, nn), np.arange(nn - 1)] = off
        w, V = np.linalg.eigh(T)
        ws.append(w)
        abs_.append((V.T @ g[idx]) * (V.T @ pf[idx]))
    return np.concatenate(ws), np.concatenate(abs_)


def corr(spec, ts):
    w, ab = spec
    return np.array([np.sum(np.exp(-1j * t * w) * ab) for t in np.atleast_1d(ts)])


def fit_ratio(Ns, errs):
    """Per-step decay ratio 2^{-slope} from a least-squares fit of log2(err) on N."""
    slope = np.polyfit(np.asarray(Ns, float), np.log2(np.asarray(errs, float)), 1)[0]
    return float(2.0 ** (-slope))


def correlator_data():
    t0 = time.time()
    ref = {k: spectral(LAM_C, k, None) for k in KS}
    panel_a, lat = {}, {}
    for k in KS:
        ca = corr(ref[k], T_PANEL_A)[0]
        errs = []
        for N in NS_PANEL_A:
            lat[(k, N)] = spectral(2 ** N, k, N)
            errs.append(float(abs(corr(lat[(k, N)], T_PANEL_A)[0] - ca)))
        panel_a[str(k)] = {
            "N": NS_PANEL_A,
            "err": errs,
            "ratios": [float(errs[i] / errs[i + 1]) for i in range(len(errs) - 1)],
            "fit_ratio_all": fit_ratio(NS_PANEL_A, errs),
            "fit_ratio_tail": fit_ratio(NS_PANEL_A[2:], errs[2:]),
        }
    ts = [round(x, 6) for x in np.linspace(0.025, 2.0, 80)]
    panel_b = {}
    for k in KS:
        cb = corr(ref[k], ts)
        lb = corr(lat[(k, N_PANEL_B)], ts)
        panel_b[str(k)] = {"t": ts, "err": [float(v) for v in np.abs(lb - cb)]}

    # how much the continuum reference itself depends on the cutoff, for the record
    cutoff = {}
    for k in KS:
        row = {}
        for L in (2 ** 9, 2 ** 10):
            s = spectral(L, k, None)
            row[str(L)] = float(max(abs(corr(s, t)[0] - corr(ref[k], t)[0]) for t in (0.5, 1.0, 2.0)))
        cutoff[str(k)] = row

    print(f"  (correlator: {time.time() - t0:.1f} s)")
    return {
        "_": "Correlator-level convergence, the setting of resubmission/numerics_correlator.py "
             "and of Fig. S7 (figure10.pdf) of the Supplemental Material.",
        "Lam_continuum": LAM_C,
        "M": 3,
        "t_panel_a": T_PANEL_A,
        "N_panel_b": N_PANEL_B,
        "panel_a": panel_a,
        "panel_b": panel_b,
        "continuum_cutoff_sensitivity": cutoff,
    }
    # deliberately NOT stored: a timing in the payload would make --check always differ


# --------------------------------------------------------------- error budget (widget E)

L_CIRC = PI            # circumference parameter of the paper; the scripts use L = pi


def eps_phys(N):
    """eps_N = L 2^{-N}, the spacing Theorem S1(i) is stated in.

    Distinct from the 2^{-N} of numerics_correlator.py, which the symbol and the
    correlator reproduce.  Theta_M is a sum over momenta and its quoted value is the
    L = pi one, so pairing it with a L = 1 spacing understates the dynamics term by
    pi^2.
    """
    return L_CIRC * 2.0 ** -N


def theta_M(M):
    ll = modes(2 ** M)
    return float(np.sqrt(np.sum(ll[ll > 0] ** 6)))


def eta_full(r):
    return float(PI / 4 * 2.0 ** -r)


def eta_chiral(r):
    return float(PI ** 2 / 16 * 4.0 ** -r)


def budget_data():
    thetas = {str(M): theta_M(M) for M in range(1, 9)}
    etas = {str(r): {"full": eta_full(r), "chiral": eta_chiral(r)} for r in range(0, 13)}
    # Theorem S1(i) evaluated at a few points, both terms separately
    pts = []
    for (N, M, dA, dB, T, chiral) in [
        (6, 3, 1, 1, 1.0, True), (6, 3, 1, 1, 1.0, False),
        (8, 3, 2, 2, 1.0, True), (10, 5, 1, 1, 1.0, True),
        (12, 5, 1, 1, 10.0, True), (10, 3, 1, 1, 0.5, True),
    ]:
        r = N - M
        eta = eta_chiral(r) if chiral else eta_full(r)
        I = (dA + dB) * eta
        II = (1.0 / 6.0) * dB * theta_M(M) * abs(T) * eps_phys(N) ** 2
        pts.append({"N": N, "M": M, "dA": dA, "dB": dB, "T": T,
                    "algebra": "chiral" if chiral else "full",
                    "I": I, "II": II, "total": I + II})
    # Lambda_k(T) = (e^{c T} - 1)/c, = T at c = 0
    lam = []
    for c in (0.0, 0.25, 0.5, 1.0):
        for T in (0.5, 1.0, 2.0, 5.0):
            v = T if c == 0 else float((np.exp(c * T) - 1.0) / c)
            lam.append({"c_k": c, "T": T, "Lambda": v})
    return {
        "_": "Theorem S1 of the Supplemental Material.  Part (i), k = 0, is established "
             "[v5, Proposition 6.3] and has every constant; part (ii), k != 0, is assembled "
             "in the supplement and its prefactor C_0 is not computed.",
        "Theta_M": thetas,
        "eta": etas,
        "theorem_s1_i": pts,
        "horizon_Lambda": lam,
    }


# ----------------------------------------------------------- resource scaling (widget F)

DELTA0, N0, NSITES0 = 0.4, 6, 128


def resources_data():
    deltas = [float(x) for x in np.logspace(0, -3, 31)]
    return {
        "_": "Resource scaling of resubmission/resource_plot.py, recomputed.  Calibration: "
             "the one-particle D10 bound at observation scale M = 3 reaches delta_0 ~ 0.4 at "
             "N = 6, i.e. n_0 = 128 sites / 256 qubits.",
        "delta0": DELTA0, "N0": N0, "n0": NSITES0,
        "sites_prefactor": float(NSITES0 * np.sqrt(DELTA0)),
        "delta": deltas,
        "sites_rel": [float((DELTA0 / d) ** 0.5) for d in deltas],
        "gates_rel": [float((DELTA0 / d) ** 1.5) for d in deltas],
        "sites_abs": [float(NSITES0 * (DELTA0 / d) ** 0.5) for d in deltas],
        "wavelet_sites_rel": [float(DELTA0 / d) for d in deltas],
        "wavelet_gates_rel": [float((DELTA0 / d) ** 2.0) for d in deltas],
        "dyadic": [{"N": N, "delta": float(DELTA0 * 4.0 ** (N0 - N)),
                    "sites": 2 ** (N + 1), "qubits": 2 ** (N + 2),
                    "sites_rel": float(2.0 ** (N - N0))} for N in range(6, 13)],
        "nearterm": nearterm_data(),
    }


def nearterm_data():
    """The near-term figure of the Letter, and the localization constraint it does not meet."""
    K, M, N = 10, 3, 6
    return {
        "_": "supp., Sec. 'The near-term figure': a D10 wavelet reaching delta = 1/2 on n = 128 "
             "sites, i.e. N = 6 with a register of 2n = 256 qubits, certified at observation "
             "scale M = 3 (r = 3) where the one-particle bound is about 0.4.  The localization "
             "constraint 2^M >= 2K-1 of [v5, Remark 6.4(3)] is NOT met there.",
        "K": K, "M": M, "N": N, "r": N - M,
        "sites": 2 ** (N + 1), "qubits": 2 ** (N + 2),
        "delta_quoted": 0.5, "delta_bound": DELTA0,
        "M_for_scale5_at_same_accuracy": 10,
        "localization": [
            {"K": kk, "M": mm, "lhs": 2 ** mm, "rhs": 2 * kk - 1, "holds": 2 ** mm >= 2 * kk - 1}
            for kk in (2, 5, 8, 10, 12) for mm in (3, 4, 5, 6)
        ],
        "sobolev_source": "QUOTED, not computed: supp., Sec. 'Discretization error "
                          "analysis', para. 'Throughout' [v5, Remark 3.13].  The companion "
                          "repository computes these from the filter taps.",
        "sobolev": {str(kk): v for kk, v in zip(
            range(2, 11),
            [1.000, 1.415, 1.776, 2.098, 2.390, 2.661, 2.917, 3.165, 3.406])},
        "regularity_thresholds": {"2-regular": 5, "3-regular": 9},
    }


# ------------------------------------------------------- ground-state circuit (widget D)

def circuit_data():
    rows = []
    for N in range(1, 11):
        n, q = 2 ** (N + 1), 2 ** (N + 2)
        stages = int(np.log2(q))
        rows.append({"N": N, "sites": n, "qubits": q,
                     "butterflies": q // 2 * stages,
                     "bogoliubov": q // 2,
                     "two_qubit_gates": q // 2 * stages + q // 2,
                     "ft_stages": stages, "ft_depth_bound": stages * stages,
                     "ancillas": 0})
    return {
        "_": "A concrete radix-2 fermionic-FFT network plus one Bogoliubov rotation per "
             "Nambu pair.  The Supplemental Material quotes only the scalings O(n log n) "
             "gates, depth O(log^2 n), no ancillas; the exact counts below are this site's "
             "arithmetic for that network, not a claim of the manuscript.",
        "rows": rows,
    }


# ------------------------------------------- Koo-Saleur one-particle symbol (widget C)

def symbol_data():
    rows = []
    for N in (4, 6, 8):
        for k in (0, 1, 2, 4):
            xs = [0.5, 1.5, 4.5, 16.5, 2 ** N - 0.5]
            rows.append({
                "N": N, "k": k, "x": xs,
                "lattice": [float(2.0 ** N * np.sin(2.0 ** -N * x)) for x in xs],
                "deviation": [float(2.0 ** N * np.sin(2.0 ** -N * x) - x) for x in xs],
                "leading": [float(-(4.0 ** -N) * x ** 3 / 6.0) for x in xs],
            })
    return {
        "_": "Lemma S1, 'Source and mechanism': the one-particle symbol difference is "
             "eps^{-1} sin(eps (l -+ k/2)) - (l -+ k/2) = O(eps^2 |l -+ k/2|^3), which is "
             "where the rate eps_N^2 comes from.  x stands for l -+ k/2.",
        "rows": rows,
    }


# ------------------------------------------------------------------------- anchors

def anchors_data():
    """Numbers quoted from the manuscript, each with the statement it comes from.
    These are not computed here; they are what the computed values are checked against."""
    return {
        "_": "Every number this site takes from the manuscript, with its locator.  "
             "'supp' is resubmission/qscft_prl_220615_supp.tex, 'main' the Letter.",
        "items": [
            {"id": "cost", "value": "delta^{-3/2}",
             "text": "gate count T^{1+o(1)} delta^{-3/2-o(1)}: a Heisenberg-limited "
                     "measurement cost delta^{-1} times a discretization cost delta^{-1/2}",
             "source": "supp, Sec. 'Per-step accounting and assembled complexity', Eq. (S32) "
                       "and the sentence after it; main, Introduction"},
            {"id": "sites", "value": "n = 2^{N+1}",
             "text": "number of lattice sites at ultraviolet scale N",
             "source": "supp, Sec. 'Discretization error analysis', para. 'Throughout'; "
                       "main, 'Representing conformal fields on a quantum computer'"},
            {"id": "qubits", "value": "2n = 2^{N+2}",
             "text": "system qubits: two per site under the Jordan-Wigner map",
             "source": "supp, Sec. 'Resource accounting and state preparation', opening para.; "
                       "main, 'Complexity'"},
            {"id": "rate", "value": "eps_N^2 propto 4^{-N}",
             "text": "the one-particle rate every leaf of the error budget carries along the "
                     "momentum-cutoff route",
             "source": "supp, caption of Fig. S1 (the error budget)"},
            {"id": "eta_full", "value": "pi/4 * 2^{-(N-M)}",
             "text": "lattice-vacuum rate eta_M(N) on the full two-component algebra",
             "source": "supp, Theorem S1(i) and Lemma S4"},
            {"id": "eta_chiral", "value": "pi^2/16 * 2^{-2(N-M)}",
             "text": "lattice-vacuum rate eta_M(N) on the chiral algebra",
             "source": "supp, Theorem S1(i) and Lemma S4"},
            {"id": "depth", "value": "r = N - M",
             "text": "renormalization depth; both error sources scale in r, not in N alone",
             "source": "supp, Lemma S4, 'Source and mechanism' [v5, Remark 6.4(1)]"},
            {"id": "nearterm", "value": "N = 6, n = 128, 256 qubits, M = 3, delta = 1/2",
             "text": "a D10 wavelet reaching accuracy delta = 1/2 on 128 sites, certified at "
                     "observation scale M = 3 (r = 3 renormalization steps)",
             "source": "supp, Sec. 'The near-term figure'; main, 'Error analysis' and abstract"},
            {"id": "delta0", "value": "0.4",
             "text": "the one-particle D10 bound on scale-3 observables at N = 6; "
                     "scale-5 observables would need N ~ 10 at the same accuracy",
             "source": "supp, Sec. 'The near-term figure'; caption of Fig. S6 (figure11.pdf)"},
            {"id": "localization", "value": "2^M >= 2K - 1 fails at M = 3, K = 10",
             "text": "the localization constraint is not met at the near-term point, so those "
                     "observables are wavelet details wrapped around the circle rather than "
                     "strictly localized fields; the register size is unaffected",
             "source": "supp, Sec. 'Reconciliation with the Letter and inversion of the rate'"},
            {"id": "horizon", "value": "Lambda_k(T) = (e^{c_k T} - 1)/c_k, Lambda_0(T) = T",
             "text": "the horizon factor; c_0 = 0, so the prefactor is linear in T only at k = 0",
             "source": "supp, Theorem S1(ii) and Lemma S5, Eq. (S22)"},
            {"id": "mpoint", "value": "O(m^2)",
             "text": "growth of the assembled constant with the number m of points",
             "source": "supp, Sec. 'Multi-point telescoping', Eq. (S27)"},
            {"id": "sobolev", "value": "sigma_K = 1.000, 1.415, 1.776, 2.098, 2.390, 2.661, "
                                       "2.917, 3.165, 3.406 for K = 2..10",
             "text": "Sobolev exponents of the Daubechies scaling functions: 2-regularity "
                     "needs K >= 5, 3-regularity K >= 9",
             "source": "supp, Sec. 'Discretization error analysis', para. 'Throughout' "
                       "[v5, Remark 3.13]"},
            {"id": "corr_ratio", "value": "4.00",
             "text": "fitted per-step decay ratio of the correlator error, i.e. 4^{-N}",
             "source": "supp, caption of Fig. S7 (figure10.pdf)"},
            {"id": "k2_growth", "value": "t ~ 1.5",
             "text": "at N = 8 the k = 2 correlator error grows sharply once the evolved "
                     "energy shell e^{c_k t} reaches the lattice cutoff",
             "source": "supp, caption of Fig. S7 (figure10.pdf)"},
        ],
    }


# ------------------------------------------------------------------------------ driver

FILES = {
    "correlator.json": correlator_data,
    "budget.json": budget_data,
    "resources.json": resources_data,
    "circuit.json": circuit_data,
    "symbol.json": symbol_data,
    "anchors.json": anchors_data,
}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true",
                    help="recompute and report differences instead of writing")
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    bad = 0
    for name, fn in FILES.items():
        payload = fn()
        text = json.dumps(payload, indent=1, sort_keys=True) + "\n"
        path = os.path.join(OUT, name)
        if args.check:
            old = open(path).read() if os.path.exists(path) else ""
            same = old == text
            print(f"{'ok  ' if same else 'DIFF'} {name}")
            bad += 0 if same else 1
        else:
            with open(path, "w") as fh:
                fh.write(text)
            print(f"wrote docs/data/{name}  ({len(text)} bytes)")
    if args.check and bad:
        sys.exit(1)


if __name__ == "__main__":
    main()
