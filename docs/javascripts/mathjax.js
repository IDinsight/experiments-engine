window.MathJax = {
  tex: {
    inlineMath: [['$', '$'], ['\\(', '\\)']],
    displayMath: [['$$', '$$'], ['\\[', '\\]']],
    processEscapes: true,
    processEnvironments: true,
    packages: {'[+]': ['base', 'ams', 'noerrors', 'noundefined', 'boldsymbol']},
    macros: {
      bm: ["\\boldsymbol{#1}", 1]
    }
  },
  options: {
    ignoreHtmlClass: 'docs-md-plain',
    processHtmlClass: 'arithmatex'
  },
  startup: {
    ready: () => {
      console.log('MathJax is loaded, but not yet initialized');
      MathJax.startup.defaultReady();
      console.log('MathJax is initialized, and the initial typeset is queued');
    }
  }
};

document$.subscribe(() => {
  MathJax.startup.output.clearCache()
  MathJax.texReset()
  MathJax.typesetClear()
  MathJax.typesetPromise()
})
