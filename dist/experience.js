(() => {
  'use strict';
  const app = document.getElementById('app');
  if (!app) return;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let paused = false;
  try { paused = sessionStorage.getItem('kedarhand-motion-paused') === 'true'; } catch (_) {}
  document.documentElement.classList.toggle('motion-paused', paused);
  const observer = 'IntersectionObserver' in window ? new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px 30px 0px' }) : null;
  const asset = (window.KEDARMART_BASE_PATH !== undefined ? (window.KEDARMART_BASE_PATH || '') + '/static/assets/' : 'assets/');
  const rituals = {
    coffee: { image: 'coffee-ritual.jpg', alt: 'Freshly brewed coffee for a quiet morning', caption: '01 / THE COFFEE MOMENT', route: 'coffee' },
    tea: { image: 'tea-moment.jpg', alt: 'A comforting cup of tea', caption: '02 / A MOMENT FOR TEA', route: 'tea' },
    kitchen: { image: 'kitchen-essentials.jpg', alt: 'Cooking oil and ingredients for everyday meals', caption: '03 / SOMETHING DELICIOUS STARTS HERE', route: 'edible-oils' }
  };
  function enhance() {
    if (observer && !reduceMotion.matches && !paused) {
      app.querySelectorAll('.modern-heading,.category,.products>article,.story-photo,.story-copy,.brand-story,.kitchen-feature,.visual-interlude,.newsletter').forEach((element, index) => {
        if (element.hasAttribute('data-reveal-ready')) return;
        element.setAttribute('data-reveal-ready', '');
        element.style.setProperty('--reveal-delay', `${element.matches('.category,.products>article') ? index % 3 * 70 : 0}ms`);
        observer.observe(element);
      });
    }
    const toggle = app.querySelector('[data-motion-toggle]');
    if (toggle) {
      toggle.setAttribute('aria-pressed', String(paused));
      const label = paused ? 'Resume motion' : 'Pause motion';
      if (toggle.textContent !== label) toggle.textContent = label;
    }
  }
  app.addEventListener('click', event => {
    const choice = event.target.closest('[data-ritual]');
    if (choice && rituals[choice.dataset.ritual]) {
      const ritual = rituals[choice.dataset.ritual];
      const photo = app.querySelector('[data-ritual-photo]');
      if (!photo) return;
      photo.src = asset + ritual.image;
      photo.alt = ritual.alt;
      app.querySelector('[data-ritual-caption]').textContent = ritual.caption;
      const link = app.querySelector('[data-ritual-link]');
      link.href = '#' + ritual.route;
      link.setAttribute('aria-label', 'Explore ' + (choice.dataset.ritual === 'kitchen' ? 'edible oils' : choice.dataset.ritual));
      app.querySelector('.ritual-stage').dataset.activeRitual = choice.dataset.ritual;
      app.querySelectorAll('[data-ritual]').forEach(button => button.setAttribute('aria-pressed', String(button === choice)));
    }
    if (event.target.closest('[data-motion-toggle]')) {
      paused = !paused;
      document.documentElement.classList.toggle('motion-paused', paused);
      try { sessionStorage.setItem('kedarhand-motion-paused', String(paused)); } catch (_) {}
      if (paused) app.querySelectorAll('[data-reveal-ready]').forEach(element => element.classList.add('is-visible'));
      enhance();
    }
  });
  let frame;
  new MutationObserver(() => {
    cancelAnimationFrame(frame);
    frame = requestAnimationFrame(enhance);
  }).observe(app, {childList: true, subtree: true});
  reduceMotion.addEventListener('change', () => {
    if (reduceMotion.matches) app.querySelectorAll('[data-reveal-ready]').forEach(element => element.classList.add('is-visible'));
    else enhance();
  });
  window.addEventListener('beforeprint', () => app.querySelectorAll('[data-reveal-ready]').forEach(element => element.classList.add('is-visible')));
  enhance();
})();
