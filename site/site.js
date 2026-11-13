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
  // Selected work carousel: arrows, a position counter, and buttons that disable at either end
  const rail = d.querySelector('.rail'), ctl = d.querySelector('.rail-controls');
  if (rail && ctl) {
    const cards = [...rail.children], prev = ctl.querySelector('.prev'), next = ctl.querySelector('.next'), count = ctl.querySelector('.rail-count');
    const step = () => cards[1] ? cards[1].offsetLeft - cards[0].offsetLeft : rail.clientWidth;
    const update = () => {
      const scrollable = rail.scrollWidth > rail.clientWidth + 4;
      ctl.hidden = !scrollable;
      if (!scrollable) return;
      const first = Math.round(rail.scrollLeft / step());
      const shown = Math.max(1, Math.round(rail.clientWidth / step()));
      count.textContent = `${first + 1}\u2013${Math.min(cards.length, first + shown)} of ${cards.length}`;
      prev.disabled = rail.scrollLeft <= 2;
      next.disabled = rail.scrollLeft + rail.clientWidth >= rail.scrollWidth - 2;
    };
    prev.addEventListener('click', () => rail.scrollBy({ left: -step(), behavior: 'smooth' }));
    next.addEventListener('click', () => rail.scrollBy({ left: step(), behavior: 'smooth' }));
    rail.addEventListener('scroll', () => requestAnimationFrame(update), { passive: true });
    addEventListener('resize', update); update();
    rail.addEventListener('keydown', e => {
      if (e.target !== rail) return;
      if (e.key === 'ArrowRight') { e.preventDefault(); next.click(); }
      if (e.key === 'ArrowLeft') { e.preventDefault(); prev.click(); }
    });
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
