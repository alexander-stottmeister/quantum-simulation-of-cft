/* check_js.mjs — run the browser's own kernels outside a browser and compare them against
 * the JSON that tools/make_data.py wrote.  This is the same comparison each widget page
 * shows as a badge; here it exits non-zero instead, so it can go in CI.
 *
 *     node tools/check_js.mjs
 *
 * docs/assets/cft.js touches no DOM, which is what makes this possible: the file the
 * browser loads is the file node loads.
 */
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import * as C from '../docs/assets/cft.js';

const HERE = dirname(fileURLToPath(import.meta.url));
const DATA = join(HERE, '..', 'docs', 'data');
const load = (n) => JSON.parse(readFileSync(join(DATA, n), 'utf8'));

const rows = [];
const add = (name, got, want, tol, atol = 0) => rows.push({ name, got, want, tol, atol });

/* ---------------------------------------------------- widgets A, E: the error budget */
{
  const B = load('budget.json');
  for (const M of Object.keys(B.Theta_M)) add(`Θ_M, M = ${M}`, C.thetaM(+M), B.Theta_M[M], 1e-12);
  for (const r of Object.keys(B.eta)) {
    add(`η full, r = ${r}`, C.etaFull(+r), B.eta[r].full, 1e-12);
    add(`η chiral, r = ${r}`, C.etaChiral(+r), B.eta[r].chiral, 1e-12);
  }
  for (const p of B.theorem_s1_i) {
    const g = C.budgetK0({ N: p.N, M: p.M, dA: p.dA, dB: p.dB, T: p.T, chiral: p.algebra === 'chiral' });
    const tag = `N=${p.N} M=${p.M} ${p.algebra} T=${p.T}`;
    add(`Thm S1(i) term I  (${tag})`, g.I, p.I, 1e-12);
    add(`Thm S1(i) term II (${tag})`, g.II, p.II, 1e-12);
    add(`Thm S1(i) total   (${tag})`, g.total, p.total, 1e-12);
  }
  for (const L of B.horizon_Lambda) {
    add(`Λ_k(T), c_k=${L.c_k}, T=${L.T}`, C.horizon(L.c_k, L.T), L.Lambda, 1e-12);
  }
}

/* ----------------------------------------------------- widgets F, G: resource scaling */
{
  const R = load('resources.json');
  add('sites prefactor n₀√δ₀', C.SITES_PREFACTOR, R.sites_prefactor, 1e-12);
  add('calibration δ₀', C.DELTA0, R.delta0, 0);
  add('calibration n₀', C.N_SITES0, R.n0, 0);
  for (let i = 0; i < R.delta.length; i += 5) {
    const d = R.delta[i];
    add(`sites_rel at δ=${d.toPrecision(3)}`, C.sitesOfDelta(d) / C.N_SITES0, R.sites_rel[i], 1e-12);
    add(`sites_abs at δ=${d.toPrecision(3)}`, C.sitesOfDelta(d), R.sites_abs[i], 1e-12);
    add(`gates_rel at δ=${d.toPrecision(3)}`, C.gatesRel(d, 1), R.gates_rel[i], 1e-12);
    add(`wavelet sites at δ=${d.toPrecision(3)}`, C.sitesOfDeltaWavelet(d) / C.N_SITES0, R.wavelet_sites_rel[i], 1e-12);
    add(`wavelet gates at δ=${d.toPrecision(3)}`, C.gatesRelWavelet(d, 1), R.wavelet_gates_rel[i], 1e-12);
  }
  for (const row of R.dyadic) {
    add(`δ certified at N=${row.N}`, C.deltaOfN(row.N), row.delta, 1e-12);
    add(`sites at N=${row.N}`, C.sites(row.N), row.sites, 0);
    add(`qubits at N=${row.N}`, C.qubits(row.N), row.qubits, 0);
  }
  const NT = R.nearterm;
  add('near-term sites', C.sites(NT.N), NT.sites, 0);
  add('near-term qubits', C.qubits(NT.N), NT.qubits, 0);
  add('near-term depth r', NT.N - NT.M, NT.r, 0);
  for (const L of NT.localization) {
    add(`2^M at M=${L.M}`, 2 ** L.M, L.lhs, 0);
    add(`2K−1 at K=${L.K}`, 2 * L.K - 1, L.rhs, 0);
  }
}

/* ---------------------------------------------------- widgets B, D: circuit counting */
{
  const K = load('circuit.json');
  for (const row of K.rows) {
    const c = C.circuit(row.N);
    add(`sites at N=${row.N}`, c.n, row.sites, 0);
    add(`qubits at N=${row.N}`, c.q, row.qubits, 0);
    add(`butterflies at N=${row.N}`, c.butterflies, row.butterflies, 0);
    add(`Bogoliubov at N=${row.N}`, c.bogoliubov, row.bogoliubov, 0);
    add(`two-qubit gates at N=${row.N}`, c.twoQubitGates, row.two_qubit_gates, 0);
    add(`depth bound at N=${row.N}`, c.ftDepthBound, row.ft_depth_bound, 0);
  }
}

/* ------------------------------------------------ widget C: the Koo-Saleur symbol */
{
  const S = load('symbol.json');
  for (const row of S.rows) {
    for (let i = 0; i < row.x.length; i++) {
      add(`symbol N=${row.N} x=${row.x[i]}`, C.ksLattice(row.x[i], row.N), row.lattice[i], 1e-12);
      add(`deviation N=${row.N} k=${row.k} x=${row.x[i]}`, C.ksDeviation(row.x[i], row.N), row.deviation[i], 1e-9);
      add(`leading N=${row.N} x=${row.x[i]}`, C.ksLeading(row.x[i], row.N), row.leading[i], 1e-12);
    }
  }
}

/* --------------------------------------------- widget H: correlator convergence */
{
  const D = load('correlator.json');
  const LAMC = D.Lam_continuum;
  for (const k of [0, 1, 2]) {
    const cont = C.corrSpectral(LAMC, k, null);
    const pa = D.panel_a[String(k)];
    const errs = pa.N.map((N) => C.cabs(C.corrAt(C.corrSpectral(2 ** N, k, N), D.t_panel_a), C.corrAt(cont, D.t_panel_a)));
    pa.N.forEach((N, i) => add(`|C⁽ᴺ⁾−C| k=${k} N=${N} t=${D.t_panel_a}`, errs[i], pa.err[i], 1e-5, 1e-12));
    add(`fit ratio (all) k=${k}`, C.fitRatio(pa.N, errs), pa.fit_ratio_all, 1e-6);
    add(`fit ratio (tail) k=${k}`, C.fitRatio(pa.N.slice(2), errs.slice(2)), pa.fit_ratio_tail, 1e-6);
    const pb = D.panel_b[String(k)];
    const lb = C.corrSpectral(2 ** D.N_panel_b, k, D.N_panel_b);
    for (let j = 0; j < pb.t.length; j += 8) {
      add(`|C⁽ᴺ⁾−C| k=${k} N=${D.N_panel_b} t=${pb.t[j]}`,
        C.cabs(C.corrAt(lb, pb.t[j]), C.corrAt(cont, pb.t[j])), pb.err[j], 1e-5, 1e-12);
    }
  }
}

/* ------------------------------------------------------------------------ report */
let worst = 0, bad = 0;
for (const r of rows) {
  const scale = r.want === 0 ? 1 : Math.abs(r.want);
  const absd = Math.abs(r.got - r.want);
  r.rel = absd / scale;
  worst = Math.max(worst, r.rel);
  r.ok = absd <= r.atol + r.tol * scale;
  if (!r.ok) bad++;
}
for (const r of rows) {
  if (!r.ok) console.log(`FAIL  ${r.name}\n      browser ${r.got}\n      numpy   ${r.want}\n      rel ${r.rel.toExponential(2)} > tol ${r.tol}`);
}
console.log(`${rows.length - bad}/${rows.length} checks agree; worst relative difference ${worst.toExponential(2)}`);
console.log('(the correlator rows carry an absolute floor of 1e-12: they compare a difference of two numbers of order 0.1)');
process.exit(bad ? 1 : 0);
