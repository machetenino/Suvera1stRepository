/* ══════════════════════════════════════════════
   SUVERA  ·  Main Script
   - Nav slim on scroll
   - Scroll reveal (IntersectionObserver)
   - Parallax: image break + statement bg
   - Smooth anchor scroll
══════════════════════════════════════════════ */

'use strict';

/* ─────────────────────────────────
   NAV — slim on scroll
───────────────────────────────── */
(function () {
  const nav = document.getElementById('nav');
  if (!nav) return;

  const update = () => nav.classList.toggle('slim', window.scrollY > 60);
  window.addEventListener('scroll', update, { passive: true });
  update();
}());


/* ─────────────────────────────────
   SCROLL REVEAL
───────────────────────────────── */
(function () {
  const els = document.querySelectorAll('.reveal');
  if (!els.length) return;

  const io = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: '0px 0px -48px 0px' }
  );

  els.forEach((el) => io.observe(el));
}());


/* ─────────────────────────────────
   PARALLAX
   Uses rAF loop for smooth motion.
   Applies to:
     .parallax       → imgbreak inner
     .parallax-stmt  → statement bg
───────────────────────────────── */
(function () {
  const vh = () => window.innerHeight;

  // Compute offset for any parallax element
  function getOffset(el, strength) {
    const section = el.parentElement;
    const r = section.getBoundingClientRect();
    const h = vh();

    // Skip elements fully off-screen
    if (r.bottom < -100 || r.top > h + 100) return null;

    // Progress: 0 when section bottom hits viewport top → 1 when section top hits viewport bottom
    const progress = (h - r.top) / (h + r.height);
    return ((progress - 0.5) * strength).toFixed(2);
  }

  const breakEl = document.querySelector('.parallax');
  const stmtEl  = document.querySelector('.parallax-stmt');

  let ticking = false;

  function onScroll() {
    if (ticking) return;
    ticking = true;

    requestAnimationFrame(() => {
      if (breakEl) {
        const y = getOffset(breakEl, 110);
        if (y !== null) breakEl.style.transform = `translateY(${y}px)`;
      }

      if (stmtEl) {
        const y = getOffset(stmtEl, 80);
        if (y !== null) stmtEl.style.transform = `translateY(${y}px)`;
      }

      ticking = false;
    });
  }

  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll, { passive: true });
  onScroll();
}());


/* ─────────────────────────────────
   SMOOTH ANCHOR LINKS
   (Polyfill for browsers that
    don't respect scroll-behavior)
───────────────────────────────── */
(function () {
  document.querySelectorAll('a[href^="#"]').forEach((a) => {
    a.addEventListener('click', (e) => {
      const target = document.querySelector(a.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}());
