/* plot.js — a small canvas plotter for the widgets: linear or log axes, lines, points,
 * stacked bars, rules, bands and notes.  Deliberately tiny and dependency-free; the page
 * loads no third-party script at all.  Labels are Unicode, not TeX, because canvas text
 * has no maths renderer.
 */

const THEMES = {
  light: {
    ink: '#1f2328', mute: '#57606a', grid: '#d8dee4', axis: '#8c959f', bg: '#ffffff',
    series: ['#0969da', '#cf222e', '#1a7f37', '#9a6700', '#8250df', '#57606a'],
  },
  dark: {
    ink: '#e6edf3', mute: '#9198a1', grid: '#30363d', axis: '#6e7681', bg: '#0d1117',
    series: ['#4493f8', '#ff7b72', '#3fb950', '#d29922', '#ab7df8', '#8b949e'],
  },
};

/** The page theme: the data-theme attribute wins, otherwise the OS preference. */
export function theme() {
  const forced = document.documentElement.getAttribute('data-theme');
  if (forced === 'light' || forced === 'dark') return THEMES[forced];
  const dark = typeof matchMedia === 'function' && matchMedia('(prefers-color-scheme: dark)').matches;
  return THEMES[dark ? 'dark' : 'light'];
}

const FONT = (px, it) =>
  `${it ? 'italic ' : ''}${px}px -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif`;

const niceTicks = (lo, hi, want = 6) => {
  if (!(hi > lo)) return [lo];
  const raw = (hi - lo) / want, mag = 10 ** Math.floor(Math.log10(raw));
  let step = 10 * mag;
  for (const m of [1, 2, 2.5, 5, 10]) if (raw <= m * mag) { step = m * mag; break; }
  const out = [];
  let v = Math.ceil(lo / step) * step;
  while (v <= hi + 1e-9 * step) { out.push(Math.round(v * 1e12) / 1e12); v += step; }
  return out;
};

export const fmt = (v) => {
  if (v === 0) return '0';
  const a = Math.abs(v);
  if (a >= 1e4 || a < 1e-3) {
    const e = Math.floor(Math.log10(a)), m = v / 10 ** e;
    return Math.abs(m - Math.round(m)) < 1e-9 ? `10${sup(e)}` : `${Math.round(m * 100) / 100}e${e}`;
  }
  return String(Math.round(v * 1e6) / 1e6);
};

const SUPS = { '-': '⁻', 0: '⁰', 1: '¹', 2: '²', 3: '³', 4: '⁴',
  5: '⁵', 6: '⁶', 7: '⁷', 8: '⁸', 9: '⁹' };
export const sup = (n) => String(n).split('').map((c) => SUPS[c] ?? c).join('');

const logTicks = (lo, hi, base) => {
  const out = [];
  let e = Math.floor(Math.log(lo) / Math.log(base));
  while (base ** e <= hi * 1.0000001) {
    if (base ** e >= lo * 0.9999999) out.push(base ** e);
    e++;
  }
  return out.length ? out : [lo, hi];
};

/**
 * spec: {
 *   series: [{x, y, label?, color?, dash?, width?, points?, size?, marker?}],
 *   bars:   [{x, y0, y1, color?, label?, width?, hatch?}],
 *   bands:  [{x0, x1, color?, opacity?}],
 *   hlines / vlines: [{y|x, color?, dash?, width?}],
 *   notes:  [{x, y, text, dx?, dy?, anchor?, color?, italic?}],
 *   xlim, ylim, xlog, ylog, xlabel, ylabel, legend: 'tl'|'tr'|'bl'|'br', ml
 * }
 */
export function plot(canvas, spec) {
  const T = theme(), dpr = window.devicePixelRatio || 1;
  const W = canvas.clientWidth || 640, H = canvas.clientHeight || 320;
  canvas.width = Math.round(W * dpr);
  canvas.height = Math.round(H * dpr);
  const g = canvas.getContext('2d');
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, W, H);
  g.font = FONT(12);

  const narrow = W < 460;
  const ml = spec.ml ?? (narrow ? 50 : 62), mr = spec.mr ?? 16;
  const mt = spec.mt ?? 14, mb = (spec.xlabel ? 42 : 26);
  const L = ml, R = W - mr, Tp = mt, B = H - mb;

  const S = (spec.series ?? []).filter((s) => s.x && s.x.length);
  const bars = spec.bars ?? [];
  const finite = Number.isFinite;
  let xs = [], ys = [];
  for (const s of S) { xs = xs.concat(Array.from(s.x)); ys = ys.concat(Array.from(s.y)); }
  for (const b of bars) { xs.push(b.x); ys.push(b.y0, b.y1); }
  xs = xs.filter(finite); ys = ys.filter(finite);
  if (spec.ylog) ys = ys.filter((v) => v > 0);
  if (spec.xlog) xs = xs.filter((v) => v > 0);
  if (!xs.length) { xs = [0, 1]; } if (!ys.length) { ys = [0, 1]; }

  let [x0, x1] = spec.xlim ?? [Math.min(...xs), Math.max(...xs)];
  let [y0, y1] = spec.ylim ?? [Math.min(...ys), Math.max(...ys)];
  if (!spec.xlim) { const p = spec.xlog ? 0 : 0.04 * (x1 - x0 || 1); x0 -= p; x1 += p; }
  if (!spec.ylim) {
    if (spec.ylog) { y0 /= 2.2; y1 *= 2.2; }
    else { const p = 0.09 * (y1 - y0 || Math.abs(y0) || 1); y0 -= p; y1 += p; }
  }
  const px = (v) => (spec.xlog
    ? L + ((Math.log(v) - Math.log(x0)) / (Math.log(x1) - Math.log(x0))) * (R - L)
    : L + ((v - x0) / (x1 - x0)) * (R - L));
  const py = (v) => (spec.ylog
    ? B - ((Math.log(v) - Math.log(y0)) / (Math.log(y1) - Math.log(y0))) * (B - Tp)
    : B - ((v - y0) / (y1 - y0)) * (B - Tp));

  const want = narrow ? 4 : 6;
  const xt = spec.xticks ?? (spec.xlog
    ? logTicks(Math.min(x0, x1), Math.max(x0, x1), spec.xlog)
      .map((v) => ({ v, label: `${spec.xlog}${sup(Math.round(Math.log(v) / Math.log(spec.xlog)))}` }))
    : niceTicks(x0, x1, want).map((v) => ({ v, label: fmt(v) })));
  const yt = spec.yticks ?? (spec.ylog
    ? logTicks(y0, y1, spec.ylog)
      .map((v) => ({ v, label: `${spec.ylog}${sup(Math.round(Math.log(v) / Math.log(spec.ylog)))}` }))
    : niceTicks(y0, y1, want).map((v) => ({ v, label: fmt(v) })));

  g.strokeStyle = T.grid; g.lineWidth = 1; g.fillStyle = T.mute; g.textBaseline = 'middle';
  for (const t of xt) {
    const X = px(t.v); if (X < L - 1 || X > R + 1) continue;
    g.beginPath(); g.moveTo(X, Tp); g.lineTo(X, B); g.stroke();
    g.textAlign = 'center'; g.fillText(t.label, X, B + 14);
  }
  for (const t of yt) {
    const Y = py(t.v); if (Y < Tp - 1 || Y > B + 1) continue;
    g.beginPath(); g.moveTo(L, Y); g.lineTo(R, Y); g.stroke();
    g.textAlign = 'right'; g.fillText(t.label, L - 7, Y);
  }
  g.strokeStyle = T.axis; g.lineWidth = 1.2; g.strokeRect(L, Tp, R - L, B - Tp);

  g.save(); g.beginPath(); g.rect(L, Tp, R - L, B - Tp); g.clip();

  for (const b of spec.bands ?? []) {
    g.fillStyle = b.color ?? T.series[0];
    g.globalAlpha = b.opacity ?? 0.10;
    const a = px(b.x0), c = px(b.x1);
    g.fillRect(Math.min(a, c), Tp, Math.abs(c - a), B - Tp);
    g.globalAlpha = 1;
  }
  for (const r of spec.hlines ?? []) {
    g.strokeStyle = r.color ?? T.mute; g.lineWidth = r.width ?? 1.2;
    g.setLineDash(r.dash ?? [4, 3]);
    const Y = py(r.y); g.beginPath(); g.moveTo(L, Y); g.lineTo(R, Y); g.stroke(); g.setLineDash([]);
  }
  for (const r of spec.vlines ?? []) {
    g.strokeStyle = r.color ?? T.mute; g.lineWidth = r.width ?? 1.2;
    g.setLineDash(r.dash ?? [4, 3]);
    const X = px(r.x); g.beginPath(); g.moveTo(X, Tp); g.lineTo(X, B); g.stroke(); g.setLineDash([]);
  }

  /* stacked bars: each entry is one segment from y0 to y1 at x */
  for (const b of bars) {
    const col = typeof b.color === 'number' ? T.series[b.color % T.series.length] : (b.color ?? T.series[0]);
    const half = (b.width ?? 0.34);
    const xa = px(b.x - half), xb = px(b.x + half);
    const ya = py(b.y1), yb = py(b.y0);
    g.fillStyle = col; g.globalAlpha = b.hatch ? 0.20 : 0.78;
    g.fillRect(Math.min(xa, xb), Math.min(ya, yb), Math.abs(xb - xa), Math.abs(yb - ya));
    g.globalAlpha = 1;
    if (b.hatch) {
      g.save();
      g.beginPath(); g.rect(Math.min(xa, xb), Math.min(ya, yb), Math.abs(xb - xa), Math.abs(yb - ya)); g.clip();
      g.strokeStyle = col; g.lineWidth = 1.1; g.globalAlpha = 0.85;
      for (let u = Math.min(xa, xb) - (B - Tp); u < Math.max(xa, xb); u += 7) {
        g.beginPath(); g.moveTo(u, Math.max(ya, yb)); g.lineTo(u + (B - Tp), Math.min(ya, yb)); g.stroke();
      }
      g.restore(); g.globalAlpha = 1;
    }
    g.strokeStyle = col; g.lineWidth = 1.2;
    g.strokeRect(Math.min(xa, xb), Math.min(ya, yb), Math.abs(xb - xa), Math.abs(yb - ya));
  }

  const marker = (X, Y, kind, size, col) => {
    g.fillStyle = col; g.strokeStyle = col; g.lineWidth = 1.4;
    if (kind === 'star') {
      g.beginPath();
      for (let i = 0; i < 10; i++) {
        const rr = i % 2 ? size * 0.45 : size, a = -Math.PI / 2 + (i * Math.PI) / 5;
        const fx = X + rr * Math.cos(a), fy = Y + rr * Math.sin(a);
        i ? g.lineTo(fx, fy) : g.moveTo(fx, fy);
      }
      g.closePath(); g.fill();
    } else if (kind === 'square') {
      g.fillRect(X - size * 0.8, Y - size * 0.8, size * 1.6, size * 1.6);
    } else if (kind === 'open') {
      g.fillStyle = T.bg;
      g.beginPath(); g.arc(X, Y, size, 0, 2 * Math.PI); g.fill(); g.stroke();
    } else {
      g.beginPath(); g.arc(X, Y, size, 0, 2 * Math.PI); g.fill();
    }
  };

  S.forEach((s, i) => {
    const col = typeof s.color === 'number' ? T.series[s.color % T.series.length]
      : (s.color ?? T.series[i % T.series.length]);
    if (s.points) {
      for (let j = 0; j < s.x.length; j++) {
        const X = px(s.x[j]), Y = py(s.y[j]);
        if (!finite(X) || !finite(Y)) continue;
        marker(X, Y, s.marker ?? 'dot', s.size ?? 3.6, col);
      }
    } else {
      g.strokeStyle = col; g.lineWidth = s.width ?? 2; g.setLineDash(s.dash ?? []);
      g.beginPath();
      let pen = false;
      for (let j = 0; j < s.x.length; j++) {
        const X = px(s.x[j]), Y = py(s.y[j]);
        if (!finite(X) || !finite(Y) || (spec.ylog && s.y[j] <= 0)) { pen = false; continue; }
        if (!pen) { g.moveTo(X, Y); pen = true; } else g.lineTo(X, Y);
      }
      g.stroke(); g.setLineDash([]);
      if (s.marker) for (let j = 0; j < s.x.length; j++) {
        const X = px(s.x[j]), Y = py(s.y[j]);
        if (finite(X) && finite(Y)) marker(X, Y, s.marker, s.size ?? 3.4, col);
      }
    }
  });

  for (const n of spec.notes ?? []) {
    g.fillStyle = n.color ?? T.ink;
    g.textAlign = n.anchor ?? 'center';
    g.font = FONT(n.size ?? 12, n.italic);
    g.fillText(n.text, px(n.x) + (n.dx ?? 0), py(n.y) + (n.dy ?? 0));
  }
  g.restore();

  g.font = FONT(12); g.fillStyle = T.ink; g.textAlign = 'center';
  if (spec.xlabel) g.fillText(spec.xlabel, (L + R) / 2, H - 9);
  if (spec.ylabel) {
    g.save(); g.translate(13, (Tp + B) / 2); g.rotate(-Math.PI / 2);
    g.fillText(spec.ylabel, 0, 0); g.restore();
  }

  const leg = [...S.filter((s) => s.label), ...bars.filter((b) => b.label)];
  if (leg.length && spec.legend !== false) {
    const wpx = Math.max(...leg.map((s) => s.label.length)) * 6.5 + 32;
    const hpx = 17 * leg.length + 9;
    const loc = spec.legend ?? 'tr';
    const bx = loc.endsWith('r') ? R - 10 - wpx : L + 10;
    const by = loc.startsWith('b') ? B - 10 - hpx : Tp + 10;
    g.fillStyle = T.bg; g.globalAlpha = 0.88; g.fillRect(bx, by, wpx, hpx); g.globalAlpha = 1;
    g.strokeStyle = T.grid; g.lineWidth = 1; g.strokeRect(bx, by, wpx, hpx);
    leg.forEach((s, i) => {
      const Y = by + 13 + 17 * i;
      const idx = S.indexOf(s);
      const col = typeof s.color === 'number' ? T.series[s.color % T.series.length]
        : (s.color ?? T.series[(idx < 0 ? i : idx) % T.series.length]);
      g.strokeStyle = col; g.lineWidth = 2.6; g.setLineDash(s.dash ?? []);
      g.beginPath(); g.moveTo(bx + 7, Y - 4); g.lineTo(bx + 24, Y - 4); g.stroke(); g.setLineDash([]);
      g.fillStyle = T.ink; g.textAlign = 'left'; g.font = FONT(12);
      g.fillText(s.label, bx + 29, Y - 4);
    });
  }
}

/* A schematic drawing surface for the widgets that draw a register or a lattice rather
 * than a graph: same theme handling, plain pixel coordinates. */
export function scene(canvas, draw) {
  const T = theme(), dpr = window.devicePixelRatio || 1;
  const W = canvas.clientWidth || 640, H = canvas.clientHeight || 320;
  canvas.width = Math.round(W * dpr);
  canvas.height = Math.round(H * dpr);
  const g = canvas.getContext('2d');
  g.setTransform(dpr, 0, 0, dpr, 0, 0);
  g.clearRect(0, 0, W, H);
  g.font = FONT(12);
  return draw(g, W, H, T, FONT);
}
