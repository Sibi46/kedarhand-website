(() => {
  'use strict';
  const button = document.getElementById('mobile-menu-button');
  const menu = document.getElementById('mobile-menu');
  if (!button || !menu) return;
  const close = () => { if (menu.open) menu.close(); };
  button.addEventListener('click', () => {
    const route = location.hash.slice(1) || 'home';
    menu.querySelectorAll('nav a').forEach(link => {
      const url = new URL(link.href);
      const target = url.hash.slice(1) || url.pathname.match(/\/categories\/([^/]+)\/?$/)?.[1] || (url.pathname.endsWith('/shop/') ? 'shop' : 'home');
      if (target === route) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    menu.showModal();
    button.setAttribute('aria-expanded', 'true');
    document.body.classList.add('mobile-menu-open');
  });
  menu.addEventListener('close', () => {
    button.setAttribute('aria-expanded', 'false');
    document.body.classList.remove('mobile-menu-open');
    button.focus({preventScroll: true});
  });
  menu.addEventListener('click', event => {
    if (event.target.closest('a,[data-close-mobile-menu]')) close();
    if (event.target === menu) {
      const box = menu.getBoundingClientRect();
      if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) close();
    }
  });
  window.addEventListener('hashchange', close);
  window.matchMedia('(min-width: 761px)').addEventListener('change', event => { if (event.matches) close(); });
})();
