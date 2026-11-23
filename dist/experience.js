(() => {
  'use strict';
  const app = document.getElementById('app');
  if (!app) return;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  let paused = false;
  let giftEnquiry = '';
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
  const slides = [
    {...rituals.coffee, image: 'coffee-table.jpg', key: 'coffee'},
    {...rituals.tea, key: 'tea'},
    {...rituals.kitchen, image: 'oil-kitchen.jpg', key: 'kitchen'},
    {...rituals.coffee, image: 'coffee-beans.jpg', alt: 'Roasted beans and ground coffee', key: 'coffee'},
    {...rituals.coffee, image: 'coffee-moment.jpg', alt: 'A fresh cup of coffee', key: 'coffee'}
  ];
  let slideIndex = 0;
  function showSlide(index, manual = false) {
    const photo = app.querySelector('[data-ritual-photo]');
    if (!photo) return;
    slideIndex = (index + slides.length) % slides.length;
    const slide = slides[slideIndex];
    photo.src = asset + slide.image;
    photo.alt = slide.alt;
    const caption = app.querySelector('[data-ritual-caption]');
    caption.setAttribute('aria-live', manual ? 'polite' : 'off');
    caption.textContent = slide.caption;
    const link = app.querySelector('[data-ritual-link]');
    link.href = '#' + slide.route;
    link.setAttribute('aria-label', 'Explore ' + (slide.key === 'kitchen' ? 'edible oils' : slide.key));
    app.querySelector('.ritual-stage').dataset.activeRitual = slide.key;
    app.querySelectorAll('[data-ritual]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.ritual === slide.key)));
    const count = app.querySelector('[data-banner-index]');
    if (count) count.textContent = String(slideIndex + 1).padStart(2, '0') + ' / 05';
  }
  slides.forEach(slide => { const preload = new Image(); preload.src = asset + slide.image; });
  setInterval(() => {
    const hero = app.querySelector('.experience-hero');
    if (!hero || paused || reduceMotion.matches || document.hidden || hero.matches(':hover,:focus-within')) return;
    const bounds = hero.getBoundingClientRect();
    if (bounds.bottom <= 0 || bounds.top >= innerHeight) return;
    showSlide(slideIndex + 1);
  }, 1000);
  function enhance() {
    const hero = app.querySelector('.experience-hero');
    if (hero && !hero.dataset.carouselReady) {
      hero.dataset.carouselReady = 'true';
      showSlide(0);
    }
    const message = app.querySelector('#contact-enquiry textarea[name="message"]');
    if (giftEnquiry && message && !message.value) {
      message.value = `Hello Kedarmart, I would like to enquire about ${giftEnquiry} for a loved one. Please share the available options, packaging, prices and delivery details.`;
      giftEnquiry = '';
    }
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
    if (event.target.closest('[data-banner-prev]')) showSlide(slideIndex - 1, true);
    if (event.target.closest('[data-banner-next]')) showSlide(slideIndex + 1, true);
    if (event.target.closest('[data-scroll-collection]')) {
      app.querySelector('.photo-collection-page .products')?.scrollIntoView({behavior: reduceMotion.matches ? 'auto' : 'smooth', block: 'start'});
    }
    const filter = event.target.closest('[data-home-filter]');
    if (filter) {
      const category = filter.dataset.homeFilter;
      const target = app.querySelector('.modern-products .products');
      if (target) {
        const selection = products.filter(product => category === 'all' || product.cat === category).slice(0, 4);
        target.innerHTML = grid(selection);
        app.querySelectorAll('[data-home-filter]').forEach(button => button.setAttribute('aria-pressed', String(button === filter)));
        const description = app.querySelector('[data-filter-description]');
        description.textContent = selection.length ? (category === 'all' ? 'Explore our featured everyday essentials.' : `Explore our ${filter.textContent.trim().toLowerCase()} collection.`) : 'New products will appear here as they are added. Explore all products or contact our team.';
      }
    }
    const giftLink = event.target.closest('[data-gift-enquiry]');
    if (giftLink) giftEnquiry = giftLink.dataset.giftEnquiry;
    const choice = event.target.closest('[data-ritual]');
    if (choice && rituals[choice.dataset.ritual]) {
      showSlide(slides.findIndex(slide => slide.key === choice.dataset.ritual), true);
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
