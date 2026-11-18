const announcementToggle = document.querySelector('#announcement-toggle');
announcementToggle?.addEventListener('click', () => {
  const paused = announcementToggle.closest('.announcement').classList.toggle('is-paused');
  announcementToggle.setAttribute('aria-pressed', String(paused));
  announcementToggle.setAttribute('aria-label', paused ? 'Resume scrolling announcement' : 'Pause scrolling announcement');
  announcementToggle.textContent = paused ? 'Resume' : 'Pause';
});
