/* cft.js — every quantity the widgets draw, computed from the formulas of the
 * Supplemental Material.  No DOM, no dependency: this module runs unchanged in the
 * browser and under `node tools/check_js.mjs`, which is how the agreement with
 * tools/make_data.py is verified outside a browser.
 *
 * Conventions (see docs/notation.html).  eps_N = 2^{-N}; the momentum set retained at
 * scale N is Gamma_N = { l in Z + 1/2 : |l| < 2^N } (Neveu-Schwarz, half-integer modes),
 * so |Gamma_N| = 2^{N+1} = n and eps_N^2 = 4^{-N}.  This is the convention of
 * resubmission/numerics_correlator.py, and the one the supplement uses when it writes
 * eps_N^2 = 4^{-N}.
 */

export const PI = Math.PI;

/* ---------------------------------------------------------------- scales (widget A) */

export const sites = (N) => 2 ** (N + 1);            // n = 2^{N+1}            [supp, "Throughout, n = 2^{N+1}"]
export const qubits = (N) => 2 ** (N + 2);           // 2n = 2^{N+2}           [supp, Sec. "Resource accounting"]
export const depth = (N, M) => N - M;                // r = N - M              [supp, Lemma S4 "Source and mechanism"]
export const epsN = (N) => 2 ** -N;

/* Lattice-vacuum rate eta_M(N) of Lemma S4, a function of the depth r = N - M alone. */
export const etaFull = (r) => (PI / 4) * 2 ** -r;          // full two-component algebra
export const etaChiral = (r) => (PI * PI / 16) * 4 ** -r;  // chiral algebra

/* ------------------------------------------------- Koo-Saleur one-particle symbol (C) */

/* The lattice symbol entry of L_k^{(N)} in the plane-wave basis, and the continuum one.
 * Lemma S1 "Source and mechanism": the difference is
 *   eps^{-1} sin(eps (l -+ k/2)) - (l -+ k/2) = O(eps^2 |l -+ k/2|^3).            */
export const ksLattice = (x, N) => (x === 0 ? 0 : 2 ** N * Math.sin(2 ** -N * x));
export const ksContinuum = (x) => x;
export const ksDeviation = (x, N) => ksLattice(x, N) - x;
export const ksLeading = (x, N) => -(4 ** -N) * x * x * x / 6;   // the -eps^2 x^3/6 term

/* ------------------------------------------------------- error budget (widget E) */

/* Gamma_M = half-integer modes |l| < 2^M. */
export function gammaModes(M) {
  const L = 2 ** M, out = [];
  for (let l = -L + 0.5; l < L; l += 1) out.push(l);
  return out;
}
/* Theta_M = ( sum_{l in Gamma_M} theta(+-l) |l|^6 )^{1/2}, Theorem S1(i). */
export function thetaM(M) {
  let s = 0;
  for (const l of gammaModes(M)) if (l > 0) s += l ** 6;
  return Math.sqrt(s);
}

/* Theorem S1(i), the established k = 0 bound, term by term.
 *   |C^(N)_t - C_t| <= (dA + dB) eta_M(N)  +  (1/6) dB Theta_M |t| eps_N^2         */
export function budgetK0({ N, M, dA, dB, T, chiral = true }) {
  const r = N - M;
  const eta = chiral ? etaChiral(r) : etaFull(r);
  const I = (dA + dB) * eta;
  const II = (1 / 6) * dB * thetaM(M) * Math.abs(T) * 4 ** -N;
  return { I, II, total: I + II, eta, theta: thetaM(M), r };
}

/* Theorem S1(ii), the assembled k != 0 bound.  C ~ C_0(M,k,L,K) m^2 Lambda_k(T) and
 * Lambda_k(T) = (e^{c_k T} - 1)/c_k, with Lambda_0(T) = T because c_0 = 0.  C_0 is NOT
 * computed in the supplement, so `shape` is the bound divided by C_0 and is a shape, not
 * a number of any absolute meaning. */
export function horizon(cK, T) {
  if (Math.abs(cK) < 1e-12) return T;
  return (Math.exp(cK * T) - 1) / cK;
}
export function budgetKnonzero({ N, m, cK, T }) {
  return { shape: m * m * horizon(cK, T) * 4 ** -N, lambda: horizon(cK, T) };
}

/* Inversion of the rate, Eq. (S..) "Reconciliation": C eps_N^2 <= delta  <=>
 *   N >= (1/2) log2(C/delta),  n <~ 2 C^{1/2} delta^{-1/2}.                        */
export const NofDelta = (C, delta) => 0.5 * Math.log2(C / delta);
export const nOfDelta = (C, delta) => 2 * Math.sqrt(C) * Math.sqrt(1 / delta);
/* k = 0, everything explicit: N - M >= (1/2) log2(C d (1+T)/delta). */
export const depthOfDelta = (C, d, T, delta) => 0.5 * Math.log2((C * d * (1 + T)) / delta);

/* ------------------------------------------------------ resource scaling (widget F) */

/* Calibration of the near-term point, read off the one-particle D10 wavelet data at
 * observation scale M = 3: delta_0 ~ 0.4 at N = 6, i.e. n_0 = 128 sites / 256 qubits. */
export const DELTA0 = 0.4;
export const N0 = 6;
export const N_SITES0 = 128;

/* error = a / n^2 with a = delta_0 n_0^2  =>  n(delta) = n_0 (delta_0/delta)^{1/2}. */
export const sitesOfDelta = (delta) => N_SITES0 * Math.sqrt(DELTA0 / delta);
export const SITES_PREFACTOR = N_SITES0 * Math.sqrt(DELTA0);          // ~ 80.96
/* Gate count relative to the near-term run: O(1/delta) x (n T)^{1+o(1)}; the o(1) is
 * dropped, so this is the exponent statement delta^{-3/2}, not a gate count. */
export const gatesRel = (delta, T = 1) => (DELTA0 / delta) ** 1.5 * T;
/* Wavelet route without re-centring: n ~ delta^{-1} for k != 0, hence gates ~ delta^{-2}. */
export const sitesOfDeltaWavelet = (delta) => N_SITES0 * (DELTA0 / delta);
export const gatesRelWavelet = (delta, T = 1) => (DELTA0 / delta) ** 2 * T;
/* Dyadic lattice sizes on the sites line: at scale N the certified accuracy is
 * delta_N = delta_0 4^{6-N}. */
export const deltaOfN = (N) => DELTA0 * 4 ** (N0 - N);

/* ------------------------------------------- ground-state circuit counts (widget D) */

/* A concrete radix-2 network realizing the O(n log n) gates / O(log^2 n) depth that the
 * supplement quotes for U_FT, plus the one Bogoliubov rotation per Nambu pair for U_B.
 * The supplement states only the big-O; these exact counts are this page's arithmetic. */
export function circuit(N) {
  const n = sites(N), q = qubits(N);        // n sites, q = 2n qubits = 2n modes
  const stages = Math.log2(q);
  const butterflies = (q / 2) * stages;     // radix-2 FFT network on q modes
  const bogoliubov = q / 2;                 // one two-mode rotation per Nambu pair (k,-k)
  return {
    n, q, stages,
    butterflies,
    bogoliubov,
    twoQubitGates: butterflies + bogoliubov,
    ftDepthStages: stages,                  // butterfly stages
    ftDepthBound: stages * stages,          // O(log^2 q): swap routing inside each stage
    bogoliubovDepth: 1,                     // disjoint pairs, applied in parallel
    ancillas: 0,
  };
}

/* ------------------------------------------------- energy-shell confinement (widget I) */

/* Lemma S5: ||(N^{(N)})^p e^{itH} Psi|| <= e^{p c_k |t|} ||(N^{(N)})^p Psi||, c_0 = 0.
 * Lambda_{k,p}(t) = (e^{p c_k |t|} - 1)/(p c_k), = |t| at k = 0. */
export const shell = (E0, cK, t) => E0 * Math.exp(cK * t);
export function shellCrossing(E0, cK, N) {
  if (cK <= 0) return Infinity;
  const t = Math.log(2 ** N / E0) / cK;
  return t > 0 ? t : 0;
}
export function horizonP(cK, p, t) {
  if (Math.abs(cK) < 1e-12) return Math.abs(t);
  return (Math.exp(p * cK * Math.abs(t)) - 1) / (p * cK);
}

/* --------------------------------------- correlator convergence (widget H) ---------- */

/* The setting of resubmission/numerics_correlator.py, reimplemented.  Modes l in Z+1/2
 * with |l| < Lam.  The one-particle symbol of the simulated generator H_k = L_k + L_{-k}
 * is s = B + B^T with B[l+k, l] = eps^{-1} sin(eps (l + k/2))  (lattice, scale N) or
 * l + k/2 (continuum).  The observable vectors f, g are fixed, supported on |l| < 8
 * (observation scale M = 3), and identical at every scale.  The vacuum is the Dirac sea
 * P_< = projection onto l < 0.  Then
 *     C^{(N)}(t) = < e^{its} g , P_< f >  =  sum_j e^{-i t w_j} a_j b_j,
 * a = V^T g, b = V^T P_< f.  For k != 0 the matrix s has nonzeros only at |i-j| = k, so
 * it splits into k independent symmetric tridiagonal chains with zero diagonal; each is
 * diagonalized by the implicit-QL sweep below, which accumulates only the two projections
 * a and b rather than the whole eigenvector matrix.  Cost O(n^2) with a tiny constant.
 */

export function corrModes(Lam) {
  const m = 2 * Lam, out = new Float64Array(m);
  for (let i = 0; i < m; i++) out[i] = -Lam + 0.5 + i;
  return out;
}

export function corrVectors(Lam) {
  const ll = corrModes(Lam), m = ll.length;
  const f = new Float64Array(m), g = new Float64Array(m);
  for (let i = 0; i < m; i++) {
    if (Math.abs(ll[i]) < 8) {
      const e = Math.exp(-((ll[i] / 4) ** 2));
      f[i] = e; g[i] = ll[i] * e;
    }
  }
  let sf = 0, sg = 0;
  for (let i = 0; i < m; i++) { sf += f[i] * f[i]; sg += g[i] * g[i]; }
  const nf = Math.sqrt(sf), ng = Math.sqrt(sg);
  for (let i = 0; i < m; i++) { f[i] /= nf; g[i] /= ng; }
  return { f, g, ll };
}

/* Implicit-QL on a symmetric tridiagonal (d, e), transporting the rows of Z (an array of
 * Float64Array of length n) exactly as the eigenvector matrix is transported.  On return
 * d holds the eigenvalues and Z[c][j] = (V^T z_c)_j.  Adapted from the classical tql2. */
export function tqlProject(d, e, Z) {
  const n = d.length, EPS = 2 ** -52;
  for (let i = 1; i < n; i++) e[i - 1] = e[i];
  e[n - 1] = 0;
  let f = 0, tst1 = 0;
  for (let l = 0; l < n; l++) {
    tst1 = Math.max(tst1, Math.abs(d[l]) + Math.abs(e[l]));
    let m = l;
    while (m < n && Math.abs(e[m]) > EPS * tst1) m++;
    if (m > l) {
      let iter = 0;
      do {
        if (++iter > 60) throw new Error('tqlProject: no convergence');
        let g = d[l];
        let p = (d[l + 1] - g) / (2 * e[l]);
        let r = Math.hypot(p, 1);
        if (p < 0) r = -r;
        d[l] = e[l] / (p + r);
        d[l + 1] = e[l] * (p + r);
        const dl1 = d[l + 1];
        let h = g - d[l];
        for (let i = l + 2; i < n; i++) d[i] -= h;
        f += h;
        p = d[m];
        let c = 1, c2 = c, c3 = c, s = 0, s2 = 0;
        const el1 = e[l + 1];
        for (let i = m - 1; i >= l; i--) {
          c3 = c2; c2 = c; s2 = s;
          g = c * e[i];
          h = c * p;
          r = Math.hypot(p, e[i]);
          e[i + 1] = s * r;
          s = e[i] / r;
          c = p / r;
          p = c * d[i] - s * g;
          d[i + 1] = h + s * (c * g + s * d[i]);
          for (const z of Z) {
            const zi = z[i], zi1 = z[i + 1];
            z[i + 1] = s * zi + c * zi1;
            z[i] = c * zi - s * zi1;
          }
        }
        p = (-s * s2 * c3 * el1 * e[l]) / dl1;
        e[l] = s * p;
        d[l] = c * p;
      } while (Math.abs(e[l]) > EPS * tst1);
    }
    d[l] += f;
    e[l] = 0;
  }
  return d;
}

/* Spectral data {w, ab} with C(t) = sum_j exp(-i t w_j) ab_j.
 * N = null gives the continuum symbol. */
export function corrSpectral(Lam, k, N) {
  const { f, g, ll } = corrVectors(Lam), m = ll.length;
  const pf = new Float64Array(m);
  for (let i = 0; i < m; i++) pf[i] = ll[i] < 0 ? f[i] : 0;
  const sym = (x) => (N === null || N === undefined ? x : 2 ** N * Math.sin(2 ** -N * x));

  if (k === 0) {
    const w = new Float64Array(m), ab = new Float64Array(m);
    for (let i = 0; i < m; i++) { w[i] = 2 * sym(ll[i]); ab[i] = g[i] * pf[i]; }
    return { w, ab };
  }
  const W = new Float64Array(m), AB = new Float64Array(m);
  let put = 0;
  for (let res = 0; res < k; res++) {
    const idx = [];
    for (let i = res; i < m; i += k) idx.push(i);
    const nn = idx.length;
    const d = new Float64Array(nn), e = new Float64Array(nn);
    for (let j = 0; j < nn - 1; j++) e[j + 1] = sym(ll[idx[j]] + k / 2);
    const za = new Float64Array(nn), zb = new Float64Array(nn);
    for (let j = 0; j < nn; j++) { za[j] = g[idx[j]]; zb[j] = pf[idx[j]]; }
    tqlProject(d, e, [za, zb]);
    for (let j = 0; j < nn; j++) { W[put] = d[j]; AB[put] = za[j] * zb[j]; put++; }
  }
  return { w: W, ab: AB };
}

/* C(t) from spectral data; returns [Re, Im]. */
export function corrAt(spec, t) {
  const { w, ab } = spec;
  let re = 0, im = 0;
  for (let j = 0; j < w.length; j++) {
    const ph = -t * w[j];
    re += ab[j] * Math.cos(ph);
    im += ab[j] * Math.sin(ph);
  }
  return [re, im];
}
export const cabs = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1]);

/* |C^{(N)}(t) - C(t)|, the quantity of Fig. S7 (figure10.pdf). */
export function corrError(N, k, t, LamC, cache = {}) {
  const key = `c${k}:${LamC}`;
  if (!cache[key]) cache[key] = corrSpectral(LamC, k, null);
  const keyN = `l${k}:${N}`;
  if (!cache[keyN]) cache[keyN] = corrSpectral(2 ** N, k, N);
  return cabs(corrAt(cache[keyN], t), corrAt(cache[key], t));
}

/* Least-squares slope of log2(err) against N: the "per-step ratio" is 2^{-slope}. */
export function fitRatio(Ns, errs) {
  const y = errs.map((v) => Math.log2(v));
  const n = Ns.length;
  const mx = Ns.reduce((a, b) => a + b, 0) / n, my = y.reduce((a, b) => a + b, 0) / n;
  let sxy = 0, sxx = 0;
  for (let i = 0; i < n; i++) { sxy += (Ns[i] - mx) * (y[i] - my); sxx += (Ns[i] - mx) ** 2; }
  return 2 ** (-sxy / sxx);
}
