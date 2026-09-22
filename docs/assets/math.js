/* math.js — render the mathematics with the vendored KaTeX in assets/katex/.
 *
 * Classic script, loaded with `defer` after katex.min.js and auto-render.min.js, so it
 * runs before DOMContentLoaded fires.  Nothing is fetched from a third-party host: the
 * stylesheet, the script and all twenty woff2 faces are in this repository, and the page
 * renders offline from a plain clone.
 *
 * If KaTeX is missing the page still reads: every formula is written so that its TeX
 * source is legible, and the delimiters are left in place rather than hidden.
 */
(function () {
  function render() {
    if (typeof renderMathInElement !== 'function') {
      /* KaTeX did not load.  Every formula on this site is written so that its TeX source
       * reads, so the fallback is to drop the delimiters rather than to hide the maths:
       * "\(\delta^{-3/2}\)" becomes "\delta^{-3/2}", which a physicist can read. */
      document.documentElement.classList.add('no-katex');
      const walk = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      const hits = [];
      for (let n = walk.nextNode(); n; n = walk.nextNode()) {
        if (/\\\(|\\\)|\$\$/.test(n.nodeValue)) hits.push(n);
      }
      for (const n of hits) n.nodeValue = n.nodeValue.replace(/\\\(|\\\)|\$\$/g, '');
      return;
    }
    renderMathInElement(document.body, {
      delimiters: [
        { left: '$$', right: '$$', display: true },
        { left: '\\[', right: '\\]', display: true },
        { left: '\\(', right: '\\)', display: false },
      ],
      ignoredClasses: ['no-math', 'plot', 'check'],
      throwOnError: false,
      errorColor: '#cf222e',
    });
    document.documentElement.classList.add('katex-ready');
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', render);
  else render();
})();
