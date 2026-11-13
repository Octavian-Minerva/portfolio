(() => {
  const d = document, root = d.documentElement;
  const head = d.querySelector('.site-head'), bar = d.querySelector('.progress');
  // Header shadow and reading progress
  const onScroll = () => {
    const max = root.scrollHeight - innerHeight;
    if (head) head.classList.toggle('scrolled', scrollY > 4);
    if (bar) bar.style.setProperty('--p', max > 0 ? Math.min(1, scrollY / max).toFixed(4) : 0);
  };
  addEventListener('scroll', onScroll, { passive: true }); addEventListener('resize', onScroll); onScroll();
  // On small screens, tuck the header away while scrolling down and bring it back on the way up
  let lastY = scrollY;
  const small = matchMedia('(max-width: 900px)');
  addEventListener('scroll', () => {
    const y = scrollY;
    if (head && small.matches) {
      if (y > lastY + 6 && y > 140 && !head.contains(d.activeElement)) head.classList.add('head-hidden');
      else if (y < lastY - 6 || y <= 140) head.classList.remove('head-hidden');
    } else if (head) head.classList.remove('head-hidden');
    lastY = y;
  }, { passive: true });
  if (head) head.addEventListener('focusin', () => head.classList.remove('head-hidden'));
  // Highlight the section currently in view: the last section whose top has passed 40% of the screen
  const pairs = [...d.querySelectorAll('.nav a[href*="#"]')]
    .map(a => [d.getElementById(a.hash.slice(1)), a]).filter(([sec]) => sec);
  const spy = () => {
    if (!pairs.length) return;
    let hit = null;
    for (const p of pairs) if (p[0].getBoundingClientRect().top <= innerHeight * 0.4) hit = p;
    if (innerHeight + scrollY >= root.scrollHeight - 2) hit = pairs[pairs.length - 1];
    pairs.forEach(([, a]) => {
      const on = hit && a === hit[1];
      a.classList.toggle('is-current', on);
      if (on) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current');
    });
  };
  addEventListener('scroll', spy, { passive: true }); spy();
  // Selected work: on wide screens, a centred carousel with the active card in focus
  const rail = d.querySelector('.rail');
  if (rail) {
    const cards = [...rail.children];
    const prev = d.querySelector('.rail-btn.prev'), next = d.querySelector('.rail-btn.next'), count = d.querySelector('.rail-count');
    const wide = matchMedia('(min-width: 701px)');
    let active = 0;
    const centreOf = el => el.offsetLeft + el.offsetWidth / 2;
    const goTo = (i, smooth = true) => {
      i = Math.max(0, Math.min(cards.length - 1, i));
      rail.scrollTo({ left: centreOf(cards[i]) - rail.clientWidth / 2, behavior: smooth ? 'smooth' : 'auto' });
    };
    const update = () => {
      if (!rail.classList.contains('cover')) return;
      const mid = rail.scrollLeft + rail.clientWidth / 2;
      let best = 0, dist = Infinity;
      cards.forEach((c, i) => { const dd = Math.abs(centreOf(c) - mid); if (dd < dist) { dist = dd; best = i; } });
      active = best;
      cards.forEach((c, i) => c.classList.toggle('is-active', i === active));
      count.textContent = `${active + 1} of ${cards.length}`;
      prev.disabled = active === 0;
      next.disabled = active === cards.length - 1;
    };
    const mode = () => {
      const on = wide.matches;
      rail.classList.toggle('cover', on);
      [prev, next, count].forEach(el => { if (el) el.hidden = !on; });
      if (!on) cards.forEach(c => c.classList.remove('is-active'));
      else { goTo(active, false); update(); }
    };
    prev.addEventListener('click', () => goTo(active - 1));
    next.addEventListener('click', () => goTo(active + 1));
    // a faded card comes to the centre when clicked (links inside it still work once it is active)
    cards.forEach((c, i) => c.addEventListener('click', e => {
      if (rail.classList.contains('cover') && i !== active) { e.preventDefault(); goTo(i); }
    }));
    // keyboard focus moving into a faded card brings it to the centre
    cards.forEach((c, i) => c.addEventListener('focusin', () => { if (rail.classList.contains('cover') && i !== active) goTo(i); }));
    rail.addEventListener('scroll', () => requestAnimationFrame(update), { passive: true });
    rail.addEventListener('keydown', e => {
      if (e.target !== rail) return;
      if (e.key === 'ArrowRight') { e.preventDefault(); goTo(active + 1); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); goTo(active - 1); }
    });
    if (wide.addEventListener) wide.addEventListener('change', mode);
    addEventListener('resize', () => { if (rail.classList.contains('cover')) goTo(active, false); });
    mode();
  }
  // Light and dark themes: follow the system unless the visitor has chosen
  const mq = matchMedia('(prefers-color-scheme: dark)');
  const now = () => root.dataset.theme || (mq.matches ? 'dark' : 'light');
  const toggle = d.querySelector('.theme-toggle');
  const sync = () => {
    root.dataset.themeNow = now();
    if (toggle) toggle.setAttribute('aria-label', now() === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
  };
  if (toggle) {
    toggle.hidden = false;
    toggle.addEventListener('click', () => {
      root.dataset.theme = now() === 'dark' ? 'light' : 'dark';
      try { localStorage.setItem('theme', root.dataset.theme); } catch (e) {}
      sync();
    });
  }
  if (mq.addEventListener) mq.addEventListener('change', sync);
  sync();
  // Copy email addresses
  const live = d.getElementById('live');
  if (navigator.clipboard) d.querySelectorAll('.copy').forEach(b => {
    b.hidden = false;
    b.addEventListener('click', async () => {
      try {
        await navigator.clipboard.writeText(b.dataset.copy);
        b.textContent = 'Copied'; if (live) live.textContent = 'Email address copied';
        setTimeout(() => { b.textContent = 'Copy'; }, 1800);
      } catch (e) {}
    });
  });
})();
