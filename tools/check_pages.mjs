/* check_pages.mjs — a smoke test for the widget pages, outside a browser.
 *
 *     node tools/check_pages.mjs
 *
 * There is no headless browser here and no framework, so this supplies the smallest DOM,
 * canvas and fetch stubs the pages actually use, extracts each page's module script, and
 * runs it.  It then drives every control through its whole range and redraws, which is
 * where widget bugs live: a divide by zero at the end of a slider, a label that assumes
 * M < N, an empty series on a logarithmic axis.
 *
 * It does not check that anything *looks* right — only that every page loads, every
 * control setting draws without throwing, and every page's own check badge passes.
 * tools/check_js.mjs is the numerical check; this is the "does it run" check.
 */
import { readFileSync, writeFileSync, mkdtempSync } from 'node:fs';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { dirname, join, relative } from 'node:path';
import { tmpdir } from 'node:os';
import { readdirSync } from 'node:fs';

const HERE = dirname(fileURLToPath(import.meta.url));
const DOCS = join(HERE, '..', 'docs');

/* ------------------------------------------------------------------ the stubs ----- */

const noop = () => {};
const ctx2d = new Proxy({}, {
  get(t, k) {
    if (k === 'measureText') return () => ({ width: 40 });
    if (k === 'createLinearGradient') return () => ({ addColorStop: noop });
    if (typeof t[k] === 'undefined') return noop;
    return t[k];
  },
  set(t, k, v) { t[k] = v; return true; },
});

class El {
  constructor(tag) {
    this.tagName = String(tag).toUpperCase();
    this.children = [];
    this.style = {};
    this.dataset = {};
    this._attrs = {};
    this.className = '';
    this.innerHTML = '';
    this.textContent = '';
    this.clientWidth = 760;
    this.clientHeight = 360;
    this._listeners = {};
  }
  appendChild(c) { this.children.push(c); return c; }
  setAttribute(k, v) { this._attrs[k] = v; }
  getAttribute(k) { return this._attrs[k] ?? null; }
  removeAttribute(k) { delete this._attrs[k]; }
  addEventListener(t, fn) { (this._listeners[t] ||= []).push(fn); }
  removeEventListener() {}
  dispatch(t) { for (const fn of this._listeners[t] ?? []) fn({ target: this }); }
  getContext() { return ctx2d; }
  querySelector() { return null; }
  get classList() { return { add: noop, remove: noop, contains: () => false }; }
}

function makeDocument(hosts) {
  const doc = {
    readyState: 'complete',
    documentElement: new El('html'),
    body: new El('body'),
    createElement: (t) => new El(t),
    addEventListener: noop,
    querySelector: (sel) => hosts[sel] ?? null,
    querySelectorAll: () => [],
  };
  return doc;
}

globalThis.performance ??= { now: () => Date.now() };
/* a bounded rAF: enough frames to exercise an animated widget, not an infinite loop */
let rafBudget = 0;
globalThis.requestAnimationFrame = (fn) => {
  if (rafBudget-- <= 0) return 0;
  setTimeout(() => fn(Date.now()), 0);
  return 1;
};
globalThis.cancelAnimationFrame = noop;
globalThis.matchMedia = () => ({ matches: false, addEventListener: noop, addListener: noop });
globalThis.localStorage = { getItem: () => null, setItem: noop, removeItem: noop };
globalThis.history = { replaceState: noop };
globalThis.location = { hash: '', pathname: '/x.html', search: '' };
globalThis.addEventListener = noop;
globalThis.removeEventListener = noop;
globalThis.dispatchEvent = noop;
globalThis.Event = class { constructor(t) { this.type = t; } };
globalThis.devicePixelRatio = 2;
globalThis.window = globalThis;
globalThis.renderMathInElement = undefined;   // the pages must survive KaTeX being absent

/* fetch, backed by the file system, relative to the page's directory */
let FETCH_BASE = DOCS;
globalThis.fetch = async (p) => {
  const path = join(FETCH_BASE, p);
  try {
    const text = readFileSync(path, 'utf8');
    return { ok: true, status: 200, json: async () => JSON.parse(text), text: async () => text };
  } catch (e) {
    return { ok: false, status: 404, json: async () => { throw e; } };
  }
};

/* ---------------------------------------------------------------- the driver ----- */

const tmp = mkdtempSync(join(tmpdir(), 'qscft-pages-'));
let failures = 0;
const log = (ok, msg) => { if (!ok) failures++; console.log(`${ok ? 'ok  ' : 'FAIL'}  ${msg}`); };

async function runPage(file) {
  const html = readFileSync(file, 'utf8');
  const m = html.match(/<script type="module">([\s\S]*?)<\/script>/);
  const name = relative(DOCS, file);
  if (!m) { log(true, `${name}: no module script`); return; }

  FETCH_BASE = dirname(file);
  const hosts = {};
  for (const sel of ['#w', '#checkhost', '#theme-toggle', '#year']) hosts[sel] = new El('div');
  globalThis.document = makeDocument(hosts);

  /* rewrite the relative imports so node resolves them from tools/ */
  const src = m[1].replace(/from '(\.\.\/|\.\/)assets\//g,
    `from '${pathToFileURL(join(DOCS, 'assets')).href}/`);
  const mod = join(tmp, name.replace(/[\/\\]/g, '_') + '.mjs');
  writeFileSync(mod, src);

  /* capture what mount() built, so the controls can be driven afterwards */
  let captured = null;
  const { mount } = await import(pathToFileURL(join(DOCS, 'assets', 'widget.js')).href);
  const origMount = mount;

  try {
    await import(pathToFileURL(mod).href + `?v=${Date.now()}`);
  } catch (e) {
    log(false, `${name}: module threw on load — ${e.message}`);
    return;
  }
  log(true, `${name}: loaded`);

  /* the readout is the last child of the #w host; a widget that threw says so there */
  const host = hosts['#w'];
  const readouts = host.children.filter((c) => c.className === 'readout');
  for (const r of readouts) {
    log(!/this widget failed/.test(r.innerHTML), `${name}: draw() did not throw`);
  }

  /* drive every range control across its range */
  const bar = host.children.find((c) => c.className === 'controls');
  if (bar) {
    for (const wrap of bar.children) {
      const input = wrap.children.find((c) => c.tagName === 'INPUT' || c.tagName === 'SELECT');
      if (!input) continue;
      const id = input.id || '?';
      if (input.type === 'range') {
        const lo = parseFloat(input.min), hi = parseFloat(input.max), st = parseFloat(input.step) || 1;
        let bad = 0;
        for (let v = lo; v <= hi + 1e-9; v += st) {
          input.value = String(v);
          input.dispatch('input');
          for (const r of readouts) if (/this widget failed/.test(r.innerHTML)) bad++;
        }
        log(bad === 0, `${name}: ${id} swept ${lo}…${hi}${bad ? ` — ${bad} failures` : ''}`);
        input.value = String(lo);
        input.dispatch('input');
      } else if (input.tagName === 'SELECT') {
        let bad = 0;
        for (const opt of input.children) {
          input.value = opt.value;
          input.dispatch('change');
          for (const r of readouts) if (/this widget failed/.test(r.innerHTML)) bad++;
        }
        log(bad === 0, `${name}: ${id} cycled${bad ? ` — ${bad} failures` : ''}`);
      }
    }
  }

  /* if the widget animates, press play and let a few frames run */
  const animrow = host.children.find((c) => c.className === 'animrow');
  if (animrow) {
    const btn = animrow.children.find((c) => c.tagName === 'BUTTON');
    if (btn) {
      rafBudget = 4;
      btn.dispatch('click');
      await new Promise((r) => setTimeout(r, 60));
      const failed = readouts.some((r) => /this widget failed/.test(r.innerHTML));
      log(!failed, `${name}: animation ran (${btn.textContent})`);
      btn.dispatch('click');              // back to paused
    }
  }

  /* Let the page's own check badge resolve.  Widget H computes for a second or two, so
   * poll rather than guess a delay. */
  let badge = null;
  const wantsBadge = /id="checkhost"/.test(html);
  for (let i = 0; wantsBadge && i < 300; i++) {
    badge = hosts['#checkhost'].children.find((c) => /badge/.test(c.className));
    if (badge && !/^checking/.test(badge.textContent || '')) break;
    await new Promise((r) => setTimeout(r, 100));
  }
  if (badge) {
    const text = badge.textContent || '';
    log(/^all \d+ checks agree/.test(text), `${name}: check badge — ${text}`);
  } else if (wantsBadge) {
    log(false, `${name}: the page has a #checkhost but no badge ever appeared`);
  }
  void origMount; void captured;
}

const pages = [];
for (const d of ['', 'widgets']) {
  const dir = join(DOCS, d);
  for (const f of readdirSync(dir)) if (f.endsWith('.html')) pages.push(join(dir, f));
}
for (const p of pages.sort()) await runPage(p);

console.log(failures ? `\n${failures} failure(s)` : '\nall page checks passed');
process.exit(failures ? 1 : 0);
