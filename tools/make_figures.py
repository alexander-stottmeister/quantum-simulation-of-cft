#!/usr/bin/env python3
"""Write the static SVG fallbacks that the widget pages show inside <noscript>.

    python3 tools/make_figures.py        # writes docs/figures/*.svg

matplotlib is not installed and is not wanted: each figure is an SVG document written
directly, with an internal stylesheet that flips its colours under
``prefers-color-scheme: dark``.  One file serves both themes, so the pages need no
``<picture>`` element and no second request.

The data come from ``docs/data/*.json``, so a figure can never drift away from what the
interactive widget checks itself against: regenerate the data first, then the figures.
"""
import json
import math
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "docs", "data")
OUT = os.path.join(HERE, "docs", "figures")

W, H = 820, 420
ML, MR, MT, MB = 76, 22, 24, 56

STYLE = """
  .bg   { fill: #ffffff; }
  .grid { stroke: #d8dee4; stroke-width: 1; fill: none; }
  .axis { stroke: #8c959f; stroke-width: 1.2; fill: none; }
  .tick, .lab { fill: #57606a; font: 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
  .ttl  { fill: #1f2328; font: 600 13px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
  .note { fill: #1f2328; font: 12px -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; }
  .s0 { stroke: #0969da; } .s1 { stroke: #cf222e; } .s2 { stroke: #1a7f37; }
  .s3 { stroke: #9a6700; } .s4 { stroke: #8250df; } .s5 { stroke: #57606a; }
  .f0 { fill: #0969da; } .f1 { fill: #cf222e; } .f2 { fill: #1a7f37; }
  .f3 { fill: #9a6700; } .f4 { fill: #8250df; } .f5 { fill: #57606a; }
  .ln { fill: none; stroke-width: 2.1; stroke-linejoin: round; stroke-linecap: round; }
  .mk { stroke-width: 1.4; }
@media (prefers-color-scheme: dark) {
  .bg   { fill: #0d1117; }
  .grid { stroke: #30363d; }
  .axis { stroke: #6e7681; }
  .tick, .lab { fill: #9198a1; }
  .ttl, .note { fill: #e6edf3; }
  .s0 { stroke: #4493f8; } .s1 { stroke: #ff7b72; } .s2 { stroke: #3fb950; }
  .s3 { stroke: #d29922; } .s4 { stroke: #ab7df8; } .s5 { stroke: #8b949e; }
  .f0 { fill: #4493f8; } .f1 { fill: #ff7b72; } .f2 { fill: #3fb950; }
  .f3 { fill: #d29922; } .f4 { fill: #ab7df8; } .f5 { fill: #8b949e; }
}
"""

SUP = str.maketrans("-0123456789", "⁻⁰¹²³⁴⁵⁶⁷⁸⁹")


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


class Fig:
    """A very small SVG axis: linear or base-b logarithmic, lines, markers, legend."""

    def __init__(self, title, xlabel, ylabel, xlim, ylim, xlog=None, ylog=None,
                 width=W, height=H, ml=ML, panel=None):
        self.w, self.h, self.ml = width, height, ml
        self.title, self.xlabel, self.ylabel = title, xlabel, ylabel
        self.x0, self.x1 = xlim
        self.y0, self.y1 = ylim
        self.xlog, self.ylog = xlog, ylog
        self.body, self.legend = [], []
        self.panel = panel or (ml, width - MR, MT, height - MB)

    # -- coordinate maps -------------------------------------------------------------
    def px(self, v):
        L, R, _, _ = self.panel
        if self.xlog:
            return L + (math.log(v) - math.log(self.x0)) / (math.log(self.x1) - math.log(self.x0)) * (R - L)
        return L + (v - self.x0) / (self.x1 - self.x0) * (R - L)

    def py(self, v):
        _, _, T, B = self.panel
        if self.ylog:
            return B - (math.log(v) - math.log(self.y0)) / (math.log(self.y1) - math.log(self.y0)) * (B - T)
        return B - (v - self.y0) / (self.y1 - self.y0) * (B - T)

    # -- content ---------------------------------------------------------------------
    def line(self, xs, ys, c=0, dash=None, label=None, width=2.1):
        pts = " ".join(f"{self.px(x):.1f},{self.py(y):.1f}" for x, y in zip(xs, ys)
                       if (not self.ylog or y > 0) and (not self.xlog or x > 0))
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.body.append(f'<polyline class="ln s{c}" points="{pts}" stroke-width="{width}"{d}/>')
        if label:
            self.legend.append((c, label, dash))

    def marks(self, xs, ys, c=0, r=3.4, open_=True):
        for x, y in zip(xs, ys):
            if self.ylog and y <= 0:
                continue
            fill = ' class="bg mk"' if open_ else f' class="f{c}"'
            extra = f' stroke="currentColor"' if False else ""
            if open_:
                self.body.append(
                    f'<circle cx="{self.px(x):.1f}" cy="{self.py(y):.1f}" r="{r}" '
                    f'class="bg mk s{c}" stroke-width="1.5"/>')
            else:
                self.body.append(
                    f'<circle cx="{self.px(x):.1f}" cy="{self.py(y):.1f}" r="{r}" class="f{c}"/>')

    def star(self, x, y, r=8):
        pts = []
        for i in range(10):
            rr = r if i % 2 == 0 else r * 0.45
            a = -math.pi / 2 + i * math.pi / 5
            pts.append(f"{self.px(x) + rr * math.cos(a):.1f},{self.py(y) + rr * math.sin(a):.1f}")
        self.body.append(f'<polygon class="note" points="{" ".join(pts)}"/>')

    def hline(self, y, c=5, dash="6 4"):
        L, R, _, _ = self.panel
        self.body.append(f'<line class="ln s{c}" x1="{L}" y1="{self.py(y):.1f}" x2="{R}" '
                         f'y2="{self.py(y):.1f}" stroke-width="1.4" stroke-dasharray="{dash}"/>')

    def text(self, x, y, s, anchor="middle", cls="note", dx=0, dy=0, size=12):
        self.body.append(f'<text class="{cls}" x="{self.px(x) + dx:.1f}" y="{self.py(y) + dy:.1f}" '
                         f'text-anchor="{anchor}" font-size="{size}">{esc(s)}</text>')

    # -- frame -----------------------------------------------------------------------
    def _ticks(self, lo, hi, log, want=6):
        if log:
            out, e = [], math.floor(math.log(min(lo, hi)) / math.log(log))
            while log ** e <= max(lo, hi) * 1.0000001:
                if log ** e >= min(lo, hi) * 0.9999999:
                    out.append((log ** e, f"{log}{str(e).translate(SUP)}"))
                e += 1
            return out
        raw = (hi - lo) / want
        mag = 10 ** math.floor(math.log10(abs(raw))) if raw else 1
        step = next((m * mag for m in (1, 2, 2.5, 5, 10) if raw <= m * mag), 10 * mag)
        out, v = [], math.ceil(lo / step) * step
        while v <= hi + 1e-9 * step:
            r = round(v, 10)
            out.append((r, f"{r:g}"))
            v += step
        return out

    def frame(self, xticks=None):
        L, R, T, B = self.panel
        g = [f'<rect class="bg" x="0" y="0" width="{self.w}" height="{self.h}"/>']
        for v, lab in (xticks or self._ticks(min(self.x0, self.x1), max(self.x0, self.x1), self.xlog)):
            X = self.px(v)
            if X < L - 1 or X > R + 1:
                continue
            g.append(f'<line class="grid" x1="{X:.1f}" y1="{T}" x2="{X:.1f}" y2="{B}"/>')
            g.append(f'<text class="tick" x="{X:.1f}" y="{B + 17}" text-anchor="middle">{esc(lab)}</text>')
        for v, lab in self._ticks(self.y0, self.y1, self.ylog):
            Y = self.py(v)
            if Y < T - 1 or Y > B + 1:
                continue
            g.append(f'<line class="grid" x1="{L}" y1="{Y:.1f}" x2="{R}" y2="{Y:.1f}"/>')
            g.append(f'<text class="tick" x="{L - 8}" y="{Y + 4:.1f}" text-anchor="end">{esc(lab)}</text>')
        g.append(f'<rect class="axis" x="{L}" y="{T}" width="{R - L}" height="{B - T}"/>')
        return g

    def render(self, legend_at="tr"):
        L, R, T, B = self.panel
        parts = self.frame() + self.body
        if self.title:
            parts.append(f'<text class="ttl" x="{L}" y="{T - 8}">{esc(self.title)}</text>')
        if self.xlabel:
            parts.append(f'<text class="lab" x="{(L + R) / 2:.0f}" y="{self.h - 14}" '
                         f'text-anchor="middle">{esc(self.xlabel)}</text>')
        if self.ylabel:
            parts.append(f'<text class="lab" transform="translate({L - 52},{(T + B) / 2:.0f}) rotate(-90)" '
                         f'text-anchor="middle">{esc(self.ylabel)}</text>')
        if self.legend:
            bw = max(len(t) for _, t, _ in self.legend) * 7.3 + 44
            bh = 18 * len(self.legend) + 10
            bx = R - 12 - bw if legend_at.endswith("r") else L + 12
            by = B - 12 - bh if legend_at.startswith("b") else T + 12
            parts.append(f'<rect class="bg" x="{bx:.0f}" y="{by:.0f}" width="{bw:.0f}" '
                         f'height="{bh:.0f}" opacity="0.9"/>')
            parts.append(f'<rect class="grid" x="{bx:.0f}" y="{by:.0f}" width="{bw:.0f}" '
                         f'height="{bh:.0f}" fill="none"/>')
            for i, (c, t, dash) in enumerate(self.legend):
                y = by + 16 + 18 * i
                d = f' stroke-dasharray="{dash}"' if dash else ""
                parts.append(f'<line class="ln s{c}" x1="{bx + 8:.0f}" y1="{y - 4:.0f}" '
                             f'x2="{bx + 28:.0f}" y2="{y - 4:.0f}" stroke-width="2.4"{d}/>')
                parts.append(f'<text class="note" x="{bx + 34:.0f}" y="{y:.0f}">{esc(t)}</text>')
        return parts


def write(name, parts, title, desc, width=W, height=H):
    os.makedirs(OUT, exist_ok=True)
    doc = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'width="{width}" height="{height}" role="img" aria-labelledby="t d">\n'
           f'<title id="t">{esc(title)}</title>\n<desc id="d">{esc(desc)}</desc>\n'
           f'<style>{STYLE}</style>\n' + "\n".join(parts) + "\n</svg>\n")
    path = os.path.join(OUT, name)
    with open(path, "w") as fh:
        fh.write(doc)
    print(f"wrote docs/figures/{name}  ({len(doc)} bytes)")


# ------------------------------------------------------------------ the four figures

def fig_error_budget():
    B = json.load(open(os.path.join(DATA, "budget.json")))
    M, T, d = 3, 1.0, 1
    theta = B["Theta_M"][str(M)]
    Ns = list(range(M + 1, 19))
    Ic = [(2 * d) * (math.pi ** 2 / 16) * 4.0 ** -(N - M) for N in Ns]
    If = [(2 * d) * (math.pi / 4) * 2.0 ** -(N - M) for N in Ns]
    II = [(1 / 6) * d * theta * T * 4.0 ** -N for N in Ns]
    lo = min(min(Ic), min(II)) / 3
    hi = max(max(If), max(II)) * 3
    f = Fig("Theorem S1(i), the established k = 0 budget:  M = 3, T = 1, d_A = d_B = 1",
            "ultraviolet scale N     (depth r = N − M)", "bound on |C⁽ᴺ⁾ − C|",
            (M + 0.7, 18.3), (lo, hi), ylog=10)
    f.line(Ns, If, 4, dash="2 3", label="term I, full algebra  ∝ 2⁻ʳ")
    f.line(Ns, Ic, 0, label="term I, chiral  ∝ 4⁻ʳ")
    f.marks(Ns, Ic, 0, 3)
    f.line(Ns, II, 1, label="term II, dynamics  ∝ Θ_M T 4⁻ᴺ")
    f.marks(Ns, II, 1, 3)
    write("error-budget.svg", f.render("tr"),
          "The error budget of Theorem S1(i)",
          "The static vacuum term and the dynamics term of Theorem S1(i) against the ultraviolet "
          "scale N at M = 3, T = 1, d = 1. On the chiral algebra both fall as 4 to the minus N "
          "and stay parallel, so their ratio is fixed by M, T and the degrees. On the full "
          "two-component algebra the static term falls only as 2 to the minus r, half the slope, "
          "and overtakes the dynamics term.")


def fig_resource_scaling():
    R = json.load(open(os.path.join(DATA, "resources.json")))
    d0, n0 = R["delta0"], R["n0"]
    ds = [10 ** (0.1 - 3.2 * i / 200) for i in range(201)]
    f = Fig("Resource scaling, relative to the near-term point (T = 1)",
            "target accuracy δ     (accuracy improves to the right)",
            "resources ÷ near-term point",
            (1.3, 8e-4), (0.4, 3e4), xlog=10, ylog=10)
    f.line(ds, [(d0 / x) ** 1.5 for x in ds], 1, dash="6 4", label="gates ∝ δ⁻³ᐟ²")
    f.line(ds, [(d0 / x) ** 0.5 for x in ds], 0, width=2.4, label="sites n(δ) ∝ δ⁻¹ᐟ²")
    f.line(ds, [(d0 / x) ** 2.0 for x in ds], 3, dash="2 3", width=1.7, label="wavelet gates ∝ δ⁻²")
    f.line(ds, [(d0 / x) for x in ds], 4, dash="2 3", width=1.7, label="wavelet sites ∝ δ⁻¹")
    dy = [r for r in R["dyadic"] if 8e-4 < r["delta"] < 1.3 and r["N"] > R["N0"]]
    f.marks([r["delta"] for r in dy], [r["sites_rel"] for r in dy], 0, 4)
    for r in dy:
        near_edge = f.px(r["delta"]) > f.panel[1] - 70
        f.text(r["delta"], r["sites_rel"], f'N={r["N"]}',
               anchor="end" if near_edge else "start",
               dx=-9 if near_edge else 9, dy=-8, size=11)
    f.star(d0, 1.0)
    f.text(d0, 1.0, f'near-term point: {n0} sites, {2 * n0} qubits, N = 6', anchor="start", dx=11, dy=15, size=11.5)
    write("resource-scaling.svg", f.render("tl"),
          "Resource scaling against target accuracy",
          "Log-log plot of resources relative to the near-term point against target accuracy: "
          "lattice sites rise as delta to the minus one half and gates as delta to the minus "
          "three halves, with the near-term point starred at delta 0.4 and the dyadic lattice "
          "sizes N = 7 to 10 marked on the sites line. The wavelet route without re-centring is "
          "one power of delta worse in each.")


def fig_correlator():
    D = json.load(open(os.path.join(DATA, "correlator.json")))
    width, height = 900, 400
    gap = 84
    half = (width - ML - MR - gap) / 2
    pa = (ML, ML + half, MT + 14, height - MB)
    pb = (ML + half + gap, ML + 2 * half + gap, MT + 14, height - MB)
    assert pb[1] <= width - MR + 0.5, pb

    A = D["panel_a"]
    ylo = min(min(A[k]["err"]) for k in A) / 3
    yhi = max(max(A[k]["err"]) for k in A) * 3
    f1 = Fig("(a)  t = 0.5,  M = 3", "lattice scale N", "|C⁽ᴺ⁾(t) − C(t)|",
             (3.6, 10.4), (ylo, yhi), ylog=10, width=width, height=height, panel=pa)
    for i, k in enumerate(["0", "1", "2"]):
        f1.line(A[k]["N"], A[k]["err"], i, label=f"k = {k}")
        f1.marks(A[k]["N"], A[k]["err"], i, 3.4)
    anchor = A["0"]["err"][A["0"]["N"].index(7)]
    f1.line([5.6, 10.4], [anchor * 4 ** (7 - 5.6), anchor * 4 ** (7 - 10.4)], 5,
            dash="5 4", width=1.3, label="∝ 4⁻ᴺ")
    p1 = f1.render("bl")

    Bp = D["panel_b"]
    ylo2 = min(min(v for v in Bp[k]["err"] if v > 0) for k in Bp) / 3
    yhi2 = max(max(Bp[k]["err"]) for k in Bp) * 3
    f2 = Fig(f'(b)  N = {D["N_panel_b"]},  M = 3', "t", "|C⁽ᴺ⁾(t) − C(t)|",
             (0, 2.05), (ylo2, yhi2), ylog=10, width=width, height=height, panel=pb)
    for i, k in enumerate(["0", "1", "2"]):
        f2.line(Bp[k]["t"], Bp[k]["err"], i, label=f"k = {k}")
    p2 = f2.render("tl")
    write("correlator-convergence.svg", p1 + p2[1:],
          "Correlator-level convergence",
          "Two panels. Left: the correlator error against the lattice scale N at fixed time 0.5, "
          "falling on a straight line of slope four per step for k equal to 0, 1 and 2. Right: "
          "the error against time at N = 8, bounded for k equal to 0 and 1 but rising sharply "
          "for k equal to 2 beyond t about 1.5.",
          width=width, height=height)


def fig_scales():
    B = json.load(open(os.path.join(DATA, "budget.json")))
    eta = lambda r: B["eta"][str(r)]["chiral"] if str(r) in B["eta"] else (math.pi ** 2 / 16) * 4.0 ** -r
    f = Fig("The lattice-vacuum bound depends on the depth r = N − M, not on N alone",
            "ultraviolet scale N", "η (chiral algebra), upper bound",
            (1.6, 14.4), (eta(13) / 3, eta(0) * 3), ylog=10)
    for i, M in enumerate([1, 2, 3, 4, 5]):
        Ns = list(range(M + 1, 15))
        ys = [eta(N - M) for N in Ns]
        f.line(Ns, ys, i, label=f"M = {M}")
        f.marks(Ns, ys, i, 3)
    write("scales.svg", f.render("tr"),
          "The vacuum bound against the ultraviolet scale, for five observation scales",
          "The lattice-vacuum bound eta against the ultraviolet scale N for observation scales "
          "M = 1 to 5: five parallel lines on a logarithmic axis, shifted by exactly one decade "
          "per two steps of M, which collapse onto a single line when plotted against the depth "
          "r = N - M.")


if __name__ == "__main__":
    fig_error_budget()
    fig_resource_scaling()
    fig_correlator()
    fig_scales()
