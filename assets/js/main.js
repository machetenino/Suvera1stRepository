/* ════════════════════════════════════════════
   SUVERA — MAIN SCRIPT
════════════════════════════════════════════ */

'use strict';

/* ─── NAV: shrink on scroll ─── */
(function initNav() {
  const nav = document.getElementById('nav');
  if (!nav) return;

  const onScroll = () => {
    if (window.scrollY > 60) {
      nav.classList.add('scrolled');
    } else {
      nav.classList.remove('scrolled');
    }
  };

  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();
})();


/* ─── SCROLL REVEAL ─── */
(function initReveal() {
  const els = document.querySelectorAll('.reveal');
  if (!els.length) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    },
    {
      threshold: 0.1,
      rootMargin: '0px 0px -56px 0px',
    }
  );

  els.forEach((el) => observer.observe(el));
})();


/* ─── PARALLAX: image break section ─── */
(function initParallax() {
  const imgs = document.querySelectorAll('.parallax-img');
  if (!imgs.length) return;

  const update = () => {
    const vh = window.innerHeight;

    imgs.forEach((img) => {
      const section = img.closest('.image-break');
      if (!section) return;

      const rect = section.getBoundingClientRect();

      // Only compute when section is near the viewport
      if (rect.bottom < -100 || rect.top > vh + 100) return;

      // Progress: 0 (section bottom at viewport top) → 1 (section top at viewport bottom)
      const progress = 1 - (rect.top / (vh + rect.height));
      // Map progress to a modest offset: -60px → +60px
      const offset = (progress - 0.5) * 120;

      img.style.transform = `translateY(${offset.toFixed(2)}px)`;
    });
  };

  window.addEventListener('scroll', update, { passive: true });
  window.addEventListener('resize', update, { passive: true });
  update();
})();


/* ─── SMOOTH anchor links ─── */
(function initSmoothAnchors() {
  document.querySelectorAll('a[href^="#"]').forEach((anchor) => {
    anchor.addEventListener('click', (e) => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (!target) return;

      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
})();


/* ─── SERVICE CARDS: stagger reveal ─── */
(function initServiceCards() {
  const cards = document.querySelectorAll('.service-card');
  if (!cards.length) return;

  // Assign grid-position-aware delays so cards cascade left→right, top→bottom
  const cols = window.innerWidth > 1024 ? 3 : window.innerWidth > 680 ? 2 : 1;

  cards.forEach((card, i) => {
    const col = i % cols;
    card.style.transitionDelay = `${col * 0.08}s`;
  });
})();
