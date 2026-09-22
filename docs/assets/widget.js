/* widget.js — the shell every widget page uses: controls, deep links, the theme switch,
 * the self-check badge and the animation gate.
 *
 * A widget page declares its controls and a draw() function; this module builds the
 * controls, keeps them in the URL hash so a particular configuration is linkable, calls
 * draw() on every change, on resize and when the theme flips, and runs the page's check()
 * against docs/data/*.json, showing a pass/fail badge with the tolerance written out.
 *
 * Under prefers-reduced-motion an animated widget starts paused and says so; the button is
 * a real <button> and every control is a real <input>, so the whole page is keyboard
 * reachable with nothing but Tab and the arrow keys.
 */

export const $ = (s, r = document) => r.querySelector(s);
export const el = (t, cls, html) => {
  const e = document.createElement(t);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
};

/* Re-render the mathematics inside a node that JavaScript has just written.  KaTeX's
 * auto-render ran once at DOMContentLoaded; readouts are written after that. */
export function typeset(node) {
  if (!node) return;
  if (typeof renderMathInElement !== 'function') {
    /* same fallback as assets/math.js: drop the delimiters so the TeX source reads */
    node.innerHTML = node.innerHTML.replace(/\\\(|\\\)|\$\$/g, '');
    return;
  }
  try {
    renderMathInElement(node, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '\\(', right: '\\)', display: false },
      ],
      throwOnError: false,
      errorColor: '#cf222e',
    });
  } catch { /* a readout without maths is better than a readout that throws */ }
}

export const reduceMotion = () =>
  typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;

export async function loadJSON(path) {
  const r = await fetch(path);
  if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
  return r.json();
}

/* ------------------------------------------------------------------ the theme switch */

const THEME_KEY = 'qscft-theme';
export function initTheme() {
  let saved = null;
  try { saved = localStorage.getItem(THEME_KEY); } catch { /* private mode */ }
  if (saved === 'light' || saved === 'dark') document.documentElement.setAttribute('data-theme', saved);
  const btn = $('#theme-toggle');
  if (!btn) return;
  const label = () => {
    const cur = document.documentElement.getAttribute('data-theme');
    btn.textContent = cur === 'dark' ? 'dark' : cur === 'light' ? 'light' : 'auto';
    btn.setAttribute('aria-label', `colour theme: ${btn.textContent}; click to change`);
  };
  label();
  btn.addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme');
    const next = cur === 'light' ? 'dark' : cur === 'dark' ? null : 'light';
    if (next) document.documentElement.setAttribute('data-theme', next);
    else document.documentElement.removeAttribute('data-theme');
    try { next ? localStorage.setItem(THEME_KEY, next) : localStorage.removeItem(THEME_KEY); } catch { /* ignore */ }
    label();
    window.dispatchEvent(new Event('themechange'));
  });
}

/* ----------------------------------------------------------------------- the controls */

function readHash() {
  const out = {};
  for (const part of location.hash.replace(/^#/, '').split('&')) {
    if (!part) continue;
    const [k, v] = part.split('=');
    if (k) out[decodeURIComponent(k)] = decodeURIComponent(v ?? '');
  }
  return out;
}

function writeHash(state, controls) {
  const parts = controls
    .filter((c) => String(state[c.k]) !== String(c.value))
    .map((c) => `${encodeURIComponent(c.k)}=${encodeURIComponent(state[c.k])}`);
  const h = parts.join('&');
  const url = `${location.pathname}${location.search}${h ? `#${h}` : ''}`;
  history.replaceState(null, '', url);
}

/**
 * mount({ mount, controls, draw, animate?, check? })
 *   controls: [{k, label, type:'range'|'select'|'check', min,max,step,value, options:[[v,label]], fmt?}]
 *   draw(state, ui) -> HTML string for the readout (or a Promise of one)
 *   animate(state, tau, ui) -> optional; called with an animation clock when running
 *   check(state) -> optional; [{name, got, want, tol}] compared and badged
 */
export function mount(opts) {
  const host = typeof opts.mount === 'string' ? $(opts.mount) : opts.mount;
  const controls = opts.controls ?? [];
  const state = {};
  const inputs = {};

  const bar = el('div', 'controls');
  bar.setAttribute('role', 'group');
  bar.setAttribute('aria-label', 'widget controls');
  const hash = readHash();

  for (const c of controls) {
    const fromHash = hash[c.k];
    state[c.k] = fromHash !== undefined
      ? (c.type === 'select' ? fromHash : c.type === 'check' ? (fromHash === '1' ? 1 : 0) : parseFloat(fromHash))
      : c.value;
    if (Number.isNaN(state[c.k])) state[c.k] = c.value;

    const wrap = el('label', 'control');
    wrap.appendChild(el('span', 'clabel', c.label));
    let input, out = null;
    if (c.type === 'select') {
      input = el('select');
      for (const [v, t] of c.options) {
        const o = el('option', null, t);
        o.value = v;
        if (String(v) === String(state[c.k])) o.selected = true;
        input.appendChild(o);
      }
      input.addEventListener('change', () => { state[c.k] = input.value; changed(); });
    } else if (c.type === 'check') {
      input = el('input');
      input.type = 'checkbox';
      input.checked = !!state[c.k];
      input.addEventListener('change', () => { state[c.k] = input.checked ? 1 : 0; changed(); });
    } else {
      input = el('input');
      input.type = 'range';
      input.min = c.min; input.max = c.max; input.step = c.step; input.value = state[c.k];
      out = el('output', 'cvalue', c.fmt ? c.fmt(state[c.k]) : String(state[c.k]));
      input.addEventListener('input', () => {
        state[c.k] = parseFloat(input.value);
        out.textContent = c.fmt ? c.fmt(state[c.k]) : input.value;
        changed();
      });
    }
    input.id = `ctl-${c.k}`;
    wrap.htmlFor = input.id;
    wrap.appendChild(input);
    if (out) wrap.appendChild(out);
    inputs[c.k] = input;
    bar.appendChild(wrap);
  }
  if (controls.length) host.appendChild(bar);

  const figure = el('figure', 'figure');
  const canvas = el('canvas', 'plot');
  canvas.setAttribute('role', 'img');
  figure.appendChild(canvas);
  host.appendChild(figure);

  let playBtn = null, running = false, t0 = 0, raf = 0, tau = 0;
  if (opts.animate) {
    const row = el('div', 'animrow');
    playBtn = el('button', 'btn');
    playBtn.type = 'button';
    row.appendChild(playBtn);
    const note = el('span', 'animnote', reduceMotion()
      ? 'starts paused: your system asks for reduced motion'
      : 'the animation only redraws the same computation at successive times');
    row.appendChild(note);
    host.appendChild(row);
    const setLabel = () => { playBtn.textContent = running ? 'pause' : 'play'; };
    const tick = (now) => {
      if (!running) return;
      tau = (now - t0) / 1000;
      render();
      raf = requestAnimationFrame(tick);
    };
    playBtn.addEventListener('click', () => {
      running = !running;
      setLabel();
      if (running) { t0 = performance.now() - tau * 1000; raf = requestAnimationFrame(tick); }
      else cancelAnimationFrame(raf);
    });
    setLabel();
  }

  const readout = el('div', 'readout');
  readout.setAttribute('aria-live', 'polite');
  host.appendChild(readout);

  const ui = { canvas, state, get tau() { return tau; }, get running() { return running; } };

  function render() {
    try {
      const html = opts.animate && running ? opts.animate(state, tau, ui) : opts.draw(state, ui);
      const put = (h) => { readout.innerHTML = h ?? ''; typeset(readout); };
      if (html && typeof html.then === 'function') html.then(put);
      else put(html);
    } catch (e) {
      readout.innerHTML = `<p class="err">this widget failed: ${e.message}</p>`;
      if (typeof console !== 'undefined') console.error(e);
    }
  }
  function changed() { writeHash(state, controls); render(); }

  render();
  let rt;
  addEventListener('resize', () => { clearTimeout(rt); rt = setTimeout(render, 140); });
  addEventListener('themechange', render);
  if (typeof matchMedia === 'function') {
    const mq = matchMedia('(prefers-color-scheme: dark)');
    (mq.addEventListener ? mq.addEventListener.bind(mq, 'change') : mq.addListener.bind(mq))(render);
  }
  ui.render = render;
  return ui;
}

/* ------------------------------------------------------------------ the check badge */

/**
 * check(hostSel, rows, note)
 *   rows: [{name, got, want, tol, atol?}]
 * A row passes when |got − want| ≤ atol + tol·|want|.  The absolute floor `atol` matters
 * whenever the quantity compared is itself a difference of two nearly equal numbers — the
 * correlator error, for instance, is a difference of two numbers of order 0.1, so agreeing
 * to a few units in their last place is agreement to only about 1e-6 *of the difference*.
 * Quoting a relative tolerance alone there would be dishonest in one direction or vacuous
 * in the other, so both are shown.
 */
export function renderCheck(hostSel, rows, note) {
  const host = typeof hostSel === 'string' ? $(hostSel) : hostSel;
  host.innerHTML = '';
  let worst = 0, bad = 0;
  const scored = rows.map((r) => {
    const scale = r.want === 0 ? 1 : Math.abs(r.want);
    const absd = Math.abs(r.got - r.want);
    const rel = absd / scale;
    worst = Math.max(worst, rel);
    const ok = absd <= (r.atol ?? 0) + r.tol * scale;
    if (!ok) bad++;
    return { ...r, rel, ok };
  });
  const badge = el('p', `badge ${bad ? 'bad' : 'ok'}`);
  badge.textContent = bad
    ? `${bad} of ${rows.length} checks disagree (worst relative difference ${worst.toExponential(1)})`
    : `all ${rows.length} checks agree, worst relative difference ${worst.toExponential(1)}`;
  badge.setAttribute('role', 'status');
  host.appendChild(badge);
  if (note) host.appendChild(el('p', 'checknote', note));
  const tbl = el('table', 'check');
  tbl.innerHTML = '<caption class="visually-hidden">browser computation against the committed JSON</caption>'
    + '<thead><tr><th scope="col">quantity</th><th scope="col">in your browser</th>'
    + '<th scope="col">from make_data.py</th><th scope="col">relative</th>'
    + '<th scope="col">tolerance</th></tr></thead>';
  const tb = el('tbody');
  for (const r of scored) {
    const tr = el('tr', r.ok ? '' : 'bad');
    const p = (v) => (Number.isFinite(v) ? Number(v).toPrecision(10) : String(v));
    const tolTxt = r.atol
      ? `${r.tol.toExponential(0)} + ${r.atol.toExponential(0)} abs`
      : r.tol.toExponential(0);
    tr.innerHTML = `<td>${r.name}</td><td>${p(r.got)}</td><td>${p(r.want)}</td>`
      + `<td>${r.rel.toExponential(1)}</td><td>${tolTxt}</td>`;
    tb.appendChild(tr);
  }
  tbl.appendChild(tb);
  host.appendChild(tbl);
  return !bad;
}

/* Every page calls this once: theme switch, KaTeX, and the year in the footer. */
export function boot() {
  initTheme();
  const y = $('#year');
  if (y) y.textContent = String(new Date().getFullYear());
}
