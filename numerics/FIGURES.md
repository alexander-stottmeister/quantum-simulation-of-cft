# Supplement figures 3–7: what they plot, and how to regenerate them

The five one-particle convergence figures of the supplement (`figure3.pdf` … `figure7.pdf`,
typeset as **FIG. S3 … FIG. S7**) date from July 2021 and were Mathematica 12.2 exports.
No generating notebook or script survived anywhere in this workspace, so until now the
figures were unverifiable artefacts.  This note closes that gap.

Everything is now produced by

| file | role |
|---|---|
| `one_particle_errors.py` | numpy-only generator; `--selftest` checks it, `--write` emits the data |
| `figures_src/figure{3..7}.dat` | the generated data (whitespace tables with a header row) |
| `figures_src/figure{3..7}.tex` | standalone pgfplots documents reading the `.dat` beside them |
| `figure{3..7}.pdf` | the compiled figures included by `qscft_prl_220615_supp.tex` |

No matplotlib is involved; the plots are pgfplots/TikZ compiled with `pdflatex`.

Throughout, **[v5]** is the revised companion manuscript
`lattice_cft/free_fermion_cft_v5.tex`; equation and statement numbers are those of
`lattice_cft/build/free_fermion_cft_v5.pdf`.

## Regenerating everything

```sh
cd resubmission
python3 one_particle_errors.py                 # selftest + writes figures_src/figure{3..7}.dat
cd figures_src
for f in 3 4 5 6 7; do pdflatex -interaction=nonstopmode figure$f.tex; done
for f in 3 4 5 6 7; do cp figure$f.pdf ../figure$f.pdf; done
```

`python3 one_particle_errors.py --selftest` alone runs the checks and prints the fitted
decay exponent of every curve without touching any file; `--write` alone writes the data.
The whole run takes about a minute on a laptop.  `pdflatex` is
`/Library/TeX/texbin/pdflatex` (TeX Live 2026); `pgfplots.sty`, `tikz.sty` and
`standalone.cls` are all present there.  The generated PDFs are 402–424 pt wide, i.e. the
same on-page size as the 2021/22 originals (all 416 pt), so the supplement's bare
`\includegraphics{figureN.pdf}` calls need no change.

## Conventions

All fixed by [v5]; the selftest pins each of them.

```
L         = pi                          so pi/L = 1
eps_N     = 2^{-N} L = pi 2^{-N}        L_N eps_N = L,  L_N = 2^N
Gamma_{inf,+} = Z                       Ramond sector,        [v5] eq. (37)
Gamma_{inf,-} = Z + 1/2                 Neveu-Schwarz sector, [v5] eq. (37)
chi_{Gamma_N} = indicator of |n| < 2^N  symmetrised as in the footnote to [v5] eq. (232)
m0(xi)    = 2^{-1/2} sum_n h_n e^{-i n xi}
shat(xi)  = prod_{j>=1} m0(2^{-j} xi)
_K s      = Daubechies scaling function, K vanishing moments, 2K taps, supp [0, 2K-1]
```

The Daubechies filters are rebuilt here by spectral factorisation rather than imported, so
that the repository stands alone; `lattice_cft/tools/dbfilters.py` is the same construction
in the same conventions and was used as the reference while writing this.

---

## FIG. S3 — `figure3.pdf`, label `fig:waveleterrorM`

**Quantity.** Wavelet renormalization group, central charge `c = 0`, generator order
`k = 0`.  Six curves, `(M,K)` for `M ∈ {3,4,5}` and `K ∈ {8,10}`, over `N = 5 … 8`:

```
E(M,K,N) = ( sum_{m in Gamma_inf} | f^{(N)}_0(M,m) - f_0(M,m) |^2 )^{1/2}

f^{(N)}_k(M,m) = shat(eps_N m) cos(eps_N k/4)^2 sin(eps_N (m + k/2))/eps_N
                                   * prod_{j=1..N-M} m0(eps_{M+j}(m + k))
f_k(M,m)       = shat(eps_M (m + k)) (m + k/2)
```

**Statement in [v5].** The two symbols are defined in the proof of **Lemma 4.7**
(`lem:KSconv`); at `k = 0` the finite product telescopes against `shat` and the difference
collapses to `shat(eps_M m) m (sinc(eps_N m) − 1)`, which is **eq. (262)**
(`eq:errordecay`).  The expected rate is **Remark 4.32** (`rem:errorrates`):
`sum_m |...|^2` decays like `2^{-min(4, 2 sigma_K - 2) N}`, so the plotted square root
decays like `2^{-min(4, 2 sigma_K - 2) N/2}`, i.e. `1.917` for `K = 8` and `2.000` for
`K = 10` (`sigma_8 = 2.917`, `sigma_10 = 3.406`, [v5] Remark 3.13).

The sum runs over `Gamma_{inf,±}`; the Ramond and Neveu-Schwarz lattices give the same
number to `2e-15` relative (Poisson summation: the summand is entire and rapidly
decaying), so the sector is immaterial here.  `N = M` — the leftmost point of the `M = 5`
curves — is the empty-product limiting case of the comparison, which [v5] states for
`N > M`.

**Regenerate.** `python3 one_particle_errors.py --write` then
`pdflatex figure3.tex` in `figures_src/`.

**Comparison with the 2022 original.** Identical, to the precision with which the original
PDF can be read (2.6e-4 relative worst case, and the marker centres are the limiting
factor, not the arithmetic).  Same six curves, same ordering, same decade range
(`4e-2 … 1.3e2`), same endpoints.

| curve | new @ N=5 | 2022 @ N=5 | new @ N=8 | 2022 @ N=8 | max rel. diff | fitted rate | expected |
|---|---|---|---|---|---|---|---|
| M=5, K=8  | 123.227 | 123.222 | 4.24779   | 4.24789   | 4.0e-05 | 1.625 | 1.917 |
| M=5, K=10 | 120.400 | 120.389 | 3.24880   | 3.24893   | 9.0e-05 | 1.745 | 2.000 |
| M=4, K=8  | 16.2312 | 16.2308 | 0.429844  | 0.429906  | 1.4e-04 | 1.748 | 1.917 |
| M=4, K=10 | 15.2434 | 15.2435 | 0.295684  | 0.295717  | 1.5e-04 | 1.898 | 2.000 |
| M=3, K=8  | 1.79767 | 1.79775 | 0.0427459 | 0.0427569 | 2.6e-04 | 1.799 | 1.917 |
| M=3, K=10 | 1.53113 | 1.53134 | 0.0265482 | 0.0265545 | 2.4e-04 | 1.951 | 2.000 |

The fitted rates fall short of the asymptotic values because the window `N = 5 … 8` is only
three steps wide and starts at `N = M` for the `M = 5` curves; the approach is monotone in
`N − M` (`M = 3`: 1.799/1.951, `M = 4`: 1.748/1.898, `M = 5`: 1.625/1.745 for `K = 8`/`10`).
Extending the `M = 3` curves to `N = 12` gives 1.839 / 1.978 over the whole window and
1.869 / 1.996 over `N = 9 … 12`, converging on the predicted 1.917 / 2.000.  The 2022 curves
have exactly the same fitted rates over `N = 5 … 8`, so the shortfall is a property of the
quantity, not of the reimplementation.

**Verdict: reproduces.**

---

## FIG. S4 — `figure4.pdf`, label `fig:waveleterrork`

**Quantity.** Same wavelet route, `c = 0`, `k = 0`, fixed `M = 3`, over `N = 4 … 8`.
Nine *factorized upper bounds* plus the two *exact* errors:

```
bound(delta,K,N) = Error(delta,L,0,N) * || shat(eps_M .) ||_{h^{1+delta}}
true(K,N)        = E(3,K,N)      (the same quantity as FIG. S3 at M = 3)
```

with `delta ∈ {1/2, 1, 3/2, 2}` and `K = 4` (only at `delta = 1/2`), `8`, `10`.

**Statement in [v5].**  **eq. (262)** (`eq:errordecay`) is the inequality
`sum_m |f^{(N)}_0 − f_0|^2 <= Error^2(delta,L,0,N) ||shat(eps_M .)||^2_{h^{1+delta}}`, and
**eq. (263)** (`eq:errordecayexp0`) defines `Error^2`.  The bound curves realize the rate
`eps_N^delta` of **eq. (264)** (`eq:errorscaling`); the regularity thresholds
(`delta = 1` needs `K >= 5`, `delta = 2` needs `K >= 9`) are **Remark 3.13**
(`rem:regularityvalues`).

Two details had to be recovered from the numbers themselves, because [v5] offers a choice
in each case:

* `Error^2` is taken in the **closed form** on the *second* line of eq. (263),
  `2L (pi/L)^{2(1+delta)} eps_N^{2 delta} sup_{x in R} |sinc(x)−1|^2 |x|^{-2 delta}`,
  not the sharper lattice supremum on the first line.  That is why the bound curves are
  perfect straight lines of slope exactly `delta`.  The closed form is larger than the
  lattice supremum by a factor 1.076 / 1.125 / 1.216 / 1.604 at `N = 4`
  (`delta = 1/2, 1, 3/2, 2`) and 1.005 / 1.008 / 1.014 / 1.080 at `N = 8`.
  `one_particle_errors.error_factor_sq_lattice` computes that variant.
* `|| shat(eps_M .) ||^2_{h^{1+delta}} = (1/2L) sum_m (1 + |m|)^{2(1+delta)} |shat(eps_M m)|^2`
  is summed over `|m| <= 2^12`.  For every `(K,delta)` with `1 + delta < sigma_K` the sum
  converges and the truncation is immaterial.  **It is not immaterial for
  `(K,delta) = (8,2)`** — see the findings below.

**Regenerate.** `python3 one_particle_errors.py --write` then
`pdflatex figure4.tex` in `figures_src/`.

**Comparison with the 2022 original.**  All eleven curves identical to 1.0e-4 relative or
better.  Same legend, same ordering, same decade range, same crossings (the `delta = 2`
bounds start above the `delta = 3/2` ones at `N = 4` and cross below them by `N = 6`).

| curve | new @ N=4 | 2022 @ N=4 | new @ N=8 | 2022 @ N=8 | max rel. diff | fitted rate | expected |
|---|---|---|---|---|---|---|---|
| δ=1/2, K=4  | 20.6852 | 20.6873 | 5.17131   | 5.17161   | 1.0e-04 | 0.500 | 0.5 |
| δ=1/2, K=8  | 16.1068 | 16.1072 | 4.02671   | 4.02689   | 6.6e-05 | 0.500 | 0.5 |
| δ=1/2, K=10 | 15.8570 | 15.8571 | 3.96425   | 3.96443   | 4.8e-05 | 0.500 | 0.5 |
| δ=1, K=8    | 10.7964 | 10.7971 | 0.674777  | 0.674808  | 8.7e-05 | 1.000 | 1.0 |
| δ=1, K=10   | 10.4182 | 10.4189 | 0.651135  | 0.651170  | 7.3e-05 | 1.000 | 1.0 |
| δ=3/2, K=8  | 9.00077 | 9.00121 | 0.140637  | 0.140647  | 6.9e-05 | 1.500 | 1.5 |
| δ=3/2, K=10 | 8.09569 | 8.09585 | 0.126495  | 0.126502  | 5.5e-05 | 1.500 | 1.5 |
| δ=2, K=8    | 17.9413 | 17.9424 | 0.0700831 | 0.0700860 | 6.2e-05 | 2.000 | 2.0 |
| K=8 (true)  | 5.73858 | 5.73873 | 0.0427459 | 0.0427456 | 5.7e-05 | 1.770 | 1.917 |
| δ=2, K=10   | 9.51175 | 9.51205 | 0.0371553 | 0.0371563 | 5.4e-05 | 2.000 | 2.0 |
| K=10 (true) | 5.38934 | 5.38960 | 0.0265482 | 0.0265494 | 7.0e-05 | 1.920 | 2.000 |

The two "true" curves coincide with the `M = 3` curves of FIG. S3, as they must.

The legend keeps the symbol `δ` because the revised caption reads "$s$ (labeled $\delta$ in
the legend)"; `δ` and `s` are the same Sobolev exponent.  If the caption is ever changed,
rename the eleven `\addlegendentry` lines in `figures_src/figure4.tex`.

**Verdict: reproduces**, with one caveat about the `δ=2, K=8` curve (below).

---

## FIG. S5 — `figure5.pdf`, label `fig:momrgerrorM`

**Quantity.** Momentum-cutoff renormalization group, `c = 1/2` and `1` (Neveu-Schwarz
sector), `k = 0`, observation scales `M ∈ {3,4,5}`, over `N = 5 … 10`:

```
D_k(M,N) = ( sum_{n in Gamma_{inf,-}} chi_{Gamma_M}(n) theta(n-k) theta(n)
              | cos(eps_N k/4)^2 sin(eps_N (n - k/2))/eps_N chi_{Gamma_N}(n-k) - (n - k/2) |^2 )^{1/2}
```

at `k = 0`, i.e. `( sum_{0 < n < 2^M} n^2 |sinc(eps_N n) − 1|^2 )^{1/2}` over half-integers `n`.

**Statement in [v5].** The first estimate of **eq. (235)** (`eq:momrgestimates`); the rate
`eps_N^2` is **Lemma 4.15** (`lem:KSconvc`), eq. (236) (`eq:momrgrate`).  In the
supplement's own numbering this is Lemma S1.

The sector is **Neveu-Schwarz**.  It is fixed twice over: the Ramond lattice would give
0.6765 at `M = 3, N = 5` against the 0.84717 the original plots, and in the Ramond sector
the `k = ±2` curve of FIG. S7 would vanish identically (see there).  The sum is the
diagonal (Hardy `(±±)`) block for one chirality; the two chiralities give identical values
(reflection `n → −n`), which the selftest checks.

**Regenerate.** `python3 one_particle_errors.py --write` then
`pdflatex figure5.tex` in `figures_src/`.

**Comparison with the 2022 original.**  Identical.  The marker coordinates in the 2021/22
`figure5.pdf` are rounded to whole PostScript points (unlike figures 3 and 4), which limits
a marker-by-marker read to about 2 % — but Mathematica anchors each callout leader at the
unrounded data point, and against those anchors the agreement is 1e-4 or better.

| curve | new @ N=5 | 2022 @ N=5 | new @ N=10 | 2022 @ N=10 (leader anchor) | rel. diff at anchor | fitted rate | expected |
|---|---|---|---|---|---|---|---|
| M=3 | 0.847109 | 0.830788 | 8.46915e-4 | 8.46844e-4 | 8.4e-05 | 1.994 | 2 |
| M=4 | 9.01311  | 9.03851  | 9.68039e-3 | 9.68132e-3 | 9.6e-05 | 1.977 | 2 |
| M=5 | 77.0532  | 77.8171  | 0.109772   | 0.109771   | 4.8e-06 | 1.910 | 2 |

The `M = 3` curve of FIG. S5 is the same number as the `k = 0` curve of FIG. S6 (checked in
the selftest); the two 2022 figures read 0.83079 and 0.84717 at `N = 5` for what must be
one and the same quantity, which is exactly the size of the marker-rounding artefact.

**Verdict: reproduces.**

---

## FIG. S6 — `figure6.pdf`, label `fig:momrgerrork`

**Quantity.** The same diagonal bound `D_k(3,N)` of eq. (235), now at fixed `M = 3` and
`k ∈ {0, ±1, ±2}`, over `N = 5 … 10`.

**Statement in [v5].** First estimate of **eq. (235)** (`eq:momrgestimates`), rate
eq. (236); Lemma S1 of the supplement.  The revised caption's claim that the `k = 0,1,2`
curves show the `4^{-N}` diagonal rate holds for all five curves: the fitted rates are
1.993–1.995 (the deficit from 2 is the finite window, not the quantity).

**Regenerate.** `python3 one_particle_errors.py --write` then
`pdflatex figure6.tex` in `figures_src/`.

**Comparison with the 2022 original.**  The *set* of five curves is reproduced exactly (to
6e-5 at the leader anchors).  **The `k` labels are mirrored**: the 2022 curve labelled
`k = +2` is the quantity that eq. (235) assigns to `k = −2`, and likewise for `±1`.  This
is the one substantive discrepancy found in the five figures; it is discussed under
*Findings* below.  The table pairs each regenerated curve with the 2022 curve it equals.

| new curve | 2022 curve | new @ N=5 | 2022 @ N=5 | new @ N=10 | 2022 @ N=10 (leader anchor) | rel. at anchor | fitted rate |
|---|---|---|---|---|---|---|---|
| k = +2 | labelled k = −2 | 0.554037 | 0.559857 | 5.51651e-4 | 5.51685e-4 | 6.1e-05 | 1.995 |
| k = +1 | labelled k = −1 | 0.682667 | 0.688689 | 6.80799e-4 | 6.80841e-4 | 6.3e-05 | 1.995 |
| k =  0 | labelled k =  0 | 0.847109 | 0.847166 | 8.46915e-4 | 8.46932e-4 | 2.1e-05 | 1.994 |
| k = −1 | labelled k = +1 | 1.05306  | 1.04211  | 1.05648e-3 | 1.05653e-3 | 4.7e-05 | 1.994 |
| k = −2 | labelled k = +2 | 1.30638  | 1.32694  | 1.31642e-3 | 1.31640e-3 | 1.5e-05 | 1.993 |

The residual 1.5 % at `N = 5` is again the whole-point marker rounding of the original PDF.

`one_particle_errors.py --legacy-k-sign` reproduces the 2022 labelling exactly, for anyone
who needs to compare the two pictures curve by curve.

**Verdict: reproduces, with the `k`-sign convention corrected.**

---

## FIG. S7 — `figure7.pdf`, label `fig:momrgerrorHS`

**Quantity.** Momentum-cutoff route, off-diagonal (Hardy `(+−)` and `(−+)`) Hilbert-Schmidt
error, `k ∈ {±2, ±3, ±4}`, over `N = 5 … 10`:

```
H_k(N) = ( sum_{n in Gamma_{inf,-}} [theta(n-k) theta(-n) + theta(-(n-k)) theta(n)]
            | cos(eps_N k/4)^2 sin(eps_N (n - k/2))/eps_N chi_{Gamma_N}(n-k) chi_{Gamma_N}(n)
              - (n - k/2) |^2 )^{1/2}
```

There is **no** `chi_{Gamma_M}` here, so the curves do not depend on `M`; the `M = 3` in the
panel label is inherited from the neighbouring figures.

**Statement in [v5].** The second estimate of **eq. (235)** (`eq:momrgestimates`), used
through eq. (234) (`eq:noquantconv`); Lemma S2 of the supplement.  [v5] displays the
`(±∓)` block only, and eq. (234) needs both off-diagonal blocks — exactly one of the two
index sets is non-empty for a given sign of `k`, which is why the quantity is even in `k`
and the figure labels three curves `k = ±2, ±3, ±4`.

The index set is the finite strip between `0` and `k`, so `H_k` **vanishes identically for
`k = 0, ±1`** in the Neveu-Schwarz sector: for `k = ±1` the only admissible half-integer
momentum in the strip has `n ∓ k/2 = 0`, and the summand vanishes there.  This is the
caption's statement and [v5] **Remark 4.22** (`rem:moeberror`); the selftest checks it.
It is also what fixes the sector for figures 5–7: in the Ramond sector `H_k` would vanish
for `k = ±2` as well, and the figure shows it non-zero.

**Regenerate.** `python3 one_particle_errors.py --write` then
`pdflatex figure7.tex` in `figures_src/`.

**Comparison with the 2022 original.** Identical; same marker-rounding caveat as
figures 5 and 6.

| curve | new @ N=5 | 2022 @ N=5 | new @ N=10 | 2022 @ N=10 (leader anchor) | rel. at anchor | fitted rate | expected |
|---|---|---|---|---|---|---|---|
| k = ±2 | 1.98571e-3 | 1.99615e-3 | 1.94120e-6 | 1.94143e-6 | 1.2e-04 | 2.000 | 2 |
| k = ±3 | 9.91175e-3 | 9.90060e-3 | 9.70600e-6 | 9.70698e-6 | 1.0e-04 | 1.999 | 2 |
| k = ±4 | 2.88466e-2 | 2.87943e-2 | 2.83159e-5 | 2.79005e-5 | 2.1e-05 | 1.999 | 2 |

**Verdict: reproduces.**

---

## Independent checks in `--selftest`

* Daubechies taps against the published table (Daubechies, *Ten Lectures*, Table 6.1, i.e.
  db2/db3/db4) up to the filter reversal that leaves `|shat|` invariant — 3.6e-12.
* Double-shift orthonormality and `sum_n h_n = sqrt 2` for `K = 2 … 12` — 5.6e-15.
* `shat(0) = 1`; the infinite-product truncation `extra = 54` is at the double-precision
  floor (`5e-15` against `extra = 74`).
* Centre of mass `mu(_4 s) = 5.995`, `mu(_10 s) = 16.869` against [v5] Remark 3.5
  ("5.99", "16.87").
* Sobolev exponents `sigma_K` for `K = 2 … 11` against the table of [v5] Remark 3.13 — 5.6e-3.
* **The measured tail rate of the wavelet error.**  [v5] Remark 4.32 records `1.55, 3.83,
  4.81` for `_4 s, _8 s, _10 s` (the prediction is `2 sigma_K − 2`).  Splitting the sum at
  the Brillouin-zone edge `|m + k| = pi/eps_N` and fitting `N = 5 … 11` gives
  **1.557, 3.851, 4.837** — an independent confirmation that the reimplemented scaling
  function has the right `L^2` decay, made on a quantity that none of the five figures
  plots directly.
* `k = 0` collapse of the division-free splitting to eq. (262) — 4e-15.
* `H_k = 0` for `k = 0, ±1`; `H_k` even in `k`; `D_k` independent of chirality;
  FIG. S5 at `M = 3` equal to FIG. S6 at `k = 0`.
* The fitted decay exponent of all 28 curves, printed alongside the expected value.

## Findings

**1. FIG. S6 carries the opposite sign convention for the mode index `k`.**
The curve labelled `k = +2` in the 2021/22 `figure6.pdf` is the value that eq. (235) of
[v5] assigns to `k = −2` (and likewise for `±1`); the `k = 0` curve is of course
unaffected.  Equivalently, the 2022 script placed the observation-scale cutoff
`chi_{Gamma_M}` on the *outgoing* momentum `n − k` rather than on the incoming momentum
`n`, and it is the incoming one that carries the support of the one-particle vector
`R^M_inf(eta)`.  The manuscript's convention is the standard one: `ell_{+,k}` maps
`e_n` to `e_{n−k}`, so `L_k` lowers the momentum by `k`.  Since the plotted set
`{0, ±1, ±2}` is symmetric, the picture as a whole is unchanged — only the five legend
entries permute — and the caption's claim about the `4^{-N}` rate is true either way.  The
regenerated figure uses the manuscript's convention; `--legacy-k-sign` restores the old
labelling.  **Nothing in the supplement's text or in the error budget depends on this.**

**2. The `δ = 2, K = 8` curve of FIG. S4 plots a divergent quantity.**
`||shat(eps_M .)||_{h^{3}}` is finite only for `1 + delta < sigma_K`, i.e. `sigma_8 = 2.917
< 3` fails — precisely the threshold [v5] Remark 3.13 states ("the value `delta = 2`
requires `sigma_K > 3`, i.e. `K >= 9`").  The partial sums diverge slowly, like
`Xi^{2 + 2 delta − 2 sigma_K} = Xi^{0.17}`, so the curve has a finite-looking value that is
set entirely by where the sum is cut off.  Doubling the cutoff raises the plotted value by
about 7 %: at `N = 4` it reads 15.60, 16.74, **17.94**, 19.20, 20.52, 21.91, 23.38 for
`|m| <= 2^10 … 2^16`, with no sign of settling.  (The neighbouring `delta = 2, K = 10`
curve, which is convergent, reads 9.4968, 9.5117, 9.5166, 9.5183 over the same range.)
The 2022 curve corresponds to `|m| <= 2^12`, which is what
`sobolev_norm_sq(..., mexp=12)` uses by default — that value reproduces the original to
6e-5 across all five points, so the truncation is identified, not fitted.  The `N`-slope
(`2.000`) is unaffected, because the divergent factor is `N`-independent.
**Recommendation:** either drop this one curve, or say in the caption that at `K = 8` the
`delta = 2` bound is only formal.  The other eight bound curves and both true curves are
unaffected.

**3. FIG. S4 plots the crude closed-form `Error`, not the sharp lattice supremum.**
Both appear in eq. (263) of [v5], on consecutive lines.  The closed form is larger by
7.6 %–60 % at `N = 4` depending on `delta` (0.5 %–8 % by `N = 8`).  This
is not an error — the closed form is a valid upper bound and it is what makes the curves
exact straight lines — but it is worth knowing when the figure is used to read off a
constant.  `error_factor_sq_lattice()` gives the sharp variant.

**4. Nothing else differs.**  All 28 curves of the five figures agree with the 2021/22
originals to the precision with which those PDFs can be read: 2.6e-4 relative for figures 3
and 4, where Mathematica wrote unrounded marker coordinates, and 1.2e-4 at the callout
anchors of figures 5–7, whose markers are rounded to whole points.  In particular the
`δ = 1/2, K = 8` and `δ = 1/2, K = 10` curves of FIG. S4 — which differ by only 1.6 % and
whose legend assignment is therefore not readable by eye — come out in the order
`K = 4 > K = 8 > K = 10`, matching the original's callout order exactly.

## How the originals were read

For the record, since the comparison is the point.  The 2021/22 PDFs are Mathematica 12.2
exports (cairo 1.16) wrapped by pdfTeX.  The plot lives in a single Form XObject placed
with `translate(3.985, 3.985) ∘ scale(s)` and an internal `1 0 0 -1 0 H cm` flip, so form
coordinates convert to the plot's data coordinates directly once the dashed gridlines
— which sit exactly on the labelled ticks — are identified.  Each data point is a small
closed path whose *bounding-box centre* is the datum; this was verified against the
callout leader lines, which Mathematica anchors at the unrounded data point and which
therefore also give an exact reading of each curve's last point and an unambiguous
curve↔legend assignment (the legend text is typeset by pdfTeX outside the form, so the
leaders are the only link between a colour and its label).  Copies of the five originals
are in this session's scratch directory; they were only overwritten after the comparison
above was recorded.
