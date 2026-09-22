# README-SITE — what is in `public/`, and what a reviewer should check

For Alexander, 22 September 2026. This is the note about the site, not part of the site's
prose. The site's own honesty statements are in `docs/status.html` and `docs/results.html`.

---

## What this is

The Pages site and documentation index required by §§ 7–8 of `PUBLICATION-PLAN.md`, built
under `public/` and nowhere else. No git command was run.

```
public/
  docs/                      ← the Pages root (.nojekyll is there)
    index.html               home + the navigable index of § 8
    status.html              established / assembled / numerical / open, plus the corrections
    notation.html            every symbol, and the two conventions this site had to fix
    definitions.html         the model, OAR, Koo–Saleur, what is simulated, the four steps
    results.html             Thm S1, Props S1–S2, Lems S1–S5, one line and a status each,
                             plus the table of every number taken from the manuscript
    widgets/
      index.html             the widget index and how the check badges work
      a-scales.html          A · N, M, r = N − M
      b-lattice-model.html   B · staggered lattice → Jordan–Wigner → XY chain
      c-koo-saleur.html      C · the one-particle symbol and where the rate comes from
      d-ground-state.html    D · U_FT U_B drawn and counted
      e-error-budget.html    E · Theorem S1, both terms                        ← priority
      f-resource-scaling.html F · δ^-1/2 sites, δ^-3/2 gates                   ← priority
      g-near-term.html       G · 128 sites / 256 qubits, and the failing constraint
      h-correlator.html      H · Fig. S7 recomputed in the browser             ← priority
      i-energy-shell.html    I · Λ_k(T), linear only at k = 0
      j-one-particle.html    J · a pointer, deliberately not a widget
    assets/
      site.css  cft.js  plot.js  widget.js  math.js
      katex/    vendored KaTeX 0.16.11: css, js, auto-render, 20 woff2 faces (296 KB)
    data/       anchors budget circuit correlator resources symbol  (*.json)
    figures/    error-budget scales resource-scaling correlator-convergence  (*.svg)
  tools/
    make_data.py      writes docs/data/*.json              (numpy + stdlib)
    make_figures.py   writes docs/figures/*.svg            (stdlib only, SVG written directly)
    check_js.mjs      the browser's kernels vs the JSON, outside a browser
    check_pages.mjs   loads every page under DOM stubs and sweeps every control
```

Reproduce everything:

```sh
python3 tools/make_data.py            # ~50 s, the correlator dominates
python3 tools/make_data.py --check    # recompute and diff against what is committed
python3 tools/make_figures.py
node    tools/check_js.mjs            # 467/467 agree, worst relative difference 8.4e-6
node    tools/check_pages.mjs         # every page loads, every control sweeps, every badge passes
cd docs && python3 -m http.server 8000
```

---

## What I built, and the two design decisions worth your veto

**1. Nine widgets, not ten, and J is a pointer.** Widget J would have rebuilt Figs. S2–S6.
Two reasons not to: the generating code for those figures does not exist anywhere in the
repository (§ 4 of the plan), so a widget would be a *new* computation presented as a
reproduction; and the mathematics is the companion project's, which already computes exactly
those quantities. `j-one-particle.html` says both, and links across. If you would rather have
the widget, § 4 has to be closed first.

**2. Widget E draws the k ≠ 0 branch with C₀ = 1 and says that is not its value.** There was no
honest alternative: the supplement names C₀(M,k,L,K) and does not evaluate it. The curve shows
the slope and the T-dependence, the readout refuses to convert it into a lattice size, and the
prose says so three times. If you think even a shape is too much, the branch can be dropped.

**Two things the site found while being built**, both now stated on the pages:

- **On the chiral algebra the two terms of Theorem S1(i) are parallel.** Term I is
  `(d_A+d_B)(π²/16)4^M · 4^-N` and term II is `(1/6)d_B Θ_M T · 4^-N`: both carry `4^-N`, so
  their ratio is fixed by M, T and the degrees and does not change with N. They cross only on
  the *full* two-component algebra, where term I is first order, `2^-r`. I had written a
  "where do they cross" readout before noticing; it is now a "they are parallel, and here is
  the ratio" readout. Worth a look — it is a structural fact about the theorem, and I did not
  find it stated in the supplement.
- **At the near-term point the k = 0 correlator bound is far below 0.4.** At N = 6, M = 3,
  d_A = d_B = 1, T = 1, chiral: term I = 1.93e-2, term II = 2.20e-2, total 4.12e-2. That is
  *not* in conflict with δ₀ ≈ 0.4, because 0.4 is a **one-particle, wavelet-route, k = 0**
  bound and 4.12e-2 is a **correlator, momentum-cutoff, k = 0** bound — different quantities on
  different routes. The site says so in `f-resource-scaling.html` ("a different, smaller number,
  because it is a different quantity") but a reader could still run them together, and the
  Letter's own near-term sentence invites it.

---

## Every number taken from the supplement, with the line it came from

All line numbers are in `resubmission/qscft_prl_220615_supp.tex` unless marked `main`.

| value | line(s) | statement |
|---|---|---|
| `δ^{-3/2} = δ^{-1} × δ^{-1/2}` | 980–987 | Eq. (S32) and the sentence after: "reproducing the Letter's headline scaling … a Heisenberg-limited measurement cost δ^{-1} times the discretization cost δ^{-1/2}" |
| `n = 2^{N+1}`, `2n = 2^{N+2}` | 212, 844–845; `main` 137 | "Throughout, n = 2^{N+1} …"; "n = 2^{N+1} is the number of lattice sites, 2n = 2^{N+2} the number of system qubits" |
| `ε_N² = 4^{-N}` | 323 | caption of Fig. S1: "every leaf carries the one-particle rate ε_N² = 4^{-N}" |
| `η ≤ (π/4)2^{-(N-M)}` (full), `(π²/16)2^{-2(N-M)}` (chiral) | 341–342, 476–477 | Theorem S1(i); Lemma S4 |
| term II `= (1/6) d_B Θ_M \|t\| ε_N²` | 339 | Theorem S1(i) |
| `Θ_M = (Σ_{l∈Γ_M} θ(±l)\|l\|⁶)^{1/2}` | 344 | Theorem S1(i), "with Θ_M … explicit" |
| `r = N − M`, error scales in r not N | 484–486 | Lemma S4, Source and mechanism, [v5, Rmk 6.4(1)] |
| `C ~ C₀ m² Λ_k(T)`, `Λ_k(T) = (e^{c_k T}−1)/c_k`, `c₀ = 0` | 350–359 | Theorem S1(ii) |
| "the numerical value of C₀ is not computed here" | 358–359, 718–721 | Theorem S1(ii); Proposition S2, Sketch |
| `N ≥ ½log₂(C/δ)`, `n ≲ 2C^{1/2}δ^{-1/2}` | 363–367, 727–732 | Eq. (S8); Eq. (S30) |
| near-term: D10, δ = 1/2, 128 sites, N = 6, 256 qubits, M = 3, r = 3 | 993–996 | § The near-term figure |
| one-particle bound ≈ 0.4 at N = 6, M = 3; scale-5 needs N ≈ 10 | 997–998 | same |
| `2^M ≳ 2K−1` not met at M = 3, K = 10 | 757–760 | § Reconciliation with the Letter |
| σ_K = 1.000 … 3.406 for K = 2…10; 2-regular ⇔ K ≥ 5, 3-regular ⇔ K ≥ 9 | 218–220 | § Discretization error analysis, "Throughout" [v5, Rmk 3.13] |
| `O(m²)` from the telescoping | 671, 678–680 | Eq. (S27) and the paragraph after |
| Table S1 per-step counts, `T^{1+o(1)}δ^{-3/2-o(1)}` | 936–965 | Table S1 |
| ground state `O(n log n)` gates, depth `O(log² n)`, 0 ancillas | 890–893 | § Cost and exactness |
| readout `O(1/δ)` calls, `r = O(log 1/δ)` ancillas | 923–928 | § Readout (Step 4) |
| fitted per-step ratio 4.00; k = 2 growth at `t ≳ 1.5` | 1106–1111 | caption of Fig. S7 |
| `c_{σ,k} ≤ C_L σ\|k\|⟨k⟩^{σ+2}` | 587–588 | § Quantitative Duhamel |
| `Λ_{k,p}(t) = (e^{p c_k \|t\|}−1)/(p c_k)` | 568 | Eq. (S22) |
| Lemma S1 rate `ε_N^{min{δ_s,2}}`, sharp; δ_s = 2 at K ≥ 5 | 394–404 | Lemma S1 |
| Lemma S2 `‖·‖₂² ≤ C₂(k)ε_N⁴`, strip `0<\|l\|<\|k\|`, `2(\|k\|−1)` points, empty at k = 0,±1 | 419–435 | Lemma S2 |
| Lemma S3 slot factor `(p+2)` | 445–454 | Lemma S3 |
| Lemma S5 `‖L_k^{(N)}Ψ‖ ≤ b_k‖N^{(N)}Ψ‖`, growth `e^{p c_k\|t\|}`, `c₀ = 0` | 524–541 | Lemma S5 |
| wavelet route: `ε_N` for k ≠ 0, `n ~ C_T δ^{-1}`; re-centring restores ½ | 369–375, 749–753 | Theorem S1 closing; § Reconciliation |
| the four corrections to the published companion | 182–191 | § Discretization error analysis, opening |
| 2022 version said "128 logical qubits" and `δ^{-1}` | — | `Final/qscft_prl_0322_main.tex`, abstract and Introduction (checked directly) |

The same list, machine-readable and with the locators, is `docs/data/anchors.json`; it is also
rendered as a table in `docs/results.html#anchors`.

---

## What a reviewer should check, in order

1. **The status labels in `results.html`.** Every statement is marked *established* (with a
   locator), *assembled here*, or *cited*. I derived these from the supplement's own
   "Established … / Assembled here …" paragraphs (lines 192–210 and 800–829). If any label is
   wrong, it is wrong in the direction that matters most.
2. **`Θ_M` and the mode-set convention.** The supplement writes `Γ_M` without normalizing it.
   I used `Γ_N = { l ∈ Z+½ : |l| < 2^N }` — half-integer NS modes, `|Γ_N| = 2^{N+1} = n`,
   `ε_N = 2^{-N}` — which is `numerics_correlator.py`'s convention and the one that makes
   `ε_N² = 4^{-N}` true. **`Θ_M`'s absolute value depends on this choice** (`Θ₃ = 539.885`),
   so if the intended Γ_M is different, every `Θ_M` number on the site changes. Flagged in
   `notation.html#conventions` and in widget E. The companion repository uses `ε = π2^{-N}`;
   the rates agree, the constants do not.
3. **Widget D's exact gate counts.** The supplement gives only `O(n log n)` and `O(log² n)`.
   The counts on the page — `(2n/2)log₂(2n)` butterflies, `n` Bogoliubov rotations — are *my*
   arithmetic for one concrete radix-2 network. The page says so twice, including in the check
   note, but it is the one place where the site puts a number where the manuscript has a
   big-O.
4. **Widget H against `numerics_correlator.py`.** My `tools/make_data.py` reimplements it with
   the band structure exploited (the symbol splits into k tridiagonal chains) instead of a dense
   `eigh`. I verified the two agree to machine precision before switching, and the browser's
   independent implicit-QL sweep agrees with numpy to ~1e-13 absolute. The numbers the site
   shows — `4.000` per-step ratio over N = 6…10, `1.2e-2` at k = 2, t = 2, N = 8 — match the
   original script's printed self-checks.
5. **The four corrections in `status.html#corrections`.** Two of them (the 2022 "128 logical
   qubits" and the `δ^{-1}`) I verified directly against `Final/qscft_prl_0322_main.tex`. The
   four about the published companion are quoted from the supplement's own opening paragraph,
   not independently verified against the companion.
6. **Every "what this does not show" line.** They are the part I would most like adversarially
   read: each is a claim about a limitation, and an understated one is worse than none.

---

## One coordination note

While I was working, `public/` also acquired `README.md`, `LICENSE`, `LICENSE-CODE`,
`CITATION.cff`, `.gitignore`, `.github/workflows/build.yml` and `.githooks/pre-commit` —
not mine, and I have not touched them. They fit together with this site cleanly, with one
loose end: the workflow's check step looks for `tools/check_widgets.py`, guarded by
`if [ -f ... ]`, so it currently does nothing. The two check scripts this site ships are
`tools/check_js.mjs` and `tools/check_pages.mjs`, both of which exit non-zero on failure.
Wiring them in is two lines:

```yaml
      - run: node tools/check_js.mjs
      - run: node tools/check_pages.mjs
```

`.gitignore` excludes nothing of the site's; `docs/pdf/` is the only `docs/` path it
touches and this site does not create one.

## What I left out

- **Widget J**, for the reasons above.
- **Static SVG fallbacks for B, C, D, G, I.** Those five have a prose fallback inside
  `<noscript>` but no picture; the four priority widgets (A, E, F, H) have both. Adding the
  rest is `tools/make_figures.py` plus four more functions.
- **A `<picture>` element per figure.** Not needed: each SVG carries its own
  `prefers-color-scheme` stylesheet, so one file serves both themes in one request.
- **Any link to the Letter or supplement PDFs.** They are built by CI in the plan's layout and
  this export does not contain them; `index.html` describes the documents without linking.
- **A CI workflow.** `.github/workflows/build.yml` is § 2.1's, not § 7's; the two check
  scripts are written to exit non-zero so they can be dropped into one.
- **The published-companion corrections, independently verified.** I took them from the
  supplement.

## Accessibility and robustness, as built

Controls are real `<input>`/`<select>` elements inside `<label>`s, so Tab and the arrow keys
reach everything; the theme button is a real `<button>`; there is a skip link; the check tables
have `<caption>` and scoped `<th>`; the canvases carry `role="img"`; readouts are
`aria-live="polite"`. Control state is mirrored into the URL fragment, so any configuration is
linkable. `prefers-reduced-motion` collapses transitions, and widget I animates the shell expanding
against the cutoff behind a play button that **starts paused whatever your settings are**, and
says why when reduced motion is requested. `tools/check_pages.mjs` presses that button and runs
a few frames. Light and dark are both first-class: tokens are redefined under
`prefers-color-scheme` *and* under an explicit `data-theme`, so the header button wins over the
system. The layout drops to a single column and shrinks the canvases below 620 px.

**Nothing is fetched from a third party.** KaTeX is vendored with its fonts; the only absolute
URLs in the whole site are the two W3C XML namespaces inside `katex.min.js`, the DOI and arXiv
links in the prose, and the GitHub link to the companion repository.
