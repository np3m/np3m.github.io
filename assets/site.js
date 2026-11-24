// NP3M — navigation, live seminar list, and hero animation
(function () {
  // ---- mobile nav + dropdowns
  var burger = document.querySelector('.burger');
  var nav = document.getElementById('primary-nav');
  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      burger.setAttribute('aria-expanded', open);
    });
  }
  document.querySelectorAll('.has-menu > button').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      var li = btn.parentElement;
      var open = !li.classList.contains('open');
      document.querySelectorAll('.has-menu.open').forEach(function (x) {
        if (x !== li) { x.classList.remove('open'); x.firstElementChild.setAttribute('aria-expanded', 'false'); }
      });
      li.classList.toggle('open', open);
      btn.setAttribute('aria-expanded', open);
      e.stopPropagation();
    });
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest('.has-menu')) {
      document.querySelectorAll('.has-menu.open').forEach(function (x) {
        x.classList.remove('open'); x.firstElementChild.setAttribute('aria-expanded', 'false');
      });
    }
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') document.querySelectorAll('.has-menu.open').forEach(function (x) { x.classList.remove('open'); });
  });

  // ---- home page: keep "upcoming seminars" current without rebuilding
  var data = document.getElementById('seminar-data');
  var list = document.getElementById('sem-list');
  if (data && list) {
    try {
      var all = JSON.parse(data.textContent);
      var today = new Date(); today.setHours(0, 0, 0, 0);
      var parse = function (s) { var p = s.split('-'); return new Date(+p[0], +p[1] - 1, +p[2]); };
      var up = all.filter(function (x) { return parse(x.d) >= today; });
      var show = up.length ? up.slice(0, 3) : all.slice(-3).reverse();
      document.getElementById('sem-heading').textContent = up.length ? 'Upcoming Seminars' : 'Recent Seminars';
      var mon = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
      list.innerHTML = '';
      show.forEach(function (x) {
        var d = parse(x.d);
        var li = document.createElement('li'); li.className = 'event';
        var tile = document.createElement('div'); tile.className = 'datetile';
        var m = document.createElement('span'); m.textContent = mon[d.getMonth()];
        var b = document.createElement('b'); b.textContent = d.getDate();
        tile.append(m, b);
        var body = document.createElement('div');
        var t = document.createElement(x.v ? 'a' : 'p'); t.className = 'event-title';
        t.textContent = 'NP3M Seminar with ' + x.s;
        if (x.v) { t.href = x.v; t.style.display = 'block'; t.style.textDecoration = 'none'; }
        var meta = document.createElement('p'); meta.className = 'event-meta'; meta.textContent = x.i;
        body.append(t, meta);
        li.append(tile, body);
        list.appendChild(li);
      });
    } catch (err) { /* keep server-rendered list */ }
  }

  // ---- hero: inspiralling neutron stars emitting gravitational waves
  var canvas = document.querySelector('.hero-canvas');
  if (!canvas) return;
  var ctx = canvas.getContext('2d');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var W, H, dpr, stars = [], waves = [], t0 = performance.now(), lastEmit = 0, running = true;

  function resize() {
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    var r = canvas.getBoundingClientRect();
    W = r.width; H = r.height;
    canvas.width = W * dpr; canvas.height = H * dpr;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    stars = [];
    var n = Math.round(W * H / 2600);
    for (var i = 0; i < n; i++) stars.push({ x: Math.random() * W, y: Math.random() * H, r: Math.random() * 1.3 + .2, a: Math.random() * .7 + .15, tw: Math.random() * 6.28 });
  }

  function center() {
    return W > 900 ? { x: W * .74, y: H * .52 } : { x: W * .78, y: H * .3 };
  }

  var CYCLE = 9; // seconds per inspiral
  function frame(now) {
    if (!running) return;
    var t = (now - t0) / 1000;
    var c = center();
    var phase = (t % CYCLE) / CYCLE;                // 0 → 1 inspiral progress
    var sep = (W > 900 ? 120 : 70) * Math.pow(1 - phase * .92, .25);
    var omega = 2.2 / Math.pow(sep / (W > 900 ? 120 : 70), 1.5);
    var ang = t * omega;
    ctx.clearRect(0, 0, W, H);

    // stars
    for (var i = 0; i < stars.length; i++) {
      var s = stars[i];
      ctx.globalAlpha = s.a * (.75 + .25 * Math.sin(t * 1.3 + s.tw));
      ctx.fillStyle = '#dfe8ff';
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, 6.283); ctx.fill();
    }
    ctx.globalAlpha = 1;

    // emit wave rings at twice orbital frequency
    var period = Math.PI / omega;
    if (t - lastEmit > period) { waves.push({ born: t, amp: 1 - phase * .2 }); lastEmit = t; }
    var maxR = Math.hypot(W, H);
    waves = waves.filter(function (w) { return (t - w.born) * 110 < maxR; });
    ctx.lineWidth = 1.4;
    waves.forEach(function (w) {
      var r = (t - w.born) * 110 + sep * .6;
      var a = Math.max(0, .38 * (1 - r / (maxR * .7))) * w.amp;
      if (a <= 0) return;
      ctx.strokeStyle = 'rgba(156,203,216,' + a + ')';
      ctx.beginPath(); ctx.ellipse(c.x, c.y, r, r * .62, -0.25, 0, 6.283); ctx.stroke();
    });

    // orbit trace
    ctx.strokeStyle = 'rgba(255,255,255,.08)';
    ctx.beginPath(); ctx.ellipse(c.x, c.y, sep, sep * .62, -0.25, 0, 6.283); ctx.stroke();

    // two neutron stars
    var flash = phase > .97 ? (phase - .97) / .03 : 0;
    [0, Math.PI].forEach(function (off, k) {
      var x0 = Math.cos(ang + off) * sep, y0 = Math.sin(ang + off) * sep * .62;
      var x = c.x + x0 * Math.cos(-.25) - y0 * Math.sin(-.25);
      var y = c.y + x0 * Math.sin(-.25) + y0 * Math.cos(-.25);
      var rad = W > 900 ? 15 : 10;
      var g = ctx.createRadialGradient(x, y, 0, x, y, rad * 4);
      g.addColorStop(0, k ? 'rgba(222,138,46,.55)' : 'rgba(156,203,216,.6)');
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g; ctx.beginPath(); ctx.arc(x, y, rad * 4, 0, 6.283); ctx.fill();
      var g2 = ctx.createRadialGradient(x - rad * .35, y - rad * .35, rad * .1, x, y, rad);
      g2.addColorStop(0, '#ffffff');
      g2.addColorStop(.45, k ? '#f2b56b' : '#bfe3ee');
      g2.addColorStop(1, k ? '#c4532a' : '#3f78ad');
      ctx.fillStyle = g2; ctx.beginPath(); ctx.arc(x, y, rad, 0, 6.283); ctx.fill();
    });

    // merger flash (kilonova)
    if (flash > 0) {
      var fr = 30 + flash * 160;
      var fg = ctx.createRadialGradient(c.x, c.y, 0, c.x, c.y, fr);
      fg.addColorStop(0, 'rgba(255,240,220,' + (.9 * flash) + ')');
      fg.addColorStop(.4, 'rgba(222,138,46,' + (.45 * flash) + ')');
      fg.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = fg; ctx.beginPath(); ctx.arc(c.x, c.y, fr, 0, 6.283); ctx.fill();
    }
    if (!reduce) requestAnimationFrame(frame);
  }

  resize();
  window.addEventListener('resize', resize);
  if (reduce) { t0 = performance.now() - 4000; frame(performance.now()); }
  else {
    requestAnimationFrame(frame);
    // pause when hero is off-screen
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (es) {
        var vis = es[0].isIntersecting;
        if (vis && !running) { running = true; requestAnimationFrame(frame); }
        else if (!vis) running = false;
      }).observe(canvas);
    }
  }
})();
