/* Animates the homepage schematic. Same toy formulas as docs/tools/make_figures.py:
   a V1 site responds when the object's edge passes over it at its preferred
   orientation; a V2 unit averages V1 drive over a larger region. Illustrative only. */
(function () {
  var svg = document.querySelector('.hero-figure svg');
  if (!svg || !svg.dataset.cfg) return;
  var cfg = JSON.parse(svg.dataset.cfg);
  var stim = svg.querySelector('#hero-stim');
  var A = cfg.stim.a, B = cfg.stim.b, TWO_S2 = 2 * cfg.stim.sigma * cfg.stim.sigma;

  var bars = Array.prototype.map.call(svg.querySelectorAll('.hero-bars line'), function (el) {
    var p = el.dataset.p.split(',').map(Number);
    return { el: el, x: p[0], y: p[1], t: p[2], d: 0, shown: -1 };
  });
  var units = Array.prototype.map.call(svg.querySelectorAll('.hero-unit'), function (el) {
    var p = el.dataset.p.split(',').map(Number), w = [], total = 0;
    bars.forEach(function (b, i) {
      var q = Math.exp(-((b.x - p[0]) * (b.x - p[0]) + (b.y - p[1]) * (b.y - p[1])) / (2 * cfg.v2Sigma * cfg.v2Sigma));
      if (q > 0.02) { w.push([i, q]); total += q; }
    });
    return { el: el, w: w, total: total, shown: -1 };
  });

  var pos = { x: cfg.start[0], y: cfg.start[1], psi: cfg.start[2] };
  var target = null, lastPointer = 0, t0 = null, running = false, visible = true;
  var still = window.matchMedia('(prefers-reduced-motion: reduce)');

  function render() {
    var c = Math.cos(pos.psi), s = Math.sin(pos.psi);
    stim.setAttribute('cx', pos.x.toFixed(1));
    stim.setAttribute('cy', pos.y.toFixed(1));
    stim.setAttribute('transform', 'rotate(' + (pos.psi * 180 / Math.PI).toFixed(1) + ' ' + pos.x.toFixed(1) + ' ' + pos.y.toFixed(1) + ')');
    for (var i = 0; i < bars.length; i++) {
      var b = bars[i], dx = b.x - pos.x, dy = b.y - pos.y;
      var u = dx * c + dy * s, v = -dx * s + dy * c;
      var f = Math.sqrt(u * u / (A * A) + v * v / (B * B)), d = 0;
      if (f > 1e-6) {
        var gu = u / (A * A) / f, gv = v / (B * B) / f, g = Math.sqrt(gu * gu + gv * gv);
        var dist = (f - 1) / g, k = Math.cos(b.t - (Math.atan2(gv, gu) + pos.psi + Math.PI / 2));
        d = Math.exp(-dist * dist / TWO_S2) * k * k;
      }
      b.d = d;
      var o = Math.round((0.13 + 0.87 * d) * 50) / 50;
      if (o !== b.shown) { b.el.setAttribute('stroke-opacity', o); b.shown = o; }
    }
    for (var j = 0; j < units.length; j++) {
      var n = units[j], sum = 0;
      for (var m = 0; m < n.w.length; m++) sum += n.w[m][1] * bars[n.w[m][0]].d;
      var a = Math.round((0.05 + 0.9 * Math.min(1, cfg.v2Gain * sum / n.total)) * 50) / 50;
      if (a !== n.shown) { n.el.setAttribute('fill-opacity', a); n.shown = a; }
    }
  }

  function frame(now) {
    if (t0 === null) t0 = now;
    var t = (now - t0) / 1000;
    var following = target && now - lastPointer < 2500;
    var goal = following ? target : { x: 100 + 30 * Math.sin(0.23 * t), y: 100 + 28 * Math.sin(0.31 * t + 1) };
    pos.x += (goal.x - pos.x) * 0.08;
    pos.y += (goal.y - pos.y) * 0.08;
    pos.psi = cfg.start[2] + 0.22 * t;
    render();
    running = visible && (following || !still.matches);
    if (running) requestAnimationFrame(frame);
  }

  function start() {
    if (!running) { running = true; requestAnimationFrame(frame); }
  }

  svg.addEventListener('pointermove', function (e) {
    if (e.pointerType && e.pointerType !== 'mouse') return;
    var m = svg.getScreenCTM();
    if (!m) return;
    var px = (e.clientX - m.e) / m.a, py = (e.clientY - m.f) / m.d, hit = null;
    ['v2', 'v1', 'img'].forEach(function (level) {
      var p = (px - cfg.cx) / cfg.kx, q = (py - cfg.ty[level]) / cfg.ky;
      var x = (q + p) / 2, y = (q - p) / 2;
      if (x >= 0 && x <= 200 && y >= 0 && y <= 200) hit = { x: Math.min(165, Math.max(35, x)), y: Math.min(165, Math.max(35, y)) };
    });
    if (hit) { target = hit; lastPointer = performance.now(); start(); }
  });

  if ('IntersectionObserver' in window) {
    new IntersectionObserver(function (entries) {
      visible = entries[0].isIntersecting;
      if (visible && !still.matches) start();
    }).observe(svg);
  }
  if (!still.matches) start();
})();
